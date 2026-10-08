"""Results tab, rail, DRC tab and Locate in the window (UI-06, UI-07, UI-31, UI-33)."""

import dataclasses

import pytest
from PySide6.QtCore import QPropertyAnimation, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication, QLabel, QPushButton
from tests.ui.qt_results.conftest import find

from embodic.api import compute
from embodic.results.status import Status
from embodic.ui.views.geometry_view import DATA_KIND

D08, WAVE = "spiral_12c10p_d08", "wave_16p_example"


@pytest.mark.req("REQ-T-01", "REQ-T-13", "REQ-F-13")
def test_ui06_results_tab_shows_one_card_per_quantity_with_value_unit_badge_eq_and_tag(make_window, load, qtbot):
    """Catches a card without unit or badge, or values that differ from the result rows."""
    window = load(make_window(), D08)
    tab = window.results_tab
    assert len(tab.cards) == 30
    row = window.results.row("resistance_phase_operating_ohm")
    card = tab.cards["r-phase"]
    assert card.objectName() == "res-card-r-phase"
    parts = {
        name: find(card, QLabel, f"res-r-phase-{name}").text() for name in ("title", "value", "unit", "badge", "eq")
    }
    assert parts == {
        "title": "Phase resistance at operating temperature R_ph",
        "value": "502",
        "unit": "mΩ",
        "badge": "not tested",
        "eq": "EQ-10",
    }
    assert find(card, QLabel, "res-r-phase-badge").property("status") == "not-tested"
    assert card.asm.text() == f"{row.assumed_count} assumptions"
    for key, other in tab.cards.items():
        assert other.unit.text(), key
        assert other.badge.label.property("status") == other.row.status.value.replace(" ", "-"), key


@pytest.mark.req("REQ-T-01")
def test_ui06_the_badge_comes_from_the_data(make_window, load):
    """Catches a hard-coded badge: an engine that reports Ke as verified shows a verified Ke card."""

    def verified_ke(design, provenance, **kwargs):
        outcome = compute(design, provenance, **kwargs)
        t = dataclasses.replace(outcome.analysis.ke_phase_v_s_per_rad, status=Status.VERIFIED)
        return dataclasses.replace(outcome, analysis=dataclasses.replace(outcome.analysis, ke_phase_v_s_per_rad=t))

    window = load(make_window(verified_ke), D08)
    badge = window.results_tab.cards["ke"].badge.label
    assert (badge.text(), badge.property("status")) == ("verified", "verified")
    assert window.results_tab.cards["kt"].badge.label.property("status") == "not-tested"


@pytest.mark.req("REQ-F-11", "REQ-F-20", "REQ-T-05")
def test_ui07_estimate_cards_show_the_estimate_badge_and_their_label(make_window, load):
    """Catches an EQ-14 or EQ-15 card without its label or with a stronger badge."""
    cards = load(make_window(), D08).results_tab.cards
    ls, ipc = cards["ls"], cards["ipc-guideline-current-a"]
    assert (ls.badge.label.property("status"), ls.badge.label.text(), ls.estimate.text()) == (
        "unresolved",
        "estimate",
        "estimate",
    )
    assert ls.badge.label.accessibleName() == "Status: unresolved"
    assert (ipc.badge.label.property("status"), ipc.estimate.text()) == ("unresolved", "guideline (unverified)")


@pytest.mark.req("REQ-T-16", "REQ-T-13")
def test_ui33_ke_disclosure_in_the_window_shows_e_edge_at_least_assumption_and_the_cap(make_window, load, qtbot):
    """Catches a Ke disclosure that hides the EC-05 lower bound, its assumption status or the 10 % cap."""
    window = load(make_window(), D08)
    card = window.results_tab.cards["ke"]
    qtbot.mouseClick(card.how_toggle, Qt.MouseButton.LeftButton)
    shown = card.disclosure_text()
    for words in ("e_edge", "at least", "assumption", "10 %"):
        assert words in shown, words
    qtbot.mouseClick(find(card, QPushButton, "res-ke-copy"), Qt.MouseButton.LeftButton)
    assert QGuiApplication.clipboard().text() == window.results.copy_trace("ke_phase_v_s_per_rad")


@pytest.mark.req("REQ-N-26")
@pytest.mark.parametrize("animations", [False, True])
def test_ui31_disclosure_slides_only_when_the_os_allows_animation(make_window, load, qtbot, animations):
    """Catches a transition that runs while the OS animation setting is off, or a reveal that never opens."""
    window = load(make_window(), D08)
    card = window.results_tab.cards["r-phase"]
    before = QApplication.isEffectEnabled(Qt.UIEffect.UI_General)
    QApplication.setEffectEnabled(Qt.UIEffect.UI_General, animations)
    try:
        qtbot.mouseClick(card.how_toggle, Qt.MouseButton.LeftButton)
        running = [
            a for a in card.how.findChildren(QPropertyAnimation) if a.state() == QPropertyAnimation.State.Running
        ]
        assert bool(running) is animations
        assert card.how.isVisibleTo(card)
        if not animations:
            assert card.how.maximumHeight() == 16_777_215
    finally:
        QApplication.setEffectEnabled(Qt.UIEffect.UI_General, before)


@pytest.mark.req("REQ-F-33")
def test_drc_tab_lists_the_wave_failures_and_locate_marks_the_first_on_the_canvas(make_window, load, qtbot):
    """Catches a DRC tab that disagrees with the status bar, or a Locate that does not reach the canvas."""
    window = load(make_window(), WAVE)
    tab = window.drc_tab
    assert tab.summary.text() == "DRC: 186 failures, 0 warnings"
    assert tab.summary.property("state") == "fail"
    assert tab.model.rowCount() == 186
    assert "186 failures" in window.status["st-drc"].text()
    window.status["st-drc"].linkActivated.emit("tab-drc")
    assert window.results_tabs.currentWidget() is tab
    assert not tab.locate.isEnabled()
    tab.table.selectRow(0)
    qtbot.mouseClick(tab.locate, Qt.MouseButton.LeftButton)
    markers = [i for i in window.canvas.scene().items() if i.data(DATA_KIND) == "drc-marker"]
    x, y = window.outcome.state.value.outcome.drc[0].violations[0].at_mm
    assert [(m.pos().x(), m.pos().y()) for m in markers] == [(x, -y)]
    copper = [i for i in window.canvas.scene().items() if i.data(DATA_KIND) == "copper"]
    assert copper and {round(i.opacity(), 2) for i in copper} == {0.35}
    assert window.canvas.zoom_factor() > 5


@pytest.mark.req("REQ-F-33")
def test_rail_keeps_the_summary_names_and_links_a_failing_drc_to_its_tab(make_window, load, qtbot):
    """Catches a rail that lost the U-M4b objectNames or hides why the design shows 'Problems found'."""
    window = load(make_window(), WAVE)
    rail = window.rail
    assert find(rail, QLabel, "sum-drc-value").text() == "186 failures"
    assert find(rail, QLabel, "sum-ke-value").text() == window.results.row("ke_line_peak_v_s_per_rad").value_text
    assert find(rail, QLabel, "sum-r-phase-unit").text() == "Ω"
    link = find(rail, QPushButton, "btn-rail-drc")
    window.show_results_tab("tab-results")
    qtbot.mouseClick(link, Qt.MouseButton.LeftButton)
    assert window.results_tabs.currentWidget() is window.drc_tab
