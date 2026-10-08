"""The results rail by window width, UX-AC-21: third pane from 1280 px, the Key results tab below (design_spec.md 5)."""

import pytest
from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QAbstractButton, QApplication, QLabel, QScrollArea

KEY_RESULTS = "Key results"


def settle():
    """Let the layout of a resized or re-tabbed window settle."""
    for _ in range(5):
        QApplication.processEvents()


def resize(window, size):
    """Resize the shown window and let the layout settle."""
    window.resize(*size)
    settle()


def key_results_tabs(window):
    """Return the indexes of the tabs named Key results."""
    tabs = window.results_tabs
    return [i for i in range(tabs.count()) if tabs.tabText(i) == KEY_RESULTS]


def clipped(window):
    """Return the visible rail widgets squeezed below their minimum size or cut off at the right edge of the view."""
    viewport = window.rail_scroll.viewport()
    found = []
    for widget in window.rail.findChildren(QLabel) + window.rail.findChildren(QAbstractButton):
        if not widget.isVisibleTo(window.rail):
            continue
        hint = widget.minimumSizeHint()
        right = widget.mapTo(viewport, QPoint(widget.width(), 0)).x()
        if widget.width() < hint.width() or widget.height() < hint.height() or right > viewport.width():
            found.append((widget.objectName() or type(widget).__name__, widget.size().toTuple(), hint.toTuple()))
    return found


@pytest.mark.req("REQ-N-15")
def test_ux_ac_21_from_1280_px_the_rail_is_the_third_pane_inside_a_scroll_area(d08_shell):
    """Catches a rail that is a bare pane (its cards then shrink below their size hint) or one that is also a tab."""
    window = d08_shell.window
    resize(window, (1280, 800))
    assert window.splitter.count() == 3
    assert window.splitter.widget(2) is window.rail_scroll
    assert isinstance(window.rail_scroll, QScrollArea) and window.rail_scroll.widget() is window.rail
    assert key_results_tabs(window) == []
    assert window.rail.isVisible()


@pytest.mark.req("REQ-N-15")
@pytest.mark.parametrize("size", [(1279, 800), (960, 540)])
def test_ux_ac_21_below_1280_px_the_rail_is_the_key_results_tab_of_the_results_tabs(d08_shell, size):
    """Catches a third pane that stays below 1280 px (it squeezed values and badges in the 960 x 540 shot)."""
    window = d08_shell.window
    resize(window, size)
    assert window.splitter.count() == 2
    (index,) = key_results_tabs(window)
    assert window.results_tabs.widget(index) is window.rail_scroll
    window.results_tabs.setCurrentIndex(index)
    settle()
    assert window.rail.isVisible()
    assert window.splitter.sizes()[0] == 300


@pytest.mark.req("REQ-N-15")
def test_ux_ac_21_the_rail_moves_with_the_width_and_never_duplicates(d08_shell):
    """Catches a second Key results tab after a resize back and forth, and a rail lost in the move."""
    window = d08_shell.window
    for size in ((960, 540), (1280, 800), (960, 540), (1400, 800), (1100, 700)):
        resize(window, size)
        wide = size[0] >= 1280
        assert len(key_results_tabs(window)) == (0 if wide else 1), size
        assert window.splitter.count() == (3 if wide else 2), size
        assert window.rail_scroll.widget() is window.rail
    assert window.splitter.sizes()[0] == 300
    resize(window, (1280, 800))
    assert window.rail.isVisible()


@pytest.mark.req("REQ-N-15")
@pytest.mark.parametrize("size", [(1280, 800), (960, 540)])
def test_ux_ac_21_no_rail_widget_is_clipped_at_the_smallest_and_the_default_size(d08_shell, size):
    """Catches F10: result values, badges and units cut in half, units read 'mr', a sideways scroll."""
    window = d08_shell.window
    resize(window, size)
    if key_results_tabs(window):
        window.results_tabs.setCurrentIndex(key_results_tabs(window)[0])
        settle()
    assert clipped(window) == []
    assert not window.rail_scroll.horizontalScrollBar().isVisible()
