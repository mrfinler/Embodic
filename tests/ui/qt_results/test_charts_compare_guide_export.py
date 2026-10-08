"""Charts, Compare, the guide and the Export dialog in the window (UI-10, UI-17, UI-29, UI-30, UI-32, UI-34)."""

import dataclasses

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QCheckBox, QMessageBox, QPushButton
from tests.ui.qt_results.conftest import find

from embodic.results.status import Status
from embodic.ui.viewmodels.results import ChartModel, ChartSeries
from embodic.ui.views.charts import ChartWidget


def ink_pixels(icon) -> int:
    """Return the number of painted pixels of a 12 px icon."""
    image = icon.pixmap(12, 12).toImage()
    return sum(1 for x in range(image.width()) for y in range(image.height()) if image.pixelColor(x, y).alpha() > 0)


D08, D14, WAVE, SERPENTINE = "spiral_12c10p_d08", "spiral_12c14p", "wave_16p_example", "serpentine_16p_example"


@pytest.mark.req("REQ-N-25")
def test_ui30_back_emf_chart_has_one_unit_legend_end_labels_data_table_and_badge(make_window, load, qtbot):
    """Catches a chart without legend or direct labels, a table that differs from the plot, or no status badge."""
    window = load(make_window(), D08)
    window.show_results_tab("tab-back-emf")
    panel = window.back_emf_tab.panels[0]
    chart = panel.chart
    assert chart.objectName() == "chart-backemf"
    assert (chart.model.y_unit, chart.y_title()) == ("V", "Back-EMF (V)")
    assert chart.legend_labels == ("Phase A", "Phase B", "Phase C")
    assert chart.end_labels == ("A", "B", "C")
    assert panel.badge.label.property("status") == "not-tested" and panel.eq.text() == "EQ-18"
    qtbot.mouseClick(panel.table_toggle, Qt.MouseButton.LeftButton)
    assert panel.table.isVisible() and panel.table.rowCount() == len(chart.model.xs) == 181
    assert [panel.table.horizontalHeaderItem(c).text() for c in range(4)] == [
        "Electrical angle (°)",
        "Phase A (V)",
        "Phase B (V)",
        "Phase C (V)",
    ]
    chart.setFocus()
    qtbot.keyClick(chart, Qt.Key.Key_Right)
    qtbot.keyClick(chart, Qt.Key.Key_Right)
    assert chart.cursor_index == 1
    assert chart.crosshair_lines()[0] == "Electrical angle 2 °"
    assert all(line.endswith(" V") for line in chart.crosshair_lines()[1:])


@pytest.mark.req("REQ-N-25", "REQ-F-20")
def test_ui30_torque_and_power_are_small_multiples_with_the_estimate_label(make_window, load):
    """Catches torque and power on one axis, or the EQ-20 estimate shown without its label and badge."""
    window = load(make_window(), D08)
    tab = window.torque_speed_tab
    assert tab.pages.currentIndex() == 0 and "DC-link voltage" in tab.empty.text()
    load(window, SERPENTINE)
    torque, power = (panel.chart for panel in tab.panels)
    assert (torque.objectName(), torque.model.y_unit, power.objectName(), power.model.y_unit) == (
        "chart-torque-speed",
        "N·m",
        "chart-power-speed",
        "W",
    )
    assert torque.model.xs == power.model.xs
    assert torque.legend_labels == ()
    for panel in tab.panels:
        assert (panel.badge.label.property("status"), panel.estimate.text()) == ("unresolved", "estimate")


