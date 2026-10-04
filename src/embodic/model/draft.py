"""The editable draft of the new-design flow and its single conversion to a design (ADR-0010 decision 1, D-014)."""

import re
import types
from collections.abc import Mapping
from dataclasses import dataclass

from embodic.errors import IssueCategory, ValidationIssue
from embodic.model.design import DesignParameters
from embodic.model.fields import FIELD_BY_KEY, FIELDS, field_for, field_specs
from embodic.model.schema import JsonValue, ValueType, design_from_json, design_values, pattern_of, resolve, unflatten
from embodic.model.validate import check_value, issue
from embodic.model.vocabulary import TopologyKind

_FORM_ORDER: Mapping[str, int] = types.MappingProxyType(
    {spec.pointer: n for n, spec in reversed(list(enumerate(FIELDS)))}
)
_CONTAINER_TYPES = (ValueType.GROUP, ValueType.LIST)


@dataclass(frozen=True, slots=True, kw_only=True)
class DesignDraft:
    """What the form edits. Values may be missing; nothing is computed from a draft (D-014)."""

    topology: TopologyKind
    values: Mapping[str, JsonValue]  # pointer -> value; absent pointer = missing


@dataclass(frozen=True, slots=True, kw_only=True)
class DraftIncomplete:
    """Why a draft is not a design yet: required pointers without a value and issues of the values present."""

    missing: tuple[str, ...]  # pointers of required fields without a value, in form order
    issues: tuple[ValidationIssue, ...]


def _conditional(pointer: str, topology: TopologyKind) -> bool:
    """Return True for a field under a list, an optional group or a tagged union (it applies only once chosen)."""
    segments = pointer.split("/")
    for depth in range(2, len(segments)):
        ancestor = "/".join(segments[:depth])
        spec = FIELD_BY_KEY.get(ancestor)
        if spec is not None and spec.value_type in _CONTAINER_TYPES:
            return True
        tags = (FIELD_BY_KEY.get(f"{ancestor}/kind"), FIELD_BY_KEY.get(f"{ancestor}/shape"))
        if any(tag is not None and topology in tag.topologies and tag.pointer != pointer for tag in tags):
            return True
    return False


def blank_draft(topology: TopologyKind) -> DesignDraft:
    """Return a draft with required fields absent and always-applicable optional fields at their neutral value."""
    values = {
        spec.pointer: spec.neutral_value
        for spec in field_specs(topology)
        if not spec.required and spec.variant is None and not _conditional(spec.pointer, topology)
    }
    return DesignDraft(topology=topology, values=values)


def _form_key(pointer: str) -> tuple[int, list[int | str]]:
    natural = [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", pointer)]
    return _FORM_ORDER.get(pattern_of(pointer), len(_FORM_ORDER)), natural


def parse_draft(draft: DesignDraft) -> DesignParameters | DraftIncomplete:
    """Return the design once every required field has a valid value; otherwise what is missing or invalid.

    Pointers that do not apply to the chosen topology, variants or list items are ignored, so values typed for another
    topology survive a topology switch.
    """
    resolution = resolve(draft.topology, draft.values)
    issues = [issue("INVALID_LIST_SHAPE", [pointer]) for pointer in resolution.malformed]
    for pointer in resolution.active:
        issues.extend(check_value(field_for(pointer, draft.values), pointer, draft.values[pointer]))
    blocking = any(found.category is IssueCategory.INVALID for found in issues)
    if resolution.missing or blocking:
        missing = tuple(sorted(resolution.missing, key=_form_key))
        return DraftIncomplete(missing=missing, issues=tuple(issues))
    data = unflatten({pointer: draft.values[pointer] for pointer in resolution.active})
    return design_from_json(draft.topology, data)


def draft_from_design(design: DesignParameters) -> DesignDraft:
    """Return the draft holding every input value of a design."""
    return DesignDraft(topology=design.topology, values=design_values(design))
