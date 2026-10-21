"""Requirement audit of one build: one status per row of requirements.md, from that build's own test records.

    python3 docs/phase3/verification/checks/req_audit.py                    # release 0.0.5: writes req_audit.md
    python3 docs/phase3/verification/checks/req_audit.py --target 0.0.4     # release 0.0.4: req_audit_0.0.4.md
    python3 docs/phase3/verification/checks/req_audit.py --target 0.0.5-pre # main 99d355d: req_audit_0.0.5_pre.md
    python3 docs/phase3/verification/checks/req_audit.py --target 0.0.1     # release 0.0.1: req_audit_0.0.1.md
    python3 docs/phase3/verification/checks/req_audit.py [--target T] --check    # exit 1 when the file is stale
    python3 docs/phase3/verification/checks/req_audit.py --target 0.0.1 --self-test
    python3 docs/phase3/verification/checks/req_audit.py --self-test                # the D-061d control on 0.0.5

Inputs (read only) of every target: requirements.md and the two test plans of this checkout, and the test sources of
the audited commit (`git archive <commit> tests`, or the folder given with --tree).

- Target 0.0.1: the REQ report and the gate log of Fable's release run on 5e74acc (/home/claude/release_0.0.1); Agent
  4's V3-01 rulings and source pins (tests/independent/m7/v3_01_rulings.py), and the union rulings of the REQ-F rows
  (v3_01_rulings_f.py) and of the REQ-N, REQ-T and REQ-L rows (v3_01_rulings_ntl.py), each of which replaces the sample
  ruling of its row; records from the RECORDS table below.
- Target 0.0.4 (U-V18): the two REQ reports of Fable's release gate on c25d8a9, the main pytest process and the
  latency process (D-074), whose outcomes replace the main report's `not run` records, and that gate's log, all three
  copied gzipped into docs/phase3/verification/inputs/; Agent 4's re-ruling of main
  (tests/independent/m7/v3_01_rulings_v13.py) with its function-level pins (records/V3-01_pins_260191f.json,
  interfaces.md section 3.2), on top the rows that U-V14 re-ruled on c0f4894 (v3_01_rulings_v14.py), and on top the
  rows that U-V18 re-ruled on c25d8a9 (v3_01_rulings_v18.py), and on top U-V19's re-rulings (v3_01_rulings_v19.py,
  wired by U-V20 as U-V19 proposed); records from docs/phase3/verification/manual_records.json (passed entries
  only). D-061d: a ruling that cites a record the index no longer holds counts only through the record that redid it
  (REDONE, followed to its last redo).
- Target 0.0.5-pre (U-V20): main 99d355d before Fable's release gate. The REQ reports of U-V20's two pytest processes
  with the release marker expressions (main and latency) and the log of the static gates and the trace matrix that
  U-V20 ran one by one (tools/ci.py did not run, so TR-05 and PK-10 have no PASS line); the 0.0.4 overlays plus
  U-V20's re-pin of the renamed tests (v3_01_rulings_v20.py).
- Target 0.0.5 (U-V21): release 0.0.5, tag v0.0.5 on 42074f2 (D-089). The two REQ reports and the log of Fable's
  release gate (/home/claude/release_0.0.5), copied gzipped into inputs/; the 0.0.5-pre overlays plus U-V21's
  re-rulings of REQ-F-05, REQ-F-13, REQ-T-05 and REQ-N-01 (v3_01_rulings_v21.py).
- Every target except 0.0.1 reads the manual-record index of this checkout, so a committed audit file of an earlier
  target is the snapshot of the index its writer had; `--check` on it compares with today's index.
- The earlier target main (U-V14, c0f4894) is gone: its gate log `inputs/gate_commit_5099401.log` was never in git
  (`*.log` is ignored) and was lost with the container on 2026-10-19 (D-071a). Its output is in git at 72ba81c.

For each planned test ID of a row, the evidence is the first that holds:
  fail   a manual record of the index with result `failed` names the ID (U-V21: a failed run on the machine the
         acceptance names outweighs any passing test of the ID)
  gate   a PASS line of the release gate log names the ID
  name   every record that carries the row's REQ marker and has the ID in its test name (ut_io_08, lg01) passed;
         when one of them failed the evidence is `fail`, when one was skipped or xfailed it is `skip`
  file   no test name holds the ID, and a passing record that carries the row's REQ marker sits in a test file whose
         text names the ID
  eqt    the test plans give the ID an EQ-nn, and a passing record with the row's REQ marker carries an EQT-nn id
  record an Agent 4 record under tests/independent names the ID (a manual or scripted run outside pytest)
  skip   only skipped or xfailed records name the ID
  none   nothing above
NEEDS lists the IDs whose acceptance needs Windows, a real display or an FEA solver, with the line that says so.

Row status: `failed` when a planned ID has `fail` evidence; `verified` when every planned ID has gate, name, file, eqt
or record evidence and none is in NEEDS; `partial` when some evidence exists but an ID lacks it or needs another machine; `not testable here` when no ID has
evidence and every ID is in NEEDS; `not tested` otherwise. Withdrawn rows keep `withdrawn`. The script matches IDs to
tests by text, so this is the text status. D-051e: a row whose text status is `verified` stays `verified` only with
Agent 4's V3-01 `checks` ruling for that row, while the SHA-256 of every source the ruling cites equals its pin;
otherwise it drops to `partial` until Agent 4 re-rules it. The Ruling column says which case applies. On main a pin
covers the cited function's source segment only, so a change to a fixture or a helper does not make a ruling stale
(interfaces.md section 3.2, `inferred`).
"""

