"""Carry-over table for Phase 4: which Phase 3 evidence stands for the named build, row by row (D-061d).

    python3 docs/phase4/verification/checks/carry_over.py            # writes carry_over_<BUILD>.md beside checks/
    python3 docs/phase4/verification/checks/carry_over.py --check    # exit 1 when that file differs from a fresh run
    python3 docs/phase4/verification/checks/carry_over.py --self-test

Inputs, read only:
- docs/phase3/verification/req_audit.md, the audit of the named build. `req_audit.py --check` proves it current. The
  script refuses an audit whose title names another build.
- docs/phase3/verification/manual_records.json, and the D-061d verdict of each record against the build commit from
  tests/independent/m7/v14_record_currency.py.
- HANDLING below: the Phase 4 handling of every live must or should row that is not `verified`, with its source.

The run fails when a non-verified row has no HANDLING entry, when an entry names a row that is now `verified`, or when
a passed manual record does not stand for the build. A failed record never counts as coverage (D-093c), so one that
does not stand is listed in its row with its verdict and does not fail the run (U-V30: PF-01 of 0.0.5 against 0.0.6).
A new build therefore cannot reuse this table by accident: its audit target (req_audit.py TARGETS), its currency run
and these entries are redone first.
"""

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
AUDIT = ROOT / "docs/phase3/verification/req_audit.md"
INDEX = ROOT / "docs/phase3/verification/manual_records.json"
CURRENCY = ROOT / "tests/independent/m7/v14_record_currency.py"
BUILD = "0.0.6"
COMMIT = "2bfca49"
OUT = ROOT / f"docs/phase4/verification/carry_over_{BUILD}.md"
LIVE_PRIOS = ("must", "should")
UNRULED = "text-verified; no V3-01 ruling"
UNRULED_HANDLING = (
    "Tests pass and name every planned ID, but V3-01 samples must rows only (verification_plan.md section 3), so no "
    "independent ruling exists. Carries as `partial`. The user sees the behaviour in the walkthrough."
)
MAY_STAY = "May stay `not tested` (verification_plan.md section 4 point 3). Carries as `not tested`."

HANDLING = {
    "REQ-N-01": "Known limit DEF-W-15, for the user to accept by name (decision K-2). The user moved its fix to "
    "Phase 5 (D-091a), and D-100b keeps the row `failed`. The PF-01 record ran on the 0.0.5 source. Against 2bfca49 "
    "its files differ only in the version strings (src/embodic/__init__.py and the app_version and engine_version of "
    "the five examples), so D-061d supersedes it and the failure carries as `inferred`. No UAT rerun.",
    "REQ-N-02": "The W8 latency gate and runs 2, 3 and 4 of the five latency runs failed on the laptop (N02-10, "
    "DEF-W-12), and their records are accepted (D-076d, D-100b, D-101). A failed run on the named machine outweighs "
    "the passing tests, as for REQ-N-01. D-100b names the row a point-1 exception, known limit K-1. Check E-08 lets "
    "the user judge the lag.",
    "REQ-N-05": "The W7 record (PK-01) and the W8 record (PK-02) failed and are accepted by name (D-100c). D-100b "
    "closes the row by name: PK-02 by runs 11 and 12, PK-01 by W7, and the exit rests on that ruling (D-101). The 3.12 "
    "and 3.13 Windows cells of PK-01 may stay `not tested` (D-048d).",
    "REQ-N-06": "The W8 record (PK-11) failed on the launcher block (DEF-W-16) and is accepted by name (D-100c). "
    "D-100b closes the row by name: PK-05 (D-099a), PK-11 by run 11, and the exit rests on that ruling (D-101). The fix "
    "of DEF-W-16 is decision S-1.",
    "REQ-N-16": "AX-06 (Narrator) on 0.0.6 is a step of the UAT walkthrough. Its record closes the row (R-1). Phase 4 "
    "starts with the row `partial`, and verdict A-1 waits for AX-06 or the user's decline (D-100b).",
    "REQ-N-24": "The same AX-06 record as REQ-N-16 (R-1, D-100b).",
    "REQ-F-29": "The audit finds no test named UT-EXP-05. Carries as `partial`. The user sees the bundle export in the "
    "walkthrough.",
    "REQ-N-20": MAY_STAY,
    "REQ-N-29": "The coverage step is Phase 5 (D-053b). Carries as `not tested`.",
    "REQ-T-12": MAY_STAY,
    "REQ-L-02": MAY_STAY,
    "REQ-L-06": MAY_STAY,
    "REQ-L-09": MAY_STAY,
}


@dataclass(frozen=True)
class Row:
    req: str
    prio: str
    status: str
    ruling: str
    records: str


@dataclass(frozen=True)
class Record:
    req: str
    test_id: str
    path: str
    result: str
    verdict: str


