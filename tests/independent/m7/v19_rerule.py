"""U-V19 lever: pin, check, predict and record the rulings of v3_01_rulings_v19.py and the ID map u_v19_id_map.py.

    python3 tests/independent/m7/v19_rerule.py --pin        # writes records/V3-01_pins_c25d8a9_v19.json
    python3 tests/independent/m7/v19_rerule.py --check      # every cite and mapped test ran, with its marker, passed
    python3 tests/independent/m7/v19_rerule.py --predict    # the audit now, with v19 wired in, and after U-M8y
    python3 tests/independent/m7/v19_rerule.py --write      # writes records/V3-01_U-V19.md and U-V19_id_map.md

The test sources are `git archive c25d8a9 tests`; the reports and the gate log are req_audit.py's 0.0.4 inputs,
merged as it merges them. "After U-M8y" applies the map to copies of both: each rename changes the def line only, the
map's TEXT_EDITS change the two UT-GEO-26 docstrings, and then `ruff format` (c25d8a9's pyproject.toml) runs on
the file; each added marker joins the records of its test; each
new test is a passed record with its markers. That prediction assumes every new test passes as specified (`inferred`).
A renamed cite's pin is the hash of the segment in that renamed copy, so the audit matches it after U-M8y only when
the rename changed nothing else.
"""

import argparse
import ast
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RULINGS_RECORD = HERE / "records/V3-01_U-V19.md"
MAP_RECORD = HERE / "records/U-V19_id_map.md"
RUFF = "/home/claude/embodic/.venv/bin/ruff"
ROWS = (
    "REQ-F-08 REQ-F-12 REQ-N-09 REQ-N-10 REQ-T-05 REQ-T-08 REQ-T-14 REQ-L-01 REQ-L-05 "
    "REQ-F-03 REQ-F-05 REQ-F-06 REQ-F-10 REQ-F-14 REQ-N-12 REQ-N-21 REQ-N-27 REQ-T-15 REQ-F-13"
).split()


def load(path: Path):
    """Import a module by path."""
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AUDIT = load(REPO / "docs/phase3/verification/checks/req_audit.py")
V13, V14, V18 = (load(HERE / f"v3_01_rulings_{v}.py") for v in ("v13", "v14", "v18"))
V19 = load(HERE / "v3_01_rulings_v19.py")
MAP = load(HERE / "u_v19_id_map.py")
TARGET = AUDIT.TARGETS["0.0.4"]


def renames() -> dict[str, str]:
    """Return {c25d8a9 cite: new function name} of every rename in the map."""
    out = {cite: new for e in MAP.ENTRIES for cite, new in e.rename}
    for cite, new in V19.RENAMES.items():
        assert out.get(cite) == new, f"v3_01_rulings_v19.RENAMES disagrees with the map on {cite}"
    return out


def added_markers() -> dict[str, set[str]]:
    """Return {c25d8a9 cite: REQ markers U-M8y adds}."""
    out: dict[str, set[str]] = defaultdict(set)
    for e in MAP.ENTRIES:
        for cite, req in e.add_req:
            out[cite].add(req)
    return out


def new_tests() -> dict[str, tuple[str, ...]]:
    """Return {cite: REQ markers} of every test that the map and EXTRA ask U-M8y to add."""
    out = {cite: markers for e in MAP.ENTRIES for cite, markers in e.new}
    out.update({cite: markers for cite, markers, _ in MAP.EXTRA.values()})
    return out


def rename_def(text: str, old: str, new: str) -> str:
    """Return the module source with the def line of function ``old`` naming ``new``; nothing else changes."""
    nodes = [n for n in ast.walk(ast.parse(text)) if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)]
    (node,) = [n for n in nodes if n.name == old]
    lines = text.splitlines(keepends=True)
    assert lines[node.lineno - 1].count(f"def {old}(") == 1, (old, lines[node.lineno - 1])
    lines[node.lineno - 1] = lines[node.lineno - 1].replace(f"def {old}(", f"def {new}(")
    return "".join(lines)


