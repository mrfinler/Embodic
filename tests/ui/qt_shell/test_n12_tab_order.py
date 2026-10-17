"""REQ-N-12 (V3-01 gap N-12): Tab visits the stops of D08 in visual order, region after region in F6 order.

The walk starts at the toolstrip tabs and presses Tab until focus returns to them. A stop's position is its top-left
in window coordinates with every scroll area counted at its top: Qt scrolls a focused widget into view, so the raw
position of a card in a scroll area would move with the walk. Stops outside the named F6 regions (the rail's scroll
area and the layer toggles) are listed with their region "-" and left out of the region sequence.
"""

from itertools import pairwise

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QAbstractScrollArea, QApplication, QWidget

from .test_keyboard_map import press, region_of

pytestmark = pytest.mark.req("REQ-N-12")

F6_ORDER = ["toolstrip", "inspector-tabs", "fig-canvas", "results-tabs", "results-rail"]
ROW_BAND_PX = 4
MAX_STOPS = 400


def position_in_window(window: QWidget, widget: QWidget) -> tuple[int, int]:
    """Return the top-left of ``widget`` in window coordinates as if every scroll area were scrolled to its top."""
    point = widget.mapTo(window, QPoint(0, 0))
    x, y = point.x(), point.y()
    parent = widget.parentWidget()
    while parent is not None:
        if isinstance(parent, QAbstractScrollArea):
            x += parent.horizontalScrollBar().value()
            y += parent.verticalScrollBar().value()
        parent = parent.parentWidget()
    return x, y


def tab_walk(qtbot, window: QWidget) -> list[tuple[str, str, int, int]]:
    """Press Tab from the focused first stop until focus returns; return (region, name, x, y) per stop."""
    first = QApplication.focusWidget()
    stops = []
    for _ in range(MAX_STOPS):
        widget = QApplication.focusWidget()
        x, y = position_in_window(window, widget)
        stops.append((region_of(widget), widget.objectName() or type(widget).__name__, x, y))
        press(qtbot, Qt.Key.Key_Tab)
        if QApplication.focusWidget() is first:
            return stops
    raise AssertionError(f"Tab did not come back to the first stop within {MAX_STOPS} presses")


def is_before(a: tuple[int, int], b: tuple[int, int]) -> bool:
    """Return True when ``b`` lies visually before ``a``: a row above, or the same 4 px row band and further left."""
    (ax, ay), (bx, by) = a, b
    return by < ay - ROW_BAND_PX or (abs(by - ay) <= ROW_BAND_PX and bx < ax)


def backward_steps(stops: list[tuple[str, str, int, int]]) -> list[str]:
    """Return a message per Tab step inside one region that moves against the (y, x) order."""
    return [
        f"{a[0]}: {a[1]} ({a[2]}, {a[3]}) -> {b[1]} ({b[2]}, {b[3]})"
        for a, b in pairwise(stops)
        if a[0] == b[0] and a[0] != "-" and is_before((a[2], a[3]), (b[2], b[3]))
    ]


def region_sequence(stops: list[tuple[str, str, int, int]]) -> list[str]:
    """Return the regions in the order Tab enters them, one entry per run of stops."""
    sequence: list[str] = []
    for region, *_ in stops:
        if region != "-" and (not sequence or sequence[-1] != region):
            sequence.append(region)
    return sequence


@pytest.fixture
def walk(make_shell, wait_ready, qtbot):
    """Return the Tab walk of the D08 window."""
    window = make_shell().window
    window.session.load_example("spiral_12c10p_d08")
    wait_ready(window)
    window.activateWindow()
    qtbot.waitUntil(window.isActiveWindow)
    window.findChild(QWidget, "toolstrip-tabs").setFocus()
    return tab_walk(qtbot, window)


def test_n12_inside_each_region_tab_moves_down_then_right(walk):
    """Catches a Tab order that jumps against the visual order inside a region (a stop above or left of the last)."""
    assert backward_steps(walk) == []


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="DEF-U-M7c-01: on main Tab goes from the inspector tab bar to the canvas, the results and the rail, and "
    "reaches the inspector fields only after the rail; the focus chain is widget creation order and src has no "
    "setTabOrder. REQ-N-12 acceptance: Tab order equals visual order",
)
def test_n12_regions_follow_the_f6_order(walk):
    """Catches Tab leaving a region and coming back to it later, or entering regions in another order than F6."""
    assert region_sequence(walk) == F6_ORDER
