"""Closed-form and Phase 1 UT-PHY checks of the physics kernels (oracle_cases.json CF-01, CF-04, CF-06)."""

import math

import numpy as np
import pytest

from embodic.geometry.arrays import LayoutArrays
from embodic.model.rotor import ArcMagnet, RotorSpec, RotorType
from embodic.model.vocabulary import ConnectionTopology
from embodic.physics import (
    copper_resistivity_ohm_m,
    current_density_a_per_mm2,
    field_harmonic,
    ipc2221_current_a,
    loss_budget_current_a,
    path_resistance_ohm,
    phase_constants,
    pole_arc_ratio_block,
    skin_depth_mm,
    symmetry_plane_mm,
    temperature_rise_k,
    thd,
    via_resistance_ohm,
)

RHO20 = 1.7241e-8  # registry EQ-10 constant (EV-53)
ALPHA20 = 0.00393  # registry EQ-10 constant (EV-53)


def _rotor(rotor_type: RotorType = RotorType.DOUBLE, *, poles: int = 2, air_gap_mm: float = 0.8) -> RotorSpec:
    magnet = ArcMagnet(pole_arc_ratio=0.85, r_inner_mm=18.0, r_outer_mm=38.0, thickness_mm=3.0)
    return RotorSpec(
        poles=poles,
        rotor_type=rotor_type,
        magnet=magnet,
        remanence_t=1.3,
        recoil_permeability=1.05,
        air_gap_mm=air_gap_mm,
        back_iron_thickness_mm=5.0,
    )


def test_cf01_field_fundamental_equals_the_1d_magnetic_circuit() -> None:
    """CF-01 (EQ-05): B_z1 = (4/pi) sin(pi a/2) Br lm/(lm + mu_r G) = 1.162077823241657 T, rel 1e-9.

    Defect caught: u built from 2p instead of p, or mu_r on the wrong term of the denominator.
    """
    bz, bt = field_harmonic(1, np.array([1e5]), np.array([0.0]), _rotor(), 1.1, np.array(0.85))
    assert bz[0] == pytest.approx(1.162077823241657, rel=1e-9)
    assert abs(bt[0]) < 1e-3


def test_ut_phy_04_symmetry_plane_per_rotor_type_and_open_rotor_limit() -> None:
    """UT-PHY-04 (EQ-05): G = (t + 2g)/2 double, t + 2g yoke, inf open; open rotor decays as exp(-u z).

    Defect caught: the yoke case using the double-rotor half plane, or a mirror applied to an open rotor.
    """
    assert symmetry_plane_mm(_rotor(RotorType.DOUBLE), 1.6) == pytest.approx(1.6, rel=1e-15)
    assert symmetry_plane_mm(_rotor(RotorType.SINGLE_YOKE), 1.6) == pytest.approx(3.2, rel=1e-15)
    assert math.isinf(symmetry_plane_mm(_rotor(RotorType.SINGLE_OPEN), 1.6))
    rotor = _rotor(RotorType.SINGLE_OPEN, poles=16)
    r, z1, z2 = np.array([28.0]), np.array([0.5]), np.array([1.5])
    b1, _ = field_harmonic(1, r, z1, rotor, math.inf, np.array(0.85))
    b2, _ = field_harmonic(1, r, z2, rotor, math.inf, np.array(0.85))
    assert b2[0] / b1[0] == pytest.approx(math.exp(-(8 / 28.0) * 1.0), rel=1e-12)


def test_field_is_mirrored_about_the_symmetry_plane() -> None:
    """Defect caught: no mirror beyond G, which would give a double rotor an asymmetric field across the board."""
    rotor = _rotor(poles=16)
    r = np.array([28.0, 28.0])
    bz, bt = field_harmonic(1, r, np.array([0.9, 1.3]), rotor, 1.1, np.array(0.85))
    assert bz[0] == pytest.approx(bz[1], rel=1e-12)
    assert bt[0] == pytest.approx(bt[1], rel=1e-12)


def test_ut_phy_02_block_magnet_pole_arc_ratio() -> None:
    """UT-PHY-02 (EQ-04): 6 mm wide block, 2p = 16: 0.853 / 0.547 / 0.402 at r 18 / 28 / 38 mm, +/-5e-4."""
    alpha = pole_arc_ratio_block(6.0, np.array([18.0, 28.0, 38.0]), 16)
    assert alpha == pytest.approx([0.853, 0.547, 0.402], abs=5e-4)


def _track_arrays() -> LayoutArrays:
    lines = np.array([[0.0, 0.0, 1000.0, 0.0, 0.5]])
    arcs = np.array([[0.0, 0.0, 30.0, 0.0, math.pi / 2, 0.5]])
    return LayoutArrays(
        lines={"F.Cu": lines},
        arcs={"F.Cu": arcs},
        path_index={"F.Cu": np.array([0, 1], dtype=np.int64)},
        prim_index={"F.Cu": np.array([0, 0], dtype=np.int64)},
        vias=np.zeros((0, 4)),
    )


