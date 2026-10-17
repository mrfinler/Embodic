"""Lay out D08 at three window sizes under the process's QT_SCALE_FACTOR and print the findings as one JSON line.

Run from the repository root (REQ-N-15, V3-01 gap N-15)::

    QT_QPA_PLATFORM=offscreen QT_SCALE_FACTOR=1.5 python -m tests.ui.qt_e2e.n15_layout_probe

Per size it reports the clipped texts of the independent M4 check, the pairs of visible sibling widgets whose
geometries intersect, and the inspector forms whose horizontal scroll bar can be shown and has a range. "Full screen"
is 1920 x 1080: the offscreen platform has no real screen, and design_spec.md UX-AC-21 names that as its largest size.
"""

import itertools
import json
import sys
import tempfile
import time
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QAbstractScrollArea, QApplication, QWidget

from embodic.ui.app import QSettingsStore, create_shell, qt_application
from embodic.ui.viewmodels.outcome import OutcomeReady
from embodic.ui.viewmodels.session import SessionComputed
from embodic.ui.views.main_window import MainWindow, ShellPaths

# The independent M4 tests import their driver as a top-level module, which pytest's rootdir handling provides.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "independent" / "m4"))
from tests.independent.m4.test_ui_behaviour import clipped_widgets

D08 = "spiral_12c10p_d08"
SIZES = {"960x540": (960, 540), "1280x800": (1280, 800), "full-screen 1920x1080": (1920, 1080)}
SETTLE_S = 60.0


def settle(app: QApplication, window: MainWindow) -> None:
    """Process events until the loaded design's compute result is on screen, then a few more rounds."""
    deadline = time.monotonic() + SETTLE_S
    while time.monotonic() < deadline:
        app.processEvents()
        state = window.session.state.value
        if (
            isinstance(state, SessionComputed)
            and not state.computing
            and isinstance(window.outcome.state.value, OutcomeReady)
        ):
            break
        time.sleep(0.01)
    for _ in range(10):
        app.processEvents()


def overlapping_siblings(window: QWidget) -> list[str]:
    """Return a message per pair of visible child widgets of one parent whose geometries share an area."""
    found = []
    for parent in [window, *window.findChildren(QWidget)]:
        if not parent.isVisible():
            continue
        kids = [c for c in parent.children() if isinstance(c, QWidget) and c.isVisible() and not c.isWindow()]
        for a, b in itertools.combinations(kids, 2):
            shared = a.geometry().intersected(b.geometry())
            if shared.width() > 0 and shared.height() > 0:
                names = [w.objectName() or type(w).__name__ for w in (a, b)]
                where = parent.objectName() or type(parent).__name__
                found.append(f"{where}: {names[0]} x {names[1]} {shared.width()}x{shared.height()}")
    return found


def sideways_forms(window: MainWindow, app: QApplication) -> list[str]:
    """Return a message per inspector form (tab) whose horizontal scroll bar is visible with a range."""
    found = []
    for name, panel in window.panels.items():
        window.inspector_tabs.setCurrentWidget(panel)
        for _ in range(5):
            app.processEvents()
        assert isinstance(panel, QAbstractScrollArea), name
        bar = panel.horizontalScrollBar()
        if bar.isVisibleTo(panel) and bar.maximum() > 0:
            found.append(f"{name}: horizontal scroll bar maximum {bar.maximum()}")
    return found


def main() -> None:
    """Print {"scale": ..., "sizes": {size: {"clipped": [...], "overlaps": [...], "sideways": [...]}}}."""
    app = qt_application()
    folder = Path(tempfile.mkdtemp(prefix="embodic-n15-"))
    store = QSettingsStore(QSettings(str(folder / "settings.ini"), QSettings.Format.IniFormat))
    window = create_shell(store, ShellPaths(recovery_dir=folder / "recovery"), prefers_dark=lambda: False).window
    window.resize(1280, 800)
    window.show()
    window.session.load_example(D08)
    settle(app, window)
    report = {}
    for label, (width, height) in SIZES.items():
        window.resize(width, height)
        settle(app, window)
        report[label] = {
            "clipped": clipped_widgets(window),
            "overlaps": overlapping_siblings(window),
            "sideways": sideways_forms(window, app),
        }
    print(json.dumps({"scale": app.devicePixelRatio(), "sizes": report}))


if __name__ == "__main__":
    main()
