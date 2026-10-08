"""Spiral generator on the default 12/16 example (CF-11): geometry properties, contract, determinism and DRC."""

import dataclasses
import itertools
import math
from collections import Counter

import numpy as np
import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st
from tests.unit.generators.d08_example import d08_design
from tests.unit.generators.default_example import default_design
from tests.unit.generators.wave.designs import wave
from tests.unit.model.designs import serpentine_design

from embodic.drc import run_drc
from embodic.errors import Unbuildable
from embodic.generators import GENERATORS, build_layout, generate_serpentine, generate_spiral, generate_wave
from embodic.geometry.details import SpiralDetail, TurnClosing, TurnLimitReason
from embodic.geometry.discretise import discretise
from embodic.geometry.layout import BoardStack, Layout, ViaRole
from embodic.geometry.paths import CopperPath, is_continuous
from embodic.geometry.primitives import PrimitiveRole
from embodic.geometry.transforms import mirror, reverse_path, rotate
from embodic.model.design import DesignParameters
from embodic.model.drc_rules import DrcRules
from embodic.model.vocabulary import TopologyKind
from embodic.model.winding_specs import SpiralWindingSpec
from embodic.results import Registry, load_registry


@pytest.fixture(scope="module")
def registry() -> Registry:
    """Return the shipped equation registry."""
    return load_registry()


@pytest.fixture(scope="module")
def board(registry: Registry) -> Layout:
    """Return the one board of the default example."""
    stack = generate_spiral(default_design(), registry)
    assert isinstance(stack, BoardStack)
    return stack.boards[0]


def _coil_paths(board: Layout, coil: int) -> dict[str, CopperPath]:
    return {p.layer: p for p in board.paths if p.element == coil}


def _points(path: CopperPath) -> np.ndarray:
    return np.vstack([discretise(p, 0.05) for p in path.primitives])


@pytest.mark.req("REQ-F-06")
def test_default_track_length_matches_cf11(board: Layout) -> None:
    """CF-11 worked example 1: 415.4808 mm per coil-layer (body + lead + stub), N = 10, eye-limited."""
    detail = board.detail
    assert isinstance(detail, SpiralDetail)
    assert detail.turns_achieved == 10 and detail.turn_limit.limiting_reason is TurnLimitReason.EYE
    assert detail.turn_limit.loops_trapezoidal == 8 and detail.turn_limit.loops_triangular == 3
    assert detail.track_length_per_coil_layer_mm["X"] == pytest.approx(415.4808, abs=5e-5)
    assert detail.plan.pattern == "ACBACBACBACB"


@pytest.mark.req("REQ-F-06")
def test_d08_builds_three_turns_with_the_half_closing(registry: Registry) -> None:
    """CF-10 worked example 2: N = 3 (2 full turns and the closing half turn), 160.2750 mm per coil-layer, no lead."""
    stack = generate_spiral(d08_design(), registry)
    assert isinstance(stack, BoardStack)
    board = stack.boards[0]
    detail = board.detail
    assert isinstance(detail, SpiralDetail)
    assert detail.turns_achieved == 3 and detail.turn_limit.eye_limit == 3
    assert detail.track_length_per_coil_layer_mm["X"] == pytest.approx(160.2750, abs=5e-5)
    assert detail.plan.pattern == "AabBCcaABbcC"
    assert not any(p.role is PrimitiveRole.LEAD for path in board.paths for p in path.primitives)


@pytest.mark.req("REQ-F-19")
def test_layout_derived_carries_turns_length_and_envelope(board: Layout) -> None:
    """Layout.derived lists the feasibility-rail values; catches a missing or stale value (CF-11 worked example 1)."""
    derived = {t.quantity: t for t in board.derived}
    assert derived["turns_per_coil_per_layer"].value == 10.0
    assert derived["turn_limit_per_coil_per_layer"].value == 10.0
    assert derived["track_length_per_coil_layer_mm"].value == pytest.approx(415.4808, abs=5e-5)
    assert (derived["copper_r_min_mm"].value, derived["copper_r_max_mm"].value) == board.envelope_mm
    assert derived["turns_per_coil_per_layer"].kind_tag == "count"
    assert all(t.inputs for t in board.derived)


