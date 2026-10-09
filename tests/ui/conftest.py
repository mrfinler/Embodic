"""Every UI test renders in the bundled fonts, as the app and the screenshot levers do (design_spec.md section 4)."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication

from embodic.ui.fonts import register_fonts


@pytest.fixture(scope="session", autouse=True)
def _bundled_fonts(qapp: QApplication) -> None:
    register_fonts(QFontDatabase.addApplicationFont, qapp)
