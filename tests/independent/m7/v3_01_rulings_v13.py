"""Agent 4's V3-01 re-ruling of every live must row on main 260191f (U-V13), after U-M7a-d and fix waves F1 to F6.

RULINGS: REQ id -> Ruling. It covers all 73 live must rows and replaces, on main, the rulings of v3_01_rulings.py,
v3_01_rulings_f.py and v3_01_rulings_ntl.py (those stay the rulings of the 0.0.1 release audit, req_audit.py).

- `checks`: every clause of the Acceptance cell is asserted by a cited test, gate or record. `cites` lists them as
  `path::function` (a pytest function; every collected item of it counts), `gate:<ID>` (a PASS line of the gate log
  that names the ID) or `record:<path>` (a record file). `v3_01_rerule.py --pin` hashes each cited function's source
  segment (interfaces.md section 3.2) and each record file into records/V3-01_pins_260191f.json.
- `partial` and `does not check`: `missing` is the one piece that would make the row `checks`, with `kind` (test,
  manual record, person's check, amendment, gate change) and `owner`.
- `reason` None means the reason of the earlier ruling still holds (the row's tests are unchanged or changed only in
  lines the ruling does not cite); the lever prints that earlier reason.

Every ruling is `verified` by reading the cited source on main 260191f; a missing part is `inferred` from a search of
the row's union (v3_01_union.py over a collect-only REQ report of 260191f, 4071 tests).
"""

from dataclasses import dataclass

BASE = "260191f"


@dataclass(frozen=True)
class Ruling:
    """One row's ruling on main BASE."""

    ruling: str
    reason: str | None
    cites: tuple[str, ...] = ()
    missing: str = ""
    kind: str = ""
    owner: str = ""


U = "tests/unit"
G = "tests/golden"
UI = "tests/ui"
GEN = f"{U}/generators"
PAIRS = f"{GEN}/test_spiral_pairs.py"
SPIRAL = f"{GEN}/test_spiral_generate.py"
PIPE = f"{U}/property/test_pipeline_properties.py"
KERN = f"{U}/physics/test_kernels.py"
NEWX = f"{UI}/qt_design/test_new_design_and_examples.py"
TOOL = f"{UI}/qt_shell/test_toolstrip_and_start.py"
EXPC = f"{U}/cli/test_export_command.py"
EXPO = f"{U}/embodic_io/exporters"
PROJ = f"{U}/embodic_io/project"
CHARTS = f"{UI}/qt_results/test_charts_compare_guide_export.py"
TR01 = f"{U}/base/test_tr01_release_gate.py"
LGW = "tests/static/test_lg_wording.py"
LGB = "tests/static/test_lg_brand_and_names.py"
N12 = f"{UI}/qt_shell/test_n12_tab_order.py"
N23 = f"{UI}/qt_shell/test_n23_high_contrast.py"
F11 = f"{G}/m2_physics/test_gr_f11_mass_thermal_current.py"
F34 = f"{G}/test_f34_drc_least_clearance.py"
STAMP = f"{EXPO}/test_stamp_fields.py"
TRACE = f"{U}/results/test_traceable.py"
REG = f"{U}/results/test_registry.py"
ORN = f"{U}/ui/results/test_oracle_dependency_note.py"
DISC = f"{U}/ui/results/test_disclosure_every_row.py"
RVM = f"{U}/ui/results/test_results_viewmodel.py"

