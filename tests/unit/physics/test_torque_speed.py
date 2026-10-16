"""EQ-20 closed forms of the torque-speed envelope (label estimate): an L = 0 winding is a DC-motor line.

With L = 0 the voltage limit gives i_q = (V - E) / R and the current limit gives i_q = I_max, so the curve is the
current-limited plateau T = Kt I_max up to the corner speed (V - R I_max) / Ke_rms, then T = Kt (V - E) / R down to
zero at V / Ke_rms. Expected values are written from those identities, not from the module.
"""

import math

import numpy as np
import pytest

from embodic.model.operating import Modulation
from embodic.model.vocabulary import ConnectionTopology
from embodic.physics import base_speed_rpm, inverter_phase_voltage_v, no_load_speed_rpm, torque_speed_envelope

pytestmark = pytest.mark.req("REQ-F-20")
R_OHM = 0.5
KE = 0.02  # V*s/rad, peak phase, star equivalent (example)
V_DC = 24.0
I_MAX = 10.0
POLES = 14
POINTS = 241
V_PHASE = V_DC / math.sqrt(6.0)  # SVPWM: V_LL,rms = V_dc / sqrt(2), V_ph = V_LL / sqrt(3)
KE_RMS = KE / math.sqrt(2.0)
KT = 3.0 * KE / math.sqrt(2.0)  # N*m per line ampere rms, m = 3
RPM_PER_RAD_S = 60.0 / (2.0 * math.pi)
STAR = ConnectionTopology.STAR


def _curve(inductance_h: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    return torque_speed_envelope(
        R_OHM, inductance_h, KE, V_DC, Modulation.SVPWM, I_MAX, POLES, POINTS, phases=3, connection=STAR
    )


def test_inverter_limit_per_modulation() -> None:
    """Defect caught: a modulation mapped to another one's voltage limit (SVPWM, sine PWM and six-step differ)."""
    assert inverter_phase_voltage_v(V_DC, Modulation.SVPWM, STAR) == pytest.approx(
        V_DC / math.sqrt(6.0), rel=1e-14, abs=0.0
    )
    assert inverter_phase_voltage_v(V_DC, Modulation.SPWM, STAR) == pytest.approx(
        V_DC / math.sqrt(8.0), rel=1e-14, abs=0.0
    )
    assert inverter_phase_voltage_v(V_DC, Modulation.SIX_STEP, STAR) == pytest.approx(
        V_DC * math.sqrt(2.0) / math.pi, rel=1e-14, abs=0.0
    )


def test_no_load_speed_is_v_dc_over_ke_line_for_svpwm() -> None:
    """Defect caught: a no-load speed from the phase constant instead of V_dc / Ke_LL with Ke_LL = sqrt(3) Ke."""
    expected = V_DC / (math.sqrt(3.0) * KE) * RPM_PER_RAD_S
    assert no_load_speed_rpm(KE, V_DC, Modulation.SVPWM, STAR) == pytest.approx(expected, rel=1e-13, abs=0.0)


def test_curve_runs_from_standstill_to_115_percent_of_the_no_load_speed() -> None:
    """Defect caught: an end point or point count that differs from Xcoil's 0 to 1.15 x no-load speed."""
    speed, torque = _curve()
    assert len(speed) == len(torque) == POINTS
    assert speed[0] == 0.0
    assert speed[-1] == pytest.approx(1.15 * V_PHASE / KE_RMS * RPM_PER_RAD_S, rel=1e-13, abs=0.0)


def test_stall_torque_is_kt_times_the_current_limit() -> None:
    """Defect caught: a stall torque limited by V / R instead of I_max, or a Kt without the 3 phases."""
    _, torque = _curve()
    assert V_PHASE / R_OHM > I_MAX  # the current limit binds at standstill
    assert torque[0] == pytest.approx(0.3 * math.sqrt(2.0), rel=1e-13, abs=0.0)  # 3 * 0.02 / sqrt(2) * 10 A


def test_corner_speed_and_the_voltage_limited_branch() -> None:
    """Defect caught: a plateau that ends at the wrong speed, or a branch off the line T = Kt (V - E) / R."""
    speed, torque = _curve()
    omega = speed / RPM_PER_RAD_S
    corner_rad_s = (V_PHASE - R_OHM * I_MAX) / KE_RMS
    plateau = omega <= corner_rad_s
    assert plateau.any() and (~plateau).any()
    np.testing.assert_allclose(torque[plateau], KT * I_MAX, rtol=1e-12)
    branch = ~plateau & (omega < V_PHASE / KE_RMS)
    np.testing.assert_allclose(torque[branch], KT * (V_PHASE - KE_RMS * omega[branch]) / R_OHM, rtol=1e-9)
    assert torque[-1] == 0.0  # above the no-load speed no torque remains


def test_base_speed_is_the_first_point_below_995_per_mille_of_the_plateau() -> None:
    """Defect caught: a base speed taken from the corner formula instead of the curve, or a wrong fraction."""
    speed, torque = _curve()
    step = speed[1] - speed[0]
    edge_rad_s = (V_PHASE - 0.995 * R_OHM * I_MAX) / KE_RMS  # T = 0.995 Kt I_max on the voltage-limited branch
    edge_rpm = edge_rad_s * RPM_PER_RAD_S
    assert edge_rpm < base_speed_rpm(speed, torque) <= edge_rpm + step


def test_base_speed_of_a_curve_that_never_drops_is_its_last_speed() -> None:
    """Defect caught: an index error or None for a flat curve (Xcoil returns the end speed)."""
    speed = np.array([0.0, 100.0, 200.0])
    assert base_speed_rpm(speed, np.array([1.0, 1.0, 1.0])) == 200.0


def test_inductance_never_lifts_torque_above_the_current_limit() -> None:
    """Defect caught: a field-weakening scan that returns a negative or above-limit torque."""
    _, torque = _curve(inductance_h=2e-4)
    assert torque.max() <= KT * I_MAX * (1.0 + 1e-12)
    assert torque.min() >= 0.0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"resistance_ohm": 0.0},
        {"ke_v_s_per_rad": 0.0},
        {"dc_link_v": 0.0},
        {"current_limit_a": 0.0},
        {"inductance_h": -1e-6},
        {"points": 1},
    ],
)
def test_invalid_inputs_raise_instead_of_returning_nan(kwargs: dict[str, float]) -> None:
    """Defect caught: R = 0 or Ke = 0 dividing by zero into a silent inf or NaN curve (no silent NaN, addendum)."""
    args = {
        "resistance_ohm": R_OHM,
        "inductance_h": 0.0,
        "ke_v_s_per_rad": KE,
        "dc_link_v": V_DC,
        "modulation": Modulation.SVPWM,
        "current_limit_a": I_MAX,
        "poles": POLES,
        "points": POINTS,
        "phases": 3,
        "connection": STAR,
    }
    args.update(kwargs)
    with pytest.raises(ValueError):
        torque_speed_envelope(**args)  # type: ignore[arg-type]


