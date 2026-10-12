Prepared by: Agent 2 (Motor Design Expert), model: claude-opus-5-5. Unit U-E9, 2026-10-12, branch unit/U-E9 from main 7b9b4c9.

# Oracle test specification: OR-02, OR-03 and OR-05 to OR-10, with a Phase 3 proposal for OR-11 and OR-12

This is a reference for the agent that writes the oracle tests. The Phase 2 test plan keeps OR-01 to OR-12
(`docs/phase2/architecture/test_plan.md` section 4, l.178). The rows come from the Phase 1 table
(`docs/phase1/architecture/test_plan_draft.md` l.218-229). Only OR-01 and OR-04 have tests
(`tests/unit/physics/test_oracles.py`). Each section below gives the design to build, the reference value, the
compared embodic quantity, the band, the independence note and the result of a run in this unit.

Every run below is `verified` in the project sense: the probe ran and its output is quoted. No run is a validation by
experiment. No input was changed after a result was seen, and no band was widened.

## How the runs were made

The probe builds each design and calls `embodic.api.compute(design, {})`, the public facade. Run it from the
repository root:

```
PYTHONPATH=src .venv/bin/python docs/phase2/engineering/checks/oracles_probe.py
```

The probe reads every literature input from `oracle_cases.json`. For an unresolved input it takes the pre-registered
`assumed` value (variant A) or `alternative_B` (variant B). Each extra assumption sits in the `ASSUMPTIONS` table of the
probe and in the sections below. The D08 design is the OR-01 design of `tests/unit/physics/test_oracles.py`
(`_d08_design`), imported read-only. The D09 design follows the same pattern from `tests/unit/model/designs.py`
`spiral_design()`.

Probe output on the U-E9 worktree (head before commit 7b9b4c9, wall time 4.9 s):

