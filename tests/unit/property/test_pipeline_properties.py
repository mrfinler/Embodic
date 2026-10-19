"""PR-03, PR-05 to PR-12 on random spiral designs."""

import cmath
import dataclasses
import json
import math
from collections.abc import Iterator
from typing import Any

import numpy as np
import pytest
from hypothesis import assume, example, given, settings
from hypothesis import strategies as st

from embodic.api import ComputeOptions, StageCache, compute, outcome_to_json
from embodic.drc import DrcCheckKind, run_drc
from embodic.errors import Severity, Unbuildable
from embodic.generators import build_layout
from embodic.geometry.layout import Layout
from embodic.geometry.paths import is_continuous
from embodic.geometry.primitives import Arc, Line, Primitive, PrimitiveRole, primitive_length_mm
from embodic.geometry.transforms import mirror, reverse_path
from embodic.io.canonical import design_hash
from embodic.model.design import DesignParameters
from embodic.model.draft import DraftIncomplete, parse_draft
from embodic.model.provenance import ExampleRef, UserValue, derive_provenance
from embodic.model.stackup import CopperLayer, DielectricLayer, Stackup
from embodic.model.winding_specs import SpiralWindingSpec
from embodic.outcome import ComputeOutcome
from embodic.results import load_registry
from embodic.results.status import Status
from embodic.results.traceable import Traceable
from embodic.winding import SpiralWindingPlan, plan_spiral_winding

from .strategies import COMPUTE_EXAMPLES, cf11, cf11_draft_with, mutated_drafts, spiral_designs

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
# DEF-M2f-03: physics chords of 0.001 mm and a 64 mm DRC rule each ran for minutes before the supported ranges.
@example(draft=cf11_draft_with({"/analysis/max_segment_mm": 0.001}))
@example(draft=cf11_draft_with({"/drc_rules/trace_clearance_mm": 64}))
# DEF-M2f-02 and the U-M2-fix3 leaf scan: each raised inside physics or DRC.
@example(draft=cf11_draft_with({"/rotor/magnet/length_mm": 1.5e-164}))
@example(draft=cf11_draft_with({"/operating/winding_temperature_degc": 3}))
@example(draft=cf11_draft_with({"/vias/plating_um": 5e-324}))
@example(draft=cf11_draft_with({"/outline/bore/radius_mm": 1e300}))
# Release run on 10c6411 (nightly profile): an empty harmonic list reached physics and raised IndexError.
@example(draft=cf11_draft_with({"/analysis/harmonics": []}))
# DEF-UV15-04 (V3-07 seed 5): 3.137566414384587e306 rad is finite, its degrees are inf, and design_hash raised.
@example(
    draft=cf11_draft_with(
        {
            "/outline/board/shape": "polygon",
            "/outline/board/sides": 12,
            "/outline/board/across_flats_mm": 93.0,
            "/outline/board/corner_radius_mm": 0.0,
            "/outline/board/rotation_rad": 3.137566414384587e306,
        }
    )
)
def test_pr_05_arbitrary_values_never_raise_and_invalid_values_return_issues(draft: Any) -> None:
    """PR-05 (exception part). Catches an uncaught exception or an invalid input that returns no issue."""
    parsed = parse_draft(draft)
    if isinstance(parsed, DraftIncomplete):
        assert parsed.missing or parsed.issues
        return
    outcome = compute(parsed, derive_provenance(parsed, None, ()), registry=REGISTRY)
    assert outcome is not None
    assert [i.code for i in outcome.issues if i.code.startswith("INTERNAL_")] == []
    if any(i.severity is Severity.ERROR for i in outcome.issues):
        assert not outcome.ok


@pytest.mark.req("REQ-F-14")
def test_pr_05_magnet_outside_the_winding_is_refused_not_infinite() -> None:
    """PR-05 (finite part, DEF-M2f-01). Catches kv and THD of +inf from CF-11 with its block magnet at r 5 mm."""
    design = cf11()
    magnet = dataclasses.replace(design.rotor.magnet, r_center_mm=5.0)
    outcome = _outcome(dataclasses.replace(design, rotor=dataclasses.replace(design.rotor, magnet=magnet)))
    assert "INVALID_MAGNET_CROSSES_AXIS" in [i.code for i in outcome.issues]
    assert list(_nonfinite_tags(outcome_to_json(outcome))) == []


def _traceables(value: object) -> Iterator[Traceable[object]]:
    if isinstance(value, Traceable):
        yield value
    elif dataclasses.is_dataclass(value) and not isinstance(value, type):
        for f in dataclasses.fields(value):
            yield from _traceables(getattr(value, f.name))
    elif isinstance(value, tuple):
        for item in value:
            yield from _traceables(item)


