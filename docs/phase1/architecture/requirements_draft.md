Prepared by: Agent 6 — Software Architecture Specialist — model: claude-opus-5-5

# embodic — Requirements (Phase 1 draft, 2026-10-04)

Status of this document: **draft for review** by Fable 5.1, Agents 1–5 and the user. Nothing here is implemented
(PROJECT_BRIEF §3 rule 9). Status labels follow PROJECT_BRIEF §3 rule 3. Every numeric acceptance threshold that is not
taken from a cited standard or from an agent's verified finding is labelled `assumption` and must be confirmed or
replaced by a measurement in Phase 2.

## 0. Conventions

- **ID scheme**: `REQ-F-xx` functional, `REQ-N-xx` non-functional, `REQ-K-xx` KiCad plugin/integration, `REQ-T-xx`
  traceability and evidence display, `REQ-L-xx` language and branding. IDs are stable; withdrawn requirements keep
  their ID with status "withdrawn".
- **Priority**: `must` (Phase gate fails without it), `should` (expected; may slip with Fable's approval), `could`
  (nice to have).
- **Phase**: `P2` = Phase 2 implementation (core engine, standalone UI, exports, KiCad integration as far as the smoke
  tests T1–T5 allow); `P3` = Phase 3 independent verification and hardening (decision_log D-002); `Later` = after
  Phase 3 (kept possible by the architecture, not scheduled).
- **"Default design"** = the first reference case of Agent 2 (`topology_analysis.md` §5.2): 12 coils / 16 poles FSCW,
  double rotor, 16 blocks 20 × 6 × 2 mm, 6 copper layers 1 oz in 0.62 mm, 3 layer pairs, w/s 0.5/0.2 mm, coil annulus
  r = 18–38 mm — every value `assumption` (Agent 2).
- **"Reference laptop"** (for performance criteria, `assumption` until the user confirms his hardware): x86-64 CPU with
  ≥ 4 cores at ≥ 2.0 GHz base clock, 8 GB RAM, Windows 11, CPython 3.11 64-bit, on mains power.
- Test IDs in the acceptance criteria refer to `test_plan_draft.md`.

Source abbreviations used below:

| Key | Source |
|---|---|
| BRIEF | `docs/PROJECT_BRIEF.md` (§1 user decisions, §3 rules) |
| DL | `docs/decision_log.md` (D-001 … D-005) |
| A2-EQ | `docs/phase1/engineering/equation_specification_draft.md` (EQ-01 … EQ-22, gate summary) |
| A2-TOP | `docs/phase1/engineering/topology_analysis.md` |
| A2-REV | `docs/phase1/engineering/existing_logic_review.md` |
| A5-KI | `docs/phase1/evidence/kicad_plugin_evidence.md` |
| A5-GAP | `docs/phase1/evidence/evidence_gaps.md` (G1 … G22) |
| A5-REG | `docs/phase1/evidence/evidence_register.md` (EV-IDs, oracles O1–O9) |
| XC | Xcoil v3 reference source `/home/claude/serpentine/` (read-only) |
| WCAG | W3C WCAG 2.2, https://www.w3.org/TR/WCAG22/ and Understanding SC 2.5.8 https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html (accessed 2026-10-04) |
| M-JS | Agent 6 timing of the Xcoil v3 JS engine on the agent container (§6 of this file) |

## 1. User's original wishes → requirement IDs

| User wish (BRIEF §1 and task statement) | Requirement IDs |
|---|---|
| Spiral coil replaces the sector coil of Xcoil | REQ-F-01, REQ-F-06 |
| 3 phases | REQ-F-02, REQ-F-08 |
| Multi-layer configuration | REQ-F-03, REQ-F-04, REQ-F-05, REQ-F-12 |
| Geometry, phase assignment, layer configuration and results displayed clearly | REQ-F-13, REQ-F-11, REQ-N-11…16 |
| Units, assumptions, limits and validation status shown | REQ-T-01…08, REQ-F-14 |
| Readable, maintainable code | REQ-N-08, REQ-N-09, REQ-N-10 |
| Requirements ↔ acceptance criteria ↔ tests linked | REQ-T-09 |
| Reproducible install / run / package | REQ-N-05, REQ-N-06, REQ-N-07 |
| English UI | REQ-L-01, REQ-L-02, REQ-L-06, REQ-L-07 |
| embodic branding | REQ-L-03, REQ-L-05 |
| White / grey / black UI | REQ-L-04, REQ-N-14 |
| KiCad plugin (KiCad 9.x) | REQ-K-01 … REQ-K-13 |
| Calculation and geometry engine in Python (BRIEF §1) | REQ-N-08, REQ-K-05 |
| Keep serpentine/wave generators possible later (coordinator constraint) | REQ-F-19 |

## 2. Functional requirements (REQ-F)

| ID | Statement | Rationale / source | Prio | Acceptance criteria | Phase |
|---|---|---|---|---|---|
| REQ-F-01 | The engine shall generate concentrated planar **spiral coils**: per layer pair, layer X spirals from the outer terminal inward to a centre via and layer Y spirals outward with mirrored artwork and the same circulation. | User decision (BRIEF §1); topology definition A2-TOP §1.3 and §4.1 (D02 p.1 EV-01, D14 p.4 EV-40) | must | (a) For the default design every coil path is continuous: end of primitive *i* = start of *i+1* within 1e-6 mm (UT-GEO-01). (b) Y, mirrored back about the coil axis, lies on X within 1e-9 mm (UT-GEO-03). (c) Centre via terminates X and Y within 1e-9 mm (UT-GEO-04). (d) Signed circulation of X and Y is equal (UT-GEO-05). | P2 |
| REQ-F-02 | The engine shall check 3-phase feasibility for any coil count Q and pole count 2p (q = Q/(2p·m), t = gcd(Q, p), balanced iff Q/(m·t) is integer) and assign phases and polarities by the star of slots using **exact integer arithmetic**. | A2-EQ EQ-08 (gate `replace`), A2-TOP §2.2; Xcoil `starOfSlots` belt-edge bug (A2-REV §2.4 Q-1, C6) | must | (a) 12/10 → pattern "AabBCcaABbcC" (D08 p.36 Fig. 3.7) (UT-WND-01). (b) 12/14, 24/14, 24/22, 24/26 reported **balanced** (UT-WND-02, regression of the Xcoil bug). (c) 12/16 → "ACBACBACBACB", all positive (UT-WND-03). (d) 16/16 rejected for 3 phases with code `UNBUILDABLE_UNBALANCED_WINDING` (UT-WND-04). (e) k_w1 values of A2-TOP §2.2 reproduced to 1e-9 (UT-WND-05). | P2 |
| REQ-F-03 | The user shall configure multi-layer windings: number of layer pairs, per-pair connection (series chain of parallel groups), per-pair rotation, and per-pair phase set (all phases, or one phase per pair). | A2-TOP §4.2 options M1–M4; A2-EQ EQ-07; Agent 2 data-model requests (architecture_draft.md §7) | must (M1, M2), should (M3 rotation, M4 phase per pair) | (a) Default design builds with 3 pairs in series (M2) and in parallel (M1) (UT-GEO-10). (b) A pair rotation of π/Q places group-2 centre vias in the inter-coil gaps of group 1 (UT-GEO-11). (c) Phase EMF of a series chain equals the phasor sum of the pair EMFs at their own z within 1e-9 rel. (UT-PHY-07). | P2 |
| REQ-F-04 | The user shall define the stack-up as an explicit ordered list of copper and dielectric layers with thicknesses; copper-layer z positions shall be derived from that list. An "even spacing" helper may generate such a list but shall not be a separate model. | A2-REV §1 `stackupFor` ("custom mode as default for z"); G3 per-layer EMF (A5-GAP) | must | (a) z of each copper centre = cumulative thickness above + t/2, exact (UT-GEO-12). (b) Helper output for 6 × 34.8 µm in 0.62 mm equals Xcoil `stackupFor` auto mode to 1e-12 mm (GR-07). (c) Board thickness shown = sum of layers. | P2 |
| REQ-F-05 | The engine shall plan vias: one centre via per coil per series pair, transfer vias between series pairs, terminal and ring vias; through vias by default; optional blind/buried spans; optional several vias per transition. | A2-TOP §4.3, A2-EQ EQ-11; open question Q3 (blind/buried) | must (through), could (blind/buried) | (a) Via count of default design = formula in architecture_draft.md §7.3 (UT-GEO-13). (b) Every through via clears all copper of layers it does not join by ≥ clearance (DRC, PR-01). (c) Via resistance included per EQ-11 with count per transition (UT-PHY-11). | P2 |
| REQ-F-06 | The coil generator shall support side styles radial and parallel, end styles arc, straight and stadium, a corner radius, and "triangular" inner turns whose inner end-turn moves outward when the sides converge. | A2-TOP §3.1 S1–S3; A2-EQ EQ-02 (gate `replace`: Xcoil fits 0 turns where D08 built 3) | must (radial, parallel, arc, triangular turns), should (straight, stadium, corner radius) | (a) D08 geometry (r_i 12.5, r_o 44, w 2.06, s 0.8 mm, 12 coils, 10 poles) yields 3 turns, ±1 turn vs EQ-02 (OR-04). (b) Generated length within ±6 % of the EQ-03 closed form (UT-GEO-07). | P2 |
| REQ-F-07 | The rotor model shall support double rotor, single rotor with opposite yoke, open single rotor; magnets as arc segments (constant α_p) or rectangular blocks (radius-dependent α_p(r)); inputs B_r, µ_r, thickness, air gap per side. | A2-EQ EQ-04, EQ-05; A2-REV Q-3, Q-4 | must | (a) Block 20 × 6 mm, 2p = 16: α_p = 0.853 / 0.547 / 0.402 at r = 18 / 28 / 38 mm, 1e-3 (UT-PHY-02). (b) Large-pole-pitch limit equals 1-D circuit to 1e-9 rel. (C1a, UT-PHY-01). | P2 |
| REQ-F-08 | The engine shall build phase connections star (default), delta and open, with phase rings and line terminals U, V, W (+ optional N) outside r_o, and warn when delta is chosen with k_w3 ≠ 0. | A2-TOP §3.4; A2-EQ EQ-09, EQ-19 | must (star), should (delta, open) | (a) Ke,LL = √3·Ke,ph (star), = Ke,ph (delta) exactly (UT-PHY-09). (b) Delta with 12/14 (k_w3 0.50) raises `RANGE_DELTA_TRIPLEN` (UT-WND-07). | P2 |
| REQ-F-09 | The engine shall generate a board outline (circle or regular polygon with corner radius), a centre bore and mounting holes. | XC `buildMechanical`; default outline A2-TOP §5.2 | should | Outline closed: every end point shared by exactly two entities after DXF export (KX-03); copper-to-edge clearance checked by DRC (UT-DRC-06). | P2 |
| REQ-F-10 | The engine shall run a **DRC on the generated copper** (trace–trace, trace–via/pad, via–via, pad–pad, copper–board edge/hole) and report the minimum measured clearance per check type with location and the violating objects. | Coordinator constraint; XC DRC tests DRC-01… (TEST_PLAN.md §DRC) | must | (a) Default design: measured min trace–trace clearance within 0.005 mm of the set clearance (UT-DRC-01). (b) Property: whenever a layout is produced without DRC errors, an independent brute-force checker finds no pair below clearance − 1e-6 mm (PR-01). (c) Fault injection: a 1 µm intrusion is detected (UT-DRC-03). | P2 |
| REQ-F-11 | The engine shall compute, for the generated copper, the quantities of Agent 2's equation list: Ke (phase, line), R at 20 °C and operating temperature, EMF waveform and THD, Kt, Kv, torque at the operating point, copper/eddy/circulating/delta losses, current density, mass, thermal estimate; and, **labelled as estimates**, inductance (EQ-14), IPC guideline current (EQ-15) and torque–speed envelope (EQ-20). | A2-EQ EQ-01…22 and gate summary | must (gates reuse / reuse with change / add), could (EQ-20) | Each value matches its A2-EQ reference calculation within the EQ's stated tolerance (OR-xx, UT-PHY-xx); each value carries a Traceable record (REQ-T-02). Values from `cannot verify yet` equations are displayed with status `unresolved` and the word "estimate" (UI-07). | P2 |
| REQ-F-12 | The engine shall evaluate the field at each copper layer's z and report per-layer and per-pair results (z, B₁, pair EMF phasor, pair resistance) and the circulating loss of parallel members. | A5-GAP G3; A2-EQ EQ-05–EQ-07 | must | Per-layer B₁ spread of the A2-REV C1d case reproduced (0.6828 / 0.6813 / 0.6805 T, 1e-4 rel.) (GR-03); two-member identity P_c = abs(E₁ − E₂)²/(2(R₁+R₂)) to 1e-12 (UT-PHY-08). | P2 |
| REQ-F-13 | The standalone UI shall show (1) the 2-D geometry with zoom, pan, layer visibility and phase identification, (2) the phase assignment (coil → phase, polarity) as table and diagram, (3) the layer configuration (stack-up, pairs, connections, vias), (4) the results with value, unit and status. | User wish (task statement); Agent 1 owns the screen design | must | Usability walkthrough UI-01…UI-06 passes; each of the four views reachable from the main window in ≤ 2 interactions; zoom 0.1×–200× without loss of stroke widths (vector rendering) (UI-03). | P2 |
| REQ-F-14 | The engine shall classify every input problem as **invalid**, **unsupported range** or **unbuildable** and return issues with stable code, severity, message, parameter path(s), value, limit and hint; it shall never raise an exception or return NaN/∞ for user input. | Coordinator task; XC "Validation" group (TEST_PLAN.md) | must | Seeded fuzzing of 1 000 random parameter sets per generator: 0 uncaught exceptions, 0 NaN/∞ in results (PR-05); every boundary in BV-01…BV-20 produces the documented code (BV-xx). | P2 |
| REQ-F-15 | The user shall save and load designs as a versioned JSON project file; older schema versions shall be migrated on load with a notice; files shall carry a canonical design hash. | ADR-0007 | must | Round trip save → load → save is byte-identical (UT-IO-01); a v1 file loads in v2 code with migration notice (UT-IO-04); hash changes iff a model input changes (PR-08). | P2 |
| REQ-F-16 | The application shall export SVG, DXF (complete board; outline only; holes only), `.kicad_pcb`, results JSON and CSV, and a PDF report, all generated from the same layout model. | XC exports (`exportSvg`, `exportDxf`, `exportKicad`, report.js); ADR-0002 | must (SVG, DXF, .kicad_pcb, JSON), should (PDF, CSV) | Independent parsers open every export (ezdxf audit 0 errors, `.kicad_pcb` parsed, PDF ≥ 1 page with "Key results"), entity counts equal the layout's primitive counts (KX-01…KX-06). | P2 |
| REQ-F-17 | The user should compare two or more designs side by side (key results with status). | XC `compareResults` | could | Comparison table shows identical values to the single-design results (UI-10). | P2 or Later |
| REQ-F-18 | A headless command-line interface shall compute, validate and export from a project file with defined exit codes (0 ok, 1 validation errors, 2 DRC errors, 3 internal error). | Testability, CI, golden regression (ADR-0006); Agent 3 N-13 | must | `embodic-cli compute examples/default.embodic.json --json out.json` exits 0 and writes results identical to the API call (UT-CLI-01). Entry points: `embodic` = standalone UI, `embodic-cli` = headless (naming as proposed by Agent 3, `dependency_and_tooling_draft.md` §4.1). | P2 |
| REQ-F-19 | The geometry engine shall accept further coil generators (serpentine, wave) through a generator interface without changes to winding, physics, DRC or exporters. | Coordinator constraint (keep serpentine/wave possible) | should | A stub "test generator" registered in tests produces a layout that passes through DRC, analysis and all exporters unchanged (UT-GEO-20). | P2 (interface), Later (generators) |
| REQ-F-20 | The engine could compute a torque–speed envelope (dq model with voltage and current limits). | A2-EQ EQ-20 (`cannot verify yet`) | could | Displayed only with status `unresolved` and a link to EQ-14 dependence (UI-07). | Later |
| REQ-F-21 | At start, the application shall load the default design with every default value marked `assumption` until the user changes it. | A2-TOP §5.2; REQ-T-06 | must | Fresh start: every input field of the default design shows the assumption marker (UI-08). | P2 |
| REQ-F-22 | The UI should provide undo/redo for parameter edits. | Usability (Agent 1 to confirm) | could | 50-step undo restores identical design hash (UI-11). | P2 or Later |
| REQ-F-23 | No silent value rewrites: the engine shall never change an input (it returns issues and suggestions); the UI may apply a suggestion automatically only with an inline notice next to the field ("Changed from X to Y: reason") plus Undo, announced politely; otherwise suggestions are applied by explicit user action. | Agent 1 `ux_analysis.md` C2 (Xcoil rewrites turns/coil count with only a 3.2 s toast, `verified` there); Agent 1 UX-AC-13 (`design_handoff_for_agent3.md` §4) — reconciled: engine purity (ADR-0001) + Agent 1's notice/Undo pattern | must | UI-15 / UX-AC-13: scripted clamp case → inline notice with old → new value and Undo; Undo restores the value and the previous design hash; engine API never returns a modified `DesignParameters`. | P2 |
| REQ-F-24 | The engine should place mounting holes from a fastener table (clearance-hole sizes) with edge, pitch and copper-keep-out checks. | Xcoil feature F-20 (Agent 3 `feature_inventory.md`); table values need a cited source (Agent 3 `migration_mapping.md` F-20) | should | UT-GEO-21: holes at the specified radius/count; violations reported as DRC `DRC_COPPER_HOLE`/mechanical issues. | P2 |
| REQ-F-25 | The application should ship presets: the default design and the oracle configurations (12/10 after D08, 12/16 after D09) as validation cases runnable from UI and tests. | Agent 3 N-12/F-03; A5-REG §C | should | UI-16 loads each preset; OR-xx tests use the same project files (`examples/`). | P2 |
| REQ-F-26 | The application should provide an equation reference view generated from the EQ registry (formula, sources, gate verdict, status), linked from every result's details. | Agent 3 F-60 proposal; Agent 1 C4 (formulas disconnected from numbers) | should | UI-17: every EQ-ID link in the results details opens the registry entry; reference view content equals the registry JSON. | P2 |
| REQ-F-27 | The UI should keep the last valid geometry visible (visually marked as outdated) while the current input is invalid or unbuildable. | Agent 1 `ux_analysis.md` W1 (Xcoil strength, `verified` there) | should | UI-18: enter an invalid value → previous drawing stays, marked "outdated", issue list shows the cause. | P2 |
| REQ-F-28 | The UI should show feasibility hints next to inputs (e.g. "8 turns per coil (max. 8)", balanced coil counts for the pole count). | Agent 1 W3; Agent 3 F-40 | should | UI-19: hints update with each recompute and match `Layout.turns_per_coil` / `Feasibility`. | P2 |
| REQ-F-29 | The application could export all outputs as one ZIP (with a plain-text summary) and could import Xcoil v3 parameter JSON for comparison. | Agent 3 F-55, F-57, N-10 | could | KX-11: ZIP contains every selected export; import maps all still-existing fields and reports dropped ones. | P2 or Later |
| REQ-F-30 | The geometry view could show a rotor-angle overlay of the magnets. | Agent 3 F-45 (Xcoil feature) | could | UI-20: magnet overlay rotates with the slider; no recompute triggered. | P2 or Later |
| REQ-F-31 | The standalone UI should autosave the current design to a recovery file in the user profile and remember the last project path. | Agent 3 `migration_mapping.md` F-04 (port with change) | should | UI-21: kill the process after an edit → next start offers recovery of that design (identical hash). | P2 |
| REQ-F-32 | Inputs that do not apply to the current configuration shall be hidden; a temporarily inapplicable input shall show the reason. | Agent 1 UX-AC-12; Xcoil defect C1 (23 disabled fields visible, `ux_analysis.md`) | must | UX-AC-12 configuration-matrix test (e.g. corner radius hidden or explained with straight ends). | P2 |
| REQ-F-33 | Placing on a KiCad board or exporting a layout with DRC errors shall require an explicit confirmation that lists the failures, with initial focus on the safe action (Cancel). | Agent 1 UX-AC-16; Xcoil defect C14; architecture §12 | must | UX-AC-16 scripted export with an injected DRC error; CLI equivalent requires `--allow-drc-errors` (UT-CLI-01). | P2 |

## 3. Non-functional requirements (REQ-N)

| ID | Statement | Rationale / source | Prio | Acceptance criteria | Phase |
|---|---|---|---|---|---|
| REQ-N-01 | A full recompute (validate → geometry → DRC → analysis) of the default design shall take < 1.0 s (95th percentile of 20 runs, warm) on the reference laptop. | Interactive design loop. The Xcoil JS engine needs 0.10–0.19 s for a comparable 12/16 sector design with 584 025 DRC pairs on a 2-core container (M-JS, `verified (measured)` for JS only). Agent 3 measured the DRC kernel `segSegDist` × 10⁶: Node 40 ms, literal CPython 1 813 ms (≈ 45×), NumPy vectorised 543 ms (`calculation_flow_and_port_notes.md` §4, `verified (run)` there) → vectorised DRC plus symmetry reuse needed (`inferred`). Threshold `assumption`. | must | PF-01 benchmark on the reference laptop; stage budget geometry ≤ 0.2 s, DRC ≤ 0.4 s, analysis ≤ 0.3 s (`assumption`). Until measured on the user's hardware the requirement stays `assumption`. | P2 |
| REQ-N-02 | The UI shall stay responsive during computation: input echo < 100 ms; recompute debounced 300 ms after the last keystroke and immediate on Enter/blur/selection; computation in a background worker; newer edits supersede running computations; within 300 ms of the last edit the results either update or show "Updating…" with previous values dimmed; a progress line when a compute exceeds 1 s; one polite announcement summarising the new result. | Agent 1 `design_spec_draft.md` §7.5 and UX-AC-22; thresholds `assumption` until the Python engine is measured | must | UI-05 (latency probe during a 3 s synthetic compute) and UX-AC-22 timing test. | P2 |
| REQ-N-03 | A large design (24 coils, 12 copper layers, 6 series pairs) shall recompute in < 5 s on the reference laptop. | Scaling headroom; `assumption` | should | PF-02. | P2 |
| REQ-N-04 | Results shall be deterministic: identical input → identical result JSON on the same platform and Python version; across Windows/Linux and Python 3.11–3.13 within 1e-9 relative for floats. | XC GEO-13 (determinism); golden regression. Agent 3: built-in `sum()` of floats uses Neumaier summation since Python 3.12, and libm results differ by up to 1 ulp between JS and Python (`calculation_flow_and_port_notes.md` §2.1–2.2, `verified` there) → numerically relevant sums must use one explicit method (`math.fsum`, explicit loop or NumPy) in all versions (`inferred`). | must | PR-09 (same platform byte-identical), PK-04 (cross-platform and cross-version rel. 1e-9); MT-06 lint: no built-in `sum()` over floats in `embodic.physics`/`embodic.drc`. | P2 |
| REQ-N-05 | The core engine and CLI shall run on Windows 10/11 x64 and Linux x86-64 with CPython 3.11, 3.12 and 3.13; the standalone UI on Windows 10/11 x64 (must) and Linux (should). | User has Python 3.11+ on Windows (BRIEF §1). NumPy ≥ 2.5 requires Python ≥ 3.12 and NumPy 2.4.x is the last line with 3.11 Windows wheels (PyPI metadata, `verified` 2026-10-04) → version ranges must be chosen per Python version. | must | CI matrix {Windows, Linux} × {3.11, 3.12, 3.13} green (PK-01); dependency resolution with Python 3.11 succeeds from a clean venv (PK-02). | P2 |
| REQ-N-06 | Installation and packaging shall be reproducible: `pip install embodic` (core + CLI), extras `embodic[desktop]`, `embodic[kicad]`; a lock file with hashes for every supported Python version; an optional Windows one-folder bundle built by one documented command. | User wish (reproducible install/run/package); ADR-0008 | must (pip + lock), should (bundle) | PK-03: two builds from the same commit produce wheels with identical file lists and identical SHA-256 of all `.py` files; bundle smoke test starts and computes the default design (PK-05). | P2 |
| REQ-N-07 | A README shall give exact install, run, test and package commands for Windows (PowerShell) and Linux; a new user with Python 3.11 shall reach the first computed result in < 10 minutes. | User wish; time `assumption` | must | PK-06 dry run on a clean Windows VM by Agent 4 or the user, timed. | P2 |
| REQ-N-08 | Code structure: engine packages shall not import UI or KiCad modules (enforced); public functions fully type-annotated; static type check strict on the core; lint clean; function complexity ≤ 10 (McCabe) and module length ≤ 600 lines unless justified in a comment. | Coordinator constraint (engine purity); user wish (readable code); thresholds `assumption` | must | CI gates: import-linter contracts (ADR-0001), mypy --strict on `embodic.*` core, ruff (incl. C901 ≤ 10) — 0 findings (MT-01…MT-03). | P2 |
| REQ-N-09 | Every public function and dataclass shall have a docstring stating purpose, units of every dimensional argument/return, assumptions, validity limits and EQ-IDs; comments explain *why*, not *what*. | User wish; brief rule 2 (references) | must | MT-04 docstring checker (ruff pydocstyle rules + custom check that every physics function docstring contains "Units:" and an EQ-ID) — 0 findings; reviewer checklist in PR template. | P2 |
| REQ-N-10 | Core test coverage ≥ 90 % lines and ≥ 80 % branches; every REQ-ID has ≥ 1 automated test or a documented manual test. | Linked requirements–tests (user wish); thresholds `assumption` | must | pytest-cov report in CI; traceability matrix generator lists 0 untested REQ (TR-01). | P2 |
| REQ-N-11 | Colour contrast shall meet WCAG 2.2 AA: text ≥ 4.5:1 (large text ≥ 3:1) — SC 1.4.3; UI components and graphical objects needed for understanding ≥ 3:1 against adjacent colours — SC 1.4.11. | WCAG 2.2 SC 1.4.3, 1.4.11 (`verified` thresholds); white/grey/black palette makes grey-on-grey a real risk (`inferred`) | must | AX-01: automated contrast computation over all theme colour pairs used for text and for copper/phase rendering — 0 pairs below threshold. | P2 |
| REQ-N-12 | All functions shall be operable by keyboard (SC 2.1.1) in visual order without keyboard traps, with a visible focus indicator (SC 2.4.7, 2 px ring + 2 px offset per Agent 1) that is not entirely hidden (SC 2.4.11); F6 cycles the six regions, Alt+1…6 select steps, tabs and toolbars use arrow keys; the geometry canvas is focusable and supports keyboard pan/zoom/fit, with single-key shortcuts active only while it has focus. | WCAG 2.2 SC 2.1.1 (A), 2.4.7 (AA), 2.4.11 (AA); Agent 1 UX-AC-07/08/09 and keyboard map (`design_spec_draft.md` §8.2) | must | AX-02 keyboard-only scenario (open project, edit three parameters, recompute, open a result's EQ details, export SVG — no pointer events); AX-03 focus indicator on every stop; UX-AC-07 Tab-order walk vs visual order; UX-AC-09 canvas keys. | P2 |
| REQ-N-13 | Pointer targets shall be ≥ 24 × 24 device-independent px at 100 % scaling (control height 32 px per Agent 1), except the WCAG 2.5.8 exceptions. The 44 × 44 px coarse-pointer/phone size of UX-AC-10 applies only if the web option C-B1 is chosen. | WCAG 2.2 SC 2.5.8 (AA) (`verified` threshold); Agent 1 UX-AC-10, `design_spec_draft.md` §5 | must | AX-04 enumerates interactive widgets and checks their geometry ≥ 24 × 24. | P2 |
| REQ-N-14 | Colour shall not be the only means of conveying information (SC 1.4.1): phases, polarity, layers and status shall also be distinguishable by text label, line pattern, hatch or icon. | WCAG 2.2 SC 1.4.1 (A); greyscale palette (BRIEF §1) | must | AX-05: render the default design in pure greyscale and in simulated deuteranopia; a reviewer identifies phase and polarity of 12 coils with 100 % accuracy from labels/patterns alone. | P2 |
| REQ-N-15 | The desktop UI shall work from a minimum window of **960 × 540 device-independent px** (= a 1920 × 1080 screen at 200 % scaling) up to full screen: ≥ 1280 px wide → three panes (step panel, figure, results rail); 960–1279 px → two panes with the results rail as a collapsible bottom panel (Agent 1's tablet pattern); panels scroll vertically; the drawing and wide tables scroll inside their own containers; no horizontal scrolling of form panels. Phone layouts (Agent 1 mockup 06, "no horizontal scroll at 360 px", UX-AC-11) are out of scope with the desktop option and apply only if C-B1 is chosen. | Laptop use at 100–200 % scaling; 960 × 540 = 1920/2 × 1080/2 (`inferred`, arithmetic); Agent 1 breakpoints (`design_spec_draft.md` §5) | must | UI-09 screenshots at 960 × 540, 1280 × 720 and 1920 × 1080 at 100/150/200 %: no clipped text, no overlapping controls, no horizontal scrollbar on form panels. | P2 |
| REQ-N-16 | Controls, results and status labels shall expose accessible names and roles; invalid inputs expose an error state with the message as accessible description. | Qt widgets implement accessibility for built-in widgets (https://doc.qt.io/qt-6/accessible-qwidget.html, `verified` statement); custom views need an accessible interface (same page); Agent 1 UX-AC-14 (`aria-invalid` equivalent) | must | AX-06 manual check with Windows Narrator: every input announces label, value and unit; every result announces value, unit and status; an invalid input announces its message. | P2 |
| REQ-N-17 | The application shall work fully offline and shall not send telemetry; the only network-like channel is the local KiCad IPC socket when the user invokes KiCad functions. | Privacy; offline lab use (`assumption`) | must | PK-07: run the full UI and CLI test suite with network disabled — all pass; code scan finds no HTTP client imports in core/UI. | P2 |
| REQ-N-18 | No user-visible crash: unexpected internal errors shall be caught by the adapter, logged with a correlation ID and shown as an English error message offering to save the project. | Robustness | must | UI-12 fault injection (engine raises) → message shown, project saved, process alive. | P2 |
| REQ-N-19 | Every runtime and build dependency shall have a recorded licence compatible with the chosen embodic licence; no code from GPL references (magnetless_motor GPL-3.0, kimotor GPL-2.0) shall be copied. | BRIEF §3 rule 7; DL D-003; ADR-0008 | must | PK-08: licence report (pip-licenses) matches the allow-list; THIRD_PARTY_LICENSES file complete; code-similarity review of plugin code against kimotor by Agent 4 (P3). | P2 |
| REQ-N-20 | The application should write a rotating log file (no personal data, design hash and app version in every session header). | Supportability | should | UT-LOG-01: log contains no user name/path components beyond the per-user log directory; rotation at 1 MB × 5 files (`assumption`). | P2 |
| REQ-N-21 | Geometry shall use float64 and a geometric tolerance of 1e-6 mm for coincidence tests; the KiCad nm conversion shall not break connectivity. | XC GEO-01 tolerance; REQ-K-08 | must | PR-04: after mm → nm rounding every connected end-point pair is identical in nm. | P2 |
| REQ-N-22 | Cold start of the standalone UI to an interactive window could be < 3 s on the reference laptop. | Usability; `assumption` | could | PF-03. | P2 |
| REQ-N-23 | The geometry view and all phase legends shall offer a greyscale mode in which phases A/B/C are distinguished by lightness, hatch (none / 45° / 135°) and labels; this mode is used automatically for print/PDF and Windows high-contrast. | Agent 1 UX-AC-05, tokens `--phase-a/b/c-grey` (`design_handoff_for_agent3.md` §1); REQ-N-14 | must | UX-AC-05 screenshot in greyscale mode; forced-colours run; AX-05. | P2 |
| REQ-N-24 | Every input shall show its unit visibly and include the unit in its accessible description (with hint, and the error message first when invalid). | Agent 1 UX-AC-15; Xcoil gap A3 (0 of 86 inputs had a description, `ux_analysis.md`) | must | UX-AC-15 widget scan; AX-06. | P2 |
| REQ-N-25 | Charts shall use one unit per y axis, a legend for ≥ 2 series plus direct labels, a data-table alternative, a keyboard-reachable read-out, and the status badge + EQ links of the plotted quantity. | Agent 1 UX-AC-18 and §9; Xcoil defect C9 (three units on one axis) | must | UX-AC-18 chart audit. | P2 |
| REQ-N-26 | No animation shall run by default; the OS "reduce animations" setting shall disable all transitions. | Agent 1 UX-AC-20 | should | UX-AC-20 emulation (OS animation setting off) shows no transitions. | P2 |

## 4. KiCad plugin and integration requirements (REQ-K)

Evidence base: A5-KI (SWIG deprecated in 9.0, removal planned 11.0; IPC API 9.0+, PCB editor only, running GUI
required, per-plugin venv with KiCad's bundled Python, no plot/export, no DRC call found). Unresolved items T1–T5
(A5-KI §4) gate several requirements.

| ID | Statement | Rationale / source | Prio | Acceptance criteria | Phase |
|---|---|---|---|---|---|
| REQ-K-01 | The application shall export a `.kicad_pcb` file (tracks, arcs, vias, terminal pads, outline, holes, nets; should also write the stack-up section) that opens in KiCad 9.x without error, independently of any plugin. | Works without KiCad running; Xcoil already validated its writer with kiutils (XC `validate_exports.py`). Which file-format version KiCad 9 writes, its copper-layer ordinals, the stack-up syntax, and whether 9.x opens the Xcoil 20221018 format unchanged: `unresolved` (Agent 3 `kicad_plugin_feasibility.md` K-3, smoke test T0). | must | KX-01 parser counts = layout counts; KS-01 (= Agent 3's T0) user opens the file in KiCad 9.x, saves it, reports the format version, and runs KiCad DRC: 0 errors from embodic copper (manual smoke test). | P2 |
| REQ-K-02 | The application shall provide a KiCad 9.x **IPC API** plugin (PCM `runtime: "ipc"`, `plugin.json`) that places the embodic copper of a project on the open board in one commit (single undo step). | User request (DL D-004); IPC is the non-deprecated route (A5-KI §1, §5) | must if T2/T4 confirm feasibility; otherwise should | KS-02: on the user's KiCad 9.x the plugin appears in the PCB editor, the default design is placed, Edit ▸ Undo removes it in one step; item counts equal the layout's counts. | P2 |
| REQ-K-03 | The plugin should read the board's stack-up (copper count, copper and dielectric thicknesses) and offer it as the embodic stack-up. | `Board.get_stackup()`, `get_copper_layer_count()` (kipy 0.8.0, A5-KI §3; copper count added 0.5.0 / KiCad 9.0.5) | should | KS-03: imported stack-up equals the KiCad board setup values to 1 µm. | P2 |
| REQ-K-04 | Re-applying a design shall replace only items previously placed by embodic (tracked by an identifier) and never modify other board items. | Safety of user's board | must | KS-04: board with user-drawn items + embodic items → re-apply with changed turns → user items unchanged (count and UUIDs), embodic items replaced. | P2 |
| REQ-K-05 | The engine packages shall not import `kipy` or `pcbnew`; all KiCad calls shall live in `embodic_kicad_plugin`. | Coordinator constraint; ADR-0001 | must | MT-01 import-linter contract. | P2 |
| REQ-K-06 | The plugin shall check the KiCad/API version at start (`KiCad.check_version()` / `get_version()`) and show a clear English message when unsupported. | Which kicad-python version matches the user's 9.0.x is `unresolved` (A5-KI §3, T4) | must | KS-05: running with a mismatched kicad-python version shows the message and changes nothing on the board. | P2 |
| REQ-K-07 | Inside KiCad's per-plugin venv the plugin should depend only on `kicad-python`, `embodic` (core) and NumPy — no GUI toolkit and no web server. | Dependencies are pip-installed on first load (A5-KI §3, `verified`); offline installation `unresolved` (G13) → keep footprint minimal (`inferred`) | should | KS-06: `requirements.txt` contains ≤ 3 top-level entries; first-load installation succeeds offline from a local wheel directory (procedure to be confirmed by T2). | P2 |
| REQ-K-08 | Geometry shall be converted from mm (float) to KiCad internal units (nm, integer) exactly once, at the adapter, with ≤ 1 nm rounding and preserved connectivity. | kipy units are nanometres (A5-KI §5 item 5, `verified`) | must | PR-04; KS-02 KiCad's connectivity shows each phase as one net without unconnected-item markers. | P2 |
| REQ-K-09 | Placed copper should carry one net per electrical node: per phase (U, V, W) for the open connection, one common net when an on-board star/delta interconnect joins the phases, so that KiCad connectivity is consistent and KiCad DRC raises no false shorts. | XC `exportKicad` uses `PHASE_A/B/C` or a single `WINDING` net when the interconnect is drawn (engine.js l.2886–2892, `verified`); KiCad clearance applies only between different nets, so KiCad cannot check turn-to-turn clearance inside one phase (Agent 3 `kicad_plugin_feasibility.md` §3, `inferred`) → embodic DRC stays the authority (REQ-F-10). | should | KX-02 (file) and KS-02 (plugin): every primitive has a non-empty net; net count = number of electrical nodes; KiCad DRC shows no shorting-items errors. | P2 |
| REQ-K-10 | The plugin could start the standalone embodic UI connected to the current board (child process inheriting KiCad's IPC environment variables). | Socket path passed in environment variables (A5-KI §1, `verified`); the variables are `KICAD_API_SOCKET` and `KICAD_API_TOKEN` (Agent 3 `kicad_plugin_feasibility.md` §4 item 2, `verified (doc extract)` there); child-process connection on Windows `unresolved` (T3) | could | KS-07 (after T3): UI launched from the plugin reads the board stack-up and places a design. | P2 or Later |
| REQ-K-11 | The product shall not depend on the SWIG `pcbnew` bindings. A SWIG fallback may only be added by a superseding ADR after T1/T2 show an essential gap. | SWIG deprecated in 9.0, removal planned 11.0 (A5-KI §2) | must | MT-01 import-linter forbids `pcbnew` everywhere. | P2 |
| REQ-K-12 | The application could run KiCad's own DRC on an exported board through `kicad-cli` and show its JSON report as a complementary check. | `kicad-cli pcb drc --format json --exit-code-violations` is documented in the KiCad 9.0 CLI manual (Agent 3 `kicad_plugin_feasibility.md` §2, `verified (doc extract)` there); not run (`not tested`, A5-KI T5) | could | KS-08 (after T5): report imported; violations listed with location. | P2 or Later |
| REQ-K-13 | If embodic is distributed through the official KiCad PCM, the plugin package shall use an open-source licence compatible with the GNU GPL. | PCM rule (A5-KI §2, EV-K3, `verified`) | should (conditional on user's licence choice) | Licence file present and listed in PCM metadata (PK-09). | P2 |
| REQ-K-14 | No silent layer remap: placement shall be blocked with an explicit message when the open board has fewer copper layers than the design, offering "change design" or "cancel"; thickness mismatches are warnings. | Agent 1 UX-AC-21 and `design_spec_draft.md` §10.6 item 2; `get_copper_layer_count()` (A5-KI §3) | must | KX-08 with a fake 4-layer board and a 6-layer design → no items created, message shown/logged; KS-02 variant. | P2 |
| REQ-K-15 | When the plugin opens an embodic window (launcher, REQ-K-10), that window shall fit 880 × 600 px with the Place action visible without scrolling, read the board's copper layer count and pre-fill the stack-up. | Agent 1 UX-AC-21, §11 (plugin dialog); realised as a compact mode of the standalone app (ADR-0004 amendment), because the plugin venv carries no GUI toolkit | could (depends on T3) | KS-07 + UX-AC-21 on the user's machine. | P2 or Later |

## 5. Traceability and evidence-display requirements (REQ-T)

| ID | Statement | Rationale / source | Prio | Acceptance criteria | Phase |
|---|---|---|---|---|---|
| REQ-T-01 | Every displayed number shall show value, unit, exactly one status badge (five values, shape-coded per Agent 1: verified ✓, inferred ≈, assumption ◇, unresolved ?, not tested ○) and a visible EQ-ID link — or a tag `input` / `derived` / `count` when no equation applies; evidence IDs, assumptions, inputs and validity notes are reachable in ≤ 1 interaction (keyboard accessible). | User wish (units/assumptions/limits/status shown); coordinator constraint; Agent 1 UX-AC-01/02, status badge spec (`design_handoff_for_agent3.md` §2) | must | UX-AC-01 (each result value has unit + badge), UX-AC-02 (EQ link or tag); UI-06; AX-02. | P2 |
| REQ-T-02 | Every computed result object shall carry value, unit, quantity name, EQ-ID(s) or kind tag (`input`/`derived`/`count`), evidence ID(s), assumptions used, input references and a status label (`verified / inferred / assumption / unresolved / not tested`); the UI takes status and links from this data, never from hard-coded labels. | Coordinator constraint; ADR-0003; Agent 1 handoff §5 ("status must come from data") | must | UT-RES-01: walk all fields of `AnalysisResult` for the default design — no field is a bare float; all IDs resolve in the registry. | P2 |
| REQ-T-03 | The status of a result shall be the weakest status among its equation(s), its inputs and its assumptions (order defined in ADR-0003); the contributing items shall be listed. | Consistency; avoids over-claiming (brief rules 3, 5, 6) | must | UT-RES-02 truth table over all status combinations. | P2 |
| REQ-T-04 | The application shall ship an equation registry (EQ-ID, title, formula, gate verdict, status, EV-IDs, validity, tolerance, linked test IDs) and an evidence registry (EV-ID, claim, document, page/section, status); every ID shown in the UI resolves to an entry. | A2-EQ and A5-REG are the content sources | must | UT-RES-03 registry integrity: no dangling IDs, all EQ-IDs used by code exist, all registry entries have a source. | P2 |
| REQ-T-05 | Gate enforcement: an equation with gate `cannot verify yet` shall only produce results with status `unresolved` labelled "estimate"; an equation may carry status `verified` only if the registry links ≥ 1 test ID that passed in the current CI run. | A2-EQ gate vocabulary; brief rule 3 | must | TR-03 CI check fails the build when a `verified` EQ lacks a passing linked test. | P2 |
| REQ-T-06 | Default values shall be marked as `assumption` (with their source note) in UI, project file and reports until the user edits them. | A2-TOP §5.2 (all defaults are assumptions) | must | UI-08; UT-IO-05 (project file keeps per-field provenance). | P2 |
| REQ-T-07 | Every export and report shall contain the embodic version, engine version, registry version, design hash, generation date and the status labels of all reported values. | Reproducibility; traceability chain | must | KX-05 / UT-IO-06: metadata fields present in SVG `<metadata>`, DXF header comment, `.kicad_pcb` generator/comment, JSON, PDF. | P2 |
| REQ-T-08 | Validity limits of each equation (e.g. w or t > δ/3, outside magnet span, Q/2p > 1 low utilisation) shall be evaluated and shown next to the affected results. | A2-EQ EQ-13 (δ/3 threshold `assumption`), EQ-05 edge validity, A2-TOP §2.4 item 5 | must | UT-PHY-13: a design with w > δ/3 raises `RANGE_SKIN_DEPTH` and marks eddy and resistance results. | P2 |
| REQ-T-09 | Requirements, acceptance criteria, tests and code shall be linked: every automated test declares the REQ-ID(s) it covers (pytest marker); CI generates the requirements-to-tests matrix. | User wish (linked requirements–acceptance–tests) | must | TR-01/TR-02: matrix generated; 0 tests without REQ-ID; 0 must-REQs without a test. | P2 |
| REQ-T-10 | Computed values shall never be called "measured"; the UI and reports shall use "computed", "estimate" or "reference (paper, measured)" for oracle values. | Brief rule 5 | must | LG-03 wording scan of strings and report templates. | P2 |
| REQ-T-11 | The UI shall not claim magnetic balance, torque or efficiency from geometry or phase angles alone; "balanced winding" shall be explained as phasor symmetry of the coil assignment. | Brief rule 6 | must | LG-04 wording scan + reviewer check of help texts. | P2 |
| REQ-T-12 | Oracle comparison results (embodic vs published case) should be viewable in the application or report, with the paper reference, page and tolerance. | A5-REG §C, A2-EQ tolerances | should | UI-13 shows O1/O2 comparison rows with source and tolerance. | P3 |
| REQ-T-13 | Each result shall have a "How was this computed" disclosure listing: equation (EQ title + formula), inputs (quantity, value + unit, origin user/default/imported, status), assumptions, limitations/validity flags, validation (tolerance, oracle, run state), sources (registry entry + paper/page), and a "Copy trace" action. | Agent 1 UX-AC-02, `design_spec_draft.md` §10.4; Xcoil defect C4 | must | UX-AC-02 content check per result; UI-06. | P2 |
| REQ-T-14 | Drawings not produced by the engine shall carry "Illustrative, not computed"; engine drawings and every export shall carry the engine version stamp (and design hash). | Agent 1 UX-AC-17; REQ-T-07 | must | UX-AC-17 DOM/widget and file-content check; KX-05. | P2 |

## 6. Language and branding requirements (REQ-L)

| ID | Statement | Rationale / source | Prio | Acceptance criteria | Phase |
|---|---|---|---|---|---|
| REQ-L-01 | All software-facing text (UI strings, messages, warnings, tooltips, chart and axis labels, export metadata, report text, plugin messages, log messages) shall be in English. | BRIEF §3 rule 8 | must | LG-01: automated scan of the string catalogue, report templates and plugin files finds 0 characters in the Thai block U+0E00–U+0E7F and 0 words outside an English allow-list (spell-check dictionary + glossary). | P2 |
| REQ-L-02 | UI strings should be defined in one catalogue module, not inline in widget code. | Reviewability of wording | should | LG-02: lint rule — no string literals passed to widget text setters outside the catalogue. | P2 |
| REQ-L-03 | The product name shall be "embodic" in window title, about box, report header, export generator fields and plugin name; the name "Xcoil" shall not appear in any user-facing text or output. | BRIEF §1 (brand) | must | LG-05: scan of strings, exports and report → 0 occurrences of "xcoil" (case-insensitive). | P2 |
| REQ-L-04 | The primary UI palette shall be white, grey and black; any other colour shall be secondary — for status semantics and, **only if the user approves**, a muted data palette for phases — always paired with a non-colour cue (label, pattern, icon) and meeting REQ-N-11/N-14. | BRIEF §1 (UI colours); Agent 1 proposes CVD-checked desaturated phase colours with greyscale fallback (`ux_analysis.md` §6 B7, §7 item 3); Agent 3 raises the same question (`migration_mapping.md` X-1) → user decision (open point 7) | must | AX-01 contrast check + AX-05 greyscale test + design review against Agent 1's palette tokens. | P2 |
| REQ-L-05 | Brand assets (logo, symbol, wordmark) shall be taken unmodified from the brand folder; no personal data from the pitch deck shall appear in code, UI or outputs. | BRIEF §2 (brand assets; pitch deck contains a personal name) | must | LG-06: asset checksum list; scan for personal names in the repository = 0. | P2 |
| REQ-L-06 | Engineering terms should follow one English glossary (coil, turn, layer pair, phase belt, star of slots, centre via, transfer via …). | Consistency between UI, docs and code identifiers | should | LG-07 glossary check of the string catalogue. | P2 |
| REQ-L-07 | Number formatting shall be locale-independent (decimal point "."), with SI units and prefixes, a space between value and unit, 3 significant figures by default, the minus sign "−", digit grouping from 4 digits; geometry in mm. | Engineering clarity; Agent 1 `design_spec_draft.md` §13 | must | UT-UNI-03: results formatted identically under a German/Thai Windows locale setting. | P2 |
| REQ-L-08 | Counts (coils, turns, poles, vias, layers) shall be shown as integers; comparison deltas shall use sign + glyph (▲/▼) and the words better/worse only where Engineering defines the preferred direction — never red/green alone. | Agent 1 UX-AC-19; Xcoil defects C10, C11 | must | UX-AC-19 formatting test. | P2 |
| REQ-L-09 | UI spelling variant shall be consistent (British proposed: "centre", "colour") pending user decision UD-17. | Agent 1 `design_spec_draft.md` §13, Q7 | should | LG-07 glossary/spelling check against the chosen variant. | P2 |

## 7. Measurement note (M-JS)

Command run by Agent 6 on 2026-10-04 (read-only use of the reference engine):
`node -e "…E.compute(Object.assign({}, E.DEFAULTS, {topology:'sector', poles:16, sectors:12, coilSides:'parallel', rIn:18, rOut:38, traceWidth:0.5, clearance:0.2}))…"`
on the agent container (2 vCPU, "Intel(R) Xeon(R) Processor @ 2.10GHz", Node v22.22.2). Three runs: 194 / 117 / 137 ms
(with `coilLayers: 6`: 146 / 105 / 107 ms); DRC pairs checked 584 025. Xcoil's own `timing.js` presets: 121–3 769 ms.
Status: `verified (measured)` for the **JS engine on this container only**; it is not a measurement of embodic and not of
the user's laptop. Use: order-of-magnitude input for REQ-N-01 only.

## 8. Open points affecting requirements

All user decisions are consolidated in `user_decisions_needed.md` (UD-01 … UD-26). Requirement-level open points:

1. Reference laptop specification (REQ-N-01/03/22) — UD-15.
2. embodic licence (REQ-N-19, REQ-K-13) — UD-02.
3. Blind/buried vias (REQ-F-05) — UD-11.
4. Plugin with or without its own window (REQ-K-07, K-10, K-15) — UD-04; depends on T2/T3.
5. Agent 1's design (`design_spec_draft.md`, `design_handoff_for_agent3.md`) is now mapped: UX-AC-01…22 → §9 below.
6. **Resolved (reconciliation round 1):** with the desktop option the minimum window is 960 × 540 device-independent px
   (REQ-N-15); phone layout, "no horizontal scroll at 360 px" and 44 px coarse-pointer targets apply only if the user
   chooses C-B1 (UD-01).
7. Phase colours vs the white/grey/black palette (REQ-L-04) — UD-05.
8. **Resolved:** the core is written to Python 3.11 syntax with no 3.12-only features; consequences of KiCad's bundled
   Python version are stated in architecture_draft.md §17 R10 (pending T1/T2).

## 9. Mapping of Agent 1's UX acceptance criteria to requirements

Source: `docs/phase1/design/design_handoff_for_agent3.md` §4 (UX-AC-01…22). Agent 1's "how to test" is web/DOM-phrased;
with the desktop option (ADR-0005) the same checks run on the Qt widget tree (`objectName` = Agent 1's element id,
architecture_draft.md §19).

| UX-AC | Criterion (short) | Requirement(s) | Desktop note |
|---|---|---|---|
| 01 | Value + unit + exactly one of five status labels on every numeric result | REQ-T-01, T-02 | — |
| 02 | EQ-ID link or tag input/derived/count; "How was this computed" disclosure | REQ-T-01, T-02, T-13 | — |
| 03 | No "Xcoil", no Thai, no personal names; logo present | REQ-L-01, L-03, L-05 | — |
| 04 | Chrome neutral; colour only on phase marks/charts and pass/fail | REQ-L-04 | style-sheet scan instead of computed CSS |
| 05 | Phases distinguishable without colour; greyscale mode | REQ-N-14, N-23 | Windows high contrast instead of forced-colors emulation |
| 06 | Text ≥ 4.5:1, controls/focus ≥ 3:1 | REQ-N-11 | token script (AX-01) instead of axe-core |
| 07 | Keyboard reach in visual order, no trap, F6 regions, arrow keys in tabs/toolbars | REQ-N-12 | — |
| 08 | Visible focus on every focusable element | REQ-N-12 | — |
| 09 | Canvas focusable, keyboard pan/zoom, single keys only while focused | REQ-N-12, F-13 | — |
| 10 | Targets ≥ 24 px desktop, ≥ 44 px coarse pointer/phone | REQ-N-13 | 44 px part out of scope unless C-B1 |
| 11 | No horizontal page scroll at 360 px | REQ-N-15 | replaced by: no horizontal scroll of form panels at the 960 × 540 minimum window; 360 px only if C-B1 |
| 12 | Inapplicable fields hidden; temporary inapplicability explained | REQ-F-32 | — |
| 13 | Engine-changed value → inline notice old → new + Undo, polite | REQ-F-23 | engine itself never changes inputs; the UI applies and announces |
| 14 | Invalid input: error state + inline message; Checks lists it; last valid geometry dimmed with stamp | REQ-F-14, F-27, N-16 | accessible error state instead of `aria-invalid` |
| 15 | Every input shows its unit; unit in accessible description | REQ-N-24 | — |
| 16 | Place/export with DRC failures needs confirmation listing failures; focus on safe action | REQ-F-33 | — |
| 17 | "Illustrative, not computed" vs engine version stamp | REQ-T-14, T-07 | — |
| 18 | Charts: one unit per axis, legend + direct labels, data table, keyboard tooltip | REQ-N-25 | — |
| 19 | Counts as integers; deltas sign + glyph, not red/green | REQ-L-08, F-17 | — |
| 20 | Reduced motion disables transitions; no animation by default | REQ-N-26 | OS animation setting instead of `prefers-reduced-motion` |
| 21 | Plugin dialog fits 880 × 600, reads copper layer count, blocks missing layers | REQ-K-14 (must), K-15 (could), K-03 | realised as the launcher's compact window (needs T3); blocking rule applies to every placement path |
| 22 | Results update ≤ 300 ms or "Updating…" with dimmed values; polite summary | REQ-N-02 | — |

## 10. Mapping of Agent 3's feature IDs to requirements (reconciliation)

Agent 3's inventory (`docs/phase1/software/feature_inventory.md`, F-01…F-64) and new features
(`migration_mapping.md` §2, N-01…N-13) map as follows. Xcoil features that Agent 3 proposes to drop or defer (serpentine
F-09/F-10/F-23, wave F-13…F-15) are covered only by the generator interface REQ-F-19 (Agent 3 recommendation "D: defer").

| Agent 3 ID | Requirement(s) |
|---|---|
| N-01 spiral generator | REQ-F-01, F-03, F-05, F-06 |
| N-02 phase assignment display | REQ-F-02, F-13 |
| N-03 layer configuration display | REQ-F-03, F-04, F-13 |
| N-04 units/assumptions/status on every result | REQ-T-01, T-02, T-03 |
| N-05 traceability | REQ-T-01…T-09 |
| N-06 KiCad plugin host | REQ-K-02, K-03, K-10 |
| N-07 magnet geometry | REQ-F-07 |
| N-08 closed-form cross-checks shown | REQ-F-06 (acceptance), REQ-F-28 (hints) |
| N-09 KiCad DRC import | REQ-K-12 |
| N-10 schema versioning, Xcoil import | REQ-F-15, F-29 |
| N-11 copper-loss-budget current | REQ-F-11 (EQ-21) |
| N-12 validation case library | REQ-F-25, T-12 |
| N-13 headless entry point | REQ-F-18 |
| F-01 validation | REQ-F-14, F-23, F-32 |
| F-02/F-06/F-07 form, reset, quick setters | REQ-F-13 (Agent 1 design) |
| F-03 presets | REQ-F-25 |
| F-04 autosave | REQ-F-31 |
| F-05/F-54 project JSON | REQ-F-15 |
| F-08 debounced recompute, last-good figure | REQ-N-02, F-27 |
| F-11 wide end-turns | REQ-F-06 (`end_width_*` fields) |
| F-12 sector coils | replaced by REQ-F-01 |
| F-16 primitives | ADR-0002 |
| F-17/F-18 interconnect, pads | REQ-F-08 |
| F-19/F-20/F-25 outline, fasteners, mechanical issues | REQ-F-09, F-24 |
| F-21/F-22 stack-up model/editor | REQ-F-04, F-13 |
| F-24/F-26 DRC, warnings | REQ-F-10, F-14, T-08 |
| F-27…F-36 analysis | REQ-F-07, F-11, F-12, F-20 |
| F-37…F-40 summary, results, DRC tab, hints | REQ-F-13, F-28, T-01 |
| F-41 compare | REQ-F-17 |
| F-42…F-47 figure and interactions | REQ-F-13, F-30, N-12, N-14 |
| F-48 3-D view | not required in P2 (could; kept possible, app_type_comparison.md §4) |
| F-49…F-53 exports | REQ-F-16, K-01 |
| F-55/F-57 ZIP, README | REQ-F-29 |
| F-56 PDF report | REQ-F-16, T-07 |
| F-58 save mechanism | adapter concern (no requirement) |
| F-59/F-64 tests, golden tooling | REQ-T-09, ADR-0006 |
| F-60 reference tab | REQ-F-26 |
| F-61 guide tab | not yet a requirement (content review needed; open) |
| F-62/F-63 status bar, shell/theme | REQ-F-13, L-03, L-04 |
