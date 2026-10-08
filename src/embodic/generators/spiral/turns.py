"""Canonical coil frame, turns and closing of one spiral coil (spiral_generator_spec.md G1, G3, G5; U-E3, U-E3b).

Canonical coil: centred on the +x axis, half-angle h = pi/Q, left sector edge at +h, right edge at -h. A side line at
offset d lies d inside its sector edge (parallel sides) or is the ray at h - asin(d/R_i0) (radial sides, G2). Both
sides of turn t lie on d_t; the pitch advance is the outer-end jog.

An end's level is where it crosses the coil centre line: the radius of an arc end, the x of a straight end. The loop
rule, the eye and the half closing compare levels on the centre line, so they hold for both end styles.
"""

import math
from dataclasses import dataclass
from enum import StrEnum

from embodic.geometry.details import TurnClosing
from embodic.model.winding_specs import EndStyle, SideStyle, SpiralCoilSpec

Point = tuple[float, float]

# The reference construction (checks/spiral_reference.py) decides its closing inequalities with this slack; the
# generator uses the same comparisons so both build the same turn count.
_FIT_SLACK_MM = 1e-9

# D-030 (assumption: no PCB coil approaches it). Bounds the turn scan, so every later step builds at most this many.
MAX_TURNS_PER_LAYER = 100


@dataclass(frozen=True, slots=True, kw_only=True)
class CoilFrame:
    """G1 derived quantities of one coil; the coil gap is already max(gap, s). Radii named here are end levels."""

    side_style: SideStyle
    end_style: EndStyle  # ARC or STRAIGHT; the stadium end has no jog construction yet
    half_angle_rad: float
    trace_width_mm: float
    clearance_mm: float
    gap_mm: float
    end_width_outer_mm: float
    end_width_inner_mm: float
    r_inner_mm: float
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
        h = math.pi / coil.coil_count
        # Straight ends (G2): the outermost chord at x = R_o0 cos h; the innermost touches R_i0 on the centre line, so
        # its middle keeps the r_inner rim (G9). Chords step by one end pitch in x, which keeps s between them.
        outer_scale = math.cos(h) if coil.end_style is EndStyle.STRAIGHT else 1.0
        return cls(
            side_style=coil.side_style,
            end_style=coil.end_style,
            half_angle_rad=h,
            trace_width_mm=w,
            clearance_mm=coil.clearance_mm,
            gap_mm=max(coil.coil_gap_mm, coil.clearance_mm),
            end_width_outer_mm=w_out,
            end_width_inner_mm=w_in,
            r_inner_mm=coil.r_inner_mm,
            r_outer_mm=coil.r_outer_mm,
            centre_outer_mm=(coil.r_outer_mm - w_out / 2) * outer_scale,
            centre_inner_mm=coil.r_inner_mm + w_in / 2,
            via_pad_mm=via_pad_mm,
            min_side_mm=2 * w if coil.min_side_length_mm is None else coil.min_side_length_mm,
        )

    @property
    def side_pitch_mm(self) -> float:
        """w_d = w + s."""
        return self.trace_width_mm + self.clearance_mm

    def offset_mm(self, t: int) -> float:
        """Side offset d_t = gap/2 + w/2 + t w_d."""
        return self.gap_mm / 2 + self.trace_width_mm / 2 + t * self.side_pitch_mm

    def outer_radius_mm(self, t: int) -> float:
        """Outer end radius R_out,t."""
        return self.centre_outer_mm - t * (self.end_width_outer_mm + self.clearance_mm)

    def inner_radius_mm(self, t: int) -> float:
        """Inner end radius R_in,t."""
        return self.centre_inner_mm + t * (self.end_width_inner_mm + self.clearance_mm)

    def apex_limit_radius_mm(self, d_mm: float) -> float:
        """rho_t: level where the two side lines at offset ``d_mm`` are w_d apart (G3); 0 for radial sides (G2)."""
        if self.side_style is SideStyle.RADIAL:
            return 0.0
        h, half = self.half_angle_rad, self.side_pitch_mm / 2
        x_c = (d_mm + half * math.cos(h)) / math.sin(h)
        return x_c if self.end_style is EndStyle.STRAIGHT else math.hypot(x_c, half)

    def ray_angle_rad(self, d_mm: float) -> float:
        """Angle below the coil axis of the radial right side at offset ``d_mm``: h - asin(d/R_i0) (G2)."""
        return self.half_angle_rad - math.asin(d_mm / self.centre_inner_mm)

    def on_right(self, d_mm: float, r_mm: float) -> Point:
        """Point of the right side line at offset ``d_mm`` on the end at level ``r_mm``."""
        h = self.half_angle_rad
        straight = self.end_style is EndStyle.STRAIGHT
        if self.side_style is SideStyle.RADIAL:
            a = self.ray_angle_rad(d_mm)
            return (r_mm, -r_mm * math.tan(a)) if straight else (r_mm * math.cos(a), -r_mm * math.sin(a))
        lam = (r_mm - d_mm * math.sin(h)) / math.cos(h) if straight else math.sqrt(r_mm * r_mm - d_mm * d_mm)
        return (lam * math.cos(h) + d_mm * math.sin(h), -lam * math.sin(h) + d_mm * math.cos(h))

    def on_left(self, d_mm: float, r_mm: float) -> Point:
        """Point of the left side line at offset ``d_mm`` and radius ``r_mm`` (mirror of ``on_right``)."""
        x, y = self.on_right(d_mm, r_mm)
        return (x, -y)

    def outer_arc_exists(self, t: int) -> bool:
        """G3 loop rule 1: the outer end of turn t lies between its side lines, d_t < R_out,t sin h (radial: R_i0)."""
        level = self.centre_inner_mm if self.side_style is SideStyle.RADIAL else self.outer_radius_mm(t)
        return self.offset_mm(t) < level * math.sin(self.half_angle_rad)

    def side_clearance_level_mm(self, d_mm: float, margin_mm: float) -> float:
        """Lowest level on the centre line at ``margin_mm`` from the side lines at offset ``d_mm`` (G5 r_lo)."""
        if self.side_style is SideStyle.RADIAL:
            return margin_mm / math.sin(self.ray_angle_rad(d_mm))
        return (d_mm + margin_mm) / math.sin(self.half_angle_rad)

    def jog_start(self, t: int) -> Point:
        """J_t: start of the outer arc of turn t; A_0 for t = 0, else on the left line d_t-1 at R_out,t."""
        return self.on_left(self.offset_mm(max(t - 1, 0)), self.outer_radius_mm(t))


