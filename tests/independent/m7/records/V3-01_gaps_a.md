Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5

# V3-01 union rulings, REQ-F rows: gap specs for Agent 3 (U-V12a)

Source of the rulings: `tests/independent/m7/v3_01_rulings_f.py` (UNION_RULINGS), read on main 8a4a8a1. The reading
list of each row comes from `python3 tests/independent/m7/v3_01_union.py <collect report>`, where the report is
`pytest --collect-only --req-report <path> tests` on 8a4a8a1 (3202 tests collected). Every statement below is
`verified` by reading the cited source unless it carries another label. No test was run for these rulings.

Result: 27 live must REQ-F rows besides REQ-F-36 (already `checks`). 10 rows are `checks`: F-01, F-04, F-07, F-08,
F-10, F-21, F-32, F-33, F-39, F-40. 17 rows are `partial`: F-02, F-03, F-05, F-06, F-11, F-12, F-13, F-14, F-15,
F-16, F-18, F-19, F-23, F-34, F-35, F-37, F-38. The partial rows need 17 test specs (part A) and 3 acceptance
amendments (part B).

## Part A: test specs

Each spec names the inputs, the expected value and its source, the tolerance, and the defect the test catches. A
test that implements a spec carries the row's REQ marker, so the union of a re-ruling finds it.

### F02-1 (REQ-F-02 e): k_w1 of every A2-TOP §2.2 row to 1e-9

- Inputs: every (Q, 2p) of `A2_TOP_TABLE` (`tests/unit/winding/test_winding_factors.py` l.18-26), outermost turn of a
  one-slot-pitch coil, as `_outermost_turn` builds it.
- Expected: `own_winding.winding_factor(Q, 2p, 1)` (`tests/independent/m2/own_winding.py` l.49, Agent 4's
  Fraction-exact star of slots times the pitch factor). The printed table holds only 3 decimals, so it cannot be the
  1e-9 reference.
- Tolerance: abs 1e-9 (Phase 1 REQ-F-02 criterion e, `docs/phase1/architecture/requirements_draft.md` l.67).
- Where: extend `COMBINATIONS` of `tests/independent/m2/test_winding.py` l.17 to every table row, or add a
  parametrised case to `test_winding_factors.py`.
- Defect caught: a k_d sum or pitch argument off by more than 1e-9 on 15/16, 18/16, 24/16, 9/10 or 18/20, which the
  1e-3 table check (l.47) passes.

### F03-1 (REQ-F-03 d): M4 16/16 generates a board with one phase per pair

- Inputs: 16 coils, 2p = 16, 3 layer pairs, one phase per pair (A, B, C), pair rotations 0, 2 pi/(3p) = pi/24 rad
  (15 degrees mechanical) and pi/12 rad (30 degrees), through `generate_spiral`.
- Expected: a `BoardStack`, not `Unbuildable`; every path of pair k has phase "ABC"[k]; the centre vias of pair B sit
  pi/24 rad and those of pair C pi/12 rad from the matching vias of pair A. Source: Phase 1 REQ-F-03 (d),
  `requirements_draft.md` l.68; A2-TOP §2.3-2.4 as that row cites.
- Tolerance: 1e-9 rad on each via angle.
- Defect caught: M4 refused at generation although the plan accepts it (`test_plan.py` l.98), or a rotation of 2 pi/p
  instead of 2 pi/(3p).

### F05-1 (REQ-F-05): via resistance uses the via count per transition

- Inputs: the CF-11 default design with `/vias/vias_per_transition` 1 and 2 (`src/embodic/model/vias.py` l.13); same
  geometry, `embodic.api.compute`.
- Expected: the via term of the phase resistance with 2 barrels is half the term with 1 barrel. The two-barrel halving
  is CF-04 (`tests/unit/physics/test_kernels.py` l.131). So R_ph(1) - R_ph(2) = n_v x R_via(1) / 2, where n_v is the
  number of via transitions on one phase path and R_via(1) is `via_resistance_ohm(0.3, 25.0, board thickness, rho, 1)`
  (`inferred` from EQ-11; Agent 2 confirms n_v for the CF-11 series path).
- Tolerance: rel 1e-9 (the integrated class of the golden harness).
- Defect caught: the analysis passing a constant 1 to `via_resistance_ohm`, or the field read but not used.

### F06-1 (REQ-F-06 b): reference-mode length at abs 1e-6 mm

