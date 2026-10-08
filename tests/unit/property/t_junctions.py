"""Brute-force T-junction exemption (D-035 b, interfaces.md section 7 rule 5), coded from the decision text.

Agent 4's ``drc_universe.contract_exemptions`` predates rule 5, so the PR-13 sweeps add these pairs to its result.
"""

from collections.abc import Sequence

from brute_clearance import centreline_bracket
from drc_universe import COINCIDENT_MM, Item, Pair, _box_gap, _ends, _owners, _pairs, _paths
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
