"""D-056d: interfaces.md names every issue code that src defines or emits.

The lever is docs/phase2/architecture/checks/issue_code_coverage.py. It reads the code literals of src/embodic and the
catalogue, and exits 1 when interfaces.md does not name one of them.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
LEVER = REPO / "docs" / "phase2" / "architecture" / "checks" / "issue_code_coverage.py"


def run_lever(script: Path) -> subprocess.CompletedProcess[str]:
    """Run the coverage script in a clean interpreter and capture its report."""
    return subprocess.run([sys.executable, "-I", str(script)], capture_output=True, encoding="utf-8", check=False)


@pytest.mark.req("REQ-F-14")
def test_interfaces_md_names_every_issue_code_of_src():
    """Catches a unit that adds an issue code and leaves the contract silent about its pointers, limit and hint."""
    result = run_lever(LEVER)
    missing = [line for line in result.stdout.splitlines() if line.startswith("MISSING ")]
    assert missing == []
    assert result.returncode == 0, result.stderr


@pytest.mark.req("REQ-F-14")
def test_lever_reports_the_codes_that_a_planted_tree_leaves_unnamed(tmp_path):
    """Catches a lever that passes every tree: a catalogue key and a code literal are each missing from the contract."""
    checks = tmp_path / "docs" / "phase2" / "architecture" / "checks"
    checks.mkdir(parents=True)
    script = checks / LEVER.name
    shutil.copy(LEVER, script)
    (checks.parent / "interfaces.md").write_text(
        "The codes `INVALID_KNOWN` and `RANGE_NAMED_ALSO`.\n", encoding="utf-8"
    )
    catalogue = tmp_path / "src" / "embodic" / "errors" / "catalogue"
    catalogue.mkdir(parents=True)
    (catalogue / "planted.py").write_text(
        'MESSAGES = {"INVALID_KNOWN": "Named.", "INVALID_ONLY_IN_CATALOGUE": "Not named."}\n', encoding="utf-8"
    )
    (catalogue.parents[1] / "planted_emitter.py").write_text(
        'NAMED = "RANGE_NAMED_ALSO"\nUNNAMED = "UNBUILDABLE_ONLY_A_LITERAL"\n', encoding="utf-8"
    )
    result = run_lever(script)
    missing = sorted(line.split()[1] for line in result.stdout.splitlines() if line.startswith("MISSING "))
    assert missing == ["INVALID_ONLY_IN_CATALOGUE", "UNBUILDABLE_ONLY_A_LITERAL"]
    assert result.returncode == 1
