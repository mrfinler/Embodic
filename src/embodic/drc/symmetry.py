"""Proof step of the symmetry shortcut: whether ``Layout.symmetry`` is true of the copper it describes.

The shortcut is sound only when rotating the canonical paths by every multiple of ``2 pi / order`` reproduces each
periodic path exactly once (same layer, roles, widths and geometry within ``MATCH_MM``), and the exempt pairs among
periodic primitives are carried onto exempt pairs by the same rotations. Anything else returns None, and
``run_drc`` falls back to the full check.
"""

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from embodic.drc.items import NO_INDEX, IntArray, Items
from embodic.geometry.layout import Layout
from embodic.geometry.paths import CopperPath
from embodic.geometry.primitives import Arc, Primitive
from embodic.geometry.transforms import rotate

MATCH_MM = 1e-9


@dataclass(frozen=True, slots=True, kw_only=True)
class RotationMaps:
    """``images[k][i]`` is the item that item ``i`` becomes after ``k`` periods; NO_INDEX for non-periodic items."""

    periodic: NDArray[np.bool_]
    canonical: NDArray[np.bool_]
    images: tuple[IntArray, ...]  # one per k = 0 .. order - 1; images[0] is the identity on periodic items


def _same(p: Primitive, q: Primitive) -> bool:
    if type(p) is not type(q) or p.role is not q.role or abs(p.width_mm - q.width_mm) > MATCH_MM:
        return False
    points = [(p.start_point(), q.start_point()), (p.end_point(), q.end_point())]
    if isinstance(p, Arc) and isinstance(q, Arc):
        if abs(p.r_mm - q.r_mm) > MATCH_MM or abs(p.sweep_rad * p.r_mm - q.sweep_rad * q.r_mm) > MATCH_MM:
            return False
        points.append((p.mid_point(), q.mid_point()))
    return all(math.dist(u, v) <= MATCH_MM for u, v in points)


def _find(rotated: tuple[Primitive, ...], layer: str, candidates: list[CopperPath]) -> CopperPath | None:
    for path in candidates:
        if path.layer == layer and len(path.primitives) == len(rotated):
            if all(_same(p, q) for p, q in zip(rotated, path.primitives, strict=True)):
                return path
    return None


def rotation_maps(layout: Layout, items: Items, first_item: dict[int, int], exempt: IntArray) -> RotationMaps | None:
    """Return the item rotation maps when the layout's symmetry claim holds, else None (shortcut disabled)."""
    sym = layout.symmetry
    if sym is None or sym.order < 2 or not set(sym.canonical_path_ids) <= set(sym.periodic_path_ids):
        return None
    by_id = {p.id: p for p in layout.paths}
    periodic_paths = [by_id[i] for i in sym.periodic_path_ids]
    sector_first: list[dict[int, int]] = []  # sector_first[k][cid]: first item of the copy of cid in sector k
    hit: set[int] = set()
    for k in range(sym.order):
        firsts: dict[int, int] = {}
        for cid in sym.canonical_path_ids:
            source = by_id[cid]
            target = _find(rotate(source.primitives, k * 2 * math.pi / sym.order), source.layer, periodic_paths)
            if target is None or target.id in hit or (k == 0 and target.id != cid):
                return None
            hit.add(target.id)
            firsts[cid] = first_item[target.id]
        sector_first.append(firsts)
    if hit != set(sym.periodic_path_ids):
        return None
    n = len(items)
    images = [np.full(n, NO_INDEX, dtype=np.int64) for _ in range(sym.order)]
    canonical = np.zeros(n, dtype=np.bool_)
    for cid in sym.canonical_path_ids:
        count = len(by_id[cid].primitives)
        canonical[first_item[cid] : first_item[cid] + count] = True
        for j in range(sym.order):
            for k in range(sym.order):
                src, dst = sector_first[j][cid], sector_first[(j + k) % sym.order][cid]
                images[k][src : src + count] = np.arange(dst, dst + count)
    periodic = images[0] != NO_INDEX
    if not _exemptions_invariant(images, periodic, exempt, n):
        return None
    return RotationMaps(periodic=periodic, canonical=canonical, images=tuple(images))


def _exemptions_invariant(images: list[IntArray], periodic: NDArray[np.bool_], exempt: IntArray, n: int) -> bool:
    a, b = exempt // n, exempt % n
    both = periodic[a] & periodic[b]
    a, b = a[both], b[both]
    for image in images[1:]:
        ra, rb = image[a], image[b]
        if not np.isin(np.minimum(ra, rb) * n + np.maximum(ra, rb), exempt).all():
            return False
    return True
