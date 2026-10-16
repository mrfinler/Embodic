"""Every UI test runs in the app's own QApplication: `qt_application` registers the bundled fonts (design_spec.md 4)."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication

from embodic.ui.app import qt_application


@pytest.fixture(scope="session", autouse=True)
def qapp() -> QApplication:
    """Replace pytest-qt's application with the one the app and the screenshot levers start."""
    return qt_application()


@pytest.fixture(autouse=True)
def _delete_closed_widgets(qapp: QApplication):
    """Delete the widgets pytest-qt closed at teardown.

    pytest-qt calls deleteLater() on every widget a test registered and then only processEvents(), which does not
    deliver a deferred delete posted outside an event loop. Without this every shell window of the session stayed
    alive, about 49 MiB and 2650 widgets each, and each new window repolished them all (DEF-U-M6f-01).
    """
    yield
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
