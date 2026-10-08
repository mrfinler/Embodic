"""The shell window: toolstrip, placeholder inspector, geometry canvas, key results rail and status bar.

The design form (U-M4c) and the results, checks and export views (U-M4d) fill the reserved regions later; their
toolstrip commands are known here and stay disabled until those view-models exist.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QAction, QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from embodic.io.examples import list_examples
from embodic.results.status import Status
from embodic.ui.strings import text
from embodic.ui.theme import ThemeName, ThemeTokens, load_theme, resolve_theme
from embodic.ui.viewmodels.appearance import AppearanceViewModel
from embodic.ui.viewmodels.outcome import (
    OutcomeComputing,
    OutcomeEmpty,
    OutcomeFailed,
    OutcomeReady,
    OutcomeState,
    OutcomeViewModel,
    SummaryItem,
    shown_result,
)
from embodic.ui.views import style
from embodic.ui.views.geometry_view import GeometryView
from embodic.ui.views.toolstrip_bar import CommandTable, FocusRingTabBar, ToolstripBar

logger = logging.getLogger(__name__)

MIN_SIZE_PX = (960, 540)
THREE_PANE_FROM_PX = 1280
INSPECTOR_TABS = ("tab-coil", "tab-phases", "tab-layers", "tab-board")
HOME_PLACEHOLDER = "%USERPROFILE%"


def display_path(path: Path) -> str:
    """Return a path for the screen or the log with the home folder replaced by a placeholder (no user name)."""
    home = str(Path.home())
    shown = str(path)
    return HOME_PLACEHOLDER + shown[len(home) :] if shown.startswith(home) else shown


def badge_property(status: Status) -> str:
    """Return the style sheet's ``status`` property value of a trust badge."""
    return status.value.replace(" ", "-")


@dataclass(frozen=True, slots=True, kw_only=True)
class ShellPaths:
    """Where the shell writes: recovery copies of the open project after an internal error."""

    recovery_dir: Path


def _repolish(widget: QWidget) -> None:
    widget.style().unpolish(widget)
    widget.style().polish(widget)


class _SummaryCard(QFrame):
    """One summary strip cell: title, value or check word, trust badge, assumption count."""

    def __init__(self, key: str) -> None:
        super().__init__()
        self.setObjectName(key)
        self.setProperty("class", "result-card")
        layout = QVBoxLayout(self)
        self.title = QLabel()
        self.title.setObjectName(f"{key}-title")
        self.value = QLabel()
        self.value.setObjectName(f"{key}-value")
        self.badge = QLabel()
        self.badge.setObjectName(f"{key}-badge")
        self.badge.setProperty("class", "badge")
        self.asm = QLabel()
        self.asm.setObjectName(f"{key}-asm")
        line = QHBoxLayout()
        line.addWidget(self.value)
        line.addStretch(1)
        line.addWidget(self.badge)
        layout.addWidget(self.title)
        layout.addLayout(line)
        layout.addWidget(self.asm)

    def show_item(self, item: SummaryItem) -> None:
        self.title.setText(item.label)
        self.value.setText(item.value_text)
        self.value.setProperty("class", "check-state" if item.state else "result-value")
        self.value.setProperty("state", item.state or "")
        self.badge.setVisible(item.status is not None)
        if item.status is not None:
            self.badge.setText(text(f"shell.badge.{item.status.value}"))
            self.badge.setProperty("status", badge_property(item.status))
        self.asm.setVisible(item.assumed_count is not None)
        self.asm.setText(text("shell.sum.assumptions", count=item.assumed_count or 0))
        for widget in (self.value, self.badge):
            _repolish(widget)


