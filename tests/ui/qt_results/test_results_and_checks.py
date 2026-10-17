"""Results tab, rail, DRC tab and Locate in the window (UI-06, UI-07, UI-31, UI-33)."""

import dataclasses
import importlib.util
from collections import Counter
from pathlib import Path

import pytest
from PySide6.QtCore import QPropertyAnimation, QRect, Qt
from PySide6.QtGui import QAccessible, QColor, QGuiApplication
from PySide6.QtWidgets import QApplication, QLabel, QListWidget, QPushButton, QWidget
from tests.ui.qt_results.conftest import find

from embodic.api import compute
from embodic.results.status import Status
from embodic.ui.theme import ThemeName
from embodic.ui.views import results_view
from embodic.ui.views.geometry_view import DATA_KIND
from embodic.ui.views.style import themed_icon

D08, WAVE, SERPENTINE = "spiral_12c10p_d08", "wave_16p_example", "serpentine_16p_example"
DRC_COLUMNS = ("severity", "board", "message", "clearance", "required", "layer")
CELL_MARGIN_PX = 3  # Fusion item text margin on each side (PM_FocusFrameHMargin + 1)

_CONTRAST_TOOL = Path(__file__).resolve().parents[3] / "tools" / "contrast_check.py"  # tools/ is not a package
_spec = importlib.util.spec_from_file_location("contrast_check", _CONTRAST_TOOL)
assert _spec is not None and _spec.loader is not None
contrast_check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(contrast_check)
contrast_ratio = contrast_check.contrast_ratio


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
def test_ui07_estimate_cards_show_the_status_word_and_their_label_beside_it(make_window, load):
    """UI-07, D-042c, DEF-UV4-04. Catches a card without its label, a stronger badge, or "estimate" as the badge."""
    cards = load(make_window(), D08).results_tab.cards
    ls, ipc = cards["ls"], cards["ipc-guideline-current-a"]
    assert (ls.badge.label.property("status"), ls.badge.label.text(), ls.estimate.text()) == (
        "unresolved",
        "unresolved",
        "estimate",
    )
    assert ls.badge.label.accessibleName() == "Status: unresolved"
    assert (ipc.badge.label.property("status"), ipc.badge.label.text(), ipc.estimate.text()) == (
        "unresolved",
        "unresolved",
        "guideline (unverified)",
    )


@pytest.mark.req("REQ-T-16", "REQ-T-13")
def test_ui33_ke_disclosure_in_the_window_shows_e_edge_at_least_assumption_and_the_cap(make_window, load, qtbot):
    """Catches a Ke disclosure that hides the EC-05 lower bound, its assumption status or the 10 % cap."""
    window = load(make_window(), D08)
    card = window.results_tab.cards["ke"]
    qtbot.mouseClick(card.how_toggle, Qt.MouseButton.LeftButton)
    shown = card.disclosure_text()
    for words in ("e_edge", "at least", "assumption", "10\u00a0%"):
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


@pytest.mark.req("REQ-N-26")
def test_ui31_a_disclosure_clicked_once_a_new_result_has_settled_opens(make_window, load, settle, monkeypatch, qtbot):
    """Catches the UI-31 order flake: a wait that returned inside the update made the click land on a 0 px toggle.

    Right after the render that shows a result, every card is squashed to 0 px height until its posted layout runs,
    and QAbstractButton ignores a click outside its rectangle. The click here happens at that moment, after settling.
    """
    seen = []
    refresh = results_view.ResultsTab.refresh

    def click_when_shown(tab):
        refresh(tab)
        card = tab.cards.get("r-phase")
        if card is None or seen:
            return
        seen.append(card.how_toggle.height())
        settle()
        qtbot.mouseClick(card.how_toggle, Qt.MouseButton.LeftButton)
        seen.append(card.how.isVisibleTo(card))

    monkeypatch.setattr(results_view.ResultsTab, "refresh", click_when_shown)
    monkeypatch.setattr(QApplication, "isEffectEnabled", lambda effect: False)
    load(make_window(), D08)
    assert seen == [0, True]


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
@pytest.mark.parametrize("size", [(1280, 800), (960, 540)])
def test_drc_table_shows_the_whole_catalogue_message_in_a_stretched_column(make_window, load, qtbot, size):
    """Catches a message cut to "A trace is ..." or a word cut at the column edge, and a row too short for the text."""
    window = load(make_window(), WAVE)
    window.resize(*size)
    window.show_results_tab("tab-drc")
    for _ in range(5):
        QApplication.processEvents()
    table, message = window.drc_tab.table, DRC_COLUMNS.index("message")
    assert table.textElideMode() == Qt.TextElideMode.ElideNone
    fonts = table.fontMetrics()
    inner = table.columnWidth(message) - 2 * CELL_MARGIN_PX
    assert table.columnWidth(message) >= 200
    for row in range(table.model().rowCount()):
        text = table.model().index(row, message).data()
        needed = fonts.boundingRect(QRect(0, 0, inner, 10_000), Qt.TextFlag.TextWordWrap, text).height()
        assert table.rowHeight(row) >= needed, (size, row, text)
        assert max(fonts.horizontalAdvance(word) for word in text.split()) <= inner, (size, row, text)
    assert table.model().index(0, message).data() in table.model().index(0, message).data(Qt.ItemDataRole.ToolTipRole)


