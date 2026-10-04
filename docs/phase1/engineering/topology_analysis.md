Prepared by: Agent 2 — Motor Design Expert — model: claude-opus-5-5

# Topology analysis — 3-phase multi-layer spiral-coil PCB stator (Phase 1 draft, 2026-10-04)

Scope: Phase 1 questions 1–6 (sub-items a–e of the task). Status labels per PROJECT_BRIEF §3: `verified`,
`inferred` (reasoning given), `assumption`, `unresolved`, `not tested`. Source aliases and EV-IDs follow
`docs/phase1/evidence/evidence_register.md` (B1 = `/mnt/user-data/uploads/paper/`, B2 =
`/mnt/user-data/uploads/Desktop/Fantastic Creature/FC-Smart_Actuator/papers/`). Page numbers are PDF page indices
(printed page in brackets where it differs). Numeric checks were run by me; scripts are in `checks/` of this folder
and the commands are listed in `existing_logic_review.md` §3. No result in this file is measured; computed results
come from analytical formulas or from the unvalidated Xcoil v3 engine and are labelled so.

**Revision 2026-10-04 (reconciliation round):** updated with Agent 5's follow-up evidence EV-53…EV-71 and gaps G23–G26
(D09 board details, D12 coil/pole rule, D15 per-turn pitch factor, repository end-turn parse, magnet data, copper
constants, ECM patent notes); conventions fixed in §3.4; new §7 "Decisions the user must make".

## 0. Key findings

| # | Finding | Status |
|---|---|---|
| K1 | Repository board = radial-conductor **wave** winding (144 radial conductors/layer, 16 magnets); it is not a concentrated spiral coil design. Agent 5's end-turn parse (EV-71): nested outer caps of 6 radii centred on 12 axes at r = 26 mm plus short inner steps offset from the coil axes → a series wave-like path. | verified (README l.1–12; Gerber parse, `repo_survey.md` §1.4; EV-71 parse verified, interpretation inferred) |
| K2 | The render's look can be read as "8 + 8 concentrated spiral coils offset by half a pitch" (Fable), but at 676 px the end-turn groups (≈3–4 nested loops) and the uniform radial conductor field are **also compatible with a wave winding with nested end connections** like the repository board. EV-71 shows that the same project's Gerber board produces a "spiral-looking" pattern with a wave path; Agent 5 also reads the render as undecidable (`ecm_pcb_stator_evidence.md` §1). | unresolved (inferred from image) |
| K3 | 16 coils sharing one layer cannot form a balanced symmetric 3-phase winding (Q must be a multiple of m = 3). 16-coil artwork is 3-phase-capable only as **one phase per layer pair** (16 full-pitch coils per phase, phases rotated by 2π/(3p) = 15° mech. for 2p = 16). | inferred (FSCW rules §2.2; script `checks/kw.py`) |
| K4 | Recommended default (design choice): fractional-slot concentrated spiral winding **12 coils / 16 poles**, all three phases on every layer, keeping the repository's 16-pole rotor; alternatives **18/16**, phase-per-layer-pair **16/16**, and the oracle configurations **12/10** (D08) and **12/16** (D09: 12 coils per layer `verified`, EV-62 — Agent 4 also counted 12 coil eyes in Fig. 1a; turns per coil 7 or 8 `unresolved`). | assumption (reasons §2.4) |
| K5 | Spiral coils favour Q/2p < 1 (coil pitch > pole pitch): the turn spans then straddle the pole pitch, so inner turns keep a high pitch factor. The engine sweep ranks 12/16 first in Ke/√R for the repository annulus, followed by 15/16 and 18/20 (all Q/2p < 1). | inferred (pitch-factor reasoning) + indicative engine numbers (not validated) |
| K6 | Xcoil v3 `starOfSlots` wrongly rejects balanced combinations whose EMF phasors fall exactly on a 60° belt edge (12/14, 24/14, 24/22, 24/26 …); 12/14 is D11's design. Must be fixed before reuse. | verified (reproduced, `existing_logic_review.md` §3 C6) |
| K7 | Xcoil v3 sector generator supports neither "triangular" inner turns (inner end-turn moving outward) nor series connection of layer pairs nor rotated layer groups; with D08's own geometry it fits **0** turns where D08 built 3. | verified (reproduced, C5) |
| K8 | Rectangular block magnets (repository: 20 × 6 × 2 mm) have a radius-dependent pole-arc ratio (0.85 at r = 18 mm → 0.40 at r = 38 mm, D08 eq. 3.3); the engine's constant α_p cannot represent this (−2.8 % on ∫B₁r dr at α_p = 0.55, and different harmonics). | verified (D08 p.31 eq. 3.3) + computed |

## 1. (a) Topologies: repository vs render; coil-type definitions

### 1.1 What the repository contains

- `verified`: README states "Wave windings, 16 coils equivalent per phase, three phases", 6 layers 1 oz, 0.5 mm radial
  traces, top 3 layers identical and bottom 3 identical, Ø25 mm hole, 12-sided outline 93 mm across flats, 16 magnets
  20 × 6 × 2 mm (`/home/claude/embodic-ref/magnetless_motor/README.md` l.1–12; EV-R1).
