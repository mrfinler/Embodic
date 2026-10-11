"""Inspector widgets U-M4c left unbuilt: segments, pair rotation, pairs notice, screw table, measured mark, phase table.

screens.md sections 2 to 5, interfaces.md section 2.4, D-024, D-031a, UI-19.
"""

import math

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QAccessible
from PySide6.QtWidgets import QComboBox, QInputDialog, QLabel, QLineEdit, QTableWidget, QToolButton
from tests.ui.qt_design.conftest import enter, find
from tests.ui.qt_design.test_editing import no_compute

from embodic.model.vocabulary import TopologyKind
from embodic.ui.viewmodels.session import SessionComputed, layer_pairs
from embodic.ui.views.coil_panel import Segment

D08 = "spiral_12c10p_d08"
WAVE = "wave_16p_example"
NAMED_SEGMENTS = {
    "param-side-style": "/winding/coil/side_style",
    "param-end-style": "/winding/coil/end_style",
    "param-x-inward-sense": "/winding/coil/x_inward_sense",
    "param-connection": "/connection/topology",
}


@pytest.mark.req("REQ-F-32")
def test_segment_fields_are_exclusive_tool_buttons_that_write_their_binding_key(make_shell, qtbot):
    """Catches a segment drawn as a combo box, two buttons checked at once, or a click that writes another pointer."""
    window = make_shell(compute_fn=no_compute).window
    window.session.new_design(TopologyKind.SERPENTINE)
    phases = find(window, "param-phase-count")
    assert isinstance(phases, Segment) and list(phases.buttons) == [1, 2, 3]
    enter(qtbot, window, "param-phase-count", 2)
    assert window.session.document.draft.values["/phases"] == 2
    window.session.new_design(TopologyKind.SPIRAL)
    for widget_id, pointer in NAMED_SEGMENTS.items():
        segment = find(window, widget_id)
        assert isinstance(segment, Segment), widget_id
        assert all(isinstance(b, QToolButton) and b.isCheckable() for b in segment.buttons.values())
        assert segment.group.exclusive()
        for choice in segment.buttons:
            qtbot.mouseClick(segment.buttons[choice], Qt.MouseButton.LeftButton)
            assert window.session.document.draft.values[pointer] == choice
            assert [c for c, b in segment.buttons.items() if b.isChecked()] == [choice]


def rotation_cell(table: QTableWidget, row: int) -> tuple[str, str]:
    """Return the value and the provenance chip a `pair-list` rotation cell shows."""
    value, chip = table.cellWidget(row, 2).findChildren(QLabel)
    return value.text(), chip.text()


@pytest.mark.req("REQ-F-32")
def test_the_layer_list_header_shows_every_column_title_in_full(make_shell):
    """Catches a truncated header such as "Thickness (µ..." (U-M4c screenshot finding), or one past the visible edge."""
    window = make_shell(compute_fn=no_compute).window
    window.session.load_example(D08)
    window.inspector_tabs.setCurrentWidget(window.panels["tab-layers"])
    table = find(window, "layer-list")
    header = table.horizontalHeader()
    shown = [c for c in range(header.count()) if not header.isSectionHidden(c)]
    assert len(shown) == 3
    assert all(header.sectionSize(c) >= header.sectionSizeHint(c) for c in shown)
    thickness = [table.horizontalHeaderItem(c).text().replace("\n", " ") for c in shown].index("Thickness (µm)")
    assert header.sectionViewportPosition(thickness) + header.sectionSize(thickness) <= table.viewport().width()


