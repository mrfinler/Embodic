"""The scene the worker builds of an outcome: its marks once per board (DEF-U-M8n-02). Qt-free."""

import sys

import pytest

import embodic.geometry.marks
from embodic.api import compute
from embodic.geometry.labels import label_anchors
from embodic.geometry.marks import coil_marks
from embodic.io.examples import load_example
from embodic.io.project import project_from_example, project_provenance
from embodic.ui.viewmodels.outcome import ready_state

EXAMPLES = ("spiral_12c10p_d08", "wave_16p_example", "serpentine_16p_example")


@pytest.fixture(scope="module", params=EXAMPLES)
def outcome(request):
    """Return the computed outcome of one packaged example."""
    project = project_from_example(load_example(request.param))
    return compute(project.design, project_provenance(project))


@pytest.mark.req("REQ-N-02")
def test_def_u_m8n_02_the_scene_computes_the_coil_marks_of_each_board_once(outcome, monkeypatch):
    """Catches label_anchors searching the spiral eyes again after the scene did (D08: 300 + 307 of 627 ms).

    Every module name bound to coil_marks is counted, so the count holds however a module imports it.
    """
    original = embodic.geometry.marks.coil_marks
    calls = []

    def counted(layout):
        calls.append(id(layout))
        return original(layout)

    for module in list(sys.modules.values()):
        if getattr(module, "__name__", "").startswith("embodic") and getattr(module, "coil_marks", None) is original:
            monkeypatch.setattr(module, "coil_marks", counted)
    scene = ready_state(outcome).scene
    assert calls == [id(board) for board in scene.boards]


@pytest.mark.req("REQ-N-23")
def test_def_u_m8n_02_the_scene_keeps_the_labels_and_marks_the_exports_draw(outcome):
    """Catches a scene whose labels or eyes drift from the ones label_anchors and coil_marks give the exporters."""
    scene = ready_state(outcome).scene
    for board, marks in zip(scene.boards, scene.marks, strict=True):
        assert marks.anchors == label_anchors(board)
        assert marks.coils == tuple(coil_marks(board))
