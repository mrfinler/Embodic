"""Inspector, dialog and canvas details of m4_review.md ruling g 1 to 6 (F11, F13 to F20); tables at 300 px."""

import re

import pytest
from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication, QLabel, QLineEdit, QListWidget, QTableWidget, QToolButton
from tests.ui.qt_design.conftest import find

from embodic.model.vocabulary import TopologyKind
from embodic.ui.views.coil_panel import CHIP_PX, FieldEditor

D08 = "spiral_12c10p_d08"
WAVE = "wave_16p_example"
FORBIDDEN = re.compile(r"xcoil|kicad|engine\.js|docs/|\.json", re.IGNORECASE)


def _two_pane(window):
    """Resize to the two-pane width, where the inspector is 300 px (design_spec.md section 5)."""
    window.resize(960, 700)
    for _ in range(3):
        QApplication.processEvents()
    assert window.splitter.sizes()[0] == 300


def _header_lines(table: QTableWidget) -> list[str]:
    return [table.horizontalHeaderItem(c).text() for c in range(table.columnCount()) if not table.isColumnHidden(c)]


def _fits_without_sideways_scroll(table: QTableWidget) -> None:
    header = table.horizontalHeader()
    QApplication.processEvents()
    assert table.horizontalScrollBar().maximum() == 0, (header.length(), table.viewport().width())
    metrics = header.fontMetrics()
    for c in range(table.columnCount()):
        if table.isColumnHidden(c):
            continue
        widest = max(metrics.horizontalAdvance(line) for line in table.horizontalHeaderItem(c).text().split("\n"))
        assert header.sectionSize(c) >= widest, table.horizontalHeaderItem(c).text()


def _layers_tab_at_300_px(make_shell, wait_computed):
    window = make_shell().window
    window.session.load_example(D08)
    wait_computed(window)
    _two_pane(window)
    window.inspector_tabs.setCurrentWidget(window.panels["tab-layers"])
    QApplication.processEvents()
    return find(window, "layer-list")


@pytest.mark.req("REQ-N-15")
def test_ruling_g1_layer_list_has_the_ruled_columns_and_the_row_tooltip_names_the_pair_vias(make_shell, wait_computed):
    """Catches a show column, a renamed or missing column (F11) or a pair row without its vias."""
    table = _layers_tab_at_300_px(make_shell, wait_computed)
    assert [line.replace("\n", " ") for line in _header_lines(table)] == [
        "Layer",
        "Kind",
        "Thickness (µm)",
        "Pair",
        "Rotation (°)",
    ]
    copper = [r for r in range(table.rowCount()) if table.item(r, 1).text() == "Copper"]
    assert [table.item(r, 0).toolTip() for r in copper] == ["Pair 1 joins L1 and L2 through vias."] * 2


@pytest.mark.req("REQ-N-15")
@pytest.mark.xfail(strict=True, reason="five header-wide columns need about 277 px; the 300 px inspector leaves 248")
def test_ruling_g1_spiral_layer_list_fits_the_300_px_inspector_without_sideways_scroll(make_shell, wait_computed):
    """Records the open part of ruling g 1: at 300 px the spiral columns overflow by about 29 px."""
    _fits_without_sideways_scroll(_layers_tab_at_300_px(make_shell, wait_computed))


@pytest.mark.req("REQ-N-15")
@pytest.mark.xfail(strict=True, reason="six header-wide columns need about 277 px; the 300 px inspector leaves 274")
def test_screw_table_fits_the_300_px_inspector_without_sideways_scroll(make_shell, wait_computed):
    """Catches the screw table scrolling sideways in the two-pane layout (U-M4c-2 open question)."""
    window = make_shell().window
    window.session.load_example(WAVE)
    wait_computed(window)
    _two_pane(window)
    window.inspector_tabs.setCurrentWidget(window.panels["tab-board"])
    QApplication.processEvents()
    table = find(window, "screw-table")
    assert table.rowCount() > 0
    _fits_without_sideways_scroll(table)


