"""Layer-X artwork of the canonical coil: terminal stub, turns and centre-via lead (spiral_generator_spec.md G4-G6)."""

import math
from dataclasses import dataclass

from embodic.generators.spiral.turns import CoilFrame, Point, Turn, TurnKind
from embodic.geometry.primitives import Arc, Line, Primitive, PrimitiveRole


@dataclass(frozen=True, slots=True, kw_only=True)
class CoilArtwork:
    """Layer X of the canonical coil, from the entry terminal via to the centre via, in current direction."""

    primitives: tuple[Primitive, ...]
    terminal: Point  # entry terminal via centre, angle +a_V
    centre_via: Point  # (r_v, 0)


def _angle(p: Point) -> float:
    return math.atan2(p[1], p[0])


def _line(a: Point, b: Point, width_mm: float, role: PrimitiveRole) -> Line:
    return Line(x1_mm=a[0], y1_mm=a[1], x2_mm=b[0], y2_mm=b[1], width_mm=width_mm, role=role)


def _arc(r_mm: float, start: Point, end: Point, width_mm: float, role: PrimitiveRole) -> Arc:
    start_rad = _angle(start)
    return Arc(
        cx_mm=0.0,
        cy_mm=0.0,
        r_mm=r_mm,
        start_rad=start_rad,
        sweep_rad=_angle(end) - start_rad,
        width_mm=width_mm,
        role=role,
    )


def terminal_point(frame: CoilFrame, first: Turn, bus_width_mm: float) -> Point:
    """G6 entry terminal: ring r_T = r_outer + s + pad/2 at a_V = min(start corner angle, the neighbour bound)."""
    s, pad = frame.clearance_mm, frame.via_pad_mm
    r_t = frame.r_outer_mm + s + pad / 2
    neighbour_rad = frame.half_angle_rad - math.asin(min(1.0, (max(pad, bus_width_mm) + s) / (2 * r_t)))
    a_v = min(_angle(first.a), neighbour_rad)
    return (r_t * math.cos(a_v), r_t * math.sin(a_v))


def coil_artwork(frame: CoilFrame, turns: tuple[Turn, ...], via_radius_mm: float, bus_width_mm: float) -> CoilArtwork:
    """Layer X for ``turns`` (the first N of the loop rule) with its centre via at ``via_radius_mm`` on the axis."""
    w, w_out, w_in = frame.trace_width_mm, frame.end_width_outer_mm, frame.end_width_inner_mm
    terminal = terminal_point(frame, turns[0], bus_width_mm)
    prims: list[Primitive] = [_line(terminal, turns[0].a, w, PrimitiveRole.STUB)]
    for turn, after in zip(turns, (*turns[1:], None), strict=True):
        prims.append(_arc(turn.outer_radius_mm, turn.a, turn.b, w_out, PrimitiveRole.END_TURN))
        prims.append(_line(turn.b, turn.c, w, PrimitiveRole.SIDE))
        if turn.kind is TurnKind.TRAPEZOID:
            prims.append(_arc(turn.end_radius_mm, turn.c, turn.e, w_in, PrimitiveRole.END_TURN))
        if after is not None:
            prims.append(_line(turn.e, after.a, w, PrimitiveRole.SIDE))
    lead_corner = frame.on_left(frame.offset_mm(len(turns)), via_radius_mm)
    centre_via = (via_radius_mm, 0.0)
    prims.append(_line(turns[-1].e, lead_corner, w, PrimitiveRole.LEAD))
    prims.append(_arc(via_radius_mm, lead_corner, centre_via, w, PrimitiveRole.LEAD))
    return CoilArtwork(primitives=tuple(prims), terminal=terminal, centre_via=centre_via)
