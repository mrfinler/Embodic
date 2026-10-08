"""The shell window: toolstrip, inspector with the design form, geometry canvas, key results rail and status bar.

The design session (U-M4c) drives the inspector, the undo history and what the canvas draws. Below the canvas the
results tabs (U-M4d) show the result cards, DRC, charts and the comparison of the same shown outcome.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from pathlib import Path

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from embodic.errors import ValidationIssue
from embodic.io.examples import list_examples
from embodic.model.vocabulary import TopologyKind
from embodic.outcome import ComputeOutcome
from embodic.results import Registry
from embodic.ui.strings import text
from embodic.ui.theme import ThemeName, ThemeTokens, load_theme, resolve_theme
from embodic.ui.viewmodels.appearance import AppearanceViewModel
from embodic.ui.viewmodels.export import PRESETS, ExportViewModel
from embodic.ui.viewmodels.outcome import (
    OutcomeComputing,
    OutcomeEmpty,
    OutcomeFailed,
    OutcomeReady,
    OutcomeState,
    OutcomeViewModel,
    coil_count,
)
from embodic.ui.viewmodels.results import (
    CompareViewModel,
    DrcTable,
    ResultsViewModel,
    drc_card,
    drc_table,
    inputs_card,
    topic_for,
)
from embodic.ui.viewmodels.session import (
    DesignSession,
    SessionDrafting,
    SessionEmpty,
    tab_of_widget,
    widget_for_pointer,
)
from embodic.ui.views import style
from embodic.ui.views.board_rotor_panel import BoardRotorPanel
from embodic.ui.views.charts import BackEmfTab, TorqueSpeedTab
from embodic.ui.views.checks_view import DrcTab, locate_on_canvas
from embodic.ui.views.coil_panel import CoilPanel, FieldPanel
from embodic.ui.views.equation_view import GuideWindow
from embodic.ui.views.examples_gallery import ExamplesGallery
from embodic.ui.views.export_view import ExportDialog
from embodic.ui.views.geometry_view import GeometryView
from embodic.ui.views.layer_panel import LayerPanel
from embodic.ui.views.new_design_dialog import NewDesignDialog
from embodic.ui.views.phase_panel import PhasePanel
from embodic.ui.views.results_rail import ResultsRail
from embodic.ui.views.results_view import CompareTab, ResultsTab, focus_ring_qss
from embodic.ui.views.toolstrip_bar import CommandTable, ToolstripBar

logger = logging.getLogger(__name__)

MIN_SIZE_PX = (960, 540)
THREE_PANE_FROM_PX = 1280
INSPECTOR_PX = (300, 340)  # two-pane and three-pane widths (design_spec.md section 5)
RAIL_PX = 360
HOME_PLACEHOLDER = "%USERPROFILE%"
EXPORT_ACTIONS = ("act-export-svg", "act-export-dxf", "act-export-pdf", "act-export-all")


def redact_home(text_with_paths: str) -> str:
    """Return text for the screen or the log with the home folder replaced by a placeholder (no user name)."""
    return text_with_paths.replace(str(Path.home()), HOME_PLACEHOLDER)


@dataclass(frozen=True, slots=True, kw_only=True)
class ShellPaths:
    """Where the shell writes: recovery copies of the open project after an internal error."""

    recovery_dir: Path


class MainWindow(QMainWindow):
    """The desktop shell."""

    def __init__(
        self,
        appearance: AppearanceViewModel,
        outcome: OutcomeViewModel,
        session: DesignSession,
        paths: ShellPaths,
        os_prefers_dark: Callable[[], bool],
        on_close: Callable[[], None],
        *,
        registry: Registry,
    ) -> None:
        super().__init__()
        self.appearance, self.outcome, self.session, self.paths = appearance, outcome, session, paths
        self.registry = registry
        self.results = ResultsViewModel(registry)
        self.compare = CompareViewModel()
        self.export_vm = ExportViewModel(self._export_source)
        self.guide: GuideWindow | None = None
        self.export_dialog: ExportDialog | None = None
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
        self.layer_boxes: dict[str, QCheckBox] = {}
        self.setCentralWidget(self._work_area())
        self._status_bar()
        outcome.state.subscribe(lambda _: self._render())
        outcome.hidden_layers.subscribe(lambda _: self._render())
        session.state.subscribe(lambda _: self._on_session())
        session.issues.subscribe(lambda _: self._show_issues())
        session.notice.subscribe(lambda _: self._show_notice())
        for action_id, available in (("act-undo", session.can_undo), ("act-redo", session.can_redo)):
            action = self.toolstrip.actions_by_id[action_id]
            action.setEnabled(available.value)
            available.subscribe(action.setEnabled)
        appearance.theme.subscribe(lambda _: self.apply_theme())
        appearance.phase_render_mode.subscribe(lambda _: self._render())
        self.canvas.cursor_moved.connect(self._show_cursor)
        self._shortcuts()
        self.apply_theme()
        self._show_issues()
        self._on_session()

    def _commands(self) -> CommandTable:
        pending = ["open_project"]
        session = self.session
        implemented: CommandTable = {
            "new_design": self.show_new_design,
            "undo": session.undo,
            "redo": session.redo,
            **{f"set_topology_{t.value}": partial(session.set_topology, t) for t in TopologyKind},
            **{f"set_connection_{c}": partial(session.edit, "/connection/topology", c) for c in ("star", "delta")},
            "save_project": self.save_project_dialog,
            "show_examples": self.show_examples,
            "compute_now": self.compute_now,
            "cycle_theme": self.appearance.cycle_theme,
            "toggle_phase_render_mode": self.appearance.toggle_phase_render_mode,
            "fit_view": self.canvas.fit_view,
            "show_checks": partial(self.show_results_tab, "tab-drc"),
            "show_equations": self.show_equations,
            **{command: partial(self.show_export, command) for command in PRESETS},
        }
        return {**dict.fromkeys(pending), **implemented}

    def _work_area(self) -> QWidget:
        inspector = QWidget()
        inspector.setObjectName("inspector")
        self.inspector_tabs = QTabWidget()
        self.inspector_tabs.setObjectName("inspector-tabs")
        self.panels: dict[str, FieldPanel] = {}
        for panel in (
            CoilPanel(self.session),
            PhasePanel(self.session),
            LayerPanel(self.session),
            BoardRotorPanel(self.session),
        ):
            self.panels[panel.tab] = panel
            self.inspector_tabs.addTab(panel, text(f"shell.{panel.tab}.label"))
        inspector_layout = QVBoxLayout(inspector)
        inspector_layout.addWidget(self._required_bar())
        inspector_layout.addWidget(self._notice_bar())
        inspector_layout.addWidget(self.inspector_tabs, 1)

        self.centre = QStackedWidget()
        self.centre.setObjectName("centre")
        self.centre.addWidget(self._empty_page())
        self.centre_split = QSplitter(Qt.Orientation.Vertical)
        self.centre_split.setObjectName("centre-split")
        self.centre_split.addWidget(self._canvas_page())
        self.centre_split.addWidget(self._results_tabs())
        self.centre_split.setStretchFactor(0, 3)
        self.centre_split.setStretchFactor(1, 2)
        self.centre.addWidget(self.centre_split)

        rail = self.rail = ResultsRail(self.results, self.registry)
        rail.show_drc.connect(partial(self.show_results_tab, "tab-drc"))
        rail.open_equation.connect(self.show_equations)
        rail_layout = rail.body
        issues_title = QLabel(text("rail.issues.title"))
        issues_title.setProperty("class", "section-title")
        self.issues_list = QListWidget()
        self.issues_list.setObjectName("issues-list")
        self.issues_list.itemActivated.connect(self._issue_activated)
        self.issues_list.itemClicked.connect(self._issue_activated)
        self.issues_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        self.issue_apply = QPushButton()
        self.issue_apply.setObjectName("btn-apply-suggestion")
        self.issue_apply.clicked.connect(self._apply_selected_suggestion)
        self.issues_list.currentItemChanged.connect(lambda *_: self._show_apply())
        rail_layout.addWidget(issues_title)
        rail_layout.addWidget(self.issues_list, 1)
        rail_layout.addWidget(self.issue_apply)
        rail_layout.addStretch(1)

        self.rail_scroll = QScrollArea()
        self.rail_scroll.setObjectName("rail-scroll")
        self.rail_scroll.setWidgetResizable(True)
        self.rail_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.rail_scroll.setWidget(rail)

        self.splitter = QSplitter()
        self.splitter.setObjectName("work-area")
        for pane in (inspector, self.centre, self.rail_scroll):
            self.splitter.addWidget(pane)
        self.splitter.setStretchFactor(1, 1)
        return self.splitter

    def _results_tabs(self) -> QTabWidget:
        self.results_tabs = QTabWidget()
        self.results_tabs.setObjectName("results-tabs")
        self.results_tab = ResultsTab(self.results, self.focus_first_missing)
        self.results_tab.open_equation.connect(self.show_equations)
        self.drc_tab = DrcTab()
        self.drc_tab.locate_requested.connect(lambda row: locate_on_canvas(self.canvas, row, self.tokens))
        self.back_emf_tab = BackEmfTab()
        self.torque_speed_tab = TorqueSpeedTab()
        self.compare_tab = CompareTab(self.compare)
        for tab in (self.results_tab, self.drc_tab, self.back_emf_tab, self.torque_speed_tab, self.compare_tab):
            self.results_tabs.addTab(tab, text(f"results.{tab.objectName()}.label"))
        for panel in (*self.back_emf_tab.panels, *self.torque_speed_tab.panels, self.compare_tab.chart):
            panel.eq.activated.connect(self.show_equations)
        return self.results_tabs

    def _shortcuts(self) -> None:
        for keys, slot in (
            ("F1", self.show_help),
            ("Alt+5", partial(self.show_results_tab, "tab-results")),
            ("Alt+6", partial(self.show_results_tab, "tab-drc")),
        ):
            shortcut = QShortcut(QKeySequence(keys), self)
            shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
            shortcut.activated.connect(slot)

    def show_results_tab(self, tab_id: str) -> None:
        """Bring a results tab forward (Alt+5 Results, Alt+6 DRC, the DRC command and the status bar link)."""
        tab = self.results_tabs.findChild(QWidget, tab_id)
        if tab is not None:
            self.results_tabs.setCurrentWidget(tab)

    def guide_window(self) -> GuideWindow:
        """Return the guide window, created on first use."""
        if self.guide is None:
            self.guide = GuideWindow(self.registry, self)
        return self.guide

    def show_equations(self, eq_id: str | None = None) -> None:
        """Open the equation register at an entry (an EQ chip) or at its first entry (the toolstrip)."""
        guide = self.guide_window()
        guide.show_topic(eq_id or next(iter(self.registry.equations)))
        guide.show()
        guide.raise_()

    def show_help(self) -> None:
        """F1: open the guide at the topic of the focused widget (its whatsThis or a parent's)."""
        widget = QApplication.focusWidget()
        hint = None
        while widget is not None and not hint:
            hint = widget.whatsThis() or None
            widget = widget.parentWidget()
        guide = self.guide_window()
        guide.show_topic(topic_for(hint, self.registry))
        guide.show()
        guide.raise_()

    def _export_source(self) -> tuple[ComputeOutcome | None, bool]:
        shown, outdated = self.session.drawn(self.outcome.state.value)
        return (None, False) if shown is None else (shown.outcome, outdated)

    def show_export(self, command: str) -> None:
        """Open the Export dialog with the format of a toolstrip command checked."""
        dialog = ExportDialog(self.export_vm, PRESETS[command], self.tokens, self)
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.export_dialog = dialog
        dialog.open()

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
        self.empty_new.clicked.connect(self.show_new_design)
        self.empty_examples = QPushButton(text("shell.empty-examples.label"))
        self.empty_examples.setObjectName("btn-empty-examples")
        self.empty_examples.setProperty("class", "primary")
        self.empty_examples.clicked.connect(self.show_examples)
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
        self.stale_label = QLabel()
        self.stale_label.setObjectName("fig-stale")
        self.stale_label.setProperty("class", "notice")
        self.stale_label.setWordWrap(True)
        self.stale_label.setVisible(False)
        layout.addWidget(self.layer_bar)
        layout.addWidget(self.stale_label)
        layout.addWidget(self.canvas, 1)
        return page

    def _required_bar(self) -> QWidget:
        bar = self.required_bar = QWidget()
        bar.setObjectName("required-bar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        self.required_count = QLabel()
        self.required_count.setObjectName("new-required-count")
        self.required_count.setProperty("class", "hint")
        self.first_missing = QPushButton(text("btn-first-missing.label"))
        self.first_missing.setObjectName("btn-first-missing")
        self.first_missing.clicked.connect(self.focus_first_missing)
        layout.addWidget(self.required_count, 1)
        layout.addWidget(self.first_missing)
        return bar

    def _notice_bar(self) -> QWidget:
        self.notice = QFrame()
        self.notice.setObjectName("design-notice")
        self.notice.setProperty("class", "notice")
        layout = QHBoxLayout(self.notice)
        self.notice_text = QLabel()
        self.notice_text.setObjectName("design-notice-text")
        self.notice_text.setWordWrap(True)
        undo = QPushButton(text("design.notice.undo"))
        undo.setObjectName("btn-notice-undo")
        undo.clicked.connect(self.session.undo)
        layout.addWidget(self.notice_text, 1)
        layout.addWidget(undo)
        self.notice.setVisible(False)
        return self.notice

    def _on_session(self) -> None:
        state = self.session.state.value
        for panel in self.panels.values():
            panel.refresh()
        drafting = isinstance(state, SessionDrafting)
        missing = len(state.missing) if isinstance(state, SessionDrafting) else 0
        self.required_count.setText(
            text("new-required-count.one") if missing == 1 else text("new-required-count.text", count=missing)
        )
        self.required_bar.setVisible(drafting)
        compute = self.toolstrip.actions_by_id["act-compute"]
        compute.setEnabled(not drafting)
        head = text("act-compute.label") + f" ({compute.shortcut().toString()})."
        reason = f"{self.required_count.text()}." if drafting else text("act-compute.tooltip")
        compute.setToolTip(f"{head} {reason}")
        self.setWindowTitle(self.session.title())
        self._render()

    def _show_stale(self, outdated: bool) -> None:
        state = self.session.state.value
        if isinstance(state, SessionDrafting):
            message = text("design.stale.drafting", count=len(state.missing))
        else:
            message = text("design.stale.invalid")
        self.stale_label.setText(message)
        self.stale_label.setVisible(outdated)

    def _show_issues(self) -> None:
        self.issues_list.clear()
        for found in self.session.issues.value:
            item = QListWidgetItem(found.message)
            item.setData(Qt.ItemDataRole.UserRole, found)
            item.setToolTip(found.code)
            self.issues_list.addItem(item)
        if not self.session.issues.value:
            self.issues_list.addItem(QListWidgetItem(text("rail.issues.none")))
        self._show_apply()

    def _selected_issue(self) -> ValidationIssue | None:
        item = self.issues_list.currentItem()
        found = None if item is None else item.data(Qt.ItemDataRole.UserRole)
        return found if isinstance(found, ValidationIssue) else None

    def _show_apply(self) -> None:
        found = self._selected_issue()
        suggestion = None if found is None else found.suggestion
        self.issue_apply.setVisible(suggestion is not None)
        if suggestion is not None:
            self.issue_apply.setText(text("design.issue.apply", value=suggestion.proposed_value))

    def _apply_selected_suggestion(self) -> None:
        found = self._selected_issue()
        if found is not None and found.suggestion is not None:
            self.session.apply_suggestion(found.suggestion)

    def _issue_activated(self, item: QListWidgetItem) -> None:
        found = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(found, ValidationIssue) and found.pointers:
            self.focus_pointer(found.pointers[0])

    def _show_notice(self) -> None:
        notice = self.session.notice.value
        self.notice.setVisible(notice is not None)
        self.notice_text.setText("" if notice is None else notice.text)

    def focus_pointer(self, pointer: str) -> bool:
        """Open the tab of the input that fills a pointer and focus it (UI-14, btn-first-missing)."""
        document = self.session.document
        if document is None:
            return False
        widget_id = widget_for_pointer(pointer, document.draft)
        if widget_id is None:
            return False
        panel = self.panels.get(tab_of_widget(widget_id, document.draft.topology))
        if panel is None:
            return False
        self.inspector_tabs.setCurrentWidget(panel)
        return panel.focus_widget(widget_id)

    def focus_first_missing(self) -> None:
        """Focus the input of the first missing required field."""
        state = self.session.state.value
        if isinstance(state, SessionDrafting) and state.missing:
            self.focus_pointer(state.missing[0])

    def new_design_dialog(self) -> NewDesignDialog:
        """Return the New design dialog for this window's session."""
        dialog = NewDesignDialog(self.session, self)
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        return dialog

    def show_new_design(self) -> None:
        """Open the New design dialog."""
        self.new_design_dialog().open()

    def examples_gallery(self) -> ExamplesGallery:
        """Return the Examples gallery for this window's session."""
        gallery = ExamplesGallery(self.session, self)
        gallery.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        return gallery

    def show_examples(self) -> None:
        """Open the Examples gallery."""
        self.examples_gallery().open()

    def compute_now(self) -> None:
        """Compute the open design again (F5); a project the shell opened directly recomputes through the shell."""
        if isinstance(self.session.state.value, SessionEmpty):
            self.outcome.compute_now()
        else:
            self.session.compute_now()

    def offer_recovery(self, path: Path) -> QMessageBox:
        """Ask whether to recover the design autosaved before the last unclean exit (UI-21)."""
        dialog = QMessageBox(
            QMessageBox.Icon.Question,
            text("recovery.title"),
            text("recovery.body"),
            QMessageBox.StandardButton.NoButton,
            self,
        )
        dialog.setObjectName("dlg-recovery")
        recover = dialog.addButton(text("recovery.recover"), QMessageBox.ButtonRole.AcceptRole)
        recover.setObjectName("btn-recover")
        discard = dialog.addButton(text("recovery.discard"), QMessageBox.ButtonRole.RejectRole)
        discard.setObjectName("btn-discard-recovery")
        recover.clicked.connect(lambda: self.session.open_project(path))
        discard.clicked.connect(lambda: path.unlink(missing_ok=True))
        dialog.open()
        return dialog

    def _status_bar(self) -> None:
        bar = QStatusBar()
        bar.setObjectName("statusbar")
        self.status: dict[str, QLabel] = {}
        for name in ("st-compute", "st-drc", "st-counts", "st-units", "st-cursor"):
            label = QLabel()
            label.setObjectName(name)
            self.status[name] = label
            if name == "st-drc":
                label.setTextFormat(Qt.TextFormat.RichText)
                label.linkActivated.connect(lambda _: self.show_results_tab("tab-drc"))
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
        for region in (self.results_tabs, self.rail_scroll):
            region.setStyleSheet(focus_ring_qss(self.tokens))
        self._render()

    def on_os_scheme_changed(self) -> None:
        """Follow an OS light / dark change while the choice is 'system'."""
        if self.appearance.theme.value is ThemeName.SYSTEM:
            self.apply_theme()

    def _render(self) -> None:
        state: OutcomeState = self.outcome.state.value
        shown, outdated = self.session.drawn(state)
        empty = isinstance(state, OutcomeEmpty) and isinstance(self.session.state.value, SessionEmpty)
        self.centre.setCurrentIndex(0 if empty else 1)
        self._show_stale(outdated)
        compute_word = {OutcomeComputing: "updating", OutcomeFailed: "error"}.get(type(state), "ready")
        self.status["st-compute"].setText(text(f"shell.st-compute.{compute_word}"))
        outcome = shown.outcome if shown else None
        table = drc_table(outcome)
        self._render_results(state, outcome, table, outdated)
        cards = None if table is None else (inputs_card(self.session.issues.value), drc_card(table))
        self.rail.show_cards(cards, self.tokens, stale=outdated)
        for action_id in EXPORT_ACTIONS:
            self.toolstrip.actions_by_id[action_id].setEnabled(shown is not None)
        if shown is None:
            self.status["st-drc"].setText(text("shell.st-drc.none"))
            self.status["st-counts"].setText("")
            self._sync_layer_boxes(())
            self.canvas.show_geometry(
                None, self.tokens, self.appearance.phase_render_mode.value, self.outcome.hidden_layers.value
            )
            return
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
            word = text("shell.st-drc.none")
        elif failures == 0:
            word = text("shell.st-drc.pass")
        else:
            word = text("shell.st-drc.fail", count=failures)
        ink = self.tokens.colours["text-1"]
        self.status["st-drc"].setText(f'<a href="tab-drc" style="color: {ink}; text-decoration: underline">{word}</a>')
        scene = shown.scene
        if scene is None:
            self.status["st-counts"].setText("")
            return
        vias = sum(len(board.vias) for board in scene.boards)
        self.status["st-counts"].setText(
            text("shell.st-counts.text", layers=len(scene.layers), coils=coil_count(scene), vias=vias)
        )

    def _render_results(
        self, state: OutcomeState, outcome: ComputeOutcome | None, table: DrcTable | None, outdated: bool
    ) -> None:
        mode = self.appearance.phase_render_mode.value
        self.results.show(outcome.analysis if outcome else None, stale=outdated)
        self.results_tab.set_tokens(self.tokens)
        self.results_tab.set_computing(isinstance(state, OutcomeComputing))
        self.drc_tab.show_table(table, self.tokens)
        self.back_emf_tab.show_outcome(outcome, self.tokens, mode)
        self.torque_speed_tab.show_outcome(outcome, self.tokens, mode)
        self.compare_tab.show_outcome(outcome, self.tokens)

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
        menu.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        for info in list_examples():
            action = QAction(info.title, menu)
            action.setObjectName(f"example-{info.example_id}")
            action.setToolTip(info.source_note)
            action.triggered.connect(lambda _=False, example_id=info.example_id: self.session.load_example(example_id))
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
        """Save the open design or draft next to the log; return the file, or None when nothing is open."""
        if self.session.document is None and self.outcome.project is None:
            return None
        self.paths.recovery_dir.mkdir(parents=True, exist_ok=True)
        path = self.paths.recovery_dir / f"recovery-{correlation_id}.embodic.json"
        if self.session.document is not None:
            self.session.save_project(path)
        else:
            self.outcome.save_project(path)
        logger.info("project saved to %s", path, extra={"correlation_id": correlation_id})
        return path

    def report_internal_error(self, correlation_id: str) -> None:
        """Save the project and show the English error message; the program keeps running (REQ-N-18)."""
        saved = self.save_recovery(correlation_id)
        body = text(
            "shell.error.body",
            saved=redact_home(str(saved)) if saved else text("shell.error.not-saved"),
            correlation_id=correlation_id,
        )
        dialog = QMessageBox(
            QMessageBox.Icon.Critical, text("shell.error.title"), body, QMessageBox.StandardButton.Ok, self
        )
        dialog.setObjectName("dlg-error")
        dialog.open()

    def on_compute_failed(self, request_id: int, correlation_id: str) -> None:
        """Show a worker crash report when it belongs to the latest request."""
        self.outcome.on_failed(request_id, correlation_id)
        if isinstance(self.outcome.state.value, OutcomeFailed):
            self.report_internal_error(correlation_id)

    def _place_rail(self, wide: bool) -> None:
        """From 1280 px the rail is the third pane; below it the rail is the first results tab (design_spec.md 5)."""
        index = self.results_tabs.indexOf(self.rail_scroll)
        if wide and index >= 0:
            self.results_tabs.removeTab(index)
            self.splitter.addWidget(self.rail_scroll)
            self.rail_scroll.show()
        elif not wide and index < 0:
            self.results_tabs.insertTab(0, self.rail_scroll, text("shell.results-rail.title"))

    def resizeEvent(self, event) -> None:  # noqa: N802 (Qt override)
        """Size the panes for the two-pane and three-pane widths (design_spec.md section 5)."""
        super().resizeEvent(event)
        wide = self.width() >= THREE_PANE_FROM_PX
        self._place_rail(wide)
        panes = self.splitter.width() - self.splitter.handleWidth() * (self.splitter.count() - 1)
        inspector = INSPECTOR_PX[wide]
        side = (RAIL_PX,) if wide else ()
        self.splitter.setSizes([inspector, max(panes - inspector - sum(side), 100), *side])

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 (Qt override)
        """Stop the compute worker before the window goes; a clean exit leaves no autosave to recover."""
        self._on_close()
        self.session.discard_autosave()
        super().closeEvent(event)
