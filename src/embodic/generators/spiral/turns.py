"""Canonical coil frame, turn table and centre-via eye (spiral_generator_spec.md G1, G3 and G5).

Canonical coil: centred on the +x axis, half-angle h = pi/Q, left sector edge at +h, right edge at -h. A side line at
offset d lies d inside its sector edge.
"""

import math
from dataclasses import dataclass
from enum import StrEnum

from embodic.model.winding_specs import SpiralCoilSpec

Point = tuple[float, float]


@dataclass(frozen=True, slots=True, kw_only=True)
class CoilFrame:
    """G1 derived quantities of one coil; the coil gap is already max(gap, s)."""

    half_angle_rad: float
    trace_width_mm: float
    clearance_mm: float
    gap_mm: float
    end_width_outer_mm: float
    end_width_inner_mm: float
    r_outer_mm: float
    centre_outer_mm: float  # R_o0
    centre_inner_mm: float  # R_i0
    via_pad_mm: float
    min_side_mm: float

    @classmethod
    def of(cls, coil: SpiralCoilSpec, via_pad_mm: float) -> "CoilFrame":
        """Build the frame of ``coil``; ``min_side_length_mm`` None means 2w (spec Inputs, `assumption`)."""
        w = coil.trace_width_mm
        w_out = coil.end_width_outer_mm or w
        w_in = coil.end_width_inner_mm or w
        return cls(
            half_angle_rad=math.pi / coil.coil_count,
            trace_width_mm=w,
            clearance_mm=coil.clearance_mm,
            gap_mm=max(coil.coil_gap_mm, coil.clearance_mm),
            end_width_outer_mm=w_out,
            end_width_inner_mm=w_in,
            r_outer_mm=coil.r_outer_mm,
            centre_outer_mm=coil.r_outer_mm - w_out / 2,
            centre_inner_mm=coil.r_inner_mm + w_in / 2,
            via_pad_mm=via_pad_mm,
            min_side_mm=2 * w if coil.min_side_length_mm is None else coil.min_side_length_mm,
        )

    def offset_mm(self, t: int) -> float:
        """Side offset d_t = gap/2 + w/2 + t (w + s)."""
        return self.gap_mm / 2 + self.trace_width_mm / 2 + t * (self.trace_width_mm + self.clearance_mm)

    def outer_radius_mm(self, t: int) -> float:
        """Outer end radius R_out,t."""
        return self.centre_outer_mm - t * (self.end_width_outer_mm + self.clearance_mm)

    def inner_radius_mm(self, t: int) -> float:
        """Inner end radius R_in,t."""
        return self.centre_inner_mm + t * (self.end_width_inner_mm + self.clearance_mm)

    def on_right(self, d_mm: float, r_mm: float) -> Point:
        """Point of the right side line at offset ``d_mm`` and radius ``r_mm``."""
        h, lam = self.half_angle_rad, math.sqrt(r_mm * r_mm - d_mm * d_mm)
        return (lam * math.cos(h) + d_mm * math.sin(h), -lam * math.sin(h) + d_mm * math.cos(h))

    def on_left(self, d_mm: float, r_mm: float) -> Point:
        """Point of the left side line at offset ``d_mm`` and radius ``r_mm`` (mirror of ``on_right``)."""
        x, y = self.on_right(d_mm, r_mm)
        return (x, -y)

    def apex(self, d_right_mm: float, d_left_mm: float) -> Point:
        """Intersection of the right line at ``d_right_mm`` and the left line at ``d_left_mm``."""
        h = self.half_angle_rad
        x = (d_right_mm + d_left_mm) / (2 * math.sin(h))
        y = (d_right_mm - d_left_mm) / (2 * math.cos(h))
        return (x, y)


class TurnKind(StrEnum):
    """Shape of one spiral turn (G3)."""

    TRAPEZOID = "trapezoid"
    TRIANGLE = "triangle"


@dataclass(frozen=True, slots=True, kw_only=True)
class Turn:
    """Turn t of layer X: outer arc A to B, right side B to C, inner end C to E (C = E at an apex)."""

    index: int
    kind: TurnKind
    offset_mm: float  # d_t
    outer_radius_mm: float  # R_out,t
    end_radius_mm: float  # R_in,t, or the apex radius
    a: Point  # outer arc on the left line d_t
    b: Point  # outer arc on the right line d_t
    c: Point  # right side end
    e: Point  # turn end, on the left line d_t+1


