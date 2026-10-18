"""Project file v2: save and load a design or an incomplete draft with its origin and provenance (interfaces.md 9.1).

`load_project` is the boundary: it parses untrusted JSON into typed values and reports every problem as an issue.
Everything past it trusts the types.
"""

import datetime
import json
import os
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import embodic
from embodic.errors import IssueCategory, Severity, ValidationIssue, message_for
from embodic.io.canonical import (
    design_document,
    design_hash,
    draft_document,
    draft_from_document,
    file_pointer,
    model_pointer,
)
from embodic.io.examples import packaged_example
from embodic.io.migrations import PROJECT_SCHEMA_VERSION, migrate
from embodic.model.design import DesignParameters
from embodic.model.draft import DesignDraft, parse_draft
from embodic.model.fields import FIELDS, FieldKind, field_for
from embodic.model.provenance import (
    DefaultValue,
    ExampleRef,
    ExampleValue,
    FieldProvenance,
    MeasuredValue,
    Measurement,
    Provenance,
    ProvenanceMap,
    UserValue,
    derive_provenance,
)
from embodic.model.schema import JsonValue, ValueType, flatten, pattern_of
from embodic.results import load_registry

PROJECT_FORMAT = "embodic-project"
PROJECT_SUFFIX = ".embodic.json"
TOP_LEVEL_KEYS_V1 = frozenset(
    {
        "format",
        "schema_version",
        "app_version",
        "saved_utc",
        "design_hash",
        "origin_example",
        "design",
        "provenance",
        "ui",
    }
)
VERSION_STAMP_KEYS = ("engine_version", "registry_version")
TOP_LEVEL_KEYS = TOP_LEVEL_KEYS_V1 | set(VERSION_STAMP_KEYS)
_STRING_STAMP_KEYS = ("app_version", "saved_utc", *VERSION_STAMP_KEYS)  # each typed `string` where its schema has it
_TOP_LEVEL_KEYS_BY_VERSION = {1: TOP_LEVEL_KEYS_V1, 2: TOP_LEVEL_KEYS}
_ORIGIN_KEYS = frozenset({"example_id", "example_sha256"})
_EXAMPLE_KEY = "example"  # optional: the gallery metadata of a packaged example file, never written by save_project
_EXAMPLE_KEYS = frozenset({"title", "source_note"})
_CONSTANT_POINTERS = frozenset({"/winding/kind", "/analysis/edge_correction"})  # written by the file, not in FIELDS
_DESIGN_PATTERNS = frozenset({*(file_pointer(spec.pointer) for spec in FIELDS), *_CONSTANT_POINTERS})

_CATEGORY_BY_PREFIX = {
    "INVALID_": IssueCategory.INVALID,
    "MISSING_": IssueCategory.MISSING,
    "INFO_": IssueCategory.INVALID,  # IssueCategory has no INFO member; severity INFO carries the meaning
}


@dataclass(frozen=True, slots=True, kw_only=True)
class ProjectFile:
    """A project file whose design is complete."""

    design: DesignParameters
    origin: ExampleRef | None
    measurements: tuple[Measurement, ...] = ()
    ui_state: Mapping[str, JsonValue] = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class LoadedDraft:
    """A project file whose design is incomplete (saved mid-entry). Loads into the new-design form."""

    draft: DesignDraft
    origin: ExampleRef | None
    measurements: tuple[Measurement, ...] = ()
    ui_state: Mapping[str, JsonValue] = field(default_factory=dict)


def _issue(
    code: str, pointers: tuple[str, ...] = (), *, severity: Severity = Severity.ERROR, value: str | None = None
) -> ValidationIssue:
    category = next(c for prefix, c in _CATEGORY_BY_PREFIX.items() if code.startswith(prefix))
    return ValidationIssue(
        code=code, category=category, severity=severity, message=message_for(code), pointers=pointers, value=value
    )


