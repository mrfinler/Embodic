"""Agent 4's V3-01 union rulings for the live must REQ-F rows (U-V12a), read on main 8a4a8a1.

UNION_RULINGS: REQ id -> (ruling, reason). The reading list of a row is every collected test that carries the row's
REQ marker, names a planned ID, or was found for a planned ID under another label (`v3_01_union.py`). A `checks`
ruling cites test:line for each part of the row's Acceptance cell. A `partial` ruling names what no test of the union
asserts; `records/V3-01_gaps_a.md` holds the test spec for Agent 3. A union ruling replaces the V3-01 sample ruling of
its row.

UNION_PINS: REQ id -> {source: SHA-256} for every test source a `checks` ruling cites, as the file stands at 8a4a8a1
(`git show 8a4a8a1:<path> | sha256sum`). req_audit.py counts the row `verified` only while every hash matches.
"""

T = "tests/unit"
G = "tests/golden"
I2 = "tests/independent/m2"
UI = "tests/ui"

GEN = f"{T}/generators/test_spiral_generate.py"
PIPE = f"{T}/property/test_pipeline_properties.py"
KERN = f"{T}/physics/test_kernels.py"
NEWX = f"{UI}/qt_design/test_new_design_and_examples.py"
TOOL = f"{UI}/qt_shell/test_toolstrip_and_start.py"
EXPC = f"{T}/cli/test_export_command.py"
CMP = f"{G}/harness/compare.py"

