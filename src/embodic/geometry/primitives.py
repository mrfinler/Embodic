"""Copper and outline primitives and their length and end points (interfaces.md section 5, Xcoil engine.js l.530-533).

An arc stores its start angle and signed sweep; Xcoil stores start and end angles. The sweep is ``a2 - a1`` of the
Xcoil record, so every kernel that reads Xcoil's ``a2 - a1`` reads ``sweep_rad`` and computes the same value.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import TypeAlias


class PrimitiveRole(StrEnum):
    """What a primitive is part of; renderers and checks may treat roles differently, the geometry does not."""

    SIDE = "side"
    END_TURN = "end_turn"
    LEAD = "lead"
    FILLET = "fillet"
    TAPER = "taper"
    LEG = "leg"
    RING = "ring"
    STUB = "stub"
    BUS = "bus"
    LINK = "link"
    OUTLINE = "outline"


@dataclass(frozen=True, slots=True, kw_only=True)
class Line:
    """Straight copper or outline segment from (x1, y1) to (x2, y2), in current direction for copper."""

    x1_mm: float
    y1_mm: float
    x2_mm: float
    y2_mm: float
    width_mm: float  # 0 for outline geometry
    role: PrimitiveRole

    def start_point(self) -> tuple[float, float]:
        """Return the first end point (mm)."""
        return (self.x1_mm, self.y1_mm)

    def end_point(self) -> tuple[float, float]:
        """Return the last end point (mm)."""
        return (self.x2_mm, self.y2_mm)


@dataclass(frozen=True, slots=True, kw_only=True)
class Arc:
    """Circular arc from ``start_rad`` through the signed ``sweep_rad`` about (cx, cy)."""

    cx_mm: float
    cy_mm: float
    r_mm: float
    start_rad: float
    sweep_rad: float  # signed, positive = counter-clockwise, y up
    width_mm: float
    role: PrimitiveRole

    def point_at(self, angle_rad: float) -> tuple[float, float]:
        """Return the point of the arc's circle at ``angle_rad`` (mm)."""
        return (self.cx_mm + self.r_mm * math.cos(angle_rad), self.cy_mm + self.r_mm * math.sin(angle_rad))

    def start_point(self) -> tuple[float, float]:
        """Return the point at the start angle (Xcoil primStart, engine.js l.530)."""
        return self.point_at(self.start_rad)

    def mid_point(self) -> tuple[float, float]:
        """Return the point half way along the sweep."""
        return self.point_at(self.start_rad + self.sweep_rad / 2)

    def end_point(self) -> tuple[float, float]:
        """Return the point at start + sweep (Xcoil primEnd, engine.js l.531)."""
        return self.point_at(self.start_rad + self.sweep_rad)


Primitive: TypeAlias = Line | Arc


def hypot_mm(dx: float, dy: float) -> float:
    """Xcoil's own hypot (engine.js l.77); math.hypot differs from it by 1 ulp in 8.8 % of cases (port notes 2.1)."""
    return math.sqrt(dx * dx + dy * dy)


def primitive_length_mm(p: Primitive) -> float:
    """Xcoil primLength (engine.js l.532)."""
    if isinstance(p, Line):
        return hypot_mm(p.x2_mm - p.x1_mm, p.y2_mm - p.y1_mm)
    return abs(p.sweep_rad) * p.r_mm


def path_length_mm(prims: Sequence[Primitive]) -> float:
    """Xcoil primsLength (engine.js l.533): a left-to-right sum, so the last bit matches Xcoil."""
    total_mm = 0.0
    for p in prims:
        total_mm += primitive_length_mm(p)
    return total_mm
