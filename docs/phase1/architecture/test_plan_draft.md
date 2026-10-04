Prepared by: Agent 6 — Software Architecture Specialist — model: claude-opus-5-5

# embodic — Test strategy and plan (Phase 1 draft, 2026-10-04)

Status: **draft**; no test has been written or run for embodic (status of every embodic test below: `not tested`).
Strategy decision: ADR-0006. Requirements: `requirements_draft.md`. Architecture: `architecture_draft.md`.
Reference values quoted from Agent 2 are computed values from analytical formulas or from the unvalidated Xcoil engine
(A2-REV §3) — never measurements (BRIEF §3 rule 5); values from papers marked "meas." are the papers' measurements.

## 1. Strategy overview

| Level | Purpose | Tooling (licence per PyPI/npm, `verified` 2026-10-04) | Runs in |
|---|---|---|---|
| Unit (UT) | Module behaviour and invariants | pytest (MIT), pytest-cov (MIT) | CI, every commit |
| Golden regression (GR) | `reuse` equations behave exactly like Xcoil v3 | Node.js harness (dump) + pytest (compare) | CI (compare); dump on demand |
| Oracle (OR) | Agreement with published cases / closed forms within stated tolerance | pytest | CI |
| Property / fuzz (PR) | Generic correctness over random inputs | Hypothesis (MPL-2.0) | CI fast profile; nightly long profile |
| Boundary / invalid (BV) | Equivalence classes and edges produce documented issues | pytest parametrised | CI |
| UI (UI) | View-model and widget behaviour headless | pytest-qt (MIT) with an offscreen Qt platform (if ADR-0005 C-A) or Playwright (Apache-2.0) (if C-B1) | CI |
| KiCad export (KX) | Files parse and match the layout; adapter mapping correct | kiutils (GPL-3.0, test-only), sexpdata (BSD) backup parser, ezdxf (MIT), pypdf (BSD-3) | CI |
| KiCad smoke (KS) | Real KiCad 9.x behaviour | manual checklist on the user's Windows machine | P2 milestones |
| Language (LG), Accessibility (AX) | REQ-L, REQ-N-11…16 | custom scripts; Narrator/manual checklist | CI + manual |
| Performance (PF) | REQ-N-01…03, N-22 | `time.perf_counter` harness (pytest-benchmark BSD-2-Clause optional) | CI (regression guard) + reference laptop |
| Maintainability (MT), Packaging (PK), Traceability (TR) | Static gates, install/bundle, matrix | import-linter (BSD), mypy (MIT), ruff (MIT), pip-licenses (MIT), pip-audit (Apache-2.0) | CI |

Pyramid target (`assumption`): ≈ 70 % unit + golden, ≈ 20 % property/boundary/oracle, ≈ 10 % UI/export/integration; manual
tests only for KiCad-in-the-loop and screen-reader checks.

Test ID scheme: `<LEVEL>-<AREA>-<nn>` for unit tests (e.g. `UT-GEO-01`), `<LEVEL>-<nn>` otherwise. Every automated
test carries `@pytest.mark.req("REQ-…")` and, for physics, `@pytest.mark.eq("EQ-…")` (REQ-T-09).

## 2. Unit tests (UT)

### 2.1 Geometry (`embodic.geometry`) — REQ-F-01, F-03…06, F-09, F-19, N-21

| ID | Check | Criterion |
|---|---|---|
| UT-GEO-01 | Every `CopperPath` is continuous | end of primitive i = start of i+1 within 1e-6 mm (Xcoil GEO-01 tolerance) |
| UT-GEO-02 | Fillets/corners tangent-continuous when corner radius > 0 | heading mismatch ≤ 1e-6 rad |
| UT-GEO-03 | Layer Y = mirror of X about the coil axis | every Y point mirrored back lies on X within 1e-9 mm |
| UT-GEO-04 | Centre via terminates X and Y | distance ≤ 1e-9 mm |
| UT-GEO-05 | X and Y have equal circulation (signed area sign) | same sign; magnitudes within 1e-9 rel. for identical artwork |
| UT-GEO-06 | Coil k = coil 0 rotated by 2πk/Q (+ pair rotation) | all primitive points coincide within 1e-9 mm |
| UT-GEO-07 | Generated coil length vs EQ-03 closed form | within ±6 % (A2-EQ EQ-03 tolerance) for the C4 cases (12 and 18 coils, r 18–38 mm, 0.5/0.2 mm) |
| UT-GEO-08 | Moving inner end-turn (triangular turns) | D08 geometry: no turn self-intersection; inner end-turn radius increases monotonically once sides converge |
| UT-GEO-09 | Turn limit | returned max N is buildable and N + 1 is not (boundary) |
| UT-GEO-10 | Series (M2) and parallel (M1) pair configurations build for the default design | circuit groups match `series_groups`; via counts per §7.3 formula |
| UT-GEO-11 | Pair rotation π/Q | group-2 centre vias lie in group-1 inter-coil gaps (angular distance to nearest coil axis = π/Q ± 1e-9) |
| UT-GEO-12 | Stack-up z | z_i = Σ thickness above + t_i/2, exact |
| UT-GEO-13 | Via plan count and spans | default design: 60 winding vias (M2) / 36 (M1) per architecture_draft.md §7.3 (`assumption` formula) |
| UT-GEO-14 | Outline closed, bore and holes placed | closed loop within 1e-9 mm; hole centres at specified radius |
| UT-GEO-15 | Determinism | two builds → identical `layout_hash` |
| UT-GEO-16 | Polarity −1 coils reverse current direction, not artwork | signed Δr of radial sides inverted; geometry identical |
| UT-GEO-17 | Side styles | radial: side line passes through origin within 1e-9 mm; parallel: constant offset d_t |
| UT-GEO-18 | End styles arc / straight / stadium | end primitives of the expected type; continuity holds |
| UT-GEO-19 | Phase-per-pair (M4) | each pair contains coils of exactly one phase; pairs rotated by 2π/(3p) |
| UT-GEO-20 | Generator interface | a stub test generator registered at runtime passes through DRC, physics and all writers unchanged (REQ-F-19) |
| UT-GEO-21 | Fastener holes | holes at specified radius/count; edge, pitch and copper keep-out violations reported (REQ-F-24) |

### 2.2 Winding (`embodic.winding`) — REQ-F-02, F-03, F-08

