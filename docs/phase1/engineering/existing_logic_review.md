Prepared by: Agent 2 — Motor Design Expert — model: claude-opus-5-5

# Review of the Xcoil v3 calculation logic relevant to spiral coils (Phase 1 draft, 2026-10-04)

Reviewed file: `/home/claude/serpentine/src/engine.js` (read-only; 2,986 lines; line numbers below refer to this source
file — e.g. `fieldHarmonic` is source l.856, built file `dist/xcoil.html` l.1336). Test suite: `node
/home/claude/serpentine/run-tests.js` → **131/131 passed** on 2026-10-04 (`verified (reproduced)`). Verdict vocabulary =
the equation-check gate of `equation_specification_draft.md`: `reuse`, `reuse with change`, `cannot verify yet`,
`replace`. Equation IDs (EQ-xx) refer to that file. All numbers below were produced by me with the commands in §3;
they are computed values, not measurements.

## 1. Function inventory and verdicts

| Function (src line) | Computes | Units | Verdict | Notes |
|---|---|---|---|---|
| constants l.11–16 | µ0; ρ₂₀ = 1.724e-8 Ω·m; α = 0.00393 /K; 1 oz = 0.0348 mm; via plating 0.025 mm; odd harmonics 1…13 | SI / mm | reuse with change | ρ₂₀ = 1.724e-8 and α = 0.00393 now sourced (IACS/IEC 28 via NBS Handbook 100, EV-53; IACS value 1.7241e-8); oz → µm conversion still a convention; make harmonic set configurable |
| `copperResistivity` l.80, `traceResistance` l.102, `primsResistance` l.97 | ρ(T) = ρ₂₀(1+α(T−20)); R = ρL/(wt) per primitive width | Ω, mm in | reuse | Matches D08 eq. 3.37–3.38 (EV-08). Check C3 |
| `skinDepthMm` l.81 | δ = √(ρ/(π f µ0)) | mm | reuse | D01 eq. 4 (EV-21); test ELE-02 |
| `ipc2221Current` l.86 | I = k ΔT^0.44 A^0.725, A in mil², k = 0.048 ext / 0.024 int | A | cannot verify yet | Standard not in corpus (G5); label every result `assumption` |
| `viaBarrelArea` l.92 | A = π(2rt − t²) | mm² | reuse | D05 eq. 3 (EV-37); test ELE-04 |
| `stackupFor` l.1156 | copper layer centre z and thickness; auto = evenly spaced | mm | reuse with change | Auto mode assumes equal dielectric gaps; real stacks (repository record: 71 µm prepreg, 100 µm core) need the custom mode as default for z |
| `fieldHarmonic` l.856 | B_z, B_t amplitude of odd harmonic n at (r, z) for a parallel-magnetised array on infinitely permeable back iron, with a flux-symmetry/iron plane at distance G | T | reuse with change | Exact linear 2-D solution (my derivation, EQ-05); equals D08 eq. 3.1 for µ_r = 1 (C1b); 1-D limit exact (C1a). Change: radius-dependent α_p for block magnets (C1e), optional Halbach (D11 eq. 8–9), radial edge correction (D09 p.4) |
| `fieldSetup` l.868 | G: double rotor (t_s+2g)/2; single+yoke t_s+2g; open ∞ | mm | reuse with change | Double rotor assumes identical rotors facing N→S (B_t = 0 at mid-plane); 'singleOpen' still has rotor back iron in the field model but none in the inductance and inertia models (Q-3 below) |
| `analyze` l.880 (serpentine/wave) and `analyzeElements` l.1846 (sector) | Per segment: λ_n += B_z,n(r_m,z) r_m Δr e^{−jnpθ}; phase sums; parallel members conductance-weighted; circulating loss; eddy loss; Ke, kw1, THD, IPC limit | V·s/rad (×1e-6 from T·mm²), W | reuse with change | Path integral is exact for in-plane conductors (EQ-06; C2 agrees to 5e-6). Circumferential pieces give Δr = 0 → no EMF (correct), but are counted in `activeLen` and in the B_t eddy term (minor over-estimate). Needs: series connection of layer pairs, per-coil element lists from the new generator |
| eddy part of `analyze`/`analyzeElements` | P = σ/24 Σ_n (nω_e)² Σ_seg len (B_z,n² w³ t + B_t,n² w t³) | W | reuse | D03 eq. 2 form with peak amplitudes; factor-2 dispute (G4) resolved as peak-vs-RMS convention (EQ-12). Units checked by hand (m⁵·S/m·T²/s² = W). Test ELE-08 |
| kw1 normalisation (l.975–983, l.1884/1892) | kw1 = Ke₁ / (series conductors × ∫B₁ r dr over the magnet span) | – | reuse with change | A numerical utilisation factor, not the textbook k_w: includes spiral spread, radial coverage, the centre-via lead (C2: 0.6305 for a 1-turn coil whose sides alone give 0.966·sin(70.7°)·…); rename and report the textbook k_w separately |
| `kdAnalytic` in `computeSector` l.2477 | star-of-slots k_d × pitch factor of the **outermost** turn | – | replace | Mislabelled ("kd"); upper bound only. Replace by EQ-08 turn-averaged k_w |
| `starOfSlots` l.1899 | phase/sign per coil by 60° belts; balance check; k_d | – | **replace** (bug) | Floating-point tie at belt edges → false "unbalanced" for 12/14, 24/14, 24/22, 24/26 (C6). Use exact integer arithmetic on phasor index (p·k mod Q) or an epsilon-rotated belt |
| `balancedSectorList` l.2253 | lists balanced Q for a pole count | – | replace | Inherits the bug: for 14 poles omits 12 and 24 (C6) |
| `deriveSector`, `sectorFeasible` l.2274, `maxSectorTurns` l.2278 | sector geometry, turn limit (corners exist, inner < outer, centre via fits) | mm | reuse with change | No "triangular" turns: inner end-turn radius = r_i + t·pitch fixed → D08 geometry fits 0 turns (C5) while D08 built 3. Add moving inner end-turn (D08 eq. 3.25–3.26) and multi-via eyes |
| `sectorCoilX` l.2285, `buildSector` l.2379 | spiral path X (outer→centre via), Y = mirror reversed; polarity by entry terminal; phase chains on rings outside r_o; ring levels | mm | reuse with change (as reference for the Python geometry engine) | Spiral (not concentric) turns: left side of turn t sits at offset d_{t+1}; final lead to centre via is radial and does produce EMF (C2). Layer pairs only in parallel (`PAIRS_PARALLEL`), no group rotation, no series pairs, only one centre via per coil |
| `computeSector` l.2426 | assembles elements (X members ∥, Y members ∥, in series), via R (one centre via ÷ pairs), ring/leg R, analysis, thermal, inductance | Ω, V·s/rad | reuse with change | Ring-to-leg and terminal vias are not included in R (minor); interconnect resistance included when the star/delta ring is drawn |
| `applyConnection` l.1398 | star/delta: T = (m/2)Ke Î_ph; Kt = mKe/√2 (÷√3 per line A in delta); Ke,LL = √3 Ke (star); R_LL; delta circulating current from Σ_phases E_h | N·m, V, Ω | reuse | Fundamental-only relations (EQ-09). Delta circulation is resistance-limited (ignores zero-sequence inductance) → conservative upper bound. Test ELE-07, SEC-04 |
| `emfWaveform` l.1020, `lineWaveform` l.1441 | harmonic synthesis of phase/line EMF | V | reuse | — |
| `windingInductance` l.2617 | current-sheet harmonic model of radial conductors between irons, inter-layer e^{−ν Δz/r}, sinc² width factor; L_s = L_self − M | H | cannot verify yet | End-turns dropped (significant for spiral coils); no measured multi-layer spiral oracle (G1). Indicative only (C9) |
| `torqueSpeed` l.2688, `inverterVoltage` l.2679, `driveAnalysis` l.2725 | dq steady state with V and I limits; SVPWM V_LL,rms = V_dc/√2, SPWM √3V_dc/(2√2), six-step √6V_dc/π | rpm, N·m | cannot verify yet | Standard relations (textbook source needed), but rely on L (G1) |
| `massThermal` l.1378 | copper/laminate mass (8.96 / 1.85 g/cm³); ΔT = P/(h·2A_board), h default 30 W/m²K | g, K | reuse with change | Copper density: IACS 8.89 g/cm³ (EV-53) vs engine 8.96; laminate density needs a source; h = 30 conflicts with D01's "widely used" 10 W/m²K (EV-22); no conduction path (D01 eq. 6–8, D08 §7) |
| `rotorInertiaEstimate` l.2671 | magnets + yoke disc (yoke thickness = magnet thickness) | kg·m² | reuse with change | 'singleOpen' → no yoke (inconsistent with field model) |
| `interconnectResistance` l.1361 | stub/link/ring resistances of star/delta interconnect | Ω | reuse | — |

