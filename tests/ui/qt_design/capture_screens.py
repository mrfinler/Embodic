"""Save the U-M4c screenshots: New design dialog, Examples gallery and every inspector tab per example and theme.

Run from the repository root: ``QT_QPA_PLATFORM=offscreen python tests/ui/qt_design/capture_screens.py build/screens``.
Names follow ``<screen>_<example>_<theme>.png``.
"""

import sys
import tempfile
import time
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from embodic.model.vocabulary import TopologyKind
from embodic.ui.app import QSettingsStore, create_shell
from embodic.ui.theme import ThemeName
from embodic.ui.viewmodels.outcome import OutcomeReady
from embodic.ui.viewmodels.session import SessionComputed
from embodic.ui.views.main_window import ShellPaths

SIZE_PX = (1280, 800)
EXAMPLES = {"d08": "spiral_12c10p_d08", "serpentine": "serpentine_16p_example", "wave": "wave_16p_example"}
TABS = ("tab-coil", "tab-phases", "tab-layers", "tab-board")


def settle(app: QApplication, window, timeout_s: float = 60.0) -> None:
    """Process events until the session's compute result is on screen."""
    deadline = time.monotonic() + timeout_s
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
    window.canvas.fit_view()
    app.processEvents()


def main(out_dir: Path) -> int:
    """Write every screenshot into out_dir; return 0."""
    app = QApplication.instance() or QApplication(sys.argv[:1])
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as scratch:
        store = QSettingsStore(QSettings(str(Path(scratch) / "settings.ini"), QSettings.Format.IniFormat))
        window = create_shell(
            store, ShellPaths(recovery_dir=Path(scratch) / "recovery"), prefers_dark=lambda: False
        ).window
        window.resize(*SIZE_PX)
        window.show()
        for theme in (ThemeName.LIGHT, ThemeName.DARK):
            window.appearance.set_theme(theme)
            dialog = window.new_design_dialog()
            dialog.name.setText("Stator A")
            dialog.topology_buttons[next(iter(dialog.topology_buttons))].setChecked(True)
            dialog.show()
            app.processEvents()
            dialog.grab().save(str(out_dir / f"new-design_blank_{theme.value}.png"))
            dialog.close()
            gallery = window.examples_gallery()
            gallery.show()
            app.processEvents()
            gallery.grab().save(str(out_dir / f"examples-gallery_all_{theme.value}.png"))
            gallery.close()
        for theme in (ThemeName.LIGHT, ThemeName.DARK):
            window.appearance.set_theme(theme)
            for short, example_id in EXAMPLES.items():
                if theme is ThemeName.DARK and short != "d08":
                    continue
                window.session.load_example(example_id)
                settle(app, window)
                for tab in TABS:
                    window.inspector_tabs.setCurrentWidget(window.panels[tab])
                    app.processEvents()
                    window.grab().save(str(out_dir / f"inspector-{tab.removeprefix('tab-')}_{short}_{theme.value}.png"))
        window.appearance.set_theme(ThemeName.LIGHT)
        window.session.new_design(TopologyKind.SPIRAL)
        window.inspector_tabs.setCurrentWidget(window.panels["tab-coil"])
        app.processEvents()
        window.grab().save(str(out_dir / "inspector-coil_blank-spiral_light.png"))
        window.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("build/screens")))
