"""UT-GEO-15 (brief U-M1b): discretised chords respect the length, angle and sagitta bounds and cover the path."""

import math

import pytest
from hypothesis import given
from hypothesis import strategies as st

from embodic.geometry.discretise import discretise, discretise_path
from embodic.geometry.paths import is_continuous
from embodic.geometry.primitives import Arc, Line, PrimitiveRole, path_length_mm, primitive_length_mm

from .strategies import chains

pytestmark = pytest.mark.req("REQ-N-21")

max_segment_mm = st.floats(0.1, 2.0)
max_angle_rad = st.floats(math.radians(1), math.radians(30))
max_sagitta_mm = st.floats(1e-4, 0.05)


@given(chains(), max_segment_mm, max_angle_rad, max_sagitta_mm)
def test_ut_geo_15_chords_respect_every_bound(chain, seg_mm, ang_rad, sag_mm) -> None:
    """Catches a piece count taken with floor, or an arc split by length alone that breaks the sagitta bound."""
    for g in discretise_path(chain, seg_mm, ang_rad, sag_mm):
        assert g.length_mm <= seg_mm * (1 + 1e-12)
        p = chain[g.prim_index]
        if isinstance(p, Arc):
            step_rad = g.length_mm / p.r_mm
            assert step_rad <= ang_rad * (1 + 1e-12)
            assert p.r_mm * (1 - math.cos(step_rad / 2)) <= sag_mm * (1 + 1e-9)


@given(chains(), max_segment_mm)
def test_ut_geo_15_chords_cover_the_path_once_in_order(chain, seg_mm) -> None:
    """Catches a skipped or doubled piece: piece lengths sum to the path length and positions increase."""
    segments = discretise_path(chain, seg_mm)
    assert math.isclose(math.fsum(g.length_mm for g in segments), path_length_mm(chain), rel_tol=1e-12)
    positions = [g.s_mm for g in segments]
    assert positions == sorted(positions)
    lines = [
        Line(x1_mm=g.x1_mm, y1_mm=g.y1_mm, x2_mm=g.x2_mm, y2_mm=g.y2_mm, width_mm=0, role=g.role) for g in segments
    ]
    assert is_continuous(lines)


def test_ut_geo_15_quarter_arc_count_follows_the_tightest_bound() -> None:
    """Catches the wrong bound winning: r = 10 mm, 90 degrees, 5 degree step gives 18 chords, not 32 by length."""
    arc = Arc(
        cx_mm=0.0, cy_mm=0.0, r_mm=10.0, start_rad=0.0, sweep_rad=math.pi / 2, width_mm=0.2, role=PrimitiveRole.SIDE
    )
    sag_angle_rad = 2 * math.acos(1 - 0.001 / 10.0)
    assert len(discretise_path((arc,), 2.0)) == math.ceil((math.pi / 2) / sag_angle_rad)
    assert len(discretise_path((arc,), 2.0, max_sagitta_mm=1.0)) == 18


def test_ut_geo_15_points_start_and_end_on_the_primitive() -> None:
    """Catches an off-by-one polyline: K chords give K + 1 points from start to end."""
    line = Line(x1_mm=0.0, y1_mm=0.0, x2_mm=3.0, y2_mm=4.0, width_mm=0.2, role=PrimitiveRole.SIDE)
    points = discretise(line, 1.0)
    assert points.shape == (6, 2)
    assert tuple(points[0]) == (0.0, 0.0)
    assert tuple(points[-1]) == (3.0, 4.0)
    assert primitive_length_mm(line) == 5.0
