"""Xcoil primitives and the path helpers the wave builders share (engine.js l.229-262, l.519-526, l.1449-1480).

Xcoil stores an arc as ``a1``/``a2`` (the sweep is ``a2 - a1``) and the builders do arithmetic on both angles. A
faithful port keeps that form until the layout is final, then ``to_primitive`` writes embodic's start and sweep, exactly
as the golden mapper reads Xcoil's records (tests/golden/m1_layout/xcoil_map.py).
"""

import math
from dataclasses import dataclass, replace
from typing import TypeAlias

from embodic.geometry.primitives import Arc, Line, Primitive, PrimitiveRole, hypot_mm

NAN = math.nan
TWO_PI = 2 * math.pi


@dataclass(frozen=True, slots=True, kw_only=True)
class XLine:
    """Xcoil ``{t: 'L'}``."""

    x1: float
    y1: float
    x2: float
    y2: float
    w: float
    kind: str


@dataclass(frozen=True, slots=True, kw_only=True)
class XArc:
    """Xcoil ``{t: 'A'}``: centre, radius and the two end angles."""

    cx: float
    cy: float
    r: float
    a1: float
    a2: float
    w: float
    kind: str


XPrim: TypeAlias = XLine | XArc

ROLE_BY_KIND: dict[str, PrimitiveRole] = {
    "side": PrimitiveRole.SIDE,
    "endturn": PrimitiveRole.END_TURN,
    "fillet": PrimitiveRole.FILLET,
    "taper": PrimitiveRole.TAPER,
    "leg": PrimitiveRole.LEG,
    "ring": PrimitiveRole.RING,
    "stub": PrimitiveRole.STUB,
    "bus": PrimitiveRole.BUS,
    "link": PrimitiveRole.LINK,
}


def acos(x: float) -> float:
    """``Math.acos``: NaN outside [-1, 1] instead of an exception."""
    return math.acos(x) if -1.0 <= x <= 1.0 else NAN


def js_mod(a: float, b: float) -> float:
    """JavaScript ``%`` on numbers: the result takes the sign of the dividend (C fmod)."""
    return math.fmod(a, b)


def ang_norm(a: float) -> float:
    """Xcoil angNorm (l.1221): the angle in [0, 2 pi)."""
    a = js_mod(a, TWO_PI)
    return a + TWO_PI if a < 0 else a


def polar(r: float, a: float) -> tuple[float, float]:
    """Xcoil polar (l.78)."""
    return r * math.cos(a), r * math.sin(a)


def to_primitive(q: XPrim) -> Primitive:
    """Xcoil record to embodic primitive; the sweep is ``a2 - a1``."""
    role = ROLE_BY_KIND[q.kind]
    if isinstance(q, XLine):
        return Line(x1_mm=q.x1, y1_mm=q.y1, x2_mm=q.x2, y2_mm=q.y2, width_mm=q.w, role=role)
    return Arc(cx_mm=q.cx, cy_mm=q.cy, r_mm=q.r, start_rad=q.a1, sweep_rad=q.a2 - q.a1, width_mm=q.w, role=role)


def prim_start(q: XPrim) -> tuple[float, float]:
    """Xcoil primStart."""
    if isinstance(q, XLine):
        return q.x1, q.y1
    return q.cx + q.r * math.cos(q.a1), q.cy + q.r * math.sin(q.a1)


def prim_end(q: XPrim) -> tuple[float, float]:
    """Xcoil primEnd."""
    if isinstance(q, XLine):
        return q.x2, q.y2
    return q.cx + q.r * math.cos(q.a2), q.cy + q.r * math.sin(q.a2)


def prim_length(q: XPrim) -> float:
    """Xcoil primLength."""
    if isinstance(q, XLine):
        return hypot_mm(q.x2 - q.x1, q.y2 - q.y1)
    return abs(q.a2 - q.a1) * q.r