```
D08 (OR-05, OR-06): turns_achieved 3 | envelope 11.470-62.960 mm | DRC pass | issues [] | e_edge 0.0174
  D08 resistance_phase_20c_ohm 0.433994, at 50 degC 0.485162
D09 A at 20 degC: turns_achieved 8 | envelope 24.800-52.500 mm | DRC pass | issues [] | e_edge 0.0259
  D09 A b1_peak_mid_radius_t per layer [0.846122, 0.846122], ke_phase 0.049776 V*s/rad, inductance 8.9536e-06 H
  D09 A phase A copper: coil paths 3416.4 mm (D09 Table 1: 3244 mm), chain 168.3 mm; B_z waveform peak (n 1-13) at mid-radius 0.7384 T
D09 B at 20 degC: turns_achieved 7 | envelope 19.800-48.700 mm | DRC pass | issues [] | e_edge 0.0334
  D09 B b1_peak_mid_radius_t per layer [0.846122, 0.846122], ke_phase 0.038822 V*s/rad, inductance 5.0355e-06 H
  D09 B phase A copper: coil paths 3088.1 mm (D09 Table 1: 3244 mm), chain 156.4 mm; B_z waveform peak (n 1-13) at mid-radius 0.7384 T

oracle | build                        | field                                  |    embodic |    ref |     diff | band | verdict
OR-05  | D08 full_phase               | resistance_phase_operating_ohm @50C    |    0.48516 |  0.390 |  +24.40% | none | characterisation
OR-06  | EQ-21 on D08's 0.39 ohm      | loss_budget_current_a                  |    1.84900 |  1.840 |   +0.49% | none | characterisation
OR-06  | EQ-21 on embodic R @50C      | loss_budget_current_a                  |    1.65778 |  1.840 |   -9.90% | none | characterisation
OR-02  | D09 A                        | resistance_phase_20c_ohm               |    1.11558 |  1.070 |   +4.26% | [-8.0%, +8.0%] | IN band
OR-02  | D09 A (sweep 40 C)           | resistance_phase_operating_ohm @40C    |    1.20326 |  1.070 |  +12.45% | [-8.0%, +8.0%] | OUT of band
OR-07  | D09 A vs calc                | emf_phase_rms_v                        |    7.37166 |  6.210 |  +18.71% | [-5.0%, +7.6%] | OUT of band
OR-07  | D09 A vs FEA                 | emf_phase_rms_v                        |    7.37166 |  6.200 |  +18.90% | [-5.0%, +7.6%] | OUT of band
OR-07  | D09 A vs meas                | emf_phase_rms_v                        |    7.37166 |  6.220 |  +18.52% | [-5.0%, +7.6%] | OUT of band
OR-08  | D09 A vs 0.72 T              | layers[0].b1_peak_mid_radius_t         |    0.84612 |  0.720 |  +17.52% | [-5.0%, +5.0%] | OUT of band
OR-08  | D09 A vs 0.75 T              | layers[0].b1_peak_mid_radius_t         |    0.84612 |  0.750 |  +12.82% | [-5.0%, +5.0%] | OUT of band
OR-09  | D09 A                        | inductance_estimate_h [uH]             |    8.95358 | 14.800 |  -39.50% | none | characterisation
OR-02  | D09 B                        | resistance_phase_20c_ohm               |    1.01158 |  1.070 |   -5.46% | [-8.0%, +8.0%] | IN band
OR-02  | D09 B (sweep 40 C)           | resistance_phase_operating_ohm @40C    |    1.09109 |  1.070 |   +1.97% | [-8.0%, +8.0%] | IN band
OR-07  | D09 B vs calc                | emf_phase_rms_v                        |    5.74941 |  6.210 |   -7.42% | [-5.0%, +8.3%] | OUT of band
OR-07  | D09 B vs FEA                 | emf_phase_rms_v                        |    5.74941 |  6.200 |   -7.27% | [-5.0%, +8.3%] | OUT of band
OR-07  | D09 B vs meas                | emf_phase_rms_v                        |    5.74941 |  6.220 |   -7.57% | [-5.0%, +8.3%] | OUT of band
OR-08  | D09 B vs 0.72 T              | layers[0].b1_peak_mid_radius_t         |    0.84612 |  0.720 |  +17.52% | [-5.0%, +5.0%] | OUT of band
OR-08  | D09 B vs 0.75 T              | layers[0].b1_peak_mid_radius_t         |    0.84612 |  0.750 |  +12.82% | [-5.0%, +5.0%] | OUT of band
OR-09  | D09 B                        | inductance_estimate_h [uH]             |    5.03549 | 14.800 |  -65.98% | none | characterisation

OR-06 print rounding: R 0.39 read as [0.385, 0.395] ohm gives I in [1.8373, 1.8610] A
```

The D08 loop-only value of OR-05 comes from the existing decomposition script, rerun in this unit:
`PYTHONPATH=src .venv/bin/python docs/phase2/engineering/checks/d08_resistance_decomposition.py` printed
"D08 loop model, span 2 pi / Q (30 deg) 177.2331 mm/coil-layer R 0.381201 ohm (-2.26% vs 0.39)".

## Summary of verdicts

| Oracle | Embodic value | Reference | Difference | Band | Verdict | Status |
|---|---|---|---|---|---|---|
| OR-02 (D09 R) | 1.11558 Ω (A, 20 °C) | 1.07 Ω meas. | +4.26 % | ±8 % | in band | verified (ran); variant B −5.46 % in band |
| OR-03 (D10 R) | not built | 2.15 Ω meas. | n/a | ±8 % | not buildable | unresolved (inputs not printed, G40) |
| OR-05 (D08 R) | 0.381201 Ω loop-only; 0.485162 Ω full phase | 0.39 Ω calc. | −2.26 %; +24.40 % | ±3 % information only; none | loop-only within ±3 %; full phase no band | verified (ran) |
| OR-06 (D08 I) | 1.84900 A | 1.84 A calc. | +0.49 % | not set (EQ-21 exact) | consistent within print rounding | verified (ran) |
| OR-07 (D09 EMF) | 7.37166 V (A) | 6.21 V calc. | +18.71 % | [−5 %, +5 % + e_edge] = [−5 %, +7.59 %] | out of band | verified (ran); cause unresolved; B −7.42 % also out |
| OR-08 (D09 B) | 0.84612 T (b1, fundamental) | 0.72 to 0.75 T figure | +17.5 % to +12.8 % | ±5 % | out of band | verified (ran); cause verified by computation (quantity mismatch) |
| OR-09 (L) | 8.95 µH (A) | 14.8 µH meas. | −39.5 % | none | characterisation | verified (ran); D07 not built (G41) |
| OR-10 (D10 T) | not built | 110.2 °C meas. | n/a | ±30 % on ΔT | not buildable | unresolved (G40, conduction model) |

