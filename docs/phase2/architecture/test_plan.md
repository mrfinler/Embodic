Prepared by: Agent 6 - Software Architecture Specialist - model: claude-opus-5-5

# embodic Phase 2 test plan (build contract v1, 2026-10-04)

This plan updates `docs/phase1/architecture/test_plan_draft.md`. Every Phase 1 test not listed under "Withdrawn tests"
stays in force with its Phase 1 ID, check and criterion. This file adds the Phase 2 tests, amends the ones whose subject
changed, and holds the generated requirements-to-tests matrix. No embodic test has run yet: every test below is
`not tested`.

## 1. What changed and why

| Change | Reason |
|---|---|
| KiCad tests withdrawn; MT-07 guards the withdrawal | D-009 |
| Golden regression gains layout-level cases for serpentine and wave (GR-20, GR-21) and function-level cases for the M1 kernels (GR-17, GR-18) | D-013 faithful ports; M1 pilot |
| Generator, draft, provenance, session, export and EC-05 tests added | D-014, D-012, D-011, D-009, DEF-23 |
| UI tests run with pytest-qt on the `offscreen` Qt platform; view-model tests need no Qt at all | D-010; Qt-free view-models (interfaces.md §11) |
| DRC soundness and rotation symmetry extended to every generator (PR-13, PR-14) | one DRC and one physics path for all topologies (ADR-0012) |

## 2. Levels, tools and where they run

| Level | Tool (licence, PyPI read 2026-10-04) | Location | Runs |
|---|---|---|---|
| Unit (UT) | pytest 9.1.1 (MIT), pytest-cov 7.1.0 (MIT) | `tests/unit/<package>/` | every commit |
| Golden (GR) | Node 22 dumper (dev only) + pytest comparators | `tools/golden/`, `tests/golden/` | every commit (fixtures committed; CI needs no Node) |
| Oracle (OR) | pytest, `xfail` until prerequisites exist | `tests/unit/physics/oracles/` | every commit |
| Property (PR), boundary (BV) | hypothesis 6.168.3 (MPL-2.0, dev only), pytest | `tests/unit/property/`, `tests/unit/boundary/` | fast profile per commit, long profile nightly |
| UI | pytest-qt 4.5.0 (MIT), `QT_QPA_PLATFORM=offscreen` | `tests/ui/` | every commit |
| Exports (UT-EXP) | ezdxf 1.4.4 (MIT), pypdf 6.19.0 (BSD-3-Clause), stdlib xml and zipfile; all test-only | `tests/unit/io/exporters/` | every commit |
| Static and gates (MT, TR, LG, AX scripts) | ruff 0.16.10 (MIT), mypy 2.4.0 (MIT), import-linter 2.15 (BSD 2-Clause), own scripts | `tools/`, `tests/static/` | every commit |
| Independent (IT) | Agent 4's own scripts and expected values | `tests/independent/` | every commit after U-V1 |
| Performance (PF), packaging (PK) | `time.perf_counter`, build, PyInstaller 6.22.3 (stretch) | `tests/performance/`, `tests/packaging/` | release profile |

One command runs the gates locally and in CI: `python tools/ci.py --profile commit` (U-M1a). Profiles: `commit` (MT,
UT, GR, BV, PR-fast, UI, UT-EXP, LG, AX scripts, TR), `nightly` (adds PR-long), `release` (adds PF, PK).

## 3. Golden regression against Xcoil v3

Harness. `tools/golden/dump_xcoil.mjs` loads `/home/claude/serpentine/src/engine.js` read-only, evaluates each case and
writes `tests/golden/data/<area>/<case>.json` with `engine_sha256`, the Node version and non-finite values encoded as
`{"$f": "inf"}`. Geometry uses the board-dump format (REQ-F-40). Python comparators in `tests/golden/harness/` apply the
Phase 1 tolerance map: discrete outputs exact, scalar kernels 1e-12 rel., integrated results 1e-9 rel., paths by sampled
distance 1e-6 mm, DRC values 1e-6 mm abs., pass/fail agreement only outside Xcoil's slack band
[rule - 0.004 mm, rule) (D-006), near-threshold decisions with margin below 1e-9 rel. logged as indeterminate.
`tests/golden/expected_diffs/<area>.toml` (one file per owning unit) lists every intentional deviation with EQ-ID, reason and the Agent 2 and Agent 4
sign-off.