- `verified` (Agent 5 parse, `repo_survey.md` §1.4, EV-R2): per layer 143–144 straight radial conductors r = 18.0 → 38.0 mm
  at 2.5° pitch; through vias Ø0.3/0.5 mm on four rings (r = 18.0, 18.5, 37.5, 38.0 mm) + 41 in clusters; three terminal
  lands at 60°/90°/120°; bottom group rotated 15° (mod 30°) relative to the top group.
- `inferred`: with 16 poles the pole pitch is 22.5° = 9 conductors = 3 conductors per phase per pole per layer
  (Agent 5). The 15° rotation equals 8 × 15° = 120° electrical, i.e. a **phase permutation** between the two layer groups,
  and 15° is a multiple of the 2.5° conductor pitch, so the two groups keep a common through-via grid. Reasoning: angle
  arithmetic on verified values; the designer's intent is not documented (`unresolved`).

### 1.2 What the render shows

- `verified` (provenance): two user screenshots of Instagram post DWvb7wWkz4M ("magnetless motor", same project name as the
  repository) and one ECM PrintStator photo; no dimensions or electrical values may be read
  (`docs/phase1/evidence/reference_images/README.md`).
- Fable's reading (`inferred from image`): concentrated spiral coils with fanned radial sides and nested stadium end-turns,
  8 bright + 8 darker coils offset by ≈22.5°, overlapping.
- My reading of frame 1 at 3× zoom (`inferred from image`): the radial conductors fill the whole annulus at an approximately
  constant pitch with no visible empty coil "eyes"; each visible end-turn group (outer rim and hub) shows about 3–4 nested
  loops. That pattern is **also** produced by a wave winding with nested ("concentric") end connections, as on the
  repository board. Whether each group closes into a concentrated coil (outer and inner end-turns centred on the same
  angle) or connects to the next pole (inner end-turns offset by one pole pitch) cannot be resolved at 676 px
  (`unresolved`).
- Consequence (`inferred`): the user's decision (concentrated planar spiral coil per coil, PROJECT_BRIEF §1) stands on its
  own; the render defines only the visual style (fanned sides, stadium end-turns, two overlapping layer groups). If the user
  wants the render's exact board, a wave option would be needed → open question Q1 (§6).

### 1.3 Coil and winding types (definitions with evidence)

| Type | Definition | Evidence | Relevance to embodic |
|---|---|---|---|
| Planar spiral (concentrated) coil | One coil = a continuous spiral of N turns on a layer around one centre; the spiral on the next layer is the complementary spiral with the same circulation, joined at the centre by a via; coils of one layer may belong to one or several phases | D02 p.1 §I, Fig. 1b (EV-01); D14 p.4 §2.1 Fig. 2 current path outer → inner, via, inner → outer (EV-40); D15 p.4–5 multi-layer spiral with vias (EV-43) | The chosen embodic topology (`verified` user decision) |
| Sector / trapezoidal spiral | Spiral coil whose footprint is an annular sector: two (near-)radial sides + inner and outer end-turns; modelled as concentric closed loops | D08 p.33–35 [28–30] Fig. 3.4–3.5, eq. 3.5–3.13 (EV-02); D08 p.43–45 [38–40] eq. 3.24–3.36 (EV-06, EV-07); D09 Fig. 1a/2 "concentric" (p.2) | Main coil shape; D08 is the best oracle (O1) |
| Concentric coils | Several closed concentric loops (not one continuous spiral) per coil or per phase, connected in series; "spiral winding" in D04 = concentric circular coils per phase in series | D04 p.3 §2.1 Fig. 3a (EV-25); D09 p.1–2 §2.1.1 (EV-12); D10 p.2–3 Fig. 2–3 concentric spiral with unequal widths, 12 layers = 2 × 6 parallel (EV-28) | Same EMF physics; the concentric-loop model is an approximation of a true spiral (−4 … −6 % length difference, §3.2) |
| Hexagonal / rhomboidal concentrated | Concentrated coil with inclined sides | D11 p.2–3 Fig. 2, 4 (EV-46); D02 p.1 (variants) | Shape variant; D11 12/14 is an oracle (O9) |
| Wave / serpentine winding | Radial conductors of one phase connected alternately at outer and inner rim, advancing one pole pitch per conductor; distributed, no coil eyes | D02 (continuous wave, EV-01 context); D07 p.2–3 Fig. 2 three wave variants (EV-17, EV-18); repository board (K1); Xcoil v3 `serpentine`/`wave` topologies | Not the embodic topology; manufacturing rules and eddy/parallel-path findings transfer, winding factors do not (`evidence_gaps.md` G18) |

Common physics (`verified` in the cited sources, `inferred` transfer): only radial track components produce back-EMF and
torque; circumferential end-turns are "passive" paths that add resistance (D07 p.3 §2, EV-17; D08 p.38–40 §3.2, EV-05).
For in-plane conductors this is exact for any field, because (v × B)·dl with v = ω r θ̂ is non-zero only for the radial
part of dl and only through B_z (derivation in `equation_specification_draft.md` EQ-06; `inferred`).

