"""Brute-force T-junction and same-net via tap exemptions (D-035 b, D-036 a), coded from the decision texts.

Agent 4's ``drc_universe.contract_exemptions`` predates rule 5 and rule 2b, so the PR-13 sweeps add these pairs to
its result.
"""

from collections.abc import Sequence

from brute_clearance import centreline_bracket
from drc_universe import COINCIDENT_MM, Cls, Item, Pair, _box_gap, _ends, _on_centreline, _owners, _pairs, _paths
from records import Line


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


def same_net_via_tap_pairs(items: Sequence[Item]) -> set[Pair]:
    """Return the pairs of a via and every primitive of a same-net path whose centreline passes within pad / 2 of it."""
    paths = _paths(items)
    return {
        pair
        for via in items
        if via.cls is Cls.VIA
        for path in paths.values()
        if path[0].net == via.net and _on_centreline(via, path)
        for pair in _pairs([via], path)
    }
