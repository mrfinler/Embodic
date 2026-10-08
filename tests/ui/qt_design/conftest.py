"""Offscreen Qt and a shell window with its design session, wired to a throwaway settings file and recovery folder."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from dataclasses import dataclass
from pathlib import Path

import pytest
from PySide6.QtCore import QSettings, QStandardPaths, Qt
from PySide6.QtWidgets import QCheckBox, QComboBox, QLineEdit, QWidget

from embodic.api import compute
from embodic.ui.app import QSettingsStore, create_shell
from embodic.ui.viewmodels.session import SessionComputed
from embodic.ui.views.main_window import MainWindow, ShellPaths

READY_TIMEOUT_MS = 60_000  # hang guard only; no assertion depends on it


@dataclass
class Shell:
    """One shell window and what a test can observe around it."""

    window: MainWindow
    recovery_dir: Path
    calls: list


@pytest.fixture(autouse=True)
def _qt_test_paths():
    QStandardPaths.setTestModeEnabled(True)
    yield
    QStandardPaths.setTestModeEnabled(False)


@pytest.fixture
def make_shell(qtbot, tmp_path):
    """Return a factory: make_shell(compute_fn=None, recovery_dir=None) opens a shown 1280 x 800 shell window."""

    def factory(compute_fn=None, recovery_dir=None):
        calls = []
        inner = compute_fn or compute

        def counting(design, provenance, **kwargs):
            calls.append(design)
            return inner(design, provenance, **kwargs)

        store = QSettingsStore(QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat))
        recovery = recovery_dir or tmp_path / "recovery"
        window, _ = create_shell(store, ShellPaths(recovery_dir=recovery), counting, lambda: False)
        qtbot.addWidget(window)
        window.resize(1280, 800)
        window.show()
        qtbot.waitExposed(window)
        return Shell(window=window, recovery_dir=recovery, calls=calls)

    return factory


@pytest.fixture
def wait_computed(qtbot):
    """Return a function that waits until the session's current design has its compute result."""

    def wait(window):
        def done():
            state = window.session.state.value
            return isinstance(state, SessionComputed) and not state.computing and state.outcome is not None

        qtbot.waitUntil(done, timeout=READY_TIMEOUT_MS)

    return wait


def find(window: MainWindow, name: str) -> QWidget:
    """Return the window's widget with an objectName; fail when there is none."""
    widget = window.findChild(QWidget, name)
    assert widget is not None, name
    return widget


def enter(qtbot, window: MainWindow, name: str, value) -> None:
    """Enter a value the way a user does: type and press Enter, pick a combo item, or click a check box."""
    widget = find(window, name)
    if isinstance(widget, QLineEdit):
        widget.setFocus()
        widget.selectAll()
        qtbot.keyClicks(widget, str(value))
        qtbot.keyClick(widget, Qt.Key.Key_Return)
    elif isinstance(widget, QComboBox):
        index = widget.findData(value)
        assert index >= 0, (name, value)
        widget.setCurrentIndex(index)
        widget.activated.emit(index)
    elif isinstance(widget, QCheckBox):
        if widget.isChecked() != bool(value):
            qtbot.mouseClick(widget, Qt.MouseButton.LeftButton)
    else:
        raise AssertionError(f"{name} is not an input")
