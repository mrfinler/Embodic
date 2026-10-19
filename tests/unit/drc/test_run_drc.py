"""UT-DRC-03 to UT-DRC-07 on hand-built layouts, rule validation, catalogue codes and cancellation."""

import math
import random
import threading
import warnings
from dataclasses import replace
from itertools import pairwise

import pytest

from embodic.api import compute
from embodic.drc import CancelToken, DrcCheckKind, DrcReport, run_drc
from embodic.errors import MESSAGES
from embodic.geometry.layout import Hole, Via, ViaRole
from embodic.geometry.paths import CopperPath
from embodic.geometry.primitives import PrimitiveRole
from embodic.io.examples import load_example
from embodic.io.project import project_from_example, project_provenance
from embodic.model.drc_rules import validate_drc_rules

from .layouts import RULES, arc, circle_outline, layout, line, pad, path, via

pytestmark = pytest.mark.req("REQ-F-10")


def _kinds(report: DrcReport) -> list[DrcCheckKind]:
    return [v.kind for v in report.violations]


def _turns(gap_mm: float, count: int = 4) -> list:
    """Concentric half-turn arcs of width 0.2 whose copper gap is ``gap_mm``, one path each."""
    return [path(i, [arc(0, 0, 5 + i * (0.2 + gap_mm), 0, math.pi)], net=f"N{i}") for i in range(count)]


def test_ut_drc_04_same_net_turns_closer_than_the_rule_are_a_violation() -> None:
    """Catches a same-net exemption: two turns of one spiral 0.199 mm apart under a 0.2 mm rule must fail."""
    spiral = path(0, [arc(0, 0, 5, 0, math.pi), line(-5, 0, -5, -2), arc(0, 0, 5.399, math.pi, -math.pi / 2)])
    report = run_drc(layout(paths=[spiral]), RULES)
    assert report is not None
    assert [(v.kind, v.objects) for v in report.violations] == [
        (DrcCheckKind.TRACE_TRACE, ("path:0/prim:0", "path:0/prim:2"))
    ]
    assert report.violations[0].clearance_mm == pytest.approx(0.199, abs=1e-12)


def test_ut_drc_04_adjacent_primitives_and_corner_fillets_are_exempt() -> None:
    """Catches a DRC that flags every joint: a line, a fillet and the next line meet at a corner, not a gap."""
    corner = path(
        0,
        [
            line(0, 0, 4.9, 0),
            replace(arc(4.9, 0.1, 0.1, -math.pi / 2, math.pi / 2), role=PrimitiveRole.FILLET),
            line(5, 0.1, 5, 4),
        ],
    )
    report = run_drc(layout(paths=[corner]), RULES)
    assert report is not None
    assert report.passed, report.violations


def test_ut_drc_04_fillet_is_checked_against_the_main_primitive_two_steps_back() -> None:
    """Catches DEF-M1V-01 (D-022 b): a fillet exempt from every main within one index of its own hides a tight U-turn.

    main0 east, fillet0 (r 0.05), main1 north 0.25 mm, fillet1 (r 0.5), main2 west, all 0.2 mm wide. fillet1 starts at
    (10.05, 0.30), 0.304 mm from main0's end (10, 0). fillet0 and fillet1 sit 0.25 mm apart along main1 and stay exempt.
    """
    hairpin = path(
        0,
        [
            line(0, 0, 10, 0),
            replace(arc(10, 0.05, 0.05, -math.pi / 2, math.pi / 2), role=PrimitiveRole.FILLET),
            line(10.05, 0.05, 10.05, 0.30),
            replace(arc(9.55, 0.30, 0.5, 0, math.pi / 2), role=PrimitiveRole.FILLET),
            line(9.55, 0.80, 0, 0.80),
        ],
    )
    report = run_drc(layout(paths=[hairpin]), RULES)
    assert report is not None
    assert [(v.kind, v.objects) for v in report.violations] == [
        (DrcCheckKind.TRACE_TRACE, ("path:0/prim:0", "path:0/prim:3"))
    ]
    assert report.violations[0].clearance_mm == pytest.approx(math.hypot(0.05, 0.30) - 0.2, abs=1e-12)