## 2. (b) Reuse vs redesign; 3-phase feasibility

### 2.1 Repository parameters

| Item (source EV-R1/EV-R2) | Reuse for embodic? | Status / reasoning |
|---|---|---|
| 6 copper layers, 1 oz (≈35 µm) | Reuse as default stack-up count/weight | assumption (example values only; repo licence GPL-3.0 → parameters as plain facts, no design data copied) |
| 0.5 mm trace, via 0.3/0.5 mm through | Reuse as defaults | assumption |
| Active radii r = 18–38 mm | Reuse as default coil annulus | assumption |
| 16 magnets 20 × 6 × 2 mm | Reuse as default rotor (16 poles) — but needs radius-dependent α_p (K8) | assumption; magnet orientation (20 mm radial) `unresolved` |
| Ø25 mm bore, 12-gon 93 mm flats, 12 × Ø3.1 at r = 45 mm | Reuse as default outline | assumption |
| Layer groups 3 + 3, bottom rotated 15° | **Redesign**: a spiral coil needs in/out layer *pairs*; a 3-layer group ends a coil at its centre (odd count) | inferred (path continuity: in → via → out returns to the rim only after an even number of layers) |
| 144 radial conductors, wave connectivity, end-turn rings at r 14.3–18 and 38–42.4 mm | **Redesign** completely (different topology) | inferred |
| "16 coils equivalent per phase" | Not transferable to concentrated coils | inferred |
| Two-group rotation idea | Reusable as a *concept* (layer-group rotation that preserves the via grid), with new rules §4.2 | inferred |

### 2.2 FSCW rules for concentrated (spiral) coils

The star-of-slots method of slotted machines applies to coreless PCB windings when "slot" is replaced by "coil side"
(D07 p.3 §2, `verified` statement); D09 p.5 states the winding-factor calculation of PCB motors is similar to
radial-flux machines (`verified`). The feasibility rules themselves are **not printed in the corpus**; they are standard
textbook results (`assumption: standard result, source needed` — proposed: J. Pyrhönen, T. Jokinen, V. Hrabovcová,
*Design of Rotating Electrical Machines*, Wiley, chapter on windings; N. Bianchi, M. Dai Prè, "Use of the star of slots
in designing fractional-slot single-layer synchronous motors", IEE Proc. EPA 153(3), 2006 — chapter/page to be confirmed
by Agent 5).

For Q coils (non-overlapping, one coil per "tooth position"), 2p poles, m = 3 phases:
1. q = Q/(2p·m) (coils per pole per phase, fractional for FSCW); t = gcd(Q, p) = machine periodicity.
2. Balanced symmetric winding iff Q/(m·t) is an integer (equivalently Q divisible by 3 and Q/t divisible by 3).
3. EMF phasor of coil k: α_k = p·2πk/Q (electrical). Assign phases by 60° belts (A+, −C, B+, −A, C+, −B).
4. Distribution factor k_d,n = |Σ_{k∈A} s_k e^{j n α_k}| / N_A; pitch factor of a coil of span σ: k_p,n = |sin(n p σ/2)|;
   k_w,n = k_d,n k_p,n. (D04 p.5 eq. 1 gives the integral-slot special case k_q = sin(qα/2)/(q sin(α/2)), EV-26.)
5. t ≥ 2 gives rotational symmetry (no net radial pull from the winding); t = 1 combinations (12/10, 12/14, 15/16) are
   asymmetric (`inferred`; D11 p.4–5 Fig. 7 shows connection-dependent pull forces for 12/14, EV-46).

Corpus support added in the reconciliation round (Agent 5, EV-56…EV-61): D12 p.3 eq. 1 gives the coil/pole relation
N_c/N_pm = m/(m+1) for coreless concentrated-coil machines (EV-56) — satisfied by 12/16 (and 6/8, 9/12, 18/24), but it
is one design rule, not a general feasibility test; D07 p.3 §2.2 (EV-58) as above; D15 p.7 eq. 6 averages the pitch factor
over the turns of a PCB coil (EV-59), which supports the spiral-average pitch factor of §3.3. Dai Pré & Bianchi 2006 (EV-60)
and Pyrhönen et al. (EV-61) were not accessed (G24), so rule 2 stays `assumption: standard result`, and each combination is
also checked by explicit phasor computation (below).

Check of the method (`verified (reproduced)`): `checks/kw.py` reproduces D08's 12-slot/10-pole connection
"AabBCcaABbcC" from the Bavaria tool (D08 p.36 [31] Fig. 3.7) letter for letter (uppercase = +, lowercase = reversed).

Winding factors (outermost-turn span σ = 2π/Q; `checks/kw.py`, formulas above):

