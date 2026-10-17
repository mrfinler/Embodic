"""Layer pairs of the spiral generator (spiral_generator_spec.md G5, G6, D-020): parallel (M1) and series (M2)."""

import dataclasses
import math

import pytest
from tests.unit.generators.default_example import default_design

from embodic.drc import run_drc
from embodic.errors import Unbuildable
from embodic.generators import generate_spiral
from embodic.generators.spiral.series import SeriesCoil, series_coil
from embodic.generators.spiral.turns import CoilFrame, FullClosing, loop_turns, max_closing
from embodic.geometry.layout import BoardStack, Layout, ViaRole
from embodic.geometry.primitives import PrimitiveRole
from embodic.model.design import DesignParameters
from embodic.model.layers import LayerConfig, LayerPair
from embodic.model.stackup import generate_even_stackup
from embodic.model.vocabulary import Phase
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
    least = {s.kind.value: s.least_clearance_mm for s in report.summaries}
    assert least["trace_trace"] == pytest.approx(0.2, abs=1e-6)
    assert least["trace_via"] == pytest.approx(0.2, abs=1e-6)


def _series_coil(groups: int) -> tuple[SeriesCoil, FullClosing]:
    """Canonical CF-11 coil of ``groups`` series groups with sharp corners."""
    design = default_design()
    assert isinstance(design.winding, SpiralWindingSpec)
    frame = CoilFrame.of(design.winding.coil, design.vias.pad_mm)
    closing = max_closing(frame, loop_turns(frame)[0], vias=groups)
    assert isinstance(closing, FullClosing)
    coil = series_coil(frame, closing, design.connection.ring_width_mm, groups, {})
    assert isinstance(coil, SeriesCoil), coil
    return coil, closing


@pytest.mark.eqt("EQT-25-UT1")
@pytest.mark.req("REQ-F-03")
def test_ut_geo_19_series_groups_get_their_own_centre_via_one_pitch_apart() -> None:
    """UT-GEO-19 (M2, G5 k centre vias): CF-11 with three series groups keeps 10 turns and r_v 30.7, 29.9, 29.1 mm.

    Spec worked example: eye 28.5914 to 30.7 mm, via pitch max(pad, w)/2 + pad/2 + s = 0.8 mm. Catches groups sharing
    one centre via (a short across a group) or the half closing's single P.
    """
    coil, closing = _series_coil(3)
    assert closing.n == 10
    assert [group.centre_via[0] for group in coil.groups] == pytest.approx([30.7, 29.9, 29.1], abs=1e-9)
    assert [group.centre_via[1] for group in coil.groups] == [0.0, 0.0, 0.0]


@pytest.mark.req("REQ-F-03")
def test_ut_geo_19_each_group_runs_from_its_ring_via_to_its_centre_and_out_to_the_next() -> None:
    """UT-GEO-19 (M2, G6): group g's X joins ring via g to its centre via, its Y the centre to ring via g + 1.

    Ring vias alternate CCW and CW sides of the coil; two on one side sit at least the fan pitch
    c_f = max(pad, w, bw) + s = 1.2 mm apart (G6 U-E6; the spec table gives a pad gap of 0.6001 mm on CF-11).
    Catches a transfer via on the wrong side, two groups landing on one ring via, the v1.0 pitch pad + s, or an odd
    group that keeps the first outer arc (it enters at the right side of turn 0).
    """
    coil, _ = _series_coil(3)
    rings = coil.ring_vias
    assert [math.copysign(1.0, p[1]) for p in rings] == [1.0, -1.0, 1.0, -1.0]
    assert math.dist(rings[0], rings[2]) - 0.6 == pytest.approx(0.6001, abs=1e-4)
    assert math.dist(rings[1], rings[3]) - 0.6 == pytest.approx(0.6001, abs=1e-4)
    for g, group in enumerate(coil.groups):
        assert math.dist(group.x[0].start_point(), rings[g]) <= 1e-9
        assert math.dist(group.x[-1].end_point(), group.centre_via) <= 1e-9
        assert math.dist(group.y[0].start_point(), group.centre_via) <= 1e-9
        assert math.dist(group.y[-1].end_point(), rings[g + 1]) <= 1e-9
        for before, after in zip(group.x, group.x[1:], strict=False):
            assert math.dist(before.end_point(), after.start_point()) <= 1e-9
    outer_arcs = [sum(p.role is PrimitiveRole.END_TURN for p in group.x) for group in coil.groups]
    assert outer_arcs[0] - outer_arcs[1] == 1 and outer_arcs[2] == outer_arcs[0]


@pytest.mark.req("REQ-F-03")
def test_ut_geo_19_series_pairs_whose_fan_sides_meet_are_refused(registry: Registry) -> None:
    """G6 step 6: a 6 mm bus ring makes the fan pitch 6.2 mm, so the innermost CCW and CW vias come closer than it.

    Catches a fan built with its levels crossed over the coil axis, or a series design silently changed to parallel.
    """
    design = _three_pairs(((0,), (1,), (2,)))
    wide = dataclasses.replace(design, connection=dataclasses.replace(design.connection, ring_width_mm=6.0))
    refused = generate_spiral(wide, registry)
    assert isinstance(refused, Unbuildable)
    assert [(i.code, i.pointers) for i in refused.issues] == [
        ("UNBUILDABLE_SERIES_VIA_FAN_DRC", ("/winding/layers/series_groups",))
    ]


