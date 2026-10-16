"""Screw holes on the spiral board (REQ-F-24, UT-GEO-21): placed from the patterns, keep-outs refused or reported.

CF-11 has copper from r_inner 18 mm (inner end of turn 0 at R_i0 18.25 mm, width 0.5 mm) and a 12.5 mm bore, so six
3.4 mm holes on the 15.9 mm pitch circle on the coil axes leave 18 - 15.9 - 1.7 = 0.4 mm to the copper and
15.9 - 1.7 - 12.5 = 1.7 mm to the bore (closed form; hole and edge clearance rules 0.3 mm).
"""

import dataclasses
import math

import pytest
from tests.unit.generators.default_example import default_design

from embodic.drc import run_drc
from embodic.drc.report import DrcCheckKind
from embodic.errors import Unbuildable
from embodic.generators import generate_spiral
from embodic.geometry.layout import BoardStack
from embodic.model.design import DesignParameters
from embodic.model.outline import ScrewFit, ScrewPattern
from embodic.model.winding_specs import SpiralWindingSpec
from embodic.results import load_registry


def _with_screws(pitch_radius_mm: float) -> DesignParameters:
    design = default_design()
    assert isinstance(design.winding, SpiralWindingSpec)
    pattern = ScrewPattern(
        size="M3", fit=ScrewFit.NORMAL, count=6, pitch_radius_mm=pitch_radius_mm, hole_diameter_mm=3.4,
        angle_offset_rad=design.winding.coil.first_coil_angle_rad,
    )  # fmt: skip
    return dataclasses.replace(design, outline=dataclasses.replace(design.outline, screws=(pattern,)))


@pytest.mark.req("REQ-F-24")
def test_ut_geo_21_screw_holes_are_built_on_the_pitch_circle_clear_of_copper() -> None:
    """Six holes at 60 degree steps with the entered diameter; DRC copper-to-hole gap 0.4 mm, no violation.

    Catches `/outline/screws` still refused, holes dropped from the outline, or a hole the DRC never checks.
    """
    design = _with_screws(15.9)
    stack = generate_spiral(design, load_registry())
    assert isinstance(stack, BoardStack), stack
    board = stack.boards[0]
    assert [h.diameter_mm for h in board.outline.holes] == [3.4] * 6
    assert {round(math.hypot(h.x_mm, h.y_mm), 9) for h in board.outline.holes} == {15.9}
    report = run_drc(board, design.drc_rules)
    assert report is not None and report.violation_count == 0
    least = {s.kind: s.least_clearance_mm for s in report.summaries}
    assert least[DrcCheckKind.COPPER_HOLE] == pytest.approx(0.4, abs=1e-6)


@pytest.mark.req("REQ-F-24")
def test_ut_geo_21_a_hole_over_copper_is_a_drc_copper_hole_violation() -> None:
    """Holes on the 17 mm pitch circle reach 18.7 mm, 0.7 mm into the turn-0 copper: the DRC reports it.

    Catches a copper keep-out that the board passes silently (D-006: violation below rule - epsilon).
    """
    design = _with_screws(17.0)
    stack = generate_spiral(design, load_registry())
    assert isinstance(stack, BoardStack), stack
    report = run_drc(stack.boards[0], design.drc_rules)
    assert report is not None and report.violation_count > 0
    assert {v.kind for v in report.violations} == {DrcCheckKind.COPPER_HOLE}
    least = {s.kind: s.least_clearance_mm for s in report.summaries}
    assert least[DrcCheckKind.COPPER_HOLE] == pytest.approx(18.0 - 18.7, abs=1e-6)


@pytest.mark.req("REQ-F-24")
def test_ut_geo_21_a_hole_across_the_bore_is_refused_with_its_pattern_pointers() -> None:
    """Holes on the 13 mm pitch circle reach 11.3 mm, inside the 12.5 mm bore: UNBUILDABLE_SCREW_HOLE_EDGE.

    Catches a hole cut through the bore edge, or the refusal pointing at the wrong input.
    """
    refused = generate_spiral(_with_screws(13.0), load_registry())
    assert isinstance(refused, Unbuildable)
    assert [(i.code, i.pointers) for i in refused.issues] == [
        ("UNBUILDABLE_SCREW_HOLE_EDGE", ("/outline/screws/0/pitch_radius_mm", "/outline/screws/0/hole_diameter_mm"))
    ]


@pytest.mark.req("REQ-N-04")
def test_same_design_with_screws_gives_the_same_stack_hash_and_holes_change_it() -> None:
    """Determinism (generators/base.py): two runs give one stack_hash; moving the holes gives another.

    Catches a hash that leaves the holes out, or nondeterministic hole order.
    """
    registry = load_registry()
    first, again, moved = (generate_spiral(_with_screws(r), registry) for r in (15.9, 15.9, 15.5))
    assert isinstance(first, BoardStack) and isinstance(again, BoardStack) and isinstance(moved, BoardStack)
    assert first.stack_hash == again.stack_hash
    assert moved.stack_hash != first.stack_hash