| Q/2p | q | t | balanced | k_w1 | k_w5 | k_w7 | pattern (coil 1…Q) | Corpus link |
|---|---|---|---|---|---|---|---|---|
| 12/10 | 0.400 | 1 | yes | 0.933 | 0.067 | 0.067 | AabBCcaABbcC | D08 (O1) |
| 12/14 | 0.286 | 1 | yes | 0.933 | 0.067 | 0.067 | ACcbBAacCBba | D11 (O9) |
| 12/16 | 0.250 | 4 | yes | 0.866 | 0.866 | 0.866 | ACB ACB ACB ACB (all +) | D09 concentric board: 12 coils/layer, 2 layers, 16 poles (coil count `verified`, EV-62; turns ≈ 6–8 `unresolved`) |
| 15/16 | 0.313 | 1 | yes | 0.951 | 0.173 | 0.111 | AaACcCcCBbBbBAa | — |
| 18/16 | 0.375 | 2 | yes | 0.945 | 0.140 | 0.061 | AabBbcCcaAabBbcCca | — |
| 24/16 | 0.500 | 8 | yes | 0.866 | 0.866 | 0.866 | ABC × 8 | — |
| 9/10 | 0.300 | 1 | yes | 0.945 | 0.140 | 0.061 | AacCcbBba | — |
| 18/20 | 0.300 | 2 | yes | 0.945 | 0.140 | 0.061 | AacCcbBbaAacCcbBba | — |
| 16/16 | — | — | **no** (Q = 2p, all phasors at 0°/180°) | — | — | — | single-phase only | — |

### 2.3 What a 16-coil arrangement would mean for 3 phases (`inferred`)

- 16 coils on one layer shared by A, B, C: Q = 16 is not a multiple of 3 → no symmetric balanced assignment (5 + 5 + 6
  coils at best, unequal phasor sums). Reject.
- 8 + 8 coils in two layer groups, each group one phase: gives 2 phases only. Reject for 3-phase.
- 8 coils per phase at 45° pitch with 2p = 16: coil pitch = 2 pole pitches = 360° el. → outermost turn links zero net
  fundamental flux (k_p = sin 180° = 0); only inner turns contribute. Reject.
- **16 full-pitch coils per phase per layer pair** (coil pitch = τ_p = 22.5°, alternating CW/CCW = N/S under each coil), one
  layer pair per phase, phases B and C rotated by 2π/(3p) = 15° and 30° mech.: balanced by construction (k_d = 1, k_p of the
  outermost turn ≈ 1). This is the 3-phase extension of D15's 2-phase stepper, which places phase A on the upper four and
  phase B on the lower four layers with a 15° offset to enlarge each coil (D15 p.5 §2.1, `verified` statement). It needs at
  least three layer pairs (6 layers fit), and each phase then sits at a different z → per-layer EMF must be evaluated
  (G3); inductances of the middle and outer pairs differ (`inferred`). Option "B" in §2.4.

### 2.4 Candidate combinations and recommendation

Indicative ranking with the **existing, unvalidated** Xcoil v3 sector generator (repository annulus 18–38 mm, w/s
0.5/0.2 mm, 1 oz, one layer pair, double rotor, Br 1.3 T, 2 mm magnets, α_p 0.55 constant, 1.0 mm gap/side — all
`assumption`; `checks/sweep2.js`, run 2026-10-04). "kw1 (num)" is the engine's numerical utilisation factor
(Ke ÷ (series conductors × ∫B₁ r dr)), which includes spiral spread, radial coverage and the centre-via lead — it is not
the textbook k_w.

| Q/2p | sides | N max (engine) | kw1 (num) | Ke₁ per pair [mV·s/rad] | R₂₀ per pair [Ω] | Ke/√R |
|---|---|---|---|---|---|---|
| 12/16 | parallel | 8 | 0.600 | 29.28 | 2.988 | 16.94 |
| 12/16 | radial | 5 | 0.668 | 20.37 | 2.045 | 14.25 |
| 18/20 | parallel | 4 | 0.668 | 23.35 | 2.316 | 15.34 |
| 15/16 | parallel | 5 | 0.639 | 24.38 | 2.443 | 15.60 |
| 18/16 | parallel | 4 | 0.595 | 21.80 | 2.316 | 14.33 |
| 9/10 | parallel | 12 | 0.449 | 26.05 | 3.234 | 14.48 |
| 12/10 | parallel | 8 | 0.468 | 24.14 | 2.994 | 13.95 |
| 24/16 | parallel | 3 | 0.496 | 18.15 | 2.180 | 12.29 |
| 16/16, 1 phase (option B, per pair) | parallel | 5 | 0.632 | 77.10 | 7.513 | 28.13 |

(Option B uses a whole pair for one phase; for equal copper the FSCW per-phase figure across 3 pairs in series would be
16.94·√3 ≈ 29.3 — comparable, `inferred`, indicative only.) These numbers must not be read as performance claims
(brief rule 6).