def _rotated(design: DesignParameters, rotations: tuple[float, ...]) -> DesignParameters:
    assert isinstance(design.winding, SpiralWindingSpec)
    layers = design.winding.layers
    pairs = tuple(dataclasses.replace(p, rotation_rad=r) for p, r in zip(layers.pairs, rotations, strict=True))
    winding = dataclasses.replace(design.winding, layers=dataclasses.replace(layers, pairs=pairs))
    return dataclasses.replace(design, winding=winding)


def _end_points(board: Layout) -> list[tuple[float, float]]:
    return [pt for path in board.paths for prim in path.primitives for pt in (prim.start_point(), prim.end_point())]


@pytest.mark.req("REQ-F-03")
def test_m3_a_rotation_every_pair_shares_turns_the_whole_winding(registry: Registry) -> None:
    """Option M3 with one rotation: pi/Q on every pair builds the board of first coil angle theta_0 + pi/Q.

    Catches a pair rotation the generator ignores (the board would equal the unrotated one).
    """
    design = _three_pairs(((0, 1, 2),))
    assert isinstance(design.winding, SpiralWindingSpec)
    step = math.pi / design.winding.coil.coil_count
    coil = design.winding.coil
    shifted_design = dataclasses.replace(
        design,
        winding=dataclasses.replace(
            design.winding, coil=dataclasses.replace(coil, first_coil_angle_rad=coil.first_coil_angle_rad + step)
        ),
    )
    boards = [generate_spiral(d, registry) for d in (_rotated(design, (step, step, step)), shifted_design, design)]
    assert all(isinstance(b, BoardStack) for b in boards)
    turned, shifted, plain = (_end_points(b.boards[0]) for b in boards)  # type: ignore[union-attr]
    assert max(math.dist(a, b) for a, b in zip(turned, shifted, strict=True)) <= 1e-9
    assert max(math.dist(a, b) for a, b in zip(turned, plain, strict=True)) > 1.0


@pytest.mark.req("REQ-F-03")
@pytest.mark.parametrize("series_groups", [((0,), (1,), (2,)), ((0, 1, 2),)], ids=["series", "parallel"])
def test_ut_geo_11_pairs_rotated_against_each_other_are_refused(
    registry: Registry, series_groups: tuple[tuple[int, ...], ...]
) -> None:
    """UT-GEO-11 (G6 U-E6): a pair at pi/Q among unrotated pairs has no coil at the others' positions, so: refused.

    Catches the rotation built silently wrong or dropped, in series or in parallel, or the old not-implemented code.
    """
    design = _three_pairs(series_groups)
    assert isinstance(design.winding, SpiralWindingSpec)
    refused = generate_spiral(_rotated(design, (0.0, math.pi / design.winding.coil.coil_count, 0.0)), registry)
    assert isinstance(refused, Unbuildable)
    assert [(i.code, i.pointers) for i in refused.issues] == [
        ("UNBUILDABLE_PAIRS_ROTATED_APART", ("/winding/layers/pairs",))
    ]


@pytest.mark.req("REQ-F-03")
@pytest.mark.parametrize(("coils", "poles"), [(16, 16), (12, 16)], ids=["16-16", "12-16"])
def test_m4_one_phase_per_pair_is_refused_until_phase_5(registry: Registry, coils: int, poles: int) -> None:
    """REQ-F-03 (d), D-054c: option M4 (one phase per pair) is refused with NOT_IMPLEMENTED at the pair list, alone.

    Catches a generator that accepts `phases` and then fails with another code or builds a board. The 16/16 case is
    the one the requirement names. The 12/16 design builds without `phases`, so only the pair list stops it.
    """
    design = _three_pairs(((0,), (1,), (2,)))
    assert isinstance(design.winding, SpiralWindingSpec)
    one_phase_each = zip(design.winding.layers.pairs, Phase, strict=True)
    pairs = tuple(dataclasses.replace(p, phases=(phase,)) for p, phase in one_phase_each)
    layers = dataclasses.replace(design.winding.layers, pairs=pairs)
    coil = dataclasses.replace(design.winding.coil, coil_count=coils)
    winding = dataclasses.replace(design.winding, coil=coil, layers=layers)
    rotor = dataclasses.replace(design.rotor, poles=poles)
    refused = generate_spiral(dataclasses.replace(design, winding=winding, rotor=rotor), registry)
    assert isinstance(refused, Unbuildable)
    assert [(i.code, i.pointers) for i in refused.issues] == [
        ("UNBUILDABLE_SPIRAL_OPTION_NOT_IMPLEMENTED", ("/winding/layers/pairs",))
    ]