def renamed_tree(tree: Path, dest: Path) -> Path:
    """Copy the test tree to dest with every rename of the map applied and the changed files formatted by ruff."""
    shutil.copytree(tree / "tests", dest / "tests")
    pyproject = subprocess.run(
        ["git", "-C", str(REPO), "show", f"{V19.BASE}:pyproject.toml"], capture_output=True, check=True
    ).stdout
    (dest / "pyproject.toml").write_bytes(pyproject)
    by_file: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for cite, new in renames().items():
        path, _, old = cite.partition("::")
        by_file[path].append((old, new))
    for path, *_ in MAP.TEXT_EDITS:
        by_file.setdefault(path, [])
    for path, pairs in by_file.items():
        file = dest / path
        text = file.read_text(encoding="utf-8")
        for old, new in pairs:
            text = rename_def(text, old, new)
        for edit_path, old, new in MAP.TEXT_EDITS:
            if edit_path == path:
                assert text.count(old) == 1, (path, old)
                text = text.replace(old, new)
        file.write_text(text, encoding="utf-8")
    subprocess.run([RUFF, "format", "--quiet", *by_file], cwd=dest, check=True)
    return dest


def pins_of(tree: Path, after: Path) -> dict[str, dict[str, str]]:
    """Return {req: {cite: sha256}} of every `checks` ruling of v19; a renamed cite is hashed in the renamed tree."""
    out = {}
    for req, ruling in sorted(V19.RULINGS.items()):
        if ruling.ruling != "checks":
            continue
        row = {}
        for cite in ruling.cites:
            if cite.startswith("gate:"):
                continue
            first = V19.original(cite)
            if first == cite:
                row[cite] = AUDIT.cite_hash(cite, tree)
                assert row[cite] == AUDIT.cite_hash(cite, after), f"the renames changed an unrenamed cite: {cite}"
            else:
                row[cite] = AUDIT.cite_hash(cite, after)
            assert row[cite] != "missing", cite
        out[req] = row
    return out


def merged_records() -> list[dict]:
    """Return the 0.0.4 REQ records, the latency report's outcomes replacing `not run` (as req_audit.py does)."""
    return AUDIT.read_reports(TARGET.reports)


def records_after(records: list[dict]) -> list[dict]:
    """Return the records as U-M8y would leave them, with each new test as a passed record."""
    moved, marks = renames(), added_markers()
    out = []
    for record in records:
        base, bracket, param = record["nodeid"].partition("[")
        r = dict(record)
        if base in marks:
            r["req"] = sorted({*r["req"], *marks[base]})
        if base in moved:
            r["nodeid"] = f"{base.partition('::')[0]}::{moved[base]}{bracket}{param}"
        out.append(r)
    seen = {r["nodeid"].split("[")[0] for r in out}
    for cite, markers in new_tests().items():
        if cite not in seen:
            out.append({"nodeid": cite, "req": list(markers), "eq": [], "eqt": [], "outcome": "passed"})
    return out


def run(tree: Path, records: list[dict], overlays) -> tuple[list, list[str]]:
    """Run req_audit.py's audit and D-051e gate on given records and test sources, with these ruling overlays."""
    rows = AUDIT.parse_requirements(AUDIT.REQUIREMENTS.read_text(encoding="utf-8"))
    gates = AUDIT.gate_ids(AUDIT.read_bytes(TARGET.gate_log).decode("utf-8"))
    eqs = AUDIT.eq_map([p.read_text(encoding="utf-8") for p in AUDIT.PLANS])
    files = {r["nodeid"].split("::")[0] for r in records}
    sources = {
        f: (tree / f).read_text(encoding="utf-8", errors="replace") if (tree / f).is_file() else "" for f in files
    }
    by_id = AUDIT.counted_records()
    counted = set(by_id.values())
    text = AUDIT.audit(rows, records, gates, eqs, sources, by_id)
    rulings = {**V13.RULINGS, **{k: v for o in overlays for k, v in o.RULINGS.items()}}
    pins = {
        **json.loads(AUDIT.PINS_V13.read_text(encoding="utf-8")),
        **{k: v for o in overlays for k, v in o.PINS.items()},
    }
    gated, notes = AUDIT.apply_rulings(
        text, lambda req: AUDIT.main_ruling_gate(req, rulings, pins, tree, gates, counted)
    )
    lacking = [[t for t, kind in evidence.items() if kind not in AUDIT.PASSING_KINDS] for *_, evidence, _ in text]
    notes = [f"{n}; no evidence: {', '.join(x)}" if x else n for n, x in zip(notes, lacking, strict=True)]
    return gated, notes


def must_counts(gated) -> Counter:
    """Return the status counts of the must rows."""
    return Counter(status for row, status, *_ in gated if row.priority == "must")


