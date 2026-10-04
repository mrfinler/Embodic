"""Self-tests for the comparators, tolerance classes and the D-006 band rule."""

import copy
import math
from dataclasses import dataclass, replace

import pytest

from harness import (
    DATA_DIR,
    DRC_VALUE,
    EXACT,
    INTEGRATED,
    KERNEL,
    KERNEL_MM,
    XCOIL_DRC_SLACK_MM,
    Comparison,
    DiffKind,
    GoldenReport,
    Verdict,
    compare_drc,
    compare_prims,
    compare_scalar,
    compare_sequence,
    load_case,
    near_threshold,
)

pytestmark = pytest.mark.req("REQ-F-10")


@dataclass(frozen=True)
class _Line:
    """Stand-in with the interfaces.md section 5 ``Line`` field names (embodic.geometry is U-M1b's)."""

    x1_mm: float
    y1_mm: float
    x2_mm: float
    y2_mm: float
    width_mm: float


@dataclass(frozen=True)
class _Arc:
    """Stand-in with the interfaces.md section 5 ``Arc`` field names."""

    cx_mm: float
    cy_mm: float
    r_mm: float
    start_rad: float
    sweep_rad: float
    width_mm: float


def _as_section5(record: dict) -> _Line | _Arc:
    if record["type"] == "line":
        return _Line(record["x1"], record["y1"], record["x2"], record["y2"], record["width"])
    return _Arc(record["cx"], record["cy"], record["r"], record["a1"], record["a2"] - record["a1"], record["width"])


def _kinds(result: Comparison) -> list[tuple[str, DiffKind]]:
    return [(d.path, d.kind) for d in result.diffs]


def test_tolerance_classes_match_test_plan() -> None:
    """Catch a tolerance class drifting from test_plan.md section 3, GR-17 and GR-18."""
    assert (EXACT.rel, EXACT.abs) == (0.0, 0.0)
    assert (KERNEL.rel, KERNEL.abs) == (1e-12, 0.0)
    assert (KERNEL_MM.rel, KERNEL_MM.abs) == (0.0, 1e-12)
    assert (INTEGRATED.rel, INTEGRATED.abs) == (1e-9, 0.0)
    assert (DRC_VALUE.rel, DRC_VALUE.abs) == (0.0, 1e-6)


@pytest.mark.parametrize(
    ("tolerance", "golden", "inside", "outside"),
    [
        (KERNEL, 123.456, 123.456 * (1 + 5e-13), 123.456 * (1 + 3e-12)),
        (KERNEL_MM, 0.0, 9e-13, 2e-12),
        (INTEGRATED, -4.2e3, -4.2e3 * (1 + 5e-10), -4.2e3 * (1 + 2e-9)),
        (DRC_VALUE, 0.19901, 0.19901 + 9e-7, 0.19901 + 1.1e-6),
        (EXACT, 0.1, 0.1, 0.1 + 2**-56),
    ],
)
def test_compare_scalar_applies_each_tolerance_class(tolerance, golden, inside, outside) -> None:
    """Catch a class that admits a seeded difference beyond its bound or rejects one within it."""
    assert compare_scalar(golden, inside, tolerance).verdict is Verdict.MATCH
    result = compare_scalar(golden, outside, tolerance)
    assert result.verdict is Verdict.MISMATCH
    assert _kinds(result) == [("$", DiffKind.VALUE)]


@pytest.mark.parametrize(
    ("golden", "actual", "same"),
    [
        (math.inf, math.inf, True),
        (-math.inf, -math.inf, True),
        (math.nan, math.nan, True),
        (math.inf, -math.inf, False),
        (math.inf, 1.7976931348623157e308, False),
        (math.nan, 0.0, False),
        (0.0, math.nan, False),
    ],
)
def test_compare_scalar_nonfinite_values(golden, actual, same) -> None:
    """Catch NaN or Infinity comparing equal to the wrong value (NaN != NaN, inf - inf = NaN)."""
    assert compare_scalar(golden, actual, KERNEL).ok is same


def test_compare_scalar_integers_are_exact_under_any_class() -> None:
    """Catch a count mismatch hidden by a relative tolerance (10**12 vs 10**12 + 1 is 1e-12 rel.)."""
    assert compare_scalar(10**12, 10**12 + 1, INTEGRATED).verdict is Verdict.MISMATCH


def test_compare_scalar_json_integer_matches_float() -> None:
    """Catch a false alarm when JSON wrote a whole-number JS double as ``5`` and Python returns ``5.0``."""
    assert compare_scalar(5, 5.0, KERNEL).verdict is Verdict.MATCH


@pytest.mark.parametrize(("golden", "actual"), [(True, 1), (1, True), ("side", "endturn"), (None, 0.0)])
def test_compare_scalar_type_and_text_differences(golden, actual) -> None:
    """Catch a bool passing for an int, a wrong kind string, or a missing value read as zero."""
    assert compare_scalar(golden, actual, KERNEL).verdict is Verdict.MISMATCH