import argparse
import ast
import gzip
import hashlib
import importlib.util
import io
import json
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve()
REPO = HERE.parents[4]
RELEASE = Path("/home/claude/release_0.0.1")
RELEASE_COMMIT = "5e74acc"
RULINGS = REPO / "tests/independent/m7/v3_01_rulings.py"
RULINGS_F = REPO / "tests/independent/m7/v3_01_rulings_f.py"
RULINGS_NTL = REPO / "tests/independent/m7/v3_01_rulings_ntl.py"
RULINGS_V13 = REPO / "tests/independent/m7/v3_01_rulings_v13.py"
RULINGS_V14 = REPO / "tests/independent/m7/v3_01_rulings_v14.py"
RULINGS_V18 = REPO / "tests/independent/m7/v3_01_rulings_v18.py"
RULINGS_V19 = REPO / "tests/independent/m7/v3_01_rulings_v19.py"
RULINGS_V20 = REPO / "tests/independent/m7/v3_01_rulings_v20.py"
RULINGS_V21 = REPO / "tests/independent/m7/v3_01_rulings_v21.py"
PINS_V13 = REPO / "tests/independent/m7/records/V3-01_pins_260191f.json"
REQUIREMENTS = REPO / "docs/phase2/architecture/requirements.md"
PLANS = (REPO / "docs/phase1/architecture/test_plan_draft.md", REPO / "docs/phase2/architecture/test_plan.md")
VERIFICATION = HERE.parents[1]
INDEX = VERIFICATION / "manual_records.json"
# D-061d: a superseded record -> the record of the same check redone on a later build (U-V14 on c0f4894, U-V18 on
# c25d8a9, U-V20 on 99d355d, U-V21 on the release wheel of 42074f2).
_M4, _M5, _M6 = (f"tests/independent/m{n}/records/" for n in (4, 5, 6))
REDONE = {
    f"{_M5}PK-06_walkthrough.md": f"{_M5}PK-06_walkthrough_c0f4894.md",
    f"{_M4}AX-05.md": f"{_M4}AX-05_c0f4894.md",
    f"{_M6}OR-11_OR-12.md": f"{_M6}OR-11_OR-12_c0f4894.md",
    f"{_M5}PK-06_walkthrough_c0f4894.md": f"{_M5}PK-06_walkthrough_c25d8a9.md",
    f"{_M4}AX-05_c0f4894.md": f"{_M4}AX-05_c25d8a9.md",
    f"{_M6}OR-11_OR-12_c0f4894.md": f"{_M6}OR-11_OR-12_c25d8a9.md",
    f"{_M4}LG-01_word_review.md": f"{_M4}LG-01_word_review_c25d8a9.md",
    f"{_M4}LG-04_T-11_reviewer.md": f"{_M4}LG-04_T-11_reviewer_c25d8a9.md",
    f"{_M5}PK-06_walkthrough_c25d8a9.md": f"{_M5}PK-06_walkthrough_99d355d.md",
    f"{_M4}AX-05_c25d8a9.md": f"{_M4}AX-05_99d355d.md",
    f"{_M6}OR-11_OR-12_c25d8a9.md": f"{_M6}OR-11_OR-12_99d355d.md",
    f"{_M4}LG-04_T-11_reviewer_c25d8a9.md": f"{_M4}LG-04_T-11_reviewer_99d355d.md",
    f"{_M5}PK-06_walkthrough_99d355d.md": f"{_M5}PK-06_walkthrough_42074f2.md",
    f"{_M6}OR-11_OR-12_99d355d.md": f"{_M6}OR-11_OR-12_42074f2.md",
    f"{_M5}PK-06_walkthrough_42074f2.md": f"{_M5}PK-06_walkthrough_6d50d0b.md",
    f"{_M4}AX-05_99d355d.md": f"{_M4}AX-05_6d50d0b.md",
    f"{_M6}OR-11_OR-12_42074f2.md": f"{_M6}OR-11_OR-12_6d50d0b.md",
    f"{_M4}LG-01_word_review_c25d8a9.md": f"{_M4}LG-01_word_review_6d50d0b.md",
    f"{_M4}LG-04_T-11_reviewer_99d355d.md": f"{_M4}LG-04_T-11_reviewer_6d50d0b.md",
}


