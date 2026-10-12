"""Turn table, turn limit and closing of one spiral coil against Agent 2's reference construction (U-E3, U-E3b).

Expected values: fixtures/spiral_r2_turns.json, written by make_r2_goldens.py from docs/phase2/engineering/checks/
spiral_reference.py (the construction spiral_r2_check.py uses), and the printed tables of spiral_generator_spec.md
worked examples 1 and 2. None of them comes from this code.
"""

import json
import math
from itertools import pairwise
from pathlib import Path

import pytest

from embodic.generators.spiral.turns import (
    CoilFrame,
    FullClosing,
    HalfClosing,
    TurnKind,
    closing_for,
    eye,
    loop_turns,
    max_closing,
    radial_bound,
    turn_table,
)
from embodic.geometry.details import TurnClosing
from embodic.model.winding_specs import SpiralCoilSpec

GOLDEN = json.loads((Path(__file__).parent / "fixtures" / "spiral_r2_turns.json").read_text())
TOL_MM = 1e-6


def _default_frame(via_pad_mm: float = 0.6) -> CoilFrame:
    coil = SpiralCoilSpec(
        coil_count=12, r_inner_mm=18.0, r_outer_mm=38.0, trace_width_mm=0.5, clearance_mm=0.2, coil_gap_mm=0.2
    )
    return CoilFrame.of(coil, via_pad_mm)


def _d08_frame(via_pad_mm: float = 0.6) -> CoilFrame:
    coil = SpiralCoilSpec(
        coil_count=12, r_inner_mm=11.47, r_outer_mm=45.03, trace_width_mm=2.06, clearance_mm=0.8, coil_gap_mm=0.8
    )
    return CoilFrame.of(coil, via_pad_mm)


FRAMES = {"CF-11": _default_frame(), "CF-10": _d08_frame(), "CF-10 pad 1.2": _d08_frame(1.2)}


@pytest.mark.req("REQ-F-06")
@pytest.mark.parametrize("case", list(FRAMES))
def test_turn_table_equals_reference_construction(case: str) -> None:
    """Catches a side on d_t+1 (the v1.0 inner-end step, D-028), a missing jog, or a wrong apex radius.

    Every per-turn radius and length equals the reference to 1e-6 mm.
    """
    frame, golden = FRAMES[case], GOLDEN[case]
    loops, _ = loop_turns(frame)
    closing = max_closing(frame, loops)
    assert closing is not None
    assert (len(loops), closing.kind.value, closing.n) == (golden["loop_turns"], golden["closing"], golden["n"])
    assert closing.centre_via[0] == pytest.approx(golden["r_v"], abs=TOL_MM)
    rows = turn_table(closing)
    assert len(rows) == len(golden["rows"])
    for row, ref in zip(rows, golden["rows"], strict=True):
        assert row.kind.value == ref["type"]
        got = (row.offset_mm, row.outer_radius_mm, row.end_radius_mm, row.jog_mm, row.outer_mm, row.right_mm)
        want = (ref["d_t"], ref["R_out"], ref["r_end"], ref["jog"], ref["outer"], ref["right"])
        assert got == pytest.approx(want, abs=TOL_MM)
        if ref["inner"] is None:
            assert row.inner_mm is None and row.left_mm is None
        else:
            assert (row.inner_mm, row.left_mm) == pytest.approx((ref["inner"], ref["left"]), abs=TOL_MM)


@pytest.mark.req("REQ-F-06")
def test_default_turn_table_matches_worked_example_1() -> None:
    """Worked example 1 printed values: 8 trapezoids and 3 triangles, apex radii 24.2978 and 27.0021, r_v 30.7."""
    frame = _default_frame()
    turns, _ = loop_turns(frame)
    assert [t.kind for t in turns] == [TurnKind.TRAPEZOID] * 8 + [TurnKind.TRIANGLE] * 3
    assert turns[8].end_radius_mm == pytest.approx(24.2978, abs=5e-5)
    assert turns[9].end_radius_mm == pytest.approx(27.0021, abs=5e-5)
    closing = max_closing(frame, turns)
    assert isinstance(closing, FullClosing) and closing.n == 10
    assert closing.eye.r_lo_mm == pytest.approx(28.5914, abs=5e-5)
    assert closing.eye.via_radius_mm == pytest.approx(30.7, abs=1e-9)