class TurnKind(StrEnum):
    """Shape of one spiral turn (G3)."""

    TRAPEZOID = "trapezoid"
    TRIANGLE = "triangle"
    HALF = "half"


@dataclass(frozen=True, slots=True, kw_only=True)
class LoopTurn:
    """Full turn t of layer X: outer arc J to B (jog J to A), right side B to C, inner end C to D, left side up."""

    index: int
    kind: TurnKind  # TRAPEZOID or TRIANGLE
    offset_mm: float  # d_t
    outer_radius_mm: float  # R_out,t
    end_radius_mm: float  # r_end,t = max(R_in,t, rho_t)
    j: Point
    a: Point
    b: Point
    c: Point
    d: Point


@dataclass(frozen=True, slots=True, kw_only=True)
class HalfTurn:
    """Closing half turn t (G3, G5 half closing): outer arc J to B, then the right side d_t from B to the via P."""

    index: int
    offset_mm: float
    outer_radius_mm: float
    j: Point
    a: Point
    b: Point
    via: Point  # P = (d_t / sin h, 0)

    @property
    def kind(self) -> TurnKind:
        """Always HALF."""
        return TurnKind.HALF


def _angle(p: Point) -> float:
    return math.atan2(p[1], p[0])


def _loop_turn(frame: CoilFrame, t: int) -> LoopTurn | None:
    """Turn t when its outer arc exists and its inner end lies inside it, else None."""
    if not frame.outer_arc_exists(t):
        return None
    d, r_out, r_in = frame.offset_mm(t), frame.outer_radius_mm(t), frame.inner_radius_mm(t)
    rho = frame.apex_limit_radius_mm(d)
    kind, r_end = (TurnKind.TRAPEZOID, r_in) if r_in >= rho else (TurnKind.TRIANGLE, rho)
    if not r_end < r_out:
        return None
    return LoopTurn(
        index=t,
        kind=kind,
        offset_mm=d,
        outer_radius_mm=r_out,
        end_radius_mm=r_end,
        j=frame.jog_start(t),
        a=frame.on_left(d, r_out),
        b=frame.on_right(d, r_out),
        c=frame.on_right(d, r_end),
        d=frame.on_left(d, r_end),
    )


class LoopStop(StrEnum):
    """The G3 rule that ended the turn sequence."""

    LATERAL = "lateral"  # rule 1, the outer arc vanishes between the side lines
    RADIAL = "radial"  # rules 2 and 3
    CAP = "cap"  # the scan stopped at MAX_TURNS_PER_LAYER while the loop rule would admit more


def loop_turns(frame: CoilFrame) -> tuple[tuple[LoopTurn, ...], LoopStop]:
    """Every turn the loop rule admits (G3) up to MAX_TURNS_PER_LAYER, and the rule that stopped the sequence."""
    turns: list[LoopTurn] = []
    while True:
        t = len(turns)
        turn = _loop_turn(frame, t)
        if turn is None:
            return tuple(turns), LoopStop.RADIAL if frame.outer_arc_exists(t) else LoopStop.LATERAL
        if math.dist(turn.b, turn.c) < frame.min_side_mm or not turn.end_radius_mm < frame.outer_radius_mm(t + 1):
            return tuple(turns), LoopStop.RADIAL
        if t == MAX_TURNS_PER_LAYER:
            return tuple(turns), LoopStop.CAP
        turns.append(turn)


