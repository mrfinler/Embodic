"""UT-IO-03: the published JSON Schema accepts every example and saved file, and agrees with the loader on mutations.

Agreement means: the schema accepts a file exactly when `parse_project` returns a project with no ERROR issue of
category INVALID. Missing design values are not INVALID (they load as a LoadedDraft), so the schema requires none.
"""

import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import jsonschema
import pytest

from embodic.errors import IssueCategory, Severity
from embodic.io import project as project_module
from embodic.io.examples import examples_dir, load_example
from embodic.io.project import LoadedDraft, ProjectFile, parse_project, save_project
from embodic.model.draft import blank_draft
from embodic.model.provenance import mark_measured
from embodic.model.vocabulary import TopologyKind

from .make_schema import SCHEMA_PATH, schema_text

Mutation = Callable[[dict[str, Any]], None]


def _validator() -> jsonschema.Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def _base_document(tmp_path: Path) -> dict[str, Any]:
    ref, design = load_example("spiral_12c16p_default")
    measured = mark_measured(design, (), "/rotor/remanence_t", "magnet datasheet rev C")
    assert isinstance(measured, tuple)
    path = tmp_path / "base.embodic.json"
    save_project(path, ProjectFile(design=design, origin=ref, measurements=measured))
    document: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return document


def _set(path: str, value: object) -> Mutation:
    def mutate(document: dict[str, Any]) -> None:
        *parents, last = path.split("/")[1:]
        node = document
        for key in parents:
            node = node[int(key)] if isinstance(node, list) else node[key]
        node[last] = value

    return mutate


def _delete(path: str) -> Mutation:
    def mutate(document: dict[str, Any]) -> None:
        *parents, last = path.split("/")[1:]
        node = document
        for key in parents:
            node = node[key]
        del node[last]

    return mutate


def _provenance(pointer: str, entry: object) -> Mutation:
    def mutate(document: dict[str, Any]) -> None:
        document["provenance"][pointer] = entry

    return mutate


ACCEPTED: dict[str, Mutation] = {
    "unchanged": lambda d: None,
    "no ui": _delete("/ui"),
    "no provenance": _delete("/provenance"),
    "empty provenance": _set("/provenance", {}),
    "no origin": _set("/origin_example", None),
    "ui with any keys": _set("/ui", {"zoom": 2.0, "view": {"x": 1}}),
    "poles missing": _delete("/design/rotor/poles"),
    "trace width missing": _delete("/design/winding/coil/trace_width_mm"),
    "operating missing": _delete("/design/operating"),
    "board rotation in degrees": _set("/design/outline/board/rotation_deg", 30.0),
    "dc link null": _set("/design/operating/dc_link_v", None),
    "turns null": _set("/design/winding/coil/turns", None),
    "measured property": _provenance("/operating/winding_temperature_degc", {"provenance": "user"}),
    "example entry": _provenance("/rotor/poles", {"provenance": "example", "example_id": "spiral_12c16p_default"}),
    "default entry": _provenance("/name", {"provenance": "default"}),
}
REFUSED: dict[str, Mutation] = {
    "format other": _set("/format", "kicad"),
    "format missing": _delete("/format"),
    "version text": _set("/schema_version", "1"),
    "version zero": _set("/schema_version", 0),
    "version bool": _set("/schema_version", True),
    "version fraction": _set("/schema_version", 1.5),
    "design missing": _delete("/design"),
    "design list": _set("/design", []),
    "design null": _set("/design", None),
    "provenance list": _set("/provenance", []),
    "ui list": _set("/ui", []),
    "origin text": _set("/origin_example", "spiral"),
    "origin without hash": _set("/origin_example", {"example_id": "spiral_12c16p_default"}),
    "winding kind unknown": _set("/design/winding/kind", "coil"),
    "winding kind missing": _delete("/design/winding/kind"),
    "poles text": _set("/design/rotor/poles", "16"),
    "poles fraction": _set("/design/rotor/poles", 16.5),
    "poles bool": _set("/design/rotor/poles", True),
    "trace width text": _set("/design/winding/coil/trace_width_mm", "0.5"),
    "trace width bool": _set("/design/winding/coil/trace_width_mm", True),
    "trace width zero": _set("/design/winding/coil/trace_width_mm", 0.0),
    "trace width negative": _set("/design/winding/coil/trace_width_mm", -0.5),
    "connection unknown": _set("/design/connection/topology", "triangle"),
    "interconnect text": _set("/design/connection/draw_interconnect", "yes"),
    "harmonics text": _set("/design/analysis/harmonics", ["1"]),
    "series groups text": _set("/design/winding/layers/series_groups", [["0"]]),
    "name number": _set("/design/name", 5),
    "name blank": _set("/design/name", "  "),
    "magnet kind unknown": _set("/design/rotor/magnet/kind", "sphere"),
    "layer thickness text": _set("/design/stackup/layers/0/thickness_mm", "thin"),
    "entry not object": _provenance("/rotor/poles", "user"),
    "entry unknown kind": _provenance("/rotor/poles", {"provenance": "guess"}),
    "measured no source": _provenance("/rotor/remanence_t", {"provenance": "measured"}),
    "measured blank source": _provenance("/rotor/remanence_t", {"provenance": "measured", "source": " "}),
    "measured design field": _provenance("/rotor/poles", {"provenance": "measured", "source": "caliper"}),
    "example without id": _provenance("/rotor/poles", {"provenance": "example"}),
}


def _loader_accepts(document: dict[str, Any]) -> bool:
    loaded, issues = parse_project(json.dumps(document))
    invalid = [i for i in issues if i.severity is Severity.ERROR and i.category is IssueCategory.INVALID]
    return loaded is not None and not invalid


@pytest.mark.req("REQ-F-15")
def test_ut_io_03_schema_file_is_the_generator_output() -> None:
    """Catches a design key added, removed or renamed without regenerating the schema (schema version rule)."""
    assert SCHEMA_PATH.read_text(encoding="utf-8") == schema_text()


@pytest.mark.req("REQ-F-15")
def test_ut_io_03_examples_and_saved_files_validate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Catches a schema that refuses what embodic itself writes: examples, a design, a blank draft."""
    monkeypatch.setattr(project_module, "_utc_now", lambda: "2026-10-08T12:00:00Z")
    validator = _validator()
    for path in sorted(examples_dir().glob("*.embodic.json")):
        assert list(validator.iter_errors(json.loads(path.read_text(encoding="utf-8")))) == [], path.name
    draft_path = tmp_path / "draft.embodic.json"
    save_project(draft_path, LoadedDraft(draft=blank_draft(TopologyKind.SPIRAL), origin=None))
    assert list(validator.iter_errors(json.loads(draft_path.read_text(encoding="utf-8")))) == []
    assert list(validator.iter_errors(_base_document(tmp_path))) == []


@pytest.mark.req("REQ-F-15")
@pytest.mark.parametrize(
    ("name", "expected"), [(n, True) for n in ACCEPTED] + [(n, False) for n in REFUSED], ids=lambda v: str(v)
)
def test_ut_io_03_loader_and_schema_agree_on_mutated_files(tmp_path: Path, name: str, expected: bool) -> None:
    """Catches a loader and a schema that disagree on what a valid file is (51 mutations of one saved project)."""
    document = copy.deepcopy(_base_document(tmp_path))
    {**ACCEPTED, **REFUSED}[name](document)
    schema_accepts = not list(_validator().iter_errors(document))
    assert (schema_accepts, _loader_accepts(document)) == (expected, expected)
