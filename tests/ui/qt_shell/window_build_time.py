r"""D-050a lever (U-M6a): window construction time, and the PF-03 cold start it adds to.

Prints, for three runs each: the QElapsedTimer milliseconds from building the shell (``create_shell``, which constructs
MainWindow) to its first show on screen, in this process; and the seconds from process start to a shown window, the
measurement of tests/performance/test_pf_baseline.py::test_pf03_cold_start_to_a_shown_window_offscreen (budget 3.0 s,
`assumption`). Not a test:

    QT_QPA_PLATFORM=offscreen PYTHONPATH=src python tests/ui/qt_shell/window_build_time.py
"""

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

RUNS = 3
COLD_START = """
import sys
from pathlib import Path
from PySide6.QtCore import QElapsedTimer, QSettings
from PySide6.QtTest import QTest
from embodic.ui import app as shell
qt = shell.qt_application()
clock = QElapsedTimer()
clock.start()
store = shell.QSettingsStore(QSettings(sys.argv[1] + "/settings.ini", QSettings.Format.IniFormat))
window = shell.create_shell(store, shell.ShellPaths(recovery_dir=Path(sys.argv[1]))).window
window.resize(1280, 800)
window.show()
QTest.qWaitForWindowExposed(window)
print(clock.elapsed(), flush=True)
"""


def main() -> None:
    """Run the cold start ``RUNS`` times and print both numbers per run."""
    env = {**os.environ, "QT_QPA_PLATFORM": os.environ.get("QT_QPA_PLATFORM", "offscreen")}
    for run in range(RUNS):
        with tempfile.TemporaryDirectory() as folder:
            started = time.perf_counter()
            done = subprocess.run(
                [sys.executable, "-c", COLD_START, folder], env=env, capture_output=True, encoding="utf-8", check=True
            )
            cold_s = time.perf_counter() - started
        build_ms = int(done.stdout.strip().splitlines()[-1])
        print(f"run {run + 1}: MainWindow to first show {build_ms} ms, process start to shown window {cold_s:.2f} s")
    print(f"PF-03 budget 3.0 s (assumption), measured in {Path(__file__).name}")


if __name__ == "__main__":
    main()
