"""V3-01: rule whether one passing test per requirement row checks that row's acceptance text.

    python3 tests/independent/m7/v3_01_sample.py                 # writes m7/records/V3-01.md, prints both counts
    python3 tests/independent/m7/v3_01_sample.py --dump FILE     # writes each sample's acceptance and test source

The sample is one passing test per `verified` must row of req_audit.py, plus every cause-B ID of
verification_plan.md part 1. Test sources are those of the release run: `git archive 5e74acc tests`, extracted to a
temporary folder, because the REQ report's records came from that tree. The sampler picks the test, never the reader:
for a verified row it takes the first planned ID whose evidence is `name`, then `file`, then `eqt`, then any other kind,
and among the passing records that carry the row's REQ marker and back that ID it takes the one whose node id has the
smallest SHA-256. The rulings in v3_01_rulings.py are Agent 4's reading of each test against the Acceptance cell of
requirements.md. The script refuses to write the record while a sample has no ruling.
"""

import argparse
import ast
import hashlib
import importlib.util
import io
import json
import subprocess
import sys
import tarfile
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RELEASE_COMMIT = "5e74acc"
RECORD = HERE / "records" / "V3-01.md"
RULINGS = ("checks", "partial", "does not check")
CAUSE_B = {
    "REQ-F-03": ("UT-GEO-24", "UT-GEO-26", "UT-PHY-07"),
    "REQ-F-04": ("GR-07",),
    "REQ-F-05": ("UT-PHY-11", "PR-01"),
    "REQ-F-06": ("UT-GEO-25",),
    "REQ-F-08": ("UT-PHY-09",),
    "REQ-F-10": ("UT-DRC-01", "PR-13"),
    "REQ-F-12": ("UT-PHY-08", "GR-05"),
    "REQ-F-14": ("BV-05",),
    "REQ-F-20": ("UT-RES-02",),
    "REQ-F-29": ("UT-EXP-05",),
    "REQ-N-21": ("UT-EXP-02",),
    "REQ-N-27": ("AX-01",),
    "REQ-T-08": ("UT-PHY-13", "UT-PHY-21"),
    "REQ-T-15": ("PR-12",),
}
KIND_ORDER = ("name", "file", "eqt", "gate", "record")


def load(name: str, path: Path):
    """Import a script by path without running its main."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def release_tests(dest: Path) -> Path:
    """Extract the test tree of the release commit into dest and return dest."""
    tar = subprocess.run(["git", "-C", str(REPO), "archive", RELEASE_COMMIT, "tests"], capture_output=True, check=True)
    with tarfile.open(fileobj=io.BytesIO(tar.stdout)) as archive:
        archive.extractall(dest, filter="data")
    return dest


def acceptance_cells(text: str) -> dict[str, str]:
    """REQ id -> Acceptance cell of requirements.md."""
    out = {}
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 9 and cells[0].startswith("REQ-"):
            out[cells[0]] = cells[5]
    return out


def backing(audit_mod, tid: str, kind: str, carriers, eqs, sources):
    """Return the passing records with the row's marker that back one planned ID with the given evidence kind."""
    passing = [r for r in carriers if r["outcome"] == "passed"]
    if kind == "name":
        pat = audit_mod.id_pattern(tid)
        return [r for r in passing if pat.search(r["nodeid"].split("::")[-1].lower())]
    if kind == "file":
        return [r for r in passing if audit_mod.file_mentions(tid, sources[r["nodeid"].split("::")[0]])]
    if kind == "eqt":
        nums = eqs.get(tid, set())
        return [r for r in passing if any(e.split("-")[1] in nums for e in r["eqt"])]
    return passing


def pick(records):
    """Return the record whose node id has the smallest SHA-256."""
    return min(records, key=lambda r: hashlib.sha256(r["nodeid"].encode()).hexdigest()) if records else None


def test_source(tree: Path, nodeid: str) -> tuple[int, str]:
    """First line and source text of the test function a node id names (parameters and class stripped)."""
    path, *names = nodeid.split("::")
    func = names[-1].split("[")[0]
    text = (tree / path).read_text(encoding="utf-8")
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name == func:
            start = min([node.lineno] + [d.lineno for d in node.decorator_list])
            return start, "\n".join(text.splitlines()[start - 1 : node.end_lineno])
    raise LookupError(nodeid)


def sample(audit_mod, tree: Path):
    """Return the audit results, the verified-row samples and the cause-B items."""
    audit_mod.RELEASE_TREE = tree
    rows = audit_mod.parse_requirements(audit_mod.REQUIREMENTS.read_text(encoding="utf-8"))
    records = json.loads(audit_mod.REPORT.read_text(encoding="utf-8"))
    gates = audit_mod.gate_ids(audit_mod.GATE_LOG.read_text(encoding="utf-8"))
    eqs = audit_mod.eq_map([p.read_text(encoding="utf-8") for p in audit_mod.PLANS])
    files = {r["nodeid"].split("::")[0] for r in records}
    sources = {f: (tree / f).read_text(encoding="utf-8", errors="replace") for f in files}
    results = audit_mod.audit(rows, records, gates, eqs, sources)

    log = audit_mod.GATE_LOG.read_text(encoding="utf-8")
    gate_lines = [line for line in log.splitlines() if line.startswith("PASS")]
    samples = []
    for row, status, *_, evidence, _ in results:
        if status == "verified" and row.priority == "must":
            carriers = [r for r in records if row.req_id in r["req"]]
            samples.append((row.req_id, choose(audit_mod, row, evidence, carriers, eqs, sources, gate_lines)))
    return results, samples


