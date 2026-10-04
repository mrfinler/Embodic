Prepared by: Agent 2 — Motor Design Expert — model: claude-opus-5-5

# Equation specification — draft for the embodic calculation engine (Phase 1, 2026-10-04)

Purpose: the **equation-check gate** required before any Xcoil v3 calculation logic is ported to Python. Every equation
has an ID, formula, sources (EV-IDs of `docs/phase1/evidence/evidence_register.md` + PDF page), variables and units,
assumptions/validity, limitations, a reference calculation, a tolerance with reasoning, and a gate verdict for the
existing implementation in `/home/claude/serpentine/src/engine.js`:

- `reuse` — equation and implementation checked; port as is (with regression tests).
- `reuse with change` — equation sound; implementation needs the stated change.
- `cannot verify yet` — no adequate evidence or oracle; may be ported only as a labelled estimate.
- `replace` — wrong or unsuitable; re-specify.

Status labels per PROJECT_BRIEF §3. "Reference calculation" numbers were computed by me (commands in
`existing_logic_review.md` §3, scripts in `checks/`); none is a measurement. Units: SI unless stated; geometry in mm
inside formulas where marked.

**Revision 2026-10-04 (reconciliation round):** sources updated from Agent 5's follow-up (EV-53…EV-71, gaps §7):
copper constants now sourced (EQ-10, EQ-16); G1 resolved in favour of D10 eq. 14 (EQ-14); D12/D15/D07 support for
EQ-08; magnet data (EQ-05); D09 oracle details (EQ-06, EQ-10, EQ-14); EQ-02 loop criterion and closed-form test values;
new sections "Status rule" and "Dominant assumed inputs" at the end. Machine-readable copy:
`equation_registry_draft.json`. Answers to other agents: `answers_to_agents.md`.

Common symbols: p pole pairs (2p poles); Q coils per layer; m = 3 phases; r radius; z axial distance from the magnet face;
θ mechanical angle; θ_e = pθ; ω_m mechanical speed [rad/s]; ω_e = pω_m; f_e = ω_e/2π; B_r remanence [T]; µ_r recoil
permeability; l_m magnet thickness [mm]; α_p pole-arc ratio; g air gap per side [mm]; t_s stator (board) thickness [mm];
w trace width, t copper thickness, s clearance, w_d = w + s [mm]; N turns per coil per layer.

---

## EQ-01 Pole pitch, coil pitch, electrical angle

- Formula: τ_p(r) = π r / p; θ_p = π/p; θ_cp = 2π/Q (coil pitch of non-overlapping coils); θ_e = p θ.
- Sources: D08 eq. 3.2 p.31 [26] (EV-03). Coil pitch: geometry (`inferred`). D08 eq. 3.27 p.44 prints the coil span as
  θ_cs = π/p, which equals θ_cp only when Q = 2p (`inferred`: for 12 coils/10 poles 12 × 36° > 360°).
- Inputs/outputs: p, Q, r → τ_p [mm], θ_p, θ_cp [rad].
- Reference: 2p = 16 → θ_p = 22.5°; Q = 12 → θ_cp = 30° = 240° el. (arithmetic). Tolerance: exact.
- Gate: `reuse` (engine `D.tau`, `S.h = π/Q`).

## EQ-02 Turn-count limits of a trapezoidal spiral coil

- Formula: w_d = w_tr + w_s (D08 3.5); N_c < ½((r_o − r_i)/w_d + 1) (3.24);
  trapezoidal turns N_c1 < r_i sin(θ_cs/2) / (w_d (1 − sin(θ_cs/2))) + 1 (3.25);
  triangular turns N_c2 < [(r_o − r_i)/w_d − csc(θ_cs/2) − 2N_c1 + 2] / (1 + csc(θ_cs/2)) (3.26).
- Sources: D08 p.33 eq. 3.5 and p.43 [38] eq. 3.24–3.26 (EV-02, EV-06), after Noh et al. 2019 (secondary).
- Variables: r_i, r_o inner/outer coil radii [mm]; θ_cs coil span [rad] (use θ_cp, EQ-01).
- Assumptions/validity: one layer; sides parallel to the sector edges; track centre-line convention of D08 Fig. 3.4; no
  centre-via room, no fillets.
- Limitations: does not include the centre via, the lead to it, or multi-via eyes (EQ-11); my derivation for centre-lines
  gives a −w_d/2 term in the numerator of 3.25 (`inferred`, may be a reference-line difference).
- Reference: D08 geometry (r_i 12.5, r_o 44, w_d 2.86 mm, θ_cs 30°): N_c < 6.01; N_c1 < 2.53 → 2; N_c2 < 1.06 → 1; total
  **3 turns = D08 Table 4.6 p.57** (3 loops) (`verified (reproduced)`, same total with θ_cs = 36°).
