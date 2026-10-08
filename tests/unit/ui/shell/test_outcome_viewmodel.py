"""Outcome view-model: empty start, latest wins, crash state, summary strip, labels, eyes (UI-02, UI-12, UI-23, UI-27).

Qt-free: the submitter is a list, and results are fed back by hand in any order.
"""

import math
import re

import pytest

from embodic.api import compute
from embodic.geometry.marks import eye_marks
from embodic.geometry.primitives import Line
from embodic.io.examples import load_example
from embodic.io.project import load_project, project_from_example, project_provenance
from embodic.model.vocabulary import Phase
from embodic.results.status import Status
from embodic.ui.viewmodels.outcome import (
    OutcomeComputing,
    OutcomeEmpty,
    OutcomeFailed,
    OutcomeViewModel,
    eyes_shown,
    ready_state,
)

D08 = "spiral_12c10p_d08"


class ListSubmitter:
    """Records requests instead of running them."""

    def __init__(self):
        self.requests = []

    def submit(self, request):
        """Record one request."""
        self.requests.append(request)


@pytest.fixture(scope="module")
def d08_ready():
    """Return what the shell shows of the computed D08 example."""
    project = project_from_example(load_example(D08))
    return ready_state(compute(project.design, project_provenance(project)))


@pytest.mark.req("REQ-F-21")
def test_ui23_the_shell_starts_empty_and_computes_nothing():
    """Catches a shell that opens on a default design or runs a compute before the user picks one (D-014)."""
    submitter = ListSubmitter()
    vm = OutcomeViewModel(submitter)
    vm.compute_now()
    assert isinstance(vm.state.value, OutcomeEmpty)
    assert submitter.requests == []


@pytest.mark.req("REQ-N-02")
def test_ui02_a_superseded_result_never_replaces_the_latest(d08_ready):
    """Catches a late result of an older request overwriting the newer one (latest wins)."""
    submitter = ListSubmitter()
    vm = OutcomeViewModel(submitter)
    vm.open_example(D08)
    vm.compute_now()
    first, second = submitter.requests
    assert second.request_id > first.request_id
    assert isinstance(vm.state.value, OutcomeComputing)
    vm.on_finished(first.request_id, d08_ready)
    assert isinstance(vm.state.value, OutcomeComputing)
    vm.on_finished(second.request_id, d08_ready)
    assert vm.state.value is d08_ready
    vm.on_failed(first.request_id, "stale-id")
    assert vm.state.value is d08_ready


@pytest.mark.req("REQ-N-18")
def test_ui12_a_crash_of_the_latest_request_keeps_the_last_result_and_its_correlation_id(d08_ready):
    """Catches a crash state that drops the drawing on screen or loses the id the log entry carries."""
    submitter = ListSubmitter()
    vm = OutcomeViewModel(submitter)
    vm.open_example(D08)
    vm.on_finished(submitter.requests[-1].request_id, d08_ready)
    vm.compute_now()
    vm.on_failed(submitter.requests[-1].request_id, "c0ffee123456")
    assert vm.state.value == OutcomeFailed(correlation_id="c0ffee123456", previous=d08_ready)


@pytest.mark.req("REQ-N-18")
def test_ui12_save_project_writes_a_file_that_loads_back_as_the_same_design(tmp_path):
    """Catches a recovery save that writes something the project loader refuses."""
    vm = OutcomeViewModel(ListSubmitter())
    vm.open_example(D08)
    path = tmp_path / "recovered.embodic.json"
    vm.save_project(path)
    loaded, issues = load_project(path)
    assert issues == ()
    assert loaded.design == vm.project.design


@pytest.mark.req("REQ-F-13", "REQ-T-01")
def test_summary_strip_shows_verdicts_and_badges_from_the_outcome(d08_ready):
    """Catches a hard-coded badge or verdict: every value and status must come from the outcome (D-007)."""
    items = {item.key: item for item in d08_ready.summary}
    analysis = d08_ready.outcome.analysis
    assert list(items) == ["sum-ok", "sum-drc", "sum-ke", "sum-r-phase"]
    assert (items["sum-ok"].state, items["sum-drc"].state) == ("pass", "pass")
    assert items["sum-ke"].status is analysis.ke_line_peak_v_s_per_rad.status
    assert items["sum-r-phase"].status is analysis.resistance_phase_operating_ohm.status
    assert items["sum-ke"].assumed_count == len(analysis.ke_line_peak_v_s_per_rad.assumed_inputs)
    # D08 values from the engine on main 8a297a0 (verified by running compute): 30.9 mV s/rad, 502 mOhm.
    assert items["sum-ke"].value_text == "30.9 mV·s/rad"
    assert items["sum-r-phase"].value_text == "502 mΩ"
    assert all(item.status is None or isinstance(item.status, Status) for item in items.values())


