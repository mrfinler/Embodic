"""Charts drawn with QPainter (PySide6-Essentials only, no QtCharts; package_layout.md section 5).

One y axis with one unit per chart. Phases differ by colour, line style (solid, dashed, dotted) and a direct end
label, and a legend is present for two or more series (design_spec.md section 3.3). A crosshair follows the mouse and
the Left and Right keys. Every chart has a data table and the badge, EQ chip and assumptions tag of its data.
"""

import itertools
import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFocusEvent,
    QFont,
    QFontMetricsF,
    QIcon,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPen,
    QPixmap,
    QPolygonF,
)
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from embodic.io.exporters import PhaseRenderMode
from embodic.outcome import ComputeOutcome
from embodic.ui.strings import text
from embodic.ui.theme import ThemeTokens
from embodic.ui.viewmodels.results import (
    ChartModel,
    ChartSeries,
    Direction,
    back_emf_chart,
    nice_ticks,
    tick_text,
    torque_speed_charts,
)
from embodic.ui.views.status_badge import AssumptionTag, EqChip, StatusBadge
from embodic.ui.views.widgets import table_widget

MARGIN_LEFT, MARGIN_RIGHT, MARGIN_TOP, MARGIN_BOTTOM = 64.0, 84.0, 34.0, 44.0
LINE_PX = 2.0
DASH_PATTERNS = {"solid": None, "dash": (3.0, 1.5), "dot": (0.75, 1.5)}  # in pen widths: 6/3 px and 1.5/3 px
MARKER_PX = 8.0
LABEL_GAP_PX = 14.0
FONT_PX = 12


def series_pen(series: ChartSeries, tokens: ThemeTokens, mode: PhaseRenderMode) -> QPen:
    """Return the pen of a series: phase colour or grey step with the phase's dash, ink, or dashed grey reference."""
    if series.reference:
        pen = QPen(QColor(tokens.colours["text-3"]), LINE_PX)
        pen.setDashPattern([3.0, 1.5])
    elif series.phase is None:
        pen = QPen(QColor(tokens.colours["text-1"]), LINE_PX)
    else:
        style = tokens.phase_style(series.phase)
        colour = style.colour_hex if mode is PhaseRenderMode.COLOUR else style.grey_hex
        pen = QPen(QColor(colour), LINE_PX)
        pattern = DASH_PATTERNS[style.dash]
        if pattern is not None:
            pen.setDashPattern(list(pattern))
    pen.setCapStyle(Qt.PenCapStyle.FlatCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return pen


def end_label(series: ChartSeries) -> str:
    """Return the direct label at a line's end: the phase letter, or the series name."""
    return series.phase.value if series.phase is not None else series.label


def spread_labels(ys: list[float], gap: float) -> list[float]:
    """Return label positions in the same order, pushed apart so that no two are closer than ``gap``."""
    order = sorted(range(len(ys)), key=lambda i: ys[i])
    placed = list(ys)
    for before, after in itertools.pairwise(order):
        placed[after] = max(placed[after], placed[before] + gap)
    return placed


def delta_icon(direction: Direction, tokens: ThemeTokens) -> QIcon:
    """Return the up or down triangle of a delta in ink; no change has no glyph (colour is never the cue)."""
    pixmap = QPixmap(12, 12)
    pixmap.fill(Qt.GlobalColor.transparent)
    if direction != "same":
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(tokens.colours["text-1"]))
        points = [(6, 1), (11, 10), (1, 10)] if direction == "up" else [(1, 2), (11, 2), (6, 11)]
        painter.drawPolygon(QPolygonF([QPointF(x, y) for x, y in points]))
        painter.end()
    return QIcon(pixmap)


