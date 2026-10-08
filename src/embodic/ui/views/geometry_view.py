"""The zoomable, pannable drawing of the boards: copper in model millimetres, coil-eye fills, phase labels, legend.

Scene units are millimetres with y negated (Qt's y points down). Copper pens are as wide as the trace in
millimetres, so stroke widths follow the zoom (UI-03). Copper is never dashed (design_spec.md section 3.3). Labels
and eyes come from `embodic.geometry.labels` and `embodic.geometry.marks`, the modules the exports draw from; the
labels are placed again after every zoom, pan or resize step, so they never overlap at any zoom (ruling b).
"""

import math

from PySide6.QtCore import QPointF, QRect, QRectF, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontMetricsF,
    QImage,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
    QResizeEvent,
    QTransform,
    QWheelEvent,
)
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsPathItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QStyleOptionGraphicsItem,
    QWidget,
)

from embodic.geometry.labels import Box, PlacedLabel, Viewport
from embodic.geometry.layout import Layout
from embodic.geometry.primitives import Line, Primitive
from embodic.model.vocabulary import Phase
from embodic.ui.strings import text
from embodic.ui.theme import PhaseStyle, ThemeTokens
from embodic.ui.viewmodels.appearance import PhaseRenderMode
from embodic.ui.viewmodels.outcome import (
    BoardMarks,
    CoilMark,
    GeometryScene,
    eyes_shown,
    phases_drawn,
    place_in_view,
)

ZOOM_MIN, ZOOM_MAX = 0.1, 200.0  # relative to the fitted view (UI-03)
ZOOM_STEP = 1.25
EYE_TINT_ALPHA = 26  # 10 % of 255: the solid eye tint of phase A
HATCH_TILE_PX = 6  # one diagonal per 6 px tile: 4.2 px between hatch lines on screen (design_spec 3.3, "about 4 px")
LABEL_PX = 12
LABEL_HALO_PX = 3  # board-coloured outline that keeps a letter readable over hatch and copper
LEGEND_MARGIN_PX = 8
LEGEND_PAD_PX = 6
LEGEND_ROW_PX = 20
LEGEND_BAR_PX = (20, 3)  # solid copper bar: length, thickness
LEGEND_SWATCH_PX = 12  # eye swatch diameter
LEGEND_GAP_PX = 6
DATA_LAYER = 0  # QGraphicsItem.data key: copper layer name ("" for board items)
DATA_PHASE = 1  # QGraphicsItem.data key: phase letter or ""
DATA_KIND = 2  # QGraphicsItem.data key: "copper", "eye", "hatch", "label", "label-halo", "leader", "via", "pad",
# "outline", "hole"
LABEL_KINDS = frozenset({"label", "label-halo", "leader"})


def primitive_path(p: Primitive) -> QPainterPath:
    """Return the centre line of one primitive in scene coordinates."""
    path = QPainterPath()
    if isinstance(p, Line):
        path.moveTo(p.x1_mm, -p.y1_mm)
        path.lineTo(p.x2_mm, -p.y2_mm)
        return path
    sx, sy = p.start_point()
    path.moveTo(sx, -sy)
    rect = QRectF(p.cx_mm - p.r_mm, -p.cy_mm - p.r_mm, 2 * p.r_mm, 2 * p.r_mm)
    path.arcTo(rect, math.degrees(p.start_rad), math.degrees(p.sweep_rad))
    return path


def _disc(x_mm: float, y_mm: float, r_mm: float) -> QRectF:
    return QRectF(x_mm - r_mm, -y_mm - r_mm, 2 * r_mm, 2 * r_mm)


def hatch_brush(colour: QColor, hatch_deg: int) -> QBrush:
    """Return a screen-space hatch tile: 45 degrees (y up) rises to the right on screen, 135 degrees falls."""
    tile = QImage(HATCH_TILE_PX, HATCH_TILE_PX, QImage.Format.Format_ARGB32_Premultiplied)
    tile.fill(Qt.GlobalColor.transparent)
    last = HATCH_TILE_PX - 1
    for i in range(HATCH_TILE_PX):
        tile.setPixelColor(i, last - i if hatch_deg == 45 else i, colour)
    return QBrush(tile)


