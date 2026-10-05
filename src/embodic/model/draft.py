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


_PAIRS = "/winding/layers/pairs"
_SERIES_GROUPS = "/winding/layers/series_groups"
_PAIR_SETTINGS = ("rotation_rad", "phases")


def _copper_names(values: Mapping[str, JsonValue]) -> list[JsonValue]:
    names: list[JsonValue] = []
    position = 0
    while f"/stackup/layers/{position}/kind" in values:
        if values[f"/stackup/layers/{position}/kind"] == "copper":
            names.append(values.get(f"/stackup/layers/{position}/name"))
        position += 1
    return names


def derive_layer_pairs(draft: DesignDraft) -> DesignDraft:
    """Return a spiral draft whose pair list follows its copper layers (D-024); other topologies are returned as is.

    Pair k joins copper layers 2k and 2k + 1 in stack order, so an odd count leaves the last layer unpaired. A pair that
    still exists keeps every value the draft holds for it; a new pair starts at the documented defaults and in its own
    series group. Pairs beyond the copper count and their group entries are removed.
    """
    if draft.topology is not TopologyKind.SPIRAL:
        return draft
    copper = _copper_names(draft.values)
    values = {p: v for p, v in draft.values.items() if not p.startswith(_PAIRS) and p != _SERIES_GROUPS}
    indices: list[JsonValue] = []
    for k in range(len(copper) // 2):
        derived: dict[str, JsonValue] = {"index": k, "layer_in": copper[2 * k], "layer_out": copper[2 * k + 1]}
        derived |= {leaf: FIELD_BY_KEY[f"{_PAIRS}/*/{leaf}"].neutral_value for leaf in _PAIR_SETTINGS}
        for leaf, value in derived.items():
            pointer = f"{_PAIRS}/{k}/{leaf}"
            values[pointer] = draft.values.get(pointer, value)
        indices.append(values[f"{_PAIRS}/{k}/index"])
    if indices:
        values[_SERIES_GROUPS] = _series_groups(draft.values.get(_SERIES_GROUPS), indices)
    return DesignDraft(topology=draft.topology, values=values)


def _series_groups(old: JsonValue, indices: list[JsonValue]) -> list[JsonValue]:
    """Keep the draft's groups for pairs that still exist; every other pair goes in its own series group."""
    groups: list[JsonValue] = []
    grouped: list[JsonValue] = []
    for group in old if isinstance(old, list) else []:
        kept = [i for i in group if i in indices] if isinstance(group, list) else []
        if kept:
            groups.append(kept)
            grouped.extend(kept)
    groups.extend([[i] for i in indices if i not in grouped])
    return groups
