"""Self-tests of the brute clearance instrument: closed-form distances and seeded 1 um intrusions (IT-12, PR-01)."""

import math
from collections.abc import Callable

import numpy as np
import pytest
from brute_clearance import (
    DRC_EPSILON_MM,
    Bracket,
    Verdict,
    brute_violations,
    centreline_bracket,
    clearance_bracket,
    no_exemptions,
    pair_verdict,
)
from records import Arc, Line, Prim, disc

pytestmark = pytest.mark.req("REQ-F-10")

TIGHT = 1e-10


def assert_brackets(bracket: Bracket, expected: float, tol: float = TIGHT) -> None:
    """Check that the closed-form value lies in the bracket and the bracket is no wider than requested."""
    assert bracket.lo <= expected <= bracket.hi, (bracket, expected)
    assert bracket.width <= tol, bracket


def test_parallel_lines_overlapping_in_x() -> None:
    """Catch a kernel that measures end point to end point only: the closest pair is interior to the long line."""
    a = Line(0.0, 0.0, 10.0, 0.0, 0.2)
    b = Line(2.0, 0.5, 8.0, 0.5, 0.2)
    assert_brackets(centreline_bracket(a, b), 0.5)
    assert_brackets(clearance_bracket(a, b), 0.3)


def test_parallel_lines_offset_past_the_end() -> None:
    """Catch a kernel that uses the infinite-line distance: the lines are 1 apart but the segments hypot(2, 1)."""
    a = Line(0.0, 0.0, 10.0, 0.0, 0.0)
    b = Line(12.0, 1.0, 15.0, 1.0, 0.0)
    assert_brackets(centreline_bracket(a, b), math.hypot(2.0, 1.0))


def test_crossing_segments_have_zero_distance_and_negative_clearance() -> None:
    """Catch a kernel that only checks end points (it would report 1.0 for this X) or clamps clearance at zero."""
    a = Line(0.0, 0.0, 2.0, 2.0, 0.3)
    b = Line(0.0, 2.0, 2.0, 0.0, 0.1)
    assert_brackets(centreline_bracket(a, b), 0.0)
    assert_brackets(clearance_bracket(a, b), -0.2)


def test_externally_tangent_arcs_touch() -> None:
    """Circles r=1 at the origin and r=2 at (3, 0) touch at (1, 0); both arcs include that point."""
    a = Arc(0.0, 0.0, 1.0, -0.5, 1.0, 0.0)
    b = Arc(3.0, 0.0, 2.0, math.pi - 0.5, 1.0, 0.0)
    assert_brackets(centreline_bracket(a, b), 0.0)


@pytest.mark.parametrize("gap", [1e-6, 1e-3, 0.25])
def test_externally_tangent_arcs_with_gap(gap: float) -> None:
    """Moving the second circle out by g along the line of centres opens a gap of exactly g."""
    a = Arc(0.0, 0.0, 1.0, -0.5, 1.0, 0.0)
    b = Arc(3.0 + gap, 0.0, 2.0, math.pi - 0.5, 1.0, 0.0)
    assert_brackets(centreline_bracket(a, b), gap)


def test_concentric_arcs_with_overlapping_spans_are_radial_gap_apart() -> None:
    """The plateau case: every angle in the overlap is a minimiser, so the bound must converge without one."""
    a = Arc(0.0, 0.0, 10.0, 0.1, 0.6, 0.2)
    b = Arc(0.0, 0.0, 10.35, 0.0, 0.5, 0.2)
    assert_brackets(centreline_bracket(a, b, tol=1e-8), 0.35, tol=1e-8)


def test_concentric_arcs_with_opposite_sweeps() -> None:
    """A negative sweep covers the same points; the distance must not depend on direction."""
    a = Arc(0.0, 0.0, 10.0, 0.7, -0.6, 0.0)
    b = Arc(0.0, 0.0, 10.35, 0.0, 0.5, 0.0)
    assert_brackets(centreline_bracket(a, b, tol=1e-8), 0.35, tol=1e-8)


