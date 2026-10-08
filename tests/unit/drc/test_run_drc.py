"""UT-DRC-03 to UT-DRC-07 on hand-built layouts, rule validation, catalogue codes and cancellation."""

import math
import threading
from dataclasses import replace

import pytest

from embodic.drc import CancelToken, DrcCheckKind, DrcReport, run_drc
from embodic.errors import MESSAGES
from embodic.geometry.layout import Hole, Via, ViaRole
from embodic.geometry.paths import CopperPath
from embodic.geometry.primitives import PrimitiveRole
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
    assert report.violations[0].measured_mm == pytest.approx(0.199, abs=1e-12)


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
    assert report.violations[0].measured_mm == pytest.approx(math.hypot(0.05, 0.30) - 0.2, abs=1e-12)


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
    assert hit.measured_mm == pytest.approx(0.199, abs=1e-12)
    assert math.hypot(*hit.at_mm) == pytest.approx(5.4 + 0.1 + 0.0995, abs=1e-9)


def test_ut_drc_03_inside_epsilon_passes() -> None:
    """Catches an epsilon above 1e-6 mm turned into a hidden slack: 0.9 um below the rule still passes."""
    report = run_drc(layout(paths=_turns(0.2 - 0.9e-6, count=2)), RULES)
    assert report is not None and report.passed


def test_ut_drc_05_through_via_is_checked_against_copper_on_every_layer() -> None:
    """Catches a via checked on its own layer pair only: copper on B.Cu near a through via must fail."""
    bottom = path(0, [line(-2, 0.5, 2, 0.5)], layer="B.Cu", net="B")
    report = run_drc(layout(paths=[bottom], vias=[via(0, 0, 0, net="A")]), RULES)
    assert report is not None
    (hit,) = report.violations
    assert (hit.kind, hit.layer, hit.objects) == (DrcCheckKind.TRACE_VIA, "B.Cu", ("path:0/prim:0", "via:0"))
    assert hit.measured_mm == pytest.approx(0.5 - 0.3 - 0.1, abs=1e-12)


def test_ut_drc_06_copper_near_the_board_edge_and_a_screw_hole_fails() -> None:
    """Catches missing edge and hole checks (REQ-F-09, REQ-F-24): both report with their own rule."""
    near_edge = path(0, [line(9.0, 0, 9.65, 0)], net="A")
    near_hole = path(1, [line(-4, -1, -4, 1)], net="B")
    hole = Hole(x_mm=-5, y_mm=0, diameter_mm=1.4, label="M1.2 normal")
    report = run_drc(layout(paths=[near_edge, near_hole], outer=circle_outline(10), holes=[hole]), RULES)
    assert report is not None
    found = {v.kind: v.measured_mm for v in report.violations}
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
    found = {v.kind: v.measured_mm for v in report.violations}
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
