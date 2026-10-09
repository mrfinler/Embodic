"""Registration of the bundled fonts in a real QApplication (design_spec.md section 4)."""

import pytest
from PySide6.QtGui import QFont, QFontDatabase, QFontInfo
from PySide6.QtWidgets import QApplication, QLabel

from embodic.ui.fonts import BODY_PX, INTER, JETBRAINS_MONO, register_fonts

pytestmark = pytest.mark.req("REQ-N-06")  # the bundled files load with no network


@pytest.fixture
def registered(qapp: QApplication):
    """Register the fonts, then give the session's application its own font back."""
    before = QApplication.font()
    register_fonts(QFontDatabase.addApplicationFont, qapp)
    yield qapp
    QApplication.setFont(before)


def test_registration_makes_inter_13px_the_font_widgets_resolve(registered, qtbot) -> None:
    """Catches fonts that load but never reach the widgets (a label would still render in the platform sans)."""
    label = QLabel("Phase resistance 502 mΩ")
    qtbot.addWidget(label)
    info = QFontInfo(label.font())
    assert (info.family(), info.pixelSize()) == (INTER, BODY_PX)


def test_registration_provides_jetbrains_mono_for_the_style_sheet(registered) -> None:
    """Catches a missing mono family: values, units and codes the style sheet sets in it would fall back."""
    assert {INTER, JETBRAINS_MONO} <= set(QFontDatabase.families())
    assert QFontInfo(QFont(JETBRAINS_MONO)).family() == JETBRAINS_MONO


def test_ruling_e2_weight_600_resolves_to_the_bundled_semibold_face(registered) -> None:
    """U-S4e ruling e2. Catches a 600 rule that Qt draws at body weight or as synthetic bold of the Regular file."""
    assert {"Regular", "SemiBold"} <= set(QFontDatabase.styles(INTER))
    heading = QFont(INTER)
    heading.setWeight(QFont.Weight.DemiBold)
    info = QFontInfo(heading)
    assert (info.family(), info.styleName(), info.weight()) == (INTER, "SemiBold", 600)
