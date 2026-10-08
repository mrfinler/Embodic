"""Wave end-turn derivation (engine.js l.1482-1566, ``deriveWave``): slot angles, base radii and via rings per style.

``WaveParams`` carries the inputs under Xcoil's meaning (millimetres, radians). ``derive_wave`` returns the frame the
builders read, or the refusals Xcoil reports as errors.
"""

import math
from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Literal

from embodic.generators.wave.involute import (
    bisect,
    invol,
    point_segment_distance,
    segment_segment_distance,
)
from embodic.generators.wave.xprim import XLine, acos, polar
from embodic.geometry.primitives import hypot_mm

WaveStyleName = Literal["involute", "jog", "chord", "overlap"]
RefusalCode = Literal["WAVE_MIN_POLES", "WAVE_SLOT_PITCH", "WAVE_OUTER_TIGHT", "WAVE_INNER_TIGHT"]
MAX_TURNS_SEARCH = 60


@dataclass(frozen=True, slots=True, kw_only=True)
class WaveParams:
    """The inputs of Xcoil's wave builders. A zero end width means the trace width, as in Xcoil."""

    poles: int
    phases: int
    turns: int
    r_in: float
    r_out: float
    trace_width_mm: float
    clearance_mm: float
    end_width_outer_mm: float = 0.0
    end_width_inner_mm: float = 0.0
    via_pad: float
    via_drill_mm: float
    start_angle_deg: float = 0.0
    wave_layers: int = 2
    wave_style: WaveStyleName = "involute"
    rounded: bool = True  # cornerStyle 'round'
    fillet_radius_mm: float = 0.4
    bus_width_mm: float = 1.0


@dataclass(frozen=True, slots=True, kw_only=True)
class WaveRefusal:
    """An Xcoil derivation error: its code and the input field it blames (``turns``, ``endWidthOuter``, ``poles``)."""

    code: RefusalCode
    field: str


@dataclass(frozen=True, slots=True, kw_only=True)
class EndGeometry:
    """One end of the tracks: via ring radius, track spacing, the spacing required and the end-turn width."""

    rv: float
    spacing_mm: float
    need: float
    w_end: float
    rb: float | None = None  # base radius of the involute end-turn; None for the other styles


@dataclass(frozen=True, slots=True, kw_only=True)
class WaveFrame:
    """Xcoil's ``W``: everything the builders derive from the inputs."""

    p: WaveParams
    pp: int
    tau: float
    m: int
    q: int
    mq: int
    d_theta: float
    n_slots: int
    w: float
    s: float
    pad: float
    w_out: float
    w_in: float
    theta0: float
    layers: int
    style: WaveStyleName
    outer: EndGeometry
    inner: EndGeometry
    r_vo: float
    r_vi: float
    r_track_min: float | None = None  # chord only
    pitch_out_mm: float = 0.0  # overlap only
    pitch_in_mm: float = 0.0

    def rho_out(self, level: int) -> float:
        """Xcoil W.rhoOut: radius of the outer end-turn arc at nesting ``level`` (overlap)."""
        return self.p.r_out + self.w / 2 + self.s + self.w_out / 2 + level * self.pitch_out_mm

    def rho_in(self, level: int) -> float:
        """Xcoil W.rhoIn: radius of the inner end-turn arc at nesting ``level`` (overlap)."""
        return self.p.r_in - self.w / 2 - self.s - self.w_in / 2 - level * self.pitch_in_mm

    def belt_phase(self, beta: int) -> int:
        """Xcoil beltPhase: the phase of belt ``beta`` (belts repeat every 2m)."""
        b = beta % (2 * self.m)
        if self.m == 3:
            return (0, 2, 1)[b % 3]
        return b % 2 if self.m == 2 else 0

    def belt_sign(self, beta: int) -> int:
        """Xcoil beltSign: +1 when the conductors of the belt carry positive phase current outward."""
        b = beta % (2 * self.m)
        phase = self.belt_phase(b)
        return 1 if b == (2 * phase if self.m == 3 else phase) else -1

    def slot_angle(self, k: int) -> float:
        """Xcoil slotAngle: the angle of slot ``k``, the belt of ``q`` slots centred on ``theta0``."""
        return self.theta0 + (k - (self.q - 1) / 2) * self.d_theta


