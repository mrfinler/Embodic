"""Equation and evidence registries, loaded once from the packaged copies and frozen (interfaces.md section 3).

`tools/sync_registry.py` copies Agent 2's `equation_registry.json` and Agent 5's `evidence_register.json` into
`resources/evidence`. The loader is the boundary where that JSON becomes typed records. A malformed file raises
`RegistryFormatError` (a packaging defect that tests catch). A gap between the two registries, or a field the contract
types but the file only describes in prose, becomes a WARNING issue in `Registry.issues` and the weakest value is used.
"""

import json
import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, TypeVar

from embodic.errors import IssueCategory, Severity, ValidationIssue, message_for
from embodic.model.vocabulary import TopologyKind
from embodic.paths import resource_root
from embodic.results.status import GateVerdict, MetricBound, Status
from embodic.units import Unit

EQUATIONS_FILE = "equations.v1.json"
EVIDENCE_FILE = "evidence.v1.json"
MANIFEST_FILE = "manifest.v1.json"
_STATUS_PREFIX = re.compile(r"\s*([a-z ]+?)\s*(?::|$)")
_Entry = TypeVar("_Entry", "EquationEntry", "EvidenceEntry")
_Value = TypeVar("_Value")
_STATUS_VALUES = frozenset(s.value for s in Status)
_TOPOLOGY_VALUES = frozenset(t.value for t in TopologyKind)
_UNIT_VALUES = frozenset(u.value for u in Unit)


class RegistryFormatError(ValueError):
    """A packaged registry file does not have the shape the loader reads."""


@dataclass(frozen=True, slots=True, kw_only=True)
class Tolerance:
    """Accuracy claim of an equation; registry v1 states it as text only, so the numbers stay None."""

    relative: float | None
    absolute: float | None
    against: str
    source_ref: str


@dataclass(frozen=True, slots=True, kw_only=True)
class Assumption:
    """An equation-level assumption, listed in every result tag whose chain contains the equation."""

    id: str
    text: str
    status: Status
    source_ref: str | None = None
    fields: tuple[str, ...] = ()  # field patterns whose measured value retires this assumption (UT-RES-06)


@dataclass(frozen=True, slots=True, kw_only=True)
class ValidityCheckSpec:
    """Registry `validity_checks` entry (Agent 2 owns the content). DEF-23 adds the four status/bound fields."""

    id: str
    name: str
    metric: str
    parameters: Mapping[str, float | str]
    basis: str
    rule: str
    threshold: float
    metric_bound: MetricBound
    calibration_status: Status
    transfer_status: Status
    threshold_status: Status
    independent_oracles: tuple[str, ...]
    dependent_oracles: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class RegistryConstant:
    """A material or physical constant with its evidence."""

    name: str
    value: float
    unit: Unit
    source: str | None  # EV-ID
    status: Status


@dataclass(frozen=True, slots=True, kw_only=True)
class EquationEntry:
    """One equation of the registry."""

    id: str
    name: str
    formula: str
    gate: GateVerdict
    status: Status  # evidence status of the equation
    sources: tuple[str, ...]
    tolerance: Tolerance | None
    dominant_assumptions: tuple[str, ...]
    validity_checks: tuple[ValidityCheckSpec, ...]
    tests: tuple[str, ...]
    implementation: str | None
    constants: tuple[RegistryConstant, ...]
    label: str | None
    applies_to: frozenset[TopologyKind]
    assumptions: tuple[Assumption, ...]  # dominant_assumptions as records, in registry order


@dataclass(frozen=True, slots=True, kw_only=True)
class EvidenceEntry:
    """One claim of the evidence register."""

    id: str
    claim: str
    document: str
    location: str
    status: Status


@dataclass(frozen=True, slots=True, kw_only=True)
class Registry:
    """Both registries, cross-checked; read-only after `load_registry`."""

    version: str
    equations: Mapping[str, EquationEntry]
    evidence: Mapping[str, EvidenceEntry]
    passed_tests: frozenset[str]  # test IDs that passed in this build; empty in a fresh install
    issues: tuple[ValidationIssue, ...] = ()

    def equation(self, eq_id: str) -> EquationEntry:
        """Return an equation; raise KeyError for an unknown ID (code declares EQ-IDs, so this is a defect)."""
        return self.equations[eq_id]

    def constant(self, name: str) -> RegistryConstant:
        """Return a registry constant; raise KeyError when the registry does not list it."""
        for entry in self.equations.values():
            for constant in entry.constants:
                if constant.name == name:
                    return constant
        raise KeyError(name)

    def tests_passed(self, eq_id: str) -> bool:
        """Return True when the equation links at least one test and every linked test passed in this build."""
        tests = self.equation(eq_id).tests
        return bool(tests) and set(tests) <= self.passed_tests

    def test_state(self, eq_id: str) -> Status:
        """NOT_TESTED until every linked test passed in this build, else the equation status."""
        return self.equation(eq_id).status if self.tests_passed(eq_id) else Status.NOT_TESTED

    def equations_for(self, topology: TopologyKind) -> tuple[EquationEntry, ...]:
        """Return the equations that apply to a topology, in registry order."""
        return tuple(e for e in self.equations.values() if topology in e.applies_to)


