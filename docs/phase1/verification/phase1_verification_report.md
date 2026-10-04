Prepared by: Agent 4 — Independent Verificator — model: claude-opus-5-5

# Phase 1 independent verification report (2026-10-04)

Scope: everything under `docs/phase1/` (evidence, engineering, software, design, architecture) plus `docs/decision_log.md`,
checked against `docs/PROJECT_BRIEF.md`. Status labels follow PROJECT_BRIEF §3. "verified (reproduced)" means I re-ran or
re-implemented the check myself in this container; "verified (read)" means I opened the cited page/file/URL myself.
Nothing here is a measurement. Defect IDs (DEF-xx) are consolidated in `defect_list.md`. My own scripts are in
`docs/phase1/verification/checks/` (v1–v8); every number quoted below was printed by one of them unless stated.

## 0. Summary of verdicts

| Area | Verdict | Defects |
|---|---|---|
| a. Evidence spot-checks (14 register rows + oracle O1 table + 2 KiCad claims) | **pass** | DEF-12, DEF-15 (minor) |
| b. Equation specification EQ-01…22 and registry | **pass with defects** | DEF-03, DEF-08, DEF-09, DEF-10, DEF-14 (minor) |
| c. Topology analysis and concept drawing | **pass** | DEF-04, DEF-11 (minor, in dependent documents) |
| d. Feature inventory and migration mapping | **pass** | DEF-05 (minor, stale wording) |
| e. Requirements, acceptance criteria, test plan | **pass with defects** | **DEF-01 (major)**, DEF-03, DEF-04, DEF-09, DEF-10, DEF-11, DEF-17 |
| f. Architecture and ADRs | **pass with defects** | **DEF-02 (major)**, DEF-05, DEF-12, DEF-13 |
| g. UX/UI mockups | **pass with defects** | DEF-06, DEF-07, DEF-16 (minor) |
| h. Language and branding | **pass** | — |
| i. Process rules | **pass** | — (two observations) |

