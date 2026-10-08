"""Involute end-turns as arc splines (engine.js l.1449-1480): the involute function, the biarc and the spline.

``involute_prims`` joins tangent-continuous biarcs along an involute of base radius ``rb``; the piece count doubles
until the deviation from the true curve is at most 0.5 um.
"""

import math
from collections.abc import Callable

from embodic.generators.wave.fillet import Vec, arc_from_tangent
from embodic.generators.wave.xprim import XArc, XLine, XPrim
from embodic.geometry.primitives import hypot_mm

MAX_DEVIATION_MM = 5e-4
MAX_PIECES = 128


class DegenerateBiarcError(ValueError):
    """No biarc joins the two points: they coincide, or the tangents agree and the chord is perpendicular to them."""


def invol(alpha: float) -> float:
    """Xcoil invol: the involute function tan(alpha) - alpha."""
    return math.tan(alpha) - alpha


def involute_point(rb: float, phi0: float, t: float) -> Vec:
    """Xcoil involutePoint: point of the involute of base radius ``rb``, rotated by ``phi0``, at parameter ``t``."""
    a = phi0 + t
    return rb * (math.cos(a) + t * math.sin(a)), rb * (math.sin(a) - t * math.cos(a))


def bisect(f: Callable[[float], float], lo: float, hi: float, n: int = 70) -> float:
    """Xcoil bisect: ``n`` halvings of [lo, hi] keeping the sign change of ``f``."""
    flo = f(lo)
    for _ in range(n):
        mid = (lo + hi) / 2
        fm = f(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def point_segment_distance(px: float, py: float, s: XLine) -> float:
    """Xcoil ptSegDist."""
    dx, dy = s.x2 - s.x1, s.y2 - s.y1
    length2 = dx * dx + dy * dy
    t = ((px - s.x1) * dx + (py - s.y1) * dy) / length2 if length2 > 0 else 0.0
    t = max(0.0, min(1.0, t))
    return hypot_mm(px - (s.x1 + t * dx), py - (s.y1 + t * dy))


def segment_segment_distance(a: XLine, b: XLine) -> float:
    """Xcoil segSegDist, with its absolute parallel test (the wave derivation decides on it)."""
    d1x, d1y, d2x, d2y = a.x2 - a.x1, a.y2 - a.y1, b.x2 - b.x1, b.y2 - b.y1
    den = d1x * d2y - d1y * d2x
    if abs(den) > 1e-15:
        ex, ey = b.x1 - a.x1, b.y1 - a.y1
        t = (ex * d2y - ey * d2x) / den
        u = (ex * d1y - ey * d1x) / den
        if 0 <= t <= 1 and 0 <= u <= 1:
            return 0.0
    return min(
        point_segment_distance(a.x1, a.y1, b),
        point_segment_distance(a.x2, a.y2, b),
        point_segment_distance(b.x1, b.y1, a),
        point_segment_distance(b.x2, b.y2, a),
    )


def biarc(p0: Vec, t0: Vec, p1: Vec, t1: Vec, w: float, kind: str) -> tuple[XPrim, XPrim]:
    """Xcoil biarc: two tangent-continuous arcs joining P0 (tangent T0) to P1 (tangent T1).

    Raises ``DegenerateBiarcError`` where Xcoil's formula divides by zero; ``generate_wave`` maps it to ``Unbuildable``.
    """
    vx, vy = p1[0] - p0[0], p1[1] - p0[1]
    tx, ty = t0[0] + t1[0], t0[1] + t1[1]
    vt, vv = vx * tx + vy * ty, vx * vx + vy * vy
    c = 2 * (1 - (t0[0] * t1[0] + t0[1] * t1[1]))
    if vv == 0 or (c <= 1e-12 and vt == 0):  # no joint to place, or a joint at infinity
        raise DegenerateBiarcError(f"no biarc from {p0} to {p1}")
    d = (-vt + math.sqrt(vt * vt + c * vv)) / c if c > 1e-12 else vv / (2 * vt)
    joint = ((p0[0] + d * t0[0] + p1[0] - d * t1[0]) / 2, (p0[1] + d * t0[1] + p1[1] - d * t1[1]) / 2)
    second = arc_from_tangent(p1, (-t1[0], -t1[1]), joint, w, kind)
    if isinstance(second, XLine):
        second = XLine(x1=joint[0], y1=joint[1], x2=p1[0], y2=p1[1], w=w, kind=kind)
    else:
        second = XArc(cx=second.cx, cy=second.cy, r=second.r, a1=second.a2, a2=second.a1, w=w, kind=kind)
    return arc_from_tangent(p0, t0, joint, w, kind), second


def _deviation(q: XPrim, pt: Vec) -> float:
    if isinstance(q, XLine):
        return point_segment_distance(pt[0], pt[1], q)
    return abs(hypot_mm(pt[0] - q.cx, pt[1] - q.cy) - q.r)


def involute_prims(rb: float, phi0: float, t1: float, t2: float, w: float, kind: str) -> list[XPrim]:
    """Xcoil involutePrims: arc spline along the involute between parameters ``t1 < t2``."""

    def tangent(t: float) -> Vec:
        return math.cos(phi0 + t), math.sin(phi0 + t)

    n = 2
    while True:
        prims: list[XPrim] = []
        worst = 0.0
        for i in range(n):  # uniform in t^2, so uniform in arc length
            ta = math.sqrt(t1 * t1 + (t2 * t2 - t1 * t1) * i / n)
            tb = math.sqrt(t1 * t1 + (t2 * t2 - t1 * t1) * (i + 1) / n)
            pa, pb = involute_point(rb, phi0, ta), involute_point(rb, phi0, tb)
            first, second = biarc(pa, tangent(ta), pb, tangent(tb), w, kind)
            for k in range(1, 4):
                pt = involute_point(rb, phi0, ta + (tb - ta) * k / 4)
                worst = max(worst, min(_deviation(first, pt), _deviation(second, pt)))
            prims += [first, second]
        if worst <= MAX_DEVIATION_MM or n >= MAX_PIECES:
            return prims
        n *= 2
