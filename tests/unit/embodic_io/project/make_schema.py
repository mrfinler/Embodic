"""Write src/embodic/io/schema/project.v1.schema.json from FIELDS; rerunning gives the same bytes.

Run from the repository root: ``python -m tests.unit.embodic_io.project.make_schema``. The `design` object lists every
key of every topology in its file form (degrees under `_deg` names), so an added, removed or renamed field changes the
schema and fails UT-IO-03 until the schema version rule of interfaces.md 9.1 is followed. No key is required inside
`design`, because an incomplete draft is a valid file (D-014).
"""

import json
import re
from pathlib import Path
from typing import Any

from embodic.io.canonical import RAD_PATTERNS
from embodic.io.project import PROJECT_FORMAT
from embodic.model.fields import FIELDS, FieldKind, FieldSpec, Sign
from embodic.model.provenance import Provenance
from embodic.model.schema import LIST_ITEM, ValueType
from embodic.model.vocabulary import TopologyKind

SCHEMA_PATH = Path(__file__).resolve().parents[4] / "src" / "embodic" / "io" / "schema" / "project.v1.schema.json"
CONSTANTS: dict[str, dict[str, Any]] = {  # one-value fields the file writes and the model does not list in FIELDS
    "/winding/kind": {"enum": [t.value for t in TopologyKind]},
    "/analysis/edge_correction": {"const": "off"},
}
_SCALARS: dict[ValueType, dict[str, Any]] = {
    ValueType.INT: {"type": "integer"},
    ValueType.FLOAT: {"type": "number"},
    ValueType.BOOL: {"type": "boolean"},
    ValueType.TEXT: {"type": "string"},
    ValueType.INT_LIST: {"type": "array", "items": {"type": "integer"}},
    ValueType.INT_GROUPS: {"type": "array", "items": {"type": "array", "items": {"type": "integer"}}},
}


def _file_pattern(spec: FieldSpec) -> str:
    return spec.pointer[: -len("_rad")] + "_deg" if spec.pointer in RAD_PATTERNS else spec.pointer


def _leaf(spec: FieldSpec) -> dict[str, Any]:
    choices = sorted(set(spec.choices), key=str)  # JSON values: StrEnum members serialise as their text
    if spec.value_type is ValueType.CHOICE:
        return {"enum": choices}
    if spec.value_type is ValueType.CHOICE_LIST:
        return {"type": "array", "items": {"enum": choices}}
    if spec.value_type is ValueType.GROUP:
        return {"type": "object"}
    if spec.value_type is ValueType.LIST:
        return {"type": "array"}
    schema = dict(_SCALARS[spec.value_type])
    if spec.value_type is ValueType.TEXT:
        schema["pattern"] = r"\S"
    if spec.limits.sign is Sign.POSITIVE:
        schema["exclusiveMinimum"] = 0
    elif spec.limits.sign is Sign.NON_NEGATIVE:
        schema["minimum"] = 0
    return schema


def _merge(node: dict[str, Any], segments: list[str], schema: dict[str, Any], nullable: bool) -> None:
    if not segments:
        for key, value in schema.items():
            node.setdefault(key, value)
        if nullable:
            node["nullable"] = True
        return
    head, rest = segments[0], segments[1:]
    if head == LIST_ITEM:
        node.update({"type": "array"})
        child = node.setdefault("items", {"type": "object"})
    else:
        node.setdefault("type", "object")
        child = node.setdefault("properties", {}).setdefault(head, {})
    if rest:
        child.setdefault("type", "array" if rest[0] == LIST_ITEM else "object")
    _merge(child, rest, schema, nullable)