Blockers (would mislead the user's Phase 2 approval): **none found**. Two major defects must be fixed before the
affected Phase 2 code is written (DRC acceptance rule; status-combination rule). Gate recommendation:
`phase1_gate_recommendation.md`.

---

## a. Evidence spot-checks

Method: I opened every cited location myself (`pdftotext -layout -f N -l N`, page renders with `pdftoppm`/`pdfimages`
and the Read tool for equation images, own Gerber parser, WebFetch/PyPI JSON for URLs). Page numbers are PDF indices.

| # | Row | What I found at the cited location (short) | Claim / location correct? | "Applies to spiral coil" judgement | Status |
|---|---|---|---|---|---|
| 1 | EV-02 | D08 p.33 (printed 28): Fig. 3.4 "Concentrated spiral windings approximated by concentric loops", eq. 3.5 w_d = w_tr + w_s, 3.6 Φ = ∬B dS, 3.7 slice-average B̄; p.34: eq. 3.8–3.11, Φ_l,q = B̄ t_sl r (φ_MAX − φ_MIN) | yes (register p.32–35 brackets it) | reasonable (direct spiral-coil method) | verified (read) |
| 2 | EV-06 | D08 p.43 (printed 38) §3.3: N_c < ½((r_o − r_i)/w_d + 1) (3.24); N_c1 (3.25); N_c2 (3.26) — verbatim | yes | reasonable (single-layer geometry rule) | verified (read) |
| 3 | EV-07 | D08 p.44–45 (printed 39–40): θ_cs = π/p (3.27); L_s,i = 2·(d/tan φ_out − d/tan φ_in) (3.34) **and** L_tot,i = L_out + L_in + 2L_s (3.36) → each side counted twice | yes; correction θ_cs → 2π/Q and one pair of sides is geometrically required | reasonable; but the added remark "suggesting the thesis model itself used π/p" is weak → DEF-15 | verified (read); remark `inferred`, weak |
| 4 | EV-13 | D09 p.4: scalar-potential model, "<1% difference at the fundamental components" at mean radius; "it does not calculate the leakage flux at the inner and outer edges"; p.5: B_r(r) "found via curve fitting" of FEA (Fig. 7) | yes | reasonable ("partly") | verified (read) |
| 5 | EV-14 | D09 p.5 eqs. 5–11: φ = ∬B·dS, V = −N dφ/dt, B = â_z B_r(r) B_max sin(ωt + pθ), double integrals with r-dependent limits; written for the parallel (wave) winding, "can be applied to any other wave winding topology regardless of the winding shape" | yes (paraphrase "any loop shape" is slightly broader than the text) | reasonable — transfer to spiral loops is `inferred` (Stokes argument holds for any closed loop) | verified (read) |
| 6 | EV-53 | NBS Handbook 100 (WebFetch extract): p.2 "0.017 241 ohm-mm²/meter at 20 °C", "58 meter/ohm-mm²"; p.3 "α20 = 0.003 93"; p.4 "8.89 g/cm³"; p.39 App. 5 IEC Publication 28 | yes (page numbers confirmed by the extract) | reasonable: annealed copper; PCB electro-deposited copper = IACS stays an assumption (G6) | verified (read, extract) |
| 7 | EV-57 | D06 p.2: "For the AFPM motor with the laminated-core, … GCD(Nc, Nm) = 2K, so as to minimize the torque pulsations" | yes | reasonable ("partly"); for coreless stators the cogging motive does not exist | verified (read) |
| 8 | EV-58 | D07 p.3: relations of slotted PMSM windings "can be directly used for coreless winding with the exception that the term 'slot' is replaced by the 'coil side'" [27] | yes | reasonable (method) | verified (read) |
| 9 | EV-59 | D15 p.7 eq. 6: K_pν = (1/N) Σ k_pi = (1/N) Σ sin(((β − 2α_i)/β)(π/2)ν) — verbatim from render | yes | reasonable | verified (read) |
| 10 | EV-71 | Own parse (`checks/v5_gerber_endturns.py`): G1 674 arcs; 144 arcs concentric with the board, radii 14.3–17.2 mm; arcs centred at r = 26.0 mm with 6 radii 13.5–16.4 mm on axes 0° + k·30° (G1) and 15° + k·30° (G3); G3 696 arcs | yes, numbers identical | reasonable ("wave-like series path" stays an interpretation) | verified (reproduced) |
| 11 | EV-31 | D10 p.4 eqs. 11–12, p.5 eqs. 13–14 (renders): (11) F₁ = (m√2/π)N₁k_w1I₁; (12) B_m1 = (µ₀/δ′)(√2m/2)(N₁k_w1/p)I₁; (13) ψ₁ = (1/√2)N₁k_w1(2/π)B_m1(π/8p)(D²_mo − D²_mi); (14) L₁ = (3µ₀/πδ′)(N₁k_w1/2p)²(D²_mo − D²_mi) | yes; revised note "(14) consistent, (12) inconsistent" confirmed (§b.5) | reasonable ("partly", magnetising term only) | verified (read) |
| 12 | EV-44 | D15 p.7 eqs. 10–12, p.8 eqs. 13–14 (renders): same (11)–(13) as D10; (14) L = m(µ₀/δ)(Nk_w1)²/(8p²)(D²_out − D²_in) | yes; (14) follows from its (12)–(13) and is π/2 larger than D10 (14) | reasonable | verified (read) |
| 13 | EV-62 | D09 p.2 Fig. 1a (embedded 1927 × 1376 raster): I count **12** coil eyes, 6 terminals at the top, ≈6–7 nested loops per coil; p.3 Table 1 concentric 3244 mm, 171 mm², 1.04 Ω; Table 2 (16 poles, w 0.8, s 0.2, 70 µm, 2 layers) | yes | reasonable (oracle O2 geometry) | verified (read); turn count stays `unresolved` |
| 14 | EV-08 | D08 p.45 (printed 40): ρ_T = ρ20(1 + α_c(T − 20°)) (3.37), R_phase = ρ_T L_tot/(w_tr t_tr) (3.38); no numeric ρ20/α | yes | reasonable | verified (read) |
| — | O1 table | D08 p.98 (printed 93) Table 9.1: V_peak 1.47 … 9.35 V at 454 … 2877 rpm, K_e 0.031 V·s/rad, "ratio of the peak line-line voltage to the rotor speed", mean K_v 32.32, model deviation "maximum 8%" | yes | — | verified (read) |
| — | O2 L | D09 p.7 Table 6 "Phase inductance, µH"; text: "Measured resistances and inductances … are presented in Table 6" — **no measurement method, frequency or rotor condition stated** (adds to G2; DEF-08) | yes | — | verified (read) |

**KiCad documentation claims** (fetched myself 2026-10-04):

| Claim | Official page | Result | Status |
|---|---|---|---|
| SWIG bindings deprecated in 9.0, removal planned 11.0 | https://dev-docs.kicad.org/en/apis-and-binding/pcbnew/ | "deprecated as of KiCad 9.0 … The current plan is to remove the SWIG bindings in KiCad 11.0"; "unstable and will generally change between KiCad major versions" | verified (read) |
| IPC API requires the running PCB editor | https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/for-addon-developers/ | "only supports communication with a running instance of the KiCad GUI"; "KiCad 9 and 10 only support IPC API plugins in the PCB Editor" | verified (read) |
| Per-plugin venv with KiCad's bundled Python | same page | "a Python virtual environment will be created for them … any declared dependencies will be installed"; venv at `${KICAD_CACHE_HOME}/python-environments/<plugin_identifier>`; Windows uses KiCad's own interpreter by default | verified (read) |
| …installed from `requirements.txt` | same page | the string "requirements.txt" is **not present** on the page. Confirmed instead in kicad-python 0.8.0 wheel (`pip download kicad-python==0.8.0`), `kipy/packaging/validate.py` l.138–164: "missing requirements.txt, KiCad will not install any Python packages for your plugin" | verified (read) — indirect source; Agent 5 cites it correctly, ADR-0004/brief attribute it to the official page → DEF-12 |
| API must be enabled in Preferences ▸ Plugins | https://pypi.org/project/kicad-python/ | "you must enable the API server through 'Preferences > Plugins'" — on PyPI, not on the dev-docs page | verified (read) |

Verdict a: **pass**. All 14 rows and the oracle table are correctly located and quoted; applicability judgements are
reasonable. Minor: DEF-15 (EV-07 remark), DEF-12 (citation attribution of requirements.txt).

---

## b. Equation specification (`engineering/equation_specification_draft.md`, `equation_registry_draft.json`)

### b.1 Structure, units, tolerances, reference cases (all 22 entries read)

- Registry parses (Python `json`), 22 entries EQ-01…EQ-22, every entry has formula, variables with units, sources,
  gate, status, tolerance {value, basis}, reference case — `verified (read)`.
- **Units / dimensions**: checked by hand for EQ-05 (T), 06 (T·mm² × 1e-6 = V·s/rad), 07 (W from V²/Ω), 09
  (T = (m/2)Ke Î: V·s/rad × A = N·m), 10, 11, 12 (S/m·s⁻²·T²·m⁵ = W), 13, 14 (H/m·m²/m = H), 15 (mil², stated), 16, 17,
  22 — **consistent**; no dimensional error found. EQ-10/EQ-11 mix mm inputs with Ω·m resistivity; the factor 1e-3 is in
  the engine and must be in the Python port (already covered by ADR-0009) — `verified (read)`.
- **Tolerance basis**: every entry states one. Weak bases: EQ-03 ±6 % (two cases only, DEF-09); EQ-05 ±5 % and EQ-12
  ±20 % are defined against 3-D FEA / 2-D FEM that nobody can run in Phase 2 (DEF-10); EQ-14 "±20 % vs LCR measurement"
  names an undefined quantity (DEF-08). EQ-12/14/16/17 are honestly labelled `assumption`.
- **Reference cases with published numbers and page refs**: EQ-02, 03 (D08 Tables 4.5/4.6 p.54/57), 08 (D08 Fig. 3.7
  p.36), 09 (D08 Table 9.1 p.98), 10 and 21 (D08 Table 4.6 p.57), 17 (D08 p.83–84), 05 (D09 figure reading, `inferred`).
  EQ-01, 07, 18, 19, 22 use arithmetic identities (adequate for identities); EQ-04, 06, 11, 12, 13, 15 use values computed
  by Agent 2 or the Xcoil engine (regression values, not independent oracles); EQ-20 has none (consistent with its gate).
- **Spot recomputation of registry values** (my arithmetic): EQ-04 α_p 0.8528/0.5467/0.4025; EQ-07 E_grp 0.99 V,
  P_c 1.0e-4 W; EQ-11 A 0.021598 mm², R 0.1596 mΩ; EQ-12 7.2314e-5 W; EQ-13 5.723 mm; EQ-15 1.955 A; EQ-16 6461.5 mm²,
  7.41 g, 3.27 g; EQ-17 40.44 °C; EQ-19 0.1 A, 0.015 W; EQ-22 57.47 A/mm²; EQ-09 0.03092 V·s/rad — all agree —
  `verified (reproduced)`.
- **EQ-12 coefficient** (G4): own derivation J = σx dB/dt, ⟨x²⟩ = w²/12, ⟨(dB/dt)²⟩ = ω²B̂²/2 → σω²B̂²w²/24 per volume =
  π²σd²B̂²f²/6 (thin-lamination form); the D04/D10 "π²f²/(3ρ)" form equals σω²/12 and is 2× larger with peak B → Agent 2's
  choice confirmed — `verified (reproduced)` (derivation; textbook source still not accessed).

### b.2 Winding factor / balanced-combination check — own star of slots

Command: `python3 docs/phase1/verification/checks/v1_star_of_slots.py` (exact `fractions.Fraction` angles; two tie rules
T1 = [c−30°, c+30°), T2 = (c−30°, c+30°]; written from scratch, does not import `checks/kw.py`).

| Q/2p | t | balanced (T1 / T2) | phasors on a belt edge | k_d1 | k_p1 | k_w1 | k_w3 | k_w5 | k_w7 | pattern (T1) |
|---|---|---|---|---|---|---|---|---|---|---|
| 12/10 | 1 | yes / yes | **6** | 0.9659 | 0.9659 | 0.9330 | 0.500 | 0.067 | 0.067 | AabBCcaABbcC (= D08 Fig. 3.7) |
| 12/14 | 1 | yes / yes | 6 | 0.9659 | 0.9659 | 0.9330 | 0.500 | 0.067 | 0.067 | ACcbBAacCBba |
| 12/16 | 4 | yes / yes | 0 | 1.0000 | 0.8660 | 0.8660 | 0.000 | 0.866 | 0.866 | ACBACBACBACB |
| 18/16 | 2 | yes / yes | 0 | 0.9598 | 0.9848 | 0.9452 | 0.577 | 0.140 | 0.061 | AabBbcCcaAabBbcCca |
| 16/16 | 8 | **no** (counts 16/0/0) | 0 | — | — | — | — | — | — | — |

Also 15/16 0.9514, 24/16 0.866, 9/10 and 18/20 0.9452, 24/14 0.7598, 24/22 and 24/26 0.9495 (all balanced). M3
(second group rotated π/Q): 12/10 and 12/14 k_w1 0.9330 → 0.9250, k_w11 = k_w13 0.9330 → 0.1218; 12/16 unchanged.
**Every value and pattern in `topology_analysis.md` §2.2 and §4.2 is reproduced** — `verified (reproduced)`.

**Agent 2's starOfSlots bug claim** (labelled K6 / Q-1 / C6 in Agent 2's files; the label "Bug 1" does not occur in any
Phase 1 document). Command: `node docs/phase1/verification/checks/v2_engine_star_of_slots.js` (engine loaded read-only):
- engine `starOfSlots` → 12/14 `ok=false`, counts 5,4,3, pattern ACcbBAaACBba; 24/14 9,8,7; 24/22 9,6,9; 24/26 7,9,8;
  12/10, 12/16, 18/16, 15/16, 9/10 ok; 16/16 ok=false (correct). `balancedSectorList(14)` = 3,6,9,15,18,21,27,30 (12 and
  24 missing).