def _entry(provenance: FieldProvenance) -> dict[str, JsonValue]:
    match provenance:
        case ExampleValue(example_id=example_id):
            return {"provenance": provenance.provenance.value, "example_id": example_id}
        case MeasuredValue(source=source):
            return {"provenance": provenance.provenance.value, "source": source}
        case UserValue() | DefaultValue():
            return {"provenance": provenance.provenance.value}


def provenance_document(provenance: ProvenanceMap) -> dict[str, JsonValue]:
    """Return the file's `provenance` object: file pointer -> entry, sorted by pointer."""
    return {file_pointer(p): _entry(provenance[p]) for p in sorted(provenance)}


def _origin_pair(origin: ExampleRef | None) -> tuple[ExampleRef, DesignParameters] | None:
    if origin is None:
        return None
    packaged = packaged_example(origin)
    return None if packaged is None else (origin, packaged)


def project_provenance(project: ProjectFile) -> dict[str, FieldProvenance]:
    """Provenance of every design pointer, derived from the values, the packaged origin and the measurements.

    An origin that is not packaged with the same hash gives no `example` entries, and since its values are not blank
    defaults either (interfaces.md 9.1, question 1), every field is `measured` where a measurement names it and `user`
    elsewhere.
    """
    pair = _origin_pair(project.origin)
    derived = derive_provenance(project.design, pair, project.measurements)
    if project.origin is None or pair is not None:
        return derived
    return {pointer: UserValue() if isinstance(kind, DefaultValue) else kind for pointer, kind in derived.items()}


def _utc_now() -> str:
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def project_document(
    project: ProjectFile | LoadedDraft, provenance: ProvenanceMap, *, saved_utc: str, registry_version: str
) -> dict[str, JsonValue]:
    """Return the file's JSON data; pure, so the caller supplies the provenance, the save time and the registry version.

    `engine_version` is the embodic version: there is no separate engine (D-038d).
    """
    origin: JsonValue = None
    if project.origin is not None:
        origin = {"example_id": project.origin.example_id, "example_sha256": project.origin.example_sha256}
    if isinstance(project, ProjectFile):
        hash_, design = design_hash(project.design), design_document(project.design)
    else:
        hash_, design = "", draft_document(project.draft)
    return {
        "format": PROJECT_FORMAT,
        "schema_version": PROJECT_SCHEMA_VERSION,
        "app_version": embodic.__version__,
        "engine_version": embodic.__version__,
        "registry_version": registry_version,
        "saved_utc": saved_utc,
        "design_hash": hash_,
        "origin_example": origin,
        "design": design,
        "provenance": provenance_document(provenance),
        "ui": dict(project.ui_state),
    }


def encode_project(document: Mapping[str, JsonValue]) -> str:
    """File text: sorted keys, one-space indent, UTF-8 characters kept, trailing newline."""
    return json.dumps(document, sort_keys=True, indent=1, ensure_ascii=False, allow_nan=False) + "\n"


def save_project(
    path: Path, project: ProjectFile | LoadedDraft, *, saved_utc: str | None = None, registry_version: str | None = None
) -> str:
    """Write atomically (temp file + os.replace) and return the design hash ('' for a draft).

    saved_utc defaults to the current UTC second. A caller that compares two saves byte for byte passes one stamp to
    both, since two clock reads can straddle a second. registry_version defaults to the packaged registry's.
    """
    if isinstance(project, ProjectFile):
        provenance: ProvenanceMap = project_provenance(project)
    else:  # a draft is not a design, so only its measurements have a provenance to keep
        provenance = {m.pointer: MeasuredValue(source=m.source) for m in project.measurements}
    stamp = _utc_now() if saved_utc is None else saved_utc
    registry = load_registry().version if registry_version is None else registry_version
    document = project_document(project, provenance, saved_utc=stamp, registry_version=registry)
    descriptor, temp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(encode_project(document))
        os.replace(temp_name, path)
    except BaseException:
        Path(temp_name).unlink(missing_ok=True)
        raise
    return str(document["design_hash"])