- Inputs: the three cases of `tests/unit/generators/test_spiral_length.py` l.43 (CF-11, CF-10, CF-10 pad 1.2).
- Expected: `GOLDEN[case]["total"]` from `fixtures/spiral_r2_turns.json` (Agent 2's reference construction).
- Tolerance: abs 1e-6 mm, as the acceptance states. The test now uses rel 1e-6 (l.56), which is about 4e-4 mm at
  415 mm.
- Defect caught: a length error between 1e-6 mm and 4e-4 mm, for example a lead arc built from a rounded angle.

### F11-1 (REQ-F-11 i): golden comparisons for EQT-16-GR, EQT-17-GR, EQT-19-GR, EQT-22-GR

- Evidence that they are missing (`verified`, scripted): no item of the 8a4a8a1 collection carries these `eqt`
  markers; the registry (`resources/evidence/equations.v1.json`) lists them under EQ-16, EQ-17, EQ-19 and EQ-22. A grep
  of `tests/golden` for `massThermal`, current density and triplen finds no comparison.
- Inputs and expected: the Xcoil functions the registry names in `golden_functions`. EQ-16 and EQ-17 use
  `massThermal`; EQ-19 uses `applyConnection` with a delta winding that has k_w3 not 0 (12/14); EQ-22 uses `analyze`,
  `analyzeWave`, `analyzeElements` and `applyConnection`. The fixtures come from the Node dumper, as the other GR
  fixtures do.
- Tolerance: the kernel class rel 1e-12 for EQ-22 (registry tolerance `exact`), and the integrated class rel 1e-9 for
  mass, the thermal estimate and the circulating current (`assumption`, Agent 2 and Agent 4 confirm). The registry's +/-10 % and +/-30 % are physical tolerances,
  not port tolerances.
- Defect caught: a ported mass, thermal or current-density formula that differs from Xcoil, for example J computed
  from the strand width instead of the trace width.
- EQT-14-O2 (D09 Table 6 oracle) may stay `xfail` under clause (ii).

### F12-1 (REQ-F-12): C1d per-layer B1 spread

- Inputs (`docs/phase1/engineering/checks/c1_field.js` l.19-21): stack-up 6 copper layers of 1 oz in a 0.62 mm board,
  air gap 1.0 mm per side, p = 8, r = 28 mm, double rotor, B_r 1.3 T, mu_r 1.05, magnet thickness 2 mm, alpha_p 0.55,
  G = (0.62 + 2)/2 = 1.31 mm; evaluate `field_harmonic(1, r, z + 1.0, ...)` at each copper z.
- Expected: B1 = 0.6828 / 0.6813 / 0.6805 T, outer to middle, mirrored for the lower half; spread 0.336 %
  (`docs/phase1/engineering/existing_logic_review.md` l.120; test plan UT-PHY-20, `test_plan_draft.md` l.99).
- Tolerance: rel 1e-4.
- Defect caught: every layer evaluated at the board centre (spread 0), or z measured from the wrong face.

### F13-1 (REQ-F-13): every view in at most 2 interactions

- Inputs: shell with the D08 example loaded, on its start view. For each view of the statement (2-D geometry, phase
  assignment, layer configuration, results), a scripted route of mouse clicks or key presses (toolstrip tab plus
  button, or a results tab).
- Expected: the view's widget is visible after at most 2 interactions. The route per view is a table in the test.
- Defect caught: a view moved into a dialog or a second-level menu.

### F13-2 (REQ-F-13): pin the zoom range

- Expected: `ZOOM_MIN == 0.1` and `ZOOM_MAX == 200.0` as literals in `test_ui03_zoom_stays_between_01x_and_200x...`
  (`tests/ui/qt_shell/test_theme_and_geometry.py` l.111 and l.114 compare with the imported constants).
- Defect caught: a range change in `src/embodic/ui/views/geometry_view.py` l.57 that the test follows.

### F14-1 (REQ-F-14): 1000 seeded parameter sets per generator, exceptions and non-finite results

- Inputs: for each of spiral, serpentine and wave, 1000 drafts from a fixed seed, built as `mutated_drafts` builds them
  (`tests/unit/property/strategies.py` l.68-74) from that topology's example draft. Run as a seeded loop
  (`numpy.random.default_rng(seed)`) or as a Hypothesis test with `max_examples=1000` and `derandomize=True` in the
  nightly profile.
- Expected: `compute` returns an outcome for every draft; no issue code starts with `INTERNAL_`; every non-finite
  number in `outcome_to_json(outcome)` belongs to a Traceable that a `RANGE_NON_FINITE_RESULT` issue names.
- Defect caught: an exception or a silent NaN on serpentine or wave input. PR-05 now draws 20 spiral drafts on the
  commit profile (l.84) and checks non-finite results on two fixed cases.

### F15-1 (REQ-F-15): hash and byte identity on every topology

- Inputs: Hypothesis pairs from `serpentine_designs()` (`tests/unit/property/serpentine/strategies.py` l.14) and from a
  wave strategy (none exists at 8a4a8a1); and the five packaged examples for `test_ut_io_01_save_load_save_is_byte_identical`
  (`tests/unit/embodic_io/project/test_project.py` l.62 lists 3 spiral ids).
- Expected: `(design_hash(a) == design_hash(b)) == (a == b)`; first save bytes equal second save bytes.
- Defect caught: a serpentine or wave field missing from `canonical_json`, so two different designs share a hash.

### F16-1 (REQ-F-16): parse the exported JSON project file

- Inputs: the bundle of `test_report_readme_bundle.py` l.204-210, its `motor.embodic.json` member.
- Expected: `jsonschema.validate` against `project.v1.schema.json` passes, and `load_project` gives a design whose
  `design_hash` equals `outcome.design_hash`.
- Defect caught: an export that writes a stale or partial project file.

### F18-1 (REQ-F-18): marker only

- `tests/unit/cli/test_export_command.py` l.84-94 asserts the refusal without `--allow-drc-errors` (exit 2, nothing
  written). Add `REQ-F-18` to its marker. No new assertion is needed.

### F19-1 (REQ-F-19): exporters on the stub's stack

- Inputs: the stub of `tests/unit/generators/test_generator_interface.py` l.37-61, registered the same way; the
  outcome from `embodic.api.compute`.
- Expected: `write_svg`, `write_dxf` (complete, outline, screws), `write_report_pdf`, `write_readme` and
  `save_project` each return an `ExportSummary`; each file equals the same export of the shipped generator's outcome,
  with the time stamp passed explicitly.
- Defect caught: an exporter that reads a generator module or branches on the topology.

### F23-1 (REQ-F-23): the engine never returns modified DesignParameters

- Inputs: the D08 example with `/rotor/air_gap_mm` = 60, above the supported 50 (the case of
  `tests/unit/ui/session/test_session_state_machine.py` l.183-199), through `embodic.api.compute`.
- Expected: `outcome.design == design`, `outcome.design_hash == design_hash(design)`,
  `outcome.design.rotor.air_gap_mm == 60.0`, and a `RANGE_ABOVE_SUPPORTED` issue with suggestion 50
  (`ComputeOutcome` fields, `src/embodic/outcome.py` l.47-48).
- Defect caught: an engine that clamps the input to 50 and returns the clamped design.

### F34-1 (REQ-F-34, REQ-F-35): DRC values within 1e-6 mm, serpentine and wave

- Why Xcoil cannot be the reference: Xcoil measures arcs by chords, with sagitta up to 0.001 mm
  (`tests/golden/m3_serpentine/test_gr20_drc.py` l.86-96), so value diffs are dropped.
- Inputs: every built GR-20 case and every GR-21 case, board by board, including per-phase stacks.
- Expected: the least trace-trace, trace-via and via-via clearance per board from `run_drc` equals an arc-exact
  independent sweep (Agent 4's brute check, `tests/independent/m3/test_drc_m3.py` l.15, extended to report least
  clearances) within abs 1e-6 mm; the verdict follows D-006.
- Defect caught: a clearance off by up to 0.004 mm that the verdict-only comparison passes, and any wave DRC error,
  since no golden test of `tests/golden/m3_wave` runs the DRC.

### F37-1 (REQ-F-37): exact blank-draft lists for serpentine and wave

- Inputs: `parse_draft(blank_draft(TopologyKind.SERPENTINE))` and the same for WAVE.
- Expected: literal tuples of the required pointers in form order, written out by hand as `SPIRAL_BLANK_MISSING` is
  (`tests/unit/model/test_draft.py` l.11), from the required leaves of the serpentine and wave winding specs
  (interfaces.md §2.2) and the shared sections in form order. Do not compute the literal from `field_specs`.
- Defect caught: a serpentine or wave required field dropped from the list, or the list in dataclass order.

### F38-1 (REQ-F-38): first Save after an example opens Save As

- Inputs: shell, load the D08 example from the gallery, trigger `act-save`.
- Expected: a modal `QFileDialog` with `acceptMode() == QFileDialog.AcceptMode.AcceptSave`; the packaged example file
  under `resources/examples` has the same bytes before and after.
- Defect caught: Save writing over the packaged example, or Save without a dialog.

## Part B: acceptance text that the product contradicts (for Fable and Agent 6)

These are not test gaps. A test cannot assert them, because a later decision changed the behaviour.

- F03-2. REQ-F-03 (b) says a pi/Q pair rotation places group-2 centre vias in the gaps. The product refuses that
  rotation with `UNBUILDABLE_PAIRS_ROTATED_APART` (G6 U-E6), and `tests/unit/generators/test_spiral_pairs.py` l.192-205
  asserts the refusal.
- F05-2. REQ-F-05 says "default via counts 60 (M2)". The G6 U-E6 count is Q(2k + 1) for k series groups
  (`tests/unit/generators/test_spiral_series_fan.py` l.88), and that docstring calls the old formula "v1.0".
- F06-2. REQ-F-06 (b) asks for production mode within 1 % of the reference. The G9 fillets remove 12.72 % on CF-11 at
  rho 0.5 mm (DEF-M2d3-02), and `tests/unit/generators/test_spiral_length.py` l.9-11 states that the bound waits for
  Agent 2's U-E5 ruling.
