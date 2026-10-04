"""Comparators, tolerance classes and the D-006 band rule for golden regression (test_plan.md section 3).

Every comparator takes the Xcoil value first (``golden``) and the embodic value second (``actual``) and returns a
``Comparison``. Its verdict is derived from its diffs: an unexplained diff is a mismatch, diffs that are all
allow-listed are ``expected``, and a DRC value inside Xcoil's slack band is ``indeterminate`` for pass/fail.
"""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum

# Phase 1 port notes section 3.1 and engine.js l.757: Xcoil accepts clearances down to rule - 0.004 mm.
XCOIL_DRC_SLACK_MM = 0.004
D006_EPSILON_MM = 1e-6
NEAR_THRESHOLD_REL = 1e-9


@dataclass(frozen=True, slots=True)
class Tolerance:
    """Admits ``|golden - actual| <= max(rel * max(|golden|, |actual|), abs)``; ``abs`` is in the value's unit."""

    name: str
    rel: float
    abs: float

    def admits(self, golden: float, actual: float) -> bool:
        """Return whether two floats agree; NaN matches only NaN and an infinity only the same infinity."""
        if math.isnan(golden) or math.isnan(actual):
            return math.isnan(golden) and math.isnan(actual)
        if math.isinf(golden) or math.isinf(actual):
            return golden == actual
        return abs(golden - actual) <= max(self.rel * max(abs(golden), abs(actual)), self.abs)


EXACT = Tolerance("exact", rel=0.0, abs=0.0)
KERNEL = Tolerance("kernel", rel=1e-12, abs=0.0)
KERNEL_MM = Tolerance("kernel_mm", rel=0.0, abs=1e-12)
INTEGRATED = Tolerance("integrated", rel=1e-9, abs=0.0)
DRC_VALUE = Tolerance("drc_value", rel=0.0, abs=1e-6)


class Verdict(StrEnum):
    """Outcome of one comparison."""

    MATCH = "match"
    EXPECTED = "expected"
    INDETERMINATE = "indeterminate"
    MISMATCH = "mismatch"


class DiffKind(StrEnum):
    """What disagreed. Only ``VALUE`` diffs can be re-admitted by an allow-list tolerance override."""

    VALUE = "value"
    TYPE = "type"
    LENGTH = "length"
    KEYS = "keys"
    DIRECTION = "direction"
    PASS_FAIL = "pass_fail"


@dataclass(frozen=True, slots=True)
class Diff:
    """One disagreement at a JSON-path-like location (``$[3].x1``)."""

    path: str
    kind: DiffKind
    golden: object
    actual: object
    detail: str
    allow_id: str | None = None


@dataclass(frozen=True, slots=True)
class Comparison:
    """Diffs plus indeterminate notes; the verdict is computed, never stored."""

    diffs: tuple[Diff, ...] = ()
    indeterminate: tuple[str, ...] = ()

    @property
    def verdict(self) -> Verdict:
        """Return mismatch if any diff is unexplained, else expected, indeterminate or match."""
        if any(d.allow_id is None for d in self.diffs):
            return Verdict.MISMATCH
        if self.diffs:
            return Verdict.EXPECTED
        return Verdict.INDETERMINATE if self.indeterminate else Verdict.MATCH

    @property
    def ok(self) -> bool:
        """Return whether the comparison passes (everything but a mismatch)."""
        return self.verdict is not Verdict.MISMATCH

    def describe(self) -> str:
        """Return a multi-line report of the verdict, every diff and every indeterminate note."""
        lines = [self.verdict.value]
        for d in self.diffs:
            allowed = f" [allowed by {d.allow_id}]" if d.allow_id else ""
            lines.append(f"  {d.path} {d.kind.value}: golden {d.golden!r}, actual {d.actual!r} ({d.detail}){allowed}")
        lines.extend(f"  indeterminate: {note}" for note in self.indeterminate)
        return "\n".join(lines)