def parse_audit(text: str) -> list[Row]:
    title = text.splitlines()[2]
    if f"release {BUILD} ({COMMIT})" not in title:
        raise SystemExit(f"{AUDIT.name} audits another build: {title!r}")
    rows = []
    for line in text.splitlines():
        if not line.startswith("| REQ-"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells[1] in LIVE_PRIOS:
            rows.append(Row(cells[0], cells[1], cells[3], cells[4], cells[5]))
    return rows


def currency_records() -> list[Record]:
    run = subprocess.run(
        [sys.executable, "-I", str(CURRENCY), "--target", COMMIT, "--index", str(INDEX)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    records = []
    head = None
    for line in run.stdout.splitlines():
        if m := re.match(r"\[\d+\] (REQ-\S+) (\S+) (\S+) \((\w+)\)$", line):
            head = m.groups()
        elif head and (m := re.match(r"\s+verdict: (.+)$", line)):
            records.append(Record(*head, m.group(1)))
            head = None
    if len(records) != len(json.loads(INDEX.read_text(encoding="utf-8"))):
        raise SystemExit("the currency run did not judge every record of the index")
    return records


def classify(rows: list[Row], records: list[Record], handling: dict[str, str]) -> tuple[list[str], list[str]]:
    problems = []
    lines = []
    for record in records:
        if record.verdict != "stands" and record.result == "passed":
            problems.append(
                f"{record.req} {record.test_id}: {record.path} does not stand for {COMMIT} ({record.verdict})"
            )
    for row in rows:
        carried = []
        if (m := re.match(r"(\d+) \((\d+), (\d+)\)", row.records)) and m.group(1) != "0":
            carried.append(f"release gate: {m.group(1)} marked test records, {m.group(2)} passed")
        if row.ruling.startswith("`checks`, sources match"):
            carried.append("V3-01 ruling stands")
        for record in (r for r in records if r.req == row.req):
            carried.append(f"{record.test_id} `{record.path}` ({record.result}, {record.verdict})")
        if row.status == "verified":
            if row.req in handling:
                problems.append(f"{row.req} is verified, but HANDLING still has an entry for it")
            action = "Carries without a rerun."
        elif row.req in handling:
            action = handling[row.req]
        elif row.ruling == UNRULED:
            action = UNRULED_HANDLING
        else:
            problems.append(f"{row.req} is {row.status} and has no HANDLING entry")
            action = "MISSING"
        lines.append(f"| {row.req} | {row.prio} | {row.status} | {', '.join(carried) or '-'} | {action} |")
    return lines, problems


def render(rows: list[Row], lines: list[str], records: list[Record]) -> str:
    counts: dict[tuple[str, str], int] = {}
    for row in rows:
        counts[(row.prio, row.status)] = counts.get((row.prio, row.status), 0) + 1
    summary = ", ".join(f"{p} {s} {n}" for (p, s), n in sorted(counts.items()))
    stand = sum(r.verdict == "stands" for r in records)
    return "\n".join(
        [
            "Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5 (units U-V25 and U-V30)",
            "",
            f"# Carry-over of Phase 3 evidence to the acceptance of release {BUILD} ({COMMIT}) (generated)",
            "",
            "Generated by `python3 docs/phase4/verification/checks/carry_over.py`. Do not edit by hand. The rule is",
            "D-061d: evidence counts for the build when the files its subject depends on are unchanged since the build",
            "it names. The release-gate tests ran on this build, so they stand by identity.",
            "",
            f"Live rows: {len(rows)} ({summary}). Manual records judged against {COMMIT}: {len(records)}, of them "
            f"{stand} stand.",
            "",
            "| REQ | Prio | Status on the build | Carries over without a rerun | Phase 4 handling |",
            "|---|---|---|---|---|",
            *lines,
            "",
        ]
    )


def self_test(rows: list[Row], records: list[Record]) -> int:
    failures = []
    _, base = classify(rows, records, HANDLING)
    if base:
        failures.append(f"the real inputs already fail: {base}")
    dropped = dict(HANDLING)
    dropped.pop("REQ-N-16")
    _, problems = classify(rows, records, dropped)
    if not any("REQ-N-16" in p and "no HANDLING" in p for p in problems):
        failures.append("a non-verified row without an entry was not reported")
    flipped = [Row(r.req, r.prio, "verified", r.ruling, r.records) if r.req == "REQ-N-16" else r for r in rows]
    _, problems = classify(flipped, records, HANDLING)
    if not any("REQ-N-16 is verified" in p for p in problems):
        failures.append("a stale entry for a verified row was not reported")
    first_passed = next(i for i, r in enumerate(records) if r.result == "passed")
    stale = [
        Record(r.req, r.test_id, r.path, r.result, "does not stand") if i == first_passed else r
        for i, r in enumerate(records)
    ]
    _, problems = classify(rows, stale, HANDLING)
    if not any("does not stand" in p for p in problems):
        failures.append("a passed record that does not stand was not reported")
    failed_stale = [
        Record(r.req, r.test_id, r.path, r.result, "does not stand") if r.result == "failed" else r for r in records
    ]
    lines, problems = classify(rows, failed_stale, HANDLING)
    if problems or not any("(failed, does not stand)" in line for line in lines):
        failures.append("a failed record that does not stand failed the run or was left out of its row")
    for failure in failures:
        print(f"self-test FAIL: {failure}")
    print(f"self-test: {5 - len(failures)} of 5 controls pass")
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="exit 1 when the table differs from a fresh run")
    parser.add_argument("--self-test", action="store_true", help="run the seeded controls")
    args = parser.parse_args(argv)
    rows = parse_audit(AUDIT.read_text(encoding="utf-8"))
    records = currency_records()
    if args.self_test:
        return self_test(rows, records)
    lines, problems = classify(rows, records, HANDLING)
    for problem in problems:
        print(f"problem: {problem}")
    if problems:
        return 1
    text = render(rows, lines, records)
    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        print(f"{OUT.name} is {'current' if current == text else 'stale'}")
        return 0 if current == text else 1
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
