"""Exact centreline distances between lines and arcs, vectorised over row pairs, and Xcoil's pad kernels.

Rows follow ``LayoutArrays``: a line is ``(x1, y1, x2, y2, width)``, an arc ``(cx, cy, r, start, sweep, width)``;
widths are ignored here. Row ``i`` of ``a`` is measured against row ``i`` of ``b``.

Exactness. Each kernel takes the least of a set of distances between a point of ``a`` and a point of ``b``, so it never
reports less than the true distance, and that set always holds a true closest pair: an intersection (distance 0), a
pair with an end point (point-to-primitive distance is exact), or an interior pair whose connecting line is normal to
both primitives. For a line and an arc that interior pair is the foot of the arc centre on the line and the arc point
above it; for two arcs both points lie on the line through the two centres. Concentric arcs need no interior pair:
when their angular ranges overlap, an end point of one lies inside the other's range and is radially closest.
"""

import math

import numpy as np
from numpy.typing import NDArray

from embodic.geometry.layout import Pad
from embodic.units import FloatArray

# Parallel test: |d1 x d2| <= eps |d1| |d2|, i.e. sin(angle) <= eps (D-032e). Xcoil's absolute 1e-15 mm^2 (engine.js
# l.565) mistakes rounding noise on long segments for a crossing (DEF-M2d3-01). A real crossing missed below eps is
# measured by its end points instead, at most eps times the longer segment (1e-10 mm for 100 mm).
_PARALLEL_SINE = 1e-12
_TWO_PI = 2 * math.pi

BoolArray = NDArray[np.bool_]

# Rows of a closest-pair array (5, N): distance, then the point on ``a`` and the point on ``b``.
D, PX, PY, QX, QY = range(5)


def _hypot(dx: FloatArray, dy: FloatArray) -> FloatArray:
    """Xcoil's hypot, ``sqrt(dx*dx + dy*dy)``, so line results match Xcoil bit for bit."""
    result: FloatArray = np.sqrt(dx * dx + dy * dy)
    return result


def _better(best: FloatArray, candidate: FloatArray, valid: BoolArray | bool = True) -> FloatArray:
    """Keep, per column, the closest pair with the smaller distance; ``valid`` masks candidates that do not exist."""
    take = valid & (candidate[D] < best[D])
    result: FloatArray = np.where(take, candidate, best)
    return result


def _swap(pair: FloatArray) -> FloatArray:
    """Exchange the roles of ``a`` and ``b`` in a closest-pair array."""
    return pair[[D, QX, QY, PX, PY]]


def in_sweep(angle_rad: FloatArray, start_rad: FloatArray, sweep_rad: FloatArray) -> BoolArray:
    """Whether a direction lies on the arc from ``start`` through the signed ``sweep`` (a full turn holds all)."""
    delta_rad = np.mod(np.where(sweep_rad >= 0, angle_rad - start_rad, start_rad - angle_rad), _TWO_PI)
    result: BoolArray = (np.abs(sweep_rad) >= _TWO_PI) | (delta_rad <= np.abs(sweep_rad))
    return result


def _point_segment(px: FloatArray, py: FloatArray, seg: FloatArray) -> FloatArray:
    """Xcoil ptSegDist (engine.js l.573) with the foot point; a zero-length segment is its start point."""
    x1, y1, x2, y2 = seg[:, 0], seg[:, 1], seg[:, 2], seg[:, 3]
    dx, dy = x2 - x1, y2 - y1
    length2 = dx * dx + dy * dy
    has_length = length2 > 0
    t = np.where(has_length, ((px - x1) * dx + (py - y1) * dy) / np.where(has_length, length2, 1.0), 0.0)
    t = np.clip(t, 0.0, 1.0)
    qx, qy = x1 + t * dx, y1 + t * dy
    return np.stack([_hypot(px - qx, py - qy), px, py, qx, qy])


