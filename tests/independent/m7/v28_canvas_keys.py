"""DEF-US18-01: send each canvas key of design_spec.md section 10 to the D08 canvas and print what it changes (U-V28).

    QT_QPA_PLATFORM=offscreen PYTHONPATH=src python tests/independent/m7/v28_canvas_keys.py

One offscreen main window, built as tests/ui/qt_shell/conftest.py builds it (1280 x 800, a throwaway settings file),
opens the example spiral_12c10p_d08 and waits for its result. For each key the script gives the canvas focus, takes a
snapshot, sends the key with QTest (which runs the shortcut map first, as a keyboard does), lets the events run, waits
for any compute it started, and takes a second snapshot. A snapshot holds the SHA-256 of the canvas viewport's
pixels, the zoom, the scroll position, the scene item count, the compute count, the canvas's board and layer step
signals, the checked actions, the focused widget, the visible windows, the tabs and the outcome state. The script
prints every field that differs, or "no change".

Order. A pass with no key, then the spec's keys on the fitted canvas with every layer shown, then the controls, then
F and F5 on a canvas zoomed 2x. A pass with no key must print no change, so a change is the key's. The keys the canvas
handles (+, 0 after a zoom, Right, ], Page Down) must print a change, so "no change" is a measurement. Exit 1 when a
control fails. Last, a click on the toolstrip's Greyscale button shows that a greyscale switch changes the pixels.

The script then lists the toolstrip's buttons on every toolstrip tab, by object name, text, tooltip and accessible
name, and the window's actions whose text or name holds "setting".
"""

import hashlib
import os
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings, QStandardPaths, Qt
from PySide6.QtGui import QAction, QPalette
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QAbstractButton, QApplication, QTabBar, QWidget

from embodic.api import compute
from embodic.ui.app import QSettingsStore, create_shell
from embodic.ui.viewmodels.outcome import OutcomeReady
from embodic.ui.views.main_window import ShellPaths

D08 = "spiral_12c10p_d08"
K, M = Qt.Key, Qt.KeyboardModifier
SPEC_KEYS = (
    ("L", K.Key_L, M.NoModifier),
    ("G", K.Key_G, M.NoModifier),
    ("C", K.Key_C, M.NoModifier),
    ("M", K.Key_M, M.NoModifier),
    ("T", K.Key_T, M.NoModifier),
    ("A", K.Key_A, M.NoModifier),
    ("B", K.Key_B, M.NoModifier),
    ("Shift+C", K.Key_C, M.ShiftModifier),
    ("Esc", K.Key_Escape, M.NoModifier),
)
UNLISTED_KEYS = (("F", K.Key_F, M.NoModifier), ("F5", K.Key_F5, M.NoModifier))
CONTROLS = (
    ("+", K.Key_Plus, M.NoModifier),
    ("0", K.Key_0, M.NoModifier),
    ("Right", K.Key_Right, M.NoModifier),
    ("]", K.Key_BracketRight, M.NoModifier),
    ("Page Down", K.Key_PageDown, M.NoModifier),
)


def settle(ms: int = 150) -> None:
    """Run the posted events, then wait so that timers and repaints that follow a key have run too."""
    for _ in range(20):
        QApplication.processEvents()
    QTest.qWait(ms)


def wait_ready(window, calls_before: int, calls: list) -> None:
    """Wait until no compute is pending: the count of computes stopped moving and the outcome is ready."""
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        settle(100)
        if isinstance(window.outcome.state.value, OutcomeReady) and len(calls) >= calls_before:
            settle(300)
            if isinstance(window.outcome.state.value, OutcomeReady):
                return
    raise TimeoutError("the outcome did not settle in 60 s")


def snapshot(window, calls: list, emitted: dict[str, int]) -> dict[str, object]:
    """Return what a key could change, as plain values."""
    canvas = window.canvas
    image = canvas.viewport().grab().toImage()
    focus = QApplication.focusWidget()
    return {
        "canvas pixels": hashlib.sha256(bytes(image.constBits())).hexdigest()[:16],
        "zoom": round(canvas.transform().m11(), 6),
        "scroll": (canvas.horizontalScrollBar().value(), canvas.verticalScrollBar().value()),
        "scene items": len(canvas.scene().items()),
        "computes": len(calls),
        "board_step": emitted["board_step"],
        "layer_step": emitted["layer_step"],
        "checked actions": tuple(
            sorted(
                a.objectName() or a.text() for a in window.findChildren(QAction) if a.isCheckable() and a.isChecked()
            )
        ),
        "focus": None if focus is None else (type(focus).__name__, focus.objectName()),
        "visible windows": tuple(
            sorted(f"{type(w).__name__}:{w.objectName()}" for w in QApplication.topLevelWidgets() if w.isVisible())
        ),
        "results tab": window.results_tabs.currentIndex(),
        "inspector tab": window.inspector_tabs.currentIndex(),
        "outcome": type(window.outcome.state.value).__name__,
    }