def _outer_residual(rb: float, i0: float, tau: float) -> Callable[[float], float]:
    """Involute angle swept from the rim to radius r, less half a pole pitch."""
    return lambda r: invol(acos(rb / r)) - i0 - tau / 2


def _inner_residual(rb: float, i1: float, tau: float) -> Callable[[float], float]:
    """Involute angle swept inward from the rim to radius r, less half a pole pitch."""
    return lambda r: invol(acos(min(1.0, rb / r))) - (i1 - tau / 2)


def _solve_end(
    which: Literal["out", "in"], p: WaveParams, tau: float, d_theta: float, w_end: float, s: float, pad: float
) -> EndGeometry | None:
    r0 = p.r_out if which == "out" else p.r_in
    d = max(w_end + s, pad / 2 + w_end / 2 + s)
    need = d
    rb = rv = 0.0
    for _ in range(12):
        rb = d / d_theta
        if which == "out":
            rb = min(rb, r0)
            i0 = invol(acos(rb / r0))
            rv = bisect(_outer_residual(rb, i0, tau), r0, r0 * 60)
        else:
            if rb >= r0 * 0.999 or invol(acos(rb / r0)) < tau / 2:
                return None
            i1 = invol(acos(rb / r0))
            rv = bisect(_inner_residual(rb, i1, tau), rb, r0)
        chord = 2 * rv * math.sin(d_theta / 2)
        if chord >= pad + s - 1e-9:
            break
        d *= (pad + s) / chord * 1.01
    return EndGeometry(rb=rb, rv=rv, spacing_mm=rb * d_theta, need=need, w_end=w_end)


def _seg(a: tuple[float, float], b: tuple[float, float]) -> XLine:
    return XLine(x1=a[0], y1=a[1], x2=b[0], y2=b[1], w=0.0, kind="side")


@dataclass(frozen=True, slots=True, kw_only=True)
class _Gap:
    ok: bool
    spacing_mm: float


@dataclass(frozen=True, slots=True, kw_only=True)
class _Base:
    """Quantities every style derives from the inputs."""

    p: WaveParams
    pp: int
    tau: float
    mq: int
    d_theta: float
    w: float
    s: float
    pad: float
    w_out: float
    w_in: float

    def frame(self, outer: EndGeometry, inner: EndGeometry, **extra: float) -> WaveFrame:
        p = self.p
        return WaveFrame(
            p=p, pp=self.pp, tau=self.tau, m=p.phases, q=p.turns, mq=self.mq, d_theta=self.d_theta,
            n_slots=2 * self.pp * self.mq, w=self.w, s=self.s, pad=self.pad, w_out=self.w_out, w_in=self.w_in,
            theta0=p.start_angle_deg * math.pi / 180, layers=p.wave_layers, style=p.wave_style, outer=outer,
            inner=inner, r_vo=outer.rv, r_vi=inner.rv, **extra,
        )  # fmt: skip

    def gap_ok(self, r_a: float, a_a: float, r_b: float, a_b: float, w_end: float) -> _Gap:
        """Chord from (r_a, a_a) to (r_b, a_b): its distance to the rotated copy and to the neighbouring via centres."""
        dth, pad, s = self.d_theta, self.pad, self.s
        a, b = polar(r_a, a_a), polar(r_b, a_b)
        ac, bc, bm = polar(r_a, a_a + dth), polar(r_b, a_b + dth), polar(r_b, a_b - dth)
        seg = _seg(a, b)
        d_chord = segment_segment_distance(seg, _seg(ac, bc))
        d_via = min(point_segment_distance(bc[0], bc[1], seg), point_segment_distance(bm[0], bm[1], seg))
        via_chord = 2 * r_b * math.sin(dth / 2)
        ok = d_chord >= w_end + s - 1e-9 and d_via >= (pad + w_end) / 2 + s - 1e-9 and via_chord >= pad + s - 1e-9
        return _Gap(ok=ok, spacing_mm=d_chord)


