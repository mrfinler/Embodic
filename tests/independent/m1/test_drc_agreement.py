"""U-V1 part 2: embodic ``run_drc`` against Agent 4's brute sweep, fault injection, symmetry and cancellation."""

import math
from collections import Counter

import pytest
from brute_clearance import Verdict, clearance_bracket
from drc_universe import Cls, Item, contract_exemptions, rotate, sweep
from embodic_adapter import pair_violations, to_layout, uniform_rules
from random_boards import random_board
from records import Arc, Line, disc

from embodic.drc import CancelToken, run_drc
from embodic.geometry.layout import RotationalSymmetry

pytestmark = pytest.mark.req("REQ-F-40")

SEEDS = range(200)
BRACKET_SLACK_MM = 1e-12


def _compare(items: tuple[Item, ...], layers: int, rule_mm: float, exempt: set[frozenset[str]]) -> dict[str, object]:
    report = run_drc(to_layout(items, layers), uniform_rules(rule_mm), use_symmetry=False)
    assert report is not None
    engine = pair_violations(report)
    mine = sweep(items, range(layers), lambda kind: rule_mm, exempt)
    found = {frozenset((r.a, r.b)): r for r in mine if r.verdict is Verdict.VIOLATION}
    undecided = {frozenset((r.a, r.b)) for r in mine if r.verdict is Verdict.UNDECIDED}
    return {"engine": engine, "found": found, "undecided": undecided}


def test_run_drc_violation_sets_equal_brute_sweep_on_random_boards() -> None:
    """Catches a missed or invented pair, a wrong kind, a wrong exemption, or a kernel that is not exact."""
    coverage: Counter[str] = Counter()
    for seed in SEEDS:
        board = random_board(seed)
        by_label = {it.label: it.prim for it in board.items}
        got = _compare(board.items, board.layers, board.rule_mm, contract_exemptions(board.items))
        engine, found, undecided = got["engine"], got["found"], got["undecided"]
        assert isinstance(engine, dict) and isinstance(found, dict) and isinstance(undecided, set)
        assert set(engine) - undecided == set(found) - undecided, f"seed {seed}"
        for key, result in found.items():
            kind, measured = engine[key]
            assert kind == result.kind, f"seed {seed} {sorted(key)}"
            tight = clearance_bracket(*(by_label[label] for label in sorted(key)), tol=1e-10)
            assert tight.lo - BRACKET_SLACK_MM <= measured <= tight.hi + BRACKET_SLACK_MM, f"seed {seed} {sorted(key)}"
            coverage[kind] += 1
            labels = sorted(key)
            if kind == "trace_trace" and labels[0].split("/")[0] == labels[1].split("/")[0]:
                coverage["same_path_non_adjacent"] += 1
        coverage[f"layers_{board.layers}"] += 1
        coverage["arcs"] += sum(isinstance(it.prim, Arc) for it in board.items)
    for need in ("trace_trace", "trace_via", "copper_edge", "copper_hole", "pad_trace", "same_path_non_adjacent"):
        assert coverage[need] > 0, f"no {need} violation in {len(SEEDS)} boards: the test lost its power"
    assert all(coverage[f"layers_{n}"] > 0 for n in (1, 2, 3)) and coverage["arcs"] > 0


INTRUSION_CASES = {
    "parallel lines": (Line(0, 0, 10, 0, 0.3), lambda gap: Line(0, gap + 0.3, 10, gap + 0.3, 0.3)),
    "concentric arcs": (Arc(0, 0, 10, 0.1, 1.0, 0.3), lambda gap: Arc(0, 0, 10 + 0.3 + gap, 0.3, 1.0, 0.3)),
    "line and arc": (Arc(0, -10, 10, 1.2, 0.8, 0.3), lambda gap: Line(-3, 0.3 + gap, 3, 0.3 + gap, 0.3)),
    "trace and via": (Line(0, 0, 10, 0, 0.3), lambda gap: disc(5, 0.15 + gap + 0.3, 0.6)),
    "trace and edge": (Line(0, 0, 10, 0, 0.3), lambda gap: Line(-5, 0.15 + gap, 15, 0.15 + gap, 0.0)),
    "trace and hole": (Arc(0, 0, 10, -0.5, 1.0, 0.3), lambda gap: disc(10 + 0.15 + gap + 1.5, 0, 3.0)),
}
_CLASS_OF_CASE = {"trace and via": Cls.VIA, "trace and edge": Cls.EDGE, "trace and hole": Cls.HOLE}
_LABEL = {Cls.TRACE: "path:1/prim:0", Cls.VIA: "via:0", Cls.EDGE: "edge:outer/prim:0", Cls.HOLE: "hole:0"}