def test_compare_scalar_refuses_containers() -> None:
    """Catch a caller comparing a list with compare_scalar and getting a meaningless verdict."""
    with pytest.raises(TypeError):
        compare_scalar([1.0], [1.0], KERNEL)


def test_compare_sequence_on_a_real_fixture() -> None:
    """Catch a seeded 1e-11 mm shift in one discretised segment; accept a 5e-13 mm shift."""
    golden = load_case(DATA_DIR / "m1" / "discretize-chain-mixed-hmax-0p3.json").calls[0].output
    assert compare_sequence(golden, copy.deepcopy(golden), KERNEL_MM).verdict is Verdict.MATCH

    near = copy.deepcopy(golden)
    near[7]["y2"] += 5e-13
    assert compare_sequence(golden, near, KERNEL_MM).verdict is Verdict.MATCH

    far = copy.deepcopy(golden)
    far[7]["y2"] += 1e-11
    result = compare_sequence(golden, far, KERNEL_MM)
    assert result.verdict is Verdict.MISMATCH
    assert _kinds(result) == [("$[7].y2", DiffKind.VALUE)]


def test_compare_sequence_length_keys_and_types() -> None:
    """Catch a missing segment, a renamed field and a scalar in place of a point."""
    assert _kinds(compare_sequence([1.0, 2.0], [1.0], KERNEL)) == [("$", DiffKind.LENGTH)]
    assert _kinds(compare_sequence([{"x": 1.0}], [{"y": 1.0}], KERNEL)) == [("$[0]", DiffKind.KEYS)]
    assert _kinds(compare_sequence([[1.0, 2.0]], [3.0], KERNEL)) == [("$[0]", DiffKind.TYPE)]
    assert compare_sequence((1.0, 2.0), [1.0, 2.0], KERNEL).verdict is Verdict.MATCH


def test_compare_sequence_refuses_scalars() -> None:
    """Catch a caller passing a scalar where a sequence is expected."""
    with pytest.raises(TypeError):
        compare_sequence(1.0, 1.0, KERNEL)


def _reverse_chain_output() -> list[dict]:
    return load_case(DATA_DIR / "m1" / "reverseprims-chain-mixed.json").calls[0].output


def test_compare_prims_accepts_section5_objects_against_fixture_records() -> None:
    """Catch a false alarm when an embodic-shaped Line/Arc reproduces the Xcoil records exactly."""
    golden = _reverse_chain_output()
    assert compare_prims(golden, [_as_section5(r) for r in golden], KERNEL_MM).verdict is Verdict.MATCH


def test_compare_prims_ignores_whole_turn_in_start_angle() -> None:
    """Catch a false alarm when the port normalises the start angle by 2 pi (same arc, other number)."""
    golden = [{"type": "arc", "cx": 1.0, "cy": 2.0, "r": 3.0, "a1": 0.2, "a2": 1.4, "width": 0.25, "kind": "endturn"}]
    actual = [_Arc(1.0, 2.0, 3.0, 0.2 + 2 * math.pi, 1.2, 0.25)]
    assert compare_prims(golden, actual, KERNEL_MM).verdict is Verdict.MATCH


def test_compare_prims_detects_half_circle_direction_flip() -> None:
    """Catch a reversed half circle: same endpoints and |sweep|, so only the direction check sees it."""
    golden = [{"type": "arc", "cx": 0.0, "cy": 0.0, "r": 1e-3, "a1": 0.0, "a2": math.pi, "width": 0.2, "kind": "bus"}]
    actual = [_Arc(0.0, 0.0, 1e-3, 0.0, -math.pi, 0.2)]
    assert _kinds(compare_prims(golden, actual, KERNEL_MM)) == [("$[0].direction", DiffKind.DIRECTION)]


def test_compare_prims_detects_width_type_count_and_shift() -> None:
    """Catch a wrong width, a line in place of an arc, a dropped primitive and a 1e-11 mm endpoint shift."""
    golden = _reverse_chain_output()
    section5 = [_as_section5(r) for r in golden]

    wide = [*section5[:2], replace(section5[2], width_mm=0.25)]
    assert _kinds(compare_prims(golden, wide, KERNEL_MM)) == [("$[2].width", DiffKind.VALUE)]

    swapped = [section5[0], _Line(0.0, 0.0, 1.0, 1.0, 0.15), section5[2]]
    assert _kinds(compare_prims(golden, swapped, KERNEL_MM)) == [("$[1]", DiffKind.TYPE)]

    assert _kinds(compare_prims(golden, section5[:2], KERNEL_MM)) == [("$", DiffKind.LENGTH)]

    shifted = [*section5[:2], replace(section5[2], x2_mm=section5[2].x2_mm + 1e-11)]
    assert _kinds(compare_prims(golden, shifted, KERNEL_MM)) == [("$[2].end.x", DiffKind.VALUE)]
    nudged = [*section5[:2], replace(section5[2], x2_mm=section5[2].x2_mm + 5e-13)]
    assert compare_prims(golden, nudged, KERNEL_MM).verdict is Verdict.MATCH


