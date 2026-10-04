Prepared by: Agent 2 — Motor Design Expert — model: claude-opus-5-5

# Answers to requests from Agents 1, 3 and 6 (reconciliation round, 2026-10-04)

Status labels per PROJECT_BRIEF §3. EQ-IDs refer to `equation_specification_draft.md` (revised in this round); the
machine-readable copy is `equation_registry_draft.json` (validated with `python -c "import json;json.load(open(...))"`).
Numbers were computed by me with the scripts in `checks/`; none is a measurement.

## 1. Agent 1 (`design/design_spec_draft.md` §10.4, Q3, Q5; §2.2 `strands`)

### 1.1 Status of a computed result — confirmed with amendments

> **Superseded by decision D-007 (defect DEF-02).** The rule below made almost every physics result `assumption` and let
> re-typing a default change a status. Current rule: badge = calculation trust (equation evidence × test state × validity),
> assumptions shown as a separate count/list, `measured` provenance only with a named source — see
> `equation_specification_draft.md` "Status rule for computed results" and the registry fields `result_badge_rule`,
> `assumptions_tag_rule`, `input_provenance_vocabulary`. The text below is kept for the record.

Rule (agreed with ADR-0003 item 4, amended):
**result status = weakest of**
1. the **equation status** of every EQ in the chain (Phase 1 evidence status: table "Equation status" in the spec);
2. the **implementation status** — `not tested` until the kernel's unit/regression tests pass in the current build (this
   should never appear in a released build; CI blocks it);
3. the status of **every input the kernel actually uses** (not every input of the design): user-entered or KiCad-imported
   = neutral; default or unsourced value = `assumption`; sourced constant = its EV status (e.g. ρ₂₀ `verified`, EV-53);
   the equation's own stated assumptions (e.g. "PCB copper = IACS copper" in EQ-10) count as `assumption` inputs unless the
   user replaces them by measured data;
4. the **validity cap** — any violated validity limit (e.g. w > δ/3 for EQ-12, conductor near the magnet's radial edge for
   EQ-05) → `unresolved`.

Amendments to Agent 1's §10.4 list:
- Item 3 ("dominated by an assumed input"): use *every used default* for the status (no judgement at run time, honest by
  construction); use my **dominant assumed inputs** list (spec section of that name; `dominant_assumptions` in the
  registry) only to **order and explain** the "n assumptions" tag. Reason: deciding at run time which input "dominates"
  requires a sensitivity analysis we do not have yet.
- Item 2 ("inferred — gate passed, no oracle match yet"): agreed; "oracle not yet run" must **not** produce `not tested`.
  `not tested` is reserved for code that has not passed its tests.
- Item 1 (`verified`): for a new user design a physical result can only be `verified` if every EQ in its chain is `verified`,
  every used input is neutral or verified, and no validity cap applies. Exact identities and counts (pole/coil pitch, k_w by
  exact arithmetic, turn count, generated track length, series turns) are `verified` once their tests pass. Never "measured".
- Item 4: an EQ with gate `cannot verify yet` (EQ-14, EQ-15, EQ-20) gives `unresolved` and the label "estimate"/"guideline".

**Order:** I agree with ADR-0003: `unresolved` < `not tested` < `assumption` < `inferred` < `verified`. Reasoning: an
untested computation can be wrong in an unknown way, whereas an assumption is explicit and reviewable; `unresolved` is
lowest because it states that the evidence is missing or conflicting, which no test can repair.

### 1.2 Dominant assumed inputs per EQ

Full table: `equation_specification_draft.md` "Dominant assumed inputs per equation"; same content in the registry field
`dominant_assumptions`. Short form: EQ-05/06/09/18 → B_r, µ_r (G23, no datasheet value), magnet thickness, air gap,
magnet shape; EQ-07 → layer z; EQ-10 → copper thickness, temperature, PCB copper = IACS; EQ-11 → plating, via count;
EQ-12 → B̂, copper thickness, frequency; EQ-14 → δ′, k_w1, missing end-turn terms; EQ-15 → ΔT, standard missing;
EQ-16 → laminate density; EQ-17 → film coefficient h; EQ-20 → L_s, V_dc; EQ-01/08 → none (exact).

### 1.3 Parallel strands (`strands`) for spiral coils — not recommended; replacements

- In Xcoil's serpentine, `strands` = several traces side by side forming one turn. In a planar spiral, side-by-side strands
  sit at different lateral offsets on every turn, so each strand links a different area → different EMF → circulating
  current between strands (`inferred`; the effect is documented for parallel traces in D02 p.4–5 Fig. 11, EV-35: 1.44 A
  circulating vs 0.315 A applied per trace). Transposition within one layer is impossible without crossings.
