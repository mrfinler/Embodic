"""English display label and spec symbol of every AnalysisResult field, for result cards and tables (D-038e, D-039).

Names follow equation_specification.md (equation titles and variable names). The two labels the shell's summary strip
shows are the same text as ``shell.sum-ke.label`` and ``shell.sum-r-phase.label`` in ``embodic.ui.strings.shell``.
"""

from collections.abc import Mapping
from types import MappingProxyType

QUANTITY_LABELS: Mapping[str, str] = MappingProxyType(
    {
        "ke_phase_v_s_per_rad": "Phase back-EMF constant, fundamental",  # EQ-09 Ke_ph
        "ke_line_v_s_per_rad": "Line back-EMF constant, fundamental",  # EQ-09 Ke_LL
        "ke_line_peak_v_s_per_rad": "Line back-EMF constant, peak",  # EQ-18
        "kt_n_m_per_a": "Torque constant per line current, rms",  # EQ-09 Kt
        "kv_rpm_per_v": "Speed constant",  # EQ-09 K_v
        "winding_factor_1": "Fundamental winding factor",  # EQ-08 k_w1
        "resistance_phase_20c_ohm": "Phase resistance at 20 °C",  # EQ-10
        "resistance_phase_operating_ohm": "Phase resistance at operating temperature",  # EQ-10
        "resistance_line_ohm": "Line-to-line resistance",  # EQ-23
        "emf_phase_rms_v": "Phase back-EMF, rms",
        "torque_n_m": "Torque",
        "loss_copper_w": "Copper loss",  # EQ-26 P_Cu
        "loss_eddy_w": "Eddy-current loss",  # EQ-12
        "loss_circulating_w": "Circulating-current loss",  # EQ-07
        "loss_delta_circulating_w": "Delta circulating-current loss",  # EQ-19
        "loss_interconnect_w": "Interconnect loss",  # EQ-23 P_ic
        "loss_total_w": "Total loss",  # EQ-26
        "output_power_w": "Output power",  # EQ-26 P_out
        "efficiency": "Efficiency, electromagnetic only",  # EQ-26
        "motor_constant_n_m_per_sqrt_w": "Motor constant",  # EQ-26 K_m
        "thd_phase": "Total harmonic distortion, phase",  # EQ-18
        "thd_line": "Total harmonic distortion, line",  # EQ-18
        "current_density_a_per_mm2": "Current density",  # EQ-22
        "skin_depth_mm": "Skin depth",  # EQ-13
        "inductance_estimate_h": "Inductance, estimate",  # EQ-14
        "ipc_guideline_current_a": "IPC-2221 current capacity, guideline",  # EQ-15
        "mass_copper_g": "Copper mass",  # EQ-16
        "mass_laminate_g": "Laminate mass",  # EQ-16
        "temperature_rise_k": "Temperature rise, first-order estimate",  # EQ-17
        "edge_leakage_fraction": "Radial edge leakage fraction",  # EC-05 e_edge
        "layers": "Field results per copper layer",
        "phases": "Results per phase",
        "emf_waveform_v": "Phase EMF waveform, one electrical period",  # EQ-18
        "torque_speed": "Torque-speed envelope",  # EQ-20
        "registry_version": "Equation registry version",
    }
)

# Symbols exactly as equation_specification.md writes them; "l." is the spec line. A field with no stated symbol has no
# entry: the peak line constant, the rms phase EMF, THD (an abbreviation) and the IPC current (the bare "I" of EQ-15).
# The four Greek ones (η, δ, ΔT, P_δ,circ) are allowed in this module only: tests/static/test_lg_language.py (D-040).
QUANTITY_SYMBOLS: Mapping[str, str] = MappingProxyType(
    {
        "ke_phase_v_s_per_rad": "Ke_ph",  # l.219
        "ke_line_v_s_per_rad": "Ke_LL",  # l.219
        "kt_n_m_per_a": "Kt",  # l.220
        "kv_rpm_per_v": "K_v",  # l.220
        "winding_factor_1": "k_w1",  # l.337, EQ-14 (N k_w1)
        "resistance_phase_20c_ohm": "R_ph",  # l.422
        "resistance_phase_operating_ohm": "R_ph",  # l.422
        "resistance_line_ohm": "R_LL",  # l.441
        "torque_n_m": "T",  # l.511
        "loss_copper_w": "P_Cu",  # l.509
        "loss_eddy_w": "P_eddy",  # l.509
        "loss_circulating_w": "P_circ",  # l.509
        "loss_interconnect_w": "P_ic",  # l.441
        "loss_total_w": "P_loss",  # l.509
        "loss_delta_circulating_w": "P_δ,circ",  # l.509
        "output_power_w": "P_out",  # l.509
        "efficiency": "η",  # l.509
        "motor_constant_n_m_per_sqrt_w": "K_m",  # l.509
        "current_density_a_per_mm2": "J",  # l.429
        "skin_depth_mm": "δ",  # l.326
        "temperature_rise_k": "ΔT",  # l.373
        "inductance_estimate_h": "L_m",  # l.337, EQ-14 (a): the form `inductance_estimate_h` computes
        "mass_copper_g": "m_Cu",  # l.362
        "mass_laminate_g": "m_lam",  # l.362
        "edge_leakage_fraction": "e_edge",  # l.114
    }
)


def quantity_title(quantity: str) -> str:
    """Return the card and report title of a field: its label, then its spec symbol when one is stated."""
    symbol = QUANTITY_SYMBOLS.get(quantity)
    return QUANTITY_LABELS[quantity] if symbol is None else f"{QUANTITY_LABELS[quantity]} {symbol}"
