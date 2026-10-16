# Prepared by: Agent 2 — Motor Design Expert — model: claude-opus-5-5
"""List every registry text the equation guide or a result disclosure shows that names another program; exit 1 on a hit.

The registry is the docs copy (docs/phase2/engineering/equation_registry.json), parsed by the shipped parser and rendered by
the shipped guide view model (src/embodic/ui/viewmodels/results.py equation_topic, l.699 to l.750). The evidence register
is filtered to phase2_scope as tools/sync_registry.py ships it. The disclosure line `{eq}: {name}. {formula}` (l.226) and
the validity-check metric (l.157) use fields the guide rows already contain, except the metric, which is scanned on its own.
Run: PYTHONPATH=src python docs/phase3/engineering/checks/guide_name_scan.py
"""

import json
import re
import sys
from pathlib import Path

from embodic.results.registry import parse_registry
from embodic.ui.viewmodels.results import equation_topic

ROOT = Path(__file__).resolve().parents[4]
PROGRAM = re.compile(r"xcoil", re.IGNORECASE)  # REQ-L-03 acceptance: 0 occurrences of "xcoil", case-insensitive
NOTE = re.compile(r"engine\.js", re.IGNORECASE)  # the reference generator's file name; reported, not a REQ-L-03 failure

equations = json.loads((ROOT / "docs/phase2/engineering/equation_registry.json").read_text(encoding="utf-8"))
evidence = json.loads((ROOT / "docs/phase2/evidence/evidence_register.json").read_text(encoding="utf-8"))
evidence["entries"] = [e for e in evidence["entries"] if e["phase2_scope"]]
registry = parse_registry(equations, evidence, version="scan")

shown = []
for eq_id, entry in registry.equations.items():
    shown += [(eq_id, label, value) for label, value in equation_topic(eq_id, registry).rows]
    shown += [(eq_id, "check metric", c.metric) for c in entry.validity_checks]

hits = [(eq, label, PROGRAM.findall(value)) for eq, label, value in shown if PROGRAM.search(value)]
notes = [(eq, label) for eq, label, value in shown if NOTE.search(value)]
print(f"displayed registry texts scanned: {len(shown)} over {len(registry.equations)} equations")
print(f"'xcoil' hits: {len(hits)}")
for eq, label, found in hits:
    print(f"  {eq} [{label}] {found}")
print(f"'engine.js' mentions (not a REQ-L-03 failure): {notes}")
sys.exit(1 if hits else 0)
