"""Carry-over table for Phase 4: which Phase 3 evidence stands for the named build, row by row (D-061d).

    python3 docs/phase4/verification/checks/carry_over.py            # writes carry_over_0.0.5.md beside checks/
    python3 docs/phase4/verification/checks/carry_over.py --check    # exit 1 when that file differs from a fresh run
    python3 docs/phase4/verification/checks/carry_over.py --self-test

Inputs, read only:
- docs/phase3/verification/req_audit.md, the audit of the named build. `req_audit.py --check` proves it current. The
  script refuses an audit whose title names another build.
- docs/phase3/verification/manual_records.json, and the D-061d verdict of each record against the build commit from
  tests/independent/m7/v14_record_currency.py.
- HANDLING below: the Phase 4 handling of every live must or should row that is not `verified`, with its source.

The run fails when a non-verified row has no HANDLING entry, when an entry names a row that is now `verified`, or when
a manual record does not stand for the build. A new build therefore cannot reuse this table by accident: its audit
target (req_audit.py TARGETS), its currency run and these entries are redone first.
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
BUILD = "0.0.5"
COMMIT = "42074f2"
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
    "Phase 5 (D-091a). The failed PF-01 record stands for the build. No UAT rerun.",
    "REQ-F-11": "OR-11 and OR-12 records stand. OR-11c (3-D) is `not tested`, and EQT-14-O2 needs a board (K-4). "
    "Check E-05 shows the EMF chain to the user.",
    "REQ-N-02": "UI-36 to UI-45 are named by no test (text rule). On Windows DEF-W-12 is a known limit (K-1, D-076d). "
    "Check E-08 lets the user judge the lag.",
    "REQ-N-04": "PK-04 on the 0.0.5 wheel passed on the laptop on all five examples (D-090d). The record is not in "
    "manual_records.json yet. Fable indexes it before Phase 3 closes.",
    "REQ-N-05": "The PK-01 Windows cell on 0.0.5 has no result (stopped by an app update, D-091b). It runs in the "
    "pending Windows chain. The 3.12 and 3.13 cells may stay `not tested` (D-048d).",
    "REQ-N-06": "PK-05 is blocked by the laptop's Application Control policy (DEF-W-14, D-086c) and stays `not tested` "
    "there. Code signing is decision S-1.",
    "REQ-N-07": "The Linux PK-06 record stands. Windows warm run 7 passed on the 0.0.5 wheel (D-090d). The cold run "
    "waits for a normal network (optional record R-3).",
    "REQ-N-16": "AX-06 (Narrator) on 0.0.5 is a step of the UAT walkthrough. Its record closes the row (R-1).",
    "REQ-N-24": "The same AX-06 record as REQ-N-16 (R-1).",
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
        if record.verdict != "stands":
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
            "Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5 (unit U-V25)",
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
    flipped = [Row(r.req, r.prio, "verified", r.ruling, r.records) if r.req == "REQ-N-04" else r for r in rows]
    _, problems = classify(flipped, records, HANDLING)
    if not any("REQ-N-04 is verified" in p for p in problems):
        failures.append("a stale entry for a verified row was not reported")
    stale = [
        Record(r.req, r.test_id, r.path, r.result, "does not stand") if i == 0 else r for i, r in enumerate(records)
    ]
    _, problems = classify(rows, stale, HANDLING)
    if not any("does not stand" in p for p in problems):
        failures.append("a record that does not stand was not reported")
    for failure in failures:
        print(f"self-test FAIL: {failure}")
    print(f"self-test: {4 - len(failures)} of 4 controls pass")
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