- Recommendation for Phase 2: **no `strands` parameter for spiral coils** (keep it reserved, validation `UNSUPPORTED`).
  Use instead: (a) **parallel layer pairs** (M1; `LayerConfig.series_groups`), with the EQ-07 circulating-loss check;
  (b) **parallel coil groups** (`parallel_paths` a ≤ t, identical phasor and identical z only); (c) narrower traces / more
  turns to cut eddy loss (EQ-12 ∝ w³); (d) later: radius-dependent width (S5, D10).
- Research option, `not tested`: a bifilar spiral whose two strands swap position at the centre via (outer strand on layer X
  continues as the inner strand on layer Y) equalises the strands' flux linkage to first order (`inferred` geometric
  argument); it needs two vias per eye. D14 reports a related "two parallel conductors via-connected" pattern, FEA only, with
  a stator yoke (EV-41).

### 1.4 Phase naming and polarity convention — confirmed (my preferred wording)

- Phases **A, B, C** are winding phases; line terminals **U, V, W** are their start terminals (A→U, B→V, C→W); N = star point.
- View: from the **F.Cu (L1) side, which faces rotor 1** (= Agent 1's "seen from the top layer" when rotor 1 is on the
  F.Cu side). World axes x right, y up, θ counter-clockwise; coil k (k = 0…Q−1, shown as k+1) centred at θ₀ + k·2π/Q.
- **Positive coil = positive phase current circulates clockwise** seen from that side (layer X spirals inward clockwise,
  layer Y is its mirror traversed outward, same circulation). Reversed ("lowercase") coils circulate counter-clockwise.
- Sequence: with the rotor turning in +θ, coil k's EMF lags by p·θ_k; the 60° belts (B at +120°) then give A→B→C
  (`inferred`, phasor arithmetic of `checks/kw.py`); the 12/16 order around the stator is A C B A C B …. Swapping B and C
  reverses the rotation for the same terminal sequence. KiCad export flips y without changing these definitions.
- `spiral_coil_concept.svg` was corrected to this convention (coils now numbered counter-clockwise; +θ arrow added).

## 2. Agent 3 (`software/calculation_flow_and_port_notes.md` §1, §7.3)

### 2.1 Two separate gates — confirmed

Yes: **port equivalence** (Python = Xcoil v3 within Agent 3's tolerances) and **engineering validity** (equation gate +
oracles) are separate, and a function needs both where both apply. Additions:
- `reuse with change` items: port equivalence applies to the unchanged core only; the change is checked by engineering
  tests alone.
- `replace` items and new items (spiral generator, EQ-04, EQ-21): engineering tests only.
- Do **not** port known defects bug-for-bug. Expected, intentional divergences from Xcoil (to be listed as such in the
  harness): `starOfSlots` belt-edge bug (12/14, 24/14, 24/22, 24/26 balanced in Python, C6); `kdAnalytic` removed;
  ρ₂₀ 1.7241e-8 instead of 1.724e-8 (+0.006 %); copper density 8.89 instead of 8.96 g/cm³; one rotor type drives field,
  inductance and inertia consistently (Q-3); the B_t eddy term on circumferential segments if dropped (Q-6). For golden
  comparisons, run Python with Xcoil-compatible constants or compare at function level.

### 2.2 Closed-form test values for the spiral generator (EQ-02, EQ-03)

Script: `python3 checks/eq02_eq03_reference.py` (prints every intermediate value). Convention: R_o0, R_i0 = **centre-line**
radii of loop 0 at the outer and inner end-turn (for copper-edge inputs r_outer, r_inner: R_o0 = r_outer − w/2,
R_i0 = r_inner + w/2); w_d = w + s; loop i: d_i = (i + ½)w_d (side offset from the sector edge, sides parallel to the edge,
coil gap = s), R_out,i = R_o0 − i·w_d, R_in,i = R_i0 + i·w_d, θ_cp = 2π/Q, S = sin(θ_cp/2). Strict "<" → largest integer
below the bound. Concentric loops, sharp corners, **no centre-via eye** (the generator's eye removes turns; test it
separately).

**EQ-02 rules.** Radial bound N_c < ½((R_o0 − R_i0)/w_d + 1). Loop criterion (used by the generator): loop i is trapezoidal iff
d_i < R_in,i·S (and R_in,i < R_out,i); otherwise triangular iff apex radius d_i/S < R_out,i; stop at the first loop that is
neither. Printed D08 eq. 3.25–3.26 are reported as a cross-check (they mis-split the loops, see EQ-02).

