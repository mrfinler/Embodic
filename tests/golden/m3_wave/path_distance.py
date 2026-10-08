"""Sampled distance between two primitive chains (test_plan.md GR-20 criterion "sampled path distance").

The arc centre and radius of an arc spline are rebuilt from three nearly collinear points, so a one-ULP difference in
cos or sin (V8 against glibc differ in 3 to 18 percent of calls, measured) reaches 1e-11 mm in them while the curve
itself moves by 1e-13 mm. This measures the curve.
"""

import math
from collections.abc import Sequence

from embodic.geometry.primitives import Line, Primitive

SAMPLES = 9


def _sample(p: Primitive, n: int) -> list[tuple[float, float]]:
    if isinstance(p, Line):
        return [(p.x1_mm + (p.x2_mm - p.x1_mm) * i / n, p.y1_mm + (p.y2_mm - p.y1_mm) * i / n) for i in range(n + 1)]
    return [
        (p.cx_mm + p.r_mm * math.cos(p.start_rad + p.sweep_rad * i / n),
         p.cy_mm + p.r_mm * math.sin(p.start_rad + p.sweep_rad * i / n))
        for i in range(n + 1)
    ]  # fmt: skip


def _distance(pt: tuple[float, float], p: Primitive) -> float:
    if isinstance(p, Line):
        dx, dy = p.x2_mm - p.x1_mm, p.y2_mm - p.y1_mm
        length2 = dx * dx + dy * dy
        t = 0.0 if length2 == 0 else max(0.0, min(1.0, ((pt[0] - p.x1_mm) * dx + (pt[1] - p.y1_mm) * dy) / length2))
        return math.hypot(pt[0] - (p.x1_mm + t * dx), pt[1] - (p.y1_mm + t * dy))
    ang = math.atan2(pt[1] - p.cy_mm, pt[0] - p.cx_mm)
    turn = (ang - p.start_rad) * (1 if p.sweep_rad >= 0 else -1) % (2 * math.pi)
    if turn <= abs(p.sweep_rad):
        return abs(math.hypot(pt[0] - p.cx_mm, pt[1] - p.cy_mm) - p.r_mm)
    return min(math.dist(pt, p.start_point()), math.dist(pt, p.end_point()))


def _one_way(a: Sequence[Primitive], b: Sequence[Primitive]) -> float:
    return max(min(_distance(pt, q) for q in b) for p in a for pt in _sample(p, SAMPLES))


def chain_deviation_mm(a: Sequence[Primitive], b: Sequence[Primitive]) -> float:
    """Largest distance from a sampled point of one chain to the other chain, in both directions."""
    return max(_one_way(a, b), _one_way(b, a))
