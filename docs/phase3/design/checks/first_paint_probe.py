r"""DEF-U-M5h-01 probe (U-S7): how long the window stalls after an example opens, with the real compute.

A check, not a fix. It opens an example the way the gallery does (`session.load_example`), runs a 10 ms GUI timer
from 1 s before the open to 1.5 s after the result, and prints one JSON line: the first paint after the open, the time
to the computed result, and the largest gap between timer ticks (the time the GUI could not answer input). REQ-N-02
names 100 ms for input echo (`assumption` threshold). Run on a real display without QT_QPA_PLATFORM:

    .venv\Scripts\python docs\phase3\design\checks\first_paint_probe.py spiral_12c10p_d08
"""

import json
import sys
import tempfile
import time
from itertools import pairwise
from pathlib import Path

from PySide6.QtCore import QEvent, QObject, QSettings, QStandardPaths, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QWidget

from embodic.ui.app import QSettingsStore, create_shell, qt_application
from embodic.ui.viewmodels.outcome import OutcomeReady
from embodic.ui.views.main_window import ShellPaths


class PaintClock(QObject):
    """Record the time of every paint event of one window."""

    def __init__(self, window: QWidget) -> None:
        super().__init__()
        self.window, self.paints = window, []

    def eventFilter(self, watched, event) -> bool:  # noqa: N802 (Qt override)
        """Note a paint of the watched window and pass every event on."""
        if event.type() == QEvent.Type.Paint and isinstance(watched, QWidget) and watched.window() is self.window:
            self.paints.append(time.perf_counter())
        return False


def main(stem: str) -> None:
    """Open ``stem`` in a shown shell and print the timing JSON line."""
    QStandardPaths.setTestModeEnabled(True)
    app = qt_application()
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        store = QSettingsStore(QSettings(str(root / "settings.ini"), QSettings.Format.IniFormat))
        window = create_shell(store, ShellPaths(recovery_dir=root / "recovery"), prefers_dark=lambda: False).window
        window.resize(1280, 800)
        window.show()
        QTest.qWaitForWindowExposed(window)
        QTest.qWait(500)
        ticks: list[float] = []
        timer = QTimer()
        timer.setInterval(10)
        timer.timeout.connect(lambda: ticks.append(time.perf_counter()))
        timer.start()
        QTest.qWait(1000)
        clock = PaintClock(window)
        app.installEventFilter(clock)
        opened = time.perf_counter()
        window.session.load_example(stem)
        returned = time.perf_counter()
        while not isinstance(window.outcome.state.value, OutcomeReady) and time.perf_counter() - opened < 60:
            QTest.qWait(5)
        ready = time.perf_counter()
        QTest.qWait(1500)
        timer.stop()
        app.removeEventFilter(clock)
        window.close()

    def gap(after: float, before: float) -> tuple[float, float]:
        pairs = [(b - a, a) for a, b in pairwise(ticks) if after <= a and b <= before]
        size, start = max(pairs)
        return round(size * 1000, 1), round((start - opened) * 1000, 1)

    idle_gap, _ = gap(ticks[0], opened)
    open_gap, open_gap_at = gap(ticks[max(i for i, t in enumerate(ticks) if t <= opened)], ready + 1.5)
    first_paint = next((p for p in clock.paints if p > returned), None)
    print(
        json.dumps(
            {
                "example": stem,
                "platform": app.platformName(),
                "device_pixel_ratio": window.devicePixelRatioF(),
                "load_example_returns_ms": round((returned - opened) * 1000, 1),
                "first_paint_after_open_ms": round((first_paint - opened) * 1000, 1) if first_paint else None,
                "result_ready_ms": round((ready - opened) * 1000, 1),
                "largest_tick_gap_idle_ms": idle_gap,
                "largest_tick_gap_after_open_ms": open_gap,
                "largest_gap_starts_ms_after_open": open_gap_at,
                "req_n_02_echo_bound_ms": 100,
            }
        )
    )


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "spiral_12c10p_d08")
