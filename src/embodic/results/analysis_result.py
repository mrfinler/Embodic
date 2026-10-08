"""Result containers of one analysis, per phase and per layer, and their JSON form (interfaces.md section 3).

Every number is a `Traceable`, so the JSON carries value, unit, EQ-IDs, evidence, badge, reasons and the assumed-inputs
tag next to each other (REQ-T-02, REQ-T-07). Non-finite floats use the board-dump encoding of interfaces.md section
9.2: ``{"$f": "nan"}``, ``{"$f": "inf"}``, ``{"$f": "-inf"}``.
"""

import dataclasses
import math
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any

from embodic.model.schema import JsonValue
from embodic.model.vocabulary import Phase
from embodic.results.traceable import Traceable


@dataclass(frozen=True, slots=True, kw_only=True)
class LayerResult:
    """Field results of one copper layer."""

    layer: str
    z_mm: Traceable[float]
    b1_peak_mid_radius_t: Traceable[float]


@dataclass(frozen=True, slots=True, kw_only=True)
class PhaseResult:
    """Results of one phase."""

    phase: Phase
    ke_peak_v_s_per_rad: Traceable[float]
    emf_phasor_angle_rad: Traceable[float]  # argument of the fundamental EMF phasor, in (-pi, pi]
    resistance_20c_ohm: Traceable[float]
    resistance_operating_ohm: Traceable[float]
    circulating_loss_w: Traceable[float]


@dataclass(frozen=True, slots=True, kw_only=True)
class TorqueSpeedEstimate:
    """Torque-speed envelope (EQ-20); only with a DC-link voltage."""

    speed_rpm: Traceable[tuple[float, ...]]
    torque_n_m: Traceable[tuple[float, ...]]
    power_w: Traceable[tuple[float, ...]]
    no_load_speed_rpm: Traceable[float]
    base_speed_rpm: Traceable[float]


@dataclass(frozen=True, slots=True, kw_only=True)
class AnalysisResult:
    """Every computed quantity of one design."""

    ke_phase_v_s_per_rad: Traceable[float]  # EQ-06, EQ-09
    ke_line_v_s_per_rad: Traceable[float]  # EQ-09
    ke_line_peak_v_s_per_rad: Traceable[float]  # EQ-18, EQ-09: peak of the synthesised line waveform per mech. rad/s
    kt_n_m_per_a: Traceable[float]  # EQ-09
    kv_rpm_per_v: Traceable[float]  # EQ-09
    winding_factor_1: Traceable[float]  # EQ-08 (spiral); kind_tag "derived" from the generator for serpentine/wave
    resistance_phase_20c_ohm: Traceable[float]  # EQ-10, EQ-11
    resistance_phase_operating_ohm: Traceable[float]
    resistance_line_ohm: Traceable[float]
    emf_phase_rms_v: Traceable[float]
    torque_n_m: Traceable[float]
    loss_copper_w: Traceable[float]
    loss_eddy_w: Traceable[float]  # EQ-12
    loss_circulating_w: Traceable[float]  # EQ-07
    loss_delta_circulating_w: Traceable[float]  # EQ-19
    loss_interconnect_w: Traceable[float]  # EQ-23 P_ic
    loss_total_w: Traceable[float]  # EQ-26 P_Cu + P_eddy + P_circ + P_delta,circ + P_ic
    output_power_w: Traceable[float]  # EQ-26 P_out = T * omega_m
    efficiency: Traceable[float]  # EQ-26 P_out / (P_out + P_loss), electromagnetic only
    motor_constant_n_m_per_sqrt_w: Traceable[float]  # EQ-26 K_m = T / sqrt(P_Cu)
    thd_phase: Traceable[float]  # EQ-18
    thd_line: Traceable[float]
    current_density_a_per_mm2: Traceable[float]  # EQ-22
    skin_depth_mm: Traceable[float]  # EQ-13
    inductance_estimate_h: Traceable[float]  # EQ-14, badge unresolved, label "estimate"
    ipc_guideline_current_a: Traceable[float]  # EQ-15, badge unresolved, label "guideline (unverified)"
    mass_copper_g: Traceable[float]  # EQ-16
    mass_laminate_g: Traceable[float]
    temperature_rise_k: Traceable[float]  # EQ-17
    edge_leakage_fraction: Traceable[float]  # EC-05 metric e_edge; status assumption (transfer, DEF-23)
    layers: tuple[LayerResult, ...]
    phases: tuple[PhaseResult, ...]
    emf_waveform_v: Traceable[tuple[float, ...]]  # EQ-18, one electrical period
    torque_speed: TorqueSpeedEstimate | None  # EQ-20; None without dc_link_v
    registry_version: str

    def to_json(self) -> dict[str, JsonValue]:
        """Return the result as JSON-compatible data; every Traceable keeps its status, reasons and tag."""
        data = to_json(self)
        assert isinstance(data, dict)
        return data


def to_json(value: Any) -> JsonValue:
    """Convert a results dataclass tree to JSON-compatible data (enums by value, tuples as lists)."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: to_json(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, Enum):
        return to_json(value.value)
    if isinstance(value, float) and not math.isfinite(value):
        return {"$f": "nan" if math.isnan(value) else ("inf" if value > 0 else "-inf")}
    if isinstance(value, tuple | list):
        return [to_json(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): to_json(item) for key, item in value.items()}
    if value is None or isinstance(value, bool | int | float | str):
        return value
    raise TypeError(f"no JSON form for {type(value).__name__}")