| ID | Check | Criterion (source) |
|---|---|---|
| UT-WND-01 | 12/10 pattern | "AabBCcaABbcC" (D08 p.36 Fig. 3.7; reproduced by A2 `checks/kw.py`, `verified (reproduced)`) |
| UT-WND-02 | **Star-of-slots belt-edge regression** | 12/14, 24/14, 24/22, 24/26 reported balanced with 4/4/4, 8/8/8 … coils per phase (Xcoil bug A2-REV C6 must not recur) |
| UT-WND-03 | 12/16 pattern | "ACBACBACBACB", all positive (A2-TOP §2.2) |
| UT-WND-04 | 16/16 three-phase | rejected `UNBUILDABLE_UNBALANCED_WINDING` |
| UT-WND-05 | k_w1/k_w5/k_w7 table | A2-TOP §2.2 values (12/10 0.933 …) to 1e-3 as printed; recomputed exact values to 1e-9 vs an independent implementation (Agent 4) |
| UT-WND-06 | q and t | exact `Fraction` q; t = gcd(Q, p) for all Q ≤ 48, 2p ≤ 48 |
| UT-WND-07 | Delta with k_w3 ≠ 0 | 12/14 delta → `RANGE_DELTA_TRIPLEN`; 12/16 delta → no warning (k_w3 = 0, A2-TOP §3.4) |
| UT-WND-08 | Parallel paths a ≤ t | a = t accepted, a = t + 1 → `UNBUILDABLE_PARALLEL_PATHS_EXCEED_T` |
| UT-WND-09 | Manual assignment override | unbalanced manual assignment accepted with warning and balance metric shown |
| UT-WND-10 | Balanced-list helper | for 14 poles includes 12 and 24 (A2-REV C6 regression of `balancedSectorList`) |

### 2.3 Physics (`embodic.physics`) — REQ-F-07, F-11, F-12, T-08 (re-run of A2 checks C1–C9)

| ID | EQ | Check | Reference / criterion |
|---|---|---|---|
| UT-PHY-01 | EQ-05 | 1-D limit (C1a: r = 1e7 mm, B_r 1.30 T, l_m 3 mm, µ_r 1.05, α_p 0.85, G 2 mm) | B₁ = 0.946752 T, rel. 1e-9 |
| UT-PHY-02 | EQ-04 | Block α_p(r) 20 × 6 mm, 2p 16 | 0.853 / 0.547 / 0.402 at r 18/28/38 mm (±5e-4) |
| UT-PHY-03 | EQ-05 | D08 rotor, µ = 1 (C1b) | B₁ = 1.1952 T (1.4 mm) and 0.9336 T (2.8 mm), ±1e-4 |
| UT-PHY-04 | EQ-05 | Rotor types: G for double, single+yoke, open | formulas of EQ-05; open-rotor limit e^{−uz} form to 1e-12 |
| UT-PHY-05 | EQ-06 | 1-turn sector coil closed form (C2, 12/10, 2 layers) | Ke₁ = 5.410812e-3 V·s/rad, rel. 1e-4 (A2-EQ tolerance for idealised geometry) |
| UT-PHY-06 | EQ-06 | Only radial components contribute | circumferential arc at constant r → zero EMF (≤ 1e-15) |
| UT-PHY-07 | EQ-07 | Series chain = phasor sum of pair EMFs at own z | rel. 1e-9 |
| UT-PHY-08 | EQ-07 | Two-member identity | P_c = abs(E₁ − E₂)² / (2(R₁ + R₂)) to 1e-12 |
| UT-PHY-09 | EQ-09 | Star/delta identities | Ke,LL = √3 Ke,ph (star), = Ke,ph (delta); T ω = m E_rms I_rms to 1e-9 |
| UT-PHY-10 | EQ-10 | 1000 mm × 0.5 mm × 34.8 µm (C3) | 0.99080 Ω (20 °C), 1.14656 Ω (60 °C), rel. 1e-5 |
| UT-PHY-11 | EQ-11 | Via barrel drill 0.3, plating 25 µm | A = 0.021598 mm²; l 0.2 mm, 20 °C → 0.160 mΩ (C9) |
| UT-PHY-12 | EQ-12 | One radial trace example (C9) | 7.23e-5 W (adopted /24 form), rel. 1e-3 |
| UT-PHY-13 | EQ-13 | Skin depth 133.3 Hz, 20 °C → 5.72 mm; w > δ/3 → `RANGE_SKIN_DEPTH` flag on R and eddy results | ±0.01 mm; flag present |
| UT-PHY-14 | EQ-05/14/16 | Rotor-type consistency (A2-REV Q-3) | the same `RotorType` drives field, inductance estimate and inertia; open rotor has no yoke in any model |
| UT-PHY-15 | EQ-15 | 0.5 mm × 34.8 µm, ΔT 20 K | 1.955 A ext / 0.977 A int; status `unresolved`, label "guideline (unverified)" |
| UT-PHY-16 | EQ-17 | D08 4 W × 5.11 K/W | 20.44 K (arithmetic check of the lumped form) |
| UT-PHY-17 | EQ-21 | 4 W, 0.39 Ω | 1.849 A |
| UT-PHY-18 | EQ-14 | Estimate labelling | status `unresolved`, quantity labelled "estimate"; value equals the documented formula (C9: 4.67 / 9.74 µH for the stated inputs) |
| UT-PHY-19 | EQ-18 | THD of a pure fundamental = 0; line waveform cancels triplens in star | ≤ 1e-12 |
| UT-PHY-20 | EQ-05 | Per-layer spread (C1d) | B₁ 0.6828 / 0.6813 / 0.6805 T, rel. 1e-4 |

### 2.4 DRC (`embodic.drc`) — REQ-F-10

| ID | Check | Criterion |
|---|---|---|
| UT-DRC-01 | Default design measured min trace–trace clearance | within 0.005 mm of the set clearance (Xcoil DRC-01 criterion) |
| UT-DRC-02 | Exact distance kernels | line–line, line–arc, arc–arc vs dense brute-force sampling: exact ≤ sampled + chord bound, ≥ sampled − 1e-9 |
| UT-DRC-03 | Fault injection | moving one turn 1 µm inward produces exactly one new violation with correct location |
| UT-DRC-04 | Connectivity exemption | adjacent primitives and terminating vias exempt; non-adjacent turns of the same spiral (same net) **checked** |
| UT-DRC-05 | Through-via vs other layers | via of pair 1 against copper of pairs 2–3 checked on all spanned layers |
| UT-DRC-06 | Copper–edge and copper–hole | violation when within edge clearance |
| UT-DRC-07 | Manufacturing minima | min width, drill, annular ring violations reported |
| UT-DRC-08 | Grid vs brute force | identical results on 50 random small layouts |

