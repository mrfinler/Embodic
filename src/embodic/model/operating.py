"""Operating point and drive inputs (interfaces.md section 2.1)."""

from dataclasses import dataclass
from enum import StrEnum


class Modulation(StrEnum):
    """Inverter modulation used by the torque-speed estimate."""

    SVPWM = "svpwm"
    SPWM = "spwm"
    SIX_STEP = "six_step"


@dataclass(frozen=True, slots=True, kw_only=True)
class OperatingPoint:
    """Speed, current, temperatures and cooling; `convection_h_w_m2k` is a property input (EQ-17)."""

    speed_rpm: float
    line_current_rms_a: float
    winding_temperature_degc: float
    ambient_temperature_degc: float
    convection_h_w_m2k: float
    dc_link_v: float | None = None  # None: no torque-speed estimate (EQ-20)
    modulation: Modulation = Modulation.SVPWM