- Internal inconsistency found (`inferred`, `checks/eq02_eq03_reference.py`): D08's own loop geometry (eq. 3.28–3.29)
  makes loop i trapezoidal iff d_i < (r_i + i w_d) sin(θ_cs/2), i.e. i < (r_i sin(θ_cs/2) − w_d/2)/(w_d(1 − sin(θ_cs/2))),
  and triangular iff its apex radius d_i/sin(θ_cs/2) < r_o − i w_d. This **constructive loop criterion** splits D08's 3 turns
  as 1 trapezoidal + 2 triangular (printed eq. 3.25–3.26: 2 + 1); for the default annulus 12/16 (0.5/0.2 mm) both give 11
  (9 + 2 vs 10 + 1), but for 18/16 the loop criterion gives 8 while eq. 3.25–3.26 give 7. → The generator and its tests
  use the loop criterion; eq. 3.24–3.26 stay as documented cross-checks. Test values: `answers_to_agents.md` §2.2.
- Tolerance: exact integer agreement with the loop criterion; printed eq. 3.25–3.26 may differ by ±1; ±1 turn against the
  constructive generator because of the centre-via eye and fillets.
- Gate: `replace` — the engine's constructive limit (`sectorFeasible`) has no triangular turns and returns 0 turns for this
  geometry (C5). Port a constructive generator with moving inner end-turns; keep EQ-02 as a cross-check.

## EQ-03 Loop geometry and track length (closed-form cross-check)

- Formula (D08 eq. 3.28–3.36, with corrections): for loop i = 0…N−1, d_i = (i + ½) w_d,
  φ_in,i = asin(d_i/(r_i + i w_d)), φ_out,i = asin(d_i/(r_o − i w_d)), β = θ_cp/2 − φ;
  L_out,i = 2(r_o − i w_d) β_out,i; L_in,i = 2(r_i + i w_d) β_in,i (0 if β_in,i ≤ 0);
  L_s,i = d_i/tan φ_out,i − d_i/tan φ_in,i (φ_in → θ_cp/2 for triangular loops); L_i = L_out,i + L_in,i + 2 L_s,i;
  L_coil-layer = Σ L_i.
- Corrections (`inferred`): θ_cs → θ_cp = 2π/Q (EQ-01); printed eq. 3.34 has a leading factor 2 **and** eq. 3.36 adds
  2L_s,i, which counts each side twice — D08's own 0.39 Ω is matched only with one pair of sides per loop (EQ-10 reference).
- Sources: D08 p.44–45 [39–40] (EV-07); D09 Table 1 p.3 (phase trace lengths, e.g. concentric 3244 mm).
- Validity: closed concentric loops (not a true spiral), sharp corners, no via/lead/stub.
- Reference: D08 geometry → 177.2 mm per coil-layer, 1417.9 mm per phase (8 coil-layers) (`checks/d08_resistance.py`).
  Against the engine's generated spiral (r 18–38 mm, 0.5/0.2 mm): closed form exceeds the spiral path by 3.7 % (8 turns) and
  5.5 % (4 turns) (C4, `verified (reproduced)`).
- Tolerance: ±6 % between closed form and generated spiral (C4 range), because the spiral steps one pitch per turn and ends
  at a centre via. The authoritative length for resistance is the sum over the generated copper primitives (exact).
- Gate: engine path-length sum `primsLength` → `reuse`; closed form not in the engine → add as a check.

## EQ-04 Pole-arc ratio of rectangular block magnets

- Formula: τ_M(r) = 2 asin(w_PM / (2r)) · r (D08 eq. 3.3); α_p(r) = τ_M(r)/τ_p(r) = 2p asin(w_PM/(2r))/π.
- Sources: D08 p.31 [26] eq. 3.3 (EV-03).
- Variables: w_PM block width [mm] (tangential), block centred on a radial line.
- Validity: blocks with long axis radial; arc-segment magnets have constant α_p.
- Reference: 20 × 6 mm blocks, 2p = 16: α_p = 0.853 / 0.547 / 0.402 at r = 18 / 28 / 38 mm; ∫B₁ r dr over 18–38 mm is 2.8 %
  lower than with constant α_p = 0.55 (C1e, computed with EQ-05).
- Tolerance: exact (geometry).
- Gate: `replace`/add — engine supports constant α_p only (Q-4). Data model must carry magnet shape (arc / block) and
  dimensions.

## EQ-05 Air-gap field (2-D harmonic model at each radius)

- Formula (odd n only):
  K_n = (4 B_r/(nπ)) sin(nπ α_p(r)/2); u = n p / r;
  B_z,n(r,z) = K_n cosh(u(G − z)) / [cosh(uG) + µ_r coth(u l_m) sinh(uG)],
  B_t,n(r,z) = K_n sinh(u(G − z)) / [same denominator];
  G = (t_s + 2g)/2 for a double rotor (mid-plane, z mirrored beyond it), G = t_s + 2g for a single rotor with an opposite
  yoke, G → ∞ for a single rotor without yoke (then B_z,n = K_n e^{−uz}/(1 + µ_r coth(u l_m))).
  B_z(r,θ,z) = Σ_n B_z,n cos(n p (θ − θ_r)).
