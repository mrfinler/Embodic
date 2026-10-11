"""AX-02, keyboard only (test_plan_draft.md): open, edit 3 inputs, recompute, open EQ details, export SVG.

Every step is a key sent to the widget that has keyboard focus; the test never sends a pointer event. "Open" is the
Examples gallery: the Windows build opens files in the native dialog, which an offscreen run cannot drive.
"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QCheckBox, QDialog, QLineEdit, QListWidget, QPushButton

from embodic.ui.strings import text

from .support import find, press, tab_until

D08 = "spiral_12c10p_d08"
EDITS = (("param-speed", "1234"), ("param-current", "1.7"), ("param-copper-temp", "65"))
Key, Mod = Qt.Key, Qt.KeyboardModifier


def _type(qtbot, value: str) -> None:
    press(qtbot, Key.Key_A, Mod.ControlModifier)
    qtbot.keyClicks(QApplication.focusWidget(), value)


def _back_to(qtbot, window) -> None:
    """Activate the main window after a dialog closes, as the window manager does; offscreen Qt does not."""
    window.activateWindow()
    qtbot.waitActive(window)
    qtbot.waitUntil(lambda: QApplication.focusWidget() is not None)


def _open_inspector_tab(qtbot, window, tab_id: str) -> None:
    tabs = window.inspector_tabs
    tab_until(qtbot, lambda w: w is tabs.tabBar())
    for _ in range(tabs.count()):
        if tabs.currentWidget() is window.panels[tab_id]:
            return
        press(qtbot, Key.Key_Right)
    raise AssertionError(f"arrow keys do not reach {tab_id}")


@pytest.mark.req("REQ-N-12", "REQ-T-01")
def test_ax02_open_edit_three_inputs_recompute_open_eq_details_and_export_svg_with_the_keyboard_only(
    window, wait_drawn, qtbot, tmp_path
):
    """Catches a step of the scenario that needs a pointer: a field, chip or button that Tab and Enter cannot reach."""
    window.activateWindow()
    qtbot.waitActive(window)
    tab_until(qtbot, lambda w: w.objectName() == "btn-empty-examples")
    press(qtbot, Key.Key_Space)
    examples = find(window, "examples-list", QListWidget)
    qtbot.waitUntil(examples.hasFocus)
    ids = [examples.item(r).data(Qt.ItemDataRole.UserRole) for r in range(examples.count())]
    for _ in range(ids.index(D08)):
        press(qtbot, Key.Key_Down)
    press(qtbot, Key.Key_Return)
    wait_drawn(window)
    assert window.session.current_outcome().design.name == "Spiral, 12 coils, 10 poles (D08)"
    _back_to(qtbot, window)

    _open_inspector_tab(qtbot, window, "tab-board")
    for name, value in EDITS:
        tab_until(qtbot, lambda w, name=name: w.objectName() == name)
        _type(qtbot, value)
        press(qtbot, Key.Key_Return)
    press(qtbot, Key.Key_F5)
    wait_drawn(window)
    assert {find(window, f"{name}-prov").text() for name, _ in EDITS} == {text("design.prov.user")}

    window.show_results_tab("tab-results")
    tab_until(qtbot, lambda w: w.objectName() == "res-r-phase-how-toggle")
    press(qtbot, Key.Key_Space)
    assert find(window, "res-r-phase-how").isVisible(), "Space opens How was this computed"
    tab_until(qtbot, lambda w: w.objectName() == "res-r-phase-eq")
    press(qtbot, Key.Key_Return)
    guide = window.findChild(QDialog, "dlg-guide") or window.guide
    assert guide is not None and guide.isVisible() and guide.current_topic() == "EQ-10"
    guide.close()
    _back_to(qtbot, window)

    folder = tmp_path / "export"
    folder.mkdir()
    press(qtbot, Key.Key_E, Mod.ControlModifier)
    dialog = find(window, "dlg-export", QDialog)
    qtbot.waitUntil(lambda: dialog.isAncestorOf(QApplication.focusWidget()) if QApplication.focusWidget() else False)
    boxes = {box.objectName(): box for box in dialog.findChildren(QCheckBox) if box.objectName().startswith("export-")}
    folder_field = find(dialog, "export-folder", QLineEdit)
    for _ in range(3 * len(boxes) + 10):
        focused = QApplication.focusWidget()
        if isinstance(focused, QCheckBox) and focused.isChecked() != (focused.objectName() == "export-format-svg"):
            press(qtbot, Key.Key_Space)
        elif focused is folder_field and focused.text() != str(folder):
            _type(qtbot, str(folder))
        elif focused.objectName() == "btn-export-run" and folder_field.text() == str(folder):
            if [n for n, box in boxes.items() if box.isChecked()] == ["export-format-svg"]:
                break
        press(qtbot, Key.Key_Tab)
    assert QApplication.focusWidget() is find(dialog, "btn-export-run", QPushButton)
    press(qtbot, Key.Key_Space)
    assert [p.suffix for p in folder.iterdir()] == [".svg"]
