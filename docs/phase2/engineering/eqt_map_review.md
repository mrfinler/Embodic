Prepared by Agent 2 (Motor Design), model claude-opus-5-5, unit U-E10, 2026-10-13.

# EQT map review on main 6243163

This document rules on every registry test ID (`EQT-nn-kind`) of `equation_registry.json`. It says whether the tests that
carry the ID with `@pytest.mark.eqt` check the ID's acceptance criterion as the registry and `oracle_cases.json` state it.
The evidence rule is interfaces.md section 3.1: an ID passes when at least one test carries it and every carrying test
passes. A skipped, xfailed, failed or not-run record keeps the ID out.

## Rulings applied (D-046, 2026-10-13)

The review below was made on main 6243163 and merged as a3fb8a0. Fable's rulings change it as follows.

- (b) DEF-UE10-02. The EQ-25 text stands. `checks/spiral_reference.py` no longer subtracts 1e-6 rad from the
  terminal-via angle (changelog in its header). The script now gives the CF-11 stub 0.7876736223934756 mm (`verified`,
  ran). `checks/build_oracle_cases.py` rebuilt `oracle_cases.json`. Only CF-11 changed: version 3, and "R per coil-layer
  20 degC" moved from 0.4116841855287007 to 0.4116841739852531 Ω (−2.8e-8 relative, inside its 1e-6). The printed CF-11
  lengths are unchanged. Agent 3 regenerates the fixture in U-M5f with
  `/home/claude/embodic/.venv/bin/python tests/unit/generators/make_r2_goldens.py`, run from the repository root. That
  script imports `spiral_reference` and writes `tests/unit/generators/fixtures/spiral_r2_turns.json`.
- (c) A marker is an all-or-nothing claim. EQT-05-EC loses its marker until the e_edge test below (Phase 2 test 8) exists.
  Then both tests carry it. EQT-02-CF10 gains `test_or_04_d08_builds_three_turns_with_the_half_closing` as a second
  carrier. EQT-23-CF06 is tightened to rel 1e-12 with 2.1999999999999997 and 0.7313131313131312 Ω. Agent 3 does all
  three in U-M5f.
- (d) The registry gains the note "v1.0 rev. U-E10": for an `EQT-nn-CFxx` test the case CF-xx governs over the Phase 1
  `reference_case` and `tolerance` texts. `equation_specification.md` repeats it under "How to read an entry" and in
  "Changes from the Phase 1 draft". `check_consistency.py` and `check_ev_ids.py` pass.
- (e) EQT-14-GR stays Phase 3 with the note in section (c).

## How the review was made

- Map. `pytest tests --collect-only --req-report` on the worktree (3085 tests collected) lists the `eqt` markers of every
  collected test, including the parametrised markers of `EQT_GR_BY_FN` in `tests/golden/m2_physics/test_physics_golden.py`
  l.91 and `tests/golden/m1_geometry/test_gr17_kernels.py` l.139. Result: 63 distinct IDs, 42 carried, 21 carried by no
  test, no marker outside the registry (`verified`, ran). This equals U-M5o's report.
- Acceptance criterion per kind (equation_specification.md l.27): `GR` golden regression against Xcoil engine.js at
  relative 1e-9 (registry `golden_tolerance_default`); `CFxx` the case CF-xx of `oracle_cases.json` with its own expected
  values and tolerances; `O1`, `O2` the oracle band of the equation; `EC` the validity check; `UTk` a rule stated in the
  equation's section of equation_specification.md.
- Each carrying unit test was read in full. For golden tests the review read the compared quantities, the tolerance
  class and the allow-list call. Probe values come from `probe_open_ids.py`, `probe_cf11.py`, `stub_by_spec.py` and
  `probe_phase2.py`, which call the product's public functions with the CF inputs (scratch scripts, not committed; their
  output is quoted where used).
- Verdicts: `correct` (the test checks the criterion as written: inputs, expected value and tolerance), `partial` (what
  is missing is stated), `remove` (none given).

## Summary

| Group | Count |
|---|---|
| Carried, `correct` | 39 |
| Carried, `partial` | 3 (EQT-02-CF10, EQT-05-EC, EQT-23-CF06) |
| Carried, `remove` | 0 |
| Not carried, Phase 2 (test specified below) | 12 IDs in 11 tests |
| Not carried, Phase 3 | 9 |
| After D-046 c | EQT-05-EC moves from carried to Phase 2 (test 8): 41 carried, 13 Phase 2 IDs |

Carried IDs that do not pass on main 6243163 (`verified`, `-m eqt` run): EQT-05-O2 and EQT-06-O2 (OR-07 strict xfail,
section d), EQT-23-GR and EQT-26-GR (carriers in `test_interconnect_golden.py` fail, DEF-UE10-01).

## (a) The map as it is on main 6243163

Status column: `verified` = read in the test and the registry, and the carrying tests ran (counts under "Commands").