def radial_bound(frame: CoilFrame) -> float:
    """D08 eq. 3.24, N < (1/2)((R_o0 - R_i0)/w_d + 1); information only."""
    return 0.5 * ((frame.centre_outer_mm - frame.centre_inner_mm) / frame.side_pitch_mm + 1)


@dataclass(frozen=True, slots=True, kw_only=True)
class Eye:
    """Radial window for the centre vias and lead-arc ends on the coil centre line (G5 full closing).

    k series groups put k vias on the centre line from r_hi downward, one via pitch apart.
    """

    r_lo_mm: float
    r_hi_mm: float
    vias: int = 1
    via_pitch_mm: float = 0.0

    @property
    def fits(self) -> bool:
        """The k vias fit when the window holds k - 1 via pitches."""
        return self.r_hi_mm - self.r_lo_mm - (self.vias - 1) * self.via_pitch_mm >= -_FIT_SLACK_MM

    @property
    def via_radius_mm(self) -> float:
        """r_v = r_hi: the last left side is as long as the window allows."""
        return self.r_hi_mm

    def group_via_radius_mm(self, group: int) -> float:
        """r_v of series group ``group``: ``group`` via pitches below r_hi."""
        return self.r_hi_mm - group * self.via_pitch_mm


def eye(frame: CoilFrame, turns: tuple[LoopTurn, ...], n: int, vias: int = 1) -> Eye:
    """Window of ``vias`` centre vias inside turn n - 1; via pad and lead-arc end share V, so m = max(pad, w)/2."""
    last, s, w = turns[n - 1], frame.clearance_mm, frame.trace_width_mm
    m = max(frame.via_pad_mm, w) / 2
    side_lo = frame.side_clearance_level_mm(frame.offset_mm(n - 1), w / 2 + s + m)
    inner_lo = last.end_radius_mm + frame.end_width_inner_mm / 2 + s + m
    return Eye(
        r_lo_mm=max(side_lo, inner_lo),
        r_hi_mm=last.outer_radius_mm - frame.end_width_outer_mm / 2 - s - m,
        vias=vias,
        via_pitch_mm=m + frame.via_pad_mm / 2 + s,
    )


def half_turn(frame: CoilFrame, t: int) -> HalfTurn | None:
    """Return closing half turn t, or None when its outer arc does not exist or the sides never meet (radial)."""
    if frame.side_style is SideStyle.RADIAL or not frame.outer_arc_exists(t):
        return None
    d, r_out = frame.offset_mm(t), frame.outer_radius_mm(t)
    return HalfTurn(
        index=t,
        offset_mm=d,
        outer_radius_mm=r_out,
        j=frame.jog_start(t),
        a=frame.on_left(d, r_out),
        b=frame.on_right(d, r_out),
        via=(d / math.sin(frame.half_angle_rad), 0.0),
    )


def _half_closing_turn(frame: CoilFrame, turns: tuple[LoopTurn, ...], n: int) -> HalfTurn | None:
    """Return the closing half turn n - 1 when G5 half-closing conditions 1 to 6 hold for n turns, else None."""
    if not 1 <= n <= len(turns) + 1 or frame.via_pad_mm > frame.trace_width_mm:
        return None
    half = half_turn(frame, n - 1)
    if half is None:
        return None
    w, s, r_v = frame.trace_width_mm, frame.clearance_mm, half.via[0]
    below = turns[n - 2].end_radius_mm + frame.end_width_inner_mm / 2 + s if n >= 2 else frame.r_inner_mm
    fits = (
        math.dist(half.b, half.via) >= frame.min_side_mm
        and r_v - w / 2 >= below - _FIT_SLACK_MM
        and r_v + w / 2 + s <= half.outer_radius_mm - frame.end_width_outer_mm / 2 + _FIT_SLACK_MM
    )
    return half if fits else None


@dataclass(frozen=True, slots=True, kw_only=True)
class FullClosing:
    """N full turns; the last left side ends at L on the line d_N-1 at r_v, the lead arc runs from L to (r_v, 0)."""

    turns: tuple[LoopTurn, ...]
    eye: Eye
    lead_point: Point  # L

    @property
    def kind(self) -> TurnClosing:
        """Always FULL."""
        return TurnClosing.FULL

    @property
    def n(self) -> int:
        """Turns built."""
        return len(self.turns)

    @property
    def centre_via(self) -> Point:
        """V = (r_v, 0)."""
        return (self.eye.via_radius_mm, 0.0)

    @property
    def start_corner(self) -> Point:
        """A_0, where the stub joins the first outer arc."""
        return self.turns[0].a


