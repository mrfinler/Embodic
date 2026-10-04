Prepared by: Agent 3 — Senior Software Engineer — model: claude-opus-5-5

# Migration mapping Xcoil v3 → embodic (Phase 1 draft, 2026-10-04)

Inputs: `feature_inventory.md` (F-01…F-64, this folder), Agent 2's gate (`docs/phase1/engineering/equation_specification_draft.md`,
`existing_logic_review.md`, `topology_analysis.md`, `spiral_coil_concept.md`), Agent 5's KiCad evidence
(`docs/phase1/evidence/kicad_plugin_evidence.md`), PROJECT_BRIEF §1 (spiral coils replace sector coils, 3 phases, multi-layer,
white/grey/black, Python engines, KiCad 9.x plugin if feasible).

Decision vocabulary (as requested): **port as-is** (same behaviour, re-implemented in Python), **port with change**,
**redesign** (same purpose, new design), **drop**, **new**. Every decision below is a *proposal* (`assumption`) for the user
and Fable; nothing is decided here.

Gate column: Agent 2's verdict for the equations used (EQ-xx: `reuse`, `reuse with change`, `cannot verify yet`,
`replace`, `add`). **Every calculation feature is blocked until the equation specification is approved for Phase 2**
(brief §1: "Every piece of calculation logic must be engineering-checked … before it is reused"). Rows marked
**BLOCKED (cannot verify yet)** may be ported only as clearly labelled estimates, and only after Phase 2 approval.
Geometry, DRC and export rows have no EQ gate but follow the Phase 2 approval of the plan.

Target names (`core.params`, `core.geometry`, `core.topology.spiral`, `core.analysis`, `core.drc`, `core.mech`, `io.export`,
`io.project`, `app.*` for the standalone UI, `kicad.*` for the plugin adapter) are **placeholders**; Agent 6 owns the
architecture.

## 1. Mapping of existing features

### 1.1 Parameters, presets, persistence, compute loop

| F | Feature | Decision | Reason | embodic target | Gate |
|---|---|---|---|---|---|
| F-01 | Parameter defaults, normalisation, validation | port with change | Keep the error-code concept (field + code + message, `engine.js` l.107–160) but use a typed schema with unit, range, default, `only`-topology and source per field; sector keys (`sectors`, `coilSides`, `coilEnds`, `coilGap`, `coilLayers`) are replaced by spiral keys (N-01); keys of dropped topologies removed | `core.params` | none (validation) |
| F-02 | Form generator from `GROUPS` | redesign | New UI technology and Agent 1's layout; keep the declarative idea (form built from the schema, so UI-01 "every parameter has a control" stays testable) | `app.forms` | — |
| F-03 | 15 presets | port with change | Replace with spiral presets: Agent 2's default 12 coils / 16 poles (`topology_analysis.md` K4, `assumption`) and the oracle configurations 12/10 (D08) and 12/16 (D09) as *validation cases* (N-12); drop serpentine/wave presets unless those topologies are kept (§3) | `io.project` presets | — |
| F-04 | Autosave of last parameters (localStorage) | port with change | Desktop: last project path + autosave file in the user profile; plugin: none (board is the document) | `app.settings` | — |
| F-05 | Open/Save parameter JSON | port with change | Project file with `schema_version`, embodic version, units; optional importer for Xcoil v3 JSON (only fields that still exist) | `io.project` | — |
| F-06 | Reset, collapse/expand | port as-is | UI convenience | `app` | — |
| F-07 | Toolstrip quick setters (topology, connection, wave style) | redesign | Topology choice becomes spiral variants (side/end style, stacking M1–M4); connection buttons stay | `app.toolbar` | — |
| F-08 | Debounced recompute, last-good dimming | port with change | CPython is ≈45× slower than V8 on the DRC kernel (measured, `calculation_flow_and_port_notes.md` §4): needs a worker thread/process, cancellation, and staged recompute (operating-point changes must not rebuild geometry or rerun DRC) | `app.controller` + `core` caching | — |

### 1.2 Topology generators and geometry

