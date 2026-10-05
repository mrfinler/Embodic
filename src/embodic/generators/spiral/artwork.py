"""Layer-X artwork of the canonical coil: terminal stub, turns and closing (spiral_generator_spec.md G4-G6)."""

import math
from dataclasses import dataclass

from embodic.generators.spiral.turns import Closing, CoilFrame, FullClosing, Point, left_side_tops
from embodic.geometry.primitives import Arc, Line, Primitive, PrimitiveRole


@dataclass(frozen=True, slots=True, kw_only=True)
class CoilArtwork:
    """Layer X of the canonical coil, from the entry terminal via to the centre via, in current direction."""

    primitives: tuple[Primitive, ...]
    terminal: Point  # entry terminal via centre, angle +a_V
    centre_via: Point


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


def terminal_point(frame: CoilFrame, start_corner: Point, bus_width_mm: float) -> Point:
    """G6 entry terminal: ring r_T = r_outer + s + pad/2 at a_V = min(start corner angle, the neighbour bound)."""
    s, pad = frame.clearance_mm, frame.via_pad_mm
    r_t = frame.r_outer_mm + s + pad / 2
    neighbour_rad = frame.half_angle_rad - math.asin(min(1.0, (max(pad, bus_width_mm) + s) / (2 * r_t)))
    a_v = min(_angle(start_corner), neighbour_rad)
    return (r_t * math.cos(a_v), r_t * math.sin(a_v))


def coil_artwork(frame: CoilFrame, closing: Closing, bus_width_mm: float) -> CoilArtwork:
    """Layer X: stub, the full turns of ``closing``, then its lead arc (full) or its half turn (half)."""
    w, w_out, w_in = frame.trace_width_mm, frame.end_width_outer_mm, frame.end_width_inner_mm
    terminal = terminal_point(frame, closing.start_corner, bus_width_mm)
    prims: list[Primitive] = [_line(terminal, closing.start_corner, w, PrimitiveRole.STUB)]
    for turn, top in zip(closing.turns, left_side_tops(closing), strict=True):
        prims += [
            _arc(turn.outer_radius_mm, turn.j, turn.b, w_out, PrimitiveRole.END_TURN),
            _line(turn.b, turn.c, w, PrimitiveRole.SIDE),
            _arc(turn.end_radius_mm, turn.c, turn.d, w_in, PrimitiveRole.END_TURN),
            _line(turn.d, top, w, PrimitiveRole.SIDE),
        ]
    if isinstance(closing, FullClosing):
        r_v = closing.eye.via_radius_mm
        prims.append(_arc(r_v, closing.lead_point, closing.centre_via, w, PrimitiveRole.LEAD))
    else:
        half = closing.half
        prims += [
            _arc(half.outer_radius_mm, half.j, half.b, w_out, PrimitiveRole.END_TURN),
            _line(half.b, half.via, w, PrimitiveRole.SIDE),
        ]
    return CoilArtwork(primitives=tuple(prims), terminal=terminal, centre_via=closing.centre_via)
