Prepared by: Agent 4 — Independent Verificator — model: claude-opus-5-5

# Independent test strategy for embodic (Phase 1 draft, 2026-10-04)

Written from `architecture/requirements_draft.md` (REQ-IDs), the evidence register and the equation specification —
**not** from Agent 6's test plan; §11 compares the two afterwards. Every test below is `not tested` (no embodic code
exists). "Here" = can run in the agent container (Linux, Python 3.11, Node 22, Chromium/Playwright); "User" = needs the
user's Windows PC with KiCad 9.x (or tools only available there, e.g. FEMM); "P3" = Phase 3.

## 1. Principles

1. **N-version oracles**: every reference implementation I own is written from first principles or from the paper page,
   never by reading the embodic implementation; I share inputs/outputs, not code. Prototypes exist already for several
   (scripts v1–v8 in `checks/`).
2. **Pre-registration of oracle runs**: for each published oracle, the input set (with page reference for every value and
   the reading chosen for ambiguous values, e.g. D08 air gap) and the tolerance are frozen in a file **before** the first
   embodic run; a failed run may not be "fixed" by changing an input without a new registration and a recorded reason.
3. **Verification ≠ validation**: agreement with a closed form or with Xcoil proves the implementation; only agreement
   with a measured oracle (within a reasoned tolerance) supports physical validity. Computed results are never called
   measured (brief rule 5).
4. **Tolerances carry a reason**: numerical (floating point/discretisation), model (the source's own model-vs-measurement
   spread) or input uncertainty (unknown temperature, copper thickness, gap). A tolerance without a reason is `assumption`.
5. **DRC is a safety property**: false negatives are never acceptable; false positives are acceptable only within a
   documented conservatism bound.

## 2. Test levels

| Level | Purpose | IDs | Where |
|---|---|---|---|
| L0 | Reference integrity before any golden dump or comparison | IT-01 | Here |
| L1 | Independent reference implementations (N-version) | IT-02 … IT-12 | Here |
| L2 | Published oracles (validation), pre-registered | IT-13 … IT-18 | Here (after implementation) |
| L3 | Property / fuzz | IT-19 … IT-25 | Here |
| L4 | Boundary and invalid input | IT-26 | Here |
| L5 | Physics checks needing FEM tools | IT-27, IT-28 | User / P3 |
| L6 | UI and accessibility | IT-29 … IT-34 | Here (automated) + User (Narrator, high contrast) |
| L7 | Language / brand automation | IT-35 | Here |
| L8 | KiCad export validation | IT-36 … IT-39 | Here + User |
| L9 | Regression after optimisation | IT-40, IT-41 | Here + User (performance) |
| L10 | Traceability audit | IT-42 | Here |

## 3. L0–L1: reference integrity and independent reference calculations I own