def press(window, calls: list, emitted: dict[str, int], key: K, modifier: M) -> list[str]:
    """Focus the canvas, send one key, and return the fields that changed as "field: before -> after"."""
    window.canvas.setFocus(Qt.FocusReason.OtherFocusReason)
    settle()
    before = snapshot(window, calls, emitted)
    if key is not None:
        QTest.keyClick(window.canvas, key, modifier)
    settle(300)
    wait_ready(window, before["computes"], calls)
    after = snapshot(window, calls, emitted)
    return [f"{field}: {before[field]} -> {after[field]}" for field in before if before[field] != after[field]]


def toolstrip_buttons(window) -> list[str]:
    """Return one line per toolstrip button on every toolstrip tab, as the tab shows it."""
    tabs = window.findChild(QWidget, "toolstrip-tabs")
    bar = tabs if isinstance(tabs, QTabBar) else (tabs.findChild(QTabBar) if tabs is not None else None)
    toolstrip = window.findChild(QWidget, "toolstrip")
    lines = []
    count = bar.count() if bar is not None else 1
    for index in range(count):
        if bar is not None:
            bar.setCurrentIndex(index)
            settle(50)
        title = bar.tabText(index) if bar is not None else "(one tab)"
        for button in toolstrip.findChildren(QAbstractButton):
            if button.isVisibleTo(window) and button.isVisible():
                lines.append(
                    f"tab {title!r}: {button.objectName()!r} text={button.text()!r} tooltip={button.toolTip()!r} "
                    f"name={button.accessibleName()!r} enabled={button.isEnabled()}"
                )
    return lines


def main() -> int:
    """Run a pass with no key, the spec's keys, the controls, F, F5 and the Greyscale button; list the toolstrip."""
    app = QApplication.instance() or QApplication(sys.argv[:1])
    QStandardPaths.setTestModeEnabled(True)
    work = Path(tempfile.mkdtemp(prefix="v28_keys_"))
    calls: list = []

    def counting(design, provenance, **kwargs):
        calls.append(design)
        return compute(design, provenance, **kwargs)

    store = QSettingsStore(QSettings(str(work / "settings.ini"), QSettings.Format.IniFormat))
    window, worker = create_shell(
        store,
        ShellPaths(recovery_dir=work / "recovery"),
        counting,
        lambda: False,
        prefers_high_contrast=lambda: False,
        system_palette=QPalette,
    )
    window.resize(1280, 800)
    window.show()
    QTest.qWaitForWindowExposed(window)
    window.outcome.open_example(D08)
    wait_ready(window, 1, calls)
    window.activateWindow()
    QTest.qWaitForWindowActive(window)
    emitted = {"board_step": 0, "layer_step": 0}
    window.canvas.board_step.connect(lambda _d: emitted.__setitem__("board_step", emitted["board_step"] + 1))
    window.canvas.layer_step.connect(lambda _d: emitted.__setitem__("layer_step", emitted["layer_step"] + 1))
    print(
        f"D08 open: outcome {type(window.outcome.state.value).__name__}, computes {len(calls)}, "
        f"canvas {window.canvas.viewport().width()} x {window.canvas.viewport().height()} px, "
        f"canvas visible {window.canvas.isVisible()}, window active {window.isActiveWindow()}"
    )

    failures = []
    null = press(window, calls, emitted, None, M.NoModifier)
    print(f"control, no key: {'; '.join(null) or 'no change'}")
    if null:
        failures.append("no key")
    for label, key, modifier in SPEC_KEYS:
        changed = press(window, calls, emitted, key, modifier)
        print(f"spec section 10 {label}: {'; '.join(changed) or 'no change'}")
    for label, key, modifier in CONTROLS:
        changed = press(window, calls, emitted, key, modifier)
        print(f"control {label}: {'; '.join(changed) or 'no change'}")
        if not changed:
            failures.append(label)
    window.canvas.zoom_by(2.0)
    settle()
    print("(canvas zoomed 2x before F, so a fit shows)")
    for label, key, modifier in UNLISTED_KEYS:
        changed = press(window, calls, emitted, key, modifier)
        print(f"bound, not in the map {label}: {'; '.join(changed) or 'no change'}")
    window.canvas.setFocus(Qt.FocusReason.OtherFocusReason)
    settle()
    before = snapshot(window, calls, emitted)
    window.findChild(QAbstractButton, "act-greyscale").click()
    settle(300)
    after = snapshot(window, calls, emitted)
    changed = [f"{field}: {before[field]} -> {after[field]}" for field in before if before[field] != after[field]]
    print(f"toolstrip Greyscale button (what G names), clicked: {'; '.join(changed) or 'no change'}")

    print("toolstrip buttons:")
    for line in toolstrip_buttons(window):
        print(f"  {line}")
    settings = [
        f"{a.objectName()!r} text={a.text()!r} shortcut={a.shortcut().toString()!r} visible={a.isVisible()}"
        for a in window.findChildren(QAction)
        if "setting" in (a.text() + a.objectName() + a.toolTip()).lower()
    ]
    print(f"actions naming settings: {settings or 'none'}")
    worker.shutdown()
    app.closeAllWindows()
    if failures:
        print(f"CONTROL FAILED: {failures}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
