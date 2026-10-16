"""Agent 4's V3-01 union rulings (U-V12b) for the live must rows REQ-N-*, REQ-T-* and REQ-L-*, read on main 8a4a8a1.

The union of a row is every test that carries its REQ marker or names one of its planned test IDs
(tests/independent/m7/v3_01_union.py over a `pytest --collect-only --req-report` of main 8a4a8a1, 3202 tests).
`checks` cites test:line for each part of the Acceptance cell. `partial` and `does not check` name the missing part;
its test spec is in records/V3-01_gaps_b.md under the same REQ id. A part I call missing is one for which a search of
every file in the union found no assertion (`inferred` from that search, not from reading every test of a large union).

UNION_RULINGS: REQ id -> (ruling, reason). req_audit.py lets these replace the V3-01 sample ruling of the same row.
UNION_PINS: REQ id -> {test file: SHA-256 at 8a4a8a1} for every `checks` ruling (D-051e).
REQ-T-01, T-02, T-05, T-07, T-13 and T-14 were ruled in the U-V12b continuation, on the same main 8a4a8a1 sources.
"""

UNION_RULINGS: dict[str, tuple[str, str]] = {
    "REQ-N-01": (
        "partial",
        "PF-01 records p95 and stage times but asserts only p95 > 0 (tests/performance/test_pf_baseline.py:70, :151). "
        "The 1.0 s threshold and the stage budgets 0.2/0.4/0.3 s are not asserted, and the acceptance needs the user's "
        "laptop (gap N-01).",
    ),
    "REQ-N-02": (
        "partial",
        "100 ms event-loop answer during a 3 s compute (tests/ui/qt_shell/test_worker_and_errors.py:66), compute off "
        "the GUI thread (:50) and latest edit wins (:22; tests/unit/ui/shell/test_outcome_viewmodel.py:63). No test "
        "in the union asserts the 300 ms debounce or the UX-AC-22 timing (gap N-02).",
    ),
    "REQ-N-04": (
        "partial",
        "Same-platform byte identity (tests/unit/api/test_compute.py:48, tests/unit/property/"
        "test_pipeline_properties.py:248) and the sum() scan (tests/static/test_mt06_numerics.py:41). The cross-"
        "platform PK-04 comparison is a Windows run; Fable's W1 record says PK-04 failed as written (gap N-04).",
    ),
    "REQ-N-05": (
        "partial",
        "A clean Python 3.11 Linux venv resolves (tests/packaging/test_pk02_clean_install.py:24). No test or record "
        "shows the Windows cells or Python 3.12 and 3.13 green (gap N-05).",
    ),
    "REQ-N-06": (
        "partial",
        "Two wheel builds have the same members and .py bytes (tests/packaging/test_pk03_reproducible_wheel.py:23). "
        "The bundle smoke tests (tests/bundle/test_bundle_smoke.py:49-109) need a built bundle, and PK-05 needs the "
        "Windows folder; the release report has them skipped (gap N-06).",
    ),
    "REQ-N-07": (
        "partial",
        "No automated test can hold this row. Manual records (manual_records.json): Linux PK-06 cold passed "
        "(tests/independent/m5/records/PK-06_walkthrough.md), Windows warm cache passed in 21.57 s and Windows cold "
        "failed in 4154.5 s on a 0.03 MB/s network (docs/phase3/fable/windows_campaign_w1.md l.33, l.38, l.66). A "
        "clean Windows machine on a usual network has no passed record (gap N-07).",
    ),
    "REQ-N-09": (
        "partial",
        "The checker runs on the real package (tests/static/test_mt04_physics_docstrings.py:36). It requires an EQ-ID, "
        "a `name:` line per parameter and a Returns heading (l.21-29); no regex checks that a unit is named, so the "
        "'names units' clause cannot fail (gap N-09).",
    ),
    "REQ-N-10": (
        "partial",
        "TR-01 half: the release profile passes --fail-untested-through M5 (tools/ci.py l.47, l.77-78) and the gate "
        "exits 1 on an untested live must row (tests/unit/base/test_tr01_release_gate.py:216-222). The pytest-cov "
        "clause has no test; D-053b moves it to Phase 5 but requirements.md still carries it (gap N-10).",
    ),
    "REQ-N-12": (
        "partial",
        "Keyboard-only scenario (tests/ui/qt_e2e/test_ax02_keyboard_only.py:43), focus ring on every focusable control "
        "(tests/ui/qt_shell/test_focus_ring.py:29), F6 region cycling (tests/ui/qt_shell/test_keyboard_map.py:85). No "
        "test asserts that Tab order equals visual order (gap N-12).",
    ),
    "REQ-N-13": (
        "checks",
        "Widget enumeration over the empty session, D08 with every inspector, results and toolstrip tab, and the New "
        "design, Examples and Export dialogs (tests/ui/qt_e2e/test_ax04_target_size.py:76-127) asserts no visible "
        "enabled target below 24 px and no check row below 32 px (:130-136), with the hit area measured by hitButton "
        "(:53-65).",
    ),
    "REQ-N-15": (
        "partial",
        "Clipped-text check at 960 x 540, 1280 x 800 and 1600 x 900 (tests/independent/m4/test_ui_behaviour.py:268). "
        "The three scalings, overlap and horizontal scroll in forms are not asserted; test_plan.md l.346 records UI-09 "
        "clipping as `not tested` by code (gap N-15).",
    ),
    "REQ-N-16": (
        "partial",
        "Every Tab stop with D08 open has an accessible name (tests/ui/qt_shell/test_keyboard_map.py:118) and spoken "
        "quantities name the unit in words (tests/unit/results/test_formatting.py:110). The Narrator check is a "
        "Windows person-run check with no record (gap N-16).",
    ),
    "REQ-N-17": (
        "partial",
        "src imports no network module (tests/static/test_pk07_no_network.py:31) with its control (:37). Nothing runs "
        "the suite with the network disabled (gap N-17).",
    ),
    "REQ-N-19": (
        "checks",
        "The runtime closure's licences equal the package_layout.md section 5 values (tests/packaging/"
        "test_pk08_licences.py:36-43; the ALLOWED map l.15-19 matches package_layout.md l.386-387, read). "
        "THIRD_PARTY_LICENSES.md has every component and the full font and Qt texts (:46-61), every declared "
        "requirement has a licence row (:75-82).",
    ),
    "REQ-N-21": (
        "partial",
        "The quantisation helper matches the reference rounding (tests/unit/base/test_units.py:105). No test in the "
        "union asserts continuity after SVG and DXF quantisation (gap N-21).",
    ),
    "REQ-N-23": (
        "partial",
        "Greyscale mode keeps labels (tests/ui/qt_shell/test_theme_and_geometry.py:70) and the eye never reaches "
        "copper (tests/unit/ui/shell/test_outcome_viewmodel.py:114). No forced-colours run is in the union (gap N-23).",
    ),
    "REQ-N-24": (
        "partial",
        "No test in the union reads an input's accessible description, so 'includes the unit in its accessible "
        "description' is not asserted (gap N-24).",
    ),
    "REQ-N-25": (
        "partial",
        "Back-EMF chart: one unit, legend, end labels, data table and badge (tests/ui/qt_results/"
        "test_charts_compare_guide_export.py:29-55). Torque and power charts: one unit each and the badge (:59-72; "
        "tests/unit/ui/results/test_checks_charts_compare_guide.py:103-117), but no data table and no direct label "
        "(gap N-25).",
    ),
    "REQ-N-27": (
        "partial",
        "Every chrome token in both theme files (tests/unit/ui/shell/test_theme.py:23-35) and persistence across a "
        "restart (tests/ui/qt_shell/test_theme_and_geometry.py:50). The runtime switch checks named region backgrounds "
        "and the app palette (:36-45), not every widget (gap N-27).",
    ),
    "REQ-N-28": (
        "partial",
        "Phase colours on canvas and board fill at 3:1 in both themes through tokens.json contrast_pairs and "
        "tests/unit/ui/shell/test_contrast_check.py:32-37; labels in both render modes (tests/ui/qt_shell/"
        "test_theme_and_geometry.py:70). The palette validator is not run: tools/contrast_check.py l.11 cites the "
        "greyscale ladder without rerunning it (gap N-28).",
    ),
    "REQ-T-03": (
        "checks",
        "Truth table: ten rows over equation status, gate verdict, test state and validity effect (tests/unit/results/"
        "test_status.py:51-70). The tag lists exactly the assumed inputs, in order, with reason and label "
        "(tests/unit/results/test_traceable.py:88-98).",
    ),
    "REQ-T-04": (
        "checks",
        "Every EQ- and EV-ID in src resolves (tests/unit/results/test_registry.py:175-183); the packaged registry's "
        "issues are exactly the known unsourced gaps, so no dangling EV-ID (:51-58, control at :61-68); every linked "
        "test ID belongs to its own equation (:186-195).",
    ),
    "REQ-T-06": (
        "partial",
        "A measured copper thickness leaves the tag (tests/unit/results/test_traceable.py:112-127); an empty source "
        "and design fields are refused (tests/unit/model/test_provenance.py:94-105). B_r, the field the acceptance "
        "names, is never shown leaving the tag (gap T-06).",
    ),
    "REQ-T-01": (
        "partial",
        "Unit and badge on every row (tests/unit/ui/results/test_results_viewmodel.py:27-36) and every card "
        "(tests/ui/qt_results/test_results_and_checks.py:52-55). Details in one interaction from the keyboard: Space "
        "opens 'How was this computed' and the EQ link opens the guide (tests/ui/qt_e2e/test_ax02_keyboard_only.py:"
        "73-77), on the R_ph card only. The EQ link or kind tag is asserted on one card (test_results_and_checks.py:"
        "41-50); test_results_viewmodel.py:37 compares eq_ids with the data, which an empty pair passes (gap T-01).",
    ),
    "REQ-T-02": (
        "partial",
        "No AnalysisResult field is a bare float, by its annotations (tests/unit/results/test_analysis_result.py:"
        "24-27). The ID walk (:64-84) runs on a result built from traced() with fixed EQ-IDs (:30-44), not on the "
        "computed result of any example, so 'for every example' and the engine's own IDs are not asserted (gap T-02).",
    ),
    "REQ-T-05": (
        "partial",
        "A verified equation links a test (tests/unit/results/test_registry.py:168-172); no result shows `verified` "
        "without a passing linked test (tests/unit/results/test_traceable.py:154-160); `cannot verify yet` gives "
        "`unresolved` (tests/unit/results/test_status.py:61); evidence is written only for a green release run "
        "(tests/unit/results/test_record_passed_tests.py:73-82). No test makes CI fail on a verified EQ whose linked "
        "IDs no passing test carries: record_main exits 0 and prints them as 'carried by no test' (:85-117) (gap "
        "T-05).",
    ),
    "REQ-T-07": (
        "partial",
        "SVG <metadata> holds all five fields and drc_passed for every example and mode (tests/unit/embodic_io/"
        "exporters/test_svg.py:67-81); each DXF part's 999 comments hold them (test_dxf.py:104-120). The PDF test "
        "(test_report_readme_bundle.py:169-177) has no generation date; the README test (:181-198) has the design "
        "hash and registry version only. No test reads the stamp in the project JSON (gap T-07).",
    ),
    "REQ-T-13": (
        "partial",
        "The disclosure's six sections, inputs with a parenthesis, assumption count, sources and validation state "
        "(tests/unit/ui/results/test_results_viewmodel.py:74-87) and Copy trace (:116-128) are checked on one row "
        "each (R_ph, the inductance estimate) of 30. The acceptance asks for a content check per result row (gap "
        "T-13).",
    ),
    "REQ-T-14": (
        "partial",
        "A non-engine chart carries 'Illustrative, not computed' and an engine chart does not (tests/ui/qt_results/"
        "test_charts_compare_guide_export.py:76-106). The stamp and design hash are in SVG (tests/unit/embodic_io/"
        "exporters/test_svg.py:67-81), DXF (test_dxf.py:104-120) and PDF (test_report_readme_bundle.py:169-177). "
        "The README test has no embodic version (:196-198), and no test reads a stamp on the on-screen engine "
        "drawing (gap T-14).",
    ),
    "REQ-T-08": (
        "partial",
        "The union holds the skin-depth value (tests/unit/physics/test_kernels.py:151) and the EC-05 one-sided add-on "
        "(tests/unit/results/test_traceable.py:66). No test raises RANGE_SKIN_DEPTH for w > delta/3, and none compares "
        "e_edge with Agent 2's 5.3 %, 4.2 %, 5.8 % within 0.1 pp (gap T-08).",
    ),
    "REQ-T-09": (
        "partial",
        "Unmarked tests and unknown IDs are found (tests/unit/base/test_trace_matrix.py:35-45) and the release gate "
        "exits 1 on an untested live must row (tests/unit/base/test_tr01_release_gate.py:216-222). No test asserts "
        "that the gate exits 1 on an unmarked test (gap T-09).",
    ),
    "REQ-T-10": (
        "does not check",
        "The union holds two tests that pin 'clearance' in the outcome JSON and the PDF DRC table "
        "(tests/unit/api/test_compute.py:193, tests/unit/embodic_io/exporters/test_report_readme_bundle.py:157). "
        "LG-03, the wording scan of strings and templates (test_plan.md l.393), does not exist on main (gap T-10).",
    ),
    "REQ-T-11": ("does not check", "No test carries REQ-T-11 or names LG-04 on main (gap T-11)."),
    "REQ-T-15": (
        "checks",
        "Truth table over origin, equality and measurement, all eight cases (tests/unit/model/test_provenance.py:"
        "37-57); re-entry invariance and back-to-example restores `example` (:68-78); load reports "
        "INFO_PROVENANCE_EXAMPLE_MISMATCH for a stored entry that disagrees with the packaged example "
        "(tests/unit/embodic_io/project/test_project.py:181-191).",
    ),
    "REQ-T-16": (
        "partial",
        "The EC-05 entry carries threshold, metric bound, calibration, transfer and threshold statuses and the oracle "
        "lists (tests/unit/results/test_registry.py:113-120); e_edge is `assumption` (tests/unit/results/"
        "test_traceable.py:131-137); the disclosure says 'at least' (tests/unit/ui/results/test_results_viewmodel.py:"
        "91-98). OR-07 and OR-08 are listed as dependent in the EC-05 entry, but no test shows the dependency note on "
        "the OR-07 and OR-08 rows (gap T-16).",
    ),
    "REQ-L-01": (
        "partial",
        "String literals in src are scanned per character: Thai and accented letters fail, ASCII and the listed unit "
        "symbols pass (tests/static/test_lg_language.py:12-30, :62); shipped files have no Thai (:108). The scan has "
        "no word allow-list, so '0 words outside the allow-list' is not asserted (gap L-01).",
    ),
    "REQ-L-03": ("does not check", "No test carries REQ-L-03 or names LG-05 on main (gap L-03)."),
    "REQ-L-04": (
        "partial",
        "The union is the contrast tests only (tests/unit/ui/shell/test_contrast_check.py:24-41). The greyscale test "
        "and the token review (white, grey and black chrome; red, blue and green reserved) are not in it (gap L-04).",
    ),
    "REQ-L-05": ("does not check", "No test carries REQ-L-05 or names LG-06 on main (gap L-05)."),
    "REQ-L-07": (
        "checks",
        "A child process under de_DE.UTF-8 and th_TH.UTF-8, compiled privately and checked to be in effect by its "
        "decimal point, formats every finite case exactly as the parent does (tests/unit/results/test_formatting.py:"
        "58-95). The fixture skips where localedef or the glibc sources are missing (:70-71).",
    ),
}