@dataclass(frozen=True, slots=True, kw_only=True)
class HalfClosing:
    """N - 1 full turns and the closing half turn N - 1, whose right side lands on the via at P."""

    turns: tuple[LoopTurn, ...]
    half: HalfTurn

    @property
    def kind(self) -> TurnClosing:
        """Always HALF."""
        return TurnClosing.HALF

    @property
    def n(self) -> int:
        """Turns built, the half turn included."""
        return len(self.turns) + 1

    @property
    def centre_via(self) -> Point:
        """V = P."""
        return self.half.via

    @property
    def start_corner(self) -> Point:
        """A_0; the half turn's own corner when it is the only turn."""
        return self.turns[0].a if self.turns else self.half.a


Closing = FullClosing | HalfClosing


def closing_for(frame: CoilFrame, turns: tuple[LoopTurn, ...], n: int, vias: int = 1) -> Closing | None:
    """Close n turns: full when its eye fits (it keeps the last left side), else half, else None.

    k > 1 series groups keep the full closing: k vias cannot share the half closing's P (G5).
    """
    if 1 <= n <= len(turns) and (window := eye(frame, turns, n, vias)).fits:
        lead_point = frame.on_left(frame.offset_mm(n - 1), window.via_radius_mm)
        return FullClosing(turns=turns[:n], eye=window, lead_point=lead_point)
    if vias == 1 and (half := _half_closing_turn(frame, turns, n)):
        return HalfClosing(turns=turns[: n - 1], half=half)
    return None


def max_closing(frame: CoilFrame, turns: tuple[LoopTurn, ...], vias: int = 1) -> Closing | None:
    """Return the closing with the most turns (G5 choice); None when not even one turn closes."""
    closings = (closing_for(frame, turns, n, vias) for n in range(len(turns) + 1, 0, -1))
    return next((c for c in closings if c is not None), None)


def group_closing(frame: CoilFrame, closing: FullClosing, group: int) -> FullClosing:
    """Return the closing of series group ``group``: its last left side and lead arc end at its own via radius (G5)."""
    r_v = closing.eye.group_via_radius_mm(group)
    return FullClosing(
        turns=closing.turns,
        eye=Eye(r_lo_mm=closing.eye.r_lo_mm, r_hi_mm=r_v),
        lead_point=frame.on_left(frame.offset_mm(closing.n - 1), r_v),
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class TurnRow:
    """One row of the G4 turn table, lengths in mm; a half turn has no inner end or left side."""

    index: int
    kind: TurnKind
    offset_mm: float
    outer_radius_mm: float
    end_radius_mm: float  # r_end, or r_v for the half turn
    jog_mm: float
    outer_mm: float  # includes the jog
    right_mm: float
    inner_mm: float | None
    left_mm: float | None


def left_side_tops(closing: Closing) -> list[Point]:
    """Upper end of each full turn's left side: the next jog start J_t+1, then L (full) or the half turn's J (half)."""
    if not closing.turns:
        return []
    last = closing.lead_point if isinstance(closing, FullClosing) else closing.half.j
    return [t.j for t in closing.turns[1:]] + [last]


def turn_table(closing: Closing) -> tuple[TurnRow, ...]:
    """G4 per-turn record; the last left side ends at L (full) or at J of the half turn (half)."""
    rows = []
    tops = left_side_tops(closing)
    for turn, top in zip(closing.turns, tops, strict=True):
        rows.append(
            TurnRow(
                index=turn.index,
                kind=turn.kind,
                offset_mm=turn.offset_mm,
                outer_radius_mm=turn.outer_radius_mm,
                end_radius_mm=turn.end_radius_mm,
                jog_mm=turn.outer_radius_mm * (_angle(turn.j) - _angle(turn.a)),
                outer_mm=turn.outer_radius_mm * (_angle(turn.j) - _angle(turn.b)),
                right_mm=math.dist(turn.b, turn.c),
                inner_mm=turn.end_radius_mm * (_angle(turn.d) - _angle(turn.c)),
                left_mm=math.dist(turn.d, top),
            )
        )
    if isinstance(closing, HalfClosing):
        half = closing.half
        rows.append(
            TurnRow(
                index=half.index,
                kind=TurnKind.HALF,
                offset_mm=half.offset_mm,
                outer_radius_mm=half.outer_radius_mm,
                end_radius_mm=half.via[0],
                jog_mm=half.outer_radius_mm * (_angle(half.j) - _angle(half.a)),
                outer_mm=half.outer_radius_mm * (_angle(half.j) - _angle(half.b)),
                right_mm=math.dist(half.b, half.via),
                inner_mm=None,
                left_mm=None,
            )
        )
    return tuple(rows)