def test_ut_drc_04_terminating_via_is_exempt_but_a_foreign_via_is_not() -> None:
    """Catches a via exemption that is too wide (any via) or missing (the via the path ends on)."""
    lead = path(0, [line(0, 0, 3, 0)], net="A")
    own = via(0, 3, 0, net="A")
    foreign = via(1, 1.5, 0.4, net="B")
    report = run_drc(layout(paths=[lead], vias=[own, foreign]), RULES)
    assert report is not None
    assert {v.objects for v in report.violations} == {("path:0/prim:0", "via:1")}


def test_ut_drc_04_interconnect_ending_on_a_terminal_via_or_a_pad_is_a_joint_whatever_the_nets() -> None:
    """Catches DEF-M1z-01 (D-022 a): a lead (U) or star link (N) ending on a terminal via or a pad is not a short."""
    phase = path(0, [line(0, 0, 3, 0)], net="PHASE_A")
    lead = path(1, [line(3, 0, 3, 3)], net="U")
    star = path(2, [line(0, 10, 3, 10)], net="N")
    terminal = via(0, 3, 0, net="PHASE_A", role=ViaRole.TERMINAL)
    land = pad(0, 3, 10, net="U")
    board = layout(paths=[phase, lead, star], vias=[terminal], pads=[land], interconnects=[1, 2])
    report = run_drc(board, RULES)
    assert report is not None
    assert report.passed, report.violations


def test_ut_drc_04_other_phase_on_a_terminal_via_and_a_phase_path_on_another_net_pad_are_reported() -> None:
    """Catches an exemption that drops the net test for paths outside the circuit's interconnects."""
    stray = path(0, [line(0, 0, 3, 0)], net="PHASE_B")
    star = path(2, [line(0, 10, 3, 10)], net="N")
    terminal = via(0, 3, 0, net="PHASE_A", role=ViaRole.TERMINAL)
    land = pad(0, 3, 10, net="U")
    board = layout(paths=[stray, star], vias=[terminal], pads=[land])
    report = run_drc(board, RULES)
    assert report is not None
    assert {(v.kind, v.objects) for v in report.violations} == {
        (DrcCheckKind.TRACE_VIA, ("path:0/prim:0", "via:0")),
        (DrcCheckKind.PAD_TRACE, ("path:2/prim:0", "pad:0")),
    }


def _reversed(prims: list) -> list:
    """Return the same copper walked from the other end."""
    flipped = [
        replace(p, x1_mm=p.x2_mm, y1_mm=p.y2_mm, x2_mm=p.x1_mm, y2_mm=p.y1_mm)
        if hasattr(p, "x1_mm")
        else replace(p, start_rad=p.start_rad + p.sweep_rad, sweep_rad=-p.sweep_rad)
        for p in prims
    ]
    return flipped[::-1]


@pytest.mark.parametrize("walked_from_the_pad", [False, True], ids=["pad at the last end", "pad at the first end"])
def test_ut_drc_04_end_group_holds_the_fillet_next_to_the_terminating_main_at_either_end(
    walked_from_the_pad: bool,
) -> None:
    """Catches DEF-UV3-01: the fillet before the last main is not exempt from the pad the path ends on.

    main0 runs east along y = 0, a half-turn fillet (r 0.25) leads to main1, 0.3 mm long, west along y = 0.5, and the
    path ends on a 0.6 mm round pad at (3.7, 0.5). The fillet centreline ends on the pad outline, so only the end
    group exemption (section 7, rule 2) keeps it out of the report. main0 clears the pad by 0.1 mm and stays reported.
    """
    prims = [
        line(0, 0, 4, 0),
        replace(arc(4, 0.25, 0.25, -math.pi / 2, math.pi), role=PrimitiveRole.FILLET),
        line(4, 0.5, 3.7, 0.5),
    ]
    walk = _reversed(prims) if walked_from_the_pad else prims
    board = layout(paths=[path(0, walk, net="A")], pads=[pad(0, 3.7, 0.5, w=0.6, h=0.6, net="A")])
    report = run_drc(board, RULES)
    assert report is not None
    main0 = "path:0/prim:2" if walked_from_the_pad else "path:0/prim:0"
    assert [(v.kind, v.objects) for v in report.violations] == [(DrcCheckKind.PAD_TRACE, (main0, "pad:0"))]


