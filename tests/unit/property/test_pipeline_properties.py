"""PR-03, PR-05 to PR-09, PR-11 and PR-12 on random spiral designs through the compute facade."""

import dataclasses
import json
import math
from collections.abc import Iterator
from typing import Any

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from embodic.api import ComputeOptions, StageCache, compute, outcome_to_json
from embodic.errors import Severity, Unbuildable
from embodic.generators import build_layout
from embodic.geometry.paths import is_continuous
from embodic.geometry.primitives import Arc
from embodic.io.canonical import design_hash
from embodic.model.design import DesignParameters
from embodic.model.draft import DraftIncomplete, parse_draft
from embodic.model.provenance import ExampleRef, UserValue, derive_provenance
from embodic.model.winding_specs import SpiralWindingSpec
from embodic.outcome import ComputeOutcome
from embodic.results import load_registry
from embodic.winding import SpiralWindingPlan, plan_spiral_winding

from .strategies import COMPUTE_EXAMPLES, cf11, mutated_drafts, spiral_designs

REGISTRY = load_registry()
NO_DRC = ComputeOptions(run_drc=False)
REL = 1e-9


def _outcome(design: DesignParameters, options: ComputeOptions = NO_DRC) -> ComputeOutcome:
    outcome = compute(design, derive_provenance(design, None, ()), options=options, registry=REGISTRY)
    assert outcome is not None
    return outcome


def _nonfinite_tags(data: Any) -> Iterator[Any]:
    if isinstance(data, dict):
        if set(data) == {"$f"}:
            yield data
        for value in data.values():
            yield from _nonfinite_tags(value)
    elif isinstance(data, list):
        for value in data:
            yield from _nonfinite_tags(value)


def _statuses(data: Any, path: str = "") -> Iterator[tuple[str, str]]:
    if isinstance(data, dict):
        if "status" in data and "value" in data:
            yield path, data["status"]
        for key, value in data.items():
            yield from _statuses(value, f"{path}/{key}")
    elif isinstance(data, list):
        for index, value in enumerate(data):
            yield from _statuses(value, f"{path}/{index}")


@pytest.mark.req("REQ-F-01")
@settings(max_examples=max(20, COMPUTE_EXAMPLES))
@given(design=spiral_designs())
def test_pr_03_every_built_path_is_continuous(design: DesignParameters) -> None:
    """PR-03 (positional part). Catches a joint gap above 1e-6 mm on any board path of any buildable design."""
    built = build_layout(design, REGISTRY)
    if isinstance(built, Unbuildable):
        return
    for board in built.boards:
        gaps = [path.id for path in board.paths if not is_continuous(path.primitives)]
        assert gaps == []


@pytest.mark.req("REQ-F-14")
@settings(max_examples=max(20, COMPUTE_EXAMPLES * 4))
@given(draft=mutated_drafts())
def test_pr_05_arbitrary_values_never_raise_or_return_non_finite(draft: Any) -> None:
    """PR-05. Catches an uncaught exception, a silent invalid input or a NaN/infinity in any result."""
    parsed = parse_draft(draft)
    if isinstance(parsed, DraftIncomplete):
        assert parsed.missing or parsed.issues
        return
    outcome = compute(parsed, derive_provenance(parsed, None, ()), registry=REGISTRY)
    assert outcome is not None
    assert [i.code for i in outcome.issues if i.code.startswith("INTERNAL_")] == []
    if any(i.severity is Severity.ERROR for i in outcome.issues):
        assert not outcome.ok
    assert list(_nonfinite_tags(outcome_to_json(outcome))) == []


def _with_br(design: DesignParameters, remanence_t: float) -> DesignParameters:
    return dataclasses.replace(design, rotor=dataclasses.replace(design.rotor, remanence_t=remanence_t))


def _with_operating(design: DesignParameters, **changes: float) -> DesignParameters:
    return dataclasses.replace(design, operating=dataclasses.replace(design.operating, **changes))


@pytest.mark.req("REQ-F-02", "REQ-F-11")
@settings(max_examples=COMPUTE_EXAMPLES)
@given(design=spiral_designs(), scale=st.floats(0.5, 2.0))
def test_pr_06_ke_linear_in_br_and_independent_of_speed_eddy_quadratic(design: DesignParameters, scale: float) -> None:
    """PR-06 (Ke, speed and eddy laws). Catches a non-linear Ke(B_r), Ke(speed) or an eddy law other than f^2."""
    base = _outcome(design)
    if base.analysis is None:
        return
    ke = base.analysis.ke_line_peak_v_s_per_rad.value
    stronger = _outcome(_with_br(design, design.rotor.remanence_t * scale)).analysis
    faster = _outcome(_with_operating(design, speed_rpm=design.operating.speed_rpm * scale)).analysis
    assume(stronger is not None and faster is not None)  # scaling may cross a supported range (RANGE_ issue)
    assert stronger is not None and faster is not None
    assert stronger.ke_line_peak_v_s_per_rad.value == pytest.approx(ke * scale, rel=REL)
    assert faster.ke_line_peak_v_s_per_rad.value == pytest.approx(ke, rel=REL)
    eddy = base.analysis.loss_eddy_w.value
    assert faster.loss_eddy_w.value == pytest.approx(eddy * scale * scale, rel=REL)


