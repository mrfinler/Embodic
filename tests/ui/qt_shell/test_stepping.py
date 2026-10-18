"""DEF-US11-04, DEF-US12-02: Up, Down and Shift step the numeric fields (rows S-1 to S-12 of fix_wave_f2.md (b)).

Field `param-r-inner` of D08 holds 11.47 mm. Steps are uncommitted edits: they preview after the 300 ms wait and commit
on Enter. The tests hold the preview timer (typing_support.hold_preview_timer) wherever the contract is "not yet" or
"once", so that no wall-clock margin decides them.
"""

import math

import pytest
from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QComboBox, QLabel, QLineEdit, QPushButton, QTableWidget

from embodic.model.schema import ValueType
from embodic.ui.viewmodels.session import SessionComputed, SessionEmpty
from embodic.ui.views.coil_panel import FieldEditor

from .conftest import D08
from .test_centre_split import resize
from .typing_support import (
    TimedCompute,
    drawn_r_inner,
    expire,
    focus_field,
    hold_preview_timer,
    r_inner_of,
)

SERPENTINE = "serpentine_16p_example"
WAVE = "wave_16p_example"
SHIFT = Qt.KeyboardModifier.ShiftModifier

pytestmark = pytest.mark.req("REQ-N-02", "REQ-N-12")


def show_field(qtbot, window, name):
    """Show the inspector tab of a field row and focus its line edit with the text selected."""
    panel = next(p for p in window.panels.values() if name in p.editors or name in p.helpers)
    window.inspector_tabs.setCurrentWidget(panel)
    QApplication.processEvents()
    return focus_field(qtbot, window, name)


def type_over(qtbot, field, text):
    """Replace the text of a focused field by typing, as a user does."""
    field.selectAll()
    qtbot.keyClicks(field, text)


def committed_r_inner(window):
    """Return r_inner of the session's committed design."""
    return r_inner_of(window.session.state.value)


def test_s1_up_adds_one_step_and_previews_after_the_wait_without_scrolling_or_committing(open_example, qtbot):
    """S-1, DEF-US12-02. Catches a step that scrolls the inspector, computes at once or writes an undo entry.

    It also catches a step written with setText: that emits no textEdited, starts no wait and previews nothing.
    """
    timed = TimedCompute()
    _, window = open_example(timed=timed)
    session, coil = window.session, window.panels["tab-coil"]
    hold = hold_preview_timer(window)
    field = focus_field(qtbot, window)
    scroll = coil.verticalScrollBar()
    assert scroll.maximum() > 0, "precondition: the Coil tab scrolls, so a stray Up or Down would show"
    before = scroll.value()
    qtbot.keyClick(field, Qt.Key.Key_Up)
    assert field.text() == "11.97"
    assert scroll.value() == before
    assert hold.isActive(), "a step starts the 300 ms wait like a keystroke"
    qtbot.wait(100)
    assert timed.starts == []
    expire(hold)
    qtbot.waitUntil(lambda: drawn_r_inner(window) == 11.97, timeout=10_000)
    assert timed.r_inner() == [11.97]
    assert field.text() == "11.97", "the preview result must not put the committed text back over the step"
    assert committed_r_inner(window) == 11.47
    session.undo()
    assert isinstance(session.state.value, SessionEmpty), "a step wrote no undo entry"


def test_s2_shift_down_moves_ten_steps(open_example, qtbot):
    """S-2. Catches Shift that is ignored (one step) or a factor other than ten."""
    _, window = open_example()
    hold_preview_timer(window)
    field = focus_field(qtbot, window)
    qtbot.keyClick(field, Qt.Key.Key_Down, SHIFT)
    assert field.text() == "6.47"
    qtbot.keyClick(field, Qt.Key.Key_Up, SHIFT)
    assert field.text() == "11.47"


def test_s3_a_burst_of_steps_makes_one_preview_of_the_last_value(open_example, qtbot):
    """S-3. Catches a compute per step, or a preview of an earlier step."""
    timed = TimedCompute()
    _, window = open_example(timed=timed)
    hold = hold_preview_timer(window)
    field = focus_field(qtbot, window)
    for _ in range(5):
        qtbot.keyClick(field, Qt.Key.Key_Up)
    assert field.text() == "13.97"
    assert timed.starts == []
    expire(hold)
    qtbot.waitUntil(lambda: bool(timed.starts), timeout=10_000)
    qtbot.wait(100)
    assert timed.r_inner() == [13.97]