**G1 — D08 geometry** (R_o0 = 44.0, R_i0 = 12.5, w = 2.06, s = 0.8, Q = 12; w_d = 2.86, θ_cp = 30°, S = 0.258819):
- Radial bound: ½(31.5/2.86 + 1) = ½(11.014 + 1) = **6.007** → N ≤ 6.
- Printed 3.25: 12.5·0.258819/(2.86·0.741181) + 1 = 3.2352/2.1198 + 1 = **2.526** → 2; 3.26: (11.014 − 3.8637 − 4 + 2)/4.8637
  = **1.059** → 1; total 3.
- Loop criterion: i = 0: d = 1.43 < 12.5·S = 3.235 → trapezoid; i = 1: d = 4.29 ≥ 15.36·S = 3.975 → apex 4.29/S = 16.58 <
  41.14 → triangle; i = 2: d = 7.15 → apex 27.63 < 38.28 → triangle; i = 3: d = 10.01 → apex 38.68 ≥ 35.42 → stop.
  **1 trapezoidal + 2 triangular = 3 loops** (= D08 Table 4.6, 3 loops).
- EQ-03 per loop (angles in degrees, β in rad for arc lengths):
  - i = 0: φ_out = asin(1.43/44) = 1.8624°, β_out = 13.1376° = 0.229294 rad → L_out = 2·44·0.229294 = **20.178**;
    φ_in = asin(1.43/12.5) = 6.5690°, β_in = 8.4310° = 0.147148 rad → L_in = 2·12.5·0.147148 = **3.679**;
    L_s = 44 cos φ_out − 12.5 cos φ_in = 43.977 − 12.418 = **31.559**; L_0 = 20.178 + 3.679 + 2·31.559 = **86.974**.
  - i = 1 (triangle): R_out = 41.14, φ_out = 5.9856°, β_out = 0.157331 rad → L_out = **12.945**; L_s = 41.14 cos φ_out −
    4.29/tan 15° = 40.916 − 16.010 = **24.905**; L_1 = 12.945 + 2·24.905 = **62.756**.
  - i = 2 (triangle): R_out = 38.28, φ_out = 10.7650°, β_out = 0.073914 rad → L_out = **5.659**; L_s = 37.606 − 26.684 =
    **10.922**; L_2 = **27.503**.
  - **Track length per coil-layer = 177.233 mm**; 8 coil-layers per phase → 1417.9 mm; with ρ(50 °C) = 1.927e-8 Ω·m,
    w·t = 2.06 × 0.0348 mm² → 0.381 Ω (D08: 0.39 Ω).

**G2 — embodic default 12/16** (r_inner 18, r_outer 38 copper edge → R_o0 = 37.75, R_i0 = 18.25; w = 0.5, s = 0.2, Q = 12;
w_d = 0.7, S = 0.258819):
- Radial bound ½(19.5/0.7 + 1) = **14.429** → N ≤ 14. Printed 3.25 → **10.104** → 10; 3.26 → **1.232** → 1; total 11.
- Loop criterion: trapezoidal while 0.35 + 0.7i < (18.25 + 0.7i)·S → last trapezoid i = 8 (5.95 < 23.85·S = 6.173; i = 9:
  6.65 ≥ 24.55·S = 6.354); triangles i = 9 (apex 25.69 < 31.45), i = 10 (28.40 < 30.75); i = 11: 31.10 ≥ 30.05 → stop.
  **9 trapezoidal + 2 triangular = 11 loops.**
- EQ-03, N = 8 (all trapezoidal; the engine fits 8 turns with a centre via, C4): i = 0: β_out = 15° − asin(0.35/37.75) =
  0.252528 rad → L_out = 2·37.75·0.252528 = **19.066**; β_in = 15° − asin(0.35/18.25) = 0.242620 rad → L_in = **8.856**;
  L_s = 37.748 − 18.247 = **19.502**; L_0 = **66.925**. … i = 7: R_out = 32.85, R_in = 23.15, d = 5.25: β_out = 0.101294 rad →
  L_out = **6.655**; β_in = 0.033027 rad → L_in = **1.529**; L_s = 32.428 − 22.547 = **9.881**; L_7 = **27.946**.
  Loops 0…7: 66.925, 61.349, 55.787, 50.233, 44.679, 39.117, 33.542, 27.946 → **379.578 mm per coil-layer**.

