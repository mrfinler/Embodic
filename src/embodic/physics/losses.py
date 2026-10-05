"""Skin depth, current limits, current density and harmonic distortion (EQ-13, EQ-15, EQ-18, EQ-21, EQ-22)."""

import math
from collections.abc import Mapping

from embodic.units import MM_PER_M, mm2_to_mil2

MU0_H_PER_M = 4e-7 * math.pi  # Xcoil MU0 (engine.js l.11), the EQ-13 reuse port


def skin_depth_mm(frequency_hz: float, resistivity_ohm_m: float) -> float:
    """Return the skin depth of copper.

    References: EQ-13, delta = sqrt(rho / (pi f mu0)); infinity at 0 Hz (Xcoil skinDepthMm).

    Parameters
    ----------
    frequency_hz : float
        Electrical frequency in Hz.
    resistivity_ohm_m : float
        Resistivity at the operating temperature in ohm*m.

    Returns
    -------
    float
        Skin depth in mm.
    """
    if not frequency_hz > 0.0:
        return math.inf
    return math.sqrt(resistivity_ohm_m / (math.pi * frequency_hz * MU0_H_PER_M)) * MM_PER_M


def ipc2221_current_a(cross_section_mm2: float, temperature_rise_k: float, internal: bool) -> float:
    """Return the IPC-2221 guideline current of one trace.

    References: EQ-15 (gate 'cannot verify yet'), I = k dT^0.44 A^0.725 with A in mil^2, k = 0.048 external, 0.024
    internal.

    Parameters
    ----------
    cross_section_mm2 : float
        Trace cross-section in mm^2.
    temperature_rise_k : float
        Allowed temperature rise in K.
    internal : bool
        True for an inner layer.

    Returns
    -------
    float
        Current in A.
    """
    k = 0.024 if internal else 0.048
    return float(k * temperature_rise_k**0.44 * mm2_to_mil2(cross_section_mm2) ** 0.725)


def thd(harmonic_amplitudes: Mapping[int, float]) -> float:
    """Return the total harmonic distortion of a waveform.

    References: EQ-18, THD = sqrt(sum_{n > 1} V_n^2) / V_1 (Xcoil analyze, engine.js l.993). Xcoil floors V_1 at
    1e-18; here a zero fundamental gives infinity, so no division by zero is hidden.

    Parameters
    ----------
    harmonic_amplitudes : Mapping[int, float]
        Amplitude by harmonic order, any consistent unit; must contain order 1.

    Returns
    -------
    float
        THD, dimensionless.
    """
    rest = math.sqrt(math.fsum(v * v for n, v in harmonic_amplitudes.items() if n != 1))
    fundamental = harmonic_amplitudes[1]
    return rest / fundamental if fundamental > 0.0 else math.inf


def loss_budget_current_a(copper_loss_w: float, phases: int, phase_resistance_ohm: float) -> float:
    """Return the phase current that dissipates a copper-loss budget.

    References: EQ-21, I_ph = sqrt((P_Cu / m) / R_ph).

    Parameters
    ----------
    copper_loss_w : float
        Copper-loss budget of the machine in W.
    phases : int
        Phase count m.
    phase_resistance_ohm : float
        Phase resistance in ohm.

    Returns
    -------
    float
        Phase current in A rms.
    """
    return math.sqrt(copper_loss_w / phases / phase_resistance_ohm)


def current_density_a_per_mm2(
    phase_current_a: float, parallel_paths: int, width_mm: float, thickness_mm: float
) -> float:
    """Return the current density in the narrowest conductor.

    References: EQ-22, J = I_ph / (a w t).

    Parameters
    ----------
    phase_current_a : float
        Phase current in A rms.
    parallel_paths : int
        Parallel paths a.
    width_mm : float
        Narrowest track width in mm.
    thickness_mm : float
        Thinnest copper in mm.

    Returns
    -------
    float
        Current density in A/mm^2.
    """
    return phase_current_a / (parallel_paths * width_mm * thickness_mm)
