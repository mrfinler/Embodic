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
    """Catches a forward/inverse pair that drifts, e.g. one side using a rounded constant."""
    assert within_ulps(units.rad_to_deg(units.deg_to_rad(value)), value, 2)
    assert within_ulps(units.mil2_to_mm2(units.mm2_to_mil2(value)), value, 2)


@pytest.mark.req("REQ-N-21")
@pytest.mark.parametrize(
    ("value", "step", "expected"),
    [
        (0.25, 0.5, 0.5),
        (-0.25, 0.5, -0.5),
        (2.5, 1.0, 3.0),
        (-2.5, 1.0, -3.0),
        (0.49999999999999994, 1.0, 0.0),
        (1.23456, 0.001, 1.235),
        (-1.23449, 0.001, -1.234),
        (7.0, 0.5, 7.0),
    ],
)
def test_units_round_half_away_from_zero_breaks_ties_away_from_zero(value, step, expected):
    """Catches built-in round() (half to even turns 2.5 into 2) and the floor(x + 0.5) trick (0.4999... becomes 1)."""
    assert within_ulps(units.round_half_away_from_zero(value, step), expected, 2)


@pytest.mark.req("REQ-N-21")
def test_units_round_half_away_from_zero_never_returns_negative_zero():
    """Catches '-0' in fixed-decimal writer output when a small negative coordinate quantises to zero."""
    result = units.round_half_away_from_zero(-1e-7, 0.001)
    assert result == 0.0
    assert math.copysign(1.0, result) == 1.0


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