@pytest.mark.req("REQ-T-14")
def test_ui32_a_drawing_not_from_the_engine_carries_the_illustrative_stamp(make_window, load, qtbot):
    """Catches an illustrative drawing shown without its stamp, or engine charts stamped as illustrative."""
    window = load(make_window(), D08)
    assert window.back_emf_tab.panels[0].chart.stamp() is None
    model = ChartModel(
        chart_id="chart-sketch",
        title="Sketch",
        x_label="x",
        x_unit="mm",
        y_label="y",
        y_unit="V",
        xs=(0.0, 1.0, 2.0),
        series=(ChartSeries(label="Sketch", phase=None, ys=(0.0, 1.0, 0.0)),),
        status=Status.UNRESOLVED,
        eq_ids=(),
        assumed_count=0,
        estimate_label=None,
        computed=False,
    )
    sketch = ChartWidget("chart-sketch")
    qtbot.addWidget(sketch)
    sketch.resize(500, 300)
    sketch.show_chart(model, window.tokens, window.appearance.phase_render_mode.value)
    stamped = sketch.grab().toImage()
    assert sketch.stamp() == "Illustrative, not computed"
    sketch.show_chart(
        dataclasses.replace(model, computed=True), window.tokens, window.appearance.phase_render_mode.value
    )
    assert sketch.stamp() is None
    assert sketch.grab().toImage() != stamped


@pytest.mark.req("REQ-F-17", "REQ-L-08")
def test_ui10_ui34_compare_shows_reference_and_current_with_integer_counts_and_glyph_deltas(make_window, load, qtbot):
    """Catches compare values that differ from the Results tab, decimals on counts, or a delta told by colour alone."""
    window = load(make_window(), D08)
    tab = window.compare_tab
    window.show_results_tab("tab-compare")
    assert tab.empty.isVisible() and not tab.table.isVisible()
    qtbot.mouseClick(tab.set_reference, Qt.MouseButton.LeftButton)
    load(window, D14)
    table = tab.table
    rows = {table.item(r, 0).text(): r for r in range(table.rowCount())}
    peak = window.results.row("ke_line_peak_v_s_per_rad")
    assert table.item(rows[peak.label], 2).text() == f"{peak.value_text} {peak.unit_text}"
    for label in ("Copper layers", "Coils", "Vias", "DRC failures"):
        r = rows[label]
        assert table.item(r, 1).text().isdigit() and table.item(r, 2).text().isdigit()
    for r in range(table.rowCount()):
        delta = table.item(r, 3)
        direction = delta.data(Qt.ItemDataRole.UserRole)
        assert (direction == "same") is (ink_pixels(delta.icon()) == 0)
        assert (direction == "up") is delta.text().startswith("+")
        assert (direction == "down") is delta.text().startswith("−")
        assert delta.data(Qt.ItemDataRole.AccessibleTextRole).endswith(
            {"up": "increase", "down": "decrease", "same": "no change"}[direction]
        )
    assert {table.item(r, 3).data(Qt.ItemDataRole.UserRole) for r in range(table.rowCount())} >= {"up", "down"}
    qtbot.mouseClick(tab.set_reference, Qt.MouseButton.LeftButton)
    confirm = window.findChild(QMessageBox, "dlg-compare-confirm")
    assert confirm is not None and confirm.defaultButton() is confirm.button(QMessageBox.StandardButton.Cancel)
    confirm.reject()
    assert tab.vm.reference.value.design.name.endswith("D08 12-coil 10-pole spiral")


@pytest.mark.req("REQ-F-26")
def test_ui17_eq_chip_and_toolstrip_open_the_register_entry_with_the_registry_content(make_window, load, qtbot):
    """Catches an EQ chip that opens the wrong entry, or a reference body that differs from the registry."""
    window = load(make_window(), D08)
    chip = window.results_tab.cards["r-phase"].eq
    qtbot.mouseClick(chip, Qt.MouseButton.LeftButton)
    guide = window.guide
    assert guide is not None and guide.isVisible() and guide.objectName() == "dlg-guide"
    assert guide.current_topic() == "EQ-10"
    registry = window.registry
    for eq_id, entry in registry.equations.items():
        guide.show_topic(eq_id)
        body = guide.body.toPlainText()
        for value in (eq_id, entry.name, entry.formula, entry.gate.value, *entry.tests):
            assert value in body, (eq_id, value)
        for ev_id in entry.sources:
            ev = registry.evidence.get(ev_id)
            assert ev_id in body and (ev is None or ev.location in body), (eq_id, ev_id)
    window.toolstrip.actions_by_id["act-equations"].trigger()
    assert guide.current_topic() == next(iter(registry.equations))
    window.results_tab.cards["ls"].eq.setFocus()
    window.show_help()
    assert guide.current_topic() == "EQ-14"