def last_redo(record: str) -> str:
    """Return the record that redid ``record`` last, following REDONE, or ``record`` itself."""
    while record in REDONE:
        record = REDONE[record]
    return record


def counted_redo(record: str, counted: set[str]) -> str | None:
    """Return the first redo of ``record`` along REDONE that the index counts, or None."""
    while record in REDONE:
        record = REDONE[record]
        if record in counted:
            return record
    return None


@dataclass(frozen=True)
class Target:
    """One audited build: its REQ reports and gate log, the commit of its test sources and the file written.

    The first report is the build's main pytest run; a later report's outcome replaces a `not run` record of it.
    """

    name: str
    title: str
    commit: str
    reports: tuple[Path, ...]
    gate_log: Path
    out: Path
    overlays: tuple[Path, ...] = ()  # rulings applied on top of v13, in order; each one's PINS replace a row's pins


TARGETS = {
    "0.0.1": Target(
        "0.0.1",
        "release 0.0.1",
        RELEASE_COMMIT,
        (RELEASE / "req_report.json",),
        RELEASE / "gate_release_5e74acc.log",
        VERIFICATION / "req_audit_0.0.1.md",
    ),
    "0.0.4": Target(
        "0.0.4",
        "release 0.0.4 (c25d8a9)",
        "c25d8a9",
        (
            VERIFICATION / "inputs/req_report_c25d8a9.json.gz",
            VERIFICATION / "inputs/req_report_latency_c25d8a9.json.gz",
        ),
        VERIFICATION / "inputs/gate_release_c25d8a9.log.gz",
        VERIFICATION / "req_audit_0.0.4.md",
        (RULINGS_V14, RULINGS_V18, RULINGS_V19),
    ),
    "0.0.5-pre": Target(
        "0.0.5-pre",
        "main 99d355d before the 0.0.5 release gate (U-V20; pytest and the static gates without tools/ci.py)",
        "99d355d",
        (
            VERIFICATION / "inputs/req_report_99d355d.json.gz",
            VERIFICATION / "inputs/req_report_latency_99d355d.json.gz",
        ),
        VERIFICATION / "inputs/gates_u_v20_99d355d.log.gz",
        VERIFICATION / "req_audit_0.0.5_pre.md",
        (RULINGS_V14, RULINGS_V18, RULINGS_V19, RULINGS_V20),
    ),
    "0.0.5": Target(
        "0.0.5",
        "release 0.0.5 (42074f2)",
        "42074f2",
        (
            VERIFICATION / "inputs/req_report_42074f2.json.gz",
            VERIFICATION / "inputs/req_report_latency_42074f2.json.gz",
        ),
        VERIFICATION / "inputs/gate_release_42074f2.log.gz",
        VERIFICATION / "req_audit.md",
        (RULINGS_V14, RULINGS_V18, RULINGS_V19, RULINGS_V20, RULINGS_V21),
    ),
}