def test_concentric_arcs_with_disjoint_spans_meet_at_their_near_ends() -> None:
    """Spans [0, 0.5] at r=10 and [1.0, 1.5] at r=10.35: law of cosines between the ends at 0.5 and 1.0."""
    a = Arc(0.0, 0.0, 10.0, 0.0, 0.5, 0.0)
    b = Arc(0.0, 0.0, 10.35, 1.0, 0.5, 0.0)
    expected = math.sqrt(10.0**2 + 10.35**2 - 2.0 * 10.0 * 10.35 * math.cos(0.5))
    assert_brackets(centreline_bracket(a, b), expected)


def test_arc_and_line_above_its_apex() -> None:
    """Arc r=5 spanning 45 to 135 deg and the line y=7: the foot (0, 5) is on the arc, so the distance is 2."""
    arc = Arc(0.0, 0.0, 5.0, math.pi / 4, math.pi / 2, 0.0)
    assert_brackets(centreline_bracket(arc, Line(-3.0, 7.0, 3.0, 7.0, 0.0)), 2.0)


def test_arc_and_tangent_line_touch() -> None:
    """The line y=5 is tangent to the arc at its apex."""
    arc = Arc(0.0, 0.0, 5.0, math.pi / 4, math.pi / 2, 0.0)
    assert_brackets(centreline_bracket(Line(-3.0, 5.0, 3.0, 5.0, 0.0), arc), 0.0)


def test_line_crossing_an_arc() -> None:
    """The chord y=4 crosses the arc twice; a sampler that only looks at chord ends would report a positive distance."""
    arc = Arc(0.0, 0.0, 5.0, math.pi / 4, math.pi / 2, 0.0)
    assert_brackets(centreline_bracket(arc, Line(-10.0, 4.0, 10.0, 4.0, 0.0)), 0.0)


def test_arc_and_line_with_the_foot_outside_the_arc_span() -> None:
    """Arc r=5 spanning 0 to 0.3 rad and the vertical line x=-1: the closest arc point is the end at 0.3 rad."""
    arc = Arc(0.0, 0.0, 5.0, 0.0, 0.3, 0.0)
    line = Line(-1.0, -10.0, -1.0, 10.0, 0.0)
    assert_brackets(centreline_bracket(arc, line), 5.0 * math.cos(0.3) + 1.0)


def test_via_disc_against_a_track() -> None:
    """A via is a zero-length line whose width is the pad: centre 1.0 above a 0.2 mm track, pad 0.6 mm."""
    track = Line(-5.0, 0.0, 5.0, 0.0, 0.2)
    assert_brackets(clearance_bracket(disc(0.0, 1.0, 0.6), track), 1.0 - 0.3 - 0.1)


RULE = 0.15
W = 0.2
ONE_MICRON = 1e-3


def parallel_tracks(intrusion: float) -> tuple[Line, Line]:
    """Two tracks whose clearance is RULE - intrusion."""
    pitch = RULE + W - intrusion
    return Line(0.0, 0.0, 20.0, 0.0, W), Line(0.0, pitch, 20.0, pitch, W)


def concentric_turns(intrusion: float) -> tuple[Arc, Arc]:
    """Two concentric end turns whose clearance is RULE - intrusion (the plateau case at the rule)."""
    pitch = RULE + W - intrusion
    return Arc(0.0, 0.0, 20.0, 0.2, 0.8, W), Arc(0.0, 0.0, 20.0 + pitch, 0.1, 1.0, W)


def turn_and_side(intrusion: float) -> tuple[Arc, Line]:
    """Return an end turn of radius 20 and a straight side parallel to the tangent at its apex."""
    y = 20.0 + RULE + W - intrusion
    return Arc(0.0, 0.0, 20.0, 1.2, 0.8, W), Line(-3.0, y, 3.0, y, W)


Shape = Callable[[float], tuple[Prim, Prim]]
SHAPES: list[Shape] = [parallel_tracks, concentric_turns, turn_and_side]


@pytest.mark.parametrize("shape", SHAPES)
def test_clearance_exactly_at_the_rule_is_clean(shape: Shape) -> None:
    """Catch a false positive at the rule: a layout built to exactly the clearance setting passes D-006."""
    result, bracket = pair_verdict(*shape(0.0), RULE)
    assert result is Verdict.CLEAN, bracket


@pytest.mark.parametrize("shape", SHAPES)
def test_one_micron_intrusion_is_a_violation(shape: Shape) -> None:
    """Seeded defect: 1 um inward is caught. A checker with Xcoil's 0.004 mm slack band would pass it."""
    result, bracket = pair_verdict(*shape(ONE_MICRON), RULE)
    assert result is Verdict.VIOLATION, bracket


