"""REQ-T-01: every result card shows an EQ chip or a kind tag, and the keyboard opens its details."""

import dataclasses

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QFrame, QLabel
from tests.ui.qt_e2e.support import press, tab_until
from tests.ui.qt_results.conftest import find

from embodic.api import compute

D08 = "spiral_12c10p_d08"
KIND_TAGS = {"input", "derived", "count"}  # ui/strings/results.py results.eq.tag-*


def with_kind_tags(design, provenance, **kwargs):
    """Compute D08, then strip the EQ-IDs of three results so that each shows a kind tag instead."""
    outcome = compute(design, provenance, **kwargs)
    analysis = outcome.analysis
    tagged = {
        "skin_depth_mm": dataclasses.replace(analysis.skin_depth_mm, eq_ids=(), kind_tag="derived"),
        "mass_copper_g": dataclasses.replace(analysis.mass_copper_g, eq_ids=(), kind_tag="input"),
        "winding_factor_1": dataclasses.replace(analysis.winding_factor_1, eq_ids=(), kind_tag="count"),
    }
    return dataclasses.replace(outcome, analysis=dataclasses.replace(analysis, **tagged))


@pytest.mark.req("REQ-T-01")
def test_t01_all_30_cards_show_an_eq_chip_and_its_chain(make_window, load):
    """Catches a card with no EQ link: the chip shows the first EQ-ID of the row and its tip lists the whole chain."""
    window = load(make_window(), D08)
    cards = window.results_tab.cards
    assert len(cards) == 30
    for key, card in cards.items():
        chip = find(card, QLabel, f"res-{key}-eq")
        assert chip.isVisible(), key
        assert card.row.eq_ids, key
        assert chip.text() == card.row.eq_ids[0], key
        assert chip.toolTip() == ", ".join(card.row.eq_ids), key
        assert chip.focusPolicy() == Qt.FocusPolicy.StrongFocus, key


@pytest.mark.req("REQ-T-01")
def test_t01_a_result_without_an_eq_id_shows_a_kind_tag_and_never_nothing(make_window, load):
    """Catches a card whose chip is empty when the row has no EQ-ID, and a tag that takes keyboard focus like a link."""
    window = load(make_window(with_kind_tags), D08)
    cards = window.results_tab.cards
    tagged = {key: card for key, card in cards.items() if not card.row.eq_ids}
    assert sorted(card.eq.text() for card in tagged.values()) == ["count", "derived", "input"]
    for key, card in cards.items():
        assert card.eq.isVisible() and card.eq.text().strip(), key
        assert (card.eq.text() in KIND_TAGS) == (key in tagged), key
    assert all(card.eq.focusPolicy() == Qt.FocusPolicy.NoFocus for card in tagged.values())


@pytest.mark.req("REQ-T-01")
def test_t01_tab_then_space_opens_the_details_of_each_of_the_30_cards(make_window, load, qtbot):
    """Catches a card whose 'How was this computed' panel the keyboard cannot open, or one that opens another card's."""
    window = load(make_window(), D08)
    window.show_results_tab("tab-results")
    cards = window.results_tab.cards
    window.results_tab.setFocus()
    assert QApplication.focusWidget() is not None
    for key in cards:
        panel = find(window, QFrame, f"res-{key}-how")
        assert not panel.isVisible(), key
        tab_until(qtbot, lambda w, name=f"res-{key}-how-toggle": w.objectName() == name)
        press(qtbot, Qt.Key.Key_Space)
        assert panel.isVisible(), key
    assert all(find(window, QFrame, f"res-{key}-how").isVisible() for key in cards)
