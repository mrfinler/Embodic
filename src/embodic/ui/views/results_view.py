"""The Results tab (one card per quantity) and the Compare tab (screens.md sections 6 and 10).

A card shows title, value, unit, one trust badge, the EQ chip, the assumptions tag and the "How was this computed"
disclosure; every part reads the `ResultRow`, never a constant (D-007).
"""

from collections.abc import Callable

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer, Signal
from PySide6.QtGui import QGuiApplication, QResizeEvent
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from embodic.outcome import ComputeOutcome
from embodic.results import Registry
from embodic.results.status import Status
from embodic.ui.strings import text
from embodic.ui.theme import ThemeTokens
from embodic.ui.viewmodels.results import (
    CompareRow,
    CompareViewModel,
    ResultRow,
    ResultsViewModel,
    compare_chart,
    compare_rows,
    disclosure,
    result_key,
)
from embodic.ui.views.charts import ChartPanel, delta_icon
from embodic.ui.views.dialogs import confirm_replace_reference
from embodic.ui.views.status_badge import AssumptionTag, EqChip, StatusBadge, badge_property, repolish

COMPUTING_DIM_AFTER_MS = 300
COMPUTING_OPACITY = 0.6
REVEAL_MS = 120
CARD_MIN_WIDTH_PX = 300


# Agent 1's style sheets ring buttons and fields; the chips, tags and scroll areas of the results area need it too.
FOCUS_QSS = """
QLabel[class="eq-chip"]:focus, QToolButton[class="asm-tag"]:focus, QScrollArea:focus {{
    border: {width}px solid {ring};
}}
"""


def focus_ring_qss(tokens: ThemeTokens) -> str:
    """Return the focus-ring rules for the results area in a theme (AX-03)."""
    return FOCUS_QSS.format(width=tokens.focus_ring_px, ring=tokens.colours["focus-ring"])


def animations_enabled() -> bool:
    """Return whether the OS allows UI animations (Qt reads the platform's effect setting into UI_General)."""
    return QApplication.isEffectEnabled(Qt.UIEffect.UI_General)


def set_revealed(widget: QWidget, shown: bool) -> QPropertyAnimation | None:
    """Show or hide a collapsible part; it slides open only when the OS allows animations (UI-31)."""
    if not shown or not animations_enabled():
        widget.setMaximumHeight(16_777_215)
        widget.setVisible(shown)
        return None
    widget.setMaximumHeight(0)
    widget.setVisible(True)
    animation = QPropertyAnimation(widget, b"maximumHeight", widget)
    animation.setDuration(REVEAL_MS)
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    animation.setStartValue(0)
    animation.setEndValue(max(widget.sizeHint().height(), 1))
    animation.finished.connect(lambda: widget.setMaximumHeight(16_777_215))
    animation.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    return animation