def _origin(raw: object) -> ExampleRef | ValidationIssue | None:
    if raw is None:
        return None
    if isinstance(raw, dict) and all(isinstance(raw.get(k), str) for k in ("example_id", "example_sha256")):
        return ExampleRef(example_id=raw["example_id"], example_sha256=raw["example_sha256"])
    return _issue("INVALID_PROJECT_FILE", ("/origin_example",))


def _measurable(pointer: str, values: Mapping[str, JsonValue]) -> bool:
    if pointer not in values:
        return False
    spec = field_for(pointer, values)
    return spec.kind is FieldKind.PROPERTY and spec.value_type is ValueType.FLOAT


def _stored_provenance(
    raw: Mapping[str, Any], values: Mapping[str, JsonValue]
) -> tuple[dict[str, str], tuple[Measurement, ...], list[ValidationIssue]]:
    """Return stored kinds by model pointer, the valid measurements, and INVALID_PROVENANCE issues."""
    kinds: dict[str, str] = {}
    measurements: list[Measurement] = []
    issues: list[ValidationIssue] = []
    known = {p.value for p in Provenance}
    for pointer_in_file, entry in sorted(raw.items()):
        pointer = model_pointer(pointer_in_file)
        kind = entry.get("provenance") if isinstance(entry, dict) else None
        if kind not in known:
            issues.append(_issue("INVALID_PROVENANCE", (f"/provenance{pointer_in_file}",)))
            continue
        if kind == Provenance.EXAMPLE and not isinstance(entry.get("example_id"), str):
            issues.append(_issue("INVALID_PROVENANCE", (f"/provenance{pointer_in_file}",)))
            continue
        if kind == Provenance.MEASURED:
            source = entry.get("source")
            if not (isinstance(source, str) and source.strip() and _measurable(pointer, values)):
                issues.append(_issue("INVALID_PROVENANCE", (f"/provenance{pointer_in_file}",)))
                continue
            measurements.append(Measurement(pointer=pointer, source=source.strip()))
        kinds[pointer] = kind
    return kinds, tuple(measurements), issues


def _check_against_example(
    design: DesignParameters,
    origin: ExampleRef | None,
    stored: Mapping[str, str],
    measurements: tuple[Measurement, ...],
) -> list[ValidationIssue]:
    """Report stored `example` entries that disagree with the packaged example (UT-IO-07)."""
    if origin is None:
        return []
    pair = _origin_pair(origin)
    if pair is None:
        return [_issue("INFO_EXAMPLE_NOT_PACKAGED", ("/origin_example",), severity=Severity.INFO)]
    derived = derive_provenance(design, pair, measurements)
    disagree = sorted(
        p for p, kind in stored.items() if (kind == Provenance.EXAMPLE) != isinstance(derived.get(p), ExampleValue)
    )
    return [
        _issue("INFO_PROVENANCE_EXAMPLE_MISMATCH", (file_pointer(p),), severity=Severity.INFO, value=stored[p])
        for p in disagree
    ]


