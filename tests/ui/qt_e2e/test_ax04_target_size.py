"""AX-04: every visible interactive widget has a clickable area of at least 24 x 24 px (WCAG 2.2 SC 2.5.8, REQ-N-13).

A check box or radio button is measured by its click rectangle, indicator and label together, which must reach 32 px
(phase 1 design review item 13; design_spec.md section "Control height 32 px. Hit targets 24 x 24 px or more").
The screens walked: the empty session, D08 with each inspector tab, each results tab and each toolstrip tab, and the
New design, Examples and Export dialogs, at 1280 x 800.
"""

from dataclasses import dataclass

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractButton,
    QAbstractItemView,
    QAbstractScrollArea,
    QAbstractSlider,
    QCheckBox,
    QFrame,
    QLabel,
    QRadioButton,
    QStyle,
    QStyleOptionButton,
    QTabBar,
    QTabWidget,
    QWidget,
)

from embodic.ui.viewmodels.export import PRESETS

WIDGET_MIN_PX = 24
CHECK_LABEL_MIN_PX = 32
D08 = "spiral_12c10p_d08"


@dataclass(frozen=True)
class Target:
    """One clickable area and the size it must reach."""

    screen: str
    name: str
    kind: str
    width: int
    height: int
    needed: int

    @property
    def undersized(self) -> bool:
        """Return True when the smaller side is below the size this target needs."""
        return min(self.width, self.height) < self.needed


# Open defects found by this test on 2026-10-11 (U-M4e-2); the views and the QSS template are outside its scope.
KNOWN_UNDERSIZED = {
    "EqChip": "DEF-M4e2-01: EQ chips are 22 px tall (status_badge.py)",
    "AssumptionTag": "DEF-M4e2-01: assumption tags are 22 px tall (status_badge.py)",
    "QCheckBox": "DEF-M4e2-02: check box click rectangles are 20 px tall (results filters, layer toggles, exports)",
    "QScrollBar": "DEF-M4e2-03: scroll bars are 12 px wide (theme_template.qss); WCAG's spacing exception is unruled",
}


def _check_rect(box: QCheckBox | QRadioButton) -> tuple[int, int]:
    option = QStyleOptionButton()
    box.initStyleOption(option)
    element = (
        QStyle.SubElement.SE_CheckBoxClickRect
        if isinstance(box, QCheckBox)
        else QStyle.SubElement.SE_RadioButtonClickRect
    )
    rect = box.style().subElementRect(element, option, box)
    return rect.width(), rect.height()


def _is_target(widget: QWidget) -> bool:
    if isinstance(widget, (QAbstractButton, QTabBar, QAbstractSlider)):
        return True
    if isinstance(widget, QLabel):  # a chip that opens something takes Tab focus; selectable text is no target
        selectable = widget.textInteractionFlags() & Qt.TextInteractionFlag.TextSelectableByMouse
        return bool(widget.focusPolicy() & Qt.FocusPolicy.TabFocus) and not selectable
    if isinstance(widget, (QAbstractItemView, QAbstractScrollArea, QFrame)) or type(widget) is QWidget:
        return False  # containers are not click targets
    return widget.focusPolicy() != Qt.FocusPolicy.NoFocus


def targets(screen: str, root: QWidget) -> list[Target]:
    """Return the clickable areas of every visible, enabled interactive widget under ``root``."""
    found = []
    for widget in [root, *root.findChildren(QWidget)]:
        if not widget.isVisible() or not widget.isEnabled() or not _is_target(widget):
            continue
        kind, name = type(widget).__name__, widget.objectName() or type(widget).__name__
        if isinstance(widget, (QCheckBox, QRadioButton)):
            found.append(Target(screen, name, kind, *_check_rect(widget), CHECK_LABEL_MIN_PX))
        elif isinstance(widget, QTabBar):
            for i in range(widget.count()):
                rect = widget.tabRect(i)
                found.append(Target(screen, f"{name}[{i}]", "tab", rect.width(), rect.height(), WIDGET_MIN_PX))
        else:
            found.append(Target(screen, name, kind, widget.width(), widget.height(), WIDGET_MIN_PX))
    return found


def walk_screens(window, wait_drawn, qtbot) -> list[Target]:
    """Show each screen of the module docstring and return every target on it."""
    found = targets("empty", window)
    window.session.load_example(D08)
    wait_drawn(window)
    for tab_id, panel in window.panels.items():
        window.inspector_tabs.setCurrentWidget(panel)
        qtbot.wait(10)
        found += targets(tab_id, window)
    results = window.findChild(QTabWidget, "results-tabs")
    for i in range(results.count()):
        results.setCurrentIndex(i)
        qtbot.wait(10)
        found += targets(results.widget(i).objectName(), window)
    for i in range(window.toolstrip.tabs.count()):
        window.toolstrip.tabs.setCurrentIndex(i)
        qtbot.wait(10)
        found += targets(f"toolstrip-tab-{i}", window)
    for make in (window.new_design_dialog, window.examples_gallery):
        dialog = make()
        dialog.show()
        qtbot.waitExposed(dialog)
        found += targets(dialog.objectName(), dialog)
        dialog.close()
    window.show_export(next(iter(PRESETS)))
    qtbot.waitExposed(window.export_dialog)
    found += targets("dlg-export", window.export_dialog)
    window.export_dialog.close()
    return found


@pytest.mark.req("REQ-N-13")
def test_ax04_every_interactive_widget_outside_the_open_defects_reaches_24_px_and_check_labels_32_px(
    window, wait_drawn, qtbot
):
    """Catches a new undersized button, field, combo or tab; the open defects are the strict xfail below."""
    found = walk_screens(window, wait_drawn, qtbot)
    assert len(found) > 150, "the walk reached the screens"
    assert [t for t in found if t.undersized and t.kind not in KNOWN_UNDERSIZED] == []


@pytest.mark.req("REQ-N-13")
@pytest.mark.parametrize("kind", sorted(KNOWN_UNDERSIZED))
def test_ax04_open_target_size_defects(kind, window, wait_drawn, qtbot, request):
    """Fails while the defect stands; the strict mark makes the fix remove it."""
    request.applymarker(pytest.mark.xfail(strict=True, reason=KNOWN_UNDERSIZED[kind]))
    found = walk_screens(window, wait_drawn, qtbot)
    assert [t for t in found if t.kind == kind and t.undersized] == []