| F | Feature | Decision | Reason | embodic target | Gate |
|---|---|---|---|---|---|
| F-09 | Serpentine generator | **user decision** (§3); proposal: drop from Phase 2 | Not the chosen topology; own DRC and analysis path (O-1 in the inventory) | — | — |
| F-10 | Max traces that fit (serpentine) | drop with F-09; concept kept as N-01 "max turns" | Spiral needs EQ-02 constructive limit | `core.topology.spiral` | EQ-02 `replace` |
| F-11 | Wide end-turns + taper | port with change | Applies to spiral end-turns (rim arcs outside the magnet span, `ui-content.js` guide l.29–46 cites Tokgöz); later radius-dependent width S5 (`topology_analysis.md` §3.1) | `core.geometry`, `core.topology.spiral` | EQ-10 `reuse` (R), EQ-06 `reuse` |
| F-12 | Sector (concentrated spiral) coils | **redesign → replaced by N-01** | Brief: spiral coil replaces sector coil. Agent 2: `sectorCoilX`/`buildSector` "reuse with change (as reference)"; `starOfSlots`, `balancedSectorList` **replace** (belt-edge bug C6); turn limit **replace** (no triangular turns, 0 turns for D08 geometry, C5); layer pairs only parallel, no group rotation (Q-2) | `core.topology.spiral` | EQ-02, EQ-08 `replace`; EQ-07 `reuse with change` |
| F-13 | Interleaved involute wave | **user decision** (§3); proposal: defer | Relevant to the reference board (repository = wave winding, `topology_analysis.md` K1) but not the chosen topology | (later) `core.topology.wave` | EQ-06/07 |
| F-14 | Wave styles jog/chord (Paul) | **user decision** (§3); proposal: defer | as F-13 | (later) | — |
| F-15 | Wave style overlap (Paul) | **user decision** (§3); proposal: defer | as F-13 | (later) | — |
| F-16 | Geometry primitives (line/arc with width, transforms, discretise, fillets, biarcs, width runs) | port with change | Foundation for every generator, DRC, exporter and the KiCad adapter; Python dataclasses with the same signed-sweep convention; exact arc–arc/line–arc distances may replace discretised DRC later | `core.geometry` | none (numerics notes §2–3, primitive design notes §6) |
| F-17 | Phase interconnect (star ring / delta links / pads / corridor) | port with change | Generalise for spiral coil chains (Agent 2 C-panel, `spiral_coil_concept.md`; Xcoil `chainCoils` as reference); keep non-crossing ring placement | `core.topology.spiral.interconnect` | EQ-19 `reuse with change` (delta circulation); interconnect R `reuse` |
| F-18 | Terminal pads | port as-is | Shapes and SMD/THT are topology-independent; add mapping to KiCad footprints in the adapter | `core.geometry.pads` | — |
| F-19 | Board outline and cut-out | port with change | Add absolute dimensions (e.g. "93 mm across flats" of the repository board, brief §2) in addition to scale factors | `core.mech` | — |
| F-20 | Fasteners (ISO 273 table) | port as-is | Table values need a cited source (not in the corpus) → `assumption` label until Agent 5 confirms | `core.mech` | (source) |
| F-21 | Stack-up model auto/custom | port with change | Agent 2: custom z as default (`existing_logic_review.md` `stackupFor` row); plugin mode can read the board stack-up (`Board.get_stackup()`, Agent 5 [K7]) | `core.stackup` | EQ-05 z-positions |
| F-22 | Stack-up editor | redesign | New UI; merged with the layer configuration display N-03 | `app.stackup` | — |

### 1.3 DRC and warnings

| F | Feature | Decision | Reason | embodic target | Gate |
|---|---|---|---|---|---|
| F-23 | Serpentine canonical-frame DRC | drop with F-09 | Only needed by serpentine | — | — |
| F-24 | Generic object DRC | port with change | Vectorised kernel (NumPy) for speed; add checks for series pairs (several centre vias per coil eye, transfer vias, through vias crossing other layers); label as "embodic pre-check" — KiCad DRC cannot see turn-to-turn clearance inside one net (`kicad_plugin_feasibility.md` §3) | `core.drc` | none |
| F-25 | Mechanical rule issues | port as-is | Topology-independent | `core.mech` | — |
| F-26 | Design and fabrication warnings | port with change | Each warning gets a threshold source or an `assumption` label (FAB limits "typical pooled-prototype capability", `engine.js` l.2502, have no source); IPC warning depends on EQ-15; IMBALANCE/CIRC rewritten for spiral multi-layer (G3) | `core.checks` | EQ-13 `reuse`, EQ-15 `cannot verify yet`, EQ-07 |

