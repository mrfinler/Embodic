"""Open a packaged example the way a user does: Examples button, pick the row, Load."""

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QListWidget, QPushButton

from embodic.ui.views.main_window import MainWindow

from .support import find


def open_example_from_gallery(
    qtbot, window: MainWindow, wait_drawn: Callable[[MainWindow], None], example_id: str
) -> None:
    """Click Examples on the empty start view, pick ``example_id`` in the gallery, load it and wait for the drawing."""
    qtbot.mouseClick(find(window, "btn-empty-examples", QPushButton), Qt.MouseButton.LeftButton)
    gallery = find(window, "dlg-examples", QDialog)
    examples = find(gallery, "examples-list", QListWidget)
    row = next(r for r in range(examples.count()) if examples.item(r).data(Qt.ItemDataRole.UserRole) == example_id)
    examples.setCurrentRow(row)
    qtbot.mouseClick(find(gallery, "btn-load-example", QPushButton), Qt.MouseButton.LeftButton)
    wait_drawn(window)