def _is_finite(value: object) -> bool:
    numbers = value if isinstance(value, tuple) else (value,)
    return all(math.isfinite(n) for n in numbers if isinstance(n, float))


@pytest.mark.req("REQ-F-14")
def test_pr_05_a_non_finite_result_is_unresolved_and_named_by_an_issue() -> None:
    """PR-05 (finite part). Catches a non-finite result without an issue or with a badge stronger than unresolved.

    CF-11 at 0 rpm is a valid input whose skin depth at 0 Hz is infinite.
    """
    outcome = _outcome(_with_operating(cf11(), speed_rpm=0.0))
    assert outcome.analysis is not None
    non_finite = [t for t in _traceables(outcome.analysis) if not _is_finite(t.value)]
    flagged = [i.value for i in outcome.issues if i.code == "RANGE_NON_FINITE_RESULT"]
    assert sorted(t.quantity for t in non_finite) == sorted(flagged)
    assert "skin_depth" in flagged
    assert {t.status for t in non_finite} == {Status.UNRESOLVED}


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


def _wrapped_rad(angle_rad: float) -> float:
    """Return ``angle_rad`` folded into (-pi, pi]."""
    return math.pi - (math.pi - angle_rad) % math.tau


@pytest.mark.req("REQ-F-02")
@settings(max_examples=COMPUTE_EXAMPLES)
@given(design=spiral_designs().filter(_balanced))
def test_pr_07_balanced_designs_have_phase_emf_phasors_120_degrees_apart(design: DesignParameters) -> None:
    """PR-07 (spacing part). Catches a phase whose EMF phasor is shifted off 120 electrical degrees from the next.

    Each step A to B, B to C and C to A turns the same way by 2 pi / 3, within 1e-9 rad; the turn direction follows
    the slot and pole combination, so it may be either sign.
    """
    analysis = _outcome(design).analysis
    if analysis is None:
        return
    angles = [p.emf_phasor_angle_rad.value for p in analysis.phases]
    assert len(angles) == 3
    steps = [_wrapped_rad(angles[(k + 1) % 3] - angles[k]) for k in range(3)]
    assert steps == pytest.approx([steps[0]] * 3, abs=1e-9)
    assert abs(steps[0]) == pytest.approx(2.0 * math.pi / 3.0, abs=1e-9)


def _cf11_with_first_coil_angle(angle_rad: float) -> DesignParameters:
    design = cf11()
    assert isinstance(design.winding, SpiralWindingSpec)
    coil = dataclasses.replace(design.winding.coil, first_coil_angle_rad=angle_rad)
    return dataclasses.replace(design, winding=dataclasses.replace(design.winding, coil=coil))


@pytest.mark.req("REQ-F-15")
@given(a=spiral_designs(), b=spiral_designs())
# Release run of 0.0.2 on Windows: 0.0 == -0.0 in Python, but the canonical JSON wrote "-0.0" and the hashes differed.
@example(a=_cf11_with_first_coil_angle(0.0), b=_cf11_with_first_coil_angle(-0.0))
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


SAMPLE_STEP_MM = 0.2


def _distance_to_outline_mm(point: tuple[float, float], outline_prim: Primitive) -> float:
    """Return the distance from ``point`` to one outline line or arc, by plain geometry (independent of the DRC)."""
    x, y = point
    if isinstance(outline_prim, Line):
        ax, ay, bx, by = outline_prim.x1_mm, outline_prim.y1_mm, outline_prim.x2_mm, outline_prim.y2_mm
        t = ((x - ax) * (bx - ax) + (y - ay) * (by - ay)) / ((bx - ax) ** 2 + (by - ay) ** 2)
        t = min(1.0, max(0.0, t))
        return math.hypot(x - (ax + t * (bx - ax)), y - (ay + t * (by - ay)))
    angle = math.atan2(y - outline_prim.cy_mm, x - outline_prim.cx_mm)
    turned = (angle - outline_prim.start_rad) * math.copysign(1.0, outline_prim.sweep_rad) % math.tau
    if turned <= abs(outline_prim.sweep_rad):
        return abs(math.hypot(x - outline_prim.cx_mm, y - outline_prim.cy_mm) - outline_prim.r_mm)
    return min(math.hypot(x - qx, y - qy) for qx, qy in (outline_prim.start_point(), outline_prim.end_point()))


def _centreline_points(p: Primitive) -> Iterator[tuple[float, float]]:
    """Yield points along a copper primitive, at most ``SAMPLE_STEP_MM`` apart, ends included."""
    count = max(1, math.ceil(primitive_length_mm(p) / SAMPLE_STEP_MM))
    for k in range(count + 1):
        t = k / count
        if isinstance(p, Line):
            yield p.x1_mm + t * (p.x2_mm - p.x1_mm), p.y1_mm + t * (p.y2_mm - p.y1_mm)
        else:
            yield p.point_at(p.start_rad + t * p.sweep_rad)