### 2.5 Results, IO, units, CLI, logging

| ID | Check | REQ |
|---|---|---|
| UT-RES-01 | No bare floats in `AnalysisResult`; every field Traceable with ≥ 1 EQ-ID; all IDs resolve | T-02, T-04 |
| UT-RES-02 | `combine_status` truth table (all 5 statuses, validity cap, defaults as assumption, `cannot verify yet` → unresolved) | T-03, T-05 |
| UT-RES-03 | Registry integrity (no dangling EQ/EV IDs; every entry has a source) | T-04 |
| UT-RES-04 | Unit vocabulary and display forms ("V·s/rad", "Ω", "A/mm²") | N-21, L-07 |
| UT-IO-01 | Save → load → save byte-identical | F-15 |
| UT-IO-02 | Canonical JSON and hash stable across runs/platforms | F-15, N-04 |
| UT-IO-03 | Example files validate against the published JSON Schema; loader and schema agree on 50 mutated files | F-15 |
| UT-IO-04 | Migration v1 → v2 (synthetic v2 in tests) with info issue; newer version refused | F-15 |
| UT-IO-05 | Provenance persists (defaults stay `assumption` until edited) | T-06 |
| UT-IO-06 | Export metadata (version, registry version, hash, date, statuses) in every writer | T-07 |
| UT-UNI-01 | deg↔rad, mm↔m, rpm↔rad/s round trips | N-21 |
| UT-UNI-02 | mm→nm rounding (half cases, negatives) | K-08 |
| UT-UNI-03 | Locale-independent formatting under de_DE/th_TH locale settings | L-07 |
| UT-CLI-01 | `compute` JSON equals API result; exit codes 0/1/2/3 | F-18 |
| UT-LOG-01 | Log header content; no user name/home path; rotation | N-20 |

## 3. Golden regression against the Xcoil v3 JS engine (GR) — ADR-0006

**Why function-level:** the embodic spiral generator intentionally differs from Xcoil's sector generator (EQ-02, EQ-08
`replace`; A2-TOP K7), so whole-design numbers must differ. Golden tests therefore feed **identical inputs** to the JS
function and its Python counterpart (`inferred`, architecture_draft.md §17 R8).

**Harness:** `tools/golden_js/dump_reference.mjs` (Node ≥ 22) `require`s `/home/claude/serpentine/src/engine.js`
read-only, evaluates each function on a fixed input set, and writes `tests/golden/data/xcoil_v3_<name>.json`:

```json
{"engine_file": "serpentine/src/engine.js", "engine_sha256": "<hex>", "node": "v22.x",
 "generated_utc": "...", "function": "fieldHarmonic",
 "cases": [{"inputs": {"n": 1, "r_mm": 28.0, "z_mm": 1.31, "...": "..."}, "outputs": {"bz_t": 0.0, "bt_t": 0.0}}]}
```

The Python test loads the JSON, converts units/conventions explicitly (documented per case), calls the embodic
function and compares with rel. tolerance 1e-9 (Xcoil's own golden tolerance, `golden-check.js` l.25) unless stated.
Primitive lists for EMF/resistance cases are exported from Xcoil's `buildSector` in the same JSON so both engines integrate
the same copper.

| ID | EQ (gate) | JS function(s) (engine.js line, A2-REV §1) | Inputs | Tolerance |
|---|---|---|---|---|
| GR-01 | EQ-01 (reuse) | `derive` / `deriveSector` pole and coil pitch | 2p ∈ {10, 14, 16, 20}, Q ∈ {9, 12, 15, 18, 24} | exact |
| GR-02 | EQ-10 (reuse) | `copperResistivity` l.80, `traceResistance` l.102, `primsResistance` l.97 | T ∈ {−20, 20, 60, 120} °C; fixed primitive lists | 1e-9 |
| GR-03 | EQ-05 (reuse with change; unchanged part = constant α_p) | `fieldHarmonic` l.856, `fieldSetup` l.868 | n ∈ odd 1…13, r ∈ {12, 18, 28, 38, 44} mm, z grid, 3 rotor types | 1e-9 |
| GR-04 | EQ-06 (reuse) | `analyzeElements` l.1846 — λ_n per element | Xcoil sector elements: 12/10 1-turn (C2), 12/16 8-turn, 18/16 | 1e-9 |
| GR-05 | EQ-07 (reuse with change; unchanged = parallel members) | `analyzeElements` parallel members, circulating loss | 2 and 3 parallel layer members at different z | 1e-9 |
| GR-06 | EQ-09 (reuse) | `applyConnection` l.1398 | star/delta/open, 3 Ke/R sets | 1e-9 |
| GR-07 | (stack-up, reuse with change) | `stackupFor` l.1156 auto + custom | 2, 4, 6, 8 layers; custom list | 1e-12 mm |
| GR-08 | EQ-11 (reuse with change; unchanged = barrel area) | `viaBarrelArea` l.92 | drill 0.2–0.6, plating 15–35 µm | 1e-12 |
| GR-09 | EQ-12 (reuse) | eddy part of `analyzeElements` | elements without primitives exactly on the magnet edge | 1e-9 (edge case tested separately: Xcoil v1/v2 differed by up to 3 %, `golden-check.js` l.23–25) |
| GR-10 | EQ-13 (reuse) | `skinDepthMm` l.81 | f 10 Hz–10 kHz, T 20/100 °C | 1e-12 |
| GR-11 | EQ-18 (reuse) | `emfWaveform` l.1020, `lineWaveform` l.1441 | harmonic sets from GR-04 | 1e-9 |
| GR-12 | EQ-22 (reuse) | current density in `analyzeElements` | 3 cases | 1e-12 |
| GR-13 | EQ-16/17 (reuse with change; unchanged = same densities and h) | `massThermal` l.1378 | 3 boards | 1e-9 |
| GR-14 | EQ-19 (reuse with change; unchanged = resistance-limited) | delta circulation in `applyConnection` | 12/14 delta | 1e-9 |
| GR-15 | interconnect R (reuse) | `interconnectResistance` l.1361 | ring/stub sets | 1e-9 |
| GR-16 | EQ-14 (cannot verify yet) — **characterisation only** | `windingInductance` l.2617 | C9 case | 1e-9; documents behaviour, is not evidence of correctness; must not raise the EQ status |

Rules: (1) a golden failure blocks merge; (2) intentional deviations (e.g. a fixed defect) are recorded in the test with
reason and A2/A4 sign-off; (3) the JSON fixtures are committed so CI needs no Node.js; (4) the dump script never writes into
`/home/claude/serpentine/`.

Refinements adopted from Agent 3's harness design (`docs/phase1/software/calculation_flow_and_port_notes.md` §2–§3, §7;
measurements `verified (run)` there, tolerances `assumption` pending Agent 4):
- **Two tiers**: JS → plain-Python *reference port* (line-by-line, readable specification) → NumPy *production kernels*.
  The reference port is compared with the JS dumps; production kernels are compared with the reference port on many more
  inputs. Both comparisons use the tolerance map below.