## 2. Detailed observations

### 2.1 `fieldHarmonic` — symmetry handling and comparison with D08/D09 (`inferred` derivation + `verified (reproduced)` numbers)

Solving Laplace's equation for the scalar potential with iron behind the magnet (z = −l_m) and H_t = 0 at the plane z = G
(iron or mid-plane of an N–S double rotor) gives, for z measured from the magnet face,

B_z,n(r,z) = K_n cosh(u(G − z)) / [cosh(uG) + µ_r coth(u l_m) sinh(uG)],  K_n = (4B_r/(nπ)) sin(nπα_p/2),  u = n p / r.

The engine's exponential form is algebraically identical (expanded by hand); with G → ∞ it becomes K_n e^{−uz}/(1 + µ_r
coth(u l_m)). Consequences:
- Double rotor: valid for two identical, aligned rotors with N facing S (through flux). Beyond the mid-plane the code
  mirrors z (z → 2G − z); B_t changes sign physically but the code returns its magnitude — harmless because B_t is only
  used squared (eddy loss).
- D08 eq. 3.1 (p.31 [26]) = the same expression with the denominator replaced by µ_PM sinh(u z₂)/sinh(u h_PM): identical
  for µ_PM = 1, and 3–4 % lower for µ_PM = 1.05 (C1b). D08 sums n = 1…∞ without stating "odd n only"; for alternating
  N/S magnets only odd n exist — implement odd n explicitly (engine does).