def test_s4_up_then_return_commits_the_step_as_one_user_edit(open_example, qtbot):
    """S-4. Catches a step that commits without Return (undo entry early), or Return that adds none."""
    timed = TimedCompute()
    _, window = open_example(timed=timed)
    session = window.session
    hold_preview_timer(window)
    chip = window.findChild(QLabel, "param-r-inner-prov")
    field = focus_field(qtbot, window)
    qtbot.keyClick(field, Qt.Key.Key_Up)
    assert chip.text() == "example"
    qtbot.keyClick(field, Qt.Key.Key_Return)
    qtbot.waitUntil(lambda: isinstance(session.state.value, SessionComputed) and committed_r_inner(window) == 11.97)
    assert chip.text() == "user"
    session.undo()
    assert committed_r_inner(window) == 11.47, "the commit is one undo entry"
    session.undo()
    assert isinstance(session.state.value, SessionEmpty)


def test_s5_esc_drops_every_uncommitted_step_and_keeps_focus(open_example, qtbot):
    """S-5. Catches an Esc that leaves a stepped text, writes an undo entry, or moves focus."""
    timed = TimedCompute()
    _, window = open_example(timed=timed)
    hold_preview_timer(window)
    field = focus_field(qtbot, window)
    qtbot.keyClick(field, Qt.Key.Key_Up)
    qtbot.keyClick(field, Qt.Key.Key_Up)
    assert field.text() == "12.47"
    qtbot.keyClick(field, Qt.Key.Key_Escape)
    assert field.text() == "11.47"
    assert QApplication.focusWidget() is field
    assert timed.starts == []
    window.session.undo()
    assert isinstance(window.session.state.value, SessionEmpty)


def test_s6_a_step_stops_at_zero_and_does_not_leave_a_positive_field(open_example, qtbot):
    """S-6. Catches Down that writes -0.03 mm into a non-negative gap, or 0.3 - 0.5 into a positive radius."""
    _, window = open_example()
    hold_preview_timer(window)
    gap = show_field(qtbot, window, "param-coil-gap")
    type_over(qtbot, gap, "0.02")
    qtbot.keyClick(gap, Qt.Key.Key_Down)
    assert gap.text() == "0"
    qtbot.keyClick(gap, Qt.Key.Key_Down)
    assert gap.text() == "0", "at the bound a further step does nothing"
    radius = show_field(qtbot, window, "param-r-inner")
    type_over(qtbot, radius, "0.3")
    qtbot.keyClick(radius, Qt.Key.Key_Down)
    assert radius.text() == "0.3"


def test_s7_a_step_stops_at_the_range_and_a_value_outside_moves_only_toward_it(open_example, qtbot):
    """S-7. Catches a step below the supported 0.05 mm, a step further out, or no way back from 60 mm."""
    _, window = open_example()
    hold_preview_timer(window)
    air_gap = show_field(qtbot, window, "param-air-gap")
    type_over(qtbot, air_gap, "0.07")
    qtbot.keyClick(air_gap, Qt.Key.Key_Down)
    assert air_gap.text() == "0.05"
    qtbot.keyClick(air_gap, Qt.Key.Key_Down)
    assert air_gap.text() == "0.05"
    type_over(qtbot, air_gap, "60")
    qtbot.keyClick(air_gap, Qt.Key.Key_Up)
    assert air_gap.text() == "60"
    qtbot.keyClick(air_gap, Qt.Key.Key_Down)
    assert air_gap.text() == "50"


def test_s8_text_that_is_no_number_stays_and_computes_nothing(open_example, qtbot):
    """S-8. Catches a step that turns "abc" into a number, or fills an empty optional field."""
    timed = TimedCompute()
    _, window = open_example(timed=timed)
    hold_preview_timer(window)
    field = focus_field(qtbot, window)
    type_over(qtbot, field, "abc")
    qtbot.keyClick(field, Qt.Key.Key_Up)
    assert field.text() == "abc"
    field.selectAll()
    qtbot.keyClick(field, Qt.Key.Key_Delete)
    qtbot.keyClick(field, Qt.Key.Key_Up)
    assert field.text() == ""
    assert timed.starts == []


def test_s9_an_angle_steps_one_degree_and_commits_radians(open_example, qtbot):
    """S-9. Catches an angle step of one radian (57.3 degrees), or a committed value left in degrees."""
    _, window = open_example()
    hold_preview_timer(window)
    field = show_field(qtbot, window, "param-first-coil-angle")
    shown = float(field.text())
    qtbot.keyClick(field, Qt.Key.Key_Up)
    qtbot.keyClick(field, Qt.Key.Key_Return)
    assert float(field.text()) == pytest.approx(shown + 1)
    qtbot.waitUntil(lambda: isinstance(window.session.state.value, SessionComputed), timeout=10_000)
    committed = window.session.state.value.design.winding.coil.first_coil_angle_rad
    assert committed == pytest.approx(math.radians(shown + 1))


def test_s10_an_integer_field_steps_by_its_own_step(open_example, qtbot):
    """S-10. Catches a pole count stepped by 1 (odd poles) or shown as 12.0."""
    _, window = open_example()
    hold_preview_timer(window)
    poles = show_field(qtbot, window, "param-poles")
    assert poles.text() == "10"
    qtbot.keyClick(poles, Qt.Key.Key_Up)
    assert poles.text() == "12"


