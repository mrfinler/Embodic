"""DesignSession: state machine, undo, suggestions, provenance chips and autosave (UT-SES-01, UT-SES-02). Qt-free.

Computes are not run here except once for D08: a recording submitter stands in for the worker, and a test delivers a
real D08 result where a kept drawing matters.
"""

import pytest

from embodic.api import compute
from embodic.io.canonical import design_hash
from embodic.io.examples import load_example
from embodic.io.project import ProjectFile, project_from_example, project_provenance
from embodic.model.draft import DesignDraft, blank_draft, draft_from_design, parse_draft
from embodic.model.provenance import ExampleValue, UserValue
from embodic.model.vocabulary import TopologyKind
from embodic.ui.viewmodels.outcome import OutcomeViewModel, ready_state
from embodic.ui.viewmodels.session import (
    DesignSession,
    SessionComputed,
    SessionDocument,
    SessionDrafting,
    SessionEmpty,
    draft_chips,
)

D08 = "spiral_12c10p_d08"


class RecordingSubmitter:
    """Keeps every compute request instead of running it."""

    def __init__(self):
        self.requests = []

    def submit(self, request):
        """Record a request."""
        self.requests.append(request)


@pytest.fixture
def rig(tmp_path):
    """Return (session, outcome view-model, submitter) with autosave into a temporary recovery folder."""
    submitter = RecordingSubmitter()
    outcome = OutcomeViewModel(submitter)
    session = DesignSession(outcome, autosave_path=tmp_path / "recovery" / "autosave.embodic.json")
    return session, outcome, submitter


@pytest.fixture(scope="module")
def d08_ready():
    """Return the real D08 result as the worker would deliver it."""
    ref, design = load_example(D08)
    return ready_state(compute(design, project_provenance(project_from_example((ref, design)))))


def d08_values():
    """Return the draft values of the D08 example."""
    return dict(draft_from_design(load_example(D08)[1]).values)


def current_hash(session):
    """Return the design hash of the open document (it must be complete)."""
    return design_hash(parse_draft(session.document.draft))


def fill(session, values):
    """Edit every pointer whose value differs from the draft's: optional ones first, the required ones last."""
    missing = set(parse_draft(session.document.draft).missing)
    pending = [(p, v) for p, v in values.items() if session.document.draft.values.get(p, object()) != v]
    pending.sort(key=lambda item: any(item[0] == m or item[0].startswith(m + "/") for m in missing))
    for pointer, value in pending:
        session.edit(pointer, value)


@pytest.mark.req("REQ-F-36")
def test_ut_ses_01_empty_to_drafting_to_computed_with_exactly_one_compute(rig):
    """Catches a compute on an incomplete draft, a second compute for one completion, or values lost on the way."""
    session, _, submitter = rig
    assert isinstance(session.state.value, SessionEmpty)
    session.new_design(TopologyKind.SPIRAL)
    state = session.state.value
    assert isinstance(state, SessionDrafting)
    assert state.missing == parse_draft(blank_draft(TopologyKind.SPIRAL)).missing
    assert len(state.missing) == 37
    values = d08_values()
    required_last = [p for p in values if not any(p == m or p.startswith(m + "/") for m in state.missing)]
    for pointer in required_last:
        session.edit(pointer, values[pointer])
    assert submitter.requests == []
    fill(session, values)
    assert isinstance(session.state.value, SessionComputed)
    assert len(submitter.requests) == 1
    assert design_hash(submitter.requests[0].design) == design_hash(load_example(D08)[1])


@pytest.mark.req("REQ-F-36", "REQ-F-27")
def test_ut_ses_01_an_edit_that_empties_a_field_returns_to_drafting_and_keeps_the_drawing_stale(rig, d08_ready):
    """Catches a drafting state that drops the last drawing, or one that is not marked outdated."""
    session, outcome, submitter = rig
    session.load_example(D08)
    outcome.on_finished(submitter.requests[-1].request_id, d08_ready)
    computed = session.state.value
    assert isinstance(computed, SessionComputed)
    assert (computed.outcome, computed.stale, computed.computing) == (d08_ready.outcome, False, False)
    session.edit("/winding/coil/r_inner_mm", None)
    state = session.state.value
    assert isinstance(state, SessionDrafting)
    assert state.missing == ("/winding/coil/r_inner_mm",)
    assert session.drawn(outcome.state.value) == (d08_ready, True)
    assert len(submitter.requests) == 1


