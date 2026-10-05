"""UT-UNI-01: unit conversions, display forms and the quantisation helper (REQ-N-21)."""

import math

import pytest
from hypothesis import given
from hypothesis import strategies as st

from embodic import units
from embodic.units import Unit

# Subnormal floats lose bits through the pi/180 factor; no length or angle in a design is that small.
physical = st.floats(min_value=-1e9, max_value=1e9).filter(lambda x: x == 0.0 or abs(x) >= 1e-12)


def within_ulps(actual: float, expected: float, ulps: int) -> bool:
    """Return True when two floats differ by at most ``ulps`` units in the last place of ``expected``."""
    return abs(actual - expected) <= ulps * math.ulp(expected)


@pytest.mark.req("REQ-N-21")
@pytest.mark.parametrize(
    ("convert", "value", "expected"),
    [
        (units.deg_to_rad, 180.0, math.pi),
        (units.deg_to_rad, -90.0, -math.pi / 2),
        (units.rad_to_deg, math.pi, 180.0),
        (units.mm_to_m, 1000.0, 1.0),
        (units.mm_to_m, 0.0348, 3.48e-5),
        (units.rpm_to_rad_per_s, 60.0, 2 * math.pi),
        (units.rpm_to_rad_per_s, 1000.0, 104.71975511965977),
        (units.copper_oz_to_mm, 1.0, 0.0348),
        (units.copper_oz_to_mm, 2.0, 0.0696),
        (units.mil2_to_mm2, 1.0, 0.00064516),
        (units.mm2_to_mil2, 0.00064516, 1.0),
        (units.mm2_to_mil2, 0.5 * 0.0348, 26.97005394010788),
    ],
)
def test_units_conversion_matches_reference_value(convert, value, expected):
    """Catches a wrong factor or direction: 1 mil = 0.0254 mm exactly, 1 oz copper = 0.0348 mm (Xcoil OZ_TO_MM)."""
    assert within_ulps(convert(value), expected, 2)


@pytest.mark.req("REQ-N-21")
@given(physical)
def test_units_round_trips_stay_within_two_ulps(value):
    """Catches a forward/inverse pair that drifts, e.g. one side using a rounded constant.

    mm to m and rpm to rad/s have no inverse function in interfaces.md section 1, so the test inverts them with the
    defining factor (1000 mm per m, 60 s per minute and 2 pi rad per revolution).
    """
    assert within_ulps(units.rad_to_deg(units.deg_to_rad(value)), value, 2)
    assert within_ulps(units.mil2_to_mm2(units.mm2_to_mil2(value)), value, 2)
    assert within_ulps(units.mm_to_m(value) * 1000.0, value, 2)
    assert within_ulps(units.rpm_to_rad_per_s(value) * 60.0 / (2.0 * math.pi), value, 2)


def is_positive_zero(value: float) -> bool:
    """Return True only for +0.0, so a test can tell it from -0.0, which compares equal."""
    return value == 0.0 and math.copysign(1.0, value) == 1.0


@pytest.mark.req("REQ-N-21")
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (2.5, 3.0),
        (-2.5, -2.0),
        (0.5, 1.0),
        (-0.5, 0.0),
        (-1.5, -1.0),
        (0.49999999999999994, 0.0),
        (-0.49999999999999994, 0.0),
        (2.4, 2.0),
        (-2.6, -3.0),
        (4503599627370495.5, 4503599627370496.0),
    ],
)
def test_units_js_round_matches_javascript_math_round(value, expected):
    """Catches half away from zero (-2.5 to -3), round() (2.5 to 2) and floor(x + 0.5) (0.49999999999999994 to 1).

    Expected values printed by Node v22 Math.round (interfaces.md section 1).
    """
    assert units.js_round(value) == expected


@pytest.mark.req("REQ-N-21")
@pytest.mark.parametrize("value", [-0.5, -0.49999999999999994, -0.3, -0.0])
def test_units_js_round_never_returns_negative_zero(value):
    """Catches a -0.0 result (JS Math.round(-0.3) is -0), which a writer would print as '-0'."""
    assert is_positive_zero(units.js_round(value))


@pytest.mark.req("REQ-N-21")
@pytest.mark.parametrize(
    ("value", "scale", "expected"),
    [
        (-0.000025, 1e5, -0.00002),
        (0.000025, 1e5, 0.00003),
        (0.123456, 1e5, 0.12346),
        (12.5, 1.0, 13.0),
        (7.0, 1e5, 7.0),
    ],
)
def test_units_quantise_matches_xcoil_fmt(value, scale, expected):
    """Catches negative ties rounded away from zero and a quantiser that divides by a step instead of the scale.

    Xcoil fmt(-0.000025) is -0.00002 (Node v22, interfaces.md section 1).
    """
    assert units.quantise(value, scale) == expected


@pytest.mark.req("REQ-N-21")
@pytest.mark.parametrize("value", [-1e-7, -0.000005, -0.0])
def test_units_quantise_never_returns_negative_zero(value):
    """Catches '-0' in fixed-decimal writer output when a small negative coordinate quantises to zero."""
    assert is_positive_zero(units.quantise(value, 1e5))


@pytest.mark.req("REQ-N-21")
def test_units_every_unit_has_a_display_form():
    """Catches a Unit member added without a display form, which would show the raw code in the UI."""
    displayed = {unit: unit.display() for unit in Unit}
    assert displayed[Unit.OHM] == "Ω"
    assert displayed[Unit.V_S_PER_RAD] == "V·s/rad"
    assert displayed[Unit.A_PER_MM2] == "A/mm²"
    assert displayed[Unit.DEGC] == "°C"
    assert displayed[Unit.ONE] == ""
    assert all(isinstance(text, str) for text in displayed.values())


@pytest.mark.req("REQ-N-21")
@pytest.mark.parametrize(
    ("code", "display"),
    [
        ("um", "µm"),
        ("W_per_m2_K", "W/(m²·K)"),
        ("ohm_m", "Ω·m"),
        ("per_K", "1/K"),
        ("g_per_cm3", "g/cm³"),
    ],
)
def test_units_property_input_units_exist(code, display):
    """Catches DEF-M2a-01: plating (µm), convection (W/(m²·K)) and material overrides (Ω·m, 1/K, g/cm³) unitless.

    The code is what a project file stores in a PropertyValue, so it is pinned; the display is the SI symbol.
    """
    assert Unit(code).display() == display


@pytest.mark.req("REQ-N-21")
@pytest.mark.parametrize(("code", "display"), [("H_per_m", "H/m"), ("F_per_m", "F/m")])
def test_units_vacuum_constant_units_exist(code, display):
    """Catches mu_0 (H/m) and eps_0 (F/m) having no unit, which keeps them out of the registry constants (U-E2)."""
    assert Unit(code).display() == display
    assert Unit(code).value == code
