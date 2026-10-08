"""Torque-speed envelope on a current- and voltage-limited inverter (EQ-20, label estimate, status unresolved).

A port of Xcoil `inverterVoltage` and `torqueSpeed` (engine.js l.2679-2720). Star and delta pass the per-phase star
equivalent of a three-phase winding (R_LL / 2, L_s / 3 for delta, Ke_ph / sqrt(3) for delta), as Xcoil's
`driveAnalysis` does. The open connection, which Xcoil uses for every phase count other than three, passes the phase
resistance, the phase inductance and Ke_ph, each phase on its own full bridge (engine.js l.2681, l.2689-2694).
"""

import math

import numpy as np

from embodic.model.operating import Modulation
from embodic.model.vocabulary import ConnectionTopology
from embodic.units import FloatArray

XCOIL_CURVE_POINTS = 121
FIELD_WEAKENING_STEPS = 80  # id = -I_max * i / 80 scan, i = 0..80
OVERSPEED_FACTOR = 1.15  # Xcoil ends the curve 15 % above the no-load speed
BASE_SPEED_TORQUE_FRACTION = 0.995  # base speed: first point below 99.5 % of the peak torque
STAR_EQUIVALENT_PHASES = 3  # star and delta run as the star equivalent of three phases
CURRENT_TIE_A = 1.0 / 10.0**12  # Xcoil's 1e-12 A margin for 'current limit reached at i_d = 0' (engine.js l.2703)


def inverter_phase_voltage_v(dc_link_v: float, modulation: Modulation, connection: ConnectionTopology) -> float:
    """Return the fundamental phase voltage (rms) that the inverter can apply.

    References: EQ-20 (Xcoil inverterVoltage, engine.js l.2679-2684). Star and delta, star equivalent:
    V_LL,rms = V_dc / sqrt(2) for SVPWM, sqrt(3) V_dc / (2 sqrt(2)) for sinusoidal PWM, sqrt(6) V_dc / pi for
    six-step, and V_ph = V_LL / sqrt(3). Open, one full bridge per phase: V_ph = 4 V_dc / (pi sqrt(2)) for six-step,
    else V_dc / sqrt(2).

    Parameters
    ----------
    dc_link_v : float
        DC-link voltage in V.
    modulation : Modulation
        Inverter modulation.
    connection : ConnectionTopology
        Star, delta or open.

    Returns
    -------
    float
        Phase voltage in V rms.
    """
    if connection is ConnectionTopology.OPEN:
        if modulation is Modulation.SIX_STEP:
            return 4.0 * dc_link_v / (math.pi * math.sqrt(2.0))
        return dc_link_v / math.sqrt(2.0)
    match modulation:
        case Modulation.SVPWM:
            line = dc_link_v / math.sqrt(2.0)
        case Modulation.SPWM:
            line = math.sqrt(3.0) / (2.0 * math.sqrt(2.0)) * dc_link_v
        case Modulation.SIX_STEP:
            line = math.sqrt(6.0) / math.pi * dc_link_v
    return line / math.sqrt(3.0)


def no_load_speed_rpm(
    ke_v_s_per_rad: float, dc_link_v: float, modulation: Modulation, connection: ConnectionTopology
) -> float:
    """Return the speed at which the back-EMF reaches the inverter voltage limit.

    References: EQ-20 (Xcoil torqueSpeed `rpmNoLoad`), omega_0 = V_ph / (Ke / sqrt(2)).

    Parameters
    ----------
    ke_v_s_per_rad : float
        Peak phase EMF constant per mechanical rad/s in V*s/rad (star equivalent for star and delta); must be
        positive.
    dc_link_v : float
        DC-link voltage in V.
    modulation : Modulation
        Inverter modulation.
    connection : ConnectionTopology
        Star, delta or open.

    Returns
    -------
    float
        No-load speed in rpm.
    """
    if not ke_v_s_per_rad > 0.0:
        raise ValueError("the no-load speed is infinite without a back-EMF constant")
    omega_0 = inverter_phase_voltage_v(dc_link_v, modulation, connection) / (ke_v_s_per_rad / math.sqrt(2.0))
    return omega_0 * 60.0 / (2.0 * math.pi)