def _ring_with_taps(net: str) -> tuple[CopperPath, list[Via]]:
    """Return an arc-plus-line ring on ``net`` and four vias of other nets that overlap its copper.

    Vias 0 and 1 sit on the centreline mid-primitive, via 2 on the far end, and via 3 lies 0.35 mm off the arc,
    beyond ``pad_mm / 2`` = 0.3 mm.
    """
    ring = path(0, [arc(0, 0, 5, 0, math.pi / 2), line(0, 5, -3, 5)], net=net)
    q = math.pi / 4
    taps = [
        via(0, 5 * math.cos(q), 5 * math.sin(q), net="PHASE_A"),
        via(1, -1.5, 5, net="PHASE_B", role=ViaRole.CENTRE),
        via(2, -3, 5, net="PHASE_C"),
        via(3, 5.35 * math.cos(q / 2), 5.35 * math.sin(q / 2), net="PHASE_C"),
    ]
    return ring, taps


def test_ut_drc_04_interconnect_tapped_mid_path_by_vias_of_any_net_and_role_is_a_joint() -> None:
    """Catches DEF-M1c3-01 (D-022c): a star-point ring tapped by a via mid-path, or ending on one, is not a short.

    A via whose centre is off the centreline is still a short, so an exemption by copper overlap would be too wide.
    """
    ring, taps = _ring_with_taps("N")
    report = run_drc(layout(paths=[ring], vias=taps, interconnects=[0]), RULES)
    assert report is not None
    assert {(v.kind, v.objects) for v in report.violations} == {(DrcCheckKind.TRACE_VIA, ("path:0/prim:0", "via:3"))}


def test_ut_drc_04_via_on_a_non_interconnect_path_of_another_net_is_reported() -> None:
    """Catches a tap exemption that ignores whether the path is an interconnect: a phase path keeps the net test."""
    ring, taps = _ring_with_taps("PHASE_D")
    report = run_drc(layout(paths=[ring], vias=taps), RULES)
    assert report is not None
    assert {(v.kind, v.objects) for v in report.violations} == {
        (DrcCheckKind.TRACE_VIA, ("path:0/prim:0", "via:0")),
        (DrcCheckKind.TRACE_VIA, ("path:0/prim:1", "via:1")),
        (DrcCheckKind.TRACE_VIA, ("path:0/prim:1", "via:2")),
        (DrcCheckKind.TRACE_VIA, ("path:0/prim:0", "via:3")),
    }


def _trunk_with_via_on_its_centreline(shape: str, via_net: str) -> tuple[CopperPath, Via]:
    """Return a net A path of one primitive and a via of ``via_net`` centred on that primitive's centreline."""
    if shape == "line":
        return path(0, [line(-5, 0, 5, 0)], net="A"), via(0, 0, 0, net=via_net)
    q = math.pi / 4
    return path(0, [arc(0, 0, 5, 0, math.pi)], net="A"), via(0, 5 * math.cos(q), 5 * math.sin(q), net=via_net)


@pytest.mark.parametrize("shape", ["line", "arc"])
def test_ut_drc_04_same_net_via_on_a_path_centreline_is_exempt_from_that_primitive(shape: str) -> None:
    """Catches D-036 a missing: a terminal via mid-bus is reported against the bus it sits on."""
    trunk, tap = _trunk_with_via_on_its_centreline(shape, via_net="A")
    report = run_drc(layout(paths=[trunk], vias=[tap]), RULES)
    assert report is not None
    assert report.passed, report.violations


@pytest.mark.parametrize("shape", ["line", "arc"])
def test_ut_drc_04_via_of_another_net_on_a_path_centreline_is_reported(shape: str) -> None:
    """Catches a tap exemption that drops the net test: the same geometry on net B is a short."""
    trunk, tap = _trunk_with_via_on_its_centreline(shape, via_net="B")
    report = run_drc(layout(paths=[trunk], vias=[tap]), RULES)
    assert report is not None
    assert [(v.kind, v.objects) for v in report.violations] == [(DrcCheckKind.TRACE_VIA, ("path:0/prim:0", "via:0"))]


