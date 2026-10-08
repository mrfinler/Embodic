"""The canonical wave track at slot angle 0 (engine.js l.1568-1626, ``waveTrack``): inner via to outer via.

``outer_sweep`` replaces the +tau/2 sweep at the outer end for the commutation tracks that start one slot earlier.
"""

import math
from dataclasses import dataclass

from embodic.generators.wave.derive import WaveFrame
from embodic.generators.wave.fillet import fillet_path, taper_junctions
from embodic.generators.wave.involute import bisect, invol, involute_point, involute_prims
from embodic.generators.wave.xprim import XArc, XLine, XPrim, acos, polar

MIN_TURN_RAD = 0.04


@dataclass(frozen=True, slots=True, kw_only=True)
class _End:
    """One involute end of the track: its primitives and where the straight side starts or stops."""

    prims: list[XPrim]
    x_side: float


def wave_track(frame: WaveFrame, outer_sweep: float | None) -> list[XPrim]:
    """Xcoil waveTrack for the style of ``frame``."""
    p = frame.p
    sweep = frame.tau / 2 if outer_sweep is None else outer_sweep
    via_in, via_out = polar(frame.r_vi, -frame.tau / 2), polar(frame.r_vo, sweep)
    if frame.style == "chord":
        return [XLine(x1=via_in[0], y1=via_in[1], x2=via_out[0], y2=via_out[1], w=frame.w, kind="side")]
    if frame.style == "jog":
        prims: list[XPrim] = [
            XLine(x1=via_in[0], y1=via_in[1], x2=p.r_in, y2=0.0, w=frame.w_in, kind="endturn"),
            XLine(x1=p.r_in, y1=0.0, x2=p.r_out, y2=0.0, w=frame.w, kind="side"),
            XLine(x1=p.r_out, y1=0.0, x2=via_out[0], y2=via_out[1], w=frame.w_out, kind="endturn"),
        ]
        if _rounded(frame):
            prims = fillet_path(prims, min(p.fillet_radius, (p.r_out - p.r_in) * 0.3), None)
        return _tapered(frame, prims)
    inner = _inner_end(frame)
    outer = _outer_end(frame, outer_sweep, sweep, inner.x_side)
    side = XLine(x1=inner.x_side, y1=0.0, x2=outer.x_side, y2=0.0, w=frame.w, kind="side")
    return _tapered(frame, [*inner.prims, side, *outer.prims])


def _rounded(frame: WaveFrame) -> bool:
    return frame.p.rounded and frame.p.fillet_radius > 1e-6


def _tapered(frame: WaveFrame, prims: list[XPrim]) -> list[XPrim]:
    if frame.w_out != frame.w or frame.w_in != frame.w:
        return taper_junctions(prims)
    return prims


def _inner_end(frame: WaveFrame) -> _End:
    """Inner involute from the via ring to the radial line; a right turn onto it takes a fillet below the x axis."""
    p, rho = frame.p, frame.p.fillet_radius
    assert frame.inner.rb is not None
    rb = frame.inner.rb
    t1 = math.tan(acos(min(1.0, rb / frame.r_vi)))
    t2 = math.tan(acos(rb / p.r_in))
    phi = -invol(math.atan(t2))
    x_start, t_end = p.r_in, t2
    fillet: XArc | None = None
    if _rounded(frame) and math.atan(t2) > MIN_TURN_RAD:

        def f(t: float) -> float:
            pt, a = involute_point(rb, phi, t), phi + t
            return (pt[1] - rho * math.cos(a)) + rho

        if f(t1) < 0 and f(t2) > 0:
            ts = bisect(f, t1, t2)
            pt = involute_point(rb, phi, ts)
            a = phi + ts
            c = (pt[0] + rho * math.sin(a), pt[1] - rho * math.cos(a))
            if c[0] < p.r_out - rho:
                t_end, x_start = ts, c[0]
                fillet = XArc(cx=c[0], cy=c[1], r=rho, a1=a + math.pi / 2, a2=math.pi / 2,
                              w=min(frame.w, frame.w_in), kind="fillet")  # fmt: skip
    prims = involute_prims(rb, phi, t1, t_end, frame.w_in, "endturn")
    return _End(prims=[*prims, fillet] if fillet else prims, x_side=x_start)


def _outer_base_radius(frame: WaveFrame, outer_sweep: float | None, sweep: float) -> float | None:
    """Return the outer involute base radius; a shorter commutation sweep needs a larger one (None: radial)."""
    assert frame.outer.rb is not None
    if outer_sweep is None:
        return frame.outer.rb
    r_out, r_vo = frame.p.r_out, frame.r_vo
    if sweep <= invol(acos(r_out / r_vo)) + 1e-9:
        return None
    return bisect(lambda rb: invol(acos(rb / r_vo)) - invol(acos(min(1.0, rb / r_out))) - sweep, frame.outer.rb, r_out)


def _outer_end(frame: WaveFrame, outer_sweep: float | None, sweep: float, x_inner: float) -> _End:
    """Outer involute from the radial line to the via ring; a left turn onto it takes a fillet above the x axis."""
    p, rho = frame.p, frame.p.fillet_radius
    rb = _outer_base_radius(frame, outer_sweep, sweep)
    if rb is None:  # nearly radial: a straight line to the via
        pv = polar(frame.r_vo, sweep)
        line = XLine(x1=p.r_out, y1=0.0, x2=pv[0], y2=pv[1], w=frame.w_out, kind="endturn")
        return _End(prims=[line], x_side=p.r_out)
    t1 = math.tan(acos(min(1.0, rb / p.r_out)))
    t2 = math.tan(acos(rb / frame.r_vo))
    phi = -invol(math.atan(t1))
    t_start, x_end = t1, p.r_out
    fillet: XArc | None = None
    if _rounded(frame) and math.atan(t1) > MIN_TURN_RAD:

        def f(t: float) -> float:
            pt, a = involute_point(rb, phi, t), phi + t
            return (pt[1] + rho * math.cos(a)) - rho

        if f(t1) < 0 and f(t2) > 0:
            ts = bisect(f, t1, t2)
            pt = involute_point(rb, phi, ts)
            a = phi + ts
            c = (pt[0] - rho * math.sin(a), pt[1] + rho * math.cos(a))
            if c[0] > x_inner + 0.2:
                t_start, x_end = ts, c[0]
                fillet = XArc(cx=c[0], cy=c[1], r=rho, a1=-math.pi / 2, a2=a - math.pi / 2,
                              w=min(frame.w, frame.w_out), kind="fillet")  # fmt: skip
    prims = involute_prims(rb, phi, t_start, t2, frame.w_out, "endturn")
    return _End(prims=[fillet, *prims] if fillet else prims, x_side=x_end)
