"""F14-1 (V3-01 union ruling): 1000 seeded arbitrary-value drafts per generator never raise and never hide a NaN.

PR-05 draws 20 spiral drafts on the commit profile. This draws 1000 per topology from a fixed seed, built as
`mutated_drafts` builds them: one to three leaves of the topology's packaged example set to arbitrary JSON values.
"""

import math
from collections.abc import Iterator

import numpy as np
import pytest

from embodic.api import compute, outcome_to_json
from embodic.io.examples import load_example
from embodic.model.draft import DesignDraft, DraftIncomplete, draft_from_design, parse_draft
from embodic.model.provenance import derive_provenance
from embodic.model.schema import JsonValue
from embodic.results import load_registry

REGISTRY = load_registry()
SEED = 20261017
DRAFTS = 1000
EXAMPLES = {
    "spiral": "spiral_12c16p_default",
    "serpentine": "serpentine_16p_example",
    "wave": "wave_16p_example",
}
NON_FINITE_CODE = "RANGE_NON_FINITE_RESULT"
INTERNAL_PREFIX = "INTERNAL_"


def _any_json(rng: np.random.Generator) -> JsonValue:
    """Draw one value of the kinds `ANY_JSON` (tests/unit/property/strategies.py) covers."""
    match int(rng.integers(0, 7)):
        case 0:
            return None
        case 1:
            return bool(rng.integers(0, 2))
        case 2:
            return int(rng.integers(-1000, 1001))
        case 3:
            return float(rng.choice([math.nan, math.inf, -math.inf, 1e300, -1e300, 5e-324, 1.5e-164]))
        case 4:
            return float(rng.uniform(-1000.0, 1000.0))
        case 5:
            return "".join(chr(int(c)) for c in rng.integers(32, 127, size=int(rng.integers(0, 7))))
        case _:
            return [int(i) for i in rng.integers(-3, 4, size=int(rng.integers(0, 4)))]


def _mutated_drafts(example_id: str) -> Iterator[DesignDraft]:
    base = draft_from_design(load_example(example_id)[1])
    rng = np.random.default_rng(SEED)
    pointers = sorted(base.values)
    for _ in range(DRAFTS):
        values = dict(base.values)
        for pointer in rng.choice(pointers, size=int(rng.integers(1, 4)), replace=False):
            values[str(pointer)] = _any_json(rng)
        yield DesignDraft(topology=base.topology, values=values)


def _is_internal(code: str) -> bool:
    return code.startswith(INTERNAL_PREFIX)


def _changed(draft: DesignDraft, topology: str) -> dict[str, JsonValue]:
    """Return the leaves of ``draft`` that differ from the packaged example, so a failure names its cause."""
    base = draft_from_design(load_example(EXAMPLES[topology])[1]).values
    return {pointer: value for pointer, value in draft.values.items() if base.get(pointer) != value}


def _non_finite_quantities(data: object, quantity: str | None = None) -> Iterator[str | None]:
    """Yield the quantity of the nearest traceable around each non-finite tag, or None when no traceable holds it."""
    if isinstance(data, dict):
        if set(data) == {"$f"}:
            yield quantity
        enclosing = data["quantity"] if isinstance(data.get("quantity"), str) else quantity
        for value in data.values():
            yield from _non_finite_quantities(value, enclosing)
    elif isinstance(data, list):
        for value in data:
            yield from _non_finite_quantities(value, quantity)


@pytest.mark.req("REQ-F-14")
@pytest.mark.slow
@pytest.mark.parametrize(
    "topology",
    ["spiral", "serpentine", "wave"],
)
def test_f14_1_seeded_drafts_return_an_outcome_without_internal_errors_or_unnamed_non_finite_numbers(topology):
    """Catches an exception or a silent NaN on serpentine or wave input, which PR-05 draws only for spiral."""
    computed = 0
    problems: list[tuple[int, str, object]] = []
    for index, draft in enumerate(_mutated_drafts(EXAMPLES[topology])):
        parsed = parse_draft(draft)
        if isinstance(parsed, DraftIncomplete):
            assert parsed.missing or parsed.issues
            continue
        outcome = compute(parsed, derive_provenance(parsed, None, ()), registry=REGISTRY)
        assert outcome is not None
        computed += 1
        problems += [(index, i.code, _changed(draft, topology)) for i in outcome.issues if _is_internal(i.code)]
        named = {i.value for i in outcome.issues if i.code == NON_FINITE_CODE}
        problems += [
            (index, "UNNAMED_NON_FINITE", (q, _changed(draft, topology)))
            for q in _non_finite_quantities(outcome_to_json(outcome))
            if q not in named
        ]
    assert computed > 0, "no draft of the seed reached compute"
    assert problems == []
