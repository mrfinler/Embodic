"""Physics kernels (interfaces.md section 8). Kernels return plain floats or arrays; each cites its EQ-ID."""

from embodic.physics.analyse import analyse
from embodic.physics.circuit import (
    CircuitSolution,
    delta_circulating_loss_w,
    efficiency,
    line_resistance_ohm,
    solve_phase_circuit,
)
from embodic.physics.constants import MotorConstants, phase_constants
from embodic.physics.drive import (
    base_speed_rpm,
    inverter_phase_voltage_v,
    no_load_speed_rpm,
    torque_speed_envelope,
)
from embodic.physics.emf import eddy_loss_w, edge_leakage_fraction, field_table, integrate_path
from embodic.physics.estimates import MassBreakdown, inductance_estimate_h, mass_g
from embodic.physics.field import field_harmonic, symmetry_plane_mm
from embodic.physics.losses import (
    current_density_a_per_mm2,
    ipc2221_current_a,
    loss_budget_current_a,
    skin_depth_mm,
    thd,
)
from embodic.physics.magnets import pole_arc_ratio_block
from embodic.physics.resistance import copper_resistivity_ohm_m, path_resistance_ohm, via_resistance_ohm
from embodic.physics.thermal import temperature_rise_k
from embodic.physics.waveform import emf_waveform_v, line_waveforms_v

__all__ = [
    "CircuitSolution",
    "MassBreakdown",
    "MotorConstants",
    "analyse",
    "base_speed_rpm",
    "copper_resistivity_ohm_m",
    "current_density_a_per_mm2",
    "delta_circulating_loss_w",
    "eddy_loss_w",
    "edge_leakage_fraction",
    "efficiency",
    "emf_waveform_v",
    "field_harmonic",
    "field_table",
    "inductance_estimate_h",
    "integrate_path",
    "inverter_phase_voltage_v",
    "ipc2221_current_a",
    "line_resistance_ohm",
    "line_waveforms_v",
    "loss_budget_current_a",
    "mass_g",
    "no_load_speed_rpm",
    "path_resistance_ohm",
    "phase_constants",
    "pole_arc_ratio_block",
    "skin_depth_mm",
    "solve_phase_circuit",
    "symmetry_plane_mm",
    "temperature_rise_k",
    "thd",
    "torque_speed_envelope",
    "via_resistance_ohm",
]