| ID | Carrying test(s) | Verdict | Status | Note |
|---|---|---|---|---|
| EQT-01-GR | m3_wave/test_gr23_helpers.py `test_belts_and_slot_angles_match_xcoil`, `test_derive_wave_matches_xcoil_frame_or_refusal` | correct | verified | `slotAngle` and `deriveWave` against Xcoil at KERNEL (rel 1e-12). Serpentine `derive` is compared in tests/golden/m3_serpentine/test_gr23_helpers.py, which carries no marker; its tolerance is not tested in this review. |
| EQT-02-CF10 | unit/generators/test_spiral_generate.py `test_d08_builds_three_turns_with_the_half_closing` | partial | verified | Asserts N = 3 and eye limit 3 (an EQ-25 outcome). CF-10's EQ-02 quantity is the loop-rule count and types [3, trapezoid, triangle, triangle], exact. A loop rule that admits a 4th turn still passes, because the eye caps N at 3. `test_or_04_d08_builds_three_turns_with_the_half_closing` (test_spiral_turns.py l.101) asserts the types and the radial bound 6.006993006993007 at rel 1e-9. Fix: put EQT-02-CF10 on that test as well. |
| EQT-02-CF11 | test_spiral_generate.py `test_default_track_length_matches_cf11` | correct | verified | 8 trapezoids + 3 triangles = 11 loop turns, N = 10 eye-limited, pattern exact. |
| EQT-03-GR | m1_geometry/test_gr17_kernels.py `test_gr17_kernel_matches_xcoil` (36 cases) | correct | verified | `primLength`, `primsLength`, `discretize` at KERNEL_MM (1e-12 mm). |
| EQT-03-CF04 | unit/physics/test_kernels.py `test_cf04_track_resistance_at_20_and_60_degc` | correct | verified | The arc enters as R = ρL/(wt) at rel 1e-12 with fixed ρ, w, t, so an arc-length error shows 1:1. CF-04's arc length 47.12388980384689 mm is not asserted as a length. |
| EQT-03-CF10 | test_spiral_generate.py `test_d08_builds_three_turns_with_the_half_closing` | correct | verified | Total 160.2750 mm at abs 5e-5 mm (rel 3e-7, tighter than CF-10's 1e-6), no lead. |
| EQT-03-CF11 | test_spiral_generate.py `test_default_track_length_matches_cf11` | correct | verified | Total 415.4808 mm at abs 5e-5 mm. Unaffected by DEF-UE10-02 (rel 2.8e-8). |
| EQT-04-UT1 | test_kernels.py `test_ut_phy_02_block_magnet_pole_arc_ratio` | correct | verified | Registry reference 0.853 / 0.547 / 0.402 is printed to 3 decimals; abs 5e-4 is that rounding. |
| EQT-05-GR | test_physics_golden.py `test_physics_kernel_matches_xcoil` (fieldHarmonic, 3 cases) | correct | verified | KERNEL rel 1e-12, open rotor included. `fieldSetup` has no carrier (`inferred` by name search). |
| EQT-05-CF01 | test_kernels.py `test_cf01_field_fundamental_equals_the_1d_magnetic_circuit` | correct | verified | CF-01 inputs, 1.162077823241657 T, rel 1e-9. |
| EQT-05-EC | golden/m2_physics/test_analyse_layouts.py `test_ec05_above_the_cap_downgrades_emf_results_to_unresolved` | partial | verified | Checks both sides of the 10 % rule (limitation below, `unresolved` above). Does not check the value of e_edge against the EC-05 formula (D_e 0.47, c_e 0.9, w = \|B_z1 r Δr\|, d to the nearer magnet end). A wrong D_e, c_e or d passes while the two designs stay on their sides of 10 %. D-046 c: the marker comes off until Phase 2 test 8 (section c) exists. |
| EQT-05-O1 | unit/physics/test_oracles.py `test_or01_d08_line_line_ke_within_the_registry_band` | correct | verified | D08 0.031 V·s/rad in [−8 %, +8 % + e_edge], e_edge computed per design. |
| EQT-05-O2 | unit/physics/test_oracles_m5.py `test_or07_d09_phase_emf_within_the_registry_band` (A, B), `test_or08_d09_synthesised_bz_peak_at_mid_radius_within_5_percent_of_the_figure_reading` | correct | verified | Markers are right. OR-07 is a strict xfail, so the ID stays out (section d). OR-08 checks the registry `additional_cases` value B_pole_centre 0.738 T against D09 Fig. 7 at ±5 % and passes. |
| EQT-06-GR | m2_physics/test_analysis_golden.py `test_result_quantities_match_xcoil`; m3_serpentine/test_gr22_results.py `test_gr22_phase_constant_equals_xcoil`; m3_wave/test_gr22_results.py `test_gr22_ke_per_phase_and_eddy_loss_match_xcoil` | correct | verified | Ke per phase and line at INTEGRATED (rel 1e-9). |
| EQT-06-O1 | test_oracles.py `test_or01_...` | correct | verified | As EQT-05-O1. |
| EQT-06-O2 | test_oracles_m5.py `test_or07_...` (A, B) | correct | verified | Marker right, ID stays out while F-OR07 is open (section d). |
| EQT-07-GR | test_analysis_golden.py `test_result_quantities_match_xcoil`; m3_wave/test_gr22_results.py (2 tests) | correct | verified | `loss_circulating` and phase sums at rel 1e-9. |
| EQT-08-CF09 | unit/winding/test_star_of_slots.py `test_cf09_patterns_and_balance`; unit/winding/test_winding_factors.py `test_ut_wnd_05_cf09_distribution_factor` | correct | verified | All 9 CF-09 rows: exact pattern, exact balance, k_d1 at abs 1e-9. |
| EQT-08-GR | test_gr23_helpers.py (wave) `test_belts_and_slot_angles_match_xcoil` | correct | verified | `beltPhase`, `beltSign` exact; `slotAngle` at KERNEL. |
| EQT-08-UT1 | test_star_of_slots.py `test_ut_wnd_06_rule_and_exact_balance_agree_for_every_small_combination` | correct | verified | The EQ-08 feasibility rule against the exact balance for Q 3 to 48, 2p 2 to 48, Q ≠ 2p. |
| EQT-09-GR | test_physics_golden.py (applyConnection, 2 cases); test_analysis_golden.py; m3_wave GR-22 line quantities | correct | verified | KERNEL and INTEGRATED. |
| EQT-09-CF06 | test_kernels.py `test_cf06_star_and_delta_constants` | correct | verified | Ke_LL star, Kt star, Kt delta at rel 1e-12. |
| EQT-09-O1 | test_oracles.py `test_or01_...` | correct | verified | OR-01 compares Ke_LL peak, which passes through the EQ-09 star conversion. |
| EQT-10-GR | test_physics_golden.py (copperResistivity, traceResistance); m3_serpentine GR-22 strand resistance | correct | verified | KERNEL and INTEGRATED with Xcoil ρ. `primsResistance` has no carrier by name (`inferred`). |
| EQT-10-CF04 | test_kernels.py `test_cf04_track_resistance_at_20_and_60_degc` | correct | verified | Rel 1e-12 at 20 and 60 °C. |
| EQT-10-O2 | test_oracles_m5.py `test_or02_d09_phase_resistance_within_8_percent_of_the_measured_value` (A, B) | correct | verified | D09 1.07 Ω ±8 % (EQ-10). Both variants pass, so the pass does not confirm the turn count (oracle_tests_spec.md OR-02). |
| EQT-11-GR | test_physics_golden.py (viaBarrelArea) | correct | verified | KERNEL. |
| EQT-11-CF04 | test_kernels.py `test_cf04_and_ut_phy_11_via_barrel_resistance` | correct | verified | 1.277202792190775 mΩ at rel 1e-12. |
| EQT-12-GR | test_analysis_golden.py; m3_serpentine GR-22 strand eddy loss; m3_wave GR-22 | correct | verified | rel 1e-9; serpentine difference allow-listed as XD-PHY-002. |
| EQT-13-GR | test_physics_golden.py (skinDepthMm, 2 cases) | correct | verified | KERNEL. |
| EQT-15-GR | test_physics_golden.py (ipc2221Current, 2 cases) | correct | verified | KERNEL. |
| EQT-18-GR | test_analysis_golden.py `test_phase_waveform_matches_xcoil`, `test_result_quantities_match_xcoil`; m3_wave GR-22 line quantities | correct | verified | THD at rel 1e-9; waveform at abs 1e-9 × peak. |
| EQT-19-CF07 | unit/physics/test_closed_forms_m2e2.py `test_eq19_triplen_in_phase` | correct | verified | 0.015 W at rel 1e-12. The kernel returns the loss only; CF-07's 0.1 A follows as √(2P/R_loop) and has no separate output. |
| EQT-20-GR | m2_physics/test_torque_speed_golden.py `test_torque_speed_curve_matches_xcoil` (10 cases) | correct | verified | KERNEL rel 1e-12. |
| EQT-21-UT1 | test_kernels.py `test_ut_phy_17_loss_budget_current` | correct | verified | 1.849 A at abs 5e-4 (the printed precision of the EQ-21 reference). |
| EQT-23-GR | test_analysis_golden.py `test_line_resistance_with_interconnect_copper_matches_xcoil`; m2_physics/test_interconnect_golden.py `test_interconnect_sums_per_phase_match_xcoil` | correct | verified | Markers right. The second carrier fails on main (DEF-UE10-01), so the ID does not pass. |
| EQT-23-CF06 | test_closed_forms_m2e2.py `test_eq23_cf06_star_and_delta` | partial | verified | Asserts 2.2 and 0.731313131 at rel 1e-9. CF-06 states 2.1999999999999997 and 0.7313131313131312 at rel 1e-12. The truncated value is 4.3e-10 off, so the test cannot run at 1e-12 as written. Fix: the CF-06 values at rel 1e-12. The product meets it: probe rel 0.0 for both. |
| EQT-24-GR | test_gr23_helpers.py (wave), 6 tests | correct | verified | `invol`, `involutePoint`, `biarc`, `involutePrims`, `waveTrack`, `deriveWave`/`maxWaveTurns` against Xcoil. |
| EQT-25-CF10 | unit/generators/test_spiral_turns.py `test_or_04_d08_builds_three_turns_with_the_half_closing` (pad 0.6, 1.2) | correct | verified | Types, half closing at N = 3, r_v = 7.15/sin(π/12) at 1e-9 and 27.6255 at abs 5e-5 (CF-10: abs 1e-4). |
| EQT-26-GR | test_analysis_golden.py `test_efficiency_matches_xcoil`; test_interconnect_golden.py (3 tests) | correct | verified | Markers right. The three interconnect carriers error on main (DEF-UE10-01). The result-level test allow-lists XD-PHY-005. |
| EQT-30-GR | test_gr17_kernels.py (30 cases); m1_drc/test_gr18_kernels.py; m1_drc/test_gr18_band_rule.py; m3_serpentine/test_gr20_drc.py (2 tests) | correct | verified | The unchanged kernels at 1e-12 mm. The run_drc-level carriers compare at DRC_VALUE 1e-6 mm and outside [rule − 0.004, rule), which is the changed part of a `reuse with change` gate (conservative sagitta, D-006), not the 1e-9 core. |
| EQT-30-UT1 | unit/drc/test_run_drc.py `test_ut_drc_03_one_micron_intrusion_is_exactly_one_new_violation_at_its_place`, `test_ut_drc_03_inside_epsilon_passes` | correct | verified | Rule − 1 µm fails at the right place, rule − 0.9 µm passes (D-006). |

The 21 IDs no test carries are ruled in sections (b) and (c).

## (b) The five open IDs

| ID | Ruling | Status |
|---|---|---|
| EQT-12-CF05 | Test insufficient. Not a spec defect. | verified (probe) |
| EQT-13-CF05 | Test insufficient. Not a spec defect. | verified (probe) |
| EQT-07-CF07 | Test insufficient. | verified (probe) |
| EQT-25-CF11 | Test insufficient. CF-11's stub value carries a reference-model artefact (DEF-UE10-02). | verified (probe) |
| EQT-14-O2 | Not checkable in Phase 2. Neither a test nor a registry edit can supply the missing band. Phase 3. | verified (read) |

### EQT-12-CF05 and EQT-13-CF05

The brief's example of a spec defect is a chord-discretised geometric value held to a closed-form 1e-9. CF-05 is not such
a value. The skin depth δ = √(ρ/(π f µ₀)) is a scalar closed form. The eddy loss of one straight radial trace in a uniform
field has Σ L_seg = L exactly, so segmentation adds no error. The product meets CF-05 at full precision (`verified`,
`probe_open_ids.py`):

```
EQT-12-CF05 eddy 7.230675123999242e-05 vs 7.230675123999244e-05 rel 2.22e-16; vs registry ref 7.2311e-5 rel 5.88e-05
EQT-13-CF05 skin 5.723108629458205 vs 5.723108629458205 rel 0.00e+00; UT-PHY-13 input 133.3 Hz gives 5.723824152200197
  with Xcoil rho 1.724e-8: eddy rel 5.80e-05, skin rel 2.90e-05
```

The existing tests check the registry's Phase 1 `reference_case` of EQ-12 (7.2311e-5 W at rel 1e-4, computed with Xcoil's
ρ 1.724e-8 by `checks/c9_reference_values.js`) and EQ-13 (5.72 mm at ±5e-3 mm). Those tolerances are the rounding of the
printed values. They cannot see the copper-resistivity constant: swapping the registry ρ 1.7241e-8 for Xcoil's 1.724e-8
moves the results by 5.8e-5 and 2.9e-5, inside 1e-4 and inside ±0.01 mm. The registry text stays as it is.