@pytest.mark.req("REQ-F-09")
def test_ut_geo_14_outline_is_closed_and_encloses_the_copper(board: Layout) -> None:
    """UT-GEO-14: edge and bore are closed loops within 1e-9 mm; the bore lies inside r_min, the edge beyond r_max."""
    for loop in (board.outline.outer, *board.outline.cutouts):
        assert math.dist(loop[-1].end_point(), loop[0].start_point()) <= 1e-9
        assert is_continuous(loop, 1e-9)
    bore = max(math.hypot(*p.start_point()) for p in board.outline.cutouts[0])
    edge = min(abs(p.x1_mm * p.y2_mm - p.x2_mm * p.y1_mm) / math.dist(p.start_point(), p.end_point())
               for p in board.outline.outer)  # fmt: skip
    assert bore < board.envelope_mm[0] and edge > board.envelope_mm[1]


@pytest.mark.req("REQ-F-01", "REQ-N-21")
def test_every_path_is_continuous(board: Layout) -> None:
    """UT-GEO-01: every joint of every coil path closes within 1e-6 mm."""
    assert all(is_continuous(p.primitives) for p in board.paths)


@pytest.mark.req("REQ-F-01")
def test_ut_geo_03_layer_y_is_the_mirror_of_x(board: Layout) -> None:
    """UT-GEO-03: coil 0's Y path mirrored about the coil axis and reversed equals its X path within 1e-9 mm."""
    paths = _coil_paths(board, 0)
    axis = default_design().winding.coil.first_coil_angle_rad  # type: ignore[union-attr]
    x, y = paths["L1"], paths["L2"]
    if x.polarity == -1:
        x, y = dataclasses.replace(x, primitives=reverse_path(x.primitives)), y
    mirrored = reverse_path(mirror(y.primitives, axis)) if x.polarity == 1 else mirror(y.primitives, axis)
    for a, b in zip(mirrored, x.primitives if x.polarity == 1 else reverse_path(x.primitives), strict=True):
        assert math.dist(a.start_point(), b.start_point()) <= 1e-9
        assert math.dist(a.end_point(), b.end_point()) <= 1e-9


@pytest.mark.req("REQ-F-01")
def test_ut_geo_04_centre_via_terminates_x_and_y(board: Layout) -> None:
    """UT-GEO-04: on every coil, X and Y meet the coil's centre via within 1e-9 mm."""
    centres = [v for v in board.vias if v.role is ViaRole.CENTRE]
    assert len(centres) == 12
    for coil, via in enumerate(centres):
        for path in _coil_paths(board, coil).values():
            ends = (path.primitives[0].start_point(), path.primitives[-1].end_point())
            assert min(math.dist(e, (via.x_mm, via.y_mm)) for e in ends) <= 1e-9


@pytest.mark.req("REQ-F-01")
def test_ut_geo_05_x_and_y_circulate_the_same_way(board: Layout) -> None:
    """UT-GEO-05: in current direction, X and Y wind the same way around the coil centre (equal turning angle)."""
    for coil in range(12):
        paths = list(_coil_paths(board, coil).values())
        angle = math.pi / 2 + coil * 2 * math.pi / 12  # a point on the coil axis, inside every turn
        centre = 28.0 * np.array([math.cos(angle), math.sin(angle)])
        sweeps = []
        for path in paths:
            angles = np.unwrap(np.arctan2(*(_points(path) - centre).T[::-1]))
            sweeps.append(angles[-1] - angles[0])
        assert np.sign(sweeps[0]) == np.sign(sweeps[1])
        assert sweeps[0] == pytest.approx(sweeps[1], rel=1e-9)
        expected_sign = -1 if paths[0].polarity == 1 else 1  # D-019: positive coil is clockwise seen from F.Cu
        assert np.sign(sweeps[0]) == expected_sign


