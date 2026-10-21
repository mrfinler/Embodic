"""TR-01 as the release gate runs it: the untested-row flag, the manual-record input and the gate in tools/ci.py."""

import importlib.util
import json
import subprocess
from collections.abc import Sequence
from pathlib import Path
from types import ModuleType

import pytest

TOOLS = Path(__file__).resolve().parents[3] / "tools"


def _load_tool(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


trace_matrix = _load_tool("trace_matrix")
ci = _load_tool("ci")
TREE_VERSION = trace_matrix.read_version(trace_matrix.EMBODIC_INIT)

EXISTING_RECORD = "pyproject.toml"  # a repository-relative path that exists; the content of a record is not read
MISSING_RECORD = "docs/phase3/fable/no_such_record.md"
MANUAL_ONLY_ROW = "REQ-N-07"
CURRENT_VERSION = f"{TREE_VERSION} (release c25d8a9)"  # a record stamp begins with the version under test
STALE_VERSION = "older build c0f4894"  # begins with no release version


def write_requirements(path: Path, rows: Sequence[tuple[str, str, str, str]]) -> Path:
    """Write a requirements file of (REQ ID, disposition, priority, milestone) rows in the nine-cell table shape."""
    lines = [
        f"| {req} | {disp} | statement | source | {prio} | acceptance | {milestone} | owner | TEST-01 |"
        for req, disp, prio, milestone in rows
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_report(path: Path, tests: Sequence[tuple[str, str]]) -> Path:
    """Write a REQ report of (REQ ID, outcome) tests, one marker each."""
    records = [
        {"nodeid": f"tests/t.py::test_{i}", "req": [req], "eq": [], "eqt": [], "outcome": outcome}
        for i, (req, outcome) in enumerate(tests)
    ]
    path.write_text(json.dumps(records), encoding="utf-8")
    return path


def manual_record(
    req: str = MANUAL_ONLY_ROW,
    *,
    result: str = "passed",
    record: str = EXISTING_RECORD,
    version: str = CURRENT_VERSION,
    accepted: str | None = None,
) -> dict[str, str]:
    """Return one manual record with the five keys of interfaces.md section 3.2, and `accepted` when it is given."""
    entry = {"req": req, "test_id": "PK-06", "record": record, "embodic_version": version, "result": result}
    return entry if accepted is None else {**entry, "accepted": accepted}


def write_records(path: Path, records: object) -> Path:
    """Write the manual-record index."""
    path.write_text(json.dumps(records), encoding="utf-8")
    return path


@pytest.fixture
def manual_only_project(tmp_path: Path) -> dict[str, Path]:
    """Return a project whose must row REQ-N-07 (M5) has no test, next to a must row REQ-F-01 (M1) that has one."""
    return {
        "requirements": write_requirements(
            tmp_path / "requirements.md",
            [("REQ-F-01", "carried", "must", "M1"), (MANUAL_ONLY_ROW, "amended", "must", "M5")],
        ),
        "report": write_report(tmp_path / "report.json", [("REQ-F-01", "passed")]),
        "out": tmp_path / "matrix.md",
        "records": write_records(tmp_path / "no_records.json", []),
    }


def run_trace_matrix(project: dict[str, Path], *extra: str, capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    """Run the script's main() on the fixture files and return (exit code, stdout)."""
    argv = [f"--report={project['report']}", f"--requirements={project['requirements']}", f"--out={project['out']}"]
    code = trace_matrix.main([*argv, *extra])
    return code, capsys.readouterr().out


@pytest.mark.req("REQ-T-09", "REQ-N-10")
def test_tr01_flag_lists_a_live_must_row_that_has_neither_a_passing_test_nor_a_manual_record(
    manual_only_project, capsys
):
    """Catches a flag that is accepted and ignored: the row stays untested and the gate still exits 0."""
    code, out = run_trace_matrix(manual_only_project, "--fail-untested-through=M5", capsys=capsys)
    assert code == 1
    assert MANUAL_ONLY_ROW in out
    assert "REQ-F-01" not in out


@pytest.mark.req("REQ-T-09")
def test_tr01_a_passed_manual_record_covers_the_row_and_the_summary_counts_it_apart(
    manual_only_project, tmp_path, capsys
):
    """Catches a manual input that is read but not counted, and one that is counted as an automated test."""
    records = write_records(tmp_path / "records.json", [manual_record()])
    code, out = run_trace_matrix(
        manual_only_project, "--fail-untested-through=M5", f"--manual-records={records}", capsys=capsys
    )
    assert code == 0
    assert "manual: 1" in out
    assert "1 requirements with a passing test" in out  # the record does not turn into an automated test
    assert "untested due: 0" in out


@pytest.mark.req("REQ-T-09", "REQ-N-10")
def test_tr01_a_record_of_the_version_under_test_counts_and_is_not_listed_as_stale(
    manual_only_project, tmp_path, capsys
):
    """D-083c. Catches a currency check that compares the whole stamp: it must only begin with the version."""
    assert CURRENT_VERSION != TREE_VERSION
    records = write_records(tmp_path / "records.json", [manual_record(version=CURRENT_VERSION)])
    code, out = run_trace_matrix(
        manual_only_project, "--fail-untested-through=M5", f"--manual-records={records}", capsys=capsys
    )
    assert code == 0, out
    assert "manual: 1" in out
    assert "untested due: 0" in out
    assert "stale" not in out


@pytest.mark.req("REQ-T-09", "REQ-N-10")
def test_tr01_a_stale_record_is_listed_with_its_path_and_d061d_and_is_not_counted(
    manual_only_project, tmp_path, capsys
):
    """D-083c. Catches a release gate that counts a record of an older build, or lists it without its path or rule."""
    stale = manual_record(version=STALE_VERSION, record="README.md")
    records = write_records(tmp_path / "records.json", [stale, manual_record("REQ-F-01")])
    _, out = run_trace_matrix(
        manual_only_project, "--fail-untested-through=M5", f"--manual-records={records}", capsys=capsys
    )
    listed = [line for line in out.splitlines() if "stale" in line]
    assert len(listed) == 1
    assert "README.md" in listed[0] and "D-061d" in listed[0]
    assert "manual: 1" in out


@pytest.mark.req("REQ-T-09", "REQ-N-10")
def test_tr01_a_due_row_whose_only_record_is_stale_fails(manual_only_project, tmp_path, capsys):
    """D-083c. Catches a stale record that still covers its row: the gate would pass on an old build's walkthrough."""
    records = write_records(tmp_path / "records.json", [manual_record(version=STALE_VERSION)])
    code, out = run_trace_matrix(
        manual_only_project, "--fail-untested-through=M5", f"--manual-records={records}", capsys=capsys
    )
    assert code == 1
    assert "untested due: 1" in out
    assert MANUAL_ONLY_ROW in out.split("untested due: 1", 1)[1]


@pytest.mark.req("REQ-T-09")
def test_tr01_a_failed_manual_record_does_not_cover_the_row_and_is_not_counted(manual_only_project, tmp_path, capsys):
    """Catches a record that covers its row whatever its result: a failed walkthrough must not pass the gate."""
    records = write_records(tmp_path / "records.json", [manual_record(result="failed")])
    code, out = run_trace_matrix(
        manual_only_project, "--fail-untested-through=M5", f"--manual-records={records}", capsys=capsys
    )
    assert code == 1
    assert MANUAL_ONLY_ROW in out
    assert "manual: 0" in out


@pytest.fixture
def covered_project(manual_only_project, tmp_path) -> dict[str, Path]:
    """Return the project with a passing test for every must row, so that only a record can fail the run."""
    covered = write_report(tmp_path / "covered.json", [("REQ-F-01", "passed"), (MANUAL_ONLY_ROW, "passed")])
    return {**manual_only_project, "report": covered}


@pytest.mark.req("REQ-T-09", "REQ-N-10")
def test_tr01_a_failed_record_fails_the_run_and_is_listed_even_when_a_test_covers_its_row(
    covered_project, tmp_path, capsys
):
    """D-093c (DEF-UV21-01). Catches a failed record that is dropped in silence while its row is covered elsewhere."""
    failed = manual_record(result="failed", record="README.md")
    records = write_records(tmp_path / "records.json", [manual_record("REQ-F-01"), failed])
    code, out = run_trace_matrix(
        covered_project, "--fail-untested-through=M5", f"--manual-records={records}", capsys=capsys
    )
    listed = [line for line in out.splitlines() if "README.md" in line]
    assert code == 1, out
    assert len(listed) == 1
    assert "failed" in listed[0] and "accepted" not in listed[0]
    assert "untested due: 0" in out


@pytest.mark.req("REQ-T-09", "REQ-N-10")
def test_tr01_every_record_that_did_not_pass_is_listed(covered_project, tmp_path, capsys):
    """D-093c. Catches a list that stops at the first failed record."""
    records = write_records(
        tmp_path / "records.json",
        [manual_record(result="failed", record="README.md"), manual_record(result="failed", record="pyproject.toml")],
    )
    _, out = run_trace_matrix(
        covered_project, "--fail-untested-through=M5", f"--manual-records={records}", capsys=capsys
    )
    assert len([line for line in out.splitlines() if "README.md" in line]) == 1
    assert len([line for line in out.splitlines() if "pyproject.toml" in line]) == 1


@pytest.mark.req("REQ-T-09", "REQ-N-10")
def test_tr01_a_failed_record_that_names_its_decision_is_listed_as_accepted_and_the_run_passes(
    covered_project, tmp_path, capsys
):
    """D-093c. Catches an `accepted` field that is ignored, or an accepted record that is left out of the list."""
    accepted = manual_record(result="failed", record="README.md", accepted="D-091")
    records = write_records(tmp_path / "records.json", [accepted])
    code, out = run_trace_matrix(
        covered_project, "--fail-untested-through=M5", f"--manual-records={records}", capsys=capsys
    )
    listed = [line for line in out.splitlines() if "README.md" in line]
    assert code == 0, out
    assert len(listed) == 1
    assert "accepted" in listed[0] and "D-091" in listed[0]


@pytest.mark.req("REQ-T-09", "REQ-N-10")
@pytest.mark.parametrize("accepted", [None, "D-091"], ids=["unaccepted", "accepted"])
def test_tr01_a_failed_record_is_never_counted_as_coverage(manual_only_project, tmp_path, capsys, accepted):
    """D-093c. Catches an accepted record that covers its row: acceptance excuses the failure, it is not a pass."""
    records = write_records(tmp_path / "records.json", [manual_record(result="failed", accepted=accepted)])
    code, out = run_trace_matrix(
        manual_only_project, "--fail-untested-through=M5", f"--manual-records={records}", capsys=capsys
    )
    assert code == 1
    assert "manual: 0" in out
    assert "untested due: 1" in out
    assert MANUAL_ONLY_ROW in out.split("untested due: 1", 1)[1]


@pytest.mark.req("REQ-T-09")
def test_tr01_without_the_flag_a_failed_record_is_not_listed(covered_project, tmp_path, capsys):
    """D-093c. Catches the rule leaking into the profiles that do not enforce TR-01: it applies under the flag."""
    records = write_records(tmp_path / "records.json", [manual_record(result="failed", record="README.md")])
    code, out = run_trace_matrix(covered_project, f"--manual-records={records}", capsys=capsys)
    assert code == 0, out
    assert "README.md" not in out


@pytest.mark.req("REQ-T-09")
@pytest.mark.parametrize(
    "accepted",
    ["91", "decision D-091", "D-91", "D-999"],
    ids=["number-only", "prose", "short-number", "no-such-row"],
)
def test_tr01_an_accepted_field_that_names_no_decision_row_is_an_invalid_record(
    covered_project, tmp_path, capsys, accepted
):
    """D-093c. Catches an `accepted` that any text satisfies: it must name a D-nnn row of docs/decision_log.md."""
    bad = manual_record(result="failed", accepted=accepted)
    records = write_records(tmp_path / "records.json", [bad])
    code, out = run_trace_matrix(
        covered_project, "--fail-untested-through=M5", f"--manual-records={records}", capsys=capsys
    )
    assert code == 1
    assert "invalid manual records: 1" in out
    assert repr(accepted) in out or accepted in out


@pytest.mark.req("REQ-T-09", "REQ-N-10")
def test_tr01_the_committed_index_passes_the_release_rule_for_its_failed_record(tmp_path, capsys):
    """D-093c. Catches a committed record that did not pass and names no decision: the release gate would fail on it.

    The requirements are the rows the committed index names, each with a passing test, so only the records decide.
    """
    committed = json.loads(ci.MANUAL_RECORDS.read_text(encoding="utf-8"))
    rows = sorted({entry["req"] for entry in committed})
    project = {
        "requirements": write_requirements(tmp_path / "requirements.md", [(r, "carried", "must", "M1") for r in rows]),
        "report": write_report(tmp_path / "report.json", [(r, "passed") for r in rows]),
        "out": tmp_path / "matrix.md",
    }
    code, out = run_trace_matrix(
        project, "--fail-untested-through=M5", f"--manual-records={ci.MANUAL_RECORDS}", capsys=capsys
    )
    assert code == 0, out
    listed = [line for line in out.splitlines() if "PF-01" in line]
    assert len(listed) == 1
    assert "accepted" in listed[0] and "D-091" in listed[0]


@pytest.mark.req("REQ-T-09")
def test_tr01_a_manual_record_for_another_row_leaves_this_row_listed(manual_only_project, tmp_path, capsys):
    """Catches a record that covers every row instead of the row named in `req`."""
    records = write_records(tmp_path / "records.json", [manual_record("REQ-F-01")])
    code, out = run_trace_matrix(
        manual_only_project, "--fail-untested-through=M5", f"--manual-records={records}", capsys=capsys
    )
    assert code == 1
    assert MANUAL_ONLY_ROW in out


@pytest.mark.req("REQ-T-09", "REQ-N-10")
def test_tr01_lists_only_live_must_rows(tmp_path, capsys):
    """Catches a flag that lists should, could and withdrawn rows, which TR-01 does not require a test for."""
    project = {
        "requirements": write_requirements(
            tmp_path / "requirements.md",
            [
                ("REQ-F-01", "carried", "should", "M1"),
                ("REQ-F-02", "carried", "could", "M2"),
                ("REQ-F-03", "withdrawn", "must", "M3"),
            ],
        ),
        "report": write_report(tmp_path / "report.json", []),
        "out": tmp_path / "matrix.md",
    }
    code, out = run_trace_matrix(project, "--fail-untested-through=M5", capsys=capsys)
    assert code == 0
    assert "untested due: 0" in out


@pytest.mark.req("REQ-T-09")
def test_tr01_without_the_flag_no_row_is_listed(manual_only_project, capsys):
    """Catches a default that enforces TR-01 in the commit and nightly profiles, which skip the release-only tests."""
    code, out = run_trace_matrix(manual_only_project, capsys=capsys)
    assert code == 0
    assert "untested due: 0" in out


@pytest.mark.req("REQ-T-09")
@pytest.mark.parametrize(
    ("bad_record", "named"),
    [
        (manual_record(result="Passed"), "Passed"),
        (manual_record("REQ-X-99"), "REQ-X-99"),
        (manual_record(record=MISSING_RECORD), MISSING_RECORD),
        ({k: v for k, v in manual_record().items() if k != "record"} | {"test_id": "PK-99"}, "PK-99"),
    ],
    ids=["unknown-result", "unknown-req", "missing-record-file", "missing-key"],
)
def test_tr01_a_malformed_manual_record_fails_the_run_and_is_named(
    manual_only_project, tmp_path, capsys, bad_record, named
):
    """Catches a typo hiding a gap: every row here is covered by a test, so only the record check can fail the run."""
    covered = write_report(tmp_path / "covered.json", [("REQ-F-01", "passed"), (MANUAL_ONLY_ROW, "passed")])
    records = write_records(tmp_path / "records.json", [manual_record(), bad_record])
    project = {**manual_only_project, "report": covered}
    code, out = run_trace_matrix(project, f"--manual-records={records}", capsys=capsys)
    assert code == 1
    assert named in out


@pytest.mark.req("REQ-T-09")
@pytest.mark.parametrize("index_text", [json.dumps(manual_record()), "[{"], ids=["one-object", "invalid-json"])
def test_tr01_a_manual_record_index_that_is_not_a_json_list_fails_the_run(
    manual_only_project, tmp_path, capsys, index_text
):
    """Catches an index shaped as one object, which would be read as its keys, and one that is not JSON."""
    covered = write_report(tmp_path / "covered.json", [("REQ-F-01", "passed"), (MANUAL_ONLY_ROW, "passed")])
    records = tmp_path / "records.json"
    records.write_text(index_text, encoding="utf-8")
    project = {**manual_only_project, "report": covered}
    code, out = run_trace_matrix(project, f"--manual-records={records}", capsys=capsys)
    assert code == 1
    assert "manual records:" in out


def release_trace_gate_argv(profile_name: str, project: dict[str, Path], *extra: str) -> tuple[str, list[str]]:
    """Return the name and the command of the trace-matrix gate of a profile, pointed at the fixture project.

    The gate's own arguments come first, so its flags are exactly those of the gate. Later occurrences of an option
    replace earlier ones, which swaps only the files. A gate that reads the committed manual-record index reads the
    project's index instead, so records added to the committed index cannot change these results (DEF-UV12b-01).
    """
    gate = next(g for g in ci.gates_for(ci.PROFILES[profile_name]) if g.name.startswith("trace matrix"))
    swap = [f"--report={project['report']}", f"--requirements={project['requirements']}", f"--out={project['out']}"]
    if any(arg.startswith("--manual-records=") for arg in gate.argv):
        swap.append(f"--manual-records={project['records']}")
    return gate.name, [*gate.argv, *swap, *extra]


def run_gate(argv: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a gate command as ci.py does and capture its output."""
    return subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", check=False)


@pytest.mark.req("REQ-T-09", "REQ-N-10")
def test_tr01_release_gate_fails_on_an_untested_must_row(manual_only_project):
    """Catches a release profile that does not pass the flag: this gate must exit 1 and list the row."""
    name, argv = release_trace_gate_argv("release", manual_only_project)
    result = run_gate(argv)
    assert name == "trace matrix (TR-01, TR-02)"
    assert result.returncode == 1, result.stdout
    assert MANUAL_ONLY_ROW in result.stdout


@pytest.mark.req("REQ-T-09", "REQ-N-10")
def test_tr01_release_gate_passes_when_a_manual_record_covers_the_row(manual_only_project, tmp_path):
    """Catches a release gate that cannot take the manual input, which would leave REQ-N-07 failing for good."""
    records = write_records(tmp_path / "records.json", [manual_record()])
    _, argv = release_trace_gate_argv("release", manual_only_project, f"--manual-records={records}")
    result = run_gate(argv)
    assert result.returncode == 0, result.stdout
    assert "manual: 1" in result.stdout


@pytest.mark.req("REQ-T-09")
def test_tr01_release_gate_passes_with_an_empty_manual_record_index(tmp_path):
    """Catches a release gate that fails on an index of no records: with every row tested it must pass and add 0."""
    project = {
        "requirements": write_requirements(tmp_path / "requirements.md", [("REQ-F-01", "carried", "must", "M1")]),
        "report": write_report(tmp_path / "report.json", [("REQ-F-01", "passed")]),
        "out": tmp_path / "matrix.md",
        "records": write_records(tmp_path / "records.json", []),
    }
    _, argv = release_trace_gate_argv("release", project)
    result = run_gate(argv)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "manual: 0" in result.stdout


@pytest.mark.req("REQ-T-09")
def test_tr01_release_gate_reads_the_committed_manual_record_index():
    """Catches a release gate pointed at another index than the committed one, or at a file that is absent."""
    gate = next(g for g in ci.gates_for(ci.PROFILES["release"]) if g.name.startswith("trace matrix"))
    assert f"--manual-records={ci.MANUAL_RECORDS}" in gate.argv
    assert ci.MANUAL_RECORDS.is_file()


@pytest.mark.req("REQ-T-09")
def test_tr01_committed_manual_records_are_valid_against_the_real_requirements_file():
    """Catches a committed record that names no requirement row, a missing record file, or a malformed entry."""
    known = {req.req_id for req in trace_matrix.parse_requirements(trace_matrix.REQUIREMENTS.read_text("utf-8"))}
    _, problems = trace_matrix.parse_manual_records(ci.MANUAL_RECORDS.read_text(encoding="utf-8"), known)
    assert problems == []


@pytest.mark.req("REQ-T-09")
@pytest.mark.parametrize("profile_name", ["commit", "nightly"])
def test_tr01_commit_and_nightly_gates_leave_an_untested_must_row_unlisted(profile_name, manual_only_project):
    """Catches the flag leaking into the profiles that skip tests/packaging and tests/performance."""
    name, argv = release_trace_gate_argv(profile_name, manual_only_project)
    result = run_gate(argv)
    assert name == "trace matrix (TR-02)"
    assert result.returncode == 0, result.stdout
