"""Item 2: UI behaviour through public widgets by objectName, offscreen, `embodic.ui.app` entry points only."""

import math
import re
import shutil

import pypdf
import pytest
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QAccessible, QContextMenuEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QAbstractButton,
    QApplication,
    QCheckBox,
    QComboBox,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QLabel,
    QMenu,
    QPushButton,
    QSplitter,
    QTabBar,
    QTabWidget,
    QToolButton,
    QWidget,
)
from ui_driver import answer_next_file_dialog, app, close, find, load_example, open_window, spin, wait_computed

from conftest import example_file, outcome_of
from embodic.api import compute_project
from embodic.io.report import write_report_pdf

NBSP = "\u00a0"
UNITS = r"(?:[nµmkM]?(?:V·s/rad|N·m/A|N·m/√W|N·m|rpm/V|Ω·m|Ω|W/\(m²·K\)|W|H|A/mm²|A|V|g|K|T|mm²|mm|µm|rad|°C|rpm))"
NUMBER_UNIT = re.compile(r"(?<![\w/.])(−?\d+(?:\.\d+)?)([ \u2009\u202f\u00a0]?)(" + UNITS + r")(?![\w²³])")

pytestmark = [
    pytest.mark.req("REQ-F-13", "REQ-N-15"),
    pytest.mark.filterwarnings("ignore::DeprecationWarning"),
]


def share(split: QSplitter) -> float:
    """Return the canvas share of the centre splitter."""
    sizes = split.sizes()
    return sizes[0] / sum(sizes)


def test_canvas_share_is_restored_after_restart_and_kept_through_a_resize(tmp_path):
    """Request 1. Catches a share that is not written, not read back at start, or reset by a resize."""
    first = open_window(tmp_path)
    load_example(first, "spiral_12c10p_d08")
    split = find(first, "centre-split", QSplitter)
    total = sum(split.sizes())
    split.moveSplitter(int(total * 0.45), 1)
    spin(lambda: abs(share(split) - 0.45) < 0.02, "handle moved")
    moved = share(split)
    assert abs(moved - 0.60) > 0.1, "precondition: the share moved away from the 60 % default"
    close(first)

    second = open_window(tmp_path)
    load_example(second, "spiral_12c10p_d08")
    split = find(second, "centre-split", QSplitter)
    assert abs(share(split) - moved) <= 0.01, f"restored {share(split):.3f}, stored {moved:.3f}"
    second.resize(1600, 900)
    spin(lambda: second.width() == 1600, "resized")
    for _ in range(10):
        app().processEvents()
    assert abs(share(split) - moved) <= 0.01, f"after resize {share(split):.3f}, stored {moved:.3f}"
    close(second)


def test_open_loads_a_saved_d08_file_with_the_identical_design_hash(tmp_path):
    """Request 11. Catches an Open that is a no-op, loads another design, or alters the design on the way in."""
    saved = tmp_path / "saved_d08.embodic.json"
    shutil.copyfile(example_file("spiral_12c10p_d08"), saved)
    expected = compute_project(saved).design_hash
    assert expected == outcome_of("spiral_12c10p_d08").design_hash

    window = open_window(tmp_path)
    open_button = find(window, "act-open", QToolButton)
    assert open_button.isEnabled()
    answer_next_file_dialog(saved)
    open_button.click()
    wait_computed(window)
    assert window.session.current_outcome().design_hash == expected
    assert find(window, "st-counts", QLabel).text() == "2 layers, 12 coils, 63 vias"
    close(window)


def test_layer_bar_reads_each_designs_layers_when_rows_share_one_window(tmp_path):
    """U-M4e-2 note. Catches a layer bar that keeps buttons of an earlier design (L1 L2 L1 L2)."""
    window = open_window(tmp_path)
    seen = []
    for example_id in ("spiral_12c10p_d08", "serpentine_16p_example", "wave_16p_example", "spiral_12c10p_d08"):
        load_example(window, example_id)
        bar = find(window, "layer-toggles")
        texts = [b.text() for b in bar.findChildren(QAbstractButton) if b.isVisibleTo(bar)]
        want = list(outcome_of(example_id).boards.boards[0].copper_layers)
        seen.append((example_id, texts, want))
    close(window)
    assert all(texts == want for _id, texts, want in seen), seen