- **Tolerance map**: discrete outputs (codes, counts, structure) exact; scalar kernels rel. 1e-12 (Agent 3 measured max
  1.6e-15 for `fieldHarmonic`); integrated results rel. 1e-9; geometry by sampled path distance ≤ 1e-6 mm; DRC values
  abs. 1e-6 mm; exported text compared as parsed numbers on the writer's grid (1e-5 mm in Xcoil's `fmt()`).
- **Near-threshold rule**: a mismatch in a discrete decision whose margin is < 1e-9 relative (discretisation counts,
  magnet-span membership, turn limits, DRC pass/fail; Agent 3 §2.3 list) is logged as "indeterminate", not failed.
- **Non-finite values** are encoded explicitly in the JSON fixtures (`{"$f": "inf"}` etc.); Xcoil results contain 1–6
  non-finite numbers per configuration (Agent 3, `verified (run)`).
- **Whole-configuration dumps** (optional, for the unchanged equation paths only) must use `{"interconnect": false}`:
  Xcoil's own golden check passes only with that override (Agent 3 `feature_inventory.md` §0, `verified (run)`).
- An **expected-differences allow-list** records each intentional deviation with EQ-ID and reason (e.g. EQ-08 integer star
  of slots: 12/14 now balanced; EQ-04 α_p(r)).
- **Constants**: embodic adopts ρ₂₀ = 1.7241e-8 Ω·m (EV-53) and copper density 8.89 g/cm³, Xcoil uses 1.724e-8 and 8.96
  (Agent 2 `answers_to_agents.md` §2.1) → golden cases inject Xcoil's constants explicitly; the embodic values are tested
  by UT-PHY/OR tests. Known Xcoil defects are not reproduced (expected-differences list).
- **Spiral generator closed forms** (no Xcoil counterpart): Agent 2's cases G1 (D08: 1 trapezoidal + 2 triangular loops,
  177.233 mm per coil-layer), G2 (default 12/16: 9 + 2 loops; N = 8 → 379.578 mm), G3 (18/16: 5 + 3 loops; N = 4 →
  195.199 mm) from `docs/phase1/engineering/checks/eq02_eq03_reference.py`; tolerances: loop counts exact in concentric
  test mode / ±1 for the true spiral, lengths 1e-3 mm vs the closed form, generated spiral within −6 … 0 % (Agent 2 §2.2).

## 4. Oracle cases (OR)

Tolerances below are Agent 2's current values where given (A2-EQ); final values are **to be set by Agent 2/4**.
Prerequisites must be met before an oracle can pass; until then the test is marked `xfail(reason=…)` and the EQ cannot be
`verified` (ADR-0003).

