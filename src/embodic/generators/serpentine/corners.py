"""Side lines, corner fillets and width tapers of the serpentine build (Xcoil engine.js l.191-250).

A side line is a straight conductor in the frame of its pole side: frame angle ``phi`` and lateral offset ``d``. A
corner joins a side line to a concentric end-turn arc, with or without a tangent fillet.
"""

import math
from dataclasses import dataclass, replace

from embodic.generators.serpentine.frame import CornerType, Frame
from embodic.geometry.primitives import Arc, Line, Primitive, PrimitiveRole, hypot_mm, primitive_length_mm
from embodic.geometry.transforms import reverse_path
from embodic.model.winding_specs import CornerStyle, SideStyle

Point = tuple[float, float]


@dataclass(frozen=True, slots=True, kw_only=True)
class SideLine:
    """Xcoil ``sideLine`` result: frame angle and lateral offset."""

    phi: float
    d: float


@dataclass(frozen=True, slots=True, kw_only=True)
class Corner:
    """Xcoil ``makeCorner`` result. ``cf``, ``a_start`` and ``a_end`` exist only for a filleted corner (rho > 0)."""

    rho: float
    p_l: Point
    p_c: Point
    ang_c: float
    ang_l: float
    x_l: float
    cf: Point = (0.0, 0.0)
    a_start: float = 0.0
    a_end: float = 0.0


def side_line(d: Frame, ju: int, i: int) -> SideLine:
    """Side line for the unwrapped side index ``ju`` and trace index ``i`` (Xcoil ``sideLine``)."""
    sgn = 1 if ju % 2 == 0 else -1
    c = i - (d.n - 1) / 2
    if d.p.style is SideStyle.RADIAL:
        return SideLine(phi=d.theta0 + ju * d.tau + sgn * c * d.d_alpha, d=0.0)
    return SideLine(phi=d.theta0 + ju * d.tau, d=sgn * c * d.pitch)


def make_corner(line: SideLine, r: float, u: int, kind: CornerType, rho: float) -> Corner | None:
    """Corner between a side line and a concentric arc of radius ``r`` (Xcoil ``makeCorner``).

    ``u`` is +1 when the arc continues toward +theta from the line and -1 toward -theta. ``kind`` INT puts the fillet
    inside the arc (the arc is the outer end), EXT outside it. None when the geometry does not close.
    """
    phi, d = line.phi, line.d
    cs, sn = math.cos(phi), math.sin(phi)

    def to_world(x: float, y: float) -> Point:
        return (x * cs - y * sn, x * sn + y * cs)

    if not rho > 1e-9:
        if abs(d) >= r:
            return None
        x = math.sqrt(r * r - d * d)
        ang = phi + math.asin(d / r)
        return Corner(rho=0.0, p_l=to_world(x, d), p_c=to_world(x, d), ang_c=ang, ang_l=ang, x_l=x)
    c = r - rho if kind is CornerType.INT else r + rho
    yc = d + u * rho
    if c <= 0 or abs(yc) >= c:
        return None
    xc = math.sqrt(c * c - yc * yc)
    k = r / c
    beta = math.atan2(yc, xc)
    a_start = phi - u * math.pi / 2
    if kind is CornerType.INT:
        a_end = phi + beta
    else:
        a_end = phi + (beta - math.pi if u > 0 else beta + math.pi)
    return Corner(
        rho=rho,
        p_l=to_world(xc, d),
        p_c=to_world(xc * k, yc * k),
        cf=to_world(xc, yc),
        a_start=a_start,
        a_end=a_end,
        ang_c=phi + beta,
        ang_l=phi + math.atan2(d, xc),
        x_l=xc,
    )


def rho_at(d: Frame, rho0: float, level: int) -> float:
    """Fillet radius at a nesting level: it grows by one pitch per level (Xcoil ``rhoAt``)."""
    return 0.0 if d.p.corner_style is CornerStyle.SHARP else rho0 + level * d.pitch


def _arc_end(q: Arc) -> float:
    return q.start_rad + q.sweep_rad


def _direction_sign(q: Arc) -> int:
    return 1 if q.sweep_rad >= 0 else -1


