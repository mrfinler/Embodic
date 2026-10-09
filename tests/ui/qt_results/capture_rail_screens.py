"""Save the U-M4d-fix screenshots: the rail by window width, and the DRC tab with its full message column.

The rail is the Key results tab at 960 x 540 and the third pane at 1280 x 800, both on D08; the DRC tab shows the wave
example. Run from the repository root:
``QT_QPA_PLATFORM=offscreen python -m tests.ui.qt_results.capture_rail_screens build/screens``.
"""

import sys
import tempfile
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication
from tests.ui.qt_results.capture_screens import D08, WAVE, grab, settle

from embodic.ui.app import QSettingsStore, create_shell, qt_application
from embodic.ui.views.main_window import MainWindow, ShellPaths


def show_size(app: QApplication, window: MainWindow, size: tuple[int, int]) -> None:
    """Resize the window, let the layout settle and bring the Key results tab forward when the rail is a tab."""
    window.resize(*size)
    for _ in range(5):
        app.processEvents()
    index = window.results_tabs.indexOf(window.rail_scroll)
    if index >= 0:
        window.results_tabs.setCurrentIndex(index)
    for _ in range(5):
        app.processEvents()


def main(out_dir: Path) -> int:
    """Write the shots into out_dir; return 0."""
    app = qt_application()
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as scratch:
        store = QSettingsStore(QSettings(str(Path(scratch) / "settings.ini"), QSettings.Format.IniFormat))
        window = create_shell(
            store, ShellPaths(recovery_dir=Path(scratch) / "recovery"), prefers_dark=lambda: False
        ).window
        window.show()
        window.session.load_example(D08)
        show_size(app, window, (1280, 800))
        settle(app, window)
        grab(app, window, out_dir / "rail_d08_1280x800_light.png")
        show_size(app, window, (960, 540))
        grab(app, window, out_dir / "rail_d08_960x540_light.png")

        window.session.load_example(WAVE)
        settle(app, window)
        for size in ((1280, 800), (960, 540)):
            show_size(app, window, size)
            window.show_results_tab("tab-drc")
            for _ in range(5):
                app.processEvents()
            grab(app, window, out_dir / f"drc_wave_{size[0]}x{size[1]}_light.png")
        window.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1] if len(sys.argv) > 1 else "build/screens")))