## Shared D09 build (OR-02, OR-07, OR-08, OR-09)

The D09 board is the concentric board of Tokgöz, Çakal and Keysan (D09). Inputs are those of `oracle_cases.json`
O2-D09 version 2, with the D09 page each row cites.

| Input | Value | Source or label |
|---|---|---|
| coils, poles, layers | 12, 16, 2 | `verified`: D09 p.2 Fig. 1a (EV-62), Table 2 p.3 |
| phase connection | open (6 terminals), `ConnectionTopology.OPEN` | `verified`: D09 p.2 Fig. 1a (EV-62) |
| layer connection | one layer pair L1 to L2 in series per coil | `inferred`: via at each coil's inner end (EV-62) and 3244 mm = 8 coil-layers per phase |
| trace width, clearance | 0.8 mm, 0.2 mm | `verified`: Table 2 p.3 |
| copper, board thickness | 0.07 mm, 1.0 mm | `verified`: Table 2 p.3 |
| turns per coil per layer | A: 8; B: 7 | `unresolved` (G2, UD-25); pre-registered A and B, both run |
| coil centre lines R_i0 / R_o0 | A: 25.2 / 47.6 mm; B: 20.2 / 43.8 mm | `unresolved`; true-spiral inversion of Table 1 p.3 (3244 mm, 171 mm²), DEF-19 |
| `SpiralCoilSpec` radii | centre line ∓ w/2: A 24.8 / 48.0 mm; B 19.8 / 44.2 mm | convention of the D08 build (spiral_generator_spec.md worked example 2) |
| coil gap | 0.2 mm | `assumption`: equal to s, as the D08 build |
| side style | parallel | `assumption`: D09 states no side construction; D08's Fig. 3.4 p.33 is reused. Effect on Ke not estimated in this unit |
| magnets | arc, pole-arc ratio 0.8, r 25 to 46 mm, 2.0 mm, B_r 1.33 T | `verified`: Table 2 p.3, Table 3 p.4 (constant arc `inferred`) |
| µ_r | 1.05 | `unresolved`, pre-registered `assumed` (G23); the sweep 1.03 to 1.10 is pre-registered and was not run in this unit |
| air gap per side, rotor | 1.0 mm, double rotor, back iron 5.0 mm | `verified`: Table 2 p.3, Fig. 4 p.3 |
| operating point | 2000 rpm, 2.0 A line RMS | `verified`: Table 2 p.3; Table 7 p.8 full load |
| winding temperature | 20 °C (sweep 40 °C) | `unresolved` (DEF-11), pre-registered |
| outline | circle r 66 mm, bore 10 mm (`D08_OUTLINE`) | `assumption`: D09 gives no board outline. Does not enter Ke or R |
| vias, chain widths, terminal pads | drill 0.3 / pad 0.6 mm, plating 25 µm; bus ring 1.0 mm | `assumption`: example values of `spiral_design()`. Enter R through the chain and via rows |
| DRC trace and via clearance | 0.2 mm | D09 s, so a DRC pass shows the 0.2 mm table |

Representation (`verified` by the run): both variants build with `turns_achieved` equal to the requested turns, DRC
passes, and compute returns no issue. The generated layout is not D09's coil. Phase A's coil paths total 3416.4 mm in
variant A and 3088.1 mm in variant B, against D09's 3244 mm (+5.3 % and −4.8 %). The inversion that chose the A and B
radii used a true spiral, and the embodic generator places both sides of turn k at offset (k + ½)·w_d with a pitch jog
(D-028). So the published length brackets the two builds instead of matching one.