def choose(audit_mod, row, evidence, carriers, eqs, sources, gate_lines):
    """Return (planned ID, evidence kind, node id or gate line or record) for one verified row."""
    for kind in KIND_ORDER:
        for tid in row.tests:
            if evidence[tid] != kind:
                continue
            if kind == "gate":
                line = next(g for g in gate_lines if tid in audit_mod.TEST_ID.findall(g))
                return (tid, kind, f"gate log: {' '.join(line.split())}")
            if kind == "record":
                return (tid, kind, f"record: {audit_mod.RECORDS[tid]}")
            if rec := pick(backing(audit_mod, tid, kind, carriers, eqs, sources)):
                return (tid, kind, rec["nodeid"])
    return None


def is_test(where: str) -> bool:
    """Return True when the sample is a pytest node id (not a gate line or a record)."""
    return "::" in where


def applied_counts(results, sample_rulings, cause_b_rulings, strict: bool):
    """Row status counts after the rulings: all rows and must rows.

    A sampled row ruled `does not check` drops to `partial`; with strict=True a `partial` ruling drops it too.
    A cause-B ID ruled `checks` counts as evidence; a row whose every planned ID then has evidence, with none
    needing another machine, becomes `verified`.
    """
    passing_kinds = ("gate", "name", "file", "eqt", "record")
    drop = {"does not check", "partial"} if strict else {"does not check"}
    statuses = []
    for row, status, *_, evidence, blocked in results:
        new = status
        ruling = sample_rulings.get(row.req_id)
        if status == "verified" and ruling and ruling[0] in drop:
            new = "partial"
        if row.req_id in CAUSE_B and status == "partial":
            ok = all(
                evidence[t] in passing_kinds or cause_b_rulings.get((row.req_id, t), ("",))[0] == "checks"
                for t in row.tests
            )
            if ok and not blocked:
                new = "verified"
        statuses.append((row, new))
    every = Counter(s for _, s in statuses)
    must = Counter(s for r, s in statuses if r.priority == "must")
    return every, must


def fmt(counter) -> str:
    """Return 'status n, status n' sorted by status."""
    return ", ".join(f"{k} {v}" for k, v in sorted(counter.items()))


def cell(text: str) -> str:
    """Return text safe for one Markdown table cell."""
    return text.replace("|", "\\|").replace("\n", " ")