- Sources: D08 eq. 3.1 p.31 [26] (EV-03, after Vansompel 2013); D09 eq. 1 p.4 (EV-13, general form only); Bumby & Martin 2005
  cited by D10/D11 but not in the corpus (G8). The closed form above is my derivation (scalar potential, iron behind the
  magnet, H_t = 0 at z = G) and is algebraically identical to the engine's exponential form (`inferred`, hand algebra;
  numerically confirmed by C1a/C1b).
- Variables: z from the magnet face [mm]; l_m, g, t_s [mm]; B_r [T]; µ_r [–].
- Magnet data (EV-54, EV-55, Arnold catalog/N42 sheet, extract — Agent 5 to re-check): N42 B_r typical 1.315 T, min
  1.28 T; temperature coefficient of B_r −0.12 %/°C. µ_r: **no datasheet value found** (G23); apparent recoil slope
  B_r/(µ₀H_cB) ≈ 1.10 for N42 (`inferred`, EV-55) → µ_r = 1.05 stays `assumption`, sensitivity range 1.03–1.10.
- Assumptions/validity: linear magnets (constant µ_r, B_r at operating temperature); infinitely permeable, unsaturated back
  iron — D08 p.112 §11.3 reports back-plate saturation in its prototype (validity limit); 2-D solution per radius (no radial
  edge leakage); double rotor = identical, aligned rotors with N facing S; parallel magnetisation (no Halbach — D11 eq. 8–9
  is the Halbach alternative).
- Differences to D08 eq. 3.1: D08 divides by µ_PM and uses sinh(u z₂)/sinh(u h_PM), which is exact only for µ_PM = 1; for
  µ_PM = 1.05 it is 3–4 % lower (C1b). D08 sums all n without stating "odd only".
- Reference: (a) large pole pitch: B₁ = 0.946752 T = 1-D circuit (4/π) sin(πα_p/2) B_r l_m/(l_m + µ_r G) (rel. 5e-12, C1a);
  (b) D08 Table 3.1 rotor, µ = 1: identical to D08 eq. 3.1 (1.1952 T); (c) D09 Table 3 rotor, mid-plane, r = 35.5 mm:
  pole-centre 0.738 T (µ_r 1.05, `assumption`) vs D09 Fig. 7 FEA ≈0.72 T and Fig. 5 ≈0.75 T (figure readings, `inferred`).
- Tolerance: ±5 % on B₁ at mid-radius vs 3-D FEA. Reasoning: D09 reports < 1 % fundamental difference for its comparable
  scalar-potential model at mean radius (p.4); add µ_r and B_r(T) uncertainty (both unsourced) and back-iron saturation.
  Not valid within about one magnetic gap of the magnet's radial ends, where D09 Fig. 7 shows up to ≈40 % drop → apply a
  radial correction factor (D09 used an FEA-fitted B_r(r), p.5) — Phase 2 item.
- Gate: `reuse with change` (add α_p(r) EQ-04, Halbach option, edge correction, temperature-dependent B_r; keep odd
  harmonics, make the set configurable).

## EQ-06 Back-EMF and flux linkage of a copper path

- Formula: e(t) = ω_m Σ_seg r_m B_z(r_m, θ_m − θ_r, z_L) Δr (Δr signed along the current direction);
  harmonic form Ke_n = |Σ_seg B_z,n(r_m, z_L) r_m Δr e^{−j n p θ_m}| [V·s/rad, peak, per mechanical rad/s] (T·mm² × 1e-6).
  Equivalent loop form: ψ = ∬ B_z dA, E = −dψ/dt = −(dψ/dθ_m) ω_m (D08 eq. 3.14).
- Derivation (`inferred`): for an in-plane element with relative velocity v = ω r θ̂, (v × B)·dl = ω r B_z dr for any B, so
  only radial components of the path and only B_z contribute; for a closed loop Stokes' theorem gives the loop form.
- Sources: D08 eq. 3.6–3.14 p.33–36 (EV-02, EV-04); D09 eq. 5–11 p.5 (EV-14); D07 p.3 (EV-17); D11 eq. 10–13 p.3–4 (EV-46);
  D15 p.8 (via current axial → no EMF, EV-43).
- Validity: rigid rotation; field from EQ-05 evaluated at each layer's z (G3); segments ≤ 0.5 mm.
- Reference: 1-turn radial-sided sector coil (12/10, 2 layers): engine 5.410784e-3 V·s/rad vs closed form 5.410812e-3
  (−5e-6, C2, `verified (reproduced)`). Oracle for Phase 2: D08 measured K_e (L-L peak) = 0.031 V·s/rad (Table 9.1 p.98,
  O1) — needs EQ-04 for its T-arrangement magnets and the gap ambiguity G10 resolved.
- Tolerance: 1e-4 relative vs closed forms for idealised geometry (numerical integration); ±8 % vs D08 measurement (D08's
  own analytical model deviated by max. 8 %, p.98); ±5 % vs D09 calc/FEA 6.21/6.20 V (Tables 4–5 p.6) once turn data are known.
