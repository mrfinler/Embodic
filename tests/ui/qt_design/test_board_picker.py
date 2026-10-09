"""Board picker of a one-board-per-phase design (screens.md section 4.1, UX board picker)."""

import dataclasses

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QLabel
from tests.ui.qt_design.conftest import find

from embodic.api import compute
from embodic.io.examples import load_example
from embodic.io.project import project_from_example, project_provenance
from embodic.ui.theme import load_theme
from embodic.ui.toolstrip import ToolstripTab
from embodic.ui.viewmodels.appearance import PhaseRenderMode
from embodic.ui.viewmodels.results import DrcRow, drc_table
from embodic.ui.views.geometry_view import DATA_KIND, DATA_PHASE
from embodic.ui.views.toolstrip_bar import board_swatch

SERPENTINE = "serpentine_16p_example"
ITEMS = ["All boards", "Board A", "Board B", "Board C"]


def settle():
    """Let the layout and the redraw of a changed window settle."""
    for _ in range(5):
        QApplication.processEvents()


def copper_phases(window) -> list[str]:
    """Return the phase letter of every copper item on the canvas scene."""
    return [item.data(DATA_PHASE) for item in window.canvas.scene().items() if item.data(DATA_KIND) == "copper"]


@pytest.fixture(scope="module")
def wave_outcome():
    """Return the computed wave example, whose DRC report has real violations to copy."""
    project = project_from_example(load_example("wave_16p_example"))
    return compute(project.design, project_provenance(project))


@pytest.fixture
def per_phase(make_shell, wait_computed):
    """Return a window that shows the serpentine example as one board per phase (two copper layers per board)."""
    window = make_shell().window
    window.session.load_example(SERPENTINE)
    wait_computed(window)
    window.session.edit("/winding/stack_mode", "one_board_per_phase")
    window.session.set_stackup_input("copper_count", 2)
    wait_computed(window)
    window.toolstrip.show_tab(ToolstripTab.VIEW)
    settle()
    return window


@pytest.mark.req("REQ-F-13")
@pytest.mark.parametrize("example", ["spiral_12c10p_d08", "wave_16p_example", SERPENTINE])
def test_the_picker_is_hidden_for_spiral_wave_and_single_board_serpentine(make_shell, wait_computed, example):
    """Catches a picker offered where it never applies (screens.md 4.1, P3)."""
    window = make_shell().window
    window.session.load_example(example)
    wait_computed(window)
    window.toolstrip.show_tab(ToolstripTab.VIEW)
    settle()
    assert not window.toolstrip.board_picker.isVisible()
    assert len(copper_phases(window)) > 0


@pytest.mark.req("REQ-F-13")
def test_the_serpentine_example_as_one_board_per_phase_offers_all_boards_and_one_item_per_phase(per_phase):
    """Catches a missing picker, a wrong item list, or items that do not name their letter in text."""
    window = per_phase
    picker = find(window, "board-picker")
    assert isinstance(picker, QComboBox) and picker.isVisible()
    assert [picker.itemText(i) for i in range(picker.count())] == ITEMS
    assert picker.currentIndex() == 0
    assert picker.itemIcon(0).isNull() and not any(picker.itemIcon(i).isNull() for i in (1, 2, 3))
    caption = [label.text() for label in window.toolstrip.board_section.findChildren(QLabel)]
    assert caption == ["Board"]
    assert sorted(set(copper_phases(window))) == ["A", "B", "C"]


@pytest.mark.req("REQ-F-13")
def test_selecting_board_b_leaves_only_board_b_copper_in_the_scene(per_phase):
    """Catches a picker that redraws every board, drops copper of the chosen board or shows another phase."""
    window = per_phase
    every = copper_phases(window)
    picker = find(window, "board-picker")
    picker.setCurrentIndex(2)
    settle()
    assert set(copper_phases(window)) == {"B"}
    assert len(copper_phases(window)) == every.count("B")
    picker.setCurrentIndex(0)
    settle()
    assert sorted(copper_phases(window)) == sorted(every)


@pytest.mark.req("REQ-F-13", "REQ-N-12")
def test_page_down_and_page_up_on_the_canvas_step_the_picker(per_phase, qtbot):
    """Catches Page Down that does nothing on the canvas, wraps around, or runs past Board C."""
    window = per_phase
    picker = find(window, "board-picker")
    window.canvas.setFocus()
    seen = []
    for key in (Qt.Key.Key_PageDown,) * 4 + (Qt.Key.Key_PageUp,) * 4:
        qtbot.keyClick(window.canvas, key)
        seen.append(picker.currentText())
    assert seen == ["Board A", "Board B", "Board C", "Board C", "Board B", "Board A", "All boards", "All boards"]