def predict() -> dict[str, tuple[Counter, dict[str, tuple[str, str]]]]:
    """Return the must counts and the status and note of every row, for the three states of the audit."""
    records = merged_records()
    out = {}
    with tempfile.TemporaryDirectory() as tmp:
        tree = AUDIT.test_tree(V19.BASE, Path(tmp) / "c25d8a9")
        after = renamed_tree(tree, Path(tmp) / "after")
        v19 = SimpleNamespace(RULINGS=V19.RULINGS, PINS=pins_of(tree, after))
        for label, t, recs, overlays in (
            ("0.0.4 as audited (v13, v14, v18)", tree, records, (V14, V18)),
            ("0.0.4 with v19 wired in", tree, records, (V14, V18, v19)),
            ("after U-M8y with v19 wired in", after, records_after(records), (V14, V18, v19)),
        ):
            gated, notes = run(t, recs, overlays)
            rows = {row.req_id: (status, note) for (row, status, *_), note in zip(gated, notes, strict=True)}
            out[label] = (must_counts(gated), rows)
    return out


def _cite_problem(req: str, cite: str, runs, gates: set[str], counted: set[str]) -> str | None:
    """Return why one cite of a v19 ruling does not stand on the 0.0.4 run, or None."""
    if cite.startswith("gate:"):
        return None if cite.removeprefix("gate:") in gates else f"{req}: no PASS line for {cite}"
    if cite.startswith("record:"):
        return None if cite.removeprefix("record:") in counted else f"{req}: record not counted by the index: {cite}"
    found = runs.get(V19.original(cite), [])
    if not found:
        return f"{req}: not in the 0.0.4 report: {V19.original(cite)}"
    outcomes, markers = sorted({r["outcome"] for r in found}), sorted({x for r in found for x in r["req"]})
    if any(req not in r["req"] for r in found) or outcomes != ["passed"]:
        return f"{req}: {cite} ran {outcomes} with {markers}"
    return None


def _entry_problems(entry, runs) -> list[str]:
    """Return why the tests and actions of one map entry do not match the 0.0.4 run."""
    out = []
    for cite in entry.tests:
        if {r["outcome"] for r in runs.get(cite, [])} != {"passed"}:
            out.append(f"{entry.req} {entry.test_id}: mapped test missing or not passed in 0.0.4: {cite}")
    for cite, _ in (*entry.rename, *entry.add_req):
        if cite not in runs:
            out.append(
                f"{entry.req} {entry.test_id}: U-M8y action names a test that is not in the 0.0.4 report: {cite}"
            )
    for cite, _ in entry.new:
        if cite in runs:
            out.append(f"{entry.req} {entry.test_id}: the new test already exists: {cite}")
    return out


def problems() -> list[str]:
    """Return one line per v19 cite or mapped test that did not run, lacks its marker or did not pass."""
    runs: dict[str, list[dict]] = defaultdict(list)
    for r in merged_records():
        runs[r["nodeid"].split("[")[0]].append(r)
    gates = AUDIT.gate_ids(AUDIT.read_bytes(TARGET.gate_log).decode("utf-8"))
    counted = set(AUDIT.counted_records().values())
    out = [
        line
        for req, ruling in sorted(V19.RULINGS.items())
        for cite in ruling.cites
        if (line := _cite_problem(req, cite, runs, gates, counted))
    ]
    for entry in MAP.ENTRIES:
        out += _entry_problems(entry, runs)
    return out


def _cites(cites) -> str:
    return "<br>".join(f"`{c}`" for c in cites) or "-"


def render_rulings(prediction) -> str:
    """Return records/V3-01_U-V19.md."""
    now = prediction["0.0.4 with v19 wired in"][1]
    lines = [
        "Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5",
        "",
        "# V3-01 on release 0.0.4: the U-V13 rows, the text-only rows and the renamed cites (U-V19, generated)",
        "",
        "Generated by `python3 tests/independent/m7/v19_rerule.py --write`. Do not edit by hand; the rulings live in",
        "`tests/independent/m7/v3_01_rulings_v19.py`, the ID map in `u_v19_id_map.py`. Ruling words as in `V3-01.md`.",
        "Audit status: the row's status when req_audit.py --target 0.0.4 applies v19 after v18 (`--predict`; wiring",
        "RULINGS_V19 and its PINS into req_audit.py is U-M8y's, outside U-V19's scope). Cites name functions as they",
        "are after U-M8y's renames; `--check` reads each under its c25d8a9 name in the 0.0.4 reports.",
        "",
        "## Predicted must-row counts (`v19_rerule.py --predict`)",
        "",
        "```",
        *(f"{label}: " + ", ".join(f"{k} {v}" for k, v in sorted(c.items())) for label, (c, _) in prediction.items()),
        "```",
        "",
        "| REQ | Ruling | Audit status with v19 | Tests cited | Reason | Missing (kind, owner) |",
        "|---|---|---|---|---|---|",
    ]
    for req, r in sorted(V19.RULINGS.items()):
        missing = f"{r.missing} ({r.kind}, {r.owner})" if r.missing else "-"
        lines.append(f"| {req} | {r.ruling} | {now[req][0]} | {_cites(r.cites)} | {r.reason} | {missing} |")
    after = prediction["after U-M8y with v19 wired in"][1]
    lines += [
        "",
        "## The 19 cloud rows of V3-15 after U-M8y (predicted)",
        "",
        "| REQ | Now | With v19 | After U-M8y | Note after U-M8y |",
        "|---|---|---|---|---|",
    ]
    base = prediction["0.0.4 as audited (v13, v14, v18)"][1]
    for req in ROWS:
        lines.append(f"| {req} | {base[req][0]} | {now[req][0]} | {after[req][0]} | {after[req][1]} |")
    return "\n".join(lines) + "\n"