Function level compares one Xcoil function with its embodic counterpart on identical inputs. Layout level compares a
whole generated board and applies only to faithful ports (serpentine, wave). The spiral generator has no Xcoil
counterpart; it is checked against closed forms and the true-spiral reference (UT-GEO-07, OR-04).

| ID | Level | Xcoil source (engine.js) | embodic target | Cases | Criterion |
|---|---|---|---|---|---|
| GR-17 | function | `discretize`, `primLength` | `geometry.discretise`, `primitive_length_mm` | lines and arcs, sweeps of both signs, segment limits 0.1 to 2 mm | point lists exact in count, coordinates 1e-12 mm |
| GR-18 | function | `segSegDist` and the arc distance helpers used by `runDrc`/`drcObjects` | `drc.min_distance_*` | 1000 seeded pairs per kind incl. touching and crossing | 1e-12 mm abs. |
| GR-19 | format | Xcoil dumper output | `io.read_board_dump`, `io.write_board_dump` | one dump per topology | the reader parses both producers; write, read, write is byte-identical |
| GR-20 | layout | serpentine `buildCanonical`, `buildLayout` (l.163-753) | `generators.generate_serpentine` | Xcoil serpentine presets plus a seeded set over phases 1 to 3, layers per phase 1/2/4, series/parallel, grouped/interleaved, round/sharp, `{"interconnect": false}` and `true` | equal primitive, via and pad counts and roles; sampled path distance at most 1e-6 mm; DRC values 1e-6 mm abs. with the band rule |
| GR-21 | layout | `buildWave` (l.1639), `buildWaveOverlap` (l.2095) | `generators.generate_wave` | each style: involute, jog, chord, overlap; 2/4/6 layers; 1 to 3 phases | GR-20 criteria |
| GR-22 | result | serpentine `analyze` (l.880-1017), wave `analyzeElements` (l.1846) | `physics.analyse` on the ported Layout | the GR-20 and GR-21 case sets | Ke, R, eddy loss: 1e-9 rel. where both integrate the same elements; any other difference goes to `expected_diffs/<area>.toml` or is a defect (open question Q-2) |
| GR-23 | function | serpentine and wave helpers that the port reproduces line by line (corner, fillet, involute biarc, jog and chord construction) | the matching private helpers, tested through their module seam | 200 seeded inputs per helper | 1e-12 rel. |

