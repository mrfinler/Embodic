"""UT-IO-01, 02, 04, 05, 07: project file save and load, canonical hash, migrations, provenance and drafts."""

import dataclasses
import hashlib
import json
from pathlib import Path

import pytest

from embodic.errors import Severity
from embodic.io import project as project_module
from embodic.io.canonical import canonical_json, design_hash
from embodic.io.examples import examples_dir, load_example
from embodic.io.migrations import PROJECT_SCHEMA_VERSION, migrate
from embodic.io.project import (
    LoadedDraft,
    ProjectFile,
    load_project,
    parse_project,
    project_provenance,
    save_project,
)
from embodic.model.draft import DraftIncomplete, blank_draft, draft_from_design, parse_draft
from embodic.model.provenance import DefaultValue, ExampleValue, MeasuredValue, UserValue, mark_measured
from embodic.model.vocabulary import TopologyKind

BR = "/rotor/remanence_t"
SOURCE = "magnet datasheet rev C, grade N42"
CF11 = "spiral_12c16p_default"
# Pinned 2026-10-11 (D-041b) from the packaged CF-11 example; a change means the canonical form or the example changed.
CF11_HASH = "sha256:ac4fab5db06f9e8f733dc495080deeddfe0bcf58faa31ebb7ec841c1b27d9c09"
EXAMPLE_OBJECT = {"title": "Example of a test file", "source_note": "test"}


@pytest.fixture(autouse=True)
def _frozen_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(project_module, "_utc_now", lambda: "2026-10-08T12:00:00Z")


def _cf11_project() -> ProjectFile:
    ref, design = load_example(CF11)
    return ProjectFile(design=design, origin=ref)


def _measured_project() -> ProjectFile:
    project = _cf11_project()
    measured = mark_measured(project.design, (), BR, SOURCE)
    assert isinstance(measured, tuple)
    return dataclasses.replace(project, measurements=measured, ui_state={"theme": "dark"})


def _round_trip(tmp_path: Path, project: ProjectFile | LoadedDraft) -> tuple[bytes, bytes]:
    first, second = tmp_path / "a.embodic.json", tmp_path / "b.embodic.json"
    save_project(first, project)
    loaded, issues = load_project(first)
    assert loaded is not None, issues
    save_project(second, loaded)
    return first.read_bytes(), second.read_bytes()


@pytest.mark.req("REQ-F-15")
@pytest.mark.parametrize("example_id", ["spiral_12c16p_default", "spiral_12c10p_d08", "spiral_12c14p"])
def test_ut_io_01_save_load_save_is_byte_identical(tmp_path: Path, example_id: str) -> None:
    """Catches a lossy field (angle conversion, list shape, provenance, ui) that changes the second save."""
    ref, design = load_example(example_id)
    first, second = _round_trip(tmp_path, ProjectFile(design=design, origin=ref, ui_state={"zoom": 1.5}))
    assert first == second


@pytest.mark.req("REQ-F-15")
def test_ut_io_01_draft_round_trip_is_byte_identical(tmp_path: Path) -> None:
    """Catches a draft save that drops or invents values: blank draft plus one typed value survives twice."""
    draft = blank_draft(TopologyKind.SPIRAL)
    draft = dataclasses.replace(draft, values={**draft.values, "/rotor/poles": 16, "/name": "half done"})
    first, second = _round_trip(tmp_path, LoadedDraft(draft=draft, origin=None))
    assert first == second


@pytest.mark.req("REQ-F-15")
def test_ut_io_01_saved_utc_reads_the_clock_unless_the_caller_passes_a_stamp(tmp_path: Path) -> None:
    """Catches a product save that stops reading the clock, or a passed stamp that the file ignores."""
    clock, passed = tmp_path / "clock.embodic.json", tmp_path / "passed.embodic.json"
    save_project(clock, _cf11_project())
    save_project(passed, _cf11_project(), saved_utc="2026-01-02T03:04:05Z")
    stamps = [json.loads(path.read_text(encoding="utf-8"))["saved_utc"] for path in (clock, passed)]
    assert stamps == ["2026-10-08T12:00:00Z", "2026-01-02T03:04:05Z"]