def test_ut_drc_04_same_net_via_tap_leaves_a_far_primitive_of_the_same_path_checked() -> None:
    """Catches D-037a: a tap exempts the whole path, so a turn of the path that passes too close to the via goes unseen.

    main0 runs through the via at (0, 0) and is exempt. main2 returns 0.5 mm away on the same net and path, clearing
    the via by 0.1 mm against a 0.2 mm rule, and stays reported. main0 and main2 are 0.3 mm apart and pass.
    """
    uturn = path(0, [line(-5, 0, 5, 0), line(5, 0, 5, 0.5), line(5, 0.5, -5, 0.5)], net="A")
    report = run_drc(layout(paths=[uturn], vias=[via(0, 0, 0, net="A")]), RULES)
    assert report is not None
    assert [(v.kind, v.objects) for v in report.violations] == [(DrcCheckKind.TRACE_VIA, ("path:0/prim:2", "via:0"))]
    assert report.violations[0].clearance_mm == pytest.approx(0.1, abs=1e-12)


@pytest.mark.parametrize(
    ("offset_mm", "reported"), [(0.29, False), (0.31, True)], ids=["inside the band", "0.01 mm outside the band"]
)
def test_ut_drc_04_same_net_via_tap_band_is_half_the_via_pad(offset_mm: float, reported: bool) -> None:
    """Catches a tap band that grows into slack: with pad_mm = 0.6 a via 0.31 mm off the centreline overlaps."""
    trunk = path(0, [line(-5, 0, 5, 0)], net="A")
    report = run_drc(layout(paths=[trunk], vias=[via(0, 0, offset_mm, net="A")]), RULES)
    assert report is not None
    assert [(v.kind, v.objects) for v in report.violations] == (
        [(DrcCheckKind.TRACE_VIA, ("path:0/prim:0", "via:0"))] if reported else []
    )


def _junction_violations(branch: CopperPath, trunk: CopperPath) -> set[tuple[DrcCheckKind, tuple[str, ...]]]:
    report = run_drc(layout(paths=[trunk, branch]), RULES)
    assert report is not None
    return {(v.kind, v.objects) for v in report.violations}


@pytest.mark.parametrize("offset_mm", [0.0, 5e-7])
def test_ut_drc_04_path_end_on_the_middle_of_a_line_of_a_same_net_path_is_a_junction(offset_mm: float) -> None:
    """Catches D-035 b missing: a strand ending on the middle of a bus is reported against the bus (case 5a).

    The branch ends on the centreline of the trunk's line, within COINCIDENCE_MM of it.
    """
    trunk = path(0, [line(-5, 0, 5, 0)], net="A")
    branch = path(1, [line(0, 4, 0, offset_mm)], net="A")
    assert _junction_violations(branch, trunk) == set()


def test_ut_drc_04_path_start_on_the_middle_of_an_arc_of_a_same_net_path_is_a_junction() -> None:
    """Catches a T-junction test that handles line trunks and path ends only: a start on an arc mid-path (case 5b)."""
    trunk = path(0, [arc(0, 0, 5, 0, math.pi)], net="A")
    branch = path(1, [line(0, 5, 0, 2)], net="A")
    assert _junction_violations(branch, trunk) == set()


def test_ut_drc_04_path_end_on_a_path_of_another_net_is_reported() -> None:
    """Catches a T-junction exemption that drops the net test: a different-net end on the middle of a line (5c)."""
    trunk = path(0, [line(-5, 0, 5, 0)], net="A")
    branch = path(1, [line(0, 4, 0, 0)], net="B")
    assert _junction_violations(branch, trunk) == {(DrcCheckKind.TRACE_TRACE, ("path:0/prim:0", "path:1/prim:0"))}


@pytest.mark.parametrize("offset_mm", [2e-6, 0.01])
def test_ut_drc_04_path_end_beyond_the_coincidence_tolerance_is_reported(offset_mm: float) -> None:
    """Catches a T-junction tolerance that grows into slack: an end 0.01 mm off the trunk is a real overlap (5d)."""
    trunk = path(0, [line(-5, 0, 5, 0)], net="A")
    branch = path(1, [line(0, 4, 0, offset_mm)], net="A")
    assert _junction_violations(branch, trunk) == {(DrcCheckKind.TRACE_TRACE, ("path:0/prim:0", "path:1/prim:0"))}


