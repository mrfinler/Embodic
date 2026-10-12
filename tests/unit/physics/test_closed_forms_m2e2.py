"""Closed-form and identity tests of the U-M2e-2 kernels; expected values are the registry reference cases."""

import math

import numpy as np
import pytest

from embodic.geometry.circuit import Circuit, Member, ParallelGroup, PhaseCircuit
from embodic.geometry.primitives import Arc, Line, PrimitiveRole
from embodic.model.rotor import ArcMagnet, RotorSpec, RotorType
from embodic.model.vocabulary import ConnectionTopology, Phase
from embodic.physics import (
    copper_resistivity_ohm_m,
    delta_circulating_loss_w,
    eddy_loss_w,
    efficiency,
    emf_waveform_v,
    field_table,
    inductance_estimate_h,
    integrate_path,
    line_resistance_ohm,
    line_waveforms_v,
    solve_phase_circuit,
)
from embodic.physics.emf import PathField

pytestmark = pytest.mark.req("REQ-F-11")
ROTOR = RotorSpec(
    poles=10,
    rotor_type=RotorType.DOUBLE,
    magnet=ArcMagnet(pole_arc_ratio=0.8, r_inner_mm=20.0, r_outer_mm=40.0, thickness_mm=3.0),
    remanence_t=1.3,
    recoil_permeability=1.05,
    air_gap_mm=1.0,
    back_iron_thickness_mm=3.0,
)


def test_eq07_two_member_identity() -> None:
    """EQ-07 reference (D01 eq. 2): E 1.0 and 0.98 V, R 1 ohm each give E_grp 0.99 V and P_c 1e-4 W."""
    circuit = Circuit(
        phases=(
            PhaseCircuit(
                phase=Phase.A,
                groups=(ParallelGroup(members=(Member(path_ids=(0,), via_ids=()), Member(path_ids=(1,), via_ids=()))),),
                terminal_net="U",
            ),
        ),
        topology=ConnectionTopology.OPEN,
        interconnect_path_ids=(),
    )
    lam = {0: np.array([1.0e6 + 0j]), 1: np.array([0.98e6 + 0j])}  # T*mm^2; x 1e-6 x omega_m 1 = V
    s = solve_phase_circuit(circuit, lam, {0: 1.0, 1: 1.0}, {}, 1.0)
    assert s.phase_emf_phasor_v_s_per_rad[Phase.A][0] == pytest.approx(0.99, rel=1e-12)
    assert s.circulating_loss_w[Phase.A] == pytest.approx(1e-4, rel=1e-9)
    assert s.phase_resistance_ohm[Phase.A] == pytest.approx(0.5, rel=1e-12)


def test_eq12_c9_single_trace() -> None:
    """EQ-12 reference (C9): L 20 mm, w 0.5 mm, t 34.8 um, B_z 0.7 T, 16 poles at 1000 rpm, 20 degC -> 7.2311e-5 W."""
    field = PathField(
        flux_linkage_t_mm2=np.zeros(1, dtype=np.complex128),
        eddy_bz_sum=np.array([20.0 * 0.7**2 * 0.5**3]),
        eddy_bt_sum=np.array([0.0]),
        edge_weight=0.0,
        edge_weighted=0.0,
    )
    omega_e = 2.0 * math.pi * 8 * 1000.0 / 60.0
    rho = copper_resistivity_ohm_m(20.0, 1.7241e-8, 0.00393)
    assert eddy_loss_w(field, (1,), 0.0348, omega_e, rho) == pytest.approx(7.2311e-5, rel=1e-4)


def test_eq14_reference_estimate() -> None:
    """EQ-14 reference (C9): N 64, k_w1 0.866, D 76/36 mm, delta' 6.62 mm, p 8 -> 9.74 uH."""
    assert inductance_estimate_h(64, 0.866, 38.0, 18.0, 8, 6.62) == pytest.approx(9.74e-6, rel=5e-4)


