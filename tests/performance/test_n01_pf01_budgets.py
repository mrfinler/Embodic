"""REQ-N-01 (V3-01 gap N-01): PF-01 holds the whole-recompute and per-stage p95 budgets on the reference laptop.

Budgets from requirements.md REQ-N-01: full recompute p95 under 1.0 s, geometry under 0.2 s, DRC under 0.4 s, physics
under 0.3 s, all strict. They are `assumption` budgets for the user's laptop, so the measuring test is marked `manual`
(no CI profile runs it) and skips unless a person selects it with `-m manual`. The verdict function is tested on
synthetic numbers in every run. `test_pf_baseline.py` keeps recording the same numbers and asserts only `p95 > 0`.
"""

from pathlib import Path

import pytest
from tests.performance.test_pf_baseline import timed_runs

pytestmark = pytest.mark.req("REQ-N-01")

EXAMPLE = Path(__file__).resolve().parents[2] / "resources" / "examples" / "spiral_12c16p_default.embodic.json"
RECOMPUTE_P95_BELOW_S = 1.0
STAGE_P95_BELOW_S = {"geometry": 0.2, "drc": 0.4, "physics": 0.3}


def budget_findings(case: dict) -> list[str]:
    """Return a message per p95 that does not stay strictly below its budget, for a `timed_runs` result."""
    findings = []
    wall = case["wall_s"]["p95"]
    if not wall < RECOMPUTE_P95_BELOW_S:
        findings.append(f"full recompute p95 {wall:.3f} s is not below {RECOMPUTE_P95_BELOW_S} s")
    for stage, budget in STAGE_P95_BELOW_S.items():
        p95 = case["stage_s"][stage]["p95"]
        if not p95 < budget:
            findings.append(f"{stage} p95 {p95:.3f} s is not below {budget} s")
    return findings


def synthetic(wall: float, geometry: float, drc: float, physics: float) -> dict:
    """Return a `timed_runs`-shaped result with the given p95 values."""
    stage = {"geometry": geometry, "drc": drc, "physics": physics}
    return {"wall_s": {"p95": wall}, "stage_s": {name: {"p95": value} for name, value in stage.items()}}


def test_n01_a_case_inside_every_budget_has_no_finding():
    """Catches a verdict that reports a healthy run."""
    assert budget_findings(synthetic(0.99, 0.19, 0.39, 0.29)) == []


@pytest.mark.parametrize(
    ("case", "expected"),
    [
        (synthetic(1.0, 0.1, 0.1, 0.1), "full recompute p95 1.000 s is not below 1.0 s"),
        (synthetic(0.5, 0.2, 0.1, 0.1), "geometry p95 0.200 s is not below 0.2 s"),
        (synthetic(0.5, 0.1, 0.4, 0.1), "drc p95 0.400 s is not below 0.4 s"),
        (synthetic(0.5, 0.1, 0.1, 0.3), "physics p95 0.300 s is not below 0.3 s"),
    ],
    ids=["recompute", "geometry", "drc", "physics"],
)
def test_n01_a_p95_equal_to_its_bound_is_a_finding(case, expected):
    """Catches a verdict with a non-strict bound, or one that checks the total and skips a stage."""
    assert budget_findings(case) == [expected]


@pytest.mark.manual
def test_n01_pf01_default_design_meets_the_budgets_on_the_reference_laptop(request):
    """Catches a regression that PF-01's `p95 > 0` assertion cannot fail on. Run `pytest -m manual` on the laptop."""
    if "manual" not in (request.config.getoption("markexpr") or "").replace("not manual", ""):
        pytest.skip("manual: select with -m manual on the user's laptop; the budgets are assumptions for that machine")
    assert budget_findings(timed_runs(EXAMPLE, 20)) == []