Recommendation (`assumption`, to be confirmed by the user and by Phase 2 computation):
1. **Default: 12/16 FSCW, all phases on every layer.** Reasons: keeps the 16-pole rotor of the repository; t = 4 (symmetric,
   up to 4 parallel paths possible); coil pitch 1.33 τ_p so spiral turns straddle τ_p (K5); all coils have the same
   polarity (simplest series chain); larger coils → more turns and room for centre vias; satisfies D12's N_c/N_pm = m/(m+1)
   (EV-56); the D09 concentric board is the same combination — 12 non-overlapping spiral coils per layer, 2 layers, 6
   terminals, 1 mm gap, 16 poles (EV-62, `verified`; turns per coil ≈ 6–8 `unresolved`) — giving oracle O2 with measured R,
   L, EMF, torque (`evidence_register.md` §C). Caveats (DEF-08, DEF-11): D09 does not state the measurement temperature —
   R₂₀ from the published 3244 mm is 0.999 Ω, so the measured 1.07 Ω equals ≈38 °C if only temperature differed — nor the
   inductance measurement method; O2 therefore tests consistency, not accuracy (EQ-10, EQ-14). Drawback: k_w5 = k_w7 =
   0.866 → EMF harmonics follow the magnet-field harmonics (magnet shape must be chosen accordingly).
2. **Alternative A: 18/16** (k_w1 0.945, strong 5th/7th suppression, t = 2) — fewer turns (narrower coils), mixed polarity.
3. **Alternative B: phase-per-layer-pair 16/16** (render-like 16-coil artwork) — for evaluation against 12/16.
4. **Mandatory validation configurations**: 12/10 (D08, measured K_e, O1) and 12/16 (D09, O2); also 12/14 (D11, O9) once
   the star-of-slots bug is fixed.
5. The tool must accept any balanced Q/2p (rule 2.2) and report q, t, k_w,n, and balance; 24/16 and other Q/2p > 1 with
   small coil pitch should carry a "low spiral utilisation" warning (`inferred`, K5).

## 3. (c) Structure of a 3-phase spiral-coil stator

### 3.1 Coil shape options

| Option | Description | Pros | Cons | Evidence |
|---|---|---|---|---|
| S1 trapezoidal, radial (fanned) sides | Sides are radial lines; lateral spacing set at the inner radius | Conductors purely radial → full EMF per active length | Spacing grows with r → copper area unused near r_o | engine `coilSides: 'radial'`; EV-17; render style (inferred from image) |
| S2 trapezoidal, sides parallel to the sector edge | Constant perpendicular offset d per turn (D08 Fig. 3.4) | More turns for the same footprint | Sides inclined by asin(d/r) → cos α loss (D09 p.2 §2.1.2) | D08 p.33 (EV-02); engine `coilSides: 'parallel'` |
| S3 circular / racetrack (stadium) ends | Rounded end-turns, nested | Large corner radii, smooth current crowding | Less active length per turn (inferred) | D15 p.4 circular coils; render (inferred from image) |
| S4 hexagonal | Inclined sides + short radial part | D11 pull-force study | Lower radial share | D11 p.2–3 (EV-46) |
| S5 unequal width | Width grows with radius | Lower R, uses area at r_o | More complex DRC | D10 p.2–3 eq. 2–3 (EV-28) |

Recommendation (`assumption`): implement S1 and S2 sides × {arc, straight, stadium} ends, plus optional radius-dependent
width (S5) later.

### 3.2 Turns per layer, trace width and spacing

- Radial limit (`verified` formula, D08 p.43 [38] eq. 3.24, after Noh et al.): N_c < ½((r_o − r_i)/w_d + 1), w_d = w_tr +
  w_s (eq. 3.5). Example (`inferred` arithmetic): repository annulus 18–38 mm with 0.5/0.2 mm → N_c < 14.4.
- Lateral limit at the inner radius: D08 eq. 3.25–3.26 split trapezoidal and triangular turns (`verified`). A turn whose
  sides meet before r_i ("triangular") needs its inner end-turn moved outward. My derivation for track centre-lines gives
  i_max = (r_i sin(θ_cs/2) − w_d/2)/(w_d(1 − sin(θ_cs/2))) for loop index i, versus D08's form without the −w_d/2 term
  (`inferred`; the difference may be a different reference line).
- Centre-via room: pad + 2 × clearance inside the innermost loop, plus the lead from the innermost turn to the via
  (engine `sectorViaSpot`, `verified` code reading). For series stacks each extra layer pair needs one more centre via (§4.3).
- Spacing: IPC-2221 is cited only second-hand (0.13 mm "at our intended voltage", D03 p.4, EV-32; D18 p.10, EV-50) →
  any voltage-based clearance rule is `assumption, source needed` (G5).
- Concentric-loop vs true spiral (`verified (reproduced)` by `checks/r2.js`): D08's closed-form loop length exceeds the
  engine's spiral path (sides + ends + lead) by ≈3.7 % (8 turns) to ≈5.5 % (4 turns), because a spiral steps one pitch per
  turn and ends at a centre via.

### 3.3 Coil span vs pole pitch

- Span of turn t (parallel sides) at radius r: σ_t(r) = θ_cp − 2 asin(d_t/r), θ_cp = 2π/Q, d_t = (t + ½) w_d (D08 eq. 3.9–3.10
  geometry). Pitch factor per turn k_p,t = |sin(p σ_t/2)|; coil value = turn average (`inferred`: standard pitch factor
  applied per turn; consistent with D04 p.3 "inner coils … smaller pitch coefficient", EV-25).