@pytest.mark.req("REQ-F-03")
def test_ut_geo_06_and_16_coils_are_rotated_copies_with_polarity_in_direction_only(board: Layout) -> None:
    """UT-GEO-06 and UT-GEO-16: coil k's copper is coil 0's rotated by 2 pi k/Q; a negative coil only reverses."""
    base = {p.layer: p for p in board.paths if p.element == 0}
    for coil in range(1, 12):
        for layer, path in _coil_paths(board, coil).items():
            ref = (
                base[layer].primitives
                if base[layer].polarity == path.polarity
                else reverse_path(base[layer].primitives)
            )
            for a, b in zip(rotate(ref, coil * 2 * math.pi / 12), path.primitives, strict=True):
                assert math.dist(a.start_point(), b.start_point()) <= 1e-9
                assert math.dist(a.end_point(), b.end_point()) <= 1e-9
    coil_paths = [p for p in board.paths if p.element is not None]
    assert Counter(p.polarity for p in coil_paths) == {1: 24}  # 12/16: every coil is positive (ACBACB...)


@pytest.mark.req("REQ-F-19")
def test_same_design_gives_the_same_stack_hash(registry: Registry) -> None:
    """Determinism: two runs of one design give one stack_hash; changing the trace width changes it."""
    first, second = (generate_spiral(default_design(), registry) for _ in range(2))
    assert isinstance(first, BoardStack) and isinstance(second, BoardStack)
    assert first.stack_hash == second.stack_hash
    design = default_design()
    assert isinstance(design.winding, SpiralWindingSpec)
    thinner = dataclasses.replace(
        design,
        winding=dataclasses.replace(design.winding, coil=dataclasses.replace(design.winding.coil, trace_width_mm=0.45)),
    )
    other = generate_spiral(thinner, registry)
    assert isinstance(other, BoardStack) and other.stack_hash != first.stack_hash


@pytest.mark.req("REQ-F-19")
def test_ut_gen_02_dispatch(registry: Registry) -> None:
    """UT-GEN-02: build_layout routes by topology to the real generators; a wrong winding is a TypeError.

    Catches a table entry pointing at the wrong or a stub generator, and a dispatcher that ignores the topology.
    """
    assert GENERATORS[TopologyKind.SPIRAL] is generate_spiral
    assert GENERATORS[TopologyKind.SERPENTINE] is generate_serpentine
    assert GENERATORS[TopologyKind.WAVE] is generate_wave
    for design, generate in (
        (default_design(), generate_spiral),
        (serpentine_design(), generate_serpentine),
        (wave(), generate_wave),
    ):
        built = build_layout(design, registry)
        assert isinstance(built, BoardStack), design.topology
        direct = generate(design, registry)
        assert isinstance(direct, BoardStack) and built.stack_hash == direct.stack_hash
    with pytest.raises(TypeError):
        generate_wave(default_design(), registry)
    with pytest.raises(TypeError):
        generate_spiral(serpentine_design(), registry)


@pytest.mark.req("REQ-F-03")
@pytest.mark.parametrize("example", ["CF-11", "CF-10"])
def test_g8_each_phase_is_one_continuous_series_route(example: str, registry: Registry) -> None:
    """G8: walking a phase's members in order, every path starts where the previous one ended (legs, coil, ring arc).

    Catches a ring arc run backwards, on the wrong level radius, or a leg on the wrong terminal.
    """
    design = default_design() if example == "CF-11" else d08_design()
    stack = generate_spiral(design, registry)
    assert isinstance(stack, BoardStack)
    board = stack.boards[0]
    paths = {p.id: p for p in board.paths}
    pair = design.winding.layers.pairs[0]  # type: ignore[union-attr]
    for phase in board.circuit.phases:
        route = [paths[i] for g in phase.groups for m in g.members for i in m.path_ids]
        assert len({p.element for p in route if p.element is not None}) == len(phase.groups)
        for before, after in itertools.pairwise(route):
            assert math.dist(before.primitives[-1].end_point(), after.primitives[0].start_point()) <= 1e-6
        chain_copper = [p for p in route if p.element is None]
        assert {p.layer for p in chain_copper if p.primitives[0].role is PrimitiveRole.LEG} == {pair.layer_out}
        assert {p.layer for p in chain_copper if p.primitives[0].role is PrimitiveRole.RING} <= {pair.layer_in}
        assert all(p.net == f"PHASE_{phase.phase.value}" for p in route)
    assert sum(v.role is ViaRole.RING and v.net.startswith("PHASE_") for v in board.vias) == 2 * 12


