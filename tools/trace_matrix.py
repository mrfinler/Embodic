"""Build the requirements-to-tests matrix from pytest REQ markers (TR-01) and enforce one marker per test (TR-02).

Usage, from the repository root after a pytest run with ``--req-report build/req_report.json``::

    python tools/trace_matrix.py --report build/req_report.json --out build/trace_matrix.md

Exit code 1 when a test has no REQ marker, a marker names an unknown REQ ID, a manual record is invalid, or (with
``--fail-untested-through``) a live must-requirement of that milestone or earlier has neither a passing test nor a
manual record that passed. ``--manual-records`` reads the checks that only a person can run (interfaces.md section 3.2).
"""

import argparse
import json
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REQUIREMENTS = REPO / "docs" / "phase2" / "architecture" / "requirements.md"
REQ_ID = re.compile(r"REQ-[FNKTL]-\d{2}")
MILESTONES = ("M1", "M2", "M3", "M4", "M5")
MANUAL_KEYS = ("req", "test_id", "record", "embodic_version", "result")
MANUAL_RESULTS = ("passed", "failed")


@dataclass(frozen=True)
class Requirement:
    """One row of requirements.md."""

    req_id: str
    disposition: str
    priority: str
    milestone: str
    owner: str
    planned_tests: str


@dataclass(frozen=True)
class CollectedTest:
    """One test from the pytest REQ report."""

    nodeid: str
    req_ids: tuple[str, ...]
    outcome: str


@dataclass(frozen=True)
class ManualRecord:
    """One check that a person ran, from the manual-record index (interfaces.md section 3.2)."""

    req: str
    test_id: str
    record: str
    embodic_version: str
    result: str


def parse_requirements(text: str) -> list[Requirement]:
    """Return the requirement rows of requirements.md in file order."""
    rows = []
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 9 and REQ_ID.fullmatch(cells[0]):
            req_id, disposition, _, _, priority, _, milestone, owner, tests = cells
            rows.append(Requirement(req_id, disposition, priority, milestone, owner, tests))
    return rows


def parse_report(text: str) -> list[CollectedTest]:
    """Return the test records written by tests/conftest.py."""
    return [CollectedTest(r["nodeid"], tuple(r["req"]), r["outcome"]) for r in json.loads(text)]


def parse_manual_records(text: str, known_reqs: set[str], repo: Path = REPO) -> tuple[list[ManualRecord], list[str]]:
    """Return (valid records, one problem line for each invalid record); a problem line holds the record it names."""
    try:
        entries = json.loads(text)
    except json.JSONDecodeError as error:
        return [], [f"manual records: not valid JSON: {error}"]
    if not isinstance(entries, list):
        return [], ["manual records: the file must hold one JSON list"]
    records, problems = [], []
    for entry in entries:
        shown = json.dumps(entry, sort_keys=True)
        if not isinstance(entry, dict) or not all(isinstance(entry.get(key), str) for key in MANUAL_KEYS):
            problems.append(f"manual record {shown}: needs the five string keys {', '.join(MANUAL_KEYS)}")
            continue
        record = ManualRecord(**{key: entry[key] for key in MANUAL_KEYS})
        reasons = []
        if record.result not in MANUAL_RESULTS:
            reasons.append(f"result {record.result!r} is neither 'passed' nor 'failed'")
        if record.req not in known_reqs:
            reasons.append(f"{record.req} is not a row of the requirements file")
        if not (repo / record.record).is_file():
            reasons.append(f"record file {record.record} does not exist")
        if reasons:
            problems.append(f"manual record {shown}: {'; '.join(reasons)}")
        else:
            records.append(record)
    return records, problems


