"""Series via fan of spiral_generator_spec.md G6 (revision 2026-10-08, U-E6) on CF-11 and D08, k = 2 and 3 (D-020).

Expected via positions come from Agent 2's reference construction (checks/series_fan_check.py), frozen in
fixtures/series_fan_vias.json by make_fan_goldens.py; expected clearances are the spec's DRC table (smallest gap s).
"""

import dataclasses
import json
import math
from pathlib import Path

import pytest
from tests.unit.generators.d08_example import d08_design
from tests.unit.generators.default_example import default_design

from embodic.drc import run_drc
from embodic.generators import generate_spiral
from embodic.geometry.layout import BoardStack, Layout, ViaRole
from embodic.geometry.transforms import Transform, transform_point
from embodic.model.design import DesignParameters
from embodic.model.layers import LayerConfig, LayerPair
from embodic.model.stackup import generate_even_stackup
from embodic.model.winding_specs import SpiralWindingSpec
from embodic.results import load_registry

GOLDEN = json.loads((Path(__file__).parent / "fixtures" / "series_fan_vias.json").read_text(encoding="utf-8"))
CASES = [("CF-11", 2), ("CF-11", 3), ("D08", 2), ("D08", 3)]
RULE_S_MM = {"CF-11": 0.2, "D08": 0.8}


def series_design(name: str, k: int) -> DesignParameters:
    """``name`` on 2k layers with k series groups of one pair, turns at the maximum (as the reference builds them)."""
    base = default_design() if name == "CF-11" else d08_design()
    assert isinstance(base.winding, SpiralWindingSpec)
    pairs = tuple(LayerPair(index=i, layer_in=f"L{2 * i + 1}", layer_out=f"L{2 * i + 2}") for i in range(k))
    layers = LayerConfig(pairs=pairs, series_groups=tuple((i,) for i in range(k)))
    coil = dataclasses.replace(base.winding.coil, turns=None)
    return dataclasses.replace(
        base,
        stackup=generate_even_stackup(2 * k, 0.0348, 1.6),
        winding=dataclasses.replace(base.winding, layers=layers, coil=coil),
    )


@pytest.fixture(scope="module", params=CASES, ids=[f"{n}-k{k}" for n, k in CASES])
def case(request: pytest.FixtureRequest) -> tuple[str, int, DesignParameters, Layout]:
    """Return the series board of one case; generate_spiral refuses a board whose whole-board DRC fails (D-020)."""
    name, k = request.param
    design = series_design(name, k)
    stack = generate_spiral(design, load_registry())
    assert isinstance(stack, BoardStack), [(i.code, i.pointers) for i in stack.issues]
    return name, k, design, stack.boards[0]


def _coil_angles(design: DesignParameters) -> list[float]:
    assert isinstance(design.winding, SpiralWindingSpec)
    coil = design.winding.coil
    first = coil.first_coil_angle_rad + design.winding.layers.pairs[0].rotation_rad
    return [first + j * 2 * math.pi / coil.coil_count for j in range(coil.coil_count)]


@pytest.mark.req("REQ-F-05")
def test_fan_ring_vias_equal_the_reference_construction(case: tuple[str, int, DesignParameters, Layout]) -> None:
    """G6 steps 1 to 3: every coil's k + 1 ring vias sit where Agent 2's fan puts them, within 1e-6 mm.

    Catches the v1.0 pitch pad + s, a_1 without the corner term (D08), a via on the wrong side, or a fan level off.
    """
    name, k, design, board = case
    canonical = GOLDEN[f"{name} k={k}"]["ring_vias"]
    expected = [transform_point(Transform(rotation_rad=a), *p) for a in _coil_angles(design) for p in canonical]
    ring = [(v.x_mm, v.y_mm) for v in board.vias if v.role in (ViaRole.TERMINAL, ViaRole.TRANSFER)]
    assert len(ring) == len(expected)
    worst = max(min(math.dist(e, r) for r in ring) for e in expected)
    assert worst <= 1e-6


@pytest.mark.req("REQ-F-05")
def test_ut_geo_13_series_coil_has_2k_plus_1_winding_vias(case: tuple[str, int, DesignParameters, Layout]) -> None:
    """UT-GEO-13 (G6 U-E6): k centre, k - 1 transfer and 2 terminal vias per coil, Q (2k + 1) in all.

    Catches the v1.0 formula Q (2k - 1 + [n1 > 1] + [nk > 1]) = Q (2k - 1) for one pair per group.
    """
    _, k, design, board = case
    assert isinstance(design.winding, SpiralWindingSpec)
    q = design.winding.coil.coil_count
    roles = (ViaRole.CENTRE, ViaRole.TRANSFER, ViaRole.TERMINAL)
    count = {role: sum(v.role is role for v in board.vias) for role in roles}
    assert count == {ViaRole.CENTRE: q * k, ViaRole.TRANSFER: q * (k - 1), ViaRole.TERMINAL: q * 2}


@pytest.mark.req("REQ-F-03")
def test_ut_geo_26_series_board_passes_drc_with_smallest_gap_s(case: tuple[str, int, DesignParameters, Layout]) -> None:
    """Spec G6 DRC table: 0 violations on the whole board; the smallest trace and via gap is s (0.2 or 0.8 mm).

    Catches a fan that passes only because a check kind found no pair, or a gap below the rule (D-006, no slack).
    """
    name, _, design, board = case
    report = run_drc(board, design.drc_rules)
    assert report is not None
    assert report.violation_count == 0, [v.objects for v in report.violations][:5]
    least = {s.kind.value: s.least_clearance_mm for s in report.summaries if s.least_clearance_mm is not None}
    assert least["trace_trace"] == pytest.approx(RULE_S_MM[name], abs=1e-6)
    assert least["trace_via"] == pytest.approx(RULE_S_MM[name], abs=1e-6)


@pytest.mark.req("REQ-N-04")
def test_same_series_design_gives_the_same_stack_hash(case: tuple[str, int, DesignParameters, Layout]) -> None:
    """Determinism (generators/base.py): a second run of the same design hashes to the same stack.

    Catches fan copper or via order that depends on set or dict iteration, or on state left by an earlier run.
    """
    _, _, design, board = case
    again = generate_spiral(design, load_registry())
    assert isinstance(again, BoardStack)
    assert again.boards[0].layout_hash == board.layout_hash
    assert (
        again.stack_hash
        == BoardStack(boards=(board,), board_thickness_mm=again.board_thickness_mm, board_gap_mm=0.0).stack_hash
    )
