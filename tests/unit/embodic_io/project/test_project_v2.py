"""REQ-T-07 and REQ-F-15: project file v2 holds the engine and registry versions; v1 files migrate (interfaces.md 9.1).

The v1 fixture is the packaged CF-11 example as the v1 writer produced it (main b977621), so it is a file from the
wild and not the output of the code under test.
"""

import copy
import json
import re
from pathlib import Path
from typing import Any

import pytest

import embodic
from embodic.errors import Severity
from embodic.io import project as project_module
from embodic.io.examples import load_example
from embodic.io.migrations import PROJECT_SCHEMA_VERSION, migrate
from embodic.io.project import ProjectFile, load_project, parse_project, project_provenance, save_project
from embodic.results import load_registry

CF11 = "spiral_12c16p_default"
V1_FIXTURE = Path(__file__).parent / "fixtures" / "spiral_12c16p_default.v1.embodic.json"
REGISTRY_VERSION = re.compile(r"v1\+[0-9a-f]{12}\.[0-9a-f]{12}")
NEW_KEYS = ("engine_version", "registry_version")
STAMP_KEYS = ("app_version", "saved_utc", *NEW_KEYS)  # every version stamp; both schemas type each one `string`
V1_STAMP_KEYS = ("app_version", "saved_utc")


@pytest.fixture(autouse=True)
def _frozen_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(project_module, "_utc_now", lambda: "2026-10-08T12:00:00Z")


def _v1_document() -> dict[str, Any]:
    document: dict[str, Any] = json.loads(V1_FIXTURE.read_text(encoding="utf-8"))
    return document


def _saved(tmp_path: Path, **kwargs: str) -> dict[str, Any]:
    ref, design = load_example(CF11)
    path = tmp_path / "saved.embodic.json"
    save_project(path, ProjectFile(design=design, origin=ref), **kwargs)
    document: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return document


@pytest.mark.req("REQ-T-07", "REQ-T-14")
def test_saved_project_names_the_engine_version_and_the_registry_version(tmp_path: Path) -> None:
    """Catches a project file that omits the versions REQ-T-07 lists, or fills in a value other than the build's."""
    document = _saved(tmp_path)
    assert document["schema_version"] == 2
    assert document["engine_version"] == embodic.__version__
    assert document["registry_version"] == load_registry().version
    assert REGISTRY_VERSION.fullmatch(document["registry_version"])


@pytest.mark.req("REQ-T-07", "REQ-F-15")
def test_a_registry_version_passed_by_the_caller_reaches_the_file_and_the_round_trip_keeps_it(tmp_path: Path) -> None:
    """Catches a save that ignores the caller's registry version, which breaks a byte-identical second save."""
    first = tmp_path / "a.embodic.json"
    second = tmp_path / "b.embodic.json"
    ref, design = load_example(CF11)
    save_project(first, ProjectFile(design=design, origin=ref), registry_version="v1+test")
    loaded, issues = load_project(first)
    assert loaded is not None and issues == ()
    save_project(second, loaded, registry_version="v1+test")
    assert json.loads(first.read_text(encoding="utf-8"))["registry_version"] == "v1+test"
    assert first.read_bytes() == second.read_bytes()


@pytest.mark.req("REQ-F-15")
def test_migrating_v1_sets_both_new_keys_to_null_and_touches_nothing_else() -> None:
    """Catches a migration that invents a version for a file that never recorded one (D-014: no invented input)."""
    v1 = _v1_document()
    migrated, issues = migrate(copy.deepcopy(v1))
    assert migrated is not None
    assert {key: migrated[key] for key in NEW_KEYS} == dict.fromkeys(NEW_KEYS)
    assert migrated["schema_version"] == 2
    unchanged = {key: value for key, value in migrated.items() if key not in (*NEW_KEYS, "schema_version")}
    assert unchanged == {key: value for key, value in v1.items() if key != "schema_version"}
    assert [(i.code, i.value, i.limit) for i in issues] == [("INFO_MIGRATED", 1, 2)]


@pytest.mark.req("REQ-F-15")
def test_a_v1_file_loads_with_the_same_design_provenance_and_one_migration_notice() -> None:
    """Catches a v2 reader that refuses a v1 file or reads it differently (the design, its origin, its provenance)."""
    ref, design = load_example(CF11)
    loaded, issues = load_project(V1_FIXTURE)
    assert isinstance(loaded, ProjectFile)
    assert (loaded.design, loaded.origin) == (design, ref)
    assert project_provenance(loaded) == project_provenance(ProjectFile(design=design, origin=ref))
    assert [(i.code, i.severity, i.value, i.limit) for i in issues] == [("INFO_MIGRATED", Severity.INFO, 1, 2)]


