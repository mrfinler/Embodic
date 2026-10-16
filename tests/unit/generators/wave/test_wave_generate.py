"""UT-GEN-04: wave validation, refusals and the shape of the generated board (REQ-F-35)."""

import dataclasses
import math
from typing import Any

import pytest
from hypothesis import event, example, given, settings
from hypothesis import strategies as st

from embodic.api import compute
from embodic.errors import IssueCategory, Severity, Unbuildable
from embodic.generators.wave import generate_wave
from embodic.geometry.circuit import LineLead, NeutralLead, NeutralRing, PhaseLink
from embodic.geometry.layout import BoardStack, Layout, ViaRole
from embodic.geometry.paths import is_continuous
from embodic.model.design import DesignParameters
from embodic.model.provenance import derive_provenance
from embodic.model.stackup import generate_even_stackup
from embodic.model.vocabulary import ConnectionTopology, Phase
from embodic.model.winding_specs import SpiralWindingSpec, WaveStyle, WaveWindingSpec
from embodic.results import Registry, load_registry

from ..hostile_sizes import HOSTILE_SETTINGS, WIDTHS, Sizes, check_hostile_build, hostile_sizes
from .designs import wave

pytestmark = pytest.mark.req("REQ-F-35")

STYLES = list(WaveStyle)


REGISTRY = load_registry()


@pytest.fixture(scope="module")
def registry() -> Registry:
    """Return the packaged registry, loaded once."""
    return REGISTRY


def _board(design: DesignParameters, registry: Registry) -> Layout:
    stack = generate_wave(design, registry)
    assert isinstance(stack, BoardStack), getattr(stack, "issues", None)
    assert len(stack.boards) == 1 and stack.board_gap_mm == 0.0
    return stack.boards[0]


def _codes(result: Any) -> list[str]:
    assert isinstance(result, Unbuildable)
    return [i.code for i in result.issues]


def _check_contract(result: BoardStack | Unbuildable) -> None:
    """Every path is in the circuit exactly once or is interconnect; every referenced via exists."""
    if isinstance(result, Unbuildable):
        return
    board = result.boards[0]
    members = [m for pc in board.circuit.phases for g in pc.groups for m in g.members]
    listed = [i for m in members for i in m.path_ids] + list(board.circuit.interconnect_path_ids)
    assert sorted(listed) == sorted(p.id for p in board.paths)
    assert all(v in {via.id for via in board.vias} for m in members for v in m.via_ids)


@pytest.mark.parametrize("style", STYLES)
@pytest.mark.parametrize("phases", [1, 2, 3])
def test_ut_gen_04_each_style_builds_for_one_two_and_three_phases(
    style: WaveStyle, phases: int, registry: Registry
) -> None:
    """UT-GEN-04. Catches a style that refuses or crashes for a phase count Xcoil builds (m = 1, 2, 3)."""
    stack = generate_wave(wave(style, phases=phases, poles=8), registry)
    assert isinstance(stack, BoardStack), getattr(stack, "issues", None)
    _check_contract(stack)
    assert [pc.phase for pc in stack.boards[0].circuit.phases] == list(Phase)[:phases]


