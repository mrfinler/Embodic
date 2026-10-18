"""Traceable results: value, unit, equations, evidence, badge and the separate assumed-inputs tag (ADR-0003, D-007).

`traced()` is the only way the engine should build a computed result. Code declares EQ-IDs; evidence IDs, assumptions
and the badge come from the registry. Inputs build the tag and never the badge.
"""

import dataclasses
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Generic, Literal, Protocol, TypeAlias, TypeVar

from embodic.model.fields import FieldKind
from embodic.model.provenance import Provenance
from embodic.model.schema import pattern_of
from embodic.results.formatting import format_quantity
from embodic.results.registry import Assumption, EquationEntry, Registry, Tolerance, ValidityCheckSpec
from embodic.results.status import (
    ChainLink,
    MetricBound,
    Status,
    ValidityEffect,
    ValidityFlag,
    combine_status,
    derive_badge,
)
from embodic.units import Unit

T = TypeVar("T")
KindTag: TypeAlias = Literal["computed", "input", "derived", "count"]
AssumedReason: TypeAlias = Literal["example", "unmeasured_property", "registry_constant", "equation_assumption"]
CONSTANT_PREFIX = "constant:"
RESULT_PREFIX = "result:"


class Chained(Protocol):
    """Anything a result can be built from: a Traceable, or an Intermediate for a value that is not reported."""

    @property
    def eq_ids(self) -> tuple[str, ...]:
        """Return the chain: own equations first, then the chains of what it was built from."""
        ...


@dataclass(frozen=True, slots=True)
class Intermediate:
    """The chain of a value a result is built from that is not a Traceable, such as a flux-linkage array."""

    eq_ids: tuple[str, ...]


def chain(eq_ids: Sequence[str], built_from: Sequence[Chained]) -> tuple[str, ...]:
    """Return own EQ-IDs first, then each source's chain in order, each EQ-ID once (interfaces.md, result chain)."""
    return tuple(dict.fromkeys([*eq_ids, *(eq_id for source in built_from for eq_id in source.eq_ids)]))


def intermediate(*eq_ids: str, built_from: Sequence[Chained] = ()) -> Intermediate:
    """Name the equations of an unreported value once, where it is produced, for every result built from it."""
    return Intermediate(chain(eq_ids, built_from))


@dataclass(frozen=True, slots=True, kw_only=True)
class InputRef:
    """One input a calculation used, with where its value came from."""

    pointer: str  # JSON pointer or "result:<quantity>" or "constant:<name>"
    value: float | int | str
    unit: Unit | None
    provenance: Provenance | None  # None for result references and registry constants
    kind: FieldKind | None
    label: Status | None  # ASSUMPTION for unmeasured property inputs; constant's EV status for registry constants


@dataclass(frozen=True, slots=True, kw_only=True)
class AssumedInput:
    """One entry of the "n assumed inputs" tag."""

    item: str
    value_text: str
    reason: AssumedReason
    label: Status
    dominant: bool


@dataclass(frozen=True, slots=True, kw_only=True)
class Traceable(Generic[T]):
    """A computed quantity and everything needed to say how far to trust it."""

    quantity: str
    value: T
    unit: Unit
    eq_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    kind_tag: KindTag = "computed"
    assumptions: tuple[Assumption, ...] = ()
    inputs: tuple[InputRef, ...] = ()
    assumed_inputs: tuple[AssumedInput, ...] = ()
    validity: tuple[ValidityFlag, ...] = ()
    tolerance: Tolerance | None = None
    status: Status
    status_reasons: tuple[str, ...] = ()
    label: str | None = None  # "estimate" / "guideline (unverified)"

    def how_computed(self) -> str:
        """Return the plain-text "How was this computed" disclosure (REQ-T-13), one fact per line."""
        lines = [
            f"Status: {self.status} ({'; '.join(self.status_reasons)})",
            f"Equations: {', '.join(self.eq_ids) or self.kind_tag}",
            f"Evidence: {', '.join(self.evidence_ids) or 'none listed'}",
            "Inputs:",
            *(f"  {i.pointer} = {_value_text(i)} ({i.provenance or 'registry'})" for i in self.inputs),
            f"Assumed inputs ({len(self.assumed_inputs)}):",
            *(f"  {a.item} {a.value_text}".rstrip() + f" [{a.label}]" for a in self.assumed_inputs),
            "Validity:",
            *(f"  {f.code}: {f.message}" for f in self.validity),
        ]
        if self.tolerance is not None:
            lines.append(f"Tolerance: {self.tolerance.against} ({self.tolerance.source_ref})")
        if self.label is not None:
            lines.append(f"Label: {self.label}")
        return "\n".join(lines)


