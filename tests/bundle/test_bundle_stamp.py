"""A bundle built from other source is not tested: the guard skips it, and fails it under the release profile (D-100c).

D-098c: the Windows commit gate ran tests/bundle on the folder that an older release had left in build/bundle, and the
test failed on an SVG width that came from comparing two versions. tools/build_bundle.py now writes
build/bundle/bundle_source.json after a good build, with the hash of src/embodic and the hash of resources. The guard
compares that file with the hashes of the tree under test. No bundle is built here: a fake repository and a fake
folder stand in for them.
"""

import ast
import hashlib
import json
import shutil
import subprocess
import sys
import types
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest
from _pytest.outcomes import Failed, Skipped
from tests.bundle import bundle_gate

from embodic.results.registry import package_source_sha256

pytestmark = pytest.mark.req("REQ-N-06")

STAMP_FILE = "bundle_source.json"  # in build/bundle, beside the embodic folder
OTHER_SOURCE = {"package_source_sha256": "0" * 64, "resources_sha256": "1" * 64}
PACKAGE_FILE = "src/embodic/__init__.py"
RESOURCE_FILE = "resources/theme/tokens.json"

refused = pytest.mark.parametrize(
    ("required", "outcome"), [("1", Failed), (None, Skipped)], ids=["required-fails", "not-required-skips"]
)


def set_required(monkeypatch: pytest.MonkeyPatch, required: str | None) -> None:
    """Set EMBODIC_REQUIRE_BUNDLE to a value, or remove it."""
    if required is None:
        monkeypatch.delenv(bundle_gate.REQUIRE_BUNDLE, raising=False)
    else:
        monkeypatch.setenv(bundle_gate.REQUIRE_BUNDLE, required)


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Build a fake repository, the smallest tree that the stamp reads, and make bundle_gate test against it."""
    root = tmp_path / "repo"
    (root / "src" / "embodic").mkdir(parents=True)
    (root / PACKAGE_FILE).write_text('VERSION = "1"\n', encoding="utf-8")
    (root / "resources" / "theme").mkdir(parents=True)
    (root / RESOURCE_FILE).write_text('{"accent": "#2a6"}\n', encoding="utf-8")
    monkeypatch.setattr(bundle_gate, "REPO", root)
    return root


@pytest.fixture
def frozen_cli(tmp_path: Path) -> Path:
    """Make a fake bundle and return its CLI at build/bundle/embodic/embodic-cli; its stamp belongs in build/bundle."""
    cli = tmp_path / "build" / "bundle" / "embodic" / "embodic-cli"
    cli.parent.mkdir(parents=True)
    cli.write_bytes(b"")
    return cli


def write_stamp(frozen_cli: Path, content: object) -> None:
    """Write the stamp file of the fake bundle as JSON."""
    (frozen_cli.parent.parent / STAMP_FILE).write_text(json.dumps(content), encoding="utf-8")


@pytest.mark.parametrize("required", ["1", None], ids=["required", "not-required"])
def test_a_bundle_stamped_with_this_source_is_tested(monkeypatch, repo, frozen_cli, required):
    """Catches a guard that refuses a fresh bundle, so that the bundle tests never run on a good build."""
    set_required(monkeypatch, required)
    write_stamp(frozen_cli, bundle_gate.build_tool().source_stamp(repo))

    assert bundle_gate.require_bundle(frozen_cli) is None


@refused
def test_a_bundle_without_a_stamp_is_refused(monkeypatch, repo, frozen_cli, required, outcome):
    """Catches a folder of unknown origin being tested: the one D-098c left in build/bundle had no stamp to compare."""
    set_required(monkeypatch, required)

    with pytest.raises(outcome):
        bundle_gate.require_bundle(frozen_cli)


@refused
def test_a_bundle_stamped_with_another_source_is_refused(monkeypatch, repo, frozen_cli, required, outcome):
    """Catches the 0.0.5 folder tested against 0.0.6 source: a stamp of other hashes must not pass."""
    set_required(monkeypatch, required)
    write_stamp(frozen_cli, OTHER_SOURCE)

    with pytest.raises(outcome):
        bundle_gate.require_bundle(frozen_cli)


@refused
@pytest.mark.parametrize("edited", [PACKAGE_FILE, RESOURCE_FILE], ids=["package", "resource"])
def test_an_edit_after_the_build_is_refused(monkeypatch, repo, frozen_cli, required, outcome, edited):
    """Catches a stamp that misses a change to the package source or to a resource file made after the build."""
    set_required(monkeypatch, required)
    write_stamp(frozen_cli, bundle_gate.build_tool().source_stamp(repo))
    (repo / edited).write_text("changed\n", encoding="utf-8")

    with pytest.raises(outcome):
        bundle_gate.require_bundle(frozen_cli)


@refused
def test_a_stamp_that_is_not_json_is_refused(monkeypatch, repo, frozen_cli, required, outcome):
    """Catches a half-written stamp file that raises inside the guard, or passes as no stamp at all."""
    set_required(monkeypatch, required)
    (frozen_cli.parent.parent / STAMP_FILE).write_text("{not json", encoding="utf-8")

    with pytest.raises(outcome):
        bundle_gate.require_bundle(frozen_cli)


@refused
def test_the_refusal_names_both_stamps_and_the_rebuild_command(monkeypatch, repo, frozen_cli, required, outcome):
    """Catches a refusal that leaves the reader without the two stamps to compare or the command that fixes it."""
    set_required(monkeypatch, required)
    write_stamp(frozen_cli, OTHER_SOURCE)
    expected = bundle_gate.build_tool().source_stamp(repo)

    with pytest.raises(outcome) as refusal:
        bundle_gate.require_bundle(frozen_cli)

    message = str(refusal.value)
    assert all(digest in message for digest in (*OTHER_SOURCE.values(), *expected.values()))
    assert "rebuild it with `python tools/build_bundle.py`" in message


def test_the_stamp_holds_the_package_hash_and_the_resources_hash(repo):
    """Catches a package part that selects other files than package_source_sha256: caches and non-Python files."""
    (repo / "src" / "embodic" / "__pycache__").mkdir()
    (repo / "src" / "embodic" / "__pycache__" / "stale.py").write_text("STALE = 1\n", encoding="utf-8")
    (repo / "src" / "embodic" / "notes.txt").write_text("not Python\n", encoding="utf-8")
    stamp = bundle_gate.build_tool().source_stamp(repo)

    assert stamp["package_source_sha256"] == package_source_sha256(repo / "src" / "embodic")
    assert set(stamp) == {"package_source_sha256", "resources_sha256"}


def test_the_package_hash_of_the_real_source_equals_the_registrys():
    """Catches the build script's copy of the scheme drifting from package_source_sha256, which the app reports."""
    stamp = bundle_gate.build_tool().source_stamp(bundle_gate.REPO)

    assert stamp["package_source_sha256"] == package_source_sha256(bundle_gate.REPO / "src" / "embodic")