- Rule (`inferred`): with Q/2p < 1 (e.g. 12/16, 18/20, 9/10) the outer turns are over-pitched and the inner ones near
  full pitch, so k_p stays high over many turns; with Q/2p > 1 every turn is short-pitched and inner turns contribute
  little (24/16 lowest in the sweep, §2.4).
- D08 eq. 3.27 prints θ_cs = π/p (the *pole* pitch); for 12 coils/10 poles the coil pitch is 2π/Q = 30°, not 36°; using
  36° would overlap neighbouring coils on one layer (`inferred`, geometric). See EQ-03 for the resistance consequence.

### 3.4 Phase belts, winding direction, connections, terminals

- **Conventions (fixed in the reconciliation round, `answers_to_agents.md` §1.4; `assumption` = design convention):**
  view from the F.Cu (L1) side, which faces rotor 1; world axes x right, y up, θ counter-clockwise; coil k (k = 0…Q−1,
  displayed as coil k+1) is centred at θ_k = θ₀ + k·2π/Q; a **positive coil carries positive phase current clockwise**
  seen from that side (layer X spirals inward clockwise); phases A, B, C end at line terminals U, V, W; with the rotor turning
  in +θ, the EMF of coil k lags by p·θ_k, so the star-of-slots belts (B at +120°) give the electrical sequence A→B→C
  (`inferred`, phasor arithmetic). The KiCad exporter flips y (KiCad y points down) without changing these definitions.
- Phase assignment: star of slots with 60° belts (§2.2), table in §2.2. For 12/16 phase A = coils 1, 4, 7, 10 (0°, 90°, 180°,
  270°), C = 2, 5, 8, 11, B = 3, 6, 9, 12, all positive (`verified (reproduced)` script output; swapping B and C reverses
  the rotation direction for the same terminal sequence).
- Winding direction: positive coils circulate one way (CW in the concept drawing), reversed ("lowercase") coils the other.
  With identical artwork the polarity is set by which outer terminal is the entry (Xcoil v3 `buildSector`, `verified` code
  reading; engine tests SEC-03/04 pass). Layer Y = mirror image of layer X traversed in reverse, giving the same
  circulation (D02 p.1, EV-01; engine test EMF-01 and my check C2 `verified (reproduced)`).
- Series/parallel per phase: series chain of all coils of a phase (default); parallel paths a ≤ t only between groups with
  identical EMF phasor **and** identical layer z, otherwise circulating current (D01 p.2–3 eq. 2, EV-20; D02 p.4–5, EV-35;
  `inferred` rule).
- Star vs delta: star default (`assumption`). Delta is unsafe where k_w3 ≠ 0 (12/14 k_w3 = 0.50, 18/16 0.577,
  `checks/kw.py`) because triplen EMF drives a circulating current around the mesh (`inferred`; the engine computes a
  resistance-limited estimate, `applyConnection`). For 12/16 k_w3 = 0.
- Terminals: three line terminals U, V, W (+ optional neutral pad) on the outer rim, outside r_o, as in Xcoil v3 and the
  repository (terminal lands at r ≈ 45.5 mm, EV-R2) (`assumption`); hub terminals (render) conflict with the shaft bore and
  the inner end-turns (`inferred`).

## 4. (d) Multi-layer configuration

### 4.1 Continuation across layers

- Basic pair (`verified`, D02 p.1 EV-01; D14 p.4 EV-40): layer X spirals outer → inner, centre via, layer Y spirals inner →
  outer with mirrored artwork; both coil terminals end at the outer rim.
- Further pairs: either **parallel** (all X layers in parallel, all Y layers in parallel through one shared centre via —
  what Xcoil v3 does, warning `PAIRS_PARALLEL`) or **series** (pair k's outer end → outer transfer via → pair k+1 spirals
  in → its own centre via → out …). Series is used by D11 ("coils in different layers are serial connected", p.4) and in
  groups by D10 (2 groups × 6 parallel layers in series, p.3, EV-28) (`verified` statements).

### 4.2 Stacking options

| Option | Description | Via implication (`inferred`) | EMF/loss implication |
|---|---|---|---|
| M1 same footprint, all pairs in parallel | Engine default | 1 centre via per coil (through) | Circulating current from per-layer EMF differences (G3); computed by the engine per layer z |
| M2 same footprint, pairs in series | Needs one centre via per pair and one outer transfer via between pairs | n_pairs through-vias in each coil eye (each clear on the layers it does not join) + (n_pairs − 1) transfer vias at the coil rim; or buried L1–L2/L3–L4/L5–L6 vias (cost) | Phase EMF = sum of pair EMFs at their z; no circulating current |
| M3 layer groups rotated by half a coil pitch | Group 2 shifted by π/Q (15° for Q = 12) | Coil-centre vias of group 1 land on the inter-coil gaps of group 2 and vice versa → through-vias become possible if the inter-coil gap ≥ via pad + 2 clearances | For 12/16 the shift is 120° el. → pure phase permutation, k_w unchanged; for 12/10 and 12/14 the combined 24-position winding lowers k_w1 0.933 → 0.925 but cuts k_w11/k_w13 0.933 → 0.122 (`checks/kw.py`) |
| M4 phase per layer pair (option B) | Each pair carries one phase, pairs rotated by 2π/(3p) | Coil eyes of one phase overlap active sides of the others → via positions must be planned jointly | Phase EMFs differ by layer z (small for thin symmetric double rotor, larger otherwise) |

