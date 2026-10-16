Prepared by: Agent 2 (Motor Design Expert), model: claude-opus-5-5. Unit U-E11, 2026-10-16, worktree U-E11 from main 99647cb. Section 1 "Variant C" added in U-E13, 2026-10-16, worktree U-E13 at 53253b1.

# Phase 3 engineering verification plan: F-OR07 diagnosis, OR-11 and OR-12 FEA cases, measurement plan, Phase 3 EQT ids

This is a reference and plan for Agents 3, 4 and 5 and for Fable. Part 1 reports runs made in this unit. Parts 2 to 5
are plans. No FEA ran and no board exists (D-048 f). Nothing here changes a band, an input, `src/` or `tests/`.

Status words follow the standing orders. "verified" means read in the source or reproduced by running something.

## How to rerun

From the repository root:

```
PYTHONPATH=src /home/claude/embodic/.venv/bin/python docs/phase3/engineering/checks/f_or07_probe.py      # 2 min 33 s
PYTHONPATH=src /home/claude/embodic/.venv/bin/python docs/phase3/engineering/checks/f_or07_probe.py --no-grid
PYTHONPATH=src /home/claude/embodic/.venv/bin/python docs/phase3/engineering/checks/or12_reference.py
PYTHONPATH=src /home/claude/embodic/.venv/bin/python docs/phase3/engineering/checks/or07_variant_c.py     # 8 s
```

`f_or07_probe.py` imports the pre-registered D09 builds of `docs/phase2/engineering/checks/oracles_probe.py`
read-only. Each probe changes one thing against variant A and calls `embodic.api.compute`. The D09 text was
re-extracted in this unit from `EPA-2020-0622-FINAL.pdf` (10 pages) with `pdftotext`.

## 1. F-OR07: why OR-07 variant A reads +18.7 %

### The feedback loop

The loop is `f_or07_probe.py`, line P0. It reproduces the D-045 a symptom on this worktree:

```
P0 baseline A: emf_phase_rms_v 7.37166 V (+18.71%); band [-5.00%, +7.59%]
P0 baseline B: emf_phase_rms_v 5.74941 V (-7.42%)
Instrument: recomputed |sum lambda| phase A 0.049776204 vs product ke_phase 0.049776204 (rel 0.00e+00)
```

The instrument line recomputes phase A's Ke from the public kernels `field_table` and `integrate_path`. It equals the
product to the last digit. So the field-substitution probes below (H-edge, H-2D) measure the product's own chain with
one table changed, not a second model.

A cause must remove 9.36 % of the A value to reach the band edge (model/calc must fall from 1.1871 to
1.05 + e_edge = 1.0759).

### Hypotheses, probes and results

Each row changes one variable. "Δ" is the change of `emf_phase_rms_v` against variant A, in points of deviation
from D09's 6.21 V (Table 4 p.6).

