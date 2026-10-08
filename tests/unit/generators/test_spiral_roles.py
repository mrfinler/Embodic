"""UT-GEN-01 (roles part): the spiral generator classifies every interconnect path for EQ-23 (interfaces.md section 5).

Expectations come from the circuit and the copper, not from the generator's own bookkeeping: a lead is on the phase
whose chain starts at its first point, a tap stub on the phase whose chain ends there, the ring taps are the vias at the
stub ends in ring order. Delta needs the D08 design, because CF-11 has crossing links.
"""

import dataclasses
import math
from collections import Counter

import pytest
from tests.unit.generators.d08_example import d08_design
from tests.unit.generators.default_example import default_design

from embodic.generators import generate_spiral
from embodic.geometry.circuit import InterconnectRole, LineLead, NeutralLead, NeutralRing, PhaseLink
from embodic.geometry.layout import BoardStack, Layout, Via, ViaRole
from embodic.geometry.primitives import Arc
from embodic.model.design import DesignParameters
from embodic.model.vocabulary import ConnectionTopology, Phase
from embodic.results import load_registry

pytestmark = pytest.mark.req("REQ-F-11")
REGISTRY = load_registry()


def _board(design: DesignParameters, topology: ConnectionTopology, neutral_pad: bool = False) -> Layout:
    connection = dataclasses.replace(design.connection, topology=topology, neutral_pad=neutral_pad)
    stack = generate_spiral(dataclasses.replace(design, connection=connection), REGISTRY)
    assert isinstance(stack, BoardStack)
    return stack.boards[0]


def _chain_vias(board: Layout, phase: Phase) -> tuple[Via, Via]:
    """Return the ring vias where the chain of a phase starts and ends."""
    vias = {v.id: v for v in board.vias}
    circuit = next(pc for pc in board.circuit.phases if pc.phase is phase)
    return vias[circuit.groups[0].members[0].via_ids[0]], vias[circuit.groups[-1].members[0].via_ids[-1]]


def _near(point: tuple[float, float], via: Via) -> bool:
    return math.dist(point, (via.x_mm, via.y_mm)) <= via.pad_mm / 2


def _roles_of(board: Layout, kind: type[InterconnectRole]) -> list[InterconnectRole]:
    return [r for r in board.circuit.interconnect_roles if isinstance(r, kind)]


def test_star_roles_follow_the_copper_of_each_phase() -> None:
    """Catches a lead or tap stub classified on the wrong phase, or a path left without a role."""
    board = _board(default_design(), ConnectionTopology.STAR)
    paths = {p.id: p for p in board.paths}
    assert Counter(type(r) for r in board.circuit.interconnect_roles) == {PhaseLink: 3, NeutralRing: 1, LineLead: 3}
    assert sorted(r.path_id for r in board.circuit.interconnect_roles) == sorted(board.circuit.interconnect_path_ids)
    for role in _roles_of(board, LineLead):
        assert isinstance(role, LineLead)
        lead = paths[role.path_id]
        start, _ = _chain_vias(board, role.phase)
        assert _near(lead.primitives[0].start_point(), start)
        assert lead.net == next(pc.terminal_net for pc in board.circuit.phases if pc.phase is role.phase)
    for role in _roles_of(board, PhaseLink):
        assert isinstance(role, PhaseLink)
        _, end = _chain_vias(board, role.phase)
        assert _near(paths[role.path_id].primitives[0].start_point(), end)
        assert paths[role.path_id].net == "N"
    assert {r.phase for r in _roles_of(board, PhaseLink)} == set(Phase)  # type: ignore[attr-defined]