- O2 details now available (EV-62, Agent 5): D09 concentric board = 12 non-overlapping trapezoidal spiral coils per layer,
  each with a via at its inner end, 2 layers, 6 terminals (open phases), air gap 1 mm per side (Table 2 p.3; consistent with
  Table 3 p.4: 7 mm between rotor cores − 2 × 2 mm magnets = 3 mm = 1 mm PCB + 2 × 1 mm), 16 poles; turns per coil per layer
  ≈ 6–8 (`unresolved`). Until the turn count is fixed, O2 can test EQ-06 only as a ratio (Ke per turn) or as a sweep over
  N = 6, 7, 8.
- Gate: `reuse`.

## EQ-07 Phase assembly, per-layer EMF, parallel paths and circulating loss

- Formula: series chain E_ph = Σ_groups E_grp; group of parallel members i: E_grp = Σ_i (E_i/R_i) / Σ_i (1/R_i);
  R_grp = 1/Σ(1/R_i); circulating loss P_c = Σ_i |E_i − E_grp|² / (2R_i) (E peak phasors). Member EMFs are evaluated at
  their own layer z (EQ-06).
- Check (`inferred`, algebra): for two members this reduces to P_c = |E₁ − E₂|²/(2(R₁ + R₂)), i.e. D01 eq. 2
  P_c = V_d²/(R₁ + R₂ + R_c) with RMS V_d and R_c = 0.
- Sources: D01 eq. 1–2 p.2–3 (EV-20); D02 p.4–5 Fig. 11 (EV-35); D13 p.3 (EV-42); conflict with D15 p.8 equal-flux
  assumption (G3).
- Validity: resistive circulating path (inductance of the loop neglected → upper bound at high frequency is not guaranteed;
  at low frequency conservative).
- Reference: identity above (exact); magnitude example per-layer B₁ spread 0.336 % for 6 layers in 0.62 mm (C1d).
- Tolerance: exact identity; physical accuracy depends on G3 (Agent 4: 3-D FEA of per-layer EMF).
- Gate: `reuse with change` — add series connection of layer pairs and per-coil elements from the new generator.

## EQ-08 Winding factor of concentrated (spiral) coils and phase assignment

- Formula: α_k = p θ_k (coil phasor, el.); 60° belts A+, −C, B+, −A, C+, −B; k_d,n = |Σ_{k∈A} s_k e^{j n α_k}|/N_A;
  k_p,n = |sin(n p σ/2)|; k_w,n = k_d,n k_p,n. Feasibility: Q/(m·t) integer, t = gcd(Q, p). Spiral average:
  k_p,avg,n = (1/N) Σ_t |sin(n p σ_t/2)|, σ_t(r) = θ_cp − 2 asin(d_t/r) (parallel sides).
- Additional sources (reconciliation): D12 eq. 1 p.3 N_c/N_pm = m/(m+1) for coreless concentrated-coil generators (EV-56;
  12 coils/16 poles satisfies it; it is one design rule, not a general feasibility test); D07 p.3 §2.2 (EV-58); **D15 eq. 6
  p.7: PCB pitch factor as the average of per-turn pitch factors** K_pν = (1/N) Σ sin(((β − 2α_i)/β)(π/2)ν) (EV-59) — the
  spiral-average term below is therefore now sourced (`verified` as printed). Dai Pré & Bianchi 2006 (EV-60) and Pyrhönen
  et al. (EV-61): bibliographic only, content not accessed (G24) → the Q/(m·t) feasibility rule remains
  `assumption: standard result`, and every chosen combination is checked by explicit phasor computation.
- Sources: D04 eq. 1 p.5 (EV-26, integral-slot special case); D07 p.3 ("slot" → "coil side", star of slots); D09 p.5; D11
  eq. 14 p.4 (overall coefficient as average over turns, EV-46). Feasibility rule and FSCW star of slots: textbook,
  `assumption: standard result, source needed` (proposed Pyrhönen et al.; Bianchi & Dai Prè 2006).
- Reference: `checks/kw.py` reproduces D08 Fig. 3.7 (p.36) "AabBCcaABbcC" for 12/10 (`verified (reproduced)`); k_w1: 12/10
  0.933, 12/14 0.933, 12/16 0.866, 18/16 0.945, 15/16 0.951, 24/16 0.866, 18/20 0.945 (table in `topology_analysis.md` §2.2).
- Validity: identical coils equally spaced; σ at mean radius for the turn average (radius dependence via the numerical
  utilisation factor of EQ-06).
- Tolerance: 1e-9 (exact arithmetic) for k_d, k_p; pattern identical to published tables.
- Gate: `replace` `starOfSlots`/`balancedSectorList` (belt-edge bug, C6) with integer phasor arithmetic; keep the
  engine's numerical "kw1" renamed as utilisation factor; replace `kdAnalytic`.

## EQ-09 EMF/torque constants, star/delta conversion

- Formula: Ke,ph = |E₁|/ω_m (peak phase EMF per mech. rad/s); star: Ke,LL = √3 Ke,ph, I_ph = I_line; delta: Ke,LL = Ke,ph,
  I_ph = I_line/√3. T = (m/2) Ke,ph Î_ph = (m/√2) Ke,ph I_ph,rms; Kt per line A_rms = (m/√2) Ke,ph (star) or
  (m/√2) Ke,ph/√3 (delta); K_v = 1/Ke,LL [rad/(V·s)]; rpm/V = 60/(2π Ke,LL). R_LL = 2R_ph (star), 2R_ph/3 (delta).
