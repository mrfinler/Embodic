"""Agent 4's own primitive records, written from interfaces.md section 5 and the board-dump format, not from embodic.

A via or round pad is a zero-length ``Line`` whose width is the pad diameter: its copper is then exactly the disc.
"""

import math
from dataclasses import dataclass

Point = tuple[float, float]


@dataclass(frozen=True, slots=True)
class Line:
    """Straight copper centreline from (x1, y1) to (x2, y2), in current direction."""

    x1: float
    y1: float
    x2: float
    y2: float
    width: float


@dataclass(frozen=True, slots=True)
class Arc:
    """Circular centreline; ``sweep`` is signed, positive counter-clockwise with y up (interfaces.md section 5)."""

    cx: float
    cy: float
    r: float
    start: float
    sweep: float
    width: float


Prim = Line | Arc


def start_point(p: Prim) -> Point:
    """Return the first point of the primitive in current direction."""
    if isinstance(p, Line):
        return (p.x1, p.y1)
    return (p.cx + p.r * math.cos(p.start), p.cy + p.r * math.sin(p.start))


def end_point(p: Prim) -> Point:
    """Return the last point of the primitive in current direction."""
    if isinstance(p, Line):
        return (p.x2, p.y2)
    end = p.start + p.sweep
    return (p.cx + p.r * math.cos(end), p.cy + p.r * math.sin(end))


def disc(x: float, y: float, diameter: float) -> Line:
    """Return a via or round pad as a zero-length line whose copper is the disc."""
    return Line(x, y, x, y, diameter)