def card_texts(window) -> list[tuple[str, str]]:
    """Return (objectName, text) of every non-empty label in the results cards."""
    scroll = find(window, "results-scroll")
    return [(label.objectName(), label.text()) for label in scroll.findChildren(QLabel) if label.text()]


def joiner_faults(texts: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Return each number and unit not joined by U+00A0."""
    return [(m.group(0), name) for name, t in texts for m in NUMBER_UNIT.finditer(t) if m.group(2) != NBSP]


@pytest.mark.parametrize("example_id", ["spiral_12c10p_d08", "wave_16p_example"])
def test_results_cards_join_every_number_and_unit_with_nbsp(example_id, tmp_path):
    """Request 6. Catches a plain space, U+202F or U+2009 (or nothing) between a number and its unit."""
    window = open_window(tmp_path)
    load_example(window, example_id)
    texts = [(n, t) for n, t in card_texts(window) if not n.endswith("-title")]
    close(window)
    assert sum(1 for _n, t in texts for _m in NUMBER_UNIT.finditer(t)) > 20, "precondition: numbers with units"
    assert joiner_faults(texts) == []


def test_results_card_titles_join_number_and_unit_with_nbsp(tmp_path):
    """Request 6 covers every displayed number and unit, titles included."""
    window = open_window(tmp_path)
    load_example(window, "spiral_12c10p_d08")
    texts = [(n, t) for n, t in card_texts(window) if n.endswith("-title")]
    close(window)
    assert joiner_faults(texts) == []


def card_and_pdf_rows(tmp_path):
    """Return the D08 cards as title -> (value, unit, badge, label) and the PDF key result rows."""
    window = open_window(tmp_path)
    load_example(window, "spiral_12c10p_d08")
    scroll = find(window, "results-scroll")
    cards = {}
    for title in scroll.findChildren(QLabel):
        name = title.objectName()
        if name.startswith("res-") and name.endswith("-title"):
            stem = name[: -len("-title")]
            value = scroll.findChild(QLabel, f"{stem}-value")
            unit = scroll.findChild(QLabel, f"{stem}-unit")
            badge = scroll.findChild(QLabel, f"{stem}-badge")
            label = scroll.findChild(QLabel, f"{stem}-label")
            shown_label = label.text() if label is not None and label.isVisible() else ""
            if value and unit and badge:
                cards[title.text()] = (value.text(), unit.text(), badge.text(), shown_label)
    close(window)
    pdf = tmp_path / "d08.pdf"
    write_report_pdf(outcome_of("spiral_12c10p_d08"), pdf)
    lines = pypdf.PdfReader(pdf).pages[0].extract_text().splitlines()
    rows = lines[lines.index("Quantity Value Status") + 1 : lines.index("DRC summary")]
    return cards, rows


def pdf_row_for(rows, title):
    """Return the part of the PDF row after a card title."""
    hits = [r for r in rows if r.startswith(title + " ")]
    assert len(hits) == 1, (title, hits)
    return hits[0][len(title) + 1 :]


def test_pdf_key_results_print_the_value_and_unit_the_cards_show(tmp_path):
    """Brief 1c, D-042d. Catches a number or unit text that differs between report and screen ("dimensionless" too)."""
    cards, rows = card_and_pdf_rows(tmp_path)
    assert len(cards) >= 25, sorted(cards)
    assert any(unit == "dimensionless" for _v, unit, _b, _l in cards.values()), "precondition: a dimensionless card"
    mismatched = [
        (title, pdf_row_for(rows, title), value, unit)
        for title, (value, unit, _badge, _label) in cards.items()
        if not pdf_row_for(rows, title).startswith(f"{value}{NBSP}{unit} ")
    ]
    assert mismatched == []


FIVE_STATUSES = {"verified", "inferred", "assumption", "unresolved", "not tested"}


def test_pdf_key_results_print_the_status_word_and_label_the_cards_show(tmp_path):
    """Brief 1c, D-042c. Catches a badge that is not a status word, or a status or label that differs from the PDF.

    The PDF prints "unresolved (estimate)"; the card shows the badge "unresolved" with "estimate" beside it.
    """
    cards, rows = card_and_pdf_rows(tmp_path)
    assert {badge for _v, _u, badge, _l in cards.values()} <= FIVE_STATUSES
    assert any(label for _v, _u, _b, label in cards.values()), "precondition: a labelled result"
    mismatched = []
    for title, (_value, _unit, badge, label) in cards.items():
        row = pdf_row_for(rows, title)
        if label:
            ok = row.endswith(f" {badge} ({label})")
        else:
            ok = re.search(r" " + re.escape(badge) + r"(?: \((?:upper|lower) bound\))?$", row) is not None
        if not ok:
            mismatched.append((title, badge, label, row))
    assert mismatched == []


def test_serpentine_as_one_board_per_phase_reads_the_board_count(tmp_path):
    """Request 10. Catches `st-counts` that still counts one board after the stack mode changes.

    One board per phase needs two copper layers per board here (INVALID_SERPENTINE_COPPER_COUNT at six), so the user
    also picks "2" in `param-layer-count`, by keyboard.
    """
    window = open_window(tmp_path)
    load_example(window, "serpentine_16p_example")
    find(window, "param-stack-mode-one_board_per_phase", QAbstractButton).click()
    copper = find(window, "param-layer-count", QComboBox)
    copper.setFocus()
    QTest.keyClick(copper, Qt.Key.Key_Home)
    assert copper.currentText() == "2"

    def three_boards() -> bool:
        outcome = window.session.current_outcome()
        return outcome is not None and outcome.boards is not None and len(outcome.boards.boards) == 3

    spin(three_boards, "three boards computed")
    wait_computed(window)
    counts = find(window, "st-counts", QLabel).text()
    close(window)
    assert counts.startswith("3 boards"), counts


def clipped_tabs(bar: QTabBar) -> list[str]:
    """List the tabs of a tab bar whose text is wider than the tab."""
    name = bar.objectName() or bar.parent().objectName()
    found = []
    for i in range(bar.count()):
        need = bar.fontMetrics().horizontalAdvance(bar.tabText(i))
        if bar.tabRect(i).width() < need:
            found.append(f"{name}[{bar.tabText(i)}] {bar.tabRect(i).width()}<{need}")
    return found


def clipped_widgets(window) -> list[str]:
    """List visible labels, buttons and tabs whose text is wider than their room."""
    found = []
    for w in window.findChildren(QWidget):
        if not w.isVisible() or w.visibleRegion().isEmpty():
            continue
        if isinstance(w, QLabel):
            text = w.text()
            if not text or w.wordWrap() or "<" in text or "\n" in text or (w.pixmap() and not w.pixmap().isNull()):
                continue
            need = w.fontMetrics().horizontalAdvance(text)
            have = w.contentsRect().width() - 2 * w.margin() - w.indent() * (w.indent() > 0)
        elif isinstance(w, QAbstractButton) and not isinstance(w, QCheckBox) and w.text():
            if isinstance(w, QToolButton) and w.toolButtonStyle().name == "ToolButtonIconOnly":
                continue
            need = w.fontMetrics().horizontalAdvance(w.text().replace("&", ""))
            have = w.contentsRect().width()
        elif isinstance(w, QTabBar):
            found.extend(clipped_tabs(w))
            continue
        else:
            continue
        if have < need:
            found.append(f"{w.objectName() or type(w).__name__} '{w.text()[:30]}' {have}<{need}")
    return found


@pytest.mark.parametrize("size", [(960, 540), (1280, 800), (1600, 900)])
def test_no_visible_text_is_clipped(size, tmp_path):
    """Request 5. Catches a label, button or tab whose text is wider than the room it gets."""
    window = open_window(tmp_path, size)
    load_example(window, "spiral_12c10p_d08")
    found = clipped_widgets(window)
    close(window)
    assert found == []


def show_inspector_tab_of(window, name: str) -> QWidget:
    """Click the inspector tab that holds a widget, as a user does before using it."""
    tabs = find(window, "inspector-tabs", QTabWidget)
    target = find(window, name)
    for i in range(tabs.count()):
        if tabs.widget(i).isAncestorOf(target):
            bar = tabs.tabBar()
            QTest.mouseClick(bar, Qt.MouseButton.LeftButton, pos=bar.tabRect(i).center())
            spin(target.isVisible, f"{name} shown")
            return target
    raise AssertionError(f"no inspector tab holds {name}")


def pair_count(window) -> int | None:
    """Return the layer pair count of the computed design, or None while a compute runs."""
    outcome = window.session.current_outcome()
    return None if outcome is None else len(outcome.design.winding.layers.pairs)


def four_layer_d08(tmp_path):
    """Open D08 and pick four copper layers by keyboard, which makes two layer pairs."""
    window = open_window(tmp_path)
    load_example(window, "spiral_12c10p_d08")
    copper = find(window, "param-layer-count", QComboBox)
    copper.setFocus()
    QTest.keyClick(copper, Qt.Key.Key_Home)
    QTest.keyClick(copper, Qt.Key.Key_Down)
    assert copper.currentText() == "4"
    spin(lambda: pair_count(window) == 2, "two pairs")
    wait_computed(window)
    return window, show_inspector_tab_of(window, "pair-list")


def test_pair_list_tooltip_and_series_group_menu(tmp_path):
    """Request 3. Catches a pair row without its via tooltip, or a right click that opens no series-group menu."""
    window, pairs = four_layer_d08(tmp_path)
    tips = [pairs.item(r, 1).toolTip() for r in range(pairs.rowCount())]
    pairs.selectRow(1)
    pos = pairs.visualItemRect(pairs.item(1, 0)).center()
    event = QContextMenuEvent(QContextMenuEvent.Reason.Mouse, pos, pairs.viewport().mapToGlobal(pos))
    QApplication.sendEvent(pairs.viewport(), event)
    spin(lambda: isinstance(QApplication.activePopupWidget(), QMenu), "menu shown")
    menu = QApplication.activePopupWidget()
    entries = [a.text() for a in menu.actions()]
    menu.close()
    close(window)
    assert tips == ["Pair 1 joins L1 and L2 through vias.", "Pair 2 joins L3 and L4 through vias."]
    assert entries == ["Series group", "In series with pair 1", "In a group of its own"]


def test_pair_list_delete_key_removes_the_selected_pair(tmp_path):
    """Request 3. Catches a Delete key that does nothing or removes the copper layers with the pair."""
    window, pairs = four_layer_d08(tmp_path)
    window.activateWindow()
    spin(lambda: QApplication.activeWindow() is window, "window active")
    pairs.selectRow(1)
    pairs.setFocus()
    spin(lambda: window.focusWidget() is pairs, "pair-list focused")
    QTest.keyClick(pairs, Qt.Key.Key_Delete)
    spin(lambda: pair_count(window) == 1, "one pair left")
    wait_computed(window)
    copper = window.session.current_outcome().design.stackup
    close(window)
    assert sum(1 for layer in copper.layers if layer.kind == "copper") == 4, "the copper layers stay"


def test_go_to_first_missing_field_focuses_the_bore_field(tmp_path):
    """Request 4 (bore). Catches a button that leaves focus where it was or opens the wrong tab."""
    window = open_window(tmp_path)
    load_example(window, "spiral_12c10p_d08")
    bore = show_inspector_tab_of(window, "param-bore-radius")
    bore.setFocus()
    bore.selectAll()
    QTest.keyClick(bore, Qt.Key.Key_Backspace)
    QTest.keyClick(bore, Qt.Key.Key_Return)
    find(window, "toolstrip").setFocus()
    button = find(window, "btn-first-missing", QPushButton)
    spin(button.isVisible, "first-missing button shown")
    button.click()
    spin(lambda: window.focusWidget() is bore, "bore field focused")
    close(window)


def phases_with_copper_in(rect, layout) -> set[str]:
    """Return the phases whose top-layer copper has a sample point inside a scene rectangle (scene y = -board y)."""
    top = layout.copper_layers[0]
    found = set()
    for path in layout.paths:
        if path.layer != top or path.phase is None or path.phase.value in found:
            continue
        for prim in path.primitives:
            for t in (0.0, 0.25, 0.5, 0.75, 1.0):
                if hasattr(prim, "r_mm"):
                    a = prim.start_rad + t * prim.sweep_rad
                    x, y = prim.cx_mm + prim.r_mm * math.cos(a), prim.cy_mm + prim.r_mm * math.sin(a)
                else:
                    x, y = prim.x1_mm + t * (prim.x2_mm - prim.x1_mm), prim.y1_mm + t * (prim.y2_mm - prim.y1_mm)
                if rect.contains(QPointF(x, -y)):
                    found.add(path.phase.value)
                    break
    return found


@pytest.mark.parametrize("zoom", [1.0, 3.0, 8.0])
@pytest.mark.parametrize("centre_deg", [0.0, 100.0])
def test_wave_canvas_labels_every_phase_in_view(zoom, centre_deg, tmp_path):
    """Request 12. Catches a zoomed view that shows a phase's copper with no label of that phase in view."""
    window = open_window(tmp_path)
    load_example(window, "wave_16p_example")
    view = find(window, "fig-canvas", QGraphicsView)
    view.zoom_by(zoom)
    r_mid = 30.0
    view.centerOn(r_mid * math.cos(math.radians(centre_deg)), -r_mid * math.sin(math.radians(centre_deg)))
    for _ in range(10):
        app().processEvents()
    visible = view.mapToScene(view.viewport().rect()).boundingRect()
    port = view.viewport().rect()
    placed = [
        (item.text(), item.deviceTransform(view.viewportTransform()).mapRect(item.boundingRect()).toRect())
        for item in view.scene().items()
        if isinstance(item, QGraphicsSimpleTextItem)
        and item.isVisible()
        and re.fullmatch("[ABC][+\u2212]", item.text())
    ]
    labels = {text[0] for text, box in placed if port.contains(box)}
    phases = phases_with_copper_in(visible, outcome_of("wave_16p_example").boards.boards[0])
    close(window)
    assert phases, "precondition: copper in view"
    assert phases <= labels, f"zoom {zoom}: phases {sorted(phases)}, viewport {port}, labels {placed}"


CARD_NAME = re.compile(r"^(.+), (−?[0-9.]+) ([^,]+), (verified|inferred|assumption|unresolved|not tested)(?:, (.+))?$")


def test_every_result_card_names_its_value_unit_and_status_for_assistive_technology(tmp_path):
    """AX-06 proxy (DEF-UV4-07). Catches a card a screen reader announces without its value, unit or status."""
    window = open_window(tmp_path)
    load_example(window, "spiral_12c10p_d08")
    scroll = find(window, "results-scroll")
    faults = []
    cards = [w for w in scroll.findChildren(QWidget) if w.objectName().startswith("res-card-")]
    for card in cards:
        stem = "res-" + card.objectName()[len("res-card-") :]
        name = QAccessible.queryAccessibleInterface(card).text(QAccessible.Text.Name)
        m = CARD_NAME.match(name)
        value = scroll.findChild(QLabel, f"{stem}-value").text()
        badge = scroll.findChild(QLabel, f"{stem}-badge").text()
        if not m or m.group(2) != value or m.group(4) != badge:
            faults.append((card.objectName(), name, value, badge))
    close(window)
    assert len(cards) >= 25
    assert faults == []
