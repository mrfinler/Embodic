"""Agent 4's V3-01 re-rulings on release 0.0.4 (c25d8a9, U-V19), applied on top of v3_01_rulings_v13, _v14 and _v18.

RULINGS has the shape of v3_01_rulings_v13.RULINGS. It holds three groups:

- The nine rows that U-V13 ruled `partial` on 260191f and nobody re-ruled (REQ-F-08, REQ-F-12, REQ-N-09, REQ-N-10,
  REQ-T-05, REQ-T-08, REQ-T-14, REQ-L-01, REQ-L-05), and the two text-only rows whose U-V13 ruling is `partial`
  (REQ-F-05, REQ-F-06), each read again on c25d8a9 against the Acceptance cell of requirements.md. REQ-F-13 keeps
  U-V18's `partial` with the width test of U-V19 item 3 as its missing piece.
- The `checks` rows whose cited test U-M8y renames (RENAMES, from the ID map u_v19_id_map.py, D-046c). Their cites
  name the function after the rename. Their pins are the SHA-256 of the c25d8a9 source segment with only the name
  changed and the file passed through `ruff format` (`v19_rerule.py --pin`), so the audit backs the row after U-M8y
  only when the rename changed nothing else.

PINS (records/V3-01_pins_c25d8a9_v19.json) holds one SHA-256 per non-gate cite of a `checks` ruling, in the form of
req_audit.py `cite_hash`. Every cite under its c25d8a9 name ran with the row's marker and passed in the 0.0.4 release
run (`v19_rerule.py --check`). Every ruling is `verified` by reading the cited sources on c25d8a9 unless its reason
labels a part `inferred` or `assumption`.
"""

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_v13 = _load("v3_01_rulings_v13")
_v18 = _load("v3_01_rulings_v18")
Ruling = _v13.Ruling

BASE = "c25d8a9"
PIN_FILE = HERE / "records/V3-01_pins_c25d8a9_v19.json"

U, G, UI = "tests/unit", "tests/golden", "tests/ui"
KERN = f"{U}/physics/test_kernels.py"
PLAN = f"{U}/winding/test_plan.py"
CF07 = f"{U}/physics/test_closed_forms_m2e2.py"
SPREAD = f"{U}/physics/test_field_layer_spread.py"
MT04 = "tests/static/test_mt04_physics_docstrings.py"
N09 = "tests/static/test_n09_parameter_units.py"
TR01 = f"{U}/base/test_tr01_release_gate.py"
SKIN = f"{U}/physics/test_skin_depth_validity_flag.py"
EDGE = f"{U}/physics/test_ut_phy_21_edge_kernel.py"
TRACE = f"{U}/results/test_traceable.py"
EXPO = f"{U}/embodic_io/exporters"
BUNDLE = f"{EXPO}/test_report_readme_bundle.py"
STAMP = f"{EXPO}/test_stamp_fields.py"
CANVAS = f"{UI}/qt_shell/test_canvas_stamp.py"
LGL = "tests/static/test_lg_language.py"
LGB = "tests/static/test_lg_brand_and_names.py"
GEN = f"{U}/generators"
SPIRAL = f"{GEN}/test_spiral_generate.py"
FILLET = f"{GEN}/test_spiral_fillet_length.py"
PAIRS = f"{GEN}/test_spiral_pairs.py"
BOUNDS = f"{GEN}/test_spiral_bounds.py"
N21 = f"{EXPO}/test_n21_joint_continuity.py"

# c25d8a9 cite -> the function name U-M8y gives it (u_v19_id_map.py, decision (a)). Only renamed functions that a
# `checks` ruling cites are listed here; the map lists every rename.
RENAMES = {
    f"{PAIRS}::test_ut_geo_19_series_groups_get_their_own_centre_via_one_pitch_apart": (
        "test_ut_geo_26_series_groups_get_their_own_centre_via_one_pitch_apart"
    ),
    f"{SPIRAL}::test_default_example_passes_drc": "test_ut_drc_01_default_example_passes_drc",
    f"{BOUNDS}::test_requested_turns_above_the_turns_that_fit_are_refused_as_the_users_request": (
        "test_bv05_requested_turns_above_the_turns_that_fit_are_refused_as_the_users_request"
    ),
    f"{N21}::test_n21_dxf_writes_one_point_for_every_line_to_line_joint": (
        "test_ut_exp_02_n21_dxf_writes_one_point_for_every_line_to_line_joint"
    ),
    f"{N21}::test_n21_dxf_arc_joints_are_continuous_within_the_coincidence_bound": (
        "test_ut_exp_02_n21_dxf_arc_joints_are_continuous_within_the_coincidence_bound"
    ),
}


