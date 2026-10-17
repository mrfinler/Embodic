"""Offscreen Qt and a shell window with its session, wired to a throwaway settings file and recovery folder."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QSettings, QStandardPaths
from PySide6.QtWidgets import QWidget

from embodic.api import compute
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
def make_window(qtbot, tmp_path):
    """Return a factory: make_window(compute_fn=None) opens a shown 1280 x 800 shell window."""

    def factory(compute_fn=None) -> MainWindow:
        store = QSettingsStore(QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat))
        window, _ = create_shell(
            store, ShellPaths(recovery_dir=tmp_path / "recovery"), compute_fn or compute, lambda: False
        )
        qtbot.addWidget(window)
        window.resize(1280, 800)
        window.show()
        qtbot.waitExposed(window)
        return window

    return factory


@pytest.fixture
def load(qtbot, settle):
    """Return a function that loads an example into a window and waits for its compute result on screen."""

    def run(window: MainWindow, example_id: str) -> MainWindow:
        window.session.load_example(example_id)

        def done():
            state = window.session.state.value
            return (
                isinstance(state, SessionComputed)
                and not state.computing
                and state.outcome is not None
                and isinstance(window.outcome.state.value, OutcomeReady)
            )

        qtbot.waitUntil(done, timeout=READY_TIMEOUT_MS)
        settle()
        squashed = [key for key, card in window.results_tab.cards.items() if card.how_toggle.height() == 0]
        assert squashed == [], "result cards still at 0 px height after settling: a click on them would be lost"
        return window

    return run


def find(parent: QWidget, cls, name: str):
    """Return the child with an objectName; fail when there is none."""
    widget = parent.findChild(cls, name)
    assert widget is not None, name
    return widget