def _arc_point(arc: FloatArray, angle_rad: FloatArray) -> tuple[FloatArray, FloatArray]:
    return arc[:, 0] + arc[:, 2] * np.cos(angle_rad), arc[:, 1] + arc[:, 2] * np.sin(angle_rad)


def _point_arc(px: FloatArray, py: FloatArray, arc: FloatArray) -> FloatArray:
    """Point to arc: radial projection when it falls on the arc, else the nearer arc end."""
    cx, cy, r, start, sweep = arc[:, 0], arc[:, 1], arc[:, 2], arc[:, 3], arc[:, 4]
    sx, sy = _arc_point(arc, start)
    ex, ey = _arc_point(arc, start + sweep)
    best = np.stack([_hypot(px - sx, py - sy), px, py, sx, sy])
    best = _better(best, np.stack([_hypot(px - ex, py - ey), px, py, ex, ey]))
    vx, vy = px - cx, py - cy
    rho = _hypot(vx, vy)
    radial = (rho > 0) & in_sweep(np.arctan2(vy, vx), start, sweep)
    scale = r / np.where(radial, rho, 1.0)
    return _better(best, np.stack([np.abs(rho - r), px, py, cx + vx * scale, cy + vy * scale]), radial)


def _line_line(a: FloatArray, b: FloatArray) -> FloatArray:
    """Xcoil segSegDist (engine.js l.563) with the closest points: 0 at a crossing, else the best end point."""
    d1x, d1y = a[:, 2] - a[:, 0], a[:, 3] - a[:, 1]
    d2x, d2y = b[:, 2] - b[:, 0], b[:, 3] - b[:, 1]
    best = _point_segment(a[:, 0], a[:, 1], b)
    best = _better(best, _point_segment(a[:, 2], a[:, 3], b))
    best = _better(best, _swap(_point_segment(b[:, 0], b[:, 1], a)))
    best = _better(best, _swap(_point_segment(b[:, 2], b[:, 3], a)))
    den = d1x * d2y - d1y * d2x
    skew = np.abs(den) > _PARALLEL_SINE * _hypot(d1x, d1y) * _hypot(d2x, d2y)
    safe = np.where(skew, den, 1.0)
    ex, ey = b[:, 0] - a[:, 0], b[:, 1] - a[:, 1]
    t = (ex * d2y - ey * d2x) / safe
    u = (ex * d1y - ey * d1x) / safe
    crossing = skew & (t >= 0) & (t <= 1) & (u >= 0) & (u <= 1)
    xx, xy = a[:, 0] + t * d1x, a[:, 1] + t * d1y
    return np.where(crossing, np.stack([np.zeros_like(xx), xx, xy, xx, xy]), best)


def _line_arc(a: FloatArray, b: FloatArray) -> FloatArray:
    """Line ``a`` to arc ``b``: end points, the foot of the arc centre, and line-circle intersections."""
    x1, y1, x2, y2 = a[:, 0], a[:, 1], a[:, 2], a[:, 3]
    cx, cy, r, start, sweep = b[:, 0], b[:, 1], b[:, 2], b[:, 3], b[:, 4]
    best = _point_arc(x1, y1, b)
    best = _better(best, _point_arc(x2, y2, b))
    for angle_rad in (start, start + sweep):
        ex, ey = _arc_point(b, angle_rad)
        best = _better(best, _swap(_point_segment(ex, ey, a)))
    dx, dy = x2 - x1, y2 - y1
    length2 = dx * dx + dy * dy
    has_length = length2 > 0
    tf = ((cx - x1) * dx + (cy - y1) * dy) / np.where(has_length, length2, 1.0)
    fx, fy = x1 + tf * dx, y1 + tf * dy
    vx, vy = fx - cx, fy - cy
    rho = _hypot(vx, vy)
    foot = has_length & (tf >= 0) & (tf <= 1) & (rho > 0) & in_sweep(np.arctan2(vy, vx), start, sweep)
    scale = r / np.where(rho > 0, rho, 1.0)
    best = _better(best, np.stack([np.abs(rho - r), fx, fy, cx + vx * scale, cy + vy * scale]), foot)
    half_chord = np.sqrt(np.maximum(r * r - rho * rho, 0.0)) / np.sqrt(np.where(has_length, length2, 1.0))
    for sign in (1.0, -1.0):
        t = tf + sign * half_chord
        xx, xy = x1 + t * dx, y1 + t * dy
        hit = has_length & (rho <= r) & (t >= 0) & (t <= 1) & in_sweep(np.arctan2(xy - cy, xx - cx), start, sweep)
        best = _better(best, np.stack([np.zeros_like(xx), xx, xy, xx, xy]), hit)
    return best


