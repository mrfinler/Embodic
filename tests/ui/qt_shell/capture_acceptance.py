"""Take the 41 rows of docs/phase2/design/screenshot_checklist.md, one function per row, focus set as each row says.

Run from the repository root::

    QT_QPA_PLATFORM=offscreen python -m tests.ui.qt_shell.capture_acceptance OUT_DIR [S01 S07 ...]
    QT_QPA_PLATFORM=offscreen QT_SCALE_FACTOR=1.5 python -m tests.ui.qt_shell.capture_acceptance OUT_DIR --scaling

Qt starts through ``qt_application()``, so every shot renders in the bundled fonts. Files are named
``<ID>_<theme>_<width>x<height>[_<part>].png``. The run works in a scratch folder that is also HOME, so a path a dialog
shows reads ``%USERPROFILE%`` or a relative name, never a user's folder. It prints one JSON line per row:
``{"row": "S01", "files": [...], "notes": [...]}``; a row the app cannot show yet has an empty file list and a note.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import QPoint, QSettings, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QTableView,
    QTabWidget,
    QToolTip,
    QWidget,
)

from embodic.io.report import write_report_pdf
from embodic.model.vocabulary import TopologyKind
from embodic.ui.app import QSettingsStore, create_shell, qt_application
from embodic.ui.theme import ThemeName
from embodic.ui.toolstrip import ToolstripTab
from embodic.ui.viewmodels.outcome import OutcomeReady
from embodic.ui.viewmodels.session import SessionComputed
from embodic.ui.views.main_window import MainWindow, ShellPaths

CF11, D08, C14 = "spiral_12c16p_default", "spiral_12c10p_d08", "spiral_12c14p"
SERP, WAVE = "serpentine_16p_example", "wave_16p_example"
WIDE, SMALL = (1280, 800), (960, 540)
L, D = ThemeName.LIGHT, ThemeName.DARK
SETTLE_S = 60.0


@dataclass
class Run:
    """The window, the output folder and what the current row has written."""

    app: QApplication
    window: MainWindow
    out: Path
    files: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def pump(self, rounds: int = 10) -> None:
        """Process pending events a few times so layout and paint settle."""
        for _ in range(rounds):
            self.app.processEvents()

    def settle(self) -> None:
        """Wait until the current design's compute result is on screen, then fit the canvas."""
        import time

        deadline = time.monotonic() + SETTLE_S
        while time.monotonic() < deadline:
            self.app.processEvents()
            state = self.window.session.state.value
            computed = isinstance(state, SessionComputed) and not state.computing
            if computed and isinstance(self.window.outcome.state.value, OutcomeReady):
                break
            if not isinstance(state, SessionComputed) and not getattr(state, "computing", False):
                break
            time.sleep(0.01)
        self.pump()
        self.window.canvas.fit_view()
        self.pump()

    def start(self, example: str | None, theme: ThemeName = L, size: tuple[int, int] = WIDE) -> MainWindow:
        """Reset to the row's state: theme, window size, and an example (None leaves the session as it is)."""
        self.window.appearance.set_theme(theme)
        self.window.resize(*size)
        if example is not None:
            self.window.session.load_example(example)
            self.settle()
        self.pump()
        return self.window

    def widget(self, name: str, root: QWidget | None = None) -> QWidget:
        """Return the widget with an objectName under ``root`` (default the window)."""
        found = (root or self.window).findChild(QWidget, name)
        assert found is not None, name
        return found

    def focus(self, name: str, root: QWidget | None = None) -> None:
        """Give keyboard focus to the Focus-column widget and let the ring paint (checklist rule Focus)."""
        target = self.widget(name, root)
        (root or self.window).activateWindow()
        target.setFocus(Qt.FocusReason.TabFocusReason)
        self.pump()
        if not target.hasFocus():
            self.notes.append(f"{name} did not take focus")

    def save(self, row: str, theme: ThemeName, size: tuple[int, int] | str, widget: QWidget | None = None, part=""):
        """Grab ``widget`` (default the window) with any open tooltip or dialog of the window drawn over it."""
        label = size if isinstance(size, str) else f"{size[0]}x{size[1]}"
        name = f"{row}_{theme.value}_{label}{'_' + part if part else ''}.png"
        self.pump()
        image = (widget or self.window).grab()
        if widget is None:
            painter = QPainter(image)
            for top in QApplication.topLevelWidgets():
                if top.isVisible() and top is not self.window and top.isWindow() and _over(top, self.window):
                    offset = top.mapToGlobal(QPoint(0, 0)) - self.window.mapToGlobal(QPoint(0, 0))
                    painter.drawPixmap(offset, top.grab())
            painter.end()
        image.save(str(self.out / name))
        self.files.append(name)