class ChartWidget(QWidget):
    """Plot area of one ChartModel."""

    def __init__(self, chart_id: str) -> None:
        super().__init__()
        self.setObjectName(chart_id)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.setMinimumHeight(170)
        self.model: ChartModel | None = None
        self.tokens: ThemeTokens | None = None
        self.mode = PhaseRenderMode.COLOUR
        self.cursor_index: int | None = None
        self.legend_labels: tuple[str, ...] = ()
        self.end_labels: tuple[str, ...] = ()

    def show_chart(self, model: ChartModel | None, tokens: ThemeTokens, mode: PhaseRenderMode) -> None:
        """Draw a model in a theme and render mode."""
        self.model, self.tokens, self.mode = model, tokens, mode
        if model is not None:
            self.setAccessibleName(model.title)
            self.legend_labels = tuple(s.label for s in model.series) if len(model.series) >= 2 else ()
            self.end_labels = tuple(end_label(s) for s in model.series)
            if self.cursor_index is not None and self.cursor_index >= len(model.xs):
                self.cursor_index = None
        self.update()

    def y_title(self) -> str:
        """Return the y axis title with its one unit, drawn level above the axis so it is never clipped."""
        return "" if self.model is None else f"{self.model.y_label} ({self.model.y_unit})"

    def stamp(self) -> str | None:
        """Return the stamp a drawing not produced by the engine carries (UI-32), or None for engine data."""
        return None if self.model is None or self.model.computed else text("chart.illustrative")

    def ranges(self) -> tuple[tuple[float, ...], tuple[float, ...]]:
        """Return the x ticks and the y ticks; the y axis covers every series."""
        assert self.model is not None
        model = self.model
        values = [y for s in model.series for y in s.ys if math.isfinite(y)]
        y_ticks = nice_ticks(min(values, default=0.0), max(values, default=1.0))
        x_ticks = model.x_ticks or nice_ticks(min(model.xs), max(model.xs))
        return x_ticks, y_ticks

    def plot_rect(self) -> QRectF:
        """Return the plot area inside the axis margins."""
        return QRectF(
            MARGIN_LEFT,
            MARGIN_TOP,
            self.width() - MARGIN_LEFT - MARGIN_RIGHT,
            self.height() - MARGIN_TOP - MARGIN_BOTTOM,
        )

    def _mapper(self):
        x_ticks, y_ticks = self.ranges()
        rect = self.plot_rect()
        x0, x1, y0, y1 = x_ticks[0], x_ticks[-1], y_ticks[0], y_ticks[-1]

        def to_px(x: float, y: float) -> QPointF:
            return QPointF(
                rect.left() + (x - x0) / (x1 - x0 or 1.0) * rect.width(),
                rect.bottom() - (y - y0) / (y1 - y0 or 1.0) * rect.height(),
            )

        return to_px, x_ticks, y_ticks, rect

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 (Qt override)
        """Draw grid, axes, series, legend, end labels, crosshair, stamp and focus ring."""
        if self.tokens is None:
            return
        c = self.tokens.colours
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(c["canvas"]))
        font = QFont(painter.font())
        font.setPixelSize(FONT_PX)
        painter.setFont(font)
        metrics = QFontMetricsF(font)
        if self.model is not None and self.model.xs:
            self._draw_plot(painter, metrics)
        if self.hasFocus():
            painter.setPen(QPen(QColor(c["focus-ring"]), self.tokens.focus_ring_px))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            inset = self.tokens.focus_ring_px / 2
            painter.drawRect(QRectF(self.rect()).adjusted(inset, inset, -inset, -inset))
        painter.end()

    def _draw_plot(self, painter: QPainter, metrics: QFontMetricsF) -> None:
        assert self.model is not None and self.tokens is not None
        to_px, x_ticks, y_ticks, rect = self._mapper()
        self._draw_axes(painter, metrics, to_px, x_ticks, y_ticks, rect)
        self._draw_series(painter, metrics, to_px, rect)

    def _draw_axes(self, painter: QPainter, metrics: QFontMetricsF, to_px, x_ticks, y_ticks, rect: QRectF) -> None:
        assert self.model is not None and self.tokens is not None
        model, c = self.model, self.tokens.colours
        painter.setPen(QPen(QColor(c["grid-line"]), 1))
        for y in y_ticks:
            p = to_px(x_ticks[0], y)
            painter.drawLine(QPointF(rect.left(), p.y()), QPointF(rect.right(), p.y()))
        painter.setPen(QPen(QColor(c["border-control"]), 1))
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())
        painter.drawLine(rect.bottomLeft(), rect.topLeft())
        painter.setPen(QPen(QColor(c["text-2"])))
        for y in y_ticks:
            p = to_px(x_ticks[0], y)
            label = tick_text(y)
            painter.drawText(QPointF(rect.left() - 6 - metrics.horizontalAdvance(label), p.y() + 4), label)
        for x in x_ticks:
            p = to_px(x, y_ticks[0])
            label = tick_text(x)
            painter.drawText(QPointF(p.x() - metrics.horizontalAdvance(label) / 2, rect.bottom() + 16), label)
        x_title = f"{model.x_label} ({model.x_unit})"
        painter.drawText(
            QPointF(rect.center().x() - metrics.horizontalAdvance(x_title) / 2, rect.bottom() + 34), x_title
        )
        painter.drawText(QPointF(8, 18), self.y_title())

    def _draw_series(self, painter: QPainter, metrics: QFontMetricsF, to_px, rect: QRectF) -> None:
        assert self.model is not None and self.tokens is not None
        model, c = self.model, self.tokens.colours
        ink, muted = QColor(c["text-1"]), QColor(c["text-3"])
        painter.setClipRect(rect.adjusted(-LINE_PX, -LINE_PX, LINE_PX, LINE_PX))
        ends: list[float] = []
        for series in model.series:
            path = QPainterPath()
            for i, (x, y) in enumerate(zip(model.xs, series.ys, strict=True)):
                if i == 0:
                    path.moveTo(to_px(x, y))
                else:
                    path.lineTo(to_px(x, y))
            painter.setPen(series_pen(series, self.tokens, self.mode))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)
            ends.append(to_px(model.xs[-1], series.ys[-1]).y())
        painter.setClipping(False)

        painter.setPen(QPen(ink))
        for label, y in zip(self.end_labels, spread_labels(ends, LABEL_GAP_PX), strict=True):
            painter.drawText(QPointF(rect.right() + 8, y + 4), label)
        if self.legend_labels:
            x = 8 + metrics.horizontalAdvance(self.y_title()) + 24
            for series in model.series:
                pen = series_pen(series, self.tokens, self.mode)
                painter.setPen(pen)
                painter.drawLine(QPointF(x, 14), QPointF(x + 24, 14))
                painter.setPen(QPen(ink))
                painter.drawText(QPointF(x + 30, 18), series.label)
                x += 30 + metrics.horizontalAdvance(series.label) + 18
        stamp = self.stamp()
        if stamp is not None:
            box = QRectF(
                rect.right() - metrics.horizontalAdvance(stamp) - 16,
                rect.top() + 6,
                metrics.horizontalAdvance(stamp) + 12,
                20,
            )
            painter.setPen(QPen(ink, 1))
            painter.setBrush(QColor(c["surface"]))
            painter.drawRect(box)
            painter.drawText(box, Qt.AlignmentFlag.AlignCenter, stamp)
        if self.cursor_index is not None:
            self._draw_crosshair(painter, metrics, to_px, rect, muted)

    def _draw_crosshair(self, painter: QPainter, metrics: QFontMetricsF, to_px, rect: QRectF, muted: QColor) -> None:
        assert self.model is not None and self.tokens is not None
        c = self.tokens.colours
        i = self.cursor_index
        assert i is not None
        x = self.model.xs[i]
        top = to_px(x, 0.0)
        painter.setPen(QPen(muted, 1))
        painter.drawLine(QPointF(top.x(), rect.top()), QPointF(top.x(), rect.bottom()))
        for series in self.model.series:
            point = to_px(x, series.ys[i])
            painter.setPen(QPen(QColor(c["canvas"]), 2))
            painter.setBrush(series_pen(series, self.tokens, self.mode).color())
            painter.drawEllipse(point, MARKER_PX / 2, MARKER_PX / 2)
        lines = self.crosshair_lines()
        width = max(metrics.horizontalAdvance(line) for line in lines) + 16
        box = QRectF(min(top.x() + 10, rect.right() - width), rect.top() + 8, width, 18 * len(lines) + 8)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(c["surface-inverse"]))
        painter.drawRoundedRect(box, 4, 4)
        painter.setPen(QPen(QColor(c["text-inverse"])))
        for k, line in enumerate(lines):
            painter.drawText(QPointF(box.left() + 8, box.top() + 18 + 18 * k), line)

    def crosshair_lines(self) -> list[str]:
        """Return the tooltip text at the crosshair: the x value, then each series' value with its unit."""
        assert self.model is not None and self.cursor_index is not None
        model, i = self.model, self.cursor_index
        head = f"{model.x_label} {tick_text(round(model.xs[i], 3))} {model.x_unit}"
        return [head, *(f"{s.label}: {tick_text(round(s.ys[i], 4))} {model.y_unit}" for s in model.series)]

    def move_cursor(self, step: int) -> None:
        """Move the crosshair by samples (Left and Right keys)."""
        if self.model is None or not self.model.xs:
            return
        start = self.cursor_index if self.cursor_index is not None else (0 if step > 0 else len(self.model.xs) - 1)
        self.cursor_index = min(max(start + (step if self.cursor_index is not None else 0), 0), len(self.model.xs) - 1)
        self.setToolTip("\n".join(self.crosshair_lines()))
        self.update()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802 (Qt override)
        """Left and Right move the crosshair; Shift moves ten samples."""
        steps = {Qt.Key.Key_Left: -1, Qt.Key.Key_Right: 1}
        if event.key() in steps:
            factor = 10 if event.modifiers() & Qt.KeyboardModifier.ShiftModifier else 1
            self.move_cursor(steps[Qt.Key(event.key())] * factor)
            return
        super().keyPressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802 (Qt override)
        """Follow the mouse with the crosshair, snapped to the nearest sample."""
        model = self.model
        if model is None or not model.xs:
            return
        to_px, *_ = self._mapper()
        px = event.position().x()
        self.cursor_index = min(range(len(model.xs)), key=lambda k: abs(to_px(model.xs[k], 0.0).x() - px))
        self.setToolTip("\n".join(self.crosshair_lines()))
        self.update()

    def leaveEvent(self, event) -> None:  # noqa: N802 (Qt override)
        """Hide the crosshair when the mouse leaves, unless the keyboard holds it."""
        if not self.hasFocus():
            self.cursor_index = None
            self.update()
        super().leaveEvent(event)

    def focusInEvent(self, event: QFocusEvent) -> None:  # noqa: N802 (Qt override)
        """Repaint for the focus ring."""
        super().focusInEvent(event)
        self.update()

    def focusOutEvent(self, event: QFocusEvent) -> None:  # noqa: N802 (Qt override)
        """Repaint without the focus ring."""
        super().focusOutEvent(event)
        self.update()