TEST_ID = re.compile(r"\b(?:UT-[A-Z]{2,3}-\d{2}|(?:PR|GR|OR|BV|UI|AX|LG|MT|TR|PK|PF)-\d{2})\b")
EQ_ID = re.compile(r"EQ-(\d{2})")

NEEDS = {
    "PK-01": ("Windows", "test_plan.md §5.7 PK-01 row: the Windows cells; §7 M5: counts only from a Windows run"),
    "PK-04": ("Windows", "test_plan.md §5.7 PK-04 row: compares Windows JSON with Linux JSON; not tested here"),
    "PK-05": ("Windows", "test_plan.md §5.7 PK-05 row: needs the Windows folder"),
    "PK-06": ("Windows", "test_plan.md §5.7 PK-06 row: the timed walkthrough on a clean Windows machine"),
    "AX-06": ("Windows display", "requirements.md REQ-N-16 acceptance: Narrator check"),
    "OR-11": ("FEA", "test_plan.md §5.6 and §7 M2 (D-045b): a Phase 3 FEA case"),
    "OR-12": ("FEA", "test_plan.md §5.6 and §7 M2 (D-045b): a Phase 3 FEA case"),
}
RECORDS = {
    "PK-06": "tests/independent/m5/records/PK-06_walkthrough.md",
    "AX-05": "tests/independent/m4/records/AX-05.md",
    "AX-06": "tests/independent/m4/records/AX-06_accessible_names.md",
}
PASSING_KINDS = ("gate", "name", "file", "eqt", "record")


@dataclass(frozen=True)
class Row:
    """One row of requirements.md with its planned test IDs."""

    req_id: str
    disposition: str
    priority: str
    milestone: str
    tests: tuple[str, ...]


def parse_requirements(text: str) -> list[Row]:
    """Return the requirement rows in file order."""
    rows = []
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 9 and re.fullmatch(r"REQ-[FNKTL]-\d{2}", cells[0]):
            rows.append(Row(cells[0], cells[1], cells[4], cells[6], tuple(TEST_ID.findall(cells[8]))))
    return rows


def eq_map(texts: list[str]) -> dict[str, set[str]]:
    """Test ID -> EQ numbers from the second cell of test-plan table rows such as `| GR-02 | EQ-10 (reuse) | ...`."""
    out: dict[str, set[str]] = {}
    for text in texts:
        for line in text.splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 3 and TEST_ID.fullmatch(cells[0]) and EQ_ID.search(cells[1]):
                out.setdefault(cells[0], set()).update(EQ_ID.findall(cells[1]))
    return out


def id_pattern(test_id: str) -> re.Pattern[str]:
    """Match the ID in a lower-case test name, with or without underscores (ut_io_08, lg01)."""
    parts = test_id.lower().split("-")
    return re.compile(r"(?<![a-z0-9])" + "_?".join(parts) + r"(?![0-9])")


def file_mentions(test_id: str, text: str) -> bool:
    """Return True when a test file names the ID in any of its spellings."""
    parts = test_id.split("-")
    return any(sep.join(parts) in text for sep in ("-", "_")) or bool(id_pattern(test_id).search(text.lower()))


def gate_ids(log: str) -> set[str]:
    """Return the test IDs named on PASS lines of the gate summary."""
    return {i for line in log.splitlines() if line.startswith("PASS") for i in TEST_ID.findall(line)}


