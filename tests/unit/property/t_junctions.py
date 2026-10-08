"""Brute-force T-junction and same-net via tap exemptions (D-035 b, D-036 a, D-037a), coded from the decision texts.

Agent 4's ``drc_universe.contract_exemptions`` predates rule 5 and rule 2b, so the PR-13 sweeps add these pairs to
its result.
"""

import math
from collections.abc import Sequence

from brute_clearance import bounding_boxes, centreline_bracket
from drc_universe import COINCIDENT_MM, Cls, Item, Pair, _ends, _owners, _pairs, _paths, disc_centre
from records import Line, Prim


def _box_gap(p: Prim, q: Prim) -> float:
    """Return the distance between the centreline bounding boxes of two primitives (0 when they overlap)."""
    a, b = bounding_boxes([p, q])
    return math.hypot(max(0.0, a[0] - b[2], b[0] - a[2]), max(0.0, a[1] - b[3], b[1] - a[3]))


def t_junction_pairs(items: Sequence[Item]) -> set[Pair]:
    """Return the pairs of an end group and every primitive of a same-net, same-layer path its end point lies on."""
    paths = _paths(items)
    pairs: set[Pair] = set()
    for path in paths.values():
        for end in _ends(path, _owners(path)):
            probe = Line(*end.point, *end.point, 0.0)
            for other in paths.values():
                if other[0].path == end.path or other[0].net != end.net or other[0].layer != end.layer:
                    continue
                on_centreline = (
                    _box_gap(probe, it.prim) <= COINCIDENT_MM
                    and centreline_bracket(probe, it.prim, threshold=COINCIDENT_MM).lo <= COINCIDENT_MM
                    for it in other
                )
                if any(on_centreline):
                    pairs.update(_pairs(end.group, other))
    return pairs


def _within(probe: Line, prim: Prim, radius: float) -> bool:
    return _box_gap(probe, prim) <= radius and centreline_bracket(probe, prim, threshold=radius).lo <= radius


def same_net_via_tap_pairs(items: Sequence[Item]) -> set[Pair]:
    """Return the pairs of a via and each primitive of a same-net path whose centreline passes within pad / 2 of it."""
    paths = _paths(items)
    pairs: set[Pair] = set()
    for via in (it for it in items if it.cls is Cls.VIA):
        probe = Line(*disc_centre(via), *disc_centre(via), 0.0)
        for path in (p for p in paths.values() if p[0].net == via.net):
            pairs.update(frozenset((via.label, it.label)) for it in path if _within(probe, it.prim, via.prim.width / 2))
    return pairs