def start_direction(q: Primitive) -> float:
    """Direction of travel at the start of a primitive (Xcoil ``primDirStartAngle``)."""
    if isinstance(q, Line):
        return math.atan2(q.y2_mm - q.y1_mm, q.x2_mm - q.x1_mm)
    return q.start_rad + _direction_sign(q) * math.pi / 2


def end_direction(q: Primitive) -> float:
    """Direction of travel at the end of a primitive (Xcoil ``primDirEndAngle``)."""
    if isinstance(q, Line):
        return math.atan2(q.y2_mm - q.y1_mm, q.x2_mm - q.x1_mm)
    return _arc_end(q) + _direction_sign(q) * math.pi / 2


def _split_head(q: Primitive, length: float, width: float) -> tuple[Primitive, Primitive]:
    """First ``length`` mm of ``q`` at ``width`` (a taper) and the rest (Xcoil ``splitHead``)."""
    if isinstance(q, Line):
        f = length / primitive_length_mm(q)
        x = q.x1_mm + (q.x2_mm - q.x1_mm) * f
        y = q.y1_mm + (q.y2_mm - q.y1_mm) * f
        head = replace(q, x2_mm=x, y2_mm=y, width_mm=width, role=PrimitiveRole.TAPER)
        return head, replace(q, x1_mm=x, y1_mm=y)
    mid = q.start_rad + (1 if _arc_end(q) > q.start_rad else -1) * length / q.r_mm
    arc_head = replace(q, sweep_rad=mid - q.start_rad, width_mm=width, role=PrimitiveRole.TAPER)
    return arc_head, replace(q, start_rad=mid, sweep_rad=_arc_end(q) - mid)


def _reversed(q: Primitive) -> Primitive:
    return reverse_path([q])[0]


def _corner_sin(prims: list[Primitive], i: int, step: int, through_fillets: bool) -> float:
    """Sine of the corner angle next to ``prims[i]``, looking through fillets when asked (Xcoil ``cornerSin``)."""
    q, j = prims[i], i + step
    while 0 <= j < len(prims) and prims[j].role is PrimitiveRole.FILLET and through_fillets:
        j += step
    if not 0 <= j < len(prims):
        return 1.0
    n = prims[j]
    a, b = (end_direction(q), start_direction(n)) if step > 0 else (start_direction(q), end_direction(n))
    return max(0.3, abs(math.sin(a - b)))


def _neighbour_narrower(prims: list[Primitive], i: int, step: int, through_fillets: bool) -> bool:
    j = i + step
    if not 0 <= j < len(prims):
        return False
    other = prims[j]
    return (through_fillets or other.role is not PrimitiveRole.FILLET) and other.width_mm < prims[i].width_mm


def _taper_length(prims: list[Primitive], i: int, step: int, through_fillets: bool) -> float:
    q, other = prims[i], prims[i + step]
    return (q.width_mm - other.width_mm) / 2 / (
        _corner_sin(prims, i, step, through_fillets) if through_fillets else 1
    ) + 0.02


def taper_junctions(prims: list[Primitive], through_fillets: bool = False) -> list[Primitive]:
    """Where a wide primitive meets a narrower one, give its first and last half width step the narrow width.

    Port of Xcoil ``taperJunctions`` (engine.js l.212). The wide trace must end before its edge comes closer than the
    pitch to the neighbouring turn, so its round end cap cannot bulge into a neighbour.
    """
    out: list[Primitive] = []
    for i, q in enumerate(prims):
        parts = [q]
        if q.role is not PrimitiveRole.FILLET:
            if _neighbour_narrower(prims, i, -1, through_fillets):
                d1 = _taper_length(prims, i, -1, through_fillets)
                if primitive_length_mm(q) > 2.5 * d1:
                    parts = list(_split_head(q, d1, prims[i - 1].width_mm))
            if _neighbour_narrower(prims, i, 1, through_fillets):
                last = parts[-1]
                d2 = _taper_length(prims, i, 1, through_fillets)
                if primitive_length_mm(last) > 2.5 * d2:
                    head, rest = _split_head(_reversed(last), d2, prims[i + 1].width_mm)
                    parts[-1] = _reversed(rest)
                    parts.append(_reversed(head))
        out.extend(parts)
    return out


def distance(a: Point, b: Point) -> float:
    """Xcoil ``dist2``."""
    return hypot_mm(a[0] - b[0], a[1] - b[1])