def test_the_build_script_imports_nothing_but_the_standard_library():
    """Catches an import of embodic or NumPy: INSTALL.md section 9 runs the script with a bare Python."""
    imported: set[str] = set()
    for node in ast.walk(ast.parse(bundle_gate.BUILD_TOOL.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".")[0])

    assert imported - set(sys.stdlib_module_names) == set()


def test_the_resources_hash_covers_every_file_by_relative_posix_path_and_bytes(tmp_path):
    """Catches a hash of another scheme than package_source_sha256's: sorted path, NUL, the SHA-256 of the bytes."""
    root = tmp_path / "repo"
    (root / "src" / "embodic").mkdir(parents=True)
    (root / PACKAGE_FILE).write_text("", encoding="utf-8")
    files = {"a.txt": b"A", "sub/b.json": b"B", "sub/deeper/c.bin": b"\x00\xff"}
    for relative, content in files.items():
        (root / "resources" / relative).parent.mkdir(parents=True, exist_ok=True)
        (root / "resources" / relative).write_bytes(content)
    digest = hashlib.sha256()
    for relative in sorted(files):
        digest.update(relative.encode("utf-8") + b"\0" + hashlib.sha256(files[relative]).digest())

    assert bundle_gate.build_tool().source_stamp(root)["resources_sha256"] == digest.hexdigest()


def test_a_tree_without_package_source_has_no_stamp(tmp_path):
    """Catches a stamp written for a tree that holds no Python source, which would vouch for any bundle."""
    (tmp_path / "resources").mkdir()

    with pytest.raises(ValueError, match="no Python source"):
        bundle_gate.build_tool().source_stamp(tmp_path)


CHANGES: dict[str, Callable[[Path], object]] = {
    "edit": lambda root: (root / RESOURCE_FILE).write_text("{}\n", encoding="utf-8"),
    "rename": lambda root: (root / RESOURCE_FILE).rename(root / "resources" / "theme" / "other.json"),
    "add": lambda root: (root / "resources" / "new.txt").write_text("new\n", encoding="utf-8"),
    "remove": lambda root: (root / RESOURCE_FILE).unlink(),
}


@pytest.mark.parametrize("change", CHANGES)
def test_the_resources_hash_follows_every_change_to_the_resources(repo, change):
    """Catches a resources hash that ignores an edit, a rename, a new file or a removed file."""
    tool = bundle_gate.build_tool()
    before = tool.source_stamp(repo)["resources_sha256"]

    CHANGES[change](repo)

    assert tool.source_stamp(repo)["resources_sha256"] != before


