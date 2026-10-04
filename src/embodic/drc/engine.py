"""``run_drc``: grid broad phase, exact narrow phase, rule D-006 verdicts and the optional symmetry shortcut."""

import math
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from types import MappingProxyType

import numpy as np

from embodic.drc.items import EVERY_LAYER, IntArray, ItemClass, Items, build_items, exempt_pairs
from embodic.drc.kernels import PX, PY, QX, QY, D, closest_pairs, pad_closest
from embodic.drc.report import (
    DRC_EPSILON_MM,
    MAX_REPORTED_VIOLATIONS,
    REQUIRED_MM,
    CancelToken,
    DrcCheckKind,
    DrcCheckSummary,
    DrcReport,
    DrcViolation,
    violates,
)
from embodic.drc.symmetry import RotationMaps, rotation_maps
from embodic.geometry.layout import Layout
from embodic.model.drc_rules import DrcRules
from embodic.units import FloatArray

PIECE_MM = 0.5
_ARC_PIECE_RAD = math.pi / 4
_CHUNK_PAIRS = 1 << 16
_NO_KIND = -1

PAIR_KINDS = (
    DrcCheckKind.TRACE_TRACE,
    DrcCheckKind.TRACE_VIA,
    DrcCheckKind.VIA_VIA,
    DrcCheckKind.PAD_TRACE,
    DrcCheckKind.PAD_PAD,
    DrcCheckKind.COPPER_EDGE,
    DrcCheckKind.COPPER_HOLE,
)
_KIND_OF_CLASSES: Mapping[frozenset[ItemClass], DrcCheckKind] = MappingProxyType(
    {
        frozenset({ItemClass.TRACE}): DrcCheckKind.TRACE_TRACE,
        frozenset({ItemClass.TRACE, ItemClass.VIA}): DrcCheckKind.TRACE_VIA,
        frozenset({ItemClass.VIA}): DrcCheckKind.VIA_VIA,
        frozenset({ItemClass.TRACE, ItemClass.PAD}): DrcCheckKind.PAD_TRACE,
        frozenset({ItemClass.PAD}): DrcCheckKind.PAD_PAD,
        frozenset({ItemClass.VIA, ItemClass.PAD}): DrcCheckKind.PAD_PAD,
        **{frozenset({c, ItemClass.EDGE}): DrcCheckKind.COPPER_EDGE for c in (ItemClass.TRACE, ItemClass.VIA)},
        frozenset({ItemClass.PAD, ItemClass.EDGE}): DrcCheckKind.COPPER_EDGE,
        **{frozenset({c, ItemClass.HOLE}): DrcCheckKind.COPPER_HOLE for c in (ItemClass.TRACE, ItemClass.VIA)},
        frozenset({ItemClass.PAD, ItemClass.HOLE}): DrcCheckKind.COPPER_HOLE,
    }
)
_KIND_TABLE = np.full((len(ItemClass), len(ItemClass)), _NO_KIND, dtype=np.int64)
for _classes, _kind in _KIND_OF_CLASSES.items():
    _first, *_rest = sorted(_classes)
    _second = _rest[0] if _rest else _first
    _KIND_TABLE[_first, _second] = _KIND_TABLE[_second, _first] = PAIR_KINDS.index(_kind)


@dataclass(frozen=True, slots=True)
class _Measured:
    """Non-exempt pairs of one layer group with their kind (index into PAIR_KINDS), clearance and location."""

    a: IntArray
    b: IntArray
    kind: IntArray
    clearance_mm: FloatArray
    at_mm: FloatArray  # (n, 2)
    layer: str | None


