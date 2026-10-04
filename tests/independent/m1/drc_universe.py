"""Agent 4's own DRC universe: every copper item of a board, the D-006 exemptions, and a brute pair sweep.

Written from interfaces.md section 7, not from embodic. Through vias, through pads, board edges and screw holes sit on
every copper layer. A via, a round pad or a hole is a disc: a zero-length ``Line`` whose width is the diameter. A board
edge piece has width 0. The sweep checks every pair of items that share a layer, except pairs of two every-layer items
inside a layer pass (they are checked once, in the every-layer pass).

Exemptions. ``contract_exemptions`` is interfaces.md section 7 read literally: primitives adjacent in a path, and a via
or pad and the primitive that ends a same-net path on it. ``extended_exemptions`` adds the three rules the U-M1c worker
documents in ``exempt_pairs``; this module codes them again from that text so minima can be compared like for like.
"""

import math
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from enum import StrEnum
from itertools import pairwise

import numpy as np
from brute_clearance import (
    DRC_EPSILON_MM,
    Bracket,
    Verdict,
    bounding_boxes,
    clearance_bracket,
    pair_verdict,
)
from records import Arc, Line, Point, Prim, end_point, start_point

COINCIDENT_MM = 1e-6


class Cls(StrEnum):
    """What an item is; the pair of classes picks the check kind."""

    TRACE = "trace"
    VIA = "via"
    PAD = "pad"
    EDGE = "edge"
    HOLE = "hole"


_LANDS = frozenset({Cls.VIA, Cls.PAD})
KIND_OF: dict[frozenset[Cls], str] = {
    frozenset({Cls.TRACE}): "trace_trace",
    frozenset({Cls.TRACE, Cls.VIA}): "trace_via",
    frozenset({Cls.VIA}): "via_via",
    frozenset({Cls.TRACE, Cls.PAD}): "pad_trace",
    frozenset({Cls.PAD}): "pad_pad",
    frozenset({Cls.VIA, Cls.PAD}): "pad_pad",
    **{frozenset({c, Cls.EDGE}): "copper_edge" for c in (Cls.TRACE, Cls.VIA, Cls.PAD)},
    **{frozenset({c, Cls.HOLE}): "copper_hole" for c in (Cls.TRACE, Cls.VIA, Cls.PAD)},
}


@dataclass(frozen=True, slots=True)
class Item:
    """One copper or keep-out item; ``layer`` None means every copper layer. ``corner`` marks a fillet or taper."""

    label: str
    cls: Cls
    prim: Prim
    layer: int | None
    net: str = ""
    path: int | None = None
    seq: int | None = None
    corner: bool = False


Pair = frozenset[str]


@dataclass(frozen=True, slots=True)
class PairResult:
    """A measured pair: labels, check kind, layer (None for the every-layer pass) and the clearance bracket."""

    a: str
    b: str
    kind: str
    layer: int | None
    clearance: Bracket
    verdict: Verdict


def disc_centre(item: Item) -> Point:
    """Return the centre of a via, pad or hole disc."""
    assert isinstance(item.prim, Line)
    return (item.prim.x1, item.prim.y1)


def _paths(items: Sequence[Item]) -> dict[int, list[Item]]:
    out: dict[int, list[Item]] = {}
    for it in items:
        if it.cls is Cls.TRACE and it.path is not None:
            out.setdefault(it.path, []).append(it)
    for prims in out.values():
        prims.sort(key=lambda it: it.seq if it.seq is not None else 0)
    return out


def _on_land(land: Item, point: Point, layer: int | None) -> bool:
    return land.layer in (None, layer) and math.dist(point, disc_centre(land)) <= land.prim.width / 2


def contract_exemptions(items: Sequence[Item]) -> set[Pair]:
    """Interfaces.md section 7 literally: consecutive primitives of one path; a land and the primitive ending on it."""
    pairs: set[Pair] = set()
    lands = [it for it in items if it.cls in _LANDS]
    for path in _paths(items).values():
        pairs.update(frozenset((a.label, b.label)) for a, b in pairwise(path))
        for end_item, point in ((path[0], start_point(path[0].prim)), (path[-1], end_point(path[-1].prim))):
            pairs.update(
                frozenset((land.label, end_item.label))
                for land in lands
                if land.net == end_item.net and _on_land(land, point, end_item.layer)
            )
    return pairs


def _mains(path: Sequence[Item]) -> list[int]:
    out, index = [], -1
    for it in path:
        if not it.corner:
            index += 1
        out.append(max(0, index))
    return out


_End = tuple[Item, Point, list[Item]]  # terminating primitive, end point, its end group


def _corner_pairs_and_ends(items: Sequence[Item], pairs: set[Pair]) -> list[_End]:
    ends: list[_End] = []
    for path in _paths(items).values():
        mains = _mains(path)
        for i, a in enumerate(path):
            pairs.update(
                frozenset((a.label, b.label)) for j, b in enumerate(path[i + 1 :], i + 1) if mains[j] - mains[i] <= 1
            )
        for k, point in ((0, start_point(path[0].prim)), (-1, end_point(path[-1].prim))):
            ends.append((path[k], point, [it for it, m in zip(path, mains, strict=True) if m == mains[k]]))
    return ends