def _over(top: QWidget, window: QWidget) -> bool:
    return type(top).__name__ == "QTipLabel" or (isinstance(top, QDialog) and top.parentWidget() is window)


def _type(run: Run, name: str, value: str) -> None:
    edit = run.widget(name)
    assert isinstance(edit, QLineEdit), name
    for panel in run.window.panels.values():
        if panel.isAncestorOf(edit):
            run.window.inspector_tabs.setCurrentWidget(panel)
            panel.ensureWidgetVisible(edit)
    edit.setText(value)
    edit.editingFinished.emit()
    run.settle()


def _inspector(run: Run, tab: str) -> QWidget:
    panel = run.window.panels[tab]
    run.window.inspector_tabs.setCurrentWidget(panel)
    run.pump()
    return panel


def _results(run: Run, tab: str) -> None:
    run.window.show_results_tab(tab)
    run.pump()


def _close_dialogs(run: Run) -> None:
    for top in QApplication.topLevelWidgets():
        if isinstance(top, QDialog) and top.isVisible():
            top.close()
    QToolTip.hideText()
    run.pump()


def _s01(run: Run) -> None:
    for theme in (L, D):
        for size in (SMALL, WIDE):
            run.start(None, theme, size)
            run.focus("toolstrip")
            run.save("S01", theme, size)


def _s02(run: Run) -> None:
    run.start(CF11)
    focus = {
        ToolstripTab.HOME: "act-new",
        ToolstripTab.DESIGN: "act-topo-spiral",
        ToolstripTab.ANALYSIS: "act-compute",
        ToolstripTab.EXPORT: "act-export-svg",
        ToolstripTab.VIEW: "act-theme",
    }
    for tab, name in focus.items():
        run.window.toolstrip.show_tab(tab)
        run.focus(name)
        run.save("S02", L, WIDE, part=tab.value)
    run.window.toolstrip.show_tab(ToolstripTab.HOME)


def _s03(run: Run) -> None:
    run.start(CF11, L, SMALL)
    for tab in ToolstripTab:
        run.window.toolstrip.show_tab(tab)
        run.focus("toolstrip")
        run.save("S03", L, SMALL, part=tab.value)
    run.window.toolstrip.show_tab(ToolstripTab.HOME)


def _canvas_row(row: str, example: str, greyscale: bool = False) -> Callable[[Run], None]:
    def take(run: Run) -> None:
        for theme in (L, D):
            run.start(example, theme)
            action = run.window.toolstrip.actions_by_id["act-greyscale"]
            if action.isChecked() != greyscale:
                action.trigger()
            run.window.canvas.fit_view()
            run.focus("fig-canvas")
            run.save(row, theme, WIDE)
        action = run.window.toolstrip.actions_by_id["act-greyscale"]
        if action.isChecked():
            action.trigger()

    return take


def _s07(run: Run) -> None:
    for theme in (L, D):
        run.start(WAVE, theme)
        run.focus("fig-canvas")
        run.save("S07", theme, WIDE, part="fit")
        r_inner, r_outer = run.window.outcome.state.value.scene.boards[0].envelope_mm
        run.window.canvas.zoom_by(3)
        run.window.canvas.centerOn(0, -(r_inner + r_outer) / 2)
        run.save("S07", theme, WIDE, part="zoom3x")