@pytest.mark.req("REQ-F-15", "REQ-N-04")
def test_ut_io_02_canonical_json_is_sorted_compact_and_in_degrees() -> None:
    """Catches whitespace, unsorted keys or radians in the hashed bytes, which would break cross-platform hashes."""
    _, design = load_example(CF11)
    text = canonical_json(design).decode()
    assert " " not in text.replace("Spiral, 12 coils, 16 poles", "")
    assert '_rad"' not in text
    assert '"rotation_deg":' in text
    data = json.loads(text)
    assert list(data) == sorted(data)
    assert design_hash(design) == "sha256:" + hashlib.sha256(text.encode()).hexdigest()


@pytest.mark.req("REQ-F-15", "REQ-N-04")
def test_ut_io_02_hash_is_pinned_and_ignores_provenance_and_ui(tmp_path: Path) -> None:
    """Catches a hash that moves between runs or covers ui/provenance (it must cover `design` only)."""
    plain, measured = _cf11_project(), _measured_project()
    assert save_project(tmp_path / "a.embodic.json", plain) == save_project(tmp_path / "b.embodic.json", measured)
    assert design_hash(plain.design) == CF11_HASH


@pytest.mark.req("REQ-F-15")
def test_ut_io_04_migration_runs_in_sequence_with_info() -> None:
    """Catches a migration that is skipped or leaves the version behind: synthetic v1 -> v2 adds its key."""
    synthetic = {1: lambda doc: {**doc, "added": True}}
    migrated, issues = migrate({"schema_version": 1}, current=2, migrations=synthetic)
    assert migrated == {"schema_version": 2, "added": True}
    assert [(i.code, i.severity) for i in issues] == [("INFO_MIGRATED", Severity.INFO)]


@pytest.mark.req("REQ-F-15")
def test_ut_io_04_newer_schema_version_is_refused(tmp_path: Path) -> None:
    """Catches a reader that silently loads a file from a newer embodic."""
    path = tmp_path / "new.embodic.json"
    save_project(path, _cf11_project())
    document = json.loads(path.read_text())
    document["schema_version"] = PROJECT_SCHEMA_VERSION + 1
    loaded, issues = parse_project(json.dumps(document))
    assert loaded is None
    assert [i.code for i in issues] == ["INVALID_SCHEMA_VERSION_NEWER"]


@pytest.mark.req("REQ-T-06")
def test_ut_io_05_defaults_stay_default_until_edited(tmp_path: Path) -> None:
    """Catches provenance lost on save: a blank-origin design keeps `default` on neutral optional fields."""
    _, design = load_example(CF11)
    path = tmp_path / "blank.embodic.json"
    save_project(path, ProjectFile(design=design, origin=None))
    stored = json.loads(path.read_text())["provenance"]
    assert stored["/materials/copper_resistivity_20c_ohm_m"] == {"provenance": "default"}
    assert stored["/rotor/poles"] == {"provenance": "user"}
    loaded, _ = load_project(path)
    assert isinstance(loaded, ProjectFile)
    assert isinstance(project_provenance(loaded)["/materials/copper_resistivity_20c_ohm_m"], DefaultValue)


@pytest.mark.req("REQ-F-15", "REQ-T-15")
def test_ut_io_07_origin_provenance_and_sources_survive(tmp_path: Path) -> None:
    """Catches a lost origin, a lost measurement source or a lost example label after save and load."""
    project = _measured_project()
    path = tmp_path / "p.embodic.json"
    save_project(path, project)
    loaded, issues = load_project(path)
    assert isinstance(loaded, ProjectFile)
    assert [i for i in issues if i.severity is Severity.ERROR] == []
    assert loaded.origin == project.origin
    assert loaded.measurements == project.measurements
    assert loaded.ui_state == {"theme": "dark"}
    provenance = project_provenance(loaded)
    assert provenance == project_provenance(project)
    assert provenance[BR] == MeasuredValue(source=SOURCE)
    assert provenance["/rotor/poles"] == ExampleValue(example_id=CF11)


