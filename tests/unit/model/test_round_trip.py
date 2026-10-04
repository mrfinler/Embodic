"""Property: random valid designs round-trip exactly through JSON data and through the draft."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from embodic.model.draft import DesignDraft, DraftIncomplete, draft_from_design, parse_draft
from embodic.model.fields import FieldSpec, Sign, field_for
from embodic.model.schema import ValueType, design_from_json, to_json

from .designs import EXAMPLES

TAG_LEAVES = ("/kind", "/shape")


def _number(spec: FieldSpec, integer: bool) -> st.SearchStrategy[float | int]:
    floor = {Sign.POSITIVE: 1 if integer else 1e-6, Sign.NON_NEGATIVE: 0.0, Sign.ANY: -1e6}[spec.limits.sign]
    low = floor if spec.limits.low is None else max(spec.limits.low, floor)
    high = 1e6 if spec.limits.high is None else spec.limits.high
    if integer:
        return st.integers(min_value=int(low), max_value=int(min(high, 1000)))
    return st.floats(min_value=low, max_value=high, allow_nan=False, allow_infinity=False)


def _leaf(spec: FieldSpec, current: object) -> st.SearchStrategy[object]:
    strategies = {
        ValueType.FLOAT: lambda: _number(spec, integer=False),
        ValueType.INT: lambda: _number(spec, integer=True),
        ValueType.BOOL: st.booleans,
        ValueType.TEXT: lambda: st.text(min_size=1, max_size=8).filter(str.strip),
        ValueType.CHOICE: lambda: st.sampled_from(spec.choices),
    }
    make = strategies.get(spec.value_type)
    keep = (
        make is None or spec.pointer.endswith(TAG_LEAVES) or spec.pointer.endswith(("/name", "/layer_in", "/layer_out"))
    )
    strategy = st.just(current) if keep else make()
    return st.one_of(st.none(), strategy) if spec.nullable and not keep else strategy


@st.composite
def drafts(draw: st.DrawFn) -> DesignDraft:
    """Draw an example draft with every non-structural leaf replaced by a value its field accepts."""
    design = EXAMPLES[draw(st.sampled_from(sorted(EXAMPLES)))]()
    values = dict(draft_from_design(design).values)
    for pointer, current in sorted(values.items()):
        values[pointer] = draw(_leaf(field_for(pointer, values), current))
    return DesignDraft(topology=design.topology, values=values)


@pytest.mark.req("REQ-F-37")
@given(draft=drafts())
def test_random_designs_round_trip_exactly(draft):
    """Defect caught: a field dropped, an int turned float or an enum left a string on the way through JSON."""
    design = parse_draft(draft)
    assert not isinstance(design, DraftIncomplete), design
    assert design_from_json(design.topology, to_json(design)) == design
    assert parse_draft(draft_from_design(design)) == design
