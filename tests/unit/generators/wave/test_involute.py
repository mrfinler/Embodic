"""Closed-form check of the wave involute (EQ-24, oracle_cases.json CF-08)."""

import math

import numpy as np
import pytest

from embodic.generators.wave.involute import involute_point

pytestmark = pytest.mark.req("REQ-F-35")
GOLDEN_SECTION = (math.sqrt(5.0) - 1.0) / 2.0


def _distance_to_involute(point: tuple[float, float], rb: float, phi0: float, u_near: float) -> float:
    """Smallest distance from ``point`` to the involute (rb, phi0): a scan around ``u_near``, then golden-section.

    Only u >= 0 counts. Negative u is the mirror branch past the cusp on the base circle, not part of the involute.
    """

    def distance(u: float) -> float:
        return math.dist(point, involute_point(rb, phi0, u))

    scan = np.linspace(max(0.0, u_near - 0.5), u_near + 0.5, 2001)
    best = int(np.argmin([distance(u) for u in scan]))
    lo, hi = float(scan[max(best - 1, 0)]), float(scan[min(best + 1, 2000)])
    for _ in range(80):
        a, b = hi - GOLDEN_SECTION * (hi - lo), lo + GOLDEN_SECTION * (hi - lo)
        if distance(a) < distance(b):
            hi = b
        else:
            lo = a
    return distance((lo + hi) / 2)


@pytest.mark.eqt("EQT-24-CF08")
def test_cf08_rotated_involute_copy_is_equidistant_by_rb_times_the_rotation() -> None:
    """CF-08 (EQ-24): r_b 20 mm, rotation 2 degrees -> every point of the curve is r_b * dphi = 0.6981317007977318 mm.

    Nine parameters t in [0.3, 1.5] rad, abs 1e-4 mm. Defect caught: a sign slip or swapped sine and cosine in the
    involute, which makes the rotated copy non-equidistant.
    """
    rb, dphi = 20.0, math.radians(2.0)
    for t in np.linspace(0.3, 1.5, 9):
        gap_mm = _distance_to_involute(involute_point(rb, 0.0, float(t)), rb, dphi, float(t))
        assert gap_mm == pytest.approx(0.6981317007977318, abs=1e-4)
