Prepared by: Agent 6 - Software Architecture Specialist - model: claude-opus-5-5

# embodic Phase 2 test plan (build contract v1, 2026-10-04)

This plan updates `docs/phase1/architecture/test_plan_draft.md`. Every Phase 1 test not listed under "Withdrawn tests"
stays in force with its Phase 1 ID, check and criterion. This file adds the Phase 2 tests, amends the ones whose subject
changed, and holds the generated requirements-to-tests matrix. It records no results, except the oracle results of
§5.6 (D-045g) and the readings that revision notes quote: unit reports and Fable's ledger hold the others.

This file and the Phase 1 plan it extends are the only sources of test IDs and their meanings. A brief, docstring or
report that gives an ID another meaning is wrong, and this plan wins. A unit that needs a new test asks for a new ID
here instead of reusing one.

Revision 2026-10-04 (U-D1, corrections from the W0 pilot): §3 states the D-006 band rule once, half-open
(DEF-M1d-02), names the "kernel" class for golden functions without EQ-IDs, ratifies the U-M1d encoding and `--out`
flag, and specifies layout dumps for GR-19 with U-M1b as owner. §5.1 amends UT-UNI-01 (2 ulp round trips, JS rounding).
§5.4 amends LG-01 (character check from M1, word check at M4). No ID changed.

Revision 2026-10-05 (U-D2, corrections from the W1 and W2 reports): the paragraph above makes this plan the single
source of test IDs (DEF-M1b-01). The U-M1b brief used UT-GEO-12 for transform exactness and UT-GEO-15 for discretise
bounds; Phase 1 gives them stack-up z and determinism, and those meanings stay. §5.1 adds UT-GEO-22 and UT-GEO-23 for
the two tests the brief meant. §5.2 restates PR-01 and PR-02 here, so M1's DRC properties no longer point at the
Phase 1 file only (DEF-V1-01). §5.4 adds MT-08. §2 renames the export test folder to `tests/unit/embodic_io/`
(U-M1y). §3 ratifies the GR-19 label for Xcoil's sector topology. §7 adds the new IDs to the M1 exit.

Revision 2026-10-05 (U-D3, D-016 and D-022): §5.1 amends UT-DRC-04 with one exempt case and one near miss per
connectivity rule of interfaces.md §7 (D-022). §5.1 amends UT-GEN-01 and UT-GEN-03 and adds UT-GEN-05 for the
one-board-per-phase serpentine stack (D-016). §3 adds stack-mode cases to GR-20. §7 adds UT-GEN-05 to the M3 exit.

Revision 2026-10-08 (U-D4, D-022c and D-031): §5.1 amends UT-DRC-04 cases 2c, 2d and 3c for the tap exemption
(D-022c), UT-GEN-01 for `interconnect_roles`, `detail` and `derived`, UT-GEN-03 for the single-mode copper count
(D-031e), UT-GEO-21 for the entered hole diameter (D-031a), and UT-WND-07 and UT-WND-09 for `plan_issues` (D-031d).
It adds UT-GEO-24 (first coil angle, D-031c), UT-GEO-25 (`TurnLimit.closing`, D-031b), UT-PHY-22 (loss sum and
interconnect copper) and UT-PHY-23 (EQ-20 for any phase count, D-031f). §5.5 adds the rule for timing tests that
Agent 4 applies in U-V2. The M2 exit of §7 already covers the new IDs (all UT-GEO, UT-WND and UT-PHY).

Revision 2026-10-08 (U-D5, D-033b, D-033c and D-033g): §3 names the first M1 allow-list entry, XD-M1-002. §5.1 amends
UT-GEO-13 for the 2k + 1 via plan (U-E6) and UT-GEO-11 for the state of pair rotation on main e1536b8. It adds
UT-GEO-26 for series layer pairs. UT-GEO-19 keeps its Phase 1 meaning, phase per pair (M4). The series-pair tests in
`tests/unit/generators/test_spiral_pairs.py` that carry the label UT-GEO-19 on main are UT-GEO-26. The M2 exit of §7
covers UT-GEO-26.

Revision 2026-10-08 (U-D7, D-035): §3 corrects the XD-M1-002 range (D-035g) and states the GR-21 criterion (D-035f).
§5.1 amends UT-DRC-04 with the rule 5 cases (D-035b) and states UT-GEN-03 and UT-GEN-04 as implemented. §5.2 gives
PR-14 its two tolerance outcomes (D-035d). §5.5 records the gate wall time (D-035h).

Revision 2026-10-09 (U-D8, D-036 and D-037; main 8a297a0 read for every item): §3 adds XD-WAVE-001 with its status and
the overlap delta case it leaves out. §5 names the one open defect that keeps a strict xfail. §5.1 amends UT-DRC-04
with the rule 2b tests (D-036a, D-037a). §5.2 sets PR-14's serpentine Ke tolerance to 1e-8 rel. with the chord-count
reason (D-036c). No ID changed.

Revision 2026-10-09 (U-D9, D-038; `tests/golden/expected_diffs/wave.toml` and `tests/golden/m3_wave/test_gr22_results.py`
on main 3acb044 read for every item): §3 gives XD-WAVE-001 the status `verified`, adds XD-WAVE-002 for the overlap wave
with a delta connection (`inferred`, true value `unresolved`) and records that the via barrel length has no entry
(D-038b). No ID changed.

Revision 2026-10-09 (U-D10, claude-sonnet-5-5, D-039, D-040; main fd190c1 read for every item, and the five strict
xfails below run): §5 records the closed defect DEF-M3b-03. §5.1 amends UT-GEN-01 (the wave and serpentine fuzz tests
and the D-030 guard tests), UT-EXP-01 and UT-EXP-03 (labels, clipped eye fills, legend and embedded fonts) and UT-IO-08
(the display note). §5.3 amends UI-27 and adds UI-04 as U-M4c-3 rewrote them (UX-AC-27). §5.6 lists the strict xfails.
No ID is new.

Revision 2026-10-09 (U-D11, claude-sonnet-5-5, D-040 and D-041a; main 9776555 read for every item, after U-M4c-4 and
U-M4e-1 merged; the test modules named below run, see the report of U-D11): §5.1 amends UT-RES-03 (the registry count
test derives from its sources, D-040 b), UT-IO-08 (example titles are free English text, D-041a), UT-EXP-01 and UT-EXP-03
(static Inter faces, the colophon line, U+00A0 between a number and its unit). §5.3 amends UI-25 (Open is enabled, F21),
UI-04 and UI-27 (forced labels per phase and sign, line numbers after U-M4e-1). §5.4 amends LG-01 (the per-module
allowance of D-040 a and c). §5.6 lists four strict xfails, not five, and two of them go when U-M4e-1b merges. No ID is new.

Revision 2026-10-11 (U-D12, claude-sonnet-5-5, D-041a and D-041b; main 4fda98d read for every item, after U-M4e-1b and
U-M4e-2 merged). §5.1 amends UT-IO-08 (the five display titles, the design name that equals the title, the pinned design
hashes). §5.3.1 is new and says which tests under `tests/ui/qt_e2e/` cover AX-02, AX-04, UI-09 and the three walkthroughs,
that UI-20 has no test, and that `.claude/skills/verify/verify.py --acceptance` is the UI verification entry point. §5.6
now lists six strict xfails: the four of AX-04 and the two of DEF-M1V-03. The two UX-AC-03 marks are gone. No ID is new.

Revision 2026-10-12 (U-D13, claude-opus-5-5, D-034, D-042a; main 7b9b4c9 read for every item, and
`checks/selftest_probe.py` run). §5.7 is new: UT-RES-08, UT-RES-09, TR-05 and PK-10 for the evidence of passing tests,
UT-SLF-01 to UT-SLF-03, UT-CLI-03, UI-35 and PK-11 for the self-tests and the Tests dialog, and the split of the PK tests
between this container and the Windows CI matrix. §7 names the new IDs in the M5 exit. PK-09 stays withdrawn, so the new
packaging IDs start at PK-10.

Revision 2026-10-13 (U-D14, claude-sonnet-5-5, D-045, D-037a, D-038d; main 6243163 read for every item, and the test
modules named below run). §5 closes DEF-M1V-03 and names F-OR07 as the one open finding that keeps a strict xfail. §5.6
is rewritten for main 6243163: one `xfail(strict=True)` mark (OR-07, two cases), the oracle results of D-045g, and the
AX-04 and DEF-M1V-03 marks that are gone. §5.3.1 amends the AX-04 row for the same reason. No ID is new.

Continuation of the same revision (U-D14, claude-sonnet-5-5, D-046; main 76f054b). §2 names the two real oracle files
(`test_oracles.py`, `test_oracles_m5.py`) instead of a folder that does not exist. §5 states D-046f: the product mapper
`layout_from_xcoil` keeps one path per Xcoil object and `split_ic_chains` is the GR-19 DRC reading. §5.1 names UT-DRC-04
cases 5e and 5f as added by U-M5f. §5.6 is re-run on main 76f054b with the same results. §5.7 names the two tests of
D-045f and D-046e and gives them no ID. §7 states the M2 exit as D-045b words it.

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
| Oracle (OR) | pytest; one strict `xfail` (OR-07, F-OR07) and two skips (OR-03, OR-10), §5.6 | `tests/unit/physics/test_oracles.py` (OR-01) and `tests/unit/physics/test_oracles_m5.py` (OR-02, OR-03, OR-05 to OR-10) | every commit |
| Property (PR), boundary (BV) | hypothesis 6.168.3 (MPL-2.0, dev only), pytest | `tests/unit/property/`, `tests/unit/boundary/` | fast profile per commit, long profile nightly |
| UI | pytest-qt 4.5.0 (MIT), `QT_QPA_PLATFORM=offscreen` | `tests/ui/` | every commit |
| Exports (UT-EXP) | ezdxf 1.4.4 (MIT), pypdf 6.19.0 (BSD-3-Clause), stdlib xml and zipfile; all test-only | `tests/unit/embodic_io/exporters/` | every commit |
| Static and gates (MT, TR, LG, AX scripts) | ruff 0.16.10 (MIT), mypy 2.4.0 (MIT), import-linter 2.15 (BSD 2-Clause), own scripts | `tools/`, `tests/static/` | every commit |
| Independent (IT) | Agent 4's own scripts and expected values | `tests/independent/` | every commit after U-V1 |
| Performance (PF), packaging (PK) | `time.perf_counter`, build, PyInstaller 6.22.3 (stretch) | `tests/performance/`, `tests/packaging/` | release profile |

One command runs the gates locally and in CI: `python tools/ci.py --profile commit` (U-M1a). Profiles: `commit` (MT,
UT, GR, BV, PR-fast, UI, UT-EXP, LG, AX scripts, TR), `nightly` (adds PR-long), `release` (adds PF, PK).