def render_matrix(requirements: list[Requirement], tests: list[CollectedTest]) -> str:
    """Return the matrix as Markdown, one row per requirement, then the TR-02 and unknown-ID findings."""
    lines = [
        "| REQ | Disp. | Prio | M | Owner module | Planned tests | Automated | Passed |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for req in requirements:
        marked = [t for t in tests if req.req_id in t.req_ids]
        passed = sum(1 for t in marked if t.outcome == "passed")
        lines.append(
            f"| {req.req_id} | {req.disposition} | {req.priority} | {req.milestone} | {req.owner} | "
            f"{req.planned_tests} | {len(marked)} | {passed} |"
        )
    unmarked, unknown = find_marker_errors(requirements, tests)
    lines += ["", "Tests without a REQ marker (TR-02):", *[f"- {t}" for t in unmarked or ["none"]]]
    lines += ["", "Unknown REQ IDs in markers:", *[f"- {u}" for u in unknown or ["none"]]]
    return "\n".join(lines) + "\n"


def find_marker_errors(requirements: list[Requirement], tests: list[CollectedTest]) -> tuple[list[str], list[str]]:
    """Return (node IDs without a REQ marker, 'node ID: REQ' pairs whose REQ is not in requirements.md)."""
    known = {req.req_id for req in requirements}
    unmarked = [t.nodeid for t in tests if not t.req_ids]
    unknown = [f"{t.nodeid}: {r}" for t in tests for r in t.req_ids if r not in known]
    return unmarked, unknown


def find_untested(
    requirements: list[Requirement],
    tests: list[CollectedTest],
    through: str,
    counted_records: Sequence[ManualRecord] = (),
) -> list[str]:
    """Return live must-requirements of milestone `through` or earlier with no passing test and no counted record."""
    due = set(MILESTONES[: MILESTONES.index(through) + 1])
    passing = {r for t in tests if t.outcome == "passed" for r in t.req_ids} | {rec.req for rec in counted_records}
    return [
        req.req_id
        for req in requirements
        if req.disposition != "withdrawn" and req.priority == "must" and req.milestone in due
        if req.req_id not in passing
    ]


def main(argv: list[str] | None = None) -> int:
    """Write the matrix, print a one-line summary and return the exit code."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--report", type=Path, required=True, help="JSON written by pytest --req-report")
    parser.add_argument("--requirements", type=Path, default=REQUIREMENTS)
    parser.add_argument("--out", type=Path, help="Markdown output; omitted means stdout")
    parser.add_argument("--fail-untested-through", choices=MILESTONES, help="enforce TR-01 up to this milestone")
    parser.add_argument(
        "--manual-records", type=Path, help="JSON list of person-run checks; a passed one counts (TR-01)"
    )
    args = parser.parse_args(argv)

    requirements = parse_requirements(args.requirements.read_text(encoding="utf-8"))
    tests = parse_report(args.report.read_text(encoding="utf-8"))
    matrix = render_matrix(requirements, tests)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(matrix, encoding="utf-8", newline="\n")
    else:
        sys.stdout.write(matrix)

    unmarked, unknown = find_marker_errors(requirements, tests)
    known_reqs = {req.req_id for req in requirements}
    index_text = args.manual_records.read_text(encoding="utf-8") if args.manual_records else "[]"
    records, record_problems = parse_manual_records(index_text, known_reqs)
    counted = [record for record in records if record.result == "passed"]
    through = args.fail_untested_through
    untested = find_untested(requirements, tests, through, counted) if through else []
    covered = sum(1 for req in requirements if any(req.req_id in t.req_ids and t.outcome == "passed" for t in tests))
    print(
        f"trace matrix: {len(requirements)} requirements, {len(tests)} tests, {covered} requirements with a passing "
        f"test; manual: {len(counted)}; invalid manual records: {len(record_problems)}; "
        f"TR-02 unmarked tests: {len(unmarked)}; unknown REQ IDs: {len(unknown)}; untested due: {len(untested)}"
    )
    for problem in [*unmarked, *unknown, *record_problems, *untested]:
        print(f"  {problem}")
    return 1 if unmarked or unknown or record_problems or untested else 0


if __name__ == "__main__":
    sys.exit(main())