def paint_eye(painter: QPainter, device_disc: QRectF, colour: QColor, hatch_deg: int) -> None:
    """Fill a disc given in device pixels with the eye fill of a phase: the 10 % tint, or the hatch tile."""
    painter.save()
    painter.resetTransform()
    painter.setPen(Qt.PenStyle.NoPen)
    if hatch_deg == 0:
        tint = QColor(colour)
        tint.setAlpha(EYE_TINT_ALPHA)
        painter.setBrush(tint)
    else:
        painter.setBrush(hatch_brush(colour, hatch_deg))
        painter.setBrushOrigin(device_disc.topLeft())
    painter.drawEllipse(device_disc)
    painter.restore()


class EyeItem(QGraphicsEllipseItem):
    """A coil eye in model millimetres whose fill is painted in screen pixels, so the hatch shows at fit zoom."""

    def __init__(self, mark: CoilMark, colour: QColor, hatch_deg: int) -> None:
        super().__init__(_disc(mark.cx_mm, mark.cy_mm, mark.eye_radius_mm))
        self.colour, self.hatch_deg = colour, hatch_deg
        self.setPen(QPen(Qt.PenStyle.NoPen))

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None) -> None:
        """Paint the fill with the item's scale undone."""
        paint_eye(painter, painter.worldTransform().mapRect(self.rect()), self.colour, self.hatch_deg)


def label_font() -> QFont:
    """Return the font of the coil labels."""
    font = QFont()
    font.setPixelSize(LABEL_PX)
    return font