def _s08(run: Run) -> None:
    run.start(C14)
    toggle = run.widget("layer-L2")
    assert isinstance(toggle, QCheckBox)
    toggle.setChecked(False)
    run.focus("layer-L2")
    run.save("S08", L, WIDE)
    toggle.setChecked(True)


def _s09(run: Run) -> None:
    for theme in (L, D):
        run.start(CF11, theme)
        run.window.toolstrip.show_tab(ToolstripTab.VIEW)
        run.focus("act-theme")
        run.save("S09", theme, WIDE)
    tip = run.window.toolstrip.buttons["act-theme"].toolTip()
    run.notes.append(f"not tested: offscreen Qt draws no tooltip; the act-theme tooltip text is {tip!r}")


def _s10(run: Run) -> None:
    run.start(D08)
    run.window.report_internal_error("0123456789ab")
    dialog = run.window.findChild(QMessageBox, "dlg-error")
    assert dialog is not None
    dialog.button(QMessageBox.StandardButton.Ok).setFocus()
    run.save("S10", L, WIDE)
    run.notes.append("raised through report_internal_error, the crash handler's call (UI-12), with a fixed id")
    _close_dialogs(run)


def _s11(run: Run) -> None:
    for theme in (L, D):
        run.start(None, theme, SMALL)
        dialog = run.window.new_design_dialog()
        dialog.show()
        run.focus("param-design-name", dialog)
        run.save("S11", theme, "dialog", dialog)
        dialog.close()


def _s12(run: Run) -> None:
    run.start(None, L, SMALL)
    dialog = run.window.new_design_dialog()
    dialog.show()
    dialog.name.setText("Stator A")
    dialog.topology_buttons[TopologyKind.SPIRAL].setChecked(True)
    run.focus("btn-create-design", dialog)
    run.save("S12", L, "dialog", dialog)
    dialog.close()


def _blank_spiral(run: Run, theme: ThemeName = L) -> None:
    run.start(None, theme)
    run.window.session.new_design(TopologyKind.SPIRAL)
    run.settle()


def _s13(run: Run) -> None:
    for theme in (L, D):
        _blank_spiral(run, theme)
        run.focus("btn-first-missing")
        run.save("S13", theme, WIDE)


def _s14(run: Run) -> None:
    for theme in (L, D):
        run.start(CF11, theme)
        _type(run, "param-r-inner", "-1")
        run.focus("param-r-inner")
        run.save("S14", theme, WIDE)


def _s15(run: Run) -> None:
    for example, part in ((SERP, "serpentine"), (WAVE, "wave")):
        run.start(example)
        _inspector(run, "tab-coil")
        run.focus("param-r-inner")
        run.save("S15", L, WIDE, part=part)


def _s16(run: Run) -> None:
    run.start(SERP)
    _inspector(run, "tab-phases")
    run.focus("param-phase-count")
    run.save("S16", L, WIDE)


def _s17(run: Run) -> None:
    for theme in (L, D):
        run.start(C14, theme)
        _inspector(run, "tab-layers")
        run.focus("param-layer-count")
        run.save("S17", theme, WIDE)


def _s18(run: Run) -> None:
    run.start(WAVE)
    _inspector(run, "tab-layers")
    run.focus("param-wave-layers")
    run.save("S18", L, WIDE)


def _s19(run: Run) -> None:
    run.start(SERP)
    run.window.session.edit("/winding/stack_mode", "one_board_per_phase")
    run.window.session.set_stackup_input("copper_count", 2)
    run.settle()
    run.window.toolstrip.show_tab(ToolstripTab.VIEW)
    run.window.toolstrip.board_picker.setCurrentIndex(2)
    run.focus("board-picker")
    run.save("S19", L, WIDE)
    run.window.toolstrip.show_tab(ToolstripTab.HOME)