def renamed(cite: str) -> str:
    """Return the cite under the name U-M8y gives its function, or the cite itself."""
    if cite in RENAMES:
        return f"{cite.partition('::')[0]}::{RENAMES[cite]}"
    return cite


def original(cite: str) -> str:
    """Return the c25d8a9 cite of a renamed cite, or the cite itself."""
    back = {renamed(old): old for old in RENAMES}
    return back.get(cite, cite)


def _after_renames(req: str, earlier, reason: str) -> Ruling:
    """Return the `checks` ruling of req from an earlier rulings file with every cite under its U-M8y name."""
    ruling = earlier.RULINGS[req]
    assert ruling.ruling == "checks", req
    return Ruling("checks", reason, tuple(renamed(c) for c in ruling.cites))


_MAP = _load("u_v19_id_map")
T05_TEST = _MAP.EXTRA["T05"][0]
F05_ANALYSED = _MAP.EXTRA["F05"]

RULINGS = {
    "REQ-F-05": Ruling(
        "partial",
        "Amended acceptance (D-054b, D-054d; UT-PHY-11 reworded by U-D23). Count Q*v*(2k + 1): 36 vias for M1 and "
        "2k + 1 per series coil (UT-GEO-13, test_spiral_pairs.py and test_spiral_series_fan.py, as U-V13 ruled). "
        "Refusal of every value other than 1 on every topology with its own NOT_IMPLEMENTED code and the one-via "
        "build: test_every_topology_refuses.py, which carries REQ-F-14, not REQ-F-05 (interfaces.md section 3.2). "
        "'Analysed' is asserted by no test of the row, and 'every through via clears foreign copper (PR-01)' rests on "
        "run_drc's own pass on the built boards: no brute-force sweep checks a spiral via (PR-01 samples one trace "
        "pair per layer, PR-13 sweeps serpentine and wave boards only). UT-PHY-11's one-barrel clause has no expected "
        "value or tolerance (u_v19_id_map.py, decision (c)).",
        missing="(1) U-M8y: the UT-GEN-06 renames with the REQ-F-05 marker, the spiral brute sweep and "
        f"{F05_ANALYSED[0]} (U-V19_id_map.md). (2) Agent 6: an observable criterion for UT-PHY-11 'the analysis "
        "gives every via one barrel'. Then Agent 4 re-rules the row.",
        kind="test; amendment",
        owner="Agent 3 (U-M8y); Agent 6",
    ),
    "REQ-F-06": Ruling(
        "checks",
        "Amended acceptance. (a) D08 gives 3 loops with the half closing: the frame (OR-04, pads 0.6 and 1.2 mm) and "
        "the built board (test_d08_builds_three_turns_with_the_half_closing). (b) Sharp: each coil layer's track "
        "length equals the reference construction at rel 1e-6 (test_spiral_length.py). Fillets: per corner the change "
        "equals the line-arc closed form at 1e-9 mm and the track equals sharp plus the corner forms at 1e-9 mm "
        "(test_spiral_fillet_length.py); the U-V13 gap is closed (U-M8p, D-068): the filleted X and Y lengths equal "
        "362.6419 mm (CF-11, rho 0.5) and 150.1692 mm (CF-10 = D08, rho 1.0) at rel 1e-6 with rho_used equal to the "
        "set radius (test_ut_geo_07_filleted_track_length_equals_the_stated_total).",
        (
            f"{GEN}/test_spiral_turns.py::test_or_04_d08_builds_three_turns_with_the_half_closing",
            f"{SPIRAL}::test_d08_builds_three_turns_with_the_half_closing",
            f"{GEN}/test_spiral_length.py::test_ut_geo_07_sharp_track_length_equals_the_reference_construction",
            f"{FILLET}::test_def_m2d3_02_each_fillet_removes_the_closed_form_length",
            f"{FILLET}::test_def_m2d3_02_track_length_changes_only_at_the_corners",
            f"{FILLET}::test_ut_geo_07_filleted_track_length_equals_the_stated_total",
        ),
    ),
    "REQ-F-08": Ruling(
        "checks",
        "Ke_LL = sqrt(3) Ke_ph in star (0.017320508075688773 V*s/rad for Ke_ph 0.01) and Ke_LL = Ke_ph in delta, "
        "rel 1e-12, by CF-06, which now carries REQ-F-08 (the U-V13 gap, closed by U-M8k, D-062a). 12/14 delta "
        "raises RANGE_DELTA_TRIPLEN as a WARNING with value k_w3 = 0.5; 12/16 delta and 12/14 star raise nothing "
        "(UT-WND-07). The cited functions are unchanged since 260191f apart from the marker.",
        (
            f"{KERN}::test_cf06_star_and_delta_constants",
            f"{PLAN}::test_ut_wnd_07_delta_with_triplen_winding_factor_warns",
            f"{PLAN}::test_ut_wnd_07_no_triplen_warning",
        ),
    ),
    "REQ-F-12": Ruling(
        "checks",
        "Two-member identity at rel 1e-12: CF-07 (E 1.00 and 0.98 V, R 0.5 ohm each give E_grp 0.99 V, R_grp 0.25 "
        "ohm and P_c 2.0e-4 W), which now carries REQ-F-12 (U-M8k, D-062a). C1d per-layer B1 0.6828, 0.6813 and "
        "0.6805 T and their mirror at rel 1e-4, spread 0.336 % (UT-PHY-20, F12-1). The layer z values come from "
        "the stack-up model (copper_z_mm) that every generator copies into the layout (`inferred` from "
        "src/embodic/generators/*/generate.py).",
        (
            f"{CF07}::test_eq07_cf07_two_member_group_with_half_ohm_members",
            f"{SPREAD}::test_ut_phy_20_b1_of_each_copper_layer_matches_c1d",
            f"{SPREAD}::test_ut_phy_20_b1_spread_over_the_layers_is_0_336_percent",
        ),
    ),
    "REQ-F-13": Ruling(
        "partial",
        "As U-V18 ruled: reach in at most 2 interactions and the zoom range are asserted; the width of the lower-layer "
        "copper that the layer cue paints is read at no end of the zoom range. U-V19 measured it on the 0.0.4 package "
        "offscreen (u_v19_f13_width.py): a 1280 x 800 view of D08 fits at 6.0152 px/mm; at 200x leg 24 (L2, 0.6 mm) "
        "spans 723.0 px against 0.6 x 1203.03 = 721.82 px; at 0.1x an isolated cue stroke of 0.6 mm sums to 0.355 to "
        "0.378 px of ink per column against 0.361 px. The width holds on 0.0.4; the row lacks the test that says so.",
        missing=f"{_MAP.EXTRA['F13_VIEW'][0]} and {_MAP.EXTRA['F13_CUE'][0]} (U-V19_id_map.md item 3); "
        "then Agent 4 re-rules the row.",
        kind="test",
        owner="Agent 3 (U-M8y)",
    ),
    "REQ-N-09": Ruling(
        "checks",
        "MT-04 requires an EQ-ID and a Parameters entry for every parameter of every public module-level function of "
        "the public embodic.physics modules, and reports a planted miss. The U-V13 gap is closed (U-M8p, D-068): "
        "every numeric Parameters and Returns entry names a unit token from embodic.units.Unit or the word "
        "`dimensionless` (D-056f), with planted controls for a missing return unit and a parameter unit that must "
        "not excuse the return. Scope `assumption`: 'every physics function' is read as MT-04 reads it since U-V12, "
        "public module-level functions. Two public methods, FieldTable.at (emf.py) and "
        "InterconnectResistance.total_ohm (interconnect.py), lie outside the checker and name no EQ-ID; whether the "
        "acceptance covers methods is Agent 6's question (a docstring change in src makes a new release, D-082).",
        (
            f"{MT04}::test_mt04_physics_functions_are_documented",
            f"{MT04}::test_mt04_flags_missing_eq_id_and_parameter",
            f"{N09}::test_n09_every_numeric_parameter_of_a_public_physics_function_names_a_unit",
            f"{N09}::test_n09_every_numeric_return_of_a_public_physics_function_names_a_unit",
            f"{N09}::test_n09_a_numeric_parameter_without_a_unit_is_reported",
            f"{N09}::test_n09_a_numeric_return_without_a_unit_is_reported",
            f"{N09}::test_n09_a_unit_in_the_parameters_does_not_excuse_the_return",
        ),
    ),
    "REQ-N-10": Ruling(
        "checks",
        "Amended (D-053b). The TR-01 tests now carry REQ-N-10 (DEF-UV13-03, closed by U-M8k, D-062a): the release "
        "gate exits 1 on a live must row without a passing test or a passed record and passes when a record covers "
        "it. The 0.0.4 release gate ran the matrix with --fail-untested-through=M5 and the manual-record index and "
        "printed `untested due: 0` (gate log l.810, PASS line 'trace matrix (TR-01, TR-02)'); every live must row is "
        "on M1 to M5 (requirements.md: 5, 26, 2, 33, 7), so the run covers all 73.",
        (
            f"{TR01}::test_tr01_release_gate_fails_on_an_untested_must_row",
            f"{TR01}::test_tr01_release_gate_passes_when_a_manual_record_covers_the_row",
            f"{TR01}::test_tr01_flag_lists_a_live_must_row_that_has_neither_a_passing_test_nor_a_manual_record",
            "gate:TR-01",
        ),
    ),
    "REQ-T-05": Ruling(
        "partial",
        "Amended acceptance (U-D20). The U-V13 gap is closed (U-M8p, D-068): stderr alone names the refused equation "
        "and exactly the registry test IDs of it that passed (test_stderr_alone_names_...). The clause 'names on "
        "stderr every equation ... for which tests_passed is false' is asserted exactly only where one equation is "
        "refused; where all ten are refused, two tests check that one named equation (EQ-04, EQ-10) appears. "
        "u_v19_t05_mutants.py ran the 13 REQ-T-05 tests of test_record_passed_tests_gate.py and "
        "test_record_passed_tests.py on a copy of c25d8a9 with `unproven = unproven[:4]` before the refusal in "
        "tools/record_passed_tests.py: all 13 passed (the [:1] and [:2] mutants fail 2 and 1).",
        missing=f"{T05_TEST} (U-V19_id_map.md item 1 spec); then Agent 4 re-rules the row.",
        kind="test",
        owner="Agent 3 (U-M8y)",
    ),
    "REQ-T-08": Ruling(
        "checks",
        "Amended acceptance. A 0.4 delta trace flags R and eddy results with RANGE_SKIN_DEPTH (EQ-13, LIMITATION) "
        "and the flag travels to every result built from the resistances; UT-PHY-21 gives 5.328140, 4.208834 and "
        "5.788521 % within 0.1 pp at 0.5 mm chords and 0.005 pp at 0.1 mm (expected values from the registry "
        "formula by scipy quad); 0.1237 and 0.1045 give the CAP effect and 0.0842 the add-on. The U-V13 gap is "
        "closed (U-M8k, D-062a): test_traceable_adr_0003_worked_example now carries REQ-T-08 and its e_edge 0.124 "
        "case reads `unresolved`.",
        (*_v13.RULINGS["REQ-T-08"].cites, f"{TRACE}::test_traceable_adr_0003_worked_example"),
    ),
    "REQ-T-14": Ruling(
        "checks",
        "Amended acceptance. A non-engine drawing carries 'Illustrative, not computed'; the canvas stamp names the "
        "version and design hash at the bottom left at 4.5:1 and renames for a new outcome (UI-32 a to d). The U-V13 "
        "gap is closed (U-M8k): every export's stamp test carries REQ-T-14: SVG metadata (both render modes), the "
        "three DXF parts, the PDF text and information dictionary, README (embodic_version and design_hash lines) "
        "and the project JSON (app_version and design_hash). The bundle holds these files.",
        (
            *_v13.RULINGS["REQ-T-14"].cites,
            f"{EXPO}/test_svg.py::test_ut_io_06_svg_metadata_holds_the_stamp",
            f"{EXPO}/test_dxf.py::test_ut_io_06_dxf_header_comment_holds_the_stamp",
            f"{BUNDLE}::test_ut_io_06_report_carries_the_stamp",
            f"{BUNDLE}::test_ut_exp_04_readme_names_every_file_units_frame_and_caveat",
            f"{STAMP}::test_t07_project_json_holds_the_embodic_version_the_design_hash_and_a_utc_date",
        ),
    ),
    "REQ-L-01": Ruling(
        "checks",
        "Amended acceptance (U-D20). LG-08: no Thai in src, resources and templates. LG-01: every string literal of "
        "src passes the character rule with MODULE_SYMBOLS. The U-V13 gap DEF-UV13-01 is closed (U-M8k, D-062a): "
        "the product printer tests/static/lg_scan.py prints the sorted distinct words one per line, and a word "
        "planted in each catalogue and template appears in the list. The manual record of release 0.0.4 "
        "(LG-01_word_review_c25d8a9.md, indexed, passed) names its reviewer and read the 805 words, the same list "
        "the product printer prints (diff empty).",
        (
            f"{LGL}::test_lg01_string_literals_are_english",
            f"{LGL}::test_lg08_shipped_files_have_no_thai",
            f"{LGL}::test_lg01_word_list_holds_a_word_planted_in_every_catalogue_and_template",
            f"{LGL}::test_lg01_word_command_prints_the_list_one_word_per_line",
            "record:tests/independent/m4/records/LG-01_word_review_c25d8a9.md",
        ),
    ),
    "REQ-L-05": Ruling(
        "checks",
        "LG-06: the table records all five originals, every tracked brand-named image equals its recorded SHA-256, "
        "and a modified copy fails; the personal scan of src, tools, tests, packaging and resources and of every "
        "export kind finds 0 hits, with planted controls in every kind of text. The U-V13 gap is closed (U-M8p, "
        "D-068): tests/static/brand_assets.sha256 holds embodic-logo-white.png. That line comes from Fable's "
        "sha256sum of the user's original (D-068); U-V19 did not see the original, and no copy of that file is in "
        "the checkout, so the line guards a future copy only.",
        (
            f"{LGB}::test_lg06_brand_table_records_all_five_originals",
            f"{LGB}::test_lg06_every_tracked_brand_named_image_has_a_recorded_hash",
            f"{LGB}::test_lg06_brand_check_passes_an_exact_copy_and_fails_a_modified_copy",
            f"{LGB}::test_lg06_code_and_resources_carry_no_e_mail_address_home_path_or_personal_name",
            f"{LGB}::test_lg06_personal_scan_finds_a_planted_value_in_every_kind_of_text",
            f"{EXPO}/test_lg_exports.py::test_lg06_exports_carry_no_e_mail_address_home_path_or_personal_name",
        ),
    ),
    "REQ-F-03": _after_renames(
        "REQ-F-03",
        _v13,
        "Carried from U-V13 (its cites equal their 260191f pins on c25d8a9). U-M8y renames the UT-GEO-19 series tests "
        "to UT-GEO-26, the ID whose criterion they check (D-046c, U-V19_id_map.md).",
    ),
    "REQ-F-10": _after_renames(
        "REQ-F-10",
        _v18,
        "Carried from U-V18. U-M8y renames test_default_example_passes_drc to carry UT-DRC-01 (D-046c).",
    ),
    "REQ-F-14": _after_renames(
        "REQ-F-14",
        _v18,
        "Carried from U-V18. U-M8y renames the BV-05 test to carry BV-05 (D-046c).",
    ),
    "REQ-N-21": _after_renames(
        "REQ-N-21",
        _v18,
        "Carried from U-V18. U-M8y renames the two N-21 DXF joint tests to carry UT-EXP-02, whose 2026-10-17 "
        "revision they check (D-046c).",
    ),
}

PINS = json.loads(PIN_FILE.read_text(encoding="utf-8")) if PIN_FILE.is_file() else {}
