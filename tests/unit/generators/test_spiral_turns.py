"""Turn table, turn limit and eye of one spiral coil against Agent 2's worked examples (spiral_generator_spec.md).

Expected values are the printed numbers of worked examples 1 and 2 (CF-11, CF-10 in oracle_cases.json); they come
from the reference model, not from this code.
"""

import math
from itertools import pairwise

import pytest

from embodic.generators.spiral.turns import CoilFrame, TurnKind, eye, eye_limited_turns, loop_turns, radial_bound
from embodic.model.winding_specs import SpiralCoilSpec


def _default_frame(via_pad_mm: float = 0.6) -> CoilFrame:
    coil = SpiralCoilSpec(
        coil_count=12, r_inner_mm=18.0, r_outer_mm=38.0, trace_width_mm=0.5, clearance_mm=0.2, coil_gap_mm=0.2
    )
    return CoilFrame.of(coil, via_pad_mm)


def _d08_frame(via_pad_mm: float = 0.6) -> CoilFrame:
    coil = SpiralCoilSpec(
        coil_count=12, r_inner_mm=12.5 - 1.03, r_outer_mm=44.0 + 1.03, trace_width_mm=2.06, clearance_mm=0.8,
        coil_gap_mm=0.8,
    )  # fmt: skip
    return CoilFrame.of(coil, via_pad_mm)


@pytest.mark.req("REQ-F-06")
def test_default_turn_table_matches_worked_example_1() -> None:
    """Catches a wrong side offset, end radius or turn-type rule (CF-11 turn table, N = 10 of 11 loops)."""
    turns, _ = loop_turns(_default_frame())
    assert [t.kind for t in turns] == [TurnKind.TRAPEZOID] * 8 + [TurnKind.TRIANGLE] * 3
    assert turns[8].end_radius_mm == pytest.approx(24.3440, abs=5e-5)
    assert turns[9].end_radius_mm == pytest.approx(27.0484, abs=5e-5)
    assert [round(t.offset_mm, 9) for t in turns[:3]] == [0.35, 1.05, 1.75]
    assert turns[7].outer_radius_mm == pytest.approx(32.85, abs=1e-12)


@pytest.mark.req("REQ-F-06")
def test_ut_geo_09_turn_limit_is_eye_limited_at_ten() -> None:
    """UT-GEO-09: N = 10 is buildable and N = 11 is not; the eye, not the loop rule, binds (CF-11)."""
    frame = _default_frame()
    turns, _ = loop_turns(frame)
    assert eye_limited_turns(frame, turns) == 10
    window = eye(frame, turns, 10)
    assert window.fits and window.via_radius_mm == pytest.approx(29.6457, abs=5e-5)
    assert window.r_lo_mm == pytest.approx(28.5914, abs=5e-5)
    assert not eye(frame, turns, 11).fits
    assert radial_bound(frame) == pytest.approx(14.43, abs=5e-3)


@pytest.mark.req("REQ-F-06")
def test_or_04_d08_coil_has_three_loops_one_trapezoid_two_triangles() -> None:
    """OR-04: D08 Table 4.6 p.57 gives 3 loops; a pad of 1.2 mm leaves 2 with an eye limit (CF-10)."""
    frame = _d08_frame()
    turns, _ = loop_turns(frame)
    assert [t.kind for t in turns] == [TurnKind.TRAPEZOID, TurnKind.TRIANGLE, TurnKind.TRIANGLE]
    assert eye_limited_turns(frame, turns) == 3
    assert eye_limited_turns(_d08_frame(1.2), loop_turns(_d08_frame(1.2))[0]) == 2
    assert radial_bound(frame) == pytest.approx(6.006993006993007, rel=1e-9)
    assert turns[1].end_radius_mm == pytest.approx(22.1499, abs=5e-5)


@pytest.mark.req("REQ-F-06")
def test_ut_geo_08_inner_end_radius_grows_once_sides_converge() -> None:
    """UT-GEO-08: the moving inner end-turn radius increases monotonically turn by turn (no self-intersection)."""
    for frame in (_default_frame(), _d08_frame()):
        turns, _ = loop_turns(frame)
        radii = [t.end_radius_mm for t in turns]
        assert all(b > a for a, b in pairwise(radii))
        assert all(t.outer_radius_mm > t.end_radius_mm for t in turns)


@pytest.mark.req("REQ-F-06")
def test_ut_geo_17_parallel_sides_keep_constant_offset() -> None:
    """UT-GEO-17 (parallel): both ends of every right side lie at offset d_t from the right sector edge."""
    frame = _default_frame()
    h = frame.half_angle_rad
    for t in loop_turns(frame)[0]:
        for x, y in (t.b, t.c):
            assert x * math.sin(h) + y * math.cos(h) == pytest.approx(t.offset_mm, abs=1e-9)