def _refusal(code: RefusalCode, field: str) -> tuple[WaveRefusal, ...]:
    return (WaveRefusal(code=code, field=field),)


def _derive_chord(b: _Base) -> WaveFrame | tuple[WaveRefusal, ...]:
    p, alpha = b.p, b.tau / 2
    rvo, rvi = p.r_out + b.pad / 2, p.r_in - b.pad / 2
    g1, g2 = b.gap_ok(rvi, -alpha, rvo, alpha, b.w), b.gap_ok(rvo, alpha, rvi, -alpha, b.w)
    if not rvi > 0.5 or not g1.ok or not g2.ok:
        return _refusal("WAVE_SLOT_PITCH", "turns")
    outer = EndGeometry(rv=rvo, spacing_mm=g2.spacing_mm, need=b.w + b.s, w_end=b.w)
    inner = EndGeometry(rv=rvi, spacing_mm=g1.spacing_mm, need=b.w + b.s, w_end=b.w)
    # a chord that sweeps a wide angle dips inside the inner via ring: remember its innermost radius for the group links
    ca, cb = polar(rvi, -alpha), polar(rvo, alpha)
    cl = hypot_mm(cb[0] - ca[0], cb[1] - ca[1])
    foot = -(ca[0] * (cb[0] - ca[0]) + ca[1] * (cb[1] - ca[1])) / (cl * cl)
    track_min = abs(ca[0] * cb[1] - ca[1] * cb[0]) / cl if 0 < foot < 1 else rvi
    return b.frame(outer, inner, r_track_min=track_min)


def _jog_outer_via_radius(b: _Base) -> tuple[float, _Gap] | None:
    """Smallest outer via radius that keeps the pitch: bisection between the straight-edge limit and 60 rOut."""
    p, alpha = b.p, b.tau / 2
    lo, hi = p.r_out / math.cos(alpha) + 0.02, p.r_out * 60
    if not b.gap_ok(p.r_out, 0, hi, alpha, b.w_out).ok:
        return None
    rvo = lo
    if not b.gap_ok(p.r_out, 0, lo, alpha, b.w_out).ok:
        lo_n, hi_f = lo, hi
        for _ in range(60):
            mid = (lo_n + hi_f) / 2
            if b.gap_ok(p.r_out, 0, mid, alpha, b.w_out).ok:
                hi_f = mid
            else:
                lo_n = mid
        rvo = hi_f
    return rvo, b.gap_ok(p.r_out, 0, rvo, alpha, b.w_out)


def _jog_inner_via_radius(b: _Base) -> tuple[float, _Gap] | None:
    """Largest inner via radius that keeps the pitch: a downward scan, then bisection inside the first fitting step."""
    p, alpha = b.p, b.tau / 2
    top = p.r_in * math.cos(alpha) - 0.02
    prev = top
    for kk in range(1, 241):
        rc = top * (1 - kk / 240)
        if rc < 0.5:
            return None
        if b.gap_ok(p.r_in, 0, rc, -alpha, b.w_in).ok:
            lo_f, hi_n = rc, prev
            for _ in range(50):
                md = (lo_f + hi_n) / 2
                if b.gap_ok(p.r_in, 0, md, -alpha, b.w_in).ok:
                    lo_f = md
                else:
                    hi_n = md
            return lo_f, b.gap_ok(p.r_in, 0, lo_f, -alpha, b.w_in)
        prev = rc
    return None


def _derive_jog(b: _Base) -> WaveFrame | tuple[WaveRefusal, ...]:
    outer_via = _jog_outer_via_radius(b)
    if outer_via is None:
        return _refusal("WAVE_OUTER_TIGHT", "endWidthOuter")
    inner_via = _jog_inner_via_radius(b)
    if inner_via is None or not inner_via[1].ok:
        return _refusal("WAVE_INNER_TIGHT", "turns")
    (rvo, g_o), (rvi, g_i) = outer_via, inner_via
    outer = EndGeometry(rv=rvo, spacing_mm=g_o.spacing_mm, need=b.w_out + b.s, w_end=b.w_out)
    inner = EndGeometry(rv=rvi, spacing_mm=g_i.spacing_mm, need=b.w_in + b.s, w_end=b.w_in)
    return b.frame(outer, inner)


