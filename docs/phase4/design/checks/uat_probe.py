"""Record what the embodic window shows at each step of uat_walkthrough.md, offscreen, as JSON.

The walkthrough quotes only text that this dump or the source holds (uat_quote_check.py checks it). Run from the
repository root:

    PYTHONPATH=src QT_QPA_PLATFORM=offscreen <venv python> docs/phase4/design/checks/uat_probe.py OUT.json

It starts its own window with a scratch settings file and scratch folders, so it reads and writes nothing of the
user's. It drives the window through its widgets and actions; it loads the five examples through the session, which
is what the Examples gallery does on Load example.
"""

import json
import sys
import tempfile
import time
from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QShortcut
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QAbstractButton,
    QAbstractItemView,
    QApplication,
    QComboBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QTabBar,
    QToolButton,
    QWidget,
)

import embodic
from embodic.ui.app import QSettingsStore, create_shell, qt_application
from embodic.ui.toolstrip import TOOLSTRIP, ToolstripTab
from embodic.ui.viewmodels.outcome import OutcomeReady
from embodic.ui.views.main_window import MainWindow, ShellPaths

EXAMPLES = (
    "spiral_12c16p_default",
    "spiral_12c14p",
    "spiral_12c10p_d08",
    "serpentine_16p_example",
    "wave_16p_example",
)
COMPUTE_TIMEOUT_S = 180.0
PREVIEW_WAIT_MS = 700  # the 300 ms preview timer plus a D08 compute
TABLE_ROWS = 6


def settle(ms: int = 50) -> None:
    QTest.qWait(ms)


def wait_until(predicate, timeout_s: float = COMPUTE_TIMEOUT_S) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        QApplication.processEvents()
        if predicate():
            return True
        time.sleep(0.02)
    return False


def item_view(view: QAbstractItemView) -> dict:
    model = view.model()
    if model is None:
        return {}
    headers = [model.headerData(c, Qt.Orientation.Horizontal) for c in range(model.columnCount())]
    rows = [
        [model.index(r, c).data() for c in range(model.columnCount())]
        for r in range(min(model.rowCount(), TABLE_ROWS))
    ]
    children = []
    for r in range(model.rowCount()):
        parent = model.index(r, 0)
        children.append([model.index(k, 0, parent).data() for k in range(min(model.rowCount(parent), TABLE_ROWS))])
    return {"headers": headers, "rows": rows, "row_count": model.rowCount(), "children": children}


def describe(widget: QWidget) -> dict:
    row: dict = {}
    if isinstance(widget, (QLabel, QAbstractButton, QLineEdit)):
        row["text"] = widget.text()
    if isinstance(widget, QAbstractButton) and widget.isCheckable():
        row["checked"] = widget.isChecked()
    if isinstance(widget, QAbstractButton):
        row["enabled"] = widget.isEnabled()
    if isinstance(widget, QLineEdit):
        row["placeholder"] = widget.placeholderText()
    if isinstance(widget, QComboBox):
        row["items"] = [widget.itemText(i) for i in range(widget.count())]
        row["current"] = widget.currentText()
    if isinstance(widget, QTabBar):
        row["tabs"] = [widget.tabText(i) for i in range(widget.count())]
        row["current"] = widget.tabText(widget.currentIndex())
    if isinstance(widget, QListWidget):
        row["items"] = [
            widget.item(i).text() or widget.item(i).data(Qt.ItemDataRole.AccessibleTextRole)
            for i in range(widget.count())
        ]
    elif isinstance(widget, QAbstractItemView):
        row.update(item_view(widget))
    if widget.isWindow():
        row["window_title"] = widget.windowTitle()
    row["accessible_name"] = widget.accessibleName()
    row["accessible_description"] = widget.accessibleDescription()
    row["tooltip"] = widget.toolTip()
    kept = {k: v for k, v in row.items() if v not in ("", None, [], {})}
    if not kept:
        return {}
    return {"name": widget.objectName(), "class": type(widget).__name__, **kept}


def snapshot(root: QWidget) -> list[dict]:
    rows = []
    for widget in (root, *root.findChildren(QWidget)):
        if widget.isVisible() and (row := describe(widget)):
            rows.append(row)
    return rows


def named(root: QWidget, name: str, kind: type[QWidget] = QWidget) -> QWidget:
    widget = root.findChild(kind, name)
    assert widget is not None, name
    return widget