def _s20(run: Run) -> None:
    for theme in (L, D):
        run.start(CF11, theme)
        board = _inspector(run, "tab-board")
        if run.widget("screw-table").rowCount() == 0:
            run.widget("btn-screw-add").click()
            run.settle()
            if theme is L:
                run.notes.append("the example has no screw pattern; btn-screw-add added one so its fields show")
        board.ensureWidgetVisible(run.widget("param-screw-angle-offset"))
        board.ensureWidgetVisible(run.widget("screw-table"))
        run.focus("param-screw-hole-diameter")
        board.ensureWidgetVisible(run.widget("param-screw-angle-offset"))
        run.save("S20", theme, WIDE)


def _s21(run: Run) -> None:
    _blank_spiral(run)
    _results(run, "tab-results")
    run.focus("btn-results-first-missing")
    run.save("S21", L, WIDE)


def _s22(run: Run) -> None:
    for size in (WIDE, SMALL):
        for theme in (L, D):
            run.start(CF11, theme, size)
            _results(run, "tab-results")
            toggle = run.widget("res-r-phase-how-toggle")
            if not run.widget("res-r-phase-how").isVisible():
                toggle.click()
            run.window.findChild(QWidget, "results-scroll").ensureWidgetVisible(run.widget("res-r-phase-how"))
            run.focus("res-r-phase-how")
            run.save("S22", theme, size)


def _s23(run: Run) -> None:
    run.start(CF11)
    _results(run, "tab-results")
    _type(run, "param-r-inner", "-1")
    _results(run, "tab-results")
    run.focus("res-r-phase-value")
    run.save("S23", L, WIDE)


def _s24(run: Run) -> None:
    run.start(CF11)
    _results(run, "tab-drc")
    run.focus("drc-summary")
    run.save("S24", L, WIDE)


def _drc_failing(run: Run, theme: ThemeName) -> None:
    run.start(CF11, theme)
    _type(run, "param-min-space", "3")


def _s25(run: Run) -> None:
    for theme in (L, D):
        _drc_failing(run, theme)
        _results(run, "tab-drc")
        table = run.widget("drc-table")
        assert isinstance(table, QTableView)
        if table.model().rowCount():
            table.selectRow(0)
            run.widget("btn-drc-locate").click()
        else:
            run.notes.append("the raised spacing rule gave no failure row")
        run.focus("drc-table")
        run.save("S25", theme, WIDE)


def _s26(run: Run) -> None:
    for theme in (L, D):
        run.start(CF11, theme)
        _results(run, "tab-back-emf")
        table = run.widget("chart-backemf-table")
        if not table.isVisible():
            run.widget("chart-backemf-table-toggle").click()
        run.focus("chart-backemf")
        run.save("S26", theme, WIDE)


def _s27(run: Run) -> None:
    run.start(CF11)
    _results(run, "tab-torque-speed")
    run.focus("chart-torque-speed")
    run.save("S27", L, WIDE)


def _s28(run: Run) -> None:
    run.start(CF11)
    _results(run, "tab-compare")
    run.focus("btn-set-reference")
    run.save("S28", L, WIDE, part="empty")
    run.widget("btn-set-reference").click()
    run.pump()
    confirm = run.window.findChild(QMessageBox, "dlg-compare-confirm")
    if confirm is not None and confirm.isVisible():
        confirm.accept()
    run.start(C14)
    _results(run, "tab-compare")
    run.focus("compare-table")
    run.save("S28", L, WIDE, part="reference")


def _export_dialog(run: Run) -> QDialog:
    run.window.show_export("export_bundle")
    run.pump()
    dialog = run.window.export_dialog
    folder = run.widget("export-folder", dialog)
    assert isinstance(folder, QLineEdit)
    folder.setText("acceptance-export")
    run.pump()
    return dialog


def _s29(run: Run) -> None:
    for theme in (L, D):
        run.start(CF11, theme)
        dialog = _export_dialog(run)
        run.focus("btn-export-run", dialog)
        run.save("S29", theme, "dialog", dialog)
        dialog.close()