@pytest.mark.req("REQ-F-06")
def test_ut_geo_09_turn_limit_is_eye_limited_at_ten() -> None:
    """UT-GEO-09: N = 10 closes and N = 11 does not, by either closing (CF-11)."""
    frame = _default_frame()
    turns, _ = loop_turns(frame)
    assert eye(frame, turns, 10).fits and not eye(frame, turns, 11).fits
    assert closing_for(frame, turns, 11) is None
    assert radial_bound(frame) == pytest.approx(14.43, abs=5e-3)


@pytest.mark.eqt("EQT-25-CF10", "EQT-02-CF10")
@pytest.mark.req("REQ-F-06")
@pytest.mark.parametrize("pad", [0.6, 1.2])
def test_or_04_d08_builds_three_turns_with_the_half_closing(pad: float) -> None:
    """OR-04 and worked example 2: 3 loops (D08 Table 4.6 p.57); full closing fits 2, half closing 3, r_v 27.6255."""
    frame = _d08_frame(pad)
    turns, _ = loop_turns(frame)
    assert [t.kind for t in turns] == [TurnKind.TRAPEZOID, TurnKind.TRIANGLE, TurnKind.TRIANGLE]
    assert not eye(frame, turns, 3).fits and eye(frame, turns, 2).fits
    closing = max_closing(frame, turns)
    assert isinstance(closing, HalfClosing) and closing.kind is TurnClosing.HALF and closing.n == 3
    assert closing.centre_via[0] == pytest.approx(7.15 / math.sin(math.pi / 12), abs=1e-9)
    assert closing.centre_via[0] == pytest.approx(27.6255, abs=5e-5)
    assert radial_bound(frame) == pytest.approx(6.006993006993007, rel=1e-9)


@pytest.mark.req("REQ-F-06")
def test_full_closing_wins_at_equal_turns() -> None:
    """G5 choice: at N = 2 on D08 both closings fit, and the full one keeps the last left side."""
    frame = _d08_frame()
    turns, _ = loop_turns(frame)
    assert isinstance(closing_for(frame, turns, 2), FullClosing)


@pytest.mark.req("REQ-F-06")
def test_half_closing_refuses_a_pad_wider_than_the_trace() -> None:
    """G5 half-closing condition 4 (pad <= w): with a 2.2 mm pad D08 falls back to the full closing at N = 2."""
    frame = _d08_frame(2.2)
    closing = max_closing(frame, loop_turns(frame)[0])
    assert isinstance(closing, FullClosing) and closing.n <= 2


@pytest.mark.req("REQ-F-06")
def test_ut_geo_08_inner_end_radius_grows_once_sides_converge() -> None:
    """UT-GEO-08: the moving inner end-turn radius increases monotonically turn by turn (no self-intersection)."""
    for frame in (_default_frame(), _d08_frame()):
        turns, _ = loop_turns(frame)
        radii = [t.end_radius_mm for t in turns]
        assert all(b > a for a, b in pairwise(radii))
        assert all(t.outer_radius_mm > t.end_radius_mm for t in turns)


@pytest.mark.req("REQ-F-06")
def test_ut_geo_17_both_sides_of_a_turn_keep_offset_d_t() -> None:
    """UT-GEO-17 (parallel): B, C on the right line and D, A on the left line all sit at offset d_t (U-E3)."""
    frame = _default_frame()
    h = frame.half_angle_rad
    for t in loop_turns(frame)[0]:
        for x, y in (t.b, t.c):
            assert x * math.sin(h) + y * math.cos(h) == pytest.approx(t.offset_mm, abs=1e-9)
        for x, y in (t.a, t.d):
            assert x * math.sin(h) - y * math.cos(h) == pytest.approx(t.offset_mm, abs=1e-9)
