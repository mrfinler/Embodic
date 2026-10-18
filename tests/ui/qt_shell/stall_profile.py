r"""DEF-U-M6a-01 lever (U-M8a, U-M8n): cProfile of the one-off GUI-thread updates of an open and of typing over it.

Opens an example as the gallery does, with the real compute, and profiles the GUI thread inside
``DesignSession.load_example`` (the open) and inside ``OutcomeViewModel.on_finished`` (the result). Then it types
over the inner radius as N02-10 does: "11.6", a wait while that preview computes (held for 2 s), and "1", the
keystroke that cancels the preview in flight; each keystroke is profiled inside ``DesignSession.type_text``. Prints,
per update, its wall and GUI-thread CPU time and, for the slowest of each kind, the functions with the most own
time; Qt's C++ work shows under the PySide6 method that started it. Run it several times and alternate with the
version you compare against:

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

from PySide6.QtCore import QEventLoop, QSettings, QStandardPaths, Qt, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QLineEdit

from embodic.api import compute
from embodic.ui.app import QSettingsStore, create_shell, qt_application
from embodic.ui.viewmodels.outcome import OutcomeReady, OutcomeViewModel
from embodic.ui.viewmodels.session import DesignSession
from embodic.ui.views.main_window import ShellPaths

PROFILES: dict[str, list[tuple[cProfile.Profile, float, float]]] = {"open": [], "result": [], "keystroke": []}
PREVIEW_R_INNER_MM = 11.6
PREVIEW_HOLD_S = 2.0


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


def held_preview(design, provenance, *, cache, cancel):
    """Compute as the shell does, but hold the preview of the typed radius so that the next keystroke cancels it."""
    if design.winding.coil.r_inner_mm == PREVIEW_R_INNER_MM:
        time.sleep(PREVIEW_HOLD_S)
    return compute(design, provenance, cache=cache, cancel=cancel)


def type_keys(field: QLineEdit, keys: str) -> None:
    """Type ``keys`` one every 50 ms, as fix_wave_f1.md (a) does, with the event loop running between them."""
    for key in keys:
        QTest.keyClick(field, key)
        pump(50)


def main(stem: str, rows: int) -> None:
    """Open ``stem``, wait for its result, type over the inner radius and print the profiles."""
    profiled(DesignSession, "load_example", "open", enabled=rows > 0)
    profiled(OutcomeViewModel, "on_finished", "result", enabled=rows > 0)
    profiled(DesignSession, "type_text", "keystroke", enabled=rows > 0)
    QStandardPaths.setTestModeEnabled(True)
    qt_application()
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        store = QSettingsStore(QSettings(str(root / "settings.ini"), QSettings.Format.IniFormat))
        paths = ShellPaths(recovery_dir=root / "recovery")
        window = create_shell(store, paths, compute_fn=held_preview, prefers_dark=lambda: False).window
        window.resize(1280, 800)
        window.show()
        QTest.qWaitForWindowExposed(window)
        pump(500)
        opened = time.perf_counter()
        window.session.load_example(stem)
        while not isinstance(window.outcome.state.value, OutcomeReady) and time.perf_counter() - opened < 90:
            pump(5)
        pump(500)
        field = window.findChild(QLineEdit, "param-r-inner")
        field.setFocus(Qt.FocusReason.MouseFocusReason)
        field.selectAll()
        type_keys(field, f"{PREVIEW_R_INNER_MM}")
        pump(450)
        type_keys(field, "1")
        pump(int(PREVIEW_HOLD_S * 1000))
        window.close()
    how = "profiled" if rows > 0 else "not profiled"
    for label, runs in PROFILES.items():
        for _, wall, cpu in runs:
            print(f"== {stem} {label}: {wall * 1000:.1f} ms wall, {cpu * 1000:.1f} ms GUI-thread CPU ({how})")
        if rows == 0 or not runs:
            continue
        slowest = max(runs, key=lambda run: run[2])[0]
        text = io.StringIO()
        pstats.Stats(slowest, stream=text).sort_stats("tottime").print_stats(rows)
        print(f"-- slowest {label}:")
        print("\n".join(line for line in text.getvalue().splitlines()[6:] if line.strip()))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "spiral_12c10p_d08", int(sys.argv[2]) if len(sys.argv) > 2 else 25)
