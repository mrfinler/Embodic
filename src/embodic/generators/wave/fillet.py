"""Fillets, tapers and tangent arcs on Xcoil primitive paths (engine.js l.229-262, l.1449-1460, l.1710-1770).

Line-by-line ports: GR-23 compares each function with Xcoil's on seeded inputs.
"""

import math
from collections.abc import Callable
from dataclasses import dataclass, replace

from embodic.generators.wave.xprim import (
    XArc,
    XLine,
    XPrim,
    prim_dir_at,
    prim_dir_end_angle,
    prim_dir_start_angle,
    prim_end,
    prim_length,
    prim_start,
    reverse_prims,
    trim_prim_end,
    trim_prim_start,
)
from embodic.geometry.primitives import hypot_mm

Vec = tuple[float, float]


def _div(a: float, b: float) -> float:
    """JavaScript division: a zero divisor gives an infinity or NaN."""
    if b != 0.0:
        return a / b
    if a == 0.0 or math.isnan(a):
        return math.nan
    return math.copysign(math.inf, a) * math.copysign(1.0, b)


def arc_from_tangent(a: Vec, ta: Vec, b: Vec, w: float, kind: str) -> XPrim:
    """Xcoil arcFromTangent: the arc from A with unit tangent TA to B, or a line when the three are collinear."""
    nx, ny = -ta[1], ta[0]
    dx, dy = b[0] - a[0], b[1] - a[1]
    den = 2 * (nx * dx + ny * dy)
    dd = dx * dx + dy * dy
    if abs(den) < 1e-12 * max(1.0, dd):
        return XLine(x1=a[0], y1=a[1], x2=b[0], y2=b[1], w=w, kind=kind)
    r = dd / den
    cx, cy = a[0] + r * nx, a[1] + r * ny
    a1, a2 = math.atan2(a[1] - cy, a[0] - cx), math.atan2(b[1] - cy, b[0] - cx)
    if r > 0:
        while a2 < a1:
            a2 += 2 * math.pi
    else:
        while a2 > a1:
            a2 -= 2 * math.pi
    return XArc(cx=cx, cy=cy, r=abs(r), a1=a1, a2=a2, w=w, kind=kind)


def fillet_line_arc(
    a: XPrim, b: XPrim, d_a: Vec, cr: float, rho: float, w_fil: float, p: Vec
) -> tuple[XPrim, float, float] | None:  # fmt: skip
    """Xcoil filletLineArc: fillet between an incoming line and an outgoing arc about the origin; (arc, ta, tb)."""
    assert isinstance(b, XArc)
    radius = b.r
    inside = (d_a[0] * p[0] + d_a[1] * p[1]) > 0
    r_c = radius - rho if inside else radius + rho
    if r_c <= 0:
        return None
    n = (-d_a[1], d_a[0]) if cr > 0 else (d_a[1], -d_a[0])
    px, py = p[0] + n[0] * rho, p[1] + n[1] * rho
    bq = px * d_a[0] + py * d_a[1]
    cq = px * px + py * py - r_c * r_c
    disc = bq * bq - cq
    if disc < 0:
        return None
    t = bq - math.sqrt(disc)
    if not t > 1e-9:
        t = bq + math.sqrt(disc)
    if not t > 1e-9 or t >= prim_length(a) - 1e-6:
        return None
    c = (px - d_a[0] * t, py - d_a[1] * t)
    start = (p[0] - d_a[0] * t, p[1] - d_a[1] * t)
    cl = hypot_mm(c[0], c[1])
    end = (c[0] / cl * radius, c[1] / cl * radius)
    ang_b, ang_p = math.atan2(end[1], end[0]), math.atan2(p[1], p[0])
    sweep_b = ang_b - ang_p
    while sweep_b > math.pi:
        sweep_b -= 2 * math.pi
    while sweep_b < -math.pi:
        sweep_b += 2 * math.pi
    tb = abs(sweep_b) * radius
    if tb >= prim_length(b) - 1e-6:
        return None
    return arc_from_tangent(start, d_a, end, w_fil, "fillet"), t, tb


def _corner_fillet(a: XPrim, b: XPrim, rc: float, w_fil: float | None) -> tuple[XPrim, float, float] | None:
    """Fillet (arc, trim of ``a``, trim of ``b``) at the corner where ``a`` ends and ``b`` starts, or None."""
    p, q = prim_end(a), prim_start(b)
    if not rc > 1e-6 or hypot_mm(p[0] - q[0], p[1] - q[1]) > 1e-6:
        return None
    d_a, d_b = prim_dir_at(a, True), prim_dir_at(b, False)
    cr = d_a[0] * d_b[1] - d_a[1] * d_b[0]
    turn = math.atan2(cr, d_a[0] * d_b[0] + d_a[1] * d_b[1])
    if abs(turn) < 0.03:
        return None
    wf = w_fil if w_fil is not None else min(a.w or 0.0, b.w or 0.0)
    if isinstance(a, XLine) and isinstance(b, XLine):
        tl = _div(rc, math.tan((math.pi - abs(turn)) / 2))
        if tl < prim_length(a) - 1e-6 and tl < prim_length(b) - 1e-6:
            start = (p[0] - d_a[0] * tl, p[1] - d_a[1] * tl)
            end = (p[0] + d_b[0] * tl, p[1] + d_b[1] * tl)
            return arc_from_tangent(start, d_a, end, wf, "fillet"), tl, tl
        return None
    if isinstance(a, XLine) and isinstance(b, XArc) and _about_origin(b):
        return fillet_line_arc(a, b, d_a, cr, rc, wf, p)
    if isinstance(a, XArc) and isinstance(b, XLine) and _about_origin(a):
        ra, rb = reverse_prims([b])[0], reverse_prims([a])[0]
        f2 = fillet_line_arc(ra, rb, prim_dir_at(ra, True), -cr, rc, wf, p)
        return None if f2 is None else (reverse_prims([f2[0]])[0], f2[2], f2[1])
    return None


