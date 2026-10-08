"""The canonical single-layer pattern of one phase and pair, built from via V to terminal T (Xcoil buildCanonical).

Port of engine.js l.411-507. Strand ``s`` runs from the start radius ``r_v`` (the centre via V) round all poles to the
terminal bus at ``r_bus``. Every layer of the stack is this pattern, rotated, mirrored or reversed.
"""

import math
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

from embodic.generators.serpentine.corners import (
    Corner,
    Point,
    distance,
    make_corner,
    rho_at,
    side_line,
    taper_junctions,
)
from embodic.generators.serpentine.fit import Fit, FitFailure, fit_status, min_straight, start_radius
from embodic.generators.serpentine.frame import Frame, far_r, near_r
from embodic.geometry.primitives import Arc, Line, Primitive, PrimitiveRole

START_CLEARANCE_MM = 0.1  # the start radius must stay this far inside the copper radii
MIN_BORE_ROOM_MM = 0.2  # inner-rim terminals: bus radius minus via pad must exceed this
SWEEP_TOLERANCE = -1e-9


class BuildFailure(StrEnum):
    """Why a canonical build, or the layout around it, returns no copper (the codes of Xcoil's errors)."""

    R_TOO_SMALL = "R_TOO_SMALL"
    ACUTE_CORNER = "ACUTE_CORNER"
    BUNDLE_TOO_WIDE = "BUNDLE_TOO_WIDE"
    GEOMETRY = "GEOMETRY"


_FIT_FAILURE = {
    FitFailure.R_TOO_SMALL: BuildFailure.R_TOO_SMALL,
    FitFailure.ACUTE_CORNER: BuildFailure.ACUTE_CORNER,
    FitFailure.BUNDLE_TOO_WIDE: BuildFailure.BUNDLE_TOO_WIDE,
}


@dataclass(frozen=True, slots=True, kw_only=True)
class CanonObject:
    """One conductor of the canonical pattern: a strand, the V bus or the T bus, in build order V to T."""

    kind: Literal["strand", "vbus", "tbus"]
    prims: tuple[Primitive, ...]
    strand: int | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class Junction:
    """Where a strand meets a bus: the point and the polar angle of the strand there."""

    xy: Point
    ang: float


@dataclass(frozen=True, slots=True, kw_only=True)
class ViaSite:
    """Xcoil ``padV`` and ``padT``. ``t_a1``, ``t_a2`` and ``bus_ang`` describe the T bus and are 0 for V."""

    r: float
    ang: float
    xy: Point
    t_a1: float = 0.0
    t_a2: float = 0.0


