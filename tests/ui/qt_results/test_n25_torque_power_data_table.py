"""REQ-N-25 (V3-01 gap N-25): the torque and power charts offer a data-table alternative and a direct end label.

Torque and Power are the two small multiples of the Torque tab. The back-EMF chart is covered by
`test_charts_compare_guide_export.py` (UI-30).
"""

import pytest
from PySide6.QtCore import Qt

pytestmark = pytest.mark.req("REQ-N-25")

SERPENTINE = "serpentine_16p_example"
UNIT_IN_HEADER = {"chart-torque-speed": "N·m", "chart-power-speed": "W"}


def test_n25_each_torque_and_power_chart_toggles_a_data_table_with_units_and_has_an_end_label(make_window, load, qtbot):
    """Catches a chart with no data-table alternative, a table short of rows or units, or a series with no end label."""
    window = load(make_window(), SERPENTINE)
    window.show_results_tab("tab-torque-speed")
    panels = window.torque_speed_tab.panels
    assert [panel.chart.objectName() for panel in panels] == list(UNIT_IN_HEADER)
    for panel in panels:
        chart, table = panel.chart, panel.table
        assert not table.isVisible()
        qtbot.mouseClick(panel.table_toggle, Qt.MouseButton.LeftButton)
        assert table.isVisible()
        assert table.rowCount() == len(chart.model.xs) > 1
        headers = [table.horizontalHeaderItem(c).text() for c in range(table.columnCount())]
        assert headers[0].endswith("(rpm)")
        assert headers[1].endswith(f"({UNIT_IN_HEADER[chart.objectName()]})")
        assert len(chart.model.series) == 1
        assert chart.end_labels == (chart.model.series[0].label,)