def _arc_arc(a: FloatArray, b: FloatArray) -> FloatArray:
    """Arc ``a`` to arc ``b``: end points, the four points on the centre line, and circle intersections."""
    acx, acy, ar, astart, asweep = a[:, 0], a[:, 1], a[:, 2], a[:, 3], a[:, 4]
    bcx, bcy, br, bstart, bsweep = b[:, 0], b[:, 1], b[:, 2], b[:, 3], b[:, 4]
    best = _point_arc(*_arc_point(a, astart), b)
    best = _better(best, _point_arc(*_arc_point(a, astart + asweep), b))
    best = _better(best, _swap(_point_arc(*_arc_point(b, bstart), a)))
    best = _better(best, _swap(_point_arc(*_arc_point(b, bstart + bsweep), a)))
    gap = _hypot(bcx - acx, bcy - acy)
    apart = gap > 0
    safe = np.where(apart, gap, 1.0)
    ux, uy = (bcx - acx) / safe, (bcy - acy) / safe
    for sa in (1.0, -1.0):
        pa_ok = apart & in_sweep(np.arctan2(sa * uy, sa * ux), astart, asweep)
        pax, pay = acx + sa * ar * ux, acy + sa * ar * uy
        for sb in (1.0, -1.0):
            ok = pa_ok & in_sweep(np.arctan2(sb * uy, sb * ux), bstart, bsweep)
            qbx, qby = bcx + sb * br * ux, bcy + sb * br * uy
            best = _better(best, np.stack([_hypot(pax - qbx, pay - qby), pax, pay, qbx, qby]), ok)
    along = (gap * gap + ar * ar - br * br) / (2 * safe)
    height = np.sqrt(np.maximum(ar * ar - along * along, 0.0))
    meets = apart & (gap <= ar + br) & (gap >= np.abs(ar - br))
    for sign in (1.0, -1.0):
        xx, xy = acx + along * ux - sign * height * uy, acy + along * uy + sign * height * ux
        hit = (
            meets
            & in_sweep(np.arctan2(xy - acy, xx - acx), astart, asweep)
            & in_sweep(np.arctan2(xy - bcy, xx - bcx), bstart, bsweep)
        )
        best = _better(best, np.stack([np.zeros_like(xx), xx, xy, xx, xy]), hit)
    return best


def closest_pairs(a: FloatArray, a_is_arc: bool, b: FloatArray, b_is_arc: bool) -> FloatArray:
    """Closest-pair array (5, N) for row pairs of one kind combination: distance, point on ``a``, point on ``b``."""
    if not a_is_arc and not b_is_arc:
        return _line_line(a, b)
    if not a_is_arc:
        return _line_arc(a, b)
    if not b_is_arc:
        return _swap(_line_arc(b, a))
    return _arc_arc(a, b)


def min_distance_line_line(a: FloatArray, b: FloatArray) -> FloatArray:
    """Centreline distance of each line pair (mm); equals Xcoil segSegDist (GR-18) except its false crossings."""
    result: FloatArray = closest_pairs(a, False, b, False)[D]
    return result


def min_distance_line_arc(a: FloatArray, b: FloatArray) -> FloatArray:
    """Centreline distance from each line of ``a`` to the arc in the same row of ``b`` (mm), exact."""
    result: FloatArray = closest_pairs(a, False, b, True)[D]
    return result


