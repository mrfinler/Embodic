"""Every UI test runs in the app's own QApplication: `qt_application` registers the bundled fonts (design_spec.md 4)."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from embodic.ui.app import qt_application


@pytest.fixture(scope="session", autouse=True)
def qapp() -> QApplication:
    """Replace pytest-qt's application with the one the app and the screenshot levers start."""
    return qt_application()