Missing test for EQT-12-CF05 (Agent 3, U-M5f):
- Inputs (CF-05, `oracle_cases.json`): L 20 mm, w 0.5 mm, t 0.0348 mm, B̂_z 0.7 T, B_t 0, f_e 133.33333333333334 Hz
  (16 poles at 1000 rpm), T 20 °C, ρ₂₀ 1.7241e-8 Ω·m and α 0.00393 /K (registry EQ-10 constants, EV-53).
- Call: `eddy_loss_w(PathField(eddy_bz_sum=[20 × 0.7² × 0.5³], eddy_bt_sum=[0], ...), (1,), 0.0348, 2π f_e,
  copper_resistivity_ohm_m(20, 1.7241e-8, 0.00393))`, as `test_eq12_c9_single_trace` already builds it.
- Expected: 7.230675123999244e-05 W, the CF-05 value (σω²B²w³tL/24, D03 eq. 2 p.5, EV-36). Tolerance rel 1e-9.
- Defect caught: a copper constant other than the registry's (Xcoil's 1.724e-8 gives rel 5.8e-5), a rounded electrical
  frequency, the /12 form of D04 and D10 (a factor 2).

Missing test for EQT-13-CF05:
- Inputs: f 133.33333333333334 Hz, ρ at 20 °C from `copper_resistivity_ohm_m(20, 1.7241e-8, 0.00393)`.
- Expected: `skin_depth_mm` = 5.723108629458205 mm (CF-05, √(ρ/(π f µ₀))). Tolerance rel 1e-9.
- Defect caught: the Xcoil constant 1.724e-8 (rel 2.9e-5), a µ₀ typed with too few digits, a frequency rounded to 133.3 Hz
  (rel 1.25e-4, the input `test_ut_phy_13_skin_depth_at_133_hz` uses).