Phase 1 GR-01 to GR-16 stay as written (equation-level cases for the spiral path's reused equations).

## 4. Closed-form, oracle and EC-05 tests

Phase 1 UT-PHY-01 to UT-PHY-21 and OR-01 to OR-12 stay. Two changes apply.

- Oracle tolerance add-on. OR-01 (O1, D08) and OR-07 (O2, D09) compare in the asymmetric band [-tol, +tol + e_edge],
  with e_edge taken from the computed `edge_leakage_fraction` of the oracle design, not from a constant (Phase 1 used
  4.2 % and 5.8 %; UT-PHY-21 pins those values within 0.1 pp).
- Independence (DEF-23 d). OR-07 and OR-08 use D09, the EC-05 calibration source, so they cannot validate EC-05. Their
  test docstrings and the oracle report say "not independent of EC-05". OR-01 is the only independent check of EC-05; its
  result depends on the D08 air-gap reading (gap G10).

## 5. New and amended tests

### 5.1 Unit tests

| ID | Check | Criterion |
|---|---|---|
| UT-GEN-01 | Generator contract for spiral, serpentine, wave and a stub | returns Layout or Unbuildable, never raises on fuzzed input; same design gives the same `layout_hash`; every circuit path and via ID exists; every winding path belongs to exactly one Member or to `interconnect_path_ids` |
| UT-GEN-02 | Dispatch | `build_layout` routes by `design.topology`; calling `generate_wave` with a spiral design raises TypeError |
| UT-GEN-03 | Serpentine validation | layers per phase 1 or even; copper count = phases x layers per phase, else INVALID with the pointer |
| UT-GEN-04 | Wave validation | copper count even and at least 2; each style builds for 1, 2 and 3 phases |
| UT-MOD-01 | Blank draft | `blank_draft(t)` has no required value and every optional field at its neutral value; `parse_draft` returns DraftIncomplete listing all required pointers in form order |
| UT-MOD-02 | Draft round trip | `parse_draft(draft_from_design(d)) == d` for every example |
| UT-MOD-03 | Field table completeness | every leaf of every DesignParameters variant has exactly one FieldSpec where it applies; `_mm` fields carry Unit.MM, `_rad` fields Unit.RAD; property fields are the closed list in ADR-0010 |
| UT-MOD-04 | Provenance derivation truth table | origin present or absent x value equal or not x measured or not; re-entering the current value changes nothing; setting a changed field back to the example value gives `example` |
| UT-MOD-05 | `mark_measured` refusals | empty source refused; design-kind field refused; a later value change drops the measurement |
| UT-RES-07 | EC-05 labelling (DEF-23) | `edge_leakage_fraction.status == assumption`; the EC-05 ValidityFlag has `metric_bound = lower_bound`, calibration `inferred`, transfer and threshold `assumption`; affected results list the transfer assumption in their tag |
| UT-IO-07 | Project file provenance and drafts | save and load keep origin example, per-field provenance and measurement sources; an incomplete draft loads as LoadedDraft with the same missing list; a stored `example` entry that disagrees with the packaged example is reported |
| UT-IO-08 | Examples | every packaged example loads, validates and computes with no ERROR issue; every title contains "Example" |
| UT-EXP-01 | SVG | parses with `xml.etree`; path, via and pad counts equal the Layout; `<metadata>` holds the REQ-T-07 fields; phases carry class and label in both render modes |
| UT-EXP-02 | DXF complete, outline, screws | ezdxf audit 0 errors; outline file holds only outline and bore entities with every end point shared by exactly two entities; screws file holds only circles, count = holes |
| UT-EXP-03 | PDF report | pypdf opens it; at least 1 page; text contains "Key results"; every reported value has a unit and a status word |
| UT-EXP-04 | README | names every exported file, units (mm), frame (y up, centred on the shaft axis) and the estimate caveat |
| UT-EXP-05 | Bundle and DRC refusal | ZIP holds the selected files plus README.txt; with DRC errors and no confirmation every writer returns ExportRefused |
| UT-SES-01 | Session state machine | empty to drafting to computed; an edit making the design incomplete returns to drafting and keeps the last outcome marked stale; re-entry is a no-op (no undo entry, no compute) |
| UT-SES-02 | Undo and redo | 50 steps restore the identical design hash and provenance map |
| UT-CLI-02 | Incomplete project in the CLI | `embodic-cli compute` on a draft exits 1 and prints the missing pointers |

### 5.2 Property tests

| ID | Property |
|---|---|
| PR-13 | DRC never under-reports, for every generator: whenever `drc.passed`, Agent 4's brute-force checker finds no non-exempt pair below rule - 1e-6 mm, and every pair it finds below that is reported (PR-01 extended to serpentine and wave) |
| PR-14 | Rotation symmetry for serpentine and wave: rotating the start angle by one electrical period shifts every phase phasor by the expected angle (1e-9 rad) and leaves abs(Ke), R and all DRC values unchanged (1e-9 rel., 1e-9 mm) |

### 5.3 UI tests (pytest-qt, offscreen)

| ID | Scenario | Criterion |
|---|---|---|
| UI-22 | Load an example | every field shows the "Example" chip; edit one field and its chip disappears; set it back and the chip returns; no badge changes |
| UI-23 | Start | the window opens in the empty session with New design and Examples; no compute runs |
| UI-24 | New design | choose a topology; the form is blank; Compute is disabled and shows the missing count; filling the last required field triggers exactly one compute |
| UI-25 | Toolstrip | every TOOLSTRIP action has an icon file, English label, tooltip and accessible name; its command resolves; arrow keys move within a tab; icons recolour after a theme switch |
| UI-26 | Themes | switch light, dark and system at runtime; every widget restyles; the choice persists after restart |
| UI-27 | Phase render mode | colour and greyscale-hatch toggle in the geometry view and charts; labels present in both; hatch stays inside coil eyes |
| UI-28 | Applicability matrix | for each topology and option combination the visible inputs equal `field_specs` filtered by applicability |
| UI-29 | Export confirmation | with an injected DRC error the confirmation lists the failures and has focus on Cancel |
| UI-30 | Chart audit | one unit per y axis, legend and direct labels, data-table alternative, status badge |
| UI-31 | Reduced animation | with the OS animation setting off no transition runs |
| UI-32 | Illustrative stamp | drawings not produced by the engine carry "Illustrative, not computed" |
| UI-33 | EC-05 disclosure | the disclosure of Ke shows e_edge, the words "at least" and "assumption", and the 10 % cap label |
| UI-34 | Number formatting in comparisons | counts as integers; deltas with sign and glyph, never colour alone |

Phase 1 UI-01 and UI-08 are withdrawn (replaced by UI-23 and UI-22). The remaining Phase 1 UI tests run on the
offscreen platform.

### 5.4 Static, language and accessibility gates

| ID | Gate |
|---|---|
| MT-01 | Amended: import-linter contracts C1 to C4 of `package_layout.md` §3 (core layers with generators above io, outcome, physics and drc; no Qt outside the Qt adapter modules; UI-internal layers; no KiCad or other GUI toolkits) |
| MT-07 | Scope guard for D-009: no `kipy` or `pcbnew` import, no `.kicad_pcb` writer, no KiCad option in CLI choices, and no "KiCad" in the string catalogue |
| LG-08 | No Thai characters in any shipped file (src, resources, examples, templates) |
| AX-08 | Phase colours at least 3:1 against the canvas in both themes; the palette validator passes for both themes; greyscale ladder steps distinguishable |
| AX-09 | Every toolstrip icon rendered in both themes reaches at least 3:1 against the toolstrip background |
| PF-05 | Baseline record for one serpentine and one wave example (no target; recorded for regression) |

## 6. Withdrawn tests

<!-- withdrawn-tests:start -->
KX-01, KX-02, KX-03, KX-04, KX-05, KX-06, KX-07, KX-08, KX-09, KX-10, KX-11, KS-01, KS-02, KS-03, KS-04, KS-05, KS-06,
KS-07, KS-08, PK-09, UT-UNI-02, PR-04, UI-01, UI-08, AX-07
<!-- withdrawn-tests:end -->

KX, KS, PK-09, UT-UNI-02 and PR-04 tested KiCad export, plugin and nm conversion (D-009). UI-01 and UI-08 tested the
default design at start (D-014). AX-07 tested the web option (D-010).

## 7. Exit criteria per milestone

| Milestone | Must pass |
|---|---|
| M1 | MT-01 to MT-03, MT-06, MT-07, UT-GEO-01, UT-DRC-01 to UT-DRC-08 on hand-built layouts, GR-17 to GR-19, PR-01 on random primitive sets, TR-02 |
| M2 | all UT-GEO, UT-WND, UT-PHY, UT-RES, UT-MOD, UT-IO, UT-GEN-01/02, GR-01 to GR-16, OR tests (pass or documented `xfail`), PR-01 to PR-12, BV, TR-01 to TR-04 |
| M3 | GR-20 to GR-23, UT-GEN-03/04, PR-13, PR-14, and every M2 gate still green |
| M4 | UI, AX, LG, UT-EXP, UT-SES tests; Agent 4 U-V4 independent export parsing |
| M5 | UT-CLI, PF (baseline recorded), PK-01 to PK-08, PK-06 walkthrough |

## 8. Requirements-to-tests matrix

Generated from `requirements.md` by `python3 docs/phase2/architecture/checks/check_contract.py --write`. Module names are
the owner packages of `interfaces.md`.

<!-- matrix:start (generated by checks/check_contract.py --write; do not edit by hand) -->

| REQ | Disp. | Prio | M | Owner module | Tests |
|---|---|---|---|---|---|
| REQ-F-01 | carried | must | M2 | embodic.generators.spiral | UT-GEO-01, UT-GEO-03, UT-GEO-04, UT-GEO-05, PR-03, PR-10 |
| REQ-F-02 | carried | must | M2 | embodic.winding | UT-WND-01, UT-WND-02, UT-WND-03, UT-WND-04, UT-WND-05, UT-WND-06 |
| REQ-F-03 | carried | must | M2 | embodic.generators.spiral | UT-GEO-10, UT-GEO-11, UT-GEO-19, UT-PHY-07 |
| REQ-F-04 | carried | must | M2 | embodic.model | UT-GEO-12, GR-07 |
| REQ-F-05 | amended | must | M2 | embodic.generators.spiral | UT-GEO-13, UT-PHY-11, PR-01 |
| REQ-F-06 | carried | must | M2 | embodic.generators.spiral | UT-GEO-07, UT-GEO-08, UT-GEO-09, UT-GEO-17, UT-GEO-18, OR-04 |
| REQ-F-07 | carried | must | M2 | embodic.physics | UT-PHY-01, UT-PHY-02, UT-PHY-04, UT-PHY-14 |
| REQ-F-08 | carried | must | M2 | embodic.generators.spiral | UT-PHY-09, UT-WND-07 |
| REQ-F-09 | carried | should | M2 | embodic.geometry | UT-GEO-14, UT-DRC-06, UT-EXP-02 |
| REQ-F-10 | carried | must | M1 | embodic.drc | UT-DRC-01, UT-DRC-02, UT-DRC-03, UT-DRC-04, UT-DRC-05, UT-DRC-08, PR-01, PR-02, PR-13, GR-18 |
| REQ-F-11 | carried | must | M2 | embodic.physics | UT-PHY-05, UT-PHY-06, UT-PHY-10, UT-PHY-12, UT-PHY-15, UT-PHY-16, UT-PHY-17, UT-PHY-18, UT-PHY-19, GR-02, GR-03, GR-04, GR-09, GR-11, GR-13, OR-01, OR-11, OR-12, UI-07 |
| REQ-F-12 | carried | must | M2 | embodic.physics | UT-PHY-08, UT-PHY-20, GR-05 |
| REQ-F-13 | carried | must | M4 | embodic.ui.views | UI-02, UI-03, UI-04, UI-06 |
| REQ-F-14 | amended | must | M2 | embodic.model | PR-05, BV-01, BV-02, BV-03, BV-05, BV-06, UI-14 |
| REQ-F-15 | amended | must | M2 | embodic.io | UT-IO-01, UT-IO-02, UT-IO-03, UT-IO-04, UT-IO-07, PR-08 |
| REQ-F-16 | amended | must | M4 | embodic.io | UT-EXP-01, UT-EXP-02, UT-EXP-03, UT-EXP-04, UT-IO-06 |
| REQ-F-17 | carried | could | M4 | embodic.ui.views | UI-10 |
| REQ-F-18 | amended | must | M5 | embodic.cli | UT-CLI-01, UT-CLI-02 |
| REQ-F-19 | amended | must | M2 | embodic.generators | UT-GEO-20, UT-GEN-01, UT-GEN-02, MT-01 |
| REQ-F-20 | carried | could | M2 | embodic.physics | UI-07, UT-RES-02 |
| REQ-F-21 | amended | must | M4 | embodic.ui.viewmodels | UI-22, UI-23, PR-12 |
| REQ-F-22 | amended | should | M4 | embodic.ui.viewmodels | UI-11, UT-SES-02 |
| REQ-F-23 | carried | must | M4 | embodic.ui.viewmodels | UI-15 |
| REQ-F-24 | carried | should | M2 | embodic.geometry | UT-GEO-21 |
| REQ-F-25 | amended | should | M4 | resources/examples | UI-16, UT-IO-08 |
| REQ-F-26 | carried | should | M4 | embodic.ui.views | UI-17 |
| REQ-F-27 | carried | should | M4 | embodic.ui.viewmodels | UI-18 |
| REQ-F-28 | carried | should | M4 | embodic.ui.views | UI-19 |
| REQ-F-29 | amended | should | M4 | embodic.io | UT-EXP-05 |
| REQ-F-30 | carried | could | M4 | embodic.ui.views | UI-20 |
| REQ-F-31 | carried | should | M4 | embodic.ui.app | UI-21 |
| REQ-F-32 | carried | must | M4 | embodic.ui.views | UI-28, UT-MOD-03 |
| REQ-F-33 | amended | must | M4 | embodic.ui.views | UI-29, UT-EXP-05, UT-CLI-01 |
| REQ-F-34 | new | must | M3 | embodic.generators.serpentine | GR-20, GR-23, UT-GEN-03, PR-13, PR-14 |
| REQ-F-35 | new | must | M3 | embodic.generators.wave | GR-21, GR-22, GR-23, UT-GEN-04, PR-13, PR-14 |
| REQ-F-36 | new | must | M4 | embodic.model | UT-MOD-01, UI-24, UT-SES-01 |
| REQ-F-37 | new | must | M2 | embodic.model | UT-MOD-01, UT-MOD-02, UT-MOD-03 |
| REQ-F-38 | new | must | M4 | embodic.ui.viewmodels | UI-22, UT-IO-08 |
| REQ-F-39 | new | must | M4 | embodic.ui.views | UI-25, AX-09 |
| REQ-F-40 | new | must | M1 | embodic.io | GR-19 |
| REQ-K-01 | withdrawn | - | - | - | MT-07 |
| REQ-K-02 | withdrawn | - | - | - | MT-07 |
| REQ-K-03 | withdrawn | - | - | - | MT-07 |
| REQ-K-04 | withdrawn | - | - | - | MT-07 |
| REQ-K-05 | withdrawn | - | - | - | MT-07 |
| REQ-K-06 | withdrawn | - | - | - | MT-07 |
| REQ-K-07 | withdrawn | - | - | - | MT-07 |
| REQ-K-08 | withdrawn | - | - | - | MT-07 |
| REQ-K-09 | withdrawn | - | - | - | MT-07 |
| REQ-K-10 | withdrawn | - | - | - | MT-07 |
| REQ-K-11 | withdrawn | - | - | - | MT-07 |
| REQ-K-12 | withdrawn | - | - | - | MT-07 |
| REQ-K-13 | withdrawn | - | - | - | MT-07 |
| REQ-K-14 | withdrawn | - | - | - | MT-07 |
| REQ-K-15 | withdrawn | - | - | - | MT-07 |
| REQ-K-16 | withdrawn | - | - | - | MT-07 |
| REQ-L-01 | carried | must | M4 | embodic.ui.strings | LG-01, LG-08 |
| REQ-L-02 | amended | should | M4 | embodic.ui.strings | LG-02 |
| REQ-L-03 | carried | must | M4 | embodic.ui.strings | LG-05 |
| REQ-L-04 | amended | must | M4 | resources/themes | AX-01, AX-05, AX-08 |
| REQ-L-05 | carried | must | M4 | resources/icons | LG-06 |
| REQ-L-06 | carried | should | M4 | embodic.ui.strings | LG-07 |
| REQ-L-07 | carried | must | M2 | embodic.results | UT-UNI-03 |
| REQ-L-08 | carried | must | M4 | embodic.ui.views | UI-34 |
| REQ-L-09 | amended | should | M4 | embodic.ui.strings | LG-07 |
| REQ-N-01 | carried | must | M5 | embodic.api | PF-01, PF-04 |
| REQ-N-02 | carried | must | M4 | embodic.ui.workers | UI-05, UI-02 |
| REQ-N-03 | carried | should | M5 | embodic.api | PF-02 |
| REQ-N-04 | carried | must | M2 | embodic.physics | PR-09, PK-04, MT-06 |
| REQ-N-05 | carried | must | M5 | pyproject.toml | PK-01, PK-02 |
| REQ-N-06 | amended | must | M5 | pyproject.toml | PK-03, PK-05 |
| REQ-N-07 | amended | must | M5 | docs | PK-06 |
| REQ-N-08 | amended | must | M1 | pyproject.toml | MT-01, MT-02, MT-03 |
| REQ-N-09 | carried | must | M2 | embodic.physics | MT-04 |
| REQ-N-10 | carried | must | M2 | tools/trace_matrix.py | TR-01 |
| REQ-N-11 | carried | must | M4 | resources/themes | AX-01 |
| REQ-N-12 | carried | must | M4 | embodic.ui.views | AX-02, AX-03 |
| REQ-N-13 | carried | must | M4 | embodic.ui.views | AX-04 |
| REQ-N-14 | carried | must | M4 | embodic.ui.views | AX-05 |
| REQ-N-15 | carried | must | M4 | embodic.ui.views | UI-09 |
| REQ-N-16 | carried | must | M4 | embodic.ui.views | AX-06 |
| REQ-N-17 | amended | must | M5 | embodic | PK-07 |
| REQ-N-18 | carried | must | M4 | embodic.ui.app | UI-12 |
| REQ-N-19 | carried | must | M5 | pyproject.toml | PK-08 |
| REQ-N-20 | carried | should | M4 | embodic.ui.app | UT-LOG-01 |
| REQ-N-21 | amended | must | M1 | embodic.geometry | UT-GEO-01, UT-UNI-01, UT-EXP-02 |
| REQ-N-22 | carried | could | M5 | embodic.ui.app | PF-03 |
| REQ-N-23 | carried | must | M4 | embodic.ui.views | UI-27, AX-05 |
| REQ-N-24 | carried | must | M4 | embodic.ui.views | AX-06, UT-MOD-03 |
| REQ-N-25 | carried | must | M4 | embodic.ui.views | UI-30 |
| REQ-N-26 | carried | should | M4 | embodic.ui.views | UI-31 |
| REQ-N-27 | new | must | M4 | embodic.ui.theme | UI-26, AX-01 |
| REQ-N-28 | new | must | M4 | embodic.ui.theme | AX-08, UI-27 |
| REQ-T-01 | carried | must | M4 | embodic.ui.views | UI-06, AX-02 |
| REQ-T-02 | carried | must | M2 | embodic.results | UT-RES-01 |
| REQ-T-03 | carried | must | M2 | embodic.results | UT-RES-02, UT-RES-05 |
| REQ-T-04 | carried | must | M2 | embodic.results | UT-RES-03, TR-04 |
| REQ-T-05 | carried | must | M2 | embodic.results | TR-03, UT-RES-02 |
| REQ-T-06 | amended | must | M2 | embodic.model | UT-RES-06, UT-MOD-05 |
| REQ-T-07 | amended | must | M4 | embodic.io | UT-IO-06 |
| REQ-T-08 | amended | must | M2 | embodic.physics | UT-PHY-13, UT-PHY-21 |
| REQ-T-09 | carried | must | M1 | tools/trace_matrix.py | TR-01, TR-02 |
| REQ-T-10 | carried | must | M4 | embodic.ui.strings | LG-03 |
| REQ-T-11 | carried | must | M4 | embodic.ui.strings | LG-04 |
| REQ-T-12 | carried | should | M4 | embodic.ui.views | UI-13 |
| REQ-T-13 | carried | must | M4 | embodic.ui.views | UI-06 |
| REQ-T-14 | carried | must | M4 | embodic.io | UT-IO-06, UI-32 |
| REQ-T-15 | new | must | M2 | embodic.model | UT-MOD-04, UT-IO-07, PR-12 |
| REQ-T-16 | new | must | M2 | embodic.results | UT-RES-07, UI-33 |

<!-- matrix:end -->
