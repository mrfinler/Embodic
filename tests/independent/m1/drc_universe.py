"""Agent 4's own DRC universe: every copper item of a board, the D-006 exemptions, and a brute pair sweep.

Written from interfaces.md section 7, not from embodic. Through vias, through pads, board edges and screw holes sit on
every copper layer. A via, a round pad or a hole is a disc: a zero-length ``Line`` whose width is the diameter. A board
edge piece has width 0. The sweep checks every pair of items that share a layer, except pairs of two every-layer items
inside a layer pass (they are checked once, in the every-layer pass).

Exemptions. ``contract_exemptions`` is interfaces.md section 7 as revised on 2026-10-20 (U-D25, D-078), coded here
from the text and labelled with the rule that exempts each pair: rule 1 neighbours in one path (a fillet or taper
belongs to the main before and after it, at a path end to one main), rule 2 a path end on a land, rule 2b a via and each
primitive whose centreline passes within pad/2 of it, rule 3 path ends at one node, rule 4 a via inside a pad, rule 5 a
path end on another path's centreline against the landing group there, each with the same-net test, and the
interconnect waiver that drops the net test between an interconnect path and the lands its ends touch (rules 2, 3) or
the vias its primitives tap (rule 2 tap).
"""

import math
from collections.abc import Callable, Collection, Container, Iterator, Sequence
from dataclasses import dataclass
from enum import StrEnum

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


class Rule(StrEnum):
    """Why interfaces.md section 7, with D-022 and D-022c, exempts a pair."""

    NEIGHBOURS = "rule 1: neighbours in one path"
    END_ON_LAND = "rule 2: path end on a same-net land"
    VIA_TAP = "rule 2b: via on a same-net primitive's centreline (D-036a, D-037a)"
    NODE = "rule 3: same-net path ends at one node"
    PAD_VIA = "rule 4: same-net via inside a pad"
    TEE = "rule 5: same-net path end against the landing group on another path (D-035b, D-078)"
    INTERCONNECT_END = "D-022a/c: interconnect end on a land, any net"
    INTERCONNECT_TAP = "rule 2 tap: via on an interconnect primitive's centreline, any net (D-022c, D-078)"


Exemptions = dict[Pair, Rule]


@dataclass(frozen=True, slots=True)
class _End:
    """One end of a path: its end point and its end group (terminating main primitive with its fillets and tapers)."""

    path: int
    net: str
    layer: int | None
    point: Point
    group: tuple[Item, ...]


def _owners(path: Sequence[Item]) -> list[frozenset[int]]:
    """Return the main indices each primitive belongs to: its own for a main, the mains around a fillet or taper."""
    total = sum(not it.corner for it in path)
    out, seen = [], 0
    for it in path:
        if it.corner:
            out.append(frozenset(m for m in (seen - 1, seen) if 0 <= m < total))
        else:
            out.append(frozenset({seen}))
            seen += 1
    return out


def _rule_1(path: Sequence[Item], owners: Sequence[frozenset[int]]) -> Iterator[Pair]:
    """Two mains at most one main index apart; otherwise a fillet or taper and anything sharing a main with it."""
    for i, a in enumerate(path):
        for j in range(i + 1, len(path)):
            b = path[j]
            if a.corner or b.corner:
                near = bool(owners[i] & owners[j])
            else:
                near = abs(min(owners[i]) - min(owners[j])) <= 1
            if near:
                yield frozenset((a.label, b.label))


def _ends(path: Sequence[Item], owners: Sequence[frozenset[int]]) -> list[_End]:
    mains = sorted(set().union(*owners))
    if not mains:
        return []
    first, last = path[0], path[-1]
    return [
        _End(first.path or 0, first.net, first.layer, start_point(first.prim),
             tuple(it for it, o in zip(path, owners, strict=True) if mains[0] in o)),
        _End(last.path or 0, last.net, last.layer, end_point(last.prim),
             tuple(it for it, o in zip(path, owners, strict=True) if mains[-1] in o)),
    ]  # fmt: skip


def _pairs(a: Sequence[Item], b: Sequence[Item]) -> Iterator[Pair]:
    return (frozenset((x.label, y.label)) for x in a for y in b)


