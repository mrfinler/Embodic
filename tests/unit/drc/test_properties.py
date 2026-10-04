"""UT-DRC-08 (grid vs exhaustive), PR-01 (never under-reports, no false positives), PR-02 (symmetry shortcut)."""

import math
from dataclasses import replace

import numpy as np
import pytest

from embodic.drc import (
    DRC_EPSILON_MM,
    DrcCheckKind,
    DrcReport,
    min_distance_arc_arc,
    min_distance_line_arc,
    min_distance_line_line,
    run_drc,
)
from embodic.geometry.layout import Layout, RotationalSymmetry
from embodic.geometry.paths import CopperPath
from embodic.geometry.primitives import Arc, Line, Primitive
from embodic.geometry.transforms import rotate

from .layouts import LAYERS, RULES, arc, layout, line, path, via

pytestmark = pytest.mark.req("REQ-F-10")

THRESHOLD_MM = RULES.trace_clearance_mm - DRC_EPSILON_MM


def _random_prim(rng: np.random.Generator) -> Primitive:
    w = float(rng.uniform(0.1, 0.4))
    if rng.random() < 0.5:
        x, y = rng.uniform(0, 8, 2)
        heading, length = rng.uniform(0, 2 * math.pi), rng.uniform(0.05, 2.5)
        return line(x, y, x + length * math.cos(heading), y + length * math.sin(heading), w=w)
    cx, cy = rng.uniform(0, 8, 2)
    return arc(cx, cy, float(rng.uniform(0.2, 3)), float(rng.uniform(-4, 4)), float(rng.uniform(-3, 3)), w=w)


def _random_paths(rng: np.random.Generator, count: int) -> list[CopperPath]:
    return [path(i, [_random_prim(rng)], layer=LAYERS[int(rng.integers(2))], net=f"N{i}") for i in range(count)]


def _row(p: Primitive) -> np.ndarray:
    if isinstance(p, Line):
        return np.array([[p.x1_mm, p.y1_mm, p.x2_mm, p.y2_mm, p.width_mm]])
    return np.array([[p.cx_mm, p.cy_mm, p.r_mm, p.start_rad, p.sweep_rad, p.width_mm]])


def _exact_mm(p: Primitive, q: Primitive) -> float:
    if isinstance(p, Arc) and isinstance(q, Line):
        p, q = q, p
    kernel = {
        (False, False): min_distance_line_line,
        (False, True): min_distance_line_arc,
        (True, True): min_distance_arc_arc,
    }[isinstance(p, Arc), isinstance(q, Arc)]
    return float(kernel(_row(p), _row(q))[0])


def _trace_violations(report: DrcReport) -> dict[frozenset[str], float]:
    return {frozenset(v.objects): v.measured_mm for v in report.violations if v.kind is DrcCheckKind.TRACE_TRACE}


def _exhaustive(paths: list[CopperPath]) -> dict[frozenset[str], float]:
    """Every same-layer primitive pair of different single-primitive paths through the public kernels."""
    found = {}
    for i, a in enumerate(paths):
        for b in paths[i + 1 :]:
            if a.layer != b.layer:
                continue
            p, q = a.primitives[0], b.primitives[0]
            clearance_mm = _exact_mm(p, q) - (p.width_mm + q.width_mm) / 2
            if clearance_mm < THRESHOLD_MM:
                found[frozenset({f"path:{a.id}/prim:0", f"path:{b.id}/prim:0"})] = clearance_mm
    return found


def test_ut_drc_08_grid_broad_phase_equals_exhaustive_pairs_on_50_random_layouts() -> None:
    """Catches a broad phase that drops a close pair (cell too small, missed neighbour offset, arc reach too short)."""
    rng = np.random.default_rng(808)
    for _ in range(50):
        paths = _random_paths(rng, 30)
        report = run_drc(layout(paths=paths), RULES)
        assert report is not None
        got, want = _trace_violations(report), _exhaustive(paths)
        assert got.keys() == want.keys()
        assert all(abs(got[k] - want[k]) <= 1e-12 for k in want)


