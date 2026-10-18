Prepared by Agent 2 (Motor Design), model claude-opus-5-5. Unit U-E22, 2026-10-18, decisions D-062 b and c.

# Fix wave F8: what EQ-27 k_u is on each topology, and the EQ-08 symmetry wording

U-M8k could not make EQT-27-GR pass. Xcoil `kw1` and embodic `winding_factor_1` differ on the sector default (0.7841880047079747 against 0.8962148625233994) and on the serpentine default (0.9839828630939396 against 0.983989150027363), and agree on the wave (U-M8k report; D-062 b). Part A rules which value EQ-27 defines on each topology, who owns each gap, and what EQT-27-GR compares. Part B rewords the EQ-08 formula that the equation guide shows (F-UV14-01, D-062 c).

Every number in this document comes from the two probes below unless a line reference says otherwise. No expected value was chosen to make a test pass. Each ruling rests on the registry formula, on Xcoil's own code and on embodic's generator, and the test follows from the ruling.

## How to rerun

```
cd /home/claude/wt/U-E22
PYTHONPATH=src /home/claude/embodic/.venv/bin/python docs/phase3/engineering/checks/f8_eq27_probe.py
python3 docs/phase3/engineering/checks/f8_registry_edit.py
```

`f8_eq27_probe.py` runs `f8_eq27_xcoil.mjs` with node on `/home/claude/serpentine/src/engine.js` (sha256 `3e06593664f3611ab4629803f307a2f336f1b2ac9e1d20d02e2c235d2b30c7f8`, node v22.22.2, the engine of the U-M8k fixtures). Then it runs `analyse()` on the three mapped Xcoil layouts exactly as `tests/golden/m2_physics/test_analysis_golden.py` does (Xcoil copper constants injected). Last, it counts primitive roles on three embodic spiral examples. It writes nothing and takes about 5 s. `f8_registry_edit.py` applies the Part B and Part A registry texts. A second run prints `unchanged`.

## Summary

| Topology | EQ-27 value of the default case | embodic on the mapped layout | Gap owner | Status |
|---|---|---|---|---|
| Spiral (Xcoil sector) | 0.7841880047079747 (64 series conductors) | 0.8962148625233994 (56 counted) | Test mapper `tests/golden/m1_layout/xcoil_map.py` (DEF-UE22-01) | ruling inferred; facts verified (ran) |
| Serpentine | 0.9839891500273656 (three-phase ratio) | 0.983989150027363 | None. Xcoil reports phase A only, a definition embodic does not port | ruling inferred; facts verified (ran) |
| Wave | 0.9659535052408438 | 0.965953505240844 | None | verified (ran, rel 2.3e-16) |

Registry fields changed: EQ-08 `formula`; EQ-27 `formula`, `variables` (Ke1, c, z_c added), `source_notes`, `changes` (one entry added); one entry in `notes`. Gate, status, tests, tolerance and golden functions of both entries are unchanged, and the script checks that every other equation is equal after parsing.

## Part A. EQ-27

### A.1 What the registry says

Before this unit the formula read `k_u = Ke1 / (sum over series conductors of integral B_z1 r dr over the magnet span)` (`docs/phase2/engineering/equation_registry.json`, EQ-27). It did not define `Ke1` and did not say what one series conductor is. Both gaps matter, one per failing topology. The tolerance is `golden 1e-9` with the golden functions `analyze`, `analyzeWave` and `analyzeElements` (verified, read).

The meaning of k_u is fixed by Xcoil's comment at `engine.js` l.975: "numeric vs ideal (all series conductors concentrated on the side centre lines, full magnet span)". The ideal gives every series conductor the full magnet-span integral. Whatever a real conductor misses (radial field variation, a partial length, angular spread) lowers k_u. The registry's first change says the same: k_u "includes radial field variation and end effects" (verified, read).

### A.2 What each program computes

| Code | Numerator | Ideal integral | Conductor count |
|---|---|---|---|
| Xcoil `analyze` (serpentine), l.975-983 | `phases[0].Ke[0]`, phase A only | sum over phase A's layers of the 200-point integral at that layer's z | `p.poles * D.Nt / (series ? 1 : nPairs)` per phase A layer |
| Xcoil `analyzeElements` (sector, overlap wave), l.1883-1892 | `Ke1`, mean of the phases (l.1883) | mean over all layers | `opts.conductorsPerPhase`; the sector passes `coilsPerPhase * 4 * S.N` (l.2478) |
| Xcoil `analyzeWave` (wave), l.2071-2083 | `Ke1`, mean of the phases (l.2071) | mean over all layers | `phases[0].nElements` |
| embodic `src/embodic/physics/analyse.py` l.421-432 | `ke1`, mean of the phases (l.314) | mean over all copper z (`_ideal_integral`, l.735-746) | `PrimitiveRole.SIDE` primitives of phase A divided by the largest parallel group |