def _pieces(items: Items, sel: IntArray) -> tuple[FloatArray, FloatArray, IntArray]:
    """Split every selected item into pieces of at most PIECE_MM; return piece midpoints, reach radii and owners.

    Every point of a piece lies within its reach radius of the piece midpoint (half chord plus sagitta for arcs).
    """
    rows, arc = items.rows[sel], items.is_arc[sel]
    r_mm, sweep_rad = rows[:, 2], np.abs(rows[:, 4])
    dx_mm, dy_mm = rows[:, 2] - rows[:, 0], rows[:, 3] - rows[:, 1]
    length_mm = np.where(arc, r_mm * sweep_rad, np.sqrt(dx_mm * dx_mm + dy_mm * dy_mm))
    count = np.ceil(np.maximum(length_mm / PIECE_MM, np.where(arc, sweep_rad / _ARC_PIECE_RAD, 0.0)))
    count = np.maximum(count, 1).astype(np.int64)
    owner = np.repeat(sel, count)
    k = np.arange(len(owner)) - np.repeat(np.cumsum(count) - count, count)
    n, frac = np.repeat(count, count), (k + 0.5) / np.repeat(count, count)
    rep = np.repeat(rows, count, axis=0)
    rep_arc = np.repeat(arc, count)
    half_rad = np.abs(rep[:, 4]) / (2 * n)
    theta_rad = rep[:, 3] + frac * rep[:, 4]
    to_chord = rep[:, 2] * np.cos(half_rad)
    arc_mid = np.stack([rep[:, 0] + to_chord * np.cos(theta_rad), rep[:, 1] + to_chord * np.sin(theta_rad)], axis=1)
    line_mid = np.stack(
        [rep[:, 0] + frac * (rep[:, 2] - rep[:, 0]), rep[:, 1] + frac * (rep[:, 3] - rep[:, 1])], axis=1
    )
    mid = np.where(rep_arc[:, None], arc_mid, line_mid)
    reach_mm = np.where(
        rep_arc,
        rep[:, 2] * np.sin(half_rad) + rep[:, 2] * (1 - np.cos(half_rad)),
        np.repeat(length_mm, count) / (2 * n),
    )
    return mid, reach_mm, owner


def candidate_pairs(items: Items, sel: IntArray, rule_mm: float) -> tuple[IntArray, IntArray]:
    """Item pairs (a < b) that may lie closer than ``rule_mm`` plus their half widths: a uniform grid on midpoints.

    The cell is at least the largest pair reach, so two pieces that can be that close sit in the same or adjacent
    cells; the five half-plane neighbour offsets visit each adjacent cell pair once.
    """
    empty = np.empty(0, dtype=np.int64)
    if len(sel) < 2:
        return empty, empty
    mid, reach_mm, owner = _pieces(items, sel)
    span_mm = reach_mm + items.half_width_mm[owner]
    cell_mm = 2 * float(span_mm.max()) + rule_mm + 1e-9
    ij = np.floor(mid / cell_mm).astype(np.int64)
    ij -= ij.min(axis=0)
    width = int(ij[:, 1].max()) + 3
    key = ij[:, 0] * width + ij[:, 1] + 1
    order = np.argsort(key, kind="stable")
    sorted_key = key[order]
    m = len(order)
    found_a, found_b = [], []
    for dx, dy in ((0, 0), (0, 1), (1, -1), (1, 0), (1, 1)):
        target = sorted_key + dx * width + dy
        lo = np.searchsorted(sorted_key, target, side="left")
        hi = np.searchsorted(sorted_key, target, side="right")
        if (dx, dy) == (0, 0):
            lo = np.maximum(lo, np.arange(m) + 1)
        count = np.maximum(hi - lo, 0)
        first = np.repeat(np.arange(m), count)
        second = np.repeat(lo, count) + np.arange(int(count.sum())) - np.repeat(np.cumsum(count) - count, count)
        pa, pb = order[first], order[second]
        gap = mid[pa] - mid[pb]
        near = np.sqrt((gap * gap).sum(axis=1)) <= span_mm[pa] + span_mm[pb] + rule_mm + 1e-9
        keep = near & (owner[pa] != owner[pb])
        found_a.append(owner[pa][keep])
        found_b.append(owner[pb][keep])
    a, b = np.concatenate(found_a), np.concatenate(found_b)
    n = len(items)
    keys = np.unique(np.minimum(a, b) * n + np.maximum(a, b))
    return keys // n, keys % n


