"""Does the winding fit between the radii? Fillet limits and the bundle checks (Xcoil engine.js l.252-405).

``fit_status`` is Xcoil ``fitStatus``: it decides whether the bundle of traces fits between neighbouring sides and
which level-0 fillet radius the build uses.
"""

import math
from dataclasses import dataclass, replace
from enum import StrEnum

from embodic.generators.serpentine.corners import Corner, Point, distance, make_corner, rho_at, side_line
from embodic.generators.serpentine.frame import CornerType, Frame, Params, derive, far_r, near_r
from embodic.model.winding_specs import CornerStyle, SideStyle

MIN_STRAIGHT_MM = 0.05  # straight active conductor that must remain between the two corner fillets
FIT_TOLERANCE = 1e-9
MAX_TRACES_SEARCH = 400


class FitFailure(StrEnum):
    """Reasons ``fit_status`` refuses a winding (the codes of Xcoil's errors)."""

    R_TOO_SMALL = "R_TOO_SMALL"
    ACUTE_CORNER = "ACUTE_CORNER"
    BUNDLE_TOO_WIDE = "BUNDLE_TOO_WIDE"


@dataclass(frozen=True, slots=True, kw_only=True)
class Fit:
    """Xcoil ``fitStatus`` result; ``reason`` is None when the winding fits."""

    ok: bool
    reason: FitFailure | None
    rho0: float = 0.0
    rho0_max: float | None = None
    leg_gap: float = 0.0
    back_gap: float = 0.0
    end_gap: float = math.inf


def _sweep_between(line_a: Corner | None, line_b: Corner | None) -> float:
    if line_a is None or line_b is None:
        return -1.0
    return line_b.ang_c - line_a.ang_c


def min_sweep(d: Frame, rho0: float) -> float:
    """Smallest main-arc sweep over the critical U-turns for a level-0 fillet radius; negative when it does not fit."""
    n, j = d.n, d.j
    smallest = math.inf

    def between(ja: int, jb: int, i_a: int, i_b: int, radius: float, kind: CornerType, level: int) -> float:
        rho = rho_at(d, rho0, level)
        ca = make_corner(side_line(d, ja, i_a), radius, 1, kind, rho)
        cb = make_corner(side_line(d, jb, i_b), radius, -1, kind, rho)
        return _sweep_between(ca, cb)

    for lv in (0, n - 1):
        i = n - 1 - lv
        smallest = min(smallest, between(0, 1, i, i, far_r(d, lv), d.type_far, lv))
        smallest = min(smallest, between(1, 2, lv, lv, near_r(d, lv), d.type_near, lv))
    if d.nt > 1:
        last = 2 * d.pp - 1
        for i in (0, n - 1 - j):
            lv = i + j
            smallest = min(smallest, between(last, last + 1, i, i + j, near_r(d, lv), d.type_near, lv))
    return smallest


def start_radius(d: Frame, rho0: float) -> float:
    """Radius at which the first-turn strands start, which is also the radius of the centre via V; NaN if none."""
    p = d.p
    offset = d.w_near / 2 + d.s + p.via_pad / 2
    r_v = p.r_out - offset if d.outer else p.r_in + offset
    rho_j = rho_at(d, rho0, d.j) if d.n > d.j else 0.0
    if rho_j > 0:  # stay out of the fillet zone of the neighbouring trace J, which curves across the gap side
        c_j = make_corner(side_line(d, 0, d.j), near_r(d, d.j), -1, d.type_near, rho_j)
        if c_j is None:
            return math.nan
        o0 = (d.n - 1) / 2 * d.pitch
        if d.outer:
            return min(r_v, c_j.x_l)
        return max(r_v, c_j.x_l if p.style is SideStyle.RADIAL else math.sqrt(c_j.x_l * c_j.x_l + o0 * o0))
    return r_v