@pytest.mark.req("REQ-F-15", "REQ-N-04")
def test_resaving_a_v1_file_writes_v2_and_keeps_the_design_hash(tmp_path: Path) -> None:
    """Catches a migration that changes the design hash, which would orphan every stored origin_example."""
    loaded, _ = load_project(V1_FIXTURE)
    assert loaded is not None
    path = tmp_path / "resaved.embodic.json"
    save_project(path, loaded, registry_version="v1+test")
    resaved = json.loads(path.read_text(encoding="utf-8"))
    assert resaved["design_hash"] == _v1_document()["design_hash"]
    assert resaved["design"] == _v1_document()["design"]
    assert (resaved["schema_version"], resaved["engine_version"], resaved["registry_version"]) == (
        PROJECT_SCHEMA_VERSION,
        embodic.__version__,
        "v1+test",
    )


@pytest.mark.req("REQ-F-15")
@pytest.mark.parametrize("key", NEW_KEYS)
def test_a_v1_file_that_holds_a_v2_key_is_refused_with_the_key_pointer(key: str) -> None:
    """Catches an unknown-key check that runs after the migration, which would let a hand-edited v1 file pass."""
    document = _v1_document()
    document[key] = "x"
    loaded, issues = parse_project(json.dumps(document))
    assert loaded is None
    assert [(i.code, i.pointers) for i in issues] == [("INVALID_PROJECT_FILE", (f"/{key}",))]


@pytest.mark.req("REQ-F-15")
def test_a_file_from_a_newer_format_is_refused_as_newer_even_when_it_holds_keys_this_version_lacks() -> None:
    """Catches the key check running before the version check: a newer file would read as a hand-edited one."""
    document = _v1_document()
    document["schema_version"] = PROJECT_SCHEMA_VERSION + 1
    document["key_of_a_later_format"] = 1
    loaded, issues = parse_project(json.dumps(document))
    assert loaded is None
    assert [i.code for i in issues] == ["INVALID_SCHEMA_VERSION_NEWER"]


@pytest.mark.req("REQ-T-07")
@pytest.mark.parametrize("key", STAMP_KEYS)
@pytest.mark.parametrize("stamp", [5, None, ["0.0.1"], {"v": "0.0.1"}], ids=["int", "null", "list", "object"])
def test_a_v2_file_whose_version_stamp_is_not_a_string_is_refused_with_the_key_pointer(
    tmp_path: Path, key: str, stamp: object
) -> None:
    """Catches a loader that reads a stamp project.v2.schema.json types as a string and passes any other type."""
    document = _saved(tmp_path)
    document[key] = stamp
    loaded, issues = parse_project(json.dumps(document))
    assert loaded is None
    assert [(i.code, i.pointers) for i in issues] == [("INVALID_PROJECT_FILE", (f"/{key}",))]


@pytest.mark.req("REQ-T-07")
@pytest.mark.parametrize("key", STAMP_KEYS)
def test_a_v2_file_with_string_version_stamps_loads_without_notice(tmp_path: Path, key: str) -> None:
    """Catches a type check that refuses the strings embodic writes, such as the registry text `v1+<hex>.<hex>`."""
    document = _saved(tmp_path)
    assert isinstance(document[key], str)
    loaded, issues = parse_project(json.dumps(document))
    assert isinstance(loaded, ProjectFile)
    assert issues == ()


@pytest.mark.req("REQ-F-15")
@pytest.mark.parametrize("key", NEW_KEYS)
def test_a_v1_file_with_a_mistyped_v2_key_reports_the_key_once(key: str) -> None:
    """Catches the unknown-key check and the type check both reporting one key, which doubles the issue."""
    document = _v1_document()
    document[key] = 5
    loaded, issues = parse_project(json.dumps(document))
    assert loaded is None
    assert [(i.code, i.pointers) for i in issues] == [("INVALID_PROJECT_FILE", (f"/{key}",))]


@pytest.mark.req("REQ-F-15")
@pytest.mark.parametrize("key", V1_STAMP_KEYS)
def test_a_v1_file_whose_app_version_or_saved_utc_is_not_a_string_is_refused_with_the_key_pointer(key: str) -> None:
    """Catches a loader that types the stamps only from v2 on: project.v1.schema.json types these two `string` too."""
    document = _v1_document()
    document[key] = 20261008
    loaded, issues = parse_project(json.dumps(document))
    assert loaded is None
    assert [(i.code, i.pointers) for i in issues] == [("INVALID_PROJECT_FILE", (f"/{key}",))]


@pytest.mark.req("REQ-F-15")
@pytest.mark.parametrize("key", STAMP_KEYS)
def test_a_newer_format_file_with_a_stamp_of_another_type_is_refused_as_newer(tmp_path: Path, key: str) -> None:
    """Catches a type check that runs before the version check: a later format may type the stamp differently."""
    document = _saved(tmp_path)
    document["schema_version"] = PROJECT_SCHEMA_VERSION + 1
    document[key] = {"name": "embodic", "version": "9.0.0"}
    loaded, issues = parse_project(json.dumps(document))
    assert loaded is None
    assert [i.code for i in issues] == ["INVALID_SCHEMA_VERSION_NEWER"]
