"""Offscreen Qt and a shell window wired to a throwaway settings file, recovery folder and compute function."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from dataclasses import dataclass
from pathlib import Path

import pytest
from PySide6.QtCore import QSettings, QStandardPaths

from embodic.api import compute
from embodic.ui.app import QSettingsStore, create_shell
from embodic.ui.viewmodels.outcome import OutcomeReady
from embodic.ui.views.main_window import MainWindow, ShellPaths
from embodic.ui.workers import ComputeWorker

D08 = "spiral_12c10p_d08"
READY_TIMEOUT_MS = 60_000  # hang guard only; no assertion depends on it


@dataclass
class Shell:
    """One shell window and what a test can change around it."""

    window: MainWindow
    worker: ComputeWorker
    settings_path: Path
    recovery_dir: Path
    calls: list


@pytest.fixture(autouse=True)
def _qt_test_paths():
    QStandardPaths.setTestModeEnabled(True)
    yield
    QStandardPaths.setTestModeEnabled(False)


@pytest.fixture
def make_shell(qtbot, tmp_path):
    """Return a factory: make_shell(compute_fn=None, os_dark=False) opens a shown 1280 x 800 shell window."""

    def factory(compute_fn=None, os_dark=False, settings_path=None):
        calls = []
        inner = compute_fn or compute

        def counting(design, provenance, **kwargs):
            calls.append(design)
            return inner(design, provenance, **kwargs)

        settings_path = settings_path or tmp_path / "settings.ini"
        store = QSettingsStore(QSettings(str(settings_path), QSettings.Format.IniFormat))
        recovery = tmp_path / "recovery"
        window, worker = create_shell(store, ShellPaths(recovery_dir=recovery), counting, lambda: os_dark)
        qtbot.addWidget(window)
        window.resize(1280, 800)
        window.show()
        qtbot.waitExposed(window)
        return Shell(window=window, worker=worker, settings_path=settings_path, recovery_dir=recovery, calls=calls)

    return factory


@pytest.fixture
def wait_ready(qtbot, settle):
    """Return a function that waits until the latest compute of a window is on screen."""

    def wait(window):
        qtbot.waitUntil(lambda: isinstance(window.outcome.state.value, OutcomeReady), timeout=READY_TIMEOUT_MS)
        settle()

    return wait


@pytest.fixture
def d08_shell(make_shell, wait_ready):
    """Return a shell with the D08 example computed and drawn."""
    shell = make_shell()
    shell.window.outcome.open_example(D08)
    wait_ready(shell.window)
    return shell