def evidence_kind(tid, carriers, gates, eqs, sources, records_by_id, failed_by_id=None) -> str:
    """Return the evidence kind of one planned test ID, given the records that carry the row's REQ marker."""
    if tid in (failed_by_id or {}) and (REPO / failed_by_id[tid]).exists():
        return "fail"
    passing = [r for r in carriers if r["outcome"] == "passed"]
    name_pat = id_pattern(tid)
    named = [r for r in carriers if name_pat.search(r["nodeid"].split("::")[-1].lower())]
    cited = {f for f, text in sources.items() if file_mentions(tid, text)}
    eq_nums = eqs.get(tid, set())
    if tid in gates:
        return "gate"
    if named:
        outcomes = {r["outcome"] for r in named}
        return "name" if outcomes == {"passed"} else ("fail" if "failed" in outcomes else "skip")
    if any(r["nodeid"].split("::")[0] in cited for r in passing):
        return "file"
    if eq_nums and any(e.split("-")[1] in eq_nums for r in passing for e in r["eqt"]):
        return "eqt"
    if tid in records_by_id and (REPO / records_by_id[tid]).exists():
        return "record"
    if any(r["nodeid"].split("::")[0] in cited for r in carriers):
        return "skip"
    return "none"


def audit(rows, records, gates, eqs, sources, records_by_id, failed_by_id=None):
    """Return one (row, status, carriers, passed, Agent 4 passed, evidence, blocked IDs) tuple per row."""
    results = []
    for row in rows:
        carriers = [r for r in records if row.req_id in r["req"]]
        passing = [r for r in carriers if r["outcome"] == "passed"]
        evidence = {
            tid: evidence_kind(tid, carriers, gates, eqs, sources, records_by_id, failed_by_id) for tid in row.tests
        }
        found = [t for t, k in evidence.items() if k in PASSING_KINDS]
        blocked = [t for t in row.tests if t in NEEDS]
        if row.disposition == "withdrawn":
            status = "withdrawn"
        elif "fail" in evidence.values():
            status = "failed"
        elif found and len(found) == len(row.tests) and not blocked:
            status = "verified"
        elif found or passing:
            status = "partial"
        elif blocked and len(blocked) == len(row.tests):
            status = "not testable here"
        else:
            status = "not tested"
        indep = sum(1 for r in passing if r["nodeid"].startswith("tests/independent/"))
        results.append((row, status, len(carriers), len(passing), indep, evidence, blocked))
    return results


def render(results, notes, inputs, target: Target) -> str:
    """Return the audit file of one target."""
    counts = Counter(status for _, status, *_ in results)
    must = Counter(status for row, status, *_ in results if row.priority == "must")
    lines = [
        "Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5",
        "",
        f"# Requirement audit of {target.title} (generated)",
        "",
        f"Generated by `python3 docs/phase3/verification/checks/req_audit.py --target {target.name}`. Do not edit by "
        "hand.",
        "The status rule and the evidence kinds are in the script's docstring. Inputs and their SHA-256:",
        "",
        *[f"- `{p}` `{h}`" for p, h in inputs],
        "",
        "Counts by status (all rows): " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())) + ".",
        "",
        "Counts by status (must rows): " + ", ".join(f"{k} {v}" for k, v in sorted(must.items())) + ".",
        "",
        "| REQ | Prio | M | Status | Ruling | Marked records (passed, of them Agent 4) | Planned tests and evidence "
        "| Needs |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for (row, status, n, passed, indep, evidence, blocked), note in zip(results, notes, strict=True):
        ev = ", ".join(f"{t} {k}" for t, k in evidence.items())
        needs = "; ".join(f"{t}: {NEEDS[t][0]} ({NEEDS[t][1]})" for t in blocked) or "-"
        lines.append(
            f"| {row.req_id} | {row.priority} | {row.milestone} | {status} | {note} | {n} ({passed}, {indep}) | {ev} "
            f"| {needs} |"
        )
    return "\n".join(lines) + "\n"


def load_rulings(path: Path = RULINGS):
    """Import one of Agent 4's V3-01 rulings files by path."""
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ruling_gate(req_id: str, sample_rulings, pins, tree: Path) -> str | None:
    """Return None when a `checks` ruling with matching source pins backs the row, else why it does not."""
    ruling = sample_rulings.get(req_id)
    if ruling is None:
        return "no V3-01 ruling"
    if ruling[0] != "checks":
        return f"ruled `{ruling[0]}`"
    if not pins.get(req_id):
        return "`checks` without a source pin"
    changed = []
    for source, pinned in sorted(pins[req_id].items()):
        path = Path(source) if Path(source).is_absolute() else tree / source
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != pinned:
            changed.append(source)
    return "source changed since the ruling: " + ", ".join(f"`{c}`" for c in changed) if changed else None