def traced(
    quantity: str,
    value: T,
    unit: Unit,
    *,
    eq_ids: Sequence[str],
    inputs: Sequence[InputRef],
    registry: Registry,
    validity: Sequence[ValidityFlag] = (),
    kind_tag: KindTag = "computed",
    built_from: Sequence[Chained] = (),
) -> Traceable[T]:
    """Badge = weakest(equation status, test state, validity cap). Inputs build the tag only (D-007).

    `eq_ids` are the result's own equations; the first gives the tolerance. The chain appends the chain of every
    result or intermediate in `built_from`, so the badge covers what the value was computed from (D-058d). `inputs`
    lists every input the calculation used, including those reached through intermediate results, because the tag of
    a result covers its whole chain (ADR-0003 decision 3).
    """
    if kind_tag == "computed" and not eq_ids:
        raise ValueError(f"computed result {quantity!r} needs at least one EQ-ID")
    full_chain = chain(eq_ids, built_from)
    entries = [registry.equation(eq_id) for eq_id in full_chain]
    status, reasons = derive_badge([_link(e, registry) for e in entries], validity)
    assumptions = _unique_assumptions(entries, validity)
    return Traceable(
        quantity=quantity,
        value=value,
        unit=unit,
        eq_ids=full_chain,
        evidence_ids=tuple(dict.fromkeys(ev for e in entries for ev in e.sources)),
        kind_tag=kind_tag,
        assumptions=assumptions,
        inputs=tuple(inputs),
        assumed_inputs=assumed_inputs_tag(inputs, assumptions, validity),
        validity=tuple(validity),
        tolerance=entries[0].tolerance if entries else None,
        status=status,
        status_reasons=reasons,
        label=next((e.label for e in entries if e.label is not None), None),
    )


def evaluate_validity(check: ValidityCheckSpec, eq_id: str, metric: float) -> ValidityFlag:
    """Grade a metric against its check: above the threshold caps the badge, at or below adds a one-sided add-on."""
    capped = not metric <= check.threshold  # a NaN metric cannot show that the limit holds
    return ValidityFlag(
        code=check.id,
        message=f"{check.name}: {format_quantity(metric, Unit.ONE)} against the limit "
        f"{format_quantity(check.threshold, Unit.ONE)} ({check.threshold_status})",
        eq_id=eq_id,
        effect=ValidityEffect.CAP if capped else ValidityEffect.LIMITATION,
        metric=metric,
        metric_bound=check.metric_bound,
        one_sided_addon=None if capped else metric,
        calibration_status=check.calibration_status,
        transfer_status=check.transfer_status,
        threshold_status=check.threshold_status,
    )