Rules (`inferred`): a group rotation must keep the via grid common to all layers when only through vias are allowed
(the repository's 15° = 6 × 2.5° does so, §1.1); groups must contain whole X/Y pairs.

### 4.3 Via requirements

- Via barrel resistance R = ρ l /(π(2rt − t²)) (D05 p.6–8 eq. 3–6, EV-37); plating 25 µm assumed in D05 (`verified`);
  current crowding at the inner via of a spiral is the likely hot spot (G7, `inferred`) → allow several vias per transition
  (D05 multi-via, EV-38, FEA only).
- Each coil needs ≥ 1 centre via per series pair and ≥ 1 transfer via per series step; via pads displace turns from the
  coil eye, reducing N (`inferred`). Winding-via count for any series/parallel grouping: `answers_to_agents.md` §3.1.
- Patent attention (G25, `ecm_pcb_stator_evidence.md` R5; `inferred — legal review needed`, not a legal opinion): ECM
  US 11,336,130 claims layers joined in series with all inter-layer vias on one radial side outside the active region, with a
  dependent claim to spiral windings (EV-65). The M2 plan above keeps centre vias inside each coil eye, i.e. inside the
  active annulus; a variant with all vias moved outside the annulus should stay a switchable option, not a default, until
  reviewed by a patent attorney.

### 4.4 Per-layer flux linkage (G3) and how the engine evaluates it

- Evidence conflict (`verified`, G3): D15 p.8 assumes equal flux for all layers (EV-43); D01 p.2–3, D02 p.4–5, D13 p.3 show
  layer-dependent EMF.
- Xcoil v3 evaluates the field for every copper layer at z_mag = z_layer + airgap from the magnet face
  (`analyzeElements`/`analyze`, `verified` code reading), with a cosh(u(G − z)) profile for the double rotor
  (G = (t_stator + 2g)/2, mirror beyond the mid-plane) and e^(−uz) for an open single rotor (engine tests FLD-02/03 pass;
  my checks C1/C2 in `existing_logic_review.md` §3, `verified (reproduced)`). Series layers therefore sum per-layer EMFs,
  parallel layers produce a conductance-weighted terminal EMF and a circulating loss.
- Magnitude example (computed with the engine field, not validated): p = 8, r = 28 mm, 6 × 1 oz layers in a 0.62 mm board,
  1.0 mm gap per side, double rotor → fundamental B_z = 0.6828 T (outer layers) vs 0.6805 T (middle layers), a 0.34 %
  spread. The spread grows with board thickness, single-sided rotors and higher pole counts (`inferred`, u = n p / r).
  Accuracy of the 2-D z-profile against 3-D FEA: `unresolved` (Agent 4 test).

## 5. (e) Information sufficiency and default design assumptions

### 5.1 Missing information (`unresolved` unless stated)

| Topic | What is missing |
|---|---|
| Rotor | single vs double rotor; magnet orientation (is the 20 mm side radial?), grade/Br, µ_r, back-iron material and thickness, N–S vs N–N facing; arc-segment vs block magnets |
| Poles | 16 magnets "to start" (README) — final pole count open |
| Air gap / axial build | mechanical clearance per side; stator board thickness (Altium record 0.62 mm may be a template, `repo_survey.md` §1.5) |
| Operating point | supply voltage (inverter DC link), rated speed, rated current/torque, duty, cooling, ambient |
| Manufacturing | min trace/space and via for the chosen fabricator, max layers, copper weight, blind/buried vias allowed?, cost limits (D09 p.3 §2.2: >6 layers cost rises sharply, supplier-specific, EV-16) |
| Electrical | connection (star/delta), terminal type/location, sensor needs (Hall?), insulation voltage |
| Validation | none of the corpus cases is a >2-layer 3-phase spiral stator with measured R, L, EMF (G2) |
| Render | true topology of the render (K2); dimensions (none may be read) |

### 5.2 Default design (all `assumption` — for the first computed reference case only)

| Parameter | Default | Basis |
|---|---|---|
| Topology | FSCW spiral coils 12/16, all phases on every layer, star | §2.4 |
| Rotor | double-sided, N facing S (through flux), 16 NdFeB blocks 20 × 6 × 2 mm, 20 mm radial over r = 18–38 mm, grade N42: B_r 1.315 T typical (1.28 T min), α(B_r) −0.12 %/°C; µ_r 1.05; steel back iron ≥ 3 mm (unsaturated) | repository README; B_r and α from the Arnold N42 sheet (EV-55, extract); grade itself `assumption`; µ_r not found in any datasheet (G23; apparent slope ≈ 1.10, `inferred`) → `assumption`, sensitivity 1.03–1.10 |
| Gap | 1.0 mm per side | assumption |
| Stator | 6 layers, 1 oz (34.8 µm), 0.62 mm (record) — treat as parameter | repo_survey §1.5 |
| Coil | S2 sides, arc ends, w 0.5 mm, s 0.2 mm, coil gap 0.2 mm, through vias 0.3/0.5 mm | repository + assumption |
| Layer connection | 3 pairs; series (M2) preferred, parallel (M1) as fallback; rotation M3 optional | §4 |
| Outline | Ø25 mm bore, 12-gon 93 mm flats, 12 × Ø3.1 mm at r = 45 mm | repository |
| Temperature | 20 °C reference, 60 °C operating for R | assumption |
| Copper constants | ρ₂₀ = 1.7241e-8 Ω·m, α₂₀ = 0.00393 /K, density 8.89 g/cm³ | IACS / IEC 28 via NBS Handbook 100 (EV-53, `verified` for annealed copper); PCB copper = IACS is an `assumption` (G6) |

## 6. Separation of statements

- **Verified facts**: repository contents (K1, EV-71 parse); render provenance; definitions and statements cited in §1.3;
  D08 eq. 3.24, 3.3, 3.27 as printed; D07 p.3 slot → coil-side rule; D12 eq. 1; D15 p.5 layer-group phase offset and p.7
  eq. 6; D09 board = 12 coils/layer, 2 layers, 6 terminals (EV-62); copper constants (EV-53); reproduction of D08's 12/10
  pattern; engine behaviours K6, K7 (reproduced).
- **Inferred conclusions**: 16-coil analysis (§2.3); 15° = 120° el. phase permutation in the repository; Q/2p < 1 rule;
  M3 via compatibility; delta risk for k_w3 ≠ 0; render ambiguity (K2).
- **Design assumptions**: default design §5.2; candidate ranking §2.4; star default; outer-rim terminals.
- **Unresolved**: render topology (D5 below); rotor data (D1, D2); FSCW textbook content (G24); magnet µ_r (G23); D09
  turns per coil (6–8); per-layer z-profile accuracy vs 3-D FEA; via crowding; inductance (G1 — D10-vs-D15 conflict
  resolved, closed form still unvalidated); D08 air gap 1.4 vs 2.8 mm (G10; my field check in `existing_logic_review.md`
  C1b favours 1.4 mm per side for D08 Fig. 3.3 — inferred from figure reading); patent overlap (G25, legal review).

## 7. Decisions the user must make

Each line: decision → consequence of each choice (all consequences `inferred` from §2–§5 unless marked).

| # | Decision | Consequence |
|---|---|---|
| D1 | Keep the 16-magnet rotor (20 × 6 × 2 mm blocks)? | **Yes** → default 12/16 (or 18/16, 16/16 per pair); block magnets need the α_p(r) model (EQ-04), α_p falls from 0.85 to 0.40 across the annulus. **No** → free choice of 2p and magnet shape (e.g. arc segments, 18/20, 12/10 for direct comparison with D08); rotor design becomes part of the task. |
| D2 | Single or double rotor? | **Double** → symmetric field, smallest per-layer EMF spread (0.34 % in the default stack, C1d), no axial pull on the stator, two rotor parts. **Single + opposite yoke** → simpler rotor, strong axial pull on the stator/yoke. **Single, no yoke** → weakest field, e^(−uz) decay → larger layer-to-layer EMF differences (parallel layers then circulate current, EQ-07). |
| D3 | Blind/buried vias acceptable? | **Yes** → series layer pairs (M2) without stacking several through-vias in each coil eye → more turns per coil; higher PCB cost (supplier quote needed, D09 p.3 notes cost steps for >6 layers). **No (through vias only)** → M2 needs n_pairs centre vias per eye (fewer turns) or parallel pairs (M1) with circulating-current risk; the M3 half-pitch rotation can place vias in the other group's coil gaps. |
| D4 | Target supply voltage, speed, torque (and cooling) | Sets turns per coil, series/parallel grouping and star/delta (Ke·ω must stay below the inverter voltage, EQ-09/EQ-20); without them the tool can only report per-turn constants. Thermal limits (EQ-17) need the cooling condition. |
| D5 | Render = exact target or style reference? | **Exact target** → may require a wave/serpentine option (the render and EV-71 are compatible with a wave path), outside the decided spiral-coil scope; patent attention to ECM serpentine claims (G25). **Style reference** → concentrated spiral coils as decided, with fanned sides / stadium ends / optional rotated layer groups as visual options. |
| D6 | Star or delta? (default star) | **Star** → triplen EMF does not circulate; 3 terminals + optional neutral. **Delta** → √3 lower Ke per line for the same winding, but combinations with k_w3 ≠ 0 (12/14, 18/16) drive circulating current (EQ-19). |

---

**Revision 2026-10-04 (defect fixes):** DEF-11 (K4 now states the D09 coil count as `verified` (EV-62, Agent 4's own count);
O2 temperature and inductance-method caveats added in §2.4). Oracle parameter sets: `oracle_cases_draft.json`.
