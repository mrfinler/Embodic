# Prepared by: Agent 2 — Motor Design Expert — model: claude-opus-5-5
# Cross-checks equation_specification.md, equation_registry.json, oracle_cases.json and engine.js. Exit code 1 on any failure.
# Run: python3 docs/phase2/engineering/checks/check_consistency.py
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENG = os.path.dirname(HERE)
ENGINE = "/home/claude/serpentine/src/engine.js"
VERDICTS = ("reuse with change", "cannot verify yet", "replace", "reuse")

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)


spec = open(os.path.join(ENG, "equation_specification.md"), encoding="utf-8").read()
reg = json.load(open(os.path.join(ENG, "equation_registry.json")))
orc = json.load(open(os.path.join(ENG, "oracle_cases.json")))
engine_src = open(ENGINE, encoding="utf-8").read()
engine_funcs = set(re.findall(r"function\s+(\w+)\s*\(", engine_src))

sections = re.split(r"^### (EQ-\d\d) ", spec, flags=re.M)
spec_eq = {}
for i in range(1, len(sections), 2):
    body = sections[i + 1].split("\n## ")[0]
    m = re.search(r"Gate: `([^`]+)`", body)
    spec_eq[sections[i]] = {"verdict": m.group(1) if m else None, "body": body}

reg_eq = {e["id"]: e for e in reg["equations"]}
check(list(spec_eq) == list(reg_eq), f"EQ ids differ: spec {list(spec_eq)} vs registry {list(reg_eq)}")
for eid, e in reg_eq.items():
    s = spec_eq.get(eid)
    if not s:
        continue
    check(s["verdict"] == e["gate_verdict"], f"{eid}: spec verdict {s['verdict']!r} vs registry {e['gate_verdict']!r}")
    for field in ("applies_to", "golden_functions", "tests", "sources", "tolerance", "reference_case", "status", "formula"):
        check(field in e, f"{eid}: registry field {field} missing")
    for f in e.get("golden_functions", []) + e.get("replaced_functions", []):
        check(f in engine_funcs, f"{eid}: function {f} not defined in engine.js")
    for t in e.get("tests", []):
        check(t in s["body"], f"{eid}: test id {t} not named in the spec entry")
    for topo in e.get("applies_to", []):
        check(topo in ("spiral", "serpentine", "wave"), f"{eid}: bad topology {topo}")
    if e["gate_verdict"] == "reuse with change":
        check(bool(e.get("changes")) or "Changes" in s["body"] or "Change" in s["body"], f"{eid}: reuse with change without a stated change")

counts = {v: sorted(k for k, e in reg_eq.items() if e["gate_verdict"] == v) for v in VERDICTS}
table = re.search(r"## Gate summary(.*?)\n## ", spec, flags=re.S).group(1)
for v, ids in counts.items():
    row = re.search(rf"^\| {re.escape(v)} \| (\d+) \| ([^|]+)\|", table, flags=re.M)
    check(row is not None, f"gate summary row {v!r} missing")
    if row:
        listed = sorted("EQ-" + x.strip() for x in row.group(2).split(","))
        check(int(row.group(1)) == len(ids), f"gate summary {v}: count {row.group(1)} vs registry {len(ids)}")
        check(listed == ids, f"gate summary {v}: ids {listed} vs registry {ids}")

status_table = re.search(r"## Equation status(.*?)\n## |## Equation status(.*)$", spec, flags=re.S)
status_rows = re.findall(r"^\| ([\d, ]+) \| (\w[\w ]*?) \|", (status_table.group(1) or status_table.group(2)), flags=re.M)
seen = set()
for ids, status in status_rows:
    for x in ids.split(","):
        eid = "EQ-" + x.strip()
        seen.add(eid)
        check(reg_eq.get(eid, {}).get("status") == status, f"{eid}: status table {status!r} vs registry {reg_eq.get(eid, {}).get('status')!r}")
check(seen == set(reg_eq), f"status table covers {sorted(set(reg_eq) - seen)} missing")

for eid, s in spec_eq.items():
    for field in ("Formula", "Sources", "Variables", "Validity", "Limitation", "Reference", "Tolerance", "Gate", "Dominant", "Applies", "Tests"):
        check(field in s["body"], f"{eid}: spec entry lacks '{field}'")

port = re.search(r"## Serpentine and wave port gate(.*?)\n## ", spec, flags=re.S).group(1)
port_funcs = set(re.findall(r"`(\w+)`", "\n".join(l.split("|")[1] for l in port.splitlines() if l.startswith("| `"))))
for f in sorted(port_funcs):
    check(f in engine_funcs, f"port gate table: {f} not defined in engine.js")

case_ids = [c["case_id"] for c in orc["cases"]]
for c in orc["cases"]:
    for eid in c.get("eq_ids", []):
        check(eid in reg_eq, f"{c['case_id']}: unknown {eid}")
for eid, e in reg_eq.items():
    for t in e.get("tests", []):
        m = re.match(r"EQT-\d\d-CF(\d\d)$", t)
        if m:
            check(f"CF-{m.group(1)}" in case_ids, f"{eid}: test {t} refers to a missing case")
for need in ("O1-D08", "O2-D09", "O3-D10"):
    check(need in case_ids, f"oracle {need} missing")
check(next(c for c in orc["cases"] if c["case_id"] == "O3-D10")["runnable"] is False, "O3 must be marked not runnable")
for c in orc["cases"]:
    for k, v in c["inputs"].items():
        check(isinstance(v, dict) and "status" in v and "source" in v, f"{c['case_id']}.{k}: input without status or source")
for name, val in (("first line spec", spec.splitlines()[0]),):
    check(val.startswith("Prepared by: Agent 2") and "claude-opus-5-5" in val, f"{name}: model line missing")
check(reg["prepared_by"].endswith("claude-opus-5-5") and orc["prepared_by"].endswith("claude-opus-5-5"), "JSON prepared_by missing")

print("equations:", len(reg_eq), "| verdict counts:", {v: len(ids) for v, ids in counts.items()})
print("oracle cases:", case_ids)
print("engine functions referenced in the port gate table:", len(port_funcs))
if failures:
    print("FAIL")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("PASS: spec, registry, oracle cases and engine.js agree")