def min_straight(d: Frame, rho0: float) -> float:
    """Shortest straight part over all traces; negative when the fillets overlap."""
    n, j = d.n, d.j
    last = 2 * d.pp - 1
    smallest = math.inf

    def signed(near_x: float, far_x: float) -> float:
        return near_x - far_x if d.outer else far_x - near_x

    for i in range(n):
        far = make_corner(side_line(d, 1, i), far_r(d, n - 1 - i), -1, d.type_far, rho_at(d, rho0, n - 1 - i))
        near = make_corner(side_line(d, 1, i), near_r(d, i), 1, d.type_near, rho_at(d, rho0, i))
        if far is None or near is None:
            return -1.0
        smallest = min(smallest, signed(near.x_l, far.x_l))
        if i + j <= n - 1:  # closing level on the last side
            near = make_corner(side_line(d, last, i), near_r(d, i + j), 1, d.type_near, rho_at(d, rho0, i + j))
            far = make_corner(side_line(d, last, i), far_r(d, n - 1 - i), -1, d.type_far, rho_at(d, rho0, n - 1 - i))
            if far is None or near is None:
                return -1.0
            smallest = min(smallest, signed(near.x_l, far.x_l))
    r_v = start_radius(d, rho0)
    if not math.isfinite(r_v):
        return -1.0
    for i in range(j):
        line = side_line(d, 0, i)
        if abs(line.d) >= r_v:
            return -1.0
        far = make_corner(line, far_r(d, n - 1 - i), 1, d.type_far, rho_at(d, rho0, n - 1 - i))
        if far is None:
            return -1.0
        smallest = min(smallest, signed(math.sqrt(r_v * r_v - line.d * line.d), far.x_l))
    return smallest


def fillet_metric(d: Frame, rho0: float) -> float:
    """Non-negative exactly when the level-0 fillet radius ``rho0`` fits (Xcoil ``filletMetric``)."""
    return min(min_sweep(d, rho0), min_straight(d, rho0) - MIN_STRAIGHT_MM)


def max_fillet(d: Frame) -> float:
    """Largest level-0 fillet radius that fits; -1 when even a sharp corner does not."""
    hi = max(0.0, (d.p.r_out - d.p.r_in) / 2)
    if fillet_metric(d, 0.0) < 0:
        return -1.0
    if d.p.corner_style is CornerStyle.SHARP:
        return 0.0
    if fillet_metric(d, hi) >= 0:
        return hi
    lo = 0.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if fillet_metric(d, mid) >= 0:
            lo = mid
        else:
            hi = mid
    return lo


def _innermost_corners(d: Frame, rho0: float) -> tuple[Corner | None, ...]:
    """Return the four corners a, b, c, d that bound the innermost U-turn and its back-to-back neighbours."""
    n = d.n
    if d.outer:  # the inner end is the far end
        specs = ((0, n - 1, 0, 1), (1, n - 1, 0, -1), (1, 0, n - 1, -1), (2, 0, n - 1, 1))
        radius, kind = far_r, d.type_far
    else:  # the inner end is the near end
        specs = ((1, 0, 0, 1), (2, 0, 0, -1), (2, n - 1, n - 1, -1), (3, n - 1, n - 1, 1))
        radius, kind = near_r, d.type_near
    return tuple(
        make_corner(side_line(d, ju, i), radius(d, level), u, kind, rho_at(d, rho0, level)) for ju, i, level, u in specs
    )


def _inner_terminal_gap(d: Frame, rho0: float) -> float | None:
    """Gap of the last-turn strands to the neighbouring side at an inner terminal; None if the geometry fails."""
    n = d.n
    line_e = side_line(d, -1, n - 1)
    c_s = make_corner(side_line(d, -2, n - 1), near_r(d, n - 1), -1, d.type_near, rho_at(d, rho0, n - 1))
    if c_s is None:
        return None
    c_e, s_e = math.cos(line_e.phi), math.sin(line_e.phi)

    def y_f(pt: Point) -> float:
        return -pt[0] * s_e + pt[1] * c_e

    gap = line_e.d - y_f(c_s.p_l)
    if c_s.rho > 0:
        gap = min(gap, line_e.d - y_f(c_s.cf) - c_s.rho)
    return gap