| ID | Test | Reference / oracle (mine) | Criterion | REQ | Where |
|---|---|---|---|---|---|
| IT-01 | Reference material unchanged before each golden dump | `git status --porcelain` of both embodic-ref repos (only `?? gerbers/` allowed), checksum list of `/home/claude/serpentine/src/*`, `run-tests.js` 131/131 | any change → stop | N-19, ADR-0006 | Here |
| IT-02 | Star of slots, exact | `v1_star_of_slots.py` (Fraction angles, tie rules T1 and T2) for all Q ≤ 48 (multiples of 3 and others), 2p ≤ 48 | same balanced verdict, counts, signs, pattern (up to the documented tie rule), k_d/k_p/k_w per harmonic to 1e-12; must include tie cases 12/10, 12/14, 24/14, 24/22, 24/26 and 16/16 (rejected unless M4) | F-02 | Here |
| IT-03 | Turn-averaged pitch factor | own implementation of D15 eq. 6 (EV-59) and of σ_t(r) = θ_cp − 2 asin(d_t/r) at mean radius, D08 and default 12/16 geometries | 1e-12 vs embodic `winding_factor_1` | F-02, F-11 | Here |
| IT-04 | Turn limits and loop geometry | `v3_geometry_resistance.py`: (3.24) bound, printed (3.25)/(3.26), constructive loop rule; loop lengths (D08: 1 + 2 loops, 177.233 mm; 12/16 N = 8: 379.578 mm; 18/16 N = 4: 195.199 mm) | counts exact in concentric test mode; lengths 1e-6 mm; generated spiral vs closed form reported (tolerance to be re-based, DEF-09) | F-06 | Here |
| IT-05 | Field at a point | own EQ-05 closed form (cosh/sinh, µ_r coth) for double / single+yoke / open rotor; α_p(r) of blocks (D08 eq. 3.3) | 1e-12 relative; 1-D limit (r → ∞) 1e-9 vs B_r l_m/(l_m + µ_r G)·(4/π) sin(πα_p/2) | F-07 | Here |
| IT-06 | EMF of a closed loop by **area integration** (Stokes), independent of the path integral | ψ(θ_r) = ∬_loop B_z dA with own field (adaptive 2-D quadrature over the polygon of each generated turn), Ke = dψ/dθ_m | 1e-4 relative vs embodic Ke for 1-turn and 3-turn coils on 2 and 6 layers | F-11, F-12 | Here |
| IT-07 | DC resistance by own primitive summation | R = ρ_T Σ L_i/(w_i t_i) + Σ R_via (EQ-11) using the exported primitive list; hand cases 1000 mm × 0.5 mm × 34.8 µm: 0.990862 Ω (ρ 1.7241e-8), 1.14665 Ω at 60 °C (IACS 1/58) | 1e-9 | F-11 | Here |
| IT-08 | Circuit identities | random sets of series groups of parallel members with random complex EMFs and resistances | conductance-weighted EMF, R_grp, P_c = Σ abs(E_i − E_grp)²/(2R_i), two-member P_c = abs(E₁ − E₂)²/(2(R₁+R₂)) to 1e-12 | F-03, F-12 | Here |
| IT-09 | Magnetising inductance (labelled estimate) | own derivation L = (3µ₀/(4πδ′))(N k_w)²(D_o² − D_i²)/p² (report §b.6); C9 case 9.744 µH (k_w 0.866) | 1e-12; status `unresolved`, label "estimate" | F-11, T-05 | Here |
| IT-10 | Star/delta identities and power balance | Ke,LL = √3 Ke,ph (star), Kt = (m/√2)Ke,ph, T ω = m E_rms I_rms | 1e-12 | F-08 | Here |
| IT-11 | Eddy loss of one straight strip | P/V = σω²(B̂_z² w² + B̂_t² t²)/24 (own derivation, report §b.1) for a uniform field | 1e-9 vs embodic for a single isolated trace; B_t term absent on circumferential segments if Q-6 is fixed | F-11 | Here |
| IT-12 | **Brute-force DRC checker** | own O(n²) checker with exact distances (line–line, line–arc, arc–arc solved analytically, incl. arc end points and interior closest points), via/pad discs, board edge/holes; exemptions only for primitives that share an end point in the connectivity graph or a via they terminate on | used by IT-19/IT-20 | F-10 | Here |

## 4. L2: published oracles — prerequisites, tolerance, reasoning