@pytest.mark.parametrize("case", sorted(INTRUSION_CASES))
@pytest.mark.parametrize(
    ("intrusion_mm", "violates"),
    [(1.05e-6, True), (0.95e-6, False), (0.0, False), (1e-3, True), (4e-3, True)],
    ids=["eps+5%", "eps-5%", "at-rule", "1um", "4um"],
)
def test_intrusion_is_decided_by_d006(case: str, intrusion_mm: float, violates: bool) -> None:
    """Catches epsilon 0, a larger epsilon, Xcoil's 0.004 mm slack, a sampled arc kernel, or a reversed comparison.

    The second item sits at rule - intrusion. D-006 (epsilon 1e-6 mm = 1 nm) reports it only when the intrusion
    exceeds epsilon, so a 1 um (1e-3 mm) intrusion is always a violation.
    """
    rule = 0.2
    first, make = INTRUSION_CASES[case]
    cls = _CLASS_OF_CASE.get(case, Cls.TRACE)
    second = make(rule - intrusion_mm)
    items = (
        Item("path:0/prim:0", Cls.TRACE, first, 0, "A", 0, 0),
        Item(_LABEL[cls], cls, second, 0 if cls is Cls.TRACE else None, "B", 1 if cls is Cls.TRACE else None,
             0 if cls is Cls.TRACE else None),
    )  # fmt: skip
    report = run_drc(to_layout(items, 1), uniform_rules(rule))
    assert report is not None
    found = pair_violations(report)
    assert (frozenset(it.label for it in items) in found) is violates, found
    if violates:
        ((_, measured),) = found.values()
        assert measured == pytest.approx(rule - intrusion_mm, abs=1e-10)


def _symmetric_board(seed: int, order: int, perturb: bool) -> tuple[tuple[Item, ...], RotationalSymmetry]:
    base = random_board(seed)
    canon = [it for it in base.items if it.cls is Cls.TRACE and it.path in (0, 1)]
    shift = (5.0, 3.0)
    items: list[Item] = []
    path_count = len({it.path for it in canon})
    for k in range(order):
        for it in canon:
            assert it.path is not None
            moved = it.prim
            if isinstance(moved, Line):
                moved = Line(
                    moved.x1 + shift[0], moved.y1 + shift[1], moved.x2 + shift[0], moved.y2 + shift[1], moved.width
                )
            else:
                moved = Arc(moved.cx + shift[0], moved.cy + shift[1], moved.r, moved.start, moved.sweep, moved.width)
            prim = rotate(moved, 2 * math.pi * k / order)
            if perturb and k == order - 1 and it.seq == 0 and isinstance(prim, Line):
                prim = Line(prim.x1, prim.y1, prim.x2 + 0.05, prim.y2, prim.width)
            pid = k * path_count + (it.path or 0)
            items.append(Item(f"path:{pid}/prim:{it.seq}", Cls.TRACE, prim, it.layer, it.net, pid, it.seq))
    extra_id = order * path_count
    items.append(Item(f"path:{extra_id}/prim:0", Cls.TRACE, Line(-1, -1, 1, 1, 0.3), 0, "N", extra_id, 0))
    periodic = tuple(range(order * path_count))
    return tuple(items), RotationalSymmetry(
        order=order, periodic_path_ids=periodic, canonical_path_ids=periodic[:path_count]
    )


