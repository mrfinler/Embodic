"""Independent brute-force clearance instrument for M1 (IT-12, PR-01), built from the contract, not from embodic.

Method (proof in README.md, "Why the bracket is certified"):

- Line to line is exact: two 2-D segments that do not properly cross are closest at an end point of one of them, so
  the distance is 0 for a proper crossing, else the least of four point-to-segment distances.
- An arc is sampled into chords. A piece of sweep ``theta <= pi`` and radius ``r`` lies within its sagitta
  ``2 r sin^2(theta / 4)`` of its chord, and every chord point lies within that sagitta of the arc. Hence the true
  centreline distance lies in ``[d_chord - sag_p - sag_q, d_chord + sag_p + sag_q]``.
- Branch and bound halves the arc piece with the larger sagitta in every pair that could still hold the minimum, until
  the bracket is narrower than ``tol`` or, with a threshold, until the threshold is decided.

Clearance is copper edge to copper edge: centreline distance minus half of each width. It is signed; overlapping copper
gives a negative clearance. Rule D-006 (interfaces.md section 7): violation when clearance < rule - 1e-6 mm.
"""

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum

import numpy as np
from numpy.typing import NDArray
from records import Line, Prim

DRC_EPSILON_MM = 1e-6
# Rounding allowance added to both bracket ends. Assumption: |coordinates| <= 1000 mm keeps double rounding in the
# distance kernels below 1e-12 mm (about 50 ulp of 1000).
FP_MARGIN_MM = 1e-12
DEFAULT_TOL_MM = 1e-10
MAX_ACTIVE_PAIRS = 4_000_000
_INITIAL_PIECE_RAD = math.pi / 2

Floats = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class Bracket:
    """Certified interval: the true value v satisfies lo <= v <= hi."""

    lo: float
    hi: float

    @property
    def width(self) -> float:
        """Return hi - lo."""
        return self.hi - self.lo

    def shifted(self, delta: float) -> "Bracket":
        """Return the bracket moved by delta."""
        return Bracket(self.lo + delta, self.hi + delta)


class Verdict(StrEnum):
    """Outcome of comparing a clearance bracket with the D-006 threshold."""

    VIOLATION = "violation"
    CLEAN = "clean"
    UNDECIDED = "undecided"


def verdict(clearance: Bracket, rule_mm: float, epsilon_mm: float = DRC_EPSILON_MM) -> Verdict:
    """Classify a clearance bracket against rule D-006: violation when clearance < rule - epsilon."""
    threshold = rule_mm - epsilon_mm
    if clearance.hi < threshold:
        return Verdict.VIOLATION
    if clearance.lo >= threshold:
        return Verdict.CLEAN
    return Verdict.UNDECIDED


def point_segment_distance(px: Floats, py: Floats, seg: Floats) -> Floats:
    """Distance from points (px, py) to segments ``seg`` (N, 4) as x1, y1, x2, y2; zero-length segments allowed."""
    x1, y1, x2, y2 = seg.T
    dx, dy = x2 - x1, y2 - y1
    length2 = dx * dx + dy * dy
    safe = np.where(length2 > 0.0, length2, 1.0)
    t = np.where(length2 > 0.0, ((px - x1) * dx + (py - y1) * dy) / safe, 0.0)
    t = np.clip(t, 0.0, 1.0)
    return np.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def segment_distance(a: Floats, b: Floats) -> Floats:
    """Exact distance between segment rows of ``a`` and ``b`` (each (N, 4)): 0 on a proper crossing, else end points."""

    def orient(ox: Floats, oy: Floats, px: Floats, py: Floats, qx: Floats, qy: Floats) -> Floats:
        return (px - ox) * (qy - oy) - (py - oy) * (qx - ox)

    ax1, ay1, ax2, ay2 = a.T
    bx1, by1, bx2, by2 = b.T
    ends = np.minimum.reduce(
        [
            point_segment_distance(ax1, ay1, b),
            point_segment_distance(ax2, ay2, b),
            point_segment_distance(bx1, by1, a),
            point_segment_distance(bx2, by2, a),
        ]
    )
    o1 = orient(ax1, ay1, ax2, ay2, bx1, by1)
    o2 = orient(ax1, ay1, ax2, ay2, bx2, by2)
    o3 = orient(bx1, by1, bx2, by2, ax1, ay1)
    o4 = orient(bx1, by1, bx2, by2, ax2, ay2)
    crossing = (o1 * o2 < 0.0) & (o3 * o4 < 0.0)
    return np.where(crossing, 0.0, ends)


