"""UT-WND-04, -07, -08, -09: the spiral winding plan of a design, its refusals and its warnings (EQ-08)."""

from dataclasses import replace

import pytest
from tests.unit.model.designs import spiral_design

from embodic.errors import IssueCategory, Severity, Unbuildable
from embodic.model.connection import ConnectionSpec
from embodic.model.design import DesignParameters
from embodic.model.layers import LayerConfig, LayerPair
from embodic.model.rotor import RotorSpec
from embodic.model.stackup import generate_even_stackup
from embodic.model.vocabulary import ConnectionTopology, Phase
from embodic.model.winding_specs import CoilAssignmentInput, SpiralWindingSpec
from embodic.results import Registry, load_registry
from embodic.winding import SpiralWindingPlan, plan_issues, plan_spiral_winding

pytestmark = pytest.mark.eq("EQ-08")


@pytest.fixture(scope="module")
def registry() -> Registry:
    """Load the packaged equation registry."""
    return load_registry()


def _design(
    coils: int,
    poles: int,
    *,
    layers: LayerConfig | None = None,
    topology: ConnectionTopology = ConnectionTopology.STAR,
    assignment: tuple[CoilAssignmentInput, ...] | None = None,
    parallel_paths: int = 1,
) -> DesignParameters:
    base = spiral_design()
    assert isinstance(base.winding, SpiralWindingSpec)
    winding = replace(
        base.winding,
        coil=replace(base.winding.coil, coil_count=coils),
        layers=layers or base.winding.layers,
        assignment=assignment,
        parallel_paths=parallel_paths,
    )
    rotor: RotorSpec = replace(base.rotor, poles=poles)
    connection: ConnectionSpec = replace(base.connection, topology=topology)
    stackup = generate_even_stackup(2 * len(winding.layers.pairs), 0.0348, 1.6)
    return replace(base, winding=winding, rotor=rotor, connection=connection, stackup=stackup)


def _plan(design: DesignParameters, registry: Registry) -> SpiralWindingPlan | Unbuildable:
    assert isinstance(design.winding, SpiralWindingSpec)
    return plan_spiral_winding(design, design.winding, registry)


def _codes(result: SpiralWindingPlan | Unbuildable) -> list[str]:
    assert isinstance(result, Unbuildable)
    return [i.code for i in result.issues]


def _one_phase_per_pair() -> LayerConfig:
    pairs = tuple(
        LayerPair(index=i, layer_in=f"L{2 * i + 1}", layer_out=f"L{2 * i + 2}", phases=(phase,))
        for i, phase in enumerate(Phase)
    )
    return LayerConfig(pairs=pairs, series_groups=((0,), (1,), (2,)))


@pytest.mark.req("REQ-F-02")
def test_default_example_plan(registry: Registry) -> None:
    """The 12/16 example plans to ACB x 4 with k_w1 = sin 120° for the outermost-turn span (CF-11, registry EQ-08)."""
    plan = _plan(_design(12, 16), registry)
    assert isinstance(plan, SpiralWindingPlan)
    assert plan.pattern == "ACBACBACBACB"
    assert plan.feasibility.balanced
    assert sorted(plan.winding_factors) == [1, 3, 5, 7]
    assert plan.winding_factors[1].value == pytest.approx(0.8660254, abs=5e-8)
    assert plan.winding_factors[1].eq_ids == ("EQ-08",)


@pytest.mark.req("REQ-F-02")
def test_ut_wnd_04_16_16_with_all_phases_on_every_pair_is_unbuildable(registry: Registry) -> None:
    """Catches a 16/16 FSCW winding slipping through: Q = 2p puts every phasor at 0° or 180°."""
    result = _plan(_design(16, 16), registry)
    assert _codes(result) == ["UNBUILDABLE_ASYMMETRIC_WINDING"]
    assert isinstance(result, Unbuildable)
    assert result.issues[0].category is IssueCategory.UNBUILDABLE
    assert result.issues[0].message == "No symmetric 3-phase pattern exists for this coil count and pole count."


@pytest.mark.req("REQ-F-02", "REQ-F-03")
def test_ut_wnd_04_16_16_with_one_phase_per_pair_is_accepted(registry: Registry) -> None:
    """Option M4: each pair carries one phase of 16 alternating full-pitch coils; k_d1 = 1, k_p1 = 1."""
    plan = _plan(_design(16, 16, layers=_one_phase_per_pair()), registry)
    assert isinstance(plan, SpiralWindingPlan)
    assert plan.feasibility.balanced
    assert plan.pattern == "Aa" * 8
    assert plan.winding_factors[1].value == pytest.approx(1.0, abs=1e-12)