def _angle(p: Point) -> float:
    return math.atan2(p[1], p[0])


def _turn(frame: CoilFrame, t: int) -> Turn | None:
    """Turn t when the outer arc exists and the inner end lies inside it (G3 rules 1 and 2), else None."""
    d, d_next = frame.offset_mm(t), frame.offset_mm(t + 1)
    r_out, r_in = frame.outer_radius_mm(t), frame.inner_radius_mm(t)
    if not d < r_out * math.sin(frame.half_angle_rad):
        return None
    a, b = frame.on_left(d, r_out), frame.on_right(d, r_out)
    if r_in > d_next and _angle(frame.on_left(d_next, r_in)) - _angle(frame.on_right(d, r_in)) > 0:
        c, e = frame.on_right(d, r_in), frame.on_left(d_next, r_in)
        kind, r_end = TurnKind.TRAPEZOID, r_in
    else:
        c = e = frame.apex(d, d_next)
        kind, r_end = TurnKind.TRIANGLE, math.hypot(*e)
    if not r_end < r_out:
        return None
    return Turn(index=t, kind=kind, offset_mm=d, outer_radius_mm=r_out, end_radius_mm=r_end, a=a, b=b, c=c, e=e)


class LoopStop(StrEnum):
    """The G3 rule that ended the turn sequence."""

    LATERAL = "lateral"  # rule 1, the outer arc vanishes between the side lines
    RADIAL = "radial"  # rules 2 to 4


def loop_turns(frame: CoilFrame) -> tuple[tuple[Turn, ...], LoopStop]:
    """Every turn the loop rule admits (G3), and the rule that stopped the sequence."""
    turns: list[Turn] = []
    while True:
        t = len(turns)
        turn = _turn(frame, t)
        if turn is None:
            outer_exists = frame.offset_mm(t) < frame.outer_radius_mm(t) * math.sin(frame.half_angle_rad)
            return tuple(turns), LoopStop.RADIAL if outer_exists else LoopStop.LATERAL
        if math.dist(turn.b, turn.c) < frame.min_side_mm:
            return tuple(turns), LoopStop.RADIAL
        if turns and not turn.outer_radius_mm > turns[-1].end_radius_mm:
            return tuple(turns), LoopStop.RADIAL
        turns.append(turn)


def radial_bound(frame: CoilFrame) -> float:
    """D08 eq. 3.24, N < (1/2)((R_o0 - R_i0)/w_d + 1); information only."""
    w_d = frame.trace_width_mm + frame.clearance_mm
    return 0.5 * ((frame.centre_outer_mm - frame.centre_inner_mm) / w_d + 1)


@dataclass(frozen=True, slots=True, kw_only=True)
class Eye:
    """Radial window for the centre via on the coil centre line (G5, one centre via)."""

    r_lo_mm: float
    r_hi_mm: float

    @property
    def fits(self) -> bool:
        """One via fits when the window is not empty."""
        return self.r_hi_mm >= self.r_lo_mm

    @property
    def via_radius_mm(self) -> float:
        """r_v, the middle of the window."""
        return (self.r_lo_mm + self.r_hi_mm) / 2


def eye(frame: CoilFrame, turns: tuple[Turn, ...], n: int) -> Eye:
    """Window of one centre via inside turn n - 1 (single pair, k = 1)."""
    last, s, w, pad = turns[n - 1], frame.clearance_mm, frame.trace_width_mm, frame.via_pad_mm
    side_lo = (frame.offset_mm(n - 1) + w / 2 + s + pad / 2) / math.sin(frame.half_angle_rad)
    inner_lo = last.end_radius_mm + frame.end_width_inner_mm / 2 + s + pad / 2
    r_lo = max(side_lo, inner_lo) if last.kind is TurnKind.TRAPEZOID else side_lo
    return Eye(r_lo_mm=r_lo, r_hi_mm=last.outer_radius_mm - frame.end_width_outer_mm / 2 - s - pad / 2)


def eye_limited_turns(frame: CoilFrame, turns: tuple[Turn, ...]) -> int:
    """Largest N whose eye fits (G5: reduce N until the via fits); 0 when none does."""
    return next((n for n in range(len(turns), 0, -1) if eye(frame, turns, n).fits), 0)