| # | Hypothesis | Probe (one change) | Result | Status |
|---|---|---|---|---|
| H1 | Arithmetic: rms vs peak, speed, Ke chain | Ke·ω_m/√2 by hand; f_e | 0.049776 × 209.4395 / √2 = 7.37166 V, equal to the product. f_e = 266.67 Hz equals D09 Table 2. Peak would be 10.43 V (+68 %), so D09's values are not peak-vs-rms swapped. D09 Fig. 15 shows about 8.8 V peak (Phase 1 register O2, `inferred`) | verified (ran); ruled out |
| H2 | Coil count or connection: wrong coils per phase, a reversed coil | Count phase A's coil paths and the phasor alignment | 8 coil paths on L1 and L2 (4 coils × 2 layers); \|Σλ\|/Σ\|λ\| = 0.999919. A reversed coil would lower the EMF, not raise it | verified (ran); ruled out |
| H3 | Input transcription from D09 | Read every O2-D09 input against D09 Table 2 p.3 and Table 3 p.4 | All printed values match: 2000 rpm, 266.67 Hz, 16 poles, 2 layers, w 0.8, s 0.2, Cu 70 µm, PCB 1 mm, gap 1 mm, B_r 1.33 T, magnet 2 mm, core 5 mm, OD 92 / ID 50 mm, L 7 mm, α_p 0.8. Two inputs are readings, not prints: magnet radii 25/46 mm = the 50/92 mm diameters (`inferred`), constant arc (`inferred`) | verified (read) |
| H3a | Magnet span narrower than the rotor diameters | Span 26–45, 25–45, 26–46 mm | +15.15 %, +15.73 %, +18.12 % (Δ −3.6, −3.0, −0.6) | verified (ran); at most a third of the gap |
| H3b | Pole-arc ratio | α_p 0.75, 0.70 | +15.31 %, +11.21 % (Δ −3.4, −7.5). D09 prints 0.8 | verified (ran); would need an input D09 contradicts |
| H4 | B_r | B_r 1.20 T (sensitivity only) | +7.10 % (Δ −11.6). D09 prints 1.33 T twice | verified (ran); ruled out as a cause |
| H5 | µ_r (G23) | 1.03, 1.10 (pre-registered sweep) | +19.73 %, +16.23 % (Δ +1.0, −2.5) | verified (ran); ruled out |
| H6 | Axial position: D09 does not state where its field is taken | B1 at r 35.5 mm, copper z 1.035 mm vs centre plane 1.5 mm | 0.84612 T vs 0.84150 T (−0.55 %) | verified (ran); ruled out |
| H7 | 2-D field assumption (no radial variation of the pole field) | Replace B1(r) by the flat B1(35.5 mm) on the generated A paths | Ke × 0.9988, +18.56 % (Δ −0.15) | verified (ran); ruled out |
| H8 | Radial edge leakage (oracle_tests_spec.md §OR-07 item 3) | Multiply the field by k(r) = Fig. 7 FEA / 2-D model (plateau-normalised, the Phase 1 method); on the generated A paths | Ke × 0.9759, +15.84 % (Δ −2.9). The EC-05 value of the same build is e_edge 2.59 %, so EC-05 agrees with the digitised profile | inferred (Fig. 7 digitisation, `edge_zone_d09.js`); explains about a quarter |
| H8a | D09's own field recipe, B_max × B_r(r) (D09 p.5 eq. 7) | B1(35.5 mm) × Fig. 7 shape normalised at 35.5 mm | Ke × 0.9737, +15.59 % (Δ −3.1) | inferred; same size as H8 |
| H9 | End-turn linkage | Read `integrate_path` (emf.py l.150–161) | An arc at constant r adds rm·(c2 − c1) = 0; copper outside the magnet span is skipped. End turns link no flux in a B_z model by construction. The 3-D part of that effect is H8 | verified (read) |
| H10 | Turn count (G2) | N 6, 7, 8, 9 at A's centre lines 25.2/47.6 mm | +7.97 %, +14.93 %, +18.71 %, +19.94 %. Turns add from the outside in: 1.359, 1.388, 1.295, 1.113, 0.893, 0.658, 0.432, 0.235 V | verified (ran); lever 1 to 7 points per turn |
| H11 | Outer radius (G2): A's outer centre line is 1.6 mm outside the magnet (47.6 vs 46 mm) | N 8 at 25.2/46.6 | +10.36 % (Δ −8.4 for 1 mm) | verified (ran); lever 8 points per mm |
| H12 | Side construction (`assumption` "parallel" in U-E9; EV-62 calls D09's coils "trapezoidal") | Radial sides | N 8 radial is not buildable at A's radii (UNBUILDABLE_TURNS_EXCEED_LIMIT, limit 6). At N 6: radial −4.83 % against parallel +7.97 % (Δ −12.8) | verified (ran); large lever |
| H13 | Coil gap (`assumption` 0.2 mm) | 0.0, 0.5, 1.0 mm | +18.71 %, +17.76 %, +15.85 % | verified (ran); small. 0.0 gives the same value as 0.2 (not investigated) |
| H14 | D09's own method: N × flux of the middle loop (D09 p.5: "The flux linked by the single loop of the coil is then multiplied by the number of turns") | 8 × mean(EMF of turns 4 and 5) on A | 8.02 V (+29.2 %) against the turn sum 7.37 V | verified (ran); see the inference below |
| H15 | k_w applied twice by D09 (eq. 8–9 carry k_w inside an area integral) | A × sin(120°) = 0.866 | 6.384 V (+2.80 %) | unresolved. Not a cause of the gap to FEA 6.20 V or measured 6.22 V: those do not use D09's formula |

### Geometry consistency with D09 Table 1

D09 Table 1 p.3 gives two geometric numbers for the concentric phase: trace length 3244 mm and the area of "the loop
in the middle of the number of turns", 171 mm². The probe measures both on generated coils (turn areas by shoelace
per 2π of winding angle; length = phase A coil paths + chain).

