"""Predict the badge of every result of an example from the registry and compare with what embodic.api returns.

Usage (inside the wheel venv): python -I badge_check.py [--example spiral_12c10p_d08] [--out table.json]

The prediction is mine and reads only the installed registry files:
- equations.v1.json: per equation its "tests" list, "status", "gate_verdict", the order "status_order_weakest_first"
  and "result_badge_rule" (badge = weakest of every chain equation's status, the implementation test state, and a
  validity cap -> unresolved).
- passed_tests.v1.json if the installed package carries it (absent -> no equation passes).
An equation passes when every EQT id it lists is in passed_tests (interfaces.md §3.1 "What changes on screen").
A gate "cannot verify yet" equation adds unresolved. An empty chain reads "not tested".
Taken from the product output, not predicted: each result's eq_ids (its chain) and which validity flags carry the
effect "cap". Exit 0 when every result's badge equals the prediction.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

from embodic import api
from embodic.paths import resource_root


def traceables(analysis: object) -> list[tuple[str, object]]:
    """Return (name, Traceable) for every result field of the analysis, tuples expanded."""
    found: list[tuple[str, object]] = []
    for f in dataclasses.fields(analysis):
        value = getattr(analysis, f.name)
        items = value if isinstance(value, tuple) else (value,)
        for k, item in enumerate(items):
            if hasattr(item, "status") and hasattr(item, "eq_ids"):
                found.append((f.name if len(items) == 1 else f"{f.name}[{k}]", item))
    return found


def predict(eq_ids: tuple[str, ...], caps: int, registry: dict, passed: set[str]) -> str:
    """Return my predicted badge for one chain and its number of validity caps."""
    order = registry["status_order_weakest_first"]
    by_id = {e["id"]: e for e in registry["equations"]}
    if not eq_ids:
        return "not tested"
    statuses: list[str] = []
    for eq_id in eq_ids:
        eq = by_id[eq_id]
        if eq["gate_verdict"] == "cannot verify yet":
            statuses.append("unresolved")
            continue
        statuses.append(eq["status"])
        if not set(eq["tests"]) <= passed:
            statuses.append("not tested")
    statuses += ["unresolved"] * caps
    return min(statuses, key=order.index)


def main() -> int:
    """Compute the example, predict every badge, print the table; exit 1 on a difference."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--example", default="spiral_12c10p_d08")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    folder = resource_root() / "evidence"
    registry = json.loads((folder / "equations.v1.json").read_text())
    evidence_path = folder / "passed_tests.v1.json"
    passed = set(json.loads(evidence_path.read_text())["passed_tests"]) if evidence_path.exists() else set()
    print(f"evidence file present: {evidence_path.exists()} ({len(passed)} passed ids)")
    eq_pass = {e["id"]: set(e["tests"]) <= passed for e in registry["equations"]}
    print(f"equations whose every test passed: {sorted(k for k, v in eq_pass.items() if v)}")

    outcome = api.compute_project(resource_root() / "examples" / f"{args.example}.embodic.json")
    rows = []
    for name, t in traceables(outcome.analysis):
        caps = sum(1 for flag in t.validity if str(flag.effect.value) == "cap")
        expected = predict(tuple(t.eq_ids), caps, registry, passed)
        actual = str(t.status.value)
        rows.append({"result": name, "eq_ids": list(t.eq_ids), "caps": caps, "predicted": expected, "actual": actual})
    width = max(len(r["result"]) for r in rows)
    for r in rows:
        mark = "ok  " if r["predicted"] == r["actual"] else "DIFF"
        print(
            f"{mark} {r['result']:<{width}} {r['actual']:<11} predicted {r['predicted']:<11} "
            f"chain {','.join(r['eq_ids']) or '-'} caps {r['caps']}"
        )
    diffs = [r for r in rows if r["predicted"] != r["actual"]]
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["actual"]] = counts.get(r["actual"], 0) + 1
    print(
        f"{len(rows)} results, actual badge counts {dict(sorted(counts.items()))}, {len(diffs)} differ from prediction"
    )
    if args.out is not None:
        args.out.write_text(json.dumps({"evidence_present": evidence_path.exists(), "rows": rows}, indent=1))
    return 1 if diffs else 0


if __name__ == "__main__":
    sys.exit(main())