def prims_length(prims: list[XPrim]) -> float:
    """Xcoil primsLength: a left-to-right sum."""
    total = 0.0
    for q in prims:
        total += prim_length(q)
    return total


def reverse_prims(prims: list[XPrim]) -> list[XPrim]:
    """Xcoil reversePrims: last to first, each primitive with its ends swapped."""
    out: list[XPrim] = []
    for q in reversed(prims):
        if isinstance(q, XLine):
            out.append(replace(q, x1=q.x2, y1=q.y2, x2=q.x1, y2=q.y1))
        else:
            out.append(replace(q, a1=q.a2, a2=q.a1))
    return out


def mirror_prims_x(prims: list[XPrim]) -> list[XPrim]:
    """Xcoil mirrorPrimsX (l.1469): y -> -y, so an arc sweeps the other way."""
    out: list[XPrim] = []
    for q in prims:
        if isinstance(q, XLine):
            out.append(replace(q, y1=-q.y1, y2=-q.y2))
        else:
            out.append(replace(q, cy=-q.cy, a1=-q.a1, a2=-q.a2))
    return out


def rotate_prims(prims: list[XPrim], ang: float) -> list[XPrim]:
    """Xcoil rotatePrims (l.1473)."""
    c, s = math.cos(ang), math.sin(ang)
    out: list[XPrim] = []
    for q in prims:
        if isinstance(q, XLine):
            out.append(replace(q, x1=q.x1 * c - q.y1 * s, y1=q.x1 * s + q.y1 * c, x2=q.x2 * c - q.y2 * s,
                               y2=q.x2 * s + q.y2 * c))  # fmt: skip
        else:
            out.append(replace(q, cx=q.cx * c - q.cy * s, cy=q.cx * s + q.cy * c, a1=q.a1 + ang, a2=q.a2 + ang))
    return out


def unit(x: float, y: float) -> tuple[float, float]:
    """Xcoil unit (l.1713): a zero vector divides by 1."""
    length = hypot_mm(x, y) or 1.0
    return x / length, y / length


def prim_dir_at(q: XPrim, at_end: bool) -> tuple[float, float]:
    """Xcoil primDirAt: unit tangent at the start or the end."""
    if isinstance(q, XLine):
        return unit(q.x2 - q.x1, q.y2 - q.y1)
    a = q.a2 if at_end else q.a1
    s = 1 if q.a2 >= q.a1 else -1
    return -math.sin(a) * s, math.cos(a) * s


def prim_dir_start_angle(q: XPrim) -> float:
    """Xcoil primDirStartAngle (l.228)."""
    if isinstance(q, XLine):
        return math.atan2(q.y2 - q.y1, q.x2 - q.x1)
    return q.a1 + (1 if q.a2 >= q.a1 else -1) * math.pi / 2


def prim_dir_end_angle(q: XPrim) -> float:
    """Xcoil primDirEndAngle (l.229)."""
    if isinstance(q, XLine):
        return math.atan2(q.y2 - q.y1, q.x2 - q.x1)
    return q.a2 + (1 if q.a2 >= q.a1 else -1) * math.pi / 2


def trim_prim_end(q: XPrim, length: float) -> XPrim | None:
    """Xcoil trimPrimEnd: shorten the end by ``length``; None when nothing remains."""
    total = prim_length(q)
    if length >= total - 1e-9:
        return None
    if isinstance(q, XLine):
        f = (total - length) / total
        return replace(q, x2=q.x1 + (q.x2 - q.x1) * f, y2=q.y1 + (q.y2 - q.y1) * f)
    return replace(q, a2=q.a1 + (q.a2 - q.a1) * (total - length) / total)


def trim_prim_start(q: XPrim, length: float) -> XPrim | None:
    """Xcoil trimPrimStart."""
    r = trim_prim_end(reverse_prims([q])[0], length)
    return reverse_prims([r])[0] if r else None