def cite_hash(cite: str, tree: Path) -> str:
    """Return the SHA-256 of a cited record file, or of a cited test function's source segment under tree."""
    if cite.startswith("record:"):
        file = REPO / cite.removeprefix("record:")
        return hashlib.sha256(file.read_bytes()).hexdigest() if file.is_file() else "missing"
    path, _, name = cite.partition("::")
    file = tree / path
    if not file.is_file():
        return "missing"
    text = file.read_text(encoding="utf-8")
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name == name:
            return hashlib.sha256(ast.get_source_segment(text, node).encode("utf-8")).hexdigest()
    return "missing"


def main_ruling_gate(
    req_id: str, rulings, pins, tree: Path, gates: set[str], counted: set[str]
) -> tuple[str | None, str]:
    """Return (why the main re-ruling does not back the row or None, the D-061d note on redone records)."""
    ruling = rulings.get(req_id)
    if ruling is None:
        return "no V3-01 ruling", ""
    if ruling.ruling != "checks":
        return f"ruled `{ruling.ruling}`", ""
    problems, redone = [], []
    for cite in ruling.cites:
        if cite.startswith("gate:"):
            if cite.removeprefix("gate:") not in gates:
                problems.append(f"no PASS line for `{cite}`")
            continue
        if pins.get(req_id, {}).get(cite) != cite_hash(cite, tree):
            problems.append(f"source changed since the ruling: `{cite}`")
        record = cite.removeprefix("record:")
        if cite.startswith("record:") and record not in counted:
            if redo := counted_redo(record, counted):
                redone.append(f"`{record}` redone as `{redo}`")
            else:
                problems.append(f"record superseded (D-061d): `{record}`")
    return ("; ".join(problems) or None), "; ".join(redone)


def apply_rulings(results, reason_of):
    """D-051e: return the results with each text-verified row gated by its ruling, and one Ruling note per row.

    `reason_of(req_id)` returns (why no ruling backs the row or None, an extra note).
    """
    out, notes = [], []
    for row, status, *rest in results:
        reason, extra = reason_of(row.req_id) if status == "verified" else (None, "")
        if status == "verified" and reason:
            status = "partial"
        if reason:
            note = f"text-verified; {reason}"
        else:
            note = "`checks`, sources match" if status == "verified" else "-"
        notes.append(f"{note}; {extra}" if extra else note)
        out.append((row, status, *rest))
    return out, notes


def test_tree(commit: str, dest: Path) -> Path:
    """Extract the test tree of a commit into dest and return dest."""
    tar = subprocess.run(["git", "-C", str(REPO), "archive", commit, "tests"], capture_output=True, check=True)
    with tarfile.open(fileobj=io.BytesIO(tar.stdout)) as archive:
        archive.extractall(dest, filter="data")
    return dest


def read_bytes(path: Path) -> bytes:
    """Return the content of a file, gunzipped when its name ends in .gz."""
    data = path.read_bytes()
    return gzip.decompress(data) if path.suffix == ".gz" else data


def read_reports(paths: tuple[Path, ...]) -> list[dict]:
    """Return the records of the first REQ report, each `not run` record replaced by a later report's run of it."""
    base, *later = (json.loads(read_bytes(p)) for p in paths)
    runs = {r["nodeid"]: r for report in later for r in report if r["outcome"] != "not run"}
    return [runs.get(r["nodeid"], r) if r["outcome"] == "not run" else r for r in base]


def counted_records(index: Path = INDEX, result: str = "passed") -> dict[str, str]:
    """Return {test ID: record path} of the index entries with this result (one record may hold two IDs)."""
    return {e["test_id"]: e["record"] for e in json.loads(index.read_text(encoding="utf-8")) if e["result"] == result}