## OR-02. D09 phase DC resistance

(a) Design. The shared D09 build, variant A primary, variant B reported (pre-registration of O2-D09).

(b) Reference. 1.07 Ω, measured, D09 Table 6 p.7 (Phase 1 register O2). D09 states no measurement temperature.
D09's own calculation is 1.04 Ω (Table 1 p.3).

(c) Compared quantity. `AnalysisResult.resistance_phase_20c_ohm` at the pre-registered 20 °C, and
`resistance_phase_operating_ohm` with `winding_temperature_degc` 40 as the sweep. It is the per-phase series sum of
copper primitives and via barrels (EQ-10, EQ-11), open phases, no neutral. No rms or line conversion applies.

(d) Band. ±8 % (Phase 1 table, EQ-10 tolerance "±8 % vs a measured R at a known temperature"). The temperature is not
known, so the 40 °C run is a sensitivity run, not a second chance. The O2-D09 row also states a consistency check of the
published numbers alone (R₂₀ from 3244 mm = 0.999 Ω ≤ 1.07 Ω). It does not apply to the embodic value.

(e) Independence. D09 is the EC-05 calibration source, but resistance does not use EC-05. OR-02 is independent of EC-05.

(f) Result (`verified`, ran). A: 1.11558 Ω, +4.26 %, in band. B: 1.01158 Ω, −5.46 %, in band. At 40 °C A is +12.45 %
(out) and B +1.97 % (in). The pass does not confirm the turn count: both variants pass at 20 °C. About 168 mm of the
phase path is the embodic series chain at example widths (`assumption`). D09's own link copper is unknown.

## OR-03. D10 phase DC resistance

(a) Design. Not built. Ruling: **not buildable in Phase 2**, and the closest representable build cannot be made either.
D10 (Wang, Pang, Gao, Zhao 2019) uses unequal-width concentric conductors (EV-28: eq. 2 and 3). `SpiralCoilSpec` has
one `trace_width_mm` per coil, so the D10 conductor is not representable. An equal-width approximation would still need
D_mi, D_mo, N per phase per pole and the widths w_ie and w_oe. D10 gives the equations but not the values
(`oracle_cases.json` O3-D10 inputs, all `unresolved` with `assumed` null; new gap G40). Inventing them is forbidden.

(b) Reference. 2.15 Ω, measured with a DC double-arm bridge, D10 p.8 (simulation 2.00 Ω).

(c) Compared quantity once buildable. `resistance_phase_20c_ohm`, with the 12 layers as 2 series groups of 6 parallel
layers (D10 p.3). D10 gives no measurement temperature (`assumption` 20 °C).

(d) Band. ±8 % (Phase 1 table, EQ-10).

(e) Independence. Independent of EC-05 and of D09.

(f) Result. Not run. Status `unresolved`. Closing needs G40.

## OR-05. D08 phase resistance (calculated in the thesis)

(a) Design. The OR-01 D08 design (`tests/unit/physics/test_oracles.py` `_d08_design`), every input from
`oracle_cases.json` O1-D08 version 4, with `winding_temperature_degc` 50, D08's track temperature (Table 4.5 PDF
p.54, printed 49). `D08_POLE_ARC_RATIO` 0.72 and the G 1.4 mm gap stay as OR-01 has them; they do not enter R.

(b) Reference. 0.39 Ω, calculated by D08's loop model (eq. 3.27 to 3.38, PDF p.44 to 45), Table 4.6 PDF p.57
(printed 52). D08 publishes no measured R.

(c) Compared quantity. Two bases, as O1-D08 version 4 defines them.
- `loop_only`: the EQ-03 concentric closed form, span 2π/Q, 8 coil-layers, at 50 °C. This is not an `AnalysisResult`
  field. `checks/d08_resistance_decomposition.py` computes it.