**G3 — 18/16, same annulus** (Q = 18, θ_cp = 20°, S = 0.173648):
- Radial bound **14.429**. Printed 3.25 → **6.479** → 6; 3.26 → **1.790** → 1; total **7**.
- Loop criterion: trapezoids i = 0…4 (i = 4: 3.15 < 21.05·S = 3.655; i = 5: 3.85 ≥ 21.75·S = 3.777); triangles i = 5 (apex 22.17 <
  34.25), 6 (26.20 < 33.55), 7 (30.23 < 32.85); i = 8: 34.27 ≥ 32.15 → stop. **5 + 3 = 8 loops** — here the printed formula
  (7) and the loop criterion (8) disagree.
- EQ-03, N = 4: i = 0: β_out = 10° − 0.5312° = 0.165261 rad → L_out = **12.477**; β_in = 0.155354 rad → L_in = **5.670**;
  L_s = **19.502** (side length does not depend on θ_cp); L_0 = **57.151**; loops 0…3: 57.151, 51.575, 46.014, 40.459 →
  **195.199 mm**.

Proposed tolerances: loop counts exact (concentric test mode) or ±1 (true spiral, which steps one pitch per turn); lengths
1e-3 mm against the closed form; generated spiral vs closed form within −6 … 0 % (C4). Registry: EQ-02/EQ-03
`reference_case` and `additional_cases`.

## 3. Agent 6 (`architecture/architecture_draft.md` §7.3, §16, R7)

### 3.1 Via-count formula (§7.3) — correct for M1 and M2; general form

Checked (`inferred`, counting argument; through vias, v vias per transition, interconnect vias excluded):
- M2, n pairs in series: per coil n centre vias + (n − 1) transfer vias → N = Q·v·(2n − 1). Default Q = 12, n = 3: **60** ✓.
- M1, n > 1 pairs in parallel: one shared centre via + one stitch via joining the X layers at the entry terminal + one joining
  the Y layers at the exit terminal → N = 3·Q·v. Default: **36** ✓.
- **General** (k series groups, group g has n_g parallel pairs): N = Q·v·(2k − 1 + [n_1 > 1] + [n_k > 1]) — one shared centre
  via per group, one through via per series node (it joins the Y layers of group g and the X layers of group g+1), and an
  entry/exit stitch via only when the end group has more than one pair. Checks: M1 (k = 1, n = 3) → 3; M2 (k = 3) → 5;
  D10 style ((0,1),(2,3)) → 2·2 − 1 + 1 + 1 = 5 per coil.
- M4 (one phase per pair): Σ over pairs of Q_pair·v (one centre via per coil); option B 16/16 × 3 pairs → 48.
- Notes: blind/buried vias change positions, not counts; all n centre vias of an M2 coil must fit in its eye (EQ-02 eye
  term); with M3 rotation counts are unchanged.

### 3.2 Spiral generator — inputs and outputs for the data model

Inputs (names follow §7.1 where they exist; new ones marked *new*; defaults are `assumption`, ranges are validation
proposals):

| Name | Unit | Range (proposal) | Default | Note |
|---|---|---|---|---|
| `coil_count` (Q) | – | 3…96; balanced per `check_feasibility`; = 2p for M4 | 12 | |
| `RotorSpec.poles` (2p) | – | 2…200, even | 16 | |
| `r_inner_mm`, `r_outer_mm` | mm | r_inner > bore/2 + edge clearance; r_outer ≥ r_inner + 2(w + s) + eye | 18.0, 38.0 | **copper-edge** radii of the coil body; centre-lines R_i0 = r_inner + w_in/2, R_o0 = r_outer − w_out/2 |
| `trace_width_mm` (w) | mm | 0.05…20; warn below fabricator minimum | 0.5 | |
| `clearance_mm` (s) | mm | 0.05…20 | 0.2 | |
| `coil_gap_mm` | mm | ≥ clearance | 0.2 | copper-to-copper between neighbouring coils; first side offset = gap/2 + w/2 |
| `turns` (N per coil per layer) | – | 1…200 or None | None (= maximum feasible) | |
| `side_style` | – | radial / parallel | parallel | S1/S2 |
| `end_style` | – | arc / straight / stadium | arc | S3 later |
| `inner_turn_mode` | – | moving / fixed | moving | EQ-02 loop criterion |
| `corner_radius_mm` | mm | 0…½·(shortest side) | 0.0 | reduced automatically if nested fillets do not fit (Xcoil behaviour) |
| `end_width_outer_mm`, `end_width_inner_mm` | mm | w…20 or None | None (= w) | |
| `first_coil_angle_rad` (θ₀) *new* | rad | −2π…2π | π/2 (coil 1 at the top) | §1.4 convention |
| `x_inward_sense` *new* | – | cw / ccw | cw | fixes "positive = clockwise" |
| `eye` (`EyeRequirement`) *new* | – | count = centre vias per coil (from `LayerConfig`), pad and clearance from `ViaSpec`/`DrcRules`, arrangement radial / tangential | count from layer plan, radial | |
| `lead_style` *new* | – | radial_then_arc / straight | radial_then_arc | Xcoil lead to centre via |
| `terminal_offset_mm` *new* | mm | ≥ clearance + pad/2 | clearance + pad/2 | terminal via beyond r_outer |
| `min_side_length_mm` *new* | mm | ≥ 0 | 2·w | rejects degenerate triangular loops |
| `LayerPair.rotation_rad` | rad | any | 0 | M3: π/Q |