def dump(path: Path, samples, sources, accept, audit_mod) -> None:
    """Write each sample's acceptance and test source, then each cause-B ID's plan rows and candidate tests."""
    out = []
    for req, chosen in samples:
        out.append(f"=== {req} | ACCEPTANCE: {accept[req]}")
        if chosen and is_test(chosen[2]):
            line, src = sources[chosen[2]]
            out.append(f"--- {chosen[0]} ({chosen[1]}) {chosen[2]} l.{line}\n{src}")
        else:
            out.append(f"--- {chosen}")
    records = json.loads(audit_mod.REPORT.read_text(encoding="utf-8"))
    plan_rows = [
        line
        for p in audit_mod.PLANS
        for line in p.read_text(encoding="utf-8").splitlines()
        if line.startswith("| ") and audit_mod.TEST_ID.match(line[2:])
    ]
    for req, ids in CAUSE_B.items():
        names = sorted({r["nodeid"].split("[")[0] for r in records if req in r["req"] and r["outcome"] == "passed"})
        for tid in ids:
            out.append(f"=== CAUSE-B {req} {tid} | ACCEPTANCE: {accept[req]}")
            out += [f"PLAN {line[:400]}" for line in plan_rows if line.startswith(f"| {tid} ")]
            out += [f"CANDIDATE {n}" for n in names]
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def render(samples, sources, accept, rulings_mod, results) -> tuple[str, list[str]]:
    """Return the record text and the summary lines to print."""
    lines = [
        "Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5",
        "",
        "# V3-01: do the tests check the acceptance text? (generated)",
        "",
        "Generated by `python3 tests/independent/m7/v3_01_sample.py` on main 3cb23e5. Do not edit by hand; the rulings",
        "live in `tests/independent/m7/v3_01_rulings.py`. Test sources are the release run's tree (`git archive "
        f"{RELEASE_COMMIT} tests`).",
        "Ruling words: `checks` = the test asserts the criterion's value and tolerance; `partial` = it asserts part of",
        "the criterion (the missing part is named); `does not check` = it asserts none of it (the reason is named).",
        "Every ruling is `verified` by reading the test source at the line given; no test was run for this table.",
        "",
        "## Part A: one passing test per `verified` must row",
        "",
        "| REQ | Acceptance (requirements.md) | Sampled test (planned ID, evidence) | Ruling | Reason |",
        "|---|---|---|---|---|",
    ]
    tally = Counter()
    for req, chosen in samples:
        ruling, reason = rulings_mod.SAMPLE_RULINGS[req]
        tally[ruling] += 1
        where = f"{chosen[2]} ({chosen[0]}, {chosen[1]})"
        if is_test(chosen[2]):
            where = f"`{chosen[2]}` l.{sources[chosen[2]][0]} ({chosen[0]}, {chosen[1]})"
        lines.append(f"| {req} | {cell(accept[req])} | {where} | {ruling} | {cell(reason)} |")
    lines += ["", f"Part A rulings: {fmt(tally)} (of {len(samples)}).", ""]
    lines += [
        "## Part B: every cause-B ID",
        "",
        "| REQ | ID | Ruling | Test(s) read | Reason |",
        "|---|---|---|---|---|",
    ]
    tally_b = Counter()
    for req, ids in CAUSE_B.items():
        for tid in ids:
            ruling, reason, nodeids = rulings_mod.CAUSE_B_RULINGS[(req, tid)]
            tally_b[ruling] += 1
            read = "; ".join(f"`{n}` l.{sources[n][0]}" for n in nodeids) or "-"
            lines.append(f"| {req} | {tid} | {ruling} | {read} | {cell(reason)} |")
    lines += ["", f"Part B rulings: {fmt(tally_b)} (of {sum(tally_b.values())}).", ""]

    base_all = Counter(s for _, s, *_ in results)
    base_must = Counter(s for r, s, *_ in results if r.priority == "must")
    sample_rulings = rulings_mod.SAMPLE_RULINGS
    lenient = applied_counts(results, sample_rulings, rulings_mod.CAUSE_B_RULINGS, strict=False)
    strict = applied_counts(results, sample_rulings, rulings_mod.CAUSE_B_RULINGS, strict=True)
    lines += [
        "## Audit counts with the rulings applied",
        "",
        "Rule (see `applied_counts`): a sampled row ruled `does not check` drops from `verified` to `partial`. In the",
        "strict count a `partial` ruling drops it too. A cause-B ID ruled `checks` counts as evidence, and a row whose",
        "every planned ID then has evidence (none needing another machine) becomes `verified`.",
        "",
        "```",
        f"req_audit.py as released:  {fmt(base_all)}; must rows: {fmt(base_must)}",
        f"rulings applied (lenient): {fmt(lenient[0])}; must rows: {fmt(lenient[1])}",
        f"rulings applied (strict):  {fmt(strict[0])}; must rows: {fmt(strict[1])}",
        "```",
    ]
    printed = [
        f"{label}: {fmt(every)}; must: {fmt(must)}"
        for label, (every, must) in (("lenient", lenient), ("strict", strict))
    ]
    printed.append(f"part A: {fmt(tally)}; part B: {fmt(tally_b)}")
    return "\n".join(lines) + "\n", printed


def main(argv=None) -> int:
    """Sample, then write the dump or the record; exit 1 while a sample has no ruling."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dump", type=Path, help="write each sample's acceptance text and test source to this file")
    args = parser.parse_args(argv)

    audit_mod = load("req_audit", REPO / "docs/phase3/verification/checks/req_audit.py")
    rulings_mod = load("v3_01_rulings", HERE / "v3_01_rulings.py")
    accept = acceptance_cells(audit_mod.REQUIREMENTS.read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory() as tmp:
        tree = release_tests(Path(tmp))
        results, samples = sample(audit_mod, tree)
        nodeids = [c[2] for _, c in samples if c and is_test(c[2])]
        nodeids += [n for ruling in rulings_mod.CAUSE_B_RULINGS.values() for n in ruling[2]]
        sources = {n: test_source(tree, n) for n in nodeids}

    base_all = Counter(s for _, s, *_ in results)
    base_must = Counter(s for r, s, *_ in results if r.priority == "must")
    print(f"audit reproduced: {fmt(base_all)}; must: {fmt(base_must)}")
    if args.dump:
        dump(args.dump, samples, sources, accept, audit_mod)
        print(f"wrote {args.dump}")
        return 0

    missing = [req for req, _ in samples if req not in rulings_mod.SAMPLE_RULINGS]
    missing += [f"{r} {t}" for r, ids in CAUSE_B.items() for t in ids if (r, t) not in rulings_mod.CAUSE_B_RULINGS]
    bad = [k for k, v in {**rulings_mod.SAMPLE_RULINGS, **rulings_mod.CAUSE_B_RULINGS}.items() if v[0] not in RULINGS]
    if missing or bad:
        print(f"no ruling for: {missing}; unknown ruling word for: {bad}")
        return 1
    text, printed = render(samples, sources, accept, rulings_mod, results)
    RECORD.parent.mkdir(parents=True, exist_ok=True)
    RECORD.write_text(text, encoding="utf-8")
    print("\n".join(printed))
    print(f"wrote {RECORD.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