RULINGS: dict[str, Ruling] = {
    "REQ-F-01": Ruling(
        "checks",
        None,
        (
            "tests/independent/m2/test_spiral.py::test_every_path_is_continuous_within_1e_6",
            f"{SPIRAL}::test_every_path_is_continuous",
            f"{PIPE}::test_pr_03_every_built_path_is_continuous",
            f"{SPIRAL}::test_ut_geo_03_layer_y_is_the_mirror_of_x",
            f"{PIPE}::test_pr_10_layer_y_mirrors_layer_x_about_every_coil_axis",
            f"{SPIRAL}::test_ut_geo_04_centre_via_terminates_x_and_y",
            f"{SPIRAL}::test_ut_geo_05_x_and_y_circulate_the_same_way",
        ),
    ),
    "REQ-F-02": Ruling(
        "checks",
        "(a) to (d) as U-V12a ruled. (e) k_w1 of every A2-TOP row equals Agent 4's Fraction-exact star of slots at abs "
        "1e-9 (test_winding_factors_exact.py l.37, gap F02-1 closed by U-M7a).",
        (
            f"{U}/winding/test_star_of_slots.py::test_ut_wnd_01_12_10_pattern_equals_d08_fig_3_7",
            f"{U}/winding/test_star_of_slots.py::test_ut_wnd_02_belt_edge_combinations_are_balanced",
            f"{U}/winding/test_star_of_slots.py::test_ut_wnd_03_12_16_pattern_all_positive",
            f"{U}/winding/test_plan.py::test_ut_wnd_04_16_16_with_all_phases_on_every_pair_is_unbuildable",
            f"{U}/winding/test_plan.py::test_ut_wnd_04_16_16_with_one_phase_per_pair_is_accepted",
            f"{U}/winding/test_winding_factors_exact.py::test_f02_1_kw1_of_every_a2_top_row_matches_the_exact_instrument_to_1e_9",
        ),
    ),
    "REQ-F-03": Ruling(
        "checks",
        "Amended acceptance (D-054b, c). (a) M1 builds (test_spiral_pairs.py l.52) and M2 builds its series groups "
        "(test_spiral_pairs.py l.104, CF-11 k = 3); (c) series EMF = phasor sum (test_ut_phy_07_series_chain.py). "
        "(b) one shared pi/Q rotation equals theta_0 + pi/Q within 1e-9 mm and differs from the unrotated board "
        "(l.169); two "
        "rotations, series and parallel, are refused at /winding/layers/pairs (l.193). (d) M4 16/16 is refused with "
        "UNBUILDABLE_SPIRAL_OPTION_NOT_IMPLEMENTED (l.211).",
        (
            f"{PAIRS}::test_ut_geo_10_parallel_pairs_put_one_route_per_pair_in_each_coil_group",
            f"{PAIRS}::test_ut_geo_19_series_groups_get_their_own_centre_via_one_pitch_apart",
            f"{U}/physics/test_ut_phy_07_series_chain.py::test_ut_phy_07_generated_series_board_phase_emf_is_the_sum_of_its_member_emfs_each_at_its_own_z",
            f"{PAIRS}::test_m3_a_rotation_every_pair_shares_turns_the_whole_winding",
            f"{PAIRS}::test_ut_geo_11_pairs_rotated_against_each_other_are_refused",
            f"{PAIRS}::test_m4_one_phase_per_pair_is_refused_until_phase_5",
        ),
    ),
    "REQ-F-04": Ruling(
        "checks",
        "As U-V12a ruled; re-read on 260191f: GR-07 case 3 now asserts the D-053a refusal "
        "(test_gr_07_case_3_a_board_thinner_than_its_copper_is_refused), outside the acceptance as before.",
        (
            f"{U}/model/test_stackup.py::test_copper_z_is_the_exact_sum_of_the_layers_above_plus_half_its_own",
            f"{U}/model/test_stackup.py::test_board_thickness_is_the_exact_sum_of_all_layers",
            f"{G}/m2_stackup/test_gr07_even_stackup.py::test_gr_07_custom_list_gives_the_copper_z_of_xcoil",
            f"{G}/m2_stackup/test_gr07_even_stackup.py::test_gr_07_auto_mode_helper_equals_xcoil_stackupfor",
            f"{G}/m2_stackup/test_gr07_even_stackup.py::test_gr_07_fixtures_hold_the_cases_of_the_specification",
        ),
    ),
    "REQ-F-05": Ruling(
        "partial",
        "Amended acceptance (D-054b). Count Q*v*(2k + 1): 36 vias for M1 (test_spiral_pairs.py l.69) and 2k + 1 per "
        "series coil (test_spiral_series_fan.py l.88); through vias clear foreign copper (test_spiral_pairs.py l.81, "
        "test_spiral_generate.py default and D08 DRC). 'Via resistance uses the count per transition' cannot be "
        "asserted: every topology refuses v != 1 (D-054d, test_every_topology_refuses.py), and only the kernel's "
        "barrel halving is tested (test_kernels.py, CF-04).",
        missing="Reword the UT-PHY-11 clause for v = 1 (other values refused with NOT_IMPLEMENTED until Phase 5), "
        "or move it to Phase 5 with D-054d.",
        kind="amendment",
        owner="Agent 6 (Fable rules)",
    ),
    "REQ-F-06": Ruling(
        "partial",
        "Amended acceptance (D-054b). (a) D08 3 loops with the half closing (test_spiral_turns.py OR-04). (b) sharp "
        "length equals the reference at rel 1e-6 (test_spiral_length.py l.56) and at abs 1e-6 mm "
        "(test_spiral_length_abs.py, F06-1); per corner the fillet change equals the line-arc closed form at 1e-9 mm "
        "and "
        "the filleted track equals sharp plus the corner forms at 1e-9 mm, on CF-11 rho 0.5 and D08 rho 1.0 "
        "(test_spiral_fillet_length.py l.122, l.137). The stated totals 362.6419 mm (CF-11, rho 0.5) and 150.1692 mm "
        "(CF-10, rho 1.0) are asserted nowhere, and CF-10 is not a case.",
        missing="Assert the filleted track length 362.6419 mm (CF-11, rho 0.5 mm) and 150.1692 mm (CF-10, rho 1.0 "
        "mm) within 1e-6 relative, with rho_used read from the detail (gap F06-3, V3-01.md).",
        kind="test",
        owner="Agent 3",
    ),
    "REQ-F-07": Ruling(
        "checks",
        None,
        (
            f"{KERN}::test_ut_phy_02_block_magnet_pole_arc_ratio",
            f"{KERN}::test_cf01_field_fundamental_equals_the_1d_magnetic_circuit",
        ),
    ),
    "REQ-F-08": Ruling(
        "partial",
        "The 12/14 delta RANGE_DELTA_TRIPLEN warning and its absence otherwise carry REQ-F-08 (test_plan.py "
        "UT-WND-07). "
        "Ke_LL = sqrt(3) Ke_ph in star and = Ke_ph in delta is asserted only by CF-06 (test_kernels.py), which carries "
        "REQ-F-11, not REQ-F-08; interfaces.md section 3.2 lets a ruling cite only tests with the row's marker.",
        (
            f"{KERN}::test_cf06_star_and_delta_constants",
            f"{U}/winding/test_plan.py::test_ut_wnd_07_delta_with_triplen_winding_factor_warns",
            f"{U}/winding/test_plan.py::test_ut_wnd_07_no_triplen_warning",
        ),
        missing="Add REQ-F-08 to the marker of test_kernels.py::test_cf06_star_and_delta_constants (no new assertion).",
        kind="test (marker)",
        owner="Agent 3",
    ),
    "REQ-F-10": Ruling(
        "partial",
        "(b) to (d) as U-V12a ruled (PR-01, UT-DRC-03, GR-18; test_run_drc.py gained only the DEF-M7a-01 grid tests). "
        "(a) the default spiral packs within rule + 0.005 mm is asserted by test_default_example_passes_drc, which "
        "carries REQ-F-05, not REQ-F-10 (interfaces.md section 3.2).",
        (
            f"{SPIRAL}::test_default_example_passes_drc",
            f"{U}/drc/test_properties.py::test_pr_01_drc_never_under_reports_and_reports_no_false_positive_on_200_random_sets",
            f"{U}/drc/test_run_drc.py::test_ut_drc_03_one_micron_intrusion_is_exactly_one_new_violation_at_its_place",
            f"{G}/m1_drc/test_gr18_band_rule.py::test_gr18_run_drc_agrees_with_xcoil_outside_the_slack_band",
        ),
        missing="Add REQ-F-10 to the marker of test_spiral_generate.py::test_default_example_passes_drc (UT-DRC-01).",
        kind="test (marker)",
        owner="Agent 3",
    ),
    "REQ-F-11": Ruling(
        "partial",
        "(i) F11-1 is closed: EQT-16-GR, EQT-17-GR, EQT-19-GR and EQT-22-GR compare with Xcoil's massThermal and "
        "applyConnection fixtures (test_gr_f11_mass_thermal_current.py, KERNEL and INTEGRATED classes, no xfail). A "
        "scripted check of the registry against the eqt markers of the 260191f collection finds four registry test IDs "
        "carried by no test: EQT-14-O2 (an oracle, allowed as xfail by (ii)), EQT-27-GR, EQT-28-GR and EQT-29-GR. "
        "EQ-28 and EQ-29 have no port in src (eqt_map_review.md l.240-241), so no dump exists to compare. EQ-27 is "
        "used (winding_factor_1, inductance_estimate) and has no golden comparison; U-V12a missed it (correction).",
        missing="EQT-27-GR: a dump of Xcoil's utilisation factor from analyze, analyzeWave and analyzeElements and a "
        "golden comparison of winding_factor_1 (eqt_map_review.md l.239).",
        kind="test",
        owner="Agent 3 (dumper), Agent 2 (tolerance)",
    ),
    "REQ-F-12": Ruling(
        "partial",
        "Two-member identity at rel 1e-12 (CF-07, which carries REQ-F-11, not REQ-F-12). C1d per-layer B1 0.6828 / "
        "0.6813 / 0.6805 T mirrored, rel 1e-4, and "
        "the 0.336 % spread (test_field_layer_spread.py, F12-1 closed).",
        (
            f"{U}/physics/test_closed_forms_m2e2.py::test_eq07_cf07_two_member_group_with_half_ohm_members",
            f"{U}/physics/test_field_layer_spread.py::test_ut_phy_20_b1_of_each_copper_layer_matches_c1d",
            f"{U}/physics/test_field_layer_spread.py::test_ut_phy_20_b1_spread_over_the_layers_is_0_336_percent",
        ),
        missing="Add REQ-F-12 to the marker of "
        "test_closed_forms_m2e2.py::test_eq07_cf07_two_member_group_with_half_ohm_"
        "members (UT-PHY-08).",
        kind="test (marker)",
        owner="Agent 3",
    ),
    "REQ-F-13": Ruling(
        "checks",
        "Each view of the statement is visible after at most 2 interactions from the D08 start view "
        "(test_f13_view_reach.py, F13-1); zoom reaches 200x and 0.1x as literals (test_zoom_range_literals.py, F13-2); "
        "copper pens stay in mm at every zoom (test_theme_and_geometry.py UI-03).",
        (
            f"{UI}/qt_e2e/test_f13_view_reach.py::test_f13_1_every_view_is_visible_after_at_most_two_interactions",
            f"{UI}/qt_e2e/test_f13_view_reach.py::test_f13_1_the_phase_and_layer_pages_are_hidden_until_their_tab_is_clicked",
            f"{UI}/qt_shell/test_zoom_range_literals.py::test_f13_2_zoom_range_is_01x_to_200x",
            f"{UI}/qt_shell/test_theme_and_geometry.py::test_ui03_zoom_stays_between_01x_and_200x_and_copper_width_stays_in_millimetres",
        ),
    ),
    "REQ-F-14": Ruling(
        "partial",
        "Every BV case gives its code (BV-01, 02, 03, 06; BV-05 is test_spiral_bounds.py, which carries REQ-F-19, not "
        "REQ-F-14). 1000 seeded drafts per generator: no INTERNAL_ code and no non-finite number that a "
        "RANGE_NON_FINITE_RESULT issue does not name (test_seeded_drafts_all_topologies.py, slow, F14-1). '0 "
        "non-finite results' is read as 'no silent non-finite result' (D-007), the reading of gap "
        "F14-1 (`assumption`, Fable confirms).",
        (
            f"{U}/boundary/test_bv_design.py::test_bv01_trace_width",
            f"{U}/boundary/test_bv_design.py::test_bv02_spiral_radius_order",
            f"{U}/boundary/test_bv_design.py::test_bv03_odd_pole_count_suggests_the_next_even_count",
            f"{U}/boundary/test_bv_design.py::test_bv06_pair_references_unknown_copper_layer",
            f"{GEN}/test_spiral_bounds.py::test_requested_turns_above_the_turns_that_fit_are_refused_as_the_users_request",
            f"{U}/property/test_seeded_drafts_all_topologies.py::test_f14_1_seeded_drafts_return_an_outcome_without_internal_errors_or_unnamed_non_finite_numbers",
        ),
        missing="Add REQ-F-14 to the marker of "
        "test_spiral_bounds.py::test_requested_turns_above_the_turns_that_fit_are_"
        "refused_as_the_users_request (BV-05).",
        kind="test (marker)",
        owner="Agent 3",
    ),
    "REQ-F-15": Ruling(
        "checks",
        "Save, load, save byte identity on every packaged example; hash equality iff design equality on spiral, "
        "serpentine and wave pairs; any winding field change changes the hash (test_hash_all_topologies.py, F15-1); "
        "the "
        "draft round trip keeps the missing list (UT-IO-07).",
        (
            f"{PROJ}/test_project.py::test_ut_io_01_save_load_save_is_byte_identical",
            f"{PROJ}/test_project.py::test_ut_io_07_incomplete_draft_loads_with_the_same_missing_list",
            f"{PIPE}::test_pr_08_hash_changes_iff_the_design_changes",
            f"{PROJ}/test_hash_all_topologies.py::test_f15_1_serpentine_hashes_agree_exactly_when_designs_are_equal",
            f"{PROJ}/test_hash_all_topologies.py::test_f15_1_wave_hashes_agree_exactly_when_designs_are_equal",
            f"{PROJ}/test_hash_all_topologies.py::test_f15_1_changing_any_winding_field_changes_the_hash",
            f"{PROJ}/test_hash_all_topologies.py::test_f15_1_save_load_save_is_byte_identical_for_every_packaged_example",
        ),
    ),
    "REQ-F-16": Ruling(
        "checks",
        "ezdxf audits every DXF part with 0 errors and counts equal the Layout; the SVG parses with counts equal the "
        "Layout; pypdf reads 'Key results'; the bundle's project file validates against project.v2 and loads back to "
        "the computed design hash (test_bundle_project_file.py, F16-1).",
        (
            f"{EXPO}/test_dxf.py::test_ut_exp_02_complete_dxf_counts_equal_the_layout",
            f"{EXPO}/test_dxf.py::test_ut_exp_02_outline_dxf_is_closed_outline_and_bore_only",
            f"{EXPO}/test_dxf.py::test_ut_exp_02_screws_dxf_is_circles_only",
            f"{EXPO}/test_svg.py::test_ut_exp_01_svg_counts_equal_the_layout",
            f"{EXPO}/test_report_readme_bundle.py::test_ut_exp_03_report_every_value_has_unit_and_status",
            f"{EXPO}/test_bundle_project_file.py::test_f16_1_the_bundle_project_file_validates_and_loads_back_to_the_computed_design",
        ),
    ),
    "REQ-F-18": Ruling(
        "checks",
        "compute --json equals the facade outcome; a draft exits 1 with the missing pointers; export with DRC errors "
        "is "
        "refused without the flag (the test now carries REQ-F-18, F18-1) and writes with --allow-drc-errors.",
        (
            f"{U}/cli/test_compute_command.py::test_compute_json_equals_the_facade_outcome",
            f"{U}/cli/test_exit_codes.py::test_exit_1_an_incomplete_draft_lists_the_missing_pointers",
            f"{EXPC}::test_a_failed_drc_refuses_drawings_and_the_bundle_without_confirmation",
            f"{EXPC}::test_every_format_of_every_example_is_written_and_readable",
        ),
    ),
    "REQ-F-19": Ruling(
        "checks",
        "A stub registered at runtime passes DRC, analysis and the board dump, and every exporter writes its stack "
        "byte-identical to the shipped generator's (F19-1); the C1 layer rule is the import-contract gate (MT-01).",
        (
            f"{GEN}/test_generator_interface.py::test_ut_geo_20_a_generator_registered_at_runtime_passes_drc_physics_and_the_board_dump",
            f"{GEN}/test_generator_interface.py::test_f19_1_every_exporter_writes_the_stub_generators_stack_as_it_writes_the_shipped_one",
            "gate:MT-01",
        ),
    ),
    "REQ-F-21": Ruling(
        "checks",
        None,
        (
            f"{TOOL}::test_ui23_window_opens_empty_with_new_design_and_examples_and_runs_no_compute",
            f"{NEWX}::test_ui22_example_load_marks_every_field_example_and_set_back_restores_it",
            f"{U}/ui/session/test_session_state_machine.py::test_ui22_example_chips_turn_user_on_edit_and_return_when_set_back",
            f"{PIPE}::test_pr_12_badges_do_not_depend_on_provenance_and_reentry_changes_nothing",
        ),
    ),
    "REQ-F-23": Ruling(
        "checks",
        "The clamp notice with old and new value and Undo (UI-15); compute keeps the out-of-range design unchanged and "
        "reports RANGE_ABOVE_SUPPORTED with suggestion 50 (test_compute_keeps_the_design.py, F23-1).",
        (
            f"{UI}/qt_design/test_editing.py::test_ui15_no_silent_rewrite_the_suggestion_applies_only_on_apply_with_notice_and_undo",
            f"{U}/api/test_compute_keeps_the_design.py::test_f23_1_a_value_above_the_supported_range_is_reported_and_never_clamped_in_the_outcome",
        ),
    ),
    "REQ-F-32": Ruling(
        "checks",
        None,
        (
            f"{NEWX}::test_ui28_visible_inputs_equal_field_specs_filtered_by_applicability",
            f"{NEWX}::test_ui28_an_option_blocked_by_a_sibling_is_disabled_with_the_reason",
        ),
    ),
    "REQ-F-33": Ruling(
        "checks",
        "As U-V12a ruled; re-read on 260191f: test_export_command.py changed only the marker of the refusal test.",
        (
            f"{CHARTS}::test_ui29_export_with_drc_failures_lists_them_with_focus_on_cancel",
            f"{EXPC}::test_a_failed_drc_refuses_drawings_and_the_bundle_without_confirmation",
            f"{EXPC}::test_allow_drc_errors_writes_the_file_and_warns",
        ),
    ),
    "REQ-F-34": Ruling(
        "checks",
        "Board by board copper and vias against Xcoil, one board per phase without cross-board violations, 200 inputs "
        "per helper (U-V12a), and now least trace-trace, trace-via and via-via clearances of every GR-20 board equal "
        "Agent 4's arc-exact sweep within 1e-6 mm with the D-006 verdict (test_f34_drc_least_clearance.py, slow).",
        (
            f"{G}/m3_serpentine/test_gr20_layouts.py::test_gr20_copper_matches_xcoil_layer_by_layer",
            f"{G}/m3_serpentine/test_gr20_layouts.py::test_gr20_vias_match_xcoil",
            f"{GEN}/serpentine/test_serpentine_generator.py::test_ut_gen_05_one_board_per_phase",
            f"{GEN}/serpentine/test_serpentine_generator.py::test_ut_gen_05_a_via_of_one_board_never_meets_the_copper_of_another",
            f"{G}/m3_serpentine/test_gr23_helpers.py::test_gr23_every_helper_has_200_inputs_and_exercises_each_branch",
            f"{F34}::test_f34_1_serpentine_least_clearances_equal_the_arc_exact_sweep",
        ),
    ),
    "REQ-F-35": Ruling(
        "checks",
        "Every wave style with 2, 4 and 6 layers and every primitive against Xcoil; EMF at rel 1e-9 and resistance up "
        "to the named via-length cause (GR-22); the GR-20 DRC criterion on every GR-21 case (test_f34, slow).",
        (
            f"{G}/m3_wave/test_gr21_layouts.py::test_gr21_covers_every_style_with_two_four_and_six_layers_and_one_to_three_phases",
            f"{G}/m3_wave/test_gr21_layouts.py::test_gr21_every_primitive_matches_xcoil",
            f"{G}/m3_wave/test_gr22_results.py::test_gr22_ke_per_phase_and_eddy_loss_match_xcoil",
            f"{G}/m3_wave/test_gr22_results.py::test_gr22_phase_resistance_differs_from_xcoil_only_by_the_via_barrel_length",
            f"{F34}::test_f34_1_wave_least_clearances_equal_the_arc_exact_sweep",
        ),
    ),
    "REQ-F-36": Ruling(
        "checks",
        None,
        (f"{NEWX}::test_ui24_blank_design_computes_once_when_the_last_required_field_is_filled",),
    ),
    "REQ-F-37": Ruling(
        "checks",
        "parse_draft gives the exact blank lists for spiral (test_draft.py) and, as hand-written literals, for "
        "serpentine and wave (test_draft_blank_lists.py, F37-1); INVALID issues beside missing fields; every example "
        "round-trips through draft_from_design.",
        (
            f"{U}/model/test_draft.py::test_blank_spiral_draft_lists_every_required_pointer_in_form_order",
            f"{U}/model/test_draft.py::test_filling_the_last_required_field_gives_the_design",
            f"{U}/model/test_draft.py::test_invalid_present_value_is_an_issue_alongside_missing_fields",
            f"{U}/model/test_draft.py::test_draft_round_trip_is_exact",
            f"{U}/model/test_draft_blank_lists.py::test_f37_1_blank_serpentine_and_wave_drafts_list_every_required_pointer_in_form_order",
        ),
    ),
    "REQ-F-38": Ruling(
        "checks",
        "Every chip reads `example` after a load, /name equals the display title, and the first Save after an example "
        "opens a modal Save As and leaves the packaged file byte-identical (test_f38_first_save.py, F38-1).",
        (
            f"{NEWX}::test_ui22_example_load_marks_every_field_example_and_set_back_restores_it",
            f"{U}/ui/session/test_session_state_machine.py::test_ui22_example_chips_turn_user_on_edit_and_return_when_set_back",
            f"{PROJ}/test_examples.py::test_d_041b_each_example_design_is_named_by_its_display_title",
            f"{UI}/qt_e2e/test_f38_first_save.py::test_f38_1_first_save_after_an_example_opens_save_as_and_leaves_the_packaged_file_alone",
        ),
    ),
    "REQ-F-39": Ruling(
        "checks",
        None,
        (
            f"{TOOL}::test_ui25_every_action_has_label_tooltip_accessible_name_and_a_resolved_command",
            f"{TOOL}::test_ui25_a_command_no_view_model_offers_is_a_startup_error",
            f"{TOOL}::test_ui25_every_toolstrip_action_has_its_icon_file",
            f"{TOOL}::test_ui25_arrow_keys_move_focus_within_a_tab_and_wrap",
            f"{TOOL}::test_ui25_icons_recolour_after_a_theme_switch",
        ),
    ),
    "REQ-F-40": Ruling(
        "checks",
        None,
        (
            f"{U}/embodic_io/board_dump/test_board_dump.py::test_board_dump_write_read_write_is_byte_identical",
            f"{U}/embodic_io/board_dump/test_board_dump.py::test_board_dump_tags_non_finite_numbers_and_rejects_bare_tokens",
            f"{G}/m1_layout/test_gr19_layouts.py::test_gr19_write_read_write_is_byte_identical",
        ),
    ),
    "REQ-N-01": Ruling(
        "partial",
        "The budget verdict is tested on synthetic numbers (test_n01_pf01_budgets.py, strict bounds 1.0 / 0.2 / 0.4 / "
        "0.3 s); the measuring test is `manual` and skips unless selected, and the acceptance keeps the row "
        "`assumption` until it runs on the user's laptop.",
        missing="Run `pytest -m manual tests/performance/test_n01_pf01_budgets.py` on the user's laptop and index the "
        "record (manual_records.json, test_id PF-01).",
        kind="manual record",
        owner="Fable with the user (laptop)",
    ),
    "REQ-N-02": Ruling(
        "partial",
        "UI-05 (100 ms during a 3 s compute) and N02-1 to N02-10: one preview 300 ms +/- 50 ms after the last "
        "textEdited, commit without a second compute, Return, Esc, cancellation, choices, toolstrip commit "
        "(test_n02_typing_preview.py, UI-36 to UI-45). The second UX-AC-22 sentence (within 300 ms the results update "
        "for the default example or show 'Updating' with the previous values dimmed) is asserted by no test of the "
        "union; N02-10 reports an echo gap only.",
        missing="A Qt test on spiral_12c16p_default: from the commit (or the timer firing) to the results update is "
        "at most 300 ms, or 'Updating' shows with the previous values dimmed (the UX-AC-15 dim tokens).",
        kind="test",
        owner="Agent 3",
    ),
    "REQ-N-04": Ruling(
        "partial",
        None,
        missing="PK-04 on Windows with the D-051f rule (arrays at 1e-9 of their largest magnitude, design_hash exact, "
        "layout_hash, stack_hash and pairs_checked left out), recorded and indexed.",
        kind="manual record",
        owner="Fable (Windows laptop)",
    ),
    "REQ-N-05": Ruling(
        "partial",
        None,
        missing="A clean venv on Windows 11 x64 with Python 3.11 and on Linux with Python 3.12 and 3.13 installs from "
        "the lock file and `embodic-cli selftest` exits 0, recorded and indexed.",
        kind="manual record",
        owner="Fable (Windows); Agent 4 (Linux 3.12 and 3.13)",
    ),
    "REQ-N-06": Ruling(
        "partial",
        "Two wheel builds are identical (PK-03). tools/build_bundle.py exists, so the stretch unit landed, but no "
        "profile of tools/ci.py builds the bundle and tests/bundle/test_bundle_smoke.py skips without one (5 skipped "
        "in the commit gate log of 5099401).",
        missing="The release profile builds the PyInstaller folder and runs tests/bundle against it with none skipped; "
        "PK-05 on the Windows folder.",
        kind="gate change",
        owner="Agent 3 (tools/ci.py), Fable (PK-05 on Windows)",
    ),
    "REQ-N-07": Ruling(
        "checks",
        "D-053c rules the row covered by the passed records: Linux cold PK-06 (U-V5) and Windows warm cache 21.6 s "
        "(Fable); the cold Windows run failed only on a 0.03 MB/s network and is stated in the report to the user.",
        (
            "record:tests/independent/m5/records/PK-06_walkthrough.md",
            "record:docs/phase3/fable/windows_campaign_w1.md",
        ),
    ),
    "REQ-N-08": Ruling("checks", None, ("gate:MT-01", "gate:MT-02", "gate:MT-03")),
    "REQ-N-09": Ruling(
        "partial",
        "The checker needs an EQ-ID per physics function (MT-04) and now a unit or `dimensionless` in every numeric "
        "Parameters entry of a public module-level physics function, with controls (test_n09_parameter_units.py). "
        "The unit of the Returns entry is not checked.",
        missing="Extend test_n09 to the Returns entry of a numeric return value (a unit token or `dimensionless`), "
        "with a planted control.",
        kind="test",
        owner="Agent 3",
    ),
    "REQ-N-10": Ruling(
        "partial",
        "Amended (D-053b, coverage moved to Phase 5). The release profile passes --fail-untested-through M5 with the "
        "manual-record index; the gate exits 1 on a live must row without a passing test or a passed record and passes "
        "when a record covers it (test_tr01_release_gate.py). No test on main carries REQ-N-10 (0 of 4071 collected), "
        "so the release gate itself lists REQ-N-10 as untested (DEF-UV13-03).",
        (
            f"{TR01}::test_tr01_release_gate_fails_on_an_untested_must_row",
            f"{TR01}::test_tr01_release_gate_passes_when_a_manual_record_covers_the_row",
            f"{TR01}::test_tr01_flag_lists_a_live_must_row_that_has_neither_a_passing_test_nor_a_manual_record",
        ),
        missing="Add REQ-N-10 to the marker of the TR-01 release-gate tests in "
        "tests/unit/base/test_tr01_release_gate.py "
        "(DEF-UV13-03).",
        kind="test (marker)",
        owner="Agent 3",
    ),
    "REQ-N-11": Ruling(
        "checks",
        None,
        (f"{U}/ui/shell/test_contrast_check.py::test_ax01_ax09_every_pair_of_both_shipped_themes_passes",),
    ),
    "REQ-N-12": Ruling(
        "checks",
        "Keyboard-only scenario (AX-02), a focus ring on every focusable control (AX-03), and Tab order equal to the "
        "visual order inside each region with regions in F6 order, on every inspector tab, a second topology and the "
        "compact height (test_n12_tab_order.py, gap N-12 closed by U-M7c and U-M8a).",
        (
            f"{UI}/qt_e2e/test_ax02_keyboard_only.py::test_ax02_open_edit_three_inputs_recompute_open_eq_details_and_export_svg_with_the_keyboard_only",
            f"{UI}/qt_shell/test_focus_ring.py::test_ax03_every_focusable_control_shows_a_focus_ring",
            f"{N12}::test_n12_inside_each_region_tab_moves_down_then_right",
            f"{N12}::test_n12_regions_follow_the_f6_order",
            f"{N12}::test_n12_every_inspector_tab_is_walked_in_visual_and_f6_order",
            f"{N12}::test_n12_a_second_design_of_another_topology_keeps_the_order",
        ),
    ),
    "REQ-N-13": Ruling(
        "checks",
        None,
        (
            f"{UI}/qt_e2e/test_ax04_target_size.py::test_ax04_every_interactive_widget_reaches_24_px_and_check_rows_32_px",
        ),
    ),
    "REQ-N-14": Ruling("checks", None, ("record:tests/independent/m4/records/AX-05.md",)),
    "REQ-N-15": Ruling(
        "checks",
        "No clipped text, no overlapping siblings and no sideways form scroll at QT_SCALE_FACTOR 1, 1.5 and 2 and "
        "three "
        "window sizes (test_n15_layout_at_scale.py, D08); every inspector form of all five examples fits its viewport "
        "at 960 x 540, 1280 x 800 and 1920 x 1080 (test_n15_inspector_fits.py, N15-1). I read the every-example clause "
        "as the N15-1 form rule the same cell defines (`inferred`).",
        (
            f"{UI}/qt_e2e/test_n15_layout_at_scale.py::test_n15_no_text_is_clipped_and_no_sibling_widgets_overlap",
            f"{UI}/qt_e2e/test_n15_layout_at_scale.py::test_n15_no_form_shows_a_horizontal_scroll_bar_with_a_range",
            f"{UI}/qt_shell/test_n15_inspector_fits.py::test_n15_1_and_2_every_inspector_form_fits_and_no_combo_box_is_narrower_than_its_hint",
        ),
    ),
    "REQ-N-16": Ruling(
        "partial",
        None,
        missing="Narrator on Windows with D08 open: each input announces label, value and unit, each result card "
        "value, "
        "unit and status; record and index it (AX-06). The Linux proxy (AX-06.md) leaves Narrator `not tested`.",
        kind="person's check",
        owner="Fable with the user (Windows)",
    ),
    "REQ-N-17": Ruling(
        "checks",
        "src imports no network module (PK-07 with its control), and every test runs with socket connect and "
        "create_connection refused by an autouse fixture of tests/conftest.py, with the socketpair exception of D-055d "
        "(test_n17_network_guard.py). A subprocess a test starts is not guarded (`inferred` from the fixture).",
        (
            "tests/static/test_pk07_no_network.py::test_pk07_src_imports_no_network_module",
            "tests/static/test_pk07_no_network.py::test_pk07_flags_each_planted_network_import",
            "tests/static/test_n17_network_guard.py::test_n17_a_connect_to_a_local_port_is_refused_by_the_guard_not_by_the_network",
            "tests/static/test_n17_network_guard.py::test_n17_create_connection_is_refused_by_the_guard",
            "tests/static/test_n17_network_guard.py::test_n17_a_direct_connect_to_a_listening_loopback_port_is_still_refused",
        ),
    ),
    "REQ-N-18": Ruling(
        "checks",
        None,
        (f"{UI}/qt_shell/test_worker_and_errors.py::test_ui12_an_exception_in_a_gui_slot_also_saves_and_explains",),
    ),
    "REQ-N-19": Ruling(
        "checks",
        None,
        (
            "tests/packaging/test_pk08_licences.py::test_pk08_the_runtime_closure_carries_only_allowed_licences",
            "tests/packaging/test_pk08_licences.py::test_pk08_third_party_licences_has_every_component_and_the_full_texts",
            "tests/packaging/test_pk08_licences.py::test_pk08_every_declared_requirement_has_a_licence_row",
        ),
    ),
    "REQ-N-21": Ruling(
        "checks",
        "Unit round trips within 2 ulp, js_round on ties of both signs, the quantiser, UT-GEO-22 and UT-GEO-23; "
        "after SVG "
        "and DXF writing every copper joint is one written point, and DXF ARC joints are continuous within "
        "COINCIDENCE_MM (test_n21_joint_continuity.py, D-055c).",
        (
            f"{U}/base/test_units.py::test_units_round_trips_stay_within_two_ulps",
            f"{U}/base/test_units.py::test_units_js_round_matches_javascript_math_round",
            f"{U}/base/test_units.py::test_units_quantise_matches_xcoil_fmt",
            f"{U}/geometry/test_transforms.py::test_ut_geo_22_rotation_by_60_degrees_matches_closed_form",
            f"{U}/geometry/test_discretise.py::test_ut_geo_23_chords_respect_every_bound",
            f"{EXPO}/test_n21_joint_continuity.py::test_n21_svg_writes_one_point_for_every_copper_joint",
            f"{EXPO}/test_n21_joint_continuity.py::test_n21_dxf_writes_one_point_for_every_line_to_line_joint",
            f"{EXPO}/test_n21_joint_continuity.py::test_n21_dxf_arc_joints_are_continuous_within_the_coincidence_bound",
        ),
    ),
    "REQ-N-23": Ruling(
        "checks",
        "Greyscale mode keeps every label; the eye never reaches copper; a high-contrast (forced-colours) run forces "
        "greyscale and hatch, takes the system colour pair and restores the theme (test_n23_high_contrast.py, N23-1 to "
        "N23-6).",
        (
            f"{UI}/qt_shell/test_theme_and_geometry.py::test_ui27_both_render_modes_draw_phase_colour_or_grey_and_keep_every_label",
            f"{U}/ui/shell/test_outcome_viewmodel.py::test_ui27_every_top_layer_coil_has_a_label_and_an_eye_that_never_reaches_copper",
            f"{N23}::test_n23_1_high_contrast_forces_greyscale_and_disables_the_toggle",
            f"{N23}::test_n23_2_the_sheet_is_the_dark_sheet_in_system_colours",
            f"{N23}::test_n23_4_the_drawing_is_dark_greyscale_with_every_label_and_eye",
            f"{N23}::test_n23_5_turning_high_contrast_off_restores_the_theme_and_the_chosen_mode",
        ),
    ),
    "REQ-N-24": Ruling(
        "partial",
        "Every unit input of the field table shows its unit and has it in its accessible description, on all three "
        "topologies (test_n24_unit_announcement.py). The cells of `layer-list` and `screw-table` are left out: they "
        "hold the unit in a column header and have no per-cell description (the test's docstring).",
        missing="A ruling whether a column-header unit satisfies 'include it in its accessible description' for table "
        "cells; otherwise a per-cell description and the test extended to both tables (DEF-UV13-02).",
        kind="test",
        owner="Agent 1 (ruling), Agent 3",
    ),
    "REQ-N-25": Ruling(
        "checks",
        "Back-EMF chart: one unit, legend, end labels, data table and badge; torque and power charts toggle a data "
        "table whose rows equal the x count, with rpm and unit headers, and carry a direct end label "
        "(test_n25_torque_power_data_table.py, gap N-25 closed).",
        (
            f"{CHARTS}::test_ui30_back_emf_chart_has_one_unit_legend_end_labels_data_table_and_badge",
            f"{UI}/qt_results/test_n25_torque_power_data_table.py::test_n25_each_torque_and_power_chart_toggles_a_data_table_with_units_and_has_an_end_label",
        ),
    ),
    "REQ-N-27": Ruling(
        "checks",
        "Every chrome token in both theme files; the choice persists after a restart; a runtime switch to dark "
        "leaves no "
        "light-only colour in any visible widget's palette or style sheet (test_n27, gap N-27 closed).",
        (
            f"{U}/ui/shell/test_theme.py::test_ui26_both_theme_files_load_with_every_chrome_token_and_the_spec_phase_colours",
            f"{UI}/qt_shell/test_theme_and_geometry.py::test_ui26_the_theme_choice_persists_after_a_restart",
            f"{UI}/qt_shell/test_n27_dark_switch_leaves_no_light_colour.py::test_n27_a_runtime_switch_to_dark_leaves_no_light_colour_in_any_visible_widget",
        ),
    ),
    "REQ-N-28": Ruling(
        "checks",
        "Phase colours at 3:1 on the canvas in both themes (contrast pairs); labels in both render modes; the palette "
        "validator reproduces the published table and passes every phase pair and grey step of both themes "
        "(test_n28_palette_separation.py, gap N-28 closed).",
        (
            f"{U}/ui/shell/test_contrast_check.py::test_ax01_ax09_every_pair_of_both_shipped_themes_passes",
            f"{UI}/qt_shell/test_theme_and_geometry.py::test_ui27_both_render_modes_draw_phase_colour_or_grey_and_keep_every_label",
            f"{U}/ui/shell/test_n28_palette_separation.py::test_n28_the_instrument_reproduces_the_published_table",
            f"{U}/ui/shell/test_n28_palette_separation.py::test_n28_every_phase_pair_and_grey_step_of_a_shipped_theme_is_separated",
        ),
    ),
    "REQ-T-01": Ruling(
        "checks",
        "Unit and badge on every card; all 30 D08 cards show an EQ chip with their chain, a result without an EQ-ID a "
        "kind tag; Tab then Space opens the details of each of the 30 cards (test_t01_every_card.py, gap T-01 closed).",
        (
            f"{UI}/qt_results/test_results_and_checks.py::test_ui06_results_tab_shows_one_card_per_quantity_with_value_unit_badge_eq_and_tag",
            f"{UI}/qt_results/test_t01_every_card.py::test_t01_all_30_cards_show_an_eq_chip_and_its_chain",
            f"{UI}/qt_results/test_t01_every_card.py::test_t01_a_result_without_an_eq_id_shows_a_kind_tag_and_never_nothing",
            f"{UI}/qt_results/test_t01_every_card.py::test_t01_tab_then_space_opens_the_details_of_each_of_the_30_cards",
        ),
    ),
    "REQ-T-02": Ruling(
        "checks",
        "For every packaged example the computed AnalysisResult holds no bare number, every EQ-ID resolves or the "
        "value carries a kind tag, every evidence ID resolves, and the walk reports a planted bare float and unknown "
        "ID "
        "(test_real_examples_traceability.py, gap T-02 closed).",
        (
            f"{U}/results/test_real_examples_traceability.py::test_t02_every_number_of_every_example_is_a_traceable",
            f"{U}/results/test_real_examples_traceability.py::test_t02_every_eq_id_resolves_or_the_value_carries_a_kind_tag",
            f"{U}/results/test_real_examples_traceability.py::test_t02_every_evidence_id_resolves",
            f"{U}/results/test_real_examples_traceability.py::test_t02_the_walk_reports_a_bare_float_and_an_unknown_id_that_it_is_given",
        ),
    ),
    "REQ-T-03": Ruling(
        "checks",
        "As U-V12b ruled; re-read on 260191f: test_traceable.py gained chain and flag tests only, and the tag test "
        "moved "
        "from l.88 to l.95.",
        (
            f"{U}/results/test_status.py::test_status_badge_truth_table",
            f"{TRACE}::test_traceable_tag_lists_exactly_the_assumed_inputs_dominant_first",
        ),
    ),
    "REQ-T-04": Ruling(
        "checks",
        None,
        (
            f"{REG}::test_tr04_every_eq_and_ev_id_in_source_code_exists_in_the_registry",
            f"{REG}::test_registry_packaged_issues_are_exactly_the_known_gaps",
            f"{REG}::test_registry_missing_evidence_is_an_issue_not_an_exception",
            f"{REG}::test_tr04_registry_test_links_belong_to_their_equation",
        ),
    ),
    "REQ-T-05": Ruling(
        "partial",
        "record_main in the release profile exits 1 and names the one verified equation whose only or one of several "
        "linked tests did not pass, and writes no evidence file (test_record_passed_tests_gate.py, D-055b, D-056a). "
        "The assertions read stdout and stderr together and do not check the list of registry test IDs that passed, "
        "which the amended acceptance requires on stderr.",
        missing="Assert that stderr (alone) names the equation and the registry test IDs of it that passed in the run.",
        kind="test",
        owner="Agent 3",
    ),
    "REQ-T-06": Ruling(
        "checks",
        "B_r marked measured with a source leaves the assumed inputs of every quantity and the count drops by one, on "
        "D08 and serpentine; without a source the mark is refused with INVALID_MEASURED_SOURCE_EMPTY; design fields "
        "are "
        "refused (test_measured_retires_assumption.py, gap T-06 closed).",
        (
            f"{U}/results/test_measured_retires_assumption.py::test_t06_marking_br_measured_with_a_source_removes_it_from_the_assumed_inputs",
            f"{U}/results/test_measured_retires_assumption.py::test_t06_marking_br_measured_without_a_source_is_refused_and_the_assumption_stays",
            f"{U}/model/test_provenance.py::test_mark_measured_refuses_empty_source_and_design_fields",
        ),
    ),
    "REQ-T-07": Ruling(
        "checks",
        "SVG metadata and DXF header comments hold the stamp; the PDF text holds a generated_utc stamp; README holds "
        "embodic, engine and generated_utc lines; the project JSON holds app_version, design_hash and saved_utc "
        "(test_stamp_fields.py) and engine_version and registry_version keys (test_project_v2.py).",
        (
            f"{EXPO}/test_svg.py::test_ut_io_06_svg_metadata_holds_the_stamp",
            f"{EXPO}/test_dxf.py::test_ut_io_06_dxf_header_comment_holds_the_stamp",
            f"{EXPO}/test_report_readme_bundle.py::test_ut_io_06_report_carries_the_stamp",
            f"{STAMP}::test_t07_project_json_holds_the_embodic_version_the_design_hash_and_a_utc_date",
            f"{STAMP}::test_t07_pdf_text_holds_a_generated_utc_value",
            f"{STAMP}::test_t07_readme_carries_the_versions_of_the_outcome_and_a_generated_utc_line",
            f"{PROJ}/test_project_v2.py::test_saved_project_names_the_engine_version_and_the_registry_version",
        ),
    ),
    "REQ-T-08": Ruling(
        "checks",
        "Amended acceptance. A 0.4 delta trace flags R and eddy results with RANGE_SKIN_DEPTH and the flag travels to "
        "every result built from the resistances (test_skin_depth_validity_flag.py); UT-PHY-21 gives 5.328140, "
        "4.208834 "
        "and 5.788521 % within 0.1 pp at 0.5 mm chords and 0.005 pp at 0.1 mm; a case above 0.10 gets the CAP effect "
        "(test_ut_phy_21_edge_kernel.py), which the status table maps to `unresolved` (test_status.py l.63, a REQ-T-03 "
        "test).",
        (
            f"{U}/physics/test_skin_depth_validity_flag.py::test_t08_a_trace_of_0_4_skin_depths_flags_the_resistance_and_the_eddy_results",
            f"{U}/physics/test_skin_depth_validity_flag.py::test_t08_the_skin_depth_flag_travels_to_every_result_built_from_the_resistances",
            f"{U}/physics/test_ut_phy_21_edge_kernel.py::test_edge_leakage_of_the_phase_1_segment_set_matches_the_registry_formula",
            f"{U}/physics/test_ut_phy_21_edge_kernel.py::test_short_magnets_cap_the_badge_and_a_15_mm_magnet_does_not",
            f"{TRACE}::test_traceable_ec05_below_cap_adds_one_sided_addon_and_limitation",
        ),
    ),
    "REQ-T-09": Ruling(
        "checks",
        "Unmarked tests and unknown IDs are found; the gate exits 1 and names an unmarked test, 0 when all are marked "
        "(test_trace_matrix_gate.py, gap T-09 closed); the release gate exits 1 on an untested live must row.",
        (
            f"{U}/base/test_trace_matrix.py::test_trace_matrix_reports_unmarked_tests_and_unknown_ids",
            f"{U}/base/test_trace_matrix_gate.py::test_gate_exits_1_and_names_a_test_without_a_req_marker",
            f"{U}/base/test_trace_matrix_gate.py::test_gate_exits_0_when_every_test_is_marked",
            f"{TR01}::test_tr01_release_gate_fails_on_an_untested_must_row",
        ),
    ),
    "REQ-T-10": Ruling(
        "checks",
        "LG-03 scans source strings and resources (the fonts note included since U-M8b) for 'measur' with the §5.8.2 "
        "allow-list and finds 0 hits; planted hits in a catalogue and an outcome copy are found (test_lg_wording.py).",
        (
            f"{LGW}::test_lg03_source_strings_never_call_a_computed_value_measured",
            f"{LGW}::test_lg03_resources_never_call_a_computed_value_measured",
            f"{LGW}::test_lg03_a_measured_column_in_the_catalogue_is_a_hit_and_the_provenance_word_is_not",
            f"{LGW}::test_lg03_a_planted_measured_key_in_an_outcome_copy_is_a_hit",
        ),
    ),
    "REQ-T-11": Ruling(
        "partial",
        "LG-04 scans source strings and resources for balance, torque and efficiency claims and finds 0 hits, with "
        "planted controls (test_lg_wording.py). The reviewer check of test_plan.md §5.8.3 has no record.",
        missing="A reviewer manual record of the LG-04 hits and allow-list (test_plan.md §5.8.3), indexed as REQ-T-11 "
        "LG-04.",
        kind="manual record",
        owner="Agent 4",
    ),
    "REQ-T-13": Ruling(
        "checks",
        "For every result row of D08 and of the wave example: six sections each with a line, every input line names "
        "its provenance word or 'registry constant' or 'result', the Assumptions count equals the card tag, and Copy "
        "trace holds every disclosure line (test_disclosure_every_row.py, gap T-13 closed).",
        (
            f"{DISC}::test_t13_every_row_has_the_six_sections_and_a_line_in_each",
            f"{DISC}::test_t13_every_input_line_names_where_the_value_came_from",
            f"{DISC}::test_t13_the_assumptions_section_counts_what_the_card_tag_counts",
            f"{DISC}::test_t13_copy_trace_holds_every_disclosure_line_of_every_row",
        ),
    ),
    "REQ-T-14": Ruling(
        "checks",
        "A non-engine drawing carries 'Illustrative, not computed'; the stamp is in SVG, DXF, PDF and README "
        "(test_stamp_fields.py t14); the on-screen drawing shows the stamp with version and design hash at the bottom "
        "left, at 4.5:1, and renames it for a new outcome (test_canvas_stamp.py, UI-32 b to d).",
        (
            f"{CHARTS}::test_ui32_a_drawing_not_from_the_engine_carries_the_illustrative_stamp",
            f"{STAMP}::test_t14_readme_names_the_embodic_version_of_the_outcome",
            f"{UI}/qt_shell/test_canvas_stamp.py::test_ui32b_canvas_stamp_names_the_version_and_the_design_hash_at_the_bottom_left",
            f"{UI}/qt_shell/test_canvas_stamp.py::test_ui32c_the_stamp_is_painted_on_its_plate_and_its_text_reaches_4_5_to_1",
            f"{UI}/qt_shell/test_canvas_stamp.py::test_ui32d_a_stale_drawing_keeps_its_stamp_and_a_new_outcome_renames_it",
        ),
    ),
    "REQ-T-15": Ruling(
        "checks",
        "As U-V12b ruled; re-read on 260191f: test_project.py changed only the schema version literal and the "
        "registry_version argument.",
        (
            f"{U}/model/test_provenance.py::test_truth_table",
            f"{U}/model/test_provenance.py::test_reentry_changes_nothing_and_back_to_example_restores_example",
            f"{PROJ}/test_project.py::test_ut_io_07_stored_example_entry_that_disagrees_is_reported",
        ),
    ),
    "REQ-T-16": Ruling(
        "checks",
        "The EC-05 entry carries the four ValidityCheckSpec fields; e_edge is `assumption`; the disclosure says 'at "
        "least'; the UI entries of OR-07 and OR-08 carry the not-independent note after every EC-05 line and in the "
        "EQ-05 register (test_oracle_dependency_note.py, T16-1 to T16-6).",
        (
            f"{REG}::test_registry_packaged_ec05_fields_are_read_as_typed",
            f"{TRACE}::test_traceable_ec05_metric_is_assumption_and_transfer_joins_affected_tags",
            f"{RVM}::test_ui33_ke_disclosure_states_e_edge_at_least_assumption_and_the_10_percent_cap",
            f"{ORN}::test_ui_entries_of_the_dependent_oracles_say_they_are_not_independent_of_ec05",
            f"{ORN}::test_every_ec05_check_line_of_d08_is_followed_by_the_oracle_note",
            f"{ORN}::test_equation_register_lists_the_oracles_right_after_the_ec05_check",
        ),
    ),
    "REQ-L-01": Ruling(
        "partial",
        "Amended acceptance (U-D20). LG-08 finds no Thai in src, resources and templates; LG-01 checks every string "
        "literal per character with MODULE_SYMBOLS; Agent 4's manual record (LG-01_word_review.md, indexed) found no "
        "non-English word in 804 distinct words. The record had to use Agent 4's own lister, because the LG-01 word "
        "printer and its planted-word test that test_plan.md l.488 specifies do not exist (DEF-UV13-01).",
        (
            "tests/static/test_lg_language.py::test_lg01_string_literals_are_english",
            "tests/static/test_lg_language.py::test_lg08_shipped_files_have_no_thai",
            "record:tests/independent/m4/records/LG-01_word_review.md",
        ),
        missing="The LG-01 function and command that print the sorted distinct words of the catalogues and report "
        "templates, with the planted-word test (test_plan.md l.488); then a reviewer compares its list with the "
        "record.",
        kind="test",
        owner="Agent 3",
    ),
    "REQ-L-03": Ruling(
        "checks",
        "LG-05 finds no 'xcoil' and no D-051c program name in source strings and resources outside the admitted board "
        "dump format and unshown source notes, with planted controls (test_lg_wording.py).",
        (
            f"{LGW}::test_lg05_source_strings_carry_no_program_name_beyond_the_board_dump_format",
            f"{LGW}::test_lg05_resources_carry_no_program_name_beyond_the_unshown_source_notes",
            f"{LGW}::test_lg05_the_board_dump_schema_text_is_admitted_only_in_its_own_module",
            f"{LGW}::test_lg05_a_program_name_is_found_but_not_inside_a_longer_word",
        ),
    ),
    "REQ-L-04": Ruling(
        "checks",
        "Contrast check of both themes; every chrome token has R = G = B and the only saturated tokens are the three "
        "phases and three statuses (test_theme_chrome_tokens.py, gap L-04 closed); greyscale mode in UI-27.",
        (
            f"{U}/ui/shell/test_contrast_check.py::test_ax01_ax09_every_pair_of_both_shipped_themes_passes",
            f"{U}/ui/shell/test_theme_chrome_tokens.py::test_every_chrome_token_has_equal_red_green_and_blue",
            f"{U}/ui/shell/test_theme_chrome_tokens.py::test_the_only_saturated_colours_are_the_phase_and_the_status_tokens",
            f"{U}/ui/shell/test_theme_chrome_tokens.py::test_a_planted_tinted_chrome_token_is_found_and_a_planted_grey_one_is_not",
        ),
    ),
    "REQ-L-05": Ruling(
        "partial",
        "LG-06: every tracked brand-named image matches its recorded SHA-256, a modified copy fails, and the personal "
        "scan finds 0 hits with planted controls (test_lg_brand_and_names.py). tests/static/brand_assets.sha256 "
        "records "
        "four of the five originals; embodic-logo-white.png has no copy in the checkout and no hash (`not tested`, "
        "the file's own note).",
        missing="The SHA-256 of the original embodic-logo-white.png appended to tests/static/brand_assets.sha256, from "
        "the user's originals (outside the checkout).",
        kind="test",
        owner="Fable (reads the original), Agent 3 (appends)",
    ),
    "REQ-L-07": Ruling(
        "checks", None, (f"{U}/results/test_formatting.py::test_formatting_identical_under_german_and_thai_locale",)
    ),
    "REQ-L-08": Ruling(
        "checks",
        None,
        (
            f"{U}/ui/results/test_checks_charts_compare_guide.py::test_ui34_counts_are_integers_and_deltas_carry_sign_and_direction",
        ),
    ),
}
