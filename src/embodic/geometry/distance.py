"""Point-segment and segment-segment distances (Xcoil ptSegDist and segSegDist, engine.js l.563-578)."""

from typing import Protocol

from embodic.geometry.primitives import hypot_mm

# Parallel test: |d1 x d2| <= eps |d1| |d2| (D-032e, D-033c). Xcoil's absolute 1e-15 mm^2 (engine.js l.565) mistakes
# rounding noise on long segments for a crossing; the same constant as embodic.drc.kernels.
_PARALLEL_SINE = 1e-12


class Chord(Protocol):
    """Anything with straight end points: a Line, a discretised Segment."""

    @property
    def x1_mm(self) -> float:
        """Start x (mm)."""

    @property
    def y1_mm(self) -> float:
        """Start y (mm)."""

    @property
    def x2_mm(self) -> float:
        """End x (mm)."""

    @property
    def y2_mm(self) -> float:
        """End y (mm)."""


def point_segment_distance_mm(px_mm: float, py_mm: float, s: Chord) -> float:
    """Distance from a point to the closed segment; a zero-length segment is its start point."""
    dx_mm, dy_mm = s.x2_mm - s.x1_mm, s.y2_mm - s.y1_mm
    length2_mm2 = dx_mm * dx_mm + dy_mm * dy_mm
    t = ((px_mm - s.x1_mm) * dx_mm + (py_mm - s.y1_mm) * dy_mm) / length2_mm2 if length2_mm2 > 0 else 0.0
    t = 0.0 if t < 0 else (1.0 if t > 1 else t)
    return hypot_mm(px_mm - (s.x1_mm + t * dx_mm), py_mm - (s.y1_mm + t * dy_mm))


def segment_segment_distance_mm(a: Chord, b: Chord) -> float:
    """0 when the segments intersect (non-parallel case), else the least end-point-to-segment distance.

    Equals Xcoil segSegDist (GR-17) except where Xcoil reports a false crossing on nearly collinear segments
    (XD-M1-002).
    """
    d1x_mm, d1y_mm = a.x2_mm - a.x1_mm, a.y2_mm - a.y1_mm
    d2x_mm, d2y_mm = b.x2_mm - b.x1_mm, b.y2_mm - b.y1_mm
    den_mm2 = d1x_mm * d2y_mm - d1y_mm * d2x_mm
    if abs(den_mm2) > _PARALLEL_SINE * hypot_mm(d1x_mm, d1y_mm) * hypot_mm(d2x_mm, d2y_mm):
        ex_mm, ey_mm = b.x1_mm - a.x1_mm, b.y1_mm - a.y1_mm
        t = (ex_mm * d2y_mm - ey_mm * d2x_mm) / den_mm2
        u = (ex_mm * d1y_mm - ey_mm * d1x_mm) / den_mm2
        if 0 <= t <= 1 and 0 <= u <= 1:
            return 0.0
    return min(
        point_segment_distance_mm(a.x1_mm, a.y1_mm, b),
        point_segment_distance_mm(a.x2_mm, a.y2_mm, b),
        point_segment_distance_mm(b.x1_mm, b.y1_mm, a),
        point_segment_distance_mm(b.x2_mm, b.y2_mm, a),
    )