def min_distance_arc_arc(a: FloatArray, b: FloatArray) -> FloatArray:
    """Centreline distance of each arc pair (mm), exact."""
    result: FloatArray = closest_pairs(a, True, b, True)[D]
    return result


def pad_bounding_radius_mm(pad: Pad) -> float:
    """Xcoil padRadius (engine.js l.1818): the circumscribed radius, so pad-to-pad checks are conservative."""
    if pad.shape == "round":
        return pad.width_mm / 2
    return math.sqrt(pad.width_mm * pad.width_mm + pad.height_mm * pad.height_mm) / 2


def pad_closest(pad: Pad, rows: FloatArray, rows_are_arcs: bool) -> FloatArray:
    """Xcoil padSegClearance (engine.js l.1819) for lines or arcs: closest pairs from the pad outline to each row.

    The distance is signed: a rectangle returns the negated edge distance when a row starts inside it. Round and
    oblong pads measure to the outline (core distance minus the core radius). The point on ``a`` is the pad's core
    point; all points are in board coordinates.
    """
    c, s = math.cos(-pad.rotation_rad), math.sin(-pad.rotation_rad)
    local = _to_pad_frame(rows, rows_are_arcs, pad.x_mm, pad.y_mm, c, s)
    hw_mm, hh_mm = pad.width_mm / 2, pad.height_mm / 2
    n = len(rows)
    if pad.shape == "round":
        cores, inset_mm = [np.zeros((n, 5))], hw_mm
    elif pad.shape == "oblong":
        core = [-max(0.0, hw_mm - hh_mm), 0.0, max(0.0, hw_mm - hh_mm), 0.0, 0.0]
        if hw_mm < hh_mm:
            core = [0.0, -(hh_mm - hw_mm), 0.0, hh_mm - hw_mm, 0.0]
        cores, inset_mm = [np.tile(core, (n, 1))], min(hw_mm, hh_mm)
    else:
        corners = [(-hw_mm, -hh_mm, hw_mm, -hh_mm), (hw_mm, -hh_mm, hw_mm, hh_mm)]
        corners += [(hw_mm, hh_mm, -hw_mm, hh_mm), (-hw_mm, hh_mm, -hw_mm, -hh_mm)]
        cores, inset_mm = [np.tile([*e, 0.0], (n, 1)) for e in corners], 0.0
    best = closest_pairs(cores[0], False, local, rows_are_arcs)
    for core_rows in cores[1:]:
        best = _better(best, closest_pairs(core_rows, False, local, rows_are_arcs))
    best[D] -= inset_mm
    if pad.shape not in ("round", "oblong"):
        sx, sy = _arc_point(local, local[:, 3]) if rows_are_arcs else (local[:, 0], local[:, 1])
        best[D] = np.where((np.abs(sx) < hw_mm) & (np.abs(sy) < hh_mm), -best[D], best[D])
    return _from_pad_frame(best, pad.x_mm, pad.y_mm, c, s)


def _to_pad_frame(rows: FloatArray, rows_are_arcs: bool, x_mm: float, y_mm: float, c: float, s: float) -> FloatArray:
    """Xcoil's ``loc``: translate to the pad centre, then rotate by minus the pad rotation."""
    local = rows.astype(np.float64, copy=True)
    pairs = ((0, 1),) if rows_are_arcs else ((0, 1), (2, 3))
    for ix, iy in pairs:
        dx, dy = rows[:, ix] - x_mm, rows[:, iy] - y_mm
        local[:, ix], local[:, iy] = dx * c - dy * s, dx * s + dy * c
    if rows_are_arcs:
        local[:, 3] = rows[:, 3] + math.atan2(s, c)
    return local


def _from_pad_frame(pair: FloatArray, x_mm: float, y_mm: float, c: float, s: float) -> FloatArray:
    out = pair.copy()
    for ix, iy in ((PX, PY), (QX, QY)):
        out[ix] = x_mm + pair[ix] * c + pair[iy] * s
        out[iy] = y_mm - pair[ix] * s + pair[iy] * c
    return out