All four rows verified (read). embodic uses one form for every topology, the `analyzeElements` form, with the count taken from primitive roles.

### A.3 Ruling SP: spiral (Xcoil sector)

EQ-27 counts 64 series conductors per phase on the sector default, and k_u is 0.7841880047079747, Xcoil's value. Status: inferred (ruling). The facts below are verified (ran, unless marked read).

1. Only the count differs. embodic `ke1` is 0.025877587927124333 and Xcoil `Ke1` is 0.02587758792712433. The ideal integral is the same 200-point sum over the same two copper z. embodic k_u × 56/64 = 0.7841880047079746, which is Xcoil `kw1` at relative 1.4e-16.
2. Xcoil's spiral has a partial radial side. Each turn of `sectorCoilX` (l.2285-2304) has a right side and a left side, except the last turn. Its left side is pushed with kind `lead` (l.2297). That primitive is a Line along the missing left side from the inner end turn up to the centre-via radius, and a `lead` arc then runs to the via (l.2298). The probe finds 7 `side` primitives and one `lead` Line from r = 24.35 mm to 30.56 mm on the canonical coil, inside the magnet span 22 to 40 mm. So each spiral has 2N = 8 radial conductors, one of them partial.
3. Xcoil counts that partial side. `coilsPerPhase * 4 * S.N` = 4 × 4 × 4 = 64 (l.2478), and `seriesTurnsPerPhase` is `coilsPerPhase * 2 * S.N` = 32 (read).
4. embodic's own generator counts it too. `src/embodic/generators/spiral/artwork.py` l.98 emits the last left side as `PrimitiveRole.SIDE` up to the lead point L (`turns.py` l.414), and only the arc from L to the centre via is `LEAD` (l.104). On `spiral_12c16p_default` and `spiral_12c14p` every phase A coil path has 20 SIDE, 1 LEAD and 20 END_TURN primitives (10 turns, so 2N SIDE). On `spiral_12c10p_d08`, a half closing, each path has 5 SIDE and no LEAD (2N − 1 for N = 3 turns built).
5. The mapped layout drops it. `tests/golden/m1_layout/xcoil_map.py` l.18-23 maps every Xcoil `lead` to `LEAD`, the radial Line included. Phase A of the mapped sector default has 56 SIDE and 16 LEAD primitives (8 lead Lines and 8 lead arcs). `analyse.py` therefore counts 56 conductors. Their linkage stays in `ke1`, because Ke integrates every primitive. So the 8 lead Lines are in the numerator and not in the denominator.

Why 64 and not 56. The formula divides by what an ideal winding of the same conductors would link. Counting the partial side in the numerator but not in the denominator makes k_u a ratio of different conductor sets. Such a ratio can pass 1: on any sector layout with Xcoil `kw1` above 56/64 = 0.875, the 56-count gives k_u above 1 (inferred, arithmetic). Three independent sources count 64: Xcoil's formula count, Xcoil's turn count and embodic's generator. The mapped layout is the only source that counts 56.