@pytest.mark.req("REQ-N-15")
def test_ruling_g2_every_label_sits_above_its_control_and_input_edges_align(make_shell, wait_computed):
    """Catches a label beside its control (F17), unaligned input edges (F16) or chips other than 20 px (F15)."""
    window = make_shell().window
    window.session.load_example(D08)
    wait_computed(window)
    for tab, panel in window.panels.items():
        window.inspector_tabs.setCurrentWidget(panel)
        QApplication.processEvents()
        edges = set()
        for editor in panel.findChildren(FieldEditor):
            if not editor.isVisibleTo(panel):
                continue
            label_bottom = editor.label.mapTo(panel, QPoint(0, editor.label.height())).y()
            assert label_bottom <= editor.input.mapTo(panel, QPoint(0, 0)).y(), (tab, editor.widget_id)
            assert editor.chip.height() == CHIP_PX
            if isinstance(editor.input, QLineEdit):
                edges.add(editor.input.mapTo(panel, QPoint(editor.input.width(), 0)).x())
        assert len(edges) <= 1, (tab, edges)
        for label in panel.findChildren(QLabel):
            buddy = label.buddy()
            if buddy is not None and label.isVisibleTo(panel) and buddy.isVisibleTo(panel):
                assert label.mapTo(panel, QPoint(0, 0)).y() < buddy.mapTo(panel, QPoint(0, 0)).y(), label.text()


@pytest.mark.req("REQ-F-36")
def test_ruling_g3_topology_buttons_show_their_icon_and_a_boundary_when_unchecked(make_shell):
    """Catches text-only topology buttons, or unchecked buttons with no visible edge (F14)."""
    window = make_shell().window
    dialog = window.new_design_dialog()
    dialog.show()
    QApplication.processEvents()
    border = window.tokens.colours["border-control"]
    for topology in TopologyKind:
        button = find(dialog, f"param-topology-{topology.value}")
        assert isinstance(button, QToolButton) and not button.isChecked()
        assert not button.icon().isNull() and button.iconSize().width() == 24
        image = button.grab().toImage()
        assert image.pixelColor(0, image.height() // 2).name() == border, topology
    dialog.close()


@pytest.mark.req("REQ-F-25")
def test_ruling_g4_example_items_show_a_600_title_over_a_text3_note_free_of_other_programs(make_shell):
    """Catches same-weight title and note (F13), or a note naming Xcoil, engine.js or a repository path (F12)."""
    window = make_shell().window
    gallery = window.examples_gallery()
    gallery.show()
    QApplication.processEvents()
    items = gallery.findChild(QListWidget, "examples-list")
    for row in range(items.count()):
        card = items.itemWidget(items.item(row))
        title, note = card.findChildren(QLabel)
        assert title.font().weight() == 600 and title.property("class") is None
        assert note.property("class") == "hint" and note.text()
        assert not FORBIDDEN.search(note.text()), note.text()
        assert not FORBIDDEN.search(items.item(row).toolTip())
    gallery.close()


@pytest.mark.req("REQ-F-25")
@pytest.mark.xfail(strict=True, reason="the serpentine example title names Xcoil; titles live in the example files")
def test_ux_ac_03_example_titles_name_no_other_program(make_shell):
    """Records DEF: 'Example: 16-pole serpentine (Xcoil default)' is shown as an example title (UX-AC-03)."""
    window = make_shell().window
    gallery = window.examples_gallery()
    items = gallery.findChild(QListWidget, "examples-list")
    titles = [items.itemWidget(items.item(row)).findChildren(QLabel)[0].text() for row in range(items.count())]
    assert not [t for t in titles if FORBIDDEN.search(t)]


@pytest.mark.req("REQ-F-13")
def test_ruling_g5_the_coil_pattern_has_its_caption_and_case_hint(make_shell, wait_computed):
    """Catches a bare pattern string with no caption or no key to its upper and lower case (F19)."""
    window = make_shell().window
    window.session.load_example(D08)
    wait_computed(window)
    panel = window.panels["tab-phases"]
    window.inspector_tabs.setCurrentWidget(panel)
    QApplication.processEvents()
    pattern = find(window, "phase-pattern-string")
    assert pattern.isVisibleTo(panel) and pattern.text()
    assert panel.pattern_caption.text() == "Coil pattern" and panel.pattern_caption.isVisibleTo(panel)
    assert panel.pattern_hint.text() == "Upper case +, lower case −." and panel.pattern_hint.isVisibleTo(panel)


@pytest.mark.req("REQ-F-36")
def test_ruling_g6_a_blank_design_shows_why_the_canvas_is_empty_and_no_layer_toggles(make_shell, wait_computed):
    """Catches layer toggles over an empty canvas, or an empty canvas with no reason (F20)."""
    window = make_shell().window
    window.session.new_design(TopologyKind.SPIRAL)
    QApplication.processEvents()
    canvas_page = window.canvas.parentWidget()
    assert not window.layer_bar.isVisibleTo(canvas_page)
    assert window.canvas_blank.isVisibleTo(canvas_page)
    assert window.canvas_blank.text() == "The drawing appears when every required field is valid."
    window.session.load_example(D08)
    wait_computed(window)
    QApplication.processEvents()
    assert window.layer_bar.isVisibleTo(canvas_page) and not window.canvas_blank.isVisibleTo(canvas_page)