class ChartPanel(QWidget):
    """Title, chart, trust metadata (``<id>-meta``), note and the collapsible data table (``<id>-table``)."""

    def __init__(self, chart_id: str) -> None:
        super().__init__()
        self.chart_id = chart_id
        self.title = QLabel()
        self.title.setObjectName(f"{chart_id}-title")
        self.title.setProperty("class", "section-title")
        self.chart = ChartWidget(chart_id)
        meta = QWidget()
        meta.setObjectName(f"{chart_id}-meta")
        meta_layout = QHBoxLayout(meta)
        meta_layout.setContentsMargins(0, 0, 0, 0)
        self.badge = StatusBadge(f"{chart_id}-badge")
        self.eq = EqChip(f"{chart_id}-eq")
        self.asm = AssumptionTag(f"{chart_id}-asm")
        self.estimate = QLabel()
        self.estimate.setObjectName(f"{chart_id}-label")
        self.estimate.setProperty("class", "hint")
        for widget in (self.badge, self.eq, self.asm, self.estimate):
            meta_layout.addWidget(widget)
        meta_layout.addStretch(1)
        self.note = QLabel()
        self.note.setObjectName(f"{chart_id}-note")
        self.note.setProperty("class", "hint")
        self.note.setWordWrap(True)
        self.table_toggle = QToolButton()
        self.table_toggle.setObjectName(f"{chart_id}-table-toggle")
        self.table_toggle.setText(text("chart.data-table"))
        self.table_toggle.setCheckable(True)
        self.table = table_widget()
        self.table.setObjectName(f"{chart_id}-table")
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setVisible(False)
        self.table.setMaximumHeight(220)
        self.table_toggle.toggled.connect(self.table.setVisible)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.title)
        layout.addWidget(meta)
        layout.addWidget(self.chart, 1)
        layout.addWidget(self.note)
        layout.addWidget(self.table_toggle, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.table)

    def show_chart(
        self, model: ChartModel | None, tokens: ThemeTokens, mode: PhaseRenderMode = PhaseRenderMode.COLOUR
    ) -> None:
        """Show a chart model, its metadata and the same samples in the table."""
        shown = self.chart
        if model == shown.model and tokens is shown.tokens and mode is shown.mode:
            return
        self.chart.show_chart(model, tokens, mode)
        if model is None:
            return
        self.title.setText(model.title)
        self.badge.show_status(model.status, (), tokens)
        self.eq.show_eq(model.eq_ids, "computed")
        self.asm.show_count(model.assumed_count)
        self.estimate.setText(model.estimate_label or "")
        self.estimate.setVisible(model.estimate_label is not None)
        self.note.setText(model.note or "")
        self.note.setVisible(model.note is not None)
        headers = [f"{model.x_label} ({model.x_unit})", *(f"{s.label} ({model.y_unit})" for s in model.series)]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(model.xs))
        for r, x in enumerate(model.xs):
            for c, value in enumerate((x, *(s.ys[r] for s in model.series))):
                item = QTableWidgetItem(tick_text(round(value, 6)))
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(r, c, item)