### EQT-07-CF07

`test_eq07_two_member_identity` uses the registry `reference_case` of EQ-07 (R 1 Ω each, P_c 1e-4 W) at rel 1e-9. CF-07
uses R 0.5 Ω each and rel 1e-12. The difference matters. With R = 1 Ω the defect "R multiplied instead of divided"
(P_c = Σ|E_i − E_grp|² R_i/2) gives the same 1e-4 W as the correct formula, so the existing test cannot catch it. At
R = 0.5 Ω it gives 5.0e-5 W against 2.0e-4 W (`verified`, `probe_open_ids.py`).

Missing test:
- Inputs (CF-07): one phase, one parallel group of two members, E 1.00 and 0.98 V peak in phase (flux linkage 1.0e6 and
  0.98e6 T·mm² at ω_m 1 rad/s, as the existing test encodes E), R 0.5 Ω each.
- Call: `solve_phase_circuit(circuit, lam, {0: 0.5, 1: 0.5}, {}, 1.0)`.
- Expected: `circulating_loss_w[Phase.A]` = 2.0e-4 W (CF-07 third entry, |E₁ − E₂|²/(2(R₁ + R₂)), D01 eq. 2), E_grp 0.99 V,
  R_grp 0.25 Ω. Tolerance rel 1e-12. Probe: P_c 0.0002, rel 1.78e-15 against 0.00020000000000000036.
