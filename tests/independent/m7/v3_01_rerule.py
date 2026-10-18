"""Apply Agent 4's main re-ruling (v3_01_rulings_v13.py) to a REQ report of main and write the V3-01 counts (U-V13).

    python3 tests/independent/m7/v3_01_rerule.py --pin
    python3 tests/independent/m7/v3_01_rerule.py --report R.json --gate-log G.log --collected C.json [--write | --check]
    python3 tests/independent/m7/v3_01_rerule.py --report R.json --gate-log G.log --self-test

--pin writes records/V3-01_pins_260191f.json: the SHA-256 of the source segment of every cited test function
(`ast.get_source_segment`, interfaces.md section 3.2) and of every cited record file, on this checkout.

With a report (a pytest `--req-report` of a run of main) and the gate log of that run, each live must row gets:

- `verified`: the ruling is `checks`, every pin matches this checkout, every cited function has records in the
  report, all of them carry the row's REQ marker and passed, and every cited gate has a PASS line naming it.
- `checks, not run here`: as `verified`, except that a cited function was not run by this report (deselected slow or
  manual tests, or the release-only folders tests/performance and tests/packaging).
- `partial`: anything else with a passing marked test or a passed manual record.
- `not tested`: no passing marked test and no passed manual record.

The release column applies the 0.0.2 release gate rule (tools/trace_matrix.py --fail-untested-through M5 with
docs/phase3/verification/manual_records.json): a row blocks when it has no passing marked test and no passed record.
A row whose marked tests all sit in tests/performance or tests/packaging, or are slow, runs only in the release profile;
the column says so instead of guessing their outcome.

--write replaces the section of records/V3-01.md from its marker line to the end; --check exits 1 when that section
is stale. --self-test shows that a failed cited test and a changed pin each move a verified row out of `verified`.
"""

import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
REQUIREMENTS = REPO / "docs/phase2/architecture/requirements.md"
MANUAL = REPO / "docs/phase3/verification/manual_records.json"
PINS = HERE / "records/V3-01_pins_260191f.json"
RECORD = HERE / "records/V3-01.md"
MARKER = "## Re-ruling on main 260191f (U-V13, generated)"
RELEASE_ONLY = ("tests/performance/", "tests/packaging/")
STATUSES = ("verified", "checks, not run here", "partial", "not tested")


def load(name: str):
    """Import a sibling rulings module by file name."""
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def live_must_rows() -> dict[str, str]:
    """REQ id -> milestone of every live must row of requirements.md."""
    rows = {}
    for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 9 and re.fullmatch(r"REQ-[FNKTL]-\d{2}", cells[0]):
            if cells[4] == "must" and cells[1] != "withdrawn":
                rows[cells[0]] = cells[6]
    return rows


def earlier_reason(req: str) -> str:
    """Return the reason of the ruling that a `reason=None` row carries over."""
    for name, attr in (("v3_01_rulings_f", "UNION_RULINGS"), ("v3_01_rulings_ntl", "UNION_RULINGS")):
        table = getattr(load(name), attr)
        if req in table:
            return table[req][1]
    return load("v3_01_rulings").SAMPLE_RULINGS[req][1]


def function_source(cite: str) -> str | None:
    """Return the source segment of a cited `path::function`, or None when the function does not exist."""
    path, _, name = cite.partition("::")
    file = REPO / path
    if not file.is_file():
        return None
    text = file.read_text(encoding="utf-8")
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name == name:
            return ast.get_source_segment(text, node)
    return None


def current_hash(cite: str) -> str | None:
    """Return the SHA-256 of what a cite points at on this checkout."""
    if cite.startswith("gate:"):
        return None
    if cite.startswith("record:"):
        file = REPO / cite.removeprefix("record:")
        return hashlib.sha256(file.read_bytes()).hexdigest() if file.is_file() else "missing"
    source = function_source(cite)
    return hashlib.sha256(source.encode("utf-8")).hexdigest() if source is not None else "missing"


def make_pins(rulings) -> dict[str, dict[str, str]]:
    """Return {req: {cite: sha256}} for every `checks` ruling."""
    return {
        req: {c: current_hash(c) for c in r.cites if not c.startswith("gate:")}
        for req, r in sorted(rulings.items())
        if r.ruling == "checks"
    }


def records_of(report: list[dict], cite: str) -> list[dict]:
    """Return the report records of one cited function, every parameter case included."""
    path, _, name = cite.partition("::")
    return [r for r in report if r["nodeid"].split("[")[0] in (f"{path}::{name}",)]