def point_to_centreline(point: Point, prim: Prim) -> float:
    """Return the exact distance from a point to a centreline.

    On a segment it is the distance to the clamped foot. On an arc it is the radial gap when the point's angle lies
    inside the sweep, else the distance to the nearer end point.
    """
    px, py = point
    if isinstance(prim, Line):
        dx, dy = prim.x2 - prim.x1, prim.y2 - prim.y1
        length2 = dx * dx + dy * dy
        t = 0.0 if length2 == 0.0 else min(1.0, max(0.0, ((px - prim.x1) * dx + (py - prim.y1) * dy) / length2))
        return math.hypot(px - prim.x1 - t * dx, py - prim.y1 - t * dy)
    turned = math.copysign(1.0, prim.sweep) * (math.atan2(py - prim.cy, px - prim.cx) - prim.start)
    if abs(prim.sweep) >= math.tau or turned % math.tau <= abs(prim.sweep):
        return abs(math.hypot(px - prim.cx, py - prim.cy) - prim.r)
    return min(math.dist(point, start_point(prim)), math.dist(point, end_point(prim)))


def _landing_group(path: Sequence[Item], owners: Sequence[frozenset[int]], k: int) -> list[Item]:
    """Rule 5 (U-D25): the landing group of primitive ``k`` of ``path``.

    A main with the fillets and tapers that belong to it; a fillet or taper with the mains it belongs to and the other
    fillets and tapers between those mains, read as the run of consecutive fillets and tapers that holds it.
    """
    if not path[k].corner:
        return [it for j, it in enumerate(path) if j == k or (it.corner and owners[k] <= owners[j])]
    lo, hi = k, k
    while lo > 0 and path[lo - 1].corner:
        lo -= 1
    while hi + 1 < len(path) and path[hi + 1].corner:
        hi += 1
    return [*path[lo : hi + 1], *(it for j, it in enumerate(path) if not it.corner and owners[j] <= owners[k])]


def _box_gap(p: Prim, q: Prim) -> float:
    """Distance between the centreline boxes of two primitives (tests/unit/property/t_junctions.py imports it)."""
    a, b = bounding_boxes([p, q])
    return math.hypot(max(0.0, a[0] - b[2], b[0] - a[2]), max(0.0, a[1] - b[3], b[1] - a[3]))


@dataclass(frozen=True, slots=True)
class _Traces:
    """Every trace primitive with its centreline box, for point queries."""

    items: Sequence[Item]
    boxes: np.ndarray

    def within(self, point: Point, reach: float) -> Iterator[Item]:
        """Yield each primitive whose centreline passes within ``reach`` of ``point``."""
        x, y = point
        gap = np.hypot(
            np.maximum(0.0, np.maximum(self.boxes[:, 0] - x, x - self.boxes[:, 2])),
            np.maximum(0.0, np.maximum(self.boxes[:, 1] - y, y - self.boxes[:, 3])),
        )
        for k in np.flatnonzero(gap <= reach):
            it = self.items[int(k)]
            if point_to_centreline(point, it.prim) <= reach:
                yield it


def _via_taps(lands: Sequence[Item], traces: _Traces, interconnect: Collection[int]) -> Iterator[tuple[Pair, Rule]]:
    """Rule 2b and the rule 2 tap: a via and each primitive whose centreline passes within pad/2 of its centre.

    Same net (D-036a, D-037a), or any net when the primitive's path is an interconnect (D-022c per primitive, D-078).
    Vias only: §7 names no pad in either clause.
    """
    for via in lands:
        if via.cls is Cls.VIA:
            for it in traces.within(disc_centre(via), via.prim.width / 2):
                if it.net == via.net:
                    yield frozenset((via.label, it.label)), Rule.VIA_TAP
                elif it.path in interconnect:
                    yield frozenset((via.label, it.label)), Rule.INTERCONNECT_TAP


