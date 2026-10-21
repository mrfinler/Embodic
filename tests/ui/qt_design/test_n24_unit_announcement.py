"""REQ-N-24 (V3-01 gap N-24): every inspector input with a unit shows it and announces it in its accessible description.

Expected values come from the field table (`embodic.model.fields.field_specs`): the unit of each row, shown with
`Unit.display()`. Angles are the one documented exception: the model holds radians and the form shows degrees
(`embodic.units` module docstring; `coil_panel.unit_text`). The tables `layer-list`, `screw-table` and `pair-list` hold
a unit in a column header. A header is not a cell's accessible description (DEF-UV13-02, D-061c), so each cell of such a
column carries the unit in its own description, and the second test below reads it.
"""

import re

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QAccessible
from PySide6.QtWidgets import QAbstractItemView, QLabel, QLineEdit, QTableWidget
from tests.ui.qt_design.conftest import enter, find

from embodic.model.fields import FIELD_BY_KEY, field_specs
from embodic.model.vocabulary import TopologyKind
from embodic.units import Unit

pytestmark = pytest.mark.req("REQ-N-24")

EXAMPLE = {
    TopologyKind.SPIRAL: "spiral_12c10p_d08",
    TopologyKind.SERPENTINE: "serpentine_16p_example",
    TopologyKind.WAVE: "wave_16p_example",
}
SHOWN_IN_DEGREES = {Unit.RAD: "°"}
TABLE_WIDGETS = {"layer-list", "screw-table"}


def no_compute(design, provenance, **kwargs):
    """Stand in for the engine: the unit labels do not depend on a result."""
    return None


def unit_symbol(unit: Unit) -> str:
    """Return the symbol the form must show for a field-table unit."""
    return SHOWN_IN_DEGREES.get(unit, unit.display())


@pytest.mark.parametrize("topology", list(EXAMPLE), ids=lambda t: t.value)
def test_n24_every_unit_input_shows_and_announces_its_unit(make_shell, topology):
    """Catches an input whose unit is shown but not announced, or announced but not shown, or shown wrongly."""
    window = make_shell(compute_fn=no_compute).window
    window.session.load_example(EXAMPLE[topology])
    checked, problems, tables = 0, [], set()
    for spec in field_specs(topology):
        if spec.unit is None or spec.widget_id is None or not unit_symbol(spec.unit):
            continue
        widget = find(window, spec.widget_id)
        if isinstance(widget, QAbstractItemView):
            tables.add(spec.widget_id)
            continue
        shown = find(window, f"{spec.widget_id}-unit")
        assert isinstance(shown, QLabel)
        symbol, announced = unit_symbol(spec.unit), widget.accessibleDescription()
        checked += 1
        if shown.text() != symbol:
            problems.append(f"{spec.widget_id}: unit label {shown.text()!r}, expected {symbol!r}")
        if symbol not in announced:
            problems.append(f"{spec.widget_id}: accessible description {announced!r} lacks {symbol!r}")
    assert checked > 25
    assert tables <= TABLE_WIDGETS
    assert problems == []


def header_units(table: QTableWidget) -> dict[int, str]:
    """Return {column: unit} for each column whose header ends in a unit in brackets, as the user reads it."""
    units = {}
    for column in range(table.columnCount()):
        header = table.horizontalHeaderItem(column)
        found = re.search(r"\(([^()]+)\)\s*$", header.text()) if header is not None else None
        if found:
            units[column] = found.group(1)
    return units


def cell_description(table: QTableWidget, row: int, column: int) -> str:
    """Return the accessible description of a cell, empty when it has none."""
    item = table.item(row, column)
    assert item is not None, (row, column)
    return str(item.data(Qt.ItemDataRole.AccessibleDescriptionRole) or "")


def test_n24_every_unit_cell_of_the_inspector_tables_announces_its_unit(make_shell):
    """Catches a table cell whose unit is only in the column header (DEF-UV13-02), or a unit column added unannounced.

    The units expected come from the field table, except the stack-up thickness: the model holds mm and the list shows
    micrometres, which the next test ties to the cell text. A screw row is added because both examples have none, and
    a new row is the one whose cells the user types into.
    """
    window = make_shell(compute_fn=no_compute).window
    window.session.load_example(EXAMPLE[TopologyKind.SPIRAL])
    window.session.add_screw_pattern()
    pitch_radius = FIELD_BY_KEY["/outline/screws/*/pitch_radius_mm"].unit
    rotation = FIELD_BY_KEY["/winding/layers/pairs/*/rotation_rad"].unit
    assert pitch_radius is not None and rotation is not None
    expected = {
        "layer-list": {Unit.UM.display()},
        "screw-table": {unit_symbol(pitch_radius)},
        "pair-list": {unit_symbol(rotation)},
    }
    problems = []
    for name, symbols in expected.items():
        table = find(window, name)
        assert isinstance(table, QTableWidget)
        columns = header_units(table)
        assert set(columns.values()) == symbols, f"{name}: unit columns {columns}, expected units {symbols}"
        assert table.rowCount() > 0, name
        for row in range(table.rowCount()):
            for column, symbol in columns.items():
                described = cell_description(table, row, column)
                if symbol not in described:
                    problems.append(f"{name} ({row}, {column}): accessible description {described!r} lacks {symbol!r}")
    assert problems == []