- `full_phase`: `AnalysisResult.resistance_phase_operating_ohm` at 50 °C. It adds terminal stubs, the series chain and
  via barrels to the generated coil body (equation_specification.md EQ-10, "What D08's 0.39 Ω phase resistance
  includes").

(d) Band. `loop_only`: within ±3 %, information only (O1-D08 version 4). `full_phase`: none, regression reference only.
The Phase 1 table left the OR-05 band "to be set by Agent 2/4". This unit sets no new band.

(e) Independence. Independent of EC-05.

(f) Result (`verified`, ran). `loop_only` 0.381201 Ω, −2.26 %, within ±3 %. The residual stays `unresolved`: D08 gives
neither ρ₂₀ nor α_c, and 0.39 is printed to two digits. `full_phase` 0.485162 Ω, +24.40 %, equal to the U-E4 bridge to
six digits, so the regression reference holds. The +24 % is a basis difference, not an error (EQ-10 note).

## OR-06. D08 copper-loss-budget current

(a) Design. EQ-21, I_ph = √((P_Cu/m)/R_ph), with P_Cu 4 W (D08 eq. 4.3 PDF p.53, EV-09; formula reading `inferred`)
and m 3. R_ph is first D08's printed 0.39 Ω, then embodic's `full_phase` R at 50 °C from the OR-05 run.

(b) Reference. 1.84 A, calculated, D08 Table 4.6 PDF p.57.

(c) Compared quantity. `embodic.physics.loss_budget_current_a(4.0, 3, R)`. `AnalysisResult` has no budget-current
field, so the probe calls the public physics function.

(d) Band. Not set in the Phase 1 table ("to be set"). EQ-21's tolerance is "exact", which EQT-21-UT1 tests as an
identity. Against the printed 1.84 A, this unit checks consistency through print rounding only: 0.39 Ω read as
[0.385, 0.395] Ω gives [1.8373, 1.8610] A.

(e) Independence. Independent of EC-05.

(f) Result (`verified`, ran). EQ-21 on 0.39 Ω gives 1.84900 A, +0.49 %. 1.84 A lies inside [1.8373, 1.8610] A, so the
two printed D08 numbers agree if D08's unrounded R lies in [0.3917, 0.3950] Ω (`inferred`, arithmetic). On embodic's
`full_phase` R (0.485162 Ω) the current is 1.65778 A, −9.90 %. That gap is the OR-05 basis difference again.

## OR-07. D09 phase EMF

(a) Design. The shared D09 build at 2000 rpm, variants A and B.

(b) Reference. 6.21 V calculated (Table 4 p.6) and 6.20 V FEA (Table 5 p.6), the Phase 1 row's values. The O2-D09
row adds 6.22 V measured at full load 2 A (Table 7 p.8). The values are RMS (`inferred` from Fig. 15 p.8, about 8.8 V
peak).

(c) Compared quantity. `AnalysisResult.emf_phase_rms_v` = Ke₁·ω_m/√2, the fundamental phase RMS at the operating
speed. The connection is open, so phase is the right basis. The model value is open-circuit, and the 6.22 V
measurement is at 2 A (`unresolved` whether D09 corrected for I·R).

(d) Band. Asymmetric [−5 %, +5 % + e_edge] (Phase 1 table; test_plan.md section 4), with e_edge the computed
`edge_leakage_fraction` of the built design: 2.59 % for A, 3.34 % for B.

(e) Independence. **Not independent of EC-05.** D09 Fig. 7 is the EC-05 calibration source (DEF-23 d). OR-07 tests
EQ-05 and EQ-06 given EC-05.

(f) Result (`verified`, ran). A: 7.37166 V, +18.71 % against 6.21 V, out of band. B: 5.74941 V, −7.42 %, out of band.
This is a finding. Best-evidence explanation (`unresolved`, three candidates):
1. The turn geometry is unknown. The pre-registered variants bracket the published EMF (+18.7 % and −7.4 %), and
   their generated phase lengths bracket the published 3244 mm (+5.3 % and −4.8 %). Neither build is D09's coil.
2. The field is not the cause at mid-radius: the synthesised B_z peak there is 0.7384 T, inside the D09 Fig. 7
   reading (see OR-08). The difference sits in the flux linkage of the coil shape.
3. Radial edge leakage. D09's analytical model fits B_r(r) to FEA (EV-13), and embodic's e_edge is 2.6 %. The
   computed e_edge on the generated layouts is lower than the Phase 1 script's values for the same cases (D09 A 2.59 %
   against 5.8 %, D08 1.74 % against 4.2 %). Why is open (question Q1 below).