def torque_speed_envelope(
    resistance_ohm: float,
    inductance_h: float,
    ke_v_s_per_rad: float,
    dc_link_v: float,
    modulation: Modulation,
    current_limit_a: float,
    poles: int,
    points: int,
    *,
    phases: int,
    connection: ConnectionTopology,
) -> tuple[FloatArray, FloatArray]:
    """Return the maximum-torque curve of the winding from standstill to 115 % of the no-load speed.

    References: EQ-20 (Xcoil torqueSpeed). Steady-state dq model, V_ph^2 = (R i_d - X i_q)^2 + (R i_q + X i_d + E)^2
    with X = omega_m p L and E = Ke omega_m / sqrt(2). At each speed the scan i_d = 0 to -I_max (80 steps) picks the
    largest i_q within the voltage and the current circle sqrt(i_d^2 + i_q^2) <= I_max; T = Kt i_q with
    Kt = m Ke / sqrt(2) per line ampere rms, m = 3 for star and delta and m = phases for open (Xcoil l.2693).
    Label estimate: L_s comes from EQ-14, which is unresolved.

    Parameters
    ----------
    resistance_ohm : float
        Star and delta: phase resistance of the star equivalent (R_LL / 2); open: phase resistance. In ohm; must be
        positive.
    inductance_h : float
        Synchronous inductance per phase (star equivalent for star and delta) in H; not negative.
    ke_v_s_per_rad : float
        Peak phase EMF constant per mechanical rad/s in V*s/rad (star equivalent for star and delta); must be
        positive.
    dc_link_v : float
        DC-link voltage in V; must be positive.
    modulation : Modulation
        Inverter modulation.
    current_limit_a : float
        Line current limit in A rms; must be positive.
    poles : int
        Rotor pole count; p = poles / 2 pole pairs.
    points : int
        Curve points, both ends included; at least 2. Xcoil uses 121.
    phases : int
        Phase count of the winding; star and delta need 3.
    connection : ConnectionTopology
        Star, delta or open.

    Returns
    -------
    tuple[FloatArray, FloatArray]
        Speed in rpm and torque in N*m, one entry per point.
    """
    if not (resistance_ohm > 0.0 and ke_v_s_per_rad > 0.0 and dc_link_v > 0.0 and current_limit_a > 0.0):
        raise ValueError("resistance, Ke, DC-link voltage and current limit must be positive")
    if inductance_h < 0.0 or points < 2 or poles < 2:
        raise ValueError("inductance must not be negative, and the curve needs 2 points and one pole pair")
    if phases < 1 or (connection is not ConnectionTopology.OPEN and phases != STAR_EQUIVALENT_PHASES):
        raise ValueError(f"{connection.value} needs three phases, got {phases}")
    voltage_v = inverter_phase_voltage_v(dc_link_v, modulation, connection)
    pole_pairs = poles // 2
    ke_rms = ke_v_s_per_rad / math.sqrt(2.0)
    kt = (phases if connection is ConnectionTopology.OPEN else STAR_EQUIVALENT_PHASES) * ke_rms
    rpm_end = no_load_speed_rpm(ke_v_s_per_rad, dc_link_v, modulation, connection) * OVERSPEED_FACTOR
    speed = np.empty(points)
    torque = np.empty(points)
    for i in range(points):
        rpm = rpm_end * i / (points - 1)
        omega = rpm * 2.0 * math.pi / 60.0
        speed[i] = rpm
        torque[i] = kt * _best_iq(omega, resistance_ohm, ke_rms, inductance_h, pole_pairs, voltage_v, current_limit_a)
    return speed, torque


def _best_iq(
    omega: float, r: float, ke_rms: float, l_h: float, pole_pairs: int, voltage_v: float, i_max: float
) -> float:
    """Largest quadrature current inside the voltage ellipse and the current circle at one speed (A rms)."""
    e = ke_rms * omega
    x = omega * pole_pairs * l_h
    z2 = r * r + x * x
    best = 0.0
    found = False
    for i in range(FIELD_WEAKENING_STEPS + 1):
        i_d = -i_max * i / FIELD_WEAKENING_STEPS
        c = r * r * i_d * i_d + (x * i_d + e) * (x * i_d + e) - voltage_v * voltage_v
        discriminant = r * e * r * e - z2 * c
        if discriminant < 0.0:
            continue
        iq_voltage = (-r * e + math.sqrt(discriminant)) / z2
        iq_current = math.sqrt(max(0.0, i_max * i_max - i_d * i_d))
        iq = min(iq_voltage, iq_current)
        if iq < 0.0:
            continue
        if not found or iq > best:
            best = iq
            found = True
        if iq >= iq_current - CURRENT_TIE_A and i == 0:
            break
    return best


def base_speed_rpm(speed_rpm: FloatArray, torque_n_m: FloatArray) -> float:
    """Return the corner speed: the first speed above zero where the torque falls below 99.5 % of its peak.

    References: EQ-20 (Xcoil torqueSpeed `rpmBase`); the last speed when the curve never drops.

    Parameters
    ----------
    speed_rpm : FloatArray
        Curve speeds in rpm, ascending.
    torque_n_m : FloatArray
        Curve torque in N*m.

    Returns
    -------
    float
        Base speed in rpm.
    """
    threshold = float(np.max(torque_n_m)) * BASE_SPEED_TORQUE_FRACTION
    for rpm, t in zip(speed_rpm, torque_n_m, strict=True):
        if t < threshold and rpm > 0.0:
            return float(rpm)
    return float(speed_rpm[-1])
