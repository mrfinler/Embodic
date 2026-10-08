"""UT-GEN-01, UT-GEN-02, UT-GEN-03 and UT-GEN-05 for the serpentine generator (REQ-F-34)."""

import math

import pytest
from tests.unit.generators.default_example import default_design

from embodic.drc import DrcCheckKind, run_drc
from embodic.errors import Severity, Unbuildable
from embodic.generators import GENERATORS, build_layout, generate_serpentine
from embodic.geometry.circuit import LineLead, NeutralLead, NeutralRing, PhaseLink
from embodic.geometry.details import SerpentineDetail
from embodic.geometry.layout import BoardStack
from embodic.model.validate import validate_design
from embodic.model.vocabulary import TopologyKind
from embodic.model.winding_specs import StackMode
from embodic.results import Registry, load_registry

from .make_example import example_design
from .support import per_phase, with_copper_count, with_winding

pytestmark = pytest.mark.req("REQ-F-34")
CLEARANCE_KINDS = {DrcCheckKind.TRACE_TRACE, DrcCheckKind.TRACE_VIA, DrcCheckKind.VIA_VIA}


@pytest.fixture(scope="module")
def registry() -> Registry:
    """Return the shipped equation registry."""
    return load_registry()


def _stack(design, registry: Registry) -> BoardStack:  # type: ignore[no-untyped-def]
    result = build_layout(design, registry)
    assert isinstance(result, BoardStack), result
    return result


def test_build_layout_dispatches_serpentine_to_the_port_not_the_stub(registry: Registry) -> None:
    """UT-GEN-02: catches a GENERATORS entry that still points to the stub, which returns Unbuildable."""
    assert GENERATORS[TopologyKind.SERPENTINE] is generate_serpentine
    stack = _stack(example_design(), registry)
    assert isinstance(stack.boards[0].detail, SerpentineDetail)
    assert stack.boards[0].topology is TopologyKind.SERPENTINE


def test_generate_serpentine_refuses_another_winding_with_type_error(registry: Registry) -> None:
    """UT-GEN-02: a spiral design is a dispatch bug, not user input."""
    with pytest.raises(TypeError):
        generate_serpentine(default_design(), registry)


def test_same_design_gives_the_same_stack_hash(registry: Registry) -> None:
    """UT-GEN-01: catches hidden state in the build (dict order, counters)."""
    design = example_design()
    assert _stack(design, registry).stack_hash == _stack(design, registry).stack_hash


@pytest.mark.parametrize("mode", [StackMode.SINGLE, StackMode.ONE_BOARD_PER_PHASE])
def test_circuit_ids_exist_and_every_winding_path_has_one_place(mode: StackMode, registry: Registry) -> None:
    """UT-GEN-01: every winding path is in exactly one Member or in interconnect_path_ids; ids and roles are complete.

    Catches a bus or link path that no circuit member lists (physics would drop its resistance) or listed twice.
    """
    design = example_design() if mode is StackMode.SINGLE else per_phase(example_design())
    for board in _stack(design, registry).boards:
        path_ids = {p.id for p in board.paths}
        members = [i for pc in board.circuit.phases for g in pc.groups for m in g.members for i in m.path_ids]
        assert len(members) == len(set(members))
        assert set(members) | set(board.circuit.interconnect_path_ids) == path_ids
        assert set(members).isdisjoint(board.circuit.interconnect_path_ids)
        via_ids = [i for pc in board.circuit.phases for g in pc.groups for m in g.members for i in m.via_ids]
        assert set(via_ids) <= {v.id for v in board.vias}
        roles = [r.path_id for r in board.circuit.interconnect_roles]
        assert sorted(roles) == sorted(board.circuit.interconnect_path_ids)
        assert board.detail is not None and board.derived


def test_interconnect_roles_follow_xcoil_items(registry: Registry) -> None:
    """UT-GEN-01 / D-031f: lead per phase, tap stub per phase, two ring segments, one neutral lead (Xcoil l.1361)."""
    (board,) = _stack(example_design(), registry).boards
    roles = board.circuit.interconnect_roles
    assert sorted(r.phase.value for r in roles if isinstance(r, LineLead)) == ["A", "B", "C"]
    assert sorted(r.phase.value for r in roles if isinstance(r, PhaseLink)) == ["A", "B", "C"]
    rings = [r for r in roles if isinstance(r, NeutralRing)]
    assert [len(r.tap_via_ids) for r in rings] == [2, 2]
    assert rings[0].tap_via_ids[1] == rings[1].tap_via_ids[0], "the two ring segments meet at the middle tap"
    assert sum(isinstance(r, NeutralLead) for r in roles) == 1
    assert {board.paths[r.path_id].net for r in roles if isinstance(r, LineLead)} == {"U", "V", "W"}


@pytest.mark.parametrize(
    ("layers", "valid"),
    [(1, True), (2, True), (4, True), (3, False), (5, False)],
)
def test_ut_gen_03_layers_per_phase_is_one_or_even(layers: int, valid: bool) -> None:
    """UT-GEN-03: catches an odd layer count that validates (Xcoil l.138 rounds it up)."""
    design = with_copper_count(with_winding(example_design(), layers_per_phase=layers), 3 * layers)
    codes = [i.code for i in validate_design(design) if i.severity is Severity.ERROR]
    assert ("INVALID_LAYERS_PER_PHASE" not in codes) is valid