GENERATED = ["resources/evidence/passed_tests.v1.json", "resources/evidence/passed_tests.v1.json.partial"]
KEPT = [
    "resources/evidence/equations.v1.json",
    "resources/theme/passed_tests.v1.json",
    "resources/evidence/x.partial.json",
]


@pytest.mark.parametrize("generated", GENERATED)
def test_the_stamp_ignores_the_evidence_a_release_run_writes_after_the_build(repo, generated):
    """Catches a release run that makes its own bundle look stale: the evidence file comes after the build."""
    tool = bundle_gate.build_tool()
    before = tool.source_stamp(repo)
    (repo / generated).parent.mkdir(parents=True, exist_ok=True)
    (repo / generated).write_text('{"passed": true}\n', encoding="utf-8")

    assert tool.source_stamp(repo) == before


@pytest.mark.parametrize("kept", KEPT)
def test_the_stamp_still_covers_the_other_files_beside_the_generated_ones(repo, kept):
    """Catches an exclusion that is wider than the two gitignored names: the packaged registries are resources."""
    tool = bundle_gate.build_tool()
    before = tool.source_stamp(repo)
    (repo / kept).parent.mkdir(parents=True, exist_ok=True)
    (repo / kept).write_text("{}\n", encoding="utf-8")

    assert tool.source_stamp(repo)["resources_sha256"] != before["resources_sha256"]


def test_the_stamp_does_not_depend_on_where_the_tree_lies(tmp_path, repo):
    """Catches a hash of absolute paths, which would refuse a good bundle on a checkout that moved."""
    tool = bundle_gate.build_tool()
    moved = tmp_path / "moved checkout"
    shutil.copytree(repo, moved)

    assert tool.source_stamp(moved) == tool.source_stamp(repo)


def fake_build(monkeypatch: pytest.MonkeyPatch, repo: Path, *, checks_pass: bool) -> tuple[ModuleType, Path]:
    """Return the build tool of the fake repository with every step but the stamp replaced, and its build/bundle."""
    tool = bundle_gate.build_tool()
    dist = repo / "build" / "bundle"
    (dist / "embodic").mkdir(parents=True)
    paths = {"ROOT": repo, "DIST": dist, "FOLDER": dist / "embodic", "WORK": repo / "build" / "bundle-work"}
    for name, value in paths.items():
        monkeypatch.setattr(tool, name, value)
    for step in ("ensure_build_venv", "add_licences", "run", "summarise"):
        monkeypatch.setattr(tool, step, lambda *args, **kwargs: None)
    monkeypatch.setattr(tool, "probe_build_venv", lambda: types.SimpleNamespace(python="3.11", versions={}))
    for check in ("checklist_ok", "source_ok", "qt_libraries_ok"):
        monkeypatch.setattr(tool, check, lambda: checks_pass)
    monkeypatch.setattr(tool, "sha256_of", lambda path: "0" * 64)
    return tool, dist


def test_a_good_build_writes_the_stamp_of_its_source(monkeypatch, repo):
    """Catches a build that exits 0 and leaves the folder without the stamp that the bundle tests compare."""
    tool, dist = fake_build(monkeypatch, repo, checks_pass=True)

    assert tool.main() == 0
    assert json.loads((dist / STAMP_FILE).read_text(encoding="utf-8")) == tool.source_stamp(repo)


def test_a_build_whose_checks_fail_leaves_no_stamp_not_even_the_one_of_the_build_before(monkeypatch, repo):
    """Catches an old stamp that vouches for a folder that a failed rebuild has just overwritten."""
    tool, dist = fake_build(monkeypatch, repo, checks_pass=False)
    (dist / STAMP_FILE).write_text(json.dumps(OTHER_SOURCE), encoding="utf-8")

    assert tool.main() == 1
    assert not (dist / STAMP_FILE).exists()


def test_a_build_that_stops_with_an_error_leaves_no_stamp_not_even_the_one_of_the_build_before(monkeypatch, repo):
    """Catches an old stamp that stays beside a folder that PyInstaller or hatchling left half written."""
    tool, dist = fake_build(monkeypatch, repo, checks_pass=True)
    (dist / STAMP_FILE).write_text(json.dumps(OTHER_SOURCE), encoding="utf-8")

    def stop(*args: object, **kwargs: object) -> None:
        raise subprocess.CalledProcessError(1, "PyInstaller")

    monkeypatch.setattr(tool, "run", stop)

    with pytest.raises(subprocess.CalledProcessError):
        tool.main()
    assert not (dist / STAMP_FILE).exists()