OR-07 cannot separate an EMF-chain error from the geometry until G2 closes. Keep the test as a strict `xfail` naming
G2, and report both variants.

## OR-08. D09 field at mid-radius

(a) Design. The shared D09 build. The field does not depend on the turn variant (both give 0.846122 T).

(b) Reference. About 0.72 to 0.75 T, read from D09 Fig. 7 (p.4), `inferred`. The figure plots |B| "at the middle of
the magnet" from FEA, axial position not stated (EQ-05 EC-05 label a).

(c) Compared quantity. `AnalysisResult.layers[i].b1_peak_mid_radius_t`, the EQ-05 fundamental of B_z at the magnet
mid-radius (35.5 mm) and the layer z.

(d) Band. ±5 % (Phase 1 table, EQ-05). With a reading range, this unit reads the band as ±5 % of every value in the
range, [0.7125, 0.7560] T. That is narrower than ±5 % of either end, not wider.

(e) Independence. **Not independent of EC-05.** Same figure as the EC-05 calibration.

(f) Result (`verified`, ran). b1 0.84612 T, +17.5 % against 0.72 T and +12.8 % against 0.75 T, out of band. Cause
(`verified` by computation in the probe): the reference is a full-waveform magnitude and b1 is a fundamental amplitude.
For a flat-topped pole field the fundamental exceeds the peak. The sum of odd harmonics 1 to 13 at the pole centre gives
0.7384 T, inside [0.7125, 0.7560] T (+2.6 % against 0.72 T, −1.5 % against 0.75 T), and equal to Phase 1's 0.738 T.
`AnalysisResult` has no field-peak quantity, so OR-08 as written compares unlike quantities. Fable decides (Q2): add a
synthesised B_z peak to `LayerResult`, or let the test sum `embodic.physics.field_harmonic` itself as the probe does.
Either way the ±5 % band stays. The remaining |B| against B_z difference (B_t at the radial ends) is `inferred` small at
mid-radius and not computed here.

## OR-09. Inductance (characterisation only)

(a) Design. The shared D09 build, variants A and B. D07 (Paul et al., O5) is not built: the Phase 1 extract gives magnet
radii 33/66 mm, 3 mm, B_r 1.17 T, gap 1 mm, 4 oz, PCB 1.6 mm and 30 tracks per phase per layer, but no trace width, end
turn shape or wave construction that maps to a `WaveStyle` (new gap G41). The D07 PDF was not reopened in this unit.

(b) Reference. D09 14.8 µH measured, Table 6 p.7, method, frequency and rotor condition not stated (DEF-08). D07
L_s 22.3 µH measured, Table 4 p.8.

(c) Compared quantity. `AnalysisResult.inductance_estimate_h` (EQ-14 magnetising form, badge `unresolved`, label
"estimate"), converted from H to µH. It has no leakage or end-turn term (G1), so it should read low (`inferred`).

(d) Band. None. EQ-14 is `cannot verify yet`.

(e) Independence. Independent of EC-05 (no edge term in EQ-14).

(f) What is recorded (`verified`, ran). A 8.95 µH (−39.5 %), B 5.04 µH (−66.0 %), with the D09 reading I1
(single phase, other phases open, rotor in place) as the pre-registered `assumption`. The test records value, variant,
reading and reference, and asserts only that the value is finite and positive. It never turns red on the difference.

## OR-10. D10 winding temperature

(a) Design. Not built. Ruling: **not buildable in Phase 2.** The D10 geometry is missing (G40, as OR-03). EQ-17 also
needs the board cooling area and D10's loss split at 12 A/mm², and the Phase 1 row lists the conduction path model as
"Later".