def _s30(run: Run) -> None:
    _drc_failing(run, L)
    dialog = _export_dialog(run)
    run.widget("btn-export-run", dialog).click()
    run.pump()
    confirm = run.window.findChild(QMessageBox, "dlg-export-confirm") or run.window.findChild(
        QDialog, "dlg-export-confirm"
    )
    if confirm is None or not confirm.isVisible():
        run.notes.append("no confirmation appeared")
        dialog.close()
        return
    run.save("S30", L, "dialog", confirm)
    run.notes.append(f"focus on {QApplication.focusWidget().objectName() if QApplication.focusWidget() else None}")
    confirm.close()
    dialog.close()


def _s31(run: Run) -> None:
    run.start(CF11)
    dialog = _export_dialog(run)
    run.widget("btn-export-run", dialog).click()
    run.pump()
    run.focus("export-result", dialog)
    run.save("S31", L, "dialog", dialog)
    dialog.close()


def _s32(run: Run) -> None:
    for theme in (L, D):
        run.start(CF11, theme)
        run.window.show_equations("EQ-18")
        guide = run.window.guide
        run.pump()
        run.focus("guide-toc", guide)
        run.save("S32", theme, "window", guide)
        guide.close()


def _s33(run: Run) -> None:
    run.notes.append("not tested: no Tests dialog (`tests-table`) exists in this build (screens.md section 13)")


def _s34(run: Run) -> None:
    for theme in (L, D):
        _drc_failing(run, theme)
        run.focus("statusbar")
        run.save("S34", theme, "crop", run.widget("statusbar"))


def _s35(run: Run) -> None:
    for size in (WIDE, SMALL):
        for theme in (L, D):
            run.start(WAVE, theme, size)
            if size == SMALL:
                tabs = run.window.findChild(QTabWidget, "results-tabs")
                rail = run.widget("results-rail")
                for i in range(tabs.count()):
                    if tabs.widget(i).isAncestorOf(rail):
                        tabs.setCurrentIndex(i)
            run.focus("rail-drc")
            run.save("S35", theme, size)


def _s36(run: Run) -> None:
    run.start(C14, L, WIDE)
    layers = _inspector(run, "tab-layers")
    run.window.resize(*SMALL)
    run.pump()
    layers.ensureWidgetVisible(run.widget("pair-list"))
    run.focus("pair-list")
    run.save("S36", L, SMALL)


def _s37(run: Run) -> None:
    run.start(WAVE)
    _results(run, "tab-drc")
    run.focus("drc-table")
    run.save("S37", L, WIDE)


def _s38(run: Run) -> None:
    for theme in (L, D):
        run.start(D08, theme, SMALL)
        run.window.canvas.fit_view()
        run.focus("fig-canvas")
        run.save("S38", theme, SMALL)


def _s39(run: Run) -> None:
    for theme in (L, D):
        run.start(None, theme)
        gallery = run.window.examples_gallery()
        gallery.show()
        examples = run.widget("examples-list", gallery)
        assert isinstance(examples, QListWidget)
        examples.setCurrentRow(1)
        run.focus("examples-list", gallery)
        run.save("S39", theme, "dialog", gallery)
        gallery.close()


def _s40(run: Run) -> None:
    run.start(D08)
    outcome = run.window.session.current_outcome()
    assert outcome is not None
    pdf = run.out / "S40_report_d08.pdf"
    write_report_pdf(outcome, pdf)
    pages = int(_tool(["pdfinfo", str(pdf)]).split("Pages:")[1].split()[0])
    texts = [_tool(["pdftotext", "-f", str(n), "-l", str(n), str(pdf), "-"]) for n in range(1, pages + 1)]
    last_text = max(n for n, page in enumerate(texts, start=1) if "Inputs" in page or "/winding" in page)
    for page, part in ((1, "page1"), (last_text, "last-text-page"), (pages, "last-page")):
        stem = run.out / f"S40_light_a4-110dpi_{part}"
        _tool(["pdftoppm", "-png", "-r", "110", "-singlefile", "-f", str(page), "-l", str(page), str(pdf), str(stem)])
        run.files.append(stem.with_suffix(".png").name)
    fonts = run.out / "S40_pdffonts.txt"
    fonts.write_text(_tool(["pdffonts", str(pdf)]), encoding="utf-8")
    run.files += [pdf.name, fonts.name]
    run.notes.append(f"{pages} pages; last text page {last_text}; colophon is the last line of page {pages}")