- Defect caught: member resistance multiplied instead of divided, R_grp in place of R_i, a missing factor 1/2.

### EQT-25-CF11

For the default 12/16 example the tests already check N = 10 eye-limited, r_v 30.7 mm (abs 1e-9 in
test_spiral_turns.py) and the total length at rel 1e-6 (test_spiral_length.py). They do not check the lead, the terminal
stub and the terminal-via radius r_T as separate quantities. The total hides an error that moves length between them.

The probe found that the stub expected value in CF-11 is not EQ-25's rule (`verified`, `probe_cf11.py`,
`stub_by_spec.py`):

```
L1 {'stub': 0.7876736224, 'end_turn': 160.308186417, 'side': 253.0508414571, 'lead': 1.3341074673} total 415.4808089637
reference lead 1.3341074672568292 stub 0.7876852722970421 body 413.35902787406434 total 415.4808206136182
rule pi/Q - asin((max(pad,bw)+s)/(2 r_T)) = 0.246214341304195 reference 0.246213341304195
stub reference (with -1e-6 rad) 0.7876852722970421 stub by the EQ-25 text 0.7876736223934756 rel 1.4790048736723627e-05
```

`checks/spiral_reference.py` l.232 subtracts an extra 1e-6 rad from the terminal-via angle. EQ-25's text
(equation_specification.md l.495 after the D-046 edit, l.492 on a3fb8a0) and `spiral_generator_spec.md` G6 have no such margin. The product follows the text.
So the CF-11 stub (0.7877 mm printed, 0.7876852722970421 in `tests/unit/generators/fixtures/spiral_r2_turns.json`) is
1.48e-5 relative off the rule, outside CF-11's 1e-6. This is a defect in the reference model, not in the product
(DEF-UE10-02). The registry's EQ-25 text is right and stays.

Missing test (expected values from the EQ-25 text, derived with the reference construction for corner A):
- Inputs (CF-11): Q 12, 16 poles, r 18 to 38 mm copper edge, w 0.5, s 0.2, gap 0.2, via pad 0.6, bus width 1.0 mm,
  through `generate_spiral(default_design(), load_registry())`, coil 0, layer L1 (X) and L2 (Y).
- Expected: Σ length of `PrimitiveRole.LEAD` primitives = 1.3341074672568292 mm (rel 1e-6); Σ length of
  `PrimitiveRole.STUB` primitives = 0.7876736223934756 mm (rel 1e-6, `stub_by_spec.py`: r_T = 38 + 0.2 + 0.3 = 38.5 mm at
  angle min(0.2525277317834161, π/12 − asin(1.2/77)) = 0.246214341304195 rad, distance to corner A of turn 0); every
  `ViaRole.TERMINAL` via at r_T = 38.5 mm (abs 1e-9); every `ViaRole.CENTRE` via at r_v = 30.7 mm (abs 1e-6).
- Defect caught: a lead arc at the wrong radius, a terminal via on the bus width instead of max(pad, bw), a stub that
  absorbs length from the body.
- D-046 b resolved the conflict in favour of the EQ-25 text. After Agent 3 regenerates the fixture, its CF-11 `stub`
  equals 0.7876736223934756 mm, and the test may read it from there.

### EQT-14-O2