### 1.4 Analysis

| F | Feature | Decision | Reason | embodic target | Gate |
|---|---|---|---|---|---|
| F-27 | Field model | port with change | Add α_p(r) for block magnets (EQ-04), Halbach option, radial edge correction, B_r(T); keep odd harmonics configurable | `core.analysis.field` | EQ-05 `reuse with change`, EQ-04 `replace/add` — blocked until approval |
| F-28 | Back-EMF / flux linkage, phase assembly, kw1, THD | port with change | Path integral `reuse` (EQ-06); assembly needs series layer pairs (EQ-07); numeric "kw1" renamed utilisation factor, textbook k_w reported separately; `kdAnalytic` **replace** (EQ-08) | `core.analysis.emf` | EQ-06 `reuse`, EQ-07 `reuse with change`, EQ-08 `replace`, EQ-18 `reuse` — blocked until approval |
| F-29 | DC resistance, via barrel, links | port as-is (formulas) / with change (vias) | EQ-10 `reuse` (ρ₂₀, α need cited source, G6); EQ-11 `reuse with change`: plating and via count as inputs, every via in the current path counted (Q-10) | `core.analysis.resistance` | EQ-10, EQ-11 — blocked until approval |
| F-30 | Losses, efficiency, Km | port with change | Copper EQ-10, eddy EQ-12 `reuse` (later drop B_t on circumferential segments, Q-6), circulating EQ-07, delta EQ-19; label efficiency "electromagnetic, estimate" (no mechanical/iron losses) | `core.analysis.losses` | EQ-07/10/12/19 — blocked until approval |
| F-31 | Star/delta/open line quantities | port as-is | EQ-09 `reuse` (fundamental only) | `core.analysis.connection` | EQ-09 — blocked until approval |
| F-32 | EMF waveforms, harmonic table | port as-is | EQ-18 `reuse`; show phase **and** line THD | `core.analysis.emf`, `app.charts` | EQ-18 — blocked until approval |
| F-33 | IPC-2221 limit, current density, skin depth | IPC: port with change as labelled guideline; J and δ: port as-is | EQ-15 **cannot verify yet** (standard not in corpus, G5) → **BLOCKED (cannot verify yet)**, display "guideline (unverified)"; EQ-22 and EQ-13 `reuse` | `core.analysis.thermal_limits` | EQ-13, EQ-15, EQ-22 |
| F-34 | Inductance (current-sheet model) | port with change, labelled estimate | EQ-14 **cannot verify yet**: end turns ignored (significant for spirals, Q-8), no oracle (G1) → **BLOCKED (cannot verify yet)**; Phase 2 proposal by Agent 2: Neumann filament model + FEMM/3-D check | `core.analysis.inductance` | EQ-14 |
| F-35 | Torque–speed, inverter, inertia | port with change, labelled estimate | EQ-20 **cannot verify yet** (needs EQ-14) → **BLOCKED (cannot verify yet)**; inertia "reuse with change" (singleOpen inconsistency Q-3) | `core.analysis.drive` | EQ-20, EQ-14 |
| F-36 | Mass and first-order thermal | port with change | EQ-16/EQ-17 `reuse with change`: densities and h need sources (h = 30 vs D01's 10 W/m²K), conduction path | `core.analysis.mass_thermal` | EQ-16, EQ-17 — blocked until approval |

### 1.5 Presentation, figure, exports, tests

| F | Feature | Decision | Reason | embodic target | Gate |
|---|---|---|---|---|---|
| F-37 | Summary strip | redesign | Agent 1 layout; every value with unit and status badge (N-04) | `app.summary` | — |
| F-38 | Results tables | redesign | Rows become traceable result records (N-05) | `app.results` | — |
| F-39 | DRC tab with Locate | port with change | Same list + locate; optional import of KiCad DRC JSON (N-09) | `app.drc` | — |
| F-40 | Inspector hints | port with change | Spiral-specific hints (turn limit, via eye, balanced Q list) | `app.forms` | — |
| F-41 | Compare with reference | port with change | Compare stored embodic runs/variants (e.g. M1 vs M2 stacking); optional comparison against an imported Xcoil v3 result | `app.compare`, `core.compare` | — |
| F-42 | 2-D plan render | redesign | White/grey/black palette: phases need a non-colour encoding (grey levels, dash/hatch, labels A/B/C, per-phase isolation) — open question for Agent 1/user; keep bottom-up layer drawing and DRC markers | `app.canvas2d` | — |
| F-43 | 2-D interactions (zoom/pan/pinch/fit/terminals/read-out/scale bar) | port with change | Re-implemented in the chosen UI toolkit | `app.canvas2d` | — |
| F-44 | Layer visibility bar | port with change | Becomes part of N-03 (per-layer visibility inside the layer table) | `app.layers` | — |
| F-45 | Rotor angle slider | port as-is | Visual check of coil/magnet alignment | `app.canvas2d` | — |
| F-46 | Current-flow animation | port with change | Optional; static direction arrows work in greyscale, print and PDF | `app.canvas2d` | — |
| F-47 | Show toggles | port as-is | — | `app` | — |
| F-48 | 3-D view (three.js) | port with change, low priority | Depends on UI technology (three.js in a web UI, or a Python 3-D library); heavy dependency for the plugin path — keep out of `core` | `app.view3d` | — |
| F-49 | SVG export | port as-is | Rendered from the shared Board model; greyscale styles | `io.export.svg` | — |
| F-50 | DXF complete | port as-is | Own R12 writer (≈50 lines in Xcoil) — no dependency needed | `io.export.dxf` | — |
| F-51 | Outline DXF | port as-is | — | `io.export.dxf` | — |
| F-52 | Screws DXF | port as-is | — | `io.export.dxf` | — |
| F-53 | KiCad `.kicad_pcb` file | port with change | Target the user's KiCad 9 format (version token and layer ordinals to be confirmed by smoke test T0, `kicad_plugin_feasibility.md` §6); write the stack-up section; per-phase nets where possible; same Board model as the IPC adapter | `io.export.kicad_pcb` | — |
| F-54 | Parameter JSON | port with change | Project schema (F-05) | `io.project` | — |
| F-55 | ZIP | port as-is | Python `zipfile` (stdlib) replaces the hand-written store-only writer | `io.export` | — |
| F-56 | PDF report | port with change | Add EQ/assumption/status table and traceability appendix; greyscale; technology open (own writer port or reportlab, see dependency draft) | `io.export.report` | — |
| F-57 | README.txt | port with change | Add versions, schema, provenance (inputs hash) | `io.export` | — |
| F-58 | Save mechanism (Claude downloads / Blob / dialog) | redesign | Desktop file dialogs; plugin writes into the open board | `app.files` | — |
| F-59 | Built-in test runner (131 + 21 tests) | port with change | pytest suite replaces the in-app runner; keep test IDs where the test still applies (GEO-01 continuity, GEO-02 G1 fillets, ELE-xx, FLD-xx, EMF-xx, EXP-xx); add JS↔Python cross-check (notes §7) and Agent 2's C1–C9 as regression tests; an optional in-app "self-test" can call the same functions | `tests/` | — |
| F-60 | Reference (formulas) tab | port with change | Generated from the equation registry (EQ-ID, formula, sources, verdict) so the UI cannot drift from the spec | `app.reference` ← `core.equations` | — |
| F-61 | Guide tab | port with change | Content review for spiral coils; every source re-checked by Agent 5 | `app.guide` | — |
| F-62 | Status bar | port as-is | — | `app.status` | — |
| F-63 | Shell, theming, fonts | redesign | embodic brand, white/grey/black; fonts bundled or system (Xcoil loads IBM Plex from Google Fonts at runtime, `build.js` l.4) | `app.shell` | — |
| F-64 | Golden/regression tooling | port with change | Capture embodic's own golden numbers; JS↔Python cross-check harness (notes §7) | `tools/`, `tests/` | — |

## 2. New features required by the brief

| N | Feature | Content | Depends on | Gate |
|---|---|---|---|---|
| N-01 | **Spiral coil generator** (replaces F-12) | Concentrated planar spiral per coil; Q coils per layer, coil gap; side styles S1 radial / S2 parallel, end styles arc / straight / stadium (`topology_analysis.md` §3.1); constructive turn generator with inner end-turns moving outward ("triangular" turns), EQ-02/EQ-03 shown as cross-checks (N-08); centre via(s) and lead in the coil eye, multi-via transitions; nested fillets; X/Y mirrored pairs; stacking M1 parallel pairs, M2 series pairs with transfer vias, M3 rotated groups, M4 phase per layer pair (`topology_analysis.md` §4.2); coil chaining per phase (Xcoil `chainCoils` as reference) and phase rings; output = Board model + electrical element list (members/series) | F-16, F-17, F-24 | EQ-01 `reuse`, EQ-02 `replace`, EQ-03 `add`, EQ-06/07 |
| N-02 | **Explicit phase assignment display** | Coil → phase/sign table, pattern string (e.g. "AabBCcaABbcC" for 12/10, D08 Fig. 3.7), k_d, k_p (turn-averaged), k_w per harmonic, feasibility Q/(m·gcd(Q,p)), list of balanced Q for the pole count; integer phasor arithmetic (no belt-edge ties, C6); optional manual override with a balance check | N-01 | EQ-08 `replace` — blocked until approval |
| N-03 | **Layer configuration display/editor** | Table per copper layer: KiCad name, z, copper thickness, role X/Y, pair, phase content, series/parallel group, rotation offset, via spans; stack drawing; connection diagram of the series path through layers and vias (concept panels B/C, `spiral_coil_concept.md`); per-layer B_z1 and per-pair EMF (G3) | N-01, F-21 | EQ-05, EQ-07 |
| N-04 | **Units, assumptions and validation status on every result** | Each result = `{value, unit, eq_id, status, assumptions[], tolerance, warnings[]}`; UI shows unit and a status badge (`verified` / `inferred` / `assumption` / `unresolved` / `not tested` per brief §3, mapped from the EQ verdict); BLOCKED estimates visually distinct; exports carry the same fields | `core.equations` registry | all EQ |
| N-05 | **Traceability** | Result → inputs (parameter keys, values, units) → assumptions → EQ-ID → evidence (EV-IDs, file/page) → engine version and geometry hash; drill-down panel; PDF appendix; JSON export | N-04 | — |
| N-06 | **KiCad plugin host** | IPC API plugin (kicad-python) as a thin adapter over the same core: read board stack-up and layer count, generate, push items in one commit; packaging as PCM zip (`runtime: "ipc"`); external-control mode from the standalone app (Agent 5 T3) as an alternative | Board model, `kicad_plugin_feasibility.md` | — |
| N-07 | Magnet geometry model | Arc segments vs rectangular blocks (repository 20 × 6 × 2 mm), α_p(r) | F-27 | EQ-04 `add` |
| N-08 | Closed-form cross-checks next to computed geometry | EQ-02 turn limit (±1 turn), EQ-03 loop length (±6 %) displayed with the constructive result | N-01 | EQ-02/03 |
| N-09 | KiCad DRC import (optional) | Run `kicad-cli pcb drc --format json` on the exported file and show the violations (CLI documented for 9.0, see `kicad_plugin_feasibility.md` §2) | F-53 | — |
| N-10 | Project schema versioning and Xcoil v3 import (optional) | `schema_version`, migrations; import of Xcoil v3 parameter JSON for comparison | F-05 | — |
| N-11 | Copper-loss-budget current (optional) | I_ph = √((P_Cu/m)/R_ph) | F-29 | EQ-21 `add` |
| N-12 | Validation case library | Oracles O1–O3 (D08 Ke, D09 R/L, D10 R, D15 torque — Agent 5) runnable from tests and UI with tolerance and status | N-01, analysis | per EQ |
| N-13 | Headless entry point | `compute(project) → results` as a CLI/API (used by the plugin, the cross-check harness and CI) | `core` | — |

## 3. Serpentine and wave generators: keep as secondary topologies or drop?

The brief says features must be preserved where the user wants them. This table supports the user's decision; it does not
make it. Line counts are ranges of `engine.js` (arithmetic on the cited ranges, `inferred`).

| Option | Pros | Cons | Effort / risk |
|---|---|---|---|
| **A. Keep serpentine** as a secondary topology | Mature (GEO-01…14, DRC-01…, golden regression of 1417 numbers passes with interconnect off — verified run); many turns per layer pair; fewest vias; useful as a comparison baseline | Not the chosen topology; phase per layer pair → layer-dependent EMF (IMBALANCE warning, `engine.js` l.2499); needs its own DRC (`runDrc` l.756–850) and analysis (`analyze` l.880–1017) besides the generic path; its oracles are not spiral oracles | ≈ 590 lines geometry (l.163–753) + ≈ 95 DRC + ≈ 140 analysis + conductor list; port + cross-check ≈ comparable to the spiral generator itself (`inferred`) |
| **B. Keep wave** (involute, jog, chord, overlap) as secondary | The reference repository board is a wave winding (`topology_analysis.md` K1) and D02 (SPARK) and D07 (Paul) are wave papers → spiral-vs-wave comparison on the same rotor; all phases on every layer (balanced EMF); uses the generic DRC/analysis path that the spiral port needs anyway (`drcObjects`, `analyzeElements`) | Not the chosen topology; many vias (2Q per stack); involute biarc approximation and adaptive thresholds complicate the JS↔Python cross-check (notes §2); four styles to maintain | ≈ 240 (l.1449–1690) + ≈ 165 (l.1921–2087) + ≈ 140 (l.2089–2230) lines; moderate (`inferred`) |
| **C. Drop both** from embodic; keep Xcoil v3 HTML as a read-only legacy tool | Smallest code base, focus on spiral coils and the plugin; no maintenance of unused paths; Xcoil v3 still answers serpentine/wave questions | Two topologies disappear from the new tool; comparisons need a second program; Xcoil v3 keeps its unverified equations (no EQ labels) | none |
| **D. Defer** (spiral only in Phase 2; architecture keeps a topology plug-in interface; decide A/B after the spiral path is validated) | Keeps the option open at near-zero cost; avoids porting code whose equations are gated anyway; the plug-in interface is good architecture regardless | Users who need serpentine/wave now must use Xcoil v3 meanwhile | interface only (Agent 6) |

Recommendation (`assumption`, for the user to decide): **D**, and if one secondary topology is wanted later, **B (wave)**
before A, because it relates to the reference board and its papers and reuses the generic path. Request to Agent 6:
the topology must be a plug-in (generator → Board model + electrical element list) so that A or B can be added without
touching `core.analysis`, `core.drc` or the exporters.

## 4. Cross-cutting migration issues

| # | Issue | Proposal | Status |
|---|---|---|---|
| X-1 | Palette: Xcoil distinguishes phases only by red/blue/green (`style.css` l.6, `report.js` l.7) | Agent 1 to define a greyscale phase encoding (grey level + dash/hatch + text labels) or ask the user whether a muted secondary data palette is allowed for phases | unresolved (user/Agent 1) |
| X-2 | Units are implicit in Xcoil (labels only) | Unit metadata in the parameter schema and on every result (N-04); internal units mm, rad, SI as in Xcoil (`engine.js` l.2); KiCad nanometres only inside the adapter | assumption |
| X-3 | Golden regression of Xcoil passes only with `interconnect:false` | Use that override in the cross-check harness | verified (run) |
| X-4 | Intentional deviations from Xcoil (star of slots, α_p(r), turn limit, series pairs) will make cross-check results differ by design | The harness keeps an allow-list of expected differences, each with EQ-ID and reason (notes §7.1, `expected_diffs`) | assumption |
| X-5 | Speed: a literal Python port of the hot loops is ≈45× slower than V8 (measured kernel) | NumPy kernels + staged recompute + reference scalar implementation for testing (notes §4) | inferred from measurement |