def test_star_ring_taps_are_the_stub_end_vias_in_ring_order() -> None:
    """Catches ring taps in the wrong order, which makes the ring segments span the wrong copper (EQ-23 l.1369)."""
    board = _board(default_design(), ConnectionTopology.STAR)
    paths = {p.id: p for p in board.paths}
    vias = {v.id: v for v in board.vias}
    (ring_role,) = _roles_of(board, NeutralRing)
    assert isinstance(ring_role, NeutralRing)
    arc = paths[ring_role.path_id].primitives[0]
    assert isinstance(arc, Arc)
    tap_vias = [vias[i] for i in ring_role.tap_via_ids]
    assert all(v.role is ViaRole.RING and v.net == "N" for v in tap_vias)
    stub_ends = [paths[r.path_id].primitives[-1].end_point() for r in _roles_of(board, PhaseLink)]  # type: ignore[attr-defined]
    assert sorted((round(v.x_mm, 9), round(v.y_mm, 9)) for v in tap_vias) == sorted(
        (round(x, 9), round(y, 9)) for x, y in stub_ends
    )
    tau, sign = 2.0 * math.pi, math.copysign(1.0, arc.sweep_rad)
    offsets = [(sign * (math.atan2(v.y_mm, v.x_mm) - arc.start_rad)) % tau for v in tap_vias]
    offsets = [0.0 if o > tau - 1e-9 else o for o in offsets]  # a tap at the ring start may land a rounding error early
    assert offsets == sorted(offsets)


def test_neutral_pad_lead_continues_a_tap_stub_and_stays_phase_link_copper() -> None:
    """Catches a NeutralLead role on the merged tap stub; Xcoil counts it in its phase link (U-E7, assumption)."""
    board = _board(default_design(), ConnectionTopology.STAR, neutral_pad=True)
    paths = {p.id: p for p in board.paths}
    merged = [p for p in board.paths if p.id in board.circuit.interconnect_path_ids and len(p.primitives) == 2]
    assert [p.net for p in merged] == ["N"]
    (role,) = (r for r in board.circuit.interconnect_roles if r.path_id == merged[0].id)
    assert isinstance(role, PhaseLink)
    assert _near(paths[role.path_id].primitives[0].start_point(), _chain_vias(board, role.phase)[1])
    assert not _roles_of(board, NeutralLead)
    assert Counter(type(r) for r in board.circuit.interconnect_roles) == {PhaseLink: 3, NeutralRing: 1, LineLead: 3}


def test_delta_roles_put_each_line_lead_on_the_merged_link_stub() -> None:
    """Catches a delta link classified on the wrong phase: link D<k> belongs to phase k (Xcoil l.1366).

    A delta lead continues the stub of the link that ends at its phase start, so the merged path is a LineLead.
    """
    board = _board(d08_design(), ConnectionTopology.DELTA)
    paths = {p.id: p for p in board.paths}
    assert Counter(type(r) for r in board.circuit.interconnect_roles) == {PhaseLink: 6, LineLead: 3}
    for role in _roles_of(board, LineLead):
        assert isinstance(role, LineLead)
        lead = paths[role.path_id]
        assert _near(lead.primitives[0].start_point(), _chain_vias(board, role.phase)[0])
        assert len(lead.primitives) == 2
    links = [r for r in board.circuit.interconnect_roles if isinstance(r, PhaseLink)]
    for role in links:
        net = paths[role.path_id].net
        assert net.startswith("D")
        assert role.phase is list(Phase)[int(net[1:])]
    assert Counter(r.phase for r in links) == {phase: 2 for phase in Phase}


@pytest.mark.parametrize("topology", [ConnectionTopology.OPEN])
def test_open_phases_have_no_interconnect_and_no_roles(topology: ConnectionTopology) -> None:
    """Catches roles invented for copper that is not built; an open layout must stay empty and consistent."""
    board = _board(default_design(), topology)
    assert board.circuit.interconnect_path_ids == () and board.circuit.interconnect_roles == ()


def test_hidden_interconnect_has_no_roles() -> None:
    """Catches roles recorded while draw_interconnect is off."""
    design = default_design()
    hidden = dataclasses.replace(design, connection=dataclasses.replace(design.connection, draw_interconnect=False))
    stack = generate_spiral(hidden, REGISTRY)
    assert isinstance(stack, BoardStack)
    circuit = stack.boards[0].circuit
    assert circuit.interconnect_path_ids == () and circuit.interconnect_roles == ()
