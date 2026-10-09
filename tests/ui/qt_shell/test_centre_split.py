"""The vertical split of the centre pane and the compact-height Drawing tab, UX-AC-21 (U-S4e ruling b)."""

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from embodic.ui.app import CANVAS_SHARE_KEY

D08 = "spiral_12c10p_d08"
pytestmark = pytest.mark.req("REQ-N-15")


def resize(window, size):
    """Resize the shown window and let the layout settle."""
    window.resize(*size)
    for _ in range(5):
        QApplication.processEvents()


def test_ruling_b_at_1280_x_800_the_canvas_gets_60_percent_and_a_results_tab_never_moves_the_split(d08_shell):
    """Catches the 124 px canvas of main fd190c1: the results cards' size hint took 524 of 648 px."""
    window = d08_shell.window
    resize(window, (1280, 800))
    canvas, results = window.centre_split.sizes()
    assert abs(canvas - 0.6 * (canvas + results)) <= 1 and canvas >= 240 and results >= 180
    for tab in ("tab-results", "tab-drc", "tab-back-emf", "tab-compare"):
        window.show_results_tab(tab)
        QApplication.processEvents()
        assert window.centre_split.sizes() == [canvas, results], tab


@pytest.mark.parametrize("size", [(960, 540), (1280, 600)])
def test_ruling_b_under_620_px_the_canvas_is_the_first_results_tab_drawing(make_shell, wait_ready, size):
    """Catches the 112 px canvas at 960 x 540: under 620 px tall the drawing must become a tab of its own."""
    window = make_shell().window
    resize(window, size)
    window.session.load_example(D08)
    wait_ready(window)
    tabs = window.results_tabs
    assert window.centre_split.count() == 1 and tabs.indexOf(window.canvas_page) == 0
    assert tabs.tabText(0) == "Drawing" and tabs.currentWidget() is window.canvas_page
    assert window.canvas.height() >= 300, window.canvas.height()
    if size[0] < 1280:
        assert tabs.tabText(1) == "Key results"
    window.show_results_tab("tab-drc")
    window.session.load_example(D08)
    assert tabs.currentWidget() is window.canvas_page, "Drawing is the current tab after a load"


def test_ruling_b_the_canvas_returns_to_the_split_when_the_window_grows_again(d08_shell):
    """Catches a Drawing tab that stays after the window is tall enough, or a canvas lost in the move."""
    window = d08_shell.window
    for size in ((960, 540), (1280, 800), (960, 540), (1100, 700)):
        resize(window, size)
        compact = size[1] < 620
        assert (window.results_tabs.indexOf(window.canvas_page) == 0) is compact, size
        assert window.centre_split.count() == (1 if compact else 2), size
    assert window.centre_split.widget(0) is window.canvas_page and window.canvas.isVisible()


def test_ruling_b_a_dragged_share_is_stored_as_a_fraction_and_restored(make_shell, wait_ready):
    """Catches a drag that is forgotten at restart, or one stored in pixels that breaks at another window size."""
    shell = make_shell()
    window = shell.window
    window.session.load_example(D08)
    wait_ready(window)
    resize(window, (1280, 800))
    total = sum(window.centre_split.sizes())
    window.centre_split.setSizes([300, total - 300])
    window.centre_split.splitterMoved.emit(300, 1)
    stored = float(QSettings(str(shell.settings_path), QSettings.Format.IniFormat).value(CANVAS_SHARE_KEY))
    assert stored == pytest.approx(300 / total)
    window.close()
    again = make_shell(settings_path=shell.settings_path).window
    again.session.load_example(D08)
    wait_ready(again)
    resize(again, (1400, 900))
    canvas, results = again.centre_split.sizes()
    assert canvas / (canvas + results) == pytest.approx(stored, abs=0.01)