(b) Reference. 110.2 °C at 27 °C ambient, natural cooling, 12 A/mm², measured, D10 p.10. The rise is 83.2 K.

(c) Compared quantity once buildable. `AnalysisResult.temperature_rise_k` against 83.2 K, with
`ambient_temperature_degc` 27 and `line_current_rms_a` set so that `current_density_a_per_mm2` = 12. Compare the rise,
not the absolute temperature.

(d) Band. ±30 % on ΔT (Phase 1 table, EQ-17 `assumption`).

(e) Independence. Independent of EC-05.

(f) Result. Not run. Status `unresolved`.

## OR-11 and OR-12. Phase 3 proposal for Agent 4 (no FEA in this unit)

OR-11 checks EQ-05: B₁ at mid-radius and B_z per copper layer. Agent 4 needs this case:
- Geometry. The D09 rotor (Table 2 p.3, Table 3 p.4): 16 poles, arc magnets 25 to 46 mm, 2 mm, ratio 0.8, 7 mm between
  rotor cores, 1 mm board. Add the D08 rotor (5 mm magnets, T-arrangement, Table 3.2 p.35) for the EC-05 transfer
  check (IT-55).
- Model. A 2-D planar section unrolled at the mean radius (one pole pair, periodic boundaries) for B₁ and B_z(θ) at each
  copper z. For the radial edge effect, a 3-D model or an axisymmetric r-z section through the pole centre.
- Material. B_r 1.33 T, µ_r 1.05 (G23); back iron as linear steel first, then a B-H curve if D08's saturation is in scope.
- Mesh (`assumption`, proposal). At least four elements across the 1 mm gap and each copper layer z; report a
  mesh-refinement pair so the discretisation error is known.
- Quantity. B_z fundamental and waveform peak at the layer z, against `b1_peak_mid_radius_t` and the synthesised peak
  of OR-08. Band ±5 %.

OR-12 checks EQ-12: eddy loss of one trace. A 2-D time-harmonic FEM of one 0.8 × 0.07 mm trace in a uniform sinusoidal
B (axial and tangential components separately) at 266.67 Hz (D09 Table 2), against `loss_eddy_w` per trace. Band ±20 %.

Tool options:

| Tool | What it solves | Licence | Source | Status |
|---|---|---|---|---|
| FEMM 4.2 | 2-D planar and axisymmetric magnetics, Windows | Aladdin Free Public License | EV-115 | verified (extract) |
| Elmer FEM | multiphysics incl. electromagnetics, 2-D and 3-D | GPL v2 for ElmerGUI, ElmerGrid and most solver modules; LGPL for the ElmerSolver library | EV-116 | verified (extract) |

FEMM fits OR-11 (2-D section) and OR-12 (planar time-harmonic). It runs on the user's Windows PC (UD-27 is still open).
Elmer is the only option above for the 3-D edge-leakage case. Neither tool may be bundled or linked from embodic
without a licence review. Agent 4 runs it as an external tool and commits only inputs and results.

## Findings and open questions

- F1 (OR-07, finding). Both pre-registered D09 builds miss the EMF band (+18.7 %, −7.4 %). Cause `unresolved` (above).
- F2 (OR-08, finding). OR-08 compares a fundamental with a waveform magnitude. The like-for-like value is in band.
- F3 (OR-02). In band for both variants at 20 °C. It cannot discriminate the turn count.
- Q1. The computed `edge_leakage_fraction` on generated layouts is about 0.4 to 0.45 of the Phase 1 script values (D08
  1.74 % against 4.2 %, D09 A 2.59 % against 5.8 %). UT-PHY-21 pins the Phase 1 values on the Phase 1 inputs. Which
  construction should the OR-01 and OR-07 bands use? Proposed owner: Agent 4 with Agent 2.
- Q2. How should OR-08 get a field-peak quantity (`LayerResult` field or test-side sum)? Fable.
- Q3. G2 (D09 turns) still blocks OR-07. The D09 author contact (UD-25) is the only closing route on record.