- Sources: D08 eq. 3.14 p.36 and Table 9.1 p.98 (K_e L-L peak, K_v = 32.32 rad/(V·s)); D06 eq. 2 p.3 (EV-24, T = m E I·60/(2πN)).
- Validity: fundamental, sinusoidal current in phase with EMF (q-axis); harmonics → ripple not included.
- Reference: D08 data 1.47 V at 454 rpm → 0.0309, 9.35 V at 2877 rpm → 0.0310 V·s/rad, 1/32.32 = 0.03094 → definition
  consistent (C9). Engine power balance T ω = m E_rms I_rms holds to 1e-9 (test ELE-07).
- Tolerance: exact identities. When comparing with measured "peak" L-L voltages, compare the synthesised waveform peak,
  not the fundamental (harmonics).
- Gate: `reuse`.

## EQ-10 DC resistance with temperature

- Formula: ρ_T = ρ₂₀ (1 + α (T − 20 °C)); R_ph = Σ_prims ρ_T L_i/(w_i t_i) + Σ R_via + R_links (+ parallel combination per
  EQ-07).
- Constants: ρ₂₀ = 1.7241e-8 Ω·m (1/58 Ω·mm²/m), α₂₀ = 0.00393 /K — **sourced**: International Annealed Copper Standard,
  IEC Publication 28 (1925) as reproduced in NBS Handbook 100 *Copper Wire Tables* (1966) p.2–4, App. 5 (EV-53; read by
  Agent 5 via an extract, page numbers to be re-checked) → `verified` for annealed copper. Remaining `assumption`:
  electrodeposited/rolled PCB copper behaves like IACS copper (G6 partly open) → manufacturer data or 4-wire coupon. The
  engine constant 1.724e-8 differs from 1.7241e-8 by 0.006 % (negligible). 1 oz → 34.8 µm `assumption` (engine and D08 p.54 use 34.8 µm; repository record 35.0–35.6 µm);
  finished thickness is supplier-dependent (`unresolved`).
- Sources: D08 eq. 3.37–3.38 p.45 (EV-08); D10 eq. 8 p.4 (EV-28/29); D15 eq. 10 p.7 (EV-44).
- Reference: 1000 × 0.5 mm × 34.8 µm → 0.99080 Ω (20 °C), 1.14656 Ω (60 °C) (C3); D08 phase: 0.381 Ω (EQ-03 lengths, 50 °C per
  Table 4.5 p.54) vs 0.39 Ω printed (Table 4.6 p.57), −2.3 % (C7).
- Tolerance: ±8 % vs measured DC resistance at known temperature. Reasoning: D10 measured 2.15 Ω vs its simulation 2.00 Ω
  (+7.5 %, p.8); D09 measured 1.07 Ω vs calculated 1.04 Ω (+2.9 %, Tables 1/6 p.3/7); copper thickness and via/joint
  resistances are not known a priori. Tighten after a coupon measurement.
- O2 detail (EV-62): D09's 3244 mm phase length over 8 coil-layers ≈ 405 mm per coil-layer; with EQ-03 this is the route to
  fix the turn count (Agent 4 task T-D).
- Gate: `reuse` (constants now sourced, EV-53; keep the PCB-copper caveat as a labelled assumption).

## EQ-11 Via barrel resistance

- Formula: A = π(r² − (r − t_p)²) = π(2 r t_p − t_p²), r = drill/2; R_via = ρ_T l / A; n vias in parallel → R/n.
- Sources: D05 eq. 3–6 p.6–8 (EV-37); plating 25 µm assumed there.
- Validity: barrel only; no pad spreading resistance, no current crowding (D05 FEA shows crowding at vias, EV-38, distributed
  winding with yoke — not transferable).
- Reference: drill 0.3 mm, t_p 25 µm → A = 0.021598 mm² (test ELE-04); l = 0.2 mm, 20 °C → 0.160 mΩ (C9).
- Tolerance: none claimed (no measured oracle, G7) — formula standard; crowding `unresolved`.
- Gate: `reuse with change` (plating and via count per transition as inputs; count every via in the current path).

## EQ-12 Eddy-current loss in traces

- Formula: P_eddy = (σ/24) Σ_n (n ω_e)² Σ_seg L_seg (B̂_z,n² w³ t + B̂_t,n² w t³), B̂ = peak amplitude of harmonic n at the
  trace (EQ-05), σ = 1/ρ_T.
- Sources: D03 eq. 2 p.5 (EV-36); D14 eq. 3 p.5 (EV-39) — same 1/24 coefficient. D04 eq. 9 p.7 (EV-27) and D10 eq. 10 p.4
  (EV-30) use π²f²/(3ρ) = ω²/(12ρ) with B "peaks" → twice as large (G4).