def test_ut_drc_04_only_the_end_group_on_the_trunk_is_exempt() -> None:
    """Catches an exemption of the whole branch: its start sits on the trunk, its other end stops 0.15 mm short (5e)."""
    trunk = path(0, [line(-5, 0, 5, 0)], net="A")
    branch = path(1, [line(0, 0, 0, 2), line(0, 2, 3, 2), line(3, 2, 3, 0.15)], net="A")
    assert _junction_violations(branch, trunk) == {(DrcCheckKind.TRACE_TRACE, ("path:0/prim:0", "path:1/prim:2"))}


def test_ut_drc_04_junction_end_group_is_exempt_from_the_whole_trunk_path() -> None:
    """Catches an exemption limited to the primitive the end lies on: the trunk turns 0.05 mm past the end (5f).

    The branch ends at (-0.05, 0) on the first trunk line; the second trunk line starts 0.05 mm further on.
    """
    trunk = path(0, [line(-5, 0, 0, 0), line(0, 0, 0, -5)], net="A")
    branch = path(1, [line(-0.05, 4, -0.05, 0)], net="A")
    assert _junction_violations(branch, trunk) == set()


_HOOK = [(0.0, 0.0), (0.0, 2.0), (4.0, 2.0), (4.0, 5.0)]


def _hook_and_branch(net: str, *, junction_at_start: bool) -> tuple[CopperPath, CopperPath]:
    """Return a three-line trunk and a one-line branch that ends on one of the trunk's two end points.

    The branch runs from (0.5, 1.8) to the trunk end point (0, 0). Its centreline stays 0.2 mm from the trunk's middle
    line, so the edge-to-edge clearance is 0, and that line is outside the trunk's end group at (0, 0).
    """
    points = _HOOK if junction_at_start else _HOOK[::-1]
    trunk = path(0, [line(*a, *b) for a, b in pairwise(points)], net="A")
    branch = path(1, [line(0.5, 1.8, 0.0, 0.0)], net=net)
    return trunk, branch


@pytest.mark.parametrize("junction_at_start", [True, False], ids=["trunk-start", "trunk-end"])
def test_ut_drc_04_path_end_on_an_end_point_of_a_same_net_path_is_exempt_from_every_primitive_of_it(
    junction_at_start: bool,
) -> None:
    """Catches a T-junction test that skips the other path's end points (end-point reading, case 5g).

    Rule 3 exempts the branch only from the trunk's end group. The trunk's middle line is 0.2 mm from the branch
    centreline, so only rule 5 (the centreline includes its end points, interfaces.md section 7) exempts that pair.
    """
    trunk, branch = _hook_and_branch("A", junction_at_start=junction_at_start)
    assert _junction_violations(branch, trunk) == set()


@pytest.mark.parametrize(
    ("junction_at_start", "touched", "middle"),
    [(True, "path:0/prim:0", "path:0/prim:1"), (False, "path:0/prim:2", "path:0/prim:1")],
    ids=["trunk-start", "trunk-end"],
)
def test_ut_drc_04_the_same_end_point_geometry_on_different_nets_is_reported(
    junction_at_start: bool, touched: str, middle: str
) -> None:
    """Catches an end-point exemption that drops the net test: the 5g geometry on nets A and B is reported (5h)."""
    trunk, branch = _hook_and_branch("B", junction_at_start=junction_at_start)
    assert _junction_violations(branch, trunk) == {
        (DrcCheckKind.TRACE_TRACE, (touched, "path:1/prim:0")),
        (DrcCheckKind.TRACE_TRACE, (middle, "path:1/prim:0")),
    }


@pytest.mark.eqt("EQT-30-UT1")
def test_ut_drc_03_one_micron_intrusion_is_exactly_one_new_violation_at_its_place() -> None:
    """Catches slack in the rule (Xcoil's 0.004 mm) or epsilon 0: rule - 1 um fails, the rule itself passes."""
    clean = run_drc(layout(paths=_turns(0.2)), RULES)
    assert clean is not None and clean.passed
    moved = _turns(0.2)
    moved[2] = path(2, [arc(0, 0, 5 + 2 * 0.4 - 0.001, 0, math.pi)], net="N2")
    report = run_drc(layout(paths=moved), RULES)
    assert report is not None
    assert [v.objects for v in report.violations] == [("path:1/prim:0", "path:2/prim:0")]
    (hit,) = report.violations
    assert hit.clearance_mm == pytest.approx(0.199, abs=1e-12)
    assert math.hypot(*hit.at_mm) == pytest.approx(5.4 + 0.1 + 0.0995, abs=1e-9)


