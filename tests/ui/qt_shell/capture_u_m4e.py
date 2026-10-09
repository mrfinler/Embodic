"""Save the U-M4e-1 screenshots (m4_review_2.md rulings b to h; checklist rows S36 to S38) and the PDF page 1.

Run from the repository root:
``QT_QPA_PLATFORM=offscreen python tests/ui/qt_shell/capture_u_m4e.py build/screens``. The app starts through
``qt_application``, so every shot renders in the bundled Inter and JetBrains Mono. Names are ``u-m4e_<shot>.png``.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QListWidget
from tests.ui.qt_design.capture_screens import settle

from embodic.io.report import write_report_pdf
from embodic.ui.app import QSettingsStore, create_shell, qt_application
from embodic.ui.theme import ThemeName
from embodic.ui.views.main_window import ShellPaths

D08, WAVE, C14 = "spiral_12c10p_d08", "wave_16p_example", "spiral_12c14p"


def main(out_dir: Path) -> int:
    """Write every shot into out_dir; return 0."""
    app = qt_application()
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as scratch:
        store = QSettingsStore(QSettings(str(Path(scratch) / "settings.ini"), QSettings.Format.IniFormat))
        window = create_shell(store, ShellPaths(recovery_dir=Path(scratch) / "r"), prefers_dark=lambda: False).window
        window.show()

        def shot(name: str, size: tuple[int, int], example: str) -> None:
            window.resize(*size)
            for _ in range(10):
                app.processEvents()
            window.grab().save(str(out_dir / f"u-m4e_{name}_{example}_{size[0]}x{size[1]}.png"))

        window.appearance.set_theme(ThemeName.LIGHT)
        window.resize(1280, 800)
        window.session.load_example(D08)
        settle(app, window)
        window.show_results_tab("tab-results")
        shot("canvas-60-40", (1280, 800), D08)
        for theme in (ThemeName.LIGHT, ThemeName.DARK):
            window.appearance.set_theme(theme)
            window.session.load_example(D08)
            settle(app, window)
            shot(f"drawing-tab-{theme.value}", (960, 540), D08)
        window.appearance.set_theme(ThemeName.LIGHT)
        for example in (D08, C14):
            window.resize(1280, 800)
            window.session.load_example(example)
            settle(app, window)
            layers = window.panels["tab-layers"]
            window.inspector_tabs.setCurrentWidget(layers)
            window.resize(960, 540)
            app.processEvents()
            layers.ensureWidgetVisible(layers.helpers["pair-list"])
            shot("layers-pair-list", (960, 540), example)
        window.resize(1280, 800)
        window.session.load_example(WAVE)
        settle(app, window)
        window.inspector_tabs.setCurrentWidget(window.panels["tab-board"])
        board = window.panels["tab-board"]
        board.ensureWidgetVisible(board.helpers["screw-table"])
        window.show_results_tab("tab-drc")
        shot("board-screws-drc", (1280, 800), WAVE)
        gallery = window.examples_gallery()
        gallery.show()
        gallery.findChild(QListWidget, "examples-list").setCurrentRow(1)
        for _ in range(5):
            app.processEvents()
        gallery.grab().save(str(out_dir / "u-m4e_gallery-selected_light.png"))
        gallery.close()
        window.session.load_example(D08)
        settle(app, window)
        outcome = window.session.current_outcome()
        assert outcome is not None
        pdf = out_dir / "u-m4e_report_d08.pdf"
        write_report_pdf(outcome, pdf)
        page_one = ["pdftoppm", "-png", "-r", "110", "-f", "1", "-l", "1", str(pdf), str(pdf.with_suffix(""))]
        subprocess.run(page_one, check=True)
        window.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1] if len(sys.argv) > 1 else "build/screens")))