def _tightest_clearances_mm(board: Layout) -> tuple[float, float]:
    """Return the smallest copper-to-outline and copper-to-hole clearance of a board (inf without holes)."""
    loops = [board.outline.outer, *board.outline.cutouts]
    edge_mm = hole_mm = math.inf
    for path in board.paths:
        for prim in path.primitives:
            for x, y in _centreline_points(prim):
                edge_mm = min(
                    edge_mm, min(_distance_to_outline_mm((x, y), q) for loop in loops for q in loop) - prim.width_mm / 2
                )
                for hole in board.outline.holes:
                    hole_mm = min(
                        hole_mm, math.hypot(x - hole.x_mm, y - hole.y_mm) - hole.diameter_mm / 2 - prim.width_mm / 2
                    )
    return edge_mm, hole_mm


@pytest.mark.req("REQ-F-09", "REQ-F-10")
@settings(max_examples=max(20, COMPUTE_EXAMPLES))
@given(design=spiral_designs())
def test_pr_11_copper_short_of_the_edge_or_hole_clearance_is_reported_by_the_drc(design: DesignParameters) -> None:
    """PR-11 (clearance part). Catches copper inside the edge or hole clearance that the DRC passes.

    The generator does not promise the clearance (a link of a 4-pole draw lies 0.14 mm from the edge under a 0.3 mm
    rule), so containment holds exactly when the DRC says so. The distance comes from point-to-line and point-to-arc
    geometry, not from the DRC kernels. A sampled point is within half a sampling step of any point of its edge, so
    only copper short of the rule by more than SAMPLE_STEP_MM / 2 must be reported.
    """
    built = build_layout(design, REGISTRY)
    if isinstance(built, Unbuildable):
        return
    slack_mm = SAMPLE_STEP_MM / 2
    for board in built.boards:
        edge_mm, hole_mm = _tightest_clearances_mm(board)
        report = run_drc(board, design.drc_rules)
        assert report is not None
        kinds = {v.kind for v in report.violations}
        assert edge_mm >= design.drc_rules.edge_clearance_mm - slack_mm or DrcCheckKind.COPPER_EDGE in kinds
        assert hole_mm >= design.drc_rules.hole_clearance_mm - slack_mm or DrcCheckKind.COPPER_HOLE in kinds


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


def _heading(p: Primitive, at_end: bool) -> float:
    if isinstance(p, Line):
        return math.atan2(p.y2_mm - p.y1_mm, p.x2_mm - p.x1_mm)
    angle = p.start_rad + (p.sweep_rad if at_end else 0.0)
    return angle + math.copysign(math.pi / 2, p.sweep_rad)


def _filleted(design: DesignParameters, radius_mm: float) -> DesignParameters:
    assert isinstance(design.winding, SpiralWindingSpec)
    coil = dataclasses.replace(design.winding.coil, corner_radius_mm=radius_mm)
    return dataclasses.replace(design, winding=dataclasses.replace(design.winding, coil=coil))


@pytest.mark.req("REQ-F-01")
@settings(max_examples=max(20, COMPUTE_EXAMPLES))
@given(design=spiral_designs(), radius_mm=st.sampled_from([0.2, 0.5]))
def test_pr_03_headings_are_continuous_at_every_fillet_joint(design: DesignParameters, radius_mm: float) -> None:
    """PR-03 (tangent part, UT-GEO-02 on random coils). Catches a fillet on the wrong side or a mis-trimmed neighbour.

    A wrong-side fillet jumps pi in heading; only joints that touch a fillet are tangent by construction (G9), the
    other corners of an end turn are real corners.
    """
    built = build_layout(_filleted(design, radius_mm), REGISTRY)
    if isinstance(built, Unbuildable):
        return
    for board in built.boards:
        for path in board.paths:
            for before, after in zip(path.primitives, path.primitives[1:], strict=False):
                if PrimitiveRole.FILLET in (before.role, after.role):
                    jump = abs(math.remainder(_heading(before, True) - _heading(after, False), 2.0 * math.pi))
                    assert jump <= 1e-6
                    assert math.dist(before.end_point(), after.start_point()) <= 1e-6