@pytest.mark.eqt("EQT-30-UT1")
def test_ut_drc_03_inside_epsilon_passes() -> None:
    """Catches an epsilon above 1e-6 mm turned into a hidden slack: 0.9 um below the rule still passes."""
    report = run_drc(layout(paths=_turns(0.2 - 0.9e-6, count=2)), RULES)
    assert report is not None and report.passed


@pytest.mark.eqt("EQT-30-UT1")
@pytest.mark.parametrize(
    ("side", "violations"), [(-1, 1), (0, 0), (1, 0)], ids=["8.9e-17 mm closer", "exactly rule - epsilon", "further"]
)
def test_ut_drc_03_the_float_boundary_of_d006_is_rule_minus_epsilon_and_equal_passes(
    side: int, violations: int
) -> None:
    """Catches DEF-UV15-01 (V3-02-09): a clearance of exactly 0.2 - 1e-6 mm passes and one 8.9e-17 mm closer fails.

    Two 0.2 mm traces on nets A and B; the second sits so that the least clearance is the float 0.2 - 1e-6 for side 0
    and one step either side of it for side -1 and 1 (D-006: a violation is clearance < rule - epsilon, strictly).
    """
    boundary_mm = RULES.trace_clearance_mm - 1e-6
    y = boundary_mm + 0.2 + side * 2**-52 * 0.4
    traces = [path(0, [line(-5, 0, 5, 0)], net="A"), path(1, [line(-5, y, 5, y)], net="B")]
    report = run_drc(layout(paths=traces), RULES)
    assert report is not None
    least = report.summaries[0].least_clearance_mm
    assert least is not None
    assert (least > boundary_mm) - (least < boundary_mm) == side, "the layout sits on the boundary it names"
    assert len(report.violations) == violations


def test_ut_drc_05_through_via_is_checked_against_copper_on_every_layer() -> None:
    """Catches a via checked on its own layer pair only: copper on B.Cu near a through via must fail."""
    bottom = path(0, [line(-2, 0.5, 2, 0.5)], layer="B.Cu", net="B")
    report = run_drc(layout(paths=[bottom], vias=[via(0, 0, 0, net="A")]), RULES)
    assert report is not None
    (hit,) = report.violations
    assert (hit.kind, hit.layer, hit.objects) == (DrcCheckKind.TRACE_VIA, "B.Cu", ("path:0/prim:0", "via:0"))
    assert hit.clearance_mm == pytest.approx(0.5 - 0.3 - 0.1, abs=1e-12)


def test_ut_drc_06_copper_near_the_board_edge_and_a_screw_hole_fails() -> None:
    """Catches missing edge and hole checks (REQ-F-09, REQ-F-24): both report with their own rule."""
    near_edge = path(0, [line(9.0, 0, 9.65, 0)], net="A")
    near_hole = path(1, [line(-4, -1, -4, 1)], net="B")
    hole = Hole(x_mm=-5, y_mm=0, diameter_mm=1.4, label="M1.2 normal")
    report = run_drc(layout(paths=[near_edge, near_hole], outer=circle_outline(10), holes=[hole]), RULES)
    assert report is not None
    found = {v.kind: v.clearance_mm for v in report.violations}
    assert found == pytest.approx({DrcCheckKind.COPPER_EDGE: 0.25, DrcCheckKind.COPPER_HOLE: 0.2}, abs=1e-12)
    required = {v.kind: v.required_mm for v in report.violations}
    assert required == {DrcCheckKind.COPPER_EDGE: 0.3, DrcCheckKind.COPPER_HOLE: 0.4}


def test_ut_drc_06_edge_ids_name_the_outer_loop_or_the_cutout() -> None:
    """Catches DEF-M1V-05: edge ids are ``edge:outer/prim:k`` and ``edge:cutout<n>/prim:k``, not ``edge:<n>/prim:k``."""
    near_outer = path(0, [line(9.0, 0, 9.65, 0)], net="A")
    near_cutout = path(1, [line(-1, 1.6, 1, 1.6)], net="B")
    board = layout(paths=[near_outer, near_cutout], outer=circle_outline(10), cutouts=[circle_outline(1.5)])
    report = run_drc(board, RULES)
    assert report is not None
    assert {v.objects for v in report.violations} == {
        ("path:0/prim:0", "edge:outer/prim:0"),
        ("path:1/prim:0", "edge:cutout0/prim:0"),
    }


