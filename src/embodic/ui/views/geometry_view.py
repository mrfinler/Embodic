"""The zoomable, pannable drawing of the boards: copper in model millimetres, coil-eye fills, phase labels, legend.

Scene units are millimetres with y negated (Qt's y points down). Copper pens are as wide as the trace in
millimetres, so stroke widths follow the zoom (UI-03). Copper is never dashed (design_spec.md section 3.3). While two or
more copper layers show, the layers below the top one are outlined and cased (section 3.3.1, `layer_cue`). Labels
and eyes come from `embodic.geometry.labels` and `embodic.geometry.marks`, the modules the exports draw from; the
labels are placed again after every zoom, pan or resize step, so they never overlap at any zoom (ruling b).
"""

import math
from collections.abc import Iterator
from contextlib import contextmanager
from typing import NamedTuple

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
from embodic.geometry.layout import Layout, Pad
from embodic.geometry.marks import CoilMark
from embodic.geometry.paths import CopperPath
from embodic.geometry.primitives import Line, Primitive
from embodic.io.exporters import pad_outline
from embodic.model.vocabulary import Phase
from embodic.ui.fonts import JETBRAINS_MONO
from embodic.ui.strings import text
from embodic.ui.theme import PhaseStyle, ThemeTokens
from embodic.ui.viewmodels.appearance import PhaseRenderMode
from embodic.ui.viewmodels.outcome import (
    BoardMarks,
    GeometryScene,
    eyes_shown,
    phases_drawn,
    place_in_view,
)
from embodic.ui.views.layer_cue import LayerCueItem, Level, Part, Strokes

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
LEGEND_LAYER_BAR_PX = (20, 6)  # the bar of a layer row: length, thickness (design_spec.md 3.3.1)
LEGEND_LAYER_OUTLINE_PX = 1.5  # the outlined bar's edge, inside its rectangle
LEGEND_SWATCH_PX = 12  # eye swatch diameter
LEGEND_GAP_PX = 6
STAMP_MARGIN_PX = 8
STAMP_PAD_PX = 4
STAMP_PX = 12
DATA_LAYER = 0  # QGraphicsItem.data key: copper layer name ("" for board items)
DATA_PHASE = 1  # QGraphicsItem.data key: phase letter or ""
DATA_KIND = 2  # QGraphicsItem.data key: "copper", "copper-cue", "eye", "hatch", "label",
# "label-halo", "leader", "via", "pad", "drill", "outline", "hole"
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


class CopperEntry(NamedTuple):
    """One primitive of a copper path with its centre line and the marks of its board (hover text)."""

    path: CopperPath
    prim: Primitive
    part: Part
    marks: BoardMarks


def _disc(x_mm: float, y_mm: float, r_mm: float) -> QRectF:
    return QRectF(x_mm - r_mm, -y_mm - r_mm, 2 * r_mm, 2 * r_mm)


def _pad_path(pad: Pad) -> QPainterPath:
    """Return the closed shape of a square, rect or oblong pad, as the exporters draw it (`pad_outline`)."""
    path = QPainterPath()
    for prim in pad_outline(pad):
        if path.elementCount() == 0:
            path.addPath(primitive_path(prim))
        else:
            path.connectPath(primitive_path(prim))
    path.closeSubpath()
    return path


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


def stamp_font() -> QFont:
    """Return the font of the version stamp (fix_wave_f1.md (d))."""
    font = QFont(JETBRAINS_MONO)
    font.setPixelSize(STAMP_PX)
    return font


