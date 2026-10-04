# Prepared by: Agent 6 - Software Architecture Specialist - model: claude-opus-5-5
"""Compare Agent 1's screens.md with the merged field table (embodic.model.fields) and print every mismatch.

Run from anywhere (needs numpy, imports embodic from src/ without installing it):
    python3 docs/phase2/architecture/checks/screen_model_diff.py

It prints three lists that screen_model_reconciliation.md resolves:
  1. screens.md input widgets that no FieldSpec names (widgets without fields);
  2. widgets whose screens.md binding key differs from the model pointer (pointer names);
  3. pointers a blank draft lists as missing that no widget can fill (the form could never be completed).
Exit code 0 always; it reports, it does not judge.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "src"))

from embodic.model.draft import blank_draft, parse_draft  # noqa: E402
from embodic.model.fields import FIELDS, field_for  # noqa: E402
from embodic.model.vocabulary import TopologyKind  # noqa: E402

SCREENS = REPO / "docs/phase2/design/screens.md"
WIDGET = re.compile(r"`(param-[a-z0-9-]+)`")
POINTER = re.compile(r"`(/[a-z0-9_/.*]+)`")


def screen_bindings() -> dict[str, str | None]:
    """objectName -> binding key for every param-* widget in screens.md (None when the row or prose gives none)."""
    found: dict[str, str | None] = {}
    for line in SCREENS.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")] if line.lstrip().startswith("|") else [line]
        names = WIDGET.findall(cells[0])
        if not names:
            names = WIDGET.findall(line)
            for name in names:
                found.setdefault(name, None)
            continue
        key = next((m.group(1) for c in cells[1:] for m in [POINTER.search(c)] if m), None)
        for name in names:
            if found.get(name) is None:
                found[name] = key
    return found


def main() -> int:
    screens = screen_bindings()
    by_widget: dict[str, list[str]] = {}
    for spec in FIELDS:
        if spec.widget_id:
            by_widget.setdefault(spec.widget_id, []).append(spec.pointer + (f"#{spec.variant}" if spec.variant else ""))
    print("1. Widgets without fields")
    for name in sorted(set(screens) - set(by_widget)):
        print(f"  {name}  (screens.md key {screens[name]})")
    print("2. Binding key differs from the model pointer")
    for name in sorted(set(screens) & set(by_widget)):
        key, pointers = screens[name], by_widget[name]
        if key is not None and key not in [p.split("#")[0] for p in pointers]:
            print(f"  {name}: screens.md {key} -> model {', '.join(pointers)}")
    print("3. Required pointers of a blank draft that no widget fills")
    for topology in TopologyKind:
        draft = blank_draft(topology)
        result = parse_draft(draft)
        missing = getattr(result, "missing", ())
        orphan = [p for p in missing if field_for(p, draft.values).widget_id is None]
        print(f"  {topology.value}: {len(orphan)} of {len(missing)}: {', '.join(orphan)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