class ResultCard(QFrame):
    """One result card. ``prefix`` names its parts: ``res-<key>`` in the Results tab, ``sum-ke`` in the rail."""

    open_equation = Signal(str)

    def __init__(self, frame_name: str, prefix: str, registry: Registry, copy_trace: Callable[[str], str]) -> None:
        super().__init__()
        self.setObjectName(frame_name)
        self.setProperty("class", "result-card")
        self.prefix, self._registry, self._copy_trace = prefix, registry, copy_trace
        self.row: ResultRow | None = None
        self.title = self._label("title")
        self.title.setWordWrap(True)
        self.value = self._label("value", "result-value")
        self.unit = self._label("unit", "result-unit")
        self.badge = StatusBadge(f"{prefix}-badge")
        self.estimate = self._label("label", "hint")
        self.eq = EqChip(f"{prefix}-eq")
        self.eq.activated.connect(self.open_equation)
        self.asm = AssumptionTag(f"{prefix}-asm")
        self.asm_list = self._label("asm-list", "hint")
        self.asm_list.setWordWrap(True)
        self.asm_list.setVisible(False)
        self.asm.toggled.connect(lambda on: set_revealed(self.asm_list, on))
        self.how_toggle = QToolButton()
        self.how_toggle.setObjectName(f"{prefix}-how-toggle")
        self.how_toggle.setText(text("results.how.toggle"))
        self.how_toggle.setCheckable(True)
        self.how_toggle.setArrowType(Qt.ArrowType.RightArrow)
        self.how_toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.how_toggle.toggled.connect(self._toggle_how)
        self.how = QFrame()
        self.how.setObjectName(f"{prefix}-how")
        self.how_layout = QVBoxLayout(self.how)
        self.how_layout.setContentsMargins(0, 4, 0, 0)
        self.how.setVisible(False)

        value_line = QHBoxLayout()
        value_line.addWidget(self.value)
        value_line.addWidget(self.unit, 0, Qt.AlignmentFlag.AlignBaseline)
        value_line.addStretch(1)
        value_line.addWidget(self.badge)
        meta = QHBoxLayout()
        meta.addWidget(self.eq)
        meta.addWidget(self.asm)
        meta.addWidget(self.estimate)
        meta.addStretch(1)
        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addLayout(value_line)
        layout.addLayout(meta)
        layout.addWidget(self.asm_list)
        layout.addWidget(self.how_toggle)
        layout.addWidget(self.how)

    def _label(self, part: str, css: str | None = None) -> QLabel:
        label = QLabel()
        label.setObjectName(f"{self.prefix}-{part}")
        label.setTextFormat(Qt.TextFormat.PlainText)
        if css:
            label.setProperty("class", css)
        return label

    def show_row(self, row: ResultRow, tokens: ThemeTokens, *, stale: bool) -> None:
        """Show a row; an open disclosure is rebuilt from the new row."""
        self.row = row
        t = row.traceable
        self.title.setText(row.label)
        self.value.setText(row.value_text)
        self.unit.setText(row.unit_text)
        self.unit.setAccessibleName(row.unit_text)
        self.badge.show_status(row.status, t.status_reasons, tokens)
        self.estimate.setVisible(row.estimate_label is not None)
        self.estimate.setText(row.estimate_label or "")
        self.eq.show_eq(row.eq_ids, t.kind_tag)
        self.asm.show_count(row.assumed_count)
        self.asm_list.setText(
            "\n".join(f"{a.item} {a.value_text}".rstrip() + f" ({a.label})" for a in t.assumed_inputs)
        )
        self.setWhatsThis(row.eq_ids[0] if row.eq_ids else "")
        self.setProperty("stale", "true" if stale else "false")
        repolish(self)
        if self.how_toggle.isChecked():
            self._fill_how()

    def _toggle_how(self, shown: bool) -> None:
        self.how_toggle.setArrowType(Qt.ArrowType.DownArrow if shown else Qt.ArrowType.RightArrow)
        if shown:
            self._fill_how()
        set_revealed(self.how, shown)

    def _fill_how(self) -> None:
        while self.how_layout.count():
            item = self.how_layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        if self.row is None:
            return
        for section in disclosure(self.row, self._registry):
            title = QLabel(section.title)
            title.setProperty("class", "section-title")
            body = QLabel("\n".join(section.lines))
            body.setTextFormat(Qt.TextFormat.PlainText)
            body.setWordWrap(True)
            body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.how_layout.addWidget(title)
            self.how_layout.addWidget(body)
        copy = QPushButton(text("results.how.copy"))
        copy.setObjectName(f"{self.prefix}-copy")
        copy.clicked.connect(self._copy)
        self.how_layout.addWidget(copy, 0, Qt.AlignmentFlag.AlignLeft)

    def disclosure_text(self) -> str:
        """Return the text of the open disclosure, section by section (for tests and screen readers)."""
        return "\n".join(label.text() for label in self.how.findChildren(QLabel))

    def _copy(self) -> None:
        if self.row is not None:
            QGuiApplication.clipboard().setText(self._copy_trace(self.row.quantity))