def _chords(p: Prim, start: Floats, sweep: Floats) -> tuple[Floats, Floats]:
    """Return chord rows (N, 4) and sagittas (N,) of the pieces [start, start + sweep] of p (ignored for a line)."""
    n = start.shape[0]
    if isinstance(p, Line):
        return np.tile([p.x1, p.y1, p.x2, p.y2], (n, 1)), np.zeros(n)
    end = start + sweep
    rows = np.column_stack(
        [
            p.cx + p.r * np.cos(start),
            p.cy + p.r * np.sin(start),
            p.cx + p.r * np.cos(end),
            p.cy + p.r * np.sin(end),
        ]
    )
    return rows, 2.0 * p.r * np.sin(sweep / 4.0) ** 2


def _initial_pieces(p: Prim) -> tuple[Floats, Floats]:
    """Split an arc into pieces of at most pi/2 so every piece satisfies the sweep <= pi premise of the bound."""
    if isinstance(p, Line):
        return np.zeros(1), np.zeros(1)
    n = max(1, math.ceil(abs(p.sweep) / _INITIAL_PIECE_RAD))
    sweep = p.sweep / n
    return p.start + sweep * np.arange(n), np.full(n, sweep)


def centreline_bracket(p: Prim, q: Prim, *, tol: float = DEFAULT_TOL_MM, threshold: float | None = None) -> Bracket:
    """Return a certified bracket of the centreline distance between p and q.

    Stops when the bracket is at most ``tol`` wide, or, when ``threshold`` is given, as soon as the bracket lies wholly
    below it or wholly at or above it. A bracket wider than ``tol`` that straddles the threshold means the pair budget
    ran out; it is still certified.
    """
    if tol < 4.0 * FP_MARGIN_MM:
        raise ValueError("tol must be at least 4 * FP_MARGIN_MM")
    p_start, p_sweep = _initial_pieces(p)
    q_start, q_sweep = _initial_pieces(q)
    pi, qi = np.meshgrid(np.arange(p_start.size), np.arange(q_start.size), indexing="ij")
    ps, pw = p_start[pi.ravel()], p_sweep[pi.ravel()]
    qs, qw = q_start[qi.ravel()], q_sweep[qi.ravel()]
    cut_threshold = math.inf if threshold is None else threshold
    best_hi, settled_lo = math.inf, math.inf
    while True:
        p_rows, p_sag = _chords(p, ps, pw)
        q_rows, q_sag = _chords(q, qs, qw)
        d = segment_distance(p_rows, q_rows)
        lo = d - p_sag - q_sag - FP_MARGIN_MM
        hi = d + p_sag + q_sag + FP_MARGIN_MM
        best_hi = min(best_hi, float(hi.min()))
        cut = min(cut_threshold, best_hi - tol)
        active = lo < cut
        alive = lo <= best_hi
        settled = alive & ~active
        if settled.any():
            settled_lo = min(settled_lo, float(lo[settled].min()))
        bracket_lo = min(settled_lo, float(lo[active].min()) if active.any() else math.inf)
        done = not active.any() or (threshold is not None and best_hi < threshold)
        if done or active.sum() * 2 > MAX_ACTIVE_PAIRS:
            return Bracket(max(0.0, min(bracket_lo, best_hi)), best_hi)
        ps, pw, qs, qw = _split(ps[active], pw[active], qs[active], qw[active], p_sag[active], q_sag[active])


