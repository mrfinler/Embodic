"""G9 concentric fillets of the canonical coil's corners (spiral_generator_spec.md G9).

Each corner kind forms one nested family: corner t of a family is corner t + 1 offset by one pitch, so all fillets of
a family share one centre. The innermost corner takes the set radius rho and each turn further out adds one pitch,
which keeps the copper gap between neighbouring fillets at exactly s.
"""

import math
from dataclasses import dataclass
from enum import StrEnum

from embodic.generators.spiral.turns import Closing, CoilFrame, FullClosing, Point, TurnKind
from embodic.geometry.primitives import Arc, PrimitiveRole
from embodic.model.winding_specs import EndStyle, SideStyle

# G9: shrink factor and retry count when a fillet does not fit.
SHRINK = 0.7
MAX_RETRIES = 12


class CornerKind(StrEnum):
    """The four corner families of a full turn (G3), named after the sharp corner they replace."""

    B = "outer_to_right"  # outer arc t into the right side t
    C = "right_to_inner"  # right side t into the inner end t (trapezoids only)
    D = "inner_to_left"  # inner end t into the left side t (trapezoids only)
    J = "left_to_outer"  # left side t into the outer arc t + 1 at its jog start J_t+1


@dataclass(frozen=True, slots=True, kw_only=True)
class Corner:
    """Junction of two primitives: the incoming one ends at ``end_in``, the outgoing one starts at ``start_out``."""

    end_in: Point
    start_out: Point
    fillet: Arc | None

    @classmethod
    def sharp(cls, vertex: Point) -> "Corner":
        """Unfilleted corner."""
        return cls(end_in=vertex, start_out=vertex, fillet=None)


def _angle(p: Point) -> float:
    return math.atan2(p[1], p[0])


def _fillet_arc(centre: Point, r_mm: float, start: Point, end: Point, width_mm: float) -> Arc:
    """Clockwise arc about ``centre``: every corner of layer X turns clockwise (G3)."""
    a0 = math.atan2(start[1] - centre[1], start[0] - centre[0])
    a1 = math.atan2(end[1] - centre[1], end[0] - centre[0])
    return Arc(
        cx_mm=centre[0], cy_mm=centre[1], r_mm=r_mm, start_rad=a0, sweep_rad=-((a0 - a1) % (2 * math.pi)),
        width_mm=width_mm, role=PrimitiveRole.FILLET,
    )  # fmt: skip


def _filleted(frame: CoilFrame, kind: CornerKind, t: int, r_mm: float) -> Corner | None:
    """Fillet of radius ``r_mm`` at corner ``kind`` of turn t, or None when no tangent circle exists.

    Built on the right line (B, C) or on the right line mirrored to the left (D, J): the centre lies on the line at
    offset d + r and at r_arc - r (outer end, inside the arc) or r_arc + r (inner end, outside the arc) from the origin.
    """
    h = frame.half_angle_rad
    d = frame.offset_mm(t)
    outer = kind in (CornerKind.B, CornerKind.J)
    r_arc = frame.outer_radius_mm(t + 1 if kind is CornerKind.J else t) if outer else frame.inner_radius_mm(t)
    centre_r = r_arc - r_mm if outer else r_arc + r_mm
    lam_sq = centre_r * centre_r - (d + r_mm) ** 2
    if centre_r <= 0 or lam_sq < 0:
        return None
    lam = math.sqrt(lam_sq)
    u, n = (math.cos(h), -math.sin(h)), (math.sin(h), math.cos(h))
    centre = (lam * u[0] + (d + r_mm) * n[0], lam * u[1] + (d + r_mm) * n[1])
    on_line = (lam * u[0] + d * n[0], lam * u[1] + d * n[1])
    on_arc = (centre[0] * r_arc / centre_r, centre[1] * r_arc / centre_r)
    if kind in (CornerKind.D, CornerKind.J):
        centre, on_line, on_arc = (centre[0], -centre[1]), (on_line[0], -on_line[1]), (on_arc[0], -on_arc[1])
    arc_first = kind in (CornerKind.B, CornerKind.D)
    start, end = (on_arc, on_line) if arc_first else (on_line, on_arc)
    return Corner(end_in=start, start_out=end, fillet=_fillet_arc(centre, r_mm, start, end, frame.trace_width_mm))


def _family(closing: Closing) -> dict[CornerKind, list[int]]:
    """Turn indices that own a corner of each kind; the last index of each list is the family's innermost corner."""
    full = [t.index for t in closing.turns]
    trapezoids = [t.index for t in closing.turns if t.kind is TurnKind.TRAPEZOID]
    # The last full turn of a full closing ends at L on the lead arc, a corner no other turn nests in.
    tops = full[:-1] if isinstance(closing, FullClosing) else full
    outer = full if isinstance(closing, FullClosing) else [*full, closing.half.index]
    return {CornerKind.B: outer, CornerKind.C: trapezoids, CornerKind.D: trapezoids, CornerKind.J: tops}


def corners(frame: CoilFrame, closing: Closing, rho_mm: float) -> dict[tuple[CornerKind, int], Corner] | None:
    """Fillets of every nested corner at ``rho_mm`` for the innermost one; None when one has no tangent circle."""
    out: dict[tuple[CornerKind, int], Corner] = {}
    pitch = frame.side_pitch_mm
    for kind, indices in _family(closing).items():
        for t in indices:
            corner = _filleted(frame, kind, t, rho_mm + (indices[-1] - t) * pitch)
            if corner is None:
                return None
            out[(kind, t)] = corner
    return out


def concentric_allowed(frame: CoilFrame) -> bool:
    """G9: concentric fillets keep s only when the end pitch equals the side pitch (w_out = w_in = w).

    Built for parallel sides and arc ends; radial sides are not parallel, so their corners do not nest by one pitch.
    """
    w = frame.trace_width_mm
    shape = frame.side_style is SideStyle.PARALLEL and frame.end_style is EndStyle.ARC
    return shape and frame.end_width_outer_mm == w and frame.end_width_inner_mm == w


def radius_sequence(rho_mm: float) -> tuple[float, ...]:
    """Return the set radius, then MAX_RETRIES shrinks by SHRINK."""
    return tuple(rho_mm * SHRINK**k for k in range(MAX_RETRIES + 1))


def ordered(start: Point, end: Point, direction: Point) -> bool:
    """Return whether ``end`` is not behind ``start`` along ``direction`` (a trimmed line keeps its direction)."""
    return (end[0] - start[0]) * direction[0] + (end[1] - start[1]) * direction[1] >= 0.0


def arc_ordered(start: Point, end: Point, clockwise: bool) -> bool:
    """Return whether a trimmed arc about the origin still runs the way it ran sharp."""
    sweep = _angle(end) - _angle(start)
    return sweep <= 0.0 if clockwise else sweep >= 0.0