def _dense_points(prim, count=400):
    for k in range(count + 1):
        f = k / count
        if isinstance(prim, Line):
            yield prim.x1_mm + f * (prim.x2_mm - prim.x1_mm), prim.y1_mm + f * (prim.y2_mm - prim.y1_mm)
        else:
            yield prim.point_at(prim.start_rad + f * prim.sweep_rad)


@pytest.mark.req("REQ-N-23", "REQ-N-14")
def test_ui27_every_top_layer_coil_has_a_label_and_an_eye_that_never_reaches_copper(d08_ready):
    """Catches hatch that crosses a trace (reads as copper) or a coil drawn without its phase letter (UX-AC-05).

    Independent of the marks module's exact arc distance: copper is sampled densely along its centre line.
    """
    scene = d08_ready.scene
    board = scene.boards[0]
    (marks,) = scene.marks
    top = board.copper_layers[0]
    coils = {(p.phase, p.element) for p in board.paths if p.element is not None and p.layer == top}
    eyes = eyes_shown(board, marks, frozenset())
    assert len(marks.anchors) == len(coils) == 12
    assert len(eyes) == 12 and {m.layer for m in eyes} == {top}
    r_inner, r_outer = board.envelope_mm
    for mark in eyes:
        assert mark.eye_radius_mm > 0, mark.label
        assert r_inner < math.hypot(mark.cx_mm, mark.cy_mm) < r_outer, mark.label
        for path in (p for p in board.paths if p.layer == mark.layer):
            for prim in path.primitives:
                nearest = min(math.dist((mark.cx_mm, mark.cy_mm), q) for q in _dense_points(prim))
                assert nearest - prim.width_mm / 2 > mark.eye_radius_mm, (mark.label, path.id)


@pytest.mark.req("REQ-N-23")
def test_ui27_the_canvas_fills_the_eyes_the_exports_fill_and_follows_a_hidden_top_layer(d08_ready):
    """Catches a canvas whose eye set differs from the drawing files (ruling a 3) or vanishes with the top layer."""
    board, marks = d08_ready.scene.boards[0], d08_ready.scene.marks[0]
    assert eyes_shown(board, marks, frozenset()) == eye_marks(board)
    below = eyes_shown(board, marks, frozenset({"L1"}))
    assert len(below) == 12 and {m.layer for m in below} == {"L2"}
    assert eyes_shown(board, marks, frozenset({"L1", "L2"})) == ()


@pytest.mark.req("REQ-N-23")
def test_ui27_spiral_labels_read_phase_number_and_a_true_minus_sign(d08_ready):
    """Catches a hyphen for negative polarity (F22) or coils numbered globally (A1, B2, C3) instead of per phase."""
    texts = [anchor.text for anchor in d08_ready.scene.marks[0].anchors]
    assert all(re.fullmatch("[ABC][1-4][+\u2212]", t) for t in texts), texts
    assert "-" not in "".join(texts)
    assert sorted(t[:2] for t in texts) == [f"{phase.value}{n}" for phase in Phase for n in range(1, 5)]
    assert {t[-1] for t in texts} == {"+", "\u2212"}  # D08 has coils of both polarities


@pytest.mark.req("REQ-N-23")
def test_ui27_each_label_names_the_copper_of_its_own_coil(d08_ready):
    """Catches a hover tooltip that names another coil than the one under the pointer (ruling b: skipped labels)."""
    board = d08_ready.scene.boards[0]
    marks = d08_ready.scene.marks[0]
    by_id = {p.id: p for p in board.paths}
    coil_of_text: dict[str, set] = {}
    for path_id, label in marks.label_of_path.items():
        path = by_id[path_id]
        assert label[0] == path.phase.value, (label, path.id)
        coil_of_text.setdefault(label, set()).add((path.element, path.polarity))
    assert set(coil_of_text) == {anchor.text for anchor in marks.anchors}
    assert all(len(coils) == 1 for coils in coil_of_text.values()), coil_of_text
    assert len({next(iter(c)) for c in coil_of_text.values()}) == 12


@pytest.mark.req("REQ-F-13")
def test_ui04_hiding_a_layer_is_recorded_and_showing_it_again_restores_it():
    """Catches a toggle that cannot bring a hidden layer back."""
    vm = OutcomeViewModel(ListSubmitter())
    vm.set_layer_visible("L2", False)
    assert vm.hidden_layers.value == frozenset({"L2"})
    vm.set_layer_visible("L2", True)
    assert vm.hidden_layers.value == frozenset()