def load_registry(root: Path | None = None) -> Registry:
    """Read resources/evidence/equations.v1.json and evidence.v1.json (packaged copies, tools/sync_registry.py)."""
    folder = (root if root is not None else resource_root()) / "evidence"
    equations, evidence, manifest = (
        json.loads((folder / name).read_text(encoding="utf-8"))
        for name in (EQUATIONS_FILE, EVIDENCE_FILE, MANIFEST_FILE)
    )
    hashes = [manifest["files"][name]["sha256"][:12] for name in (EQUATIONS_FILE, EVIDENCE_FILE)]
    return parse_registry(equations, evidence, version=f"v1+{hashes[0]}.{hashes[1]}")


def parse_registry(equations_json: Any, evidence_json: Any, *, version: str) -> Registry:
    """Turn the two registry documents into a frozen Registry; pure, so tests feed it fixtures."""
    issues: list[ValidationIssue] = []
    evidence = _unique((_parse_evidence(raw) for raw in _list(evidence_json, "entries")), "evidence")
    equations = _unique((_parse_equation(raw, issues) for raw in _list(equations_json, "equations")), "equation")
    for entry in equations.values():
        if not entry.sources:
            issues.append(_issue("INTERNAL_REGISTRY_EQUATION_UNSOURCED", f"/equations/{entry.id}/sources", entry.id))
        issues += [
            _issue("INTERNAL_REGISTRY_EVIDENCE_MISSING", f"/equations/{entry.id}/sources", ev_id)
            for ev_id in entry.sources
            if ev_id not in evidence
        ]
    return Registry(
        version=version,
        equations=MappingProxyType(equations),
        evidence=MappingProxyType(evidence),
        passed_tests=frozenset(),
        issues=tuple(issues),
    )


def _issue(code: str, pointer: str, value: str) -> ValidationIssue:
    return ValidationIssue(
        code=code,
        category=IssueCategory.INTERNAL,
        severity=Severity.WARNING,
        message=message_for(code),
        pointers=(pointer,),
        value=value,
    )


def _list(document: Any, key: str) -> list[Any]:
    items = document.get(key) if isinstance(document, dict) else None
    if not isinstance(items, list):
        raise RegistryFormatError(f"registry document has no list under {key!r}")
    return items


def _unique(entries: Iterable[_Entry], what: str) -> dict[str, _Entry]:
    by_id: dict[str, _Entry] = {}
    for entry in entries:
        if entry.id in by_id:
            raise RegistryFormatError(f"{what} ID {entry.id!r} appears twice")
        by_id[entry.id] = entry
    return by_id


def _status(text: Any, where: str) -> Status:
    try:
        return Status(text)
    except ValueError:
        raise RegistryFormatError(f"{where}: {text!r} is not a status label") from None


def _parse_evidence(raw: Any) -> EvidenceEntry:
    where = f"evidence {raw.get('id')!r}"
    try:
        return EvidenceEntry(
            id=raw["id"],
            claim=raw["claim"],
            document=raw["source"]["document"],
            location=raw["location"]["text"],
            status=_status(raw["status"], where),
        )
    except (KeyError, TypeError) as missing:
        raise RegistryFormatError(f"{where}: missing {missing}") from None