def test_cf04_track_resistance_at_20_and_60_degc() -> None:
    """CF-04 (EQ-10): straight 1000 mm and 90 degree arc r 30 mm, 0.5 mm x 34.8 um, rel 1e-12.

    Expected 0.9908620689655171 ohm (20 degC), 1.1466255862068966 ohm (60 degC), arc 0.04669327494874277 ohm.

    Defect caught: arc length from the chord, a missing mm-to-m factor, or alpha applied around 0 degC.
    """
    thickness = {"F.Cu": 0.0348}
    r20 = path_resistance_ohm(_track_arrays(), thickness, copper_resistivity_ohm_m(20.0, RHO20, ALPHA20))
    r60 = path_resistance_ohm(_track_arrays(), thickness, copper_resistivity_ohm_m(60.0, RHO20, ALPHA20))
    assert r20[0] == pytest.approx(0.9908620689655171, rel=1e-12)
    assert r20[1] == pytest.approx(0.04669327494874277, rel=1e-12)
    assert r60[0] == pytest.approx(1.1466255862068966, rel=1e-12)


def test_cf04_and_ut_phy_11_via_barrel_resistance() -> None:
    """CF-04 / UT-PHY-11 (EQ-11): drill 0.3 mm, plating 25 um.

    Expected l 1.6 mm -> 1.277202792190775 mOhm (rel 1e-12), l 0.2 mm -> 0.160 mOhm; two barrels halve it.

    Defect caught: plating grown outward (pi (2 r t + t^2)) or the barrel count ignored.
    """
    rho = copper_resistivity_ohm_m(20.0, RHO20, ALPHA20)
    assert via_resistance_ohm(0.3, 25.0, 1.6, rho, 1) == pytest.approx(0.001277202792190775, rel=1e-12)
    assert via_resistance_ohm(0.3, 25.0, 0.2, rho, 1) == pytest.approx(0.160e-3, abs=0.5e-6)
    assert via_resistance_ohm(0.3, 25.0, 1.6, rho, 2) == pytest.approx(0.001277202792190775 / 2, rel=1e-12)


def test_cf06_star_and_delta_constants() -> None:
    """CF-06 (EQ-09): Ke_ph 0.01 V*s/rad, rel 1e-12.

    Expected Ke_LL star 0.017320508075688773, Kt star 0.021213203435596423, Kt delta 0.01224744871391589.

    Defect caught: the sqrt(3) applied in delta instead of star, or Kt per phase ampere instead of per line ampere.
    """
    star = phase_constants(0.01, ConnectionTopology.STAR, 3, 10)
    delta = phase_constants(0.01, ConnectionTopology.DELTA, 3, 10)
    assert star.ke_line_v_s_per_rad == pytest.approx(0.017320508075688773, rel=1e-12)
    assert star.kt_n_m_per_a == pytest.approx(0.021213203435596423, rel=1e-12)
    assert delta.kt_n_m_per_a == pytest.approx(0.01224744871391589, rel=1e-12)
    assert delta.ke_line_v_s_per_rad == pytest.approx(0.01, rel=1e-12)
    assert star.kv_rpm_per_v == pytest.approx(60.0 / (2.0 * math.pi * 0.017320508075688773), rel=1e-12)


def test_ut_phy_13_skin_depth_at_133_hz() -> None:
    """UT-PHY-13 (EQ-13): 133.3 Hz, 20 degC -> 5.72 mm +/-0.01 mm; 0 Hz has no skin effect (infinity)."""
    assert skin_depth_mm(133.3, copper_resistivity_ohm_m(20.0, RHO20, ALPHA20)) == pytest.approx(5.72, abs=0.01)
    assert math.isinf(skin_depth_mm(0.0, RHO20))


def test_ut_phy_15_ipc2221_guideline_current() -> None:
    """UT-PHY-15 (EQ-15): 0.5 mm x 34.8 um, dT 20 K -> 1.955 A external, 0.977 A internal (+/-1 mA)."""
    assert ipc2221_current_a(0.5 * 0.0348, 20.0, internal=False) == pytest.approx(1.955, abs=1e-3)
    assert ipc2221_current_a(0.5 * 0.0348, 20.0, internal=True) == pytest.approx(0.977, abs=1e-3)


def test_ut_phy_17_loss_budget_current() -> None:
    """UT-PHY-17 (EQ-21): 4 W over 3 phases of 0.39 ohm -> 1.849 A (D08 Table 4.6 gives 1.84 A)."""
    assert loss_budget_current_a(4.0, 3, 0.39) == pytest.approx(1.849, abs=5e-4)


def test_ut_phy_19_thd_of_a_pure_fundamental_is_zero() -> None:
    """UT-PHY-19 (EQ-18): THD of a pure fundamental is 0; 3rd and 5th of 0.3 and 0.4 give 0.5."""
    assert thd({1: 2.0, 3: 0.0, 5: 0.0}) <= 1e-12
    assert thd({1: 1.0, 3: 0.3, 5: 0.4}) == pytest.approx(0.5, rel=1e-12)


def test_current_density_and_temperature_rise_worked_examples() -> None:
    """EQ-22: 1 A over 2 paths of 0.5 mm x 0.035 mm -> 28.571 A/mm^2. EQ-17: 2 W, 2500 mm^2, h 20 -> 20 K."""
    assert current_density_a_per_mm2(1.0, 2, 0.5, 0.035) == pytest.approx(1.0 / 0.035, rel=1e-12)
    assert temperature_rise_k(2.0, 2500.0, 20.0) == pytest.approx(20.0, rel=1e-12)
