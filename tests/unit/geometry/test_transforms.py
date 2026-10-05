"""UT-GEO-22 (brief U-M1b): rotation, mirror and reversal against closed-form results."""

import math

import pytest
from hypothesis import given

from embodic.geometry.primitives import Arc, Line, PrimitiveRole
from embodic.geometry.transforms import Transform, mirror, reverse_path, rotate, transform_point

from .strategies import angle_rad, chains

pytestmark = pytest.mark.req("REQ-N-21")

TOL_MM = 1e-12


def _close(a: tuple[float, float], b: tuple[float, float], tol_mm: float = TOL_MM) -> bool:
    return math.dist(a, b) <= tol_mm


def test_ut_geo_22_rotation_by_60_degrees_matches_closed_form() -> None:
    """Catches a rotation applied clockwise or in degrees: (2, 0) must land on (1, sqrt 3)."""
    (moved,) = rotate(
        (Line(x1_mm=2.0, y1_mm=0.0, x2_mm=4.0, y2_mm=0.0, width_mm=0.3, role=PrimitiveRole.SIDE),), math.pi / 3
    )
    assert isinstance(moved, Line)
    assert _close(moved.start_point(), (1.0, math.sqrt(3)))
    assert _close(moved.end_point(), (2.0, 2 * math.sqrt(3)))
    assert moved.width_mm == 0.3


def test_ut_geo_22_mirror_about_45_degrees_swaps_x_and_y_and_reverses_arc_sense() -> None:
    """Catches a mirror that keeps the arc's sweep sign: a mirrored counter-clockwise arc runs clockwise."""
    arc = Arc(
        cx_mm=3.0, cy_mm=1.0, r_mm=0.5, start_rad=0.0, sweep_rad=math.pi / 2, width_mm=0.2, role=PrimitiveRole.FILLET
    )
    (moved,) = mirror((arc,), math.pi / 4)
    assert isinstance(moved, Arc)
    assert _close((moved.cx_mm, moved.cy_mm), (1.0, 3.0))
    assert moved.sweep_rad == -math.pi / 2
    assert _close(moved.start_point(), (1.0, 3.5))
    assert _close(moved.end_point(), (1.5, 3.0))


def test_ut_geo_22_transform_mirrors_before_rotating() -> None:
    """Catches the opposite order: mirror about x then rotate 90 degrees sends (1, 1) to (1, 1), not (-1, -1)."""
    assert _close(transform_point(Transform(rotation_rad=math.pi / 2, mirror_axis_rad=0.0), 1.0, 1.0), (1.0, 1.0))


@given(chains(), angle_rad)
def test_ut_geo_22_rotation_preserves_end_points_distance_and_reverses_with_its_inverse(chain, turn_rad) -> None:
    """Catches a rotation that scales or shears: rotating forward and back returns every end point."""
    back = rotate(rotate(chain, turn_rad), -turn_rad)
    for p, q in zip(chain, back, strict=True):
        assert _close(p.start_point(), q.start_point(), 1e-9)
        assert _close(p.end_point(), q.end_point(), 1e-9)


@given(chains())
def test_ut_geo_22_reverse_runs_the_same_copper_backwards(chain) -> None:
    """Catches a reversal that keeps primitive order or forgets to swap an arc's direction."""
    reversed_chain = reverse_path(chain)
    assert len(reversed_chain) == len(chain)
    for p, q in zip(chain, reversed(reversed_chain), strict=True):
        assert type(p) is type(q)
        assert _close(p.start_point(), q.end_point(), 1e-9)
        assert _close(p.end_point(), q.start_point(), 1e-9)