UNION_PINS: dict[str, dict[str, str]] = {
    "REQ-N-13": {
        "tests/ui/qt_e2e/test_ax04_target_size.py": (
            "a52f4de6556330e0249120083f1cc9db5d3452cba64791407ea0d31d98e88b0c"
        ),
    },
    "REQ-N-19": {
        "tests/packaging/test_pk08_licences.py": ("af989b31579097573729eb3efa3e24ff55cb4c1002072847488c11314db4110f"),
    },
    "REQ-T-03": {
        "tests/unit/results/test_status.py": ("53530fed36bce22fbc412e5bf2cc65fd1d62cffefffcaf4ed83d7054d373af5b"),
        "tests/unit/results/test_traceable.py": ("cc6b1b48b602b198dd3cee6a0487d8091d6a1a4764f895136070e776c39161cc"),
    },
    "REQ-T-04": {
        "tests/unit/results/test_registry.py": ("16981e4c58bf6690ff287ef22546a7f69387b56e4570de710650e2136230663e"),
    },
    "REQ-T-15": {
        "tests/unit/model/test_provenance.py": ("f100f5cf76364d3189dd2dc0f033dabf038f17989dc61bdaa8fb95d3c454a504"),
        "tests/unit/embodic_io/project/test_project.py": (
            "9423375594f76167e718087909e7e13da945a95160221881e8e1048d82e5864b"
        ),
    },
    "REQ-L-07": {
        "tests/unit/results/test_formatting.py": ("9b412b7ac6d4d06c880bd361a6d39610b6b99fcccbef2f23b961d450accc7d88"),
    },
}