class GeometryView(QGraphicsView):
    """Draws a GeometryScene; layers in ``hidden`` are left out of the scene, not merely hidden."""

    cursor_moved = Signal(float, float)
    board_step = Signal(int)  # Page Up -1, Page Down +1: the board picker moves (screens.md 4.1)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("fig-canvas")
        self.setAccessibleName(text("shell.fig-canvas.accessible"))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setMouseTracking(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setScene(QGraphicsScene(self))
        self.viewport().setFocusProxy(self)
        self._fit_scale = 1.0
        self._tokens: ThemeTokens | None = None
        self._geometry: GeometryScene | None = None
        self._mode = PhaseRenderMode.COLOUR
        self._hidden: frozenset[str] = frozenset()
        self._board: int | None = None
        self._extent = QRectF()
        self._label_items: list[QGraphicsItem] = []
        self._font = label_font()
        self._metrics = QFontMetricsF(self._font)
        self.placed: tuple[PlacedLabel, ...] = ()

    def show_geometry(
        self,
        geometry: GeometryScene | None,
        tokens: ThemeTokens,
        mode: PhaseRenderMode,
        hidden: frozenset[str],
        board: int | None = None,
    ) -> None:
        """Redraw with new content, theme, render mode, layer visibility or board; keeps the zoom when it can.

        ``board`` is the index of the one board to draw, or None for every board (screens.md 4.1).
        """
        first = self._geometry is None and geometry is not None
        self._geometry, self._tokens, self._mode, self._hidden = geometry, tokens, mode, hidden
        self._board = board
        self.setBackgroundBrush(QColor(tokens.colours["canvas"]))
        self._rebuild()
        if first:
            self.fit_view()

    def _shown(self) -> list[tuple[Layout, BoardMarks]]:
        if self._geometry is None:
            return []
        pairs = list(zip(self._geometry.boards, self._geometry.marks, strict=True))
        return pairs if self._board is None else [pairs[self._board]]

    def _phase_colour(self, style: PhaseStyle) -> QColor:
        return QColor(style.colour_hex if self._mode is PhaseRenderMode.COLOUR else style.grey_hex)

    def _copper_colour(self, phase: Phase | None) -> QColor:
        assert self._tokens is not None
        if phase is None:
            return QColor(self._tokens.colours["text-2"])
        return self._phase_colour(self._tokens.phase_style(phase))

    def _tag(self, item: QGraphicsItem, kind: str, layer: str = "", phase: Phase | None = None) -> None:
        item.setData(DATA_KIND, kind)
        item.setData(DATA_LAYER, layer)
        item.setData(DATA_PHASE, phase.value if phase else "")

    def _rebuild(self) -> None:
        scene = self.scene()
        scene.clear()
        self._label_items, self.placed = [], ()
        self._extent = QRectF()
        if self._geometry is None or self._tokens is None:
            return
        shown = self._shown()
        for board, _ in shown:
            self._draw_board(board)
        visible = [layer for layer in self._geometry.layers if layer not in self._hidden]
        for layer in reversed(visible):
            for board, marks in shown:
                self._draw_copper(board, marks, layer)
        for board, marks in shown:
            for mark in eyes_shown(board, marks, self._hidden):
                self._draw_eye(mark)
        bounds = self._extent
        scene.setSceneRect(bounds.adjusted(-bounds.width(), -bounds.height(), bounds.width(), bounds.height()))
        self.place_labels()

    def _draw_board(self, board: Layout) -> None:
        assert self._tokens is not None
        colours = self._tokens.colours
        outline = QPainterPath()
        for prim in board.outline.outer:
            outline.addPath(primitive_path(prim))
        for cutout in board.outline.cutouts:
            for prim in cutout:
                outline.addPath(primitive_path(prim))
        outline.setFillRule(Qt.FillRule.OddEvenFill)
        pen = QPen(QColor(colours["border-control"]), 0)
        canvas = QColor(colours["canvas"])
        item = self.scene().addPath(outline, pen, QBrush(QColor(colours["board-fill"])))
        self._tag(item, "outline")
        self._extent = self._extent.united(item.boundingRect())
        for hole in board.outline.holes:
            self._tag(self.scene().addEllipse(_disc(hole.x_mm, hole.y_mm, hole.diameter_mm / 2), pen, canvas), "hole")

    def _draw_copper(self, board: Layout, marks: BoardMarks, layer: str) -> None:
        assert self._tokens is not None
        no_pen = QPen(Qt.PenStyle.NoPen)
        for path in (p for p in board.paths if p.layer == layer):
            colour = self._copper_colour(path.phase)
            tip = marks.label_of_path.get(path.id, "")
            for prim in path.primitives:
                pen = QPen(colour, prim.width_mm, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
                item = self.scene().addPath(primitive_path(prim), pen)
                item.setToolTip(tip)
                self._tag(item, "copper", layer, path.phase)
        via_fill = QColor(self._tokens.colours["text-3"])
        for via in (v for v in board.vias if layer in (v.layer_from, v.layer_to)):
            self._tag(
                self.scene().addEllipse(_disc(via.x_mm, via.y_mm, via.pad_mm / 2), no_pen, via_fill), "via", layer
            )
        pad_fill = QColor(self._tokens.colours["text-2"])
        for pad in (p for p in board.pads if p.layer in (None, layer)):
            rect = QRectF(pad.x_mm - pad.width_mm / 2, -pad.y_mm - pad.height_mm / 2, pad.width_mm, pad.height_mm)
            self._tag(self.scene().addRect(rect, no_pen, pad_fill), "pad", layer)

    def _draw_eye(self, mark: CoilMark) -> None:
        assert self._tokens is not None
        style = self._tokens.phase_style(mark.phase)
        eye = EyeItem(mark, self._phase_colour(style), style.hatch_deg)
        self.scene().addItem(eye)
        self._tag(eye, "eye" if style.hatch_deg == 0 else "hatch", mark.layer, mark.phase)

    def _viewport_mm(self) -> Viewport:
        seen = self.mapToScene(self.viewport().rect()).boundingRect()
        return Viewport(
            x_min_mm=seen.left(),
            y_min_mm=-seen.bottom(),
            x_max_mm=seen.right(),
            y_max_mm=-seen.top(),
            px_per_mm=self.transform().m11(),
        )

    def _text_size(self, label: str) -> tuple[float, float]:
        return self._metrics.horizontalAdvance(label), self._metrics.height()

    def _legend_box_mm(self) -> Box | None:
        legend = self.legend_rect()
        if legend.isEmpty():
            return None
        corners = self.mapToScene(legend.toAlignedRect()).boundingRect()
        return Box(
            x_min_mm=corners.left(), y_min_mm=-corners.bottom(), x_max_mm=corners.right(), y_max_mm=-corners.top()
        )

    def place_labels(self) -> None:
        """Place the labels of the shown boards for the current zoom and viewport (ruling b, UX-AC-27)."""
        scene = self.scene()
        for item in self._label_items:
            scene.removeItem(item)
        self._label_items = []
        shown = self._shown()
        if not shown or self._tokens is None:
            self.placed = ()
            return
        anchors = [a for _, m in shown for a in m.anchors]
        obstacles = [box for _, m in shown for box in m.pads]
        if (legend := self._legend_box_mm()) is not None:
            obstacles.append(legend)
        self.placed = place_in_view(
            [a for a in anchors if a.first_of_phase] + [a for a in anchors if not a.first_of_phase],
            view=self._viewport_mm(),
            text_size=self._text_size,
            obstacles=obstacles,
            ring_outer_mm=max(board.envelope_mm[1] for board, _ in shown),
        )
        for label in self.placed:
            self._draw_label(label)

    def _draw_label(self, label: PlacedLabel) -> None:
        assert self._tokens is not None
        colours = self._tokens.colours
        if label.leader is not None:
            (ax, ay), (bx, by) = label.leader
            leader = QGraphicsLineItem(ax, -ay, bx, -by)
            leader.setPen(QPen(QColor(colours["text-2"]), 0))
            self._add_label_item(leader, "leader", label.phase)
        item = QGraphicsSimpleTextItem(label.text)
        item.setFont(self._font)
        item.setBrush(QColor(colours["text-1"]))
        bounds = item.boundingRect()
        centre = QTransform.fromTranslate(-bounds.width() / 2, -bounds.height() / 2)
        outline = QPainterPath()
        outline.addText(0, self._metrics.ascent(), self._font, label.text)
        halo = QGraphicsPathItem(outline)
        halo.setPen(
            QPen(
                QColor(colours["board-fill"]),
                LABEL_HALO_PX,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )
        for part, kind in ((halo, "label-halo"), (item, "label")):
            part.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
            part.setPos(label.x_mm, -label.y_mm)
            part.setTransform(centre)
            self._add_label_item(part, kind, label.phase)

    def _add_label_item(self, item: QGraphicsItem, kind: str, phase: Phase) -> None:
        item.setZValue(10)
        self.scene().addItem(item)
        self._tag(item, kind, phase=phase)
        self._label_items.append(item)

    def legend_phases(self) -> tuple[Phase, ...]:
        """Return the legend rows: every phase drawn, when two or more are (design_spec.md 3.3)."""
        phases = phases_drawn([board for board, _ in self._shown()])
        return phases if len(phases) >= 2 else ()

    def legend_rect(self) -> QRectF:
        """Return the legend panel in viewport pixels, top left; empty when there is no legend."""
        rows = self.legend_phases()
        if not rows:
            return QRectF()
        widest = max(self._metrics.horizontalAdvance(text("shell.legend.phase", phase=p.value)) for p in rows)
        width = 2 * LEGEND_PAD_PX + LEGEND_BAR_PX[0] + LEGEND_SWATCH_PX + 2 * LEGEND_GAP_PX + widest
        return QRectF(LEGEND_MARGIN_PX, LEGEND_MARGIN_PX, width, 2 * LEGEND_PAD_PX + LEGEND_ROW_PX * len(rows))

    def legend_row_geometry(self, row: int) -> tuple[QRectF, QRectF, QPointF]:
        """Return, for one legend row in viewport pixels, the copper bar, the eye swatch and the text origin."""
        panel = self.legend_rect()
        mid = panel.top() + LEGEND_PAD_PX + (row + 0.5) * LEGEND_ROW_PX
        x = panel.left() + LEGEND_PAD_PX
        length, thickness = LEGEND_BAR_PX
        bar = QRectF(x, mid - thickness / 2, length, thickness)
        x += length + LEGEND_GAP_PX
        swatch = QRectF(x, mid - LEGEND_SWATCH_PX / 2, LEGEND_SWATCH_PX, LEGEND_SWATCH_PX)
        x += LEGEND_SWATCH_PX + LEGEND_GAP_PX
        return bar, swatch, QPointF(x, mid + (self._metrics.ascent() - self._metrics.descent()) / 2)

    def _draw_legend(self, painter: QPainter) -> None:
        assert self._tokens is not None
        rows = self.legend_phases()
        if not rows:
            return
        colours = self._tokens.colours
        painter.setPen(QPen(QColor(colours["border-control"]), 1))
        painter.setBrush(QColor(colours["surface"]))
        painter.drawRoundedRect(self.legend_rect(), 6, 6)
        painter.setFont(self._font)
        for row, phase in enumerate(rows):
            style = self._tokens.phase_style(phase)
            colour = self._phase_colour(style)
            bar, swatch, origin = self.legend_row_geometry(row)
            painter.fillRect(bar, colour)
            paint_eye(painter, swatch, colour, style.hatch_deg)
            painter.setPen(QPen(colour, 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(swatch)
            painter.setPen(QColor(colours["text-1"]))
            painter.drawText(origin, text("shell.legend.phase", phase=phase.value))

    def zoom_factor(self) -> float:
        """Return the current scale relative to the fitted view."""
        return self.transform().m11() / self._fit_scale

    def fit_view(self) -> None:
        """Fit the drawn boards into the view."""
        if self._extent.isEmpty():
            return
        self.resetTransform()
        self.fitInView(self._extent, Qt.AspectRatioMode.KeepAspectRatio)
        self._fit_scale = self.transform().m11()
        self.place_labels()

    def zoom_by(self, factor: float) -> None:
        """Zoom by a factor, kept between 0.1x and 200x the fitted view, then place the labels again."""
        target = min(max(self.zoom_factor() * factor, ZOOM_MIN), ZOOM_MAX)
        step = target / self.zoom_factor()
        self.scale(step, step)
        self.place_labels()

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802 (Qt override)
        """Place the labels again for the new viewport."""
        super().resizeEvent(event)
        self.place_labels()

    def scrollContentsBy(self, dx: int, dy: int) -> None:  # noqa: N802 (Qt override)
        """Place the labels again after a pan step: the view edge decides which labels fit."""
        super().scrollContentsBy(dx, dy)
        self.place_labels()

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802 (Qt override)
        """Zoom around the pointer."""
        self.zoom_by(ZOOM_STEP if event.angleDelta().y() > 0 else 1 / ZOOM_STEP)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802 (Qt override)
        """Arrow keys pan (Shift five times as far); +, - and 0 zoom (design_spec.md section 10)."""
        key = Qt.Key(event.key())
        pan = {Qt.Key.Key_Left: (-1, 0), Qt.Key.Key_Right: (1, 0), Qt.Key.Key_Up: (0, -1), Qt.Key.Key_Down: (0, 1)}
        if key in pan:
            step = (self.viewport().width() // 10) * (5 if event.modifiers() & Qt.KeyboardModifier.ShiftModifier else 1)
            dx, dy = pan[key]
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + dx * step)
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + dy * step)
        elif key in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
            self.zoom_by(ZOOM_STEP)
        elif key == Qt.Key.Key_Minus:
            self.zoom_by(1 / ZOOM_STEP)
        elif key == Qt.Key.Key_0:
            self.fit_view()
        elif key in (Qt.Key.Key_PageUp, Qt.Key.Key_PageDown):
            self.board_step.emit(-1 if key == Qt.Key.Key_PageUp else 1)
        else:
            super().keyPressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802 (Qt override)
        """Report the pointer position in model millimetres."""
        point: QPointF = self.mapToScene(event.position().toPoint())
        self.cursor_moved.emit(point.x(), -point.y())
        super().mouseMoveEvent(event)

    def drawForeground(self, painter: QPainter, rect: QRectF | QRect) -> None:  # noqa: N802 (Qt override)
        """Draw the legend, and the focus ring inside the viewport edge while the canvas has focus (AX-03)."""
        if self._tokens is None:
            return
        painter.save()
        painter.resetTransform()
        self._draw_legend(painter)
        painter.restore()
        if not self.hasFocus():
            return
        painter.save()
        painter.resetTransform()
        width = self._tokens.focus_ring_px
        painter.setPen(QPen(QColor(self._tokens.colours["focus-ring"]), width))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        inset = width / 2
        painter.drawRect(QRectF(self.viewport().rect()).adjusted(inset, inset, -inset, -inset))
        painter.restore()

    def focusInEvent(self, event) -> None:  # noqa: N802 (Qt override)
        """Repaint so the focus ring appears."""
        super().focusInEvent(event)
        self.viewport().update()

    def focusOutEvent(self, event) -> None:  # noqa: N802 (Qt override)
        """Repaint so the focus ring disappears."""
        super().focusOutEvent(event)
        self.viewport().update()