def _measure(items: Items, layout: Layout, a: IntArray, b: IntArray, kind: IntArray) -> tuple[FloatArray, FloatArray]:
    """Clearance (centreline distance minus half widths) and location of each pair; kinds decide the kernel.

    Pad-to-pad and pad-to-via use the circumscribed land radii (Xcoil padsClearance), any other pair with a pad uses
    ``pad_closest``, and the rest use the exact line and arc kernels.
    """
    clearance_mm = np.empty(len(a))
    at_mm = np.empty((len(a), 2))
    cls_a, cls_b = items.item_class[a], items.item_class[b]
    lands = kind == PAIR_KINDS.index(DrcCheckKind.PAD_PAD)
    if lands.any():
        ca, cb = items.centre_mm[a[lands]], items.centre_mm[b[lands]]
        ra, rb = items.land_radius_mm[a[lands]], items.land_radius_mm[b[lands]]
        gap = cb - ca
        dist_mm = np.sqrt((gap * gap).sum(axis=1))
        u = gap / np.where(dist_mm > 0, dist_mm, 1.0)[:, None]
        clearance_mm[lands] = dist_mm - ra - rb
        at_mm[lands] = (ca + ra[:, None] * u + cb - rb[:, None] * u) / 2
    padded = ~lands & ((cls_a == ItemClass.PAD) | (cls_b == ItemClass.PAD))
    for p in np.unique(np.where(cls_a == ItemClass.PAD, items.pad[a], items.pad[b])[padded]):
        on_pad = padded & ((items.pad[a] == p) | (items.pad[b] == p))
        other = np.where(items.pad[a] == p, b, a)[on_pad]
        for arc in (False, True):
            sel = items.is_arc[other] == arc
            if not sel.any():
                continue
            pair = pad_closest(layout.pads[p], items.rows[other[sel]], arc)
            idx = np.flatnonzero(on_pad)[sel]
            clearance_mm[idx] = pair[D] - items.half_width_mm[other[sel]]
            at_mm[idx] = np.stack([(pair[PX] + pair[QX]) / 2, (pair[PY] + pair[QY]) / 2], axis=1)
    rest = ~lands & ~padded
    for arc_a in (False, True):
        for arc_b in (False, True):
            sel = rest & (items.is_arc[a] == arc_a) & (items.is_arc[b] == arc_b)
            if not sel.any():
                continue
            pair = closest_pairs(items.rows[a[sel]], arc_a, items.rows[b[sel]], arc_b)
            clearance_mm[sel] = pair[D] - items.half_width_mm[a[sel]] - items.half_width_mm[b[sel]]
            at_mm[sel] = np.stack([(pair[PX] + pair[QX]) / 2, (pair[PY] + pair[QY]) / 2], axis=1)
    return clearance_mm, at_mm


def _check(items: Items, layout: Layout, a: IntArray, b: IntArray, exempt: IntArray, layer: str | None) -> _Measured:
    """Drop pairs no check applies to and exempt pairs, then measure the rest."""
    kind = _KIND_TABLE[items.item_class[a], items.item_class[b]]
    same_path = (items.path[a] == items.path[b]) & (items.path[a] >= 0)
    adjacent = same_path & (np.abs(items.main[a] - items.main[b]) <= 1)
    keep = (kind != _NO_KIND) & ~adjacent & ~np.isin(a * len(items) + b, exempt)
    a, b, kind = a[keep], b[keep], kind[keep]
    clearance_mm, at_mm = _measure(items, layout, a, b, kind)
    return _Measured(a, b, kind, clearance_mm, at_mm, layer)


def _layer_groups(items: Items, layout: Layout) -> Iterator[tuple[str | None, IntArray, bool]]:
    """Each copper layer with the every-layer items (pairs of two every-layer items dropped), then those alone."""
    every = items.layer == EVERY_LAYER
    for index, name in enumerate(layout.copper_layers):
        yield name, np.flatnonzero(every | (items.layer == index)), True
    yield None, np.flatnonzero(every), False


