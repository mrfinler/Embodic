"""What a user does in a walkthrough: find a widget by objectName, type into a field, answer a file dialog."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QFileDialog, QLineEdit, QTabBar, QToolButton, QWidget

from embodic.ui.toolstrip import TOOLSTRIP, ToolstripTab
from embodic.ui.views.main_window import MainWindow


def find(root: QWidget, name: str, kind: type[QWidget] = QWidget) -> QWidget:
    """Return the widget under ``root`` with an objectName; fail when there is none."""
    widget = root.findChild(kind, name)
    assert widget is not None, name
    return widget


def show_field(window: MainWindow, name: str) -> QLineEdit:
    """Open the inspector tab that holds a field and scroll it into view, as a user does before typing."""
    for panel in window.panels.values():
        edit = panel.findChild(QLineEdit, name)
        if edit is not None:
            window.inspector_tabs.setCurrentWidget(panel)
            panel.ensureWidgetVisible(edit)
            return edit
    raise AssertionError(f"no inspector tab holds {name}")


def type_value(qtbot, window: MainWindow, name: str, value: str) -> None:
    """Replace a field's text the way a user does: select all, type, press Enter."""
    edit = show_field(window, name)
    edit.setFocus()
    edit.selectAll()
    qtbot.keyClicks(edit, value)
    qtbot.keyClick(edit, Qt.Key.Key_Return)


def answer_file_dialog(path: str) -> None:
    """Fill the open Qt file dialog with ``path`` and accept it, as a user typing a file name does."""
    dialog = QApplication.activeModalWidget()
    assert isinstance(dialog, QFileDialog), dialog
    dialog.selectFile(path)
    dialog.accept()


def run_action(qtbot, window: MainWindow, action_id: str) -> None:
    """Open the toolstrip tab of an action and click its button, as a user does."""
    tab = next(row.tab for row in TOOLSTRIP if row.id == action_id)
    tabs = find(window, "toolstrip-tabs", QTabBar)
    qtbot.mouseClick(tabs, Qt.MouseButton.LeftButton, pos=tabs.tabRect(list(ToolstripTab).index(tab)).center())
    button = find(window, action_id, QToolButton)
    assert button.isVisible() and button.isEnabled(), action_id
    qtbot.mouseClick(button, Qt.MouseButton.LeftButton)


def press(qtbot, key: Qt.Key, modifier: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier) -> None:
    """Send one key to the widget that has keyboard focus, as a keyboard does."""
    target = QApplication.focusWidget()
    assert target is not None, "some widget has keyboard focus"
    qtbot.keyClick(target, key, modifier)


def tab_until(qtbot, reached, limit: int = 400) -> QWidget:
    """Press Tab until ``reached(focus widget)`` holds; fail when ``limit`` presses do not get there."""
    for _ in range(limit):
        widget = QApplication.focusWidget()
        if widget is not None and reached(widget):
            return widget
        press(qtbot, Qt.Key.Key_Tab)
    raise AssertionError(f"not reachable with {limit} Tab presses")
