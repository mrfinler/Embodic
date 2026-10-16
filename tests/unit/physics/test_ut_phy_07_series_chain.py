"""UT-PHY-07 (REQ-F-03 criterion c): the series chain EMF is the phasor sum of the member EMFs, each at its own z.

Specification: docs/phase3/architecture/v3_contract_rulings.md section 3 (D-051e). The test checks the arithmetic of the
chain. It does not show that a series pair behaves this way on a real board, which stays unresolved under D-020.
"""

import math
from collections.abc import Callable, Mapping

import numpy as np
import pytest
from numpy.typing import NDArray
from tests.unit.generators.test_spiral_series_fan import series_design

from embodic.generators import generate_spiral
from embodic.geometry.circuit import Circuit, Member, ParallelGroup, PhaseCircuit
from embodic.geometry.layout import BoardStack, Layout
from embodic.geometry.paths import CopperPath
from embodic.model.design import DesignParameters
from embodic.model.vocabulary import ConnectionTopology, Phase
from embodic.physics import analyse
from embodic.physics.circuit import solve_phase_circuit
from embodic.physics.emf import FieldTable, field_table, integrate_path
from embodic.physics.field import symmetry_plane_mm
from embodic.results import load_registry

pytestmark = pytest.mark.req("REQ-F-03")

REL = 1e-9
EDGE_DECAY_MM = 1.0  # only the EC-05 edge sums read it, never the flux linkage that these tests compare
OMEGA_M = 1.0  # only the circulating loss reads it, and a member alone circulates nothing
Complex = NDArray[np.complex128]


def solve_chain(flux: Mapping[int, Complex], groups: list[list[int]], resistance: Mapping[int, float]) -> Complex:
    """Return the EMF phasors of a phase A whose series groups each hold one member with the given path ids."""
    phase = PhaseCircuit(
        phase=Phase.A,
        groups=tuple(ParallelGroup(members=(Member(path_ids=tuple(g), via_ids=()),)) for g in groups),
        terminal_net="A",
    )
    circuit = Circuit(phases=(phase,), topology=ConnectionTopology.OPEN, interconnect_path_ids=())
    solution = solve_phase_circuit(circuit, flux, resistance, {}, OMEGA_M)
    return solution.phase_emf_phasor_v_s_per_rad[Phase.A]


@pytest.fixture(scope="module")
def flux_linkage() -> tuple[Complex, Complex]:
    """Return two path flux linkages of equal magnitude at every harmonic, 90 degrees apart."""
    first = np.array([2.0 * np.exp(0.3j), 0.5 * np.exp(-1.1j), 0.1 + 0.0j])
    return first, 1j * first


# The member resistances differ, so an EMF that leaks a resistance weight into a series sum is seen.
RESISTANCE = {0: 0.5, 1: 2.0}


def test_ut_phy_07_series_chain_of_two_members_adds_as_a_phasor_sum(flux_linkage: tuple[Complex, Complex]) -> None:
    """Catches a scalar sum of magnitudes (2 times one member) or a phase lost between the two groups (0).

    Two members of equal magnitude 90 degrees apart add to sqrt(2) times one member, at every harmonic.
    """
    first, second = flux_linkage
    chain = solve_chain({0: first, 1: second}, [[0], [1]], RESISTANCE)
    alone_first = solve_chain({0: first}, [[0]], RESISTANCE)
    alone_second = solve_chain({1: second}, [[1]], RESISTANCE)
    assert chain == pytest.approx(alone_first + alone_second, rel=REL, abs=0.0)
    assert np.abs(chain) == pytest.approx(math.sqrt(2.0) * np.abs(alone_first), rel=REL, abs=0.0)


def test_ut_phy_07_a_reversed_member_enters_the_series_sum_with_its_sign(flux_linkage: tuple[Complex, Complex]) -> None:
    """Catches a chain that adds the magnitude of a reversed member: its EMF must subtract.

    The signature has no polarity input, so a reversed member shows as a negated flux linkage.
    """
    first, second = flux_linkage
    chain = solve_chain({0: first, 1: -second}, [[0], [1]], RESISTANCE)
    alone_first = solve_chain({0: first}, [[0]], RESISTANCE)
    alone_reversed = solve_chain({1: -second}, [[1]], RESISTANCE)
    assert chain == pytest.approx(alone_first + alone_reversed, rel=REL, abs=0.0)
    unreversed_sum = alone_first + solve_chain({1: second}, [[1]], RESISTANCE)
    assert np.max(np.abs(chain - unreversed_sum)) > 1e-6 * np.max(np.abs(chain))  # the sign is visible in this case


@pytest.fixture(scope="module")
def series_board() -> tuple[DesignParameters, BoardStack]:
    """Return the CF-11 spiral with k = 2 series pairs of test_spiral_series_fan.py, generated once."""
    design = series_design("CF-11", 2)
    stack = generate_spiral(design, load_registry())
    assert isinstance(stack, BoardStack), [(i.code, i.pointers) for i in stack.issues]
    return design, stack