| ID | Oracle (source) | Quantity | Prerequisites before it can be used | Tolerance and reasoning | REQ | Where |
|---|---|---|---|---|---|---|
| IT-13 | **O1** D08 thesis, Table 9.1 p.98 (meas.) | Ke = 0.031 V·s/rad, **line-line peak of the waveform** per mech. rad/s | geometry r_i 12.5, r_o 44, w 2.06, s 0.8 mm, 3 loops, 12 coils/side, 2 sides in series (Tables 4.5–4.6 p.54/57); rotor: N45SH 18 × 10 × 5 mm, two blocks per pole (T-arrangement, p.35 Table 3.2, p.49) → needs a multi-block pole model beyond EQ-04; B_rem 1.38 T; gap reading frozen at 1.4 mm per side (`inferred` from Fig. 3.3 by Agent 2) with 2.8 mm run as recorded sensitivity; µ_r 1.05 `assumption`; back-plate unsaturated `assumption` (D08 p.112 reports saturation) | **±8 %**: D08's own analytical model deviated by max 8 % from the same measurement (p.98). The test discriminates: changing the gap reading from 1.4 to 2.8 mm lowers B₁ at r = 40 mm by 21.9 % (1.1952 → 0.9336 T, reproduced). Compare the synthesised L-L waveform peak, not the fundamental | F-11, T-12 | Here |
| IT-14 | **O2** D09 Tokgöz, Table 6 p.7 (meas.) | phase DC resistance 1.07 Ω | step 1 (now): R from the published phase length 3244 mm (Table 1), w 0.8 mm, 70 µm → R20 = 0.9988 Ω (computed by me); step 2: turn count N (7 or 8 — my inversion `v8_d09_turn_count.py` cannot decide), coil radii, coil gap → generated length vs 405.5 mm per coil-layer | **±8 %** (EQ-10 basis: D09 calc vs meas. +2.9 %, D10 sim vs meas. +7.5 %); input uncertainty: measurement temperature not stated (1.07 Ω ⇔ ≈38 °C if only temperature differs), finished copper thickness unknown. Step 1 checks ρ and cross-section only; step 2 is the generator test | F-11 | Here |
| IT-15 | O2 D09, Tables 4–5 p.6 (calc/FEA) | phase EMF 6.21 V (calc) / 6.20 V (FEA) RMS at 2000 rpm | as IT-14 step 2 + rotor Table 3 p.4 (α_p 0.8, B_r 1.33 T, 2 mm magnets, 7 mm between cores); until N is known compare **Ke per turn** (ratio) | ±5 % (D09's own calc vs FEA within 0.2 %; add field-model edge error, which D09 corrected with FEA-fitted B_r(r)) | F-11 | Here |
| IT-16 | O3 D10 Wang 2019 p.8 (meas.) | phase R 2.15 Ω | unequal-width concentric geometry (S5, deferred) | ±8 % (D10's own sim 2.00 Ω deviates 7.5 %) | F-11 | Later |
| IT-17 | O4 D15 Pan p.13–14, p.22 | L 16.7 µH (FEA), torque 46.4 mN·m at 1.5 A (meas.) | 2-phase stepper: characterisation only | none (record ratio) | F-11 | Here |
| IT-18 | Inductance characterisation | D09 14.8 µH (method unknown, DEF-08), D07 L_s 22.3 µH / M −8.55 µH (wave) | define measured quantity first | none — EQ-14 stays `unresolved`; record ratio and quantity definition | T-05 | Here |

An oracle result is reported as: pre-registration ID, embodic version, inputs hash, value, oracle value, deviation,
tolerance, verdict, and the list of open prerequisites. A passing oracle allows the linked EQ status to rise only as far as
the rule in DEF-02's fix permits; a failing oracle opens a defect, it is never silently re-tuned.

## 5. L3: property and fuzz tests (Hypothesis; seeds logged; shrunk cases kept as regressions)

| ID | Property | Generator of inputs | Oracle | REQ | Where |
|---|---|---|---|---|---|
| IT-19 | **DRC never under-reports**: every non-exempt pair whose exact distance < rule − 1e-6 mm (IT-12) is reported by embodic; embodic false positives allowed only within its documented conservatism bound | random valid designs + fault injection (move one turn, via or pad inward by 0.1–10 µm; shrink clearance setting) | IT-12 | F-10 | Here |
| IT-20 | Clearance ≥ setting by construction: for designs the generator reports DRC-clean, exact minimum distance ≥ clearance − 1e-6 mm, per check type | random Q, 2p, w, s, radii, layers, M1–M4 | IT-12 | F-10, F-01 | Here |
| IT-21 | **Continuity**: each phase circuit is one connected path from its line terminal to N (graph of primitives + vias), consecutive end points coincide ≤ 1e-6 mm; after mm → nm rounding they are identical; no dangling primitive | random designs | own graph walk | F-01, K-08, N-21 | Here |
| IT-22 | **Rotation symmetry**: rotating the whole design (copper and coil numbering) by one coil pitch 2π/Q at fixed rotor reference shifts every phase phasor by the same electrical angle p·2π/Q (sign per the documented convention), keeps abs(Ke) per phase, R per phase and all DRC minimum distances unchanged (1e-9), and the star of slots of the shifted coil set equals the relabelled assignment; for 12/16 the shift is 240° el. (pure phase relabelling A→C→B) | random balanced Q/2p incl. t = 1 cases (12/10, 12/14) | IT-02 + exact arithmetic | F-02, F-11 | Here |
| IT-23 | Mirror and polarity: reversing every coil's entry terminal negates every phasor; layer Y mirrored about the coil axis lies on X (1e-9 mm) | random coil specs | geometry | F-01 | Here |
| IT-24 | Scaling laws: R ∝ 1/t_cu; R(T) linear (α); Ke ∝ B_r; Ke independent of speed; eddy ∝ f² and (B_z term) ∝ w³ at fixed t; k_w independent of radii | perturbation pairs | exact ratios (1e-9) | F-11 | Here |
| IT-25 | Status rule: truth table over all status combinations, validity caps, `cannot verify yet` → `unresolved` + "estimate"; monotonicity (default → user never lowers; re-entering an identical value never changes any status) | enumerated + random | rule as fixed for DEF-02 | T-03, T-05, T-06 | Here |

## 6. L4: boundary and invalid inputs (derived from REQ-F-14/F-23, independent of BV-01…20)

IT-26 — parametrised set, each case asserting: documented issue code and severity, no exception, no NaN/∞ anywhere in the
result, the input object unchanged (REQ-F-23), last valid layout kept (REQ-F-27):
r_outer = r_inner + 2(w + s) ± 1e-9 mm; turns = max and max + 1; Q ∈ {3, 6, 9, 16, 2p, 2p ± 1}; odd 2p; w, s ∈ {0, −1,
NaN, ±∞, 1e-9, 1e6}; via pad = coil eye ± 1e-6 mm; 1 copper layer; odd layer count; 64 / 65 layers; parallel paths = t
and t + 1; temperatures −273.15 ± ε °C; speed 0 and negative; project JSON truncated, wrong types, unknown keys, newer
schema, non-ASCII strings; delta with k_w3 ≠ 0 (12/14 → warning); copper within one gap of the magnet edge (validity
cap). REQ: F-14, F-23, F-27, T-08. Here.

## 7. L5: physics checks needing FEM tools (not available here)

| ID | Test | Method | Tolerance (reason) | REQ | Where |
|---|---|---|---|---|---|
| IT-27 | Field model and per-layer B_z (G3) | FEMM 2-D at mean radius (free, Windows) or 3-D FEA of the D09 rotor (Table 3 p.4) and the default rotor; B_z(θ) at each copper layer z | ±5 % on B₁ at mid-radius (D09 reports < 1 % for a comparable model; µ_r/B_r uncertainty); report radial-edge drop separately | F-07, F-12 | User / P3 |
| IT-28 | Eddy coefficient | 2-D FEM of one 0.5 × 0.035 mm trace in a uniform sinusoidal field (B_z and B_t separately) | ±20 % (`assumption`, end effects) | F-11 | User / P3 |

## 8. L6: UI and accessibility (after implementation; baseline from the mockups in my report §g)

| ID | Test | Method | Criterion | REQ | Where |
|---|---|---|---|---|---|
| IT-29 | Automated accessibility audit | C-B1 (web): Playwright + axe-core (MPL-2.0) on every state (default, invalid input, DRC failure, results expanded, export dialog); C-A (Qt): dump of the QAccessible tree (name, role, value, description) for every widget | 0 serious/critical axe violations; every input exposes label + unit + error text; every result exposes value + unit + status | N-11…N-16, N-24 | Here (+ Narrator: User) |
| IT-30 | Keyboard walk | scripted Tab/Shift+Tab/F6/Alt+1…6/arrow keys; record (widget id, region, bounding box) per stop; compare with visual order (region order, then top-to-bottom, left-to-right); check focus-ring pixels (≥ 3:1 vs neighbours, 2 px) by screenshot diff | no trap; order = visual order; every stop has a visible ring; baseline: mockup 01 walk (45 stops) | N-12 | Here |
| IT-31 | Forced colours / greyscale / CVD | Chromium `forced-colors: active` emulation (C-B1) or Windows high contrast (C-A, manual); luminance-only conversion and deuteranopia/protanopia simulation of geometry screenshots | reviewer identifies phase and polarity of all 12 coils from labels/hatch alone (100 %); hatch never crosses copper | N-14, N-23 | Here + User |
| IT-32 | Contrast from the theme file | `v6_contrast_tokens.py` re-pointed at the implementation theme | 0 pairs below 4.5:1 (text) / 3:1 (non-text) | N-11, L-04 | Here |
| IT-33 | Numeric result audit | walk every displayed number (widget tree or DOM): unit present, exactly one status badge, EQ link or `input`/`derived`/`count` tag; status equals the result object's status | 100 % | T-01, T-02 | Here |
| IT-34 | Window sizes and scaling | 960 × 540, 1280 × 720, 1920 × 1080 at 100/150/200 % | no horizontal scroll of form panels; no clipped text | N-15 | Here + User |

## 9. L7–L8: language/brand automation and KiCad export validation

| ID | Test | Criterion | REQ | Where |
|---|---|---|---|---|
| IT-35 | Scan of string catalogue, report templates, logs and **generated files** (SVG, DXF, `.kicad_pcb`, JSON, PDF text via pypdf): Thai block `U+0E00–U+0E7F`, "xcoil" (case-insensitive), personal-name tokens read at run time from the deck (never stored), "measured" next to computed values, balance/torque/efficiency claim phrases | 0 hits (allow-list: "reference (paper, measured)") | L-01, L-03, L-05, T-10, T-11 | Here |
| IT-36 | Parse `.kicad_pcb` with **my own minimal s-expression parser** (independent of the writer and of kiutils) | counts, positions (nm), widths, layers and nets equal the layout; arc start/mid/end on one circle ≤ 1 nm; connected end points identical in nm | K-01, K-08, K-09 | Here |
| IT-37 | Second parser: kiutils (GPL-3.0, test-only) | parses without error; same counts | K-01 | Here |
| IT-38 | **T0 round trip** on the user's machine: open the default design's `.kicad_pcb` in KiCad 9.x, save, re-parse the saved file with IT-36 | KiCad opens without error; after save, item counts equal and coordinates within 1 nm; KiCad DRC (GUI or `kicad-cli pcb drc --format json`) shows 0 errors attributable to embodic copper; record KiCad version and file-format token | K-01, K-12 | User |
| IT-39 | IPC plugin smoke (T2/T4) | plugin appears; default design placed in one commit; one Undo removes all; user items untouched; layer-count block message on a 4-layer board | K-02, K-04, K-14 | User |

## 10. L9–L10: regression after optimisation and traceability audit

| ID | Test | Criterion | REQ | Where |
|---|---|---|---|---|
| IT-40 | Reference (scalar, readable) implementation vs optimised NumPy kernels on the same inputs, Windows + Linux, Python 3.11/3.12/3.13 | scalar kernels rel. 1e-12; integrated results rel. 1e-9; DRC violation sets identical; layout hash identical; any change of an embodic golden value needs a recorded reason and Agent 2/4 sign-off | N-04, ADR-0006 | Here + User |
| IT-41 | Performance guard | PF budgets of REQ-N-01/03 on the user's laptop; CI guard against > 25 % regressions | N-01, N-03 | User |
| IT-42 | Traceability audit | every REQ has ≥ 1 IT/UT test; every EQ shown `verified` links a passing test; every EV-ID resolves; manual audit of 10 random results back to the PDF page (I open the page) | T-04, T-09 | Here |

## 11. Comparison with Agent 6's plan (`architecture/test_plan_draft.md`)

| Topic | Agent 6 | This strategy | Note |
|---|---|---|---|
| DRC soundness | PR-01 both directions, UT-DRC-02 exact kernels | IT-12/IT-19/IT-20 with exact arcs | agree; DEF-01 must remove the inherited 4 µm slack first |
| Oracles | OR-01…10 with prerequisites | IT-13…18 + pre-registration, R from published length (IT-14 step 1), Ke-per-turn ratio (IT-15) | adds pre-registration and two runnable-now partial checks |
| Symmetry | PR-06 abs(Ke) invariant under rotation | IT-22 phasor shift by p·2π/Q + relabelling | stronger (DEF-17) |
| EMF independence | GR-04 vs Xcoil; UT-PHY-05 closed form | IT-06 Stokes area integral | adds a method-independent check |
| Pitch factor | — | IT-03 | gap in Agent 6's plan (DEF-17) |
| Inductance | OR-09 characterisation | IT-09 own derivation + IT-18 quantity definition | DEF-08 |
| Status rule | UT-RES-02, PR-12 | IT-25 incl. "identical re-entry never changes status" | depends on DEF-02 fix |
| KiCad | KX-01…11, KS-01…08 | IT-36 own parser, IT-38 re-parse after KiCad save | agree; adds round-trip comparison |
| Mutation testing | §15 item 6 | not duplicated | I endorse it for `winding`, `drc`, `results.status` |
| Accessibility | AX-01…07 | IT-29…34 | agree; IT-30 adds an automatic visual-order comparison |

## 12. What I need from others before these tests can run

- Agent 3: exported primitive lists and circuit objects in a documented JSON form (for IT-06, IT-07, IT-12, IT-21).
- Agent 2: frozen oracle input sets (O1 magnet model, O2 geometry) for pre-registration; re-based EQ-03 tolerance.
- Agent 6: DEF-01 and DEF-02 decisions recorded (they define the pass criteria of IT-19/20 and IT-25).
- User (via Fable): T0–T6 runs, FEMM availability, D09 author contact (UD-25) for the turn count.

## 13. Additions after the defect-fix round (re-verification 2026-10-04; D-006, D-007)

These tests were made necessary by the fixes. Same conventions as above; all `not tested` against embodic. Prototype
scripts for IT-43/IT-45/IT-49/IT-50 already exist in `checks/` and were run on Phase 1 artefacts.

| ID | Test | Oracle / method | Criterion | REQ | Where |
|---|---|---|---|---|---|
| IT-43 | **Exact phase assignment for all Q/2p** (DEF-14) | the port's integer rule `b = ((4·m·r + Q) // (2·Q)) mod 2m`, r = (k·p) mod Q, against my Fraction implementation (`v1_star_of_slots.py`, tie rule T1); run on Windows and Linux, Python 3.11–3.13 | identical patterns for all Q = 3…48, 2p = 2…48 (already 1104/1104 for the rule as written in the port notes); 12/10 = "AabBCcaABbcC" on every platform; no float comparison in the decision path (AST check) | F-02 | Here + User |
| IT-44 | **DRC ε rule (D-006)** at the boundary | fault injection with a 1 µm resolution sweep: measured clearance = rule + {+2, +1, 0, −0.5, −1, −2, −4, −5} µm on line–line, line–arc, arc–arc and via–trace pairs | violation reported iff measured < rule − ε (ε ≤ 1e-6 mm): +2 … −0.5 µm pass, ≤ −1 µm fail; with the discretised kernel the documented sagitta bound is subtracted, so no case < rule − ε passes; Xcoil-slack-band cases are listed as "indeterminate" in golden runs, never as failures | F-10 | Here |
| IT-45 | **Badge rule (D-007)** truth table | enumerate {EQ evidence status} × {test state} × {validity cap} for chains of 1–5 EQs; assert inputs never change the badge | badge = weakest of the three; `assumption` only via an equation whose own status is `assumption` (EQ-16, EQ-17); `cannot verify yet` ⇒ `unresolved` + "estimate" | T-03, T-05 | Here |
| IT-46 | **Assumed-input tag** membership | for the default design and three variants (all geometry changed; B_r marked `measured` with source; copper thickness `measured`): compute the expected tag from ADR-0003 decision 3 by hand | tag = inputs equal to default + physical-property inputs not `measured` + equation-level assumptions not retired; dominant first (registry order); count shown on every number (my v11 audit on the live widget tree) | T-01, T-03, T-06 | Here |
| IT-47 | **Re-entry invariance and real changes** | (a) re-enter the current value of every input; (b) type the default into an input whose current value differs; (c) mark an input `measured` without a source | (a) no badge, tag or hash change; (b) hash changes and the input joins the tag (corrects PR-12 wording, DEF-21); (c) refused | T-03, T-06, F-21 | Here |
| IT-48 | **`measured` provenance round trip** | save/load project with measured inputs and source records; export JSON/PDF | provenance and source survive byte-identically; exports list them; a computed value is never labelled measured | T-06, T-07, T-10 | Here |
| IT-49 | **EQ-05 validity check** (DEF-18), once Agent 2 specifies it | compute the edge-zone share of the EMF integral (my `v9_edge_zone_share.js` method) for the default design, O1 (D08) and O2 (D09) geometries and for designs with conductors ≥ G inside the magnet span | cap/limitation decision follows the specified threshold; the oracle designs are not capped merely because their coils span the magnet ends (otherwise OR-01/OR-02 could never raise Ke) | T-08, F-11 | Here |
| IT-50 | **True-spiral generator length** (DEF-09) | my independent polar-form construction (`v10_true_spiral_length.py`, equal to Agent 2's `eq03_spiral_vs_loops.py` to 0.001 mm) | generator path vs true spiral within ±1 % (lead/stub conventions documented); closed-form band per case ±2 percentage points (D08 N = 3: +23.1 %; 12/16 N = 8: +4.2 %; 18/16 N = 4: +6.8 %) | F-06 | Here |
| IT-51 | **Turn criterion, three modes** (DEF-09) | concentric test mode / spiral without eye / spiral with eye | D08 3 / 3 / 2 (`limiting_reason = eye`); 12/16 11 / 11 / 10; 18/16 8 / 8 / 7 — exact | F-06 | Here |
| IT-52 | **O2 pre-registration pre-check** (DEF-19) | before any O2 model run, the frozen (N, coil radii) must reproduce D09 Table 1 (3244 mm per phase incl./excl. links as declared, 171 mm² mid-loop area) within 2 % | runs with geometries that fail the pre-check are rejected as invalid oracle inputs | F-11, T-12 | Here |
| IT-53 | **KiCad compact window** (REQ-K-15) | Playwright at 880 × 600 (C-B1) or Qt widget geometry (C-A) | no scroll; "Place on board" fully visible; layer-count block message shown for a 4-layer board (baseline: mockup 05b passes) | K-14, K-15 | Here + User |

## 14. Additions after the final round (EC-05)

| ID | Test | Oracle / method | Criterion | REQ | Where |
|---|---|---|---|---|---|
| IT-54 | **EC-05 metric reproduction** | my own digitisation of D09 Fig. 7 and own e_edge implementation (`checks/v12_ec05_independent.py`) | embodic e_edge within ±0.1 pp of 5.33 % (default), 4.21 % (O1), 5.79 % (O2, N = 8); D09-like rotor with 10 mm radial magnets → > 10 % → badge `unresolved` | T-08, F-11 | Here |
| IT-55 | **EC-05 transfer check** (DEF-23) | FEMM 2-D (axisymmetric section through the pole centre, r–z plane) or 3-D FEA of the default rotor and of D08 (5 mm magnets, T-arrangement): B_z at the copper-layer z versus r near both magnet ends | fitted D_e and c_e within the stated EC-05 values ± their declared uncertainty; otherwise EC-05 is re-calibrated; B_z deficit compared with the ‖B‖ deficit used for calibration | T-08, F-07 | User / P3 |
| IT-56 | **Independence of EC-05 validation** | OR-01 (D08) evaluated with and without the EC-05 add-on; OR-07/OR-08 flagged "not independent of the EC-05 calibration" in the report | report lists which oracle tests EC-05 independently; no oracle used for both calibration and validation counts as validation | T-12 | Here |