class MainWindow(QMainWindow):
    """The desktop shell."""

    def __init__(
        self,
        appearance: AppearanceViewModel,
        outcome: OutcomeViewModel,
        paths: ShellPaths,
        os_prefers_dark: Callable[[], bool],
        on_close: Callable[[], None],
    ) -> None:
        super().__init__()
        self.appearance, self.outcome, self.paths = appearance, outcome, paths
        self._on_close = on_close
        self._os_prefers_dark = os_prefers_dark
        self.tokens: ThemeTokens = load_theme("light")
        self.setObjectName("main-window")
        self.setWindowTitle(text("shell.window.title"))
        self.setMinimumSize(*MIN_SIZE_PX)
        self.canvas = GeometryView()
        self.toolstrip = ToolstripBar(self._commands(), self)
        self.addToolBar(self.toolstrip)
        for action in self.toolstrip.actions_by_id.values():
            self.addAction(action)
        self.cards: dict[str, _SummaryCard] = {}
        self.layer_boxes: dict[str, QCheckBox] = {}
        self.setCentralWidget(self._work_area())
        self._status_bar()
        self.error_dialog: QMessageBox | None = None
        outcome.state.subscribe(lambda _: self._render())
        outcome.hidden_layers.subscribe(lambda _: self._render())
        appearance.theme.subscribe(lambda _: self.apply_theme())
        appearance.phase_render_mode.subscribe(lambda _: self._render())
        self.canvas.cursor_moved.connect(self._show_cursor)
        self.apply_theme()

    def _commands(self) -> CommandTable:
        pending = (
            "new_design open_project undo redo set_topology_spiral set_topology_serpentine set_topology_wave "
            "set_connection_star set_connection_delta show_checks show_equations export_svg export_dxf export_pdf "
            "export_bundle"
        ).split()
        implemented: CommandTable = {
            "save_project": self.save_project_dialog,
            "show_examples": self.show_examples_menu,
            "compute_now": self.outcome.compute_now,
            "cycle_theme": self.appearance.cycle_theme,
            "toggle_phase_render_mode": self.appearance.toggle_phase_render_mode,
            "fit_view": self.canvas.fit_view,
        }
        return {**dict.fromkeys(pending), **implemented}

    def _work_area(self) -> QWidget:
        inspector = QWidget()
        inspector.setObjectName("inspector")
        tabs = QTabWidget()
        tabs.setObjectName("inspector-tabs")
        self.inspector_tab_bar = FocusRingTabBar()
        tabs.setTabBar(self.inspector_tab_bar)
        for name in INSPECTOR_TABS:
            page = QLabel(text("shell.inspector.placeholder"))
            page.setObjectName(name)
            page.setProperty("class", "hint")
            page.setAlignment(Qt.AlignmentFlag.AlignCenter)
            tabs.addTab(page, text(f"shell.{name}.label"))
        QVBoxLayout(inspector).addWidget(tabs)

        self.centre = QStackedWidget()
        self.centre.setObjectName("centre")
        self.centre.addWidget(self._empty_page())
        self.centre.addWidget(self._canvas_page())

        rail = QWidget()
        rail.setObjectName("results-rail")
        rail_layout = QVBoxLayout(rail)
        title = QLabel(text("shell.results-rail.title"))
        title.setProperty("class", "section-title")
        self.rail_empty = QLabel(text("shell.results-rail.empty"))
        self.rail_empty.setObjectName("results-rail-empty")
        self.rail_empty.setWordWrap(True)
        self.rail_empty.setProperty("class", "hint")
        rail_layout.addWidget(title)
        rail_layout.addWidget(self.rail_empty)
        for key in ("sum-ok", "sum-drc", "sum-ke", "sum-r-phase"):
            self.cards[key] = _SummaryCard(key)
            rail_layout.addWidget(self.cards[key])
        rail_layout.addStretch(1)

        self.splitter = QSplitter()
        self.splitter.setObjectName("work-area")
        for pane in (inspector, self.centre, rail):
            self.splitter.addWidget(pane)
        self.splitter.setStretchFactor(1, 1)
        return self.splitter

    def _empty_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("empty-state")
        layout = QVBoxLayout(page)
        layout.addStretch(1)
        title = QLabel(text("shell.empty.title"))
        title.setProperty("class", "section-title")
        body = QLabel(text("shell.empty.body"))
        body.setProperty("class", "hint")
        buttons = QHBoxLayout()
        self.empty_new = QPushButton(text("shell.empty-new.label"))
        self.empty_new.setObjectName("btn-empty-new")
        self.empty_new.setEnabled(False)
        self.empty_new.setToolTip(text("toolstrip.unavailable.reason"))
        self.empty_examples = QPushButton(text("shell.empty-examples.label"))
        self.empty_examples.setObjectName("btn-empty-examples")
        self.empty_examples.setProperty("class", "primary")
        self.empty_examples.clicked.connect(lambda: self.show_examples_menu(self.empty_examples))
        for widget in (title, body):
            widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(widget)
        buttons.addStretch(1)
        buttons.addWidget(self.empty_new)
        buttons.addWidget(self.empty_examples)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        layout.addStretch(1)
        return page

    def _canvas_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        self.layer_bar = QWidget()
        self.layer_bar.setObjectName("layer-toggles")
        self.layer_bar_layout = QHBoxLayout(self.layer_bar)
        self.layer_bar_layout.addWidget(QLabel(text("shell.layers.title")))
        self.layer_bar_layout.addStretch(1)
        layout.addWidget(self.layer_bar)
        layout.addWidget(self.canvas, 1)
        return page

    def _status_bar(self) -> None:
        bar = QStatusBar()
        bar.setObjectName("statusbar")
        self.status: dict[str, QLabel] = {}
        for name in ("st-compute", "st-drc", "st-counts", "st-units", "st-cursor"):
            label = QLabel()
            label.setObjectName(name)
            self.status[name] = label
            if name == "st-compute":
                bar.addWidget(label, 1)
            else:
                bar.addPermanentWidget(label)
        self.status["st-units"].setText(text("shell.st-units.text"))
        self.setStatusBar(bar)

    def apply_theme(self) -> None:
        """Resolve the theme choice against the OS and restyle the whole application with it."""
        name = resolve_theme(self.appearance.theme.value, self._os_prefers_dark())
        self.tokens = load_theme(name)
        app = QApplication.instance()
        assert isinstance(app, QApplication)
        style.apply_theme(app, self.tokens)
        self.toolstrip.apply_theme(self.tokens)
        self.inspector_tab_bar.set_ring(self.tokens)
        self._render()

    def on_os_scheme_changed(self) -> None:
        """Follow an OS light / dark change while the choice is 'system'."""
        if self.appearance.theme.value is ThemeName.SYSTEM:
            self.apply_theme()

    def _render(self) -> None:
        state: OutcomeState = self.outcome.state.value
        shown = shown_result(state)
        self.centre.setCurrentIndex(0 if isinstance(state, OutcomeEmpty) else 1)
        compute_word = {OutcomeComputing: "updating", OutcomeFailed: "error"}.get(type(state), "ready")
        self.status["st-compute"].setText(text(f"shell.st-compute.{compute_word}"))
        self.rail_empty.setVisible(shown is None)
        for card in self.cards.values():
            card.setVisible(shown is not None)
        if shown is None:
            self.status["st-drc"].setText(text("shell.st-drc.none"))
            self.status["st-counts"].setText("")
            return
        for item in shown.summary:
            self.cards[item.key].show_item(item)
        self._show_counts(shown)
        scene = shown.scene
        self._sync_layer_boxes(scene.layers if scene else ())
        self.canvas.show_geometry(
            scene, self.tokens, self.appearance.phase_render_mode.value, self.outcome.hidden_layers.value
        )

    def _show_counts(self, shown: OutcomeReady) -> None:
        drc = shown.outcome.drc
        failures = sum(r.violation_count for r in drc) if drc is not None else 0
        if drc is None:
            self.status["st-drc"].setText(text("shell.st-drc.none"))
        elif failures == 0:
            self.status["st-drc"].setText(text("shell.st-drc.pass"))
        else:
            self.status["st-drc"].setText(text("shell.st-drc.fail", count=failures))
        scene = shown.scene
        if scene is None:
            self.status["st-counts"].setText("")
            return
        coils = {(m.phase, m.label) for m in scene.marks}
        vias = sum(len(board.vias) for board in scene.boards)
        self.status["st-counts"].setText(
            text("shell.st-counts.text", layers=len(scene.layers), coils=len(coils), vias=vias)
        )

    def _sync_layer_boxes(self, layers: tuple[str, ...]) -> None:
        if tuple(self.layer_boxes) != layers:
            for box in self.layer_boxes.values():
                box.deleteLater()
            self.layer_boxes = {}
            for index, layer in enumerate(layers):
                box = QCheckBox(layer)
                box.setObjectName(f"layer-{layer}")
                box.toggled.connect(lambda checked, name=layer: self.outcome.set_layer_visible(name, checked))
                self.layer_bar_layout.insertWidget(1 + index, box)
                self.layer_boxes[layer] = box
        for layer, box in self.layer_boxes.items():
            box.blockSignals(True)
            box.setChecked(layer not in self.outcome.hidden_layers.value)
            box.blockSignals(False)

    def _show_cursor(self, x_mm: float, y_mm: float) -> None:
        self.status["st-cursor"].setText(text("shell.st-cursor.text", x=f"{x_mm:.2f}", y=f"{y_mm:.2f}"))

    def examples_menu(self) -> QMenu:
        """Return a menu with one entry per packaged example."""
        menu = QMenu(text("shell.examples-menu.title"), self)
        menu.setObjectName("menu-examples")
        for info in list_examples():
            action = QAction(info.title, menu)
            action.setObjectName(f"example-{info.example_id}")
            action.setToolTip(info.source_note)
            action.triggered.connect(lambda _=False, example_id=info.example_id: self.outcome.open_example(example_id))
            menu.addAction(action)
        return menu

    def show_examples_menu(self, anchor: QWidget | None = None) -> None:
        """Open the examples menu under its button."""
        anchor = anchor or self.toolstrip.buttons["act-examples"]
        self.examples_menu().popup(anchor.mapToGlobal(QPoint(0, anchor.height())))

    def save_project_dialog(self) -> None:
        """Ask for a file name and save the open project."""
        if self.outcome.project is None:
            return
        name, _ = QFileDialog.getSaveFileName(self, text("shell.save.title"), "", text("shell.save.filter"))
        if name:
            self.outcome.save_project(Path(name))

    def save_recovery(self, correlation_id: str) -> Path | None:
        """Save the open project next to the log; return the file, or None when no project is open."""
        if self.outcome.project is None:
            return None
        self.paths.recovery_dir.mkdir(parents=True, exist_ok=True)
        path = self.paths.recovery_dir / f"recovery-{correlation_id}.embodic.json"
        self.outcome.save_project(path)
        logger.info("project saved to %s", display_path(path), extra={"correlation_id": correlation_id})
        return path

    def report_internal_error(self, correlation_id: str) -> None:
        """Save the project and show the English error message; the program keeps running (REQ-N-18)."""
        saved = self.save_recovery(correlation_id)
        body = text(
            "shell.error.body",
            saved=display_path(saved) if saved else text("shell.error.not-saved"),
            correlation_id=correlation_id,
        )
        dialog = QMessageBox(
            QMessageBox.Icon.Critical, text("shell.error.title"), body, QMessageBox.StandardButton.Ok, self
        )
        dialog.setObjectName("dlg-error")
        dialog.open()
        self.error_dialog = dialog

    def on_compute_failed(self, request_id: int, correlation_id: str) -> None:
        """Show a worker crash report when it belongs to the latest request."""
        self.outcome.on_failed(request_id, correlation_id)
        if isinstance(self.outcome.state.value, OutcomeFailed):
            self.report_internal_error(correlation_id)

    def resizeEvent(self, event) -> None:  # noqa: N802 (Qt override)
        """Size the side panes for the two-pane and three-pane widths (design_spec.md section 5)."""
        super().resizeEvent(event)
        wide = self.width() >= THREE_PANE_FROM_PX
        side = (340, 360) if wide else (240, 240)
        self.splitter.setSizes([side[0], max(self.width() - sum(side), 100), side[1]])

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 (Qt override)
        """Stop the compute worker before the window goes."""
        self._on_close()
        super().closeEvent(event)