def _split(
    ps: Floats, pw: Floats, qs: Floats, qw: Floats, p_sag: Floats, q_sag: Floats
) -> tuple[Floats, Floats, Floats, Floats]:
    """Halve, in every pair, the piece with the larger sagitta; a line-line pair (both zero) never stays active."""
    split_p = p_sag >= q_sag
    half_p = np.where(split_p, pw / 2.0, pw)
    half_q = np.where(split_p, qw, qw / 2.0)
    second_ps = np.where(split_p, ps + half_p, ps)
    second_qs = np.where(split_p, qs, qs + half_q)
    return (
        np.concatenate([ps, second_ps]),
        np.concatenate([half_p, half_p]),
        np.concatenate([qs, second_qs]),
        np.concatenate([half_q, half_q]),
    )


def clearance_bracket(p: Prim, q: Prim, *, tol: float = DEFAULT_TOL_MM, threshold: float | None = None) -> Bracket:
    """Return a certified bracket of the copper clearance (edge to edge) between p and q."""
    half_widths = (p.width + q.width) / 2.0
    centre_threshold = None if threshold is None else threshold + half_widths
    return centreline_bracket(p, q, tol=tol, threshold=centre_threshold).shifted(-half_widths)


def pair_verdict(
    p: Prim, q: Prim, rule_mm: float, epsilon_mm: float = DRC_EPSILON_MM, *, tol: float = DEFAULT_TOL_MM
) -> tuple[Verdict, Bracket]:
    """Decide rule D-006 for one pair and return the bracket the decision rests on."""
    bracket = clearance_bracket(p, q, tol=tol, threshold=rule_mm - epsilon_mm)
    return verdict(bracket, rule_mm, epsilon_mm), bracket


@dataclass(frozen=True, slots=True)
class PairFinding:
    """A pair of primitives on one layer that violates rule D-006 or cannot be decided within ``tol``."""

    i: int
    j: int
    verdict: Verdict
    clearance: Bracket


def bounding_boxes(prims: Sequence[Prim]) -> Floats:
    """Return (N, 4) boxes xmin, ymin, xmax, ymax that contain each centreline (arc pieces: chord box plus sagitta)."""
    boxes = np.empty((len(prims), 4))
    for k, p in enumerate(prims):
        start, sweep = _initial_pieces(p)
        rows, sag = _chords(p, start, sweep)
        xs, ys = rows[:, [0, 2]], rows[:, [1, 3]]
        boxes[k] = (
            float((xs.min(axis=1) - sag).min()),
            float((ys.min(axis=1) - sag).min()),
            float((xs.max(axis=1) + sag).max()),
            float((ys.max(axis=1) + sag).max()),
        )
    return boxes


def brute_violations(
    prims: Sequence[Prim],
    rule_mm: float,
    exempt: Callable[[int, int], bool],
    epsilon_mm: float = DRC_EPSILON_MM,
    *,
    tol: float = DEFAULT_TOL_MM,
) -> tuple[list[PairFinding], int]:
    """Check every non-exempt pair of one layer; return non-clean findings and the count of pairs run exactly.

    A pair is skipped without the exact kernel only when the distance between its boxes, a lower bound of the
    centreline distance, already reaches the centreline threshold rule - epsilon + (w_i + w_j) / 2.
    """
    boxes = bounding_boxes(prims)
    widths = np.array([p.width for p in prims])
    findings: list[PairFinding] = []
    checked = 0
    for i in range(len(prims) - 1):
        rest = boxes[i + 1 :]
        gap_x = np.maximum(0.0, np.maximum(rest[:, 0] - boxes[i, 2], boxes[i, 0] - rest[:, 2]))
        gap_y = np.maximum(0.0, np.maximum(rest[:, 1] - boxes[i, 3], boxes[i, 1] - rest[:, 3]))
        need = rule_mm - epsilon_mm + (widths[i] + widths[i + 1 :]) / 2.0
        for j in np.flatnonzero(np.hypot(gap_x, gap_y) < need) + i + 1:
            if exempt(i, int(j)):
                continue
            checked += 1
            result, bracket = pair_verdict(prims[i], prims[int(j)], rule_mm, epsilon_mm, tol=tol)
            if result is not Verdict.CLEAN:
                findings.append(PairFinding(i, int(j), result, bracket))
    return findings, checked


def no_exemptions(i: int, j: int) -> bool:
    """Exempt nothing; the default when a test builds its own primitive list."""
    return False
