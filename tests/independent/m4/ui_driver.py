"""Agent 4's own offscreen driver: start the shell through `embodic.ui.app`, act on widgets by objectName."""

import time
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QLineEdit,
    QListWidget,
    QPushButton,
    QToolButton,
    QWidget,
)

from embodic.ui.app import QSettingsStore, create_shell, qt_application
from embodic.ui.viewmodels.session import SessionComputed
from embodic.ui.views.main_window import ShellPaths

HANG_GUARD_S = 90.0


def app() -> QApplication:
    """Return the running QApplication, started by embodic's own entry point."""
    return qt_application()


def spin(done: Callable[[], bool], what: str) -> None:
    """Process events until ``done()``; the timeout is a hang guard, never an assertion of speed."""
    end = time.monotonic() + HANG_GUARD_S
    while time.monotonic() < end:
        app().processEvents()
        if done():
            return
        time.sleep(0.01)
    raise AssertionError(f"hang guard: {what}")


def open_window(settings_dir: Path, size: tuple[int, int] = (1280, 800)):
    """Start a shell on a settings file of its own, the way `embodic` does, and show it."""
    app()
    store = QSettingsStore(QSettings(str(settings_dir / "settings.ini"), QSettings.Format.IniFormat))
    window = create_shell(store, ShellPaths(recovery_dir=settings_dir / "recovery"), prefers_dark=lambda: False).window
    window.resize(*size)
    window.show()
    spin(window.isVisible, "window shown")
    return window


def find(root: QWidget, name: str, kind: type[QWidget] = QWidget) -> QWidget:
    """Return the widget under root with an objectName; fail when there is none."""
    widget = root.findChild(kind, name)
    assert widget is not None, f"no widget named {name}"
    return widget


def computed(window) -> bool:
    """Tell whether the current design's compute result is in."""
    state = window.session.state.value
    return isinstance(state, SessionComputed) and not state.computing


def wait_computed(window) -> None:
    """Wait until the current design is computed and drawn."""
    spin(lambda: computed(window), "compute finished")
    for _ in range(5):
        app().processEvents()


def load_example(window, example_id: str) -> None:
    """Open the Examples gallery (empty-state button, else the toolstrip action) and load one example."""
    empty = window.findChild(QPushButton, "btn-empty-examples")
    if empty is not None and empty.isVisible():
        empty.click()
    else:
        find(window, "act-examples", QToolButton).click()
    gallery = find(window, "dlg-examples", QDialog)
    spin(gallery.isVisible, "gallery shown")
    items = find(gallery, "examples-list", QListWidget)
    ids = [items.item(r).data(Qt.ItemDataRole.UserRole) for r in range(items.count())]
    items.setCurrentRow(ids.index(example_id))
    find(gallery, "btn-load-example", QPushButton).click()
    wait_computed(window)


def answer_next_file_dialog(path: Path) -> None:
    """Queue an answer for the next modal Qt file dialog: type the full path into its file name box and press Open.

    `selectFile` waits for the dialog's file model to read the folder and was seen to leave the selection empty, so
    the driver types the path as a user does, and repeats until the dialog closes.
    """
    answered = [False]

    def answer() -> None:
        dialog = QApplication.activeModalWidget()
        if isinstance(dialog, QFileDialog):
            name = dialog.findChild(QLineEdit, "fileNameEdit")
            assert name is not None, "the Qt file dialog has a file name box"
            name.setText(str(path))
            dialog.accept()
            answered[0] = True
        elif answered[0]:
            return
        QTimer.singleShot(100, answer)

    QTimer.singleShot(20, answer)


def close(window) -> None:
    """Close a window and let Qt delete it."""
    window.close()
    window.deleteLater()
    for _ in range(5):
        app().processEvents()