def render_map() -> str:
    """Return records/U-V19_id_map.md."""
    counts = Counter(e.decision for e in MAP.ENTRIES)
    lines = [
        "Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5",
        "",
        "# Planned test IDs of the nine text-only must rows of release 0.0.4 (U-V19 item 2, generated)",
        "",
        "Generated by `python3 tests/independent/m7/v19_rerule.py --write` from",
        "`tests/independent/m7/u_v19_id_map.py`.",
        "Do not edit by hand. Decisions (D-046c): (a) the tests named check the ID's criterion as written in",
        "test_plan.md, together; U-M8y renames or marks them so that a test with the row's REQ marker names the ID;",
        "(b) no test checks it, U-M8y adds the test specified; (c) spec defect, for Agent 6. Tests are named as on",
        "c25d8a9. A rename changes the def line only; the body stays as it is. Rows: the IDs with evidence `none` in",
        "req_audit.md of 0.0.4, and UT-GEO-19, whose `name` evidence comes from tests that check UT-GEO-26.",
        "",
        f"Counts: (a) {counts['a']}, (b) {counts['b']}, (c) {counts['c']} of {len(MAP.ENTRIES)} planned IDs.",
        "",
        "| REQ | Planned ID | Decision | Tests on c25d8a9 | U-M8y action "
        "| Spec (input, expected and source, tolerance) or defect |",
        "|---|---|---|---|---|---|",
    ]
    for e in MAP.ENTRIES:
        actions = [f"rename `{c.partition('::')[2]}` to `{n}`" for c, n in e.rename]
        actions += [f"add {req} to `{c.partition('::')[2]}`" for c, req in e.add_req]
        actions += [f"add `{c}` (markers {', '.join(m)})" for c, m in e.new]
        actions += [f"in `{p}` replace `{o}` by `{n}`" for p, o, n in MAP.TEXT_EDITS if e.test_id == "UT-GEO-26"]
        lines.append(
            f"| {e.req} | {e.test_id} | {e.decision} | {_cites(e.tests)} | {'<br>'.join(actions) or '-'} | {e.spec} |"
        )
    lines += [
        "",
        "## Tests specified by U-V19 items 1 and 3 (not planned IDs)",
        "",
        "| Key | New test | Markers | Spec |",
        "|---|---|---|---|",
        *(f"| {key} | `{cite}` | {', '.join(m)} | {spec} |" for key, (cite, m, spec) in MAP.EXTRA.items()),
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    """Run the action the flag names."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group(required=True)
    for flag in ("--pin", "--check", "--predict", "--write"):
        group.add_argument(flag, action="store_true")
    args = parser.parse_args()
    if args.pin:
        with tempfile.TemporaryDirectory() as tmp:
            tree = AUDIT.test_tree(V19.BASE, Path(tmp) / "c25d8a9")
            pins = pins_of(tree, renamed_tree(tree, Path(tmp) / "after"))
        V19.PIN_FILE.write_text(json.dumps(pins, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote {V19.PIN_FILE.relative_to(REPO)}: {sum(len(v) for v in pins.values())} pins, {len(pins)} rows")
        return 0
    if args.check:
        found = problems()
        print("\n".join(found) or "every v19 cite and mapped test ran with its marker and passed in the 0.0.4 run")
        return 1 if found else 0
    prediction = predict()
    if args.predict:
        for label, (counts, rows) in prediction.items():
            print(f"{label}: must " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
            print("   " + ", ".join(f"{r} {rows[r][0]}" for r in ROWS))
        return 0
    RULINGS_RECORD.write_text(render_rulings(prediction), encoding="utf-8")
    MAP_RECORD.write_text(render_map(), encoding="utf-8")
    print(f"wrote {RULINGS_RECORD.relative_to(REPO)} and {MAP_RECORD.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
