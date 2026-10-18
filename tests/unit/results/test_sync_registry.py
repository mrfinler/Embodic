"""tools/sync_registry.py: the packaged registries equal their sources by SHA-256 (REQ-T-04)."""

import json
import shutil

import pytest
from tests.unit.results.registries import REPO, load_sync_tool


def _bytes_by_name(folder):
    """Return every file of a folder as name -> bytes, to show that a run left it as it was."""
    return {path.name: path.read_bytes() for path in sorted(folder.iterdir())}


@pytest.mark.req("REQ-T-04")
def test_sync_registry_check_passes_on_the_committed_copies(capsys):
    """Catches committed copies or a manifest that drifted from Agent 2's and Agent 5's files."""
    assert load_sync_tool().main(["--check"]) == 0
    assert "0 drifted" in capsys.readouterr().out


@pytest.mark.req("REQ-T-04")
def test_sync_registry_check_reports_an_edited_copy_and_sync_repairs_it(tmp_path, monkeypatch, capsys):
    """Catches a --check that compares sizes or names only, and a sync that is not idempotent."""
    tool = load_sync_tool()
    destination = tmp_path / "evidence"
    shutil.copytree(REPO / "resources" / "evidence", destination)
    monkeypatch.setattr(tool, "DESTINATION", destination)
    monkeypatch.setattr(tool, "MANIFEST", destination / "manifest.v1.json")
    monkeypatch.setattr(tool, "EXAMPLES_DIR", tmp_path / "examples")
    shutil.copytree(REPO / "resources" / "examples", tool.EXAMPLES_DIR)
    packaged_before = _bytes_by_name(REPO / "resources" / "examples")
    copy = destination / "equations.v1.json"
    copy.write_bytes(copy.read_bytes().replace(b'"verified"', b'"inferred"', 1))

    assert tool.main(["--check"]) == 1
    assert "equations.v1.json: differs from" in capsys.readouterr().out
    assert tool.main([]) == 0
    assert tool.main([]) == 0
    assert copy.read_bytes() == tool.SOURCES["equations.v1.json"][0].read_bytes()
    assert _bytes_by_name(REPO / "resources" / "examples") == packaged_before


@pytest.mark.req("REQ-T-04")
def test_sync_registry_check_reports_an_edited_example_and_sync_rewrites_only_the_folder_it_is_given(
    tmp_path, monkeypatch, capsys
):
    """Catches a --check blind to example drift, and a sync that writes the packaged folder instead of its own."""
    tool = load_sync_tool()
    monkeypatch.setattr(tool, "EXAMPLES_DIR", tmp_path / "examples")
    shutil.copytree(REPO / "resources" / "examples", tool.EXAMPLES_DIR)
    packaged_before = _bytes_by_name(REPO / "resources" / "examples")
    edited = tool.EXAMPLES_DIR / "wave_16p_example.embodic.json"
    original = edited.read_bytes()
    assert b'"engine_version": "0.0.1"' in original
    edited.write_bytes(original.replace(b'"engine_version": "0.0.1"', b'"engine_version": "0.0.2"', 1))

    assert tool.main(["--check"]) == 1
    assert "wave_16p_example.embodic.json: differs from the generator output" in capsys.readouterr().out
    assert tool.main([]) == 0
    assert "wave_16p_example.embodic.json: rewritten" in capsys.readouterr().out
    assert edited.read_bytes() == original
    assert _bytes_by_name(REPO / "resources" / "examples") == packaged_before


@pytest.mark.req("REQ-T-04", "REQ-K-01")
def test_sync_registry_evidence_copy_is_the_phase2_scope_filter_of_the_source():
    """Catches hand-picked evidence: the copy holds exactly the in-scope entries and no KiCad text (D-009, MT-07)."""
    tool = load_sync_tool()
    source = json.loads(tool.SOURCES["evidence.v1.json"][0].read_bytes())
    copy = json.loads((REPO / "resources" / "evidence" / "evidence.v1.json").read_bytes())
    assert [e["id"] for e in copy["entries"]] == [e["id"] for e in source["entries"] if e["phase2_scope"]]
    assert "kicad" not in json.dumps(copy).lower()