UNION_RULINGS: dict[str, tuple[str, str]] = {
    "REQ-F-01": (
        "checks",
        f"(a) continuity 1e-6 mm: {I2}/test_spiral.py:104 (own end points, every path of each example), {GEN}:140, "
        f"{PIPE}:80 (PR-03, random designs). (b) mirror 1e-9 mm: {GEN}:153 (coil 0) and {PIPE}:420 (PR-10, every coil "
        f"of random designs). "
        f"(c) centre via 1e-9 mm on all 12 coils: {GEN}:165. (d) equal circulation: {GEN}:194 (rel 1e-9, every coil).",
    ),
    "REQ-F-02": (
        "partial",
        "(a) 12/10 test_star_of_slots.py:52; (b) 12/14, 24/14, 24/22, 24/26 balanced :66; (c) 12/16 :75; (d) 16/16 "
        "refused test_plan.py:86 and accepted in M4 :98. (e) k_w1 to 1e-9 is asserted only for the five independent "
        f"combinations ({I2}/test_winding.py:37, abs 1e-12); the A2-TOP table rows 15/16, 18/16, 24/16, 9/10, 18/20 "
        "are checked at 1e-3 (test_winding_factors.py:47). Gap F02-1.",
    ),
    "REQ-F-03": (
        "partial",
        "(a) M1 builds test_spiral_pairs.py:63; M2 (series) builds test_spiral_series_fan.py:88. (c) series EMF = "
        "phasor sum at rel 1e-9: test_ut_phy_07_series_chain.py:166. (b) contradicts the product: a pi/Q pair "
        "rotation is refused UNBUILDABLE_PAIRS_ROTATED_APART (test_spiral_pairs.py:204, G6 U-E6), so the acceptance "
        "needs an amendment, not a test (Gap F03-2). (d) M4 16/16 is accepted at plan level only (test_plan.py:98); no "
        "test generates the board or checks the 15/30 degree pair rotations (Gap F03-1).",
    ),
    "REQ-F-04": (
        "checks",
        f"z exact: {T}/model/test_stackup.py:20. Board thickness = sum of layers: test_stackup.py:26 (exact 1.1) and "
        f"{G}/m2_stackup/test_gr07_even_stackup.py:114 (custom lists, board equals Xcoil). Even-spacing helper equals "
        "Xcoil auto mode: test_gr07_even_stackup.py:89 on the 10 auto cases (:75) at KERNEL_MM abs 1e-12 "
        f"({CMP}:38), check raises on a mismatch ({CMP}:300). The thin-board case (:118) is the DEF-U-M6h-01 pin; "
        "D-053a makes that input a refusal, so it is outside the acceptance.",
    ),
    "REQ-F-05": (
        "partial",
        "36 vias (M1): test_spiral_pairs.py:74. Through vias clear foreign copper on the M1, default and D08 boards "
        f"(test_spiral_pairs.py:86, {GEN}:427, :438 trace_via at s within 1e-6 mm). Two gaps: '60 (M2)' contradicts "
        "the G6 U-E6 count Q(2k + 1) that test_spiral_series_fan.py:88 asserts (Gap F05-2, an amendment); the "
        "analysis using vias_per_transition is not asserted, only the kernel's barrel count (test_kernels.py:131) "
        "(Gap F05-1).",
    ),
    "REQ-F-06": (
        "partial",
        "(a) D08 3 loops: test_spiral_turns.py:108 and the half closing n = 3 at :111. (b) reference mode is "
        "asserted at rel 1e-6 against Agent 2's construction (test_spiral_length.py:56), not abs 1e-6 mm against the "
        "true spiral; the 1 % production clause is deliberately not applied (test_spiral_length.py:9-11, "
        "DEF-M2d3-02). Gaps F06-1 (tolerance) and F06-2 (amendment).",
    ),
    "REQ-F-07": (
        "checks",
        f"Block alpha_p 0.853 / 0.547 / 0.402 at r 18 / 28 / 38 mm: {KERN}:89 (abs 5e-4, inside 1e-3). 1-D limit: "
        f"{KERN}:54, B_z1 at r = 1e5 mm equals the 1-D magnetic circuit 1.162077823241657 T at rel 1e-9.",
    ),
    "REQ-F-08": (
        "checks",
        f"Ke_LL = sqrt(3) Ke_ph in star: {KERN}:144 (0.017320508075688773, rel 1e-12). Ke_LL = Ke_ph in delta: "
        f"{KERN}:147. 12/14 delta raises RANGE_DELTA_TRIPLEN: {T}/winding/test_plan.py:109 (WARNING, k_w3 0.5), and "
        "12/16 delta and 12/14 star raise nothing (:125).",
    ),
    "REQ-F-10": (
        "checks",
        f"(a) default spiral passes ({GEN}:418) with trace_trace and trace_via least clearance 0.2 mm within 1e-6 mm "
        f"({GEN}:426), inside [rule - 1e-6, rule + 0.005]. (b) PR-01 brute force on 200 random sets: every pair the "
        f"dense sampler proves below rule - 1e-6 is reported and none above it ({T}/drc/test_properties.py:139, "
        f":142). (c) 1 um intrusion is exactly one violation at 0.199 mm ({T}/drc/test_run_drc.py:359, :361). "
        f"(d) Xcoil values within 1e-6 mm and pass/fail outside the slack band: {G}/m1_drc/test_gr18_band_rule.py:120 "
        f"via compare_drc ({CMP}:265), and the D-006 verdict of its own value at :123.",
    ),
    "REQ-F-11": (
        "partial",
        "Ruled on the registry, not on all 119 union tests: a scripted check of resources/evidence/equations.v1.json "
        "against the eqt markers of the 8a4a8a1 collection finds no test for EQT-16-GR, EQT-17-GR (massThermal), "
        "EQT-19-GR (applyConnection, delta triplen) and EQT-22-GR (current density), and a grep of tests/golden finds "
        "no comparison of those quantities. EQT-14-O2 has no test either; clause (ii) allows it as xfail. Gap F11-1.",
    ),
    "REQ-F-12": (
        "partial",
        "Two-member identity at rel 1e-12: test_closed_forms_m2e2.py:73-75 (CF-07). The C1d per-layer B1 spread "
        "(0.6828 / 0.6813 / 0.6805 T, rel 1e-4) is in no test; a grep of tests for those values finds nothing. "
        "Gap F12-1.",
    ),
    "REQ-F-13": (
        "partial",
        "Zoom reaches its limits and copper pens stay in mm, non-cosmetic: test_theme_and_geometry.py:111-118. The "
        "limits are compared with the product constants ZOOM_MAX and ZOOM_MIN, not with 200 and 0.1, and no test "
        "counts the interactions to reach each view. Gaps F13-1 and F13-2.",
    ),
    "REQ-F-14": (
        "partial",
        "Every BV case gives its code: test_bv_design.py:53 (BV-01), :79 (BV-02), :98 (BV-03), :109 (BV-06), "
        "test_spiral_bounds.py:199 (BV-05, limit = the turns that fit). PR-05 (test_pipeline_properties.py:84-104) "
        "mutates the CF-11 spiral draft "
        "only, with max(20, 4 x COMPUTE_EXAMPLES) = 20 examples on the commit profile (strategies.py:16, :70), and "
        "checks non-finite results on two fixed cases only. Gap F14-1.",
    ),
    "REQ-F-15": (
        "partial",
        "Save, load, save is byte-identical on three spiral examples (test_project.py:67); on all five examples the "
        f"re-save is JSON-equal except saved_utc ({I2}/test_project_round_trip.py:59). A draft "
        "keeps its missing list: test_project.py:178. Hash iff design: test_pipeline_properties.py:241 on random "
        "spiral pairs, provenance and ui excluded at test_project.py:106. Serpentine and wave designs are absent from "
        "the hash property and the byte test. Gap F15-1.",
    ),
    "REQ-F-16": (
        "partial",
        "ezdxf audit 0 errors on every DXF part: test_dxf.py:26; DXF counts equal the Layout: :62 and l.36-69. SVG "
        "parses (test_svg.py:37) with counts equal to the Layout (:50-55). pypdf reads 'Key results' on page 1: "
        "test_report_readme_bundle.py:110. The JSON project file of an export (motor.embodic.json, :210) is never "
        "opened by a parser in the union. Gap F16-1.",
    ),
    "REQ-F-18": (
        "partial",
        "compute --json equals outcome_to_json(compute_project): test_compute_command.py:22. A draft exits 1 and "
        "lists the missing pointers: test_exit_codes.py:69-76. With --allow-drc-errors the wave export writes "
        "(test_export_command.py:43-49). The refusal without the flag is asserted at test_export_command.py:84-94, "
        "but that test carries only REQ-F-33. Gap F18-1 (a marker, no new assertion).",
    ),
    "REQ-F-19": (
        "partial",
        "A stub registered at runtime is dispatched to and passes DRC (test_generator_interface.py:56), analysis "
        "(:59) and the board dump (:61). No exporter runs on the stub's stack. The C1 rule is the MT-01 gate. "
        "Gap F19-1.",
    ),
    "REQ-F-21": (
        "checks",
        f"Fresh start is the empty session with no compute: {TOOL}:33, :40. Example chip on every field: {NEWX}:204 "
        f"(every visible chip) and {T}/ui/session/test_session_state_machine.py:211 (every session chip). Editing "
        f"removes it: {NEWX}:207. Setting the value back restores it: {NEWX}:210. Badges never change: {NEWX}:212 "
        f"across the edit, and {PIPE}:362 (PR-12, badges equal for example and user provenance).",
    ),
    "REQ-F-23": (
        "partial",
        "The scripted clamp shows 'Changed from 60 to 50' with Undo (test_editing.py:106) and Undo restores value and "
        "hash (:109). 'The engine never returns modified DesignParameters' is in no test: no test compares "
        "ComputeOutcome.design with the input for an out-of-range value. Gap F23-1.",
    ),
    "REQ-F-32": (
        "checks",
        f"Configuration matrix driven by field_specs: {NEWX}:142 compares the visible inputs with "
        f"field_specs(topology) "
        f"filtered by applicability ({NEWX}:108) on 48 combinations of the three topologies, outline, magnet, bore "
        f"and fillet ({NEWX}:150). A temporarily inapplicable input shows its reason: {NEWX}:162.",
    ),
    "REQ-F-33": (
        "checks",
        f"Scripted export of the failing wave example: {UI}/qt_results/test_charts_compare_guide_export.py:178 lists "
        "'DRC: 186 failures', the confirmation lists the failures (:185), initial focus is on Cancel (:183), and "
        "Cancel "
        f"writes nothing (:190). The CLI needs --allow-drc-errors: {EXPC}:90-94 refuses with exit 2 and writes "
        f"nothing, {EXPC}:122-125 writes with the flag and warns.",
    ),
    "REQ-F-34": (
        "partial",
        "Board by board: copper counts and sampled distance within 1e-6 mm (test_gr20_layouts.py:122, "
        "layout_compare.py:20), copper z equal to Xcoil within 1e-12 mm (:126), vias and pads (l.154-191); one board "
        "per phase (test_serpentine_generator.py:159) and no clearance violation across boards (:184); 200 inputs per "
        "ported helper (test_gr23_helpers.py:42). DRC values are not compared within 1e-6 mm: the verdict drops value "
        "diffs (test_gr20_drc.py:96) and via-via values are compared on one-board stacks only (:123). Gap F34-1.",
    ),
    "REQ-F-35": (
        "partial",
        "Per style: every style with 2, 4 and 6 layers (test_gr21_layouts.py:50) and every primitive against Xcoil "
        "(l.91-139). EMF at rel 1e-9 (test_gr22_results.py:109) and resistance up to the named via-length cause "
        "(:142). The GR-20 DRC criterion has no wave golden test: no test in tests/golden/m3_wave calls run_drc or "
        "compare_drc. Gap F34-1 covers it.",
    ),
    "REQ-F-37": (
        "partial",
        "parse_draft returns DraftIncomplete with the exact list for a blank spiral (test_draft.py:69) and the exact "
        "one-pointer list on each topology's example (:83); present fields get INVALID issues (:123); every example "
        "round-trips through draft_from_design (:92). The exact blank-draft lists of serpentine and wave are not "
        "asserted (only that each pointer has a widget, :156). Gap F37-1.",
    ),
    "REQ-F-38": (
        "partial",
        "Every visible chip after an example load reads `example` (test_new_design_and_examples.py:204) and every "
        "session chip is ExampleValue (test_session_state_machine.py:211); /name equals the display title "
        "(test_examples.py:54). 'First Save after loading an example opens Save As' is in no union test; "
        "test_walkthroughs.py:160 answers a file dialog on Save but carries no REQ-F-38 marker and asserts neither "
        "the dialog's save mode nor an untouched example. Gap F38-1.",
    ),
    "REQ-F-39": (
        "checks",
        f"Every TOOLSTRIP entry resolves its command ({TOOL}:54, enabled exactly when implemented; :62 an unknown "
        f"command is a startup error) and its icon file ({TOOL}:72). Arrow keys move within a tab and wrap: "
        f"{TOOL}:100, :102. Icons recolour with the theme: {TOOL}:125, :127.",
    ),
    "REQ-F-40": (
        "checks",
        "One reader: read_board_dump wraps decode_board_dump (src/embodic/io/board_dump.py:246). embodic dumps: "
        f"write, read, write is identical ({T}/embodic_io/board_dump/test_board_dump.py:78). Xcoil dumps, which "
        "test_plan.md l.185-191 defines as Xcoil's raw layout mapped to embodic.board-dump v1: decoded and re-encoded "
        f"identically ({G}/m1_layout/test_gr19_layouts.py:119). Non-finite values are tagged and bare tokens refused "
        "(test_board_dump.py:109, :111, :113).",
    ),
}

