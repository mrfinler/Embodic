"""Item 5: provenance truth table through compute(), expected values from the text of D-007 and D-023b.

D-007: the badge is the calculation's trust; provenance never changes it. D-023b: the "n assumed inputs" tag lists
example-valued inputs and property inputs not marked measured; a design input that is user-typed or at its default
is not listed. Subject: Ke_LL of the packaged D08 example, whose inputs hold one property and one design pointer.
Defects caught: a measured property still listed, a re-typed default that changes the badge, an example-valued
design input dropped from the tag.
"""

import pytest

from embodic.api import StageCache, compute
from embodic.io.examples import load_example
from embodic.model.provenance import DefaultValue, ExampleValue, MeasuredValue, UserValue

EXAMPLE = "spiral_12c10p_d08"
PROPERTY, DESIGN = "/rotor/remanence_t", "/rotor/air_gap_mm"
SOURCES = {
    "user": UserValue(),
    "example": ExampleValue(example_id=EXAMPLE),
    "default": DefaultValue(),
    "measured": MeasuredValue(source="example bench measurement (label: example)"),
}
LISTED = {
    (PROPERTY, "user"): True,
    (PROPERTY, "example"): True,
    (PROPERTY, "default"): True,
    (PROPERTY, "measured"): False,
    (DESIGN, "user"): False,
    (DESIGN, "example"): True,
    (DESIGN, "default"): False,
    (DESIGN, "measured"): False,
}
_CACHE = StageCache()


def _ke(pointer: str, source: str):
    _, design = load_example(EXAMPLE)
    outcome = compute(design, {pointer: SOURCES[source]}, cache=_CACHE)
    assert outcome is not None and outcome.analysis is not None
    return outcome.analysis.ke_line_peak_v_s_per_rad


@pytest.mark.parametrize(("pointer", "source"), list(LISTED))
def test_assumed_inputs_tag_follows_d023(pointer: str, source: str) -> None:
    """Each (kind, provenance) cell lists or omits the pointer as D-023b says."""
    items = [entry.item for entry in _ke(pointer, source).assumed_inputs]
    assert (pointer in items) is LISTED[(pointer, source)], items


def test_badge_and_value_do_not_depend_on_provenance() -> None:
    """Status and value are the same for all eight provenance cells (D-007)."""
    results = [_ke(pointer, source) for pointer, source in LISTED]
    assert len({(r.status, r.value) for r in results}) == 1, [(r.status, r.value) for r in results]
