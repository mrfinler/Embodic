"""Save the U-M4d screenshots: Results (light and dark), DRC with a located failure, charts, Compare, Export, guide.

Run from the repository root: ``QT_QPA_PLATFORM=offscreen python tests/ui/qt_results/capture_screens.py build/screens``.
The torque-speed shot enters a DC-link voltage of 24 V on D08 (an example input; D08 has none) so the EQ-20 estimate
exists. Export folders are temporary folders outside the home folder.
"""

import sys
import tempfile
import time
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QWidget

from embodic.ui.app import QSettingsStore, create_shell
from embodic.ui.theme import ThemeName
from embodic.ui.viewmodels.outcome import OutcomeReady
from embodic.ui.viewmodels.session import SessionComputed
from embodic.ui.views.main_window import MainWindow, ShellPaths

SIZE_PX = (1280, 800)
D08, D14, WAVE = "spiral_12c10p_d08", "spiral_12c14p", "wave_16p_example"


def settle(app: QApplication, window: MainWindow, timeout_s: float = 60.0) -> None:
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
    for _ in range(5):
        app.processEvents()


def grab(app: QApplication, widget: QWidget, path: Path) -> None:
    """Let the widget paint, then save it."""
    for _ in range(5):
        app.processEvents()
    widget.grab().save(str(path))


def tab(window: MainWindow, tab_id: str, app: QApplication, canvas_px: int = 300) -> None:
    """Bring a results tab forward; the canvas keeps ``canvas_px`` of the centre height."""
    window.show_results_tab(tab_id)
    app.processEvents()
    window.centre_split.setSizes([canvas_px, 660 - canvas_px])
    app.processEvents()


def main(out_dir: Path) -> int:
    """Write every screenshot into out_dir; return 0."""
    app = QApplication.instance() or QApplication(sys.argv[:1])
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as scratch, tempfile.TemporaryDirectory(dir="/tmp") as export_dir:
        store = QSettingsStore(QSettings(str(Path(scratch) / "settings.ini"), QSettings.Format.IniFormat))
        window = create_shell(
            store, ShellPaths(recovery_dir=Path(scratch) / "recovery"), prefers_dark=lambda: False
        ).window
        window.resize(*SIZE_PX)
        window.show()
        window.session.load_example(D08)
        settle(app, window)
        for theme in (ThemeName.LIGHT, ThemeName.DARK):
            window.appearance.set_theme(theme)
            tab(window, "tab-results", app)
            card = window.results_tab.cards["ke"]
            card.how_toggle.setChecked(True)
            window.results_tab.findChild(QWidget, "results-scroll").ensureWidgetVisible(card)
            grab(app, window, out_dir / f"results_d08_{theme.value}.png")
            card.how_toggle.setChecked(False)
            tab(window, "tab-back-emf", app)
            grab(app, window, out_dir / f"back_emf_d08_{theme.value}.png")
        window.appearance.set_theme(ThemeName.LIGHT)
        window.session.edit("/operating/dc_link_v", 24.0)
        settle(app, window)
        tab(window, "tab-torque-speed", app, canvas_px=60)
        grab(app, window, out_dir / "torque_speed_d08_dc24v_light.png")

        window.session.load_example(D08)
        settle(app, window)
        window.compare_tab.set_reference.click()
        window.session.load_example(D14)
        settle(app, window)
        tab(window, "tab-compare", app, canvas_px=60)
        grab(app, window, out_dir / "compare_d08_vs_12c14p_light.png")

        window.session.load_example(WAVE)
        settle(app, window)
        tab(window, "tab-drc", app)
        window.drc_tab.table.selectRow(0)
        window.drc_tab.locate.click()
        grab(app, window, out_dir / "drc_wave_located_light.png")

        dialog = window.show_export("export_bundle")
        dialog.folder.setText(export_dir)
        grab(app, dialog, out_dir / "export_dialog_wave_light.png")
        dialog.run_clicked()
        grab(app, dialog.confirm, out_dir / "export_confirm_wave_light.png")
        dialog.confirm.reject()
        dialog.close()

        window.show_equations("EQ-18")
        grab(app, window.guide, out_dir / "guide_eq18_light.png")
        window.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1] if len(sys.argv) > 1 else "build/screens")))
