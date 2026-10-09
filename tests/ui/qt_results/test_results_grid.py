"""Results tab card grid: no card is cut off at the right edge of its scroll area (U-M4d-fix DEF-1)."""

import pytest
from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication, QScrollArea

from embodic.ui.views.results_view import CARD_MIN_WIDTH_PX

D08 = "spiral_12c10p_d08"


def settle():
    """Let the layout of a resized or re-tabbed window settle."""
    for _ in range(5):
        QApplication.processEvents()


@pytest.mark.req("REQ-N-15")
@pytest.mark.parametrize("size", [(1280, 800), (1600, 900)])
def test_no_result_card_is_cut_off_at_the_right_of_the_grid(make_window, load, size):
    """Catches a column count taken from the tab width: the scroll bar then clips the last column."""
    window = load(make_window(), D08)
    window.resize(*size)
    window.show_results_tab("tab-results")
    settle()
    tab = window.results_tab
    scroll = tab.findChild(QScrollArea, "results-scroll")
    viewport = scroll.viewport()
    assert scroll.verticalScrollBar().isVisible()
    assert not scroll.horizontalScrollBar().isVisible()
    right_edges = {
        key: card.mapTo(viewport, QPoint(card.width(), 0)).x() for key, card in tab.cards.items() if card.isVisible()
    }
    assert len(right_edges) == 30
    assert {k: x for k, x in right_edges.items() if x > viewport.width()} == {}
    assert all(card.width() >= CARD_MIN_WIDTH_PX for card in tab.cards.values())
    columns = len(set(right_edges.values()))
    card = max(CARD_MIN_WIDTH_PX, *(c.minimumSizeHint().width() for c in tab.cards.values()))
    assert (columns + 1) * card + columns * 8 > viewport.width(), "one more column would fit"
