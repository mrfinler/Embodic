"""Agent 4's V3-01 re-rulings on release 0.0.4 (c25d8a9, U-V18) that replace rows of v3_01_rulings_v13.py and _v14.py.

The rows are the 19 live must rows whose tests changed between 0a74974 (0.0.2) and c25d8a9, found by
`v18_changed_rows.py` from `git diff --name-only 0a74974 c25d8a9 -- tests` and the REQ markers of the 0.0.4 reports.
RULINGS has the shape of v3_01_rulings_v13.RULINGS. PINS (records/V3-01_pins_c25d8a9.json, written by
`v18_rerule.py --pin`) holds the SHA-256 of each cited function's source segment, or of the cited record file, on
c25d8a9. req_audit.py --target 0.0.4 applies v13 first, v14 on top and these last.

A carried ruling keeps the cites of the earlier ruling, whose sources still equal their pins on c25d8a9, and may add
tests that 0.0.4 brought. Every ruling is `verified` by reading the cited test sources and the 0a74974..c25d8a9 diff
of the row's changed test files on c25d8a9; every cited test passed with the row's marker in the 0.0.4 release run
(`v18_rerule.py --check`).
"""

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("v3_01_rulings_v13", HERE / "v3_01_rulings_v13.py")
_v13 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_v13)
Ruling = _v13.Ruling

BASE = "c25d8a9"
PIN_FILE = HERE / "records/V3-01_pins_c25d8a9.json"

DRC = "tests/unit/drc/test_run_drc.py"
ANGLE = "tests/unit/model/test_angle_file_form.py"
ZERO = "tests/unit/embodic_io/project/test_hash_negative_zero.py"
N21 = "tests/unit/embodic_io/exporters/test_n21_joint_continuity.py"
TRACE = "tests/unit/base/test_trace_matrix.py"
GATE = "tests/unit/base/test_trace_matrix_gate.py"
PIPE = "tests/unit/property/test_pipeline_properties.py"
SAME = "the cited functions equal their pins on c25d8a9 and passed with the marker in the 0.0.4 run"


def _carry(req: str, reason: str, *extra: str) -> "Ruling":
    """Return a `checks` ruling of req that cites what the U-V13 ruling cited, with a new reason and extra cites."""
    return Ruling("checks", reason, (*_v13.RULINGS[req].cites, *extra))


