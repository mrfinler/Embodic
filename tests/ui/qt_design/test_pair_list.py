"""`pair-list` of the Layers tab: one row per layer pair, Delete, the series-group menu, the rotation chip (ruling c).

screens.md section 4 as U-S4e revised it; m4_review_2.md ruling c.
"""

import math

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from tests.ui.qt_design.conftest import enter, find
from tests.ui.qt_design.test_editing import no_compute
from tests.ui.qt_design.test_inspector_widgets import rotation_cell

from embodic.model.vocabulary import TopologyKind
from embodic.ui.viewmodels.session import layer_pairs, series_groups

pytestmark = pytest.mark.req("REQ-F-23", "REQ-N-15")


def _spiral_with_pairs(make_shell, qtbot, copper):
    window = make_shell(compute_fn=no_compute).window
    window.session.new_design(TopologyKind.SPIRAL)
    for name, value in (("param-coil-count", "12"), ("param-copper-weight", "1"), ("param-board-thickness", "1.6")):
        enter(qtbot, window, name, value)
    enter(qtbot, window, "param-layer-count", copper)
    window.inspector_tabs.setCurrentWidget(window.panels["tab-layers"])
    QApplication.processEvents()
    return window, find(window, "pair-list")


def test_ruling_c_pair_list_has_one_row_per_pair_with_its_layers_vias_and_rotation_chip(make_shell, qtbot):
    """Catches a pair shown twice (once per copper layer), a row without its vias, or a rotation cell without a chip."""
    _, table = _spiral_with_pairs(make_shell, qtbot, 6)
    assert table.rowCount() == 3
    assert [table.item(r, 1).text() for r in range(3)] == ["L1, L2", "L3, L4", "L5, L6"]
    assert table.item(1, 0).toolTip() == "Pair 2 joins L3 and L4 through vias."
    assert [rotation_cell(table, r) for r in range(3)] == [("0", "default")] * 3


def test_ruling_c_delete_removes_the_selected_pair_and_keeps_its_row_dimmed(make_shell, qtbot):
    """Catches Delete removing a copper layer, a vanished row, or the next pair shifting into the deleted one's slot."""
    window, table = _spiral_with_pairs(make_shell, qtbot, 6)
    layers = find(window, "layer-list").rowCount()
    table.setFocus()
    table.selectRow(1)
    qtbot.keyClick(table, Qt.Key.Key_Delete)
    values = window.session.document.draft.values
    assert [(p.layer_in, p.index) for p in layer_pairs(values)] == [("L1", 0), ("L5", 2)]
    assert sorted(i for group in series_groups(values) for i in group) == [0, 2]
    assert find(window, "layer-list").rowCount() == layers
    assert table.rowCount() == 3 and table.item(1, 2).text() == "No coil" and table.cellWidget(1, 2) is None
    assert not table.item(1, 0).flags() & Qt.ItemFlag.ItemIsEnabled
    assert find(window, "layer-pairs-notice-text").text() == (
        "Pair 2 removed. It returns with default values when the copper layer count changes."
    )
    window.session.undo()
    assert len(layer_pairs(window.session.document.draft.values)) == 3


def test_ruling_c_the_row_menu_puts_the_selected_pair_in_series_with_another(make_shell, qtbot):
    """Catches a series-group menu that writes nothing, writes another pair, or loses a pair from every group."""
    window, table = _spiral_with_pairs(make_shell, qtbot, 6)
    table.selectRow(2)
    panel = window.panels["tab-layers"]
    menu = panel._series_menu(table)
    labels = [action.text() for action in menu.actions() if not action.isSeparator()]
    assert labels == ["In series with pair 1", "In series with pair 2", "In a group of its own"]
    menu.actions()[[a.text() for a in menu.actions()].index("In series with pair 1")].trigger()
    assert series_groups(window.session.document.draft.values) == [[0, 2], [1]]
    menu = panel._series_menu(table)
    menu.actions()[[a.text() for a in menu.actions()].index("In a group of its own")].trigger()
    assert series_groups(window.session.document.draft.values) == [[0], [1], [2]]


def test_ruling_c_the_rotation_field_edits_the_pair_selected_in_the_pair_list(make_shell, qtbot):
    """Catches the custom rotation field writing the first pair whatever row the pair list selects."""
    window, table = _spiral_with_pairs(make_shell, qtbot, 4)
    enter(qtbot, window, "param-rotation-mode", "custom")
    table.selectRow(1)
    enter(qtbot, window, "param-pair-rotation", "10")
    pairs = layer_pairs(window.session.document.draft.values)
    assert [round(p.rotation_rad, 6) for p in pairs] == [0.0, round(math.radians(10), 6)]
    assert rotation_cell(table, 1) == ("10", "user")