def _close(node: dict[str, Any]) -> dict[str, Any]:
    """Turn the merge tree into JSON Schema: objects refuse unknown keys, nullable nodes also accept null."""
    nullable = node.pop("nullable", False)
    if "properties" in node:
        node["properties"] = {k: _close(v) for k, v in sorted(node["properties"].items())}
        node["additionalProperties"] = False
    if isinstance(node.get("items"), dict) and "properties" in node["items"]:
        node["items"] = _close(node["items"])
    return {"anyOf": [node, {"type": "null"}]} if nullable else node


def _with_topology_required(design: dict[str, Any]) -> dict[str, Any]:
    """Require `/winding/kind`: the loader needs the topology even for a blank draft."""
    design["required"] = ["winding"]
    design["properties"]["winding"]["required"] = ["kind"]
    return design


def _measurable_regex() -> str:
    patterns = sorted(
        re.escape(_file_pattern(s)).replace(re.escape(LIST_ITEM), r"\d+")
        for s in FIELDS
        if s.kind is FieldKind.PROPERTY and s.value_type is ValueType.FLOAT
    )
    return "^(" + "|".join(patterns) + ")$"


def build_schema() -> dict[str, Any]:
    """Return the JSON Schema (Draft 2020-12) of project file v1."""
    design: dict[str, Any] = {"type": "object"}
    for spec in FIELDS:
        _merge(design, _file_pattern(spec).split("/")[1:], _leaf(spec), spec.nullable)
    for pointer, schema in CONSTANTS.items():
        _merge(design, pointer.split("/")[1:], schema, nullable=False)
    plain = [p.value for p in Provenance if p not in (Provenance.EXAMPLE, Provenance.MEASURED)]
    entry = {
        "plain": {
            "type": "object",
            "required": ["provenance"],
            "properties": {"provenance": {"enum": sorted(plain)}},
            "additionalProperties": False,
        },
        "example": {
            "type": "object",
            "required": ["provenance", "example_id"],
            "properties": {"provenance": {"const": "example"}, "example_id": {"type": "string"}},
            "additionalProperties": False,
        },
        "measured": {
            "type": "object",
            "required": ["provenance", "source"],
            "properties": {"provenance": {"const": "measured"}, "source": {"type": "string", "pattern": r"\S"}},
            "additionalProperties": False,
        },
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "embodic project file v1",
        "type": "object",
        "required": ["format", "schema_version", "design"],
        "additionalProperties": False,
        "properties": {
            "format": {"const": PROJECT_FORMAT},
            "schema_version": {"const": 1},
            "app_version": {"type": "string"},
            "saved_utc": {"type": "string"},
            "design_hash": {"type": "string"},
            "origin_example": {
                "anyOf": [
                    {"type": "null"},
                    {
                        "type": "object",
                        "required": ["example_id", "example_sha256"],
                        "properties": {"example_id": {"type": "string"}, "example_sha256": {"type": "string"}},
                        "additionalProperties": False,
                    },
                ]
            },
            "design": _with_topology_required(_close(design)),
            "provenance": {
                "type": "object",
                "propertyNames": {"pattern": "^/"},
                "patternProperties": {
                    _measurable_regex(): {
                        "oneOf": [{"$ref": "#/$defs/plain"}, {"$ref": "#/$defs/example"}, {"$ref": "#/$defs/measured"}]
                    }
                },
                "additionalProperties": {"oneOf": [{"$ref": "#/$defs/plain"}, {"$ref": "#/$defs/example"}]},
            },
            "ui": {"type": "object"},
            "example": {
                "type": "object",
                "required": ["title", "source_note"],
                "properties": {"title": {"type": "string"}, "source_note": {"type": "string"}},
                "additionalProperties": False,
            },
        },
        "$defs": entry,
    }


def schema_text() -> str:
    """Return the schema file text: sorted keys, one-space indent, trailing newline."""
    return json.dumps(build_schema(), sort_keys=True, indent=1) + "\n"


if __name__ == "__main__":
    SCHEMA_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCHEMA_PATH.write_text(schema_text(), encoding="utf-8", newline="\n")
    print(SCHEMA_PATH)