@pytest.mark.req("REQ-F-09", "REQ-F-24")
def test_ut_drc_06_copper_clear_of_edge_and_hole_passes() -> None:
    """Catches an edge check that measures to the board centre or a hole check that ignores the hole radius."""
    report = run_drc(
        layout(
            paths=[path(0, [line(-2, 0, 2, 0)])],
            outer=circle_outline(10),
            holes=[Hole(x_mm=5, y_mm=0, diameter_mm=1, label="x")],
        ),
        RULES,
    )
    assert report is not None and report.passed


def test_ut_drc_07_manufacturing_minima_are_reported() -> None:
    """Catches unchecked width, drill or annular ring: each undersized object reports once with its rule."""
    thin = path(0, [line(0, 0, 2, 0, w=0.149)])
    small = via(0, 10, 10, pad=0.45, drill=0.29)
    report = run_drc(layout(paths=[thin], vias=[small]), RULES)
    assert report is not None
    assert {(v.kind, v.objects) for v in report.violations} == {
        (DrcCheckKind.MIN_WIDTH, ("path:0/prim:0",)),
        (DrcCheckKind.MIN_DRILL, ("via:0",)),
        (DrcCheckKind.ANNULAR_RING, ("via:0",)),
    }
    assert report.violation_count == 3


def test_pad_pad_and_pad_trace_use_xcoil_pad_kernels() -> None:
    """Catches a rectangle pad measured as a circle against a trace, or pads that skip the pad-pad check."""
    rect = pad(0, 0, 0, shape="rect", w=2, h=1, net="U")
    near = pad(1, 1.8, 0, shape="round", w=1, h=1, net="V")
    trace = path(0, [line(-1, 0.65, 1, 0.65)], net="B")
    report = run_drc(layout(paths=[trace], pads=[rect, near]), RULES)
    assert report is not None
    found = {v.kind: v.clearance_mm for v in report.violations}
    assert found[DrcCheckKind.PAD_TRACE] == pytest.approx(0.05, abs=1e-12)
    assert found[DrcCheckKind.PAD_PAD] == pytest.approx(1.8 - math.hypot(2, 1) / 2 - 0.5, abs=1e-12)


def test_summaries_cover_every_applicable_kind_and_no_other() -> None:
    """Catches a summary list that drops a check kind the layout has objects for, or invents one it cannot have."""
    report = run_drc(
        layout(paths=_turns(0.3, count=2), vias=[via(0, 20, 0), via(1, 22, 0)], outer=circle_outline(30)), RULES
    )
    assert report is not None
    assert {s.kind for s in report.summaries} == {
        DrcCheckKind.TRACE_TRACE,
        DrcCheckKind.TRACE_VIA,
        DrcCheckKind.VIA_VIA,
        DrcCheckKind.COPPER_EDGE,
        DrcCheckKind.MIN_WIDTH,
        DrcCheckKind.MIN_DRILL,
        DrcCheckKind.ANNULAR_RING,
    }
    assert all(s.pairs_checked > 0 for s in report.summaries if s.kind is DrcCheckKind.TRACE_TRACE)


@pytest.fixture(scope="module")
def wave_outcome():
    """Return the computed wave example, whose board fails DRC with 186 violations (D-045g)."""
    project = project_from_example(load_example("wave_16p_example"))
    return compute(project.design, project_provenance(project))


@pytest.mark.parametrize("seed", [None, 7], ids=["reversed", "shuffled"])
def test_violation_order_is_canonical_whatever_the_order_of_paths_and_vias(wave_outcome, seed: int | None) -> None:
    """Catches DEF-W-01: the 186 wave violations came out in another order on Windows.

    The list must follow (kind, layer, objects), so neither the input order nor float noise in the clearances moves it.
    """
    board = wave_outcome.boards.boards[0]
    paths, vias = list(board.paths), list(board.vias)
    if seed is None:
        paths.reverse()
        vias.reverse()
    else:
        random.Random(seed).shuffle(paths)
        random.Random(seed).shuffle(vias)
    report = run_drc(replace(board, paths=tuple(paths), vias=tuple(vias)), wave_outcome.design.drc_rules)
    assert report is not None
    expected = [(v.kind, v.layer, v.objects) for v in wave_outcome.drc[0].violations]
    assert len(expected) == len(set(expected)) == 186
    assert [kind for kind, _, _ in expected] == [DrcCheckKind.TRACE_TRACE] * 6 + [DrcCheckKind.TRACE_VIA] * 180
    assert [(v.kind, v.layer, v.objects) for v in report.violations] == expected


