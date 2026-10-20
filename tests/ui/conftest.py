"""Every UI test runs in the app's own QApplication: `qt_application` registers the bundled fonts (design_spec.md 4)."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
import shiboken6
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication

from embodic.ui.app import qt_application


@pytest.fixture(scope="session", autouse=True)
def qapp() -> QApplication:
    """Replace pytest-qt's application with the one the app and the screenshot levers start."""
    return qt_application()


SETTLE_ROUNDS = 5


def settle_events() -> None:
    """Run the events a GUI update posted, and those they post, as a user's event loop does before the next input.

    A wait returns the moment its condition holds, which can be right after the update that made it true. Right
    after a result the shell's cards are squashed to 0 px height until their posted layout request runs, and a click
    on a 0 px button is lost: the UI-31 flake (U-M8a).
    """
    for _ in range(SETTLE_ROUNDS):
        QCoreApplication.processEvents()


@pytest.fixture
def settle():
    """Return settle_events, for the fixtures that wait for a result before a test acts on the window."""
    return settle_events


def _parentless_widgets() -> dict[int, str]:
    """Return the live top-level widgets that no widget owns, by C++ address, with their class names."""
    return {
        shiboken6.getCppPointer(w)[0]: type(w).__name__
        for w in QApplication.topLevelWidgets()
        if w.parentWidget() is None
    }


@pytest.fixture(autouse=True)
def _delete_closed_widgets(qapp: QApplication):
    """Delete the widgets pytest-qt closed at teardown; fail a test that leaves a parentless widget alive.

    pytest-qt calls deleteLater() on every widget a test registered and then only processEvents(), which does not
    deliver a deferred delete posted outside an event loop. Without this every shell window of the session stayed
    alive, about 49 MiB and 2650 widgets each, and each new window repolished them all (DEF-U-M6f-01).

    A parentless widget that is still alive after that flush is left to Python. Once its wrapper is in a reference
    cycle, the cyclic GC frees it on whichever thread collects, the compute worker's included, and a widget freed off
    the GUI thread crashes the GUI thread's next event for it (U-M9c).
    """
    before = _parentless_widgets()
    yield
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    left = sorted(name for address, name in _parentless_widgets().items() if address not in before)
    if left:
        pytest.fail(
            f"parentless widgets outlived the test: {left}. Register each with qtbot.addWidget, or set "
            "WA_DeleteOnClose before closing it, so it is deleted here on the GUI thread (U-M9c)."
        )