def _required(rules: DrcRules) -> FloatArray:
    return np.array([REQUIRED_MM[k](rules) for k in PAIR_KINDS])


def run_drc(
    layout: Layout, rules: DrcRules, *, use_symmetry: bool = True, cancel: CancelToken | None = None
) -> DrcReport | None:
    """Check every applicable DrcCheckKind on ``layout`` under rule D-006. None only when cancelled.

    With ``use_symmetry`` and a ``layout.symmetry`` whose claim ``rotation_maps`` proves, pairs of two periodic
    primitives are checked only when one of them is canonical, and each violation found there is re-measured on
    every rotated copy; otherwise every pair is checked (method ``grid+exact``).
    """
    stopped: Callable[[], bool] = (lambda: False) if cancel is None else (lambda: cancel.cancelled)
    items, first_item = build_items(layout)
    exempt = exempt_pairs(layout, items, first_item)
    maps = rotation_maps(layout, items, first_item, exempt) if use_symmetry else None
    required_mm = _required(rules)
    rule_mm = float(required_mm.max()) + DRC_EPSILON_MM
    measured: list[_Measured] = []
    for layer, sel, drop_every in _layer_groups(items, layout):
        if stopped():
            return None
        a, b = candidate_pairs(items, sel, rule_mm)
        if drop_every:
            mixed = (items.layer[a] != EVERY_LAYER) | (items.layer[b] != EVERY_LAYER)
            a, b = a[mixed], b[mixed]
        if maps is not None:
            redundant = maps.periodic[a] & maps.periodic[b] & ~maps.canonical[a] & ~maps.canonical[b]
            a, b = a[~redundant], b[~redundant]
        for start in range(0, len(a), _CHUNK_PAIRS):
            if stopped():
                return None
            chunk = slice(start, start + _CHUNK_PAIRS)
            measured.append(_check(items, layout, a[chunk], b[chunk], exempt, layer))
    if maps is not None:
        measured += _rotated_copies(items, layout, measured, maps, required_mm, exempt)
    if stopped():
        return None
    return _report(items, layout, rules, measured, required_mm, maps)


def _rotated_copies(
    items: Items,
    layout: Layout,
    measured: list[_Measured],
    maps: RotationMaps,
    required_mm: FloatArray,
    exempt: IntArray,
) -> list[_Measured]:
    """Re-measure every rotated copy of each violating periodic pair, so violations match the full check."""
    a = np.concatenate([m.a[m.clearance_mm < required_mm[m.kind] - DRC_EPSILON_MM] for m in measured])
    b = np.concatenate([m.b[m.clearance_mm < required_mm[m.kind] - DRC_EPSILON_MM] for m in measured])
    periodic = maps.periodic[a] & maps.periodic[b]
    a, b = a[periodic], b[periodic]
    copies_a = np.concatenate([image[a] for image in maps.images[1:]]) if len(a) else a
    copies_b = np.concatenate([image[b] for image in maps.images[1:]]) if len(b) else b
    n = len(items)
    keys = np.unique(np.minimum(copies_a, copies_b) * n + np.maximum(copies_a, copies_b))
    seen = np.concatenate([m.a * n + m.b for m in measured])
    keys = keys[~np.isin(keys, seen)]
    ca, cb = keys // n, keys % n
    return [
        _check(items, layout, ca[on], cb[on], exempt, layout.copper_layers[index])
        for index in np.unique(items.layer[ca])
        for on in [items.layer[ca] == index]
    ]