CITED: dict[str, tuple[str, ...]] = {
    "REQ-F-01": (GEN, PIPE, f"{I2}/test_spiral.py"),
    "REQ-F-04": (f"{T}/model/test_stackup.py", f"{G}/m2_stackup/test_gr07_even_stackup.py", CMP),
    "REQ-F-07": (KERN,),
    "REQ-F-08": (KERN, f"{T}/winding/test_plan.py"),
    "REQ-F-10": (
        GEN,
        f"{T}/drc/test_properties.py",
        f"{T}/drc/test_run_drc.py",
        f"{G}/m1_drc/test_gr18_band_rule.py",
        CMP,
    ),
    "REQ-F-21": (TOOL, NEWX, f"{T}/ui/session/test_session_state_machine.py", PIPE),
    "REQ-F-32": (NEWX,),
    "REQ-F-33": (f"{UI}/qt_results/test_charts_compare_guide_export.py", EXPC),
    "REQ-F-39": (TOOL,),
    "REQ-F-40": (f"{T}/embodic_io/board_dump/test_board_dump.py", f"{G}/m1_layout/test_gr19_layouts.py"),
}

UNION_PINS: dict[str, dict[str, str]] = {
    "REQ-F-01": {
        "tests/unit/generators/test_spiral_generate.py": (
            "83a2104cc24695ab06fbe274106d32329f199b0acd69862e67fca2e14d6a6873"
        ),
        "tests/unit/property/test_pipeline_properties.py": (
            "f746665629010cf86edf10974af6f0a99e6cacdc66b9ddfadf1e7fa3704631c5"
        ),
        "tests/independent/m2/test_spiral.py": ("89ad104603bc962c8e358ac0d3f326b379708e29ddfa51ba54094bcd34f64185"),
    },
    "REQ-F-04": {
        "tests/unit/model/test_stackup.py": ("9da5348f0d0a793e4b21de9232e20b1a76f1b0a6c5f52d4f2296dabaed9b919e"),
        "tests/golden/m2_stackup/test_gr07_even_stackup.py": (
            "9100b34dc9a72b1ef89f6c9408bc217eadba337ffa5b6315c9e49c8d0ff74761"
        ),
        "tests/golden/harness/compare.py": ("8850d18ad76e59aa9a4b66995aaecda9fcc5db9476774698e82ba40ad37aa982"),
    },
    "REQ-F-07": {
        "tests/unit/physics/test_kernels.py": ("74ac893202433b3bebf5d448e6c778940bc1f6863db971486af0b634ef340597"),
    },
    "REQ-F-08": {
        "tests/unit/physics/test_kernels.py": ("74ac893202433b3bebf5d448e6c778940bc1f6863db971486af0b634ef340597"),
        "tests/unit/winding/test_plan.py": ("541264649245ba725e8f83af510032e5bf6ec5bb9538fad7d0ad65e59e862fbc"),
    },
    "REQ-F-10": {
        "tests/unit/generators/test_spiral_generate.py": (
            "83a2104cc24695ab06fbe274106d32329f199b0acd69862e67fca2e14d6a6873"
        ),
        "tests/unit/drc/test_properties.py": ("544afca122923069e0e05679f4b85cc07d9c0a1a856d7201533fa4995da9e0c0"),
        "tests/unit/drc/test_run_drc.py": ("0ad74f9647780ed8eea65f8e2fcbbd057b7eb6c4cfc7d5ce0b185e34593c3e5f"),
        "tests/golden/m1_drc/test_gr18_band_rule.py": (
            "fdcc39084c39896b1ec3127ee5152d51a358662b53affee4e2b6eb6a9d5d2713"
        ),
        "tests/golden/harness/compare.py": ("8850d18ad76e59aa9a4b66995aaecda9fcc5db9476774698e82ba40ad37aa982"),
    },
    "REQ-F-21": {
        "tests/ui/qt_shell/test_toolstrip_and_start.py": (
            "e9acb38dbb6bdf8f0485bb606a1639e39f81d5ff249ffe31be6a87a874f8a05d"
        ),
        "tests/ui/qt_design/test_new_design_and_examples.py": (
            "28aa167bbb4276133f60223a4eaaaba28cd71f133918c6d1f62f966088f0eaef"
        ),
        "tests/unit/ui/session/test_session_state_machine.py": (
            "8ee7ac731a201e6e8f153f4b53f1474176a7f73c5e53d565f8567aa0ecbaf840"
        ),
        "tests/unit/property/test_pipeline_properties.py": (
            "f746665629010cf86edf10974af6f0a99e6cacdc66b9ddfadf1e7fa3704631c5"
        ),
    },
    "REQ-F-32": {
        "tests/ui/qt_design/test_new_design_and_examples.py": (
            "28aa167bbb4276133f60223a4eaaaba28cd71f133918c6d1f62f966088f0eaef"
        ),
    },
    "REQ-F-33": {
        "tests/ui/qt_results/test_charts_compare_guide_export.py": (
            "c2964199ea3bc00d32aad80b8a580dd7cf2ba187bb3f09568f18cf23c6ebcb7c"
        ),
        "tests/unit/cli/test_export_command.py": ("ba3b0886b108c386935adcae2e32d1dabdb2ef74bee441d7978957855edcca6b"),
    },
    "REQ-F-39": {
        "tests/ui/qt_shell/test_toolstrip_and_start.py": (
            "e9acb38dbb6bdf8f0485bb606a1639e39f81d5ff249ffe31be6a87a874f8a05d"
        ),
    },
    "REQ-F-40": {
        "tests/unit/embodic_io/board_dump/test_board_dump.py": (
            "7ee0a9cf47df424ade6bea0146984a33cb48601761dc966924ec590e84630529"
        ),
        "tests/golden/m1_layout/test_gr19_layouts.py": (
            "2a0de75bcdf5fd122ffd6ba8887361c29fc735f7eb0d6eea15524b6132d016a3"
        ),
    },
}
