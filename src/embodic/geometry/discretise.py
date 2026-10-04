"""Polyline discretisation of primitive chains: a port of Xcoil discretize (engine.js l.536-560) with its segment rule.

A line splits into ``max(1, ceil(L / max_segment))`` equal chords. An arc splits into the largest of that count and
``ceil(|sweep| / min(max_angle, sagitta_angle))``, where ``sagitta_angle = 2 acos(1 - max_sagitta / r)`` keeps each
chord's sagitta below ``max_sagitta`` (Xcoil uses ``max_angle`` when ``r <= max_sagitta``). Primitives shorter than
1e-12 mm are skipped but keep their index. The counts are ``ceil`` decisions on floats, so a 1-ulp difference can change
one count near an integer ratio (port notes section 2.3, test_plan.md section 3 near-threshold rule).
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from embodic.geometry.primitives import Line, Primitive, PrimitiveRole, primitive_length_mm
from embodic.units import FloatArray

DEFAULT_MAX_SEGMENT_MM = 0.5
DEFAULT_MAX_ANGLE_RAD = 5 * math.pi / 180
DEFAULT_MAX_SAGITTA_MM = 0.001
_SKIP_BELOW_MM = 1e-12


@dataclass(frozen=True, slots=True, kw_only=True)
class Segment:
    """One straight chord of a discretised chain (Xcoil keys x1, y1, x2, y2, s, len, w, kind, pi)."""

    x1_mm: float
    y1_mm: float
    x2_mm: float
    y2_mm: float
    s_mm: float  # path position of the chord midpoint, measured along the primitives
    length_mm: float  # primitive length / piece count, not the chord length
    width_mm: float
    role: PrimitiveRole
    prim_index: int


def piece_ratios(
    p: Primitive,
    max_segment_mm: float = DEFAULT_MAX_SEGMENT_MM,
    max_angle_rad: float = DEFAULT_MAX_ANGLE_RAD,
    max_sagitta_mm: float = DEFAULT_MAX_SAGITTA_MM,
) -> tuple[float, ...]:
    """Return the ratios whose ``ceil`` Xcoil takes for the piece count (engine.js l.543 and l.551)."""
    by_length = primitive_length_mm(p) / max_segment_mm
    if isinstance(p, Line):
        return (by_length,)
    if p.r_mm > max_sagitta_mm:
        sagitta_angle_rad = 2 * math.acos(1 - max_sagitta_mm / p.r_mm)
    else:
        sagitta_angle_rad = max_angle_rad
    return (by_length, abs(p.sweep_rad) / min(max_angle_rad, sagitta_angle_rad))


def piece_count(
    p: Primitive,
    max_segment_mm: float = DEFAULT_MAX_SEGMENT_MM,
    max_angle_rad: float = DEFAULT_MAX_ANGLE_RAD,
    max_sagitta_mm: float = DEFAULT_MAX_SAGITTA_MM,
) -> int:
    """Return the number of chords Xcoil cuts ``p`` into."""
    return max(1, *(math.ceil(r) for r in piece_ratios(p, max_segment_mm, max_angle_rad, max_sagitta_mm)))


def discretise_path(
    prims: Sequence[Primitive],
    max_segment_mm: float = DEFAULT_MAX_SEGMENT_MM,
    max_angle_rad: float = DEFAULT_MAX_ANGLE_RAD,
    max_sagitta_mm: float = DEFAULT_MAX_SAGITTA_MM,
) -> tuple[Segment, ...]:
    """Chords of a primitive chain with their path positions, in Xcoil's order and with Xcoil's arithmetic."""
    out: list[Segment] = []
    s_mm = 0.0
    for index, p in enumerate(prims):
        length_mm = primitive_length_mm(p)
        if length_mm < _SKIP_BELOW_MM:
            continue
        n = piece_count(p, max_segment_mm, max_angle_rad, max_sagitta_mm)
        for k in range(n):
            if isinstance(p, Line):
                t1, t2 = k / n, (k + 1) / n
                dx_mm, dy_mm = p.x2_mm - p.x1_mm, p.y2_mm - p.y1_mm
                x1_mm, y1_mm = p.x1_mm + dx_mm * t1, p.y1_mm + dy_mm * t1
                x2_mm, y2_mm = p.x1_mm + dx_mm * t2, p.y1_mm + dy_mm * t2
                mid_mm = s_mm + length_mm * (t1 + t2) / 2
            else:
                b1_rad = p.start_rad + p.sweep_rad * k / n
                b2_rad = p.start_rad + p.sweep_rad * (k + 1) / n
                x1_mm, y1_mm = p.point_at(b1_rad)
                x2_mm, y2_mm = p.point_at(b2_rad)
                mid_mm = s_mm + length_mm * (k + 0.5) / n
            out.append(
                Segment(
                    x1_mm=x1_mm,
                    y1_mm=y1_mm,
                    x2_mm=x2_mm,
                    y2_mm=y2_mm,
                    s_mm=mid_mm,
                    length_mm=length_mm / n,
                    width_mm=p.width_mm,
                    role=p.role,
                    prim_index=index,
                )
            )
        s_mm += length_mm
    return tuple(out)


def discretise(
    p: Primitive,
    max_segment_mm: float,
    max_angle_rad: float = DEFAULT_MAX_ANGLE_RAD,
    max_sagitta_mm: float = DEFAULT_MAX_SAGITTA_MM,
) -> FloatArray:
    """Polyline points (K, 2) of one primitive: the chord end points of ``discretise_path`` (GR-17)."""
    segments = discretise_path((p,), max_segment_mm, max_angle_rad, max_sagitta_mm)
    if not segments:
        start = p.start_point()
        return np.array([start, p.end_point()], dtype=np.float64)
    points = [(segments[0].x1_mm, segments[0].y1_mm)] + [(g.x2_mm, g.y2_mm) for g in segments]
    return np.array(points, dtype=np.float64)