@pytest.mark.parametrize(
    ("mode", "copper", "valid"),
    [
        (StackMode.SINGLE, 6, True),
        (StackMode.SINGLE, 2, False),
        (StackMode.ONE_BOARD_PER_PHASE, 2, True),
        (StackMode.ONE_BOARD_PER_PHASE, 6, False),
    ],
)
def test_ut_gen_03_copper_count_follows_the_stack_mode(
    mode: StackMode, copper: int, valid: bool, registry: Registry
) -> None:
    """UT-GEN-03: copper count is phases x layers (single) or layers (per phase); the generator refuses a mismatch too.

    Catches a stack-up for one mode used in the other: validate_design names the pointers and the generator returns
    Unbuildable instead of indexing past the stack-up.
    """
    design = with_copper_count(with_winding(example_design(), stack_mode=mode), copper)
    codes = [i.code for i in validate_design(design) if i.code == "INVALID_SERPENTINE_COPPER_COUNT"]
    assert (codes == []) is valid
    result = build_layout(design, registry)
    assert isinstance(result, BoardStack) is valid
    if not valid:
        assert isinstance(result, Unbuildable)
        assert [i.code for i in result.issues] == ["UNBUILDABLE_SERPENTINE_COPPER_COUNT"]


@pytest.mark.parametrize(
    ("gap", "code"), [(-0.1, "INVALID_NEGATIVE"), (0.0, None), (10.0, None), (10.5, "RANGE_ABOVE_SUPPORTED")]
)
def test_ut_gen_03_board_gap_follows_the_xcoil_clamp_range(gap: float, code: str | None) -> None:
    """UT-GEN-03: board_gap_mm outside 0 to 10 mm (Xcoil l.127) is reported on its pointer."""
    codes = [
        i.code for i in validate_design(per_phase(example_design(), gap)) if i.pointers == ("/winding/board_gap_mm",)
    ]
    assert codes == ([code] if code else [])


def test_ut_gen_05_one_board_per_phase(registry: Registry) -> None:
    """UT-GEN-05: three boards in phase order, each with its own phase, z offset by the board pitch, no interconnect."""
    gap = 0.5
    design = per_phase(example_design(), gap)
    stack = _stack(design, registry)
    assert len(stack.boards) == 3
    thickness = design.stackup.board_thickness_mm()
    assert stack.board_thickness_mm == thickness and stack.board_gap_mm == gap
    assert stack.stack_thickness_mm == pytest.approx(3 * thickness + 2 * gap, abs=1e-12)
    base_z = design.stackup.copper_z_mm()
    for k, board in enumerate(stack.boards):
        assert [pc.phase.value for pc in board.circuit.phases] == ["ABC"[k]]
        assert {p.phase.value for p in board.paths if p.phase} == {"ABC"[k]}
        assert {v.net for v in board.vias} == {f"PHASE_{'ABC'[k]}"}
        assert not board.pads and not board.circuit.interconnect_path_ids and not board.circuit.interconnect_roles
        for name, z in board.copper_z_mm.items():
            assert z == pytest.approx(base_z[name] + k * (thickness + gap), abs=1e-12)


def test_ut_gen_05_single_mode_ignores_the_board_gap(registry: Registry) -> None:
    """UT-GEN-05: catches a gap that leaks into a one-board stack (Xcoil l.689 and l.695)."""
    a, b = (with_winding(example_design(), board_gap_mm=gap) for gap in (0.1, 0.5))
    stack_a, stack_b = _stack(a, registry), _stack(b, registry)
    assert stack_a.boards[0].layout_hash == stack_b.boards[0].layout_hash
    assert stack_a.board_gap_mm == stack_b.board_gap_mm == 0.0


def test_ut_gen_05_a_via_of_one_board_never_meets_the_copper_of_another(registry: Registry) -> None:
    """UT-GEN-05 / Xcoil DRC-05: wide bundles on one board break via clearance; on three boards they pass.

    Catches a stack that still puts the other phases' copper on the board of a through via.
    """
    wide = with_winding(example_design(), turns=12, trace_width_mm=0.3, clearance_mm=0.2)
    single = build_layout(with_copper_count(wide, 6), registry)
    assert isinstance(single, BoardStack)
    report = run_drc(single.boards[0], wide.drc_rules)
    assert report is not None and any(v.kind is DrcCheckKind.TRACE_VIA for v in report.violations)
    separate = _stack(per_phase(wide), registry)
    for board in separate.boards:
        report = run_drc(board, wide.drc_rules)
        assert report is not None
        assert not any(v.kind in CLEARANCE_KINDS for v in report.violations)


def test_the_example_builds_drc_clean_with_xcoils_envelope(registry: Registry) -> None:
    """Catches an envelope that leaves out the terminal pads (Xcoil rMaxAll): copper must lie inside it."""
    design = example_design()
    (board,) = _stack(design, registry).boards
    radii = [
        math.hypot(x, y)
        for p in board.paths
        for prim in p.primitives
        for x, y in (prim.start_point(), prim.end_point())
    ]
    assert min(radii) >= board.envelope_mm[0] - 1e-9 and max(radii) <= board.envelope_mm[1] + 1e-9