@pytest.mark.req("REQ-F-33", "REQ-N-15")
@pytest.mark.parametrize("size", [(1280, 800), (960, 540)])
def test_ruling_d_drc_table_shows_glyph_message_measured_required_layer_without_sideways_scroll(
    make_window, load, size
):
    """U-S4e ruling d, DEF-2. Catches Measured, Required or Layer pushed off screen by the code and severity columns."""
    window = load(make_window(), WAVE)
    window.resize(*size)
    window.show_results_tab("tab-drc")
    for _ in range(5):
        QApplication.processEvents()
    table = window.drc_tab.table
    model = table.model()
    shown = [c for c in range(model.columnCount()) if not table.isColumnHidden(c)]
    headers = [model.headerData(c, Qt.Orientation.Horizontal).replace("\n", " ") for c in shown]
    assert headers == ["", "Message", "Clearance (mm)", "Required (mm)", "Layer"]
    assert table.columnWidth(0) == 24
    assert table.horizontalHeader().length() <= table.viewport().width(), size
    first = model.index(0, DRC_COLUMNS.index("clearance"))
    assert first.data() == "0.199965" and first.data(Qt.ItemDataRole.FontRole).family() == "JetBrains Mono"
    tooltip = model.index(0, DRC_COLUMNS.index("layer")).data(Qt.ItemDataRole.ToolTipRole)
    assert tooltip.startswith("Error. DRC_") and "Clearance 0.199965\u00a0mm, required" in tooltip
    assert model.index(0, 0).data() == "" and model.index(0, 0).data(Qt.ItemDataRole.DecorationRole) is not None


@pytest.mark.req("REQ-F-33")
def test_rail_heads_with_inputs_and_drc_cards_that_carry_a_glyph_and_a_word(make_window, load, qtbot):
    """Catches 'Design: Problems found' beside 'No issues.', a state shown by colour alone, no way to the DRC tab."""
    window = load(make_window(), WAVE)
    rail = window.rail
    assert find(rail, QLabel, "rail-inputs-title").text() == "Inputs"
    assert find(rail, QLabel, "rail-inputs-value").text() == "No input issues"
    assert find(rail, QLabel, "rail-inputs-value").property("state") == "pass"
    assert find(rail, QLabel, "rail-drc-title").text() == "DRC"
    assert find(rail, QLabel, "rail-drc-value").text() == "186 failures"
    assert find(rail, QLabel, "rail-drc-value").property("state") == "fail"
    pass_glyph = find(rail, QLabel, "rail-inputs-icon").pixmap().toImage()
    fail_glyph = find(rail, QLabel, "rail-drc-icon").pixmap().toImage()
    assert not pass_glyph.isNull() and not fail_glyph.isNull() and pass_glyph != fail_glyph
    assert rail.findChild(QWidget, "sum-ok") is None
    assert "Design" not in [label.text() for label in rail.findChildren(QLabel)]
    assert find(rail, QLabel, "sum-ke-value").text() == window.results.row("ke_line_peak_v_s_per_rad").value_text
    assert find(rail, QLabel, "sum-r-phase-unit").text() == "Ω"
    assert find(rail, QLabel, "sum-r-phase-title").text() == "Phase resistance at operating temperature R_ph"
    link = find(rail, QPushButton, "btn-rail-drc")
    window.show_results_tab("tab-results")
    qtbot.mouseClick(link, Qt.MouseButton.LeftButton)
    assert window.results_tabs.currentWidget() is window.drc_tab


@pytest.mark.req("REQ-F-33")
def test_rail_drc_card_says_passed_for_a_clean_design_and_hides_the_link(make_window, load):
    """Catches a pass card with a failure count or with a link to an empty DRC tab."""
    window = load(make_window(), D08)
    assert find(window.rail, QLabel, "rail-drc-value").text() == "Passed"
    assert find(window.rail, QLabel, "rail-drc-value").property("state") == "pass"
    assert not find(window.rail, QPushButton, "btn-rail-drc").isVisibleTo(window)