@pytest.mark.req("REQ-F-11")
@settings(max_examples=COMPUTE_EXAMPLES)
@given(design=spiral_designs(), temperatures=st.tuples(st.floats(0.0, 60.0), st.floats(70.0, 150.0)))
def test_pr_06_resistance_is_linear_in_temperature(design: DesignParameters, temperatures: tuple[float, float]) -> None:
    """PR-06 (EQ-10). Catches a resistance that is not linear in winding temperature."""
    t1, t3 = temperatures
    t2 = (t1 + t3) / 2
    values = []
    for t in (t1, t2, t3):
        analysis = _outcome(_with_operating(design, winding_temperature_degc=t)).analysis
        if analysis is None:
            return
        values.append(analysis.resistance_phase_operating_ohm.value)
    r1, r2, r3 = values
    assert r2 - r1 == pytest.approx(r3 - r2, rel=1e-6)


def _balanced(design: DesignParameters) -> bool:
    assert isinstance(design.winding, SpiralWindingSpec)
    plan = plan_spiral_winding(design, design.winding, REGISTRY)
    return isinstance(plan, SpiralWindingPlan) and plan.feasibility.balanced


@pytest.mark.req("REQ-F-02")
@settings(max_examples=COMPUTE_EXAMPLES)
@given(design=spiral_designs().filter(_balanced))
def test_pr_07_balanced_designs_have_equal_phase_ke(design: DesignParameters) -> None:
    """PR-07 (magnitude part). Catches unequal |Ke| between phases of a balanced coil and pole combination."""
    analysis = _outcome(design).analysis
    if analysis is None:
        return
    magnitudes = [abs(p.ke_peak_v_s_per_rad.value) for p in analysis.phases]
    assert len(magnitudes) == 3
    assert max(magnitudes) == pytest.approx(min(magnitudes), rel=REL)


@pytest.mark.req("REQ-F-15")
@given(a=spiral_designs(), b=spiral_designs())
def test_pr_08_hash_changes_iff_the_design_changes(a: DesignParameters, b: DesignParameters) -> None:
    """PR-08. Catches a hash that ignores a field or depends on something other than the design."""
    assert (design_hash(a) == design_hash(b)) == (a == b)
    assert design_hash(dataclasses.replace(a)) == design_hash(a)


@pytest.mark.req("REQ-N-04")
@settings(max_examples=COMPUTE_EXAMPLES)
@given(design=spiral_designs())
def test_pr_09_results_json_is_byte_identical_across_runs(design: DesignParameters) -> None:
    """PR-09. Catches non-determinism in any stage: two fresh computes give the same results JSON text."""
    provenance = derive_provenance(design, None, ())
    texts = []
    for _ in range(2):
        outcome = compute(design, provenance, cache=StageCache(), registry=REGISTRY)
        assert outcome is not None
        texts.append(json.dumps(outcome_to_json(outcome), sort_keys=True))
    assert texts[0] == texts[1]


@pytest.mark.req("REQ-F-09", "REQ-F-10")
@settings(max_examples=max(20, COMPUTE_EXAMPLES))
@given(design=spiral_designs())
def test_pr_11_copper_stays_inside_the_envelope(design: DesignParameters) -> None:
    """PR-11 (envelope part). Catches copper drawn outside the radial envelope the layout declares."""
    built = build_layout(design, REGISTRY)
    if isinstance(built, Unbuildable):
        return
    for board in built.boards:
        r_min, r_max = board.envelope_mm
        for path in board.paths:
            for p in path.primitives:
                points = [p.start_point(), p.end_point()] + ([p.mid_point()] if isinstance(p, Arc) else [])
                for x, y in points:
                    assert r_min - 1e-9 <= math.hypot(x, y) <= r_max + 1e-9


@pytest.mark.req("REQ-T-03", "REQ-F-21")
@settings(max_examples=COMPUTE_EXAMPLES)
@given(design=spiral_designs())
def test_pr_12_badges_do_not_depend_on_provenance_and_reentry_changes_nothing(design: DesignParameters) -> None:
    """PR-12 (re-entry and badge parts). Catches a badge that reads provenance, or a re-entry that changes state."""
    ref = ExampleRef(example_id="spiral_12c16p_default", example_sha256=design_hash(cf11()))
    as_example = derive_provenance(design, (ref, cf11()), ())
    as_user = {pointer: UserValue() for pointer in as_example}
    reentered = dataclasses.replace(design, rotor=dataclasses.replace(design.rotor, poles=design.rotor.poles))
    assert design_hash(reentered) == design_hash(design)
    assert derive_provenance(reentered, (ref, cf11()), ()) == as_example
    first = compute(design, as_example, options=NO_DRC, registry=REGISTRY)
    second = compute(reentered, as_user, options=NO_DRC, registry=REGISTRY)
    assert first is not None and second is not None
    if first.analysis is None or second.analysis is None:
        return
    assert dict(_statuses(first.analysis.to_json())) == dict(_statuses(second.analysis.to_json()))