def _item_checks(
    layout: Layout, rules: DrcRules
) -> dict[DrcCheckKind, list[tuple[float, str | None, tuple[float, float], str]]]:
    """Width, drill and annular ring of each object: (measured, layer, location, object id) per kind."""
    found: dict[DrcCheckKind, list[tuple[float, str | None, tuple[float, float], str]]] = {
        DrcCheckKind.MIN_WIDTH: [],
        DrcCheckKind.MIN_DRILL: [],
        DrcCheckKind.ANNULAR_RING: [],
    }
    for path in layout.paths:
        for k, prim in enumerate(path.primitives):
            found[DrcCheckKind.MIN_WIDTH].append(
                (prim.width_mm, path.layer, prim.start_point(), f"path:{path.id}/prim:{k}")
            )
    for via in layout.vias:
        at = (via.x_mm, via.y_mm)
        found[DrcCheckKind.MIN_DRILL].append((via.drill_mm, None, at, f"via:{via.id}"))
        found[DrcCheckKind.ANNULAR_RING].append(((via.pad_mm - via.drill_mm) / 2, None, at, f"via:{via.id}"))
    for pad in layout.pads:
        if pad.drill_mm > 0:
            at = (pad.x_mm, pad.y_mm)
            found[DrcCheckKind.MIN_DRILL].append((pad.drill_mm, None, at, f"pad:{pad.id}"))
            ring_mm = (min(pad.width_mm, pad.height_mm) - pad.drill_mm) / 2
            found[DrcCheckKind.ANNULAR_RING].append((ring_mm, None, at, f"pad:{pad.id}"))
    return found


def _report(
    items: Items,
    layout: Layout,
    rules: DrcRules,
    measured: list[_Measured],
    required_mm: FloatArray,
    maps: RotationMaps | None,
) -> DrcReport:
    summaries: list[DrcCheckSummary] = []
    violations: list[DrcViolation] = []
    kinds = np.concatenate([m.kind for m in measured]) if measured else np.empty(0, dtype=np.int64)
    values = np.concatenate([m.clearance_mm for m in measured]) if measured else np.empty(0)
    for index, kind in enumerate(PAIR_KINDS):
        if not _applicable(items, kind):
            continue
        mine = values[kinds == index]
        least = float(mine.min()) if len(mine) else None
        summaries.append(
            DrcCheckSummary(
                kind=kind, measured_min_mm=least, required_mm=float(required_mm[index]), pairs_checked=len(mine)
            )
        )
    for m in measured:
        bad = np.flatnonzero(m.clearance_mm < required_mm[m.kind] - DRC_EPSILON_MM)
        for i in bad:
            kind = PAIR_KINDS[int(m.kind[i])]
            violations.append(
                DrcViolation(
                    kind=kind,
                    layer=m.layer,
                    measured_mm=float(m.clearance_mm[i]),
                    required_mm=float(required_mm[m.kind[i]]),
                    at_mm=(float(m.at_mm[i, 0]), float(m.at_mm[i, 1])),
                    objects=(items.labels[int(m.a[i])], items.labels[int(m.b[i])]),
                )
            )
    for kind, rows in _item_checks(layout, rules).items():
        if not rows:
            continue
        need_mm = REQUIRED_MM[kind](rules)
        summaries.append(
            DrcCheckSummary(
                kind=kind, measured_min_mm=min(r[0] for r in rows), required_mm=need_mm, pairs_checked=len(rows)
            )
        )
        violations += [
            DrcViolation(kind=kind, layer=layer, measured_mm=value_mm, required_mm=need_mm, at_mm=at, objects=(label,))
            for value_mm, layer, at, label in rows
            if violates(value_mm, need_mm)
        ]
    violations.sort(key=lambda v: (v.measured_mm - v.required_mm, v.kind, v.objects))
    return DrcReport(
        passed=not violations,
        summaries=tuple(summaries),
        violations=tuple(violations[:MAX_REPORTED_VIOLATIONS]),
        violation_count=len(violations),
        method="grid+exact" if maps is None else "symmetric+grid+exact",
    )


def _applicable(items: Items, kind: DrcCheckKind) -> bool:
    present = np.bincount(items.item_class, minlength=len(ItemClass))
    for classes, k in _KIND_OF_CLASSES.items():
        if k is not kind:
            continue
        first, *rest = sorted(classes)
        if (rest and present[first] and present[rest[0]]) or (not rest and present[first] >= 2):
            return True
    return False
