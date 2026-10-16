"""Expected-announcement tables for the Phase 3 Narrator and keyboard walkthroughs (U-S7).

Not a test and not a Windows result. It drives the real shell offscreen with key events only and writes what Qt's
accessibility layer exposes at every Tab stop, which is what the Windows UI Automation bridge hands Narrator
(`inferred` until a Narrator run). It also presses every key of design_spec.md section 10 that the walkthrough uses and
records what changed.

    QT_QPA_PLATFORM=offscreen PYTHONPATH=src:. python docs/phase3/design/checks/keyboard_walk.py OUT.md
"""

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import PySide6
from PySide6.QtCore import QSettings, QStandardPaths, Qt
from PySide6.QtGui import QAccessible, QAction, QShortcut
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QWidget

from embodic.ui.app import QSettingsStore, create_shell, qt_application
from embodic.ui.viewmodels.outcome import OutcomeReady

D08 = "spiral_12c10p_d08"
REGIONS = ("toolstrip", "inspector", "inspector-tabs", "fig-canvas", "results-tabs", "results-rail", "statusbar")
KEY, MOD = Qt.Key, Qt.KeyboardModifier
PROBES = (
    ("F6", KEY.Key_F6, MOD.NoModifier),
    ("Shift+F6", KEY.Key_F6, MOD.ShiftModifier),
    ("Alt+1", KEY.Key_1, MOD.AltModifier),
    ("Alt+4", KEY.Key_4, MOD.AltModifier),
    ("Alt+5", KEY.Key_5, MOD.AltModifier),
    ("Alt+6", KEY.Key_6, MOD.AltModifier),
    ("Ctrl+Shift+T", KEY.Key_T, MOD.ControlModifier | MOD.ShiftModifier),
    ("Ctrl+Shift+N", KEY.Key_N, MOD.ControlModifier | MOD.ShiftModifier),
    ("F5", KEY.Key_F5, MOD.NoModifier),
)


def pump(ms: int = 30) -> None:
    """Let Qt process events for ``ms``."""
    QTest.qWait(ms)


def focus() -> QWidget | None:
    """Return the widget with keyboard focus."""
    return QApplication.focusWidget()


def press(key: Qt.Key, modifier: Qt.KeyboardModifier = MOD.NoModifier) -> None:
    """Send one key to the focused widget, as a keyboard does."""
    target = focus() or QApplication.activeWindow()
    QTest.keyClick(target, key, modifier)
    pump()


def region_of(widget: QWidget | None) -> str:
    """Return the design_spec.md section 5 region that holds ``widget``."""
    while widget is not None:
        if widget.objectName() in REGIONS:
            return widget.objectName()
        widget = widget.parentWidget()
    return "-"


def described(widget: QWidget | None) -> dict[str, str]:
    """Return what QAccessible reports for ``widget``."""
    if widget is None:
        return {"object": "(none)", "class": "", "role": "", "name": "", "description": "", "value": "", "region": "-"}
    face = QAccessible.queryAccessibleInterface(widget)
    role = face.role().name if face is not None else ""
    return {
        "object": widget.objectName() or "(no objectName)",
        "class": type(widget).__name__,
        "role": role,
        "name": face.text(QAccessible.Text.Name) if face else "",
        "description": face.text(QAccessible.Text.Description) if face else "",
        "value": face.text(QAccessible.Text.Value) if face else "",
        "region": region_of(widget),
    }


def tab_chain(limit: int) -> list[dict[str, str]]:
    """Press Tab until the first stop comes back or ``limit`` presses pass; return every stop in order."""
    first, stops = focus(), []
    for _ in range(limit):
        stops.append(described(focus()))
        press(KEY.Key_Tab)
        if focus() is first:
            break
    return stops


def snapshot(window) -> tuple:
    """Return the state a key may change: focus, tabs, theme and modal dialog."""
    modal = QApplication.activeModalWidget()
    return (
        region_of(focus()),
        focus().objectName() if focus() else "",
        window.inspector_tabs.currentWidget().objectName(),
        window.results_tabs.currentWidget().objectName(),
        window.appearance.theme.value.value,
        modal.objectName() if modal else "",
    )


def probe_keys(window) -> list[tuple[str, tuple, tuple]]:
    """Press each probe key and return the state before and after."""
    rows = []
    for label, key, modifier in PROBES:
        window.activateWindow()
        pump()
        before = snapshot(window)
        press(key, modifier)
        pump(300)
        after = snapshot(window)
        modal = QApplication.activeModalWidget()
        if modal is not None:
            modal.close()
            pump()
        rows.append((label, before, after))
    return rows