def cite_findings(req, cite, pins, report, gates) -> tuple[list[str], bool]:
    """Return (problems, not run here) of one cite of a `checks` ruling."""
    if cite.startswith("gate:"):
        return ([] if cite.removeprefix("gate:") in gates else [f"no PASS line for {cite}"]), False
    problems = [] if pins.get(req, {}).get(cite) == current_hash(cite) else [f"stale pin {cite}"]
    if cite.startswith("record:"):
        return problems, False
    found = records_of(report, cite)
    if not found:
        return (problems, True) if cite.startswith(RELEASE_ONLY) else ([*problems, f"not collected {cite}"], False)
    if any(req not in r["req"] for r in found):
        problems.append(f"lacks the {req} marker: {cite}")
    outcomes = {r["outcome"] for r in found}
    if outcomes - {"passed", "not run"}:
        problems.append(f"{'/'.join(sorted(outcomes - {'passed', 'not run'}))}: {cite}")
    return problems, outcomes == {"not run"}


def row_status(req, ruling, pins, report, gates, manual_passed) -> tuple[str, list[str]]:
    """Return (status, notes) of one row."""
    marked = [r for r in report if req in r["req"]]
    has_pass = any(r["outcome"] == "passed" for r in marked) or req in manual_passed
    if ruling.ruling != "checks":
        return ("partial" if has_pass else "not tested"), []
    findings = [cite_findings(req, cite, pins, report, gates) for cite in ruling.cites]
    notes = [note for problems, _ in findings for note in problems]
    if notes:
        return ("partial" if has_pass else "not tested"), notes
    return ("checks, not run here" if any(not_run for _, not_run in findings) else "verified"), []


def release_column(req, report, collected, manual_passed) -> str:
    """Return whether the row blocks the 0.0.2 release trace gate, judged from this report."""
    marked = [r for r in report if req in r["req"]]
    if any(r["outcome"] == "passed" for r in marked):
        return "no (passing test)"
    if req in manual_passed:
        return "no (passed manual record)"
    release_only = [n for n in collected.get(req, []) if n.startswith(RELEASE_ONLY)]
    if release_only:
        return f"release-only tests ({len(release_only)}), not run here"
    return "yes"


def evaluate(rulings, pins, report, gates, manual_passed, collected):
    """Return one (req, milestone, ruling, status, notes, release) tuple per live must row."""
    rows = live_must_rows()
    assert set(rows) == set(rulings), sorted(set(rows) ^ set(rulings))
    out = []
    for req, milestone in rows.items():
        status, notes = row_status(req, rulings[req], pins, report, gates, manual_passed)
        out.append((req, milestone, rulings[req], status, notes, release_column(req, report, collected, manual_passed)))
    return out


def render(results, inputs, note: str) -> str:
    """Return the generated section of V3-01.md."""
    counts = Counter(status for _, _, _, status, _, _ in results)
    rulings = Counter(r.ruling for _, _, r, _, _, _ in results)
    blocking = [req for req, *_, release in results if release == "yes"]
    lines = [
        MARKER,
        "",
        "Generated by `python3 tests/independent/m7/v3_01_rerule.py --write`; rulings in "
        "`tests/independent/m7/v3_01_rulings_v13.py`, pins in `records/V3-01_pins_260191f.json`. Inputs and SHA-256:",
        "",
        *[f"- `{name}` `{digest}`" for name, digest in inputs],
        "",
        *([note, ""] if note else []),
        f"Rulings on the {len(results)} live must rows: "
        + ", ".join(f"{k} {rulings[k]}" for k in ("checks", "partial", "does not check") if rulings[k])
        + ".",
        "",
        "Status with the rulings applied to this report: "
        + ", ".join(f"{s} {counts[s]}" for s in STATUSES)
        + ". `checks, not run here` counts as `partial` until the release run passes its cited tests.",
        "",
        "Release profile (0.0.2 gate: trace_matrix --fail-untested-through M5 with the manual records): "
        + (f"{len(blocking)} blocking: {', '.join(blocking)}." if blocking else "no row blocks on this report.")
        + " A row marked `release-only tests` has its marked tests only in tests/performance or tests/packaging,"
        " which this report did not run.",
        "",
        "Rows that are not `verified`, with the one missing piece:",
        "",
        "| REQ | M | Ruling | Status | Missing piece (kind) | Owner | Blocks 0.0.2 |",
        "|---|---|---|---|---|---|---|",
    ]
    for req, milestone, ruling, status, notes, release in results:
        if status == "verified":
            continue
        if ruling.ruling == "checks":
            piece = "; ".join(notes) or "the release run passes the cited tests that this report did not run"
            kind, owner = "release run", "Fable (release gate)"
        else:
            piece, kind, owner = ruling.missing, ruling.kind, ruling.owner
        lines.append(f"| {req} | {milestone} | {ruling.ruling} | {status} | {piece} ({kind}) | {owner} | {release} |")
    lines += ["", "Reasons of every ruling (carried reasons come from the earlier rulings files):", ""]
    for req, _, ruling, _, _, _ in results:
        lines.append(f"- {req} `{ruling.ruling}`: {ruling.reason or earlier_reason(req)}")
    return "\n".join(lines) + "\n"


