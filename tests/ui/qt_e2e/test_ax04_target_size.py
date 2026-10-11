"""AX-04: every visible interactive widget has a clickable area of at least 24 x 24 px (WCAG 2.2 SC 2.5.8, REQ-N-13).

A check box or radio button is measured by the area its ``hitButton`` accepts, which must reach 32 px (UX-AC-28,
m4_review_2.md ruling k2; design_spec.md section "Control height 32 px. Hit targets 24 x 24 px or more").
The screens walked: the empty session, D08 with each inspector tab, each results tab and each toolstrip tab, and the
New design, Examples and Export dialogs, at 1280 x 800.
"""

from dataclasses import dataclass

import pytest
from PySide6.QtCore import QPoint, Qt
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


def _hit_extent(box: QCheckBox | QRadioButton) -> tuple[int, int]:
    """Return how wide and tall the area ``hitButton`` accepts is, on the lines through the style's click rectangle."""
    option = QStyleOptionButton()
    box.initStyleOption(option)
    element = (
        QStyle.SubElement.SE_CheckBoxClickRect
        if isinstance(box, QCheckBox)
        else QStyle.SubElement.SE_RadioButtonClickRect
    )
    centre = box.style().subElementRect(element, option, box).center()
    width = sum(box.hitButton(QPoint(x, centre.y())) for x in range(box.width()))
    height = sum(box.hitButton(QPoint(centre.x(), y)) for y in range(box.height()))
    return width, height


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
            kind = "QCheckBox" if isinstance(widget, QCheckBox) else "QRadioButton"
            found.append(Target(screen, name, kind, *_hit_extent(widget), CHECK_LABEL_MIN_PX))
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
def test_ax04_every_interactive_widget_reaches_24_px_and_check_rows_32_px(window, wait_drawn, qtbot):
    """Catches an undersized button, field, combo, tab, chip or scroll bar, or a check row under 32 px (DEF-M4e2-0x)."""
    found = walk_screens(window, wait_drawn, qtbot)
    assert len(found) > 150, "the walk reached the screens"
    assert {t.kind for t in found} >= {"EqChip", "AssumptionTag", "QCheckBox", "QScrollBar"}, "the walk met each kind"
    assert [t for t in found if t.undersized] == []


@pytest.mark.req("REQ-N-13")
def test_ax04_check_rows_take_a_click_in_their_whole_32_px_rectangle(window, wait_drawn, qtbot):
    """DEF-M4e2-02. Catches a check box on any walked screen that accepts clicks only on its indicator and label."""
    found = walk_screens(window, wait_drawn, qtbot)
    assert [t for t in found if t.kind == "QCheckBox" and t.undersized] == []


@pytest.mark.req("REQ-N-13")
def test_ax04_a_click_anywhere_in_a_check_row_toggles_the_box(window, wait_drawn, qtbot):
    """UX-AC-28: catches a check box that takes a click only on its indicator and label, not the whole 32 px row."""
    window.session.load_example(D08)
    wait_drawn(window)
    box = window.layer_boxes["L1"]
    assert box.height() >= CHECK_LABEL_MIN_PX
    for point in (QPoint(1, 1), QPoint(box.width() - 2, box.height() - 2)):
        before = box.isChecked()
        qtbot.mouseClick(box, Qt.MouseButton.LeftButton, pos=point)
        assert box.isChecked() is not before, point


@pytest.mark.req("REQ-N-13")
def test_ax04_a_click_on_the_label_text_toggles_the_box(window, wait_drawn, qtbot):
    """UX-AC-28: catches a whole-row hit test that loses the label itself, the target users aim at first."""
    window.session.load_example(D08)
    wait_drawn(window)
    box = window.layer_boxes["L1"]
    option = QStyleOptionButton()
    box.initStyleOption(option)
    label = box.style().subElementRect(QStyle.SubElement.SE_CheckBoxContents, option, box)
    assert label.width() > 0 and box.rect().contains(label.center())
    before = box.isChecked()
    qtbot.mouseClick(box, Qt.MouseButton.LeftButton, pos=label.center())
    assert box.isChecked() is not before