def test_every_check_kind_has_a_catalogue_message() -> None:
    """Catches a new DrcCheckKind without an English message: the issue layer would raise KeyError."""
    assert all(kind.issue_code in MESSAGES for kind in DrcCheckKind)


@pytest.mark.parametrize("bad", [math.nan, math.inf, -0.1])
def test_drc_rules_validation_refuses_non_finite_and_negative_values(bad: float) -> None:
    """Catches a NaN or negative rule reaching run_drc, where every comparison would pass silently."""
    (issue,) = validate_drc_rules(replace(RULES, via_clearance_mm=bad))
    assert issue.pointers == ("/drc_rules/via_clearance_mm",)
    assert issue.code in MESSAGES
    assert validate_drc_rules(RULES) == ()


def test_cancel_token_returns_none_promptly() -> None:
    """Catches a cancel flag that is never read: a cancelled run must return None, not a report."""
    token = CancelToken()
    token.cancel()
    assert run_drc(layout(paths=_turns(0.2)), RULES, cancel=token) is None


class _FlippedByAnotherThread(CancelToken):
    """Counts reads and, at the k-th read, has another thread call ``cancel`` and waits for it (no clock involved)."""

    def __init__(self, k: int | None) -> None:
        super().__init__()
        self.k, self.reads = k, 0

    @property
    def cancelled(self) -> bool:
        """Return whether the token is cancelled, flipping it from a second thread at read ``k``."""
        self.reads += 1
        if self.reads == self.k:
            flipper = threading.Thread(target=self.cancel)
            flipper.start()
            flipper.join()
        return super().cancelled


def test_cancel_from_another_thread_stops_a_long_run() -> None:
    """Catches a token read only before the run starts: a cancel mid-run must return None and stop reading.

    The run polls the token between stages and chunks (section 5.5 rule 1). An uncancelled run sets the read count;
    cancelling at its middle read must stop right there, so the token is read exactly that often and no more.
    """
    many = [path(i, [line(0, 0.5 * i, 200, 0.5 * i)], net=f"N{i}") for i in range(200)]
    board = layout(paths=many)
    full = _FlippedByAnotherThread(None)
    assert run_drc(board, RULES, cancel=full) is not None
    assert full.reads >= 3, "the run must poll the token more than once to have a middle"
    middle = full.reads // 2
    token = _FlippedByAnotherThread(middle)
    assert run_drc(board, RULES, cancel=token) is None
    assert token.reads == middle


_TOUCHING = [path(1, [line(0, 0, 0, 1)], net="A"), path(2, [line(0.3, 0, 0.3, 1)], net="B")]


@pytest.mark.parametrize("far_mm", [1e30, 1e20])
def test_a_coordinate_whose_grid_cell_index_is_not_representable_is_refused_by_name(far_mm: float) -> None:
    """Catches DEF-M7a-01: floor(x / cell) of a 1e30 mm item was cast to int64 as garbage and the cell key overflowed.

    The run must stop with the broad phase's own error, before numpy warns about the cast.
    """
    board = layout(paths=[*_TOUCHING, path(3, [line(far_mm, 0, far_mm, 1)], net="C")])
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with pytest.raises(OverflowError, match="DRC grid cell index"):
            run_drc(board, RULES)


def test_items_on_the_largest_supported_board_keep_their_grid_and_violations() -> None:
    """Catches a grid guard tighter than the outline maximum: copper 2000 mm out still finds the 0.1 mm overlap."""
    edge = [path(4, [line(2000, 0, 2000, 1)], net="C"), path(5, [line(-2000, 0, -2000, 1)], net="D")]
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        report = run_drc(layout(paths=[*_TOUCHING, *edge]), RULES)
    assert report is not None
    assert [(v.kind, v.objects) for v in report.violations] == [
        (DrcCheckKind.TRACE_TRACE, ("path:1/prim:0", "path:2/prim:0"))
    ]