def _tees(
    ends: Sequence[_End], paths: dict[int, list[Item]], owners: dict[int, list[frozenset[int]]], traces: _Traces
) -> Iterator[Pair]:
    """Rule 5 (D-035b, D-078): an end group and the landing group of each primitive the end lies on.

    That primitive belongs to another path of the same net on the end's layer.
    """
    for e in ends:
        for it in traces.within(e.point, COINCIDENT_MM):
            if it.path != e.path and it.net == e.net and it.layer == e.layer:
                path = paths[it.path]
                yield from _pairs(e.group, _landing_group(path, owners[it.path], path.index(it)))


def _at_lands(
    lands: Sequence[Item], ends: Sequence[_End], interconnect: Collection[int]
) -> Iterator[tuple[Pair, Rule]]:
    """Rules 2 and 3 at a via or pad, with the interconnect waiver of the net test."""
    for land in lands:
        node = [e for e in ends if _on_land(land, e.point, e.layer)]
        for e in node:
            if e.net == land.net or e.path in interconnect:
                rule = Rule.END_ON_LAND if e.net == land.net else Rule.INTERCONNECT_END
                yield from ((pair, rule) for pair in _pairs([land], e.group))
        for x, e in enumerate(node):
            for f in node[x + 1 :]:
                if f.path != e.path and (f.net == e.net or e.path in interconnect or f.path in interconnect):
                    rule = Rule.NODE if f.net == e.net else Rule.INTERCONNECT_END
                    yield from ((pair, rule) for pair in _pairs(e.group, f.group))


def _at_points(ends: Sequence[_End]) -> Iterator[Pair]:
    """Rule 3 without a land: same-net ends of two paths on one layer within ``COINCIDENT_MM``; no waiver."""
    for x, e in enumerate(ends):
        for f in ends[x + 1 :]:
            same = f.path != e.path and f.layer == e.layer and f.net == e.net
            if same and math.dist(f.point, e.point) <= COINCIDENT_MM:
                yield from _pairs(e.group, f.group)


def _vias_in_pads(lands: Sequence[Item]) -> Iterator[Pair]:
    """Rule 4: a pad and a same-net via whose centre lies inside it."""
    pads = [it for it in lands if it.cls is Cls.PAD]
    vias = [it for it in lands if it.cls is Cls.VIA]
    for p in pads:
        for v in vias:
            if p.net == v.net and math.dist(disc_centre(p), disc_centre(v)) <= p.prim.width / 2:
                yield frozenset((p.label, v.label))


def contract_exemptions(items: Sequence[Item], interconnect: Collection[int] = ()) -> Exemptions:
    """Return every pair interfaces.md section 7 (revision 2026-10-20, U-D25) exempts, with its first rule.

    ``interconnect`` holds the ids of interconnect paths (``Circuit.interconnect_path_ids``). The net test applies to
    rules 2 to 5, except that an interconnect path is exempt from any via or pad its end lies on (rules 2 and 3), and
    each of its primitives from any via whose centre lies within pad/2 of that primitive's centreline (the rule 2 tap),
    whatever the nets. Rule 2b and the tap are per primitive. Rule 5 exempts an end group from the landing group of each
    primitive its end point lies on, end points of that primitive included, and from nothing else of that path.
    """
    lands = [it for it in items if it.cls in (Cls.VIA, Cls.PAD)]
    paths = _paths(items)
    owners = {pid: _owners(path) for pid, path in paths.items()}
    out: Exemptions = {}
    ends: list[_End] = []
    for pid, path in paths.items():
        out.update(dict.fromkeys(_rule_1(path, owners[pid]), Rule.NEIGHBOURS))
        ends += _ends(path, owners[pid])
    flat = [it for path in paths.values() for it in path]
    traces = _Traces(flat, bounding_boxes([it.prim for it in flat]) if flat else np.empty((0, 4)))
    labelled = [
        _at_lands(lands, ends, interconnect),
        ((pair, Rule.NODE) for pair in _at_points(ends)),
        ((pair, Rule.PAD_VIA) for pair in _vias_in_pads(lands)),
        _via_taps(lands, traces, interconnect),
        ((pair, Rule.TEE) for pair in _tees(ends, paths, owners, traces)),
    ]
    for source in labelled:
        for pair, rule in source:
            out.setdefault(pair, rule)
    return out


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
    exempt: Container[Pair],
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
