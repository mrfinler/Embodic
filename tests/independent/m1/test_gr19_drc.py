"""U-V1 part 2 on the three GR-19 Xcoil layouts: minima inside own brackets, violation classes, injected faults."""

import dataclasses
import json
import math
from functools import cache
from typing import Any

import pytest
from board_dump_reader import parse_board_dump
from brute_clearance import DRC_EPSILON_MM, Verdict, bounding_boxes, clearance_bracket
from continuity import first_gap
from drc_universe import Item, PairResult, Rule, contract_exemptions, sweep
from embodic_adapter import pair_violations, uniform_rules
from gr19 import WAIVER, Board, boards, classify, universe, violations
from records import Line

from embodic.drc import DrcReport, run_drc
from embodic.io.board_dump import dump_layout, encode_board_dump

pytestmark = pytest.mark.req("REQ-F-40")

RULE_MM = 0.2
REACH_MM = 0.05


@cache
def _boards() -> dict[str, Board]:
    return {b.case_id: b for b in boards()}


@cache
def _report(case_id: str) -> DrcReport:
    report = run_drc(_boards()[case_id].layout, uniform_rules(RULE_MM))
    assert report is not None
    return report


@cache
def _mapped_sweep(case_id: str) -> list[PairResult]:
    """Decided sweep with run_drc's nets and the contract exemptions: every pair below the rule, verdict known."""
    board = _boards()[case_id]
    exempt = contract_exemptions(board.as_mapped, board.interconnect)
    return sweep(board.as_mapped, range(len(board.dump.layers)), lambda kind: RULE_MM, exempt)


@cache
def _intended_violations(case_id: str) -> dict[frozenset[str], PairResult]:
    board = _boards()[case_id]
    exempt = contract_exemptions(board.intended, board.interconnect)
    return violations(sweep(board.intended, range(len(board.dump.layers)), lambda kind: RULE_MM, exempt))


CASES = ["layout-sector-default", "layout-serpentine-default", "layout-wave-turns-2"]


def test_three_topologies_and_xcoil_clearance() -> None:
    """The rules below assume Xcoil's single 0.2 mm clearance; catch a fixture regenerated with another value."""
    assert sorted(_boards()) == CASES
    assert {b.raw["params"]["clearance"] for b in _boards().values()} == {RULE_MM}


@pytest.mark.parametrize("case_id", CASES)
def test_dump_geometry_equals_raw_xcoil_records(case_id: str) -> None:
    """Catches a mapper or writer that reorders, drops or alters primitives: compared with the raw Xcoil records."""
    board = _boards()[case_id]
    raw_prims = [r for layer in board.raw["layers"] for obj in layer["objs"] for r in obj["prims"]]
    assert len(raw_prims) == len(board.dump.primitives)
    for rec, got in zip(raw_prims, board.dump.primitives, strict=True):
        p = got.prim
        if isinstance(p, Line):
            assert (rec["type"], p.x1, p.y1, p.x2, p.y2) == ("line", rec["x1"], rec["y1"], rec["x2"], rec["y2"])
        else:
            assert (rec["type"], p.cx, p.cy, p.r, p.start) == ("arc", rec["cx"], rec["cy"], rec["r"], rec["a1"])
            assert math.isclose(p.sweep, rec["a2"] - rec["a1"], rel_tol=0.0, abs_tol=1e-12)
        assert p.width == rec["width"]


@pytest.mark.parametrize("case_id", CASES)
def test_every_dumped_object_is_a_continuous_path(case_id: str) -> None:
    """CopperPath is a continuous chain (interfaces.md section 5); a broken object fakes same-path violations."""
    board = _boards()[case_id]
    gaps = {oid: first_gap([p.prim for p in prims]) for oid, prims in board.dump.paths.items()}
    assert {oid: g for oid, g in gaps.items() if g is not None} == {}


