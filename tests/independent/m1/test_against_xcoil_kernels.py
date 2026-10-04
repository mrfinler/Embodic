"""Validate the instrument, not embodic: Agent 4 kernels against Xcoil v3 segSegDist, ptSegDist and drcObjects.

The Xcoil engine is the team's own prior work, run read-only under Node (port notes section 7.4).
"""

import math

import numpy as np
import pytest
import xcoil_oracle
from brute_clearance import centreline_bracket, clearance_bracket, point_segment_distance
from records import Arc, Line

pytestmark = [
    pytest.mark.req("REQ-F-10"),
    pytest.mark.skipif(not xcoil_oracle.available(), reason="needs node and /home/claude/serpentine/src/engine.js"),
]

AGREEMENT_MM = 1e-9


def random_pairs(seed: int) -> list[tuple[Line, Line]]:
    """200 seeded segment pairs: 120 general, and 20 each crossing, parallel, collinear and touching."""
    rng = np.random.default_rng(seed)

    def seg(x1: float, y1: float, x2: float, y2: float) -> Line:
        return Line(float(x1), float(y1), float(x2), float(y2), 0.0)

    pairs = [(seg(*rng.uniform(-20, 20, 4)), seg(*rng.uniform(-20, 20, 4))) for _ in range(120)]
    for _ in range(20):
        cx, cy, a, b = *rng.uniform(-10, 10, 2), *rng.uniform(0, math.pi, 2)
        r1, r2 = rng.uniform(0.5, 5, 2)
        pairs.append(
            (
                seg(cx - r1 * math.cos(a), cy - r1 * math.sin(a), cx + r1 * math.cos(a), cy + r1 * math.sin(a)),
                seg(cx - r2 * math.cos(b), cy - r2 * math.sin(b), cx + r2 * math.cos(b), cy + r2 * math.sin(b)),
            )
        )
    for _ in range(20):
        x, y, dx, dy = rng.uniform(-10, 10, 4)
        off, shift = rng.uniform(-2, 2), rng.uniform(-15, 15)
        nx, ny = -dy / math.hypot(dx, dy), dx / math.hypot(dx, dy)
        pairs.append((seg(x, y, x + dx, y + dy), seg(x + off * nx + shift * dx / 10, y + off * ny + shift * dy / 10,
                                                      x + off * nx + dx, y + off * ny + dy)))  # fmt: skip
    for _ in range(20):
        x, y, dx, dy = rng.uniform(-10, 10, 4)
        t0, t1 = sorted(rng.uniform(-1, 2, 2))
        pairs.append((seg(x, y, x + dx, y + dy), seg(x + t0 * dx, y + t0 * dy, x + t1 * dx, y + t1 * dy)))
    for _ in range(20):
        x, y, dx, dy, ex, ey = rng.uniform(-10, 10, 6)
        t = rng.uniform(0, 1)
        px, py = x + t * dx, y + t * dy
        pairs.append((seg(x, y, x + dx, y + dy), seg(px, py, px + ex, py + ey)))
    return pairs


def test_segment_distance_agrees_with_xcoil_seg_seg_dist_on_200_pairs() -> None:
    """Catch a wrong crossing test or end-point reduction in the instrument's exact line kernel."""
    pairs = random_pairs(20261004)
    assert len(pairs) == 200
    reference = xcoil_oracle.seg_seg_dist(pairs)
    worst = 0.0
    for (a, b), expected in zip(pairs, reference, strict=True):
        bracket = centreline_bracket(a, b)
        assert bracket.lo - AGREEMENT_MM <= expected <= bracket.hi + AGREEMENT_MM, (a, b, bracket, expected)
        worst = max(worst, abs((bracket.lo + bracket.hi) / 2 - expected))
    assert worst <= AGREEMENT_MM
    assert sum(d == 0.0 for d in reference) >= 20, "the crossing cases must reach the zero branch"


def test_point_segment_distance_agrees_with_xcoil_pt_seg_dist() -> None:
    """Includes zero-length segments, which is how the instrument represents a via disc."""
    rng = np.random.default_rng(7)
    cases = [(*rng.uniform(-20, 20, 2), Line(*rng.uniform(-20, 20, 4), 0.0)) for _ in range(180)]
    cases += [(*rng.uniform(-20, 20, 2), Line(x, y, x, y, 0.0)) for x, y in rng.uniform(-20, 20, (20, 2))]
    reference = xcoil_oracle.pt_seg_dist(cases)
    px = np.array([c[0] for c in cases])
    py = np.array([c[1] for c in cases])
    segs = np.array([[c[2].x1, c[2].y1, c[2].x2, c[2].y2] for c in cases])
    np.testing.assert_allclose(point_segment_distance(px, py, segs), reference, rtol=0, atol=AGREEMENT_MM)


def test_drc_objects_agrees_on_parallel_tracks() -> None:
    """Xcoil's layered DRC on two straight tracks equals the instrument's clearance (lines discretise exactly)."""
    a = Line(0.0, 0.0, 3.0, 0.0, 0.2)
    b = Line(0.5, 0.35, 2.5, 0.35, 0.2)
    expected = clearance_bracket(a, b)
    assert abs(xcoil_oracle.drc_objects([[a], [b]], 0.15) - expected.hi) <= AGREEMENT_MM


def test_drc_objects_on_concentric_arcs_is_within_its_discretisation_bound() -> None:
    """Xcoil chords each arc with sagitta <= 0.001 mm, so it may differ from the exact 0.15 mm by at most 0.002 mm."""
    a = Arc(0.0, 0.0, 2.0, 0.0, 1.0, 0.2)
    b = Arc(0.0, 0.0, 2.35, 0.0, 1.0, 0.2)
    exact = clearance_bracket(a, b, tol=1e-9)
    assert exact.lo <= 0.15 <= exact.hi
    assert abs(xcoil_oracle.drc_objects([[a], [b]], 0.15) - 0.15) <= 0.002