def _samples(p: Primitive) -> tuple[np.ndarray, float]:
    """Points along the centreline and the largest distance from any centreline point to its nearest sample."""
    if isinstance(p, Line):
        length_mm = math.hypot(p.x2_mm - p.x1_mm, p.y2_mm - p.y1_mm)
        count = max(16, math.ceil(length_mm / 0.004))
        t = np.linspace(0, 1, count)
        pts = np.stack([p.x1_mm + t * (p.x2_mm - p.x1_mm), p.y1_mm + t * (p.y2_mm - p.y1_mm)], axis=1)
    else:
        length_mm = abs(p.sweep_rad) * p.r_mm
        count = max(16, math.ceil(length_mm / 0.004))
        angle = p.start_rad + np.linspace(0, 1, count) * p.sweep_rad
        pts = np.stack([p.cx_mm + p.r_mm * np.cos(angle), p.cy_mm + p.r_mm * np.sin(angle)], axis=1)
    return pts, length_mm / (count - 1) / 2


def _dense_bracket(p: Primitive, q: Primitive, cache: dict[int, tuple[np.ndarray, float]]) -> tuple[float, float]:
    """Clearance bracket (lo, hi) from point sampling: hi is a sampled clearance, lo subtracts the sampling bound."""
    (pa, ha), (pb, hb) = cache[id(p)], cache[id(q)]
    box_gap = np.maximum(0, np.maximum(pa.min(0) - pb.max(0), pb.min(0) - pa.max(0)))
    half_mm = (p.width_mm + q.width_mm) / 2
    if math.hypot(*box_gap) - ha - hb - half_mm > RULES.trace_clearance_mm:
        return math.inf, math.inf
    sampled = min(float(np.sqrt(((c[:, None, :] - pb[None, :, :]) ** 2).sum(-1)).min()) for c in np.array_split(pa, 4))
    return sampled - ha - hb - half_mm, sampled - half_mm


def test_pr_01_drc_never_under_reports_and_reports_no_false_positive_on_200_random_sets() -> None:
    """Catches an under-report (a pair the dense check proves below the rule is missing) and a false positive.

    The reference is independent of embodic's kernels: it samples both centrelines every 4 um or finer, so the true
    clearance lies in [lo, hi]. A pair with hi below rule - epsilon must be reported; a pair with lo at or above it
    must not. Pairs inside the bracket are undecided and skipped.
    """
    rng = np.random.default_rng(101)
    decided = 0
    for _ in range(200):
        paths = _random_paths(rng, 12)
        report = run_drc(layout(paths=paths), RULES)
        assert report is not None
        reported = _trace_violations(report)
        cache = {id(p.primitives[0]): _samples(p.primitives[0]) for p in paths}
        for i, a in enumerate(paths):
            for b in paths[i + 1 :]:
                if a.layer != b.layer:
                    continue
                lo, hi = _dense_bracket(a.primitives[0], b.primitives[0], cache)
                key = frozenset({f"path:{a.id}/prim:0", f"path:{b.id}/prim:0"})
                if hi < THRESHOLD_MM:
                    assert key in reported, (key, lo, hi)
                    decided += 1
                elif lo >= THRESHOLD_MM:
                    assert key not in reported, (key, lo, hi, reported.get(key))
    assert decided > 100


SECTOR_RAD = 2 * math.pi / 12


