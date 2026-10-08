# Prepared by: Agent 1 (UX/UI Expert Designer) - model: claude-opus-5-5
"""Check screens.md against the field table from the screens side; FieldSpec.widget_id is not read.

    .venv/bin/python docs/phase2/design/checks/screens_coverage.py          # check; exit 1 on a finding
    .venv/bin/python docs/phase2/design/checks/screens_coverage.py --table  # print the coverage table

Findings: an objectName defined in two rows; a binding pointer that is not a FIELDS pointer and not in AWAITING_FIELDS;
an AWAITING_FIELDS pointer that FIELDS now holds; a required pointer of a blank draft, or a required field under a
bound container, that no widget binds for its topology; a coverage table in screens.md that differs from the generated
one; a literal objectName that the UI code sets and that no screens.md table defines (screens.md section 14a).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "src"))

from embodic.model.draft import blank_draft, parse_draft  # noqa: E402
from embodic.model.fields import FIELD_BY_KEY, FIELDS, field_specs  # noqa: E402
from embodic.model.schema import pattern_of  # noqa: E402
from embodic.model.vocabulary import TopologyKind  # noqa: E402

SCREENS = REPO / "docs/phase2/design/screens.md"
WIDGET_ID = re.compile(r"`([a-z][a-z0-9*<>-]*)`")
POINTER = re.compile(r"`(/[a-z0-9_/*]+)`")
SEPARATOR = re.compile(r"^\|(\s*:?-+:?\s*\|)+\s*$")
TABLE_START = "| Pointer | spiral | serpentine | wave |"
# Pointers a decision has settled that FIELDS does not hold yet. Each entry becomes a finding once FIELDS holds it.
AWAITING_FIELDS: dict[str, str] = {}
UI_CODE = REPO / "src/embodic/ui"
SET_NAME = re.compile(r'setObjectName\("([a-z][a-z0-9-]*)"\)')


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _widget_tables(lines: list[str]) -> list[tuple[list[str], list[list[str]]]]:
    tables, i = [], 0
    while i < len(lines) - 1:
        if lines[i].startswith("|") and SEPARATOR.match(lines[i + 1]):
            header, rows, i = _cells(lines[i]), [], i + 2
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(_cells(lines[i]))
                i += 1
            if "objectName" in header:
                tables.append((header, rows))
        else:
            i += 1
    return tables


def _topologies_of(text: str) -> set[TopologyKind]:
    named = {t for t in TopologyKind if t.value in text}
    return named or set(TopologyKind)


def _read_screens() -> tuple[dict[str, int], dict[tuple[str, TopologyKind], list[str]], list[str]]:
    defined: dict[str, int] = {}
    bound: dict[tuple[str, TopologyKind], list[str]] = {}
    pointers: list[str] = []
    for header, rows in _widget_tables(SCREENS.read_text(encoding="utf-8").splitlines()):
        name_col = header.index("objectName")
        key_col = header.index("Binding key") if "Binding key" in header else None
        top_col = header.index("Topology") if "Topology" in header else None
        for row in rows:
            ids = WIDGET_ID.findall(row[name_col])
            for widget in ids:
                defined[widget] = defined.get(widget, 0) + 1
            if key_col is None:
                continue
            found = POINTER.findall(row[key_col])
            pointers.extend(found)
            for topology in _topologies_of(row[top_col] if top_col is not None else ""):
                for pointer in found:
                    bound.setdefault((pointer, topology), []).extend(ids)
    return defined, bound, pointers


def _blank_missing() -> dict[TopologyKind, list[str]]:
    result = {}
    for topology in TopologyKind:
        parsed = parse_draft(blank_draft(topology))
        result[topology] = [pattern_of(p) for p in getattr(parsed, "missing", ())]
    return result


def _reachable(pointer: str, topology: TopologyKind, bound: dict) -> bool:
    """Return False when an optional container of the field has no widget, so the field can never apply."""
    segments = pointer.split("/")
    for depth in range(2, len(segments)):
        ancestor = "/".join(segments[:depth])
        spec = FIELD_BY_KEY.get(ancestor)
        if spec is not None and not spec.required and (ancestor, topology) not in bound:
            return False
    return True


def _coverage_table(bound: dict, missing: dict[TopologyKind, list[str]]) -> list[str]:
    order = list(dict.fromkeys(p for topology in TopologyKind for p in missing[topology]))
    lines = [TABLE_START, "|---|---|---|---|"]
    for pointer in order:
        row = []
        for topology in TopologyKind:
            if pointer not in missing[topology]:
                row.append("not required")
            else:
                row.append(", ".join(f"`{w}`" for w in bound.get((pointer, topology), ["MISSING"])))
        lines.append(f"| `{pointer}` | " + " | ".join(row) + " |")
    return lines


def _names_in_code() -> set[str]:
    """Return the literal objectNames the UI code sets; f-string names follow a pattern row of section 14a."""
    return {name for path in UI_CODE.rglob("*.py") for name in SET_NAME.findall(path.read_text(encoding="utf-8"))}


def main() -> int:
    """Print the findings and return 1 when there is any."""
    defined, bound, pointers = _read_screens()
    spec_names = set(WIDGET_ID.findall((REPO / "docs/phase2/design/design_spec.md").read_text(encoding="utf-8")))
    missing = _blank_missing()
    findings = [f"objectName defined in {n} rows: {w}" for w, n in sorted(defined.items()) if n > 1]
    findings += [
        f"UI code sets an objectName no screens.md table defines: {name}"
        for name in sorted(_names_in_code() - set(defined) - spec_names)
    ]
    model = {spec.pointer for spec in FIELDS}
    findings += [
        f"binding pointer is not a FIELDS pointer: {p}" for p in sorted(set(pointers) - model - set(AWAITING_FIELDS))
    ]
    findings += [
        f"FIELDS now holds {p} ({why}): remove it from AWAITING_FIELDS"
        for p, why in AWAITING_FIELDS.items()
        if p in model
    ]
    for topology in TopologyKind:
        for pointer in missing[topology]:
            if (pointer, topology) not in bound:
                findings.append(f"{topology.value}: blank-draft required pointer without a widget: {pointer}")
        for spec in field_specs(topology):
            key = (spec.pointer, topology)
            if spec.required and key not in bound and _reachable(spec.pointer, topology, bound):
                findings.append(f"{topology.value}: required field without a widget: {spec.pointer}")
    table = _coverage_table(bound, missing)
    if "--table" in sys.argv:
        print("\n".join(table))
        return 0
    text = SCREENS.read_text(encoding="utf-8").splitlines()
    start = text.index(TABLE_START) if TABLE_START in text else None
    if start is None or text[start : start + len(table)] != table:
        findings.append("coverage table in screens.md differs from --table output")
    counts = ", ".join(f"{t.value} {len(missing[t])}" for t in TopologyKind)
    print(f"{len(defined)} objectNames, {len(set(pointers))} binding pointers, blank-draft required: {counts}")
    for pointer, why in AWAITING_FIELDS.items():
        print(f"awaiting FIELDS: {pointer} ({why})")
    findings = list(dict.fromkeys(findings))
    print("\n".join(findings) if findings else "no findings")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
