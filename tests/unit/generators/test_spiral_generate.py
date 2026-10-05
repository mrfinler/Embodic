"""Spiral generator on the default 12/16 example (CF-11): geometry properties, contract, determinism and DRC."""

import dataclasses
import math
from collections import Counter

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from tests.unit.generators.d08_example import d08_design
from tests.unit.generators.default_example import default_design
from tests.unit.model.designs import serpentine_design

from embodic.drc import run_drc
from embodic.errors import Unbuildable
from embodic.generators import GENERATORS, build_layout, generate_spiral, generate_wave
from embodic.geometry.details import SpiralDetail, TurnLimitReason
from embodic.geometry.discretise import discretise
from embodic.geometry.layout import BoardStack, Layout, ViaRole
from embodic.geometry.paths import CopperPath, is_continuous
from embodic.geometry.primitives import PrimitiveRole
from embodic.geometry.transforms import mirror, reverse_path, rotate
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
    assert Counter(p.polarity for p in board.paths) == {1: 24}  # 12/16: every coil is positive (ACBACB...)


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
    """UT-GEN-02: build_layout routes by topology; a stub refuses; a wrong winding is a TypeError."""
    assert set(GENERATORS) == set(TopologyKind)
    assert isinstance(build_layout(default_design(), registry), BoardStack)
    refused = build_layout(serpentine_design(), registry)
    assert isinstance(refused, Unbuildable)
    assert [i.code for i in refused.issues] == ["UNBUILDABLE_UNSUPPORTED_TOPOLOGY"]
    with pytest.raises(TypeError):
        generate_wave(default_design(), registry)
    with pytest.raises(TypeError):
        generate_spiral(serpentine_design(), registry)


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