- Mechanism (raw value of the engine's belt-index expression `((a + π/6) mod 2π)/(π/3)`): for 12/14 coil 7 at 30° gives
  0.99999999999999933 → floor 0 (A+) while coil 9 at 90° gives 2.0000000000000018 → floor 2 (B+): inconsistent tie
  breaking → unequal counts.
- **Claim confirmed** — `verified (reproduced)`. Additional finding: 12/10 also has 6 phasors exactly on belt edges; it
  passes only because all six raw values happen to round to ≥ the integer (1.0000000000000011, 2.0000000000000000,
  3.0000000000000000, 4.0000000000000036 …). The D08 oracle configuration therefore relies on rounding luck in Xcoil
  (DEF-14).

### b.3 D08 turn limit (eq. 3.24) and loop rule

Command: `python3 docs/phase1/verification/checks/v3_geometry_resistance.py` (own implementation from the D08 page text).

| Geometry | (3.24) bound | printed (3.25)+(3.26) | constructive loop rule | Agent 2 |
|---|---|---|---|---|
| D08 (r_o 44, r_i 12.5, w_d 2.86, θ = 30°) | N_c < 6.0070 | 2.5262 → 2, 1.0589 → 1 = **3** | **1 trapezoidal + 2 triangular = 3** | same |
| D08 with printed θ = π/p = 36° | 6.0070 | 2 + 1 = 3 | 2 + 2 = 4 | (not stated) |
| default 12/16 (centre-lines 18.25/37.75, w_d 0.7) | 14.4286 | 10 + 1 = 11 | 9 + 2 = 11 | same |
| 18/16 same annulus | 14.4286 | 6 + 1 = 7 | 5 + 3 = 8 | same |

Closed-form lengths: D08 3 loops 177.233 mm per coil-layer; default 12/16 N = 8 → 379.578 mm; 18/16 N = 4 → 195.199 mm
— identical to `answers_to_agents.md` §2.2 — `verified (reproduced)`. Agent 2's "printed eq. 3.25–3.26 mis-split the
loops" is confirmed.

### b.4 1-D magnetic-circuit limit of the field model

Command: `node docs/phase1/verification/checks/v4_field_inductance.js`.
- Own implementation of the EQ-05 closed form (cosh/sinh with µ_r coth(u l_m)) vs engine `fieldHarmonic` at 144 points
  (3 rotors incl. open rotor, n ∈ {1, 3, 5, 13}, r ∈ {18, 28, 38} mm, 4 z values): max relative difference 9.0e-16 →
  Agent 2's statement "algebraically identical to the engine's exponential form" — `verified (reproduced)`.
- Limit u → 0 (my algebra): cosh → 1, sinh(uG) → uG, coth(u l_m) → 1/(u l_m) ⇒ B_z,1 → K₁ l_m/(l_m + µ_r G) with
  K₁ = (4/π) B_r sin(πα_p/2), i.e. the 1-D circuit. Engine at r = 10⁷ mm: 0.946752 T (C1a inputs), 0.754351 T and
  0.820095 T (two further input sets) vs 1-D closed form, max relative difference 1.3e-11 at z = 0, G/2, G —
  `verified (reproduced)`.
- D08 rotor sensitivity (used in my strategy): B₁ at r = 40 mm is 1.1952 T with 1.4 mm per side and 0.9336 T with 2.8 mm
  (ratio 0.781) — matches Agent 2's C1b.

### b.5 Resistance hand calculation

- 1000 mm × 0.5 mm × 34.8 µm at 20 °C: 0.99088 Ω with IACS ρ = 1/58 Ω·mm²/m; 0.99080 Ω with the engine's 1.724e-8;
  1.14665 Ω at 60 °C — `verified (reproduced)`. The registry gives 0.990862 Ω for ρ = 1.7241e-8 (consistent); test plan
  UT-PHY-10 still expects 0.99080 Ω at rel. 1e-5 → would fail with the adopted constant (DEF-03).
- D08 phase (8 coil-layers, w 2.06 mm, 34.8 µm): 2π/Q, 50 °C → **0.3812 Ω** (D08 Table 4.6: 0.39 Ω, −2.3 %); π/p at 20 °C
  0.3931 Ω, at 50 °C 0.4394 Ω; with the printed double count 0.6003 Ω (20 °C) — reproduces Agent 2's C7.
- D09 concentric phase from the published length (Table 1 p.3: 3244 mm; Table 2: w 0.8 mm, 70 µm): R20 = **0.9988 Ω**;
  D09's calculated 1.04 Ω corresponds to ≈30.5 °C and the measured 1.07 Ω to ≈38 °C if only temperature differed
  (`inferred`; D09 does not state the temperature in the pages I read). Indicative turn-count inversion (Agent 2 task
  T-D, `checks/v8_d09_turn_count.py`): with the concentric-loop model, N = 8 (R_i0 ≈ 25.6, R_o0 ≈ 47.8 mm) and N = 7
  (R_i0 ≈ 20.2, R_o0 ≈ 43.8 mm) both fit 405.5 mm per coil-layer and the 171 mm² mid-loop area within ≈5 % → **N = 7 or 8,
  not decidable** from the published numbers (`inferred`, indicative; leads/vias ignored).

### b.6 Inductance: D10 eq. 14 vs D15 eq. 14

Derivation steps I checked (3-phase, balanced, sinusoidal; N series turns per phase; I RMS):
1. Fundamental MMF per pole of the rotating field: F̂ = (m/2)(4/π)(N k_w/(2p)) Î = (m√2/π)(N k_w/p) I.
2. Flux crosses the iron-to-iron gap δ′ (= 2l_m + 2g + t_s with µ_r ≈ 1) once per pole: B̂ = µ₀F̂/δ′.
3. Flux per pole: Φ = (2/π)B̂ · π(R_o² − R_i²)/(2p) = B̂(R_o² − R_i²)/p = B̂(D_o² − D_i²)/(4p).
4. Peak flux linkage ψ̂ = N k_w Φ; L = ψ̂/Î.
⇒ **L = (3µ₀/(4πδ′))(N k_w)²(D_o² − D_i²)/p²** for m = 3 — identical to D10 eq. 14 as printed (= (3µ₀/πδ′)(Nk_w/2p)²ΔD²).
- Both printed formulas are dimensionally consistent (H) — dimensions cannot decide; the ratio D15/D10 is exactly π/2
  (computed: 1.570796).
- D15: (14) follows from its own (12)–(13), but (12) uses √2m/2 instead of √2m/π → **D15 eq. 14 is π/2 too large**.
- D10: (12) carries the same error, and (11) omits 1/p; its (14) does **not** follow from its own (12)–(13) but agrees with
  the correct derivation → D10's (14) is right, its intermediate steps are not.
- Numbers (C9 case: N = 64, D 76/36 mm, δ′ 6.62 mm, p = 8): own 9.744 µH = D10 form 9.744 µH; D15 form 15.307 µH
  (k_w = 0.866); 4.678 / 7.348 µH with k_w = 0.600 — reproduces Agent 2's C9.
- **Decision: EQ-14(a) = D10 eq. 14 is the physically consistent magnetising inductance; Agent 2's and Agent 5's G1
  revision confirmed** — `verified (reproduced)` as a derivation; the formula remains **magnetising term only**
  (no leakage, end-turn or FSCW sub-harmonic terms), gate `cannot verify yet` stays correct.
- Caveat for the oracle: EQ-14(a) is a synchronous (rotating-field) inductance including the mutual coupling of the other
  phases; an LCR "phase inductance" is normally a single-phase self-inductance. D09 does not define its measurement →
  the ±20 % target compares unlike quantities until defined (DEF-08). Indicative: a D09-like geometry (N_series 48–64,
  D 92/50 mm, δ′ 7 mm) gives 6.9–12.3 µH vs 14.8 µH measured — order of magnitude only, not a validation.

Verdict b: **pass with defects** (DEF-03, DEF-08, DEF-09, DEF-10, DEF-14 — all minor). The gate verdicts (`reuse`,
`replace`, `cannot verify yet`) are supported by what I could reproduce; no equation was found wrong.

---

## c. Topology analysis and concept drawing

- **Repository = wave winding**: README l.1–12 ("Wave windings") and my own arc parse (EV-71: nested outer caps centred at
  r = 26 mm on 12 axes, inner arcs concentric with the board) support it — `verified (reproduced)`.
- **16 coils not balanced for 3-phase on shared layers**: Q = 16 cannot split into three equal phase groups for any pole
  count; my star of slots for 16/16 gives counts 16/0/0 — `verified (reproduced)`. The phase-per-layer-pair alternative
  (16 coils per phase, pairs rotated 2π/(3p) = 15°) is correctly reasoned (`inferred`).
- **Recommended 12/16**: balanced, t = 4, k_w1 0.866, k_w3 = 0, all coils positive, satisfies D12 eq. 1 (N_c/N_pm = 3/4),
  same Q/2p as the D09 concentric board (12 coils counted myself) — the supporting facts are reproduced; the
  recommendation itself is correctly labelled `assumption`. The stated drawback (k_w5 = k_w7 = 0.866) is real. The
  engine-based ranking (§2.4) uses the unvalidated Xcoil engine and is labelled indicative — acceptable.
- Minor inconsistency: K4 calls the D09 coil count "inferred from figure" while §2.4 and EV-62 call it `verified`
  (topology_analysis.md l.24 vs l.128) → folded into DEF-11.
- **SVG phase order and polarity** (`spiral_coil_concept.svg`, centre (282, 300)): label angles A1+ 90.0°, C1+ 120.6°,
  B1+ 151.1°, A2+ 181.3°, … B4+ 59.4° → counter-clockwise A C B ×4 starting at the top, matching my 12/16 pattern
  ACBACBACBACB; all arrows clockwise (SVG arcs with sweep-flag 1); 16 alternating pole wedges; panel D reproduces
  "AabBCcaABbcC"; phase sequence argument (coil k lags by pθ_k ⇒ A C B order CCW gives A→B→C for +θ rotation) re-derived
  — `verified (reproduced)`.
- Drawing language and status: all labels English, no colour other than greys, title "CONCEPT (not computed geometry)",
  footer "concept only (design assumption) … no dimension, turn count, field or electrical value is implied" — `verified`.

Verdict c: **pass**.

---

## d. Feature inventory and migration mapping

- **86 DEFAULTS parameters**: `Object.keys(E.DEFAULTS).length` = 86; parsed the inventory's group table: 86/86 keys
  present, none extra; `ui.js` GROUPS contains all 86 — `verified (reproduced)`.
- **15 sampled F-ids** (file:line opened): F-01 (`normalizeParams` l.107), F-03 (15 presets, ui.js l.140–156), F-04
  (`xcoil.params.v3`, ui.js l.7), F-08 (140 ms debounce, ui.js l.251), F-12 (`starOfSlots` l.1899–1918, `deriveSector`
  l.2237, `sectorCoilX` l.2285, `chainCoils` l.2330, `buildSector` l.2379, `computeSector` l.2426), F-20 (`SCREWS` l.1039),
  F-21 (`DIELECTRICS` l.1150, `stackupFor` l.1156), F-27 (`fieldHarmonic` l.856–867, `fieldSetup` l.868–874), F-29
  (l.80, 92, 102), F-31 (`applyConnection` l.1398–1438), F-34 (`windingInductance` l.2617–2668), F-41 (`COMPARE_METRICS`
  l.2734, `compareResults` l.2748), F-53 (`exportKicad` l.2877, version 20221018 at l.2881), F-55 (`makeZip` l.2946–2966),
  F-60 (20 formula cards, ui-content.js l.7–26), F-63 (title "Xcoil v3.0" body.html l.42, `--ph-a/b/c` style.css l.6) —
  **all correct**. Trivia: F-36 cites l.1377 (constant line), function starts l.1378.
- **"Port as-is" vs Agent 2 `replace`**: port-as-is rows are F-06, F-18, F-20, F-25, F-29 (formulas), F-31, F-32,
  F-33 (J, δ), F-45, F-47, F-49–F-52, F-55, F-62. None corresponds to an Agent 2 `replace` item (`starOfSlots`,
  `balancedSectorList`, `kdAnalytic`, sector turn limit are all mapped to "redesign/replaced by N-01/N-02") — `verified`.
  F-29 still says "ρ₂₀, α need cited source" (stale since EV-53) → DEF-05.
- Mapping reasoning (drop/defer serpentine and wave behind a generator interface; spiral generator new) is consistent with
  the brief and with Agent 2's gate.

Verdict d: **pass**.

---

## e. Requirements, acceptance criteria and test plan

Machine checks (script in this report's shell log; reproducible by parsing the tables):
- 97 requirements (33 F, 26 N, 15 K, 14 T, 9 L); **IDs unique**; **every row has a non-empty acceptance criterion**;
  112 test IDs referenced by requirements, **all defined** in `test_plan_draft.md`; the traceability matrix (§14)
  **covers all 97 REQ-IDs** with module and test IDs — `verified (reproduced)`.

**Brief-wish checklist** (PROJECT_BRIEF §1–§3 and the task statement as quoted in requirements §1):

| Wish | REQ | Covered? |
|---|---|---|
| Python tool branded embodic | L-03, N-08 | yes |
| 3-phase spiral-coil coreless AF PCB stator | F-01, F-02, F-07 | yes |
| Multi-layer configuration | F-03, F-04, F-05, F-12 | yes |
| Xcoil v3 as reference for features/flow/screens/logic | §10 mapping, F-19, F-25, F-26 | yes (F-61 guide tab and 3-D view intentionally open: UD-08/UD-20) |
| Every calculation engineering-checked before reuse | T-05, F-11 (gate), test plan §3 rules | yes |
| embodic replaces Xcoil branding | L-03 | yes |
| White/grey/black primary palette | L-04, N-14, N-23 | yes |
| Spiral replaces sector coil | F-01, F-06 | yes |
| KiCad plugin if feasible, KiCad 9.x | K-01…K-15 | yes |
| Python 3.11+ on Windows, separate from KiCad's Python | N-05 (+ architecture R10) | yes |
| App type proposed, approved before Phase 2 | ADR-0005 / UD-01 (process) | yes (process item) |
| Calculation and geometry engines in Python | N-08, K-05 | yes |
| Render look (fanned sides, stadium ends, rotated groups) | F-06 (stadium should), F-03 (rotation should), UD-13 | yes |
| English UI and documents | L-01, L-02, L-06 | yes |
| Units, assumptions, limits, status shown | T-01…T-08, T-13 | yes |
| Readable, maintainable code | N-08…N-10 | yes |
| Requirements ↔ acceptance ↔ tests linked | T-09 | yes |
| Reproducible install/run/package | N-05…N-07 | yes |
| Geometry, phases, layers, results displayed clearly | F-13 | yes |
| No "measured" for computed values; no balance/torque claims from geometry | T-10, T-11 | yes |
| Licences recorded; no GPL code copied | N-19 | yes |
| DRC of generated copper | F-10 | yes |

**Independent oracle cases** in the plan: OR-01…OR-10 (O1 D08 Ke, O2 D09 R/EMF/field, O3 D10 R, inductance
characterisation) — present. **"DRC never under-reports"**: PR-01 states both directions against an independent
brute-force checker — present, but contradicted by other criteria (DEF-01).

**Untestable or contradictory requirements found:**
1. **REQ-F-10 / PR-01 / UT-DRC-03 vs inherited Xcoil DRC slack** (DEF-01, major): Xcoil passes clearances down to
   `clearance − 0.004 mm` (`engine.js` l.757, l.774, l.1988); REQ-F-10(a) accepts "within 0.005 mm of the set clearance";
   Agent 3's port tolerance anchors pass/fail at `clearance − 0.004` (`calculation_flow_and_port_notes.md` l.85); PR-01
   requires no pair below `rule − 1e-6 mm` and UT-DRC-03 a 1 µm intrusion detected. These cannot all hold.
2. REQ-F-02(d)/UT-WND-04/BV-04 reject 16/16 for 3 phases, while REQ-F-03 (M4, should) and topology alternative B use
   16/16 with one phase per pair (DEF-04).
3. REQ-F-21 / REQ-T-06 ("every default value marked `assumption`") vs the status rule "sourced constant = its EV status"
   for defaults that are sourced (ρ₂₀, α, copper density) (part of DEF-02).
4. REQ-F-11 acceptance "within the EQ's stated tolerance": for EQ-05 and EQ-12 the tolerance is against 3-D FEA / 2-D FEM
   that no plan provides in Phase 2 → untestable as written (DEF-10).
5. REQ-F-06(a) "3 turns, ±1 turn" accepts 2–4 and cannot discriminate; REQ-F-06(b)/UT-GEO-07 ±6 % rests on two
   trapezoid-only cases (DEF-09).
6. UT-PHY-10 expects the Xcoil-constant value (DEF-03); OR-02 lists a stale prerequisite and an undocumented measurement
   temperature (DEF-11).
7. Subjective but measurable (accepted): REQ-F-13 walkthrough, REQ-N-07 "< 10 min", REQ-N-14 "100 % reviewer accuracy".
8. Coverage gaps in the plan (DEF-17): no rotation-symmetry property (rotating the design by one coil pitch must
   permute/shift phasors by p·2π/Q), no test of the turn-averaged pitch factor (D15 eq. 6, EV-59).

Verdict e: **pass with defects** (DEF-01 major; DEF-03, 04, 09, 10, 11, 17 minor).

---

## f. Architecture and ADRs

### f.1 Consistency checks

| Check | Result | Status |
|---|---|---|
| Engine purity / adapters (ADR-0001) vs REQ-K-05, N-08, Agent 3 §6.1 | consistent (import-linter contracts) | verified (read) |
| One primitive model (ADR-0002) vs Agent 3 §6 and F-16 | consistent | verified (read) |
| KiCad route (ADR-0004) vs Agent 5 evidence | consistent; citation of requirements.txt/Preferences attributed to the official page (DEF-12) | verified (read) |
| App type (ADR-0005) vs Agent 1 (desktop + phone mockups) | resolved: phone only if C-B1 (REQ-N-15) | verified (read) |
| Python floor | 3.11 syntax everywhere (Agent 3 §4.1, ADR-0008, §18.1); KiCad 9's bundled Python unknown (T1) → consequences stated for 3.9/3.10/3.11/≥3.12 | verified (read); outcome `not tested` |
| Dependency licences — my PyPI spot checks | PySide6-Essentials 6.11.2: "LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only", Python ≥3.10,<3.15; kiutils 1.4.8: GPLv3 classifier, last upload 2024-02-02; also numpy 2.5.3 requires ≥3.12 and 2.4.6 is the newest release with a cp311 win_amd64 wheel; hypothesis 6.168.3 MPL-2.0 — all as stated in ADR-0008 | verified (read) |
| Stale "constants source needed" | ADR-0003 l.16, architecture_draft l.319, l.1220, l.1420, migration_mapping l.73, mockup 04 l.363–364 (DEF-05) | verified (read) |

### f.2 Agent 1's 16 mismatches — re-checked myself

| # | Agent 1 item | My check | Result |
|---|---|---|---|
| 1 | Status rule | REQ-T-03, §13, ADR-0003 Amendment 1 all use "every used default = assumption"; spec §10.4 marked superseded (design_spec l.410) | confirmed; logic problem → DEF-02 |
| 2 | Default marker | REQ-T-06/F-21 present; spec fixed; mockups have no "default" chip (I searched) | confirmed open in mockups (acknowledged by Agent 1) |
| 3 | Focus on Cancel | REQ-F-33 "initial focus on the safe action (Cancel)" | confirmed fixed |
| 4 | Terminal location | `terminal_location: Literal["outer"]` (architecture l.386); mockup 03 uses `param-terminal-location` | confirmed fixed |
| 5 | Terminal names | not a Phases field any more | confirmed (no model field) |
| 6 | "Balanced phasors" | REQ-T-11; mockups use the wording | confirmed |
| 7 | DRC codes | §12 `DRC_*` style | accepted (not re-checked in all mockups) |
| 8 | Element ids | mockups use `param-poles`, `param-side-style`, `param-end-style`, `param-corner-radius`, `param-clearance`, `param-x-inward-sense`, `param-first-coil-angle`, `param-terminal-location` (old ids absent) | confirmed fixed in mockups; architecture §19 still says "Agent 1 to confirm" (l.1607) → DEF-13 |
| 9 | torque_speed result | not in `AnalysisResult` (§7.7) | confirmed open → DEF-13 |
| 10 | Feasibility rail values | no `GeometryDerived`/`balanced_coil_counts` in §7/§8 | confirmed open → DEF-13 |
| 11 | Breakpoints | REQ-N-15 960 × 540 | confirmed |
| 12 | Plugin window fallback | R2-only setup has no in-KiCad message path | confirmed open (no requirement for the fallback) |
| 13 | AX-04 label area | AX-04 (test_plan l.344) still "enumerate widgets … check geometry" | confirmed open → DEF-13 |
| 14 | Hatch never crosses copper | REQ-N-23 (l.126) unchanged | confirmed open → DEF-13 |
| 15 | Contrast pairs | my recomputation: 99 pairs with a minimum + 12 exempt (disabled/decorative); 0 below requirement; all stated ratios within 0.015 (§g) | confirmed |
| 16 | Pure-greyscale mockup 07 | present | confirmed |

Additional mismatches I found: DEF-01 (DRC slack across REQ/test plan/port tolerances), DEF-03, DEF-04, DEF-05, DEF-12.

### f.3 Status-ordering rule and "default input ⇒ assumption" rule

Rule under review (ADR-0003 Amendment 1, architecture §13, equation spec l.377–385, REQ-T-03/T-06/F-21): result status =
weakest of {EQ evidence status, implementation status, status of every used input (user/imported = neutral, default or
unsourced = `assumption`, sourced constant = its EV status, the equation's own stated assumptions = `assumption`), validity
cap}, order `unresolved` < `not tested` < `assumption` < `inferred` < `verified`.

The order itself is defensible (an untested computation is less trustworthy than an explicit assumption; `unresolved`
lowest). The combination has five logical problems (DEF-02, major):
1. **Practically everything is `assumption` forever.** EQ-10 carries the built-in assumption "PCB copper = IACS copper";
   EQ-05 uses µ_r (no datasheet value, G23) and back-iron assumptions. The data model (`InputSource`: user / default /
   imported) has **no `measured` provenance**, so these built-in assumptions can never be retired; every R, Ke, torque and
   loss result stays `assumption` even for a fully user-specified design. `inferred`/`verified` become unreachable for
   physics results, and the badge degenerates to two values (`assumption` / `unresolved`) — Agent 1 already observed this
   for the default design.
2. **Status depends on keystrokes, not evidence.** Re-typing the default µ_r = 1.05 turns it "neutral (verified strength)"
   (architecture §7.7 `InputRef` comment) and can upgrade a result from `assumption` to `inferred` with no new evidence.
3. **Category conflation.** "Sourced constant = its EV status" feeds the register's `verified`, which by Agent 5's own
   definition means "read in the source", not "applies to embodic" (the "Applies" judgement is always `inferred`). A
   sourced constant should contribute at most min(EV status, applicability) — e.g. IACS ρ for PCB copper = `inferred`.
4. **Contradiction** with REQ-F-21/T-06: a sourced default (ρ₂₀) is simultaneously `assumption` (default) and `verified`
   (sourced constant).
5. **Mixed dimensions in one scalar** (evidence strength, provenance, implementation state, validity): the weakest-link
   hides which dimension failed unless `status_reasons` is shown (Agent 1's request).

**Proposed fix** (for Fable's decision; Agents 2 and 6 to specify):
- (a) Badge = **method status** = weakest of {EQ evidence status, implementation status, validity cap}. This tells the user
  how trustworthy the *computation* is.
- (b) Separate **input-reliance tag** "n assumptions" listing used inputs by provenance class, dominant ones first
  (Agent 2's `dominant_assumptions`): `default-unsourced` (assumption), `default-sourced` (min(EV, applies), typically
  `inferred`), `user-unsourced` (user's responsibility, listed), `user-sourced`/`measured` (with a reference: datasheet,
  coupon, LCR record), `imported` (KiCad).
- (c) **Overall status** = weakest of (a) and the input classes — used in exports/report summaries and wherever one label is
  required; always shown together with (b).
- (d) Add a `measured` provenance (with record ID) so that equation-level assumptions (e.g. PCB copper = IACS, finished
  copper thickness) can be replaced by data; keep "never call computed results measured" (REQ-T-10).
- (e) Keep the monotonicity property PR-12 and add: re-entering an identical value never changes any status.
With this, the default design would show e.g. R: method `verified`/`inferred`, "4 assumptions"; the user still sees every
assumption, and the badge keeps discriminating power.

Verdict f: **pass with defects** (DEF-02 major; DEF-05, DEF-12, DEF-13 minor).

---

## g. UX/UI drafts (static HTML mockups)

Command: `python3 docs/phase1/verification/checks/v7_mockups_playwright.py` (Chromium via Playwright) and
`python3 docs/phase1/verification/checks/v6_contrast_tokens.py`.

| Check | Result | Status |
|---|---|---|
| Horizontal overflow (scrollWidth − clientWidth), desktop mockups at 1920/1440/1280/1024/960/768 px | 0 px at ≥ 1280 for all; 02/03/04/07 also 0 at 1024 and 960; **01: 252 px at 1024, 316 px at 960** (caused by an absolutely positioned annotation `span.callout`, l.407); all desktop mockups overflow at 768 px (164–184 px) although design spec §5 (l.212) promises no horizontal scroll 768–1279 px; no width media queries exist → tablet pattern not mocked (DEF-07) | verified (reproduced) |
| Phone mockup 06 at 320/360/390/420 px | 0 px overflow at all four | verified (reproduced) |
| Compat mode with the comment before `<!doctype>` | `CSS1Compat` (standards mode) for all 7; `lang="en"` | verified (reproduced) |
| Thai characters `U+0E00–U+0E7F` in source and rendered text/ARIA/title/alt | 0 in all 7 | verified (reproduced) |
| "Xcoil" (case-insensitive) in source and rendered text | 0 in all 7 | verified (reproduced) |
| Personal names from the deck (tokens read from the PDF at run time, not stored) | 0 hits in mockups and in all Phase 1 documents | verified (reproduced) |
| Brand assets | 4 PNGs in `mockups/brand/` byte-identical (md5) to the brand folder originals | verified (reproduced) |
| Contrast from `tokens.json`, own WCAG formula | 99 pairs with a requirement: **0 below**; 12 exempt pairs recomputed only; all stated ratios within 0.015 of mine; all pair hex values equal the theme tokens; tightest: light text-3 on surface-selected 4.52:1 (min 4.5), dark phase-a on surface 3.12:1 (min 3.0); mockup CSS colour properties equal the light tokens (07 overrides pass/fail to ink, as designed) | verified (reproduced) |
| Keyboard Tab walk, mockup 01 at 1440 px | 45 stops, no trap, returns to the skip link: skip link → Undo, Redo, Open, Save, More, Export → steps 1–6 → panel inputs (coil count, poles, side-style radio, end-style radio, turns, width, clearance, r-inner, r-outer, coil gap) → "Next: Phases" → colour/greyscale radio → labels, fit, zoom in/out → canvas (focusable) → layer chips L1–L6 → DRC Locate, Open checks → EQ links (EQ-10, 06, 09, 14, 17) → All results. Order follows the visual order; every stop has a 2 px outline (inputs via `.input-unit:focus-within`). Deviation from spec §8.3: no focusable "rename" control in the top bar and no status-bar links (DEF-16) | verified (reproduced) |
| Mockup 04: unit + EQ-ID + status badge on every numeric result | 5/5 result cards: value + unit + exactly one badge + ≥ 1 EQ link (Ke 12.4 mV·s/rad inferred EQ-06/09; L_s 21 µH unresolved EQ-14; R_ph 1.9 Ω inferred EQ-10/11; J 9.8 A/mm² inferred EQ-22; EMF 2.0 V pk inferred EQ-06/18). Inputs in "How was this computed" carry a badge or the `input` tag. **But** example statuses contradict the agreed rule: R_ph shows `inferred` while its inputs are `assumption` (l.352 vs l.361–364); ρ₂₀ row "1.724 × 10⁻⁸ … source needed" is stale (DEF-05, DEF-06) | verified (reproduced) |
| "Illustrative / example values" stamp | present on all 7 | verified (reproduced) |

Cannot be verified until implementation (`not tested`): recompute latency and "Updating…" behaviour (REQ-N-02), screen
reader announcements (REQ-N-16, Narrator), real widget focus rings in Qt, forced-colours/high-contrast rendering of the
geometry, target sizes of live widgets, behaviour of the 960 × 540 two-pane layout, chart keyboard read-outs, axe-core
results on a live DOM (only if C-B1).

Verdict g: **pass with defects** (DEF-06, DEF-07, DEF-16 — minor).

---

## h. Language and branding (brief §3 rule 8)

- Thai scan over every text file in `docs/` (all agents' files, SVG, JSON, HTML): 0 Thai characters (my own script
  initially contained a literal Thai range; replaced by escapes) — `verified (reproduced)`.
- "Xcoil" appears only in internal documents describing the reference tool, never in mockups or the concept SVG —
  `verified (reproduced)`. Brand written "embodic" (lower case) in all UI-facing artefacts; no "Embodic/EMBODIC" variants
  in mockups or SVG — `verified (reproduced)`.
- Personal data: no deck name anywhere. Observation: the Windows user name from the brief's destination path appears in
  `software/dependency_and_tooling_draft.md` l.106–115 (internal install walkthrough, copied from the brief) — acceptable
  in an internal document; must not reach code, UI, logs or exports (REQ-N-20 already covers logs).

Verdict h: **pass**.

## i. Process rules

- Line 1 of every agent document names the agent, role and `claude-opus-5-5` (Markdown first line; HTML/SVG comment;
  JS/Py comment; JSON `prepared_by` key) — checked for all 54 agent-authored text files (55 text files in
  `docs/phase1/` before my work, incl. Fable's README) — `verified (reproduced)`.
  `evidence/reference_images/README.md` has no "Prepared by" line; it was written by Fable (coordinator), to whom rule 11
  does not apply (observation).
- Folder ownership: every file's author line matches the folder owner (architecture = 6, design = 1, engineering = 2,
  evidence = 5, software = 3); `verification/` was empty when I started — `verified (reproduced)`. Git history was not
  used (not available/allowed).
- Reference material unchanged: `git -C …/magnetless_motor status --porcelain` → only `?? gerbers/` (the Gerber
  extraction described in the brief; tracked files clean; HEAD c6ec327e…); `git -C …/kimotor status --porcelain` → empty
  (HEAD dc6cac3a…); `/home/claude/serpentine` is not a git repository → `find … -newer docs/PROJECT_BRIEF.md` finds no
  file in serpentine or embodic-ref newer than the brief; `node /home/claude/serpentine/run-tests.js` → **131/131
  passed** — `verified (reproduced)`.

Verdict i: **pass**.

---

## Commands used (all run 2026-10-04 in this container)

```
node /home/claude/serpentine/run-tests.js
git -C /home/claude/embodic-ref/magnetless_motor status --porcelain ; git -C /home/claude/embodic-ref/kimotor status --porcelain
python3 docs/phase1/verification/checks/v1_star_of_slots.py        # own star of slots, k_w, M3
node    docs/phase1/verification/checks/v2_engine_star_of_slots.js # engine starOfSlots, tie mechanism
python3 docs/phase1/verification/checks/v3_geometry_resistance.py  # D08 eq. 3.24-3.26, loops, lengths, R hand calcs
node    docs/phase1/verification/checks/v4_field_inductance.js     # EQ-05 identity, 1-D limit, D10 vs D15 inductance
python3 docs/phase1/verification/checks/v5_gerber_endturns.py      # EV-71 arcs
python3 docs/phase1/verification/checks/v6_contrast_tokens.py      # WCAG ratios from tokens.json
python3 docs/phase1/verification/checks/v7_mockups_playwright.py   # overflow, language, names, Tab walk, mockup 04
python3 docs/phase1/verification/checks/v8_d09_turn_count.py       # indicative D09 turn-count inversion (T-D)
pdftotext -layout -f N -l N <pdf> - ; pdftoppm/pdfimages + Read (equation renders) ; WebFetch (KiCad, PyPI, NBS) ;
curl https://pypi.org/pypi/<pkg>/json ; pip download --no-deps kicad-python==0.8.0
```