def _about_origin(arc: XArc) -> bool:
    return abs(arc.cx) < 1e-9 and abs(arc.cy) < 1e-9


def fillet_path(
    prims: list[XPrim], rho: float | Callable[[int], float], w_fil: float | None
) -> list[XPrim]:  # fmt: skip
    """Xcoil filletPath: circular fillets at every corner of a path whose arcs are concentric with the origin.

    Corners whose neighbours are too short stay sharp. ``rho`` is a radius or a function of the corner index.
    """
    rho_of = rho if callable(rho) else (lambda _corner: rho)
    if (not callable(rho) and not rho > 1e-6) or len(prims) < 2:
        return prims
    out = list(prims)
    i, corner = 0, 0
    while i + 1 < len(out):
        fil = _corner_fillet(out[i], out[i + 1], rho_of(corner), w_fil)
        na = trim_prim_end(out[i], fil[1]) if fil else None
        nb = trim_prim_start(out[i + 1], fil[2]) if fil else None
        if fil is None or na is None or nb is None:
            i, corner = i + 1, corner + 1
            continue
        out[i : i + 2] = [na, fil[0], nb]
        i, corner = i + 2, corner + 1
    return out


@dataclass(frozen=True, slots=True, kw_only=True)
class _TaperContext:
    prims: list[XPrim]
    through_fillets: bool

    def corner_sin(self, i: int, direction: int) -> float:
        q = self.prims[i]
        j = i + direction
        n = self.prims[j] if 0 <= j < len(self.prims) else None
        while n is not None and n.kind == "fillet" and self.through_fillets:
            j += direction
            n = self.prims[j] if 0 <= j < len(self.prims) else None
        if n is None:
            return 1.0
        a = prim_dir_end_angle(q) if direction > 0 else prim_dir_start_angle(q)
        b = prim_dir_start_angle(n) if direction > 0 else prim_dir_end_angle(n)
        return max(0.3, abs(math.sin(a - b)))


def _split_head(q: XPrim, length_mm: float, w: float) -> tuple[XPrim, XPrim]:
    """First ``length_mm`` mm of ``q`` as a taper of width ``w``, then the rest."""
    total = prim_length(q)
    if isinstance(q, XLine):
        f = length_mm / total
        x, y = q.x1 + (q.x2 - q.x1) * f, q.y1 + (q.y2 - q.y1) * f
        return replace(q, x2=x, y2=y, w=w, kind="taper"), replace(q, x1=x, y1=y)
    da = (1 if q.a2 > q.a1 else -1) * length_mm / q.r
    mid = q.a1 + da
    return replace(q, a2=mid, w=w, kind="taper"), replace(q, a1=mid)


def taper_junctions(prims: list[XPrim], through_fillets: bool = False) -> list[XPrim]:
    """Xcoil taperJunctions: where a wide primitive meets a narrower one, its end stretch takes the narrow width."""
    ctx = _TaperContext(prims=prims, through_fillets=through_fillets)
    out: list[XPrim] = []
    for i, q in enumerate(prims):
        prev = prims[i - 1] if i > 0 else None
        nxt = prims[i + 1] if i + 1 < len(prims) else None
        parts: list[XPrim] = [q]
        if q.kind != "fillet":
            if prev is not None and (through_fillets or prev.kind != "fillet") and prev.w < q.w:
                d1 = (q.w - prev.w) / 2 / (ctx.corner_sin(i, -1) if through_fillets else 1) + 0.02
                if prim_length(q) > 2.5 * d1:
                    parts = list(_split_head(q, d1, prev.w))
            if nxt is not None and (through_fillets or nxt.kind != "fillet") and nxt.w < q.w:
                last = parts[-1]
                d2 = (q.w - nxt.w) / 2 / (ctx.corner_sin(i, 1) if through_fillets else 1) + 0.02
                if prim_length(last) > 2.5 * d2:
                    head, rest = _split_head(reverse_prims([last])[0], d2, nxt.w)
                    parts[-1] = reverse_prims([rest])[0]
                    parts.append(reverse_prims([head])[0])
        out.extend(parts)
    return out