@pytest.mark.req("REQ-F-14")
def test_inputs_card_counts_the_issues_of_the_input_issues_list(make_window, load, qtbot):
    """Catches an Inputs card that stays on 'No input issues' after a bad edit, or that disagrees with the list."""
    window = load(make_window(), D08)
    issues = find(window, QListWidget, "issues-list")
    assert find(window, QLabel, "rail-inputs-value").text() == "No input issues"
    assert [label.text() for label in window.rail.findChildren(QLabel) if label.property("class") == "section-title"][
        -1
    ] == "Input issues"
    assert issues.item(0).text() == "No input issues."
    window.session.edit("/winding/coil/r_inner_mm", 50.0)
    qtbot.waitUntil(lambda: not window.session.state.value.computing)
    listed = [issues.item(row) for row in range(issues.count()) if issues.item(row).data(Qt.ItemDataRole.UserRole)]
    assert listed
    value = find(window, QLabel, "rail-inputs-value")
    assert value.text() == (f"{len(listed)} input issues" if len(listed) > 1 else "1 input issue")
    assert value.property("state") == "fail"


@pytest.mark.req("REQ-F-14")
def test_inputs_card_shows_the_serpentine_one_board_per_phase_advice_as_a_note_with_the_warn_glyph(
    make_window, load, qtbot
):
    """U-S4h N4. Catches advice counted as a failing input: "1 input issue" with the fail glyph for a warning."""
    window = load(make_window(), SERPENTINE)
    window.session.edit("/winding/stack_mode", "one_board_per_phase")
    window.session.set_stackup_input("copper_count", 2)
    qtbot.waitUntil(lambda: not window.session.state.value.computing)
    advice = [i for i in window.session.issues.value if i.code == "RANGE_SERPENTINE_INTERCONNECT_BOARDS"]
    assert [i.severity.value for i in advice] == ["warning"], "precondition: the advice is a warning"
    assert all(i.severity.value != "error" for i in window.session.issues.value)
    value = find(window, QLabel, "rail-inputs-value")
    assert value.text() == "1 input note"
    assert value.property("state") == "warn"
    icon = find(window, QLabel, "rail-inputs-icon").pixmap().toImage()
    for stem, same in (("check-warn", True), ("check-fail", False)):
        drawn = themed_icon(stem, window.tokens).pixmap(16, 16).toImage()
        assert (icon == drawn) is same, stem


def overlapping_labels(host: QWidget) -> list[tuple[str, str]]:
    """Return each pair of visible, non-empty labels under ``host`` whose rectangles intersect (in host coordinates)."""
    boxes = [
        (label.text()[:40], QRect(label.mapTo(host, label.rect().topLeft()), label.size()))
        for label in host.findChildren(QLabel)
        if label.isVisibleTo(host) and label.text()
    ]
    return [(a, b) for i, (a, ra) in enumerate(boxes) for b, rb in boxes[i + 1 :] if ra.intersects(rb)]


@pytest.mark.req("REQ-T-13", "REQ-N-15")
@pytest.mark.parametrize("size", [(960, 540), (1280, 800), (1600, 900)])
def test_open_disclosure_lays_out_again_at_each_width_so_no_line_prints_over_another(make_window, load, size):
    """U-S4g S22 (critical). Catches section lines of an earlier layout left on screen over the new ones.

    The S22 lever opens R_ph, then resizes and switches theme with the section open; it pumps events without an event
    loop, so a label waiting for ``deleteLater`` stays visible. The check runs at that same point.
    Under 620 px tall the resize brings the Drawing tab forward, so the Results tab comes back before the check: a
    hidden tab is never laid out, and the check read its stale or default geometry (order dependent).
    """
    QApplication.setEffectEnabled(Qt.UIEffect.UI_General, False)
    window = load(make_window(), D08)
    window.show_results_tab("tab-results")
    card = window.results_tab.cards["r-phase"]
    card.how_toggle.click()
    window.resize(*size)
    window.show_results_tab("tab-results")
    window.appearance.set_theme(ThemeName.DARK)
    for _ in range(10):
        QApplication.processEvents()
    assert "Assumptions" in card.disclosure_text(), "precondition: the section is open"
    assert overlapping_labels(window.results_tab.grid_host) == []


