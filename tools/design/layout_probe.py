# Prepared by: Agent 1 (UX/UI Expert Designer) - model: claude-opus-5-5
"""Measure the layout numbers the U-S4e rulings b, c and d rest on, with or without the bundled fonts.

    QT_QPA_PLATFORM=offscreen PYTHONPATH=src:. .venv/bin/python tools/design/layout_probe.py [--fonts] [--shots DIR]

Prints one line per window size and state: inspector width, canvas and results heights in `centre-split`, whether
the inspector tab bar needs scroll buttons, and the sideways overflow of `layer-list`, `screw-table`, `drc-table` and
`results-scroll` (header or content length minus viewport width; 0 means it fits). Reads the app; writes only the
optional screenshots. Exit 0.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QAbstractScrollArea, QApplication, QTabBar, QTableView

from tests.ui.qt_results.capture_screens import settle

from embodic.ui.app import QSettingsStore, create_shell
from embodic.ui.fonts import register_fonts
from embodic.ui.views.main_window import MainWindow, ShellPaths

EXAMPLES = {"d08": "spiral_12c10p_d08", "wave": "wave_16p_example"}


def _overflow(view: QAbstractScrollArea | None) -> int | str:
    if view is None:
        return "absent"
    if isinstance(view, QTableView):
        return view.horizontalHeader().length() - view.viewport().width()
    return view.horizontalScrollBar().maximum()


def _tabs_scroll(bar: QTabBar) -> bool:
    return sum(bar.tabRect(i).width() for i in range(bar.count())) > bar.width()


def _probe(app: QApplication, window: MainWindow, size: tuple[int, int], state: str, shots: Path | None) -> None:
    window.resize(*size)
    for _ in range(10):
        app.processEvents()
    split = window.centre_split.sizes()
    find = window.findChild
    print(
        f"{size[0]}x{size[1]} {state}: panes={window.splitter.sizes()} canvas/results={split} "
        f"inspector_tabs_scroll={_tabs_scroll(window.inspector_tabs.tabBar())} "
        f"results_tabs_scroll={_tabs_scroll(window.results_tabs.tabBar())} "
        f"layer-list={_overflow(find(QTableView, 'layer-list'))} screw-table={_overflow(find(QTableView, 'screw-table'))} "
        f"drc-table={_overflow(find(QTableView, 'drc-table'))} "
        f"results-scroll={_overflow(find(QAbstractScrollArea, 'results-scroll'))}"
    )
    if shots is not None:
        window.grab().save(str(shots / f"{state}_{size[0]}x{size[1]}.png"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fonts", action="store_true", help="register the bundled fonts as app.py does")
    parser.add_argument("--shots", type=Path, default=None)
    args = parser.parse_args()
    app = QApplication.instance() or QApplication(sys.argv[:1])
    if args.fonts:
        register_fonts(QFontDatabase.addApplicationFont, app)
    print(f"font: {app.font().family()} {app.font().pixelSize()} px")
    if args.shots:
        args.shots.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as scratch:
        store = QSettingsStore(QSettings(str(Path(scratch) / "s.ini"), QSettings.Format.IniFormat))
        window = create_shell(store, ShellPaths(recovery_dir=Path(scratch) / "r"), prefers_dark=lambda: False).window
        window.show()
        for name, example in EXAMPLES.items():
            window.session.load_example(example)
            settle(app, window)
            for size in ((1280, 800), (960, 540)):
                window.show_results_tab("tab-results")
                window.inspector_tabs.setCurrentWidget(window.panels["tab-layers"])
                _probe(app, window, size, f"{name}-layers-results", args.shots)
                window.inspector_tabs.setCurrentWidget(window.panels["tab-board"])
                window.show_results_tab("tab-drc")
                _probe(app, window, size, f"{name}-board-drc", args.shots)
        window.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
