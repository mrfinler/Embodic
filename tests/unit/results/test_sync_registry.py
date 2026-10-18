"""tools/sync_registry.py: the packaged registries equal their sources by SHA-256 (REQ-T-04).

Every test here leaves resources/evidence and resources/examples as it found them (D-062d): a sync that is not given the
real folders writes under tmp_path, so a test cannot rewrite the shipped manifest.
"""

import json
import os

import pytest
from tests.unit.results.registries import (
    REPO,
    SHIPPED_FOLDERS,
    folders_unchanged,
    load_sync_tool,
    sandbox_sync_tool,
)


@pytest.fixture(autouse=True)
def shipped_files_untouched():
    """Fail the test that writes a file of resources/evidence or resources/examples, even with equal bytes."""
    with folders_unchanged(*SHIPPED_FOLDERS):
        yield


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """Return the tool with its evidence copy, manifest and example folder redirected to copies in tmp_path."""
    return sandbox_sync_tool(tmp_path, monkeypatch)


def _bytes_by_name(folder):
    """Return every file of a folder as name -> bytes."""
    return {path.name: path.read_bytes() for path in sorted(folder.iterdir())}


@pytest.mark.req("REQ-T-04")
def test_sync_registry_check_passes_on_the_committed_copies(capsys):
    """Catches committed copies or a manifest that drifted from Agent 2's and Agent 5's files."""
    assert load_sync_tool().main(["--check"]) == 0
    assert "0 drifted" in capsys.readouterr().out


@pytest.mark.req("REQ-T-04")
def test_sync_registry_check_reports_an_edited_copy_and_sync_repairs_it(sandbox, capsys):
    """Catches a --check that compares sizes or names only, and a sync that is not idempotent."""
    tool, destination, _ = sandbox
    copy = destination / "equations.v1.json"
    copy.write_bytes(copy.read_bytes().replace(b'"verified"', b'"inferred"', 1))

    assert tool.main(["--check"]) == 1
    assert "equations.v1.json: differs from" in capsys.readouterr().out
    assert tool.main([]) == 0
    assert tool.main([]) == 0
    assert copy.read_bytes() == tool.SOURCES["equations.v1.json"][0].read_bytes()


@pytest.mark.req("REQ-T-04")
def test_sync_registry_check_reports_an_edited_example_and_sync_rewrites_only_the_folder_it_is_given(sandbox, capsys):
    """Catches a --check blind to example drift, and a sync that writes the packaged folder instead of its own."""
    tool, _, examples = sandbox
    edited = examples / "wave_16p_example.embodic.json"
    original = edited.read_bytes()
    assert b'"engine_version": "0.0.1"' in original
    edited.write_bytes(original.replace(b'"engine_version": "0.0.1"', b'"engine_version": "0.0.2"', 1))

    assert tool.main(["--check"]) == 1
    assert "wave_16p_example.embodic.json: differs from the generator output" in capsys.readouterr().out
    assert tool.main([]) == 0
    assert "wave_16p_example.embodic.json: rewritten" in capsys.readouterr().out
    assert edited.read_bytes() == original


@pytest.mark.req("REQ-T-04")
def test_sync_registry_writes_the_manifest_into_the_destination_it_is_given(sandbox, capsys):
    """Catches a manifest path fixed at import: a sync into another destination rewrote the shipped one (D-062d)."""
    tool, destination, _ = sandbox
    manifest = destination / "manifest.v1.json"
    committed = manifest.read_bytes()
    manifest.write_bytes(b"{}")

    assert tool.main(["--check"]) == 1
    assert "manifest.v1.json: missing or stale" in capsys.readouterr().out
    assert tool.main([]) == 0
    assert manifest.read_bytes() == committed


@pytest.mark.req("REQ-T-04", "REQ-N-04")
def test_sync_registry_check_reports_a_manifest_with_crlf_line_ends(sandbox, capsys):
    """Catches a --check that reads the manifest as text, so the CRLF file from the Windows gate passed as current."""
    tool, destination, _ = sandbox
    manifest = destination / "manifest.v1.json"
    committed = manifest.read_bytes()
    manifest.write_bytes(committed.replace(b"\n", b"\r\n"))

    assert tool.main(["--check"]) == 1
    assert "manifest.v1.json: missing or stale" in capsys.readouterr().out
    assert tool.main([]) == 0
    assert manifest.read_bytes() == committed


@pytest.mark.req("REQ-T-04", "REQ-N-04")
@pytest.mark.usefixtures("windows_text_mode")
def test_windows_text_mode_translates_a_plain_text_write(tmp_path):
    """Catches a fixture that no longer simulates Windows, which would let the sync check below pass vacuously."""
    plain = tmp_path / "plain.txt"
    plain.write_text("a\nb\n", encoding="utf-8")
    assert plain.read_bytes() == b"a\r\nb\r\n"


@pytest.mark.req("REQ-T-04", "REQ-N-04")
@pytest.mark.usefixtures("windows_text_mode")
def test_sync_registry_writes_the_committed_bytes_under_windows_text_mode(sandbox):
    """Catches the manifest written with the platform newline: CRLF on Windows, so the shipped file changed (D-062d)."""
    tool, evidence, examples = sandbox
    (evidence / "manifest.v1.json").unlink()

    assert tool.main([]) == 0
    for written, shipped in ((evidence, REPO / "resources" / "evidence"), (examples, REPO / "resources" / "examples")):
        assert _bytes_by_name(written) == _bytes_by_name(shipped)


@pytest.mark.req("REQ-T-04")
def test_sync_registry_evidence_copy_is_the_phase2_scope_filter_of_the_source():
    """Catches hand-picked evidence: the copy holds exactly the in-scope entries and no KiCad text (D-009, MT-07)."""
    tool = load_sync_tool()
    source = json.loads(tool.SOURCES["evidence.v1.json"][0].read_bytes())
    copy = json.loads((REPO / "resources" / "evidence" / "evidence.v1.json").read_bytes())
    assert [e["id"] for e in copy["entries"]] == [e["id"] for e in source["entries"] if e["phase2_scope"]]
    assert "kicad" not in json.dumps(copy).lower()


@pytest.mark.req("REQ-T-04")
def test_folders_unchanged_sees_a_rewrite_with_equal_bytes(tmp_path):
    """Catches a guard that compares bytes only, which cannot see a rewrite on Linux where the bytes come out equal."""
    shipped = tmp_path / "shipped.json"
    shipped.write_bytes(b"{}\n")
    os.utime(shipped, ns=(10**9, 10**9))  # an old stamp, so that any later write carries another one

    with folders_unchanged(tmp_path):
        pass
    with pytest.raises(AssertionError, match=r"shipped\.json"), folders_unchanged(tmp_path):
        shipped.write_bytes(b"{}\n")