@dataclass(frozen=True, slots=True, kw_only=True)
class Canon:
    """Xcoil's canonical build result without errors."""

    objs: tuple[CanonObject, ...]
    rho0: float
    rho0_max: float
    min_main_sweep_rad: float
    bus_level: int
    r_bus: float
    r_v: float
    gap_v: float
    pad_v: ViaSite
    pad_t: ViaSite
    junction_v: tuple[Junction, ...]
    junction_t: tuple[Junction, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class CanonFailure:
    """Xcoil returned errors; ``reasons`` keeps their order."""

    reasons: tuple[BuildFailure, ...]
    rho0: float = 0.0
    rho0_max: float | None = None


def _polar(r: float, a: float) -> Point:
    return (r * math.cos(a), r * math.sin(a))


def _on_line(d: Frame, i_side: int, i: int, r: float) -> Junction | None:
    """Xcoil ``ptOnLine``: where the side line meets the circle of radius ``r``."""
    line = side_line(d, i_side, i)
    if abs(line.d) >= r:
        return None
    x = math.sqrt(r * r - line.d * line.d)
    cs, sn = math.cos(line.phi), math.sin(line.phi)
    return Junction(xy=(x * cs - line.d * sn, x * sn + line.d * cs), ang=line.phi + math.asin(line.d / r))


def _on_line_corner(j: Junction) -> Corner:
    return Corner(rho=0.0, p_l=j.xy, p_c=j.xy, ang_c=j.ang, ang_l=j.ang, x_l=0.0)


@dataclass(slots=True)
class _StrandBuild:
    prims: list[Primitive]
    v_junction: Junction | None = None
    t_junction: Junction | None = None
    min_sweep_rad: float = math.inf


@dataclass(frozen=True, slots=True, kw_only=True)
class _Pending:
    """The end-turn arc that waits for the next side's entry angle."""

    radius_mm: float
    start: float
    width_mm: float


def _side_corners(d: Frame, rho0: float, line_index: int, i: int, j: int) -> tuple[Corner | None, Corner | None]:
    """Entry and exit corner of one side that is neither the first nor the last of the strand."""
    poles = d.p.poles
    near_lv = i + d.j if j == poles - 1 else i
    far_lv = d.n - 1 - i
    line = side_line(d, line_index, i)
    if j % 2 == 0:
        entry = make_corner(line, near_r(d, near_lv), -1, d.type_near, rho_at(d, rho0, near_lv))
        exit_ = make_corner(line, far_r(d, far_lv), 1, d.type_far, rho_at(d, rho0, far_lv))
    else:
        entry = make_corner(line, far_r(d, far_lv), -1, d.type_far, rho_at(d, rho0, far_lv))
        exit_ = make_corner(line, near_r(d, near_lv), 1, d.type_near, rho_at(d, rho0, near_lv))
    return entry, exit_


def _fillet_arc(corner: Corner, a1: float, a2: float, width_mm: float) -> Arc:
    return Arc(
        cx_mm=corner.cf[0],
        cy_mm=corner.cf[1],
        r_mm=corner.rho,
        start_rad=a1,
        sweep_rad=a2 - a1,
        width_mm=width_mm,
        role=PrimitiveRole.FILLET,
    )


def _build_strand(d: Frame, s: int, rho0: float, r_v: float, r_bus: float) -> _StrandBuild | None:
    """One strand over all turns and sides; None when a corner does not close (Xcoil ``bad``)."""
    poles, out = d.p.poles, _StrandBuild(prims=[])
    pending: _Pending | None = None
    for k in range(d.nt):
        i = k * d.j + s
        for j in range(poles):
            ju = k * poles + j
            is_start, is_end = k == 0 and j == 0, k == d.nt - 1 and j == poles - 1
            even = j % 2 == 0
            entry, exit_ = _side_corners(d, rho0, ju, i, j)
            if is_start:
                junction = _on_line(d, ju, i, r_v)
                entry = None if junction is None else _on_line_corner(junction)
                out.v_junction = junction
            if is_end:
                junction = _on_line(d, ju, i, r_bus)
                exit_ = None if junction is None else _on_line_corner(junction)
                out.t_junction = junction
            if entry is None or exit_ is None:
                return None
            if pending is not None:
                out.min_sweep_rad = min(out.min_sweep_rad, entry.ang_c - pending.start)
                out.prims.append(
                    Arc(
                        cx_mm=0.0,
                        cy_mm=0.0,
                        r_mm=pending.radius_mm,
                        start_rad=pending.start,
                        sweep_rad=entry.ang_c - pending.start,
                        width_mm=pending.width_mm,
                        role=PrimitiveRole.END_TURN,
                    )
                )
                pending = None
            w_entry, w_exit = (d.w_near, d.w_far) if even else (d.w_far, d.w_near)
            if entry.rho > 0:
                out.prims.append(_fillet_arc(entry, entry.a_end, entry.a_start, d.w_fillet(w_entry)))
            out.prims.append(
                Line(
                    x1_mm=entry.p_l[0],
                    y1_mm=entry.p_l[1],
                    x2_mm=exit_.p_l[0],
                    y2_mm=exit_.p_l[1],
                    width_mm=d.w,
                    role=PrimitiveRole.SIDE,
                )
            )
            if exit_.rho > 0:
                out.prims.append(_fillet_arc(exit_, exit_.a_start, exit_.a_end, d.w_fillet(w_exit)))
            if not is_end:
                near_lv, far_lv = (i + d.j if j == poles - 1 else i), d.n - 1 - i
                pending = _Pending(
                    radius_mm=far_r(d, far_lv) if even else near_r(d, near_lv),
                    start=exit_.ang_c,
                    width_mm=w_exit,
                )
    return out


def _bus_arc(r: float, a1: float, a2: float, width_mm: float) -> Arc:
    return Arc(cx_mm=0.0, cy_mm=0.0, r_mm=r, start_rad=a1, sweep_rad=a2 - a1, width_mm=width_mm, role=PrimitiveRole.BUS)


def _precondition(d: Frame, fit: Fit, bus_level: int) -> CanonFailure | tuple[float, float]:
    """Check before any copper is built; return the start radius ``r_v`` and the bus radius when the checks pass."""
    assert fit.reason is None
    rho0, rho0_max = fit.rho0, fit.rho0_max
    r_bus = near_r(d, bus_level)
    if not d.outer and r_bus - d.p.via_pad <= MIN_BORE_ROOM_MM:
        return CanonFailure(reasons=(BuildFailure.R_TOO_SMALL,), rho0=rho0, rho0_max=rho0_max)
    r_v = start_radius(d, rho0)
    inside = r_v > d.p.r_in + START_CLEARANCE_MM and r_v < d.p.r_out - START_CLEARANCE_MM
    if not inside or min_straight(d, rho0) < 0:
        return CanonFailure(reasons=(BuildFailure.GEOMETRY,), rho0=rho0, rho0_max=rho0_max)
    return r_v, r_bus


def build_canonical(d: Frame, bus_level_extra: int = 0) -> Canon | CanonFailure:
    """Build the canonical pattern of phase 0, pair 0 in build order V to T (Xcoil ``buildCanonical``).

    ``bus_level_extra`` shifts the terminal bus outward by that many pitch levels.
    """
    fit = fit_status(d)
    if not fit.ok:
        assert fit.reason is not None
        return CanonFailure(reasons=(_FIT_FAILURE[fit.reason],), rho0_max=fit.rho0_max)
    bus_level = d.n + bus_level_extra
    checked = _precondition(d, fit, bus_level)
    if isinstance(checked, CanonFailure):
        return checked
    r_v, r_bus = checked
    rho0, rho0_max = fit.rho0, fit.rho0_max
    assert rho0_max is not None
    strands: list[_StrandBuild] = []
    for s in range(d.j):
        built = _build_strand(d, s, rho0, r_v, r_bus)
        if built is None:
            return CanonFailure(reasons=(BuildFailure.GEOMETRY,), rho0=rho0, rho0_max=rho0_max)
        strands.append(built)
    reasons: list[BuildFailure] = []
    min_main_sweep_rad = min(b.min_sweep_rad for b in strands)
    if min_main_sweep_rad < SWEEP_TOLERANCE:
        reasons.append(BuildFailure.BUNDLE_TOO_WIDE)
    tapered = d.w_near != d.w or d.w_far != d.w
    objs = [
        CanonObject(kind="strand", strand=s, prims=tuple(taper_junctions(b.prims) if tapered else b.prims))
        for s, b in enumerate(strands)
    ]
    junction_v = tuple(b.v_junction for b in strands if b.v_junction is not None)
    junction_t = tuple(b.t_junction for b in strands if b.t_junction is not None)
    a_v, a_j = d.theta_g, junction_v[d.j - 1].ang
    objs.append(CanonObject(kind="vbus", prims=(_bus_arc(r_v, a_v, a_j, d.w),)))
    if a_j - a_v <= 0:
        reasons.append(BuildFailure.BUNDLE_TOO_WIDE)
    t_a1, t_a2 = junction_t[d.j - 1].ang, junction_t[0].ang
    if d.j > 1:
        objs.append(CanonObject(kind="tbus", prims=(_bus_arc(r_bus, t_a1, t_a2, d.w_near),)))
    if reasons:
        return CanonFailure(reasons=tuple(reasons), rho0=rho0, rho0_max=rho0_max)
    a_t = (t_a1 + t_a2) / 2
    r_t = r_bus + d.sg * (d.p.via_pad - d.w_near) / 2
    g_a, g_b = _on_line(d, -1, 0, r_v), _on_line(d, 0, 0, r_v)
    gap_v = distance(g_a.xy, g_b.xy) if g_a is not None and g_b is not None and g_b.ang > g_a.ang else 0.0
    return Canon(
        objs=tuple(objs),
        rho0=rho0,
        rho0_max=rho0_max,
        min_main_sweep_rad=min_main_sweep_rad,
        bus_level=bus_level,
        r_bus=r_bus,
        r_v=r_v,
        gap_v=gap_v,
        pad_v=ViaSite(r=r_v, ang=a_v, xy=_polar(r_v, a_v)),
        pad_t=ViaSite(r=r_t, ang=a_t, xy=_polar(r_t, a_t), t_a1=t_a1, t_a2=t_a2),
        junction_v=junction_v,
        junction_t=junction_t,
    )