- Choice and justification (`inferred`): for a strip of width w in a uniform field B̂ sin ωt normal to its face, J = σ x dB/dt,
  ⟨x²⟩ = w²/12 and ⟨(dB/dt)²⟩ = ω²B̂²/2 → σω²B̂²w²/24 per unit volume — the classical thin-lamination result
  π²σd²B̂²f²/6 (standard; textbook source needed). The 1/12 form is correct only with RMS B. Adopt the D03 form with peak
  amplitudes; tangential field pairs with thickness (D03), not width (D04/D10).
- Validity: w, t ≪ skin depth (EQ-13); field uniform across the conductor; no proximity effect from load current; straight
  conductor sections (end turns: the B_t term should be dropped for field along the conductor — engine applies it, minor
  over-estimate).
- Reference: one radial trace 20 × 0.5 mm × 34.8 µm, B̂_z 0.70 T, 16 poles at 1000 rpm (f_e 133.3 Hz): 7.23e-5 W (adopted)
  vs 1.45e-4 W (D04/D10 form); δ = 5.72 mm (C9). Order-of-magnitude statement: D09 p.3 "10–20 mW at 2000 RPM" for its PCB
  windings (not a separated measurement).
- Tolerance: ±20 % vs a 2-D FEM of a single trace in a uniform sinusoidal field (`assumption` until Agent 4 runs it).
- Gate: `reuse` (drop the B_t term on circumferential segments as a later refinement).

## EQ-13 Skin depth (validity check for EQ-10/EQ-12)

- Formula: δ = 1/√(π f µ0 σ). Source: D01 eq. 4 p.3 (EV-21).
- Reference: 133.3 Hz, 20 °C → 5.72 mm (C9); ≈2.1 mm at 1 kHz (test ELE-02). Tolerance: exact.
- Gate: `reuse` (warn when w or t > δ/3 — threshold `assumption`, cf. D03 strand rule δ/3, EV-33).

## EQ-14 Inductance — first estimate only

- Formula (a) magnetising (synchronous, balanced 3-phase): L_m = (3µ0/(4π)) (N k_w1)² (D_o² − D_i²) / (p² δ′),
  δ′ = iron-to-iron gap (2l_m + 2g + t_s, magnets µ_r ≈ 1), N series turns per phase.
  Derivation (`inferred`): F̂ = (3/2)(4/π)(N k_w/(2p)) Î; B̂ = µ0 F̂/δ′; Φ = B̂ (R_o² − R_i²)/p; ψ̂ = N k_w Φ.
- (b) engine current-sheet model (`windingInductance`): all space orders ν of the radial-conductor distribution between the
  irons, inter-layer coupling e^{−νΔz/r}, sinc² width factor; L_s = L_self − M; end turns excluded.
- Sources: D10 eq. 11–14 p.4–5 (EV-31); D15 eq. 14 p.8 (EV-44); gap G1. My derivation **agrees with D10 eq. 14 as printed**;
  D15 eq. 14 is π/2 larger. **G1 revised by Agent 5 (evidence_gaps.md G1, 2026-10-04):** with F̂₁ = (m√2/π)(N₁k_w1/p)I₁
  both derivations give L₁ = mµ₀(N₁k_w1)²(D_mo² − D_mi²)/(4πδ′p²) = D10 eq. 14 for m = 3; the error is in eq. 12 of D10 and
  D15 (√2m/2 instead of √2m/π), and eq. 11 of both omits 1/p. Conflict resolved in favour of D10 eq. 14 (`inferred`, two
  independent derivations; Agent 4 to confirm). G1 itself stays `unresolved`: magnetising term only.
- Validity: (a) sinusoidal MMF, no leakage/end-turn/sub-harmonic terms (FSCW sub-harmonics are large: fundamental share only
  0.37 in the engine example); (b) radial conductors only.
- Reference (C9, 12/16, 8 turns, 2 layers, default assumptions): engine L_s = 17.96 µH; (a) 4.67 µH (k_w 0.600 numeric) /
  9.74 µH (k_w 0.866); D15 form 7.34 / 15.31 µH. Oracles: D09 measured 14.8 µH concentric 2 layers (Table 6 p.7, turn count
  unknown, G2); D07 measured L_s 22.3 µH, M −8.55 µH (Table 4 p.8, wave).
- Tolerance: none claimed; target ±20 % vs LCR measurement after validation (`assumption`).
- Gate: `cannot verify yet` — port only as a labelled estimate; Phase 2: Neumann filament model + FEMM/3-D check (G1 proposal).

## EQ-15 IPC-2221 current capacity

- Formula: I = k ΔT^0.44 A^0.725, A in mil², k = 0.048 (external) / 0.024 (internal).
- Sources: IPC-2221 — **not in the corpus** (G5); corpus cites IPC-2221 only for spacing (D03 p.4, EV-32; D18 p.10, EV-50).
  `assumption: standard value, source needed` (licensed copy; IPC-2152 is the newer standard).
- Reference: 0.5 mm × 34.8 µm, ΔT 20 K → 1.955 A external / 0.977 A internal (C9).
- Limitation (`inferred`): single isolated trace in still air; densely packed coils share heat → use EQ-17 for limits.
- Gate: `cannot verify yet` — display as "guideline (unverified)".