Variant A matches the area and misses the length:

```
H-geometry A: 8 full turns, areas outer->inner [403.1, 326.7, 257.9, 197.2, 144.4, 99.5, 62.6, 33.6] mm^2; mid-turn 170.8 mm^2 (D09 171 mm^2, -0.1%)
  phase A coil paths 3416.4 mm + chain 168.3 mm (D09 3244 mm)
```

So A's phase is 3584.7 mm, +10.5 % over D09 (`verified`, ran). D09's numbers alone also argue against N = 8. With
N turns per coil-layer and 8 coil-layers, the mean turn perimeter is 3244/(8N) mm. A loop of area 171 mm² with that
perimeter has an isoperimetric ratio 4πA/P² of 0.836 at N 8, 0.640 at N 7 and 0.470 at N 6. A square is 0.785 and a
circle 1. A trapezoidal coil in a 30° sector cannot be rounder than a square, so N 8 fits D09's two numbers only if
the 3244 mm leaves out copper (`inferred`, arithmetic; the generated A coil has 0.753).

The grid covers parallel sides with N 6 to 8 and R_i0 22 to 27 mm, and radial sides with N 6 to 7 and R_i0 22 to
28 mm, with R_o0 44 to 48 mm, all in 1 mm steps. It gives these builds within 5 % of both Table 1 numbers:

```
  parallel N 7 22.0/44.0 | 5.78323 V (-6.87%) | -3.4% | -4.1%
  parallel N 7 22.0/45.0 | 6.35103 V (+2.27%) | +1.1% | +4.6%
  parallel N 7 23.0/45.0 | 6.23829 V (+0.46%) | -1.5% | +0.8%
  parallel N 7 24.0/45.0 | 6.06441 V (-2.34%) | -4.1% | -3.3%
  parallel N 7 25.0/46.0 | 6.41194 V (+3.25%) | -2.1% | +1.3%
  parallel N 7 26.0/46.0 | 6.10902 V (-1.63%) | -4.7% | -3.5%
  parallel N 7 27.0/47.0 | 6.30393 V (+1.51%) | -2.7% | +0.8%
  parallel: 90 buildable grid points, 7 within 5 % of both; N per hit [7]
  radial: 30 buildable grid points, 0 within 5 % of both; N per hit []
```

Every consistent build has N = 7. Their EMF spans −6.9 % to +3.3 %. Six of the seven lie inside the OR-07 band of
their own e_edge. No N = 8 build is consistent.

### Verdict

**F-OR07 cause: `inferred`. The pre-registered variant A is not D09's coil, and no EMF-chain defect was found.**

- The chain is exact (H1, instrument line) and the field side moves the result by at most 3 points (H6, H7, H8, H8a,
  H5). That is a third of the 9.36 % needed.
- The geometry levers each move the result by 5 to 13 points (H10, H11, H12). These inputs are `unresolved` (G2) or
  `assumption` (side style).
- The generated coils that reproduce both D09 Table 1 numbers all have 7 turns, and their EMF falls from −6.9 % to
  +3.3 % of 6.21 V. Variant A reproduces the area but not the length (+10.5 %).
- D09's own method (H14) predicts the A coil at 8.02 V. D09 published 6.21 V with that method, so D09's coil links
  about 23 % less flux than A's under D09's own recipe. 7 turns removes 12.5 %, the edge profile about 3 %.
  The rest is the coil shape (`inferred`).

