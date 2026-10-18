r"""U-M8o probe: the speed of float math on the shell's GUI thread, after an open and after a repaint.

Opens D08 in a shown shell as the gallery does and waits for its result, then times one million ``math.atan2`` calls
and one D08 ``ready_state`` on the GUI thread; then again after a 64 MiB ``ctypes.memmove`` and after
``window.repaint()``. In U-M8o the GUI thread ran atan2 about five times and ready_state about twice as slow after the
open as after the repaint; the memmove changed nothing, and the worker thread ran at the speed of a plain process.
The cause is unresolved.

Not a test. From the repository root, with the project's interpreter:

    QT_QPA_PLATFORM=offscreen PYTHONPATH=src python tests/ui/qt_shell/gui_thread_math.py
"""

import ctypes
import math
import tempfile
import time
import timeit
from pathlib import Path

from PySide6.QtCore import QEventLoop, QSettings, QStandardPaths, QTimer

from embodic.ui.app import QSettingsStore, create_shell, qt_application
from embodic.ui.viewmodels.outcome import OutcomeReady, ready_state
from embodic.ui.views.main_window import ShellPaths

COPY_BYTES = 64 * 1024 * 1024


def pump(ms: int) -> None:
    """Run the event loop for ``ms``."""
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def measure(label: str, outcome: object) -> None:
    """Print the time of 1e6 atan2 calls and of one ready_state on this thread."""
    atan2_s = timeit.timeit("atan2(0.3, 0.7)", globals={"atan2": math.atan2}, number=1_000_000)
    started = time.perf_counter()
    ready_state(outcome)
    scene_ms = (time.perf_counter() - started) * 1000
    print(f"{label}: 1e6 atan2 {atan2_s * 1000:.0f} ms, D08 ready_state {scene_ms:.0f} ms")


def main() -> None:
    """Open D08, then measure after the open, after a memmove and after a repaint."""
    QStandardPaths.setTestModeEnabled(True)
    qt_application()
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        store = QSettingsStore(QSettings(str(root / "settings.ini"), QSettings.Format.IniFormat))
        window = create_shell(store, ShellPaths(recovery_dir=root / "recovery"), prefers_dark=lambda: False).window
        window.resize(1280, 800)
        window.show()
        pump(300)
        window.outcome.open_example("spiral_12c10p_d08")
        while not isinstance(window.outcome.state.value, OutcomeReady):
            pump(5)
        pump(300)
        outcome = window.outcome.state.value.outcome
        measure("after the open", outcome)
        source, target = ctypes.create_string_buffer(COPY_BYTES), ctypes.create_string_buffer(COPY_BYTES)
        ctypes.memmove(target, source, COPY_BYTES)
        measure("after a 64 MiB memmove", outcome)
        window.repaint()
        measure("after window.repaint()", outcome)
        window.close()


if __name__ == "__main__":
    main()