def field(window: MainWindow, name: str) -> QLineEdit:
    for panel in window.panels.values():
        edit = panel.findChild(QLineEdit, name)
        if edit is not None:
            window.inspector_tabs.setCurrentWidget(panel)
            panel.ensureWidgetVisible(edit)
            return edit
    raise AssertionError(name)


def type_into(window: MainWindow, name: str, value: str, *, commit: bool = True) -> QLineEdit:
    edit = field(window, name)
    edit.setFocus()
    edit.selectAll()
    QTest.keyClicks(edit, value)
    if commit:
        QTest.keyClick(edit, Qt.Key.Key_Return)
    return edit


def choose(window: MainWindow, name: str, item: str) -> None:
    for panel in window.panels.values():
        combo = panel.findChild(QComboBox, name)
        if combo is not None:
            window.inspector_tabs.setCurrentWidget(panel)
            index = combo.findText(item)
            assert index >= 0, (name, item)
            combo.setCurrentIndex(index)
            combo.activated.emit(index)
            return
    raise AssertionError(name)


def text_of(root: QWidget, name: str) -> str:
    widget = root.findChild(QWidget, name)
    if widget is None:
        return "<absent>"
    if not widget.isVisible():
        return "<hidden>"
    return widget.text() if hasattr(widget, "text") else "<no text>"


def computed(window: MainWindow) -> bool:
    return isinstance(window.outcome.state.value, OutcomeReady)


def toolstrip(window: MainWindow) -> dict:
    tabs = named(window, "toolstrip-tabs", QTabBar)
    out = {"tabs": [tabs.tabText(i) for i in range(tabs.count())], "buttons": {}}
    for index, tab in enumerate(ToolstripTab):
        tabs.setCurrentIndex(index)
        settle()
        for row in TOOLSTRIP:
            if row.tab is tab:
                button = named(window, row.id, QToolButton)
                out["buttons"][row.id] = {
                    "tab": tabs.tabText(index),
                    "text": button.text(),
                    "tooltip": button.toolTip(),
                    "enabled": button.isEnabled(),
                    "visible": button.isVisible(),
                    "shortcut": row.shortcut,
                }
    tabs.setCurrentIndex(0)
    return out


def example_state(window: MainWindow) -> dict:
    canvas = window.canvas
    state = {
        "window_title": window.windowTitle(),
        "legend": canvas._legend_texts(),
        "canvas_accessible_name": canvas.accessibleName(),
        "status_bar": {n: text_of(window, n) for n in ("st-compute", "st-drc", "st-counts", "st-units", "st-cursor")},
    }
    window.show_results_tab("tab-results")
    settle(200)
    state["results_tab"] = [r for r in snapshot(window) if r["name"].startswith(("res-", "results-", "sum-", "rail-"))]
    window.show_results_tab("tab-drc")
    settle(200)
    state["drc_tab"] = [r for r in snapshot(window) if r["name"].startswith("drc-")]
    state["layer_toggles"] = [r for r in snapshot(window) if r["name"].startswith("layer-")]
    state["board"] = [r for r in snapshot(window) if r["name"] in ("board-picker", "ts-section-board")]
    window.show_results_tab("tab-results")
    return state


def open_dialog(window: MainWindow, opener) -> QWidget:
    opener()
    settle(200)
    dialog = QApplication.activeModalWidget()
    assert dialog is not None
    return dialog