def test_compare_prims_detects_arc_radius_change() -> None:
    """Catch an arc whose radius drifts while its sweep stays the same."""
    golden = _reverse_chain_output()
    section5 = [_as_section5(r) for r in golden]
    arc = section5[1]
    bad = [section5[0], replace(arc, r_mm=arc.r_mm + 1e-9)]
    paths = {path for path, _ in _kinds(compare_prims(golden[:2], bad, KERNEL_MM))}
    assert "$[1].r" in paths


def test_compare_prims_rejects_unknown_shapes() -> None:
    """Catch a record without a known type being compared as if it were a primitive."""
    with pytest.raises(TypeError):
        compare_prims([{"type": "circle"}], [{"type": "circle"}], KERNEL_MM)


RULE_MM = 0.2


def test_drc_band_rule_xcoil_baseline_is_indeterminate() -> None:
    """Catch a band-rule implementation that fails Xcoil's default design (0.19901 mm at a 0.20 mm rule)."""
    result = compare_drc(0.19901, 0.19901, rule_mm=RULE_MM, golden_pass=True)
    assert result.verdict is Verdict.INDETERMINATE
    assert result.ok


@pytest.mark.parametrize(
    ("value", "golden_pass"),
    [(0.25, True), (RULE_MM, True), (0.19, False), (RULE_MM - XCOIL_DRC_SLACK_MM - 1e-9, False), (math.inf, True)],
)
def test_drc_band_rule_agreement_outside_the_band(value, golden_pass) -> None:
    """Catch a disagreement-free case outside [rule - 0.004, rule) being reported as anything but a match."""
    assert compare_drc(value, value, rule_mm=RULE_MM, golden_pass=golden_pass).verdict is Verdict.MATCH


@pytest.mark.parametrize("value", [RULE_MM - XCOIL_DRC_SLACK_MM, RULE_MM - 1e-9, 0.198])
def test_drc_band_rule_band_edges(value) -> None:
    """Catch an off-by-edge band: the lower edge rule - 0.004 is inside, the rule itself is outside."""
    assert compare_drc(value, value, rule_mm=RULE_MM, golden_pass=True).verdict is Verdict.INDETERMINATE


def test_drc_band_rule_requires_agreement_above_the_rule() -> None:
    """Catch a symmetric band |v - rule| <= 0.004 that would excuse a disagreement at rule + 0.002."""
    result = compare_drc(RULE_MM + 0.002, RULE_MM + 0.002, rule_mm=RULE_MM, golden_pass=False)
    assert _kinds(result) == [("$", DiffKind.PASS_FAIL)]


def test_drc_band_rule_requires_agreement_below_the_band() -> None:
    """Catch embodic passing a clearance that Xcoil fails outside the band."""
    result = compare_drc(0.19, 0.19, rule_mm=RULE_MM, golden_pass=True)
    assert _kinds(result) == [("$", DiffKind.PASS_FAIL)]


def test_drc_values_compared_at_one_micrometre() -> None:
    """Catch a DRC value drift beyond 1e-6 mm even when both sides pass."""
    assert compare_drc(0.25, 0.25 + 9e-7, rule_mm=RULE_MM, golden_pass=True).verdict is Verdict.MATCH
    result = compare_drc(0.25, 0.25 + 1.1e-6, rule_mm=RULE_MM, golden_pass=True)
    assert _kinds(result) == [("$", DiffKind.VALUE)]


def test_drc_epsilon_decides_embodic_pass() -> None:
    """Catch embodic's flag using a slack other than epsilon: rule - 2e-6 fails, rule - 5e-7 passes."""
    in_band = compare_drc(RULE_MM - 2e-6, RULE_MM - 2e-6, rule_mm=RULE_MM, golden_pass=True)
    assert in_band.verdict is Verdict.INDETERMINATE
    assert "embodic fails" in in_band.indeterminate[0]
    passing = compare_drc(RULE_MM - 5e-7, RULE_MM - 5e-7, rule_mm=RULE_MM, golden_pass=True)
    assert "embodic passes" in passing.indeterminate[0]


def test_near_threshold_uses_1e9_relative_margin() -> None:
    """Catch a near-threshold window wider or narrower than test_plan.md's 1e-9 relative."""
    assert near_threshold(4.0 * (1 + 5e-10), 4.0)
    assert not near_threshold(4.0 * (1 + 2e-9), 4.0)


def test_golden_report_fails_mismatch_and_logs_the_rest() -> None:
    """Catch a mismatch passing silently, or an indeterminate result vanishing from the summary."""
    report = GoldenReport()
    with pytest.raises(AssertionError, match=r"case-a: mismatch[\s\S]*\$\[7\]"):
        report.check("case-a", compare_sequence([0.0] * 8, [0.0] * 7 + [1.0], KERNEL_MM))
    report.check("case-b", compare_drc(0.19901, 0.19901, rule_mm=RULE_MM, golden_pass=True))
    report.check("case-c", compare_scalar(1.0, 1.0, KERNEL))
    lines = report.summary_lines()
    assert len(lines) == 1
    assert lines[0].startswith("case-b: indeterminate")