@pytest.mark.req("REQ-F-03")
def test_g8_star_joins_the_three_phase_ends_and_leads_reach_pads(board: Layout) -> None:
    """D-022 nets: the neutral N taps the end of every phase chain; U/V/W leads run from each phase start to its pad.

    Catches a lead on the wrong phase end, a missing neutral tap, or interconnect copper left out of the circuit.
    """
    paths = {p.id: p for p in board.paths}
    vias = {v.id: v for v in board.vias}
    ic = [paths[i] for i in board.circuit.interconnect_path_ids]
    assert Counter(p.net for p in ic) == {"N": 4, "U": 1, "V": 1, "W": 1}
    for phase in board.circuit.phases:
        start_via = vias[phase.groups[0].members[0].via_ids[0]]
        end_via = vias[phase.groups[-1].members[0].via_ids[-1]]
        lead = next(p for p in ic if p.net == phase.terminal_net)
        assert math.dist(lead.primitives[0].start_point(), (start_via.x_mm, start_via.y_mm)) <= start_via.pad_mm / 2
        pad = next(d for d in board.pads if d.label == phase.terminal_net)
        assert math.dist(lead.primitives[-1].end_point(), (pad.x_mm, pad.y_mm)) <= 1e-9
        neutral_stub_starts = [p.primitives[0].start_point() for p in ic if p.net == "N" and len(p.primitives) == 1]
        assert min(math.dist(q, (end_via.x_mm, end_via.y_mm)) for q in neutral_stub_starts) <= end_via.pad_mm / 2


def _check_contract(result: BoardStack | Unbuildable) -> None:
    if isinstance(result, Unbuildable):
        return
    assert len(result.boards) == 1
    board = result.boards[0]
    path_ids = {p.id for p in board.paths}
    via_ids = {v.id for v in board.vias}
    members = [m for pc in board.circuit.phases for g in pc.groups for m in g.members]
    listed = [i for m in members for i in m.path_ids] + list(board.circuit.interconnect_path_ids)
    assert sorted(listed) == sorted(path_ids)
    assert all(v in via_ids for m in members for v in m.via_ids)


@pytest.mark.req("REQ-F-19")
@settings(max_examples=40, deadline=None)
@example(coils=12, poles=16, r_inner=60.0, span=40.0, w=0.001, s=0.0, gap=0.0, pad=0.6, turns=None)  # DEF-M2d2-01
@example(coils=12, poles=16, r_inner=60.0, span=40.0, w=1e-9, s=0.0, gap=0.0, pad=0.6, turns=None)  # unbounded turns
@example(coils=12, poles=16, r_inner=60.0, span=40.0, w=0.15, s=1e-6, gap=0.0, pad=0.6, turns=None)  # turn cap
@given(
    coils=st.sampled_from([3, 6, 9, 12, 18, 24]),
    poles=st.sampled_from([2, 4, 8, 10, 14, 16, 20]),
    r_inner=st.floats(-5.0, 60.0),
    span=st.floats(-5.0, 40.0),
    w=st.floats(-0.1, 3.0),
    s=st.floats(-0.1, 1.0),
    gap=st.floats(0.0, 1.0),
    pad=st.floats(0.0, 2.0),
    turns=st.none() | st.integers(-1, 30),
)
def test_ut_gen_01_fuzz_never_raises(
    coils: int, poles: int, r_inner: float, span: float, w: float, s: float, gap: float, pad: float, turns: int | None
) -> None:
    """UT-GEN-01: fuzzed spiral inputs give a BoardStack or Unbuildable, never an exception; the circuit is complete."""
    design = default_design()
    assert isinstance(design.winding, SpiralWindingSpec)
    coil = dataclasses.replace(
        design.winding.coil, coil_count=coils, r_inner_mm=r_inner, r_outer_mm=r_inner + span,
        trace_width_mm=w, clearance_mm=s, coil_gap_mm=gap, turns=turns,
    )  # fmt: skip
    fuzzed = dataclasses.replace(
        design,
        rotor=dataclasses.replace(design.rotor, poles=poles),
        winding=dataclasses.replace(design.winding, coil=coil),
        vias=dataclasses.replace(design.vias, pad_mm=pad),
    )
    _check_contract(generate_spiral(fuzzed, load_registry()))