Outputs (`SpiralArtwork` + reports):

| Output | Unit | Content |
|---|---|---|
| `x_prims`, `y_prims` | mm | canonical coil on layers X (in) and Y (out, mirrored), lines/arcs with width and kind (side, endturn, lead, stub) |
| `turns_achieved` | – | N actually built |
| `turn_limit` | – | {radial_bound, loop_trapezoidal, loop_triangular, printed_3_25, printed_3_26, eye_limit, limiting_reason: radial / lateral / eye / user} |
| `turn_table` | mm, rad | per turn: type (trapezoid/triangle), d_t, R_out,t, R_in,t or apex radius, span σ_t at mean radius (for EQ-08 per-turn pitch factor), side/arc lengths, length |
| `track_length_mm` | mm | per layer (X, Y), per coil; closed-form EQ-03 value alongside for the report |
| `eye_vias` | mm | local centre-via positions per pair; free-eye check |
| `terminals` | mm | entry/exit points and their layers |
| `envelope` | mm, rad | r_min_cu, r_max_cu, angular half-width of the footprint |
| `copper_area_mm2` | mm² | per layer (EQ-16) |
| `min_spacing_mm` | mm | smallest side-to-side and side-to-via spacing achieved (DRC pre-check) |

### 3.3 `equation_registry_draft.json`

22 entries EQ-01…EQ-22 with the requested fields (`id`, `name`, `formula`, `variables` [{symbol, unit, meaning}],
`sources` [EV-IDs] + `source_notes`, `gate_verdict`, `status`, `tolerance` {value, basis}, `dominant_assumptions`,
`reference_case` {source, inputs, expected, tolerance} and optional `additional_cases`). Top-level `notes` explain that
`status` is the Phase 1 evidence status (implementation status starts as `not tested`, ADR-0003 item 5) and that
`gate_verdict: "replace"` for EQ-04/EQ-21 means "new implementation, no Xcoil counterpart". Line 1 carries the required
"Prepared by" text as the `prepared_by` key so the file stays valid JSON.

## 4. Files changed in this round

`equation_specification_draft.md` (sources/statuses EQ-02, 05, 06, 08, 10, 14, 16; equation-status table; status rule;
dominant inputs), `topology_analysis.md` (EV-56…71, conventions §3.4, patent note §4.3, defaults §5.2, §7 decisions),
`existing_logic_review.md` (constants rows), `spiral_coil_concept.svg/.md` (counter-clockwise numbering, +θ arrow,
conventions), new `answers_to_agents.md`, `equation_registry_draft.json`, `checks/eq02_eq03_reference.py`.

---

**Revision 2026-10-04 (defect fixes):** DEF-02 (§1.1 marked superseded by D-007); DEF-09 (see EQ-02/EQ-03 in the spec for the
three-mode turn criterion and the true-spiral tolerance basis that replace the "±1 turn" and "−6 … 0 %" statements of §2.2);
oracle inputs frozen in `oracle_cases_draft.json` (§5 below).

## 5. Frozen oracle parameter sets (for pre-registered Phase 2 runs)

`oracle_cases_draft.json` lists O1 (D08), O2 (D09) and O3 (Wang 2019, D10) as explicit parameter sets: every input with
value, unit, source (document/page) and status; inputs the paper does not give are marked `unresolved` together with the
value Phase 2 will assume (and, where it matters, a sweep range); expected published values with their kind (measured /
calculated / FEA) and the comparison rule. Changing a frozen value after a Phase 2 run requires a new case version.
