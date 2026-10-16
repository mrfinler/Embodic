"""EQ-23 closed forms of the interconnect copper loss and the neutral-ring segments (U-M2e-4).

Expected values are written from Xcoil applyConnection l.1422-1429 and interconnectResistance l.1369-1370 with example
resistances, not from the module.
"""

import math

import pytest

from embodic.geometry.primitives import Arc, Line, PrimitiveRole
from embodic.model.vocabulary import ConnectionTopology
from embodic.physics.interconnect import InterconnectResistance, interconnect_loss_w, ring_segment_resistance_ohm

pytestmark = pytest.mark.req("REQ-F-11")
SUMS = InterconnectResistance(  # example values in ohm
    line_stub_ohm=(0.001, 0.002, 0.003),
    link_ohm=(0.004, 0.005, 0.006),
    neutral_ring_ohm=(0.007, 0.008),
)
RHO = 1.7e-8  # ohm*m, example
T_MM = 0.035
W_MM = 1.0
OHM_PER_MM = RHO / 1e3 / (W_MM / 1e3 * T_MM / 1e3)


@pytest.mark.parametrize(
    ("connection", "expected_w"),
    [
        (ConnectionTopology.STAR, 4.0 * 0.036),  # every role carries the 2 A line current
        (ConnectionTopology.DELTA, 4.0 * 0.006 + (4.0 / 3.0) * 0.015),  # links carry I_line / sqrt 3, no ring
        (ConnectionTopology.OPEN, 0.0),
    ],
)
def test_interconnect_loss_uses_the_current_of_each_role(connection: ConnectionTopology, expected_w: float) -> None:
    """Defect caught: delta links at the line current, a delta ring counted, or an open winding with P_ic."""
    assert interconnect_loss_w(SUMS, connection, 2.0) == pytest.approx(expected_w, rel=1e-14, abs=0.0)


def _ring(start: float, sweep: float, r_mm: float = 30.0) -> Arc:
    return Arc(
        cx_mm=0.0, cy_mm=0.0, r_mm=r_mm, start_rad=start, sweep_rad=sweep, width_mm=W_MM, role=PrimitiveRole.RING
    )


def _at(angle: float, r_mm: float = 30.0) -> tuple[float, float]:
    return (r_mm * math.cos(angle), r_mm * math.sin(angle))


@pytest.mark.parametrize("sweep_sign", [1.0, -1.0])
def test_ring_segments_are_the_arc_between_consecutive_taps(sweep_sign: float) -> None:
    """Defect caught: the whole ring per segment, a wrong direction on a clockwise ring, or a segment from the centre.

    Taps at 0, 50 and 120 degrees along the sweep of a 30 mm ring: segments 30 * 50 deg and 30 * 70 deg.
    """
    angles = [0.0, math.radians(50.0), math.radians(120.0)]
    ring = _ring(0.0, sweep_sign * math.radians(120.0))
    taps = [_at(sweep_sign * a) for a in angles]
    got = ring_segment_resistance_ohm([ring], taps, T_MM, RHO)
    expected = [30.0 * math.radians(50.0) * OHM_PER_MM, 30.0 * math.radians(70.0) * OHM_PER_MM]
    assert got == pytest.approx(expected, rel=1e-12, abs=0.0)


def test_a_tap_a_rounding_error_before_the_ring_start_lands_on_the_start() -> None:
    """Defect caught: an angle of -1e-12 rad wrapped to 2 pi, which puts the first tap at the far ring end."""
    ring = _ring(1.0, math.radians(90.0))
    taps = [_at(1.0 - 1e-12), _at(1.0 + math.radians(90.0))]
    got = ring_segment_resistance_ohm([ring], taps, T_MM, RHO)
    assert got == pytest.approx([30.0 * math.radians(90.0) * OHM_PER_MM], rel=1e-9)


def test_a_segment_spanning_two_primitives_adds_both_parts() -> None:
    """Defect caught: a segment cut at the end of the first primitive of the path."""
    first = Line(x1_mm=0.0, y1_mm=0.0, x2_mm=10.0, y2_mm=0.0, width_mm=W_MM, role=PrimitiveRole.RING)
    second = Line(x1_mm=10.0, y1_mm=0.0, x2_mm=10.0, y2_mm=10.0, width_mm=2.0 * W_MM, role=PrimitiveRole.RING)
    got = ring_segment_resistance_ohm([first, second], [(4.0, 0.3), (10.2, 5.0)], T_MM, RHO)
    assert got == pytest.approx([6.0 * OHM_PER_MM + 5.0 * OHM_PER_MM / 2.0], rel=1e-12, abs=0.0)
