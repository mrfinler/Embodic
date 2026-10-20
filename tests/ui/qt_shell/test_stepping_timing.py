"""UI-46, UI-48, UI-53 and UI-57: the 300 ms wait of a step, on the wall clock (REQ-N-12, REQ-N-02).

test_stepping.py holds the preview timer wherever the contract is "not yet" or "once", so that no wall-clock margin
decides it. These cases leave the timer alone, so a step that starts the preview when it must not, or never, shows.
UI-46 and UI-48 depend on the wall clock (a 300 ms interval within 50 ms; five keys 50 ms apart), so they carry the
`latency` marker and run in the latency process (D-074). UI-53 and UI-57 assert that nothing starts after a 600 ms wait,
which a loaded machine cannot turn into a failure, so they stay in the main process.
"""

import pytest
from PySide6.QtCore import Qt

from embodic.ui.viewmodels.session import SessionEmpty

from .test_stepping import committed_r_inner, show_field, type_over
from .typing_support import DEBOUNCE_MS, TOLERANCE_MS, TimedCompute, focus_field

pytestmark = pytest.mark.req("REQ-N-12", "REQ-N-02")

SETTLE_MS = 600


@pytest.mark.latency
def test_ui46_s1_a_step_previews_once_300_ms_after_the_key(open_example, qtbot):
    """UI-46, UX-AC-22. Catches a step that previews at once, late or twice, scrolls the inspector or commits."""
    timed = TimedCompute()
    _, window = open_example(timed=timed)
    session, coil = window.session, window.panels["tab-coil"]
    field = focus_field(qtbot, window)
    scroll = coil.verticalScrollBar()
    assert scroll.maximum() > 0, "precondition: the Coil tab scrolls, so a stray Up or Down would show"
    before = scroll.value()
    t0 = timed.now()
    qtbot.keyClick(field, Qt.Key.Key_Up)
    assert field.text() == "11.97"
    assert scroll.value() == before
    qtbot.wait(max(0, DEBOUNCE_MS - TOLERANCE_MS - (timed.now() - t0)))
    assert timed.starts == [], "no preview before the wait is over"
    qtbot.wait(max(0, SETTLE_MS - (timed.now() - t0)))
    assert timed.r_inner() == [11.97]
    assert abs(timed.starts[0][0] - t0 - DEBOUNCE_MS) <= TOLERANCE_MS, timed.starts[0][0] - t0
    assert committed_r_inner(window) == 11.47
    session.undo()
    assert isinstance(session.state.value, SessionEmpty), "a step wrote no undo entry"


@pytest.mark.latency
def test_ui48_s3_five_steps_at_50_ms_preview_once_with_the_last_value(open_example, qtbot):
    """UI-48. Catches a compute per step, or a preview of an earlier step."""
    timed = TimedCompute()
    _, window = open_example(timed=timed)
    field = focus_field(qtbot, window)
    for _ in range(5):
        qtbot.keyClick(field, Qt.Key.Key_Up)
        qtbot.wait(50)
    qtbot.wait(SETTLE_MS)
    assert field.text() == "13.97"
    assert timed.r_inner() == [13.97]


def test_ui53_s8_a_step_on_text_that_is_no_number_computes_nothing(open_example, qtbot):
    """UI-53. Catches a step on "abc" or on an empty field that starts the 300 ms preview."""
    timed = TimedCompute()
    _, window = open_example(timed=timed)
    field = focus_field(qtbot, window)
    type_over(qtbot, field, "abc")
    qtbot.keyClick(field, Qt.Key.Key_Up)
    assert field.text() == "abc"
    field.selectAll()
    qtbot.keyClick(field, Qt.Key.Key_Delete)
    qtbot.keyClick(field, Qt.Key.Key_Up)
    assert field.text() == ""
    qtbot.wait(SETTLE_MS)
    assert timed.starts == []


def test_ui57_s12_a_stack_up_step_computes_only_after_return(open_example, qtbot):
    """UI-57. Catches a stack-up input that previews after the 300 ms wait, which exists only for design inputs."""
    timed = TimedCompute()
    _, window = open_example(timed=timed)
    session = window.session
    field = show_field(qtbot, window, "param-board-thickness")
    before = session.stackup_inputs().board_thickness_mm
    assert before is not None
    qtbot.keyClick(field, Qt.Key.Key_Up)
    qtbot.wait(SETTLE_MS)
    assert timed.starts == []
    qtbot.keyClick(field, Qt.Key.Key_Return)
    qtbot.waitUntil(lambda: session.stackup_inputs().board_thickness_mm != before, timeout=10_000)
    assert session.stackup_inputs().board_thickness_mm == pytest.approx(before + 0.1, abs=1e-9)