class _ChartTab(QWidget):
    """A results tab of charts with its empty state."""

    def __init__(self, tab_id: str, panels: tuple[ChartPanel, ...]) -> None:
        super().__init__()
        self.setObjectName(tab_id)
        self.panels = panels
        self.pages = QStackedWidget()
        self.empty = QLabel(text("chart.empty"))
        self.empty.setObjectName(f"{tab_id}-empty")
        self.empty.setProperty("class", "hint")
        self.empty.setWordWrap(True)
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        charts = QWidget()
        charts_layout = QVBoxLayout(charts)
        for panel in panels:
            charts_layout.addWidget(panel, 1)
        scroll = QScrollArea()
        scroll.setObjectName(f"{tab_id}-scroll")
        scroll.setWidgetResizable(True)
        scroll.setWidget(charts)
        self.pages.addWidget(self.empty)
        self.pages.addWidget(scroll)
        QVBoxLayout(self).addWidget(self.pages)

    def show_models(
        self, models: tuple[ChartModel, ...] | None, empty_key: str, tokens: ThemeTokens, mode: PhaseRenderMode
    ) -> None:
        self.empty.setText(text(empty_key))
        self.pages.setCurrentIndex(0 if models is None else 1)
        for panel, model in zip(self.panels, models or (None,) * len(self.panels), strict=True):
            panel.show_chart(model, tokens, mode)