@pytest.mark.parametrize("phases", [1, 2, 5])
def test_open_winding_uses_a_full_bridge_per_phase_and_m_phases(phases: int) -> None:
    """Defect caught: an open winding run as a three-phase star equivalent (wrong voltage limit or Kt).

    Open connection (Xcoil l.2681, l.2693): V_ph = V_dc / sqrt(2) for SVPWM, Kt = m Ke / sqrt(2), and with L = 0 the
    plateau is Kt I_max up to (V_ph - R I_max) / Ke_rms and the curve ends at 1.15 V_ph / Ke_rms.
    """
    v_open = V_DC / math.sqrt(2.0)
    assert inverter_phase_voltage_v(V_DC, Modulation.SVPWM, ConnectionTopology.OPEN) == pytest.approx(
        v_open, rel=1e-14, abs=0.0
    )
    assert inverter_phase_voltage_v(V_DC, Modulation.SIX_STEP, ConnectionTopology.OPEN) == pytest.approx(
        4.0 * V_DC / (math.pi * math.sqrt(2.0)), rel=1e-14, abs=0.0
    )
    speed, torque = torque_speed_envelope(
        R_OHM, 0.0, KE, V_DC, Modulation.SVPWM, I_MAX, POLES, POINTS, phases=phases, connection=ConnectionTopology.OPEN
    )
    assert torque[0] == pytest.approx(phases * KE / math.sqrt(2.0) * I_MAX, rel=1e-13, abs=0.0)
    assert speed[-1] == pytest.approx(1.15 * v_open / KE_RMS * RPM_PER_RAD_S, rel=1e-13, abs=0.0)


@pytest.mark.parametrize("connection", [ConnectionTopology.STAR, ConnectionTopology.DELTA])
def test_star_and_delta_refuse_a_phase_count_other_than_three(connection: ConnectionTopology) -> None:
    """Defect caught: a two-phase winding silently run as a three-phase star equivalent."""
    with pytest.raises(ValueError, match="three phases"):
        torque_speed_envelope(
            R_OHM, 0.0, KE, V_DC, Modulation.SVPWM, I_MAX, POLES, POINTS, phases=2, connection=connection
        )
