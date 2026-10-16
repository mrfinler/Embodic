"""F13-1 (V3-01 union ruling): each view of REQ-F-13 is on screen after at most two user interactions."""

from dataclasses import dataclass

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QListWidget, QPushButton, QTabBar, QTabWidget, QToolButton

from embodic.ui.toolstrip import ToolstripTab

from .support import find

EXAMPLE_ID = "spiral_12c10p_d08"
MAX_INTERACTIONS = 2


@dataclass(frozen=True)
class ClickTab:
    """A mouse click on the tab of a QTabWidget or a toolstrip tab bar."""

    bar: str  # objectName of the QTabWidget, or "toolstrip-tabs" for the toolstrip's own tab bar
    target: str  # objectName of the page the tab shows, or the ToolstripTab value


@dataclass(frozen=True)
class ClickButton:
    """A mouse click on a toolstrip button."""

    button: str


Interaction = ClickTab | ClickButton

# View -> (route from the start view with the D08 example loaded, objectName of the widget that must be visible).
ROUTES: dict[str, tuple[tuple[Interaction, ...], str]] = {
    "2-D geometry": ((), "fig-canvas"),
    "phase assignment": ((ClickTab("inspector-tabs", "tab-phases"),), "tab-phases"),
    "layer configuration": ((ClickTab("inspector-tabs", "tab-layers"),), "tab-layers"),
    "results": ((ClickTab("results-tabs", "tab-results"),), "tab-results"),
    "checks": ((ClickTab("toolstrip-tabs", ToolstripTab.ANALYSIS.value), ClickButton("act-drc")), "tab-drc"),
}


def _open_d08_from_gallery(qtbot, window, wait_drawn) -> None:
    qtbot.mouseClick(find(window, "btn-empty-examples", QPushButton), Qt.MouseButton.LeftButton)
    gallery = find(window, "dlg-examples", QDialog)
    examples = find(gallery, "examples-list", QListWidget)
    row = next(r for r in range(examples.count()) if examples.item(r).data(Qt.ItemDataRole.UserRole) == EXAMPLE_ID)
    examples.setCurrentRow(row)
    qtbot.mouseClick(find(gallery, "btn-load-example", QPushButton), Qt.MouseButton.LeftButton)
    wait_drawn(window)


def _interact(qtbot, window, step: Interaction) -> None:
    if isinstance(step, ClickButton):
        qtbot.mouseClick(find(window, step.button, QToolButton), Qt.MouseButton.LeftButton)
    elif step.bar == "toolstrip-tabs":
        bar = find(window, step.bar, QTabBar)
        index = list(ToolstripTab).index(ToolstripTab(step.target))
        qtbot.mouseClick(bar, Qt.MouseButton.LeftButton, pos=bar.tabRect(index).center())
    else:
        tabs = find(window, step.bar, QTabWidget)
        index = tabs.indexOf(find(window, step.target))
        assert index >= 0, step.target
        qtbot.mouseClick(tabs.tabBar(), Qt.MouseButton.LeftButton, pos=tabs.tabBar().tabRect(index).center())


@pytest.mark.req("REQ-F-13")
@pytest.mark.parametrize("view", list(ROUTES))
def test_f13_1_every_view_is_visible_after_at_most_two_interactions(view, window, wait_drawn, qtbot):
    """Catches a view moved into a dialog or a second-level menu: its widget is not visible within two interactions."""
    _open_d08_from_gallery(qtbot, window, wait_drawn)
    route, target = ROUTES[view]
    assert len(route) <= MAX_INTERACTIONS, view
    for step in route:
        _interact(qtbot, window, step)
    assert find(window, target).isVisible(), (view, target)


@pytest.mark.req("REQ-F-13")
def test_f13_1_the_phase_and_layer_pages_are_hidden_until_their_tab_is_clicked(window, wait_drawn, qtbot):
    """Catches a route check that passes without any interaction: tab-phases and tab-layers start hidden."""
    _open_d08_from_gallery(qtbot, window, wait_drawn)
    assert not find(window, "tab-phases").isVisible()
    assert not find(window, "tab-layers").isVisible()
