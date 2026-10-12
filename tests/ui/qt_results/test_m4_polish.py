"""The M4 polish carried into M5 (m4_review_2.md section 8): S31, S39 and the focused DRC cell."""

import pytest
from PySide6.QtCore import QItemSelectionModel, Qt
from PySide6.QtGui import qGray
from PySide6.QtWidgets import QApplication, QLineEdit, QListWidget

CF11, WAVE = "spiral_12c16p_default", "wave_16p_example"


def dark_pixels(view, index) -> int:
    """Count the text pixels inside one cell, a little in from its edges."""
    rect = view.visualRect(index).adjusted(6, 4, -4, -4)
    image = view.viewport().grab(rect).toImage()
    return sum(1 for x in range(image.width()) for y in range(image.height()) if qGray(image.pixel(x, y)) < 110)


@pytest.mark.req("REQ-F-33")
def test_s31_the_before_you_export_list_shows_every_row_and_no_empty_band(make_window, load) -> None:
    """S31. Catches the checklist cut after three lines (the old 150 px cap) or a list taller than its rows."""
    window = load(make_window(), CF11)
    window.show_export("export_bundle")
    dialog = window.export_dialog
    dialog.findChild(QLineEdit, "export-folder").setText("out")
    for _ in range(10):
        QApplication.processEvents()
    checklist = dialog.findChild(QListWidget, "export-checklist")
    assert checklist.count() >= 4
    viewport = checklist.viewport().height()
    bottoms = [checklist.visualItemRect(checklist.item(row)).bottom() for row in range(checklist.count())]
    assert max(bottoms) < viewport, (bottoms, viewport)
    assert viewport - max(bottoms) <= 4, (bottoms, viewport)
    assert not checklist.verticalScrollBar().isVisible()
    dialog.reject()


@pytest.mark.req("REQ-F-25")
def test_s39_example_notes_say_neither_default_nor_preset_nor_2_turns(make_window) -> None:
    """S39 (m4_review_2.md 8.1). Catches gallery notes that keep the words ruling g took out of the titles."""
    window = make_window()
    gallery = window.examples_gallery()
    examples = gallery.findChild(QListWidget, "examples-list")
    shown = [examples.item(row).data(Qt.ItemDataRole.AccessibleTextRole) for row in range(examples.count())]
    assert len(shown) == 5
    assert [s for s in shown if any(word in s.lower() for word in ("default", "preset", "2 turns"))] == []
    gallery.close()


@pytest.mark.req("REQ-F-11")
def test_the_focused_drc_message_cell_keeps_all_its_text(make_window, load, qtbot) -> None:
    """U-M4e-5 pattern on drc-table. Catches a focused cell whose focus border pushes out its last wrapped line."""
    window = load(make_window(), WAVE)
    window.resize(1280, 800)
    window.show_results_tab("tab-drc")
    table = window.drc_tab.table
    message = 2
    for _ in range(10):
        QApplication.processEvents()
    window.activateWindow()
    table.setFocus(Qt.FocusReason.TabFocusReason)
    rows = range(min(8, table.model().rowCount()))
    flags = QItemSelectionModel.SelectionFlag.ClearAndSelect
    table.selectionModel().setCurrentIndex(table.model().index(0, 0), flags)
    unfocused = {row: dark_pixels(table, table.model().index(row, message)) for row in rows if row != 0}
    table.selectionModel().setCurrentIndex(table.model().index(1, 0), flags)
    unfocused[0] = dark_pixels(table, table.model().index(0, message))
    short = []
    for row in rows:
        index = table.model().index(row, message)
        table.selectionModel().setCurrentIndex(index, flags)
        QApplication.processEvents()
        focused = dark_pixels(table, index)
        if focused < 0.85 * unfocused[row]:
            short.append((row, index.data(), unfocused[row], focused))
    assert short == []