def _derive_overlap(b: _Base) -> WaveFrame | tuple[WaveRefusal, ...]:
    p, mq = b.p, b.mq
    pitch_out = max(b.w_out + b.s, (b.pad + b.w_out) / 2 + b.s)
    pitch_in = max(b.w_in + b.s, (b.pad + b.w_in) / 2 + b.s)
    r_vi = p.r_in - b.w / 2 - b.s - b.w_in / 2 - (mq - 1) * pitch_in
    deepest = r_vi - b.w_in / 2
    via_chord_in = 2 * r_vi * math.sin(b.d_theta / 2)
    if deepest < 0.5 or via_chord_in < max(b.pad, b.w) + b.s - 1e-9:
        return _refusal("WAVE_INNER_TIGHT", "turns")
    r_vo = p.r_out + b.w / 2 + b.s + b.w_out / 2 + (mq - 1) * pitch_out
    outer = EndGeometry(rv=r_vo, spacing_mm=pitch_out, need=pitch_out, w_end=b.w_out)
    inner = EndGeometry(rv=r_vi, spacing_mm=pitch_in, need=pitch_in, w_end=b.w_in)
    return b.frame(outer, inner, pitch_out_mm=pitch_out, pitch_in_mm=pitch_in)


def _derive_involute(b: _Base) -> WaveFrame | tuple[WaveRefusal, ...]:
    p = b.p
    outer = _solve_end("out", p, b.tau, b.d_theta, b.w_out, b.s, b.pad)
    inner = _solve_end("in", p, b.tau, b.d_theta, b.w_in, b.s, b.pad)
    if inner is None:
        return _refusal("WAVE_INNER_TIGHT", "turns")
    assert outer is not None
    if outer.spacing_mm < outer.need - 1e-9:
        return _refusal("WAVE_OUTER_TIGHT", "endWidthOuter")
    return b.frame(outer, inner)


_BY_STYLE = {"involute": _derive_involute, "jog": _derive_jog, "chord": _derive_chord, "overlap": _derive_overlap}


def derive_wave(p: WaveParams) -> WaveFrame | tuple[WaveRefusal, ...]:
    """Xcoil deriveWave: the frame of ``p``, or the refusals that stop the build."""
    pp = p.poles // 2
    tau = math.pi / pp
    mq = p.phases * p.turns
    d_theta = tau / mq
    refusals: list[WaveRefusal] = []
    if p.phases > 1 and pp < 2:
        refusals.append(WaveRefusal(code="WAVE_MIN_POLES", field="poles"))
    if 2 * p.r_in * math.sin(d_theta / 2) < p.trace_width_mm + p.clearance_mm - 1e-9:
        refusals.append(WaveRefusal(code="WAVE_SLOT_PITCH", field="turns"))
    if refusals:
        return tuple(refusals)
    base = _Base(
        p=p, pp=pp, tau=tau, mq=mq, d_theta=d_theta, w=p.trace_width_mm, s=p.clearance_mm, pad=p.via_pad,
        w_out=p.end_width_outer_mm if p.end_width_outer_mm > 0 else p.trace_width_mm,
        w_in=p.end_width_inner_mm if p.end_width_inner_mm > 0 else p.trace_width_mm,
    )  # fmt: skip
    return _BY_STYLE[p.wave_style](base)


def max_wave_turns(p: WaveParams) -> int:
    """Xcoil maxWaveTurns: the largest turn count (1 to 60) whose end-turns can be laid out, searched upward."""
    best = 0
    for q in range(1, MAX_TURNS_SEARCH + 1):
        if isinstance(derive_wave(replace(p, turns=q)), tuple):
            break
        best = q
    return best