def traced_validity_metric(
    quantity: str,
    check: ValidityCheckSpec,
    eq_id: str,
    metric: float,
    *,
    inputs: Sequence[InputRef],
    registry: Registry,
) -> Traceable[float]:
    """Trace a validity metric such as EC-05's e_edge (REQ-T-16).

    Its badge is the weakest of its equation's badge, the calibration status and the transfer status. The threshold
    decides the cap on other results, not the trust in the metric, so a metric above its limit keeps its own badge.
    """
    flag = evaluate_validity(check, eq_id, metric)
    base = traced(quantity, metric, Unit.ONE, eq_ids=(eq_id,), inputs=inputs, registry=registry, validity=(flag,))
    status = combine_status(_uncapped_badge(eq_id, registry), check.calibration_status, check.transfer_status)
    reasons = (
        *(r for r in base.status_reasons if not r.endswith("validity limit exceeded")),
        f"{check.id} calibration {check.calibration_status}",
        f"{check.id} transfer to this design {check.transfer_status}",
    )
    label = "lower bound" if check.metric_bound is MetricBound.LOWER_BOUND else base.label
    return dataclasses.replace(base, status=status, status_reasons=reasons, label=label)


def assumed_inputs_tag(
    inputs: Sequence[InputRef], assumptions: Sequence[Assumption], validity: Sequence[ValidityFlag]
) -> tuple[AssumedInput, ...]:
    """Build the "n assumed inputs" tag, dominant entries first (ADR-0003 decision 3, ADR-0010 decision 6).

    Listed: example-valued inputs, property inputs not marked measured, registry constants, and the equation-level
    assumptions of the chain. A measured input retires the assumption whose `fields` name it. An assumption whose
    field is among the inputs is shown once, as that input, marked dominant.
    """
    measured = {pattern_of(i.pointer) for i in inputs if i.provenance is Provenance.MEASURED}
    used = {pattern_of(i.pointer) for i in inputs}
    active = [a for a in assumptions if not measured.intersection(a.fields)]
    dominant_fields = {f for a in active for f in a.fields}
    tag = [
        AssumedInput(
            item=i.pointer,
            value_text=_value_text(i),
            reason=reason,
            label=i.label or Status.ASSUMPTION,
            dominant=pattern_of(i.pointer) in dominant_fields,
        )
        for i in inputs
        if (reason := _reason(i)) is not None
    ]
    tag += [
        AssumedInput(item=a.text, value_text="", reason="equation_assumption", label=a.status, dominant=True)
        for a in active
        if not used.intersection(a.fields)
    ]
    return tuple(sorted(tag, key=lambda entry: not entry.dominant))


def _reason(i: InputRef) -> AssumedReason | None:
    if i.provenance is Provenance.MEASURED or i.pointer.startswith(RESULT_PREFIX):
        return None
    if i.pointer.startswith(CONSTANT_PREFIX):
        return "registry_constant"
    if i.kind is FieldKind.PROPERTY:
        return "unmeasured_property"
    if i.provenance is Provenance.EXAMPLE:
        return "example"
    return None


def _value_text(i: InputRef) -> str:
    if isinstance(i.value, bool) or not isinstance(i.value, int | float):
        return str(i.value)
    return format_quantity(float(i.value), i.unit or Unit.ONE)


def _link(entry: EquationEntry, registry: Registry) -> ChainLink:
    return ChainLink(
        eq_id=entry.id, gate=entry.gate, evidence=entry.status, tests_passed=registry.tests_passed(entry.id)
    )


def _uncapped_badge(eq_id: str, registry: Registry) -> Status:
    return derive_badge([_link(registry.equation(eq_id), registry)], ())[0]


def _unique_assumptions(entries: Sequence[EquationEntry], validity: Sequence[ValidityFlag]) -> tuple[Assumption, ...]:
    """Chain assumptions by text, then one transfer assumption per check that carries a transfer status."""
    by_text = {a.text: a for e in entries for a in e.assumptions}
    transfers = [
        Assumption(
            id=f"{flag.code}/transfer",
            text=f"{flag.code} calibration transferred to this rotor",
            status=flag.transfer_status,
            source_ref=flag.eq_id,
        )
        for flag in validity
        if flag.transfer_status is not None
    ]
    return (*by_text.values(), *transfers)