def test_interconnect_objects_are_cut_only_at_their_gaps() -> None:
    """Catch a split that also cuts joined stubs, or none at all: Xcoil's 7 / 5 / 5 ``ic`` objects give 7 / 8 / 8 paths.

    Read from the fixtures: the serpentine and wave star items are 3 stubs and a ring with a gap at each joint; the wave
    U, V and W leads and one sector N lead are 2 joined stubs each.
    """
    counts = {case_id: len(board.interconnect) for case_id, board in _boards().items()}
    assert counts == dict(zip(CASES, (7, 8, 8), strict=True))


@pytest.mark.parametrize("case_id", CASES)
def test_run_drc_minima_lie_in_brute_brackets(case_id: str) -> None:
    """Catches a kernel, broad phase or exemption error on real layouts: lo <= measured min <= hi per pair kind.

    Same nets as run_drc sees (``as_mapped``) and the contract exemptions. The minimum of a kind lies among its
    violating pairs when there are any: the pairs the sweep finds below the rule plus the pairs run_drc reports (a pair
    the contract exempts but run_drc reports, DEF-M1c3-01, is the job of the two exemption tests below). Those are
    refined to 1e-10 mm. Otherwise it lies among the pairs within 1e-6 mm above the rule, refined to 1e-8 mm because
    concentric arcs at the rule are a plateau (README). A kind with no pair near the rule may report None or any value
    at or above the rule, since only pairs near the rule are measured.
    """
    board = _boards()[case_id]
    prims = {it.label: it.prim for it in board.as_mapped}
    engine = pair_violations(_report(case_id))
    for summary in _report(case_id).summaries:
        kind = summary.kind.value
        if kind in ("min_width", "min_drill", "annular_ring"):
            continue
        mine = [r for r in _mapped_sweep(case_id) if r.kind == kind]
        bad = {frozenset((r.a, r.b)) for r in mine if r.verdict is not Verdict.CLEAN}
        bad |= {key for key, (reported, _) in engine.items() if reported == kind}
        if bad:
            brackets = [clearance_bracket(*(prims[label] for label in sorted(key)), tol=1e-10) for key in bad]
        else:
            near = [r for r in mine if r.clearance.lo < RULE_MM + 1e-6]
            brackets = [clearance_bracket(prims[r.a], prims[r.b], tol=1e-8) for r in near]
        measured = summary.measured_min_mm
        if brackets:
            lo, hi = min(b.lo for b in brackets), min(b.hi for b in brackets)
            assert measured is not None and lo - 1e-12 <= measured <= hi + 1e-12, (kind, lo, measured, hi)
        else:
            assert measured is None or measured >= RULE_MM - DRC_EPSILON_MM, (kind, measured)


@pytest.mark.parametrize("case_id", CASES)
def test_every_violation_class_is_accounted_for(case_id: str) -> None:
    """Every run_drc violation is a brute violation or a known artefact; every brute miss is a documented exemption."""
    classes = classify(_boards()[case_id], pair_violations(_report(case_id)), RULE_MM)
    assert not [name for name in classes if "OTHER" in name], classes


def _reported_exempt(case_id: str, rules: frozenset[Rule]) -> list[tuple[str, ...]]:
    board = _boards()[case_id]
    exempt = contract_exemptions(board.intended, board.interconnect)
    engine = pair_violations(_report(case_id))
    hits = [key for key, (kind, _) in engine.items() if kind == "trace_via" and exempt.get(key) in rules]
    return sorted(tuple(sorted(key)) for key in hits)


@pytest.mark.parametrize("case_id", CASES)
def test_no_trace_via_violation_where_the_via_ends_a_same_phase_path(case_id: str) -> None:
    """Rule 2 exempts a via and the end group of a same-net path ending on it; run_drc must not report those pairs.

    Via nets come from the raw Xcoil phase, so a mapper that renames via nets again (DEF-M1c-01) fails here.
    """
    assert _reported_exempt(case_id, frozenset({Rule.END_ON_LAND})) == []


@pytest.mark.parametrize("case_id", CASES)
def test_no_trace_via_violation_where_a_via_touches_an_interconnect_path(case_id: str) -> None:
    """D-022c exempts an interconnect path from any via its end lies on or whose centre lies on its centreline."""
    assert _reported_exempt(case_id, WAIVER) == []