@pytest.mark.req("REQ-N-15")
def test_def_uv4_07_every_result_card_announces_label_value_unit_and_status(make_window, load):
    """WCAG 4.1.2, AX-06 proxy. Catches a card whose accessible name is empty or lacks the number, unit or status."""
    window = load(make_window(), D08)
    names = {}
    for key, card in window.results_tab.cards.items():
        iface = QAccessible.queryAccessibleInterface(card)
        names[key] = iface.text(QAccessible.Text.Name)
        row = card.row
        assert names[key].startswith(f"{row.title}, {row.value_text} "), key
        assert f", {row.status.value}" in names[key][len(row.title) :], key
    assert len(names) == 30
    assert names["r-phase"] == "Phase resistance at operating temperature R_ph, 502 milliohm, not tested"
    value = QAccessible.queryAccessibleInterface(find(window.results_tab, QLabel, "res-r-phase-value"))
    assert value.text(QAccessible.Text.Name) == "502"


def colours_painted(card: QWidget, part: QWidget) -> set[str]:
    """Return the colours (#rrggbb) the card paints inside one of its parts."""
    image = card.grab(QRect(part.mapTo(card, part.rect().topLeft()), part.size())).toImage()
    return {QColor(image.pixel(x, y)).name() for x in range(image.width()) for y in range(image.height())}


def strongest_ink(card: QWidget, part: QWidget, fill: str) -> str:
    """Return the colour the card paints inside a part that contrasts most with the fill: the text at full coverage."""
    return max(colours_painted(card, part), key=lambda found: contrast_ratio(found, fill))


def card_fill(card: QWidget) -> str:
    """Return the colour that covers most of the card."""
    image = card.grab().toImage()
    counts = Counter(QColor(image.pixel(x, y)).name() for x in range(image.width()) for y in range(image.height()))
    return counts.most_common(1)[0][0]


# Light and dark values of text-1, text-3, bg-app and border-control, from design_spec.md appendix A (tokens.json).
STALE_INK = {
    ThemeName.LIGHT: {"text-1": "#141414", "text-3": "#666666", "bg-app": "#f7f7f7", "border-control": "#858585"},
    ThemeName.DARK: {"text-1": "#f2f2f2", "text-3": "#a0a0a0", "bg-app": "#0f0f0f", "border-control": "#7d7d7d"},
}


@pytest.mark.req("REQ-F-14")
@pytest.mark.parametrize("theme", [ThemeName.LIGHT, ThemeName.DARK])
def test_ux_ac_15_stale_cards_dim_value_unit_and_badge_by_token_and_keep_4_5_to_1(make_window, load, theme):
    """U-S4h ruling m. Catches the 0.6 opacity dim (2.44:1 light, 3.34:1 dark) and a verified badge with its fill."""

    def verified_ke(design, provenance, **kwargs):
        outcome = compute(design, provenance, **kwargs)
        t = dataclasses.replace(outcome.analysis.ke_phase_v_s_per_rad, status=Status.VERIFIED)
        return dataclasses.replace(outcome, analysis=dataclasses.replace(outcome.analysis, ke_phase_v_s_per_rad=t))

    window = load(make_window(verified_ke), D08)
    window.appearance.set_theme(theme)
    window.show_results_tab("tab-results")
    ink = STALE_INK[theme]
    cards = {"r-phase": window.results_tab.cards["r-phase"], "ke": window.results_tab.cards["ke"]}
    assert cards["ke"].badge.label.property("status") == "verified", "precondition: one verified badge"
    QApplication.processEvents()
    fresh = {key: strongest_ink(card, card.value, card_fill(card)) for key, card in cards.items()}
    assert fresh == dict.fromkeys(cards, ink["text-1"]), "precondition: a current value prints in text-1"
    window.results.show(window.session.current_outcome().analysis, stale=True)
    QApplication.processEvents()
    assert window.results_tab.stale_stamp.isVisible(), "precondition: the results are marked stale"
    for key, card in cards.items():
        assert card_fill(card) == ink["bg-app"], key
        parts = {"value": card.value, "unit": card.unit, "badge word": card.badge.label, "badge glyph": card.badge.icon}
        assert card.badge.icon.isVisible(), key
        printed = {name: strongest_ink(card, part, ink["bg-app"]) for name, part in parts.items()}
        assert printed["value"] == ink["text-3"], key
        # Small text may never reach full coverage, so its strongest pixel is a blend of text-3 and the fill: between
        # the AA floor and text-3 itself. A text-1 pixel or a surface-inverse fill would sit above the ceiling.
        ceiling = contrast_ratio(ink["text-3"], ink["bg-app"])
        ratios = {name: contrast_ratio(found, ink["bg-app"]) for name, found in printed.items()}
        assert {name: 4.5 <= ratio <= ceiling + 0.01 for name, ratio in ratios.items()} == dict.fromkeys(parts, True), (
            key,
            printed,
        )
        assert ink["border-control"] in colours_painted(card, card.badge.label), key