@pytest.mark.req("REQ-F-15", "REQ-T-15")
def test_ut_io_07_incomplete_draft_loads_with_the_same_missing_list(tmp_path: Path) -> None:
    """Catches a draft that loads as a design with invented values, or with a different missing list."""
    _, design = load_example(CF11)
    values = dict(draft_from_design(design).values)
    del values["/rotor/poles"], values["/winding/coil/trace_width_mm"]
    draft = dataclasses.replace(draft_from_design(design), values=values)
    before = parse_draft(draft)
    assert isinstance(before, DraftIncomplete)
    path = tmp_path / "draft.embodic.json"
    assert save_project(path, LoadedDraft(draft=draft, origin=None)) == ""
    loaded, _ = load_project(path)
    assert isinstance(loaded, LoadedDraft)
    after = parse_draft(loaded.draft)
    assert isinstance(after, DraftIncomplete)
    assert after.missing == before.missing == ("/winding/coil/trace_width_mm", "/rotor/poles")


@pytest.mark.req("REQ-F-15", "REQ-T-15")
def test_ut_io_07_stored_example_entry_that_disagrees_is_reported(tmp_path: Path) -> None:
    """Catches a loader that trusts a hand-edited provenance map over the packaged example."""
    path = tmp_path / "p.embodic.json"
    save_project(path, _cf11_project())
    document = json.loads(path.read_text())
    document["design"]["rotor"]["poles"] = 20
    loaded, issues = parse_project(json.dumps(document))
    assert isinstance(loaded, ProjectFile)
    reported = [(i.code, i.pointers) for i in issues]
    assert reported == [("INFO_PROVENANCE_EXAMPLE_MISMATCH", ("/rotor/poles",))]
    assert isinstance(project_provenance(loaded)["/rotor/poles"], UserValue)


@pytest.mark.req("REQ-T-06")
def test_ut_io_07_measured_entry_without_source_is_invalid_provenance(tmp_path: Path) -> None:
    """Catches a `measured` label accepted without a named source (D-007)."""
    path = tmp_path / "p.embodic.json"
    save_project(path, _cf11_project())
    document = json.loads(path.read_text())
    document["provenance"][BR] = {"provenance": "measured", "source": " "}
    document["provenance"]["/rotor/poles"] = {"provenance": "measured", "source": SOURCE}
    loaded, issues = parse_project(json.dumps(document))
    assert isinstance(loaded, ProjectFile)
    assert loaded.measurements == ()
    assert sorted((i.code, i.pointers) for i in issues) == [
        ("INVALID_PROVENANCE", ("/provenance/rotor/poles",)),
        ("INVALID_PROVENANCE", (f"/provenance{BR}",)),
    ]


@pytest.mark.req("REQ-F-15", "REQ-T-06")
@pytest.mark.parametrize("kind", [[], {}], ids=["array", "object"])
def test_load_reports_a_nonstring_provenance_kind(tmp_path: Path, kind: object) -> None:
    """Report a malformed entry and keep the complete design available to the desktop editor."""
    path = tmp_path / "project.embodic.json"
    save_project(path, _cf11_project())
    document = json.loads(path.read_text(encoding="utf-8"))
    document["provenance"][BR] = {"provenance": kind}
    path.write_text(json.dumps(document), encoding="utf-8")

    loaded, issues = load_project(path)

    assert isinstance(loaded, ProjectFile)
    assert [(issue.code, issue.pointers) for issue in issues] == [("INVALID_PROVENANCE", (f"/provenance{BR}",))]


