"""Unit vocabulary, conversions and rounding with JavaScript Math.round semantics.

Every conversion between unit systems goes through this module (ADR-0009). Inside the core, lengths are millimetres
and angles radians; degrees, ounces of copper and square mils exist only at input and output boundaries.
"""

import math
from enum import StrEnum
from types import MappingProxyType
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]

MM_PER_M = 1000.0
MM_PER_MIL = 0.0254
"""One mil is 0.001 inch and one inch is exactly 25.4 mm."""
MM2_PER_MIL2 = MM_PER_MIL * MM_PER_MIL
MM_PER_COPPER_OZ = 0.0348
"""Finished thickness of 1 oz/ft² copper. Status: assumption (Xcoil engine.js l.14 and D08 p.54 use 34.8 µm)."""


class Unit(StrEnum):
    """Closed unit vocabulary of every Traceable. The value is the canonical code; `display()` gives the UI form."""

    MM = "mm"
    MM2 = "mm2"
    M = "m"
    UM = "um"
    RAD = "rad"
    T = "T"
    V = "V"
    V_S_PER_RAD = "V_s_per_rad"
    N_M_PER_A = "N_m_per_A"
    RPM_PER_V = "rpm_per_V"
    OHM = "ohm"
    OHM_M = "ohm_m"
    H = "H"
    H_PER_M = "H_per_m"
    W = "W"
    W_PER_M2_K = "W_per_m2_K"
    A = "A"
    A_PER_MM2 = "A_per_mm2"
    K = "K"
    PER_K = "per_K"
    DEGC = "degC"
    G = "g"
    G_PER_CM3 = "g_per_cm3"
    N_M = "N_m"
    RPM = "rpm"
    HZ = "Hz"
    F_PER_M = "F_per_m"
    ONE = "one"
    COUNT = "count"

    def display(self) -> str:
        """Return the form shown next to a number in the UI and in reports."""
        return _DISPLAY[self]


_DISPLAY = MappingProxyType(
    {
        Unit.MM: "mm",
        Unit.MM2: "mm²",
        Unit.M: "m",
        Unit.UM: "µm",
        Unit.RAD: "rad",
        Unit.T: "T",
        Unit.V: "V",
        Unit.V_S_PER_RAD: "V·s/rad",
        Unit.N_M_PER_A: "N·m/A",
        Unit.RPM_PER_V: "rpm/V",
        Unit.OHM: "Ω",
        Unit.OHM_M: "Ω·m",
        Unit.H: "H",
        Unit.H_PER_M: "H/m",
        Unit.W: "W",
        Unit.W_PER_M2_K: "W/(m²·K)",
        Unit.A: "A",
        Unit.A_PER_MM2: "A/mm²",
        Unit.K: "K",
        Unit.PER_K: "1/K",
        Unit.DEGC: "°C",
        Unit.G: "g",
        Unit.G_PER_CM3: "g/cm³",
        Unit.N_M: "N·m",
        Unit.RPM: "rpm",
        Unit.HZ: "Hz",
        Unit.F_PER_M: "F/m",
        Unit.ONE: "",
        Unit.COUNT: "",
    }
)


def deg_to_rad(angle_deg: float) -> float:
    """Convert an angle from degrees to radians."""
    return math.radians(angle_deg)


def rad_to_deg(angle_rad: float) -> float:
    """Convert an angle from radians to degrees."""
    return math.degrees(angle_rad)


def mm_to_m(length_mm: float) -> float:
    """Convert a length from millimetres to metres."""
    return length_mm / MM_PER_M


def rpm_to_rad_per_s(speed_rpm: float) -> float:
    """Convert a mechanical speed from revolutions per minute to radians per second."""
    return speed_rpm * (2.0 * math.pi / 60.0)


def copper_oz_to_mm(copper_oz: float) -> float:
    """Convert a copper weight in oz/ft² to a finished thickness in mm (see `MM_PER_COPPER_OZ` for the status)."""
    return copper_oz * MM_PER_COPPER_OZ


def mm2_to_mil2(area_mm2: float) -> float:
    """Convert a cross-section area from mm² to mil², the area unit of the IPC-2221 current formula."""
    return area_mm2 / MM2_PER_MIL2


def mil2_to_mm2(area_mil2: float) -> float:
    """Convert a cross-section area from mil² to mm²."""
    return area_mil2 * MM2_PER_MIL2


def js_round(value: float) -> float:
    """Round like ECMAScript Math.round: the nearest integer, ties toward +inf (js_round(-2.5) == -2.0).

    Parameters
    ----------
    value : float
        A finite number.

    Returns
    -------
    float
        The rounded integer as a float. Never -0.0, so a writer cannot emit "-0".
    """
    count = math.floor(value)
    # Comparing the exact fractional part avoids floor(x + 0.5), which turns 0.49999999999999994 into 1.
    if value - count >= 0.5:
        count += 1
    return float(count)


def quantise(value: float, scale: float) -> float:
    """Quantise like Xcoil fmt(): js_round(value * scale) / scale. Built-in round() is banned on coordinates (MT-06).

    Parameters
    ----------
    value : float
        The number to quantise, in any unit.
    scale : float
        Quanta per unit of `value`, positive; writers that emit fixed decimals use 1e5 (0.00001 mm).

    Returns
    -------
    float
        `value` on the grid of 1 / `scale`. Never -0.0.
    """
    return js_round(value * scale) / scale
