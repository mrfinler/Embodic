"""Physics kernels (interfaces.md section 8). Kernels return plain floats or arrays; each cites its EQ-ID."""

from embodic.physics.constants import MotorConstants, phase_constants
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

__all__ = [
    "MotorConstants",
    "copper_resistivity_ohm_m",
    "current_density_a_per_mm2",
    "field_harmonic",
    "ipc2221_current_a",
    "loss_budget_current_a",
    "path_resistance_ohm",
    "phase_constants",
    "pole_arc_ratio_block",
    "skin_depth_mm",
    "symmetry_plane_mm",
    "temperature_rise_k",
    "thd",
    "via_resistance_ohm",
]
