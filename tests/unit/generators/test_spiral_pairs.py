"""Several layer pairs of the spiral generator (spiral_generator_spec.md G6, D-020): parallel pairs (option M1)."""

import dataclasses

import pytest
from tests.unit.generators.default_example import default_design

from embodic.drc import run_drc
from embodic.errors import Unbuildable
from embodic.generators import generate_spiral
from embodic.geometry.layout import BoardStack, Layout, ViaRole
from embodic.model.design import DesignParameters
from embodic.model.layers import LayerConfig, LayerPair
from embodic.model.stackup import generate_even_stackup
from embodic.model.winding_specs import SpiralWindingSpec
from embodic.results import Registry, load_registry


@pytest.fixture(scope="module")
def registry() -> Registry:
    """Return the shipped equation registry."""
    return load_registry()


def _three_pairs(series_groups: tuple[tuple[int, ...], ...]) -> DesignParameters:
    """CF-11 on six copper layers: pairs L1/L2, L3/L4, L5/L6 (option M1 when all three form one group)."""
    design = default_design()
    assert isinstance(design.winding, SpiralWindingSpec)
    pairs = tuple(LayerPair(index=i, layer_in=f"L{2 * i + 1}", layer_out=f"L{2 * i + 2}") for i in range(3))
    layers = LayerConfig(pairs=pairs, series_groups=series_groups)
    return dataclasses.replace(
        design,
        stackup=generate_even_stackup(6, 0.0348, 1.6),
        winding=dataclasses.replace(design.winding, layers=layers),
    )


@pytest.fixture(scope="module")
def m1(registry: Registry) -> Layout:
    """Return the board of CF-11 with three parallel layer pairs."""
    stack = generate_spiral(_three_pairs(((0, 1, 2),)), registry)
    assert isinstance(stack, BoardStack), stack
    return stack.boards[0]


@pytest.mark.req("REQ-F-03")
def test_ut_geo_10_parallel_pairs_put_one_route_per_pair_in_each_coil_group(m1: Layout) -> None:
    """UT-GEO-10 (M1): each coil's parallel group holds one X-Y route per pair, on that pair's two layers.

    Catches pairs chained in series, a pair left out, or two routes sharing one layer pair.
    """
    paths = {p.id: p for p in m1.paths}
    assert m1.copper_layers == ("L1", "L2", "L3", "L4", "L5", "L6")
    for phase in m1.circuit.phases:
        coil_groups = [g for g in phase.groups if len(g.members) > 1]
        assert len(coil_groups) == 4  # 12 coils, 3 phases
        for group in coil_groups:
            layer_sets = [frozenset(paths[i].layer for i in m.path_ids) for m in group.members]
            assert sorted(sorted(s) for s in layer_sets) == [["L1", "L2"], ["L3", "L4"], ["L5", "L6"]]
            assert len({m.via_ids for m in group.members}) == 1  # one shared centre via and two stitch terminals


@pytest.mark.req("REQ-F-05")
def test_ut_geo_13_parallel_pairs_need_36_winding_vias(m1: Layout) -> None:
    """UT-GEO-13 (M1): Q (2k - 1 + [n1 > 1] + [nk > 1]) = 12 x 3 = 36 centre and stitch vias, all through L1 to L6.

    A centre via per pair would give 60.
    """
    winding = [v for v in m1.vias if v.role in (ViaRole.CENTRE, ViaRole.TERMINAL)]
    assert len(winding) == 36
    assert sum(v.role is ViaRole.CENTRE for v in winding) == 12
    assert {(v.layer_from, v.layer_to) for v in winding} == {("L1", "L6")}


@pytest.mark.req("REQ-F-05")
def test_parallel_pairs_pass_drc(m1: Layout) -> None:
    """G6 and G9: three identical pairs and shared through vias keep every gap at s or more."""
    report = run_drc(m1, _three_pairs(((0, 1, 2),)).drc_rules)
    assert report is not None and report.violation_count == 0, [v.objects for v in report.violations]
    least = {s.kind.value: s.measured_min_mm for s in report.summaries}
    assert least["trace_trace"] == pytest.approx(0.2, abs=1e-6)
    assert least["trace_via"] == pytest.approx(0.2, abs=1e-6)


@pytest.mark.req("REQ-F-03")
def test_series_groups_are_refused_until_the_via_fan_is_built(registry: Registry) -> None:
    """D-020 series pairs (M2) need the terminal via fan, not built yet; the generator refuses with the pointer."""
    refused = generate_spiral(_three_pairs(((0,), (1,), (2,))), registry)
    assert isinstance(refused, Unbuildable)
    assert refused.issues[0].code == "UNBUILDABLE_SPIRAL_OPTION_NOT_IMPLEMENTED"
    assert refused.issues[0].pointers == ("/winding/layers/series_groups",)