class GeometryView(QGraphicsView):
    """Draws a GeometryScene; layers in ``hidden`` are left out of the scene, not merely hidden."""

    cursor_moved = Signal(float, float)
    board_step = Signal(int)  # Page Up (-1) and Page Down (+1): the board picker's previous and next item
    layer_step = Signal(int)  # [ (-1) and ] (+1): the previous and next layer solo

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
        self._fitted = True  # at fit zoom until the user zooms or pans; a resize then fits again (U-S4e ruling h)
        self._press_scroll = (0, 0)
        self._tokens: ThemeTokens | None = None
        self._geometry: GeometryScene | None = None
        self._mode = PhaseRenderMode.COLOUR
        self._hidden: frozenset[str] = frozenset()
        self._extent = QRectF()
        self._label_items: list[QGraphicsItem] = []
        self._labels_held = False
        self._font = label_font()
        self._metrics = QFontMetricsF(self._font)
        self._stamp: str | None = None
        self._stamp_font = stamp_font()
        self._stamp_metrics = QFontMetricsF(self._stamp_font)

    def show_geometry(
        self,
        geometry: GeometryScene | None,
        tokens: ThemeTokens,
        mode: PhaseRenderMode,
        hidden: frozenset[str],
        stamp: str | None = None,
    ) -> None:
        """Redraw with new content, theme, render mode or layer visibility; keeps the zoom when the extent stays.

        ``stamp`` names the outcome of ``geometry`` (REQ-T-14); None while nothing is drawn.
        """
        self.set_stamp(stamp)
        if geometry is self._geometry and tokens is self._tokens and mode is self._mode and hidden == self._hidden:
            return
        first = self._geometry is None and geometry is not None
        self._geometry, self._tokens, self._mode, self._hidden = geometry, tokens, mode, hidden
        self.setBackgroundBrush(QColor(tokens.colours["canvas"]))
        with self._holding_labels():
            self._rebuild()
        if first:
            self.fit_view()
        else:
            self.place_labels()

    @contextmanager
    def _holding_labels(self) -> Iterator[None]:
        """Hold label placement while the view changes in several scroll steps; the caller places them once after."""
        held, self._labels_held = self._labels_held, True
        try:
            yield
        finally:
            self._labels_held = held

    def _shown(self) -> list[tuple[Layout, BoardMarks]]:
        if self._geometry is None:
            return []
        return list(zip(self._geometry.boards, self._geometry.marks, strict=True))

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
        self._label_items = []
        self._extent = QRectF()
        if self._geometry is None or self._tokens is None:
            return
        shown = self._shown()
        for board, _ in shown:
            self._draw_board(board)
        layers = [(layer, self._copper_entries(shown, layer)) for layer in reversed(self._visible_layers())]
        if len(layers) >= 2:
            for layer, entries in layers[:-1]:
                self._add_copper(layer, entries, painted=False)
            self._add_cue(layers)
        for layer, entries in layers[-1:]:
            self._add_copper(layer, entries, painted=True)
        visible = [layer for layer, _ in reversed(layers)]
        for board, _ in shown:
            self._draw_lands(board, visible)
        for board, marks in shown:
            for mark in eyes_shown(board, marks, self._hidden):
                self._draw_eye(mark)
        bounds = self._extent
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
        item = self.scene().addPath(outline, pen, QBrush(QColor(colours["board-fill"])))
        self._tag(item, "outline")
        self._extent = self._extent.united(item.boundingRect())
        for hole in board.outline.holes:
            self._tag(self.scene().addEllipse(_disc(hole.x_mm, hole.y_mm, hole.diameter_mm / 2), pen, canvas), "hole")

    def _visible_layers(self) -> list[str]:
        """Return the copper layers shown, top of the stack first."""
        if self._geometry is None:
            return []
        return [layer for layer in self._geometry.layers if layer not in self._hidden]

    def _copper_entries(self, shown: list[tuple[Layout, BoardMarks]], layer: str) -> list[CopperEntry]:
        """Return the primitives of ``layer`` on every board, each with its centre line, built once per view change."""
        return [
            CopperEntry(path, prim, Part.of(prim.width_mm, primitive_path(prim)), marks)
            for board, marks in shown
            for path in board.paths
            if path.layer == layer
            for prim in path.primitives
        ]

    def _add_copper(self, layer: str, entries: list[CopperEntry], *, painted: bool) -> None:
        """Add one item per primitive of ``layer``: its solid stroke, or only its hover text and tags if not painted.

        A layer below the top one is drawn by the cue item (`layer_cue`), so its items paint nothing.
        """
        for entry in entries:
            colour, width = self._copper_colour(entry.path.phase), entry.prim.width_mm
            pen = QPen(colour, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            item = self.scene().addPath(entry.part.centre, pen)
            item.setToolTip(entry.marks.label_of_path.get(entry.path.id, ""))
            self._tag(item, "copper", layer, entry.path.phase)
            if not painted:
                item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemHasNoContents)

    def _add_cue(self, layers: list[tuple[str, list[CopperEntry]]]) -> None:
        """Add the casings and outlines of ``layers``, bottom layer first, as one item (design_spec.md 3.3.1).

        Every layer but the bottom one has a casing; every layer but the top one is drawn as an outline per phase.
        """
        assert self._tokens is not None
        board_fill = QColor(self._tokens.colours["board-fill"])
        levels = []
        for rank, (_, entries) in enumerate(layers):
            if not entries:
                continue
            casing = Strokes.of(entry.part for entry in entries) if rank > 0 else None
            inks: dict[Phase | None, list[Part]] = {}
            if rank < len(layers) - 1:
                for entry in entries:
                    inks.setdefault(entry.path.phase, []).append(entry.part)
            outlines = tuple((self._copper_colour(phase), Strokes.of(parts)) for phase, parts in inks.items())
            levels.append(Level(casing, outlines))
        if levels:
            cue = LayerCueItem(levels, board_fill)
            self.scene().addItem(cue)
            self._tag(cue, "copper-cue")

    def _draw_lands(self, board: Layout, visible: list[str]) -> None:
        """Draw the vias and pads that land on a visible layer, once each and after all copper (design_spec.md 3.3.1).

        A land joins layers, so it is never outlined or cased. Its layer tag is the top visible layer it lands on.
        """
        assert self._tokens is not None and self._geometry is not None
        colours = self._tokens.colours
        no_pen = QPen(Qt.PenStyle.NoPen)
        stack = self._geometry.layers
        via_fill, pad_fill, drill_fill = (QColor(colours[k]) for k in ("text-3", "text-2", "canvas"))
        for via in board.vias:
            first, last = sorted((stack.index(via.layer_from), stack.index(via.layer_to)))
            if landed := [layer for layer in visible if first <= stack.index(layer) <= last]:
                disc = self.scene().addEllipse(_disc(via.x_mm, via.y_mm, via.pad_mm / 2), no_pen, via_fill)
                self._tag(disc, "via", landed[0])
        for pad in board.pads:
            if pad.layer is not None and pad.layer not in visible:
                continue
            layer = pad.layer or visible[0]
            if pad.shape == "round":
                land: QGraphicsEllipseItem | QGraphicsPathItem = self.scene().addEllipse(
                    _disc(pad.x_mm, pad.y_mm, pad.width_mm / 2), no_pen, pad_fill
                )
            else:
                land = self.scene().addPath(_pad_path(pad), no_pen, pad_fill)
            self._tag(land, "pad", layer)
            if pad.drill_mm > 0:
                drill = self.scene().addEllipse(_disc(pad.x_mm, pad.y_mm, pad.drill_mm / 2), no_pen, drill_fill)
                self._tag(drill, "drill", layer)

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

    def _box_mm(self, rect: QRectF) -> Box | None:
        if rect.isEmpty():
            return None
        corners = self.mapToScene(rect.toAlignedRect()).boundingRect()
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
            return
        anchors = [a for _, m in shown for a in m.anchors]
        obstacles = [box for _, m in shown for box in m.pads]
        obstacles += [
            box for rect in (self.legend_rect(), self.stamp_rect()) if (box := self._box_mm(rect)) is not None
        ]
        copper: dict[Phase, list[tuple[float, float]]] = {}
        for _, marks in shown:
            for phase, spots in marks.copper.items():
                copper.setdefault(phase, []).extend(spots)
        placed = place_in_view(
            anchors,
            view=self._viewport_mm(),
            text_size=self._text_size,
            obstacles=obstacles,
            ring_outer_mm=max(board.envelope_mm[1] for board, _ in shown),
            copper=copper,
            copper_reach_mm=max(marks.copper_reach_mm for _, marks in shown),
        )
        for label in placed:
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

    def legend_layer_rows(self) -> tuple[str, ...]:
        """Return the texts of the layer rows under the phase rows: "{layer} on top", "Layers below".

        They show while the layer cue applies: two or more copper layers visible (design_spec.md 3.3.1).
        """
        visible = self._visible_layers()
        if len(visible) < 2:
            return ()
        return (text("shell.legend.layer-top", layer=visible[0]), text("shell.legend.layers-below"))

    def _legend_texts(self) -> list[str]:
        phases = [text("shell.legend.phase", phase=p.value) for p in self.legend_phases()]
        return phases + list(self.legend_layer_rows())

    def legend_rect(self) -> QRectF:
        """Return the legend panel in viewport pixels, top left; empty when there is no legend."""
        rows = self._legend_texts()
        if not rows:
            return QRectF()
        widest = max(self._metrics.horizontalAdvance(row) for row in rows)
        width = 2 * LEGEND_PAD_PX + LEGEND_BAR_PX[0] + LEGEND_SWATCH_PX + 2 * LEGEND_GAP_PX + widest
        return QRectF(LEGEND_MARGIN_PX, LEGEND_MARGIN_PX, width, 2 * LEGEND_PAD_PX + LEGEND_ROW_PX * len(rows))

    def legend_row_geometry(self, row: int) -> tuple[QRectF, QRectF, QPointF]:
        """Return, for one legend row in viewport pixels, the copper bar, the eye swatch and the text origin.

        Rows after the phase rows are the layer rows: their bar is thicker and they have no eye, so the swatch of such
        a row is the empty rectangle where it would be.
        """
        panel = self.legend_rect()
        mid = panel.top() + LEGEND_PAD_PX + (row + 0.5) * LEGEND_ROW_PX
        x = panel.left() + LEGEND_PAD_PX
        length, thickness = LEGEND_BAR_PX if row < len(self.legend_phases()) else LEGEND_LAYER_BAR_PX
        bar = QRectF(x, mid - thickness / 2, length, thickness)
        x += length + LEGEND_GAP_PX
        swatch = QRectF(x, mid - LEGEND_SWATCH_PX / 2, LEGEND_SWATCH_PX, LEGEND_SWATCH_PX)
        x += LEGEND_SWATCH_PX + LEGEND_GAP_PX
        return bar, swatch, QPointF(x, mid + (self._metrics.ascent() - self._metrics.descent()) / 2)

    def _draw_legend(self, painter: QPainter) -> None:
        assert self._tokens is not None
        phases = self.legend_phases()
        layer_rows = self.legend_layer_rows()
        if not phases and not layer_rows:
            return
        colours = self._tokens.colours
        painter.setPen(QPen(QColor(colours["border-control"]), 1))
        painter.setBrush(QColor(colours["surface"]))
        painter.drawRoundedRect(self.legend_rect(), 6, 6)
        painter.setFont(self._font)
        for row, phase in enumerate(phases):
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
        for offset, label in enumerate(layer_rows):
            bar, _, origin = self.legend_row_geometry(len(phases) + offset)
            painter.fillRect(bar, QColor(colours["text-1"]))
            if offset == 1:
                inset = LEGEND_LAYER_OUTLINE_PX
                painter.fillRect(bar.adjusted(inset, inset, -inset, -inset), QColor(colours["surface"]))
            painter.setPen(QColor(colours["text-1"]))
            painter.drawText(origin, label)

    def set_stamp(self, stamp: str | None) -> None:
        """Show ``stamp`` at the bottom left and end the accessible description with it; labels avoid it once placed."""
        if stamp == self._stamp:
            return
        self._stamp = stamp
        self.setAccessibleDescription(stamp or "")
        self.viewport().update()

    def stamp(self) -> str | None:
        """Return the version stamp drawn on the canvas (UI-32), or None while nothing is drawn."""
        return self._stamp

    def stamp_rect(self) -> QRectF:
        """Return the stamp plate in viewport pixels, bottom left; empty without a stamp."""
        if self._stamp is None:
            return QRectF()
        width = self._stamp_metrics.horizontalAdvance(self._stamp) + 2 * STAMP_PAD_PX
        height = self._stamp_metrics.height() + 2 * STAMP_PAD_PX
        return QRectF(STAMP_MARGIN_PX, self.viewport().height() - STAMP_MARGIN_PX - height, width, height)

    def _draw_stamp(self, painter: QPainter) -> None:
        assert self._tokens is not None
        if self._stamp is None:
            return
        plate = self.stamp_rect()
        painter.fillRect(plate, QColor(self._tokens.colours["canvas"]))
        painter.setFont(self._stamp_font)
        painter.setPen(QColor(self._tokens.colours["text-3"]))
        painter.drawText(plate, Qt.AlignmentFlag.AlignCenter, self._stamp)

    def zoom_factor(self) -> float:
        """Return the current scale relative to the fitted view."""
        return self.transform().m11() / self._fit_scale

    def fit_view(self) -> None:
        """Fit the drawn boards into the view."""
        if self._extent.isEmpty():
            return
        with self._holding_labels():
            self.resetTransform()
            self.fitInView(self._extent, Qt.AspectRatioMode.KeepAspectRatio)
        self._fit_scale = self.transform().m11()
        self._fitted = True
        self.place_labels()

    def zoom_by(self, factor: float) -> None:
        """Zoom by a factor, kept between 0.1x and 200x the fitted view, then place the labels again."""
        target = min(max(self.zoom_factor() * factor, ZOOM_MIN), ZOOM_MAX)
        step = target / self.zoom_factor()
        self.scale(step, step)
        self._fitted = False
        self.place_labels()

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802 (Qt override)
        """Fit again while the view is at fit zoom (a resize, splitter drag or tab switch); else place the labels."""
        super().resizeEvent(event)
        if self._fitted:
            self.fit_view()
        else:
            self.place_labels()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802 (Qt override)
        """Remember the scroll position, so a drag that pans leaves fit zoom."""
        self._press_scroll = (self.horizontalScrollBar().value(), self.verticalScrollBar().value())
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802 (Qt override)
        """End a drag; one that moved the view leaves fit zoom."""
        super().mouseReleaseEvent(event)
        if (self.horizontalScrollBar().value(), self.verticalScrollBar().value()) != self._press_scroll:
            self._fitted = False

    def scrollContentsBy(self, dx: int, dy: int) -> None:  # noqa: N802 (Qt override)
        """Place the labels again after a pan step: the view edge decides which labels fit."""
        super().scrollContentsBy(dx, dy)
        if not self._labels_held:
            self.place_labels()

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802 (Qt override)
        """Zoom around the pointer."""
        self.zoom_by(ZOOM_STEP if event.angleDelta().y() > 0 else 1 / ZOOM_STEP)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802 (Qt override)
        """Arrow keys pan (Shift five times as far); +, - and 0 zoom; Page Up and Down and [ and ] step (spec 10)."""
        key = Qt.Key(event.key())
        pan = {Qt.Key.Key_Left: (-1, 0), Qt.Key.Key_Right: (1, 0), Qt.Key.Key_Up: (0, -1), Qt.Key.Key_Down: (0, 1)}
        if key in pan:
            step = (self.viewport().width() // 10) * (5 if event.modifiers() & Qt.KeyboardModifier.ShiftModifier else 1)
            dx, dy = pan[key]
            self._fitted = False
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + dx * step)
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + dy * step)
        elif key in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
            self.zoom_by(ZOOM_STEP)
        elif key == Qt.Key.Key_Minus:
            self.zoom_by(1 / ZOOM_STEP)
        elif key == Qt.Key.Key_0:
            self.fit_view()
        elif key in (Qt.Key.Key_PageUp, Qt.Key.Key_PageDown):
            self.board_step.emit(1 if key == Qt.Key.Key_PageDown else -1)
        elif key in (Qt.Key.Key_BracketLeft, Qt.Key.Key_BracketRight):
            self.layer_step.emit(1 if key == Qt.Key.Key_BracketRight else -1)
        else:
            super().keyPressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802 (Qt override)
        """Report the pointer position in model millimetres."""
        point: QPointF = self.mapToScene(event.position().toPoint())
        self.cursor_moved.emit(point.x(), -point.y())
        super().mouseMoveEvent(event)

    def drawForeground(self, painter: QPainter, rect: QRectF | QRect) -> None:  # noqa: N802 (Qt override)
        """Draw the legend, the stamp and, with focus, the focus ring inside the viewport edge (AX-03)."""
        if self._tokens is None:
            return
        painter.save()
        painter.resetTransform()
        self._draw_legend(painter)
        self._draw_stamp(painter)
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