def wait_ready(window, timeout_ms: int = 60_000) -> None:
    """Wait for the computed outcome."""
    waited = 0
    while not isinstance(window.outcome.state.value, OutcomeReady) and waited < timeout_ms:
        pump(50)
        waited += 50
    assert isinstance(window.outcome.state.value, OutcomeReady), "D08 did not compute"


def open_d08_by_keyboard(window) -> None:
    """Open D08 as AX-02 does: Tab to Examples, Space, Down to D08, Enter."""
    for _ in range(200):
        if focus() is not None and focus().objectName() == "btn-empty-examples":
            break
        press(KEY.Key_Tab)
    assert focus().objectName() == "btn-empty-examples", "Tab does not reach btn-empty-examples"
    press(KEY.Key_Space)
    pump(200)
    gallery = focus()
    ids = [gallery.item(r).data(Qt.ItemDataRole.UserRole) for r in range(gallery.count())]
    for _ in range(ids.index(D08)):
        press(KEY.Key_Down)
    press(KEY.Key_Return)
    wait_ready(window)
    window.activateWindow()
    pump(200)


def cell(text: str) -> str:
    """Escape ``text`` for one Markdown table cell."""
    return text.replace("|", "\\|").replace("\n", " / ").replace("\u00a0", "&#160;")[:140]


def table(stops: list[dict[str, str]]) -> list[str]:
    """Return the Markdown table of a Tab chain."""
    head = ["#", "region", "objectName", "class", "role", "name", "description", "value"]
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for n, stop in enumerate(stops, 1):
        keys = ("region", "object", "class", "role", "name", "description", "value")
        values = [str(n)] + [cell(stop[k]) for k in keys]
        lines.append("| " + " | ".join(values) + " |")
    return lines


def shortcut_rows(window) -> list[str]:
    """Return the Markdown table of every key sequence bound in the window."""
    rows = set()
    for action in window.findChildren(QAction):
        for sequence in action.shortcuts():
            rows.add((sequence.toString(), action.objectName() or action.text(), "QAction"))
    for shortcut in window.findChildren(QShortcut):
        owner = shortcut.parent().objectName() or type(shortcut.parent()).__name__
        rows.add((shortcut.key().toString(), owner, "QShortcut"))
    lines = ["| keys | owner | kind |", "|---|---|---|"]
    lines += [f"| {cell(k)} | {cell(o)} | {kind} |" for k, o, kind in sorted(rows) if k]
    return lines


def main(out: Path) -> None:
    """Walk the start state and D08, probe the keys, and write ``out``."""
    QStandardPaths.setTestModeEnabled(True)
    app = qt_application()
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        store = QSettingsStore(QSettings(str(root / "settings.ini"), QSettings.Format.IniFormat))
        from embodic.ui.views.main_window import ShellPaths

        shell = create_shell(store, ShellPaths(recovery_dir=root / "recovery"), prefers_dark=lambda: False)
        window = shell.window
        window.resize(1280, 800)
        window.show()
        window.activateWindow()
        QTest.qWaitForWindowExposed(window)
        pump(200)
        start = tab_chain(80)
        open_d08_by_keyboard(window)
        d08 = tab_chain(400)
        keys = probe_keys(window)
        shortcuts = shortcut_rows(window)
        window.close()
        pump()
    lines = [
        "# Keyboard walk, offscreen (generated by keyboard_walk.py; do not edit)",
        "",
        f"PySide6 {PySide6.__version__}, platform {app.platformName()}, 1280 x 800, light theme.",
        "Status of every row: `verified` on this platform, `not tested` on Windows.",
        "The name, description and value columns are what QAccessible reports.",
        "",
        f"## Tab chain at start ({len(start)} stops)",
        "",
        *table(start),
        "",
        f"## Tab chain with D08 loaded through the gallery ({len(d08)} stops)",
        "",
        *table(d08),
        "",
        "## Key probes with D08 loaded",
        "",
        "Each cell is (focus region, focus objectName, inspector tab, results tab, theme, modal dialog).",
        "",
        "| keys | before | after | changed |",
        "|---|---|---|---|",
        *[f"| {k} | {cell(str(b))} | {cell(str(a))} | {'yes' if a != b else 'no'} |" for k, b, a in keys],
        "",
        "## Shortcuts registered in the window",
        "",
        *shortcuts,
        "",
    ]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"start {len(start)} stops, d08 {len(d08)} stops, {len(keys)} key probes -> {out}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