| ID | Oracle (A5-REG §C) | Quantity | Published value | Tolerance (source) | Prerequisites / blocking gaps |
|---|---|---|---|---|---|
| OR-01 | O1 D08 thesis | Line-line peak back-EMF constant | 0.031 V·s/rad, meas. (Table 9.1 p.98) | ±8 % (A2-EQ EQ-06: D08's own model within max 8 %) | EQ-04 T-arrangement magnets; air gap 1.4 vs 2.8 mm (G10); compare synthesised waveform peak, not fundamental (EQ-09) |
| OR-02 | O2 D09 Tokgöz | Phase DC resistance | 1.07 Ω, meas. (Table 6 p.7) | ±8 % (A2-EQ EQ-10) | turns per coil and coil count (G2, task T-D) |
| OR-03 | O3 D10 Wang 2019 | Phase DC resistance | 2.15 Ω, meas. (p.8) | ±8 % (A2-EQ EQ-10) | unequal-width concentric geometry (S5, reserved) → Later |
| OR-04 | O1 D08 | Turns per coil | 3 (Table 4.6 p.57) | exact vs EQ-02 rule; ±1 vs constructive generator (A2-EQ EQ-02) | moving inner end-turn (REQ-F-06) |
| OR-05 | O1 D08 | Phase resistance (calc. in paper) | 0.39 Ω (Table 4.6 p.57); A2 reproduction 0.381 Ω (C7) | to be set by Agent 2/4 (A2 residual −2.3 %, ρ₂₀/α of D08 unknown) | EQ-03 one pair of sides per loop |
| OR-06 | O1 D08 | Copper-loss-budget current | 1.84 A (Table 4.6); A2 1.849 A | to be set (A2: reproduced) | — |
| OR-07 | O2 D09 | Phase EMF | calc. 6.21 V / FEA 6.20 V RMS (Tables 4–5 p.6) | ±5 % (A2-EQ EQ-06) | turn data (G2) |
| OR-08 | O2 D09 | Field at mid-radius | ≈ 0.72–0.75 T (figure readings, `inferred`) | ±5 % (A2-EQ EQ-05) | µ_r assumption |
| OR-09 | O2 / O5 | Inductance | 14.8 µH (D09 Table 6), 22.3 µH (D07 Table 4), meas. | **none** — characterisation only (EQ-14 `cannot verify yet`) | G1 |
| OR-10 | O3 D10 | Temperature at 12 A/mm² | 110.2 °C at 27 °C ambient, meas. (p.10) | ±30 % on ΔT (A2-EQ EQ-17, `assumption`) | conduction path model → Later |

## 5. Property and fuzz tests (PR) — Hypothesis

| ID | Property | REQ |
|---|---|---|
| PR-01 | **DRC soundness**: whenever a layout is produced and `drc.passed`, an independent brute-force checker (Agent 4) finds no non-exempt pair closer than the rule − 1e-6 mm; conversely every violation found by the checker is reported by `run_drc` | F-10 |
| PR-02 | Symmetric DRC shortcut = full DRC (same min clearances within 1e-9 mm, same violation set) | F-10, N-01 |
| PR-03 | Continuity (UT-GEO-01) and tangent continuity hold for every built layout | F-01 |
| PR-04 | After mm→nm rounding every connected end-point pair is identical in nm; no two distinct primitives collapse | K-08, N-21 |
| PR-05 | 1 000 random parameter sets per profile: no uncaught exception, no NaN/∞ in any result; invalid inputs return issues | F-14 |
| PR-06 | Scaling laws: R ∝ 1/t_cu; R(T) linear per EQ-10; Ke ∝ B_r (linear model); eddy ∝ f²; Ke independent of speed; rotating the design rotates geometry and leaves abs(Ke) unchanged | ADR-0009, F-11 |
| PR-07 | Balanced combinations → abs(Ke_A) = abs(Ke_B) = abs(Ke_C) within 1e-9 rel. and 120° el. spacing within 1e-9 rad | F-02 |
| PR-08 | Design hash changes iff a design field changes; provenance/ui changes do not change it | F-15 |
| PR-09 | Determinism: same input → byte-identical result JSON (same platform) | N-04 |
| PR-10 | Mirror property (UT-GEO-03) for random coil specs | F-01 |
| PR-11 | Containment: all copper inside the envelope and ≥ edge clearance from outline, bore and holes | F-09, F-10 |
| PR-12 | Status monotonicity: replacing a user input by a default never raises a result's status | T-03 |

Profiles: `fast` (CI, ≤ 2 min total, `assumption`), `long` (nightly, 10× examples). Seeds printed on failure; shrunk examples
added as regression cases.

## 6. Boundary and invalid inputs (BV)

| ID | Input class | Expected |
|---|---|---|
| BV-01 | trace width ≤ 0, NaN, ∞ | `INVALID_NON_POSITIVE` / `INVALID_TYPE` |
| BV-02 | r_outer ≤ r_inner | `INVALID_ORDER` |
| BV-03 | odd pole count | `INVALID_POLE_COUNT_ODD` |
| BV-04 | Q not multiple of 3 (e.g. 16) | `UNBUILDABLE_UNBALANCED_WINDING` |
| BV-05 | turns = max / max + 1 | builds / `UNBUILDABLE_ZERO_TURNS` or `…_TURNS_EXCEED_MAX` |
| BV-06 | pair references unknown copper layer | `INVALID_PAIR_LAYER_UNKNOWN` |
| BV-07 | odd number of copper layers for pairs | `UNBUILDABLE_ODD_PAIR_LAYERS` |
| BV-08 | via pad larger than coil eye | `UNBUILDABLE_VIA_DOES_NOT_FIT` |
| BV-09 | parallel paths > t | `UNBUILDABLE_PARALLEL_PATHS_EXCEED_T` |
| BV-10 | Q/2p > 1 | warning `RANGE_LOW_SPIRAL_UTILISATION` |
| BV-11 | w or t > δ/3 at operating frequency | warning `RANGE_SKIN_DEPTH` |
| BV-12 | copper outside magnet span / within one gap of the magnet ends | warning `RANGE_MAGNET_EDGE` |
| BV-13 | delta with k_w3 ≠ 0 | warning `RANGE_DELTA_TRIPLEN` |
| BV-14 | parallel members at different z | warning `RANGE_PARALLEL_UNEQUAL_Z` |
| BV-15 | topology "serpentine"/"wave" in P2 | `UNSUPPORTED_TOPOLOGY` |
| BV-16 | magnetisation "halbach" | `UNSUPPORTED_MAGNETISATION` |
| BV-17 | > 64 copper layers, > 256 coils (resource limits, `assumption`) | `INVALID_TOO_LARGE` |
| BV-18 | project file newer schema / malformed JSON / missing field | `INVALID_SCHEMA_VERSION_NEWER` / `INVALID_JSON` / `INVALID_MISSING_FIELD` with JSON pointer |
| BV-19 | temperature below −273.15 °C or speed < 0 | `INVALID_RANGE` |
| BV-20 | clearance 0 | `INVALID_NON_POSITIVE` |

## 7. UI tests (UI) — headless

Technology-neutral definitions; implemented with pytest-qt offscreen (C-A) or Playwright (C-B1) after ADR-0005 approval.

| ID | Scenario | Criterion | REQ |
|---|---|---|---|
| UI-01 | Start → default design displayed | geometry, phase, layer and results views populated | F-13, F-21 |
| UI-02 | Edit trace width → recompute | results update; superseded computations cancelled | F-13, N-02 |
| UI-03 | Zoom 0.1×–200× and pan | stroke widths stay in model units; no rasterisation artefacts in SVG export of the view | F-13 |
| UI-04 | Layer visibility toggles | hidden layers absent from the scene | F-13 |
| UI-05 | Event-loop latency probe during a 3 s synthetic compute | input echo < 100 ms (`assumption` threshold) | N-02 |
| UI-06 | Results details panel | every result row shows value, unit, status; details list EQ, EV, assumptions, inputs, validity, tolerance | T-01 |
| UI-07 | Estimates | EQ-14/15/20 values show "estimate"/"guideline (unverified)" and status `unresolved` | F-11, T-05 |
| UI-08 | Default markers | all untouched default inputs show the assumption marker; marker disappears after edit | T-06, F-21 |
| UI-09 | Scaling 100/150/200 % | no clipped/overlapping text (screenshot review) | N-15 |
| UI-10 | Compare designs (if implemented) | values identical to single-design results | F-17 |
| UI-11 | Undo/redo 50 steps | design hash restored | F-22 |
| UI-12 | Engine raises (fault injection) | English error dialog, project saved, app alive, log entry with correlation ID | N-18 |
| UI-13 | Oracle comparison view (P3) | O1/O2 rows with source, page, tolerance | T-12 |
| UI-14 | Issue navigation | selecting an issue focuses the offending input | F-14 |
| UI-15 | No silent rewrite | infeasible edit leaves the user's value unchanged; suggestion shown with explicit "Apply"; hash changes only after Apply | F-23 |
| UI-16 | Presets | default and oracle presets load and compute | F-25 |
| UI-17 | Equation reference | every EQ-ID link opens its registry entry; reference view equals registry content | F-26 |
| UI-18 | Last valid figure | invalid input keeps the previous drawing marked "outdated" | F-27 |
| UI-19 | Feasibility hints | hints match `turns_per_coil` and `Feasibility` after each recompute | F-28 |
| UI-20 | Rotor-angle overlay (if implemented) | magnets rotate, no recompute | F-30 |
| UI-21 | Autosave/recovery | process killed after an edit → next start offers recovery with identical design hash | F-31 |
| UX-AC-01…22 | Agent 1's acceptance criteria (`design_handoff_for_agent3.md` §4), run on the Qt widget tree via `objectName` ids (architecture_draft.md §19) | as defined by Agent 1; mapping to REQ-IDs in requirements_draft.md §9 | see §9 there |

## 8. KiCad export validation (KX) and smoke tests (KS)

### 8.1 Automated (CI)

| ID | Check | REQ |
|---|---|---|
| KX-01 | Parse `.kicad_pcb` with kiutils **and** a minimal independent s-expression parser (sexpdata or own test parser — kiutils' last release is 2024-02-02, KiCad 9 support `unresolved`): counts of segments, arcs, vias, footprints/pads, edge items equal `ExportSummary` and the layout | K-01, F-16 |
| KX-02 | Every track/arc/via has a non-empty net; per-phase nets present | K-09 |
| KX-03 | DXF: ezdxf audit 0 errors; outline closed (every end point shared by exactly two entities); extents within the outline radius (Xcoil `validate_exports.py` pattern) | F-09, F-16 |
| KX-04 | Arc start/mid/end lie on the circle within 1 nm; consecutive primitive end points coincide in nm | K-08 |
| KX-05 | Metadata (generator "embodic", versions, design hash) present in all files | T-07, L-03 |
| KX-06 | Widths and layer names match the layout; inner layers named per mapping rule | K-01 |
| KX-07 | `embodic.io.kicad_items.layout_to_item_specs` (pure, no KiCad): counts, mm→nm, y flip, start/mid/end order; identical specs feed the `.kicad_pcb` writer and the plugin | K-02, K-08 |
| KX-08 | `apply_item_specs` against `FakeBoardApi`: begin/commit on success, rollback on exception, removes only tracked embodic items; a 4-layer fake board with a 6-layer design creates nothing and reports `KICAD_LAYERS_MISSING` | K-02, K-04, K-14 |
| KX-09 | SVG parses as XML; layer groups per copper layer; viewBox covers the outline | F-16 |
| KX-10 | PDF opens with pypdf; ≥ 1 page; contains "Key results" and status labels | F-16, T-07 |
| KX-11 | ZIP bundle (if implemented): contains every selected export + summary text; Xcoil v3 JSON import maps existing fields and lists dropped ones | F-29 |

### 8.2 Manual on the user's machine (Windows, KiCad 9.x)

| ID | Procedure | Pass criterion | Depends on |
|---|---|---|---|
| KS-01 | (= Agent 3's T0) Open the default design's `.kicad_pcb` in KiCad 9.x; run KiCad DRC; save; note the file-format version and layer list KiCad writes | opens without error; 0 DRC errors from embodic copper; format version recorded | REQ-K-01 |
| KS-02 | Install plugin (folder, or PCM "install from file" = Agent 3's T6), enable API, run "Apply embodic project" | items placed; counts = layout; one Undo removes all | T2, T4, T6 |
| KS-03 | "Import stack-up" | values equal Board Setup to 1 µm | T2 |
| KS-04 | Re-apply with changed turns on a board with user items | user items unchanged (count, UUID); embodic items replaced | KS-02 |
| KS-05 | Mismatched kicad-python version | clear English message; board unchanged | T4 |
| KS-06 | First load offline with a local wheel directory | venv created, plugin runs | T2 |
| KS-07 | "Open embodic" launcher | standalone UI connects to the board | T3 |
| KS-08 | `kicad-cli` DRC on an exported board | report produced | T5 |
| T1–T5 | Agent 5's smoke tests (A5-KI §4) | as defined there | — |

## 9. Language checks (LG)

| ID | Check | REQ |
|---|---|---|
| LG-01 | Scan string catalogue, report templates, plugin files, log message templates: 0 characters in U+0E00–U+0E7F; all words in English dictionary + glossary allow-list | L-01 |
| LG-02 | No string literals passed to widget text setters outside `strings.py` (AST lint) | L-02 |
| LG-03 | No "measured" applied to computed values in strings/report templates (allow-list: "reference (paper, measured)") | T-10 |
| LG-04 | No balance/torque/efficiency claims phrased from geometry alone (reviewed phrase list) | T-11 |
| LG-05 | 0 occurrences of "xcoil" (case-insensitive) in user-facing strings and generated files | L-03 |
| LG-06 | Brand asset checksums; personal-name scan of the repository = 0 | L-05 |
| LG-07 | Glossary consistency (e.g. "layer pair", not "layer couple") | L-06 |

## 10. Accessibility checks (AX)

| ID | Check | Method | REQ |
|---|---|---|---|
| AX-01 | Contrast of every theme colour pair used for text (≥ 4.5:1; large ≥ 3:1) and for UI components/graphics (≥ 3:1) | script computes WCAG relative-luminance ratios from `theme.py` tokens (WCAG 2.2 SC 1.4.3, 1.4.11) | N-11, L-04 |
| AX-02 | Keyboard-only scenario (open, edit 3 inputs, recompute, open EQ details, export SVG) | scripted key events, no pointer | N-12, T-01 |
| AX-03 | Visible, unobscured focus indicator on every focusable control | screenshot diff focused vs unfocused | N-12 |
| AX-04 | Interactive targets ≥ 24 × 24 px (SC 2.5.8) | enumerate widgets/DOM nodes and check geometry | N-13 |
| AX-05 | Colour not sole cue: greyscale + deuteranopia simulation, reviewer identifies phase and polarity of 12 coils | manual, 100 % accuracy | N-14 |
| AX-06 | Screen reader (Windows Narrator) announces label, value, unit (inputs) and value, unit, status (results) | manual checklist | N-16 |
| AX-07 | If web front-end (C-B1): axe-core (MPL-2.0) automated audit, 0 serious/critical violations | Playwright + axe-core | N-11…16 |

## 11. Performance baseline (PF)

| ID | Measurement | Target (`assumption` until measured) | REQ |
|---|---|---|---|
| PF-01 | Full recompute of the default design, 20 warm runs, stage timings | p95 < 1.0 s on the reference laptop; stage budgets geometry 0.2 / DRC 0.4 / physics 0.3 s | N-01 |
| PF-02 | Large design (24 coils, 12 layers, 6 series pairs) | < 5 s | N-03 |
| PF-03 | Cold start to interactive window | < 3 s | N-22 |
| PF-04 | CI regression guard | fail if > 3× budget on the CI runner or > 25 % slower than the last baseline file | N-01 |

Baseline record: machine (CPU model, cores, RAM, OS, Python, NumPy), git commit, design hash, timings — stored as JSON per
run. Context value: Xcoil JS engine 0.10–0.19 s for a comparable design on the agent container (requirements_draft.md §7,
`verified (measured)` JS only, not a target).

## 12. Static, packaging and traceability gates

| ID | Gate | REQ |
|---|---|---|
| MT-01 | import-linter contracts (layers, forbidden PySide6/kipy/pcbnew in core, physics ⟂ drc, io ⟂ physics) | N-08, K-05, K-11 |
| MT-02 | mypy --strict on core packages: 0 errors | N-08 |
| MT-03 | ruff lint + format, McCabe ≤ 10 | N-08 |
| MT-04 | Docstring check: public physics functions contain "Units"/parameter units and an EQ-ID | N-09 |
| MT-05 | Unit-suffix lint for dimensional fields; no bare power-of-ten literals in `embodic.physics` | ADR-0009 |
| MT-06 | No built-in `sum()` over floats and no built-in `round()` on coordinates in `embodic.physics`, `embodic.drc`, `embodic.geometry` (AST check; architecture_draft.md §15.4) | N-04, K-08 |
| PK-01 | CI matrix Windows/Linux × Python 3.11/3.12/3.13 green | N-05 |
| PK-02 | Clean-venv install with Python 3.11 resolves (NumPy < 2.5 marker) | N-05 |
| PK-03 | Reproducible wheel (same file list, same `.py` hashes from two builds) | N-06 |
| PK-04 | Cross-platform results within 1e-9 rel. (Windows vs Linux JSON) | N-04 |
| PK-05 | Windows bundle smoke test: start, compute default, export SVG | N-06 |
| PK-06 | Timed fresh-install walkthrough from README (< 10 min) | N-07 |
| PK-07 | Full test suite with network disabled | N-17 |
| PK-08 | Licence report vs allow-list; THIRD_PARTY_LICENSES complete; pip-audit clean | N-19 |
| PK-09 | Plugin package: `plugin.json`, `requirements.txt`, licence file, PCM metadata `runtime: "ipc"` | K-13, K-02 |
| TR-01 | Matrix generator: every must-REQ has ≥ 1 passing test or a manual test record | T-09, N-10 |
| TR-02 | Every test carries ≥ 1 REQ marker | T-09 |
| TR-03 | Registry: EQ with status `verified` links ≥ 1 test that passed in this run | T-05 |
| TR-04 | Every EQ-ID used in code exists in the registry; no unused registry test links | T-04 |

## 13. CI profiles and phase exit criteria

- **Commit profile** (`assumption` ≤ 10 min): MT, UT, GR, BV, PR-fast, KX, LG, AX-01/04, TR, PK-01/02.
- **Nightly**: PR-long, PF-04, PK-03/04/07/08, UI full.
- **Milestone (manual)**: KS-01…08, AX-05/06, PK-05/06.
- **Phase 2 exit** (proposal): all must-REQ tests pass; all GR pass or documented deviations signed off by Agent 2/4;
  OR-04 passes; OR-01/02 pass or remain `xfail` with their gap IDs (then the related EQs stay below `verified`); KS-01
  passed on the user's machine; KS-02 passed if the plugin is in scope after T2/T4.

## 14. Requirements-to-tests traceability matrix (skeleton)

Generated automatically in Phase 2 from pytest markers (TR-01); this skeleton defines the intended coverage.

| REQ-ID | Module(s) | Test IDs |
|---|---|---|
| REQ-F-01 | geometry.generators.spiral | UT-GEO-01, 03, 04, 05, 06, 16; PR-03, PR-10 |
| REQ-F-02 | winding.feasibility, winding.star_of_slots, winding.winding_factors | UT-WND-01…06, 10; PR-07 |
| REQ-F-03 | model.layers, geometry.placement, physics.circuit_solution | UT-GEO-10, 11, 19; UT-PHY-07 |
| REQ-F-04 | model.stackup | UT-GEO-12; GR-07 |
| REQ-F-05 | geometry.vias, physics.resistance | UT-GEO-13; UT-DRC-05; UT-PHY-11; GR-08 |
| REQ-F-06 | geometry.generators.spiral | UT-GEO-07, 08, 09, 17, 18; OR-04 |
| REQ-F-07 | model.rotor, physics.magnets, physics.field | UT-PHY-01…04, 14, 20; GR-03 |
| REQ-F-08 | winding.circuit_topology, geometry.interconnect, physics | UT-WND-07; UT-PHY-09; GR-06, GR-14, GR-15 |
| REQ-F-09 | geometry.outline | UT-GEO-14; KX-03; PR-11 |
| REQ-F-10 | drc | UT-DRC-01…08; PR-01, PR-02, PR-11 |
| REQ-F-11 | physics.* | UT-PHY-05…19; GR-02, 04, 09…13, 16; OR-01…10 |
| REQ-F-12 | physics.field, physics.circuit_solution | UT-PHY-08, 20; GR-05 |
| REQ-F-13 | ui.views | UI-01…04 |
| REQ-F-14 | model.validate, api, errors | BV-01…20; PR-05; UI-14 |
| REQ-F-15 | io.project, io.canonical, io.migrations | UT-IO-01…05; PR-08 |
| REQ-F-16 | io.*_writer, io.report | KX-01…03, 09, 10 |
| REQ-F-17 | ui | UI-10 |
| REQ-F-18 | cli | UT-CLI-01 |
| REQ-F-19 | geometry.generators.base | UT-GEO-20 |
| REQ-F-20 | physics.drive | UI-07 (labelling only) |
| REQ-F-21 | model.defaults, ui | UI-01, UI-08 |
| REQ-F-22 | ui.viewmodels | UI-11 |
| REQ-F-23 | ui.viewmodels, model.validate | UI-15 |
| REQ-F-24 | geometry.outline (fasteners) | UT-GEO-21 |
| REQ-F-25 | examples/, io.project | UI-16; OR-xx |
| REQ-F-26 | results.registry, ui | UI-17 |
| REQ-F-27 | ui.viewmodels | UI-18 |
| REQ-F-28 | ui.views, winding, geometry | UI-19 |
| REQ-F-29 | io | KX-11 |
| REQ-F-30 | ui.views.geometry_view | UI-20 |
| REQ-F-31 | ui.app | UI-21 |
| REQ-F-32 | ui.viewmodels.step_vm | UX-AC-12 |
| REQ-F-33 | ui.dialogs, cli | UX-AC-16; UT-CLI-01 |
| REQ-N-01…03 | api, drc, physics | PF-01, PF-02, PF-04 |
| REQ-N-02 | ui.workers | UI-02, UI-05 |
| REQ-N-04 | api, io.canonical | PR-09, PK-04, UT-IO-02, MT-06 |
| REQ-N-05…07 | packaging | PK-01, 02, 03, 05, 06 |
| REQ-N-08…10 | all | MT-01…05, TR-01 |
| REQ-N-11…16 | ui.theme, ui.views | AX-01…07, UI-09 |
| REQ-N-17 | all | PK-07 |
| REQ-N-18 | ui.app | UI-12 |
| REQ-N-19 | packaging | PK-08 |
| REQ-N-20 | adapters | UT-LOG-01 |
| REQ-N-21 | units, geometry | UT-UNI-01, 02; PR-04 |
| REQ-N-22 | ui | PF-03 |
| REQ-N-23 | ui.theme, ui.views.geometry_view | UX-AC-05; AX-05 |
| REQ-N-24 | ui.views | UX-AC-15; AX-06 |
| REQ-N-25 | ui.views.charts | UX-AC-18 |
| REQ-N-26 | ui | UX-AC-20 |
| REQ-K-01 | io.kicad_pcb_writer | KX-01, 02, 04, 05, 06; KS-01 |
| REQ-K-02 | embodic_kicad_plugin | KX-07, KX-08; KS-02 |
| REQ-K-03 | embodic_kicad_plugin.stackup_import | KS-03 |
| REQ-K-04 | embodic_kicad_plugin.tracking | KX-08; KS-04 |
| REQ-K-05, K-11 | all | MT-01 |
| REQ-K-06 | embodic_kicad_plugin.connection | KS-05 |
| REQ-K-07 | plugin packaging | KS-06; PK-09 |
| REQ-K-08 | io.kicad_items, io.kicad_pcb_writer, plugin.apply | UT-UNI-02; PR-04; KX-04, KX-07 |
| REQ-K-09 | plugin, writer | KX-02 |
| REQ-K-10 | plugin.launcher | KS-07 |
| REQ-K-12 | — | KS-08 |
| REQ-K-13 | packaging | PK-09 |
| REQ-K-14 | plugin.apply, ui.export_view | KX-08; KS-02 |
| REQ-K-15 | ui.views.kicad_compact | KS-07; UX-AC-21 |
| REQ-T-01 | ui.results_view | UI-06, AX-02 |
| REQ-T-02 | results | UT-RES-01 |
| REQ-T-03 | results.status | UT-RES-02; PR-12 |
| REQ-T-04 | results.registry | UT-RES-03; TR-04 |
| REQ-T-05 | results, physics | UT-RES-02; UT-PHY-15, 18; TR-03; UI-07 |
| REQ-T-06 | model.provenance, io.project, ui | UT-IO-05; UI-08 |
| REQ-T-07 | io.* | UT-IO-06; KX-05, KX-10 |
| REQ-T-08 | physics, results | UT-PHY-13; BV-10…14 |
| REQ-T-09 | tests infrastructure | TR-01, TR-02 |
| REQ-T-10, T-11 | ui.strings, io.report | LG-03, LG-04 |
| REQ-T-12 | ui, io.report | UI-13 |
| REQ-T-13 | ui.results_view | UX-AC-02; UI-06 |
| REQ-T-14 | ui.views.geometry_view, io.* | UX-AC-17; KX-05 |
| REQ-L-01, L-02 | ui.strings, plugin | LG-01, LG-02 |
| REQ-L-03 | ui, io | LG-05, KX-05 |
| REQ-L-04 | ui.theme | AX-01 |
| REQ-L-05 | assets | LG-06 |
| REQ-L-06 | ui.strings | LG-07 |
| REQ-L-07 | results.formatting | UT-UNI-03 |
| REQ-L-08 | results.formatting, ui | UX-AC-19 |
| REQ-L-09 | ui.strings | LG-07 |

## 15. Expected independent coverage by Agent 4

Agent 4 should cover, **without reading the embodic implementation** where possible:
1. **Independent implementations** for N-version comparison: brute-force DRC checker (PR-01), star of slots and winding
   factors (UT-WND-05), field at a point for EQ-05 (closed form), EQ-07 circuit identity.
2. **Physics validation tasks** proposed by Agent 2 (A2-EQ end): T-A 3-D FEA / FEMM 2-D for EQ-05 and per-layer B_z (G3);
   T-B 2-D FEM of one trace for EQ-12; T-C re-create O1 for EQ-06; T-D recover D09 turn count for OR-02/OR-07; T-E arbitrate
   EQ-14 (D10 vs D15 form); T-F re-run C1–C9 against the Python port.
3. **Oracle tolerance sign-off** (§4) and review of every golden deviation (§3 rule 2).
4. **Black-box requirement tests** from `requirements_draft.md` acceptance criteria (especially REQ-F-14 invalid inputs and
   REQ-T traceability displays).
5. **Golden harness audit**: confirm the dump script reads the reference engine read-only and that unit/convention
   conversions in GR tests are correct.
6. **Mutation testing** of `winding`, `drc` and `results.status` (tool to be chosen, licence-checked) to measure test
   strength.
7. **Accessibility audit** (AX-05, AX-06) and **language audit** (LG-01, LG-03, LG-04) as an independent reviewer.
8. **Licence/code-provenance review**: plugin code vs kimotor (GPL-2.0) similarity check (REQ-N-19).
9. **KiCad smoke-test coordination** with the user (KS-01…08, T1–T5) and recording of results as evidence.
