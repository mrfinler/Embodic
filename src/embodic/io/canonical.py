"""The file form of a design: degrees under `_deg` names, canonical JSON and the design hash (interfaces.md 9.1).

The model stores radians under `_rad` names; the file stores degrees under `_deg` names. The renamed fields are the
`FIELDS` rows whose unit is `Unit.RAD`, so a new angle field converts without a code change here.
"""

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from embodic.model.design import DesignParameters
from embodic.model.draft import DesignDraft
from embodic.model.fields import FIELDS
from embodic.model.schema import JsonValue, flatten, pattern_of, to_json, unflatten
from embodic.model.vocabulary import TopologyKind
from embodic.units import Unit, deg_to_rad, rad_to_deg

_RAD_SUFFIX, _DEG_SUFFIX = "_rad", "_deg"
TOPOLOGY_POINTER = "/winding/kind"
RAD_PATTERNS = frozenset(spec.pointer for spec in FIELDS if spec.unit is Unit.RAD)


def _is_angle(model_pointer: str) -> bool:
    return pattern_of(model_pointer) in RAD_PATTERNS


def file_pointer(model_pointer: str) -> str:
    """Return the file name of a model pointer ("/rotor/magnet_offset_rad" -> "/rotor/magnet_offset_deg")."""
    return model_pointer[: -len(_RAD_SUFFIX)] + _DEG_SUFFIX if _is_angle(model_pointer) else model_pointer


def model_pointer(pointer: str) -> str:
    """Return the model name of a file pointer; the inverse of file_pointer."""
    if pointer.endswith(_DEG_SUFFIX):
        candidate = pointer[: -len(_DEG_SUFFIX)] + _RAD_SUFFIX
        if _is_angle(candidate):
            return candidate
    return pointer


def _convert(value: JsonValue, convert: Any) -> JsonValue:
    return convert(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else value


def to_file_values(values: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    """Map model pointers and radians to file pointers and degrees."""
    return {file_pointer(p): _convert(v, rad_to_deg) if _is_angle(p) else v for p, v in values.items()}


def to_model_values(values: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    """Map file pointers and degrees to model pointers and radians."""
    converted: dict[str, JsonValue] = {}
    for pointer, value in values.items():
        name = model_pointer(pointer)
        converted[name] = _convert(value, deg_to_rad) if name != pointer else value
    return converted


def design_document(design: DesignParameters) -> dict[str, JsonValue]:
    """Return the `design` object of a project file, constants included (`/winding/kind` names the topology)."""
    data = to_json(design)
    assert isinstance(data, dict)
    data.pop("schema_version")
    nested: dict[str, JsonValue] = unflatten(to_file_values(flatten(data)))
    return nested


def dumps_canonical(data: JsonValue) -> bytes:
    """Sorted keys, no whitespace, shortest round-trip float repr, UTF-8; NaN and infinity refused."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def canonical_json(design: DesignParameters) -> bytes:
    """Canonical JSON of the design in its file form."""
    return dumps_canonical(design_document(design))


def design_hash(design: DesignParameters) -> str:
    """SHA-256 over canonical_json(design), as "sha256:<hex>"."""
    return "sha256:" + hashlib.sha256(canonical_json(design)).hexdigest()


def draft_document(draft: DesignDraft) -> dict[str, JsonValue]:
    """Return the `design` object of a project file holding an incomplete draft."""
    nested: dict[str, JsonValue] = unflatten({**to_file_values(draft.values), TOPOLOGY_POINTER: draft.topology.value})
    return nested


def draft_from_document(design: Mapping[str, Any]) -> DesignDraft | None:
    """Read a file's `design` object into a draft (model names, radians); None without a known `/winding/kind`."""
    values = to_model_values(flatten(dict(design)))
    kind = values.pop(TOPOLOGY_POINTER, None)
    if kind not in {t.value for t in TopologyKind}:
        return None
    return DesignDraft(topology=TopologyKind(kind), values=values)
