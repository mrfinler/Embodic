"""tools/sync_registry.py: the packaged registries equal their sources by SHA-256 (REQ-T-04)."""

import importlib.util
import shutil
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]


def load_tool():
    """Import tools/sync_registry.py, which is a script and not a package module."""
    spec = importlib.util.spec_from_file_location("sync_registry", REPO / "tools" / "sync_registry.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.req("REQ-T-04")
def test_sync_registry_check_passes_on_the_committed_copies(capsys):
    """Catches committed copies or a manifest that drifted from Agent 2's and Agent 5's files."""
    assert load_tool().main(["--check"]) == 0
    assert "0 drifted" in capsys.readouterr().out


@pytest.mark.req("REQ-T-04")
def test_sync_registry_check_reports_an_edited_copy_and_sync_repairs_it(tmp_path, monkeypatch, capsys):
    """Catches a --check that compares sizes or names only, and a sync that is not idempotent."""
    tool = load_tool()
    destination = tmp_path / "evidence"
    shutil.copytree(REPO / "resources" / "evidence", destination)
    monkeypatch.setattr(tool, "DESTINATION", destination)
    monkeypatch.setattr(tool, "MANIFEST", destination / "manifest.v1.json")
    copy = destination / "equations.v1.json"
    copy.write_bytes(copy.read_bytes().replace(b'"verified"', b'"inferred"', 1))

    assert tool.main(["--check"]) == 1
    assert "equations.v1.json: differs from" in capsys.readouterr().out
    assert tool.main([]) == 0
    assert tool.main([]) == 0
    assert copy.read_bytes() == tool.SOURCES["equations.v1.json"].read_bytes()