@pytest.mark.parametrize("layers", [2, 4, 6])
def test_ut_gen_04_copper_count_even_and_at_least_two_builds(layers: int, registry: Registry) -> None:
    """UT-GEN-04. Catches a layer loop that skips the T or B parity: layer i carries T tracks when i is even."""
    board = _board(wave(layers=layers), registry)
    assert board.copper_layers == tuple(f"L{i + 1}" for i in range(layers))
    per_layer = [
        sum(1 for p in board.paths if p.layer == name and p.element is not None) for name in board.copper_layers
    ]
    assert per_layer == [90, 96] * (layers // 2)


@pytest.mark.parametrize("copper", [1, 3, 5])
def test_ut_gen_04_odd_or_single_copper_count_is_unbuildable(copper: int, registry: Registry) -> None:
    """UT-GEN-04. Catches a wave built on an odd stack: T and B tracks come in pairs (Xcoil LAYERS_ODD)."""
    design = dataclasses.replace(wave(), stackup=generate_even_stackup(copper, 0.0696, 1.6))
    result = generate_wave(design, registry)
    assert _codes(result) == ["UNBUILDABLE_WAVE_LAYER_COUNT"]
    assert result.issues[0].pointers == ("/stackup/layers",)


def test_wrong_winding_kind_is_a_dispatch_bug(registry: Registry) -> None:
    """Catches a generator that quietly accepts a spiral design (interfaces.md section 6)."""
    design = dataclasses.replace(wave(), winding=SpiralWindingSpec.__new__(SpiralWindingSpec))
    with pytest.raises(TypeError, match="wave winding"):
        generate_wave(design, registry)


def test_same_design_gives_the_same_stack_hash(registry: Registry) -> None:
    """Catches hidden state (a cache, an ordering from a set) in the builder."""
    first, second = generate_wave(wave(), registry), generate_wave(wave(), registry)
    assert isinstance(first, BoardStack) and isinstance(second, BoardStack)
    assert first.stack_hash == second.stack_hash


def test_two_poles_with_three_phases_cannot_place_terminals(registry: Registry) -> None:
    """Xcoil WAVE_MIN_POLES: a phase belt needs a second pole pair to put its minus terminal."""
    result = generate_wave(wave(poles=2, turns=1), registry)
    assert "UNBUILDABLE_WAVE_MIN_POLES" in _codes(result)
    assert result.issues[0].pointers == ("/rotor/poles",)


@pytest.mark.parametrize("style", STYLES)
def test_turn_limit_is_the_largest_count_that_builds(style: WaveStyle, registry: Registry) -> None:
    """Catches a refusal limit that disagrees with the builder: turns = limit builds, limit + 1 is refused."""
    refused = generate_wave(wave(style, turns=40), registry)
    (issue,) = [i for i in refused.issues if i.pointers == ("/winding/turns",)]  # type: ignore[union-attr]
    assert isinstance(issue.limit, int) and 1 <= issue.limit < 40
    assert isinstance(generate_wave(wave(style, turns=issue.limit), registry), BoardStack)
    assert isinstance(generate_wave(wave(style, turns=issue.limit + 1), registry), Unbuildable)


@pytest.mark.parametrize(("style", "r_inner"), [(WaveStyle.INVOLUTE, 5.0), (WaveStyle.CHORD, 4.0)])
def test_no_room_inside_the_via_ring_for_the_group_links_is_refused(
    style: WaveStyle, r_inner: float, registry: Registry
) -> None:  # fmt: skip
    """Xcoil R_TOO_SMALL (engine.js l.1928, the same inputs refused in Xcoil): the links need room inside the ring."""
    result = generate_wave(wave(style, turns=1, poles=8, r_inner_mm=r_inner, r_outer_mm=30.0), registry)
    assert _codes(result) == ["UNBUILDABLE_WAVE_LINK_ROOM"]
    assert result.issues[0].pointers == ("/winding/r_inner_mm",)


def test_nets_follow_d022(registry: Registry) -> None:
    """D-022. Catches a phase track on an interconnect net or a lead on a phase net."""
    board = _board(wave(), registry)
    ic = set(board.circuit.interconnect_path_ids)
    assert {p.net for p in board.paths if p.id not in ic} == {"PHASE_A", "PHASE_B", "PHASE_C"}
    assert {p.net for p in board.paths if p.id in ic} == {"U", "V", "W", "N"}
    assert {v.net for v in board.vias} == {"PHASE_A", "PHASE_B", "PHASE_C"}
    assert sorted(p.label for p in board.pads) == ["N", "U", "V", "W"]


def test_star_interconnect_roles(registry: Registry) -> None:
    """Catches an interconnect path with no role or the wrong one: physics reads only the roles (section 5)."""
    board = _board(wave(), registry)
    roles = board.circuit.interconnect_roles
    assert (
        sorted(type(r).__name__ for r in roles) == ["LineLead"] * 3 + ["NeutralLead", "NeutralRing"] + ["PhaseLink"] * 3
    )
    ring = next(r for r in roles if isinstance(r, NeutralRing))
    taps = [board.vias[i] for i in ring.tap_via_ids]
    assert [v.role for v in taps] == [ViaRole.TERMINAL] * 3 and len({v.net for v in taps}) == 3
    leads = {r.phase for r in roles if isinstance(r, LineLead)}
    assert leads == set(Phase)
    assert any(isinstance(r, NeutralLead) for r in roles)


@pytest.mark.parametrize("style", STYLES)
def test_star_tap_stubs_are_phase_links_that_start_on_their_own_terminal_via(
    style: WaveStyle, registry: Registry
) -> None:
    """Catches DEF-U-M3b-01: the tap stubs sat in the ring path, so the ring resistance between taps counted stubs.

    Each stub is the PhaseLink of the phase whose terminal via it starts on, and the ring path holds the arc only.
    """
    board = _board(wave(style), registry)
    paths = {p.id: p for p in board.paths}
    for role in board.circuit.interconnect_roles:
        if isinstance(role, PhaseLink):
            x, y = paths[role.path_id].primitives[0].start_point()
            (via,) = [v for v in board.vias if math.dist((v.x_mm, v.y_mm), (x, y)) < 1e-9]
            assert via.net == f"PHASE_{role.phase.value}" and via.role is ViaRole.TERMINAL
        if isinstance(role, NeutralRing):
            assert {type(q).__name__ for q in paths[role.path_id].primitives} == {"Arc"}


@pytest.mark.parametrize("topology", [ConnectionTopology.STAR, ConnectionTopology.DELTA])
@pytest.mark.parametrize("style", STYLES)
def test_every_interconnect_path_is_one_continuous_chain(
    style: WaveStyle, topology: ConnectionTopology, registry: Registry
) -> None:
    """Catches DEF-U-M3b-01: a ring item of stubs and an arc is no chain (interfaces.md section 5).

    As one CopperPath its pieces are neighbours by index only, so DRC rule 1 exempts the wrong pairs.
    """
    design = wave(style)
    design = dataclasses.replace(design, connection=dataclasses.replace(design.connection, topology=topology))
    board = _board(design, registry)
    broken = [
        p.id for p in board.paths if p.id in board.circuit.interconnect_path_ids and not is_continuous(p.primitives)
    ]
    assert broken == []


def test_delta_links_belong_to_their_phase(registry: Registry) -> None:
    """Catches a delta link attributed to the wrong phase: Xcoil's link[k] is net D<k>, in series with phase k."""
    design = dataclasses.replace(
        wave(), connection=dataclasses.replace(wave().connection, topology=ConnectionTopology.DELTA)
    )
    board = _board(design, registry)
    links = {r.phase for r in board.circuit.interconnect_roles if isinstance(r, PhaseLink)}
    assert links == set(Phase)
    assert {p.net for p in board.paths if p.id in board.circuit.interconnect_path_ids} == {
        "U",
        "V",
        "W",
        "D0",
        "D1",
        "D2",
    }


def _connected(style: WaveStyle, topology: ConnectionTopology, draw: bool = True) -> DesignParameters:
    design = wave(style)
    connection = dataclasses.replace(design.connection, topology=topology, draw_interconnect=draw)
    return dataclasses.replace(design, connection=connection)


def test_overlap_delta_connection_that_cannot_be_drawn_is_a_warning_on_the_stack(registry: Registry) -> None:
    """Catches D-036 d: Xcoil's INTERCONNECT_EXTERNAL warning (engine.js l.2190) was dropped for the overlap wave.

    The overlap winding has one terminal per rim, so the delta connection is left to the user.
    """
    stack = generate_wave(_connected(WaveStyle.OVERLAP, ConnectionTopology.DELTA), registry)
    assert isinstance(stack, BoardStack)
    (issue,) = stack.issues
    assert (issue.code, issue.severity, issue.category) == (
        "RANGE_WAVE_INTERCONNECT_EXTERNAL",
        Severity.WARNING,
        IssueCategory.UNSUPPORTED_RANGE,
    )
    assert issue.message == (
        "The overlapping radial winding has one terminal per rim: make the delta connection externally "
        "(star is routed on-board)."
    )
    assert not any(p.net.startswith("D") for p in stack.boards[0].paths)


@pytest.mark.parametrize(
    ("style", "topology", "draw"),
    [
        (WaveStyle.OVERLAP, ConnectionTopology.STAR, True),
        (WaveStyle.OVERLAP, ConnectionTopology.DELTA, False),
        (WaveStyle.OVERLAP, ConnectionTopology.OPEN, True),
        (WaveStyle.INVOLUTE, ConnectionTopology.DELTA, True),
        (WaveStyle.JOG, ConnectionTopology.STAR, True),
        (WaveStyle.CHORD, ConnectionTopology.DELTA, True),
    ],
    ids=["overlap-star", "overlap-delta-not-asked", "overlap-open", "involute-delta", "jog-star", "chord-delta"],
)
def test_no_interconnect_warning_when_it_is_drawn_or_not_asked_for(
    style: WaveStyle, topology: ConnectionTopology, draw: bool, registry: Registry
) -> None:
    """Catches a warning for an interconnect nobody asked for, or one the board does carry."""
    stack = generate_wave(_connected(style, topology, draw), registry)
    assert isinstance(stack, BoardStack)
    assert stack.issues == ()


def test_compute_reports_the_wave_stack_warning_in_the_outcome(registry: Registry) -> None:
    """Catches D-035 a for the wave: the facade must merge BoardStack.issues, or the user never sees the warning."""
    design = _connected(WaveStyle.OVERLAP, ConnectionTopology.DELTA)
    outcome = compute(design, derive_provenance(design, None, ()), registry=registry)
    assert outcome is not None and outcome.boards is not None
    assert [i.code for i in outcome.issues if i.severity is Severity.WARNING] == ["RANGE_WAVE_INTERCONNECT_EXTERNAL"]


@pytest.mark.parametrize("style", STYLES)
def test_each_phase_chain_has_xcoils_element_count(style: WaveStyle, registry: Registry) -> None:
    """Catches a dropped or doubled series element.

    T/B styles: 4 q pp - 2 track elements per phase (two terminal slots have no T track) plus the group link.
    Overlap: one track per slot of the phase's belts, 2 q pp, less the one removed slot, and no link.
    """
    q, pp = 2, 8
    board = _board(wave(style, turns=q), registry)
    expected = 2 * q * pp - 1 if style is WaveStyle.OVERLAP else 4 * q * pp - 2 + 1
    assert [len(pc.groups) for pc in board.circuit.phases] == [expected] * 3
    parallel = {len(g.members) for pc in board.circuit.phases for g in pc.groups}
    assert parallel == {1}  # two layers: one copy of each track position


def test_extra_layer_pairs_put_track_copies_in_parallel(registry: Registry) -> None:
    """Catches layers that are not parallel copies: with 4 layers every track position has 2 members."""
    board = _board(wave(layers=4), registry)
    sizes = [len(g.members) for pc in board.circuit.phases for g in pc.groups]
    assert sizes.count(2) == len(sizes) - 3 and sizes.count(1) == 3  # the three group links are single members


def test_terminals_sit_on_the_outer_ring_vias(registry: Registry) -> None:
    """Catches a terminal on the wrong via: the plus terminals are the line pads' feeds, 6 vias in all."""
    board = _board(wave(), registry)
    assert sum(v.role is ViaRole.TERMINAL for v in board.vias) == 6
    radii = [math.hypot(v.x_mm, v.y_mm) for v in board.vias if v.role is ViaRole.TERMINAL]
    assert radii == [pytest.approx(42.175, abs=1e-3)] * 6


@pytest.mark.req("REQ-F-19")
@settings(max_examples=40, deadline=None)
@example(r_inner=float("nan"), span=18.0, w=0.4, s=0.2, pad=0.6, turns=2, poles=16, layers=2, style="involute")
@example(r_inner=22.0, span=18.0, w=0.4, s=0.0, pad=0.6, turns=200, poles=200, layers=2, style="jog")
@example(r_inner=22.0, span=18.0, w=1e-9, s=0.2, pad=0.6, turns=2, poles=16, layers=16, style="chord")
@example(  # DEF-M3b-03: biarc divides by zero when p0 == p1 and the width is denormal
    r_inner=1.0, span=1.0, w=1.175494351e-38, s=1.401298464324817e-45, pad=1.401298464324817e-45,
    turns=1, poles=4, layers=2, style="involute",
)  # fmt: skip
@given(
    r_inner=st.floats(-5.0, 60.0) | st.just(float("nan")) | st.just(float("inf")),
    span=st.floats(-5.0, 40.0),
    w=st.floats(-0.1, 3.0),
    s=st.floats(-0.1, 1.0),
    pad=st.floats(0.0, 2.0),
    turns=st.integers(-1, 250),
    poles=st.sampled_from([0, 1, 2, 4, 8, 16, 20, 200, 202]),
    layers=st.sampled_from([1, 2, 4, 6, 18]),
    style=st.sampled_from([s.value for s in WaveStyle]),
)
def test_fuzzed_inputs_give_a_stack_or_unbuildable_never_an_exception(
    r_inner: float, span: float, w: float, s: float, pad: float, turns: int, poles: int, layers: int, style: str
) -> None:  # fmt: skip
    """UT-GEN-01 for wave. Catches an exception, an unbounded build or an incomplete circuit on hostile numbers."""
    design = wave(WaveStyle(style), turns=turns, poles=poles, layers=layers)
    assert isinstance(design.winding, WaveWindingSpec)
    spec = dataclasses.replace(
        design.winding, r_inner_mm=r_inner, r_outer_mm=r_inner + span, trace_width_mm=w, clearance_mm=s
    )
    fuzzed = dataclasses.replace(design, winding=spec, vias=dataclasses.replace(design.vias, pad_mm=pad))
    _check_contract(generate_wave(fuzzed, REGISTRY))


_EXAMPLE = wave()
_EXAMPLE_SIZES = Sizes(
    clearance_mm=_EXAMPLE.winding.clearance_mm,  # type: ignore[union-attr]
    pad_mm=_EXAMPLE.vias.pad_mm,
    terminal_pad_mm=_EXAMPLE.connection.terminal_pad_mm,
)
_TINIEST = Sizes(clearance_mm=5e-324, pad_mm=5e-324, terminal_pad_mm=5e-324)


@pytest.mark.slow
@pytest.mark.req("REQ-F-19")
@HOSTILE_SETTINGS
@example(style=WaveStyle.INVOLUTE, r_inner=1.0, span=1.0, width="example", turns=1, sizes=_TINIEST)  # DEF-M3b-03 shape
@example(
    style=WaveStyle.INVOLUTE, r_inner=22.0, span=18.0, width="example", turns=2,
    sizes=dataclasses.replace(_EXAMPLE_SIZES, pad_mm=2.2250738585072014e-308),
)  # fmt: skip  # smallest normal float
@given(
    style=st.sampled_from(list(WaveStyle)),
    r_inner=st.floats(1.0, 60.0),
    span=st.floats(1.0, 40.0),
    width=st.sampled_from(WIDTHS),
    turns=st.integers(1, 30),
    sizes=hostile_sizes(_EXAMPLE.drc_rules, _EXAMPLE_SIZES, terminal_pad=True),
)
def test_d030_hostile_clearance_and_pads_are_built_or_refused_within_bounds(
    style: WaveStyle, r_inner: float, span: float, width: str, turns: int, sizes: Sizes
) -> None:
    """D-030 lower bounds (d030_property_spec.md): a positive clearance, via pad or terminal pad below the DRC rules.

    Defect caught: a division by one of these sizes (DEF-M3b-03 for the width), a count derived from 1/size without the
    width floor (the unbounded build of D-030), a non-finite coordinate, or an exception instead of Unbuildable. The
    width is valid by construction, so the width refusal never stops the build.
    """
    assert isinstance(_EXAMPLE.winding, WaveWindingSpec)
    width_mm = _EXAMPLE.drc_rules.min_trace_width_mm if width == WIDTHS[0] else _EXAMPLE.winding.trace_width_mm

    def build(at: Sizes) -> BoardStack | Unbuildable:
        design = wave(
            style, turns=turns, r_inner_mm=r_inner, r_outer_mm=r_inner + span, trace_width_mm=width_mm,
            clearance_mm=at.clearance_mm,
        )  # fmt: skip
        design = dataclasses.replace(
            design,
            vias=dataclasses.replace(design.vias, pad_mm=at.pad_mm),
            connection=dataclasses.replace(design.connection, terminal_pad_mm=at.terminal_pad_mm),
        )
        return generate_wave(design, REGISTRY)

    event(
        f"example reached: {check_hostile_build(lambda: build(sizes), lambda: build(_EXAMPLE_SIZES), _check_contract)}"
    )
