"""PR-01 and PR-13 on the spiral generator: run_drc against Agent 4's brute sweep, through vias included.

The wave and serpentine PR-13 tests cover their generators; the PR-01 test of tests/unit/drc samples one random
primitive per path on one layer and no via. This module sweeps whole spiral boards with their through vias, as
test_plan.md PR-01 and PR-13 and REQ-F-05 ("every through via clears foreign copper") ask. The sweep is
tests/independent/m1 (Agent 4); its exemptions are coded there from interfaces.md section 7, not from embodic.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass
from functools import cache

import pytest
from board_dump_reader import parse_board_dump
from brute_clearance import Verdict
from drc_universe import Cls, Item, contract_exemptions, sweep
from embodic_adapter import pair_violations
from gr19 import universe
from tests.unit.generators.test_spiral_series_fan import series_design
from tests.unit.property.t_junctions import same_net_via_tap_pairs, t_junction_pairs

from embodic.drc import run_drc
from embodic.generators import generate_spiral
from embodic.geometry.layout import BoardStack, Layout
from embodic.io.board_dump import dump_layout, encode_board_dump
from embodic.io.examples import load_example
from embodic.model.design import DesignParameters
from embodic.model.drc_rules import DrcRules
from embodic.results import load_registry

REGISTRY = load_registry()
EXAMPLES = ("spiral_12c16p_default", "spiral_12c10p_d08", "spiral_12c14p")
SERIES_CF11_K3 = "cf11_series_k3"


@dataclass(frozen=True)
class SpiralBoard:
    """One spiral board and the design whose rules it is checked at."""

    design: DesignParameters
    layout: Layout


@cache
def _board(case: str) -> SpiralBoard:
    design = series_design("CF-11", 3) if case == SERIES_CF11_K3 else load_example(case)[1]
    stack = generate_spiral(design, REGISTRY)
    assert isinstance(stack, BoardStack), case
    return SpiralBoard(design, stack.boards[0])


def _rule_of(rules: DrcRules) -> Callable[[str], float]:
    """Return the clearance rule of a check kind (interfaces.md section 7, "Clearance rule per check kind")."""
    return {
        "trace_trace": rules.trace_clearance_mm,
        "pad_trace": rules.trace_clearance_mm,
        "trace_via": rules.via_clearance_mm,
        "via_via": rules.via_clearance_mm,
        "pad_pad": rules.via_clearance_mm,
        "copper_edge": rules.edge_clearance_mm,
        "copper_hole": rules.hole_clearance_mm,
    }.__getitem__


def _is_via_against_foreign_copper(a: Item, b: Item) -> bool:
    return (
        Cls.VIA in (a.cls, b.cls)
        and a.cls in (Cls.TRACE, Cls.VIA, Cls.PAD)
        and b.cls in (Cls.TRACE, Cls.VIA, Cls.PAD)
        and a.net != b.net
    )


@pytest.mark.req("REQ-F-05", "REQ-F-10")
@pytest.mark.slow
@pytest.mark.parametrize("case", [*EXAMPLES, SERIES_CF11_K3])
def test_pr_01_pr_13_spiral_boards_agree_with_the_brute_sweep_including_every_through_via(case: str) -> None:
    """PR-01, PR-13. Catches a through via that run_drc skips or invents: the sweep and the report agree on pairs.

    Every violation the sweep finds is reported; a passing report leaves the sweep none; every reported pair is a
    sweep violation; and the swept pairs include a via against copper of another net, so that the vias are in play.
    Tolerance: the D-006 threshold rule (1e-6 mm), no slack band.
    """
    board = _board(case)
    report = run_drc(board.layout, board.design.drc_rules)
    assert report is not None
    dump = parse_board_dump(json.loads(encode_board_dump(dump_layout(board.layout, case_id=case))))
    items = universe(dump, {"vias": [{"phase": 0}] * len(dump.vias)}, intended=False)
    exempt = (
        set(contract_exemptions(items, frozenset(board.layout.circuit.interconnect_path_ids)))
        | t_junction_pairs(items)
        | same_net_via_tap_pairs(items)
    )
    results = sweep(items, range(len(dump.layers)), _rule_of(board.design.drc_rules), exempt)
    brute = {frozenset((r.a, r.b)) for r in results if r.verdict is Verdict.VIOLATION}
    engine = set(pair_violations(report))
    assert brute <= engine, f"unreported: {sorted(map(sorted, brute - engine))[:3]}"
    assert engine <= brute, f"invented: {sorted(map(sorted, engine - brute))[:3]}"
    if report.passed:
        assert not brute
    by_label = {item.label: item for item in items}
    assert any(_is_via_against_foreign_copper(by_label[r.a], by_label[r.b]) for r in results)
