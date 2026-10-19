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


def run_gate_on_reports(tmp_path: Path, *reports: list[dict[str, object]]) -> subprocess.CompletedProcess[str]:
    """Run the tool on several REQ reports given to one --report option; the matrix goes to tmp_path / matrix.md."""
    paths = []
    for number, records in enumerate(reports):
        path = tmp_path / f"req_report_{number}.json"
        path.write_text(json.dumps(records), encoding="utf-8")
        paths.append(str(path))
    return subprocess.run(
        [sys.executable, str(TOOL), "--report", *paths, "--out", str(tmp_path / "matrix.md")],
        capture_output=True,
        text=True,
        check=False,
    )


def latency_reports(latency_outcome: str) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Return the main and the latency report of one run: the latency test is `not run` in the main one (D-074)."""
    steady, slow = "tests/unit/a.py::test_steady", "tests/ui/b.py::test_latency"
    main = [record(steady, ["REQ-T-09"]), {**record(slow, ["REQ-N-02"]), "outcome": "not run"}]
    latency = [
        {**record(steady, ["REQ-T-09"]), "outcome": "not run"},
        {**record(slow, ["REQ-N-02"]), "outcome": latency_outcome},
    ]
    return main, latency


@pytest.mark.req("REQ-T-09", "REQ-N-02")
@pytest.mark.parametrize(("latency_outcome", "passed"), [("passed", "1"), ("failed", "0")])
def test_gate_counts_a_test_once_and_takes_its_outcome_from_the_report_that_ran_it(tmp_path, latency_outcome, passed):
    """Catches a gate that reads the first report only, or that counts the 4000 shared tests twice."""
    done = run_gate_on_reports(tmp_path, *latency_reports(latency_outcome))

    assert done.returncode == 0, done.stdout
    assert " 2 tests," in done.stdout
    row = next(
        line for line in (tmp_path / "matrix.md").read_text(encoding="utf-8").splitlines() if "| REQ-N-02 |" in line
    )
    assert row.endswith(f"| 1 | {passed} |")


@pytest.mark.req("REQ-T-09")
def test_gate_still_names_an_unmarked_test_that_only_the_second_report_holds(tmp_path):
    """Control. Catches a merge that stops TR-02 at the first report."""
    done = run_gate_on_reports(tmp_path, [record(MARKED, ["REQ-T-09"])], [record(UNMARKED, [])])

    assert done.returncode == 1
    assert UNMARKED in done.stdout