def path_z_mm(layout: Layout, path: CopperPath) -> float:
    """Return the copper z of the layer that the path lies on."""
    return layout.copper_z_mm[path.layer]


def member_chain_emf_by_phase(
    design: DesignParameters, stack: BoardStack, z_of_path: Callable[[Layout, CopperPath], float]
) -> dict[Phase, complex]:
    """Return the fundamental EMF of each phase as the sum of its members' EMFs, each from a one-member circuit.

    A member's flux linkage is the sum over its paths, each integrated against the field table at the copper z that
    `z_of_path` gives it.
    """
    layout = stack.boards[0]
    rotor = design.rotor
    plane = symmetry_plane_mm(rotor, stack.stack_thickness_mm)
    tables: dict[float, FieldTable] = {}
    paths = {p.id: p for p in layout.paths}
    emf: dict[Phase, complex] = {}
    for phase in layout.circuit.phases:
        total = 0j
        for group in phase.groups:
            for member in group.members:
                flux: dict[int, Complex] = {}
                for i in member.path_ids:
                    z = z_of_path(layout, paths[i])
                    if z not in tables:
                        tables[z] = field_table(rotor, plane, z + rotor.air_gap_mm, (1,))
                    flux[i] = integrate_path(
                        paths[i].primitives, tables[z], rotor.poles // 2, design.analysis.max_segment_mm, EDGE_DECAY_MM
                    ).flux_linkage_t_mm2
                alone = PhaseCircuit(
                    phase=phase.phase, groups=(ParallelGroup(members=(member,)),), terminal_net=phase.terminal_net
                )
                circuit = Circuit(phases=(alone,), topology=layout.circuit.topology, interconnect_path_ids=())
                resistance = dict.fromkeys(member.path_ids, 1.0)
                vias = dict.fromkeys(member.via_ids, 1.0)
                solved = solve_phase_circuit(circuit, flux, resistance, vias, OMEGA_M)
                total += complex(solved.phase_emf_phasor_v_s_per_rad[phase.phase][0])
        emf[phase.phase] = total
    return emf


@pytest.fixture(scope="module")
def analysed_fundamental(series_board: tuple[DesignParameters, BoardStack]) -> dict[Phase, complex]:
    """Return the fundamental phase EMF phasor of analyse(), rebuilt from its magnitude and angle."""
    design, stack = series_board
    result = analyse(design, stack, {}, load_registry())
    assert result is not None
    return {
        p.phase: complex(p.ke_peak_v_s_per_rad.value * np.exp(1j * p.emf_phasor_angle_rad.value)) for p in result.phases
    }


def test_ut_phy_07_generated_series_board_phase_emf_is_the_sum_of_its_member_emfs_each_at_its_own_z(
    series_board: tuple[DesignParameters, BoardStack], analysed_fundamental: dict[Phase, complex]
) -> None:
    """Catches a wrong z in the chain (DEF-M3a-01 added k times the pitch to a z that already held it).

    A member of the series board has paths on four copper layers, so the precondition is that the z values of the
    paths of every member differ, as a case with one z could not see a wrong z.
    """
    design, stack = series_board
    layout = stack.boards[0]
    paths = {p.id: p for p in layout.paths}
    spirals = [m for pc in layout.circuit.phases for g in pc.groups for m in g.members]
    for member in spirals:
        assert len({path_z_mm(layout, paths[i]) for i in member.path_ids}) > 1

    expected = member_chain_emf_by_phase(design, stack, path_z_mm)
    assert analysed_fundamental.keys() == expected.keys() == {Phase.A, Phase.B, Phase.C}
    for phase, emf in expected.items():
        assert analysed_fundamental[phase] == pytest.approx(emf, rel=REL, abs=0.0), phase


def test_ut_phy_07_the_member_sum_at_one_z_for_every_member_differs_from_analyse(
    series_board: tuple[DesignParameters, BoardStack], analysed_fundamental: dict[Phase, complex]
) -> None:
    """Control: the same sum with every path at the z of the first member's first spiral differs by more than 1e-6.

    Catches a test that cannot see a wrong z, which would pass whatever z the chain used.
    """
    design, stack = series_board
    layout = stack.boards[0]
    paths = {p.id: p for p in layout.paths}
    first_member = layout.circuit.phases[0].groups[0].members[0]
    first_spiral = next(paths[i] for i in first_member.path_ids if len(paths[i].primitives) > 1)
    one_z = path_z_mm(layout, first_spiral)

    collapsed = member_chain_emf_by_phase(design, stack, lambda _layout, _path: one_z)
    for phase, emf in collapsed.items():
        assert abs(analysed_fundamental[phase] - emf) > 1e-6 * abs(analysed_fundamental[phase]), phase