@pytest.mark.req("REQ-T-06")
def test_def_u_d6_01_origin_that_is_not_packaged_gives_measured_and_user_only(tmp_path: Path) -> None:
    """Catches DEF-U-D6-01: a design with a non-blank origin that is not packaged got 30 `default` entries.

    Interfaces.md 9.1 question 1: every field is `measured` where a measurement names it and `user` everywhere else, and
    the origin travels unchanged so an app that packages that hash derives `example` again.
    """
    project = _measured_project()
    foreign = dataclasses.replace(project, origin=dataclasses.replace(project.origin, example_sha256="sha256:0"))
    path = tmp_path / "foreign.embodic.json"
    save_project(path, foreign)
    stored = json.loads(path.read_text())["provenance"]
    assert {entry["provenance"] for entry in stored.values()} == {"measured", "user"}
    assert stored[BR] == {"provenance": "measured", "source": SOURCE}
    loaded, issues = load_project(path)
    assert isinstance(loaded, ProjectFile)
    assert [i.code for i in issues] == ["INFO_EXAMPLE_NOT_PACKAGED"]
    assert loaded.origin == foreign.origin
    assert project_provenance(loaded) == project_provenance(foreign)
    assert {type(p) for p in project_provenance(loaded).values()} == {MeasuredValue, UserValue}
    again = tmp_path / "again.embodic.json"
    save_project(again, loaded)
    assert again.read_bytes() == path.read_bytes()


@pytest.mark.req("REQ-F-15")
@pytest.mark.parametrize(
    ("edit", "pointers"),
    [
        (lambda d: d.update(extra_top=1), ["/extra_top"]),
        (lambda d: d["design"]["rotor"].update(polez=16), ["/design/rotor/polez"]),
        (lambda d: d["origin_example"].update(note="x"), ["/origin_example/note"]),
        (lambda d: d.update(example={**EXAMPLE_OBJECT, "note": "x"}), ["/example/note"]),
        (lambda d: d.update(example="Example"), ["/example"]),
        (lambda d: d.update(example={"title": "Example"}), ["/example"]),
        (
            lambda d: d["design"]["rotor"].update(polez=16) or d.update(extra_top=1),
            ["/extra_top", "/design/rotor/polez"],
        ),
    ],
)
def test_def_u_d6_02_unknown_keys_are_refused_with_their_pointer(edit, pointers) -> None:
    """Catches DEF-U-D6-02: a misspelt key was ignored and its value silently dropped (D-014).

    The project schema refuses these keys (additionalProperties false), and the loader must refuse what it refuses.
    """
    project = _cf11_project()
    document = json.loads(
        json.dumps(
            project_module.project_document(project, project_provenance(project), saved_utc="t", registry_version="v")
        )
    )
    edit(document)
    loaded, issues = parse_project(json.dumps(document))
    assert loaded is None
    assert [(i.code, i.pointers) for i in issues] == [("INVALID_PROJECT_FILE", (p,)) for p in pointers]


@pytest.mark.req("REQ-F-15")
@pytest.mark.parametrize("path", sorted(examples_dir().glob("*.embodic.json")), ids=lambda p: p.name.split(".")[0])
def test_every_packaged_example_file_loads_as_a_project(path: Path) -> None:
    """Catches D-036 f: the loader refused the `example` object that the published schema allows (UT-IO-03).

    Reading the file as the gallery does and as a user does must give the same design, without an issue.
    """
    loaded, issues = load_project(path)
    assert isinstance(loaded, ProjectFile) and issues == ()
    assert loaded.design == load_example(path.name.split(".")[0])[1]


@pytest.mark.req("REQ-F-15")
def test_def_u_d6_02_ui_stays_free_form_and_every_packaged_example_still_loads() -> None:
    """Catches an unknown-key check that rejects the free-form `ui` object or a key the writer itself emits."""
    project = _cf11_project()
    document = project_module.project_document(
        project, project_provenance(project), saved_utc="t", registry_version="v"
    )
    assert set(document) == project_module.TOP_LEVEL_KEYS
    document["ui"] = {"anything": {"nested": [1, 2]}}
    loaded, issues = parse_project(json.dumps(document))
    assert isinstance(loaded, ProjectFile) and issues == ()