@pytest.mark.req("REQ-F-33")
def test_ui29_export_with_drc_failures_lists_them_with_focus_on_cancel(make_window, load, qtbot, tmp_path):
    """Catches an export of a failing design without a confirmation, or a confirmation that defaults to export."""
    window = load(make_window(), WAVE)
    window.toolstrip.actions_by_id["act-export-all"].trigger()
    dialog = window.export_dialog
    assert dialog.objectName() == "dlg-export" and dialog.isVisible()
    assert find(dialog, QCheckBox, "export-format-zip").isChecked()
    checklist = [dialog.checklist.item(i).text() for i in range(dialog.checklist.count())]
    assert "DRC: 186 failures. Export asks you to confirm." in checklist
    dialog.folder.setText(str(tmp_path / "wave"))
    qtbot.mouseClick(dialog.run, Qt.MouseButton.LeftButton)
    confirm = dialog.confirm
    assert confirm.objectName() == "dlg-export-confirm" and confirm.isVisible()
    qtbot.waitUntil(lambda: QApplication.focusWidget() is confirm.cancel)
    assert confirm.cancel.isDefault() and not confirm.proceed.isDefault()
    assert confirm.failures.count() == 51 and confirm.failures.item(50).text() == "... and 136 more"
    assert confirm.failures.item(0).text() == "DRC_TRACE_VIA on L1: 0.199965 mm measured, 0.200000 mm required"
    qtbot.mouseClick(confirm.cancel, Qt.MouseButton.LeftButton)
    assert not (tmp_path / "wave").exists() or list((tmp_path / "wave").iterdir()) == []
    qtbot.mouseClick(dialog.run, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(find(dialog.confirm, QPushButton, "btn-export-confirm-run"), Qt.MouseButton.LeftButton)
    written = sorted(p.name for p in (tmp_path / "wave").iterdir())
    assert written and sorted(dialog.result_text.text().splitlines()[1:]) == written


@pytest.mark.req("REQ-F-33")
def test_export_dialog_on_d08_writes_svg_dxf_pdf_readme_zip_and_lists_only_those_files(
    make_window, load, qtbot, tmp_path
):
    """Catches a result list that claims a file the run did not write (screens.md section 11)."""
    window = load(make_window(), D08)
    actions = window.toolstrip.actions_by_id
    assert all(actions[a].isEnabled() for a in ("act-export-svg", "act-export-dxf", "act-export-pdf", "act-export-all"))
    window.toolstrip.actions_by_id["act-export-all"].trigger()
    dialog = window.export_dialog
    screws = find(dialog, QCheckBox, "export-format-dxf-screws")
    assert not screws.isEnabled() and screws.toolTip() == "The board has no screw holes."
    dialog.folder.setText(str(tmp_path / "d08"))
    qtbot.mouseClick(dialog.run, Qt.MouseButton.LeftButton)
    on_disk = sorted(p.name for p in (tmp_path / "d08").iterdir())
    assert sorted(dialog.result_text.text().splitlines()[1:]) == on_disk
    suffixes = sorted(name.split("spiral", 1)[-1] for name in on_disk if name != "README.txt")
    assert suffixes == [".dxf", ".embodic.json", ".svg", ".zip", "_outline.dxf", "_report.pdf"]
    assert "README.txt" in on_disk
    assert dialog.open_folder.isVisible()


@pytest.mark.req("REQ-F-39")
def test_export_commands_wait_for_a_computed_design(make_window):
    """Catches export buttons that are clickable before anything was computed."""
    window = make_window()
    actions = window.toolstrip.actions_by_id
    assert not any(
        actions[a].isEnabled() for a in ("act-export-svg", "act-export-dxf", "act-export-pdf", "act-export-all")
    )
    assert actions["act-drc"].isEnabled() and actions["act-equations"].isEnabled()
