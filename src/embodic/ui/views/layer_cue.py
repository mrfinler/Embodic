"""The layer cue of the geometry view (design_spec.md 3.3.1): a casing and an outline, both measured in screen pixels.

The view builds the centre lines of a layer's copper once per view change (`Strokes`). The items below keep them and
stroke them at paint time with pens whose width follows the zoom, so a zoom step builds no geometry, as the eye hatch
does (design_spec.md 3.3). A pen stroke of each centre line at its trace width is the copper of that layer, and the
strokes of one item fill as one union, so copper that joins shows one edge and no seam.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import NamedTuple

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget

CASING_PX = 2.0  # board-fill band around the copper of every visible layer except the bottom one
OUTLINE_PX = 1.5  # width of the outline of every visible layer below the top one, inside the true edge
SOLID_BELOW_PX = 2 * OUTLINE_PX + 1  # a shape narrower than this keeps no empty inside, so it reads solid (3.3.1)


class Part(NamedTuple):
    """The centre line of one primitive, its trace width and the rectangle of the line alone, in scene millimetres."""

    width_mm: float
    centre: QPainterPath
    box: QRectF


@dataclass(frozen=True, slots=True)
class Strokes:
    """The centre lines of a layer's copper, one part per primitive; ``bounds`` holds them at full width.

    The lines stay separate: one path of all of them strokes about ten times slower in Qt's rasteriser than one
    ``drawPath`` per primitive, which is how the view drew copper before the cue (measured on the serpentine example).
    """

    parts: tuple[Part, ...]
    bounds: QRectF

    @classmethod
    def of(cls, parts: Iterable[Part]) -> "Strokes":
        """Collect ``parts`` and their extent."""
        kept = tuple(parts)
        bounds = QRectF()
        for part in kept:
            half = part.width_mm / 2
            bounds = bounds.united(part.box.adjusted(-half, -half, half, half))
        return cls(kept, bounds)


class _StrokedItem(QGraphicsItem):
    """An item that strokes ``Strokes`` in screen pixels.

    The bounding rectangle reaches one extent past the copper on every side, which holds a casing of CASING_PX at any
    zoom down to one pixel per extent, so no zoom step has to resize it.
    """

    def __init__(self, strokes: Strokes) -> None:
        super().__init__()
        self._strokes = strokes
        reach = max(strokes.bounds.width(), strokes.bounds.height(), 1.0)
        self._bounds = strokes.bounds.adjusted(-reach, -reach, reach, reach)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemUsesExtendedStyleOption)

    def boundingRect(self) -> QRectF:  # noqa: N802 (Qt override)
        """Return the copper's extent grown by one extent on every side."""
        return self._bounds

    def _stroke(
        self, painter: QPainter, colour: QColor, grow_mm: float, seen: QRectF, from_width_mm: float = 0.0
    ) -> None:
        """Stroke every trace of at least ``from_width_mm``, at its width plus ``grow_mm``, that reaches ``seen``."""
        painter.setBrush(Qt.BrushStyle.NoBrush)
        pens: dict[float, QPen] = {}
        for part in self._strokes.parts:
            reach = (part.width_mm + grow_mm) / 2
            if part.width_mm < from_width_mm or not part.box.adjusted(-reach, -reach, reach, reach).intersects(seen):
                continue
            if part.width_mm not in pens:
                pens[part.width_mm] = QPen(
                    colour,
                    part.width_mm + grow_mm,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                    Qt.PenJoinStyle.RoundJoin,
                )
            painter.setPen(pens[part.width_mm])
            painter.drawPath(part.centre)


class CasingItem(_StrokedItem):
    """A band of ``colour`` CASING_PX wide around a layer's copper, over the layers already drawn."""

    def __init__(self, strokes: Strokes, colour: QColor) -> None:
        super().__init__(strokes)
        self._colour = colour

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None) -> None:
        """Stroke every trace CASING_PX wider on each side."""
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._stroke(painter, self._colour, 2 * CASING_PX / painter.worldTransform().m11(), option.exposedRect)
        painter.restore()


class OutlineItem(_StrokedItem):
    """Copper of one ink drawn as its edge only: OUTLINE_PX wide, inside the true edge, the inside left empty.

    The copper is stroked in its ink, then the inside of every trace wide enough to have one is stroked OUTLINE_PX
    narrower on each side in ``inside``, the board colour, at full opacity. The casing under the layer already hides
    the layers below, so the inside reads as empty; full opacity keeps it empty while the layer is dimmed. A trace
    narrower than SOLID_BELOW_PX has no inside and stays solid.
    """

    def __init__(self, strokes: Strokes, ink: QColor, inside: QColor) -> None:
        super().__init__(strokes)
        self._ink, self._inside = ink, inside

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None) -> None:
        """Paint the copper, then the inside of the traces wide enough to have one."""
        scale = painter.worldTransform().m11()
        hollow_from_mm = SOLID_BELOW_PX / scale
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._stroke(painter, self._ink, 0.0, option.exposedRect)
        painter.setOpacity(1.0)
        self._stroke(painter, self._inside, -2 * OUTLINE_PX / scale, option.exposedRect, from_width_mm=hollow_from_mm)
        painter.restore()
