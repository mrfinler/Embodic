"""A shown 1280 x 800 shell window on a throwaway settings file and recovery folder, and a wait for its result."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from collections.abc import Callable

import pytest
from PySide6.QtCore import QSettings, QStandardPaths

from embodic.ui.app import QSettingsStore, create_shell
from embodic.ui.viewmodels.outcome import OutcomeReady
from embodic.ui.viewmodels.session import SessionComputed
from embodic.ui.views.main_window import MainWindow, ShellPaths

READY_TIMEOUT_MS = 60_000  # hang guard only; no assertion depends on it


@pytest.fixture(autouse=True)
def _qt_test_paths():
    QStandardPaths.setTestModeEnabled(True)
    yield
    QStandardPaths.setTestModeEnabled(False)


@pytest.fixture
def window(qtbot, tmp_path) -> MainWindow:
    """Return the app's shell window, shown at 1280 x 800 in the light theme, as `embodic` starts it."""
    store = QSettingsStore(QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat))
    shell = create_shell(store, ShellPaths(recovery_dir=tmp_path / "recovery"), prefers_dark=lambda: False)
    qtbot.addWidget(shell.window)
    shell.window.resize(1280, 800)
    shell.window.show()
    qtbot.waitExposed(shell.window)
    return shell.window


@pytest.fixture
def wait_drawn(qtbot) -> Callable[[MainWindow], None]:
    """Return a function that waits until the current design's compute result is on screen."""

    def wait(window: MainWindow) -> None:
        def drawn() -> bool:
            state = window.session.state.value
            return (
                isinstance(state, SessionComputed)
                and not state.computing
                and isinstance(window.outcome.state.value, OutcomeReady)
            )

        qtbot.waitUntil(drawn, timeout=READY_TIMEOUT_MS)

    return wait
