"""DEF-UE18-01 (fix_wave_f2.md A.5): an EMF-derived result carries the equations of the intermediate results it uses.

The D08 example (resources/examples/spiral_12c10p_d08.embodic.json) is computed through the public compute() stage.
Ke is formed from the phase EMF phasors (EQ-07) of the path flux linkages (EQ-06) in the EQ-05 field. Every result
derived from that Ke must say so in `eq_ids`, because the badge is the weakest equation of the chain.
"""

import dataclasses
from collections.abc import Iterator

import pytest

from embodic.api import compute
from embodic.io.examples import load_example
from embodic.io.project import project_from_example, project_provenance
from embodic.results import Registry, Status, Traceable, load_registry

pytestmark = pytest.mark.req("REQ-T-05")
D08 = "spiral_12c10p_d08"
FLUX_CHAIN = {"EQ-05", "EQ-07"}  # what a result that holds EQ-06 must also hold (fix_wave_f2.md A.5, test spec)
DEF_UE18_01_RESULTS = ("ke_line", "kt", "kv", "torque", "output_power")  # fix_wave_f2.md A.4, A.5: shown verified by V3


def _traceables(value: object) -> Iterator[Traceable]:
    if isinstance(value, Traceable):
        yield value
    elif dataclasses.is_dataclass(value) and not isinstance(value, type):
        for field in dataclasses.fields(value):
            yield from _traceables(getattr(value, field.name))
    elif isinstance(value, tuple):
        for item in value:
            yield from _traceables(item)


def _d08(registry: Registry) -> list[Traceable]:
    project = project_from_example(load_example(D08))
    outcome = compute(project.design, project_provenance(project), registry=registry)
    assert outcome is not None and outcome.analysis is not None
    return list(_traceables(outcome.analysis))


def _all_tests_passed(registry: Registry) -> Registry:
    linked = frozenset(t for e in registry.equations.values() for t in e.tests)
    return dataclasses.replace(registry, passed_tests=linked)


def _eq06_verified_all_passed() -> Registry:
    """Return the registry once OR-07 passes: EQ-06 `verified`, every linked test passed (fix_wave_f2.md A.3, V3)."""
    registry = _all_tests_passed(load_registry())
    eq06 = dataclasses.replace(registry.equation("EQ-06"), status=Status.VERIFIED)
    return dataclasses.replace(registry, equations={**registry.equations, "EQ-06": eq06})


def test_every_result_holding_eq06_also_holds_eq05_and_eq07() -> None:
    """Defect caught: DEF-UE18-01, a result with EQ-06 in its chain that omits the field model or the phase assembly."""
    with_eq06 = [t for t in _d08(load_registry()) if "EQ-06" in t.eq_ids]
    assert with_eq06
    missing = {t.quantity: sorted(FLUX_CHAIN - set(t.eq_ids)) for t in with_eq06 if FLUX_CHAIN - set(t.eq_ids)}
    assert missing == {}


def test_torque_is_not_verified_while_eq05_is_inferred() -> None:
    """Defect caught: a `verified` torque, kt, kv, ke_line or output_power badge that rests on an `inferred` field.

    The registry is the V3 state of A.4: EQ-06 `verified` and every linked test passed. EQ-05 stays `inferred`, so no
    result that uses the EQ-05 field may read `verified`.
    """
    registry = _eq06_verified_all_passed()
    assert registry.equation("EQ-05").status is Status.INFERRED
    results = {t.quantity: t for t in _d08(registry)}
    verified = [q for q in DEF_UE18_01_RESULTS if results[q].status is Status.VERIFIED]
    assert verified == []
    assert results["torque"].status is Status.INFERRED
