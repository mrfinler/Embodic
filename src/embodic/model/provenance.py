"""Per-field provenance derived from values, origin and measurements (interfaces.md section 2.4, D-007, D-019).

The first matching rule gives a field's provenance: `measured` for a marked property field, `example` while the value
equals the origin example's, `default` while an optional field the origin holds no value for (a blank design, or a
pointer the example lacks) equals its neutral value, `user` otherwise.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal, TypeAlias

from embodic.errors import ValidationIssue
from embodic.model.design import DesignParameters
from embodic.model.fields import FieldKind, field_for
from embodic.model.schema import JsonValue, ValueType, design_values
from embodic.model.validate import issue


class Provenance(StrEnum):
    """Where a field's value came from."""

    USER = "user"
    EXAMPLE = "example"
    DEFAULT = "default"
    MEASURED = "measured"


@dataclass(frozen=True, slots=True, kw_only=True)
class UserValue:
    """Typed or changed by the user."""

    provenance: Literal[Provenance.USER] = Provenance.USER


@dataclass(frozen=True, slots=True, kw_only=True)
class ExampleValue:
    """Equal to the value in the origin example."""

    provenance: Literal[Provenance.EXAMPLE] = Provenance.EXAMPLE
    example_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class DefaultValue:
    """An optional field of a blank design still at its documented neutral value (D-019)."""

    provenance: Literal[Provenance.DEFAULT] = Provenance.DEFAULT


@dataclass(frozen=True, slots=True, kw_only=True)
class MeasuredValue:
    """A property field backed by a named measurement source."""

    provenance: Literal[Provenance.MEASURED] = Provenance.MEASURED
    source: str  # never empty: mark_measured refuses an empty source


FieldProvenance: TypeAlias = UserValue | ExampleValue | DefaultValue | MeasuredValue
ProvenanceMap: TypeAlias = Mapping[str, FieldProvenance]


@dataclass(frozen=True, slots=True, kw_only=True)
class ExampleRef:
    """The packaged example a design started from."""

    example_id: str  # file stem in resources/examples
    example_sha256: str  # of the example's canonical design JSON


@dataclass(frozen=True, slots=True, kw_only=True)
class Measurement:
    """A property field marked measured, with its source."""

    pointer: str
    source: str


def _measurable(pointer: str, values: Mapping[str, JsonValue]) -> bool:
    if pointer not in values:
        return False
    spec = field_for(pointer, values)
    return spec.kind is FieldKind.PROPERTY and spec.value_type is ValueType.FLOAT


def derive_provenance(
    design: DesignParameters,
    origin: tuple[ExampleRef, DesignParameters] | None,
    measurements: Sequence[Measurement],
) -> dict[str, FieldProvenance]:
    """Return the provenance of every concrete pointer; rule 3 applies where the origin holds no value (D-043a)."""
    values = design_values(design)
    origin_values = design_values(origin[1]) if origin is not None else {}
    sources = {m.pointer: m.source for m in measurements if _measurable(m.pointer, values) and m.source.strip()}
    derived: dict[str, FieldProvenance] = {}
    for pointer, value in values.items():
        spec = field_for(pointer, values)
        if pointer in sources:
            derived[pointer] = MeasuredValue(source=sources[pointer])
        elif origin is not None and pointer in origin_values and origin_values[pointer] == value:
            derived[pointer] = ExampleValue(example_id=origin[0].example_id)
        elif pointer not in origin_values and not spec.required and value == spec.neutral_value:
            derived[pointer] = DefaultValue()
        else:
            derived[pointer] = UserValue()
    return derived


def mark_measured(
    design: DesignParameters, measurements: Sequence[Measurement], pointer: str, source: str
) -> tuple[Measurement, ...] | ValidationIssue:
    """Record a measurement, or refuse it (INVALID_MEASURED_SOURCE_EMPTY, INVALID_MEASURED_DESIGN_FIELD)."""
    if not source.strip():
        return issue("INVALID_MEASURED_SOURCE_EMPTY", [pointer])
    if not _measurable(pointer, design_values(design)):
        return issue("INVALID_MEASURED_DESIGN_FIELD", [pointer])
    kept = tuple(m for m in measurements if m.pointer != pointer)
    return (*kept, Measurement(pointer=pointer, source=source.strip()))


def drop_stale_measurements(
    old: DesignParameters, new: DesignParameters, measurements: Sequence[Measurement]
) -> tuple[Measurement, ...]:
    """Keep only measurements whose field still holds the value it had when measured."""
    old_values, new_values = design_values(old), design_values(new)
    return tuple(
        m for m in measurements if m.pointer in new_values and old_values.get(m.pointer) == new_values[m.pointer]
    )
