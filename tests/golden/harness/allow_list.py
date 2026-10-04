"""Reader for ``tests/golden/expected_diffs/<area>.toml`` and its application to comparisons.

Each ``[[diff]]`` entry names an intentional deviation from Xcoil with its owning EQ-ID, a reason and the Agent 2
and Agent 4 sign-offs (test_plan.md section 3). An entry turns matching diffs into ``expected``; with a
``tolerance`` override it admits only numeric value diffs inside that bound.
"""

import math
import re
import tomllib
from collections.abc import Iterable
from dataclasses import dataclass, replace
from pathlib import Path

from .compare import Comparison, Diff, DiffKind, Tolerance

EXPECTED_DIFFS_DIR = Path(__file__).resolve().parents[1] / "expected_diffs"

_REQUIRED = ("id", "case", "eq_id", "reason", "agent2_signoff", "agent4_signoff")
_OPTIONAL = ("path", "tolerance")
_EQ_ID = re.compile(r"EQ-\d{2}")


class AllowListError(ValueError):
    """An allow-list file or entry outside the schema."""


@dataclass(frozen=True, slots=True)
class AllowEntry:
    """One intentional deviation. ``case`` and ``path`` are patterns where ``*`` matches any run of characters."""

    id: str
    case: str
    path: str
    eq_id: str
    reason: str
    tolerance: Tolerance | None
    agent2_signoff: str
    agent4_signoff: str


def _matches(pattern: str, text: str) -> bool:
    # Diff paths contain "[" and "]", which fnmatch would read as character classes.
    return re.fullmatch(".*".join(re.escape(part) for part in pattern.split("*")), text) is not None


def _parse_tolerance(raw: object, where: str) -> Tolerance:
    if not isinstance(raw, dict) or set(raw) != {"rel", "abs"}:
        raise AllowListError(f"{where}: tolerance must be a table with exactly rel and abs")
    for key in ("rel", "abs"):
        value = raw[key]
        if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value) or value < 0:
            raise AllowListError(f"{where}: tolerance {key} must be a finite number >= 0")
    return Tolerance(f"{where} override", rel=float(raw["rel"]), abs=float(raw["abs"]))


def _parse_entry(raw: dict[str, object], where: str) -> AllowEntry:
    for key in raw:
        if key not in _REQUIRED + _OPTIONAL:
            raise AllowListError(f"{where}: unknown key {key}")
    missing = [key for key in _REQUIRED if key not in raw]
    if missing:
        raise AllowListError(f"{where}: missing {', '.join(missing)}")
    for key in (*_REQUIRED, "path"):
        if key in raw and (not isinstance(raw[key], str) or not raw[key].strip()):
            raise AllowListError(f"{where}: {key} must be a non-empty string")
    if not _EQ_ID.fullmatch(raw["eq_id"]):
        raise AllowListError(f"{where}: eq_id {raw['eq_id']!r} is not of the form EQ-nn")
    return AllowEntry(
        id=raw["id"],
        case=raw["case"],
        path=raw.get("path", "*"),
        eq_id=raw["eq_id"],
        reason=raw["reason"],
        tolerance=_parse_tolerance(raw["tolerance"], where) if "tolerance" in raw else None,
        agent2_signoff=raw["agent2_signoff"],
        agent4_signoff=raw["agent4_signoff"],
    )


def load_allow_list(path: Path) -> tuple[AllowEntry, ...]:
    """Parse and validate one allow-list file; raise ``AllowListError`` naming the file and entry on any defect."""
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    if data.get("schema_version") != 1:
        raise AllowListError(f"{path}: schema_version must be 1")
    if set(data) - {"schema_version", "diff"}:
        raise AllowListError(f"{path}: unknown top-level keys {sorted(set(data) - {'schema_version', 'diff'})}")
    entries = tuple(_parse_entry(raw, f"{path} diff[{i}]") for i, raw in enumerate(data.get("diff", [])))
    seen: set[str] = set()
    for entry in entries:
        if entry.id in seen:
            raise AllowListError(f"{path}: duplicate id {entry.id}")
        seen.add(entry.id)
    return entries


def _admits(entry: AllowEntry, diff: Diff) -> bool:
    if not _matches(entry.path, diff.path):
        return False
    if entry.tolerance is None:
        return True
    numeric = all(isinstance(v, int | float) and not isinstance(v, bool) for v in (diff.golden, diff.actual))
    return diff.kind is DiffKind.VALUE and numeric and entry.tolerance.admits(float(diff.golden), float(diff.actual))


def apply_allow_list(comparison: Comparison, case_id: str, entries: Iterable[AllowEntry]) -> Comparison:
    """Mark every diff that an entry for ``case_id`` admits with that entry's id; other diffs stay unexplained."""
    relevant = [e for e in entries if _matches(e.case, case_id)]

    def allow(diff: Diff) -> Diff:
        if diff.allow_id is not None:
            return diff
        entry = next((e for e in relevant if _admits(e, diff)), None)
        return diff if entry is None else replace(diff, allow_id=entry.id)

    return replace(comparison, diffs=tuple(allow(d) for d in comparison.diffs))