## EQ-16 Mass

- Formula: m_Cu = ρ_Cu Σ_L A_Cu,L t_L; m_lam = ρ_lam (A_board t_board − V_Cu) (+ mask, optional); ρ_Cu = 8.89 g/cm³
  (IACS standard density, NBS Handbook 100 p.4, EV-53 — `verified` for annealed copper; the engine's 8.96 g/cm³ is
  unsourced, +0.8 %); ρ_FR-4 1.85 g/cm³ — `assumption: typical value, source needed` (laminate datasheet).
- Reference (example, `assumption`): 12-gon 93 mm flats minus Ø25 bore ≈ 6461 mm² × 0.62 mm × 1.85 g/cm³ ≈ 7.4 g laminate;
  copper 6 layers × 50 % of the 18–38 mm annulus × 34.8 µm ≈ 367 mm³ ≈ 3.3 g (hand arithmetic).
- Tolerance: ±10 % vs weighed board (resin content, mask, plating) — `assumption`.
- Gate: `reuse with change` (densities per stack-up material with source; holes and mask).

## EQ-17 First-order thermal estimate

- Formula (engine): ΔT = P_loss / (h · 2 A_board). Lumped alternative (D01 eq. 6–8 p.4): θ = L/(K A_c), ΔT_cond = P θ,
  ΔT_conv = P/(h_t A_PCB) with h_t = 10 W/m²K "widely used", K (Table 3 p.4): Cu 355, FR-4 0.25, mask 0.21, air 0.0275 W/mK;
  D08 network eq. 7.1–7.5 p.81–83 (EV-11).
- Assumptions: uniform board temperature; h unsourced in the engine (default 30 W/m²K vs D01 10 W/m²K).
- Reference: D08 4 W per side × 5.11 K/W = 20.44 K → 40.44 °C at 20 °C ambient (D08 p.83–84 [78–79] values; arithmetic
  consistent).
  Oracle for Phase 2: D10 measured 110.2 °C at 12 A/mm², 27 °C ambient, natural cooling (p.10).
- Tolerance: ±30 % on ΔT (`assumption`; h uncertain by ×3 between sources).
- Gate: `reuse with change` (cite h, add conduction path and enclosure option, validate vs D10).

## EQ-18 EMF waveform and THD

- Formula: E(θ_e) = Σ_n |E_n| cos(n θ_e + arg E_n); THD_ph = √(Σ_{n>1} Ke_n²)/Ke_1; line EMF = difference of phase
  waveforms (triplens cancel in star).
- Sources: engine `emfWaveform`/`lineWaveform`; oracle D09 Table 7 p.8 concentric THD 5.7 % (measured; phase/line basis
  not stated → `unresolved`).
- Tolerance: n/a until the basis of D09's THD is known.
- Gate: `reuse` (report both phase and line THD).

## EQ-19 Delta circulating current

- Formula: I_circ,n = |Σ_ph E_n| / R_loop (resistance-limited), P = Σ_n I_circ,n² R_loop / 2.
- Source: engine `applyConnection`; relevance: combinations with k_w3 ≠ 0 (12/14 0.50, 18/16 0.577; EQ-08).
- Limitation: zero-sequence inductance ignored → upper bound (`inferred`).
- Gate: `reuse with change` (add zero-sequence reactance once EQ-14 is validated).

## EQ-20 Torque–speed envelope

- Formula: steady-state dq model with R_ph, L_s, Ke, inverter voltage limit (SVPWM V_LL,rms = V_dc/√2; SPWM √3V_dc/(2√2);
  six-step fundamental √6V_dc/π) and current limit.
- Sources: standard PMSM/inverter theory — textbook source needed (`assumption`).
- Gate: `cannot verify yet` (depends on EQ-14).

## EQ-21 Copper-loss-budget current (design aid, optional)

- Formula: I_ph = √((P_Cu/m)/R_ph). Source: D08 eq. 4.3 p.53 (EV-09).
- Reference: P_Cu = 4 W, R_ph = 0.39 Ω → 1.849 A vs 1.84 A in D08 Table 4.6 p.57 (`verified (reproduced)`, confirms the reading
  (4 W/3)/R).
- Gate: not in engine → add (optional).

## EQ-22 Current density

- Formula: J = I_ph/(a w t) with a parallel paths. Context only: D16 p.16–17 limits 30 A/mm² (yoke machine, FEA, EV-49); D10
  12 A/mm² → 110.2 °C (p.10). No validated limit for spiral PCB stators (`unresolved`).
- Gate: `reuse` (engine `currentDensity`).

---

## Gate summary

