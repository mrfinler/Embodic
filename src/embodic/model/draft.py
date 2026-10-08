"""The editable draft of the new-design flow and its single conversion to a design (ADR-0010 decision 1, D-014)."""

import itertools
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
_PAIR_LEAVES = ("index", "layer_in", "layer_out", *_PAIR_SETTINGS)


def _copper_names(values: Mapping[str, JsonValue]) -> list[JsonValue]:
    names: list[JsonValue] = []
    position = 0
    while f"/stackup/layers/{position}/kind" in values:
        if values[f"/stackup/layers/{position}/kind"] == "copper":
            names.append(values.get(f"/stackup/layers/{position}/name"))
        position += 1
    return names


def _listed_pairs(values: Mapping[str, JsonValue]) -> list[dict[str, JsonValue]]:
    """Return what the draft holds for each listed pair, by leaf name, in list order."""
    pairs: list[dict[str, JsonValue]] = []
    while f"{_PAIRS}/{len(pairs)}/layer_in" in values:
        base = f"{_PAIRS}/{len(pairs)}/"
        pairs.append({leaf: values[base + leaf] for leaf in _PAIR_LEAVES if base + leaf in values})
    return pairs


def _pair_indices(kept: list[dict[str, JsonValue]]) -> list[int]:
    """Give every pair an index: a kept pair keeps its own while no earlier pair holds it, the others take free ones."""
    held = [pair["index"] for pair in kept if isinstance(pair.get("index"), int)]
    free = (index for index in itertools.count() if index not in held)
    indices: list[int] = []
    for pair in kept:
        index = pair.get("index")
        indices.append(index if isinstance(index, int) and index not in indices else next(free))
    return indices


def derive_layer_pairs(draft: DesignDraft) -> DesignDraft:
    """Return a spiral draft whose pair list follows its copper layers (D-024); other topologies are returned as is.

    Pair k joins copper layers 2k and 2k + 1 in stack order, so an odd count leaves the last layer unpaired. A pair is
    identified by those two layer names, never by its list position (D-032b). The draft pair with the same names keeps
    its index, rotation, phases and series group. Any other pair starts at the documented defaults, in its own series
    group, with the lowest index that no kept pair holds. Draft pairs whose names the stack-up no longer yields are
    removed with their group entries.
    """
    if draft.topology is not TopologyKind.SPIRAL:
        return draft
    copper = _copper_names(draft.values)
    listed = _listed_pairs(draft.values)
    layers = [(copper[2 * k], copper[2 * k + 1]) for k in range(len(copper) // 2)]
    kept = [next((p for p in listed if (p["layer_in"], p.get("layer_out")) == names), {}) for names in layers]
    indices = _pair_indices(kept)
    values = {p: v for p, v in draft.values.items() if not p.startswith(_PAIRS) and p != _SERIES_GROUPS}
    for k, ((layer_in, layer_out), pair, index) in enumerate(zip(layers, kept, indices, strict=True)):
        derived: dict[str, JsonValue] = {"index": index, "layer_in": layer_in, "layer_out": layer_out}
        derived |= {leaf: pair.get(leaf, FIELD_BY_KEY[f"{_PAIRS}/*/{leaf}"].neutral_value) for leaf in _PAIR_SETTINGS}
        values |= {f"{_PAIRS}/{k}/{leaf}": value for leaf, value in derived.items()}
    if indices:
        retained = {index for index, pair in zip(indices, kept, strict=True) if pair.get("index") == index}
        values[_SERIES_GROUPS] = _series_groups(draft.values.get(_SERIES_GROUPS), retained, indices)
    return DesignDraft(topology=draft.topology, values=values)


def _series_groups(old: JsonValue, retained: set[int], indices: list[int]) -> list[JsonValue]:
    """Keep the draft's groups for the pairs it kept; every other pair goes in its own series group."""
    groups: list[JsonValue] = []
    grouped: list[JsonValue] = []
    for group in old if isinstance(old, list) else []:
        kept: list[JsonValue] = [i for i in group if i in retained] if isinstance(group, list) else []
        if kept:
            groups.append(kept)
            grouped.extend(kept)
    groups.extend([[i] for i in indices if i not in grouped])
    return groups