Defects. The gap is a defect of the test mapper (DEF-UE22-01, Agent 3's test code). It is not a defect of Xcoil. It is not a defect of `analyse.py` on embodic's own spiral layouts, whose SIDE labels follow the definition (inferred from the counts in item 4). This unit does not judge the k_u values of those examples. EQ-14 is not affected by the choice: it uses N = conductors / 2 and k_w1 = k_u, and N·k_u = 28 × 0.8962148625233994 = 32 × 0.7841880047079747 = 25.094016 (relative 1.4e-16). The product is Ke1 / (2 · ideal) whatever the count (verified, ran).

### A.4 Ruling S: serpentine

EQ-27 on serpentine is the three-phase ratio. Its numerator is Ke1, the mean of the three phase Ke_1, and its denominator is the mean of the three phases' ideal sums, each conductor at its own copper z. With an equal conductor count on every layer this is embodic's form. The default case gives 0.9839891500273656 from Xcoil's own parts, and embodic gives 0.983989150027363. Status: inferred (ruling); the numbers are verified (ran).

The probe splits the 6.4e-6 gap. It assembles four variants from Xcoil's `Ke` and Xcoil's `fieldHarmonic`, `fieldSetup` and 200-point integral:

| Variant (numerator over ideal) | Value | Relative difference to embodic |
|---|---|---|
| phase A Ke over phase A's layers (Xcoil `kw1`, l.983) | 0.9839828630939396 | 6.4e-6 |
| mean Ke over phase A's layers | 0.9798798887548054 | 4.2e-3 |
| phase A Ke over the mean of all layers | 0.9881093307544945 | 4.2e-3 |
| mean Ke over the mean of all layers | 0.9839891500273656 | 2.7e-15 |

The conductor count is 128 on both sides (embodic 128 SIDE primitives; Xcoil `conductorsPerPhase` 128, l.1013). The phases sit on different copper z (A at 0.0348 and 0.34088 mm, B at 0.64696 and 0.95304 mm, C at 1.25912 and 1.5652 mm). Phase A's Ke is 0.4187 % above the mean, and the ideal at phase A's z is 0.4194 % above the all-layer mean. The two nearly cancel. The 6.4e-6 that remains is the z dependence of the per-phase k_u itself. analyze's ratio on each phase's own layers gives A 0.9839828630939396, B 0.9840018834229524 and C 0.9839828630939434 (spread 1.9e-5). This also explains why U-M8k's phase-A-only ideal made the gap worse (4.2e-3). It changed the denominator and kept the mean numerator.

Why the three-phase ratio:

1. The formula's numerator is `Ke1`. Xcoil's own `Ke1` is the phase mean (l.988), and so is embodic's `ke1`. Xcoil `analyze` divides `phases[0].Ke[0]` instead, so it does not compute the formula as written (verified, read).
2. Xcoil's other two k_u functions, `analyzeElements` (l.1892) and `analyzeWave` (l.2083), use the mean `Ke1` and the all-layer mean ideal. `analyze` is the only one that uses phase A (verified, read).
3. A winding result should not change when the phases are renamed. Phase A's value would become B's 0.9840018834229524 if B's layers were phase 0 (inferred, because only the per-phase values were run, not a renamed design). The three-phase ratio is symmetric in the phases by construction.

Defects. Neither value is a numerical error. Xcoil's `kw1` is a correct phase-A ratio of a different definition. embodic computes the formula. The registry text was the gap. It named `analyze` as a 1e-9 golden function without saying that its phase-A form is not ported. This unit adds that as a change and defines `Ke1`, the conductor and its z (DEF-UE22-03, Agent 2's own text, fixed here).

### A.5 Ruling W: wave

The wave-turns-2 case has wave style `involute`, so `computeWave` does not branch to the overlap code (l.1928) and calls `analyzeWave` (l.1996). Both programs use the mean Ke1, the all-layer ideal and 62 conductors (embodic 62 SIDE primitives; Xcoil `nElements` 62). embodic 0.965953505240844 against Xcoil 0.9659535052408438, relative 2.3e-16. Status: verified (ran). No defect.

### A.6 What else the gaps could have been

Sector. A field-model difference would not give an exact rational ratio, and the ideal sums are the same code path on the same z. A phase-mean effect is ruled out because the three sector phase Ke values agree to 6e-16 in Xcoil and 3e-16 in embodic. A parallel-member effect is ruled out because both sides have one layer pair (`coilLayers` 2) and groups of one member. Serpentine. The count is 128 on both sides, and the field model is ruled out because the formula assembled from Xcoil's parts matches embodic at 2.7e-15. Each statement is verified (ran) on the default cases only. No other parameter set was run.

### A.7 What EQT-27-GR compares

EQT-27-GR compares embodic `AnalysisResult.winding_factor_1` with the EQ-27 value of the same layout computed from Xcoil's numerics, at relative 1e-9 (the `INTEGRATED` class, `tests/golden/harness/compare.py` l.39). On spiral and wave that value is Xcoil `kw1`. On serpentine it is Xcoil's `Ke1` × 1e6 over the all-layer mean of `analyze`'s ideal integral (l.977-981) times Xcoil `conductorsPerPhase`.

Why 1e-9. It is the registry tolerance of EQ-27. k_u is a ratio of Ke1, which GR-22 already holds at 1e-9, and of a 200-point sum both programs evaluate with the same arithmetic, so its relative error is at most the sum of the two. After the ruling the measured gaps on Linux are 1.4e-16 (sector, by arithmetic until the mapper is fixed), 2.7e-15 (serpentine) and 2.3e-16 (wave). The smallest defect named in this document is 6.4e-6 (phase A in place of the three-phase ratio). So 1e-9 sits more than five orders of magnitude above the measured gaps and almost four below the nearest named defect. No Windows run was made (not tested).

### A.8 Test specification for Agent 3