@pytest.mark.req("REQ-F-23")
def test_pair_rotation_mode_and_the_selected_pair_field_edit_the_pair_rotations(make_shell, qtbot):
    """Catches Alternate on the wrong pairs, Custom editing an unselected pair, or a notice and Undo that disagree."""
    window = make_shell(compute_fn=no_compute).window
    session = window.session
    session.new_design(TopologyKind.SPIRAL)
    enter(qtbot, window, "param-coil-count", "12")
    enter(qtbot, window, "param-copper-weight", "1")
    enter(qtbot, window, "param-board-thickness", "1.6")
    enter(qtbot, window, "param-layer-count", 6)
    notice = find(window, "layer-pairs-notice")
    assert notice.isVisibleTo(window.panels["tab-layers"])
    assert find(window, "layer-pairs-notice-text").text() == (
        "Layer pairs: 3. Pairs 1, 2 and 3 added with the default rotation."
    )
    enter(qtbot, window, "param-rotation-mode", "alternate")
    table: QTableWidget = find(window, "pair-list")
    assert [rotation_cell(table, r)[0] for r in range(table.rowCount())] == ["0", "15", "0"]
    assert not notice.isVisibleTo(window.panels["tab-layers"])
    rotation = find(window, "param-pair-rotation")
    assert not rotation.isVisibleTo(window.panels["tab-layers"])
    enter(qtbot, window, "param-rotation-mode", "custom")
    table.selectRow(2)
    assert rotation.isVisibleTo(window.panels["tab-layers"])
    enter(qtbot, window, "param-pair-rotation", "7.5")
    assert [pair.rotation_rad for pair in layer_pairs(session.document.draft.values)] == [
        0.0,
        math.pi / 12,
        math.radians(7.5),
    ]
    assert find(window, "param-pair-rotation-prov").text() == "user"
    enter(qtbot, window, "param-layer-count", 4)
    assert find(window, "layer-pairs-notice-text").text() == (
        "Layer pairs: 2. Pair 3 removed: the stack-up has 4 copper layers."
    )
    qtbot.mouseClick(find(window, "btn-layer-pairs-undo"), Qt.MouseButton.LeftButton)
    assert len(layer_pairs(session.document.draft.values)) == 3
    assert session.stackup_inputs().copper_count == 6
    assert not notice.isVisibleTo(window.panels["tab-layers"])


@pytest.mark.req("REQ-F-24")
def test_ruling_c_the_screw_table_has_three_columns_and_the_selected_pattern_its_own_fields(make_shell, qtbot):
    """Catches an uneditable row, a UI-filled hole (D-031a), a field writing another pattern, fit back in the table."""
    window = make_shell(compute_fn=no_compute).window
    session = window.session
    session.load_example(WAVE)
    table: QTableWidget = find(window, "screw-table")
    headers = [table.horizontalHeaderItem(c).text().replace("\n", " ") for c in range(table.columnCount())]
    assert headers == ["Size", "Count", "Pitch radius (mm)"]
    patterns = table.rowCount()
    assert patterns >= 1
    hole = find(window, "param-screw-hole-diameter")
    assert hole.text() == "3.4"
    qtbot.mouseClick(find(window, "btn-screw-add"), Qt.MouseButton.LeftButton)
    assert table.rowCount() == patterns + 1 and table.currentRow() == patterns
    assert hole.text() == "" and find(window, "param-screw-hole-diameter-hint").text() == "Required"
    for column, typed in ((0, "M3"), (1, "4"), (2, "30")):
        table.item(patterns, column).setText(typed)
    enter(qtbot, window, "param-screw-fit", "normal")
    enter(qtbot, window, "param-screw-hole-diameter", "3.4")
    enter(qtbot, window, "param-screw-angle-offset", "15")
    values = session.document.draft.values
    base = f"/outline/screws/{patterns}/"
    leaves = ("size", "fit", "count", "pitch_radius_mm", "hole_diameter_mm")
    assert [values[base + leaf] for leaf in leaves] == ["M3", "normal", 4, 30.0, 3.4]
    assert values[base + "angle_offset_rad"] == pytest.approx(math.radians(15))
    assert find(window, "param-screw-angle-offset-prov").text() == "user"
    assert isinstance(session.state.value, SessionComputed)
    qtbot.mouseClick(find(window, "btn-screw-remove"), Qt.MouseButton.LeftButton)
    assert table.rowCount() == patterns
    assert f"{base}size" not in session.document.draft.values
    while table.rowCount():
        qtbot.mouseClick(find(window, "btn-screw-remove"), Qt.MouseButton.LeftButton)
    panel = window.panels["tab-board"]
    assert not any(find(window, name).isVisibleTo(panel) for name in ("param-screw-fit", "param-screw-angle-offset"))