@pytest.mark.parametrize("shape", SHAPES)
def test_epsilon_edge_follows_d006(shape: Shape) -> None:
    """Rule - 0.9 nm passes, rule - 1.1 nm fails (epsilon 1e-6 mm): catches epsilon 0 and any larger slack."""
    inside, _ = pair_verdict(*shape(0.9 * DRC_EPSILON_MM), RULE)
    outside, _ = pair_verdict(*shape(1.1 * DRC_EPSILON_MM), RULE)
    assert (inside, outside) == (Verdict.CLEAN, Verdict.VIOLATION)


def exact_point_arc_distance(px: np.ndarray, py: np.ndarray, arc: Arc) -> np.ndarray:
    """Second, closed-form point-to-arc distance: clamp the point's polar angle into the arc's span."""
    lo, hi = sorted((arc.start, arc.start + arc.sweep))
    angle = np.arctan2(py - arc.cy, px - arc.cx)
    angle = lo + np.mod(angle - lo, 2.0 * math.pi)
    inside = angle <= hi
    radial = np.abs(np.hypot(px - arc.cx, py - arc.cy) - arc.r)
    ends = [(arc.cx + arc.r * math.cos(a), arc.cy + arc.r * math.sin(a)) for a in (lo, hi)]
    to_ends = np.minimum(*(np.hypot(px - ex, py - ey) for ex, ey in ends))
    return np.where(inside, radial, to_ends)


def test_bracket_contains_dense_point_sampling_on_random_arc_pairs() -> None:
    """Catch an unsound bound (sagitta dropped or of the wrong sign) on general arc pairs.

    Points every h of arc length on p, exact distance to q: the sampled minimum m satisfies D <= m <= D + h/2
    (distance to q is 1-Lipschitz along arc length), so [m - h/2, m] must overlap the instrument's bracket.
    """
    rng = np.random.default_rng(20261004)
    for _ in range(40):
        p = Arc(*rng.uniform(-5, 5, 2), rng.uniform(1, 10), rng.uniform(-math.pi, math.pi), rng.uniform(-6, 6), 0.0)
        q = Arc(*rng.uniform(-5, 5, 2), rng.uniform(1, 10), rng.uniform(-math.pi, math.pi), rng.uniform(-6, 6), 0.0)
        n = 200_000
        h = abs(p.sweep) * p.r / n
        angles = p.start + p.sweep * (np.arange(n + 1) / n)
        sampled = exact_point_arc_distance(p.cx + p.r * np.cos(angles), p.cy + p.r * np.sin(angles), q)
        m = float(sampled.min())
        bracket = centreline_bracket(p, q, tol=1e-9)
        assert bracket.width <= 1e-9, bracket
        assert bracket.lo <= m + 1e-12 and bracket.hi >= m - h / 2 - 1e-12, (p, q, bracket, m, h)


def test_brute_violations_finds_the_seeded_pair_and_respects_exemptions() -> None:
    """Three tracks at the rule, the middle one moved 1 um toward the top one; only that pair is reported."""
    pitch = RULE + W
    prims = [
        Line(0.0, 0.0, 20.0, 0.0, W),
        Line(0.0, pitch + ONE_MICRON, 20.0, pitch + ONE_MICRON, W),
        Line(0.0, 2 * pitch, 20.0, 2 * pitch, W),
    ]
    findings, _ = brute_violations(prims, RULE, no_exemptions)
    assert [(f.i, f.j, f.verdict) for f in findings] == [(1, 2, Verdict.VIOLATION)]
    exempted, _ = brute_violations(prims, RULE, lambda i, j: (i, j) == (1, 2))
    assert exempted == []


@pytest.mark.parametrize("shape", SHAPES)
def test_brute_violations_box_cull_keeps_every_seeded_intrusion(shape: Shape) -> None:
    """Catch an unsound cull: the end turn's apex lies 1.4 mm beyond its chord's box, next to the intruding side."""
    findings, _ = brute_violations(list(shape(ONE_MICRON)), RULE, no_exemptions)
    assert [(f.i, f.j, f.verdict) for f in findings] == [(0, 1, Verdict.VIOLATION)]