- D09 eq. 1 (p.4) gives only the general exponential form with unknown coefficients — consistent, but not a numerical check.
- The 2-D solution is evaluated at each radius with τ_p = πr/p (D08 eq. 3.2; D09 p.4). It ignores radial edge leakage:
  D09 p.4 Fig. 7 shows the FEA field dropping from ≈0.72 T to ≈0.4 T at the magnet's inner/outer edges (figure reading,
  `inferred`), which the model cannot reproduce.

### 2.2 `analyze`/`analyzeElements` — circumferential segments and EMF formula (`inferred` derivation)

The per-segment term B_z r Δr e^{−jnpθ} is the motional EMF per unit mechanical speed: for an in-plane element dl and
relative velocity v = ω r θ̂, (v × B)·dl = ω r B_z dr exactly, for any B_r, B_t, B_z. So radial pieces carry all the EMF
and circumferential pieces none (D07 p.3, EV-17), the via (axial) none (D15 p.8, EV-43). For a closed loop this equals
−dψ/dt with ψ = ∬B_z dA (Stokes), i.e. the D08 loop method (eq. 3.6–3.14) and the D09 area integral (eq. 5–11) give the same
result. Remaining approximations: B_z from §2.1; segment midpoint angle; magnet span clipping r ∈ [r_A, r_B] with zero
field outside (edge leakage ignored).

### 2.3 Sector generator — turns and pitch