Build on the draft `scratchpad/U-M8k-eqt27-draft.patch` (read, not applied). Every expected value below is the probe's output. Do not derive new ones.

1. Mapper (DEF-UE22-01), `tests/golden/m1_layout/xcoil_map.py`. In a sector layout, map the `lead` Line that starts at the inner end-turn corner `iL` (`engine.js` l.2297 for arc ends, l.2301 for chord ends) to `PrimitiveRole.SIDE`. It is the `lead` primitive with no end point at the coil's centre via. The arc of l.2298 and the chord Line of l.2302 end at the via and stay `LEAD`. In the Y layer the coil is reversed (l.2380), so the same Line appears with its ends swapped. Acceptance: phase A of `layout-sector-default` has 64 SIDE and 8 LEAD primitives (56 and 16 before). Run the other users of the mapper before committing: `tests/golden/m1_layout/test_gr19_layouts.py`, `tests/golden/m1_drc/test_gr18_band_rule.py`, `tests/golden/m3_wave/test_gr21_layouts.py`, `tests/golden/m3_serpentine/test_gr23_helpers.py`, `tests/golden/m2_physics/test_analyse_layouts.py`, `tests/golden/m2_physics/test_gr_f11_mass_thermal_current.py` and `tests/golden/m1_geometry/test_gr17_kernels.py`.
2. Dump lever, `tools/golden/functions/physics.mjs`. `utilisationFactor` returns an object `{kw1, ku, conductorsPerPhase, Ke1}` from `E.compute(params).analysis`. On sector and wave, `ku` is `kw1`. On serpentine, `ku = Ke1 * 1e6 / (mean over r.layout.layers of ideal(L.z) * conductorsPerPhase)`. Here `ideal(z)` is the sum over i < 200 of `fieldHarmonic(1, r_i, z + p.airgap, F).Bz * r_i * (rB - rA) / 200`, with `r_i = rA + (rB - rA) * (i + 0.5) / 200`, `rA = p.magnetRIn`, `rB = p.magnetROut` and `F = E.fieldSetup(E.derive(r.params), r.layout)`. `idealAt` in `docs/phase3/engineering/checks/f8_eq27_xcoil.mjs` is this computation. The serpentine fixture note says that `ku` is the EQ-27 three-phase ratio from Xcoil's parts and that `kw1` is phase A only (fix_wave_f8.md A.4).
3. Fixtures. Dump the three cases of the draft. The dump must give these values:

| Fixture | kw1 | ku | conductorsPerPhase | Ke1 |
|---|---|---|---|---|
| utilisation-factor-sector-default | 0.7841880047079747 | 0.7841880047079747 | 64 | 0.02587758792712433 |
| utilisation-factor-serpentine-default | 0.9839828630939396 | 0.9839891500273656 | 128 | 0.06426723542757902 |
| utilisation-factor-wave-turns-2 | 0.9659535052408438 | 0.9659535052408438 | 62 | 0.0308795907787231 |

4. Test `test_utilisation_factor_matches_eq27` in `tests/golden/m2_physics/test_analysis_golden.py`, marked `@pytest.mark.eqt("EQT-27-GR")` and parametrised over `CASES`. Assert `golden["ku"] > 0`. Then assert `compare_scalar(golden["ku"], results[case].winding_factor_1.value, INTEGRATED).ok`. Docstring: "Defect caught: a k_u that drops the partial last side of a spiral from the conductor count (sector 0.896 against 0.784), divides phase A's Ke instead of the three-phase ratio (serpentine, 6.4e-6), evaluates the ideal at phase A's z only (4.2e-3), or loses the 1e-6 scale (EQ-27)."
5. Test `test_mapped_side_count_is_the_series_conductor_count`, same file, parametrised over `CASES`. The SIDE primitives of phase A in `_stack(_raw(case))`, divided by the largest parallel group, equal the fixture's `conductorsPerPhase`. Docstring: "Defect caught: a mapping that loses or adds a radial conductor, such as the sector's partial last side (56 against 64)."
6. Show each test red before it counts. Revert the mapper change, and the sector case fails in both tests. In a scratch copy of `analyse.py` l.432, put phase A's Ke in place of `ke1`, and serpentine k_u becomes about 0.98811 (relative 4.2e-3). Remove `T_MM2_TO_V_S_PER_RAD`, and all three cases fail by 1e6. Quote the real failure lines in the report.

The registry keeps `tests: ["EQT-27-GR"]`. The draft's `test_every_physics_fixture_has_a_port` constraint is met because test 4 reads all three fixtures.