@pytest.mark.eqt("EQT-19-CF07")
def test_eq19_triplen_in_phase() -> None:
    """EQ-19 reference: 0.1 V third harmonic in phase on all three phases, R_loop 3 ohm -> P 0.015 W."""
    e3 = np.array([0.0, 0.1 + 0j])
    assert delta_circulating_loss_w([e3, e3, e3], 3.0) == pytest.approx(0.015, rel=1e-12)


def test_eq19_balanced_fundamental_drives_nothing() -> None:
    """Defect caught: a balanced fundamental (sum zero) counted as circulating current."""
    phasors = [np.array([np.exp(1j * k * 2 * math.pi / 3)]) for k in range(3)]
    assert delta_circulating_loss_w(phasors, 3.0) == pytest.approx(0.0, abs=1e-30)


@pytest.mark.eqt("EQT-23-CF06")
def test_eq23_cf06_star_and_delta() -> None:
    """EQ-23 reference (CF-06): branches 1.0, 1.1, 1.2 ohm -> R_LL 2.2 (star), 0.731313131 (delta)."""
    branches = [1.0, 1.1, 1.2]
    assert line_resistance_ohm(branches, ConnectionTopology.STAR) == pytest.approx(2.2, rel=1e-9)
    assert line_resistance_ohm(branches, ConnectionTopology.DELTA) == pytest.approx(0.731313131, rel=1e-9)


def test_eq26_efficiency() -> None:
    """EQ-26 reference: P_out 10 W, P_loss 2.5 W -> eta 0.8; no output gives 0, not a division by zero."""
    assert efficiency(10.0, 2.5) == pytest.approx(0.8, rel=1e-12)
    assert efficiency(0.0, 2.5) == 0.0


def test_eq18_star_line_waveform_cancels_triplens() -> None:
    """UT-PHY-19: a third harmonic common to all phases vanishes from the star line EMF."""
    phases = [emf_waveform_v({1: np.exp(-1j * k * 2 * math.pi / 3), 3: 0.2 + 0j}, samples=361) for k in range(3)]
    line = line_waveforms_v(phases, ConnectionTopology.STAR)[0]
    spectrum = np.abs(np.fft.rfft(line[:-1])) / 180.0
    assert spectrum[3] < 1e-12
    assert spectrum[1] == pytest.approx(math.sqrt(3.0), rel=1e-12)


def test_eq06_circumferential_arc_links_no_flux() -> None:
    """UT-PHY-06: an arc at constant radius has no radial extent, so it contributes no EMF."""
    table = field_table(ROTOR, 2.6, 1.8, (1, 3))
    arc = Arc(cx_mm=0.0, cy_mm=0.0, r_mm=30.0, start_rad=0.0, sweep_rad=1.0, width_mm=0.4, role=PrimitiveRole.END_TURN)
    ke_v_s_per_rad = np.abs(integrate_path((arc,), table, 5, 0.5, 2.0).flux_linkage_t_mm2) * 1e-6
    assert np.max(ke_v_s_per_rad) <= 1e-15


def test_eq06_reversed_path_reverses_the_phasor() -> None:
    """Defect caught: a flux linkage that ignores the current direction of the chain."""
    table = field_table(ROTOR, 2.6, 1.8, (1,))
    out = Line(x1_mm=20.0, y1_mm=0.0, x2_mm=40.0, y2_mm=0.0, width_mm=0.4, role=PrimitiveRole.SIDE)
    back = Line(x1_mm=40.0, y1_mm=0.0, x2_mm=20.0, y2_mm=0.0, width_mm=0.4, role=PrimitiveRole.SIDE)
    forward = integrate_path((out,), table, 5, 0.5, 2.0).flux_linkage_t_mm2[0]
    reverse = integrate_path((back,), table, 5, 0.5, 2.0).flux_linkage_t_mm2[0]
    assert abs(forward) > 0.0
    assert reverse == pytest.approx(-forward, rel=1e-12)