- Lateral pitch on sides: w + s; radial pitch on rims: w_end + s; first side offset gap/2 + w/2 from the sector edge
  (= D08's (i + ½) w_d convention when gap = s). 'radial' sides are lines through the origin whose offset is set at r_i
  (spacing grows outward); 'parallel' sides keep a constant offset (D08 geometry).
- The coil is a real spiral: turn t's right side at offset d_t, its inner arc runs from d_t to d_{t+1}, the left side
  continues at d_{t+1} to the next outer arc; the last turn ends with a radial lead to a centre via midway between the
  innermost end-turns (`sectorViaSpot`). Compared with D08's concentric loops, the path is 3.7–5.5 % shorter for the cases in
  C4.
- Turn limit = first N for which a corner does not exist, the inner and outer end-turns collide, or the centre via does not
  fit. Inner end-turn radius is not moved outward for narrow coils → strong under-estimate of feasible turns for small r_i
  or wide traces (C5).

### 2.4 Questionable assumptions / issues found

| ID | Issue | Severity for embodic | Status |
|---|---|---|---|
| Q-1 | `starOfSlots` belt-edge floating-point tie → false "unbalanced" (12/14, 24/14, 24/22, 24/26) | High (blocks valid combos incl. D11) | verified (reproduced, C6) |
| Q-2 | Sector generator: no triangular turns, no series layer pairs, no layer-group rotation, one centre via | High (core of the spiral topology) | verified (code reading + C5) |
| Q-3 | 'singleOpen': field model keeps rotor back iron, inductance model uses no iron at all (T = 2), inertia model no yoke | Medium | verified (code reading: `fieldHarmonic` l.856–866 always has back iron; `windingInductance` l.2642; `rotorInertiaEstimate` l.2674) |
| Q-4 | Constant α_p only; block magnets have α_p(r) (D08 eq. 3.3) | Medium (−2.8 % ∫B₁r dr and different harmonics for 20 × 6 blocks, C1e) | verified |
| Q-5 | `kdAnalytic` (sector) = k_d × outermost-turn pitch factor, labelled "kd" | Low (label) | verified (code reading l.2477) |
| Q-6 | Eddy B_t term applied to circumferential segments (field along conductor) | Low (over-estimate) | inferred |
| Q-7 | No radial edge-leakage correction of B_z | Medium (EMF over-estimate near magnet ends; D09 used an FEA-fitted B_r(r)) | inferred from D09 p.4–5 |
| Q-8 | Inductance ignores end-turns | Medium (spiral coils have long end-turns) | verified (code comment l.2616) |
| Q-9 | Thermal h = 30 W/m²K default, no conduction | Medium | verified (code) vs D01 p.4 |
| Q-10 | Via resistance in sector: only the centre via is counted; ring-leg vias omitted | Low | verified (code l.2470–2476) |

## 3. Numeric sanity checks (all run by me on 2026-10-04 in `/home/claude/embodic/docs/phase1/engineering`)

Scripts live in `checks/`; each was first run as an inline `node -e` / `python3` command with the same code and then
saved. Engine loaded read-only from `/home/claude/serpentine/src/engine.js`.

**C0 — engine regression.** `node /home/claude/serpentine/run-tests.js` → `131/131 passed`. `verified (reproduced)`.

**C1 — field model.** Command: `node checks/c1_field.js`
- C1a (large pole pitch, r = 10⁷ mm, Br 1.30 T, l_m 3 mm, µ_r 1.05, α_p 0.85, G 2 mm) vs 1-D magnetic circuit
  B₁ = (4/π) sin(πα_p/2)·B_r l_m/(l_m + µ_r G): engine 0.946752 T, closed form 0.946752 T, rel. diff 4.8e-12 (z = 0, 1, 2 mm).
  `verified (reproduced)`.
- C1b (D08 Table 3.1 rotor: B_rem 1.38 T, h_PM 5 mm, 18 mm wide block at r = 40 mm → α_p = 0.7224 via D08 eq. 3.3, p = 5):
  µ_PM = 1: engine B₁ 1.1952 T = D08 eq. 3.1 1.1952 T (gap 1.4 mm/side) and 0.9336 = 0.9336 (2.8 mm/side) → identity
  `verified (reproduced)`. µ_PM = 1.05: D08/engine = 0.9637 (1.4 mm) and 0.9704 (2.8 mm). Pole-centre field (n ≤ 13) with
  µ = 1.05: engine 1.065 T / D08 1.026 T for 1.4 mm per side; 0.847 / 0.822 T for 2.8 mm per side. D08 Fig. 3.3 (p.32)
  shows peaks of ≈1.03 T (figure reading) → consistent with 1.4 mm from magnet face to mid-plane, not 2.8 mm (`inferred`;
  bears on gap G10).
- C1c (D09 Table 3 rotor: 16 poles, B_r 1.33 T, h_m 2 mm, rotor cores 7 mm apart → G = 1.5 mm, α_p 0.8; mid-plane):
  pole-centre B (n ≤ 13) = 0.738 T (µ_r 1.05) / 0.754 T (µ_r 1.0) at r = 35.5 mm; D09 Fig. 5 (p.4) flat top ≈0.75 T and
  Fig. 7 FEA ≈0.72 T mid-radius (figure readings, `inferred`) → within ≈2–5 %. µ_r not given in D09 (`assumption`).
- C1d per-layer spread (6 × 1 oz in 0.62 mm, 1.0 mm gap, p = 8, r = 28 mm): B₁ = 0.6828 / 0.6813 / 0.6805 T (outer → middle),
  spread 0.336 %.
- C1e block magnets 20 × 6 mm, r 18–38 mm: α_p = 0.853 / 0.547 / 0.402 at r = 18 / 28 / 38 mm; ∫B₁ r dr = 369.60 T·mm² vs
  380.06 with constant α_p 0.55 (ratio 0.9725).

**C2 — closed-form back-EMF of a 1-turn sector coil.** Command: `node checks/e1.js` (12 coils/10 poles, radial sides, 2 layers,
double rotor, magnet span set to the side ends so the end-turns lie on the edge). Closed form: Ke = N_c,ph k_d Σ_layers
[sin(pβ₀) ∫_{r_i'}^{r_o'} B₁ r dr + sin(pβ₁) ∫_{r_i'}^{r_v} B₁ r dr] (side at β₀, centre-via lead at β₁). Output: engine
Ke₁ = 5.410784e-3 V·s/rad, closed form 5.410812e-3, rel. diff −5.0e-6; phase imbalance 9.6e-16. `verified (reproduced)` —
confirms segment integration, X/Y mirroring, polarity and phase assembly (not the field model).

**C3 — resistance of a known track.** Command: `node checks/r2.js` (part a) / `node checks/c9_reference_values.js`.
1000 mm × 0.5 mm × 34.8 µm: engine 0.99080 Ω at 20 °C (hand 1.724e-8·1/(0.5e-3·34.8e-6) = 0.99080 Ω) and 1.14656 Ω at 60 °C
(hand ×(1 + 0.00393·40) = 1.14656). `verified (reproduced)` (formula; constants themselves unsourced, G6).

**C4 — spiral path vs D08 concentric-loop closed form.** Command: `node checks/r2.js` (part b), r 18–38 mm, w/s 0.5/0.2,
sharp corners, parallel sides. 12 coils: engine 8 turns, sides+ends 359.36 mm + lead 6.32 mm vs D08 eq. 3.27–3.36 (θ_cs = 2π/Q)
379.58 mm (−3.7 % incl. lead); 18 coils: 4 turns, 174.99 + 9.45 mm vs 195.20 mm (−5.5 %). `verified (reproduced)`.

**C5 — sector generator with D08's own geometry.** Command: `node checks/c5_c6_engine_limits.js`. r_i 12.5, r_o 44, w 2.06,
s 0.8, 12/10: maxTurns = 0 (parallel and radial sides); r_i 16 → 1 (parallel); r_i 24 → 1. D08 built 3 turns (Table 4.6
p.57). `verified (reproduced)`.

**C6 — star-of-slots belt-edge bug.** Same command. `12/14 ok=false … counts 5,4,3`; `24/14 9,8,7`; `24/22 9,6,9`;
`24/26 7,9,8`; 12/10 and 18/14 ok. `balancedSectorList(14 poles) = 3, 6, 9, 15, 18, 21, 27, 30` (12 and 24 missing). My
independent script `python3 checks/kw.py` finds all of these balanced and reproduces D08's 12/10 pattern "AabBCcaABbcC"
(D08 p.36 Fig. 3.7). `verified (reproduced)`.

**C7 — D08 phase resistance.** Command: `python3 checks/d08_resistance.py` (D08 eq. 3.27–3.38; r_i 12.5, r_o 44, w_tr 2.06,
w_s 0.8, 3 loops, t 34.8 µm, 4 coils/phase/side × 2 sides). θ_cs = 2π/Q (30°), two straight segments per loop, 50 °C
(D08 Table 4.5 p.54 track temperature; ρ = 1.927e-8 Ω·m from the engine constants): **0.381 Ω** vs D08 Table 4.6 0.39 Ω
(−2.3 %). Variant θ_cs = π/p (36°) at 20 °C gives 0.393 Ω but is geometrically inconsistent (12 × 36° > 360°). Printed
eq. 3.34 × 3.36 would count each straight side twice (0.600 Ω at 20 °C) → inconsistent with Table 4.6 (`inferred`: typo).
D08's ρ₂₀/α are not stated, so the residual is `unresolved`. Cross-check (`verified`): I = √((4 W/3)/0.39 Ω) = 1.849 A ≈ 1.84 A
(Table 4.6), confirming Agent 5's reading of eq. 4.3 (EV-09).

**C8 — winding factors.** Command: `python3 checks/kw.py` → table in `topology_analysis.md` §2.2 (12/10 0.933, 12/16 0.866,
18/16 0.945, 15/16 0.951, 24/16 0.866, 18/20 0.945; two-group rotation results §4.2). Classic values 12/10 → 0.933 and
12/16 → 0.866 also appear in engine test SEC-01. `verified (reproduced)` for the arithmetic; rule source `assumption`
(textbook needed).

**C9 — reference values and inductance comparison.** Command: `node checks/c9_reference_values.js`. Eddy example and via
values are listed in EQ-12/EQ-11. Inductance, 12/16, 8 turns, 2 layers, default assumptions: engine current-sheet
L_s = 17.96 µH (L_self 13.87, M −4.09, fundamental share 0.368); magnetising formula with N = 64 series turns,
δ′ = 6.62 mm: 4.67 µH (D10 eq. 14 form, k_w = 0.600 numeric) / 9.74 µH (k_w = 0.866); D15 eq. 14 form 7.34 / 15.31 µH. All
in the µH range seen in coreless PCB windings (D09 Table 6 14.8 µH; D07 Table 4 22.3 µH), but **not validated**
(`cannot verify yet`).

**C10 — indicative candidate sweep.** Command: `node checks/sweep2.js` → `topology_analysis.md` §2.4. Engine output,
unvalidated; used only to rank.

## 4. Gate summary

| Verdict | Items |
|---|---|
| reuse | ρ(T)/R; skin depth; via barrel area; EMF path integration (EQ-06); eddy formula (EQ-12); star/delta relations; waveform synthesis; interconnect R |
| reuse with change | constants (sources), field model (α_p(r), Halbach, edge correction), analysis assembly (series pairs), sector geometry generator (as reference only, rewrite in Python), stack-up z, mass/thermal, inertia |
| cannot verify yet | IPC-2221 current, inductance, torque–speed/drive |
| replace | `starOfSlots`, `balancedSectorList`, `kdAnalytic` |

Note for Agent 3/6: "reuse" means the *equation and its implementation logic* passed this check; the Python port must
re-run C1–C9 as regression tests with the same tolerances (EQ tables) before Phase 2 sign-off.