def run_audit(tree: Path, target: Target = TARGETS["0.0.1"], index: Path = INDEX):
    """Return the text results, the gated results and the Ruling notes for the test sources under tree."""
    rows = parse_requirements(REQUIREMENTS.read_text(encoding="utf-8"))
    records = read_reports(target.reports)
    gates = gate_ids(read_bytes(target.gate_log).decode("utf-8"))
    eqs = eq_map([p.read_text(encoding="utf-8") for p in PLANS])
    files = {r["nodeid"].split("::")[0] for r in records}
    sources = {f: (tree / f).read_text(encoding="utf-8", errors="replace") for f in files}
    if target.name != "0.0.1":
        by_id = counted_records(index)
        counted = set(by_id.values())
        text_results = audit(rows, records, gates, eqs, sources, by_id, counted_records(index, "failed"))
        overlays = tuple(load_rulings(path) for path in target.overlays)
        rulings = {**load_rulings(RULINGS_V13).RULINGS, **{k: v for o in overlays for k, v in o.RULINGS.items()}}
        pins = {
            **json.loads(PINS_V13.read_text(encoding="utf-8")),
            **{k: v for o in overlays for k, v in o.PINS.items()},
        }
        gated, notes = apply_rulings(
            text_results, lambda req: main_ruling_gate(req, rulings, pins, tree, gates, counted)
        )
        return text_results, gated, notes
    text_results = audit(rows, records, gates, eqs, sources, RECORDS)
    rulings = load_rulings()
    row_rulings, pins = dict(rulings.SAMPLE_RULINGS), dict(rulings.CHECKS_PINS)
    for union in (load_rulings(RULINGS_F), load_rulings(RULINGS_NTL)):
        row_rulings.update(union.UNION_RULINGS)
        pins.update({req: union.UNION_PINS.get(req, {}) for req in union.UNION_RULINGS})
    gated, notes = apply_rulings(text_results, lambda req: (ruling_gate(req, row_rulings, pins, tree), ""))
    return text_results, gated, notes


def self_test(tree: Path) -> int:
    """Control for D-051e: a ruled row stays verified on the ruled sources and drops when a copy of its test changes."""
    req, cited = "REQ-F-36", "tests/ui/qt_design/test_new_design_and_examples.py"
    unruled = "REQ-F-02"
    ok = True

    def status_of(results, req_id):
        return next(status for row, status, *_ in results if row.req_id == req_id)

    text, gated, _ = run_audit(tree)
    for label, got, want in (
        (f"{req} text status on the ruled sources", status_of(text, req), "verified"),
        (f"{req} gated status on the ruled sources", status_of(gated, req), "verified"),
        (f"{unruled} text status (its V3-01 ruling is `partial`)", status_of(text, unruled), "verified"),
        (f"{unruled} gated status", status_of(gated, unruled), "partial"),
    ):
        ok &= got == want
        print(f"self-test {'ok' if got == want else 'WRONG'}: {label}: {got}, expected {want}")
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp)
        shutil.copytree(tree / "tests", copy / "tests")
        edited = copy / cited
        edited.write_text(edited.read_text(encoding="utf-8") + "\n# edited after the ruling\n", encoding="utf-8")
        text, gated, notes = run_audit(copy)
        note = next(n for (row, *_), n in zip(gated, notes, strict=True) if row.req_id == req)
    for label, got, want in (
        (f"{req} text status after editing a copy of {cited}", status_of(text, req), "verified"),
        (f"{req} gated status after the edit", status_of(gated, req), "partial"),
    ):
        ok &= got == want
        print(f"self-test {'ok' if got == want else 'WRONG'}: {label}: {got}, expected {want}")
    named = cited in note
    ok &= named
    print(f"self-test {'ok' if named else 'WRONG'}: the Ruling note names the changed file: {note}")
    print("self-test " + ("passed" if ok else "FAILED"))
    return 0 if ok else 1