## 3. Golden regression against Xcoil v3

Harness. `tools/golden/dump_xcoil.mjs` loads `/home/claude/serpentine/src/engine.js` read-only, evaluates each case and
writes `tests/golden/data/<area>/<case>.json` with `engine_sha256` and the Node version. `--out <dir>` writes the same
fixtures to a scratch folder instead, so a unit can compare a fresh dump with the committed one without overwriting it.
Numbers follow the encoding in interfaces.md §9.2: `{"$f": "inf"}`, `{"$f": "-inf"}` and `{"$f": "nan"}` for
non-finite values, `-0.0` for negative zero. Primitives use the board-dump record (REQ-F-40). Python comparators in
`tests/golden/harness/` apply the Phase 1 tolerance map: discrete outputs exact, scalar kernels 1e-12 rel., integrated
results 1e-9 rel., paths by sampled distance 1e-6 mm, DRC values 1e-6 mm abs., near-threshold decisions with margin
below 1e-9 rel. logged as indeterminate. `tests/golden/expected_diffs/<area>.toml` (one file per owning unit) lists
every intentional deviation with EQ-ID, reason and the Agent 2 and Agent 4 sign-off.

Revision 2026-10-08 (U-D5, D-033c; `tests/golden/expected_diffs/m1.toml` on main e1536b8, `verified` by reading). The
first M1 entry is XD-M1-002, case `segsegdist-seeded-collinear`, EQ-30. Xcoil's `segSegDist` skips its crossing test
only when |d1 x d2| <= 1e-15 mm² (`engine.js` l.565). In 19 of the 1000 fixture calls it returns a false crossing (0)
where embodic and a dense sample give 0.5288 to 13.0848 mm (corrected 2026-10-08, U-D7, D-035g: D-033c and D-034
stated 4.0001 mm as the low end; Agent 4 measured 0.5288 mm, DEF-UV2-01). The entry admits numeric diffs up to 13.1 mm abs. for
that case only. Fable signed off on behalf of Agents 2 and 4 (D-033c), and Agent 4 re-checks the entry in U-V2.

Revision 2026-10-09 (U-D8, D-036e, D-037d; corrected by U-D9 with D-038b; `tests/golden/expected_diffs/wave.toml` on
main 3acb044, `verified` by reading). Wave entries:

| ID | Case | EQ-ID | Status | Difference | Not covered |
|---|---|---|---|---|---|
| XD-WAVE-001 | `wave-analysis-overlap-l2-m3-p16-t2` | EQ-23 | `verified` (U-E8, `open_positions_m3.md` §1a); Agent 2 confirmed, Agent 4 sign-off pending | overlap wave, star connection: the three tap stubs are the only copper between each minus terminal and the star ring, so each carries I_line. embodic counts them as phase link copper, and Xcoil sets its link sum to zero (`engine.js` l.2172), an omission. Interconnect loss 0.007422 W against 0.005007 W (+48.2 %, the entry's own measurement) | the overlap wave with a delta connection (XD-WAVE-002) and the via barrel length, which has no entry (D-038b) |
| XD-WAVE-002 | `wave-analysis-overlap-l2-m3-p16-t2-delta` | EQ-23 | `inferred` (U-E8, `open_positions_m3.md` §1b); the true value is `unresolved` until the spec names the external closure point; Agent 4 sign-off pending | overlap wave, delta connection: embodic counts the three line leads at I_line^2 x R, 1.962909e-03 W, an upper bound (6.543030e-04 W if the leads carry I_ph). Xcoil reports 0 W because its overlap path leaves `icR` null (`engine.js` l.2154) | the true loss, which depends on where the external delta closure lands |

The serpentine entries that U-M3-fix2 removed from `expected_diffs/serpentine.toml` (seeded-04, -13 and -19 are now
DRC-clean) were never listed in this section, so no row changes.

D-006 band rule (the only statement of it; every other document refers here). Xcoil passes a clearance when it is at
least rule - 0.004 mm (`engine.js` `runDrc` l.757 sets `tol = 0.004`; l.773 and l.774 report an error when the value is
below `clearance - tol`; `verified` by reading, 2026-10-04). embodic passes it when it is at least rule - 1e-6 mm. The two verdicts can differ only for a
measured clearance v with rule - 0.004 mm <= v < rule, the half-open band [rule - 0.004 mm, rule). Inside the band the
golden comparison records the verdict as indeterminate. Outside it, Xcoil and embodic must agree. A symmetric band,
|v - rule| <= 0.004 mm, is wrong: it would excuse disagreements above the rule, where both tools must pass
(`tools/golden/README.md`, test `test_drc_band_rule_requires_agreement_above_the_rule`). DRC values themselves always
compare within 1e-6 mm.

Kernel class. Geometry kernels that the registry gives no EQ-ID (`tfPrim`, `tfPoint`, `reversePrims`, `primStart`,
`primEnd`; `equation_registry.json` `golden_functions`, read by U-M1d on 2026-10-04) are golden "kernel" class. Their
fixtures carry `"eq_ids": []`, they use the 1e-12 tolerance classes, and an allow-list entry for them names the
geometry module instead of an EQ-ID. They pass no equation gate, because they compute no physics.

Layout dumps (GR-19, and later GR-20 and GR-21). The dumper keeps the M1 kernel functions in `dump_xcoil.mjs` and loads
any other area's functions from `tools/golden/functions/<area>.mjs`, one file per owning unit, so no two units edit the
dumper. A layout function takes Xcoil's `compute()` input object, runs Xcoil's own path to the builder (serpentine:
`normalizeParams`, `derive`, `buildLayout`; wave and sector: the builders that `computeWave` and `computeSector` call)
and emits the raw result: every copper layer with its identifying fields and its primitives as board-dump primitive
records, the via list and the pad list, all with Xcoil's own keys and names. It maps nothing to embodic names. The
Python test maps the raw layout to `embodic.board-dump` v1 and feeds it to `io.read_board_dump`.

The GR-19 mapper (`tests/golden/m1_layout/xcoil_map.py`) labels Xcoil's `sector` layouts `TopologyKind.SPIRAL`
(ratified 2026-10-05, U-D2). A `Layout` needs a topology, both are concentrated-coil boards, and GR-19 tests the
format only. The label claims no geometric equivalence: the spiral generator is not a port of `sector`. A board dump
has no topology key, so the label never reaches a fixture. No other code may use the mapping.

Function level compares one Xcoil function with its embodic counterpart on identical inputs. Layout level compares a
whole generated board and applies only to faithful ports (serpentine, wave). The spiral generator has no Xcoil
counterpart; it is checked against closed forms and the true-spiral reference (UT-GEO-07, OR-04).

| ID | Level | Xcoil source (engine.js) | embodic target | Cases | Criterion |
|---|---|---|---|---|---|
| GR-17 | function | `discretize`, `primLength` | `geometry.discretise`, `primitive_length_mm` | lines and arcs, sweeps of both signs, segment limits 0.1 to 2 mm | point lists exact in count, coordinates 1e-12 mm |
| GR-18 | function | `segSegDist` and the arc distance helpers used by `runDrc`/`drcObjects` | `drc.min_distance_*` | 1000 seeded pairs per kind incl. touching and crossing | 1e-12 mm abs. |
| GR-19 | format | raw layouts from `tools/golden/functions/m1_layout.mjs` (serpentine `buildLayout`, wave, sector), mapped to board dumps in Python | `io.read_board_dump`, `io.write_board_dump` | one layout per Xcoil topology, from Xcoil's default parameters; owner U-M1b (amended 2026-10-04) | the reader parses both producers; write, read, write is byte-identical; primitive, via and pad counts per layer equal the raw layout's |
| GR-20 | layout | serpentine `buildCanonical`, `buildLayout` (l.163-753) | `generators.generate_serpentine` | Xcoil serpentine presets plus a seeded set over phases 1 to 3, layers per phase 1/2/4, series/parallel, grouped/interleaved, round/sharp, `{"interconnect": false}` and `true`, `stackMode` `single` and `perPhase` with `boardGap` 0.1 and 0.5 mm (Xcoil tests.js l.32, l.354; added 2026-10-05, U-D3); a `perPhase` case is compared board by board | equal primitive, via and pad counts and roles; sampled path distance at most 1e-6 mm; DRC values 1e-6 mm abs. with the band rule |
| GR-21 | layout | `buildWave` (l.1639), `buildWaveOverlap` (l.2095) | `generators.generate_wave` | each style: involute, jog, chord, overlap; 2/4/6 layers; 1 to 3 phases | GR-20 criteria, with paths at 1e-9 mm and arc splines compared as curves, not by centre and radius (revision 2026-10-08, U-D7, D-035f; `tests/golden/m3_wave/test_gr21_layouts.py` l.23-26). V8 and glibc differ by 1 ulp in some trig calls, which moves arc centres by about 1e-11 mm. The one chord-count flip this causes (case overlap l6 m1) is an expected diff with that reason, not an indeterminate result. No fdlibm port in Phase 2 |
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

Closed defect DEF-M1V-03 (revision 2026-10-13, U-D14; U-V1c and U-M5o reports, D-045g, D-046f; main 6243163 and 76f054b). Revision
2026-10-09 (U-D8) named it as the only open defect with a strict xfail: the GR-19 mapper put an Xcoil `ic` object into one
`CopperPath` with gaps (11.28 mm on serpentine path 15, 22.11 mm on wave path 192). Two units closed it.

- U-V1c split the `ic` objects in Agent 4's harness (`split_interconnect_chains`, `tests/independent/m1/gr19.py` l.68)
  and removed the strict xfail from `tests/independent/m1/test_gr19_drc.py`.
- The product tests read the same cut through `split_ic_chains` (`tests/golden/m1_layout/xcoil_map.py` l.75), and
  `layout_from_xcoil(split_ic_chains(raw))` is the GR-19 DRC reading. `test_gr19_every_path_is_one_continuous_chain`
  (`tests/golden/m1_layout/test_gr19_layouts.py` l.66) asserts that every path of that reading is one chain.
- `layout_from_xcoil` itself does not split (D-046f). It keeps one path per Xcoil object, Xcoil's circuit member, which the
  physics goldens and Agent 4's DEF-M2e3-01 test pin. `test_gr19_physics_mapping_keeps_one_path_per_xcoil_object`
  (l.55) asserts it. The first version of the cut sat inside `layout_from_xcoil` (U-M5o) and broke the physics goldens in
  Fable's gate on 3e765f2 (D-046, sources).

`grep -rn "xfail" tests --include=*.py` finds no mark in either file (`verified` by running it on main 76f054b). The
continuity tests pass: `10 passed, 45 deselected` from `pytest tests/golden/m1_layout/test_gr19_layouts.py
tests/independent/m1/test_gr19_drc.py -k "continuous or cut_only or one_path_per"`. `run_drc` on the three GR-19 layouts
of the DRC reading reports sector 0, serpentine 0 and wave 186 violations (6 `trace_trace` and 180 `trace_via`),
`verified` by running `PYTHONPATH=src python3 tests/golden/m1_drc/time_gr19_layouts.py --runs 1` on main 76f054b. The
counts are the D-045g counts and D-046f did not change them. Before the split the counts were 0, 3 and 190 (U-M5o report,
not rerun). The 186 wave violations are the D-006 pairs of D-034 (`tests/independent/README.md`, U-V1c section). After the
split no GR-19 pair depends on the end-point clause of rule 5 (interfaces.md §7), and U-M5f adds UT-DRC-04 cases 5e and 5f
for that clause (§5.1).

The one finding that keeps a strict xfail is F-OR07, the OR-07 band miss of D-045a (§5.6).

Closed defect DEF-M3b-03 (revision 2026-10-09, U-D10; U-M3-fix3 report, main fd190c1). The wave fuzz test failed with
`ZeroDivisionError` in `biarc` for a denormal trace width on the merged gate of main 3d70170. U-M3-fix3 reproduced it
with an explicit `@example` (`tests/unit/generators/wave/test_wave_generate.py` l.306), kept that example, added the
D-030 guards of interfaces.md §6, and the gate passed 6 of 6 on its branch. The wave fuzz test had passed on main with
an empty `.hypothesis` database, so the example, not the random draw, is what keeps the case from returning.

### 5.1 Unit tests

| ID | Check | Criterion |
|---|---|---|
| UT-GEO-22 | New 2026-10-05: transform exactness | rotating (2, 0) by 60 degrees gives (1, sqrt 3) within 1e-12 mm; a mirror about 45 degrees swaps x and y and negates an arc's sweep; `transform` mirrors before it rotates; rotating forward and back, and `reverse_path`, return or swap every end point within 1e-9 mm (`tests/unit/geometry/test_transforms.py`, labelled UT-GEO-12 there until relabelled) |
| UT-GEO-23 | New 2026-10-05: discretise bounds | every chord of `discretise_path` respects `max_segment_mm`, `max_angle_rad` and `max_sagitta_mm`; piece lengths sum to the path length and `s_mm` increases; a 90 degree arc of r = 10 mm with a 5 degree step gives 18 chords; K chords give K + 1 points from start to end (`tests/unit/geometry/test_discretise.py`, labelled UT-GEO-15 there until relabelled) |
| UT-GEO-21 | Amended 2026-10-08 (U-D4, D-031a): fastener holes | holes at the specified pitch radius, count and angle offset with `Hole.diameter_mm` equal to the pattern's `hole_diameter_mm` for every `size` and `fit`; a pattern without `hole_diameter_mm` does not parse; edge, pitch and copper keep-out violations reported (REQ-F-24) |
| UT-GEO-11 | Amended revision 2026-10-08 (U-D5): pair rotation pi/Q | Phase 1 criterion (group-2 centre vias in the group-1 inter-coil gaps, pi/Q ± 1e-9 rad) is not met on main e1536b8. One rotation shared by every pair (option M3) builds the board of first coil angle θ₀ + pi/Q (`test_spiral_pairs.py`). Pairs at two rotations: main returns Unbuildable `UNBUILDABLE_SPIRAL_OPTION_NOT_IMPLEMENTED` at `/winding/layers/pairs`; spec G6 (U-E6, `inferred`) forbids the combination with `UNBUILDABLE_PAIRS_ROTATED_APART`, which U-M2d-5 adds. Whether the Phase 1 build criterion for two rotations is withdrawn is open for Fable |
| UT-GEO-13 | Amended revision 2026-10-08 (U-D5, spec G6 via plan, U-E6): via plan count and spans | per coil k centre, k - 1 transfer and 2 terminal vias, 2k + 1 in all; N_via = Q·v·(2k + 1), all through vias (D-015). The default totals stay: 36 for M1 (Q = 12, k = 1) and 60 for M2 (k = 2) (`verified` by arithmetic). `checks/series_fan_check.py` counts 5 per coil for k = 2 and 7 for k = 3 |
| UT-GEO-26 | New revision 2026-10-08 (U-D5, D-020, D-033b, D-033g): series layer pairs (G5 k centre vias, G6 via fan) | CF-11 with k = 3 series groups keeps 10 turns and centre-via radii 30.7, 29.9 and 29.1 mm; group g's X joins ring via g to its centre via and its Y joins that centre via to ring via g + 1. `generate_spiral` never returns a series board with a DRC violation: it returns the board with 0 violations or Unbuildable `UNBUILDABLE_SERIES_VIA_FAN_DRC` at `/winding/layers/series_groups`. On main e1536b8 CF-11 is refused (DEF-M2d4-02). From U-M2d-5, CF-11 and D08 with k = 2 and k = 3 build with 0 violations and a smallest clearance of 0.2 mm (CF-11) and 0.8 mm (D08), the values of `series_fan_check.py` |
| UT-GEO-24 | New 2026-10-08 (U-D4, D-031c): first coil angle any finite | a spiral design with `first_coil_angle_rad` = 1.0, 1.0 + 2 pi, and 1.0 - 2 pi builds in every case, and coil 0's axis and every primitive end point agree within 1e-9 rad and 1e-9 mm; the model accepts the value as typed and the project file stores it unchanged |
| UT-GEO-25 | New 2026-10-08 (U-D4, D-031b): closing of the last turn | `SpiralDetail.turn_limit.closing` equals the closing the generator built: `half` for the D08 example (3 turns, D-030) and `full` for a design whose G5 eye fits; the value is not a `FIELDS` pointer and is absent from the project file |
| UT-UNI-01 | Amended 2026-10-04: unit conversions and rounding | deg and rad, mm and m, rpm and rad/s, mil² and mm² round trips within 2 ulp of the input (`math.ulp`), not exact (requirements.md revision note); `js_round` gives 3, -2, 1, 0, -1, 0 for 2.5, -2.5, 0.5, -0.5, -1.5, 0.49999999999999994 (JS `Math.round`); `quantise(-0.000025, 1e5) == -0.00002`; neither returns -0.0 |
| UT-DRC-04 | Amended 2026-10-05 (U-D3, D-022), 2026-10-08 (U-D4, D-022c) and 2026-10-08 (U-D7, D-035b, cases 5a to 5d): connectivity exemptions, one exempt case and one near miss per rule of interfaces.md §7, each below the rule so only the exemption decides | 1a adjacent main primitives exempt; 1b same-net main primitives two indices apart reported; 1c a corner fillet or taper exempt from both mains it belongs to and from the other fillets and tapers of those mains; 1d the DEF-M1V-01 hairpin: a fillet against the main two steps back reported; 2a a path end group exempt from the via or pad its end lies on; 2b a via the path does not end on reported; 2c an interconnect path (net `U`) ending on a `PHASE_A` via of any role (terminal, centre, transfer), and on a pad of another net, exempt; 2d vias of any net and role tapping an interconnect ring (net `N`) mid-path and at its ends, each centre within `pad_mm / 2` of the centreline, exempt from every primitive of the ring, and the same ring with a phase net (not an interconnect) reported against the same vias; 3a same-net end groups meeting at one via, one pad or within `COINCIDENCE_MM` exempt; 3b different-net end groups at a coincident point with no via or pad reported; 3c an interconnect end group and a phase path end group on one via of any role, or on one pad, exempt; 4a a same-net via inside a pad exempt; 4b an other-net via inside a pad reported; 5a a path end point on the middle of a same-net line exempt from every primitive of that path; 5b the same on the middle of a same-net arc; 5c the 5a T with the two paths on different nets reported; 5d the 5a T with the end point 0.01 mm short of the centreline reported. Revision 2026-10-13 (U-D14, Fable's ruling): U-M5f adds 5e (a same-net path's end point on the other path's end point region, exempt: the end-point reading of rule 5) and 5f (the same geometry on different nets, reported). Neither is on main 76f054b, and this plan does not claim that they pass. Rule 2b (amended 2026-10-09, U-D8, D-036a, D-037a; D-036a's "rule 2b" is not case 2b above), in `tests/unit/drc/test_run_drc.py`: `test_ut_drc_04_same_net_via_on_a_path_centreline_is_exempt_from_that_primitive` (a same-net via on a line and on an arc exempt); `test_ut_drc_04_via_of_another_net_on_a_path_centreline_is_reported` (the same geometry on another net reported); `test_ut_drc_04_same_net_via_tap_band_is_half_the_via_pad` (0.29 mm off the centreline exempt, 0.31 mm, 0.01 mm outside the `pad_mm / 2` band, reported); `test_ut_drc_04_same_net_via_tap_leaves_a_far_primitive_of_the_same_path_checked` (the far primitive of the tapped path, 0.1 mm from the via against a 0.2 mm rule, reported) |
| UT-GEN-01 | Amended 2026-10-05 (U-D3) and 2026-10-08 (U-D4, D-031f): generator contract for spiral, serpentine, wave and a stub | returns a `BoardStack` or Unbuildable, never raises on fuzzed input; spiral and wave stacks hold exactly one board; same design gives the same `stack_hash`; on every board, every circuit path and via ID exists and every winding path belongs to exactly one Member or to `interconnect_path_ids`; every board sets `detail` and a non-empty `derived`; from U-M2e-4, every id of `interconnect_path_ids` has exactly one `interconnect_roles` entry. Revision 2026-10-09 (U-D10, DEF-M3b-03, U-M3-fix3): the wave and the serpentine port each have the fuzz test `test_fuzzed_inputs_give_a_stack_or_unbuildable_never_an_exception` (`tests/unit/generators/wave/test_wave_generate.py` l.321 and `tests/unit/generators/serpentine/test_serpentine_inputs.py` l.88), each with the explicit denormal `@example`. The guard tests refuse each unusable size, count and degenerate end turn with the code of interfaces.md §6 before any geometry is built (`test_unusable_size_is_refused_before_any_geometry` in both `*_inputs.py` files, l.85 and l.148), accept a width exactly at the DRC minimum, and turn `biarc` of coincident points into `DegenerateBiarcError` (`test_wave_inputs.py` l.121). U-M3-fix3 showed that the new serpentine tests fail without the guard (31 of 33, its report) |
| UT-GEN-02 | Dispatch | `build_layout` routes by `design.topology`; calling `generate_wave` with a spiral design raises TypeError |
| UT-GEN-03 | Amended 2026-10-05 (U-D3); single-mode rule ratified 2026-10-08 (U-D4, D-031e; main checks only `one_board_per_phase`, DEF-U-D4-02): serpentine validation | layers per phase 1 or even; copper count = phases x layers per phase for `stack_mode` `single` and = layers per phase for `one_board_per_phase` (one board's stack-up, Xcoil `stackupFor(p, perBoard)` l.686-688), else INVALID with the pointer; `board_gap_mm` below 0 is INVALID and above 10 mm is UNSUPPORTED_RANGE (Xcoil l.127). As implemented (revision 2026-10-08, U-D7; `tests/unit/generators/serpentine/test_serpentine_generator.py` l.88-139): an odd layers per phase gives `INVALID_LAYERS_PER_PHASE`; a copper count that does not fit the stack mode gives `INVALID_SERPENTINE_COPPER_COUNT` in both modes, and the generator also refuses it with `UNBUILDABLE_SERPENTINE_COPPER_COUNT`; a gap of -0.1 mm gives `INVALID_NEGATIVE`, 0 and 10 mm give nothing, and 10.5 mm gives `RANGE_ABOVE_SUPPORTED` |
| UT-GEN-04 | Wave validation; stated as implemented 2026-10-08 (U-D7; `tests/unit/generators/wave/test_wave_generate.py` l.60-89) | each style builds for 1, 2 and 3 phases with the phases in order; 2, 4 and 6 copper layers build with T tracks on even layers and B tracks on odd ones; 1, 3 and 5 copper layers give `UNBUILDABLE_WAVE_LAYER_COUNT` on `/stackup/layers`. After U-M3-fix (D-035e) `validate_design` also reports the count with an INVALID code |
| UT-GEN-05 | New 2026-10-05 (U-D3): one board per phase | `stack_mode` `one_board_per_phase` with 3 phases gives 3 boards in phase order; board k holds only phase k copper and one PhaseCircuit, and its `copper_z_mm` equals the single-board stack-up z plus k x (board thickness + `board_gap_mm`) within 1e-12 mm (Xcoil l.695); `stack_thickness_mm` = n x board thickness + (n - 1) x gap (l.689); no board has interconnect paths or pads, and with the interconnect requested for three phases in star or delta the outcome carries a WARNING issue that the phase connection is made externally (Xcoil warning `INTERCONNECT_EXTERNAL`, l.2525-2535); `stack_mode` `single` gives one board whose `layout_hash` equals the one built with `board_gap_mm` changed (the gap has no effect, l.689 and l.695); a via of board A placed over board B copper produces no DRC pair |
| UT-WND-07 | Amended 2026-10-08 (U-D4, D-031d): delta with k_w3 not zero | `plan_issues(plan, design)` returns `RANGE_DELTA_TRIPLEN` (WARNING, pointer `/connection/topology`) for 12/14 delta and nothing for 12/16 delta; `plan_spiral_winding` returns a plan in both cases |
| UT-WND-09 | Amended 2026-10-08 (U-D4, D-031d): manual assignment override | an unbalanced manual assignment returns a plan, and `plan_issues` returns `RANGE_MANUAL_ASSIGNMENT_UNBALANCED` with the magnitude spread as `value`; a balanced one returns no issue |
| UT-PHY-22 | New 2026-10-08 (U-D4, D-031f): interconnect copper and loss sum (EQ-23, EQ-26), U-M2e-4 | on a hand-built star layout with known lead, link and ring resistances: `resistance_line_ohm` and `loss_interconnect_w` equal the EQ-23 closed form within 1e-12 relative; delta: P_ic = I_line^2 sum stub + I_ph^2 sum link and the circulating loop includes the links; open: P_ic = 0; `loss_total_w` is the sum of its five terms, `efficiency` = P_out / (P_out + P_loss), `motor_constant_n_m_per_sqrt_w` = T / sqrt(P_Cu) and 0 at zero current; a layout with interconnect paths and no roles gives `loss_interconnect_w` status `unresolved`; golden cases against Xcoil `pInterconnect`, `rLineLine`, `lossTotal`, `efficiency` and `motorConstant` on star and delta layouts |
| UT-PHY-23 | New 2026-10-08 (U-D4, D-031f): EQ-20 for any phase count, U-M2e-4 | with `dc_link_v` set, one-, two- and three-phase designs return a `torque_speed` estimate; the open connection uses the full-bridge voltage (SVPWM and SPWM V_dc / sqrt 2, six-step 4 V_dc / (pi sqrt 2), Xcoil l.2681) and the phase resistance; star and delta keep today's three-phase values unchanged; golden against Xcoil `driveAnalysis` for a two-phase design |
| UT-MOD-01 | Blank draft | `blank_draft(t)` has no required value and every optional field at its neutral value; `parse_draft` returns DraftIncomplete listing all required pointers in form order |
| UT-MOD-02 | Draft round trip | `parse_draft(draft_from_design(d)) == d` for every example |
| UT-MOD-03 | Field table completeness | every leaf of every DesignParameters variant has exactly one FieldSpec where it applies; `_mm` fields carry Unit.MM, `_rad` fields Unit.RAD; property fields are the closed list in ADR-0010 |
| UT-MOD-04 | Provenance derivation truth table | origin present or absent x value equal or not x measured or not; re-entering the current value changes nothing; setting a changed field back to the example value gives `example` |
| UT-MOD-05 | `mark_measured` refusals | empty source refused; design-kind field refused; a later value change drops the measurement |
| UT-RES-03 | Registry integrity (Phase 1 row, REQ-T-04). Amended 2026-10-09 (U-D11, D-040 b, U-M4c-4 f) | the packaged registries equal what their source documents give. `test_registry_packaged_counts_and_versions` (`tests/unit/results/test_registry.py` l.34) reads `expected_copies` of `tools/sync_registry.py` (l.51), which applies the filter that writes the copies to `docs/phase2/engineering/equation_registry.json` and `docs/phase2/evidence/evidence_register.json`. It compares the number of equations, the number of evidence entries and the version string (`v1+` and the first 12 hex digits of each copy's SHA-256) with `load_registry()`. The literal counts 30 and 108 are gone: they broke three times when Agent 5 added EV rows (store `decisions.tsv`, 2026-10-09T11:40Z). A stale packaged copy still fails, and Fable repairs it with `tools/sync_registry.py`. The helper `load_sync_tool` (`tests/unit/results/registries.py` l.26) loads that script for this test and for `test_sync_registry.py` |
| UT-RES-07 | EC-05 labelling (DEF-23) | `edge_leakage_fraction.status == assumption`; the EC-05 ValidityFlag has `metric_bound = lower_bound`, calibration `inferred`, transfer and threshold `assumption`; affected results list the transfer assumption in their tag |
| UT-IO-07 | Project file provenance and drafts | save and load keep origin example, per-field provenance and measurement sources; an incomplete draft loads as LoadedDraft with the same missing list; a stored `example` entry that disagrees with the packaged example is reported |
| UT-IO-08 | Examples | every packaged example loads, validates and computes with no ERROR issue; every title contains "Example". Revision 2026-10-09 (U-D10, U-M4c-3): every example has a `display_note` that names no other program, no `engine.js` and no repository path (UX-AC-03; `test_ruling_g4_example_items_show_a_600_title_over_a_text3_note_free_of_other_programs`, `tests/ui/qt_design/test_ruling_g.py` l.132; interfaces.md §9.1). The title check of UX-AC-03 is a strict xfail (§5.6). Revision 2026-10-09 (U-D11, D-041a (Fable, 2026-10-09), U-S4e ruling g): a title is free English display text, so "every title contains "Example"" no longer holds. The criterion becomes: the title, the note and the saved design name of each example name no other program and no repository path, and the saved project holds no `example` object (`test_ux_ac_03_an_exported_example_names_no_other_program_and_no_repository_path`, `tests/unit/embodic_io/project/test_examples.py` l.47, one case per example file). UX-AC-03 (`docs/phase2/design/acceptance_criteria.md`) also asks that the five gallery titles equal the list of ruling g: "Spiral, 12 coils, 16 poles", "Spiral, 12 coils, 14 poles", "Spiral, 12 coils, 10 poles (D08)", "Serpentine, 16 poles", "Wave, 16 poles, involute". No test on main 9776555 asserts that equality (`verified` by reading `test_ruling_g.py` and `test_examples.py`), and the brief of U-M4e-1b asks for the files to carry those titles exactly, for the two xfails to flip and for a check that a title change leaves the design hash alone. A title change does not change the design hash. On main 9776555 `test_ut_io_08_spiral_examples_are_packaged_with_example_titles` (`test_examples.py` l.30) still asserts "Example" in each title, and U-M4e-1b (in flight) replaces it. Revision 2026-10-11 (U-D12, D-041a, D-041b; main 4fda98d, `verified` by reading, and by running the tests named here, 2026-10-11): the sentences above that say "still asserts", "in flight" or "no test" are closed. `test_ut_io_08_examples_are_packaged_with_the_ruling_g_display_titles` (`test_examples.py` l.44) asserts that the five titles equal the list of ruling g (`RULING_G_TITLES`, l.26). `test_d_041b_each_example_design_is_named_by_its_display_title` (l.52) asserts that `load_example(id)[1].name` equals the title, because D-041b makes the design `/name` equal the title (the window title and the export stem show it). `/name` is inside the design hash and the title is not, so U-M4e-1b left the five hashes unchanged and D-041b moved all five (`EXAMPLE_HASHES`, l.34). `test_ut_io_08_the_packaged_design_hashes_are_pinned` (l.58) pins them, and the unit that changes an example design edits that table. `test_ux_ac_03_an_exported_example_names_no_other_program_and_no_repository_path` is at l.68 and has no xfail mark. Run: `9 passed, 39 deselected` for `pytest tests/unit/embodic_io/project/test_examples.py tests/unit/embodic_io/exporters/test_report_readme_bundle.py -k "test_ut_io_08_examples_are_packaged or test_d_041b or hashes_are_pinned or ux_ac_03 or ruling_f"` (the filter also selects the five cases of UX-AC-03 and the colophon test) |
| UT-EXP-01 | SVG | parses with `xml.etree`; path, via and pad counts equal the Layout; `<metadata>` holds the REQ-T-07 fields; phases carry class and label in both render modes. Revision 2026-10-09 (U-D10, D-039 c): in both render modes the D08 drawing holds the 12 `coil-label` texts with the D08 polarities and 12 eye fills clipped to their discs, with no hatch end outside the disc (`test_d08_drawing_labels_every_coil_and_fills_every_eye_clipped`, `test_svg.py` l.117); the B hatch lines are 0.4 mm apart at 1:1 (`test_d08_hatch_pitch_is_0_4_mm_at_1_to_1`, l.140); each phase has a legend swatch and the text "Phase A", "Phase B" or "Phase C" (l.102-106); no copper or legend bar has a dash pattern (l.152); the footer fits inside the drawing (l.161). The halo is a second `coil-label-halo` text under each label, which `tests/unit/embodic_io/exporters` does not assert (`not tested`) |
| UT-EXP-02 | DXF complete, outline, screws | ezdxf audit 0 errors; outline file holds only outline and bore entities with every end point shared by exactly two entities; screws file holds only circles, count = holes |
| UT-EXP-03 | PDF report | pypdf opens it; at least 1 page; text contains "Key results"; every reported value has a unit and a status word. Revision 2026-10-09 (U-D10, D-039 b and c): the embedded fonts print units as the UI does, so pypdf extracts `µH`, `mΩ` and the U+2212 minus (`test_ut_exp_03_report_prints_units_as_the_ui_does`, `test_report_readme_bundle.py` l.70); the drawing page holds the 12 D08 labels and the legend and no dash pattern (l.127); a character without a glyph fails the export with `INVALID_EXPORT_GLYPH_MISSING` and is never dropped (l.145); the stdlib font reader agrees with fontTools on every code point and width (`test_pdf_fonts.py` l.19). Revision 2026-10-09 (U-D11, U-S4e rulings e1, e2 and f): the extracted text joins every number and unit with U+00A0 (`502\u00a0mΩ`, `1.34\u00a0µH`) and holds no number, plain space and unit (l.70); the first page lists exactly three font resources, `Inter-Regular`, `Inter-SemiBold` and `JetBrainsMono-Regular`, each a Type0 font with Identity-H, a `FontFile2` and a `ToUnicode` map (l.70); the report headings use the SemiBold file and no stroke trick (`test_ruling_e2_report_headings_use_the_semibold_file_and_no_faux_bold`, l.95); the tables end with one colophon line and the report has no page footer (`test_ruling_f_report_ends_its_tables_with_one_colophon_line_and_no_page_footer`, l.113) |
| UT-EXP-04 | README | names every exported file, units (mm), frame (y up, centred on the shaft axis) and the estimate caveat |
| UT-EXP-05 | Bundle and DRC refusal | ZIP holds the selected files plus README.txt; with DRC errors and no confirmation every writer returns ExportRefused |
| UT-SES-01 | Session state machine | empty to drafting to computed; an edit making the design incomplete returns to drafting and keeps the last outcome marked stale; re-entry is a no-op (no undo entry, no compute) |
| UT-SES-02 | Undo and redo | 50 steps restore the identical design hash and provenance map |
| UT-CLI-02 | Incomplete project in the CLI | `embodic-cli compute` on a draft exits 1 and prints the missing pointers |

### 5.2 Property tests

| ID | Property |
|---|---|
| PR-01 | Amended 2026-10-05 (restated from Phase 1, DEF-V1-01): DRC soundness under D-006. Whenever `drc.passed`, an independent dense check finds no non-exempt pair below rule - 1e-6 mm; every pair it finds below that is reported by `run_drc`; and every pair `run_drc` reports is below rule - 1e-6 mm by the dense check (no false positives). The last clause excludes pad to pad and pad to via pairs with a non-round pad, which the circumscribed-radius rule may over-report (interfaces.md §7). Exemptions follow interfaces.md §7 |
| PR-02 | Restated from Phase 1 (DEF-V1-01): the symmetry shortcut equals the full check. With `use_symmetry` True and False, the same violation set and the same `measured_min_mm` per kind within 1e-9 mm; an asymmetric layout falls back to `grid+exact` |
| PR-13 | DRC never under-reports, for every generator: whenever `drc.passed`, Agent 4's brute-force checker finds no non-exempt pair below rule - 1e-6 mm, and every pair it finds below that is reported (PR-01 extended to serpentine and wave) |
| PR-14 | Rotation symmetry for serpentine and wave: rotating the start angle by one electrical period shifts every phase phasor by the expected angle (1e-9 rad) and leaves abs(Ke), R and all DRC values unchanged (1e-9 rel., 1e-9 mm). Revision 2026-10-08 (U-D7, D-035d, D-035e): the wave has no start angle field, so the wave test rotates through `generate_wave_rotated`, and its phasor part waits for a per-phase phasor field (PR-07). The serpentine counter-example with sharp corners and one turn (DEF-M3a-02) changes Ke by 8.5e-9 rel. U-M3-fix diagnoses it, and the outcome sets the tolerance. If the cause is float accumulation, the Ke tolerance becomes 1e-8 rel. and this row names that cause. If the cause is a defect, U-M3-fix fixes it and 1e-9 rel. stays. Revision 2026-10-09 (U-D8, D-036c; `tests/unit/property/serpentine/test_serpentine_properties.py` l.39 and l.156-175 on main 8a297a0, `verified` by reading): the cause is float accumulation (branch B). A side line that is a whole number of 0.5 mm chords changes its computed length by 1 ulp under rotation, so `ceil` gives 36 or 37 chords. The serpentine Ke tolerance is 1e-8 rel. (`KE_REL_TOL`), and the DEF-M3a-02 strict xfail is removed. The phasor angle, R and the DRC values keep 1e-9. The wave test keeps 1e-9 rel. |

### 5.3 UI tests (pytest-qt, offscreen)

| ID | Scenario | Criterion |
|---|---|---|
| UI-22 | Load an example | every field shows the "Example" chip; edit one field and its chip disappears; set it back and the chip returns; no badge changes |
| UI-23 | Start | the window opens in the empty session with New design and Examples; no compute runs |
| UI-24 | New design | choose a topology; the form is blank; Compute is disabled and shows the missing count; filling the last required field triggers exactly one compute |
| UI-25 | Toolstrip | every TOOLSTRIP action has an icon file, English label, tooltip and accessible name; its command resolves; arrow keys move within a tab; icons recolour after a theme switch. Revision 2026-10-09 (U-D11, F21, U-M4e-1): `act-open` is enabled and its command `open_project` opens a saved D08 file into the inspector and computes it (`tests/ui/qt_shell/test_open_project.py` l.25); a file that does not load shows why and keeps the open design (l.43). The board picker is not a TOOLSTRIP action and is not part of this row (interfaces.md §11) |
| UI-26 | Themes | switch light, dark and system at runtime; every widget restyles; the choice persists after restart |
| UI-04 | Layer visibility toggles. Phase 1 row, amended 2026-10-09 (U-D10, U-M4c-3) | hidden layers are absent from the scene and return when shown (`tests/ui/qt_shell/test_theme_and_geometry.py` l.134); hiding the top layer keeps a label for every phase and moves the eye fills to the next visible layer, 12 of them for D08 (l.147); the view-model records a hidden layer and restores it (`tests/unit/ui/shell/test_outcome_viewmodel.py` l.190) |
| UI-27 | Phase render mode. Amended 2026-10-09 (U-D10, D-039 d, U-M4c-3, UX-AC-27) | colour and greyscale-hatch toggle in the geometry view and charts; labels present in both and read phase, number and U+2212 for minus (D08: A1 to A4, B1 to B4, C1 to C4; the earlier assertion that pinned a hyphen is replaced); the canvas fills the eyes the exports fill and each eye fill is its coil's eye disc, clipped to it; no label overlaps another at fit zoom or at 3x, and the labels are placed again after every zoom, pan and resize step; a skipped label shows in the hover tooltip of its copper; the legend shows a solid copper bar, an eye swatch and the phase name; the eye hatch is a screen-space pattern, so it shows at fit zoom (`test_outcome_viewmodel.py` l.130-189, `tests/ui/qt_shell/test_canvas_labels.py` l.77-182, `test_theme_and_geometry.py` l.70 and l.88). Revision 2026-10-09 (U-D11, U-S4e ruling h, U-M4e-1): the first label of each phase and sign is forced, so the wave fit view shows both signs of every phase (`test_ruling_h_the_wave_fit_view_labels_both_signs_of_every_phase`, `test_canvas_labels.py` l.201); every phase with copper in view has a label and every leader stays inside the view at 4x zoom on three corners of the D08 and wave examples (l.211); fit zoom survives a resize until the user zooms (l.231); the pure placement is pinned in `tests/unit/geometry/marks/test_labels.py` (l.55, l.139, l.150, l.158, l.169) |
| UI-28 | Applicability matrix | for each topology and option combination the visible inputs equal `field_specs` filtered by applicability |
| UI-29 | Export confirmation | with an injected DRC error the confirmation lists the failures and has focus on Cancel |
| UI-30 | Chart audit | one unit per y axis, legend and direct labels, data-table alternative, status badge |
| UI-31 | Reduced animation | with the OS animation setting off no transition runs |
| UI-32 | Illustrative stamp | drawings not produced by the engine carry "Illustrative, not computed" |
| UI-33 | EC-05 disclosure | the disclosure of Ke shows e_edge, the words "at least" and "assumption", and the 10 % cap label |
| UI-34 | Number formatting in comparisons | counts as integers; deltas with sign and glyph, never colour alone |

Phase 1 UI-01 and UI-08 are withdrawn (replaced by UI-23 and UI-22). The remaining Phase 1 UI tests run on the
offscreen platform.

### 5.3.1 End-to-end tests and the verify skill (revision 2026-10-11, U-D12)

U-M4e-2 built `tests/ui/qt_e2e/` and `.claude/skills/verify/` on main 4fda98d (`verified` by reading the files). The
tests start the app's own shell through `create_shell` (`conftest.py`, fixture `window`: 1280 x 800, light theme, a
throwaway settings file) and find every widget by `objectName`. They run offscreen, so Windows behaviour is `not tested`.

| ID | Test (file in `tests/ui/qt_e2e/`) | What it checks | `not tested` |
|---|---|---|---|
| AX-02 | `test_ax02_open_edit_three_inputs_recompute_open_eq_details_and_export_svg_with_the_keyboard_only` (`test_ax02_keyboard_only.py` l.43) | key events only, no pointer event: open D08 from the Examples gallery, type `param-speed`, `param-current` and `param-copper-temp`, recompute, open `res-r-phase-how`, open the guide at EQ-10, export one SVG | Keys inside the file dialog. The Windows build opens files in the native dialog, which an offscreen run cannot drive, so "open" is the gallery |
| AX-04 | `test_ax04_every_interactive_widget_reaches_24_px_and_check_rows_32_px` (`test_ax04_target_size.py` l.130), `test_ax04_check_rows_take_a_click_in_their_whole_32_px_rectangle` (l.139), `test_ax04_a_click_anywhere_in_a_check_row_toggles_the_box` (l.146) and `test_ax04_a_click_on_the_label_text_toggles_the_box` (l.159) | every visible, enabled button, tab, slider, field and focusable chip is at least 24 px on its smaller side, and a check box or radio button is measured by its click rectangle at 32 px. The screens are the empty session, D08 with each inspector, results and toolstrip tab, and the New design, Examples and Export dialogs, all at 1280 x 800. Revision 2026-10-13 (U-D14): the four tests pass on main 6243163 and carry no xfail mark (§5.6). The names above replace `test_ax04_every_interactive_widget_outside_the_open_defects_reaches_24_px_and_check_labels_32_px`, `test_ax04_open_target_size_defects` and `KNOWN_UNDERSIZED`, which no longer exist (`verified` by grep) | WCAG's spacing exception for scroll bars was unruled (U-S4g). The scroll bars now reach 24 px, so the walk needs no exception |
| UI-09 | `test_ui09_the_window_renders_at_each_scale_factor` (`test_ui09_scaling.py` l.31) | one new process per `QT_SCALE_FACTOR` of 1, 1.5 and 2; the grab is 1280 x 800, 1920 x 1200 and 2560 x 1600 pixels. The grabs are kept for Agent 1 | "No clipped or overlapping text" is a judgement on the images, so it is `not tested` by code |
| walkthroughs | `test_walkthrough_open_edit_recompute_inspect_export_save_and_reopen` (`test_walkthroughs.py` l.123), three cases | one user route per topology, listed below | typing into the file dialog. The cases answer it with `QFileDialog.selectFile` |
| UX fixes of `m4_review_2.md` §6 | `test_f2_the_pair_list_rotation_chip_carries_its_provenance_for_the_dashed_example_rule` (`test_review_2_fixes.py` l.27), `test_ruling_i_the_screw_buttons_are_push_buttons_with_a_3_to_1_boundary` (l.45), `test_ruling_j_the_last_column_takes_the_remaining_width_so_no_header_cell_is_empty` (l.65, two sizes) | chip provenance, screw buttons, stretched last column at 1280 x 800 and 960 x 540 | |

The three walkthroughs (`WALKTHROUGHS`, `test_walkthroughs.py`) cover the three topologies. Each case checks that the app
starts in the empty session, opens a design, types the same three operating inputs, recomputes with `act-compute`, opens
`res-r-phase-how`, shows the `tab-drc` tab, exports SVG and PDF, saves with `act-save`, edits one input, reopens with
`act-open` and compares the design hash with the saved one.

| Case | Opened from | Example |
|---|---|---|
| `spiral-d08` | the Examples gallery (`btn-empty-examples`) | `spiral_12c10p_d08` |
| `serpentine` | New design (`btn-empty-new`), with the example as the starting values | `serpentine_16p_example` |
| `wave` | the Examples gallery | `wave_16p_example` |

The module docstring of `test_walkthroughs.py` calls the save and reopen step "the UI-21 path". UI-21 is the autosave and
recovery test of Phase 1 (a process killed after an edit), and these cases do not kill a process. They cover REQ-F-15,
REQ-F-31 and REQ-T-01 through their `req` marks, and UI-21 stays without an e2e test (`verified` by reading).

UI-20 (rotor-angle overlay, REQ-F-30, priority `could`) has no test because the build has no overlay. Phase 1 wrote it
"if implemented". A search of `src/embodic/ui` for "rotor angle" and "overlay" finds nothing (`verified` by grep), and
`verify.py` lists it under `NOT_TESTED` (l.29). The row stays in the matrix and counts as not implemented, not as a
pass. The U-M4e row of `work_breakdown.md` §1 listed UI-20 among the tests that pass, and its done predicate is amended there.

The verify skill is the UI verification entry point. From the repository root:

```
.venv/bin/python .claude/skills/verify/verify.py --acceptance
```

It runs a read-only doctor, then `tests/ui/qt_e2e`, then the 41 rows of `docs/phase2/design/screenshot_checklist.md`
through `tests/ui/qt_shell/capture_acceptance.py`, then the UI-09 grabs, then `shot_measure.py`. It writes PNGs and
`report.json` to `build/verify/<UTC timestamp>/` and copies the shots to `build/screens/acceptance/`. The exit code is
0 when the doctor passed, every e2e test passed or was a strict xfail, and every captured row has files. `report.json`
carries a `not_tested` list with a reason per item (`NOT_TESTED`, `verify.py` l.27-35). `--doctor` runs the read-only checks only and
`--rows S04 S07` captures only those rows. U-M4e-2 reported `12 passed, 4 xfailed` for the e2e step, `40 of 41` rows
captured and `passed: true` (U-M4e-2 report, quoted). Row S33 is the one not captured: the build has no Tests dialog, and M5
carries it (D-042 draft, `unresolved` until Fable records it; `work_breakdown.md` §8).

### 5.4 Static, language and accessibility gates

| ID | Gate |
|---|---|
| MT-01 | Amended: import-linter contracts C1 to C4 of `package_layout.md` §3 (core layers with generators above io, outcome, physics and drc; no Qt outside the Qt adapter modules; UI-internal layers; no KiCad or other GUI toolkits) |
| MT-07 | Scope guard for D-009: no `kipy` or `pcbnew` import, no `.kicad_pcb` writer, no KiCad option in CLI choices, and no "KiCad" in the string catalogue |
| MT-08 | New 2026-10-05 (U-M1y): no package folder under `tests/` or `src/` whose name becomes a top-level module name shadows a standard-library or installed module (`sys.stdlib_module_names`, `importlib.metadata.packages_distributions()`), and no two such folders share a name (`tests/static/test_mt08_no_stdlib_shadowing.py`; naming rule in package_layout.md §1) |
| LG-01 | Amended 2026-10-04 (U-M1a deviation, ratified in part). From M1: every string literal in `src` holds only printable ASCII, tab, newline and the allowed unit symbols (U-M1a's character-class check). From M4: every word in the string catalogue and report templates is in an English word list plus the glossary allow-list. The word list has no source yet (no dictionary package in package_layout.md §5): `unresolved`; U-M4b proposes one through Fable before M4 exit. Revision 2026-10-09 (U-D11, D-040 a and c): one module may add characters of its own. `MODULE_SYMBOLS` (`tests/static/test_lg_language.py` l.12) maps a module name to them. `embodic.results.labels` admits η, δ and Δ, the Greek letters of the equation-specification symbols, and no other module may hold them (`test_lg01_admits_the_spec_greek_letters_in_the_label_module_only`, l.81). D-040 c adds U+00A0 for `embodic.results.formatting` only, which U-M4e-1b builds; `MODULE_SYMBOLS` has no such entry on main 9776555 |
| LG-08 | No Thai characters in any shipped file (src, resources, examples, templates) |
| AX-08 | Phase colours at least 3:1 against the canvas in both themes; the palette validator passes for both themes; greyscale ladder steps distinguishable |
| AX-09 | Every toolstrip icon rendered in both themes reaches at least 3:1 against the toolstrip background |
| PF-05 | Baseline record for one serpentine and one wave example (no target; recorded for regression) |

### 5.5 Timing tests (revision 2026-10-08, U-D4)

A test that runs in the commit profile does not depend on how fast the machine is. The commit gate failed once on
`tests/unit/drc/test_run_drc.py` `test_cancel_from_another_thread_stops_a_long_run` (U-E3 report, Fable's gate on
bd019c5): the test cancels from a 0.05 s timer and asserts a 2 s wall-clock bound, so it fails both when the run ends
before the timer fires and when a loaded machine runs slowly. Agent 4 applies these rules in U-V2:

1. Prefer a trigger that does not use the clock. To test mid-run cancellation, pass a token whose `cancelled`
   property turns true after its k-th read. Assert that the run returns `None` and that the token was read fewer
   times than an uncancelled run reads it.
2. When the property under test is a time, measure a baseline in the same test (for example, the same operation
   uncancelled) and bound the result relative to it, such as "below half the baseline". State the ratio and why.
   An absolute bound in seconds is allowed only beside a baseline of the same run.
3. A test that needs neither form is marked `slow` (`tools/ci.py` runs it in the nightly profile only), and its
   docstring names the time it measures.
4. Performance budgets (PF tests) stay in the release profile with their own measured baselines.

Gate wall time (revision 2026-10-08, U-D7, D-035h). The commit gate on main 4aec992 ran 2006 tests in 422 s, about 7
minutes (Fable's gate run, U-M3a report). U-M3b measured 269 s for 1490 tests on its branch. The time is not a gate
criterion. Shortening it is a Phase 5 item.

### 5.6 Strict xfails on main 76f054b (revision 2026-10-13, U-D14; first written 2026-10-11, U-D12)

One mark, `xfail(strict=True)`, is left on main 76f054b (the same on main 6243163). `grep -rn "xfail" tests --include=*.py` finds it at
`tests/unit/physics/test_oracles_m5.py` l.239, and finds three docstrings that use the word (`test_oracles.py` l.98,
`test_oracles_m5.py` l.124 and l.252). The mark covers `test_or07_d09_phase_emf_within_the_registry_band`, which is
parametrised over the D09 builds A and B, so it holds two cases. `pytest tests/unit/physics/test_oracles.py
tests/unit/physics/test_oracles_m5.py -rxs` printed `8 passed, 2 skipped, 2 xfailed` (`verified` by running it on main 76f054b, 3 s, and earlier on main 6243163).
A strict xfail fails the run when it passes, so the owner removes the mark in the same change that fixes the cause. The
commit and nightly profiles run the test. They ignore only `tests/performance` and `tests/packaging` (`tools/ci.py` l.28
and l.42-43), and the test carries no `slow` or `manual` mark.

| Test | Mark reason | Ids it carries | Open point and owner |
|---|---|---|---|
| `test_or07_d09_phase_emf_within_the_registry_band[A]` and `[B]` (`test_oracles_m5.py` l.238-262) | F-OR07 (D-045a): the D09 phase EMF lies outside [-5 %, +5 % + e_edge] for both pre-registered builds | OR-07, EQT-05-O2, EQT-06-O2 | The cause is `unresolved`: the spiral geometry G2 and the edge leakage (`docs/phase2/engineering/oracle_tests_spec.md` §OR-07; U-E9 lists UD-25 and G2 as the blocker). The band is never widened. No owner is named, and the mark goes in the change that fixes the cause |

The mark has one effect on the evidence of §5.7. A record that xfails has the outcome "skipped" in the REQ report, and
interfaces.md §3.1 keeps an ID out of `passed_tests` unless every record that carries it passed. EQT-05-O2 and EQT-06-O2
therefore cannot enter `passed_tests` while OR-07 is an xfail (`inferred` from that rule and the U-M5o report; not run).

Oracle results on main 76f054b (D-045g; the values equal those on main 6243163). The plan records them here because this section is where the one oracle outside
its band is listed. `verified` by running `PYTHONPATH=src pytest tests/unit/physics/test_oracles.py
tests/unit/physics/test_oracles_m5.py -s -rxs`, which prints each line below, except where the cell says D-045g. A value
here compares a model with a published figure. None is a validation by experiment.

| Oracle | Quantity (model against reference) | Result | Band | Verdict |
|---|---|---|---|---|
| OR-01 | D08 line-line Ke, `test_oracles.py` | -0.40 % (D-045g, read; the test passed in this run and prints no value) | O1 band with e_edge (§4) | in band |
| OR-02 | D09 phase R at 20 °C against 1.07 ohm | A 1.11558 ohm, +4.26 %. B 1.01158 ohm, -5.46 % | +-8 % | in band |
| OR-03 | D10 phase R against 2.15 ohm | skipped: not representable, unequal-width concentric geometry and unprinted inputs (G40), `test_oracles_m5.py` l.313 | none | not run |
| OR-05 | D08 phase R at 50 °C against 0.39 ohm | loop only 0.381201 ohm, -2.26 %. Full phase 0.485162 ohm, +24.40 % | information, no band | information |
| OR-06 | D08 current at the copper-loss budget | 1.84900 A on 0.39 ohm, inside the print-rounding interval [1.8373, 1.8610] A that holds 1.84 A. On the embodic full-phase R: 1.65778 A | no band | consistent within print rounding |
| OR-07 | D09 phase EMF at 2000 rpm against 6.21 V | A 7.37166 V, +18.71 %, band [-5.0 %, +7.59 %]. B 5.74941 V, -7.42 %, band [-5.0 %, +8.34 %] | [-5 %, +5 % + e_edge] | out of band, strict xfail F-OR07 |
| OR-08 | D09 B_z peak at mid-radius, harmonics 1 to 13, against the figure reading 0.72 to 0.75 T | 0.7384 T. The fundamental b1 is 0.846122 T and is recorded, not compared | [0.7125, 0.7560] T | in band |
| OR-09 | D09 inductance against 14.8 uH measured | A 8.9536 uH (-39.5 %). B 5.0355 uH (-66.0 %) | none, characterisation only | the test checks only that the value is finite and positive |
| OR-10 | D10 winding temperature rise against 83.2 K | skipped: not representable (G40), `test_oracles_m5.py` l.318 | none | not run |
| OR-11, OR-12 | EQ-05 field per layer and EQ-12 eddy loss | no Phase 2 test. The cases need FEA and move to Phase 3 (`oracle_tests_spec.md` §OR-11 and OR-12, U-E9, D-045b) | none | Phase 3 |

OR-04 is outside D-045g, and this unit did not look at it. OR-07 and OR-08 are "not independent of EC-05" (§4). The
skipped tests carry the reason `NOT_REPRESENTABLE` (`test_oracles_m5.py` l.42). The M2 exit of §7 names the four
outcomes that D-045b allows: pass, the strict xfail F-OR07, the skip of OR-03 and OR-10, and the Phase 3 cases OR-11 and
OR-12.

Marks that are gone since main 4fda98d (U-D12 listed six):

- The four AX-04 cases. DEF-M4e2-01 (the EQ chip and the "n assumptions" tag, 22 px) and DEF-M4e2-03 (scroll bars, 12 px)
  were fixed in U-M4e-3b. DEF-M4e2-02 (check box click rectangles) was fixed in U-M4e-3c, which also removed both AX-04
  marks (reports of U-M4e-3b and U-M4e-3c, read). `test_ax04_target_size.py` now holds four tests and no mark
  (`def test_` at l.130, l.139, l.146 and l.159), and `pytest tests/ui/qt_e2e/test_ax04_target_size.py` printed
  `4 passed in 40.71s` (`verified` by running it). The first test, `test_ax04_every_interactive_widget_reaches_24_px_and_check_rows_32_px`,
  fails for any new undersized button, field, combo, tab, chip, scroll bar or check row.
- The two DEF-M1V-03 cases, closed by U-V1c and the GR-19 DRC reading of D-046f (§5).

The two UX-AC-03 cases that this section listed on main 9776555 are closed. U-M4e-1b retitled the five examples and
removed the mark on the title test. The mark on the serpentine export scan stayed, because the design `/name` still held
the old title, which names Xcoil. D-041b made the name equal the display title in U-M4e-2, and the case passed, so
U-M4e-2 removed the mark (U-M4e-2 report; `grep` finds no `SERPENTINE_TITLE_NAMES_XCOIL` in `tests`). The cases are now
`test_ux_ac_03_example_titles_are_the_ruling_g_list_and_name_no_other_program` (`tests/ui/qt_design/test_ruling_g.py`
l.177) and `test_ux_ac_03_an_exported_example_names_no_other_program_and_no_repository_path`
(`tests/unit/embodic_io/project/test_examples.py` l.68, one case per example file).

The five marks of U-D10 are closed as follows. The two U+202F cases passed after ruling e1 replaced U+202F by U+00A0
(`test_font_files.py`, `KNOWN_GAPS` is gone, `verified` by grep). The two 300 px inspector tests passed after ruling c
split `pair-list` out of `layer-list` and cut the screw table to three columns
(`test_ruling_c_layer_and_pair_lists_fit_the_300_px_inspector_with_kind_in_full`, `test_ruling_g.py` l.64, and
`test_ruling_c_the_screw_table_has_three_columns_and_the_selected_pattern_its_own_fields`, `test_inspector_widgets.py`
l.112). The fifth is the title case above.

### 5.7 M5 tests: test evidence, self-tests and packaging (revision 2026-10-12, U-D13)

Each new contract point of interfaces.md §3.1, §12 and §14 and package_layout.md §5.2 has one ID here. The `req`
marker each test carries is in the second column; the requirements' Tests column lists the same IDs.

| ID | Check (REQ marker) | Criterion |
|---|---|---|
| UT-RES-08 | Evidence reader (REQ-T-05), U-M5b | `load_registry(root)` on a temporary copy of `resources/` plus a written `passed_tests.v1.json` whose versions and `source_sha256` match returns `passed_tests` equal to the file's list and `evidence_build_id` equal to its `build_id`. Each of these gives `frozenset()`, `evidence_build_id` None, no exception and no issue added to `Registry.issues`: no file; a file that is not JSON; `format` other than `"embodic.passed-tests"`; `format_version` 2; a missing key; `passed_tests` not a list of strings; `embodic_version` changed; `registry_version` changed; `source_sha256` changed. `evidence_applies(..., source_sha256=None)` ignores only the source hash. `package_source_sha256` changes when one byte of one `.py` file changes and returns None for a folder without `.py` files |
| UT-RES-09 | Badge change from the evidence (REQ-T-05), U-M5b | with evidence that lists every linked test of EQ-10 and of EQ-05: a result whose chain is EQ-10 alone has badge `verified`, and `test_state("EQ-10")` is `verified`; a result whose chain holds EQ-05 has badge `inferred` and `test_state("EQ-05")` is `inferred`; an EQ-14 chain (`cannot verify yet`) stays `unresolved`; a result with an empty chain stays `not tested`; the assumed-inputs tag, the validity flags and the value are equal to the same result computed without evidence. With evidence that lists all but one linked test of EQ-10, the EQ-10 result stays `not tested` |
| TR-05 | Evidence writer (REQ-T-05), U-M5b | on fixture REQ reports, `passed_registry_tests` passes an ID only when at least one record carries it and every carrying record passed; one skipped carrier keeps it out; an unknown eqt ID raises ValueError. `record_main` exits 1 and writes nothing for `--profile commit`, a missing report, a report with one failed record, or an unknown ID. On a valid report it writes a file that `parse_passed_tests` reads back with the same `passed_tests`, sorted keys, a `platform` value equal to `platform.platform()` and no key or value that holds `platform.node()` or the home folder path |
| PK-10 | Evidence in the wheel (REQ-N-06, REQ-T-05), U-M5b; runs after the record step | `tools/ci.py --profile release` deletes the evidence file first; when every gate passed it writes it, builds the wheel, and `tests/packaging/evidence/` checks that `embodic/_resources/evidence/passed_tests.v1.json` in the wheel is byte-identical to the recorded file and that a clean venv with the wheel installed reports a non-empty `load_registry().passed_tests`. A release run with one red gate leaves no evidence file |
| PK-11 | Self-test from the installed wheel (REQ-N-06), U-M5d | in a clean venv holding only the runtime lock file and the wheel (no pytest, no `tests/`, no `docs/`), `embodic-cli selftest` exits 0 and prints "45 tests: 45 passed, 0 failed" |
| UT-SLF-01 | The catalogue holds on the build (REQ-F-25), U-M5d | `run_selftests(SELFTESTS)` returns 45 results in catalogue order, every one `passed`; the IDs are unique and equal the ID list of interfaces.md §14 |
| UT-SLF-02 | Catalogue drift (REQ-F-25), U-M5d | the CF-09 literals equal the CF-09 rows of `docs/phase2/engineering/oracle_cases.json`; the hash literals equal `EXAMPLE_HASHES` of `tests/unit/embodic_io/project/test_examples.py`; every `source_test` names a file that exists and a `def` of that name in it |
| UT-SLF-03 | Runner behaviour (REQ-F-25), U-M5d | with fake checks: a value outside tolerance gives `failed` with a message that names the expected value, the observed value and the tolerance; a `measure` that raises gives `failed` with the exception type and text, and the next check still runs; a token cancelled from `on_result` after the first result leaves every later check `not run` and `cancelled` True; `ok` is False for any failure or any `not run`; `selftest_to_json` round-trips through `json.loads` |
| UT-CLI-03 | `embodic-cli selftest` (REQ-F-18), U-M5d | one line per check and the summary line; exit 0 when every check passed; exit 1 with the catalogue monkeypatched to hold one failing check, and that check's line names it; `--json OUT` writes the `selftest_to_json` document |
| UI-35 | Tests dialog (REQ-F-25), U-M5d, pytest-qt offscreen | `btn-tests-run` starts the run in a worker thread (the measure functions run on a thread other than the GUI thread); `tests-table` gains one row per result with ID, group, the result icon and its word, duration and message; `tests-summary` reads "45 tests: 45 passed, 0 failed"; Esc and **Stop** cancel, and the remaining rows read `not run`; a second run starts from an empty table; no badge in the results view changes during or after a run |

D-045f and D-046e (revision 2026-10-13, U-D14; main 76f054b, `verified` by reading the files and by running the two
tests). A release run leaves `resources/evidence/passed_tests.v1.json` in the tree, and no later session may read it. The
test side meets this (`tests/conftest.py` l.42-71 points the registry at a session copy without the file, and
`tests/packaging/support.py` `build_wheel` builds from a copy without it), and the product gains no switch
(interfaces.md §3.1). Two tests pin it. This plan gives them no ID of their own, and Fable decides whether they get one.

| Test (file, line) | Check (REQ marker) | Criterion | Result |
|---|---|---|---|
| `test_d045f_evidence_a_release_run_left_in_the_tree_never_reaches_the_test_session` (`tests/unit/results/test_evidence.py` l.202) | evidence reader (REQ-T-05) | with an applicable file planted in `resources/evidence`, `load_registry(resource_root())` reads it and `load_registry()` returns `evidence_build_id` None and an empty `passed_tests`; the file is restored afterwards | `1 passed`, `verified` by running it |
| `test_pk03_the_session_wheel_leaves_out_evidence_a_release_run_left_in_the_tree` (`tests/packaging/test_pk03_reproducible_wheel.py` l.67) | wheel (REQ-N-06) | with a file planted in `resources/evidence`, the wheel from `build_wheel` holds `embodic/_resources/evidence/equations.v1.json` and not `passed_tests.v1.json` | `1 passed`, `verified` by running it |

Where each packaging test runs. This container is Linux x86-64 with CPython 3.10 to 3.13 in `/usr/bin` and uv
0.8.17 (`verified` by listing, 2026-10-12). `unshare -rn` gives a process with no network (`verified`: a socket connect
returned 101, network unreachable). Anything that needs Windows is `not tested` here. The route for it is
`.github/workflows/ci.yml` with `workflow_dispatch` and the profile `release`, run by Fable. Nothing is published
without the user's approval.

| ID | Here (Linux container) | Needs Windows or the CI matrix | Owner |
|---|---|---|---|
| PK-01 | the Linux cells for 3.11, 3.12 and 3.13, with `tools/ci.py --profile commit` in one venv per version | the Windows cells. `ci.yml` lacks 3.13 and installs `.[dev]` only (interfaces.md §13 point 12) | U-M5b |
| PK-02 | yes: a clean venv per Python version installs from `requirements/py3xx.txt` with `--require-hashes`, then the wheel with `--no-deps` | the Windows resolve of the same files | U-M5b |
| PK-03 | yes: two wheel builds give the same member list and the same SHA-256 per `.py` member. The session wheel is built without the evidence file (D-045f), so the criterion has nothing to leave out; the release profile's own wheel carries the file and PK-10 checks it | none | U-M5b |
| PK-04 | no: it compares Windows JSON with Linux JSON (1e-9 rel.) | yes; `not tested` here | U-M5b sets it up, CI runs it |
| PK-05 | no: the bundle smoke test (start, compute the default example, export SVG) needs the Windows folder | yes; `not tested` here. The Linux smoke of the spec is `tests/bundle/test_bundle_smoke.py` (6 tests, labelled as a smoke of the spec only). D-046h records `6 passed` and a frozen `embodic-cli selftest` of 45 of 45 on U-M5c's Linux folder. This unit did not run them against a folder: in a tree without `build/bundle/embodic` the 6 tests skip (`verified`) | U-M5c |
| PK-06 | yes, on Linux: Agent 4 follows README.md from a clean venv and times each step to a first computed example | the timed walkthrough on a clean Windows machine (REQ-N-07 acceptance), Agent 4 or the user; `not tested` here | U-V5 |
| PK-07 | yes: `unshare -rn python tools/ci.py --profile commit` passes; a static test finds no `socket`, `http.client` or `urllib.request` import in `src` | none | U-M5b |
| PK-08 | yes: the runtime closure read with `importlib.metadata` (numpy, PySide6-Essentials, shiboken6) matches the licences of §5 of `package_layout.md`; `THIRD_PARTY_LICENSES.md` has one section per runtime dependency and bundled font and the LGPL-3.0 and GPL-3.0 texts; the wheel listing shows it under `dist-info/licenses/`. pip-audit is not a dependency (§5 needs Fable's approval to add one), so the audit part is `not tested` | none | U-M5b |
| PK-10, PK-11 | yes | none | U-M5b, U-M5d |

Performance (PF-01 to PF-05, Phase 1 rows and §5.4) run in the release profile on this container and write
`tests/performance/baseline.json` with the machine data of `package_layout.md` §5.2. A number measured here describes a
2-CPU container and is no target for the user's laptop.

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
| M1 | MT-01 to MT-03, MT-06 to MT-08, UT-GEO-01, UT-GEO-15, UT-GEO-22, UT-GEO-23, UT-DRC-01 to UT-DRC-08 on hand-built layouts, GR-17 to GR-19, PR-01 and PR-02 on random primitive sets, TR-02 |
| M2 | all UT-GEO, UT-WND, UT-PHY, UT-RES, UT-MOD, UT-IO, UT-GEN-01/02, GR-01 to GR-16, every OR test has one of four outcomes (revision 2026-10-13, U-D14, D-045b, which records a decision already taken and is no looser gate): it passes, or it is the documented strict xfail F-OR07 (OR-07), or it is a documented skip as not representable in Phase 2 (OR-03 and OR-10, G40), or it is a Phase 3 FEA case (OR-11 and OR-12). OR-09 is characterisation only and passes when the value is finite and positive, PR-01 to PR-12, BV, TR-01 to TR-04 |
| M3 | GR-20 to GR-23, UT-GEN-03/04/05, PR-13, PR-14, and every M2 gate still green |
| M4 | UI, AX, LG, UT-EXP, UT-SES tests; Agent 4 U-V4 independent export parsing |
| M5 | UT-CLI, PF (baseline recorded), PK-01 to PK-08, PK-06 walkthrough; from revision 2026-10-12 (U-D13) also UT-RES-08, UT-RES-09, TR-05, PK-10, PK-11, UT-SLF-01 to UT-SLF-03 and UI-35. PK-01, PK-04, PK-05 and the Windows half of PK-06 count only from a Windows run (§5.7); until then they are `not tested` |

## 8. Requirements-to-tests matrix

Generated from `requirements.md` by `python3 docs/phase2/architecture/checks/check_contract.py --write`. Module names are
the owner packages of `interfaces.md`.

<!-- matrix:start (generated by checks/check_contract.py --write; do not edit by hand) -->

| REQ | Disp. | Prio | M | Owner module | Tests |
|---|---|---|---|---|---|
| REQ-F-01 | carried | must | M2 | embodic.generators.spiral | UT-GEO-01, UT-GEO-03, UT-GEO-04, UT-GEO-05, PR-03, PR-10 |
| REQ-F-02 | carried | must | M2 | embodic.winding | UT-WND-01, UT-WND-02, UT-WND-03, UT-WND-04, UT-WND-05, UT-WND-06 |
| REQ-F-03 | carried | must | M2 | embodic.generators.spiral | UT-GEO-10, UT-GEO-11, UT-GEO-19, UT-GEO-24, UT-GEO-26, UT-PHY-07 |
| REQ-F-04 | carried | must | M2 | embodic.model | UT-GEO-12, GR-07 |
| REQ-F-05 | amended | must | M2 | embodic.generators.spiral | UT-GEO-13, UT-PHY-11, PR-01 |
| REQ-F-06 | carried | must | M2 | embodic.generators.spiral | UT-GEO-07, UT-GEO-08, UT-GEO-09, UT-GEO-17, UT-GEO-18, UT-GEO-25, OR-04 |
| REQ-F-07 | carried | must | M2 | embodic.physics | UT-PHY-01, UT-PHY-02, UT-PHY-04, UT-PHY-14 |
| REQ-F-08 | carried | must | M2 | embodic.generators.spiral | UT-PHY-09, UT-WND-07 |
| REQ-F-09 | carried | should | M2 | embodic.geometry | UT-GEO-14, UT-DRC-06, UT-EXP-02 |
| REQ-F-10 | carried | must | M1 | embodic.drc | UT-DRC-01, UT-DRC-02, UT-DRC-03, UT-DRC-04, UT-DRC-05, UT-DRC-08, PR-01, PR-02, PR-13, GR-18 |
| REQ-F-11 | carried | must | M2 | embodic.physics | UT-PHY-05, UT-PHY-06, UT-PHY-10, UT-PHY-12, UT-PHY-15, UT-PHY-16, UT-PHY-17, UT-PHY-18, UT-PHY-19, GR-02, GR-03, GR-04, GR-09, GR-11, GR-13, OR-01, OR-11, OR-12, UT-PHY-22, UI-07 |
| REQ-F-12 | carried | must | M2 | embodic.physics | UT-PHY-08, UT-PHY-20, GR-05 |
| REQ-F-13 | carried | must | M4 | embodic.ui.views | UI-02, UI-03, UI-04, UI-06 |
| REQ-F-14 | amended | must | M2 | embodic.model | PR-05, BV-01, BV-02, BV-03, BV-05, BV-06, UI-14 |
| REQ-F-15 | amended | must | M2 | embodic.io | UT-IO-01, UT-IO-02, UT-IO-03, UT-IO-04, UT-IO-07, PR-08 |
| REQ-F-16 | amended | must | M4 | embodic.io | UT-EXP-01, UT-EXP-02, UT-EXP-03, UT-EXP-04, UT-IO-06 |
| REQ-F-17 | carried | could | M4 | embodic.ui.views | UI-10 |
| REQ-F-18 | amended | must | M5 | embodic.cli | UT-CLI-01, UT-CLI-02, UT-CLI-03 |
| REQ-F-19 | amended | must | M2 | embodic.generators | UT-GEO-20, UT-GEN-01, UT-GEN-02, MT-01 |
| REQ-F-20 | carried | could | M2 | embodic.physics | UI-07, UT-RES-02, UT-PHY-23 |
| REQ-F-21 | amended | must | M4 | embodic.ui.viewmodels | UI-22, UI-23, PR-12 |
| REQ-F-22 | amended | should | M4 | embodic.ui.viewmodels | UI-11, UT-SES-02 |
| REQ-F-23 | carried | must | M4 | embodic.ui.viewmodels | UI-15 |
| REQ-F-24 | amended | should | M2 | embodic.geometry | UT-GEO-21 |
| REQ-F-25 | amended | should | M4 | resources/examples | UI-16, UT-IO-08, UT-SLF-01, UT-SLF-02, UT-SLF-03, UI-35 |
| REQ-F-26 | carried | should | M4 | embodic.ui.views | UI-17 |
| REQ-F-27 | carried | should | M4 | embodic.ui.viewmodels | UI-18 |
| REQ-F-28 | carried | should | M4 | embodic.ui.views | UI-19 |
| REQ-F-29 | amended | should | M4 | embodic.io | UT-EXP-05 |
| REQ-F-30 | carried | could | M4 | embodic.ui.views | UI-20 |
| REQ-F-31 | carried | should | M4 | embodic.ui.app | UI-21 |
| REQ-F-32 | carried | must | M4 | embodic.ui.views | UI-28, UT-MOD-03 |
| REQ-F-33 | amended | must | M4 | embodic.ui.views | UI-29, UT-EXP-05, UT-CLI-01 |
| REQ-F-34 | new | must | M3 | embodic.generators.serpentine | GR-20, GR-23, UT-GEN-03, UT-GEN-05, PR-13, PR-14 |
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
| REQ-N-06 | amended | must | M5 | pyproject.toml | PK-03, PK-05, PK-10, PK-11 |
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
| REQ-N-21 | amended | must | M1 | embodic.geometry | UT-GEO-01, UT-GEO-22, UT-GEO-23, UT-UNI-01, UT-EXP-02 |
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
| REQ-T-05 | carried | must | M2 | embodic.results | TR-03, UT-RES-02, UT-RES-08, UT-RES-09, TR-05 |
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