@pytest.mark.req("REQ-F-27")
def test_ui18_an_invalid_complete_design_keeps_the_last_drawing_marked_outdated(rig, d08_ready):
    """Catches an invalid edit whose empty result replaces the last valid drawing."""
    session, outcome, submitter = rig
    session.load_example(D08)
    outcome.on_finished(submitter.requests[-1].request_id, d08_ready)
    session.edit("/winding/coil/r_inner_mm", 50.0)  # beyond the outer radius: INVALID_ORDER, no board
    assert {i.code for i in session.issues.value} >= {"INVALID_ORDER"}
    request = submitter.requests[-1]
    invalid = ready_state(compute(request.design, request.provenance))
    assert invalid.scene is None
    outcome.on_finished(request.request_id, invalid)
    state = session.state.value
    assert isinstance(state, SessionComputed)
    assert (state.outcome, state.stale, state.computing) == (d08_ready.outcome, True, False)
    assert session.drawn(outcome.state.value) == (d08_ready, True)
    assert "INVALID_ORDER" in {i.code for i in session.issues.value}


@pytest.mark.req("REQ-F-21")
def test_ut_ses_01_reentering_the_current_value_adds_no_undo_entry_and_no_compute(rig):
    """Catches PR-12: a re-entered value that recomputes, adds an undo step or turns an example chip into user."""
    session, _, submitter = rig
    session.load_example(D08)
    before = (len(submitter.requests), session.can_undo.value, session._undo[:])
    value = session.document.draft.values["/rotor/air_gap_mm"]
    session.edit("/rotor/air_gap_mm", value)
    session.edit("/rotor/air_gap_mm", float(value))
    assert (len(submitter.requests), session.can_undo.value, session._undo) == before
    assert isinstance(session.chips()["/rotor/air_gap_mm"], ExampleValue)


@pytest.mark.req("REQ-F-22")
def test_ut_ses_02_fifty_undo_steps_restore_the_identical_hash_and_provenance(rig):
    """Catches an undo that restores values but not provenance, or a history shorter or longer than 50 steps."""
    session, _, _ = rig
    session.load_example(D08)
    history = [(current_hash(session), dict(session.chips()))]
    for step in range(50):
        session.edit("/operating/speed_rpm", 1100.0 + step)
        history.append((current_hash(session), dict(session.chips())))
    assert len({h for h, _ in history}) == 51
    for expected in reversed(history[:-1]):
        session.undo()
        assert (current_hash(session), dict(session.chips())) == expected
    assert session.can_undo.value is False
    assert isinstance(session.chips()["/operating/speed_rpm"], ExampleValue)
    for expected in history[1:]:
        session.redo()
        assert (current_hash(session), dict(session.chips())) == expected
    assert session.can_redo.value is False


@pytest.mark.req("REQ-F-22")
def test_ut_ses_02_the_history_keeps_only_the_last_fifty_steps(rig):
    """Catches an unbounded history (memory) or one that drops the newest step instead of the oldest."""
    session, _, _ = rig
    session.load_example(D08)
    for step in range(60):
        session.edit("/operating/speed_rpm", 2000.0 + step)
    for _ in range(50):
        session.undo()
    assert session.can_undo.value is False
    assert session.document.draft.values["/operating/speed_rpm"] == 2009.0


@pytest.mark.req("REQ-F-23")
def test_ui15_out_of_range_value_stays_until_apply_then_notice_and_undo(rig):
    """Catches a silent clamp, an Apply without notice, or an Apply that cannot be undone."""
    session, _, _ = rig
    session.load_example(D08)
    session.edit("/rotor/air_gap_mm", 60.0)
    assert session.document.draft.values["/rotor/air_gap_mm"] == 60.0
    typed_hash = current_hash(session)
    found = next(i for i in session.issues.value if i.code == "RANGE_ABOVE_SUPPORTED")
    assert (found.suggestion.pointer, found.suggestion.proposed_value) == ("/rotor/air_gap_mm", 50)
    assert session.notice.value is None
    session.apply_suggestion(found.suggestion)
    assert session.document.draft.values["/rotor/air_gap_mm"] == 50
    assert current_hash(session) != typed_hash
    assert session.notice.value.text == "Changed from 60 to 50: Xcoil clamps to the supported range."
    session.undo()
    assert (session.document.draft.values["/rotor/air_gap_mm"], current_hash(session)) == (60.0, typed_hash)
    assert session.notice.value is None


@pytest.mark.req("REQ-F-21", "REQ-F-38")
def test_ui22_example_chips_turn_user_on_edit_and_return_when_set_back(rig):
    """Catches a chip keyed to keystrokes instead of values, or an example load that marks fields user."""
    session, _, _ = rig
    session.load_example(D08)
    chips = session.chips()
    assert chips and all(isinstance(chip, ExampleValue) for chip in chips.values())
    original = session.document.draft.values["/vias/drill_mm"]
    session.edit("/vias/drill_mm", 0.35)
    assert isinstance(session.chips()["/vias/drill_mm"], UserValue)
    session.edit("/vias/drill_mm", original)
    assert isinstance(session.chips()["/vias/drill_mm"], ExampleValue)


