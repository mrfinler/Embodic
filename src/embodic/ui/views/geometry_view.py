"""The zoomable, pannable drawing of the boards: copper in model millimetres, coil-eye fills, phase letters.

Scene units are millimetres with y negated (Qt's y points down). Copper pens are as wide as the trace in
millimetres, so stroke widths follow the zoom (UI-03). Copper is never dashed (design_spec.md section 3.3).
"""

import math

from PySide6.QtCore import QPointF, QRect, QRectF, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFontMetricsF,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
    QTransform,
    QWheelEvent,
)
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
)

from embodic.geometry.layout import Layout
from embodic.geometry.primitives import Line, Primitive
from embodic.model.vocabulary import Phase
from embodic.ui.strings import text
from embodic.ui.theme import PhaseStyle, ThemeTokens
from embodic.ui.viewmodels.appearance import PhaseRenderMode
from embodic.ui.viewmodels.outcome import CoilMark, GeometryScene

ZOOM_MIN, ZOOM_MAX = 0.1, 200.0  # relative to the fitted view (UI-03)
ZOOM_STEP = 1.25
EYE_TINT_ALPHA = 26  # 10 % of 255: the solid eye tint of phase A
HATCH_LINES = 4  # per eye radius
LABEL_PX = 12
LABEL_HALO_PX = 3  # board-coloured outline that keeps a letter readable over hatch and copper
DATA_LAYER = 0  # QGraphicsItem.data key: copper layer name ("" for board items)
DATA_PHASE = 1  # QGraphicsItem.data key: phase letter or ""
DATA_KIND = 2  # QGraphicsItem.data key: "copper", "eye", "hatch", "label", "label-halo", "via", "pad", "outline"


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


def hatch_path(mark: CoilMark, angle_deg: int) -> QPainterPath:
    """Return parallel chords of the eye disc at ``angle_deg``; each chord ends on the circle, so none leaves it."""
    path = QPainterPath()
    r = mark.eye_radius_mm
    ux, uy = math.cos(math.radians(angle_deg)), math.sin(math.radians(angle_deg))
    spacing = r / HATCH_LINES
    for k in range(-HATCH_LINES + 1, HATCH_LINES):
        offset = k * spacing
        half = math.sqrt(max(r * r - offset * offset, 0.0))
        mx, my = mark.cx_mm - uy * offset, mark.cy_mm + ux * offset
        path.moveTo(mx - ux * half, -(my - uy * half))
        path.lineTo(mx + ux * half, -(my + uy * half))
    return path


