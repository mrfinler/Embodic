"""Save the U-M4c-4 screenshots: the board picker on Board B and the DRC tab with its Board column (1280 x 800, light).

Run from the repository root with QT_QPA_PLATFORM=offscreen:
``python tests/ui/qt_design/capture_board_picker.py build/screens``.
The design is the serpentine example as one board per phase. The DRC shot raises the trace clearance rule so that
every board reports real failures; the rule value is a screenshot input, not a design proposal.
"""

import sys
import tempfile
import time
from pathlib import Path

from PySide6.QtCore import QSettings, QStandardPaths
from PySide6.QtWidgets import QApplication

from embodic.api import compute
from embodic.ui.app import QSettingsStore, create_shell, qt_application
from embodic.ui.theme import ThemeName
from embodic.ui.toolstrip import ToolstripTab
from embodic.ui.viewmodels.session import SessionComputed
from embodic.ui.views.main_window import ShellPaths

SIZE_PX = (1280, 800)
TIMEOUT_S = 90


def wait_computed(app: QApplication, window) -> None:
    """Run the event loop until the session's design has its compute result."""
    end = time.monotonic() + TIMEOUT_S
    while time.monotonic() < end:
        state = window.session.state.value
        if isinstance(state, SessionComputed) and not state.computing and state.outcome is not None:
            break
        app.processEvents()
    for _ in range(10):
        app.processEvents()


def main(out_dir: Path) -> int:
    """Write the two screenshots into out_dir; return 0."""
    app = qt_application()
    QStandardPaths.setTestModeEnabled(True)
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as scratch:
        store = QSettingsStore(QSettings(str(Path(scratch) / "settings.ini"), QSettings.Format.IniFormat))
        window, _ = create_shell(store, ShellPaths(recovery_dir=Path(scratch) / "recovery"), compute, lambda: False)
        window.resize(*SIZE_PX)
        window.show()
        window.appearance.set_theme(ThemeName.LIGHT)
        window.session.load_example("serpentine_16p_example")
        wait_computed(app, window)
        window.session.edit("/winding/stack_mode", "one_board_per_phase")
        window.session.set_stackup_input("copper_count", 2)  # one board holds one phase: 2 layers per phase
        wait_computed(app, window)
        window.toolstrip.show_tab(ToolstripTab.VIEW)
        window.toolstrip.board_picker.setCurrentIndex(2)
        for _ in range(10):
            app.processEvents()
        window.grab().save(str(out_dir / "u-m4c-4_board-picker-b_1280x800_light.png"))
        window.session.edit("/drc_rules/trace_clearance_mm", 3.0)
        wait_computed(app, window)
        window.show_results_tab("tab-drc")
        table = window.drc_tab.table
        first_of_b = next(r for r in range(table.model().rowCount()) if window.drc_tab.model.item(r, 1).text() == "B")
        table.selectRow(first_of_b)
        table.scrollTo(table.model().index(first_of_b, 0), table.ScrollHint.PositionAtTop)
        for _ in range(10):
            app.processEvents()
        window.grab().save(str(out_dir / "u-m4c-4_drc-board-column_1280x800_light.png"))
        window.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("build/screens")))