def _drc_summary(board: Layout, rules: DrcRules) -> dict[str, float | None]:
    report = run_drc(board, rules)
    assert report is not None
    assert report.violation_count == 0 and report.passed, [v.objects for v in report.violations]
    return {s.kind.value: s.measured_min_mm for s in report.summaries}


@pytest.mark.req("REQ-F-05")
def test_default_example_passes_drc(board: Layout) -> None:
    """Acceptance (DEF-M2d-01 closed): the default 12/16 spiral passes run_drc; its tightest gaps are exactly s."""
    least = _drc_summary(board, default_design().drc_rules)
    assert least["trace_trace"] == pytest.approx(0.2, abs=1e-6)
    assert least["trace_via"] == pytest.approx(0.2, abs=1e-6)


@pytest.mark.req("REQ-F-05")
def test_d08_example_passes_drc_at_its_own_clearance(registry: Registry) -> None:
    """Worked example 2: D08 passes run_drc with trace and via rules at s 0.8 mm; the tightest gaps are exactly s."""
    design = d08_design()
    stack = generate_spiral(design, registry)
    assert isinstance(stack, BoardStack)
    least = _drc_summary(stack.boards[0], design.drc_rules)
    assert least["trace_trace"] == pytest.approx(0.8, abs=1e-6)
    assert least["trace_via"] == pytest.approx(0.8, abs=1e-6)


def _with_coil(design: DesignParameters, **changes: object) -> DesignParameters:
    assert isinstance(design.winding, SpiralWindingSpec)
    coil = dataclasses.replace(design.winding.coil, **changes)  # type: ignore[arg-type]
    return dataclasses.replace(design, winding=dataclasses.replace(design.winding, coil=coil))


@pytest.mark.req("REQ-F-06")
def test_turn_limit_reports_the_closing(board: Layout, registry: Registry) -> None:
    """D-031b: CF-11 closes with the lead arc (full), D08 with the half turn; catches a closing left unreported."""
    assert isinstance(board.detail, SpiralDetail) and board.detail.turn_limit.closing is TurnClosing.FULL
    d08 = generate_spiral(d08_design(), registry)
    assert isinstance(d08, BoardStack) and isinstance(d08.boards[0].detail, SpiralDetail)
    assert d08.boards[0].detail.turn_limit.closing is TurnClosing.HALF


@pytest.mark.req("REQ-F-01")
@pytest.mark.parametrize("turns_offset", [-1, 3])
def test_first_coil_angle_any_finite_value_is_normalised(turns_offset: int, board: Layout, registry: Registry) -> None:
    """D-031c: pi/2 + 2 pi k builds the same copper as pi/2 (within 1e-9 mm); a negative angle is no longer refused."""
    shifted = _with_coil(default_design(), first_coil_angle_rad=math.pi / 2 + turns_offset * 2 * math.pi)
    stack = generate_spiral(shifted, registry)
    assert isinstance(stack, BoardStack)
    for a, b in zip(stack.boards[0].vias, board.vias, strict=True):
        assert math.dist((a.x_mm, a.y_mm), (b.x_mm, b.y_mm)) <= 1e-9


@pytest.mark.req("REQ-F-19")
@pytest.mark.parametrize("angle", [math.nan, math.inf])
def test_non_finite_first_coil_angle_is_unbuildable(angle: float, registry: Registry) -> None:
    """D-031c: only a finite angle can be normalised; NaN or inf returns Unbuildable naming the input."""
    refused = generate_spiral(_with_coil(default_design(), first_coil_angle_rad=angle), registry)
    assert isinstance(refused, Unbuildable)
    assert refused.issues[0].pointers == ("/winding/coil/first_coil_angle_rad",)
