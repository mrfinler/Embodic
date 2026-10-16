"""Agent 4's V3-01 rulings: each test's source, read at the release commit, against the Acceptance cell of its row.

SAMPLE_RULINGS: REQ id -> (ruling, reason) for the test that v3_01_sample.py picked.
CAUSE_B_RULINGS: (REQ id, test ID) -> (ruling, reason, node ids read). For a cause-B ID, `checks` means a passing test
asserts the ID's criterion under another label or marker; `does not check` means I found no such test.
"""

T = "tests/unit"
G = "tests/golden"

SAMPLE_RULINGS: dict[str, tuple[str, str]] = {
    "REQ-F-01": (
        "partial",
        "Asserts the X/Y mirror within 1e-9 mm for coil 0 only. Continuity 1e-6 mm, the centre via 1e-9 mm and equal "
        "circulation are not in this test.",
    ),
    "REQ-F-02": (
        "partial",
        "Asserts the 12/10 pattern exactly (criterion a). 12/16, 12/14, the 24-slot balance cases, the 16/16 rule and "
        "the k_w1 table are not in this test.",
    ),
    "REQ-F-07": (
        "partial",
        "Asserts alpha_p 0.853, 0.547, 0.402 at abs 5e-4, inside the criterion's 1e-3. The 1-D limit to 1e-9 rel. is "
        "not in this test.",
    ),
    "REQ-F-13": (
        "does not check",
        "Asserts that arrow keys pan a zoomed canvas. It asserts neither the two-interaction reach of each view nor "
        "stroke widths over zoom 0.1x to 200x.",
    ),
    "REQ-F-15": (
        "partial",
        "Asserts save, load, save byte identity on three spiral examples. The draft round trip and the "
        "hash-changes-iff-a-design-field-changes clause are not in this test.",
    ),
    "REQ-F-16": (
        "partial",
        "Parses the SVG with an XML reader and asserts phase classes, labels and inks. The ezdxf audit, the pypdf "
        "'Key results' page and the entity counts against the Layout are not in this test.",
    ),
    "REQ-F-18": (
        "does not check",
        "Asserts the selftest command's exit code and lines. None of the three clauses (compute --json equality, a "
        "draft exits 1 with the missing pointers, --allow-drc-errors) is in this test.",
    ),
    "REQ-F-19": (
        "partial",
        "A stub registered at runtime passes DRC, analysis and the board dump with the shipped generator's values. "
        "The exporters (SVG, DXF, PDF, README, JSON) are not driven; the C1 import rule is the MT-01 gate.",
    ),
    "REQ-F-21": (
        "partial",
        "Asserts that one edited field turns `user` and setting it back restores `example`. The empty fresh start, "
        "the chip on every field and unchanged badges are not in this test.",
    ),
    "REQ-F-23": (
        "partial",
        "Asserts the notice with old and new value, and that Undo restores value and hash. 'The engine never returns "
        "modified DesignParameters' is not in this test. The notice it pins says 'Xcoil clamps to the supported "
        "range.' (DEF-UV8-01).",
    ),
    "REQ-F-32": (
        "partial",
        "Asserts that one temporarily inapplicable spiral input (corner radius with straight ends) is disabled with "
        "its reason. The test is not driven by field_specs, and serpentine and wave are absent.",
    ),
    "REQ-F-33": (
        "partial",
        "Asserts the confirmation lists the 186 failures with focus and default on Cancel, and Cancel writes nothing. "
        "The CLI --allow-drc-errors clause is not in this test. The failure line it pins calls a computed clearance "
        "'measured' (DEF-UV8-03).",
    ),
    "REQ-F-34": (
        "partial",
        "Asserts per-path primitive counts and nets against Xcoil, board by board. Via and pad counts, the 1e-6 mm "
        "sampled distance, DRC values and board z offsets are not in this test.",
    ),
    "REQ-F-35": (
        "partial",
        "Asserts every primitive of one wave case against Xcoil within the layout tolerance. EMF and resistance "
        "against Xcoil (GR-22) are not in this test.",
    ),
    "REQ-F-36": (
        "checks",
        "Asserts a blank spiral draft shows its required inputs empty and '34 required fields left', no compute while "
        "the fields are filled, and exactly one compute after the last one.",
    ),
    "REQ-F-37": (
        "does not check",
        "Asserts blank_draft holds no required value. It never calls parse_draft, so the DraftIncomplete pointer "
        "list, INVALID issues and the draft_from_design round trip are absent.",
    ),
    "REQ-F-38": (
        "partial",
        "Asserts the gallery lists the packaged examples and every visible chip reads `example` after load. /name "
        "equal to the display title and the first Save opening Save As are not in this test.",
    ),
    "REQ-F-39": (
        "partial",
        "Asserts label, tooltip, accessible name, and that each command is enabled exactly when implemented. Icon "
        "files, arrow-key movement and icon recolouring are not in this test.",
    ),
    "REQ-F-40": (
        "does not check",
        "Asserts DRC violation counts on Xcoil layouts. The one reader, write-read-write identity and non-finite "
        "encoding of board dumps are not in this test.",
    ),
    "REQ-N-01": (
        "does not check",
        "Records p95 and stage times and asserts only p95 > 0, so neither the 1.0 s threshold nor a stage budget can "
        "fail it. The acceptance keeps the row `assumption` until the laptop run.",
    ),
    "REQ-N-02": (
        "partial",
        "Asserts the largest GUI tick gap during a 3 s synthetic compute is below 100 ms. The UX-AC-22 timing is not "
        "in this test.",
    ),
    "REQ-N-08": (
        "checks",
        "The release gate ran lint-imports (C1 to C4), mypy and ruff on the tree and each passed (gate log); exit 0 "
        "of each tool is 0 findings.",
    ),
    "REQ-N-09": (
        "partial",
        "Runs the checker on the real package and asserts no finding. The checker needs an EQ-ID, a 'name:' line per "
        "parameter and a Returns heading; no regex checks that a unit is named, and it reads module-level functions "
        "only.",
    ),
    "REQ-N-10": (
        "does not check",
        "The gate runs tools/trace_matrix.py without --fail-untested-through, so 'untested due: 0' is printed without "
        "the check. With the flag the release report gives 6 untested live must rows and exit 1 (DEF-UV8-02). The "
        "pytest gate runs without pytest-cov (tools/ci.py at 5e74acc).",
    ),
    "REQ-N-11": ("checks", "Runs the contrast script over both shipped themes and asserts '0 failures'."),
    "REQ-N-12": (
        "partial",
        "Drives the whole scenario with Tab, Space, Return and arrow keys. The focus ring on every stop and Tab order "
        "equal to visual order are not asserted.",
    ),
    "REQ-N-13": (
        "does not check",
        "Asserts that a click on one check box's label text toggles it. No widget enumeration and no 24 x 24 px bound.",
    ),
    "REQ-N-14": (
        "checks",
        "The record reads phase and polarity of 12 D08 coils, 12 of 12 in greyscale and 12 of 12 in simulated "
        "deuteranopia, against the Layout. The deuteranopia render is a simulation, which the record labels "
        "`inferred`.",
    ),
    "REQ-N-15": (
        "does not check",
        "Asserts the grab size at one scale factor and no error note. No clipping, overlap or horizontal-scroll check.",
    ),
    "REQ-N-17": (
        "does not check",
        "Asserts that the network-import lint flags planted modules. It is the lint's control, not the scan of src, "
        "and nothing runs the suite with the network disabled.",
    ),
    "REQ-N-18": (
        "checks",
        "Injects a GUI-slot exception and asserts the error dialog is shown and names the one recovery file saved; "
        "the process carries on.",
    ),
    "REQ-N-19": (
        "partial",
        "Asserts every declared requirement has a licence row (--coverage exits 0). The match with the allow-list of "
        "package_layout.md §5 and THIRD_PARTY_LICENSES completeness are not asserted here.",
    ),
    "REQ-N-23": (
        "partial",
        "Asserts grey pens, labels and hatch item counts in greyscale mode. No forced-colours run and no check that a "
        "hatch never crosses copper.",
    ),
    "REQ-N-25": (
        "partial",
        "Asserts one y unit, three series labelled 'Phase A/B/C' and the badge of the data. The data-table "
        "alternative and direct labels are not in this test.",
    ),
    "REQ-N-28": (
        "partial",
        "Asserts phase pens equal the theme tokens and labels exist in colour and greyscale modes. 3:1 against the "
        "canvas and the palette validator are not in this test.",
    ),
    "REQ-T-01": (
        "partial",
        "Asserts every card has a unit and its row's badge, and one card's EQ link. An EQ link or tag on every card "
        "and keyboard-reachable details are not in this test.",
    ),
    "REQ-T-02": (
        "partial",
        "Asserts five fields of one packaged result keep value, unit, status and eq_ids in JSON. There is no walk "
        "over all fields of every example and no ID resolution.",
    ),
    "REQ-T-03": (
        "partial",
        "Asserts ten rows of the badge truth table. 'The tag lists exactly the assumed inputs used' is not in this "
        "test.",
    ),
    "REQ-T-04": (
        "partial",
        "Asserts every EQ- and EV-ID written in src resolves in the packaged registry. IDs referenced inside the "
        "registry files are not checked here.",
    ),
    "REQ-T-05": (
        "partial",
        "Asserts every verified equation lists a linked test. Whether that test passed in this build is the TR-05 "
        "gate, not this test.",
    ),
    "REQ-T-06": (
        "partial",
        "Asserts a measured property input (copper thickness) leaves the tag. The refusal without a source and on a "
        "design field is not in this test.",
    ),
    "REQ-T-07": (
        "partial",
        "Asserts the five stamp fields and drc_passed in the SVG metadata. The DXF header, project JSON, PDF and "
        "README are not in this test.",
    ),
    "REQ-T-09": (
        "partial",
        "The trace-matrix gate enforces 0 unmarked tests and 0 unknown IDs (TR-02). Run without "
        "--fail-untested-through, it does not enforce 0 live must rows without a test (DEF-UV8-02).",
    ),
    "REQ-T-13": (
        "does not check",
        "Asserts card title, value, unit, badge, EQ link and assumption count. The 'How was this computed' "
        "disclosure and Copy trace are never opened.",
    ),
    "REQ-T-14": (
        "partial",
        "Asserts the PDF text and information dictionary carry the versions and the design hash. The 'Illustrative, "
        "not computed' widget clause and the other exports are not in this test.",
    ),
    "REQ-T-16": (
        "partial",
        "Asserts the disclosure says e_edge, 'at least', 'assumption' and the 10 % cap. The registry's four fields, "
        "the Traceable status and the OR-07/OR-08 note are not in this test.",
    ),
    "REQ-L-01": (
        "does not check",
        "Asserts the no-break-space allowance on two planted modules. It is the scanner's control, not the scan of "
        "src, resources and templates.",
    ),
    "REQ-L-04": (
        "partial",
        "Asserts the contrast check of both themes passes. The greyscale test and the token review are not in this "
        "test.",
    ),
    "REQ-L-07": (
        "does not check",
        "Asserts format_quantity output for one case under the process locale. No German or Thai locale is set.",
    ),
    "REQ-L-08": (
        "checks",
        "Asserts counts print as integers and every delta's sign matches its direction (up, down, same). That the "
        "glyph follows the direction is `inferred`; no widget is drawn.",
    ),
}