@pytest.mark.req("REQ-F-21")
@pytest.mark.parametrize("from_example", [True, False])
def test_draft_chips_equal_project_provenance_for_a_complete_draft(from_example):
    """Catches the draft chip rules drifting from derive_provenance (the computed state uses the model's)."""
    ref, design = load_example(D08)
    origin = ref if from_example else None
    values = dict(draft_from_design(design).values) | {"/vias/drill_mm": 0.35, "/winding/coil/turns": None}
    document = SessionDocument(draft=DesignDraft(topology=design.topology, values=values), origin=origin)
    expected = project_provenance(ProjectFile(design=parse_draft(document.draft), origin=origin))
    assert draft_chips(document, design if from_example else None) == expected


@pytest.mark.req("REQ-F-31")
def test_ui21_autosave_after_an_edit_recovers_with_the_identical_hash(rig, tmp_path):
    """Catches an autosave that is not written after an edit, or one that loads back as a different design."""
    session, _, _ = rig
    session.load_example(D08)
    session.edit("/operating/speed_rpm", 1234.0)
    autosave = tmp_path / "recovery" / "autosave.embodic.json"
    assert autosave.exists()
    restored = DesignSession(OutcomeViewModel(RecordingSubmitter()))
    assert restored.open_project(autosave) == ()
    assert current_hash(restored) == current_hash(session)
    assert restored.chips() == session.chips()


@pytest.mark.req("REQ-F-31")
def test_ui21_a_draft_autosaves_and_recovers_with_the_same_missing_list(rig, tmp_path):
    """Catches a recovery that loses an incomplete draft (drafts are included, REQ-F-31)."""
    session, _, _ = rig
    session.new_design(TopologyKind.WAVE)
    session.edit("/name", "Draft")
    session.edit("/winding/r_inner_mm", 20.0)
    restored = DesignSession(OutcomeViewModel(RecordingSubmitter()))
    restored.open_project(tmp_path / "recovery" / "autosave.embodic.json")
    assert restored.state.value == session.state.value
    session.discard_autosave()
    assert not (tmp_path / "recovery" / "autosave.embodic.json").exists()


@pytest.mark.req("REQ-F-32")
def test_a_topology_switch_keeps_values_typed_for_the_other_topology(rig):
    """Catches a switch that erases what the user typed, so switching back loses work."""
    session, _, _ = rig
    session.new_design(TopologyKind.SPIRAL)
    session.edit("/winding/coil/coil_count", 12)
    session.set_topology(TopologyKind.WAVE)
    assert session.state.value.draft.topology is TopologyKind.WAVE
    assert "/winding/r_inner_mm" in session.state.value.missing
    session.set_topology(TopologyKind.SPIRAL)
    assert session.document.draft.values["/winding/coil/coil_count"] == 12
    assert "/winding/coil/coil_count" not in session.state.value.missing


@pytest.mark.req("REQ-F-32")
def test_the_stackup_generator_writes_layers_and_pairs_in_one_undoable_edit(rig):
    """Catches a generator that writes the stack-up without its layer pairs (D-024) or as several undo steps."""
    session, _, _ = rig
    session.new_design(TopologyKind.SPIRAL)
    session.set_stackup_input("copper_count", 4)
    session.set_stackup_input("copper_oz", 1.0)
    assert "/stackup/layers" in session.state.value.missing
    session.set_stackup_input("board_thickness_mm", 1.6)
    values = session.document.draft.values
    assert [values[f"/stackup/layers/{i}/name"] for i in range(7)] == ["L1", "D1", "L2", "D2", "L3", "D3", "L4"]
    assert values["/stackup/layers/0/thickness_mm"] == pytest.approx(0.0348)
    assert [
        (values[f"/winding/layers/pairs/{k}/layer_in"], values[f"/winding/layers/pairs/{k}/layer_out"])
        for k in range(2)
    ] == [("L1", "L2"), ("L3", "L4")]
    missing = session.state.value.missing
    assert not any(p.startswith(("/stackup", "/winding/layers")) for p in missing)
    session.undo()
    assert "/stackup/layers" in session.state.value.missing


@pytest.mark.req("REQ-F-27")
def test_a_new_design_does_not_show_the_previous_design_as_its_outdated_drawing(rig, d08_ready):
    """Catches a blank design that inherits another design's drawing and labels it outdated."""
    session, outcome, submitter = rig
    session.load_example(D08)
    outcome.on_finished(submitter.requests[-1].request_id, d08_ready)
    session.new_design(TopologyKind.WAVE)
    assert session.drawn(outcome.state.value) == (None, False)
    session.undo()
    assert isinstance(session.state.value, SessionComputed)
