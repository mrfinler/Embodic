"""Layer-X artwork of the canonical coil: terminal stub, turns and closing (spiral_generator_spec.md G4-G6)."""

import math
from collections.abc import Mapping
from dataclasses import dataclass
from functools import partial

from embodic.generators.spiral.fillets import Corner, CornerKind, arc_ordered, ordered
from embodic.generators.spiral.turns import Closing, CoilFrame, FullClosing, Point, left_side_tops
from embodic.geometry.primitives import Arc, Line, Primitive, PrimitiveRole
from embodic.model.winding_specs import EndStyle


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


def _build(
    frame: CoilFrame, closing: Closing, bus_width_mm: float, filleted: Mapping[tuple[CornerKind, int], Corner]
) -> tuple[CoilArtwork, bool]:
    """Layer X and whether every primitive the fillets trimmed still runs the way it ran sharp."""
    w, w_out, w_in = frame.trace_width_mm, frame.end_width_outer_mm, frame.end_width_inner_mm
    terminal = terminal_point(frame, closing.start_corner, bus_width_mm)
    prims: list[Primitive] = [_line(terminal, closing.start_corner, w, PrimitiveRole.STUB)]
    fits = True

    def corner(kind: CornerKind, t: int, vertex: Point) -> Corner:
        return filleted.get((kind, t)) or Corner.sharp(vertex)

    def add_fillet(c: Corner) -> None:
        if c.fillet is not None:
            prims.append(c.fillet)

    straight = frame.end_style is EndStyle.STRAIGHT

    def arc(r_mm: float, start: Point, end: Point, sharp: tuple[Point, Point], width_mm: float) -> None:
        """End turn at level ``r_mm``: an arc about the origin, or a chord for straight ends (G2)."""
        nonlocal fits
        if straight:
            fits = fits and ordered(start, end, (sharp[1][0] - sharp[0][0], sharp[1][1] - sharp[0][1]))
            prims.append(_line(start, end, width_mm, PrimitiveRole.END_TURN))
            return
        clockwise = _angle(sharp[1]) <= _angle(sharp[0])
        fits = fits and arc_ordered(start, end, clockwise)
        prims.append(_arc(r_mm, start, end, width_mm, PrimitiveRole.END_TURN))

    def side(start: Point, end: Point, sharp: tuple[Point, Point]) -> None:
        nonlocal fits
        fits = fits and ordered(start, end, (sharp[1][0] - sharp[0][0], sharp[1][1] - sharp[0][1]))
        prims.append(_line(start, end, w, PrimitiveRole.SIDE))

    start = closing.start_corner
    for turn, top in zip(closing.turns, left_side_tops(closing), strict=True):
        t = turn.index
        b, c, d = corner(CornerKind.B, t, turn.b), corner(CornerKind.C, t, turn.c), corner(CornerKind.D, t, turn.d)
        j_next = corner(CornerKind.J, t, top)
        arc(turn.outer_radius_mm, start, b.end_in, (turn.j, turn.b), w_out)
        add_fillet(b)
        side(b.start_out, c.end_in, (turn.b, turn.c))
        add_fillet(c)
        arc(turn.end_radius_mm, c.start_out, d.end_in, (turn.c, turn.d), w_in)
        add_fillet(d)
        side(d.start_out, j_next.end_in, (turn.d, top))
        add_fillet(j_next)
        start = j_next.start_out
    if isinstance(closing, FullClosing):
        r_v = closing.eye.via_radius_mm
        lead = _line if straight else partial(_arc, r_v)
        prims.append(lead(closing.lead_point, closing.centre_via, w, PrimitiveRole.LEAD))
    else:
        half = closing.half
        b = corner(CornerKind.B, half.index, half.b)
        arc(half.outer_radius_mm, start, b.end_in, (half.j, half.b), w_out)
        add_fillet(b)
        side(b.start_out, half.via, (half.b, half.via))
    return CoilArtwork(primitives=tuple(prims), terminal=terminal, centre_via=closing.centre_via), fits


def sharp_artwork(frame: CoilFrame, closing: Closing, bus_width_mm: float) -> CoilArtwork:
    """Layer X with every corner sharp: stub, the full turns of ``closing``, then its lead arc or its half turn."""
    return _build(frame, closing, bus_width_mm, {})[0]


def coil_artwork(
    frame: CoilFrame, closing: Closing, bus_width_mm: float, filleted: Mapping[tuple[CornerKind, int], Corner]
) -> CoilArtwork | None:
    """Layer X with the corners of ``filleted`` rounded; None when a fillet trims a primitive past its other end."""
    art, fits = _build(frame, closing, bus_width_mm, filleted)
    return art if fits else None
