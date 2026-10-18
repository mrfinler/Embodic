"""D-056b: tools/sync_registry.py regenerates the packaged examples after a registry change and --check reports drift.

Each example file carries `registry_version` (REQ-T-07), so a registry change changes the bytes of all five.
"""

import hashlib
import json
from pathlib import Path

import pytest
from tests.unit.results.registries import REPO, SHIPPED_FOLDERS, folders_unchanged, load_sync_tool, sandbox_sync_tool

EXAMPLE_FILES = sorted(path.name for path in (REPO / "resources" / "examples").glob("*.embodic.json"))


def _sha12(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


@pytest.fixture(autouse=True)
def shipped_files_untouched():
    """Fail the test that writes a file of resources/evidence or resources/examples, even with equal bytes (D-062d)."""
    with folders_unchanged(*SHIPPED_FOLDERS):
        yield


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """Return the tool with its evidence copy, manifest and example folder redirected to copies in tmp_path."""
    return sandbox_sync_tool(tmp_path, monkeypatch)


@pytest.mark.req("REQ-T-07", "REQ-T-04")
def test_check_passes_on_the_committed_examples(capsys):
    """Catches an example file that was edited by hand or kept across a registry change."""
    assert load_sync_tool().main(["--check"]) == 0
    assert "0 drifted" in capsys.readouterr().out


@pytest.mark.req("REQ-T-07", "REQ-T-04")
def test_check_reports_an_edited_example_and_sync_restores_its_bytes(sandbox, capsys):
    """Catches a --check that ignores the example folder, and a sync that leaves a stale example or repeats itself."""
    tool, _, examples = sandbox
    edited = examples / "spiral_12c14p.embodic.json"
    original = edited.read_bytes()
    edited.write_bytes(original.replace(b'"registry_version": "v1+', b'"registry_version": "v1+0', 1))
    assert edited.read_bytes() != original

    assert tool.main(["--check"]) == 1
    assert "spiral_12c14p.embodic.json: differs from the generator output" in capsys.readouterr().out
    assert tool.main([]) == 0
    assert edited.read_bytes() == original
    assert tool.main([]) == 0
    assert "0 drifted" in capsys.readouterr().out


@pytest.mark.req("REQ-T-07", "REQ-T-04")
def test_a_registry_change_rewrites_only_the_registry_version_of_every_example(sandbox, monkeypatch):
    """Catches an example that keeps the old registry version after a registry change, or moves anything else."""
    tool, evidence, examples = sandbox
    source = tool.SOURCES["equations.v1.json"][0]
    monkeypatch.setattr(tool, "SOURCES", {**tool.SOURCES, "equations.v1.json": (source, lambda raw: raw + b"\n")})
    before = {name: json.loads((examples / name).read_text(encoding="utf-8")) for name in EXAMPLE_FILES}

    assert tool.main(["--check"]) == 1
    assert tool.main([]) == 0

    version = f"v1+{_sha12(evidence / 'equations.v1.json')}.{_sha12(evidence / 'evidence.v1.json')}"
    assert _sha12(evidence / "equations.v1.json") != before[EXAMPLE_FILES[0]]["registry_version"][3:15]
    for name in EXAMPLE_FILES:
        after = json.loads((examples / name).read_text(encoding="utf-8"))
        assert after["registry_version"] == version != before[name]["registry_version"]
        assert {k: v for k, v in after.items() if k != "registry_version"} == {
            k: v for k, v in before[name].items() if k != "registry_version"
        }