def test_n24_the_layer_list_thickness_cells_are_in_micrometres_as_their_description_says(make_shell):
    """Catches a description that says µm over a cell that shows millimetres, or the reverse."""
    window = make_shell(compute_fn=no_compute).window
    window.session.load_example(EXAMPLE[TopologyKind.SPIRAL])
    table = find(window, "layer-list")
    assert isinstance(table, QTableWidget)
    (column,) = header_units(table)
    values = window.session.document.draft.values
    assert table.rowCount() > 0
    for row in range(table.rowCount()):
        millimetres = values[f"/stackup/layers/{row}/thickness_mm"]
        assert float(table.item(row, column).text()) == pytest.approx(millimetres * 1000, rel=1e-3)


STACKUP_GENERATOR_INPUTS = {"param-copper-weight": ("1", "oz"), "param-board-thickness": ("1.6", "mm")}


@pytest.mark.parametrize("name", list(STACKUP_GENERATOR_INPUTS))
def test_n24_the_stackup_generator_inputs_show_their_unit_beside_a_value_and_announce_it(make_shell, qtbot, name):
    """Catches DEF-US17-01: a unit that shows only as placeholder text, which a typed value hides, and is not announced.

    The copper weight and the board thickness are helper inputs without a field-table row. They follow the same rule
    as every field row (screens.md, table conventions): the unit sits in a `<id>-unit` label beside the input and is
    part of the accessible description, which the assistive technology reads through `QAccessible`.
    """
    value, symbol = STACKUP_GENERATOR_INPUTS[name]
    window = make_shell(compute_fn=no_compute).window
    window.session.new_design(TopologyKind.SPIRAL)
    window.inspector_tabs.setCurrentWidget(window.panels["tab-board"])
    enter(qtbot, window, name, value)
    edit = find(window, name)
    assert isinstance(edit, QLineEdit)
    assert edit.text() == value
    unit = find(window, f"{name}-unit")
    assert isinstance(unit, QLabel)
    assert unit.text() == symbol
    assert unit.isVisibleTo(window)
    right_of_input = edit.mapToGlobal(QPoint(edit.width(), 0)).x()
    assert unit.mapToGlobal(QPoint(0, 0)).x() >= right_of_input, "the unit is not beside the input"
    assert (
        edit.mapToGlobal(QPoint(0, 0)).y()
        <= unit.mapToGlobal(QPoint(0, unit.height() // 2)).y()
        <= (edit.mapToGlobal(QPoint(0, edit.height())).y())
    ), "the unit is not on the input's line"
    interface = QAccessible.queryAccessibleInterface(edit)
    assert symbol in edit.accessibleDescription()
    assert symbol in interface.text(QAccessible.Text.Description)


def test_n24_the_stackup_generator_inputs_line_up_with_the_field_rows_of_their_group(make_shell, settle):
    """Catches a unit label outside the section's unit column, which leaves its input wider than the rows' (ruling g 2).

    The unit column of a section has the width of its widest unit, so the input edges of one group box align
    (screens.md, layout of a field row). The widest unit is a stand-in so that the test does not depend on the width
    of "oz" against "mm" in the font of the machine.
    """
    window = make_shell(compute_fn=no_compute).window
    window.session.new_design(TopologyKind.SPIRAL)
    panel = window.panels["tab-board"]
    window.inspector_tabs.setCurrentWidget(panel)
    group = find(window, "tab-board-group-manufacturing")
    find(window, "param-copper-weight-unit").setText("W/(m²·K)")
    panel.refresh()
    settle()
    labels = [label.objectName() for label in group.findChildren(QLabel)]
    names = [name.removesuffix("-unit") for name in labels if name.endswith("-unit")]
    assert {"param-copper-weight", "param-board-thickness", "param-min-trace"} <= set(names)
    right_edges = {n: find(window, n).mapTo(group, QPoint(find(window, n).width(), 0)).x() for n in names}
    assert len(set(right_edges.values())) == 1, right_edges
