r"""DEF-U-M6a-01 lever (U-M8a): cProfile of the two one-off GUI-thread updates, example open and result arrival.

Opens an example as the gallery does, with the real compute, and profiles the GUI thread inside
``DesignSession.load_example`` (the open) and inside ``OutcomeViewModel.on_finished`` (the result). Prints, per
update, its wall and GUI-thread CPU time and the functions with the most own time; Qt's C++ work shows under the
PySide6 method that started it. Run it several times and alternate with the version you compare against:

    QT_QPA_PLATFORM=offscreen PYTHONPATH=src python tests/ui/qt_shell/stall_profile.py spiral_12c10p_d08 [rows]

Not a test. cProfile slows Python code down, so compare its CPU times with each other, not with the 100 ms bound;
``rows`` 0 skips the profiler and prints the plain wall and CPU times.
"""

import cProfile
import functools
import io
import pstats
import sys
import tempfile
import time
from pathlib import Path

from PySide6.QtCore import QEventLoop, QSettings, QStandardPaths, QTimer
from PySide6.QtTest import QTest

from embodic.ui.app import QSettingsStore, create_shell, qt_application
from embodic.ui.viewmodels.outcome import OutcomeReady, OutcomeViewModel
from embodic.ui.viewmodels.session import DesignSession
from embodic.ui.views.main_window import ShellPaths

PROFILES: dict[str, list[tuple[cProfile.Profile, float, float]]] = {"open": [], "result": []}


def pump(ms: int) -> None:
    """Run the event loop for ``ms``; QTest.qWait keeps the GIL and starves the worker (D-050a)."""
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def profiled(owner: type, name: str, label: str, *, enabled: bool) -> None:
    """Time every call of ``owner.name`` under ``label`` (wall and thread CPU), with cProfile when ``enabled``."""
    original = getattr(owner, name)

    @functools.wraps(original)
    def wrapper(*args, **kwargs):
        profile = cProfile.Profile()
        wall, cpu = time.perf_counter(), time.thread_time()
        if enabled:
            profile.enable()
        try:
            return original(*args, **kwargs)
        finally:
            profile.disable()
            PROFILES[label].append((profile, time.perf_counter() - wall, time.thread_time() - cpu))

    setattr(owner, name, wrapper)


def main(stem: str, rows: int) -> None:
    """Open ``stem``, wait for its result and print both profiles."""
    profiled(DesignSession, "load_example", "open", enabled=rows > 0)
    profiled(OutcomeViewModel, "on_finished", "result", enabled=rows > 0)
    QStandardPaths.setTestModeEnabled(True)
    qt_application()
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        store = QSettingsStore(QSettings(str(root / "settings.ini"), QSettings.Format.IniFormat))
        window = create_shell(store, ShellPaths(recovery_dir=root / "recovery"), prefers_dark=lambda: False).window
        window.resize(1280, 800)
        window.show()
        QTest.qWaitForWindowExposed(window)
        pump(500)
        opened = time.perf_counter()
        window.session.load_example(stem)
        while not isinstance(window.outcome.state.value, OutcomeReady) and time.perf_counter() - opened < 90:
            pump(5)
        pump(500)
        window.close()
    for label, runs in PROFILES.items():
        for profile, wall, cpu in runs:
            how = "profiled" if rows > 0 else "not profiled"
            print(f"== {stem} {label}: {wall * 1000:.1f} ms wall, {cpu * 1000:.1f} ms GUI-thread CPU ({how})")
            if rows == 0:
                continue
            text = io.StringIO()
            pstats.Stats(profile, stream=text).sort_stats("tottime").print_stats(rows)
            print("\n".join(line for line in text.getvalue().splitlines()[6:] if line.strip()))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "spiral_12c10p_d08", int(sys.argv[2]) if len(sys.argv) > 2 else 25)
