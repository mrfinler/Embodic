"""Registry builders for the results tests: raw packaged JSON, EC-05 in its contract shape, all tests passed."""

import dataclasses
import json

from embodic.paths import resource_root
from embodic.results.registry import Registry, parse_registry

# requirements.md section 6 (DEF-23 closure): the typed EC-05 fields Agent 2 is to add. Registry v1 has them as prose.
EC05_CONTRACT_FIELDS = {
    "threshold": 0.10,
    "metric_bound": "lower_bound",
    "calibration_status": "inferred",
    "transfer_status": "assumption",
    "threshold_status": "assumption",
    "independent_oracles": ["OR-01"],
    "dependent_oracles": ["OR-07", "OR-08"],
}


def raw_documents() -> tuple[dict, dict]:
    """Return fresh copies of the packaged equation and evidence JSON."""
    folder = resource_root() / "evidence"
    return tuple(
        json.loads((folder / name).read_text(encoding="utf-8")) for name in ("equations.v1.json", "evidence.v1.json")
    )


def with_all_tests_passed(registry: Registry) -> Registry:
    """Return the registry as it would be in a build where every linked test passed."""
    return dataclasses.replace(
        registry, passed_tests=frozenset(t for e in registry.equations.values() for t in e.tests)
    )


def contract_shaped() -> Registry:
    """Return the shipped registry with EC-05 carrying the typed DEF-23 fields of requirements.md section 6."""
    equations, evidence = raw_documents()
    eq05 = next(e for e in equations["equations"] if e["id"] == "EQ-05")
    eq05["validity_checks"][0].update(EC05_CONTRACT_FIELDS)
    return parse_registry(equations, evidence, version="test")