class BackEmfTab(_ChartTab):
    """``tab-back-emf``: the three phases' back-EMF over one electrical period."""

    def __init__(self) -> None:
        super().__init__("tab-back-emf", (ChartPanel("chart-backemf"),))

    def show_outcome(self, outcome: ComputeOutcome | None, tokens: ThemeTokens, mode: PhaseRenderMode) -> None:
        """Show the chart of an outcome or the empty state."""
        model = back_emf_chart(outcome)
        self.show_models(None if model is None else (model,), "chart.empty", tokens, mode)


class TorqueSpeedTab(_ChartTab):
    """``tab-torque-speed``: torque and power against speed as two charts sharing the rpm axis."""

    def __init__(self) -> None:
        super().__init__("tab-torque-speed", (ChartPanel("chart-torque-speed"), ChartPanel("chart-power-speed")))

    def show_outcome(self, outcome: ComputeOutcome | None, tokens: ThemeTokens, mode: PhaseRenderMode) -> None:
        """Show both charts, the empty state, or the note that a DC-link voltage is needed."""
        models = torque_speed_charts(outcome)
        no_dc_link = outcome is not None and outcome.analysis is not None and models is None
        self.show_models(models, "chart.no-dc-link" if no_dc_link else "chart.empty", tokens, mode)