class ResultsTab(QWidget):
    """``tab-results``: status filter, stale stamp and the card grid; the empty state before a valid design."""

    open_equation = Signal(str)

    def __init__(self, vm: ResultsViewModel, first_missing: Callable[[], None]) -> None:
        super().__init__()
        self.setObjectName("tab-results")
        self.vm = vm
        self.tokens: ThemeTokens | None = None
        self.cards: dict[str, ResultCard] = {}
        self._columns = 0
        self.pages = QStackedWidget()
        empty = QWidget()
        empty_layout = QVBoxLayout(empty)
        message = QLabel(text("results.empty.text"))
        message.setObjectName("results-empty")
        message.setProperty("class", "hint")
        self.first_missing = QPushButton(text("results.empty.first-missing"))
        self.first_missing.setObjectName("btn-results-first-missing")
        self.first_missing.clicked.connect(first_missing)
        empty_layout.addStretch(1)
        empty_layout.addWidget(message, 0, Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(self.first_missing, 0, Qt.AlignmentFlag.AlignCenter)
        empty_layout.addStretch(1)

        content = QWidget()
        filters = QHBoxLayout()
        filters.addWidget(QLabel(text("results.filter.label")))
        self.filter_boxes: dict[Status, QCheckBox] = {}
        for status in Status:
            box = QCheckBox(text(f"shell.badge.{badge_property(status)}"))
            box.setObjectName(f"results-filter-{badge_property(status)}")
            box.setAccessibleName(f"Show {status.value} results")
            box.setChecked(True)
            box.toggled.connect(self._filter_changed)
            self.filter_boxes[status] = box
            filters.addWidget(box)
        filters.addStretch(1)
        self.stale_stamp = QLabel(text("results.stale.stamp"))
        self.stale_stamp.setObjectName("results-stale")
        self.stale_stamp.setProperty("class", "notice")
        self.stale_stamp.setVisible(False)
        self.grid_host = QWidget()
        self.grid = QGridLayout(self.grid_host)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll = QScrollArea()
        scroll.setObjectName("results-scroll")
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.grid_host)
        content_layout = QVBoxLayout(content)
        content_layout.addLayout(filters)
        content_layout.addWidget(self.stale_stamp)
        content_layout.addWidget(scroll, 1)
        self.pages.addWidget(empty)
        self.pages.addWidget(content)
        QVBoxLayout(self).addWidget(self.pages)

        self._dim = QTimer(self)
        self._dim.setSingleShot(True)
        self._dim.setInterval(COMPUTING_DIM_AFTER_MS)
        self._dim.timeout.connect(self._apply_dim)
        vm.rows.subscribe(lambda _: self.refresh())
        vm.stale.subscribe(lambda _: self.refresh())

    def set_tokens(self, tokens: ThemeTokens) -> None:
        """Take a theme and redraw the cards."""
        self.tokens = tokens
        self.refresh()

    def set_computing(self, computing: bool) -> None:
        """Dim the shown values to 60 % once a compute has run for 300 ms; restore them when it ends."""
        if computing:
            if not self._dim.isActive() and self.grid_host.graphicsEffect() is None:
                self._dim.start()
            return
        self._dim.stop()
        self.grid_host.setGraphicsEffect(None)

    def _apply_dim(self) -> None:
        effect = QGraphicsOpacityEffect(self.grid_host)
        effect.setOpacity(COMPUTING_OPACITY)
        self.grid_host.setGraphicsEffect(effect)

    def _filter_changed(self) -> None:
        self.vm.set_status_filter(frozenset(s for s, box in self.filter_boxes.items() if box.isChecked()))

    def refresh(self) -> None:
        """Show the view-model's rows, one card per quantity."""
        if self.tokens is None:
            return
        rows = self.vm.rows.value
        has_rows = bool(rows) or any(not b.isChecked() for b in self.filter_boxes.values())
        self.pages.setCurrentIndex(1 if has_rows else 0)
        self.stale_stamp.setVisible(self.vm.stale.value)
        keys = [result_key(r.quantity) for r in rows]
        for key in set(self.cards) - set(keys):
            self.cards.pop(key).deleteLater()
        for row, key in zip(rows, keys, strict=True):
            card = self.cards.get(key)
            if card is None:
                card = ResultCard(f"res-card-{key}", f"res-{key}", self.vm.registry, self.vm.copy_trace)
                card.open_equation.connect(self.open_equation)
                self.cards[key] = card
            card.show_row(row, self.tokens, stale=self.vm.stale.value)
        self._layout_cards(keys, force=True)

    def _layout_cards(self, keys: list[str], *, force: bool = False) -> None:
        columns = max(1, self.width() // CARD_MIN_WIDTH_PX)
        if columns == self._columns and not force:
            return
        self._columns = columns
        for key in keys:
            self.grid.removeWidget(self.cards[key])
        for index, key in enumerate(keys):
            self.grid.addWidget(self.cards[key], index // columns, index % columns, Qt.AlignmentFlag.AlignTop)

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802 (Qt override)
        """Fit as many card columns as the width allows."""
        super().resizeEvent(event)
        self._layout_cards([result_key(r.quantity) for r in self.vm.rows.value])


class CompareTab(QWidget):
    """``tab-compare``: the stored reference against the current design; deltas carry sign and glyph."""

    COLUMNS = ("compare.column.quantity", "compare.column.reference", "compare.column.current")
    COLUMNS += ("compare.column.delta", "compare.column.unit")

    def __init__(self, vm: CompareViewModel) -> None:
        super().__init__()
        self.setObjectName("tab-compare")
        self.vm = vm
        self.current: ComputeOutcome | None = None
        self.tokens: ThemeTokens | None = None
        self.set_reference = QPushButton(text("compare.set-reference"))
        self.set_reference.setObjectName("btn-set-reference")
        self.set_reference.clicked.connect(self._set_reference_clicked)
        self.caption = QLabel()
        self.caption.setObjectName("compare-caption")
        self.caption.setProperty("class", "hint")
        self.empty = QLabel(text("compare.empty"))
        self.empty.setObjectName("compare-empty")
        self.empty.setWordWrap(True)
        self.empty.setProperty("class", "hint")
        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setObjectName("compare-table")
        self.table.setHorizontalHeaderLabels([text(c) for c in self.COLUMNS])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.chart = ChartPanel("compare-chart")
        top = QHBoxLayout()
        top.addWidget(self.set_reference)
        top.addWidget(self.caption, 1)
        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self.empty)
        layout.addWidget(self.table, 3)
        layout.addWidget(self.chart, 2)
        vm.reference.subscribe(lambda _: self.refresh())
        self.confirm: QWidget | None = None

    def show_outcome(self, outcome: ComputeOutcome | None, tokens: ThemeTokens) -> None:
        """Take the current outcome and theme."""
        self.current, self.tokens = outcome, tokens
        self.refresh()

    def _set_reference_clicked(self) -> None:
        if self.current is None:
            return
        if not self.vm.needs_confirmation():
            self.vm.set_reference(self.current)
            return
        current = self.current
        dialog = confirm_replace_reference(self)
        dialog.accepted.connect(lambda: self.vm.set_reference(current))
        self.confirm = dialog
        dialog.open()

    def refresh(self) -> None:
        """Rebuild the table and the chart from the reference and the current outcome."""
        reference, current = self.vm.reference.value, self.current
        self.set_reference.setEnabled(current is not None)
        ready = reference is not None and current is not None
        self.empty.setVisible(not ready)
        self.empty.setText(text("compare.empty") if reference is None else text("compare.no-current"))
        self.table.setVisible(ready)
        self.chart.setVisible(ready)
        self.caption.setText("" if reference is None else text("compare.reference.caption", name=reference.design.name))
        if not ready or self.tokens is None:
            return
        assert reference is not None and current is not None
        rows = compare_rows(reference, current)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self._fill(r, row)
        self.chart.show_chart(compare_chart(reference, current), self.tokens)

    def _fill(self, r: int, row: CompareRow) -> None:
        assert self.tokens is not None
        cells = (row.label, row.reference_text, row.current_text, row.delta_text, row.unit_text)
        for c, value in enumerate(cells):
            item = QTableWidgetItem(value)
            if c == 3:
                item.setIcon(delta_icon(row.direction, self.tokens))
                item.setData(Qt.ItemDataRole.AccessibleTextRole, f"{value}, {text(f'compare.delta.{row.direction}')}")
                item.setData(Qt.ItemDataRole.UserRole, row.direction)
            if c in (1, 2, 3):
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(r, c, item)