@pytest.mark.parametrize("order", [3, 4, 6])
@pytest.mark.parametrize("seed", range(6))
def test_symmetry_shortcut_reports_the_same_violations_as_the_full_check(seed: int, order: int) -> None:
    """Catches a shortcut that drops rotated copies, double counts, or keeps a stale exemption map."""
    items, sym = _symmetric_board(seed, order, perturb=False)
    layers = 1 + max(it.layer or 0 for it in items)
    rules = uniform_rules(0.2)
    fast = run_drc(to_layout(items, layers, sym), rules, use_symmetry=True)
    full = run_drc(to_layout(items, layers, sym), rules, use_symmetry=False)
    assert fast is not None and full is not None
    assert (fast.method, full.method) == ("symmetric+grid+exact", "grid+exact"), "the shortcut did not run"
    a, b = pair_violations(fast), pair_violations(full)
    assert set(a) == set(b)
    assert all(a[k][1] == pytest.approx(b[k][1], abs=1e-9) for k in a)
    mine = sweep(items, range(layers), lambda kind: 0.2, contract_exemptions(items))
    assert set(a) == {frozenset((r.a, r.b)) for r in mine if r.verdict is Verdict.VIOLATION}
    mins = {s.kind: s.measured_min_mm for s in full.summaries}
    for s in fast.summaries:
        if s.measured_min_mm is not None and mins[s.kind] is not None and s.measured_min_mm < 0.2:
            assert s.measured_min_mm == pytest.approx(mins[s.kind], abs=1e-9)


@pytest.mark.parametrize("seed", range(4))
def test_false_symmetry_claim_falls_back_to_the_full_check(seed: int) -> None:
    """Catches a shortcut that trusts the claim: one copy moved 50 um must disable it."""
    items, sym = _symmetric_board(seed, 4, perturb=True)
    report = run_drc(to_layout(items, 3, sym), uniform_rules(0.2), use_symmetry=True)
    assert report is not None and report.method == "grid+exact"


class _CancelAfter(CancelToken):
    """Reports cancelled from the ``after``-th poll on; counts polls."""

    def __init__(self, after: int) -> None:
        super().__init__()
        self.after, self.polls = after, 0

    @property
    def cancelled(self) -> bool:
        self.polls += 1
        return self.polls > self.after or super().cancelled


def test_cancel_token_stops_the_check() -> None:
    """Catches a token that is never read, read only at the start, or a cancelled run that still returns a report."""
    board = random_board(3)
    layout, rules = to_layout(board.items, board.layers), uniform_rules(board.rule_mm)
    pre = CancelToken()
    pre.cancel()
    assert pre.cancelled and run_drc(layout, rules, cancel=pre) is None
    idle = _CancelAfter(10**9)
    assert run_drc(layout, rules, cancel=idle) is not None
    assert idle.polls >= 3, "token read fewer times than there are stages"
    for after in range(1, idle.polls):
        assert run_drc(layout, rules, cancel=_CancelAfter(after)) is None, f"cancel at poll {after} ignored"


def _hairpin() -> tuple[Item, ...]:
    """main0 east, fillet0 (r 0.05) left, main1 north 0.25 mm, fillet1 (r 0.5) left, main2 west; width 0.2.

    fillet1 sits 0.304 mm (centreline) from main0, so its clearance is 0.104 mm. Neither neighbour of fillet1 is main0.
    """
    w, a, length, b = 0.2, 0.05, 0.25, 0.5
    prims = [
        Line(0, 0, 10, 0, w),
        Arc(10, a, a, -math.pi / 2, math.pi / 2, w),
        Line(10 + a, a, 10 + a, a + length, w),
        Arc(10 + a - b, a + length, b, 0.0, math.pi / 2, w),
        Line(10 + a - b, a + length + b, 0, a + length + b, w),
    ]
    return tuple(
        Item(f"path:0/prim:{k}", Cls.TRACE, p, 0, "A", 0, k, corner=isinstance(p, Arc)) for k, p in enumerate(prims)
    )


def test_fillet_is_not_exempt_from_the_main_primitive_two_steps_back() -> None:
    """Rule 1 (D-022b): fillet1 belongs to main1 and main2, not main0, so the 0.104 mm pair must be reported."""
    items = _hairpin()
    report = run_drc(to_layout(items, 1), uniform_rules(0.2))
    assert report is not None
    assert frozenset(("path:0/prim:0", "path:0/prim:3")) in pair_violations(report)