@pytest.mark.req("REQ-F-01")
@settings(max_examples=max(20, COMPUTE_EXAMPLES))
@given(design=spiral_designs())
def test_pr_10_layer_y_mirrors_layer_x_about_every_coil_axis(design: DesignParameters) -> None:
    """PR-10 (UT-GEO-03 on random coil specs). Catches a Y spiral that is not the reversed mirror of X on any coil.

    Both paths are stored in current direction, so X equals Y mirrored and reversed for every polarity.
    """
    built = build_layout(design, REGISTRY)
    if isinstance(built, Unbuildable):
        return
    assert isinstance(design.winding, SpiralWindingSpec)
    coil, pair = design.winding.coil, design.winding.layers.pairs[0]
    board = built.boards[0]
    for k in range(coil.coil_count):
        axis = coil.first_coil_angle_rad + 2.0 * math.pi * k / coil.coil_count
        x = next(p for p in board.paths if p.element == k and p.layer == pair.layer_in)
        y = next(p for p in board.paths if p.element == k and p.layer == pair.layer_out)
        expected = reverse_path(mirror(y.primitives, axis))
        assert len(expected) == len(x.primitives)
        for a, b in zip(expected, x.primitives, strict=True):
            assert math.dist(a.start_point(), b.start_point()) <= 1e-9
            assert math.dist(a.end_point(), b.end_point()) <= 1e-9


def _with_copper_scale(design: DesignParameters, scale: float) -> DesignParameters:
    """Scale every copper layer and give the difference to the first dielectric, so the board thickness is kept."""
    layers = design.stackup.layers
    removed = sum(layer.thickness_mm * (1.0 - scale) for layer in layers if isinstance(layer, CopperLayer))
    first_dielectric = next(i for i, layer in enumerate(layers) if isinstance(layer, DielectricLayer))
    scaled = tuple(
        dataclasses.replace(layer, thickness_mm=layer.thickness_mm * scale)
        if isinstance(layer, CopperLayer)
        else dataclasses.replace(layer, thickness_mm=layer.thickness_mm + removed)
        if i == first_dielectric
        else layer
        for i, layer in enumerate(layers)
    )
    return dataclasses.replace(design, stackup=Stackup(layers=scaled))


@pytest.mark.req("REQ-F-11")
@settings(max_examples=COMPUTE_EXAMPLES)
@given(design=spiral_designs(), scales=st.tuples(st.floats(0.5, 0.8), st.floats(1.25, 2.0)))
def test_pr_06_phase_resistance_is_affine_in_inverse_copper_thickness(
    design: DesignParameters, scales: tuple[float, float]
) -> None:
    """PR-06 (R and t_cu). Catches a track resistance not proportional to 1/t_cu (EQ-10).

    Vias keep their plating, so R = a / t + b: the three points (1/t, R) of three thicknesses lie on one line.
    """
    points = []
    for scale in (scales[0], 1.0, scales[1]):
        analysis = _outcome(_with_copper_scale(design, scale)).analysis
        if analysis is None:
            return
        points.append((1.0 / scale, analysis.resistance_phase_20c_ohm.value))
    (x1, r1), (x2, r2), (x3, r3) = points
    assert (r2 - r1) * (x3 - x2) == pytest.approx((r3 - r2) * (x2 - x1), rel=1e-6)
    assert r3 < r1


def _first_phase_angle_rad(analysis: Any) -> float:
    """Angle of the fundamental of the first phase EMF waveform; the last sample repeats the first."""
    return cmath.phase(np.fft.fft(np.array(analysis.emf_waveform_v.value)[:-1])[1])


@pytest.mark.req("REQ-F-02")
@settings(max_examples=COMPUTE_EXAMPLES)
@given(design=spiral_designs().filter(_balanced))
def test_pr_06_rotating_by_one_coil_pitch_shifts_the_phasor_and_keeps_ke(design: DesignParameters) -> None:
    """PR-06 (rotation, DEF-17). Catches a phasor that does not follow the rotor field or a Ke that depends on theta_0.

    Rotating the first coil by 2 pi / Q moves the phase EMF by p 2 pi / Q electrical (p = pole pairs); numpy's fft
    angle convention gives the delay -p 2 pi / Q (inferred from a run on CF-11). R and DRC values are not compared:
    see the unit report, the chain routing and the terminal pads depend on where the angular cut falls.
    """
    assert isinstance(design.winding, SpiralWindingSpec)
    coil = design.winding.coil
    pitch = 2.0 * math.pi / coil.coil_count
    rotated = dataclasses.replace(
        design,
        winding=dataclasses.replace(
            design.winding, coil=dataclasses.replace(coil, first_coil_angle_rad=coil.first_coil_angle_rad + pitch)
        ),
    )
    before, after = _outcome(design).analysis, _outcome(rotated).analysis
    if before is None or after is None:
        return
    expected = -(design.rotor.poles // 2) * pitch
    shift = _first_phase_angle_rad(after) - _first_phase_angle_rad(before)
    assert abs(math.remainder(shift - expected, 2.0 * math.pi)) <= 1e-9
    assert sorted(p.ke_peak_v_s_per_rad.value for p in after.phases) == pytest.approx(
        sorted(p.ke_peak_v_s_per_rad.value for p in before.phases), rel=REL
    )
