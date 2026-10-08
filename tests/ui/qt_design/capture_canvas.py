"""Save the U-M4c-3 screenshots: canvas labels and legend per topology, a zoomed wave, Layers tab, dialogs, dark D08.

Run from the repository root: ``QT_QPA_PLATFORM=offscreen python tests/ui/qt_design/capture_canvas.py build/screens``.
The splitter under the canvas is dragged down as a user does to look at the drawing (1280 x 800 window).
"""

import sys
import tempfile
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication
from tests.ui.qt_design.capture_screens import EXAMPLES, SIZE_PX, settle

from embodic.ui.app import QSettingsStore, create_shell
from embodic.ui.theme import ThemeName
from embodic.ui.views.main_window import ShellPaths

CANVAS_PX = 520


def main(out_dir: Path) -> int:
    """Write the screenshots into out_dir; return 0."""
    app = QApplication.instance() or QApplication(sys.argv[:1])
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as scratch:
        store = QSettingsStore(QSettings(str(Path(scratch) / "settings.ini"), QSettings.Format.IniFormat))
        window = create_shell(
            store, ShellPaths(recovery_dir=Path(scratch) / "recovery"), prefers_dark=lambda: False
        ).window
        window.resize(*SIZE_PX)
        window.show()
        window.appearance.set_theme(ThemeName.LIGHT)
        dialog = window.new_design_dialog()
        dialog.name.setText("Stator A")
        dialog.show()
        app.processEvents()
        dialog.grab().save(str(out_dir / "u-m4c-3_new-design_light.png"))
        dialog.close()
        gallery = window.examples_gallery()
        gallery.show()
        app.processEvents()
        gallery.grab().save(str(out_dir / "u-m4c-3_examples-gallery_light.png"))
        gallery.close()
        for theme in (ThemeName.LIGHT, ThemeName.DARK):
            window.appearance.set_theme(theme)
            for short, example_id in EXAMPLES.items():
                if theme is ThemeName.DARK and short != "d08":
                    continue
                window.session.load_example(example_id)
                settle(app, window)
                window.centre_split.setSizes([CANVAS_PX, SIZE_PX[1] - CANVAS_PX])
                app.processEvents()
                window.canvas.fit_view()
                app.processEvents()
                window.grab().save(str(out_dir / f"u-m4c-3_canvas_{short}_{theme.value}.png"))
                if short == "wave":
                    r_inner, r_outer = window.outcome.state.value.scene.boards[0].envelope_mm
                    window.canvas.zoom_by(3)
                    window.canvas.centerOn(0, -(r_inner + r_outer) / 2)
                    app.processEvents()
                    window.grab().save(str(out_dir / f"u-m4c-3_canvas-zoom3x_{short}_{theme.value}.png"))
                if short == "d08" and theme is ThemeName.LIGHT:
                    window.inspector_tabs.setCurrentWidget(window.panels["tab-layers"])
                    app.processEvents()
                    window.grab().save(str(out_dir / f"u-m4c-3_inspector-layers_{short}_{theme.value}.png"))
                    window.inspector_tabs.setCurrentWidget(window.panels["tab-coil"])
        window.appearance.set_theme(ThemeName.LIGHT)
        window.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1] if len(sys.argv) > 1 else "build/screens")))