def _sector() -> list[tuple[Primitive, str]]:
    deg = math.pi / 180
    radial = line(12 * math.cos(14 * deg), 12 * math.sin(14 * deg), 15 * math.cos(14 * deg), 15 * math.sin(14 * deg))
    normal = (-math.sin(14 * deg), math.cos(14 * deg))
    offset = replace(
        radial,
        x1_mm=radial.x1_mm + 0.4 * normal[0],
        y1_mm=radial.y1_mm + 0.4 * normal[1],
        x2_mm=radial.x2_mm + 0.4 * normal[0],
        y2_mm=radial.y2_mm + 0.4 * normal[1],
        width_mm=0.25,
    )
    return [
        (arc(0, 0, 10, 0, 25 * deg, w=0.3), "F.Cu"),
        (arc(0, 0, 10.45, 2 * deg, 29 * deg, w=0.3), "F.Cu"),
        (arc(0, 0, 11.0, 1 * deg, 27 * deg, w=0.3), "F.Cu"),
        (replace(radial, width_mm=0.25), "B.Cu"),
        (offset, "B.Cu"),
    ]


def _symmetric_layout(order: int = 12, nudge_mm: float = 0.0) -> Layout:
    paths, canonical = [], []
    for k in range(order):
        for prim, layer in _sector():
            (rotated,) = rotate([prim], k * SECTOR_RAD)
            if nudge_mm and k == 5 and isinstance(rotated, Arc):
                rotated = replace(rotated, r_mm=rotated.r_mm + nudge_mm)
            if k == 0:
                canonical.append(len(paths))
            paths.append(path(len(paths), [rotated], layer=layer, net=f"N{len(paths)}"))
    periodic = tuple(p.id for p in paths)
    ring = path(len(paths), [arc(0, 0, 9.5, 0, 2 * math.pi, w=0.3)], net="RING")
    return layout(
        paths=[*paths, ring],
        vias=[via(0, 10.2, 0.3, net="X")],
        symmetry=RotationalSymmetry(order=order, periodic_path_ids=periodic, canonical_path_ids=tuple(canonical)),
    )


def _comparable(report: DrcReport) -> tuple[set[tuple[DrcCheckKind, str | None, frozenset[str]]], dict]:
    violations = {(v.kind, v.layer, frozenset(v.objects)) for v in report.violations}
    return violations, {s.kind: s.measured_min_mm for s in report.summaries}


@pytest.mark.req("REQ-F-10", "REQ-N-01")
def test_pr_02_symmetric_shortcut_equals_the_full_check_on_a_12_fold_layout() -> None:
    """Catches a shortcut that loses cross-sector pairs or rotated copies: same violations, minima within 1e-9 mm."""
    sym = run_drc(_symmetric_layout(), RULES, use_symmetry=True)
    full = run_drc(_symmetric_layout(), RULES, use_symmetry=False)
    assert sym is not None and full is not None
    assert (sym.method, full.method) == ("symmetric+grid+exact", "grid+exact")
    (sym_v, sym_min), (full_v, full_min) = _comparable(sym), _comparable(full)
    assert sym_v == full_v
    assert sym.violation_count == full.violation_count > 3 * 12
    assert sym_min.keys() == full_min.keys()
    assert all(abs(sym_min[k] - full_min[k]) <= 1e-9 for k in full_min if full_min[k] is not None)
    sym_pairs = {s.kind: s.pairs_checked for s in sym.summaries}
    full_pairs = {s.kind: s.pairs_checked for s in full.summaries}
    assert sym_pairs[DrcCheckKind.TRACE_TRACE] < full_pairs[DrcCheckKind.TRACE_TRACE]


@pytest.mark.req("REQ-F-10", "REQ-N-01")
def test_pr_02_a_layout_that_breaks_its_symmetry_claim_gets_the_full_check() -> None:
    """Catches a shortcut that trusts Layout.symmetry: one copy moved 1 um disables it, and the result stays full."""
    broken = _symmetric_layout(nudge_mm=0.001)
    sym = run_drc(broken, RULES, use_symmetry=True)
    full = run_drc(broken, RULES, use_symmetry=False)
    assert sym is not None and full is not None
    assert sym.method == "grid+exact"
    assert _comparable(sym) == _comparable(full)
