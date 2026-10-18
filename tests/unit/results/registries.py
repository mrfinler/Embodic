"""Registry builders for the results tests: raw packaged JSON, EC-05 in its contract shape, all tests passed.

Also the lever that keeps the sync tool's tests off the shipped files: a sandbox copy of the two folders it writes, and
a check that the shipped folders came out of a test as they went in (D-062d).
"""

import dataclasses
import hashlib
import importlib.util
import json
import shutil
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from embodic.paths import resource_root
from embodic.results.registry import Registry, parse_registry

# requirements.md section 6 (DEF-23 closure): the typed EC-05 fields Agent 2 is to add. Registry v1 has them as prose.
EC05_CONTRACT_FIELDS = {
    "threshold": 0.10,
    "metric_bound": "lower_bound",
    "calibration_status": "inferred",
    "transfer_status": "assumption",
    "threshold_status": "assumption",
    "independent_oracles": ["OR-01"],
    "dependent_oracles": ["OR-07", "OR-08"],
}


REPO = Path(__file__).resolve().parents[3]
SHIPPED_FOLDERS = (REPO / "resources" / "evidence", REPO / "resources" / "examples")


def load_sync_tool():
    """Import tools/sync_registry.py, which is a script and not a package module."""
    spec = importlib.util.spec_from_file_location("sync_registry", REPO / "tools" / "sync_registry.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sandbox_sync_tool(tmp_path: Path, monkeypatch):
    """Return the sync tool with its evidence and example folders redirected to copies under tmp_path, and the copies.

    Only DESTINATION and EXAMPLES_DIR are patched: the manifest has to follow DESTINATION by itself.
    """
    tool = load_sync_tool()
    evidence, examples = tmp_path / "resources" / "evidence", tmp_path / "resources" / "examples"
    shutil.copytree(REPO / "resources" / "evidence", evidence)
    shutil.copytree(REPO / "resources" / "examples", examples)
    monkeypatch.setattr(tool, "DESTINATION", evidence)
    monkeypatch.setattr(tool, "EXAMPLES_DIR", examples)
    return tool, evidence, examples


def _signature(folders: tuple[Path, ...]) -> dict[str, tuple[str, int]]:
    """Return each file below the folders as path -> (SHA-256, mtime in ns); the time shows a rewrite to equal bytes."""
    return {
        path.as_posix(): (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)
        for folder in folders
        for path in sorted(folder.rglob("*"))
        if path.is_file()
    }


@contextmanager
def folders_unchanged(*folders: Path) -> Iterator[None]:
    """Fail when the body adds, removes, rewrites or touches a file below the folders, even to the same bytes."""
    before = _signature(folders)
    yield
    after = _signature(folders)
    changed = sorted(path for path in before.keys() | after.keys() if before.get(path) != after.get(path))
    assert not changed, f"the test wrote shipped files: {changed}"


def raw_documents() -> tuple[dict, dict]:
    """Return fresh copies of the packaged equation and evidence JSON."""
    folder = resource_root() / "evidence"
    return tuple(
        json.loads((folder / name).read_text(encoding="utf-8")) for name in ("equations.v1.json", "evidence.v1.json")
    )


def with_all_tests_passed(registry: Registry) -> Registry:
    """Return the registry as it would be in a build where every linked test passed."""
    return dataclasses.replace(
        registry, passed_tests=frozenset(t for e in registry.equations.values() for t in e.tests)
    )


def contract_shaped() -> Registry:
    """Return the shipped registry with EC-05 carrying the typed DEF-23 fields of requirements.md section 6."""
    equations, evidence = raw_documents()
    eq05 = next(e for e in equations["equations"] if e["id"] == "EQ-05")
    eq05["validity_checks"][0].update(EC05_CONTRACT_FIELDS)
    return parse_registry(equations, evidence, version="test")
