"""REQ-T-09: tools/trace_matrix.py exits 1 on a test without a REQ marker and names that test."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

TOOL = Path(__file__).resolve().parents[3] / "tools" / "trace_matrix.py"
MARKED = "tests/unit/a.py::test_marked"
UNMARKED = "tests/unit/a.py::test_without_a_marker"


def run_gate(tmp_path: Path, records: list[dict[str, object]]) -> subprocess.CompletedProcess[str]:
    """Run the tool on a REQ report made of the given records and return the finished process."""
    report = tmp_path / "req_report.json"
    report.write_text(json.dumps(records), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(TOOL), "--report", str(report), "--out", str(tmp_path / "matrix.md")],
        capture_output=True,
        text=True,
        check=False,
    )


def record(nodeid: str, req: list[str]) -> dict[str, object]:
    """Return one report record in the shape that tests/conftest.py writes."""
    return {"nodeid": nodeid, "req": req, "eq": [], "eqt": [], "outcome": "passed"}


@pytest.mark.req("REQ-T-09")
def test_gate_exits_1_and_names_a_test_without_a_req_marker(tmp_path: Path) -> None:
    """Catches a gate that finds an unmarked test but still exits 0, which lets it into the matrix unnoticed."""
    done = run_gate(tmp_path, [record(MARKED, ["REQ-T-09"]), record(UNMARKED, [])])
    assert done.returncode == 1
    assert UNMARKED in done.stdout
    assert MARKED not in done.stdout


@pytest.mark.req("REQ-T-09")
def test_gate_exits_0_when_every_test_is_marked(tmp_path: Path) -> None:
    """Control. Catches a gate that exits 1 whatever the report holds, which would make the test above pass."""
    done = run_gate(tmp_path, [record(MARKED, ["REQ-T-09"])])
    assert done.returncode == 0, done.stdout
    assert UNMARKED not in done.stdout
