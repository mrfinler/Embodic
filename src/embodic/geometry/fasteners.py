"""Screw clearance holes of the fastener patterns and their keep-out gaps (REQ-F-24, interfaces.md sections 2.1, 5).

Hole j of a pattern sits on the pitch circle at angle_offset + 2 pi j / count with the diameter the user entered
(D-031a); `size` and `fit` only label it. Gaps are edge to edge: hole to board edge or cutout, hole to hole. Copper to
hole is the DRC's COPPER_HOLE check once the holes are on the outline.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from embodic.geometry.distance import point_segment_distance_mm
from embodic.geometry.layout import BoardOutline, Hole
from embodic.geometry.primitives import Arc, Primitive
from embodic.model.outline import ScrewFit


class HolePattern(Protocol):
    """The ScrewPattern fields a hole needs (interfaces.md section 2.1 with D-031a ``hole_diameter_mm``)."""

    @property
    def size(self) -> str:
        """Screw size label, e.g. "M3"."""

    @property
    def fit(self) -> ScrewFit:
        """Clearance fit label."""

    @property
    def count(self) -> int:
        """Holes on the pitch circle."""

    @property
    def pitch_radius_mm(self) -> float:
        """Pitch circle radius."""

    @property
    def hole_diameter_mm(self) -> float:
        """Drilled hole diameter the user entered."""

    @property
    def angle_offset_rad(self) -> float:
        """Angle of hole 0."""


@dataclass(frozen=True, slots=True, kw_only=True)
class PlacedHole:
    """A screw hole and the index of the pattern it came from (for issue pointers)."""

    pattern: int
    hole: Hole


def place_holes(patterns: Sequence[HolePattern]) -> tuple[PlacedHole, ...]:
    """Every hole of every pattern, pattern by pattern, hole 0 at the pattern's angle offset."""
    placed = []
    for k, pattern in enumerate(patterns):
        for j in range(pattern.count):
            a_rad = pattern.angle_offset_rad + 2 * math.pi * j / pattern.count
            hole = Hole(
                x_mm=pattern.pitch_radius_mm * math.cos(a_rad),
                y_mm=pattern.pitch_radius_mm * math.sin(a_rad),
                diameter_mm=pattern.hole_diameter_mm,
                label=f"{pattern.size} {pattern.fit.value}",
            )
            placed.append(PlacedHole(pattern=k, hole=hole))
    return tuple(placed)


def _point_arc_mm(x_mm: float, y_mm: float, arc: Arc) -> float:
    a_rad = math.atan2(y_mm - arc.cy_mm, x_mm - arc.cx_mm)
    along = (a_rad - arc.start_rad) % (2 * math.pi) if arc.sweep_rad >= 0 else (arc.start_rad - a_rad) % (2 * math.pi)
    if along <= abs(arc.sweep_rad):
        return abs(math.hypot(x_mm - arc.cx_mm, y_mm - arc.cy_mm) - arc.r_mm)
    return min(math.dist((x_mm, y_mm), arc.start_point()), math.dist((x_mm, y_mm), arc.end_point()))


def _point_primitive_mm(x_mm: float, y_mm: float, prim: Primitive) -> float:
    return _point_arc_mm(x_mm, y_mm, prim) if isinstance(prim, Arc) else point_segment_distance_mm(x_mm, y_mm, prim)


def _inside(x_mm: float, y_mm: float, loop: Sequence[Primitive]) -> bool:
    """Return whether the point lies inside a closed loop: a circle of arcs, or a polygon by ray casting."""
    if all(isinstance(p, Arc) for p in loop):
        circle = loop[0]
        assert isinstance(circle, Arc)
        return math.hypot(x_mm - circle.cx_mm, y_mm - circle.cy_mm) < circle.r_mm
    inside = False
    for p in loop:
        (x1, y1), (x2, y2) = p.start_point(), p.end_point()
        if (y1 > y_mm) != (y2 > y_mm) and x_mm < x1 + (y_mm - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def edge_gap_mm(hole: Hole, outline: BoardOutline) -> float:
    """Least distance from the hole's edge to the board edge or a cutout.

    Negative when the hole crosses one or its centre lies off the board (outside the edge or inside a cutout).
    """
    loops = (outline.outer, *outline.cutouts)
    centre_mm = min(_point_primitive_mm(hole.x_mm, hole.y_mm, p) for loop in loops for p in loop)
    on_board = _inside(hole.x_mm, hole.y_mm, outline.outer) and not any(
        _inside(hole.x_mm, hole.y_mm, cutout) for cutout in outline.cutouts
    )
    return (centre_mm if on_board else -centre_mm) - hole.diameter_mm / 2


def hole_gap_mm(a: Hole, b: Hole) -> float:
    """Board material between two holes, edge to edge (negative when they overlap)."""
    return math.hypot(a.x_mm - b.x_mm, a.y_mm - b.y_mm) - (a.diameter_mm + b.diameter_mm) / 2
