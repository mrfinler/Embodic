"""Self-tests of the continuity check (IT-21)."""

import math

import pytest
from continuity import first_gap
from records import Arc, Line

pytestmark = pytest.mark.req("REQ-N-21")

W = 0.2


def side_turn_side() -> list[Line | Arc]:
    """Return a side, a quarter end turn about the origin and a side back, continuous by construction."""
    return [
        Line(10.0, -5.0, 10.0, 0.0, W),
        Arc(0.0, 0.0, 10.0, 0.0, math.pi / 2, W),
        Line(0.0, 10.0, -5.0, 10.0, W),
    ]


def test_continuous_line_arc_line_path_has_no_gap() -> None:
    """Catch a checker that compares an arc's start angle instead of its end point, or ignores the sweep."""
    assert first_gap(side_turn_side()) is None


def test_negative_sweep_arc_ends_where_its_sweep_says() -> None:
    """A clockwise arc from 90 deg to 0 deg joins a side that starts at (10, 0)."""
    path = [
        Line(-5.0, 10.0, 0.0, 10.0, W),
        Arc(0.0, 0.0, 10.0, math.pi / 2, -math.pi / 2, W),
        Line(10.0, 0.0, 10.0, -5.0, W),
    ]
    assert first_gap(path) is None


def test_reports_the_first_gap_with_its_index_and_distance() -> None:
    """Seeded defect: the last side starts 2e-6 mm (2 nm) off, twice the bound; the gap is at joint 1."""
    path = side_turn_side()
    path[2] = Line(0.0, 10.0 + 2e-6, -5.0, 10.0, W)
    gap = first_gap(path)
    assert gap is not None
    assert gap.index == 1
    assert math.isclose(gap.distance_mm, 2e-6, rel_tol=1e-6)
    assert gap.next_start == (0.0, 10.0 + 2e-6)


def test_tolerance_is_1e6_mm() -> None:
    """A 0.9e-6 mm offset passes and 1.1e-6 mm fails: the bound is REQ-N-21's 1e-6 mm (revision 2026-10-05)."""
    within = [Line(0.0, 0.0, 1.0, 0.0, W), Line(1.0 + 0.9e-6, 0.0, 2.0, 0.0, W)]
    beyond = [Line(0.0, 0.0, 1.0, 0.0, W), Line(1.0 + 1.1e-6, 0.0, 2.0, 0.0, W)]
    assert first_gap(within) is None
    assert first_gap(beyond) is not None


def test_reversed_primitive_is_a_gap() -> None:
    """Catch a checker that accepts either end: a side drawn against current direction breaks the chain."""
    path = side_turn_side()
    path[0] = Line(10.0, 0.0, 10.0, -5.0, W)
    gap = first_gap(path)
    assert gap is not None and gap.index == 0


def test_nan_coordinate_is_a_gap() -> None:
    """A NaN end point never compares as close; the check must not pass it silently."""
    path = [Line(0.0, 0.0, math.nan, 0.0, W), Line(1.0, 0.0, 2.0, 0.0, W)]
    assert first_gap(path) is not None