def test_s11_a_combo_box_and_a_table_keep_their_own_arrow_keys(open_example, qtbot):
    """S-11. Catches a step filter on a combo box or a table: the choice must change once, the table must move rows."""
    timed = TimedCompute()
    _, window = open_example(timed=timed)
    hold_preview_timer(window)
    board = window.panels["tab-board"]
    window.inspector_tabs.setCurrentWidget(board)
    combo = window.findChild(QComboBox, "param-rotor-kind")
    key = Qt.Key.Key_Down if combo.currentIndex() < combo.count() - 1 else Qt.Key.Key_Up
    combo.setFocus(Qt.FocusReason.TabFocusReason)
    qtbot.waitUntil(combo.hasFocus)
    before = combo.currentIndex()
    qtbot.keyClick(combo, key)
    assert combo.currentIndex() == before + (1 if key == Qt.Key.Key_Down else -1)
    qtbot.waitUntil(lambda: len(timed.starts) == 1, timeout=10_000)
    for _ in range(2):
        add = window.findChild(QPushButton, "btn-screw-add")
        board.ensureWidgetVisible(add)
        qtbot.mouseClick(add, Qt.MouseButton.LeftButton)
    table = window.findChild(QTableWidget, "screw-table")
    assert table.rowCount() >= 2
    table.setCurrentCell(0, 0)
    table.setFocus(Qt.FocusReason.TabFocusReason)
    values = dict(window.session.document.draft.values)
    qtbot.keyClick(table, Qt.Key.Key_Down)
    assert table.currentRow() == 1
    assert window.session.document.draft.values == values


@pytest.mark.parametrize(
    ("name", "step", "read"),
    [
        ("param-board-thickness", 0.1, lambda inputs: inputs.board_thickness_mm),
        ("param-copper-weight", 0.5, lambda inputs: inputs.copper_oz),
    ],
)
def test_s12_the_stack_up_inputs_step_and_compute_only_after_return(open_example, qtbot, name, step, read):
    """S-12. Catches a stack-up input that previews (no wait exists for it) or that ignores Up."""
    timed = TimedCompute()
    _, window = open_example(timed=timed)
    session = window.session
    hold_preview_timer(window)
    field = show_field(qtbot, window, name)
    before = read(session.stackup_inputs())
    assert before is not None and float(field.text()) == pytest.approx(before, rel=1e-5)
    qtbot.keyClick(field, Qt.Key.Key_Up)
    assert float(field.text()) == pytest.approx(before + step)
    qtbot.wait(600)
    assert timed.starts == []
    qtbot.keyClick(field, Qt.Key.Key_Return)
    qtbot.waitUntil(lambda: read(session.stackup_inputs()) != before, timeout=10_000)
    assert read(session.stackup_inputs()) == pytest.approx(before + step)


class _KeysThatReachTheBody(QObject):
    """Counts the Up and Down presses a field did not consume: they travel on to the form's body.

    QTest sends the Shift key press before a Shift+Down, so only the arrow keys count.
    """

    def __init__(self):
        super().__init__()
        self.reached = 0

    def eventFilter(self, watched, event):  # noqa: N802 (Qt override)
        if event.type() == QEvent.Type.KeyPress and event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down):
            self.reached += 1
        return False


@pytest.mark.parametrize("example", [D08, WAVE, SERPENTINE])
def test_up_and_down_never_reach_the_inspector_from_a_numeric_field(make_shell, wait_ready, example):
    """DEF-US12-02. Catches Up or Down that a numeric field lets through, which scrolls the inspector by 20 px.

    The text "abc" makes every step a no-op, which is the case that leaked.
    """
    window = make_shell().window
    window.session.load_example(example)
    wait_ready(window)
    resize(window, (960, 540))
    seen = 0
    for panel in window.panels.values():
        window.inspector_tabs.setCurrentWidget(panel)
        QApplication.processEvents()
        spy = _KeysThatReachTheBody()
        panel.widget().installEventFilter(spy)
        for editor in panel.findChildren(FieldEditor):
            numeric = editor.spec.value_type in (ValueType.FLOAT, ValueType.INT)
            if not (numeric and isinstance(editor.input, QLineEdit) and editor.isVisibleTo(panel)):
                continue
            editor.input.setText("abc")
            for key, modifier in ((Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier), (Qt.Key.Key_Down, SHIFT)):
                QTest.keyClick(editor.input, key, modifier)
            assert editor.input.text() == "abc", editor.widget_id
            seen += 1
        assert spy.reached == 0, panel.objectName()
        panel.widget().removeEventFilter(spy)
    assert seen >= 10
