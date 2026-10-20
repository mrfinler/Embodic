"""The layer cue of the geometry view (design_spec.md 3.3.1): a casing and an outline, both measured in screen pixels.

The view builds the centre lines of a layer's copper once per view change (`Strokes`). `LayerCueItem` keeps them and
strokes them at paint time with pens whose width follows the zoom, so a zoom step builds no geometry, as the eye hatch
does (design_spec.md 3.3). A pen stroke of each centre line at its trace width is the copper of that layer, and the
strokes of one pass fill as one union, so copper that joins shows one edge and no seam.

The item caches what it painted in device pixels (Qt's `DeviceCoordinateCache`). A pan moves the cache and paints only
the strip that comes into view; a repaint with nothing changed paints nothing; a zoom paints the view again.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import NamedTuple

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmapCache
from PySide6.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget

CASING_PX = 2.0  # board-fill band around the copper of every visible layer except the bottom one
OUTLINE_PX = 1.5  # width of the outline of every visible layer below the top one, inside the true edge
SOLID_BELOW_PX = 2 * OUTLINE_PX + 1  # a shape narrower than this keeps no empty inside, so it reads solid (3.3.1)
CACHE_LIMIT_KB = 200 * 1024  # what Qt's pixmap cache may hold: the device cache of the cue stays under 200 MB


class Part(NamedTuple):
    """The centre line of one primitive, its trace width and the rectangle of its copper, in scene millimetres."""

    width_mm: float
    centre: QPainterPath
    box: QRectF

    @classmethod
    def of(cls, width_mm: float, centre: QPainterPath) -> "Part":
        """Return the part of ``centre`` stroked ``width_mm`` wide; the box is never empty, even for a straight line."""
        half = width_mm / 2
        return cls(width_mm, centre, centre.boundingRect().adjusted(-half, -half, half, half))


@dataclass(frozen=True, slots=True)
class Strokes:
    """The centre lines of a layer's copper, one part per primitive, grouped by trace width; ``bounds`` holds them.

    The lines stay separate: one path of all of them strokes about ten times slower in Qt's rasteriser than one
    ``drawPath`` per primitive, which is how the view drew copper before the cue (measured on the serpentine example).
    """

    groups: tuple[tuple[float, tuple[Part, ...]], ...]
    bounds: QRectF

    @classmethod
    def of(cls, parts: Iterable[Part]) -> "Strokes":
        """Collect ``parts`` by width and their extent."""
        by_width: dict[float, list[Part]] = {}
        bounds = QRectF()
        for part in parts:
            by_width.setdefault(part.width_mm, []).append(part)
            bounds = bounds.united(part.box)
        return cls(tuple((width, tuple(kept)) for width, kept in by_width.items()), bounds)


class Level(NamedTuple):
    """One copper layer of the cue: the casing under its copper, then its outlines, one `Strokes` per ink.

    ``casing`` is None for the bottom layer. ``outlines`` is empty for the top layer, whose solid copper the view draws
    over the cue.
    """

    casing: Strokes | None
    outlines: tuple[tuple[QColor, Strokes], ...]


def _stroke(
    painter: QPainter, strokes: Strokes, colour: QColor, grow_mm: float, seen: QRectF, from_width_mm: float = 0.0
) -> None:
    """Stroke every trace of at least ``from_width_mm``, at its width plus ``grow_mm``, that reaches ``seen``."""
    for width, parts in strokes.groups:
        if width < from_width_mm:
            continue
        reach = max(grow_mm, 0.0) / 2
        near = seen.adjusted(-reach, -reach, reach, reach)
        painter.setPen(
            QPen(colour, width + grow_mm, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        )
        for part in parts:
            if part.box.intersects(near):
                painter.drawPath(part.centre)


def _drawn_rect(painter: QPainter, exposed: QRectF) -> QRectF:
    """Return the part of ``exposed`` that the painter can show, in item coordinates, grown by a pixel.

    Qt hands a cached item the whole bounding rectangle to paint and clips to the cache, which holds the view only, so
    the clip and the device give the rectangle the paint is for. A trace outside it is left out before it is stroked.
    """
    world = painter.worldTransform()
    scale = world.m11()
    device = painter.device()
    inverse, invertible = world.inverted()
    seen = exposed
    if invertible:
        seen = seen.intersected(inverse.mapRect(QRectF(0, 0, device.width(), device.height())))
    clip = painter.clipBoundingRect()
    if not clip.isEmpty():
        seen = seen.intersected(clip)
    pixel = 1 / scale
    return seen.adjusted(-pixel, -pixel, pixel, pixel)


class LayerCueItem(QGraphicsItem):
    """The casings and outlines of all copper layers, from the bottom one up, in one item.

    Per layer, bottom first: a casing, CASING_PX wide around the copper in the board colour, over the layers already
    drawn; then the layer's copper as an outline, OUTLINE_PX wide inside the true edge with the inside left empty. The
    copper is stroked in its ink, then the inside of every trace wide enough to have one is stroked OUTLINE_PX narrower
    on each side in the board colour, at full opacity. The casing under the layer already hides the layers below, so the
    inside reads as empty; full opacity keeps it empty while the ink is dimmed. A trace narrower than SOLID_BELOW_PX
    has no inside and stays solid.

    The bounding rectangle reaches one extent past the copper on every side, which holds a casing of CASING_PX at any
    zoom down to one pixel per extent, so no zoom step has to resize it. Qt keeps the cache of the part in view only.
    """

    def __init__(self, levels: Iterable[Level], board_fill: QColor) -> None:
        super().__init__()
        self._levels = tuple(levels)
        self._board_fill = board_fill
        self._ink_opacity = 1.0
        extent = QRectF()
        for level in self._levels:
            for strokes in (level.casing, *(strokes for _, strokes in level.outlines)):
                if strokes is not None:
                    extent = extent.united(strokes.bounds)
        reach = max(extent.width(), extent.height(), 1.0)
        self._bounds = extent.adjusted(-reach, -reach, reach, reach)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemUsesExtendedStyleOption)
        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)
        if QPixmapCache.cacheLimit() < CACHE_LIMIT_KB:
            QPixmapCache.setCacheLimit(CACHE_LIMIT_KB)

    def boundingRect(self) -> QRectF:  # noqa: N802 (Qt override)
        """Return the copper's extent grown by one extent on every side."""
        return self._bounds

    def set_ink_opacity(self, opacity: float) -> None:
        """Paint the ink of the outlines at ``opacity``, as the DRC locate dims the copper; the casings stay opaque."""
        if opacity != self._ink_opacity:
            self._ink_opacity = opacity
            self.update()

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None) -> None:
        """Stroke the casing and the outlines of every layer that reaches the exposed rectangle."""
        scale = painter.worldTransform().m11()
        seen = _drawn_rect(painter, option.exposedRect)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for level in self._levels:
            painter.setOpacity(1.0)
            if level.casing is not None:
                _stroke(painter, level.casing, self._board_fill, 2 * CASING_PX / scale, seen)
            for ink, strokes in level.outlines:
                painter.setOpacity(self._ink_opacity)
                _stroke(painter, strokes, ink, 0.0, seen)
                painter.setOpacity(1.0)
                _stroke(
                    painter,
                    strokes,
                    self._board_fill,
                    -2 * OUTLINE_PX / scale,
                    seen,
                    from_width_mm=SOLID_BELOW_PX / scale,
                )
        painter.restore()
