"""REQ-F-20 (DEF-US17-03): the torque-speed message names the place of the DC-link voltage field as the user sees it."""

import pytest
from PySide6.QtWidgets import QGroupBox, QWidget
from tests.ui.qt_results.conftest import find

D08 = "spiral_12c10p_d08"  # leaves the DC-link voltage empty, so the Torque-speed tab shows its message

pytestmark = pytest.mark.req("REQ-F-20")


def test_the_torque_speed_message_names_the_tab_and_group_that_hold_the_dc_link_field(make_window, load):
    """Catches a message that names a place the field is not in.

    The message said "Board and rotor, operating point" while the tab reads "Board" and the field sits in the group
    "Drive".
    """
    window = load(make_window(), D08)
    window.show_results_tab("tab-torque-speed")
    message = window.torque_speed_tab.empty.text()
    field = find(window, QWidget, "param-dc-link")
    panel = next(panel for panel in window.panels.values() if panel.isAncestorOf(field))
    tab = window.inspector_tabs.tabText(window.inspector_tabs.indexOf(panel))
    group = next(box for box in window.findChildren(QGroupBox) if box.isAncestorOf(field)).title()
    assert (tab, group) == ("Board", "Drive")
    assert message == "The torque-speed estimate needs a DC-link voltage (Board tab, Drive group)."