The registry gives EQ-14 no acceptance band: tolerance "none claimed; target +/-20 % vs LCR measurement after
validation", gate `cannot verify yet`, status `unresolved`. OR-09 records the estimate (A 8.95 µH, −39.5 %; B 5.04 µH,
−66.0 % against D09's 14.8 µH) and asserts only a finite positive value (oracle_tests_spec.md OR-09). That is correct for
a characterisation test, and OR-09 must not carry EQT-14-O2. Writing a band now would invent a tolerance, and the
registry text already says honestly that none exists. The ID stays `not tested`. Closing it needs, in Phase 3: D09's
measurement method, frequency and rotor condition (DEF-08 readings I1 to I3, `unresolved`), and a leakage and end-turn
term for EQ-14 (gap G1). Then the ±20 % target can become a band with a source.

## (c) The 21 IDs no test carries

Status: Phase 2 rows are `verified` (the expected value was reproduced through the product, probe output below);
Phase 3 rows carry their own status.

| ID | Phase | What it needs |
|---|---|---|
| EQT-01-UT1 | 2 | Test 1 below. |
| EQT-02-UT1 | 2 | Test 2 below. |
| EQT-05-CF03 | 2 | Test 3 below (one test carries both CF-03 IDs). |
| EQT-06-CF02 | 2 | Test 4 below. |
| EQT-06-CF03 | 2 | Test 3 below. |
| EQT-07-CF07 | 2 | Section (b). |
| EQT-12-CF05 | 2 | Section (b). |
| EQT-13-CF05 | 2 | Section (b). |
| EQT-14-GR | 3 | embodic has no port of `windingInductance`, `conductorsSerpentine`, `conductorsWave` or `conductorsFromElements` (`verified` by search of src/embodic). `AnalysisResult.inductance_estimate_h` is EQ-14 form (a). See the Phase 3 note on EQ-14 below. |
| EQT-14-O2 | 3 | Section (b). |
| EQT-16-GR | 3 | `mass_g` exists, but no Xcoil `massThermal` dump is in tests/golden/data (`inferred` by key search). A dump from tools/golden/dump_xcoil.mjs with Xcoil's copper density 8.96 g/cm³ injected. |
| EQT-16-UT1 | 2 | Test 5 below. |
| EQT-17-GR | 3 | As EQT-16-GR (`massThermal` gives ΔT). The layout dumps carry `tempRise` only as an input parameter (`verified`, read). |
| EQT-19-GR | 3 | tests/golden/data/physics/apply-connection-delta.json has all EMF phasors 0 (`verified`, read), so it drives no circulating current. A delta dump with a triplen EMF. |
| EQT-22-GR | 3 | No Xcoil current-density value in the analysis dumps (`inferred` by key search). A dump with Xcoil's per-phase-ampere current density. |
| EQT-24-CF08 | 2 | Test 6 below. |
| EQT-25-CF11 | 2 | Section (b). |
| EQT-25-UT1 | 2 | Test 7 below. |
| EQT-27-GR | 3 | No `kw1` in the dumps (`inferred` by key search). A dump of Xcoil's utilisation factor. |
| EQT-28-GR | 3 | No rotor-inertia function in src/embodic (`verified` by search). The port comes first. |
| EQT-29-GR | 3 | No capacitance function in src/embodic (`verified` by search). The port comes first. The CODATA ε₀ change of EQ-29 (U-E5) applies to it. |

Phase 3 note on EQ-14 (D-046 e). The registry gate of EQ-14 is `cannot verify yet` with Xcoil's current-sheet functions
(`windingInductance`, `conductorsSerpentine`, `conductorsWave`, `conductorsFromElements`) as golden functions at 1e-9.
embodic ships the magnetising form (a) instead, so EQT-14-GR has nothing to compare. Phase 3 decides one of two paths.
Port the current-sheet model and add its golden test, or change the gate to name form (a) and drop EQT-14-GR. The
registry stays unchanged until then.

The Phase 3 "dump" rows need Xcoil data that is not in hand. tools/golden/dump_xcoil.mjs can probably write it (not run
in this unit), so each is cheap once Fable schedules it.

### Phase 2 test specifications (Agent 3, U-M5f)

Each value was reproduced through the product's public function (`probe_phase2.py`, output quoted).

1. EQT-01-UT1. Input: the default example (16 poles, Q 12; EQ-01 reference, arithmetic). Assert: the 12 `ViaRole.CENTRE`
   vias sit at `first_coil_angle_rad` + k·π/6, k 0 to 11, abs 1e-9 rad (θ_cp = 2π/Q = 30°). Probe: angles 0, 30, ...,
   330° at 9 decimals. Defect caught: θ_cp = π/p (D08 eq. 3.27, valid only for Q = 2p) gives 22.5°. θ_e = pθ (240° per
   coil) is exercised by the CF-09 pattern test of 12/16.
2. EQT-02-UT1. Input: `loop_turns(CoilFrame.of(SpiralCoilSpec(...), 0.6))` for 18/16 (r 18 to 38, w 0.5, s 0.2, gap 0.2),
   12/16 (same) and D08 (r 11.47 to 45.03, w 2.06, s 0.8, gap 0.8). Expected (EQ-02 text, equation_specification.md l.67 to 68): 7, 11, 3 turns,
   exact. Probe: 7 (stop radial), 11 (lateral), 3 (lateral). Defect caught: a missing `min_side_length` = 2w rule
   (18/16 gives 8).