def _parse_equation(raw: Any, issues: list[ValidationIssue]) -> EquationEntry:
    eq_id = raw.get("id")
    where = f"equation {eq_id!r}"
    try:
        gate = GateVerdict(raw["gate_verdict"])
        tolerance = raw.get("tolerance")
        dominant = tuple(_assumption_text(a) for a in raw["dominant_assumptions"])
        return EquationEntry(
            id=eq_id,
            name=raw["name"],
            formula=raw["formula"],
            gate=gate,
            status=_status(raw["status"], where),
            sources=tuple(raw["sources"]),
            tolerance=_parse_tolerance(tolerance) if tolerance is not None else None,
            dominant_assumptions=dominant,
            validity_checks=tuple(_parse_check(eq_id, c, issues) for c in raw.get("validity_checks", ())),
            tests=tuple(raw["tests"]),
            implementation=raw.get("implementation"),
            constants=_parse_constants(eq_id, raw.get("constants", ()), issues),
            label=raw.get("label", "estimate" if gate is GateVerdict.CANNOT_VERIFY_YET else None),
            applies_to=frozenset(TopologyKind(t) for t in raw["applies_to"] if t in _TOPOLOGY_VALUES),
            assumptions=tuple(_parse_assumption(eq_id, n, a) for n, a in enumerate(raw["dominant_assumptions"], 1)),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise RegistryFormatError(f"{where}: {error!r}") from None


def _assumption_text(raw: Any) -> str:
    return raw if isinstance(raw, str) else raw["text"]


def _parse_assumption(eq_id: str, number: int, raw: Any) -> Assumption:
    """Read plain text (v1) or an object that adds `status` and the `fields` a measurement retires."""
    if isinstance(raw, str):
        return Assumption(id=f"{eq_id}/A{number}", text=raw, status=Status.ASSUMPTION, source_ref=eq_id)
    return Assumption(
        id=f"{eq_id}/A{number}",
        text=raw["text"],
        status=_status(raw.get("status", Status.ASSUMPTION), f"{eq_id} assumption {number}"),
        source_ref=eq_id,
        fields=tuple(raw.get("fields", ())),
    )


def _parse_tolerance(raw: Any) -> Tolerance:
    """Typed keys when present; registry v1 gives `value` and `basis` as prose."""
    return Tolerance(
        relative=raw.get("relative"),
        absolute=raw.get("absolute"),
        against=raw.get("against", raw.get("value", "")),
        source_ref=raw.get("source_ref", raw.get("basis", "")),
    )


def _parse_constants(eq_id: str, raw: Sequence[Any], issues: list[ValidationIssue]) -> tuple[RegistryConstant, ...]:
    constants = []
    for item in raw:
        if item["unit"] not in _UNIT_VALUES:
            issues.append(_issue("INTERNAL_REGISTRY_UNIT_UNKNOWN", f"/equations/{eq_id}/constants", item["unit"]))
            continue
        constants.append(
            RegistryConstant(
                name=item["name"],
                value=float(item["value"]),
                unit=Unit(item["unit"]),
                source=item.get("source"),
                status=_status(item["status"], f"{eq_id} constant {item['name']!r}"),
            )
        )
    return tuple(constants)


def _leading_status(text: Any) -> Status | None:
    """Read a status label that opens a prose field ("assumption: scaling the decay length ...")."""
    match = _STATUS_PREFIX.match(text) if isinstance(text, str) else None
    return Status(match.group(1)) if match and match.group(1) in _STATUS_VALUES else None


def _parse_check(eq_id: str, raw: Any, issues: list[ValidationIssue]) -> ValidityCheckSpec:
    """Read the DEF-23 fields; a field the file lacks or gives as prose costs one issue naming it."""
    check_id = raw["id"]
    pointer = f"/equations/{eq_id}/validity_checks/{check_id}"

    def untyped(name: str, value: _Value) -> _Value:
        issues.append(_issue("INTERNAL_REGISTRY_FIELD_UNTYPED", pointer, name))
        return value

    def status_field(name: str, *prose_fields: str) -> Status:
        if raw.get(name) in _STATUS_VALUES:
            return Status(raw[name])
        found = next(filter(None, (_leading_status(raw.get(key)) for key in (name, *prose_fields))), None)
        return untyped(name, found if found is not None else Status.UNRESOLVED)

    def typed(name: str, parse: Callable[[Any], _Value], weakest: _Value) -> _Value:
        return parse(raw[name]) if name in raw else untyped(name, weakest)

    threshold = raw.get("threshold")
    return ValidityCheckSpec(
        id=check_id,
        name=raw["name"],
        metric=raw["metric"],
        parameters=MappingProxyType(dict(raw.get("parameters", {}))),
        basis=raw["basis"],
        rule=raw["rule"],
        # Without a typed threshold every positive metric caps: the conservative reading of a missing limit.
        threshold=float(threshold) if isinstance(threshold, int | float) else untyped("threshold", 0.0),
        metric_bound=typed("metric_bound", MetricBound, MetricBound.ESTIMATE),
        calibration_status=status_field("calibration_status"),
        transfer_status=status_field("transfer_status"),
        threshold_status=status_field("threshold_status", "threshold_basis"),
        independent_oracles=typed("independent_oracles", tuple, ()),
        dependent_oracles=typed("dependent_oracles", tuple, ()),
    )
