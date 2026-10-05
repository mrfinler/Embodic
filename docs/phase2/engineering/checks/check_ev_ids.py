# Prepared by: Agent 2 — Motor Design Expert — model: claude-opus-5-5
"""Check every EV id the equation registry cites (sources, constants) against the evidence register; exit 1 on a miss.

An id outside phase2_scope also fails: tools/sync_registry.py ships only phase2_scope entries (D-023 a).
Run: python3 docs/phase2/engineering/checks/check_ev_ids.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
reg = json.loads((ROOT / "docs/phase2/engineering/equation_registry.json").read_text(encoding="utf-8"))
register = json.loads((ROOT / "docs/phase2/evidence/evidence_register.json").read_text(encoding="utf-8"))
entries = {e["id"]: e for e in register["entries"]}
cited = {
    (e["id"], ev)
    for e in reg["equations"]
    for ev in [*e["sources"], *(c["source"] for c in e["constants"] if c["source"])]
}
missing = sorted(pair for pair in cited if pair[1] not in entries)
unscoped = sorted(pair for pair in cited if pair[1] in entries and not entries[pair[1]]["phase2_scope"])
print(f"cited (equation, EV) pairs: {len(cited)} | distinct EV ids: {len({ev for _, ev in cited})}")
print(f"missing: {missing} | outside phase2_scope: {unscoped}")
sys.exit(1 if missing or unscoped else 0)