def test_wave_reports_xcoil_near_rule_pairs_as_d006_violations() -> None:
    """Xcoil's 4 um slack hides 0.199965 mm pairs; D-006 must report each, and Agent 4's sweep agrees on the count."""
    engine = pair_violations(_report("layout-wave-turns-2"))
    near = {k for k, (_, m) in engine.items() if RULE_MM - 1e-4 < m < RULE_MM - DRC_EPSILON_MM}
    mine = _intended_violations("layout-wave-turns-2")
    assert near == {k for k, r in mine.items() if r.clearance.lo > RULE_MM - 1e-4}
    assert len(near) == 186


def _widen(board: Board, label: str, delta_mm: float) -> tuple[Any, list[Any]]:
    """Return the layout with one primitive widened by ``delta_mm`` and the as-mapped universe of its dump."""
    path_id, prim = (int(part.split(":")[1]) for part in label.split("/"))
    layout = board.layout
    paths = list(layout.paths)
    target = paths[path_id]
    prims = list(target.primitives)
    prims[prim] = dataclasses.replace(prims[prim], width_mm=prims[prim].width_mm + delta_mm)
    paths[path_id] = dataclasses.replace(target, primitives=tuple(prims))
    changed = dataclasses.replace(layout, paths=tuple(paths))
    dump = parse_board_dump(json.loads(encode_board_dump(dump_layout(changed, case_id=board.case_id))))
    return changed, universe(dump, board.raw, intended=False)


def _neighbourhood(items: list[Item], label: str, reach_mm: float) -> list[Item]:
    """Items whose boxes lie within ``reach_mm`` of the box of item ``label``, that item included."""
    boxes = bounding_boxes([it.prim for it in items])
    (k,) = [i for i, it in enumerate(items) if it.label == label]
    gap_x = (boxes[:, 0] - boxes[k, 2]).clip(0) + (boxes[k, 0] - boxes[:, 2]).clip(0)
    gap_y = (boxes[:, 1] - boxes[k, 3]).clip(0) + (boxes[k, 1] - boxes[:, 3]).clip(0)
    return [it for it, gx, gy in zip(items, gap_x, gap_y, strict=True) if math.hypot(gx, gy) < reach_mm]


@pytest.mark.parametrize("case_id", CASES)
@pytest.mark.parametrize(("intrusion_mm", "caught"), [(1e-3, True), (1.05e-6, True), (0.95e-6, False)])
def test_injected_intrusion_in_a_real_layout(case_id: str, intrusion_mm: float, caught: bool) -> None:
    """Widen one primitive of the line pair closest above the rule until that pair sits at rule - intrusion.

    Catches a broad phase that misses a pair once it nears the rule, or an epsilon other than 1e-6 mm, on real copper.
    Every new violation run_drc reports must be one Agent 4's sweep finds around the widened primitive.
    """
    board = _boards()[case_id]
    prims = {it.label: it.prim for it in board.as_mapped}
    lines = [
        r for r in _mapped_sweep(case_id)
        if r.kind == "trace_trace" and r.verdict is Verdict.CLEAN and isinstance(prims[r.a], Line)
        and isinstance(prims[r.b], Line)
    ]  # fmt: skip
    target = min(lines, key=lambda r: r.clearance.hi)
    exact = clearance_bracket(prims[target.a], prims[target.b], tol=1e-11)
    assert exact.width < 1e-10
    centre = (exact.lo + exact.hi) / 2
    changed, items = _widen(board, target.a, 2 * (centre - RULE_MM + intrusion_mm))
    report = run_drc(changed, uniform_rules(RULE_MM))
    assert report is not None
    new = set(pair_violations(report)) - set(pair_violations(_report(case_id)))
    pair = frozenset((target.a, target.b))
    assert (pair in new) is caught, (target, exact, sorted(map(sorted, new))[:5])
    local = _neighbourhood(items, target.a, 2.0)
    exempt = contract_exemptions(items, board.interconnect)
    found = violations(sweep(local, range(len(board.dump.layers)), lambda kind: RULE_MM, exempt))
    assert new == {k for k in found if target.a in k} - set(pair_violations(_report(case_id)))