def collected_by_req(report: list[dict]) -> dict[str, list[str]]:
    """Return REQ id -> node ids of the report's records that carry it."""
    out: dict[str, list[str]] = {}
    for r in report:
        for req in r["req"]:
            out.setdefault(req, []).append(r["nodeid"])
    return out


def inputs_of(args) -> list[tuple[str, str]]:
    """Return (name, sha256 prefix) of every input file."""
    files = [args.report, args.gate_log, *[f for f in (args.collected, args.extra_report) if f], MANUAL, PINS]
    files += [HERE / "v3_01_rulings_v13.py", REQUIREMENTS]
    shown = []
    for f in files:
        name = str(f.relative_to(REPO)) if f.resolve().is_relative_to(REPO) else f.name
        shown.append((name, hashlib.sha256(f.read_bytes()).hexdigest()[:16]))
    return shown


def self_test(rulings, pins, report, gates, manual_passed, collected) -> int:
    """Control: a failed cited test and a stale pin each take a verified row out of `verified`."""
    base = {req: status for req, _, _, status, _, _ in evaluate(rulings, pins, report, gates, manual_passed, collected)}
    req = next(r for r, s in base.items() if s == "verified")
    cite = next(c for c in rulings[req].cites if "::" in c)
    failed = copy.deepcopy(report)
    for r in failed:
        if r["nodeid"].split("[")[0] == cite:
            r["outcome"] = "failed"
    after_fail = dict((r, s) for r, _, _, s, _, _ in evaluate(rulings, pins, failed, gates, manual_passed, collected))
    stale = copy.deepcopy(pins)
    stale[req][cite] = "0" * 64
    after_pin = dict((r, s) for r, _, _, s, _, _ in evaluate(rulings, stale, report, gates, manual_passed, collected))
    ok = base[req] == "verified" and after_fail[req] != "verified" and after_pin[req] != "verified"
    print(f"self-test row {req}, cite {cite}")
    print(f"  as reported: {base[req]}; cited test failed: {after_fail[req]}; pin changed: {after_pin[req]}")
    print("self-test " + ("passed" if ok else "FAILED"))
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    """Pin, or evaluate and print, write or check the V3-01 section."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pin", action="store_true")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--gate-log", type=Path)
    parser.add_argument("--collected", type=Path, help="collect-only REQ report of the same tree (all folders)")
    parser.add_argument("--extra-report", type=Path, help="REQ report of an extra run; its outcomes replace the main's")
    parser.add_argument("--note", default="", help="one paragraph on where the report and log come from")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    rulings = load("v3_01_rulings_v13").RULINGS
    if args.pin:
        PINS.write_text(json.dumps(make_pins(rulings), indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote {PINS.relative_to(REPO)}")
        return 0
    pins = json.loads(PINS.read_text(encoding="utf-8"))
    report = json.loads(args.report.read_text(encoding="utf-8"))
    if args.extra_report:
        extra = {r["nodeid"]: r for r in json.loads(args.extra_report.read_text(encoding="utf-8"))}
        report = [extra.pop(r["nodeid"], r) for r in report] + list(extra.values())
    log = args.gate_log.read_text(encoding="utf-8")
    gates = {i for line in log.splitlines() if line.startswith("PASS") for i in re.findall(r"\b[A-Z]{2}-\d{2}\b", line)}
    manual = json.loads(MANUAL.read_text(encoding="utf-8"))
    manual_passed = {m["req"] for m in manual if m["result"] == "passed"}
    collected = collected_by_req(json.loads(args.collected.read_text(encoding="utf-8")) if args.collected else report)
    if args.self_test:
        return self_test(rulings, pins, report, gates, manual_passed, collected)
    results = evaluate(rulings, pins, report, gates, manual_passed, collected)
    counts = Counter(status for _, _, _, status, _, _ in results)
    print("live must rows: " + ", ".join(f"{s} {counts[s]}" for s in STATUSES))
    for req, _, _, status, notes, release in results:
        if notes or release != "no (passing test)":
            print(f"  {req}: {status}; release: {release}" + (f"; {'; '.join(notes)}" if notes else ""))
    section = render(results, inputs_of(args), args.note)
    text = RECORD.read_text(encoding="utf-8")
    head = text.split(MARKER)[0].rstrip("\n") + "\n\n"
    if args.check:
        stale = text != head + section
        print("V3-01.md section is " + ("stale" if stale else "current"))
        return 1 if stale else 0
    if args.write:
        RECORD.write_text(head + section, encoding="utf-8")
        print(f"wrote {RECORD.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
