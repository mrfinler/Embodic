r"""DEF-U-M5h-01 lever (U-M6a): where the GUI thread spends a stall when an example opens and its result arrives.

Opens an example as the gallery does, with the real compute, and prints:

- the largest gaps between 10 ms timer ticks, each with the GUI thread's CPU time inside it (``time.thread_time``):
  CPU close to the gap is GUI-thread work, CPU near zero is the GUI thread waiting (GIL or OS scheduler);
- the worker's compute span, wall and CPU;
- the wall-clock call tree of the shell's view entry points on the GUI thread, every span of 3 ms or more.

Not a test. Run offscreen or on a display:

    QT_QPA_PLATFORM=offscreen PYTHONPATH=src python tests/ui/qt_shell/stall_breakdown.py spiral_12c10p_d08
"""

import functools
import sys
import tempfile
import threading
import time
from itertools import pairwise
from pathlib import Path

from PySide6.QtCore import QEventLoop, QSettings, QStandardPaths, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QGraphicsView

from embodic.api import compute
from embodic.ui.app import QSettingsStore, create_shell, qt_application
from embodic.ui.viewmodels import results as results_vm
from embodic.ui.viewmodels import session as session_vm
from embodic.ui.viewmodels.outcome import OutcomeReady, OutcomeViewModel
from embodic.ui.views import charts, checks_view, coil_panel, geometry_view, main_window, results_rail, results_view
from embodic.ui.views.main_window import ShellPaths

GUI_THREAD = threading.main_thread().ident
SPAN_MIN_MS = 3.0
SPANS: list[tuple[int, float, float, str]] = []
DEPTH = [0]

TIMED = (
    (session_vm.DesignSession, ("load_example", "_refresh", "_autosave", "_on_outcome")),
    (OutcomeViewModel, ("on_finished",)),
    (main_window.MainWindow, ("_on_session", "_render", "_render_results", "_show_issues")),
    (coil_panel.FieldPanel, ("refresh", "_rebuild")),
    (results_vm.ResultsViewModel, ("show",)),
    (results_view.ResultsTab, ("refresh", "_layout_cards", "set_tokens")),
    (results_view.CompareTab, ("show_outcome",)),
    (results_rail.ResultsRail, ("show_cards",)),
    (checks_view.DrcTab, ("show_table",)),
    (charts.BackEmfTab, ("show_outcome",)),
    (charts.TorqueSpeedTab, ("show_outcome",)),
    (geometry_view.GeometryView, ("show_geometry", "place_labels", "fit_view", "resizeEvent", "paintEvent")),
)


def pump(ms: int) -> None:
    """Run the event loop for ``ms``, as app.exec does; QTest.qWait keeps the GIL and starves the worker."""
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def timed(owner: type, name: str) -> None:
    """Replace ``owner.name`` with a wrapper that records its GUI-thread wall time and call depth."""
    original = getattr(owner, name)

    @functools.wraps(original)
    def wrapper(*args, **kwargs):
        if threading.get_ident() != GUI_THREAD:
            return original(*args, **kwargs)
        DEPTH[0] += 1
        start = time.perf_counter()
        try:
            return original(*args, **kwargs)
        finally:
            DEPTH[0] -= 1
            SPANS.append((DEPTH[0], start, time.perf_counter(), f"{owner.__name__}.{name}"))

    setattr(owner, name, wrapper)


def main(stem: str) -> None:
    """Open ``stem``, wait for its result and print the gaps, the worker span and the call tree."""
    geometry_view.GeometryView.paintEvent = lambda self, event: QGraphicsView.paintEvent(self, event)
    for owner, names in TIMED:
        for name in names:
            timed(owner, name)
    worker_span: list[float] = []

    def timed_compute(*args, **kwargs):
        wall, cpu = time.perf_counter(), time.thread_time()
        try:
            return compute(*args, **kwargs)
        finally:
            worker_span.extend((wall, time.perf_counter(), time.thread_time() - cpu))

    QStandardPaths.setTestModeEnabled(True)
    qt_application()
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        store = QSettingsStore(QSettings(str(root / "settings.ini"), QSettings.Format.IniFormat))
        paths = ShellPaths(recovery_dir=root / "recovery")
        window = create_shell(store, paths, compute_fn=timed_compute, prefers_dark=lambda: False).window
        window.resize(1280, 800)
        window.show()
        QTest.qWaitForWindowExposed(window)
        pump(500)
        ticks: list[tuple[float, float]] = []
        timer = QTimer()
        timer.setInterval(10)
        timer.timeout.connect(lambda: ticks.append((time.perf_counter(), time.thread_time())))
        timer.start()
        pump(500)
        SPANS.clear()
        opened = time.perf_counter()
        window.session.load_example(stem)
        while not isinstance(window.outcome.state.value, OutcomeReady) and time.perf_counter() - opened < 90:
            pump(5)
        pump(1500)
        timer.stop()
        window.close()

    def ms(seconds: float) -> str:
        return f"{seconds * 1000:.1f}"

    gaps = sorted(((b[0] - a[0], a[0], b[1] - a[1]) for a, b in pairwise(ticks) if b[0] > opened), reverse=True)
    print(f"== {stem}: largest tick gaps (wall ms, start ms after open, GUI CPU ms inside)")
    for wall, start, cpu in gaps[:5]:
        print(f"   {ms(wall):>8}  at {ms(start - opened):>8}  GUI CPU {ms(cpu)}")
    if worker_span:
        start, end, cpu = worker_span
        print(f"== worker compute: {ms(end - start)} ms wall, {ms(cpu)} ms CPU, from {ms(start - opened)} ms")
    print(f"== GUI-thread spans of {SPAN_MIN_MS:.0f} ms or more (start ms after open, wall ms)")
    for depth, start, end, label in sorted(SPANS, key=lambda span: (span[1], span[0])):
        if (end - start) * 1000 >= SPAN_MIN_MS:
            print(f"   {ms(start - opened):>8}  {'  ' * depth}{label}  {ms(end - start)}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "spiral_12c10p_d08")