def load_project(path: Path) -> tuple[ProjectFile | LoadedDraft | None, tuple[ValidationIssue, ...]]:
    """Parse a project file; None with the issues when it is missing, unreadable, malformed or newer."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None, (_issue("INVALID_PROJECT_NOT_FOUND", (), value=str(path)),)
    except (OSError, UnicodeDecodeError) as error:
        return None, (_issue("INVALID_PROJECT_FILE", (), value=str(error)),)
    return parse_project(text)


def _refuse(pointer: str) -> tuple[None, tuple[ValidationIssue, ...]]:
    return None, (_issue("INVALID_PROJECT_FILE", (pointer,)),)


def _unknown_keys(document: Mapping[str, Any]) -> list[str]:
    """Return the pointer of every key the file's own schema version refuses.

    `ui` is free-form and `provenance` is checked apart. The check runs before the migration, which adds the v2 keys
    to a v1 document, so a v1 file that holds one of them is refused as its schema refuses it.
    """
    allowed = _TOP_LEVEL_KEYS_BY_VERSION[document["schema_version"]]
    unknown = [f"/{key}" for key in sorted(document.keys() - allowed - {_EXAMPLE_KEY})]
    for key, nested_keys in (("origin_example", _ORIGIN_KEYS), (_EXAMPLE_KEY, _EXAMPLE_KEYS)):
        if isinstance(nested := document.get(key), dict):
            unknown += [f"/{key}/{name}" for name in sorted(nested.keys() - nested_keys)]
    unknown += [
        f"/design{pointer}"
        for pointer in sorted(flatten(document["design"]))
        if pattern_of(pointer) not in _DESIGN_PATTERNS
    ]
    return unknown


def _mistyped_stamps(document: Mapping[str, Any]) -> list[str]:
    """Return the pointer of each version stamp this file's schema allows whose value is not a string.

    Both schemas type app_version and saved_utc `string`, and v2 types engine_version and registry_version the same
    way. A v1 file cannot hold the v2 stamps, and `_unknown_keys` already names them, so only the keys of the file's
    own version are checked.
    """
    allowed = _TOP_LEVEL_KEYS_BY_VERSION[document["schema_version"]]
    return [
        f"/{key}"
        for key in _STRING_STAMP_KEYS
        if key in allowed and key in document and not isinstance(document[key], str)
    ]


def _malformed(document: object) -> str | None:
    """Return the pointer of the first top-level key that breaks the v1 file shape, or None."""
    if not isinstance(document, dict) or document.get("format") != PROJECT_FORMAT:
        return "/format"
    version = document.get("schema_version")
    if not (isinstance(version, int) and not isinstance(version, bool) and version >= 1):
        return "/schema_version"
    expected = {"design": dict, "provenance": dict, "ui": dict}
    for key, kind in expected.items():
        if key in document and not isinstance(document[key], kind):
            return f"/{key}"
    example = document.get(_EXAMPLE_KEY)
    if _EXAMPLE_KEY in document and not (
        isinstance(example, dict) and all(isinstance(example.get(key), str) for key in _EXAMPLE_KEYS)
    ):
        return f"/{_EXAMPLE_KEY}"
    return None if "design" in document else "/design"


def parse_project(text: str) -> tuple[ProjectFile | LoadedDraft | None, tuple[ValidationIssue, ...]]:
    """Parse project file text; see load_project."""
    try:
        document = json.loads(text, parse_constant=lambda token: float("nan"))
    except json.JSONDecodeError as error:
        return None, (_issue("INVALID_PROJECT_FILE", (), value=str(error)),)
    if (pointer := _malformed(document)) is not None:
        return _refuse(pointer)
    if document["schema_version"] <= PROJECT_SCHEMA_VERSION and (
        refused := [*_unknown_keys(document), *_mistyped_stamps(document)]
    ):
        return None, tuple(_issue("INVALID_PROJECT_FILE", (pointer,)) for pointer in refused)
    migrated, issues = migrate(document)
    if migrated is None:
        return None, issues
    origin = _origin(migrated.get("origin_example"))
    if isinstance(origin, ValidationIssue):
        return None, (origin,)
    draft = draft_from_document(migrated["design"])
    if draft is None:
        return _refuse("/design/winding/kind")
    ui = migrated.get("ui", {})
    stored, measurements, found = _stored_provenance(migrated.get("provenance", {}), draft.values)
    parsed = parse_draft(draft)
    if not isinstance(parsed, DesignParameters):
        loaded = LoadedDraft(draft=draft, origin=origin, measurements=measurements, ui_state=ui)
        return loaded, (*issues, *found, *parsed.issues)
    checked = _check_against_example(parsed, origin, stored, measurements)
    project = ProjectFile(design=parsed, origin=origin, measurements=measurements, ui_state=ui)
    return project, (*issues, *found, *checked)


def project_from_example(example: tuple[ExampleRef, DesignParameters]) -> ProjectFile:
    """Return a new project that starts from a packaged example."""
    ref, design = example
    return ProjectFile(design=design, origin=ref)