CAUSE_B_RULINGS: dict[tuple[str, str], tuple[str, str, tuple[str, ...]]] = {
    ("REQ-F-03", "UT-GEO-24"): (
        "partial",
        "Found under REQ-F-01: pi/2 + 2 pi k (k = -1, 3) gives the same via positions within 1e-9 mm. The plan's "
        "1e-9 rad axis, every primitive end point and the stored typed value are not asserted.",
        (f"{T}/generators/test_spiral_generate.py::test_first_coil_angle_any_finite_value_is_normalised",),
    ),
    ("REQ-F-03", "UT-GEO-26"): (
        "checks",
        "Found as UT-GEO-19 under REQ-F-03: CF-11 with k = 3 keeps 10 turns and centre vias at 30.7, 29.9, 29.1 mm "
        "(abs 1e-9); each group joins ring via g, its centre via and ring via g + 1 within 1e-9 mm; series boards "
        "have 0 DRC violations with the smallest gap s within 1e-6 mm.",
        (
            f"{T}/generators/test_spiral_pairs.py::test_ut_geo_19_series_groups_get_their_own_centre_via_one_pitch_apart",
            f"{T}/generators/test_spiral_pairs.py::test_ut_geo_19_each_group_runs_from_its_ring_via_to_its_centre_and_out_to_the_next",
            f"{T}/generators/test_spiral_series_fan.py::test_series_board_passes_drc_with_smallest_gap_s",
        ),
    ),
    ("REQ-F-03", "UT-PHY-07"): (
        "does not check",
        "Missing test. I found no test that asserts series EMF = phasor sum of pair EMFs at 1e-9 rel.: searches for "
        "'phasor sum', 'series chain', 'EQ-07' and test names with 'series' in tests/unit/physics and "
        "tests/golden/m2_physics find only the parallel two-member identity (CF-07) and Xcoil golden comparisons.",
        (),
    ),
    ("REQ-F-04", "GR-07"): (
        "does not check",
        "Missing test. No test names stackupFor, stackup_for, 'even spac' or 'auto mode'; the stack-up tests check "
        "z sums (UT-GEO-12) and board thickness, not the even-spacing helper against Xcoil at 1e-12 mm.",
        (),
    ),
    ("REQ-F-05", "UT-PHY-11"): (
        "partial",
        "Found under REQ-F-11: drill 0.3 mm, plating 25 um, l 0.2 mm gives 0.160 mOhm (abs 0.5 uOhm), and two "
        "barrels halve it (rel 1e-12). That the analysis passes the design's via count per transition is not "
        "asserted.",
        (f"{T}/physics/test_kernels.py::test_cf04_and_ut_phy_11_via_barrel_resistance",),
    ),
    ("REQ-F-05", "PR-01"): (
        "partial",
        "PR-01 exists under REQ-F-10 but samples single-primitive trace pairs on one layer, with no via. PR-13 "
        "sweeps vias on wave boards. Neither checks that a spiral through via clears foreign copper.",
        (
            f"{T}/drc/test_properties.py::test_pr_01_drc_never_under_reports_and_reports_no_false_positive_on_200_random_sets",
            f"{T}/property/wave/test_wave_properties.py::test_pr_13_run_drc_never_under_reports_on_a_wave_board",
        ),
    ),
    ("REQ-F-06", "UT-GEO-25"): (
        "partial",
        "Found under REQ-F-06: CF-11 reports the FULL closing and D08 the HALF closing. That closing is not a FIELDS "
        "pointer and is absent from the project file is not asserted.",
        (f"{T}/generators/test_spiral_generate.py::test_turn_limit_reports_the_closing",),
    ),
    ("REQ-F-08", "UT-PHY-09"): (
        "checks",
        "Found as CF-06 under REQ-F-11: Ke_ph 0.01 gives Ke_LL 0.017320508075688773 in star and 0.01 in delta, "
        "rel 1e-12.",
        (f"{T}/physics/test_kernels.py::test_cf06_star_and_delta_constants",),
    ),
    ("REQ-F-10", "UT-DRC-01"): (
        "checks",
        "Found under REQ-F-05: the default spiral has 0 violations and its tightest trace-trace and trace-via gaps "
        "equal 0.2 mm within 1e-6 mm, inside [rule - 1e-6, rule + 0.005] mm.",
        (f"{T}/generators/test_spiral_generate.py::test_default_example_passes_drc",),
    ),
    ("REQ-F-10", "PR-13"): (
        "checks",
        "Found under REQ-F-35: on six wave boards an independent sweep's violations at the D-006 threshold are a "
        "subset of run_drc's, and a passed report has none.",
        (f"{T}/property/wave/test_wave_properties.py::test_pr_13_run_drc_never_under_reports_on_a_wave_board",),
    ),
    ("REQ-F-12", "UT-PHY-08"): (
        "checks",
        "Found as CF-07 under REQ-F-11: two members of 0.5 ohm give P_c 2.0e-4 W, R_grp 0.25 ohm and E_grp 0.99 V at "
        "rel 1e-12.",
        (f"{T}/physics/test_closed_forms_m2e2.py::test_eq07_cf07_two_member_group_with_half_ohm_members",),
    ),
    ("REQ-F-12", "GR-05"): (
        "partial",
        "Circulating loss is compared with Xcoil's pCirc on three layouts (sector, serpentine and wave defaults). No "
        "case with 2 and 3 parallel members at different z, as the plan asks.",
        (f"{G}/m2_physics/test_analysis_golden.py::test_result_quantities_match_xcoil",),
    ),
    ("REQ-F-14", "BV-05"): (
        "checks",
        "Found under REQ-F-19: the turns that fit build, and one more is refused with UNBUILDABLE_TURNS_EXCEED_LIMIT "
        "and limit = the turns that fit, the code interfaces.md §6 documents.",
        (
            f"{T}/generators/test_spiral_bounds.py::test_requested_turns_above_the_turns_that_fit_are_refused_as_the_users_request",
        ),
    ),
    ("REQ-F-20", "UT-RES-02"): (
        "checks",
        "The truth table maps `cannot verify yet` to `unresolved` (REQ-T-03 marker), and the torque-speed estimate's "
        "five Traceables are `unresolved`, labelled 'estimate', with EQ-20 (REQ-F-11 marker).",
        (
            f"{T}/results/test_status.py::test_status_badge_truth_table",
            f"{G}/m2_physics/test_analyse_layouts.py::test_torque_speed_estimate_is_an_unresolved_estimate_tied_to_the_other_results",
        ),
    ),
    ("REQ-F-29", "UT-EXP-05"): (
        "checks",
        "Found under REQ-F-16, F-33, T-07 and T-14: the ZIP holds exactly the selected files plus README.txt. The "
        "Xcoil-import clause (could) has no planned ID.",
        (
            f"{T}/embodic_io/exporters/test_report_readme_bundle.py::test_ut_exp_05_bundle_holds_selected_files_and_readme",
        ),
    ),
    ("REQ-N-21", "UT-EXP-02"): (
        "partial",
        "Found under REQ-F-16: after DXF writing every outline end point is shared by exactly two entities. Copper "
        "continuity after SVG and DXF quantisation is not asserted.",
        (f"{T}/embodic_io/exporters/test_dxf.py::test_ut_exp_02_outline_dxf_is_closed_outline_and_bore_only",),
    ),
    ("REQ-N-27", "AX-01"): (
        "partial",
        "Found under REQ-N-11: both theme files pass the contrast script. It does not assert that every token exists "
        "in both files, the REQ-N-27 clause (UI-26 asserts that).",
        (f"{T}/ui/shell/test_contrast_check.py::test_ax01_ax09_every_pair_of_both_shipped_themes_passes",),
    ),
    ("REQ-T-08", "UT-PHY-13"): (
        "partial",
        "Found under REQ-F-11: skin depth 5.72 mm within 0.01 mm. I found no test that raises RANGE_SKIN_DEPTH for "
        "w > delta/3 and marks R and eddy results; the only hit is the message catalogue test "
        "(tests/unit/base/test_errors.py l.79).",
        (f"{T}/physics/test_kernels.py::test_ut_phy_13_skin_depth_at_133_hz",),
    ),
    ("REQ-T-08", "UT-PHY-21"): (
        "partial",
        "The EC-05 kernel on a closed-form case (rel 1e-12) and the DEF-23 labels are asserted. The plan's e_edge "
        "5.3 %, 4.2 % and 5.8 % within 0.1 pp of Agent 2 are not found.",
        (
            f"{T}/physics/test_closed_forms_m2e2.py::test_ec05_edge_leakage_value_from_the_registry_constants",
            f"{G}/m2_physics/test_analyse_layouts.py::test_edge_leakage_metric_is_labelled_per_def23",
        ),
    ),
    ("REQ-T-15", "PR-12"): (
        "checks",
        "Found under REQ-F-21 and T-03: re-entry keeps the hash, the provenance and every badge; the REQ-T-15 unit "
        "test asserts that setting B_r back restores `example`.",
        (
            f"{T}/property/test_pipeline_properties.py::test_pr_12_badges_do_not_depend_on_provenance_and_reentry_changes_nothing",
            f"{T}/model/test_provenance.py::test_reentry_changes_nothing_and_back_to_example_restores_example",
        ),
    ),
}
