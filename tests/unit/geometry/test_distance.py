"""Segment-segment distance for nearly collinear segments (D-033c, same defect as DEF-M2d3-01 in the DRC kernel)."""

import math

import pytest

from embodic.geometry.distance import segment_segment_distance_mm
from embodic.geometry.primitives import Line, PrimitiveRole

pytestmark = pytest.mark.req("REQ-N-21")


def _line(x1: float, y1: float, x2: float, y2: float) -> Line:
    return Line(x1_mm=x1, y1_mm=y1, x2_mm=x2, y2_mm=y2, width_mm=0.0, role=PrimitiveRole.SIDE)


def test_nearly_collinear_disjoint_pair_reports_its_gap() -> None:
    """Catches an absolute cross-product threshold that turns rounding noise into a crossing (distance 0).

    The CF-11 pair pinned by DEF-M2d3-01 has a cross product of -2.7e-15 mm^2 on lengths of 19 mm and 1 mm. Its
    centre distance is 0.75 mm (tests/unit/drc/test_kernels.py checks that figure against a dense sample).
    """
    side = _line(4.384504814773052, -17.715490891568088, 9.069318178503163, -36.64437157022988)
    leg = _line(9.489750147043045, -38.34311727216107, 9.249503307877399, -37.372405442486105)
    assert segment_segment_distance_mm(side, leg) == pytest.approx(0.75, abs=1e-9)


def test_collinear_disjoint_segments_measure_the_gap_in_every_direction() -> None:
    """Catches a false crossing on two 20 mm segments of one line, 0.2 mm apart, in any of 720 directions."""
    ox, oy = 9.1, -36.6
    wrong = []
    for step in range(720):
        angle_rad = math.radians(step * 0.5) + 0.01
        ux, uy = math.cos(angle_rad), math.sin(angle_rad)
        a = _line(ox, oy, ox + 20 * ux, oy + 20 * uy)
        b = _line(ox + 20.2 * ux, oy + 20.2 * uy, ox + 40.2 * ux, oy + 40.2 * uy)
        if abs(segment_segment_distance_mm(a, b) - 0.2) > 1e-9:
            wrong.append(step)
    assert not wrong, f"{len(wrong)} of 720 directions report a false crossing, first at step {wrong[0]}"


def test_shallow_true_crossing_is_exactly_zero() -> None:
    """Catches a tolerance so wide that a real crossing at 2e-7 rad is measured by its end points (5e-6 mm)."""
    assert segment_segment_distance_mm(_line(0, 0, 10, 0), _line(0, -1e-6, 10, 1e-6)) == 0.0