def self_test_main(tree: Path, target: Target) -> int:
    """Controls for D-061d and for a failed record.

    REQ-N-14 cites the superseded AX-05 record; it stays verified only through the redone one. REQ-N-01 is `failed`
    with the failed PF-01 record of the index and not `failed` without it (U-V21).
    """
    redone = last_redo("tests/independent/m4/records/AX-05.md")
    other = "tests/independent/m4/records/AX-06.md"

    def row_of(index: Path, req: str) -> tuple[str, str]:
        _, gated, notes = run_audit(tree, target, index)
        return next((status, note) for (row, status, *_), note in zip(gated, notes, strict=True) if row.req_id == req)

    ok = True
    entries = json.loads(INDEX.read_text(encoding="utf-8"))
    failed = [e for e in entries if e["result"] == "failed"]
    with tempfile.TemporaryDirectory() as tmp:
        cases = [
            ("REQ-N-14", "with the redone record", entries, "verified", "redone as"),
            (
                "REQ-N-14",
                "with another AX-05 record",
                [{**e, "record": other} if e["record"] == redone else e for e in entries],
                "partial",
                "record superseded (D-061d)",
            ),
            ("REQ-N-14", "with no AX-05 record", [e for e in entries if e["record"] != redone], "partial", ""),
        ]
        if any(e["test_id"] == "PF-01" for e in failed):
            cases += [
                ("REQ-N-01", "with the failed PF-01 record", entries, "failed", ""),
                ("REQ-N-01", "without it", [e for e in entries if e not in failed], "partial", ""),
            ]
        for n, (req, label, index_entries, want_status, want_note) in enumerate(cases):
            index = Path(tmp) / f"index{n}.json"
            index.write_text(json.dumps(index_entries), encoding="utf-8")
            status, note = row_of(index, req)
            good = status == want_status and want_note in note
            ok &= good
            print(f"self-test {'ok' if good else 'WRONG'}: {req} {label}: {status}; {note}")
    print("self-test " + ("passed" if ok else "FAILED"))
    return 0 if ok else 1


def sha(path: Path) -> str:
    """Return the first 16 hex digits of a file's SHA-256."""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def main(argv: list[str] | None = None) -> int:
    """Write the audit file of a target and print the counts, or with --check report whether it is stale."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", choices=sorted(TARGETS), default="0.0.5", help="the build to audit")
    parser.add_argument("--check", action="store_true", help="exit 1 when the audit file differs from a fresh run")
    parser.add_argument("--self-test", action="store_true", help="run the D-051e (0.0.1) or D-061d (main) control")
    parser.add_argument("--tree", type=Path, help="test sources to audit (default: git archive of the target commit)")
    args = parser.parse_args(argv)
    target = TARGETS[args.target]

    with tempfile.TemporaryDirectory() as tmp:
        tree = args.tree.resolve() if args.tree else test_tree(target.commit, Path(tmp))
        if args.self_test:
            return self_test(tree) if target.name == "0.0.1" else self_test_main(tree, target)
        _, results, notes = run_audit(tree, target)
    main_inputs = (RULINGS_V13, PINS_V13, *target.overlays, INDEX)
    rulings = main_inputs if target.name != "0.0.1" else (RULINGS, RULINGS_F, RULINGS_NTL)
    inputs = [(p, sha(p)) for p in (REQUIREMENTS, *PLANS, *target.reports, target.gate_log, *rulings)]
    shown = [(str(p.relative_to(REPO)) if p.is_relative_to(REPO) else str(p), h) for p, h in inputs]
    text = render(results, notes, shown, target)

    if args.check:
        stale = not target.out.exists() or target.out.read_text(encoding="utf-8") != text
        print(f"{target.out.name} is " + ("stale" if stale else "current"))
        return 1 if stale else 0
    target.out.write_text(text, encoding="utf-8")
    counts = Counter(status for _, status, *_ in results)
    print(f"{len(results)} requirements: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    must = Counter(status for row, status, *_ in results if row.priority == "must")
    print("must rows: " + ", ".join(f"{k} {v}" for k, v in sorted(must.items())))
    kinds = Counter(k for *_, evidence, _ in results for k in evidence.values())
    print("planned-test evidence: " + ", ".join(f"{k} {v}" for k, v in sorted(kinds.items())))
    print(f"wrote {target.out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