RULINGS = {
    "REQ-F-01": _carry(
        "REQ-F-01",
        f"Carried from U-V13: {SAME}. 0.0.4 adds only the helper `_cf11_with_first_coil_angle` to {PIPE} (PR-08's "
        "negative-zero case); src/embodic/generators and src/embodic/geometry are unchanged since 0a74974.",
    ),
    "REQ-F-02": _carry(
        "REQ-F-02",
        f"Carried from U-V13: {SAME}. The only changed test file of the row is {PIPE} (a PR-08 helper); "
        "src/embodic/winding is unchanged since 0a74974.",
    ),
    "REQ-F-04": _carry(
        "REQ-F-04",
        f"Carried from U-V13: {SAME}. In test_gr07_even_stackup.py only the fixture freshness test changed (the "
        "node runtime line of D-075); the stack-up model is unchanged since 0a74974.",
    ),
    "REQ-F-10": _carry(
        "REQ-F-10",
        "(a) test_default_example_passes_drc now carries REQ-F-10 (the U-V13 gap, closed by U-M8k). (b) to (d) as "
        "U-V13 ruled (PR-01's dense bracket, UT-DRC-03 1 um, GR-18 against Xcoil). 0.0.4 narrows the rule 5 and rule 2 "
        "exemptions (U-D25, D-080a); the row's soundness clause now also rests on UT-DRC-04 cases that put a "
        "below-rule pair just outside the narrowed exemption (5f, the D08 wide leg) and on the exact D-006 float "
        "boundary (DEF-UV15-01). V3-02 on 0.0.4 seeds the widened exemptions and the band flip into items.py and "
        "engine.py (records/V3-02.md).",
        f"{DRC}::test_ut_drc_03_the_float_boundary_of_d006_is_rule_minus_epsilon_and_equal_passes",
        f"{DRC}::test_ut_drc_04_junction_end_group_is_exempt_only_from_the_primitive_the_end_lies_on",
        f"{DRC}::test_ut_drc_04_wide_leg_on_a_coil_end_is_reported_against_the_coil_turn",
    ),
    "REQ-F-11": Ruling(
        "checks",
        "(i) The 0.0.4 evidence holds 58 of the registry's 63 test IDs (passed_tests.v1.json of c25d8a9, TR-05 PASS). "
        "The U-V13 gap EQT-27-GR is closed: test_utilisation_factor_matches_eq27 compares k_u with Xcoil on sector, "
        "serpentine and wave at 1e-9 (D-064a). The five IDs without a passing test are EQT-05-O2, EQT-06-O2 and "
        "EQT-14-O2, oracle validations that clause (ii) lets wait for a reference (D-048f: no board), and EQT-28-GR "
        "and EQT-29-GR, whose equations have no port (D-061e). (ii) OR-11 and OR-12 are Agent 4's FEA records; the "
        "audit keeps the row `partial` through NEEDS (FEA), whatever this ruling says.",
        (
            "tests/golden/m2_physics/test_analysis_golden.py::test_utilisation_factor_matches_eq27",
            "gate:TR-05",
        ),
    ),
    "REQ-F-13": Ruling(
        "partial",
        "Reach in at most 2 interactions (test_f13_view_reach.py, F13-1) and the zoom range 0.1x to 200x (F13-2, "
        "UI-03) are asserted as U-V13 ruled. 'Keeps stroke widths' is asserted for the top visible layer only. In "
        "0.0.4 a layer below the top one is painted by the layer cue (LayerCueItem, U-M8x), and its copper items are "
        "kept for tags and tooltips with ItemHasNoContents (geometry_view.py `_add_copper`, l.328-340). UI-03 "
        "(test_theme_and_geometry.py l.105-118) still reads the pen of every `copper` item, so for D08's L2 it reads "
        "pens that paint nothing. The cue strokes that copper's ink at its trace width in scene millimetres and its "
        "casing and empty inside at pixel widths divided by the zoom (layer_cue.py `_stroke` l.73-87, `paint` "
        "l.151-174), so the width holds by construction (`inferred` from the code), but no test reads the cue's ink "
        "width: UI-58 and UI-59 measure the cue's pixels at 5, 6, 20 and 24 px/mm, not at 0.1x and 200x.",
        missing="A test that the lower-layer copper the cue paints keeps its trace width in millimetres at zoom 0.1x "
        "and 200x (for example, the extent of a lower-layer primitive in a grab at both ends of the range).",
        kind="test",
        owner="Agent 3",
    ),
    "REQ-F-14": _carry(
        "REQ-F-14",
        "Every BV case gives its code: BV-05 (test_spiral_bounds.py) now carries REQ-F-14 (the U-V13 gap, closed by "
        "U-M8k). 1000 seeded drafts per generator as U-V13 ruled (F14-1, slow, passed in the release run). "
        "DEF-UV15-04 is fixed at its root: an angle whose degree value is not finite is refused by validation and "
        "compute returns the issue (test_angle_file_form.py, all seven angle fields). '0 non-finite results' stays "
        "read as 'no silent non-finite result' (`assumption`, D-061f).",
        f"{ANGLE}::test_an_angle_with_no_finite_degrees_is_refused_by_validation",
        f"{ANGLE}::test_compute_returns_the_issue_for_an_angle_with_no_finite_degrees",
    ),
    "REQ-F-15": _carry(
        "REQ-F-15",
        f"Carried from U-V13: {SAME}. 0.0.4 adds the negative-zero cases of D-073a: -0.0 in any float field leaves "
        "the design hash unchanged and save, load, save stays byte-identical (test_hash_negative_zero.py), and PR-08 "
        "draws the -0.0 angle.",
        f"{ZERO}::test_f15_negative_zero_in_any_float_field_leaves_the_design_hash_unchanged",
        f"{ZERO}::test_f15_save_load_save_is_byte_identical_with_a_negative_zero_in_the_design",
    ),
    "REQ-F-21": _carry(
        "REQ-F-21",
        f"Carried from U-V13: {SAME}. The only changed test file of the row is {PIPE} (a PR-08 helper).",
    ),
    "REQ-F-34": _carry(
        "REQ-F-34",
        f"Carried from U-V13: {SAME}. In test_serpentine_properties.py only the module-level example count of PR-13 "
        "and PR-14 changed (min(25, ...), DEF-UV15-03); the cited golden and generator tests are unchanged.",
    ),
    "REQ-F-37": _carry(
        "REQ-F-37",
        f"Carried from U-V13: {SAME}. test_n02_typing_preview.py changed only in its latency markers (D-074); no "
        "draft test changed.",
    ),
    "REQ-F-40": _carry(
        "REQ-F-40",
        f"Carried from U-V13: {SAME}. The changed file of the row is Agent 4's M1 exemption model "
        "(test_exemption_model.py, U-V17), not a board-dump test.",
    ),
    "REQ-N-02": Ruling(
        "partial",
        "On Linux every clause is asserted: UI-05 during a 3 s compute, N02-1 to N02-10 (UI-36 to UI-45), and the "
        "UX-AC-22 'Updating' state with the previous values dimmed at 300 ms or updated before it "
        "(test_n02_updating_state.py, four cases); the latency gate ran in its own process and passed 6 of 6 in the "
        "0.0.4 release run (D-074, D-081). On Windows the 0.0.3 laptop runs failed UI-05 and the N02-10 arrival case "
        "intermittently (D-076c, D-077), DEF-W-12 is open and the fix is in Phase 5 (D-076d, the user). No Windows "
        "run of the 0.0.4 build exists.",
        missing="A Windows latency gate run on the 0.0.4 wheel (D-081 lists it); a pass there does not close DEF-W-12, "
        "which D-077 calls intermittent.",
        kind="Windows run",
        owner="Fable (laptop); the fix is Phase 5",
    ),
    "REQ-N-04": Ruling(
        "partial",
        "Same-platform byte identity holds on Linux: two runs of pk04_reference.py from the 0.0.4 wheel gave six "
        "byte-identical files, and pk04_compare.py --self-test passes 8 of 8 (docs/phase3/verification/reference, "
        "U-V18). The cross-platform clause needs PK-04 on Windows against the 0.0.4 reference; none exists.",
        missing="PK-04 on Windows with the 0.0.4 wheel against reference/linux of U-V18, recorded and indexed.",
        kind="manual record",
        owner="Fable (Windows laptop)",
    ),
    "REQ-N-18": _carry(
        "REQ-N-18",
        f"Carried from U-V13: {SAME}. In test_worker_and_errors.py only the DEF-U-M8n-01 cancel test and its "
        "`build` helper changed (D-076b), not the cited UI-12 fault-injection test.",
    ),
    "REQ-N-21": _carry(
        "REQ-N-21",
        "Carried from U-V13 with the V3-05-01 test that 0.0.4 adds: SVG joint ends that round apart across a "
        "rounding step are written once from the shared coordinate (D-072).",
        f"{N21}::test_n21_svg_joint_ends_that_round_apart_are_written_once_from_the_shared_coordinate",
    ),
    "REQ-N-23": _carry(
        "REQ-N-23",
        f"Carried from U-V13: {SAME}. test_layer_cue.py carries REQ-N-23 for the cue in greyscale; the cue adds no "
        "hatch, and the eye and hatch tests the ruling cites are unchanged.",
    ),
    "REQ-T-03": _carry(
        "REQ-T-03",
        f"Carried from U-V13: {SAME}. The only changed test file of the row is {PIPE} (a PR-08 helper).",
    ),
    "REQ-T-09": _carry(
        "REQ-T-09",
        "Carried from U-V13 with the two-report cases that 0.0.4 adds for the separate latency process (D-074): "
        "merged reports give each test the outcome of the report that ran it, and the gate still names an unmarked "
        "test that only the second report holds. The release run's TR-02 line reads 0 unmarked tests.",
        f"{TRACE}::test_merged_reports_give_each_test_the_outcome_of_the_report_that_ran_it",
        f"{GATE}::test_gate_still_names_an_unmarked_test_that_only_the_second_report_holds",
    ),
}

PINS = json.loads(PIN_FILE.read_text(encoding="utf-8")) if PIN_FILE.is_file() else {}