@pytest.mark.req("REQ-F-21")
def test_mark_as_measured_is_offered_on_property_fields_only_and_sets_the_measured_chip(make_shell, monkeypatch):
    """Catches a mark without its source, a property field without the entry, or a design field that offers it."""
    window = make_shell(compute_fn=no_compute).window
    window.session.load_example(D08)
    panel = window.panels["tab-board"]
    editors = {**panel.editors, **window.panels["tab-layers"].editors}
    measurable = {
        w for w, e in editors.items() if e.input.contextMenuPolicy() is Qt.ContextMenuPolicy.CustomContextMenu
    }
    assert measurable == {"param-magnet-br", "param-magnet-mur", "param-h-conv", "param-via-plating"}
    monkeypatch.setattr(QInputDialog, "getText", lambda *args: ("magnet datasheet rev C", True))
    menu = panel.editors["param-magnet-br"].context_menu()
    action = next(a for a in menu.actions() if a.objectName() == "param-magnet-br-mark-measured")
    action.trigger()
    chip = find(window, "param-magnet-br-prov")
    assert (chip.text(), chip.toolTip()) == ("measured", "Measured: magnet datasheet rev C")


@pytest.mark.req("REQ-F-28")
def test_phase_balance_status_and_manual_assignment_follow_the_winding_plan(make_shell, qtbot, wait_computed):
    """Catches a stale balance status, a manual list not from the computed pattern, or a table editable in auto."""
    window = make_shell().window
    window.session.load_example(D08)
    wait_computed(window)
    status = find(window, "phase-balance-status")
    assert status.text() == "Balanced."
    table: QTableWidget = find(window, "phase-table")
    pattern = "".join(
        table.item(r, 1).text() if table.item(r, 2).text() == "1" else table.item(r, 1).text().lower()
        for r in range(table.rowCount())
    )
    assert pattern == find(window, "phase-pattern-string").text()
    assert not table.item(0, 1).flags() & Qt.ItemFlag.ItemIsEditable
    enter(qtbot, window, "param-phase-assign-mode", "manual")
    assert window.session.document.draft.values["/winding/assignment/0/phase"] == table.item(0, 1).text()
    assert table.item(0, 1).flags() & Qt.ItemFlag.ItemIsEditable
    table.item(0, 2).setText("-1" if table.item(0, 2).text() == "1" else "1")
    wait_computed(window)
    assert status.text() == "Not balanced: each phase needs the same number of coils."
    enter(qtbot, window, "param-phase-assign-mode", "auto")
    wait_computed(window)
    assert window.session.document.draft.values["/winding/assignment"] is None
    assert status.text() == "Balanced."
    enter(qtbot, window, "param-coil-count", "11")
    wait_computed(window)
    assert status.text() == "Not balanced: choose 9, 12 or 15 coils."


def _announced(widget) -> str:
    iface = QAccessible.queryAccessibleInterface(widget)
    return f"{iface.text(QAccessible.Text.Name)} | {iface.text(QAccessible.Text.Description)}"


@pytest.mark.req("REQ-N-16")
def test_def_uv4_05_06_combo_boxes_segment_buttons_and_pattern_fields_announce_their_field_label(
    make_shell, wait_computed
):
    """WCAG 3.3.2, 4.1.2 (AX-06 proxy). Catches an input announced without its field label.

    On e693046 a combo box or segment button announced only its value ("Circle", "Delta") and the screw pattern fields
    announced nothing.
    """
    window = make_shell().window
    window.session.load_example(D08)
    wait_computed(window)
    captions = {label.buddy(): label.text() for label in window.findChildren(QLabel) if label.buddy() is not None}
    inputs = []
    for widget in window.findChildren(QComboBox) + window.findChildren(QToolButton) + window.findChildren(QLineEdit):
        owner = widget.parentWidget() if isinstance(widget.parentWidget(), Segment) else widget
        if owner.objectName().startswith("param-") and (owner is not widget or not isinstance(widget, QToolButton)):
            inputs.append((widget, owner))
    kinds = {type(widget).__name__ for widget, _ in inputs}
    assert {"QComboBox", "QToolButton", "QLineEdit"} <= kinds, kinds
    assert {"param-screw-angle-offset", "param-screw-hole-diameter"} <= {owner.objectName() for _, owner in inputs}
    unnamed = [
        (owner.objectName(), widget.text() if isinstance(widget, QToolButton) else "", _announced(widget))
        for widget, owner in inputs
        if captions.get(owner, "") == "" or captions[owner] not in _announced(widget)
    ]
    assert unnamed == []