class GeometryView(QGraphicsView):
    """Draws a GeometryScene; layers in ``hidden`` are left out of the scene, not merely hidden."""

    cursor_moved = Signal(float, float)

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

    def show_geometry(
        self,
        geometry: GeometryScene | None,
        tokens: ThemeTokens,
        mode: PhaseRenderMode,
        hidden: frozenset[str],
    ) -> None:
        """Redraw with new content, theme, render mode or layer visibility; keeps the zoom when the extent stays."""
        first = self._geometry is None and geometry is not None
        self._geometry, self._tokens, self._mode, self._hidden = geometry, tokens, mode, hidden
        self.setBackgroundBrush(QColor(tokens.colours["canvas"]))
        self._rebuild()
        if first:
            self.fit_view()

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
        if self._geometry is None or self._tokens is None:
            return
        for board in self._geometry.boards:
            self._draw_board(board)
        visible = [layer for layer in self._geometry.layers if layer not in self._hidden]
        for layer in reversed(visible):
            for board in self._geometry.boards:
                self._draw_copper(board, layer)
        if visible:
            for mark in (m for m in self._geometry.marks if m.layer == visible[0]):
                self._draw_mark(mark)
        bounds = scene.itemsBoundingRect()
        scene.setSceneRect(bounds.adjusted(-bounds.width(), -bounds.height(), bounds.width(), bounds.height()))

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
        self._tag(self.scene().addPath(outline, pen, QBrush(QColor(colours["board-fill"]))), "outline")
        for hole in board.outline.holes:
            self._tag(self.scene().addEllipse(_disc(hole.x_mm, hole.y_mm, hole.diameter_mm / 2), pen, canvas), "hole")

    def _draw_copper(self, board: Layout, layer: str) -> None:
        assert self._tokens is not None
        no_pen = QPen(Qt.PenStyle.NoPen)
        for path in (p for p in board.paths if p.layer == layer):
            colour = self._copper_colour(path.phase)
            for prim in path.primitives:
                pen = QPen(colour, prim.width_mm, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
                self._tag(self.scene().addPath(primitive_path(prim), pen), "copper", layer, path.phase)
        via_fill = QColor(self._tokens.colours["text-3"])
        for via in (v for v in board.vias if layer in (v.layer_from, v.layer_to)):
            self._tag(
                self.scene().addEllipse(_disc(via.x_mm, via.y_mm, via.pad_mm / 2), no_pen, via_fill), "via", layer
            )
        pad_fill = QColor(self._tokens.colours["text-2"])
        for pad in (p for p in board.pads if p.layer in (None, layer)):
            rect = QRectF(pad.x_mm - pad.width_mm / 2, -pad.y_mm - pad.height_mm / 2, pad.width_mm, pad.height_mm)
            self._tag(self.scene().addRect(rect, no_pen, pad_fill), "pad", layer)

    def _draw_mark(self, mark: CoilMark) -> None:
        assert self._tokens is not None
        style = self._tokens.phase_style(mark.phase)
        colour = self._phase_colour(style)
        r = mark.eye_radius_mm
        if r > 0:
            disc = _disc(mark.cx_mm, mark.cy_mm, r)
            if style.hatch_deg == 0:
                tint = QColor(colour)
                tint.setAlpha(EYE_TINT_ALPHA)
                eye = self.scene().addEllipse(disc, QPen(Qt.PenStyle.NoPen), tint)
                self._tag(eye, "eye", mark.layer, mark.phase)
            else:
                hatch = self.scene().addPath(hatch_path(mark, style.hatch_deg), QPen(colour, 0))
                self._tag(hatch, "hatch", mark.layer, mark.phase)
        label = QGraphicsSimpleTextItem(mark.label)
        font = label.font()
        font.setPixelSize(LABEL_PX)
        label.setFont(font)
        label.setBrush(QColor(self._tokens.colours["text-1"]))
        bounds = label.boundingRect()
        centre = QTransform.fromTranslate(-bounds.width() / 2, -bounds.height() / 2)
        outline = QPainterPath()
        outline.addText(0, QFontMetricsF(font).ascent(), font, mark.label)
        halo_colour = QColor(self._tokens.colours["board-fill"])
        halo_pen = QPen(
            halo_colour, LABEL_HALO_PX, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin
        )
        halo = QGraphicsPathItem(outline)
        halo.setPen(halo_pen)
        for item, kind in ((halo, "label-halo"), (label, "label")):
            item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
            item.setPos(mark.cx_mm, -mark.cy_mm)
            item.setTransform(centre)
            self.scene().addItem(item)
            self._tag(item, kind, mark.layer, mark.phase)

    def zoom_factor(self) -> float:
        """Return the current scale relative to the fitted view."""
        return self.transform().m11() / self._fit_scale

    def fit_view(self) -> None:
        """Fit every drawn item into the view."""
        items = self.scene().itemsBoundingRect()
        if items.isEmpty():
            return
        self.resetTransform()
        self.fitInView(items, Qt.AspectRatioMode.KeepAspectRatio)
        self._fit_scale = self.transform().m11()

    def zoom_by(self, factor: float) -> None:
        """Zoom by a factor, kept between 0.1x and 200x the fitted view."""
        target = min(max(self.zoom_factor() * factor, ZOOM_MIN), ZOOM_MAX)
        step = target / self.zoom_factor()
        self.scale(step, step)

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
        else:
            super().keyPressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802 (Qt override)
        """Report the pointer position in model millimetres."""
        point: QPointF = self.mapToScene(event.position().toPoint())
        self.cursor_moved.emit(point.x(), -point.y())
        super().mouseMoveEvent(event)

    def drawForeground(self, painter: QPainter, rect: QRectF | QRect) -> None:  # noqa: N802 (Qt override)
        """Draw the focus ring inside the viewport edge while the canvas has focus (AX-03)."""
        if not self.hasFocus() or self._tokens is None:
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
