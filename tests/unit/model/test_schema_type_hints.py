"""Opening a design resolves the type hints of each model class once, not once per field (U-M8a follow-up)."""

import typing
from collections import Counter

import pytest

from embodic.model.draft import draft_from_design, parse_draft
from embodic.model.schema import design_from_json, leaves, to_json

from .designs import EXAMPLES


@pytest.mark.req("REQ-N-02")
def test_opening_the_example_designs_resolves_the_hints_of_each_class_at_most_once(monkeypatch):
    """Catches get_type_hints running per field, as it did 970 times to load one example.

    Evaluating a class's annotations costs the same on every call, so a repeat is wasted time on the GUI thread.
    """
    resolved: Counter[object] = Counter()
    real = typing.get_type_hints

    def counting(obj, *args, **kwargs):
        resolved[obj] += 1
        return real(obj, *args, **kwargs)

    monkeypatch.setattr(typing, "get_type_hints", counting)
    for build in EXAMPLES.values():
        design = build()
        leaves(design.topology)
        assert parse_draft(draft_from_design(design)) == design
        assert design_from_json(design.topology, to_json(design)) == design

    repeated = {cls.__name__: count for cls, count in resolved.items() if count > 1}
    assert repeated == {}