def _is_number(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _is_sequence(value: object) -> bool:
    return isinstance(value, list | tuple)


def _is_container(value: object) -> bool:
    return _is_sequence(value) or isinstance(value, Mapping)


def _scalar_diffs(golden: object, actual: object, tolerance: Tolerance, path: str) -> list[Diff]:
    if _is_number(golden) and _is_number(actual):
        if isinstance(golden, int) and isinstance(actual, int):
            agrees = golden == actual
        else:
            agrees = tolerance.admits(float(golden), float(actual))
        if agrees:
            return []
        delta = abs(float(golden) - float(actual))
        return [Diff(path, DiffKind.VALUE, golden, actual, f"|diff| {delta:.3g} outside {tolerance.name}")]
    if type(golden) is not type(actual):
        detail = f"{type(golden).__name__} vs {type(actual).__name__}"
        return [Diff(path, DiffKind.TYPE, golden, actual, detail)]
    return [] if golden == actual else [Diff(path, DiffKind.VALUE, golden, actual, "not equal")]


def _tree_diffs(golden: object, actual: object, tolerance: Tolerance, path: str) -> list[Diff]:
    if _is_sequence(golden) and _is_sequence(actual):
        if len(golden) != len(actual):
            return [Diff(path, DiffKind.LENGTH, len(golden), len(actual), "different lengths")]
        return [
            d
            for i, (g, a) in enumerate(zip(golden, actual, strict=True))
            for d in _tree_diffs(g, a, tolerance, f"{path}[{i}]")
        ]
    if isinstance(golden, Mapping) and isinstance(actual, Mapping):
        if golden.keys() != actual.keys():
            detail = f"missing {sorted(golden.keys() - actual.keys())}, extra {sorted(actual.keys() - golden.keys())}"
            return [Diff(path, DiffKind.KEYS, sorted(golden), sorted(actual), detail)]
        return [d for k in sorted(golden) for d in _tree_diffs(golden[k], actual[k], tolerance, f"{path}.{k}")]
    if _is_container(golden) or _is_container(actual):
        return [Diff(path, DiffKind.TYPE, golden, actual, f"{type(golden).__name__} vs {type(actual).__name__}")]
    return _scalar_diffs(golden, actual, tolerance, path)


def compare_scalar(golden: object, actual: object, tolerance: Tolerance, *, path: str = "$") -> Comparison:
    """Compare two scalars: numbers by ``tolerance`` (two ints exactly), everything else by type and equality."""
    if _is_container(golden) or _is_container(actual):
        raise TypeError("compare_scalar takes scalars; use compare_sequence for lists and records")
    return Comparison(diffs=tuple(_scalar_diffs(golden, actual, tolerance, path)))


def compare_sequence(
    golden: Sequence[object], actual: Sequence[object], tolerance: Tolerance, *, path: str = "$"
) -> Comparison:
    """Compare two sequences element by element; elements may be scalars, sequences or records (mappings)."""
    if not (_is_sequence(golden) and _is_sequence(actual)):
        raise TypeError("compare_sequence takes two lists or tuples")
    return Comparison(diffs=tuple(_tree_diffs(golden, actual, tolerance, path)))


@dataclass(frozen=True, slots=True)
class GoldenLine:
    """Line in the harness's own shape, whichever producer it came from."""

    x1: float
    y1: float
    x2: float
    y2: float
    width: float


@dataclass(frozen=True, slots=True)
class GoldenArc:
    """Arc with a signed sweep (positive counter-clockwise, y up)."""

    cx: float
    cy: float
    r: float
    start: float
    sweep: float
    width: float

    def point(self, angle: float) -> tuple[float, float]:
        """Return the point of the arc's circle at ``angle``."""
        return (self.cx + self.r * math.cos(angle), self.cy + self.r * math.sin(angle))


def as_prim(value: object) -> GoldenLine | GoldenArc:
    """Read a board-dump primitive record or an object with the interfaces.md section 5 field names."""
    if isinstance(value, Mapping):
        if value.get("type") == "line":
            return GoldenLine(value["x1"], value["y1"], value["x2"], value["y2"], value["width"])
        if value.get("type") == "arc":
            sweep = value["a2"] - value["a1"]
            return GoldenArc(value["cx"], value["cy"], value["r"], value["a1"], sweep, value["width"])
    elif hasattr(value, "x1_mm"):
        return GoldenLine(value.x1_mm, value.y1_mm, value.x2_mm, value.y2_mm, value.width_mm)
    elif hasattr(value, "cx_mm"):
        return GoldenArc(value.cx_mm, value.cy_mm, value.r_mm, value.start_rad, value.sweep_rad, value.width_mm)
    raise TypeError(f"not a line or arc primitive: {value!r}")


def _point_diffs(golden: tuple[float, float], actual: tuple[float, float], tol: Tolerance, path: str) -> list[Diff]:
    return _scalar_diffs(golden[0], actual[0], tol, f"{path}.x") + _scalar_diffs(golden[1], actual[1], tol, f"{path}.y")


def _arc_diffs(golden: GoldenArc, actual: GoldenArc, tol: Tolerance, path: str) -> list[Diff]:
    diffs = _point_diffs((golden.cx, golden.cy), (actual.cx, actual.cy), tol, f"{path}.centre")
    diffs += _scalar_diffs(golden.r, actual.r, tol, f"{path}.r")
    # Endpoints compare the angles modulo 2 pi, so a port may normalise its start angle.
    diffs += _point_diffs(golden.point(golden.start), actual.point(actual.start), tol, f"{path}.start")
    end_g, end_a = golden.point(golden.start + golden.sweep), actual.point(actual.start + actual.sweep)
    diffs += _point_diffs(end_g, end_a, tol, f"{path}.end")
    diffs += _scalar_diffs(abs(golden.sweep), abs(actual.sweep), tol, f"{path}.sweep")
    # A reversed half circle keeps both endpoints and |sweep|; only the sign shows it.
    if golden.sweep != 0 and actual.sweep != 0 and (golden.sweep > 0) != (actual.sweep > 0):
        diffs.append(Diff(f"{path}.direction", DiffKind.DIRECTION, golden.sweep, actual.sweep, "sweep sign differs"))
    return diffs


def compare_prims(
    golden: Sequence[object], actual: Sequence[object], tolerance: Tolerance, *, path: str = "$"
) -> Comparison:
    """Compare primitive chains: type, endpoints, centre, radius, |sweep|, sweep direction and width."""
    gs, acts = [as_prim(g) for g in golden], [as_prim(a) for a in actual]
    if len(gs) != len(acts):
        return Comparison(diffs=(Diff(path, DiffKind.LENGTH, len(gs), len(acts), "different primitive counts"),))
    diffs: list[Diff] = []
    for i, (g, a) in enumerate(zip(gs, acts, strict=True)):
        here = f"{path}[{i}]"
        if type(g) is not type(a):
            diffs.append(Diff(here, DiffKind.TYPE, type(g).__name__, type(a).__name__, "line vs arc"))
            continue
        if isinstance(g, GoldenLine):
            diffs += _point_diffs((g.x1, g.y1), (a.x1, a.y1), tolerance, f"{here}.start")
            diffs += _point_diffs((g.x2, g.y2), (a.x2, a.y2), tolerance, f"{here}.end")
        else:
            diffs += _arc_diffs(g, a, tolerance, here)
        diffs += _scalar_diffs(g.width, a.width, tolerance, f"{here}.width")
    return Comparison(diffs=tuple(diffs))


def d006_pass(value_mm: float, rule_mm: float, epsilon_mm: float = D006_EPSILON_MM) -> bool:
    """Return embodic's DRC verdict: a violation is a clearance below ``rule - epsilon`` (decision D-006)."""
    return not value_mm < rule_mm - epsilon_mm


def compare_drc(
    golden_mm: float,
    actual_mm: float,
    *,
    rule_mm: float,
    golden_pass: bool,
    epsilon_mm: float = D006_EPSILON_MM,
    path: str = "$",
) -> Comparison:
    """Compare one DRC clearance: value within 1e-6 mm, pass/fail agreement outside ``[rule - 0.004, rule)``.

    Inside that band Xcoil passes by its slack while embodic may fail by design, so the case is indeterminate
    for pass/fail agreement (Phase 1 port notes section 3.1).
    """
    diffs = _scalar_diffs(golden_mm, actual_mm, DRC_VALUE, path)
    actual_pass = d006_pass(actual_mm, rule_mm, epsilon_mm)
    if rule_mm - XCOIL_DRC_SLACK_MM <= golden_mm < rule_mm:
        band = f"[{rule_mm} - {XCOIL_DRC_SLACK_MM}, {rule_mm})"
        verdicts = f"Xcoil {'passes' if golden_pass else 'fails'}, embodic {'passes' if actual_pass else 'fails'}"
        note = f"{path}: golden {golden_mm!r} mm in Xcoil's slack band {band}; {verdicts}"
        return Comparison(diffs=tuple(diffs), indeterminate=(note,))
    if actual_pass != golden_pass:
        detail = f"Xcoil pass={golden_pass}, embodic pass={actual_pass} outside the slack band"
        diffs.append(Diff(path, DiffKind.PASS_FAIL, golden_pass, actual_pass, detail))
    return Comparison(diffs=tuple(diffs))


def near_threshold(value: float, threshold: float, rel: float = NEAR_THRESHOLD_REL) -> bool:
    """Return whether a decision on ``value`` against ``threshold`` is within the 1e-9 relative margin.

    A mismatch in such a decision (a ceil count, a branch) is logged as indeterminate, not failed.
    """
    return abs(value - threshold) <= rel * max(abs(value), abs(threshold))


class GoldenReport:
    """Session log for golden tests: fails a mismatch, keeps expected and indeterminate results for the summary."""

    def __init__(self) -> None:
        self._logged: list[tuple[str, Comparison]] = []

    def check(self, case_id: str, comparison: Comparison) -> None:
        """Raise ``AssertionError`` on a mismatch; log an expected or indeterminate comparison."""
        if not comparison.ok:
            raise AssertionError(f"{case_id}: {comparison.describe()}")
        if comparison.verdict is not Verdict.MATCH:
            self._logged.append((case_id, comparison))

    def summary_lines(self) -> list[str]:
        """Return one line per logged comparison, ``<case>: <verdict>`` followed by its details."""
        return [f"{case_id}: {comparison.describe()}" for case_id, comparison in self._logged]