def _acute_corner(d: Frame) -> bool:
    """Parallel-offset lines meet the concentric end-turn arcs at 90 degrees minus asin(offset / R): keep above 60."""
    p = d.p
    if p.style is not SideStyle.PARALLEL:
        return False
    r_bus_deep = near_r(d, d.n + (p.phases - 1) * d.bus_step)
    sharp = p.corner_style is CornerStyle.SHARP
    if d.outer:
        r_corner = far_r(d, d.n - 1) if sharp else math.inf
    else:
        r_corner = min(r_bus_deep, near_r(d, d.n - 1)) if sharp else r_bus_deep
    return d.bundle / 2 > 0.5 * r_corner


def _gaps(d: Frame, rho0: float) -> tuple[float, float, float] | None:
    """Leg gap, back-to-back gap and inner-terminal gap of the innermost U-turn; None if a corner does not close."""
    corners = _innermost_corners(d, rho0)
    if any(c is None for c in corners):
        return None
    a, b, c, e = (corner for corner in corners if corner is not None)
    legs, back = distance(a.p_l, b.p_l), distance(c.p_l, e.p_l)
    if c.rho > 0 and e.rho > 0:  # back-to-back fillets keep converging a little after their tangent points
        back = min(back, distance(c.cf, e.cf) - c.rho - e.rho)
    if b.ang_l - a.ang_l <= 0:
        legs = -legs  # the two legs have crossed over
    if e.ang_l - c.ang_l <= 0:
        back = -back  # neighbouring bundles overlap at the inner end
    end_gap = math.inf
    if not d.outer:
        measured = _inner_terminal_gap(d, rho0)
        if measured is None:
            return None
        end_gap = measured
    return legs, back, end_gap


def _level0_fillet(d: Frame, rho0_max: float) -> float:
    p = d.p
    if p.corner_style is CornerStyle.SHARP:
        return 0.0
    return rho0_max if p.fillet_max else min(p.fillet_radius, rho0_max)


def fit_status(d: Frame) -> Fit:
    """Decide whether the bundle fits between neighbouring sides (Xcoil ``fitStatus``, engine.js l.341).

    Checks that end-turn arcs have non-negative sweep, that the two legs of the innermost U-turn and the back-to-back
    legs of neighbouring U-turns stay one pitch apart at their deepest point, and the inner-terminal gap.
    """
    p, n = d.p, d.n
    if p.style is SideStyle.RADIAL and not d.r_ref > d.pitch:
        return Fit(ok=False, reason=FitFailure.R_TOO_SMALL)
    if p.r_in - (n - 1) * (d.p_far if d.outer else d.p_near) <= d.bundle / 2 + 0.2:
        return Fit(ok=False, reason=FitFailure.R_TOO_SMALL)
    if _acute_corner(d):
        return Fit(ok=False, reason=FitFailure.ACUTE_CORNER)
    rho0_max = max_fillet(d)
    too_wide = Fit(ok=False, reason=FitFailure.BUNDLE_TOO_WIDE, rho0_max=rho0_max)
    if rho0_max < 0:
        return too_wide
    rho0 = _level0_fillet(d, rho0_max)
    gaps = _gaps(d, rho0)
    if gaps is None:
        return too_wide
    legs, back, end_gap = gaps
    ok = legs >= d.pitch - FIT_TOLERANCE and back >= d.pitch - FIT_TOLERANCE and end_gap >= d.pitch - FIT_TOLERANCE
    return Fit(
        ok=ok,
        reason=None if ok else FitFailure.BUNDLE_TOO_WIDE,
        rho0=rho0,
        rho0_max=rho0_max,
        leg_gap=legs,
        back_gap=back,
        end_gap=end_gap,
    )


def max_traces_fit(p: Params) -> int:
    """Largest number of traces (turns x strands) that still fits (Xcoil ``maxTracesFit``, one strand per turn)."""
    best = 0
    for turns in range(1, MAX_TRACES_SEARCH + 1):
        if not fit_status(derive(replace(p, strands=1, turns=turns))).ok:
            if best > 0:
                break
            continue
        best = turns
    return best