def _s41(run: Run) -> None:
    run.start(D08, L, WIDE)
    run.window.resize(960, 700)
    run.pump(20)
    run.focus("fig-canvas")
    run.save("S41", L, (960, 700))


def _tool(argv: list[str]) -> str:
    return subprocess.run(argv, check=True, capture_output=True, text=True).stdout


ROWS: dict[str, Callable[[Run], None]] = {
    "S01": _s01,
    "S02": _s02,
    "S03": _s03,
    "S04": _canvas_row("S04", CF11),
    "S05": _canvas_row("S05", CF11, greyscale=True),
    "S06": _canvas_row("S06", SERP),
    "S07": _s07,
    "S08": _s08,
    "S09": _s09,
    "S10": _s10,
    "S11": _s11,
    "S12": _s12,
    "S13": _s13,
    "S14": _s14,
    "S15": _s15,
    "S16": _s16,
    "S17": _s17,
    "S18": _s18,
    "S19": _s19,
    "S20": _s20,
    "S21": _s21,
    "S22": _s22,
    "S23": _s23,
    "S24": _s24,
    "S25": _s25,
    "S26": _s26,
    "S27": _s27,
    "S28": _s28,
    "S29": _s29,
    "S30": _s30,
    "S31": _s31,
    "S32": _s32,
    "S33": _s33,
    "S34": _s34,
    "S35": _s35,
    "S36": _s36,
    "S37": _s37,
    "S38": _s38,
    "S39": _s39,
    "S40": _s40,
    "S41": _s41,
}


def _scaling(run: Run) -> None:
    """UI-09: one D08 window at 1280 x 800 logical px, grabbed at the QT_SCALE_FACTOR this process started with."""
    scale = os.environ.get("QT_SCALE_FACTOR", "1")
    run.start(D08)
    run.focus("fig-canvas")
    image = run.window.grab()
    name = f"UI09_light_1280x800_scale{scale}.png"
    image.save(str(run.out / name))
    run.files.append(name)
    run.notes.append(f"device px {image.width()}x{image.height()}, ratio {image.devicePixelRatio()}")


def _fresh_window(folder: Path) -> MainWindow:
    """Open a new shell on its own settings and recovery folder, so a row's shots depend on that row alone."""
    store = QSettingsStore(QSettings(str(folder / "settings.ini"), QSettings.Format.IniFormat))
    window = create_shell(store, ShellPaths(recovery_dir=folder / "recovery"), prefers_dark=lambda: False).window
    window.show()
    return window


def main(argv: list[str]) -> int:
    """Take the rows named in argv (all when none), or the UI-09 shot with --scaling; print one JSON line per row."""
    out = Path(argv[0]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    wanted = [a for a in argv[1:] if a != "--scaling"]
    with tempfile.TemporaryDirectory() as scratch:
        os.environ["HOME"] = scratch
        os.chdir(scratch)
        app = qt_application()
        jobs = {"UI09": _scaling} if "--scaling" in argv else {row: ROWS[row] for row in (wanted or ROWS)}
        for row, take in jobs.items():
            run = Run(app=app, window=_fresh_window(Path(scratch) / row), out=out)
            try:
                take(run)
            except Exception as error:  # a broken row is reported and the others still run
                run.notes.append(f"error: {type(error).__name__}: {error}")
            _close_dialogs(run)
            run.window.close()
            run.window.deleteLater()
            print(json.dumps({"row": row, "files": run.files, "notes": run.notes}), flush=True)
        shutil.rmtree(Path(scratch) / "acceptance-export", ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