| EQ | Verdict | Blocking item before port |
|---|---|---|
| 01, 06, 09, 10, 12, 13, 18, 22 | reuse | none (EQ-10 constants sourced, EV-53; PCB-copper caveat stays a labelled assumption) |
| 05, 07, 11, 16, 17, 19 | reuse with change | α_p(r), series pairs, via counts, material densities, h source |
| 03, 04, 21 | add (not in engine) | EQ-03: engine path-length sum reused, closed form added as check (registry gate `reuse`); EQ-04, EQ-21: new implementation (registry gate `replace` = implement from this spec) |
| 02, 08 | replace | constructive turn generator; integer star of slots |
| 14, 15, 20 | cannot verify yet | inductance oracle (G1/G2), IPC source (G5) |

Validation tasks proposed for Agent 4 (`not tested`): T-A 3-D FEA (or FEMM 2-D at mean radius) of the D09 rotor for EQ-05
and per-layer B_z (G3); T-B 2-D FEM of one trace for EQ-12; T-C re-create O1 (D08) with EQ-04 magnets for EQ-06 (±8 %);
T-D recover D09 concentric turn count (Fig. 1a/2, image measurement) and check EQ-10 (±8 %), EQ-14 vs 14.8 µH; T-E arbitrate
EQ-14 (D10 vs D15 form) by independent derivation (Agent 5 now agrees with D10 eq. 14 — confirmation only); T-F re-run
C1–C9 against the Python port; T-G check the generator against the EQ-02 loop criterion and EQ-03 values in
`answers_to_agents.md` §2.2.

## Equation status (Phase 1 evidence status, per equation)

This is the status of the *equation and its evidence* as of this draft; the status of a computed *result* follows the rule
below. Implementation status starts as `not tested` for every port and becomes irrelevant once its tests pass in CI
(ADR-0003 item 5).

| EQ | Status | Why |
|---|---|---|
| 01, 04, 09, 13, 21, 22 | verified | geometric/definitional identities or reproduced published numbers (D08 eq. 3.2/3.3, Table 9.1, eq. 4.3) |
| 06 | verified | kernel exact for in-plane conductors; closed form reproduced to 5e-6 (C2); accuracy of results inherits EQ-05 |
| 10 | verified | D08 eq. 3.37–3.38; constants EV-53; PCB copper = IACS remains an assumption input |
| 02, 03 | inferred | derived from D08's own loop geometry; printed eq. 3.25–3.26 and 3.34/3.36 corrected |
| 05, 07, 08, 11, 12, 18, 19 | inferred | derivations/identities checked; no 3-D FEA or measurement oracle yet |
| 16, 17 | assumption | laminate density and film coefficient h unsourced or disputed |
| 14, 15, 20 | unresolved | gate `cannot verify yet` → outputs labelled "estimate" / "guideline" |

## Status rule for computed results (answer to Agents 1 and 6; details `answers_to_agents.md` §1.1)

result status = weakest of { equation status (table above); implementation status (`not tested` until its tests pass);
status of every input the kernel actually uses (user-entered or KiCad-imported = neutral; default or unsourced = `assumption`;
sourced constant = its EV status); validity cap (any violated validity limit → `unresolved`) }, with the order
`unresolved` < `not tested` < `assumption` < `inferred` < `verified` (ADR-0003 order, agreed). `verified` for a result of a
new design is reached only by exact identities/counts (pole pitch, coil pitch, k_w by exact arithmetic, turn count,
generated track length) or when every input is neutral/verified and every equation in the chain is `verified`; it is
never called "measured".

## Dominant assumed inputs per equation

"Dominant" = the inputs that, when left at a default or unsourced value, dominate the uncertainty of the result; the UI lists
them first under "n assumptions". Every other used default still caps the status at `assumption`.

| EQ | Dominant assumed inputs |
|---|---|
| 01 | none (exact) |
| 02, 03 | trace width w, clearance s, coil gap (fabricator capability); centre-via pad/clearance (eye); loop model (concentric loops vs spiral) |
| 04 | magnet block width and orientation (repository: 20 mm side radial — unresolved) |
| 05 | B_r (grade, temperature), µ_r (G23), magnet thickness l_m, air gap g, unsaturated back iron, α_p |
| 06 | as EQ-05 + copper-layer z from the stack-up |
| 07 | per-layer z (dielectric thicknesses), member resistances (copper thickness) |
| 08 | none for k_d/k_p (exact); turn spans from the generated geometry |
| 09 | as EQ-06 (Ke); operating current |
| 10 | finished copper thickness t, winding temperature T, PCB copper = IACS (G6) |
| 11 | plating thickness t_p, barrel length, vias per transition |
| 12 | B̂ (via EQ-05), copper thickness, electrical frequency; /24 coefficient (G4 by derivation) |
| 13 | winding temperature (ρ_T) |
| 14 | effective gap δ′, k_w1, omission of end-turn/leakage terms |
| 15 | allowed temperature rise ΔT; external/internal classification; standard not in corpus (G5) |
| 16 | laminate density, copper fill/thickness |
| 17 | film coefficient h (10 vs 30 W/m²K), cooling area/enclosure |
| 18 | magnet shape (α_p(r)), µ_r |
| 19 | loop resistance, triplen EMF (magnet shape) |
| 20 | L_s (EQ-14), DC-link voltage, modulation |
| 21 | copper-loss budget P_Cu (user target) |
| 22 | operating current, copper thickness |
