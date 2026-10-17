"""REQ-N-12 (V3-01 gap N-12): Tab visits the stops of a design in visual order, region after region in F6 order.

The walk starts at the toolstrip tabs and presses Tab until focus returns to them, so a table that keeps Tab inside it
(design_spec.md section 10: "Tab leaves it") fails the walk. A stop's position is its top-left
in window coordinates with every scroll area counted at its top: Qt scrolls a focused widget into view, so the raw
position of a card in a scroll area would move with the walk. Stops outside the named F6 regions (the rail's scroll
area and the layer toggles) are listed with their region "-" and left out of the region sequence.
"""

from functools import partial
from itertools import pairwise

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QAbstractScrollArea, QApplication, QWidget

from embodic.model.vocabulary import TopologyKind
from embodic.ui.viewmodels.outcome import OutcomeReady

from .conftest import D08
from .test_centre_split import WAVE, resize
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
    """Press Tab from the focused first stop until focus returns; return (region, name, x, y) per stop.

    Events run before each stop is read, as a user's event loop runs between key presses: a result that just arrived
    has its cards placed by a posted layout request, and reading before it ran found them a few pixels apart.
    """
    first = QApplication.focusWidget()
    stops = []
    for _ in range(MAX_STOPS):
        QApplication.processEvents()
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
def walk_of(make_shell, qtbot):
    """Return walk(*examples, tab=, sizes=): open the examples in turn, resize, then walk from the toolstrip."""

    def walk(*examples: str, tab: str = "tab-coil", sizes: tuple[tuple[int, int], ...] = ()):
        window = make_shell().window
        for example in examples:
            window.session.load_example(example)
            qtbot.waitUntil(partial(opened, window, example), timeout=60_000)
        for size in sizes:
            resize(window, size)
        window.inspector_tabs.setCurrentWidget(window.panels[tab])
        window.activateWindow()
        qtbot.waitUntil(window.isActiveWindow)
        window.findChild(QWidget, "toolstrip-tabs").setFocus()
        return tab_walk(qtbot, window)

    return walk


def opened(window, example: str) -> bool:
    """Return True when the drawn result is the one of ``example`` (its topology is the example id's first word)."""
    state = window.outcome.state.value
    topology = TopologyKind(example.split("_")[0])
    return isinstance(state, OutcomeReady) and state.outcome.design.topology is topology


@pytest.fixture
def walk(walk_of):
    """Return the Tab walk of the D08 window."""
    return walk_of(D08)


def test_n12_inside_each_region_tab_moves_down_then_right(walk):
    """Catches a Tab order that jumps against the visual order inside a region (a stop above or left of the last)."""
    assert backward_steps(walk) == []


def test_n12_regions_follow_the_f6_order(walk):
    """Catches Tab leaving a region and coming back to it later, or entering regions in another order than F6.

    DEF-U-M7c-01: main e68d5ff reached the inspector fields only after the rail, because Qt chains a widget at the
    window's end when it joins the window and the shell attaches a topology's form when a design opens.
    """
    assert region_sequence(walk) == F6_ORDER


@pytest.mark.parametrize("tab", ["tab-phases", "tab-layers", "tab-board"])
def test_n12_every_inspector_tab_is_walked_in_visual_and_f6_order(walk_of, tab):
    """Catches a table that keeps Tab (phase-table, layer-list on e68d5ff) and a row built after the rows below it.

    On e68d5ff the Board tab went from param-min-ring at its bottom back up to the bore choice, which the tab adds
    after its outline rows are built.
    """
    stops = walk_of(D08, tab=tab)
    assert (backward_steps(stops), region_sequence(stops)) == ([], F6_ORDER)


def test_n12_a_second_design_of_another_topology_keeps_the_order(walk_of):
    """Catches an order fixed once for the first form only: opening a wave after a spiral swaps every inspector form."""
    stops = walk_of(D08, WAVE)
    assert (backward_steps(stops), region_sequence(stops)) == ([], F6_ORDER)


def test_n12_the_drawing_keeps_its_place_after_a_compact_height(walk_of):
    """Catches the canvas page chained at the window's end when it leaves the compact-height "Drawing" tab."""
    stops = walk_of(D08, sizes=((1280, 560), (1280, 800)))
    assert (backward_steps(stops), region_sequence(stops)) == ([], F6_ORDER)


def test_n12_the_layer_toggles_come_right_before_the_canvas_they_sit_above(walk):
    """Catches the toggles a design adds to the shown window chained at its end, after the rail (e68d5ff)."""
    names = [name for _, name, *_ in walk]
    canvas = names.index("fig-canvas")
    assert names[canvas - 2 : canvas] == ["layer-L1", "layer-L2"]


def test_n12_at_compact_height_tab_reaches_the_drawing_tab_bar_then_its_page_then_the_rail(make_shell, qtbot):
    """Catches the "Drawing" page walked before the results tab bar above it (e68d5ff at 960 x 540 and 1280 x 560).

    Qt keeps a widget's place in the chain when it moves inside one window, so the page kept its place above the bar.
    """
    window = make_shell().window
    window.session.load_example(D08)
    qtbot.waitUntil(partial(opened, window, D08), timeout=60_000)
    resize(window, (1280, 560))
    window.results_tabs.setCurrentWidget(window.canvas_page)
    window.activateWindow()
    qtbot.waitUntil(window.isActiveWindow)
    window.findChild(QWidget, "toolstrip-tabs").setFocus()
    stops = [(region, name) for region, name, *_ in tab_walk(qtbot, window)]
    expected = [("results-tabs", "qt_tabwidget_tabbar"), ("results-tabs", "layer-L1"), ("fig-canvas", "fig-canvas")]
    expected.append(("-", "rail-scroll"))
    assert [stop for stop in stops if stop in expected] == expected
