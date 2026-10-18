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
    edge_leakage_fraction,
    efficiency,
    emf_waveform_v,
    field_table,
    inductance_estimate_h,
    integrate_path,
    line_resistance_ohm,
    line_waveforms_v,
    solve_phase_circuit,
)
from embodic.physics.emf import FIELD_TABLE_STEPS, FieldTable, PathField
from embodic.results import load_registry

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


def _two_member_circuit() -> Circuit:
    return Circuit(
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


def test_eq07_two_member_identity() -> None:
    """EQ-07 reference (D01 eq. 2): E 1.0 and 0.98 V, R 1 ohm each give E_grp 0.99 V and P_c 1e-4 W."""
    lam = {0: np.array([1.0e6 + 0j]), 1: np.array([0.98e6 + 0j])}  # T*mm^2; x 1e-6 x omega_m 1 = V
    s = solve_phase_circuit(_two_member_circuit(), lam, {0: 1.0, 1: 1.0}, {}, 1.0)
    assert s.phase_emf_phasor_v_s_per_rad[Phase.A][0] == pytest.approx(0.99, rel=1e-12, abs=0.0)
    assert s.circulating_loss_w[Phase.A] == pytest.approx(1e-4, rel=1e-9)
    assert s.phase_resistance_ohm[Phase.A] == pytest.approx(0.5, rel=1e-12, abs=0.0)


@pytest.mark.req("REQ-F-12")
@pytest.mark.eqt("EQT-07-CF07")
def test_eq07_cf07_two_member_group_with_half_ohm_members() -> None:
    """CF-07 (EQ-07): E 1.00 and 0.98 V, R 0.5 ohm each -> E_grp 0.99 V, R_grp 0.25 ohm, P_c 2.0e-4 W, rel 1e-12.

    Defect caught: member resistance multiplied instead of divided (5.0e-5 W; R = 1 ohm hides it), R_grp used in place
    of R_i, or a missing factor 1/2.
    """
    lam = {0: np.array([1.0e6 + 0j]), 1: np.array([0.98e6 + 0j])}
    s = solve_phase_circuit(_two_member_circuit(), lam, {0: 0.5, 1: 0.5}, {}, 1.0)
    assert s.phase_emf_phasor_v_s_per_rad[Phase.A][0] == pytest.approx(0.99, rel=1e-12, abs=0.0)
    assert s.phase_resistance_ohm[Phase.A] == pytest.approx(0.25, rel=1e-12, abs=0.0)
    assert s.circulating_loss_w[Phase.A] == pytest.approx(2.0e-4, rel=1e-12, abs=0.0)


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


@pytest.mark.eqt("EQT-12-CF05")
def test_eq12_cf05_single_trace_at_full_precision() -> None:
    """CF-05 (EQ-12): L 20, w 0.5, t 0.0348 mm, B_z 0.7 T, 133.33333333333334 Hz, 20 degC -> 7.230675123999244e-05 W.

    Defect caught: a copper constant other than the registry's (Xcoil's 1.724e-8 is off by 5.8e-5), a rounded
    electrical frequency, or the /12 form of D04 and D10 (a factor 2). The C9 test above reads 7.2311e-5 at 1e-4 and
    sees none of them.
    """
    field = PathField(
        flux_linkage_t_mm2=np.zeros(1, dtype=np.complex128),
        eddy_bz_sum=np.array([20.0 * 0.7**2 * 0.5**3]),
        eddy_bt_sum=np.array([0.0]),
        edge_weight=0.0,
        edge_weighted=0.0,
    )
    omega_e = 2.0 * math.pi * 133.33333333333334
    rho = copper_resistivity_ohm_m(20.0, 1.7241e-8, 0.00393)
    assert eddy_loss_w(field, (1,), 0.0348, omega_e, rho) == pytest.approx(7.230675123999244e-05, rel=1e-9, abs=0.0)


@pytest.mark.eqt("EQT-14-CF12")
def test_eq14_reference_estimate() -> None:
    """CF-12 (EQ-14 form a): N 64, k_w1 0.866, D 76/36 mm, delta' 6.62 mm, p 8 -> L_m 9.744443398187309e-06 H.

    Relative 1e-12. The value is the formula, not a prediction of a measured inductance (EQ-14 stays unresolved).
    The rounded Phase 1 figure 9.74 uH is 4.6e-4 away and hides what the tight tolerance sees. Defect caught: a mu0
    other than 4 pi 1e-7 (rounded 1.2566e-6 moves L_m by 2.9e-5, CODATA 2022 by 1.3e-10), or a diameter, pole-pair
    or gap term off by a small factor. abs=0 matters: approx keeps an absolute 1e-12 H by default, which is 1e-7
    relative at 9.7e-6 H and would let the CODATA change through.
    """
    expected_h = 9.744443398187309e-06
    assert inductance_estimate_h(64, 0.866, 38.0, 18.0, 8, 6.62) == pytest.approx(expected_h, rel=1e-12, abs=0.0)


@pytest.mark.eqt("EQT-19-CF07")
def test_eq19_triplen_in_phase() -> None:
    """EQ-19 reference: 0.1 V third harmonic in phase on all three phases, R_loop 3 ohm -> P 0.015 W."""
    e3 = np.array([0.0, 0.1 + 0j])
    assert delta_circulating_loss_w([e3, e3, e3], 3.0) == pytest.approx(0.015, rel=1e-12, abs=0.0)


def test_eq19_balanced_fundamental_drives_nothing() -> None:
    """Defect caught: a balanced fundamental (sum zero) counted as circulating current."""
    phasors = [np.array([np.exp(1j * k * 2 * math.pi / 3)]) for k in range(3)]
    assert delta_circulating_loss_w(phasors, 3.0) == pytest.approx(0.0, abs=1e-30)


@pytest.mark.eqt("EQT-23-CF06")
def test_eq23_cf06_star_and_delta() -> None:
    """EQ-23 reference (CF-06): branches 1.0, 1.1, 1.2 ohm -> R_LL 2.1999999999999997 star, 0.7313131313131312 delta."""
    branches = [1.0, 1.1, 1.2]
    assert line_resistance_ohm(branches, ConnectionTopology.STAR) == pytest.approx(
        2.1999999999999997, rel=1e-12, abs=0.0
    )
    assert line_resistance_ohm(branches, ConnectionTopology.DELTA) == pytest.approx(
        0.7313131313131312, rel=1e-12, abs=0.0
    )


def test_eq26_efficiency() -> None:
    """EQ-26 reference: P_out 10 W, P_loss 2.5 W -> eta 0.8; no output gives 0, not a division by zero."""
    assert efficiency(10.0, 2.5) == pytest.approx(0.8, rel=1e-12, abs=0.0)
    assert efficiency(0.0, 2.5) == 0.0


def test_eq18_star_line_waveform_cancels_triplens() -> None:
    """UT-PHY-19: a third harmonic common to all phases vanishes from the star line EMF."""
    phases = [emf_waveform_v({1: np.exp(-1j * k * 2 * math.pi / 3), 3: 0.2 + 0j}, samples=361) for k in range(3)]
    line = line_waveforms_v(phases, ConnectionTopology.STAR)[0]
    spectrum = np.abs(np.fft.rfft(line[:-1])) / 180.0
    assert spectrum[3] < 1e-12
    assert spectrum[1] == pytest.approx(math.sqrt(3.0), rel=1e-12, abs=0.0)


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
    assert reverse == pytest.approx(-forward, rel=1e-12, abs=0.0)


def _radial(r_from_mm: float, r_to_mm: float, angle_rad: float) -> Line:
    return Line(
        x1_mm=r_from_mm * math.cos(angle_rad),
        y1_mm=r_from_mm * math.sin(angle_rad),
        x2_mm=r_to_mm * math.cos(angle_rad),
        y2_mm=r_to_mm * math.sin(angle_rad),
        width_mm=0.5,
        role=PrimitiveRole.SIDE,
    )


def _cf02_coil() -> list[Line | Arc]:
    """CF-02 coil: radial sides from 18 to 38 mm at -15 and +15 degrees, arcs at 38 and 18 mm, out along -15 degrees."""
    a, b = -math.radians(15.0), math.radians(15.0)
    return [
        _radial(18.0, 38.0, a),
        Arc(cx_mm=0.0, cy_mm=0.0, r_mm=38.0, start_rad=a, sweep_rad=b - a, width_mm=0.5, role=PrimitiveRole.END_TURN),
        _radial(38.0, 18.0, b),
        Arc(cx_mm=0.0, cy_mm=0.0, r_mm=18.0, start_rad=b, sweep_rad=a - b, width_mm=0.5, role=PrimitiveRole.END_TURN),
    ]


def _uniform_table(bz_t: float) -> FieldTable:
    return FieldTable(
        r_inner_mm=18.0,
        r_outer_mm=38.0,
        harmonics=(1,),
        bz_t=np.full((1, FIELD_TABLE_STEPS + 1), bz_t),
        bt_t=np.zeros((1, FIELD_TABLE_STEPS + 1)),
    )


@pytest.mark.eqt("EQT-05-CF03", "EQT-06-CF03")
def test_cf03_coil_in_the_eq05_field_of_a_double_rotor() -> None:
    """CF-03 (EQ-05, EQ-06): the CF-02 coil at z 0.8 mm, G 1.1 mm -> Ke1 = 1.0201338249421754e-3 V*s/rad, rel 1e-5.

    The tolerance is CF-03's: Xcoil's 48-step field table and 0.5 mm segments. Defect caught: z measured from the wrong
    plane, G of a single rotor, or a harmonic index error in u = n p / r.
    """
    rotor = RotorSpec(
        poles=16,
        rotor_type=RotorType.DOUBLE,
        magnet=ArcMagnet(pole_arc_ratio=0.85, r_inner_mm=18.0, r_outer_mm=38.0, thickness_mm=3.0),
        remanence_t=1.3,
        recoil_permeability=1.05,
        air_gap_mm=0.8,
        back_iron_thickness_mm=5.0,
    )
    table = field_table(rotor, 1.1, 0.8, (1,))
    ke_v_s_per_rad = abs(integrate_path(_cf02_coil(), table, 8, 0.5, 1.0).flux_linkage_t_mm2[0]) * 1e-6
    assert ke_v_s_per_rad == pytest.approx(1.0201338249421754e-3, rel=1e-5)


@pytest.mark.eqt("EQT-06-CF02")
def test_cf02_coil_in_a_uniform_field_matches_the_closed_form() -> None:
    """CF-02 (EQ-06): B1 0.8 T, p 8, sigma 30 deg -> Ke1 = B1 (r_b^2 - r_a^2) sin(p sigma / 2) = 7.75958761790857e-4.

    Rel 1e-9, and the two arcs alone link exactly 0. Defect caught: sin(sigma / 2) in mechanical angle, an arc that
    links flux, or a missing r in r dr.
    """
    table = _uniform_table(0.8)
    coil = _cf02_coil()
    ke_v_s_per_rad = abs(integrate_path(coil, table, 8, 0.5, 1.0).flux_linkage_t_mm2[0]) * 1e-6
    arcs_only = integrate_path([coil[1], coil[3]], table, 8, 0.5, 1.0).flux_linkage_t_mm2[0]
    assert ke_v_s_per_rad == pytest.approx(7.75958761790857e-4, rel=1e-9)
    assert abs(arcs_only) == 0.0


@pytest.mark.eqt("EQT-05-EC")
def test_ec05_edge_leakage_value_from_the_registry_constants() -> None:
    """EC-05 (EQ-05): two radial lines of 0.4 mm in a uniform 0.8 T field, G 1.1 mm -> e_edge 0.11285496821276436.

    Line 1 (r 18.3 to 18.7 mm, r_m 18.5, d 0.5 mm) weighs 0.8 * 18.5 * 0.4 = 5.92, line 2 (r 27.8 to 28.2 mm, r_m 28.0,
    d 10 mm) 8.96. The expected values are written with D_e 0.47 and c_e 0.9 as literals, rel 1e-12.

    Defect caught: a wrong D_e or c_e in the registry or the kernel, d measured to the farther magnet end, a weight
    without r, or a decay length without G.
    """
    check = load_registry().equation("EQ-05").validity_checks[0]
    table = _uniform_table(0.8)

    decay_mm = float(check.parameters["c_e"]) * 1.1
    near = integrate_path([_radial(18.3, 18.7, 0.0)], table, 8, 0.5, decay_mm)
    far = integrate_path([_radial(27.8, 28.2, 0.5)], table, 8, 0.5, decay_mm)
    amplitude = float(check.parameters["D_e"])
    assert edge_leakage_fraction([near], amplitude) == pytest.approx(0.28363329517506497, rel=1e-12, abs=0.0)
    assert edge_leakage_fraction([near, far], amplitude) == pytest.approx(0.11285496821276436, rel=1e-12, abs=0.0)