## Part B. EQ-08 wording (F-UV14-01)

The EQ-08 formula ended with `balance = signed angle sets of B and C equal those of A shifted by 4Q and 8Q units`. That clause is a test on phase angles alone. The user's rule forbids calling it balance (D-051 b). It now reads `symmetric 3-phase pattern (a property of the coil pattern only) = signed angle sets of B and C equal those of A shifted by 4Q and 8Q units`. The arithmetic and every other EQ-08 field are unchanged (verified, `f8_registry_edit.py` checks). The shipped parser `parse_registry` reads the edited file, and `equation_topic` renders the new text (verified, ran). `docs/phase3/engineering/checks/guide_name_scan.py` reports 0 program names in 326 displayed texts (verified, ran).

UI strings that follow from the registry once Fable syncs it (`tools/sync_registry.py` l.47 copies the docs registry verbatim to `resources/evidence/equations.v1.json`):

1. The equation guide, topic EQ-08, row "Formula" (`src/embodic/ui/viewmodels/results.py` l.780; label `guide.eq.formula`, `src/embodic/ui/strings/results.py` l.161). Verified (read).
2. The "How was this computed" disclosure line `EQ-08: {name}. {formula}` (`results.py` l.258) on every result row that carries EQ-08. The phase plan's k_w,n values carry it (`src/embodic/winding/winding_factors.py` l.64, built at `winding/plan.py` l.81). Inferred: this unit did not open the views that show those rows.
3. The same two places show the new EQ-27 formula, in guide topic EQ-27 and in the disclosure of the `winding_factor_1` row.

No file under `src/embodic/ui/strings/` changes. The design-view strings already say "Symmetric 3-phase pattern" (`src/embodic/ui/strings/design.py` l.218-231, verified, read). Three texts keep the word on purpose. The EQ-08 `source_notes` quote EV-89's own term "balance condition", which the guide does not show (D-051 c). The `reference_case` key `balanced` and the replaced function name `balancedSectorList` are internal identifiers (D-052 c). The tolerance line of the disclosure (`results.py` l.277) shows the registry's `tolerance.basis` (as `source_ref`), and this unit leaves both tolerances unchanged.

After the sync, rerun `python tests/static/lg_scan.py`. It renders the guide texts (l.271-275), so the LG-01 word list can change from 804 words (inferred). Any test that compares the shipped `equations.v1.json` with the docs registry fails until the sync (inferred).

## Defects

| ID | Owner | Defect | Reproduce | Status |
|---|---|---|---|---|
| DEF-UE22-01 | Agent 3 (test code) | `xcoil_map.py` l.23 maps the radial `lead` Line of every Xcoil sector coil to `LEAD`, so `analyse()` counts 56 conductors in place of 64 and the mapped sector k_u is 0.896 in place of 0.784 | Run `f8_eq27_probe.py`. Part 1 prints phase A roles `side 56, lead 16`, and `k_u x sides / count` equal to Xcoil `kw1` at 1.4e-16 | verified (ran) |
| DEF-UE22-02 | Agent 3 (UI labels) | `src/embodic/results/labels.py` l.19 shows `winding_factor_1` as "Fundamental winding factor" (comment "EQ-08 k_w1") and l.61 as symbol `k_w1`. The value is EQ-27 k_u (`analyse.py` l.527, quantity `utilisation_factor_k_u`), and EQ-27's first change requires the name "utilisation factor k_u" | Read the three lines | verified (read) |
| DEF-UE22-03 | Agent 2 (registry) | EQ-27 did not define Ke1 or a series conductor, and held serpentine to `analyze` at 1e-9 without recording that its phase-A form is not ported | Registry EQ-27 before this unit | fixed here; verified (read) |

## Follow-ups

1. Agent 3 adds a generator test that pins the SIDE contract EQ-27 now names. A full-closing spiral path has 2N SIDE primitives and a half-closing path has 2N − 1 (Part 2 of the probe: 20 for N = 10, 5 for N = 3). A role change would otherwise move k_u, and EQ-14's N, without a failing test.
2. Agent 2 updates `docs/phase2/engineering/equation_specification.md` l.540-551 in a later unit. It still has the old EQ-27 formula text, and its validity line says no downstream result uses k_u. EQ-14 does (`analyse.py` l.435), though only through N·k_u, which the count does not change (A.3). That file is outside this unit's scope.
3. Fable renames the label per DEF-UE22-02 in the same merge as the sync, so that the guide's EQ-27 text and the result label agree.

## Open questions

None for the user. Fable may decide whether the results should also list the three per-phase k_u values. This ruling reports one winding value.