3. EQT-05-CF03 and EQT-06-CF03. Input (CF-03): `field_table(rotor, 1.1, 0.8, (1,))` with 16 poles, B_r 1.3 T, µ_r 1.05,
   l_m 3 mm, α_p 0.85, magnet 18 to 38 mm; the CF-02 coil (radial sides from 18 to 38 mm at ±15°, arcs at 38 and 18 mm,
   current direction out on −15°); `integrate_path(prims, table, 8, 0.5, edge_decay)`. Expected: |flux_linkage[0]| × 1e-6
   = 1.0201338249421754e-3 V·s/rad, rel 1e-5 (CF-03 basis: Xcoil's 48-step field table and 0.5 mm segments). Probe: rel
   8.2e-6. The margin is 1.8e-6, and the limiter is the 48-step table interpolation (`inferred`). Defect caught: z
   measured from the wrong plane, G of a single rotor, a harmonic index error in u = np/r.
4. EQT-06-CF02. Input: a hand-built `FieldTable(r_inner_mm=18, r_outer_mm=38, harmonics=(1,), bz_t=0.8 T at all 49
   radii, bt_t=0)`, the coil of test 3, p 8. Expected: Ke1 = B₁(r_b² − r_a²) sin(pσ/2) × 1e-6 = 7.75958761790857e-4 V·s/rad,
   rel 1e-9; the two arcs alone give 0 exactly. Probe: rel 0.0, arcs 0.0. Defect caught: sin(σ/2) in mechanical angle,
   an arc that links flux, a missing r in r Δr.
5. EQT-16-UT1. Input (EQ-16 reference, example arithmetic): `mass_g({}, {}, 6461.0, 0.62, 8.89, 1.85)`. Expected
   laminate 6461 × 0.62 × 1.85 / 1000 = 7.410767 g, rel 1e-12 (probe 7.410767000000001). Second case to catch the copper
   volume: `mass_g({"L1": 1000.0}, {"L1": 0.0348}, 6461.0, 0.62, 8.89, 1.85)` (example values): copper
   8.89 × 34.8 / 1000 = 0.309372 g, laminate (4005.82 − 34.8) × 1.85 / 1000 = 7.346387 g, rel 1e-12 (probe
   0.30937200000000004 g and 7.346387000000001 g). Defect caught: copper volume not subtracted from the
   laminate, a g/cm³ to g/mm³ factor error.
6. EQT-24-CF08. Input (CF-08): r_b 20 mm, Δφ 2°. For 9 values of t in [0.3, 1.5] rad, the distance from
   `involute_point(20, 0, t)` to the curve `involute_point(20, Δφ, u)` minimised over u. Expected: r_b Δφ =
   0.6981317007977318 mm, abs 1e-4 mm (CF-08). Probe: max deviation 7.2e-15 mm. Defect caught: a sign slip or swapped sine
   and cosine, which makes the rotated copy non-equidistant.
7. EQT-25-UT1. Input: CF-11 frame (12/16, pad 0.6). Expected (EQ-25 eye rule: r_hi − r_lo = 30.7 − 28.5914 = 2.1086 mm ≥
   (k − 1)(max(pad, w)/2 + pad/2 + s) = (k − 1) × 0.8 mm): `eye(frame, turns, 10, vias=k).fits` is True for k 1 to 3 and
   False for k 4. Probe: [True, True, True, False]. Also put EQT-25-UT1 on
   `test_ut_geo_19_series_groups_get_their_own_centre_via_one_pitch_apart` (test_spiral_pairs.py), which asserts r_v
   30.7, 29.9, 29.1 mm at abs 1e-9. Defect caught: the v1.0 pitch pad + s, or k in place of k − 1.
8. EQT-05-EC, e_edge value (D-046 c; the existing threshold test keeps checking the 10 % rule). Inputs: a hand-built
   `FieldTable(r_inner_mm=18, r_outer_mm=38, harmonics=(1,), bz_t=0.8 T at all 49 radii, bt_t=0)`; two radial lines of
   0.4 mm, each one segment at `max_segment_mm` 0.5: r 18.3 to 18.7 mm at angle 0 (r_m 18.5, d 0.5 mm) and r 27.8 to
   28.2 mm at angle 0.5 rad (r_m 28.0, d 10 mm); D_e and c_e read from `load_registry().equation("EQ-05").validity_checks[0]`
   `.parameters`, as `analyse` does (analyse.py l.256 to 259); G 1.1 mm (example), so c_e G = 0.99 mm. Call
   `edge_leakage_fraction([integrate_path(line_k, table, 8, 0.5, c_e * G) for each line], D_e)`. Expected, from the EC-05
   formula (equation_specification.md l.117 to 118) with D_e 0.47 and c_e 0.9 written as literals: w₁ = 0.8 × 18.5 × 0.4
   = 5.92, w₂ = 0.8 × 28.0 × 0.4 = 8.96, e_edge = 0.47 (w₁ e^(−0.5/0.99) + w₂ e^(−10/0.99))/(w₁ + w₂) =
   0.11285496821276436, rel 1e-12. The first line alone gives 0.47 e^(−0.5/0.99) = 0.28363329517506497. Probe
   (`probe_ec05.py`): 0.11285496821276378 (rel 5.2e-15) and 0.28363329517506497; registry D_e 0.47, c_e 0.9. Defect
   caught: a wrong D_e or c_e in the registry or the kernel, d measured to the farther magnet end, the weight without r,
   the decay length without G.

## (d) EQT-05-O2 and EQT-06-O2 while F-OR07 is open

Both IDs stay `not tested` while F-OR07 is open. `test_or07_d09_phase_emf_within_the_registry_band` carries both and is a
strict xfail with `raises=AssertionError` (test_oracles_m5.py l.238). The report records an xfail as "skipped", and the
evidence rule keeps an ID out when any carrying record did not pass. The `-m eqt` run shows exactly that: EQT-05-O2
{skipped 2, passed 1}, EQT-06-O2 {skipped 2}. The markers are right and stay. The band is never widened (D-045 a).

What closes F-OR07 (oracle_tests_spec.md section "OR-07. D09 phase EMF"):
- G2: D09's real coil turn geometry. The pre-registered variants bracket the published EMF (A +18.7 %, B −7.4 %) and the
  published phase length 3244 mm (+5.3 %, −4.8 %). Neither build is D09's coil.
- Q1: why the computed e_edge on generated layouts (D09 A 2.59 %) is lower than the Phase 1 script's 5.8 %.
- Then OR-07 must fall inside [−5 %, +5 % + e_edge] for the build that matches D09. Agent 3 removes the xfail, and both
  IDs pass. If the matching build stays outside the band, F-OR07 becomes an EMF-chain defect, and the IDs stay out.

## Defects found

| ID | Defect | Reproduce | Owner |
|---|---|---|---|
| DEF-UE10-01 | `tests/golden/m2_physics/test_interconnect_golden.py` fails on main 6243163: `xcoil_roles.classify` raises `ValueError: zip() argument 2 is shorter than argument 1` (xcoil_roles.py l.44). The layout has more paths than Xcoil has objects. U-M5o's GR-19 split is the likely cause (`inferred`). It blocks EQT-23-GR and EQT-26-GR. | `cd /home/claude/wt/U-E10 && PYTHONPATH=/home/claude/wt/U-E10/src /home/claude/embodic/.venv/bin/python -m pytest tests/golden/m2_physics/test_interconnect_golden.py -q` gives "2 failed, 2 passed, 15 errors". | Agent 3 (Fable routes) |
| DEF-UE10-02 | `docs/phase2/engineering/checks/spiral_reference.py` l.232 subtracts 1e-6 rad from the terminal-via angle, which EQ-25 does not state. CF-11's stub (0.7876852722970421 mm) is 1.48e-5 relative off the rule (0.7876736223934756 mm, which the product gives). The same value is in tests/unit/generators/fixtures/spiral_r2_turns.json. CF-10 is unaffected (its start-corner angle is the smaller one). | `stub_by_spec.py` (output in section b). | Fixed in the script and `oracle_cases.json` (D-046 b, this unit); fixture: Agent 3, U-M5f |

## Commands and output

All with `PYTHONPATH=/home/claude/wt/U-E10/src` and `/home/claude/embodic/.venv/bin/python -m pytest ... -q -p no:cacheprovider`.

| Command | Output |
|---|---|
| `tests --collect-only --req-report collect.json` | "3085 tests collected in 10.59s"; 63 IDs, 42 carried, 21 not |
| `tests -m eqt --req-report eqt_run.json` | "2 failed, 447 passed, 2625 deselected, 2 xfailed, 9 errors in 154.96s"; 38 of 42 carried IDs pass |
| `tests/golden/m2_physics/test_interconnect_golden.py` | "2 failed, 2 passed, 15 errors in 1.65s" (DEF-UE10-01) |
| `tests/unit/physics/test_closed_forms_m2e2.py tests/unit/physics/test_kernels.py tests/unit/generators/test_spiral_turns.py tests/unit/generators/test_spiral_length.py tests/unit/physics/test_oracles_m5.py` | "43 passed, 2 skipped, 2 xfailed in 5.38s" |

D-046 continuation (2026-10-13), from the repository root:

| Command | Output |
|---|---|
| `python3 docs/phase2/engineering/checks/spiral_reference.py --json` and `coil_path` on the three cases | CF-11 stub 0.7876736223934756, total 415.48080896371465; CF-10 stub 2.130000000000003 (unchanged) |
| `python3 docs/phase2/engineering/checks/build_oracle_cases.py` | `oracle_cases.json` diff: CF-11 version 2 to 3 and R per coil-layer 0.4116841855287007 to 0.4116841739852531, nothing else |
| `python3 docs/phase2/engineering/checks/build_registry.py` | "30 equations"; diff: one added note, every other key equal |
| `python3 docs/phase2/engineering/checks/check_consistency.py` | "PASS: spec, registry, oracle cases and engine.js agree" |
| `python3 docs/phase2/engineering/checks/check_ev_ids.py` | "missing: [] \| outside phase2_scope: []", exit 0 |

## Open questions for Fable

Questions 1 to 4 of the first hand-back were ruled in D-046 (b to e). None is open.
