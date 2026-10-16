"""Requirement audit of release 0.0.1: one status per row of requirements.md, from the release run's own records.

    python3 docs/phase3/verification/checks/req_audit.py            # prints the counts, writes req_audit.md
    python3 docs/phase3/verification/checks/req_audit.py --check    # exit 1 when req_audit.md is stale
    python3 docs/phase3/verification/checks/req_audit.py --self-test

Inputs (read only): requirements.md and the two test plans of this checkout; the REQ report and the gate log of
Fable's release run on 5e74acc (/home/claude/release_0.0.1); the test sources of that run (`git archive 5e74acc tests`,
or the folder given with --tree); Agent 4's V3-01 rulings and source pins (tests/independent/m7/v3_01_rulings.py),
and the union rulings of the REQ-F rows (tests/independent/m7/v3_01_rulings_f.py), each of which replaces the sample
ruling of its row.

For each planned test ID of a row, the evidence is the first that holds:
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

Row status: `verified` when every planned ID has gate, name, file, eqt or record evidence and none is in NEEDS;
`partial` when some evidence exists but an ID lacks it or needs another machine; `not testable here` when no ID has
evidence and every ID is in NEEDS; `not tested` otherwise. Withdrawn rows keep `withdrawn`. The script matches IDs to
tests by text, so this is the text status. D-051e: a row whose text status is `verified` stays `verified` only with
Agent 4's V3-01 `checks` ruling for that row, while the SHA-256 of every source the ruling cites equals its pin;
otherwise it drops to `partial` until Agent 4 re-rules it. The Ruling column says which case applies.
"""

import argparse
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
REQUIREMENTS = REPO / "docs/phase2/architecture/requirements.md"
PLANS = (REPO / "docs/phase1/architecture/test_plan_draft.md", REPO / "docs/phase2/architecture/test_plan.md")
REPORT = RELEASE / "req_report.json"
GATE_LOG = RELEASE / "gate_release_5e74acc.log"
OUT = HERE.parents[1] / "req_audit.md"

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


def evidence_kind(tid, carriers, gates, eqs, sources) -> str:
    """Return the evidence kind of one planned test ID, given the records that carry the row's REQ marker."""
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
    if tid in RECORDS and (REPO / RECORDS[tid]).exists():
        return "record"
    if any(r["nodeid"].split("::")[0] in cited for r in carriers):
        return "skip"
    return "none"


def audit(rows, records, gates, eqs, sources):
    """Return one (row, status, carriers, passed, Agent 4 passed, evidence, blocked IDs) tuple per row."""
    results = []
    for row in rows:
        carriers = [r for r in records if row.req_id in r["req"]]
        passing = [r for r in carriers if r["outcome"] == "passed"]
        evidence = {tid: evidence_kind(tid, carriers, gates, eqs, sources) for tid in row.tests}
        found = [t for t, k in evidence.items() if k in PASSING_KINDS]
        blocked = [t for t in row.tests if t in NEEDS]
        if row.disposition == "withdrawn":
            status = "withdrawn"
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


def render(results, notes, inputs) -> str:
    """Return req_audit.md."""
    counts = Counter(status for _, status, *_ in results)
    must = Counter(status for row, status, *_ in results if row.priority == "must")
    lines = [
        "Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5",
        "",
        "# Requirement audit of release 0.0.1 (generated)",
        "",
        "Generated by `python3 docs/phase3/verification/checks/req_audit.py`. Do not edit by hand.",
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


def apply_rulings(results, sample_rulings, pins, tree: Path):
    """D-051e: return the results with each text-verified row gated by its ruling, and one Ruling note per row."""
    out, notes = [], []
    for row, status, *rest in results:
        reason = ruling_gate(row.req_id, sample_rulings, pins, tree) if status == "verified" else None
        if status == "verified" and reason:
            status = "partial"
        if reason:
            notes.append(f"text-verified; {reason}")
        else:
            notes.append("`checks`, sources match" if status == "verified" else "-")
        out.append((row, status, *rest))
    return out, notes


def release_tests(dest: Path) -> Path:
    """Extract the test tree of the release commit into dest and return dest."""
    tar = subprocess.run(["git", "-C", str(REPO), "archive", RELEASE_COMMIT, "tests"], capture_output=True, check=True)
    with tarfile.open(fileobj=io.BytesIO(tar.stdout)) as archive:
        archive.extractall(dest, filter="data")
    return dest


def run_audit(tree: Path):
    """Return the text results, the gated results and the Ruling notes for the test sources under tree."""
    rows = parse_requirements(REQUIREMENTS.read_text(encoding="utf-8"))
    records = json.loads(REPORT.read_text(encoding="utf-8"))
    gates = gate_ids(GATE_LOG.read_text(encoding="utf-8"))
    eqs = eq_map([p.read_text(encoding="utf-8") for p in PLANS])
    files = {r["nodeid"].split("::")[0] for r in records}
    sources = {f: (tree / f).read_text(encoding="utf-8", errors="replace") for f in files}
    text_results = audit(rows, records, gates, eqs, sources)
    rulings, union_f = load_rulings(), load_rulings(RULINGS_F)
    row_rulings = {**rulings.SAMPLE_RULINGS, **union_f.UNION_RULINGS}
    pins = {**rulings.CHECKS_PINS, **union_f.UNION_PINS}
    gated, notes = apply_rulings(text_results, row_rulings, pins, tree)
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


def sha(path: Path) -> str:
    """Return the first 16 hex digits of a file's SHA-256."""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def main(argv: list[str] | None = None) -> int:
    """Write req_audit.md and print the counts, or with --check report whether it is stale."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="exit 1 when req_audit.md differs from a fresh run")
    parser.add_argument("--self-test", action="store_true", help="run the D-051e control")
    parser.add_argument("--tree", type=Path, help="test sources to audit (default: git archive of the release commit)")
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory() as tmp:
        tree = args.tree.resolve() if args.tree else release_tests(Path(tmp))
        if args.self_test:
            return self_test(tree)
        _, results, notes = run_audit(tree)
    inputs = [(p, sha(p)) for p in (REQUIREMENTS, *PLANS, REPORT, GATE_LOG, RULINGS, RULINGS_F)]
    shown = [(str(p.relative_to(REPO)) if p.is_relative_to(REPO) else str(p), h) for p, h in inputs]
    text = render(results, notes, shown)

    if args.check:
        stale = not OUT.exists() or OUT.read_text(encoding="utf-8") != text
        print("req_audit.md is " + ("stale" if stale else "current"))
        return 1 if stale else 0
    OUT.write_text(text, encoding="utf-8")
    counts = Counter(status for _, status, *_ in results)
    print(f"{len(results)} requirements: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    must = Counter(status for row, status, *_ in results if row.priority == "must")
    print("must rows: " + ", ".join(f"{k} {v}" for k, v in sorted(must.items())))
    kinds = Counter(k for *_, evidence, _ in results for k in evidence.values())
    print("planned-test evidence: " + ", ".join(f"{k} {v}" for k, v in sorted(kinds.items())))
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
