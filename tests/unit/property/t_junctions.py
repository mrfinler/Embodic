"""Rule 5 (D-035b) and rule 2b (D-036a, D-037a) exempt pairs, read from Agent 4's public ``contract_exemptions``.

PR-13 once re-derived both rules here because ``contract_exemptions`` predated them. It carries them now, so these views
only select pairs by rule. ``contract_exemptions`` keeps the first rule that exempts a pair, so a pair that rule 1 or 3
also exempts is labelled with that rule and is not listed here. Callers union these sets with ``contract_exemptions``.
"""

from collections.abc import Sequence

from drc_universe import Item, Pair, Rule, contract_exemptions


def _pairs_under(items: Sequence[Item], rule: Rule) -> set[Pair]:
    return {pair for pair, why in contract_exemptions(items).items() if why is rule}


def t_junction_pairs(items: Sequence[Item]) -> set[Pair]:
    """Return the pairs rule 5 exempts: a path end group and the same-net path whose centreline holds the end."""
    return _pairs_under(items, Rule.TEE)


def same_net_via_tap_pairs(items: Sequence[Item]) -> set[Pair]:
    """Return the pairs rule 2b exempts: a via and each same-net primitive whose centreline passes within pad / 2."""
    return _pairs_under(items, Rule.VIA_TAP)