def run(out_path: Path) -> int:
    app = qt_application()
    scratch = Path(tempfile.mkdtemp(prefix="uat_probe_"))
    settings = QSettings(str(scratch / "settings.ini"), QSettings.Format.IniFormat)
    shell = create_shell(QSettingsStore(settings), ShellPaths(recovery_dir=scratch / "recovery"), prefers_dark=lambda: False)
    window = shell.window
    window.resize(1280, 800)
    window.show()
    window.activateWindow()
    settle(300)
    dump: dict = {"embodic_version": embodic.__version__, "scratch": "<temp>"}
    dump["start"] = snapshot(window)
    dump["toolstrip"] = toolstrip(window)

    dialog = open_dialog(window, window.show_new_design)
    dump["new_design_dialog"] = snapshot(dialog)
    name = named(dialog, "param-design-name", QLineEdit)
    QTest.keyClicks(name, "UAT blank spiral")
    QTest.mouseClick(named(dialog, "param-topology-spiral", QAbstractButton), Qt.MouseButton.LeftButton)
    settle()
    dump["new_design_dialog_filled"] = snapshot(dialog)
    QTest.mouseClick(named(dialog, "btn-create-design", QAbstractButton), Qt.MouseButton.LeftButton)
    settle(300)
    window.activateWindow()
    settle(100)
    dump["blank_spiral"] = snapshot(window)
    QTest.mouseClick(named(window, "btn-first-missing", QAbstractButton), Qt.MouseButton.LeftButton)
    settle(200)
    focus = QApplication.focusWidget()
    dump["blank_first_missing_focus"] = focus.objectName() if focus else None
    choose(window, "param-layer-count", "4")
    type_into(window, "param-copper-weight", "1")
    type_into(window, "param-board-thickness", "1.6")
    settle(300)
    dump["stackup_helper"] = [
        r for r in snapshot(window) if r["name"].startswith(("layer-", "pair-", "new-required", "param-board", "param-copper"))
    ]
    window.inspector_tabs.setCurrentWidget(window.panels["tab-layers"])
    settle(200)
    dump["stackup_helper_layers_tab"] = [
        r for r in snapshot(window) if r["name"].startswith(("layer-", "pair-", "param-layer", "param-rotation"))
    ]
    type_into(window, "param-board-thickness", "0.1")
    settle(300)
    dump["stackup_helper_thin_board"] = [r for r in snapshot(window) if r["name"].startswith("param-board-thickness")]
    type_into(window, "param-board-thickness", "1.6")
    settle(300)

    gallery = open_dialog(window, window.show_examples)
    dump["examples_gallery"] = snapshot(gallery)
    gallery.reject()
    settle()

    dump["examples"] = {}
    for example_id in EXAMPLES:
        window.session.load_example(example_id)
        ok = wait_until(lambda: computed(window))
        settle(500)
        window.canvas.fit_view()
        settle(200)
        dump["examples"][example_id] = {"computed": ok, **example_state(window)}
        if example_id == "spiral_12c10p_d08":
            dump["d08_inputs"] = {
                tab: [r for r in panel_rows(window, tab) if r["name"].startswith("param-")]
                for tab in ("tab-coil", "tab-board")
            }
            dump["d08_how"] = how_steps(window)
            dump["d08_charts"] = chart_steps(window)
            dump["d08_preview"] = preview_steps(window)
            dump["d08_after_preview_rail"] = [r for r in snapshot(window) if r["name"].startswith(("sum-", "rail-"))]
            dump["export_d08"] = export_steps(window, scratch / "export_d08", "export_bundle")
            dump["guide"] = [r for r in snapshot(open_guide(window)) if r["name"].startswith("guide")]
            window.guide.close()
            dump["tests_dialog"] = tests_dialog(window)
        if example_id == "wave_16p_example":
            dump["export_wave"] = export_steps(window, scratch / "export_wave", "export_svg")
            window.show_results_tab("tab-torque-speed")
            settle(300)
            dump["wave_torque_speed"] = [r for r in snapshot(window) if r["name"].startswith("chart")]
            window.show_results_tab("tab-results")
    dump["bound_keys"] = sorted(
        {s.key().toString() for s in window.findChildren(QShortcut)}
        | {a.shortcut().toString() for a in window.actions() if not a.shortcut().isEmpty()}
    )

    theme = window.toolstrip.actions_by_id["act-theme"]
    seen = [window.appearance.theme.value.value]
    for _ in range(3):
        theme.trigger()
        settle()
        seen.append(window.appearance.theme.value.value)
    dump["theme_cycle"] = {"label": theme.text(), "tooltip": theme.toolTip(), "choices": seen}
    greyscale = window.toolstrip.actions_by_id["act-greyscale"]
    window._prefers_high_contrast = lambda: True  # offscreen Qt reports no contrast theme; this is the test seam
    window.on_os_contrast_changed()
    settle(300)
    dump["high_contrast"] = {
        "greyscale_checked": greyscale.isChecked(),
        "greyscale_enabled": greyscale.isEnabled(),
        "greyscale_tooltip": greyscale.toolTip(),
        "legend": window.canvas._legend_texts(),
    }
    out_path.write_text(json.dumps(dump, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    window.close()
    settle()
    return 0 if all(e["computed"] for e in dump["examples"].values()) else 1


def preview_steps(window: MainWindow) -> dict:
    steps = {}
    value = lambda: text_of(window, "res-r-phase-value")  # noqa: E731
    chip = lambda: text_of(window, "param-r-inner-prov")  # noqa: E731
    edit = field(window, "param-r-inner")
    steps["committed"] = {"field": edit.text(), "chip": chip(), "r_phase": value()}
    type_into(window, "param-r-inner", "11.8", commit=False)
    QTest.qWait(PREVIEW_WAIT_MS)
    wait_until(lambda: computed(window))
    settle(300)
    steps["typed_no_enter"] = {"field": edit.text(), "chip": chip(), "r_phase": value()}
    QTest.keyClick(edit, Qt.Key.Key_Escape)
    wait_until(lambda: computed(window))
    settle(500)
    steps["after_esc"] = {"field": edit.text(), "chip": chip(), "r_phase": value()}
    QTest.keyClick(edit, Qt.Key.Key_Up)
    steps["after_up"] = {"field": edit.text()}
    QTest.keyClick(edit, Qt.Key.Key_Up, Qt.KeyboardModifier.ShiftModifier)
    steps["after_shift_up"] = {"field": edit.text()}
    QTest.keyClick(edit, Qt.Key.Key_Return)
    wait_until(lambda: computed(window))
    settle(500)
    steps["after_enter"] = {"field": edit.text(), "chip": chip(), "r_phase": value()}
    window.toolstrip.actions_by_id["act-undo"].trigger()
    wait_until(lambda: computed(window))
    settle(500)
    steps["after_undo"] = {"field": edit.text(), "chip": chip(), "r_phase": value()}
    return steps


def panel_rows(window: MainWindow, tab: str) -> list[dict]:
    window.inspector_tabs.setCurrentWidget(window.panels[tab])
    settle(200)
    return snapshot(window.panels[tab])


def how_steps(window: MainWindow) -> dict:
    window.show_results_tab("tab-results")
    settle(200)
    toggle = named(window, "res-r-phase-how-toggle", QAbstractButton)
    QTest.mouseClick(toggle, Qt.MouseButton.LeftButton)
    settle(300)
    how = named(window, "res-r-phase-how")
    rows = snapshot(how)
    QTest.mouseClick(toggle, Qt.MouseButton.LeftButton)
    window.show_equations("EQ-10")
    settle(300)
    body = named(window.guide, "guide-body")
    guide = {"title": window.guide.windowTitle(), "body_start": body.toPlainText()[:600]}
    window.guide.close()
    return {"how": rows, "guide_eq10": guide}


def chart_steps(window: MainWindow) -> dict:
    out = {}
    for tab in ("tab-back-emf", "tab-torque-speed", "tab-compare"):
        window.show_results_tab(tab)
        settle(300)
        out[tab] = [r for r in snapshot(window) if r["name"].startswith(("chart", "compare", "btn-set", tab))]
    window.show_results_tab("tab-results")
    return out


def export_steps(window: MainWindow, folder: Path, command: str) -> dict:
    window.show_export(command)
    settle(300)
    dialog = window.export_dialog
    steps = {"dialog": snapshot(dialog)}
    folder_field = named(dialog, "export-folder", QLineEdit)
    folder_field.setText(str(folder))
    QTest.mouseClick(named(dialog, "btn-export-run", QAbstractButton), Qt.MouseButton.LeftButton)
    settle(300)
    confirm = QApplication.activeModalWidget()
    if confirm is not None and confirm is not dialog and confirm.objectName() == "dlg-export-confirm":
        steps["confirm"] = snapshot(confirm)
        QTest.mouseClick(named(confirm, "btn-export-confirm-cancel", QAbstractButton), Qt.MouseButton.LeftButton)
        settle(200)
    else:
        wait_until(lambda: text_of(dialog, "export-result") not in ("", "<hidden>", "<absent>"), 60)
        settle(300)
        steps["result"] = text_of(dialog, "export-result").replace(str(folder), "<folder>")
        steps["files"] = sorted(p.name for p in folder.iterdir()) if folder.exists() else []
    dialog.close()
    settle()
    return steps


def open_guide(window: MainWindow) -> QWidget:
    window.show_equations()
    settle(300)
    return window.guide


def tests_dialog(window: MainWindow) -> list[dict]:
    window.show_tests()
    settle(300)
    rows = snapshot(window.tests_dialog)
    window.tests_dialog.close()
    return rows


if __name__ == "__main__":
    sys.exit(run(Path(sys.argv[1])))