@pytest.mark.req("REQ-F-13", "REQ-N-12")
def test_bracket_keys_solo_a_layer_of_the_selected_board(per_phase, qtbot):
    """Catches a solo that leaves the other layer's copper of the selected board on the canvas."""
    window = per_phase
    find(window, "board-picker").setCurrentIndex(2)
    window.canvas.setFocus()
    qtbot.keyClick(window.canvas, Qt.Key.Key_BracketRight)
    settle()
    boxes = {name: box.isChecked() for name, box in window.layer_boxes.items() if isinstance(box, QCheckBox)}
    assert boxes == {"L1": True, "L2": False}
    layers = {item.data(0) for item in window.canvas.scene().items() if item.data(DATA_KIND) == "copper"}
    assert layers == {"L1"}
    assert set(copper_phases(window)) == {"B"}
    qtbot.keyClick(window.canvas, Qt.Key.Key_BracketRight)
    qtbot.keyClick(window.canvas, Qt.Key.Key_BracketRight)
    settle()
    assert all(box.isChecked() for box in window.layer_boxes.values())


@pytest.mark.req("REQ-F-13", "REQ-N-28")
@pytest.mark.parametrize(
    ("mode", "edge"), [(PhaseRenderMode.COLOUR, "colour_hex"), (PhaseRenderMode.GREYSCALE_HATCH, "grey_hex")]
)
def test_the_swatch_repeats_the_letter_in_the_phase_colour_and_turns_grey_in_greyscale(qtbot, mode, edge):
    """Catches a swatch that stays red, blue and green in greyscale mode, or one without the phase letter."""
    tokens = load_theme("light")
    letters = {}
    for style in tokens.phases:
        image = board_swatch(style.phase, tokens, mode).pixmap(16, 16).toImage()
        assert image.pixelColor(0, 8) == QColor(getattr(style, edge))
        letters[style.phase] = [image.pixelColor(x, y).lightness() for x in range(4, 12) for y in range(4, 12)]
        assert min(letters[style.phase]) < 100  # ink of the letter on the light surface
    assert len({tuple(v) for v in letters.values()}) == 3


@pytest.mark.req("REQ-F-13", "REQ-N-28")
def test_the_picker_swatches_follow_the_render_mode(per_phase):
    """Catches a picker that keeps its coloured swatches after the greyscale toggle."""
    window = per_phase
    picker = find(window, "board-picker")
    style = window.tokens.phase_style(next(iter(window.tokens.phases)).phase)
    edge = lambda: picker.itemIcon(1).pixmap(16, 16).toImage().pixelColor(0, 8)  # noqa: E731
    assert edge() == QColor(style.colour_hex)
    window.appearance.toggle_phase_render_mode()
    settle()
    assert edge() == QColor(style.grey_hex)


@pytest.mark.req("REQ-F-33")
def test_locate_sets_the_picker_to_the_failures_board(per_phase):
    """Catches a Locate that zooms on a board the canvas does not draw."""
    window = per_phase
    row = DrcRow(
        number=1,
        board=3,
        severity="error",
        rule_code="DRC_TRACE_VIA",
        message="",
        measured_text="",
        required_text="",
        layer_text="L1",
        at_mm=(0.0, 0.0),
        board_text="C",
    )
    window.drc_tab.locate_requested.emit(row)
    settle()
    assert find(window, "board-picker").currentText() == "Board C"
    assert set(copper_phases(window)) == {"C"}


@pytest.mark.req("REQ-F-33")
def test_the_drc_table_lists_every_board_whatever_the_picker_shows(per_phase, wave_outcome):
    """Catches a table that follows the picker and so hides a failure, or a Board column that is not there."""
    window = per_phase
    clean = dataclasses.replace(wave_outcome.drc[0], passed=True, violations=(), violation_count=0)
    two = dataclasses.replace(wave_outcome.drc[0], violations=wave_outcome.drc[0].violations[:2], violation_count=2)
    outcome = dataclasses.replace(window.session.state.value.outcome, drc=(clean, two, clean))
    find(window, "board-picker").setCurrentIndex(1)
    settle()
    window.drc_tab.show_table(drc_table(outcome), window.tokens)
    tab = window.drc_tab
    headers = [tab.model.headerData(c, Qt.Orientation.Horizontal) for c in range(tab.model.columnCount())]
    column = headers.index("Board")
    assert not tab.table.isColumnHidden(column)
    assert [tab.model.item(r, column).text() for r in range(tab.model.rowCount())] == ["B", "B"]
    assert tab.summary.text() == "DRC: 2 failures, 0 warnings. Board A pass, Board B 2 failures, Board C pass."


@pytest.mark.req("REQ-F-33")
def test_the_drc_table_of_one_board_hides_its_board_column(make_shell, wait_computed):
    """Catches a Board column of empty cells on a design that has one board."""
    window = make_shell().window
    window.session.load_example("spiral_12c10p_d08")
    wait_computed(window)
    tab = window.drc_tab
    headers = [tab.model.headerData(c, Qt.Orientation.Horizontal) for c in range(tab.model.columnCount())]
    assert tab.table.isColumnHidden(headers.index("Board"))