@pytest.mark.req("REQ-F-08")
def test_ut_wnd_07_delta_with_triplen_winding_factor_warns(registry: Registry) -> None:
    """Catches a missing delta warning: 12/14 has k_w3 = 0.5, so delta raises RANGE_DELTA_TRIPLEN with that value."""
    design = _design(12, 14, topology=ConnectionTopology.DELTA)
    plan = _plan(design, registry)
    assert isinstance(plan, SpiralWindingPlan)
    issues = plan_issues(plan, design)
    assert [i.code for i in issues] == ["RANGE_DELTA_TRIPLEN"]
    assert issues[0].severity is Severity.WARNING
    assert issues[0].value == pytest.approx(0.5, abs=1e-9)


@pytest.mark.req("REQ-F-08")
@pytest.mark.parametrize(
    ("coils", "poles", "topology"),
    [(12, 16, ConnectionTopology.DELTA), (12, 14, ConnectionTopology.STAR)],
    ids=["12-16-delta", "12-14-star"],
)
def test_ut_wnd_07_no_triplen_warning(coils: int, poles: int, topology: ConnectionTopology, registry: Registry) -> None:
    """Catches a false alarm: 12/16 has k_w3 = 0 (A2-TOP §3.4), and star never circulates a triplen current."""
    design = _design(coils, poles, topology=topology)
    plan = _plan(design, registry)
    assert isinstance(plan, SpiralWindingPlan)
    assert plan_issues(plan, design) == ()


@pytest.mark.req("REQ-F-02")
@pytest.mark.parametrize(
    ("coils", "poles", "paths", "periodicity", "buildable"),
    [
        (12, 16, 1, 4, True),
        (12, 16, 2, 4, True),
        (12, 16, 4, 4, True),
        (12, 16, 3, 4, False),
        (12, 16, 5, 4, False),
        (9, 6, 1, 3, True),
        (9, 6, 3, 3, True),
        (9, 6, 2, 3, False),
    ],
)
def test_ut_wnd_08_parallel_paths_must_divide_the_periodicity(
    coils: int, poles: int, paths: int, periodicity: int, buildable: bool, registry: Registry
) -> None:
    """D-032a, D-033d. Catches `a <= t`: Q = 9, 2p = 6 has t = 3 and a = 2 passes that rule, but 3 mod 2 = 1.

    The expected verdicts are the divisors of t written out by hand. A refusal carries the requested paths and t.
    """
    result = _plan(_design(coils, poles, parallel_paths=paths), registry)
    if buildable:
        assert isinstance(result, SpiralWindingPlan)
        return
    assert _codes(result) == ["UNBUILDABLE_PARALLEL_PATHS_NOT_DIVISOR"]
    assert isinstance(result, Unbuildable)
    assert (result.issues[0].value, result.issues[0].limit) == (paths, periodicity)
    assert result.issues[0].pointers == ("/winding/parallel_paths",)


@pytest.mark.req("REQ-F-02")
def test_ut_wnd_09_unbalanced_manual_assignment_is_accepted_with_a_warning(registry: Registry) -> None:
    """Catches a manual override that is refused or silently trusted: it builds, flags imbalance and shows a metric."""
    manual = tuple(
        CoilAssignmentInput(coil_index=k, phase=(Phase.A, Phase.A, Phase.B, Phase.C)[k % 4], polarity=1)
        for k in range(12)
    )
    design = _design(12, 16, assignment=manual)
    plan = _plan(design, registry)
    assert isinstance(plan, SpiralWindingPlan)
    assert plan.pattern == "AABC" * 3
    assert not plan.feasibility.balanced
    issues = plan_issues(plan, design)
    assert [i.code for i in issues] == ["RANGE_MANUAL_ASSIGNMENT_ASYMMETRIC"]
    assert issues[0].message == (
        "The manual phase assignment is not a symmetric 3-phase pattern; the value is the relative spread of the three "
        "phase phasor sums, each coil counted as a unit phasor."
    )
    assert isinstance(issues[0].value, float)
    assert 0.0 < issues[0].value <= 1.0


@pytest.mark.req("REQ-F-02")
def test_ut_wnd_09_balanced_manual_assignment_has_no_warning(registry: Registry) -> None:
    """A manual copy of the star-of-slots result is balanced and draws no warning."""
    manual = tuple(CoilAssignmentInput(coil_index=k, phase=Phase("ACB"[k % 3]), polarity=1) for k in range(12))
    design = _design(12, 16, assignment=manual)
    plan = _plan(design, registry)
    assert isinstance(plan, SpiralWindingPlan)
    assert plan.feasibility.balanced
    assert plan_issues(plan, design) == ()


@pytest.mark.req("REQ-F-02")
def test_manual_assignment_must_cover_every_coil_once(registry: Registry) -> None:
    """Catches a plan built from a partial manual list: a missing coil index is refused."""
    manual = tuple(CoilAssignmentInput(coil_index=k, phase=Phase("ACB"[k % 3]), polarity=1) for k in range(11))
    assert _codes(_plan(_design(12, 16, assignment=manual), registry)) == ["UNBUILDABLE_ASSIGNMENT_COVERAGE"]