This is a sensitivity result, not a pass. The grid hits were found after the A and B verdicts were known, so they are
not a re-registration. OR-07 stays a strict xfail naming F-OR07. The band is unchanged. EQT-05-O2 and EQT-06-O2 stay
`not tested`.

**DEF rows: none.** No product defect was found. The finding is in the oracle case that Agent 2 owns: O2-D09 version 2
primary A matches 171 mm² but not 3244 mm when built by the embodic generator.

**What closes F-OR07.** G2 needs D09's real turn count and radii: the authors (address on D09 p.1, UD-25), or a scaled
measurement of D09 Fig. 11a (photo of the made board). Then Fable decides one new pre-registered build from that
evidence only. Proposal for Fable (decision, not done here): O2-D09 version 3 records the Table 1 consistency
envelope above as information, keeps A and B as they are, and registers no new variant until G2 has a source.

**Q1 of oracle_tests_spec.md (e_edge 2.59 % vs Phase 1's 5.8 %).** `inferred`, explained. `edge_zone_d09.js`
weights the edge zone with "uniform radial coverage of the coil annulus within the magnet span" (its section 3
comment). A generated spiral covers the edges with its outer turns only, because turn k runs from R_i0 + k·d to
R_o0 − k·d. H8 shows that the digitised FEA profile on the generated paths removes 2.41 % of Ke, close to the
generated-layout e_edge of 2.59 %. So the generated-layout value is the right one for OR-01 and OR-07. The
calibration is still D09 Fig. 7 (DEF-23), so OR-11c below is the independent check.

### Variant C: the build read from D09 Fig. 1a (U-E13)

Variant C is `variant_C` of O2-D09 version 4 in `docs/phase2/engineering/oracle_cases.json`. It was committed in
53253b1 before any build. Its inputs are Agent 5's Fig. 1a readings (EV-127 to EV-133): 7 turns, parallel sides,
centre lines 25.104 / 45.214 mm, coil gap 0.342 mm, arc ends. `checks/or07_variant_c.py` reads the four registered
builds from that file and runs each through `embodic.api.compute`. Every build met the registered preconditions:
turns_achieved 7, DRC pass, and no issue of any severity. For each build, Ke recomputed from the public kernels
equals the product's `ke_phase` within 1.1e-15.

```
C: turns_achieved 7 | DRC pass | issues [] | preconditions met
  OR-07 emf_phase_rms_v 5.90328 V | e_edge 0.0172 | band [-5.00%, +6.72%] | -4.94% vs 6.21 V, -4.79% vs 6.2 V, -5.09% vs 6.22 V | OUT of band
  OR-02 resistance_phase_20c_ohm 0.94680 ohm | -11.51% vs 1.07 ohm | band [-8.00%, +8.00%] | OUT of band
  phase A copper (information): coil paths 2874.2 mm + chain 160.8 mm = 3035.0 mm (-6.4% vs 3244 mm); coil paths alone -11.4%
```

| Build | Role | E_ph | vs 6.21 / 6.20 / 6.22 V | OR-07 band | OR-07 | R at 20 °C | vs 1.07 Ω | OR-02 |
|---|---|---|---|---|---|---|---|---|
| C | verdict | 5.90328 V | −4.94 / −4.79 / −5.09 % | [−5 %, +6.72 %] | out | 0.94680 Ω | −11.51 % | out |
| C-pitch | envelope | 5.78063 V | −6.91 / −6.76 / −7.06 % | [−5 %, +6.75 %] | out | 0.93810 Ω | −12.33 % | out |
| C-hole | envelope | 6.02442 V | −2.99 / −2.83 / −3.14 % | [−5 %, +6.70 %] | in | 0.95550 Ω | −10.70 % | out |
| C-straight | sensitivity | 5.95153 V | −4.16 / −4.01 / −4.32 % | [−5 %, +7.86 %] | in | 0.97008 Ω | −9.34 % | out |

C at 40 °C (sensitivity, not a second chance): 1.02122 Ω, −4.56 %.

**Verdicts (`verified`, ran).**

- OR-07 on C is out of band. C is inside the band against 6.21 V (calculated) and 6.20 V (FEA). Against 6.22 V
  (measured) it is 0.09 points below −5 %. The registered rule needs all three, so the verdict is out.
- The OR-07 verdict is not robust to the reading. C-hole and C-straight are in band, and C-pitch is out. The two
  drawing scales differ by 1.3 % (EV-129), and that difference alone moves the EMF by 3.9 points.
- OR-02 on C is out of band at −11.51 %. Every envelope build is out too, from −12.33 % to −9.34 %.

**What the numbers say (`inferred`).**

- The +18.7 % of F-OR07 does not appear on the geometry read from D09's own drawing. C links 19.9 % less flux than
  variant A (5.90328 / 7.37166 V). The H14 inference above expected about 23 % from D09's own method.
- The generator reproduces the drawn turns. C's coil paths (2874.2 mm per phase) are 0.9 % to 2.5 % above the sum of
  the read centre lines (2804 to 2848 mm, EV-132), and the coil paths also hold the leads and stubs.
- R follows the copper length. C's phase A is 3035.0 mm, 6.4 % under D09's 3244 mm. Scaled to 3244 mm, C's R would be
  1.012 Ω, close to the 0.999 Ω that D09's 3244 mm gives at 20 °C (O2-D09 phase resistance row). So OR-02 misses by
  the EV-132 gap: copper that D09 Table 1 counts and Fig. 1a does not show (`unresolved`, a registered open note).

**Status.** OR-07 stays a strict xfail on A and B. C is not in the test suite, and any change of test status is
Fable's ruling. Still open: the EV-132 length gap, the Fig. 11a radius shift (EV-133), the unread end style, and the
innermost-turn prediction of the registration (`not tested` on the generated layout). Variant C is not changed after
these results. Any further variant is a new pre-registration.

## 2. FEA case specifications OR-11 and OR-12

Both cases are tool-neutral. Agent 4 builds them in Elmer (D-048 e). Agent 5 sets up the toolchain (U-S6). The
solver choice inside Elmer is Agent 4's. Commit only inputs, meshes or mesh scripts, and results.

### OR-11. Rotor field of D09 at the copper plane (checks EQ-05)

**Model choice.** OR-11a and OR-11b are 2-D planar, linearised at a radius: the machine is unrolled along the
circumference at one radius. Reason: EQ-05 is itself a 2-D harmonic solution at each radius (`field.py` docstring,
"2-D harmonic model at each radius"; u = n·p/r). A 2-D FEA at the same radius tests exactly that model: magnet
representation, µ_r handling, iron backing and double-rotor symmetry, with no radial term. D09 p.4 did the same
comparison at the mean radius against 3-D FEA (<1 % on the fundamental). OR-11c is 3-D, because the radial edge
effect (EC-05) exists only in 3-D.

| Item | OR-11a / OR-11b (2-D) | Source or label |
|---|---|---|
| Radius | a: r_m = 35.5 mm. b: 27.0 mm and 44.0 mm | r_m = (25 + 46)/2 from D09 Table 2 p.3 (diameters 50/92 mm, magnet span `inferred`) |
| Domain in x | One pole pair, 2τ = 2πr/p (r_m: 27.88 mm), periodic boundaries. One pole with anti-periodic boundaries is equivalent | p = 8, D09 Table 2 |
| Layers in y | iron 5 mm, magnet 2 mm, air 1 mm, board 1 mm (µ_r 1), air 1 mm, magnet 2 mm, iron 5 mm; 17 mm | D09 Table 2 (core 5 mm, magnet 2 mm, gap 1 mm, PCB 1 mm); Table 3 p.4 (7 mm between cores) |
| Magnets | Width α_p·τ (r_m: 11.15 mm), centred on each pole. Magnetised along y, alternating per pole. The two rotors at the same x carry the same direction, so flux crosses the gap | α_p 0.8, D09 Table 3; double rotor, D09 Fig. 4 p.3 |
| Magnet material | B_r 1.33 T, µ_r 1.05, linear | B_r: D09 Table 2. µ_r: `assumption` G23. Run 1.03 and 1.10 too: on EMF they move −2.5 to +1.0 points (H5) |
| Iron | Linear, µ_r 1000 (`assumption`; D09 names no steel). Effect: EQ-05 assumes ideal iron behind the magnet. The yoke flux density is about (2/π)·B1·τ/(2·5 mm) = 0.75 T (`inferred`, estimate), below saturation for common steels. Run µ_r 10000 once; b1 must move < 0.1 %, or report the change | D09 Table 2 (core 5 mm) |
| Outer boundary | A_z = 0 (flux parallel) 5 mm beyond each iron face | `assumption`; effect negligible with iron (check with the µ_r 10000 run) |
| Mesh convergence | Halve the element size twice. Accept when the last halving changes b1 and the waveform peak by ≤ 0.5 %. Use at least 4 elements across the 1 mm gap and across each 0.07 mm copper plane | `assumption`: 0.5 % is one tenth of the ±5 % band, so mesh error cannot decide the verdict |
| Compared quantities | (1) B_z(x) on the line y = copper L1 mid-plane, 1.035 mm from the magnet face. (2) Its Fourier fundamental b1. (3) The waveform peak at the pole centre (sum of harmonics 1 to 13). (4) The same on the centre plane, y = 1.5 mm | (2) compares with `AnalysisResult.layers[i].b1_peak_mid_radius_t`, 0.846122 T at r_m. (3) compares with the OR-08 peak, 0.7384 T. (4) compares with `embodic.physics.field_harmonic` at z = G: 0.84150 T (H6). b: `field_harmonic` at the same r and z |
| Band | ±5 % on b1 and on the peak | Registry EQ-05 tolerance: "+/-5 % on B1 at mid-radius vs 3-D FEA", basis D09 p.4 (<1 %) plus µ_r and B_r uncertainty. Not chosen in this unit |

**OR-11c (3-D, optional in Phase 3).** One pole pitch of the D09 rotor as a 22.5° sector, periodic on the two cut
planes, magnets as arc segments 25 to 46 mm, the same layers and materials. Compare B_z(r) at the pole centre on the
copper plane, r from 22 to 49 mm, with (1) EQ-05 times the EC-05 factor 1 − D_e·exp(−d/(c_e·G)), D_e 0.47, c_e 0.9,
and (2) the Fig. 7 digitisation. Quantity: the integral ∫B_z,1·r dr over the coil's radial span, against the model's
`edge_weight` sum. This is the only check of EC-05 that does not use D09 Fig. 7 as its own reference. Band: none
exists for EC-05 (D-017 cap 10 % is a rule, not a tolerance). Report the deficit as characterisation.

### OR-12. Eddy loss of one D09 trace (checks EQ-12)

| Item | Specification | Source or label |
|---|---|---|
| Model | 2-D cross-section of one rectangular conductor, time-harmonic (sinusoidal steady state), infinitely long | EQ-12 is a per-length formula; a cross-section tests it exactly |
| Conductor | 0.8 × 0.07 mm, copper, σ = 1/1.7241e-8 S/m (20 °C), µ_r 1 | D09 Table 2; registry `copper_resistivity_20c_ohm_m` |
| Excitation | A uniform external flux density of amplitude B0, at 266.67 Hz. Case 12a: B0 normal to the wide face (B_z). Case 12b: B0 along the wide face (B_t). The conductor carries no net current | D09 Table 2 (266.67 Hz). B0 0.846122 T is an example level (the D09 A b1); the loss scales with B0² |
| Boundary | Air box at least 20 × the trace width. Impose the uniform field on the box edge (for example A_z linear in the coordinate across B0) | `assumption`; check the field at the trace without the conductor equals B0 within 0.1 % |
| Mesh convergence | At least 4 elements across the 0.07 mm thickness, element size ≤ δ/10 inside copper (δ 4.047 mm, so geometry decides). Accept when halving changes the loss by ≤ 2 % | `assumption`: 2 % is one tenth of the ±20 % band |
| Compared quantity | Loss per metre P′ in W/m, from the volume integral of \|J\|²/(2σ) | Embodic: `embodic.physics.eddy_loss_w` on one straight path (`checks/or12_reference.py`): 12a 1.740834e-01 W/m, 12b 1.332826e-03 W/m at 0.846122 T, equal to σω²B0²w³t/24 and σω²B0²wt³/24 to 4e-16 |
| Band | ±20 % | Registry EQ-12 tolerance "+/-20 % vs 2-D FEM of one trace", basis `assumption` (uniform field, end effects). Not chosen in this unit |
| Second point | Repeat 12a at 13 × 266.67 Hz (δ 1.122 mm): the low-frequency formula should still hold within the band, since w < δ | `checks/or12_reference.py` prints both skin depths |

What OR-12 cannot test: the field non-uniformity across a trace near a magnet edge, and 3-D end effects. Those stay
inside the ±20 % assumption.

## 3. Measurement plan for a future board (a plan, not a result)

No board exists (D-048 f). Every row below is `not tested`. Run the steps in this order on the first built board.

| # | Quantity | Instrument | Procedure | Embodic quantity | Band (registry) |
|---|---|---|---|---|---|
| M1 | Phase DC resistance | 4-wire (Kelvin) milliohm meter, ≤ 1 mΩ resolution on a 1 Ω range; thermocouple on the copper | Soak the board at room temperature for 30 min, rotor removed. Measure each phase between its two terminals (open) or line to line (star or delta). Test current ≤ 100 mA. Record the copper temperature T | `resistance_phase_20c_ohm` after correcting the reading to 20 °C with α 0.00393 /K, or `resistance_phase_operating_ohm` with `winding_temperature_degc` = T. Star line-line: 2 × phase. Delta line-line: (2/3) × phase | EQ-10: ±8 % at a known temperature |
| M2 | Phase inductance | LCR meter, series model | Measure each phase alone, the other phases open, at 1 kHz and at 10 kHz. Measure twice: rotor removed (I1 rotor out) and rotor in place at a pole-aligned and a mid-pole position (I1 rotor in). Then line to line for star (L_LL/2 reading, I2) | `inductance_estimate_h` (EQ-14 form a, no leakage term, G1) | None: EQ-14 is `cannot verify yet`; target ±20 % after validation. Record only (characterisation), as OR-09 |
| M3 | Back-EMF | Spin rig (drive motor and coupling), optical tachometer, oscilloscope with a differential probe | Open circuit. Speeds 500, 1000 and 2000 rpm, steady. Capture at least 10 electrical periods. Compute the fundamental by FFT. Measure phase voltages for open topology, line-line for star | Ke = V1,peak/ω_m against `ke_phase_v_s_per_rad` (phase) or `ke_line_v_s_per_rad` (line); the waveform against `emf_waveform_v` | EQ-06 against a measured Ke: [−8 %, +8 % + e_edge] (the OR-01 basis). THD (EQ-18): information only (G31) |
| M4 | Winding temperature rise | Thermocouple or IR camera (emissivity of the solder mask stated) | DC current through one phase at ambient T_a until steady (ΔT changes < 1 K in 10 min) | `temperature_rise_k` with the same current and ambient | EQ-17: ±30 % on ΔT |
| M5 | Mass | Scale, 0.01 g | Bare board | `mass_g` | EQ-16: ±10 % |

**How a measurement enters the evidence (D-007).** A measurement becomes evidence only with a written record.

1. The user writes a measurement record: date, board id and design hash, instrument model and serial, calibration
   date, procedure row (M1 to M5), conditions (temperature, frequency, rotor state, speed), raw readings and the
   reading uncertainty. The record is a file under `docs/phase3/evidence/measurements/`.
2. Agent 5 adds an evidence register entry for the record (a new EV id, document = that file).
3. Agent 2 adds an oracle case with `kind: measured` and the source EV id, and pre-registers the comparison and band
   before anyone computes the model value.
4. In the app, an input gains the `measured` provenance only when the user marks it measured and names the source.
   A typed value equal to a default stays `default`.
5. Agent 3 or 4 writes the oracle test. The registry test id counts once that test passes in a release run.

## 4. The 9 Phase 3 EQT ids (eqt_map_review.md §c)

"Cloud now" means Phase 3 can close it in this container without a board.

| ID | Closing method | Cloud now | Reason |
|---|---|---|---|
| EQT-14-GR | Withdrawn (revision 2026-10-16, U-E12, D-049 d) | n/a | No port to compare. EQT-14-CF12 (oracle_cases.json CF-12) replaces it; `tests/unit/physics/test_closed_forms_m2e2.py` `test_eq14_reference_estimate` can carry it once it asserts the CF-12 value at relative 1e-12 (Agent 3) |
| EQT-14-O2 | Literature value (D09 14.8 µH) or measurement (M2) | no | D09 gives no method, frequency or rotor state (DEF-08), the D09 coil is unknown (G2), and EQ-14 has no leakage term (G1) |
| EQT-16-GR | Xcoil data: `massThermal` dump with copper density 8.96 g/cm³ | yes | `tools/golden/dump_xcoil.mjs` and Node v22 are present (`/opt/node22/bin/node`); not run in this unit |
| EQT-17-GR | Xcoil data: the same `massThermal` dump (ΔT) | yes | As EQT-16-GR |
| EQT-19-GR | Xcoil data: a delta dump with a triplen EMF | yes | The committed delta fixture has all EMF phasors 0 (eqt_map_review.md §c) |
| EQT-22-GR | Xcoil data: per-phase-ampere current density | yes | A new dump case |
| EQT-27-GR | Xcoil data: `kw1` | yes | A new dump case |
| EQT-28-GR | Xcoil data after a port | yes, after a code unit | No rotor-inertia function in src/embodic; Agent 3 ports it first |
| EQT-29-GR | Xcoil data after a port | yes, after a code unit | No capacitance function in src/embodic; the port uses CODATA ε₀ (U-E5) |

None of the 9 needs an FEA case. OR-11 and OR-12 close no EQT id in the present map. They give EQ-05 and EQ-12
their first non-D09 evidence.

## 5. Open engineering items of D-047 owned by Agent 2

| Item | Decision | Reason |
|---|---|---|
| Wave example: 186 D-006 violations (D-034) | Phase 5 change | The example is a faithful port of Xcoil's preset, which hid the violations in a 4 µm slack. The fix is new example values (clearance), not a DRC rule change (D-006). Phase 3 can only re-count |
| Serpentine strands > 1 not DRC-clean (D-036 a) | Phase 5 change | A generator spec revision by Agent 2, then a code unit. Phase 3 keeps the counts (12/0/0/0/0/0/18, D-037 a) as the regression state |
| D-030 lower bounds for clearance and pad | Phase 3 verification task | A property test with hostile clearance and pad values in bounded memory shows whether a failure exists (D-040 d names only the width). A found failure becomes a Phase 5 change. Specification for Agent 3: `d030_property_spec.md` (revision 2026-10-16, U-E12) |
| Per-phase stack interconnect `unresolved` (D-037 b) | Stays open | No interconnect is built for a stack, so no result exists to verify. A design spec belongs to Phase 5, and a physical check needs a board |
| e_edge on generated layouts ≈ 0.4 × Phase 1 (Q1) | Phase 3 verification task, done here (`inferred`) | Section 1: the Phase 1 script assumed uniform radial coverage. The FEA-profile probe gives −2.41 % against e_edge 2.59 %. OR-11c gives the independent check |

## Open questions for Fable

- Q1. O2-D09 version 3: record the Table 1 consistency envelope (section 1) as information, with no new variant
  until G2 has a source? Agent 2 recommends yes.
- Q2. Should Agent 5 attempt a scaled turn count from D09 Fig. 11a (photo) to close G2? It is the only route on
  record besides the authors.
- Q3. EQT-14-GR: port the current-sheet model or change the EQ-14 gate (D-046 e)?