def _nodes(ends: list[_End], lands: list[Item], pairs: set[Pair]) -> list[list[_End]]:
    nodes: list[list[_End]] = []
    for land in lands:
        node = [e for e in ends if e[0].net == land.net and _on_land(land, e[1], e[0].layer)]
        pairs.update(frozenset((land.label, it.label)) for e in node for it in e[2])
        nodes.append(node)
    for i, e in enumerate(ends):
        meet = [
            f
            for f in ends[i + 1 :]
            if f[0].layer == e[0].layer and f[0].net == e[0].net and math.dist(f[1], e[1]) <= COINCIDENT_MM
        ]
        if meet:
            nodes.append([e, *meet])
    return nodes


def extended_exemptions(items: Sequence[Item]) -> set[Pair]:
    """Return the exemptions the U-M1c worker documents, coded again from the text of ``exempt_pairs``.

    Fillets and tapers join the corner before them, and items whose corner indices differ by at most one are exempt. A
    land is exempt with the whole end group. End groups of different same-net paths that meet at one land or one point
    are exempt with each other. A pad is exempt with a same-net via inside it.
    """
    pairs: set[Pair] = set()
    lands = [it for it in items if it.cls in _LANDS]
    for node in _nodes(_corner_pairs_and_ends(items, pairs), lands, pairs):
        for x, e in enumerate(node):
            for f in node[x + 1 :]:
                if f[0].path != e[0].path:
                    pairs.update(frozenset((a.label, b.label)) for a in e[2] for b in f[2])
    pads = [it for it in lands if it.cls is Cls.PAD]
    vias = [it for it in lands if it.cls is Cls.VIA]
    pairs.update(
        frozenset((p.label, v.label))
        for p in pads
        for v in vias
        if p.net == v.net and math.dist(disc_centre(p), disc_centre(v)) <= p.prim.width / 2
    )
    return pairs


def layer_passes(items: Sequence[Item], layers: Sequence[int]) -> Iterator[tuple[int | None, list[int], bool]]:
    """Each copper layer with the every-layer items (pairs of two every-layer items skipped), then those alone."""
    every = [i for i, it in enumerate(items) if it.layer is None]
    for layer in layers:
        yield layer, sorted(every + [i for i, it in enumerate(items) if it.layer == layer]), True
    yield None, every, False


def sweep(
    items: Sequence[Item],
    layers: Sequence[int],
    rule_of: Callable[[str], float],
    exempt: set[Pair],
    *,
    reach_mm: float = 0.0,
    tol: float = 1e-10,
    decide: bool = True,
) -> list[PairResult]:
    """Measure every non-exempt pair whose boxes lie closer than ``rule + reach_mm`` plus the half widths.

    ``decide`` stops each bracket once the D-006 verdict is known; otherwise each bracket is refined to ``tol``.
    """
    results: list[PairResult] = []
    widest_rule = max(rule_of(kind) for kind in set(KIND_OF.values()))
    for layer, sel, skip_every in layer_passes(items, layers):
        group = [items[i] for i in sel]
        if len(group) < 2:
            continue
        boxes = bounding_boxes([it.prim for it in group])
        widths = np.array([it.prim.width for it in group])
        for i in range(len(group) - 1):
            rest = boxes[i + 1 :]
            gap_x = np.maximum(0.0, np.maximum(rest[:, 0] - boxes[i, 2], boxes[i, 0] - rest[:, 2]))
            gap_y = np.maximum(0.0, np.maximum(rest[:, 1] - boxes[i, 3], boxes[i, 1] - rest[:, 3]))
            near = np.hypot(gap_x, gap_y) < widest_rule + reach_mm + (widths[i] + widths[i + 1 :]) / 2.0
            for j in np.flatnonzero(near) + i + 1:
                p, q = group[i], group[int(j)]
                kind = KIND_OF.get(frozenset({p.cls, q.cls}))
                if kind is None or (skip_every and p.layer is None and q.layer is None):
                    continue
                if frozenset((p.label, q.label)) in exempt:
                    continue
                rule = rule_of(kind)
                gap = math.hypot(float(gap_x[j - i - 1]), float(gap_y[j - i - 1])) - (p.prim.width + q.prim.width) / 2
                if gap >= rule + reach_mm - DRC_EPSILON_MM:
                    continue
                if decide:
                    found, bracket = pair_verdict(p.prim, q.prim, rule, tol=tol)
                else:
                    bracket = clearance_bracket(p.prim, q.prim, tol=tol)
                    found = _verdict(bracket, rule)
                results.append(PairResult(p.label, q.label, kind, layer, bracket, found))
    return results


def _verdict(b: Bracket, rule: float) -> Verdict:
    threshold = rule - DRC_EPSILON_MM
    if b.hi < threshold:
        return Verdict.VIOLATION
    if b.lo >= threshold:
        return Verdict.CLEAN
    return Verdict.UNDECIDED


def rotate(p: Prim, angle: float) -> Prim:
    """Rotate a record about the origin by ``angle`` (own transform, for the symmetry tests)."""
    c, s = math.cos(angle), math.sin(angle)
    if isinstance(p, Line):
        return Line(c * p.x1 - s * p.y1, s * p.x1 + c * p.y1, c * p.x2 - s * p.y2, s * p.x2 + c * p.y2, p.width)
    return Arc(c * p.cx - s * p.cy, s * p.cx + c * p.cy, p.r, p.start + angle, p.sweep, p.width)
