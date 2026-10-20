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

Revision 2026-10-13 (U-D15, claude-sonnet-5-5, D-046 and the U-M5h and U-M5f reports; main 5e74acc read for every
item). §5.2 restates PR-05 and adds its counterexample, the empty `/analysis/harmonics`. §5.3 restates UI-05 and adds
its measurement note. §5.7 re-reads the two D-045f tests on main 5e74acc and names the row each extends. PR-05 and
UI-05 are Phase 1 IDs, so no ID is new.

Revision 2026-10-17 (U-D17, claude-sonnet-5-5, D-051; main 0547f20 read for every item, and
`docs/phase3/architecture/v3_contract_rulings.md` supplies the specifications of U-D16). §3 says "computed clearance"
in the D-006 band rule and points at GR-07 (D-051a, D-051e). §5.1 restates UT-PHY-07 and GR-07 with the cases of
U-D16, renames the code in UT-WND-09 (D-051b) and renames `measured_min_mm` in PR-02 (D-051a). §5.7 restates the PK-04
rule for hashes and arrays (D-051f), adds the TR-01 row with the release-profile flag and the manual records
(D-051e), and §7 states that the release gate enforces TR-01 from 0.0.2. No ID is new, because UT-PHY-07, GR-07,
PK-04 and TR-01 are Phase 1 IDs.

Revision 2026-10-17 (U-D18, claude-sonnet-5-5, D-051e, D-052c; main 7d34543 read for every item). §5.8 is new. It says
how each must row that the release flag `--fail-untested-through M5` leaves without a passing test gets one. REQ-T-11,
REQ-L-03 and REQ-L-05 get the product tests LG-04, LG-05 and LG-06. REQ-N-07 gets a manual record of PK-06. REQ-N-10
gets one of two options, and Fable chooses between them. REQ-T-10 has one marked test and no wording scan, so §5.8
restates LG-03 too. REQ-N-05 needs nothing. §5.4 lists LG-03 to LG-06 and §7 names the manual record in the M5 exit.
`checks/lg_wording_probe.py` is new and reproduces every hit count that §5.8 quotes. No ID is new, because LG-03 to
LG-06 and PK-06 are Phase 1 IDs. This unit ran no test suite, so any statement that a test passes is `not tested`.

Revision 2026-10-17 (U-D19, claude-sonnet-5-5, D-053a, D-053b, D-054a, D-054b, D-054d, D-054e; main b026fa3 read for
every item). PR-14 gets the chord-count method of D-054a and drops the tolerances of D-036c. UT-GEO-11 records that D-054b
settled the two-rotation question. GR-07 case 3 asserts the refusal of D-053a. Four IDs are new: UT-GEN-06 (every
topology refuses `vias_per_transition` other than 1, D-054d), BV-21 and UT-DRC-09 (the screw pitch radius that overflows
the DRC grid index, D-054e) and TR-06 (the coverage checker of Phase 5, D-053b). §5.8.7 and §5.8.9 record that D-053b
chose option B. §7 changes by one sentence about REQ-N-10, and no new row is named in a milestone exit. This unit ran no test suite, so any
statement that a test passes is `not tested`. The matrix of §8 is regenerated by `checks/check_contract.py --write`.

Revision 2026-10-17 (U-D20, claude-opus-5-5, D-055b, D-055c, D-055d, DEF-UM7d-01; main e68d5ff read for every item).
§5.1 corrects the M2 total of UT-GEO-13 from 60 to 84, restates UT-IO-04 and UT-IO-06 for the project file v2 of
interfaces.md §9.1, and adds the DXF ARC joint rule of D-055c to UT-EXP-02. §5.4 withdraws the word-list clause of
LG-01 and puts the word review in a manual record (REQ-L-01). §5.7 restates TR-03 as the release gate of REQ-T-05
(D-055b), amends TR-05 to match it, and states the PK-07 guard of D-055d. No ID is new, because UT-IO-04, UT-IO-06 and
TR-03 are Phase 1 IDs. This unit ran no test suite, so any statement that a test passes is `not tested`. The matrix of
§8 is regenerated, because REQ-T-05 and REQ-L-01 become `amended`.

Revision 2026-10-17 (U-D21, claude-sonnet-5-5, D-056; main b977621 read for every item). §5.3 replaces UI-32 with the text
of `docs/phase3/design/fix_wave_f1.md` section (d). §5.1 adds the tests of `docs/phase3/engineering/fix_wave_f1.md`
(U-E17). T-A1, T-A2, T-A4 and T-C3 go to GR-13, T-C1 and T-C2 go to UT-PHY-16, and the UT-PHY-21 cases of §B.5 go to
UT-PHY-21. T-A3 has no row that fits, because no earlier row tests the closed-form board area, so UT-PHY-24 is the one
new ID. §5.4 amends MT-04 for the word `dimensionless` (D-056f). §4 points at the restated UT-PHY-21. The numbers in
these rows are copied from the two fix wave documents, where the units that wrote them ran the checks. This unit
re-ran none of them and ran no test suite, so any statement that a test passes is `not tested`. The matrix of §8 is
regenerated by `checks/check_contract.py --write`, because REQ-T-14 and REQ-N-02 become `amended`.

Revision 2026-10-17 (U-D22, claude-sonnet-5-5, D-057e; main eea9757 read for every item). §5.3.2 is new. It gives plan IDs
to the rows N02-1 to N02-10 of `docs/phase3/design/fix_wave_f1.md` section (a), one ID per row (UI-36 to UI-45), and to
the stepping rows S-1 to S-12 of `docs/phase3/design/fix_wave_f2.md` section (b), one ID per row (UI-46 to UI-57). U-D21
found no ID for either set. The ten N02 rows have tests on main in `tests/ui/qt_shell/test_n02_typing_preview.py`. The
twelve stepping rows have none. §5.3.1 adds a row beside UI-09 for the form-fit rows of REQ-N-15, which now cover the five
packaged examples and not D08 only. The matrix of §8 is regenerated by `checks/check_contract.py --write`, because
REQ-N-15 becomes `amended` and the Tests columns of REQ-N-02 and REQ-N-12 grow. The M4 exit of §7 already names every
UI test. This unit ran no test suite, so any statement that a test passes is `not tested`.

Revision 2026-10-19 (U-D23, claude-sonnet-5-5, D-054d, D-068; main 06bbe53 read for every item). §5.1 amends UT-PHY-11. The
Phase 1 barrel criterion stays. The via-count clause that REQ-F-05 attached to it now tests what D-054d decides. The value
1 builds and is analysed with one barrel per via. Every other value is refused on every topology with the NOT_IMPLEMENTED
code of that topology until Phase 5. No ID is new, because UT-PHY-11 is a Phase 1 ID. The UT-GEN-06 row still gives the
spiral code for all three topologies, which src does not (`src/embodic/generators/serpentine/generate.py` l.120,
`src/embodic/generators/wave/generate.py` l.82), and this unit leaves that row for Fable. This unit ran no test suite, so
any statement that a test passes is `not tested`. The matrix of §8 does not change.

Revision 2026-10-19 (U-D24, claude-sonnet-5-5, D-068; main 4fa3198, `src/embodic/generators` and `tests/unit/generators`
read for every item). §5.1 corrects the UT-GEN-06 row. It gave the spiral code for all three topologies and said that no
unit test pins the refusal. Each topology has its own NOT_IMPLEMENTED code, and
`tests/unit/generators/test_every_topology_refuses.py` pins the code and the pointer for the values 2 and 3. The
UT-PHY-11 row loses its note that the UT-GEN-06 row is out of date. §5.7 corrects the PK-05 row: the 6 bundle tests skip
under the commit and nightly profiles and fail under the release profile (U-M8q). No ID is new. This unit ran no test
suite, so any statement that a test passes is `not tested`. The matrix of §8 does not change.

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
computed clearance v (wording of D-051a, 2026-10-17) with rule - 0.004 mm <= v < rule, the half-open band [rule - 0.004 mm, rule). Inside the band the
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

Phase 1 GR-01 to GR-16 stay as written (equation-level cases for the spiral path's reused equations), except GR-07,
which §5.1 restates with the cases of U-D16 (revision 2026-10-17, U-D17, D-051e).

## 4. Closed-form, oracle and EC-05 tests

Phase 1 UT-PHY-01 to UT-PHY-21 and OR-01 to OR-12 stay. Two changes apply.

- Oracle tolerance add-on. OR-01 (O1, D08) and OR-07 (O2, D09) compare in the asymmetric band [-tol, +tol + e_edge],
  with e_edge taken from the computed `edge_leakage_fraction` of the oracle design, not from a constant (Phase 1 used
  4.2 % and 5.8 %; UT-PHY-21 pins the EC-05 kernel on those cases within 0.1 pp, with the values restated in §5.1,
  revision 2026-10-17, U-D21).
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
| UT-GEO-11 | Amended revision 2026-10-08 (U-D5): pair rotation pi/Q | Phase 1 criterion (group-2 centre vias in the group-1 inter-coil gaps, pi/Q ± 1e-9 rad) is not met on main e1536b8. One rotation shared by every pair (option M3) builds the board of first coil angle θ₀ + pi/Q (`test_spiral_pairs.py`). Pairs at two rotations: main returns Unbuildable `UNBUILDABLE_SPIRAL_OPTION_NOT_IMPLEMENTED` at `/winding/layers/pairs`; spec G6 (U-E6, `inferred`) forbids the combination with `UNBUILDABLE_PAIRS_ROTATED_APART`, which U-M2d-5 adds. Whether the Phase 1 build criterion for two rotations is withdrawn is open for Fable. Revision 2026-10-17 (U-D19, D-054b; `src/embodic/generators/spiral/generate.py` l.142-143, `verified` by reading): decided. Pairs at two rotations return Unbuildable `UNBUILDABLE_PAIRS_ROTATED_APART` at `/winding/layers/pairs`, the code exists on main, and the Phase 1 build criterion for two rotations is withdrawn. The statements above that U-M2d-5 adds the code and that the question is open are out of date. The tests are `test_m3_a_rotation_every_pair_shares_turns_the_whole_winding` and `test_ut_geo_11_pairs_rotated_against_each_other_are_refused` (`tests/unit/generators/test_spiral_pairs.py` l.168 and l.192). REQ-F-03 (b) carries the criterion |
| UT-GEO-13 | Amended revision 2026-10-08 (U-D5, spec G6 via plan, U-E6): via plan count and spans | per coil k centre, k - 1 transfer and 2 terminal vias, 2k + 1 in all; N_via = Q·v·(2k + 1), all through vias (D-015). The default totals are 36 for M1 (Q = 12, three parallel pairs in one group, k = 1) and 84 for M2 (Q = 12, three series groups of one pair, k = 3). Revision 2026-10-17 (U-D20): the row said 60 for M2 with k = 2, but M2 has three series groups, so k = 3 (spec G6, `spiral_generator_spec.md` l.513: "three series groups 84"). `generate_spiral` on `_three_pairs` of `tests/unit/generators/test_spiral_pairs.py` gives 12 centre and 24 terminal vias for M1, and 36 centre, 24 transfer and 24 terminal vias for M2 (`verified (run)`, main e68d5ff, 2026-10-17). `test_ut_geo_13_parallel_pairs_need_36_winding_vias` (`test_spiral_pairs.py` l.68) checks M1. `test_ut_geo_13_series_coil_has_2k_plus_1_winding_vias` (`test_spiral_series_fan.py` l.78) checks the counts by role for k = 2 and k = 3 on CF-11 and D08, and its CF-11 k = 3 case is the 84 of M2. `checks/series_fan_check.py` counts 5 per coil for k = 2 and 7 for k = 3 |
| UT-GEO-26 | New revision 2026-10-08 (U-D5, D-020, D-033b, D-033g): series layer pairs (G5 k centre vias, G6 via fan) | CF-11 with k = 3 series groups keeps 10 turns and centre-via radii 30.7, 29.9 and 29.1 mm; group g's X joins ring via g to its centre via and its Y joins that centre via to ring via g + 1. `generate_spiral` never returns a series board with a DRC violation: it returns the board with 0 violations or Unbuildable `UNBUILDABLE_SERIES_VIA_FAN_DRC` at `/winding/layers/series_groups`. On main e1536b8 CF-11 is refused (DEF-M2d4-02). From U-M2d-5, CF-11 and D08 with k = 2 and k = 3 build with 0 violations and a smallest clearance of 0.2 mm (CF-11) and 0.8 mm (D08), the values of `series_fan_check.py` |
| UT-GEO-24 | New 2026-10-08 (U-D4, D-031c): first coil angle any finite | a spiral design with `first_coil_angle_rad` = 1.0, 1.0 + 2 pi, and 1.0 - 2 pi builds in every case, and coil 0's axis and every primitive end point agree within 1e-9 rad and 1e-9 mm; the model accepts the value as typed and the project file stores it unchanged |
| UT-GEO-25 | New 2026-10-08 (U-D4, D-031b): closing of the last turn | `SpiralDetail.turn_limit.closing` equals the closing the generator built: `half` for the D08 example (3 turns, D-030) and `full` for a design whose G5 eye fits; the value is not a `FIELDS` pointer and is absent from the project file |
| UT-UNI-01 | Amended 2026-10-04: unit conversions and rounding | deg and rad, mm and m, rpm and rad/s, mil² and mm² round trips within 2 ulp of the input (`math.ulp`), not exact (requirements.md revision note); `js_round` gives 3, -2, 1, 0, -1, 0 for 2.5, -2.5, 0.5, -0.5, -1.5, 0.49999999999999994 (JS `Math.round`); `quantise(-0.000025, 1e5) == -0.00002`; neither returns -0.0 |
| UT-DRC-04 | Amended 2026-10-05 (U-D3, D-022), 2026-10-08 (U-D4, D-022c), 2026-10-08 (U-D7, D-035b, cases 5a to 5d) and 2026-10-20 (U-D24, D-078, cases 2d to 2f and 5a to 5l): connectivity exemptions, one exempt case and one near miss per rule of interfaces.md §7, each below the rule so only the exemption decides | 1a adjacent main primitives exempt; 1b same-net main primitives two indices apart reported; 1c a corner fillet or taper exempt from both mains it belongs to and from the other fillets and tapers of those mains; 1d the DEF-M1V-01 hairpin: a fillet against the main two steps back reported; 2a a path end group exempt from the via or pad its end lies on; 2b a via the path does not end on reported; 2c an interconnect path (net `U`) ending on a `PHASE_A` via of any role (terminal, centre, transfer), and on a pad of another net, exempt; 2d vias of any net and role tapping an interconnect ring (net `N`) mid-path and at its end, each centre within `pad_mm / 2` of the centreline, exempt from each primitive whose centreline passes within `pad_mm / 2` of the via centre, and the same ring with a phase net (not an interconnect) reported against the same vias (revision U-D24: the geometry and the assertion of `test_ut_drc_04_interconnect_tapped_mid_path_by_vias_of_any_net_and_role_is_a_joint` stay, because no other primitive of the ring comes within the rule of a via); 2e a `PHASE_A` via 0.2 mm before a sharp corner of an interconnect path (net `N`), inside `pad_mm / 2` of both primitives of the corner, exempt from both; 2f an interconnect U-turn (net `N`) tapped on the middle of its first main primitive by a `PHASE_A` via, with the return main primitive 0.01 mm inside the via rule: that pair reported, and with it 0.01 mm outside, no violation; 3a same-net end groups meeting at one via, one pad or within `COINCIDENCE_MM` exempt; 3b different-net end groups at a coincident point with no via or pad reported; 3c an interconnect end group and a phase path end group on one via of any role, or on one pad, exempt; 4a a same-net via inside a pad exempt; 4b an other-net via inside a pad reported; 5a a path end point on the middle of a same-net line exempt from that line; 5b the same on the middle of a same-net arc; 5c the 5a T with the two paths on different nets reported; 5d the 5a T with the end point 0.01 mm short of the centreline reported; 5e a branch that starts on the trunk and whose far main primitive stops 0.15 mm short of it: only the end group on the trunk exempt, the far main primitive reported; 5f an end point 0.05 mm before a sharp corner of the trunk, with no fillet: the trunk's next main primitive reported; 5g a branch that ends on the trunk's end point, at the trunk's start and at its end: the trunk's middle main primitive, outside the trunk's end group, reported at clearance 0; 5h the 5g geometry on different nets: both trunk primitives reported; 5i a coil path (a turn, then a stub) ends on a same-net terminal via, and a leg starts on that via and runs back past the turn 0.01 mm inside the trace rule: exactly the turn against the leg reported; 5j the 5i joint with the leg 0.01 mm outside the rule: no violation, because rules 2 and 3 exempt the leg, the stub's end group and the via from one another; 5k a branch that lands on a main primitive 0.1 mm before its corner fillet, so that its copper overlaps the fillet: exempt; 5l a branch on the middle of the first line of a trunk that turns back, with the trunk's return main primitive 0.01 mm inside the rule of the branch: that pair reported, and with it 0.01 mm outside, no violation. Revision 2026-10-13 (U-D14, Fable's ruling): U-M5f adds the end-point cases. Revision 2026-10-20 (U-D24, D-078, DEF-UV16-01; interfaces.md §7 rule 5 and the rule 2 tap as U-D24 revises them): rule 5 exempts an end group only from the landing group of the primitive its end point lies on, and the tap is per primitive. The case letters follow `tests/unit/drc/test_run_drc.py` on main 14c8b7a. There 5e and 5f are U-M3-fix's cases, and U-M5f's end-point cases are 5g and 5h, not the 5e and 5f that the revision of 2026-10-13 named. Cases 5f and 5g invert: `test_ut_drc_04_junction_end_group_is_exempt_from_the_whole_trunk_path` and `test_ut_drc_04_path_end_on_an_end_point_of_a_same_net_path_is_exempt_from_every_primitive_of_it` assert the exemptions that U-D24 withdraws. With `_junctions` and `_taps` replaced by the U-D24 reading, exactly those two tests fail (three items with the parametrisation) and the other 27 UT-DRC-04 items pass (`verified` by running `pytest tests/unit/drc/test_run_drc.py -k ut_drc_04` on main 14c8b7a with a scratch plugin). The outcomes stated for 2e, 2f and 5i to 5l are `verified` in the same way under that reading. 2f, 5i and 5l give no violation on main 14c8b7a, so each fails on the old reading. 5k fails under a reading that exempts only the primitive the end point lies on. The geometry of 2e, 2f and 5i to 5l is in `docs/phase3/architecture/u_d24_rule5.md` section 4. This plan does not claim that the cases pass on main. Rule 2b (amended 2026-10-09, U-D8, D-036a, D-037a; D-036a's "rule 2b" is not case 2b above), in `tests/unit/drc/test_run_drc.py`: `test_ut_drc_04_same_net_via_on_a_path_centreline_is_exempt_from_that_primitive` (a same-net via on a line and on an arc exempt); `test_ut_drc_04_via_of_another_net_on_a_path_centreline_is_reported` (the same geometry on another net reported); `test_ut_drc_04_same_net_via_tap_band_is_half_the_via_pad` (0.29 mm off the centreline exempt, 0.31 mm, 0.01 mm outside the `pad_mm / 2` band, reported); `test_ut_drc_04_same_net_via_tap_leaves_a_far_primitive_of_the_same_path_checked` (the far primitive of the tapped path, 0.1 mm from the via against a 0.2 mm rule, reported) |
| UT-GEN-01 | Amended 2026-10-05 (U-D3) and 2026-10-08 (U-D4, D-031f): generator contract for spiral, serpentine, wave and a stub | returns a `BoardStack` or Unbuildable, never raises on fuzzed input; spiral and wave stacks hold exactly one board; same design gives the same `stack_hash`; on every board, every circuit path and via ID exists and every winding path belongs to exactly one Member or to `interconnect_path_ids`; every board sets `detail` and a non-empty `derived`; from U-M2e-4, every id of `interconnect_path_ids` has exactly one `interconnect_roles` entry. Revision 2026-10-09 (U-D10, DEF-M3b-03, U-M3-fix3): the wave and the serpentine port each have the fuzz test `test_fuzzed_inputs_give_a_stack_or_unbuildable_never_an_exception` (`tests/unit/generators/wave/test_wave_generate.py` l.321 and `tests/unit/generators/serpentine/test_serpentine_inputs.py` l.88), each with the explicit denormal `@example`. The guard tests refuse each unusable size, count and degenerate end turn with the code of interfaces.md §6 before any geometry is built (`test_unusable_size_is_refused_before_any_geometry` in both `*_inputs.py` files, l.85 and l.148), accept a width exactly at the DRC minimum, and turn `biarc` of coincident points into `DegenerateBiarcError` (`test_wave_inputs.py` l.121). U-M3-fix3 showed that the new serpentine tests fail without the guard (31 of 33, its report) |
| UT-GEN-02 | Dispatch | `build_layout` routes by `design.topology`; calling `generate_wave` with a spiral design raises TypeError |
| UT-GEN-03 | Amended 2026-10-05 (U-D3); single-mode rule ratified 2026-10-08 (U-D4, D-031e; main checks only `one_board_per_phase`, DEF-U-D4-02): serpentine validation | layers per phase 1 or even; copper count = phases x layers per phase for `stack_mode` `single` and = layers per phase for `one_board_per_phase` (one board's stack-up, Xcoil `stackupFor(p, perBoard)` l.686-688), else INVALID with the pointer; `board_gap_mm` below 0 is INVALID and above 10 mm is UNSUPPORTED_RANGE (Xcoil l.127). As implemented (revision 2026-10-08, U-D7; `tests/unit/generators/serpentine/test_serpentine_generator.py` l.88-139): an odd layers per phase gives `INVALID_LAYERS_PER_PHASE`; a copper count that does not fit the stack mode gives `INVALID_SERPENTINE_COPPER_COUNT` in both modes, and the generator also refuses it with `UNBUILDABLE_SERPENTINE_COPPER_COUNT`; a gap of -0.1 mm gives `INVALID_NEGATIVE`, 0 and 10 mm give nothing, and 10.5 mm gives `RANGE_ABOVE_SUPPORTED` |
| UT-GEN-04 | Wave validation; stated as implemented 2026-10-08 (U-D7; `tests/unit/generators/wave/test_wave_generate.py` l.60-89) | each style builds for 1, 2 and 3 phases with the phases in order; 2, 4 and 6 copper layers build with T tracks on even layers and B tracks on odd ones; 1, 3 and 5 copper layers give `UNBUILDABLE_WAVE_LAYER_COUNT` on `/stackup/layers`. After U-M3-fix (D-035e) `validate_design` also reports the count with an INVALID code |
| UT-GEN-05 | New 2026-10-05 (U-D3): one board per phase | `stack_mode` `one_board_per_phase` with 3 phases gives 3 boards in phase order; board k holds only phase k copper and one PhaseCircuit, and its `copper_z_mm` equals the single-board stack-up z plus k x (board thickness + `board_gap_mm`) within 1e-12 mm (Xcoil l.695); `stack_thickness_mm` = n x board thickness + (n - 1) x gap (l.689); no board has interconnect paths or pads, and with the interconnect requested for three phases in star or delta the outcome carries a WARNING issue that the phase connection is made externally (Xcoil warning `INTERCONNECT_EXTERNAL`, l.2525-2535); `stack_mode` `single` gives one board whose `layout_hash` equals the one built with `board_gap_mm` changed (the gap has no effect, l.689 and l.695); a via of board A placed over board B copper produces no DRC pair |
| UT-GEN-06 | Amended (revision 2026-10-19, U-D24; D-068); new 2026-10-17 (U-D19, D-054d): every topology refuses `vias_per_transition` other than 1, each with the code of its own topology | For the spiral, serpentine and wave examples with `/vias/vias_per_transition` set to 2, and again to 3, the build returns Unbuildable with one issue. Its pointer is `/vias/vias_per_transition`, and its code belongs to the topology: `UNBUILDABLE_SPIRAL_OPTION_NOT_IMPLEMENTED` (`src/embodic/generators/spiral/generate.py` l.94 adds the pointer and l.145 emits the code), `UNBUILDABLE_SERPENTINE_OPTION_NOT_IMPLEMENTED` (`serpentine/generate.py` l.119-120) and `UNBUILDABLE_WAVE_OPTION_NOT_IMPLEMENTED` (`wave/generate.py` l.81-82), `verified` by reading on main 4fa3198. With 1 each example builds as before. Each code has its own message that names its topology (`src/embodic/errors/catalogue/generators.py` l.6, `serpentine.py` l.22 and `wave.py` l.27, `verified` by reading). The serpentine and wave generators therefore do not reuse the spiral code, and the first version of this row was wrong about that. Two tests in `tests/unit/generators/test_every_topology_refuses.py` pin the behaviour. `test_parallel_vias_per_transition_are_refused_by_every_topology` (l.50, values 2 and 3 on the three examples) asserts the pair of code and pointer for each topology. Its docstring names DEF-M7a-02, where the serpentine and wave built one via and gave an unchanged R_ph for 2 without a message, so the test fails on that defect. `test_one_via_per_transition_still_builds_every_example` (l.65) asserts that the value 1 returns a `BoardStack`, so a refusal that also stops the packaged value fails it. Both tests are `not tested` here, because this unit ran no suite. The analysis still passes the constant 1 to `via_resistance_ohm` (`src/embodic/physics/analyse.py` l.193, `verified` by reading). Because the build refuses a count above 1, a board that `build_layout` returns never carries one (`inferred`). Phase 5 replaces the refusal with parallel vias that the generator builds and the analysis counts |
| UT-PHY-11 | Amended (revision 2026-10-19, U-D23; D-068): barrel resistance, and the vias per transition that D-054d allows | The Phase 1 criterion stays: drill 0.3 mm, plating 25 µm, A = 0.021598 mm², l 0.2 mm at 20 °C gives 0.160 mΩ (C9), and two barrels in parallel halve it (`test_cf04_and_ut_phy_11_via_barrel_resistance`, `tests/unit/physics/test_kernels.py` l.121). The via-count clause of REQ-F-05 has two halves. (1) `vias_per_transition` = 1 builds and is analysed: the spiral, serpentine and wave examples return a `BoardStack`, and the analysis gives every via one barrel (`_via_resistance` passes count 1, `src/embodic/physics/analyse.py` l.193, `verified` by reading). (2) Every other value is refused on every topology until Phase 5 (D-054d). The build returns Unbuildable at `/vias/vias_per_transition` with the NOT_IMPLEMENTED code of the topology, so the build makes no board for a count above 1. The codes are `UNBUILDABLE_SPIRAL_OPTION_NOT_IMPLEMENTED` (`src/embodic/generators/spiral/generate.py` l.94 and l.145), `UNBUILDABLE_SERPENTINE_OPTION_NOT_IMPLEMENTED` (`serpentine/generate.py` l.119-120) and `UNBUILDABLE_WAVE_OPTION_NOT_IMPLEMENTED` (`wave/generate.py` l.81-82), `verified` by reading on main 06bbe53. `test_parallel_vias_per_transition_are_refused_by_every_topology` (values 2 and 3, l.50) and `test_one_via_per_transition_still_builds_every_example` (l.65), both in `tests/unit/generators/test_every_topology_refuses.py`, assert the build side of the two halves. They are `not tested` here, because this unit ran no suite. Nothing in `tests/unit` reads the via resistance of a built board from the analysis (grep for `via_resistance` finds only `test_kernels.py`), so the one-barrel part of half (1) is `not tested` above the kernel. The old sentence "Via resistance uses the count per transition" is withdrawn, because the V3-01 ruling on REQ-F-05 found it unassertable while every topology refuses a count above 1 (`tests/independent/m7/records/V3-01.md` l.161). Phase 5 replaces the refusal with parallel vias that the generator builds and the analysis counts, and a count-per-transition criterion returns then. The UT-GEN-06 row above first named `UNBUILDABLE_SPIRAL_OPTION_NOT_IMPLEMENTED` for all three topologies and said no unit test pins the refusal. Both statements were out of date on main 06bbe53, and the revision of 2026-10-19 (U-D24) corrected that row |
| BV-21 | New 2026-10-17 (U-D19, D-054e): a screw pitch radius outside the physical range | `validate_design` returns an ERROR at `/outline/screws/0/pitch_radius_mm` for 1e30 mm on the spiral, serpentine and wave examples, and `compute` on the same draft returns no `INTERNAL_` issue. The code is `RANGE_ABOVE_SUPPORTED` (`inferred`: the existing range mechanism, `src/embodic/model/validate.py` l.135). The field has only the sign limit `POS` today (`src/embodic/model/fields.py` l.203, `verified` by reading), so the upper limit is new, and D-054e does not state its value (`unresolved`, Agent 2 or Fable sets it). 1e9 mm passes validation and computes without an `INTERNAL_` issue (U-M7a report, not re-run). The strict xfail on the serpentine case of `test_f14_1_seeded_drafts_return_an_outcome_without_internal_errors_or_unnamed_non_finite_numbers` (`tests/unit/property/test_seeded_drafts_all_topologies.py` l.93-96) is removed in the same change; it is strict, so it fails when the defect is fixed. Catches the `INTERNAL_DRC_FAILED` of DEF-M7a-01 |
| UT-DRC-09 | New 2026-10-17 (U-D19, D-054e): the broad phase refuses a cell index it cannot represent | `candidate_pairs` (`src/embodic/drc/engine.py` l.108) on two items whose midpoints are 1e30 mm apart refuses, and does not return a pair list built from a wrapped index. The cause is `np.floor(mid / cell_mm).astype(np.int64)` at l.120 (`inferred`, U-M7a report DEF-M7a-01; not reproduced here). The form of the refusal, an exception or an issue code, is not fixed by D-054e and is `unresolved`; the test pins it when Agent 3 chooses. Validation (BV-21) stops the input first, so this row guards the DRC function against a caller that skips validation |
| UT-WND-07 | Amended 2026-10-08 (U-D4, D-031d): delta with k_w3 not zero | `plan_issues(plan, design)` returns `RANGE_DELTA_TRIPLEN` (WARNING, pointer `/connection/topology`) for 12/14 delta and nothing for 12/16 delta; `plan_spiral_winding` returns a plan in both cases |
| UT-WND-09 | Amended 2026-10-08 (U-D4, D-031d): manual assignment override | an asymmetric manual assignment returns a plan, and `plan_issues` returns `RANGE_MANUAL_ASSIGNMENT_ASYMMETRIC` with the magnitude spread as `value`; a symmetric one returns no issue. Renamed 2026-10-17 (U-D17, D-051b): the code was `RANGE_MANUAL_ASSIGNMENT_UNBALANCED` (`tests/unit/winding/test_plan.py` l.171 on main 0547f20), and the meaning is unchanged (interfaces.md §4) |
| UT-PHY-22 | New 2026-10-08 (U-D4, D-031f): interconnect copper and loss sum (EQ-23, EQ-26), U-M2e-4 | on a hand-built star layout with known lead, link and ring resistances: `resistance_line_ohm` and `loss_interconnect_w` equal the EQ-23 closed form within 1e-12 relative; delta: P_ic = I_line^2 sum stub + I_ph^2 sum link and the circulating loop includes the links; open: P_ic = 0; `loss_total_w` is the sum of its five terms, `efficiency` = P_out / (P_out + P_loss), `motor_constant_n_m_per_sqrt_w` = T / sqrt(P_Cu) and 0 at zero current; a layout with interconnect paths and no roles gives `loss_interconnect_w` status `unresolved`; golden cases against Xcoil `pInterconnect`, `rLineLine`, `lossTotal`, `efficiency` and `motorConstant` on star and delta layouts |
| UT-PHY-23 | New 2026-10-08 (U-D4, D-031f): EQ-20 for any phase count, U-M2e-4 | with `dc_link_v` set, one-, two- and three-phase designs return a `torque_speed` estimate; the open connection uses the full-bridge voltage (SVPWM and SPWM V_dc / sqrt 2, six-step 4 V_dc / (pi sqrt 2), Xcoil l.2681) and the phase resistance; star and delta keep today's three-phase values unchanged; golden against Xcoil `driveAnalysis` for a two-phase design |
| UT-PHY-16 | Amended 2026-10-17 (U-D21, D-056i; U-E17 §C.4, tests T-C1 and T-C2): EQ-17 on a stack of boards | The Phase 1 criterion stays (D08, 4 W at 5.11 K/W gives 20.44 K). `analyse()` cools a stack through its two outer faces, so `temperature_rise_k.value == loss_total_w.value / (h * 2 * board_area_mm2(boards[0]) * 1e-6)` with h = `design.operating.convection_h_w_m2k`, rel 1e-12 (`docs/phase3/engineering/fix_wave_f1.md` §C.1 and §C.4; the ruling is `inferred`, because it assumes an unventilated board gap). T-C1: `per_phase(example_design())` from `tests/unit/generators/serpentine/support.py`, built with `build_layout`. The test asserts first that there are 3 boards, that `board_gap_mm == 0.1` and that `board_area_mm2` is equal on every board. It catches the cooling area of n boards (today the ratio is exactly 1/3). T-C2: the same relation on `example_design()`, one board. It catches a fix that divides by n or special-cases one board. The document leaves the folder open (`tests/golden/m2_physics/` or `tests/unit/physics/`) |
| UT-PHY-21 | Restated 2026-10-17 (U-D21, D-056; U-E17 §B.3 to §B.5): the EC-05 kernel on the Phase 1 cases | A kernel test on the idealised segment set of `docs/phase1/engineering/checks/edge_zone_d09.js`. It does not pin `edge_leakage_fraction` of a generated layout (`unresolved`; §B.2 and Follow-up 3 of `docs/phase3/engineering/fix_wave_f1.md`). Per case: build the rotor of §B.4 and `table = field_table(rotor, G, G, (1,))`; build one `Line` from (r_lo, 0) to (r_hi, 0); compute `field = integrate_path([line], table, p, 0.5, c_e * G)` and `e = edge_leakage_fraction([field], D_e)`, with D_e and c_e from `load_registry()`. The cases are (G = z, radial line, expected e_edge) default_12_16 (1.31 mm, 18 to 38 mm) 5.328140 %, O1_D08 (1.4 mm, 12.5 to 44 mm) 4.208834 % and O2_D09_N8 (1.5 mm, 25.2 to 47.6 mm) 5.788521 %. Assert \|e - expected\| <= 0.001 (0.1 pp). Repeat with `max_segment_mm=0.1` and assert <= 0.00005 (0.005 pp). The 0.1 pp bound holds the quadrature error of 0.5 mm chords (0.025 to 0.038 pp on these cases). The 0.005 pp bound catches a weight without r and the field taken at z = 0 in more cases than 0.1 pp does (§B.5 table). Cap cases run the same steps and then `evaluate_validity(check, "EQ-05", e)`: a 10 mm magnet (30.5 to 40.5 mm) gives e = 12.373846 % and `ValidityEffect.CAP`; a 12 mm magnet (29.5 to 41.5 mm) gives 10.445833 % and `ValidityEffect.CAP`; a 15 mm magnet (28 to 43 mm) gives 8.420015 % and `ValidityEffect.LIMITATION` with `one_sided_addon == e` |
| UT-PHY-24 | New 2026-10-17 (U-D21, D-056j; U-E17 §A.4, test T-A3): board area from the outline loops (EQ-16, EQ-17) | Unit test in `tests/unit/physics/` of `board_area_mm2` on `build_outline` loops, rel 1e-12. The area is the exact area of the loops (Green's theorem per line and arc, `docs/phase3/engineering/fix_wave_f1.md` §A.3). The board loop counts positive, and every cutout loop and round hole is subtracted. C1: `CircleOutline(radius_mm=57.84)`, no bore, 10510.09015179737 mm^2. C2: `PolygonOutline(sides=12, across_flats_mm=93.0)`, 6952.477696010341. C3: C2 with bore `CircleOutline(radius_mm=12.5)` and `ScrewPattern(size="M3", fit=NORMAL, count=6, pitch_radius_mm=42.0, hole_diameter_mm=3.4)`, 6407.128627273689. C4: `CircleOutline(radius_mm=50.0)` with bore `PolygonOutline(sides=6, across_flats_mm=20.0, rotation_rad=0.3)`, 7507.571472460708. It catches the chord area (relative error -1.24e-5 in C1, +8.1e-6 in C3 and -1.73e-5 in C4), a dropped segment term, a polygon circumradius taken as across-flats / 2 (C2), and a bore or holes that are not subtracted (C3, C4) |
| GR-13 | Restated 2026-10-17 (U-D21, D-056i and D-056j; U-E17 §A.4 and §C.4, tests T-A1, T-A2, T-A4 and T-C3): EQ-16 and EQ-17 against Xcoil `massThermal` and the board area | The Phase 1 row stays (`massThermal` l.1378, 3 boards, 1e-9). T-A1: the strict xfail of `test_laminate_mass_of_the_mapped_layout_matches_xcoil_mass_thermal` (`tests/golden/m2_physics/test_gr_f11_mass_thermal_current.py`, DEF-M7b-01) is removed. The three mapped layouts match Xcoil `massLaminate` 27.287553101421075, 25.563329279667865 and 25.964418691799764 g in the INTEGRATED class (rel 1e-9). The chord area is 5.6e-6 to 7.5e-6 low on them. T-A2, new in the same file: `board_area_mm2(layout_from_xcoil(raw))` equals Xcoil `boardArea` 9338.872994612557, 8843.35209863596 and 8875.335981185855 mm^2 for the three tags (`_raw(f"layout-{tag}")`) in the KERNEL class (rel 1e-12). T-A4, new: Xcoil `outlinePrims("polygon", 8, 50, 0, 5)` and `outlineArea("polygon", 8, 50, 5)` dumped through `tools/golden/dump_xcoil.mjs`, the 16 records (8 lines and 8 corner arcs) mapped with `prim_from_record`, area 8279.968351327027 mm^2 within rel 1e-12, and the same area for the reversed loop. It catches the chord area on small corner arcs, a missing `abs` on a clockwise loop and a segment term of the wrong sign. T-C3, optional: a `mass_thermal` case with the parameters of `tests/golden/data/serpentine/layout-per-phase-3-gap-0p1.json` (`stackMode` perPhase, nBoards 3), run through the kernel tests that exist (INTEGRATED, rel 1e-9). It passes before and after the fix, because the kernels are already right, and it would catch a laminate mass that counts one board of a stack or a kernel that takes n x A |
| UT-PHY-07 | Restated 2026-10-17 (U-D17, D-051e; specification of U-D16, `docs/phase3/architecture/v3_contract_rulings.md` §3): the series chain EMF is the phasor sum of the pair EMFs, each at its own z. Marker `@pytest.mark.req("REQ-F-03")`; the test name holds `ut_phy_07` | Complex values compare with a relative tolerance of 1e-9 and `abs=0.0`, because the default absolute tolerance of `pytest.approx` voids a relative claim (D-050b). Case 1, a closed form on `solve_phase_circuit` (`src/embodic/physics/circuit.py` l.53; interfaces.md §8). Phase A of the `Circuit` holds two `ParallelGroup` values in series, each with one `Member` of one path. The two path flux linkages have equal magnitude and differ by 90 degrees. The expected phase EMF is the sum of the EMFs of two circuits that each hold one of the members alone. The magnitude of that sum is the square root of 2 times the magnitude of one member, within 1e-9 relative. A scalar sum would give 2 times, so the case tells a phasor sum from a scalar sum. A second run negates the flux linkage of one path, and its EMF enters the sum with its sign (the signature has no polarity input, so a reversed member shows as a negated flux linkage; `inferred` from `circuit.py` l.53-108). Case 2, the generated board. Use `series_design("CF-11", 2)`, the CF-11 spiral with k = 2 series pairs that `tests/unit/generators/test_spiral_series_fan.py` builds (`CASES`, l.27). For each member, compute its flux linkage with `field_table` at the copper z of that member and `integrate_path` over its paths (`src/embodic/physics/emf.py` l.69 and l.115), then take the EMF of the member from a one-member circuit. The fundamental of the phase EMF of `analyse()` (`physics/analyse.py` l.191) equals the sum of the member EMFs for every phase, within 1e-9 relative. First assert that the copper z values of the members differ, because a case with equal z cannot detect a wrong z. As a control, the same sum with every member evaluated at the z of the first member differs from `analyse()` by more than 1e-6 relative. The z clause needs a test because DEF-M3a-01 added k times the pitch to a z that already held it (D-035c). The test checks the arithmetic of the chain. It does not show that a series pair behaves this way on a board, which stays `unresolved` under D-020 and D-048f until a board exists |
| GR-07 | Restated 2026-10-17 (U-D17, D-051e; specification of U-D16, v3_contract_rulings.md §3): the even stack-up helper against Xcoil `stackupFor`, golden function level. Marker `@pytest.mark.req("REQ-F-04")`; the test name holds `gr_07` | Target: `generate_even_stackup` (`src/embodic/model/stackup.py` l.55-93) and `Stackup.copper_z_mm()`. The fixtures come from the function-level dumper (`tools/golden/dump_xcoil.mjs` with `tools/golden/functions` and `cases`), as the M1 function fixtures under `tests/golden/data/m1` are written. Xcoil `stackupFor` (`/home/claude/serpentine/src/engine.js` l.1156-1178, `verified` by reading). Auto mode places copper i at tOuter / 2 + i x (boardThickness - tOuter) / (nCu - 1) (l.1170), or at tOuter / 2 for one layer. A dielectric is the gap between two copper layers, never below 0 (l.1174-1175), and the board thickness stays the input value (l.1177). Custom mode takes the entry list as given, raises each thickness to at least 0.001 mm and stacks z from the sums (l.1159-1168). Case 1, auto mode. Copper counts are 1, 2, 4, 6 and 8, the board thickness is 1.6 mm, and copper is 1 oz or 2 oz with inner equal to outer. Each copper z, each copper thickness, each dielectric thickness and the board thickness equal Xcoil's within 1e-12 mm absolute (the Phase 1 tolerance, `test_plan_draft.md` l.165). Case 2, custom mode. Two Xcoil custom lists, one symmetric and one with unequal dielectrics, against a `Stackup` built from the same entries. Copper z equals Xcoil's within 1e-12 mm. Case 3, a board thinner than its copper, 8 layers of 2 oz on a 0.4 mm board (revision 2026-10-17, U-D19, D-053a; ruling `docs/phase3/engineering/gr07_case3_ruling.md` l.87-105; test `test_gr_07_case_3_a_board_thinner_than_its_copper_is_refused`, `tests/golden/m2_stackup/test_gr07_even_stackup.py` l.120-155, `verified` by reading). embodic refuses the input, because a board with B <= n x t has no room for a dielectric layer (the rule is `inferred`, a reasoned engineering ruling). The case does not compare embodic's values with Xcoil's, because Xcoil's output is not physical: its entries sum to 0.5568 mm while it reports 0.4 mm. It does not go through `golden_report`, so it needs no expected-difference entry. The test asserts four things. First, the committed fixture `stackupfor-auto-thin-8cu-2oz-0p4mm` records Xcoil's inconsistency within 1e-12 mm: the sum of its entries minus its `boardThickness` equals 8 x 0.0696 - 0.4, and its layer-centre pitch is smaller than the copper thickness. Second, `even_stackup_issues(8, 0.0696, 0.4)` (`src/embodic/model/validate.py` l.374) returns one ERROR `INVALID_STACKUP_COPPER_EXCEEDS_BOARD` with `value` 0.4 and `limit` equal to `math.fsum([0.0696] * 8)` within 1e-12 mm. Third, at the boundary B = n x t is refused, B = n x t + 1e-6 mm gives no issue, and the helper's dielectrics are all greater than 0 and sum with the copper to B within 1e-12 mm. Fourth, `generate_even_stackup(8, 0.0696, 0.4)` raises `ValueError` (`src/embodic/model/stackup.py` l.88), so the assertion fails if a clamp returns. The ruling's optional fifth item, an Xcoil fixture of 8 layers of 2 oz on 0.6 mm that pins agreement near the boundary, is not built (U-M6j report, item 2): `not tested`. A 0 mm dielectric in a hand-edited list yields `INVALID_NON_POSITIVE` because the field limit is `POS` (`src/embodic/model/fields.py` l.216, D-053a). That is a unit test of the validation module and not part of GR-07. Out of scope are unequal inner and outer copper, which the helper cannot express, and custom thicknesses below 0.001 mm, which Xcoil clamps. The helper takes one copper thickness for every layer (`stackup.py` l.55-57), and each of the 74 golden files that carry copper weights uses 2 oz inner and 2 oz outer (`verified` by grep over `tests/golden/data`), so no golden case exercises that difference. The helper feeds the UI stack-up inputs (`src/embodic/ui/viewmodels/session.py` l.921) and the serpentine and wave golden mappers (`tests/golden/m3_serpentine/design_map.py` l.72, `tests/golden/m3_wave/param_map.py` l.24), so a wrong z in the helper reaches all three, and this row compares the helper with `stackupFor` directly. The EMF goldens of GR-22 would see a wrong z only through the EMF (`inferred`) |
| UT-MOD-01 | Blank draft | `blank_draft(t)` has no required value and every optional field at its neutral value; `parse_draft` returns DraftIncomplete listing all required pointers in form order |
| UT-MOD-02 | Draft round trip | `parse_draft(draft_from_design(d)) == d` for every example |
| UT-MOD-03 | Field table completeness | every leaf of every DesignParameters variant has exactly one FieldSpec where it applies; `_mm` fields carry Unit.MM, `_rad` fields Unit.RAD; property fields are the closed list in ADR-0010 |
| UT-MOD-04 | Provenance derivation truth table | origin present or absent x value equal or not x measured or not; re-entering the current value changes nothing; setting a changed field back to the example value gives `example` |
| UT-MOD-05 | `mark_measured` refusals | empty source refused; design-kind field refused; a later value change drops the measurement |
| UT-RES-03 | Registry integrity (Phase 1 row, REQ-T-04). Amended 2026-10-09 (U-D11, D-040 b, U-M4c-4 f) | the packaged registries equal what their source documents give. `test_registry_packaged_counts_and_versions` (`tests/unit/results/test_registry.py` l.34) reads `expected_copies` of `tools/sync_registry.py` (l.51), which applies the filter that writes the copies to `docs/phase2/engineering/equation_registry.json` and `docs/phase2/evidence/evidence_register.json`. It compares the number of equations, the number of evidence entries and the version string (`v1+` and the first 12 hex digits of each copy's SHA-256) with `load_registry()`. The literal counts 30 and 108 are gone: they broke three times when Agent 5 added EV rows (store `decisions.tsv`, 2026-10-09T11:40Z). A stale packaged copy still fails, and Fable repairs it with `tools/sync_registry.py`. The helper `load_sync_tool` (`tests/unit/results/registries.py` l.26) loads that script for this test and for `test_sync_registry.py` |
| UT-RES-07 | EC-05 labelling (DEF-23) | `edge_leakage_fraction.status == assumption`; the EC-05 ValidityFlag has `metric_bound = lower_bound`, calibration `inferred`, transfer and threshold `assumption`; affected results list the transfer assumption in their tag |
| UT-IO-04 | Restated 2026-10-17 (U-D20, DEF-UM7d-01, interfaces.md §9.1): migration v1 to v2 | `parse_project` on a v1 file gives the design, provenance and issues that it gave before the change, plus `INFO_MIGRATED` with pointer `/schema_version`, `value` 1 and `limit` 2. A v1 file with a top-level `engine_version` or `registry_version` gives `INVALID_PROJECT_FILE` with that key's pointer and loads nothing. A file with `schema_version` 3 gives `INVALID_SCHEMA_VERSION_NEWER` with `value` 3 and `limit` 2 and loads nothing. Saving the migrated project writes `schema_version` 2. UT-IO-03 validates each file against the schema that its `schema_version` names, `project.v1.schema.json` or `project.v2.schema.json` |
| UT-IO-06 | Restated 2026-10-17 (U-D20, DEF-UM7d-01; REQ-T-07): export metadata in every writer | The Phase 1 criterion stays for SVG, DXF, PDF and README. Project JSON: without the keyword, `save_project` writes `engine_version` equal to `embodic.__version__` and `registry_version` equal to `load_registry().version`; with `registry_version` it writes the value passed. The bundle's project file holds `outcome.versions.registry`. The design hash of each packaged example does not change (the `EXAMPLE_HASHES` pin of UT-IO-08 stays). Save, load, save with one `saved_utc` gives identical bytes. The strict xfail `test_t07_project_json_holds_the_engine_version_and_the_registry_version` (`tests/unit/embodic_io/exporters/test_stamp_fields.py` l.53) becomes a plain test |
| UT-IO-07 | Project file provenance and drafts | save and load keep origin example, per-field provenance and measurement sources; an incomplete draft loads as LoadedDraft with the same missing list; a stored `example` entry that disagrees with the packaged example is reported |
| UT-IO-08 | Examples | every packaged example loads, validates and computes with no ERROR issue; every title contains "Example". Revision 2026-10-09 (U-D10, U-M4c-3): every example has a `display_note` that names no other program, no `engine.js` and no repository path (UX-AC-03; `test_ruling_g4_example_items_show_a_600_title_over_a_text3_note_free_of_other_programs`, `tests/ui/qt_design/test_ruling_g.py` l.132; interfaces.md §9.1). The title check of UX-AC-03 is a strict xfail (§5.6). Revision 2026-10-09 (U-D11, D-041a (Fable, 2026-10-09), U-S4e ruling g): a title is free English display text, so "every title contains "Example"" no longer holds. The criterion becomes: the title, the note and the saved design name of each example name no other program and no repository path, and the saved project holds no `example` object (`test_ux_ac_03_an_exported_example_names_no_other_program_and_no_repository_path`, `tests/unit/embodic_io/project/test_examples.py` l.47, one case per example file). UX-AC-03 (`docs/phase2/design/acceptance_criteria.md`) also asks that the five gallery titles equal the list of ruling g: "Spiral, 12 coils, 16 poles", "Spiral, 12 coils, 14 poles", "Spiral, 12 coils, 10 poles (D08)", "Serpentine, 16 poles", "Wave, 16 poles, involute". No test on main 9776555 asserts that equality (`verified` by reading `test_ruling_g.py` and `test_examples.py`), and the brief of U-M4e-1b asks for the files to carry those titles exactly, for the two xfails to flip and for a check that a title change leaves the design hash alone. A title change does not change the design hash. On main 9776555 `test_ut_io_08_spiral_examples_are_packaged_with_example_titles` (`test_examples.py` l.30) still asserts "Example" in each title, and U-M4e-1b (in flight) replaces it. Revision 2026-10-11 (U-D12, D-041a, D-041b; main 4fda98d, `verified` by reading, and by running the tests named here, 2026-10-11): the sentences above that say "still asserts", "in flight" or "no test" are closed. `test_ut_io_08_examples_are_packaged_with_the_ruling_g_display_titles` (`test_examples.py` l.44) asserts that the five titles equal the list of ruling g (`RULING_G_TITLES`, l.26). `test_d_041b_each_example_design_is_named_by_its_display_title` (l.52) asserts that `load_example(id)[1].name` equals the title, because D-041b makes the design `/name` equal the title (the window title and the export stem show it). `/name` is inside the design hash and the title is not, so U-M4e-1b left the five hashes unchanged and D-041b moved all five (`EXAMPLE_HASHES`, l.34). `test_ut_io_08_the_packaged_design_hashes_are_pinned` (l.58) pins them, and the unit that changes an example design edits that table. `test_ux_ac_03_an_exported_example_names_no_other_program_and_no_repository_path` is at l.68 and has no xfail mark. Run: `9 passed, 39 deselected` for `pytest tests/unit/embodic_io/project/test_examples.py tests/unit/embodic_io/exporters/test_report_readme_bundle.py -k "test_ut_io_08_examples_are_packaged or test_d_041b or hashes_are_pinned or ux_ac_03 or ruling_f"` (the filter also selects the five cases of UX-AC-03 and the colophon test) |
| UT-EXP-01 | SVG | parses with `xml.etree`; path, via and pad counts equal the Layout; `<metadata>` holds the REQ-T-07 fields; phases carry class and label in both render modes. Revision 2026-10-09 (U-D10, D-039 c): in both render modes the D08 drawing holds the 12 `coil-label` texts with the D08 polarities and 12 eye fills clipped to their discs, with no hatch end outside the disc (`test_d08_drawing_labels_every_coil_and_fills_every_eye_clipped`, `test_svg.py` l.117); the B hatch lines are 0.4 mm apart at 1:1 (`test_d08_hatch_pitch_is_0_4_mm_at_1_to_1`, l.140); each phase has a legend swatch and the text "Phase A", "Phase B" or "Phase C" (l.102-106); no copper or legend bar has a dash pattern (l.152); the footer fits inside the drawing (l.161). The halo is a second `coil-label-halo` text under each label, which `tests/unit/embodic_io/exporters` does not assert (`not tested`) |
| UT-EXP-02 | DXF complete, outline, screws | ezdxf audit 0 errors; outline file holds only outline and bore entities with every end point shared by exactly two entities; screws file holds only circles, count = holes. Revision 2026-10-17 (U-D20, D-055c; REQ-N-21): R12 stores an ARC as centre, radius and two angles, so the end points of an ARC are derived and are not the written numbers of its neighbour. A copper joint of the complete file that touches an ARC holds when every written or derived end point at the joint lies within `COINCIDENCE_MM` (1e-6 mm) of every other; U-M7c measured at most 1.4e-9 mm on D08 and the wave example. A joint of LINE entities only still writes one number (`test_n21_dxf_writes_one_point_for_every_line_to_line_joint`, `tests/unit/embodic_io/exporters/test_n21_joint_continuity.py` l.142). The joints are those of the Layout, as in that module. A control that moves one ARC centre by 2e-6 mm must fail, and the test asserts that it checked at least one ARC joint per example |
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
| PR-02 | Restated from Phase 1 (DEF-V1-01): the symmetry shortcut equals the full check. With `use_symmetry` True and False, the same violation set and the same `least_clearance_mm` per kind (was `measured_min_mm` until 2026-10-17, U-D17, D-051a; `src/embodic/drc/report.py` l.79 on main 0547f20) within 1e-9 mm; an asymmetric layout falls back to `grid+exact` |
| PR-05 | Phase 1 row, kept as written (`docs/phase1/architecture/test_plan_draft.md` l.239): random parameter sets give no uncaught exception and no NaN or infinity in any result, and invalid inputs return issues. Revision 2026-10-13 (U-D15, U-M5h; `tests/unit/property/test_pipeline_properties.py`, `src/embodic/model/validate.py` and `src/embodic/api.py` on main 5e74acc, `verified` by reading). Counterexample: an empty `/analysis/harmonics`. The release run on 10c6411 in the nightly profile found it. The empty list passed validation, reached physics and raised IndexError (the comment at l.94; not reproduced here). That breaks the first clause. The test pins it as `@example(draft=cf11_draft_with({"/analysis/harmonics": []}))` (l.95) on `test_pr_05_arbitrary_values_never_raise_and_invalid_values_return_issues` (l.96). The cause was a missing rule: physics reads index 0 as harmonic 1 (`physics/analyse.py` l.298) and nothing checked it. `validate_design` now returns the ERROR `INVALID_HARMONIC_FUNDAMENTAL` for an empty list or a first entry other than 1 (`validate.py` l.337-340, interfaces.md §2.2), and `compute` stops before geometry and physics (`api.py` l.270-283). The example asserts that no exception and no `INTERNAL_` issue occur and that `outcome.ok` is False when an ERROR issue exists (l.97-106). It does not assert the code. `test_a_harmonic_list_that_does_not_start_with_the_fundamental_is_an_error` (`tests/unit/model/test_validate.py` l.32) does, for `()`, `(3, 5)` and `(3, 1)`. U-M5h reports `17 passed` for the nightly PR file; this unit did not re-run it (`not tested` here) |
| PR-13 | DRC never under-reports, for every generator: whenever `drc.passed`, Agent 4's brute-force checker finds no non-exempt pair below rule - 1e-6 mm, and every pair it finds below that is reported (PR-01 extended to serpentine and wave) |
| PR-14 | Rotation symmetry for serpentine and wave: rotating the start angle by one electrical period shifts every phase phasor by the expected angle (1e-9 rad) and leaves abs(Ke), R and all DRC values unchanged (1e-9 rel., 1e-9 mm). Revision 2026-10-08 (U-D7, D-035d, D-035e): the wave has no start angle field, so the wave test rotates through `generate_wave_rotated`, and its phasor part waits for a per-phase phasor field (PR-07). The serpentine counter-example with sharp corners and one turn (DEF-M3a-02) changes Ke by 8.5e-9 rel. U-M3-fix diagnoses it, and the outcome sets the tolerance. If the cause is float accumulation, the Ke tolerance becomes 1e-8 rel. and this row names that cause. If the cause is a defect, U-M3-fix fixes it and 1e-9 rel. stays. Revision 2026-10-09 (U-D8, D-036c; `tests/unit/property/serpentine/test_serpentine_properties.py` l.39 and l.156-175 on main 8a297a0, `verified` by reading): the cause is float accumulation (branch B). A side line that is a whole number of 0.5 mm chords changes its computed length by 1 ulp under rotation, so `ceil` gives 36 or 37 chords. The serpentine Ke tolerance is 1e-8 rel. (`KE_REL_TOL`), and the DEF-M3a-02 strict xfail is removed. The phasor angle, R and the DRC values keep 1e-9. The wave test keeps 1e-9 rel. Revision 2026-10-17 (U-D19, D-054a; `docs/phase3/engineering/pr14_and_reqf_texts.md` §1.5 and §1.6, `verified` by reading): the Ke tolerances of D-036c and of the wave test are withdrawn. Both Windows failures are a chord-count flip, not a rotation defect (DEF-UE16-01, a test defect, no product change). A side whose length sits within a few ulp of a whole number of 0.5 mm chords gets m or m + 1 chords from `ceil`, depending on the last bits of the platform's sin and cos. The flip envelope is 7.8e-7 relative on the serpentine counter-example (84 lines) and 2.8e-7 on the wave overlap case (54 primitives), and the tolerances cover about one net flip (`verified`, U-E16's probe `checks/pr14_chord_flip_probe.py`; not re-run here). With equal chord counts the base and the rotated board agree to 6e-16 relative on the serpentine and bit for bit on the wave. New method. First, in both builds `pytest.MonkeyPatch` replaces `embodic.geometry.discretise.piece_count`, so that a length ratio within eta = 1e-9 relative of an integer m gives exactly m chords, and every other ratio keeps `ceil`. Second, Ke, `ke_line` and `loss_eddy_w` are compared at rel = 2 (N + 10) u kappa, with u = 2^-53, N the chord count that `discretise_path` gives on the base board, and kappa = 1 unless the test measures it. That is 1.3e-12 on the serpentine counter-example (N = 6001) and 1.2e-12 on the wave overlap case (N = 5389), `verified` by arithmetic on the N and kappa that U-E16's `checks/pr14_roundoff_inputs.py` measured. The bound is `inferred` (Higham, section 4.2, cited from memory in U-E16) and its 10 u term for the interpolation and `exp` steps is an `assumption`. A fixed constant is allowed only with its range stated: rel = 1e-10 holds for N up to 4.5e5 at kappa = 1. Third, the phasor angle, R and the DRC values keep 1e-9 rad, 1e-9 rel. and 1e-9 mm. eta is `verified` for these two boards, where every designed integer lands within 23 ulp (5.1e-15 relative), and `inferred` for Hypothesis designs. That `loss_eddy_w` flips as Ke does is `inferred`, and `not tested`. Agent 3 changes the tests; this row is their specification |

### 5.3 UI tests (pytest-qt, offscreen)

| ID | Scenario | Criterion |
|---|---|---|
| UI-22 | Load an example | every field shows the "Example" chip; edit one field and its chip disappears; set it back and the chip returns; no badge changes |
| UI-23 | Start | the window opens in the empty session with New design and Examples; no compute runs |
| UI-24 | New design | choose a topology; the form is blank; Compute is disabled and shows the missing count; filling the last required field triggers exactly one compute |
| UI-25 | Toolstrip | every TOOLSTRIP action has an icon file, English label, tooltip and accessible name; its command resolves; arrow keys move within a tab; icons recolour after a theme switch. Revision 2026-10-09 (U-D11, F21, U-M4e-1): `act-open` is enabled and its command `open_project` opens a saved D08 file into the inspector and computes it (`tests/ui/qt_shell/test_open_project.py` l.25); a file that does not load shows why and keeps the open design (l.43). The board picker is not a TOOLSTRIP action and is not part of this row (interfaces.md §11) |
| UI-26 | Themes | switch light, dark and system at runtime; every widget restyles; the choice persists after restart |
| UI-04 | Layer visibility toggles. Phase 1 row, amended 2026-10-09 (U-D10, U-M4c-3) | hidden layers are absent from the scene and return when shown (`tests/ui/qt_shell/test_theme_and_geometry.py` l.134); hiding the top layer keeps a label for every phase and moves the eye fills to the next visible layer, 12 of them for D08 (l.147); the view-model records a hidden layer and restores it (`tests/unit/ui/shell/test_outcome_viewmodel.py` l.190) |
| UI-05 | Event-loop latency probe during a 3 s synthetic compute. Phase 1 row, kept as written, with a measurement note (revision 2026-10-13, U-D15, U-M5h; `tests/ui/qt_shell/test_worker_and_errors.py` on main 5e74acc, `verified` by reading unless a clause says otherwise) | Input echo under 100 ms (`assumption` threshold, REQ-N-02). Two tests carry the ID. `test_ui05_compute_runs_off_the_gui_thread` (l.50) records the thread of the compute call. `test_ui05_event_loop_answers_within_100ms_during_a_3s_compute` (l.66; marked `slow`, so only the nightly and release profiles run it) takes the largest gap between 10 ms GUI timer ticks over 2.5 s inside the compute. Measurement note: opening the example posts the window's repaint. Left in the event queue, that repaint became the first tick's gap, 4 ms alone and about 250 ms against the worker's GIL (comment at l.96-97), so the earlier test timed the opening paint and not the answers of the loop during the compute. The test now calls `QApplication.processEvents()` (l.98) before it measures, and it asserts that the compute is still running (`(len(shell.calls), finished) == (1, [])`, l.101). The bound `during < 100` (l.102) is unchanged. U-M5h measured the earlier test at 243 to 251 ms in 3 of 3 runs alone on an idle machine and the fixed test at 23 to 35 ms in 5 of 5 runs (its report; `inferred`, not re-run here). The test does not cover the first paint after opening. Fable recorded that stall as DEF-U-M5h-01: about 250 ms under a pure-Python compute, `inferred`, Phase 5. The real compute is `not tested`, and Fable's own run of the earlier test alone on 10c6411 passed once, so the timing varies |
| UI-27 | Phase render mode. Amended 2026-10-09 (U-D10, D-039 d, U-M4c-3, UX-AC-27) | colour and greyscale-hatch toggle in the geometry view and charts; labels present in both and read phase, number and U+2212 for minus (D08: A1 to A4, B1 to B4, C1 to C4; the earlier assertion that pinned a hyphen is replaced); the canvas fills the eyes the exports fill and each eye fill is its coil's eye disc, clipped to it; no label overlaps another at fit zoom or at 3x, and the labels are placed again after every zoom, pan and resize step; a skipped label shows in the hover tooltip of its copper; the legend shows a solid copper bar, an eye swatch and the phase name; the eye hatch is a screen-space pattern, so it shows at fit zoom (`test_outcome_viewmodel.py` l.130-189, `tests/ui/qt_shell/test_canvas_labels.py` l.77-182, `test_theme_and_geometry.py` l.70 and l.88). Revision 2026-10-09 (U-D11, U-S4e ruling h, U-M4e-1): the first label of each phase and sign is forced, so the wave fit view shows both signs of every phase (`test_ruling_h_the_wave_fit_view_labels_both_signs_of_every_phase`, `test_canvas_labels.py` l.201); every phase with copper in view has a label and every leader stays inside the view at 4x zoom on three corners of the D08 and wave examples (l.211); fit zoom survives a resize until the user zooms (l.231); the pure placement is pinned in `tests/unit/geometry/marks/test_labels.py` (l.55, l.139, l.150, l.158, l.169) |
| UI-28 | Applicability matrix | for each topology and option combination the visible inputs equal `field_specs` filtered by applicability |
| UI-29 | Export confirmation | with an injected DRC error the confirmation lists the failures and has focus on Cancel |
| UI-30 | Chart audit | one unit per y axis, legend and direct labels, data-table alternative, status badge |
| UI-31 | Reduced animation | with the OS animation setting off no transition runs |
| UI-32 | Drawing stamps. Replaced 2026-10-17 (U-D21, D-056; text of `docs/phase3/design/fix_wave_f1.md` section (d), Agent 1) | (a) A chart model with `computed=False` shows "Illustrative, not computed"; an engine chart shows no such stamp. (b) With D08 open, `fig-canvas` `stamp()` equals "embodic " + `versions.embodic` + " \| design " + the first 12 hex digits of `design_hash`, and its rectangle lies inside the viewport's bottom-left 50 % by 25 %. (c) A grab of the canvas differs inside `stamp_rect()` from a grab with the stamp switched off, and the darkest text pixel in the plate reaches 4.5:1 on the plate. (d) After an invalid edit makes the drawing stale, `stamp()` is unchanged. After loading `spiral_12c14p`, `stamp()` names that outcome's hash. (e) At fit zoom no phase label box meets `stamp_rect()`. (f) The canvas accessible description ends with the stamp text. Clause (a) is the present test (`tests/ui/qt_results/test_charts_compare_guide_export.py` l.78). Clauses (b) to (f) are new |
| UI-33 | EC-05 disclosure | the disclosure of Ke shows e_edge, the words "at least" and "assumption", and the 10 % cap label |
| UI-34 | Number formatting in comparisons | counts as integers; deltas with sign and glyph, never colour alone |
| UI-58 | Layer cue at a crossing (design_spec.md 3.3.1, DEF-UV16-02; revision 2026-10-20, U-S16). D08, all layers visible, `fig-canvas` without focus, 24 px/mm centred on (-11.01, 47.19) mm, where ring A (path 32, L1, 1.0 mm) crosses leg 24 (L2, 0.6 mm). Three runs: dark colour, dark greyscale, light greyscale | Follow leg 24's centre line outward (growing radius) from the crossing. (a) The pixel at the crossing equals the phase A ink of the run exactly (`#c43b10`, `#e0e0e0`, `#262626`). (b) The pixels 1 and 2 px beyond the ring's edge equal `board-fill`; their contrast to the pixel of (a) is at least 3:1. (c) At radius 49.36 mm, between rings A and B, across the leg: the centre pixel equals `board-fill`; on each side of the centre the largest contrast to `board-fill` is at least 2:1 (the outline); the span of pixels with contrast above 1.3 to `board-fill` is at most the true width + 1.5 px (14.4 px + 1.5 px). (d) With L2 solo (one layer visible, so no cue), the centre pixel of (c) equals the phase A ink. U-S16 measured (b) 3.09:1, 12.34:1 and 14.13:1; (c) sides 2.55 and 3.09, 9.24 and 12.34, 8.81 and 14.13, spans 14.75, 15.5 and 15.5 px, on its prototype (`docs/phase3/design/checks/u_s16/u_s16_measurements.json`, `d08_crossing`, rows `hybrid`). 0.0.3 gives 1.0:1 in (b) and the phase ink in (c), so it fails |
| UI-59 | No lower copper touches upper copper (design_spec.md 3.3.1). D08 at 6 px/mm centred on (4.8, 27.45) mm in a 560 x 352 px viewport; serpentine_16p_example at 5 px/mm centred on (0, 0) in 480 x 480 px and at 20 px/mm centred on (0, 33) mm in 480 x 320 px; all layers visible, no focus; dark colour, dark greyscale, light greyscale | For each visible layer except the bottom one, take the band of pixels whose centres lie 0.75 to 1.5 px outside that layer's true copper, computed from the layout (the stroke of each primitive at its width plus 2 x 1.5 px, less the same at plus 2 x 0.75 px, filled without antialiasing). Leave out pixels inside the copper of a layer above it grown by 1 px, inside a via or pad grown by 2 px, inside an eye disc grown by 1 px, and inside the legend, the stamp and every label box grown by 3 px. At most 1 % of the band pixels have a contrast above 1.1 to `board-fill`. U-S16 measured 0.03 %, 0.04 % and 0.30 % to 0.31 % on its prototype; 0.0.3 measured 8.0 % to 8.2 %, 12.5 % to 12.6 % and 5.2 % (`u_s16_measurements.json`, `band_violations`, the lever `u_s16_layer_cue_renders.py` in the same folder) |
| UI-60 | Layer legend (design_spec.md 3.3.1) | D08 with all layers: the legend has the phase rows, then "L1 on top" with a solid `text-1` bar and "Layers below" with an outlined `text-1` bar whose centre pixel is the legend surface. With L2 solo, neither layer row shows. serpentine_16p_example with L1 hidden: row 1 reads "L2 on top". The legend panel stays inside the viewport at 1280 x 800 in both |
| UI-61 | Land shapes (design_spec.md 3.3.1, DEF-UV16-03) | D08: each of pads U, V and W is a `QGraphicsEllipseItem` tagged "pad" whose rect is 2.4 x 2.4 mm centred on the pad; the item's shape does not contain the point (+1.0, +1.0) mm from the pad centre, which lies inside the old square and outside the circle; an item tagged "drill", a `canvas` disc 1.2 mm across, sits at each pad centre. A layout with one oblong pad 3.0 x 1.5 mm at 30 degrees and one rect pad 2.0 x 1.0 mm: each pad item's path, mapped to model millimetres, has the bounding box of `pad_outline(pad)` within 1e-6 mm, and a corner of the oblong's rotated 3.0 x 1.5 mm box lies outside the oblong's path. Pads and vias are drawn after all copper: in the scene's stacking order every via, pad and drill item is above every item that draws copper, its outline or its casing |

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
| UI-09 | `test_ui09_the_window_renders_at_each_scale_factor` (`test_ui09_scaling.py` l.31) | one new process per `QT_SCALE_FACTOR` of 1, 1.5 and 2; the grab is 1280 x 800, 1920 x 1200 and 2560 x 1600 pixels. The grabs are kept for Agent 1. The form-fit rows of REQ-N-15 are in the next row | "No clipped or overlapping text" is a judgement on the images, so it is `not tested` by code |
| UI-09, form-fit rows of REQ-N-15 (revision 2026-10-17, U-D22; D-057e; text of `docs/phase3/design/fix_wave_f2.md` section (a)) | `tests/ui/qt_shell/test_n15_inspector_fits.py`, rows N15-1 to N15-7 | N15-1 loads each of the five packaged examples (`spiral_12c10p_d08`, `spiral_12c14p`, `spiral_12c16p_default`, `wave_16p_example` and `serpentine_16p_example`) at 960 x 540, 1280 x 800 and 1920 x 1080 and asserts `wider == {}` for all 15 cases. `wider` collects each inspector tab whose form is wider than its viewport. N15-2 uses the same windows and examples and compares the width of each visible `QComboBox` that has a current item with its size hint, which it must never be narrower than. N15-3 (D08 at 960 x 540, each shown chip lies above its input), N15-4 (`test_ruling_g.py`, one right edge per section), N15-5 (serpentine Layers tab at 960 x 540, `param-stack-mode-single` lies above `param-stack-mode-one_board_per_phase` and the body fits), N15-6 (Board tab, `btn-screw-add` reads "Add" and `btn-screw-remove` reads "Remove", with the accessible names "Add screw pattern" and "Remove screw pattern") and N15-7 (the UX-AC-17 and N-24 tests pass unchanged) are worded in that section | The test file on main eea9757 loads D08 only, runs 960 x 540 and 1280 x 800, and carries a strict xfail for DEF-U-M7c-02 (`verified` by reading). N15-1 and N15-2 over the five examples are `not tested` until Agent 3 builds them |
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

### 5.3.2 Typing preview and stepping rows (revision 2026-10-17, U-D22; D-057)

Two Agent 1 documents word offscreen Qt rows that had no plan ID. Rows N02-1 to N02-10 test the typing rule of REQ-N-02
and UX-AC-22 (`docs/phase3/design/fix_wave_f1.md` section (a)). Rows S-1 to S-12 test Up, Down and Shift stepping in
numeric fields (DEF-US11-04, `docs/phase3/design/fix_wave_f2.md` section (b)). Each row gets one ID, so a test that covers
two rows carries two IDs. The row text is copied from the document that words it. That document holds the derivations
and the rest of the contract, and this plan holds the IDs and the meaning they give a row.

Every row uses the `make_shell` fixture with its counting `compute_fn`, loads D08 (`spiral_12c10p_d08`), waits for the
first result and clears the call list. Field `param-r-inner` holds 11.47 mm. Times use `QElapsedTimer`. Rows UI-36 to
UI-45 link to REQ-N-02. Rows UI-46 to UI-57 link to REQ-N-12, and the link is `inferred` (requirements.md revision
2026-10-17, U-D22).

The N02 rows have tests on main eea9757 in `tests/ui/qt_shell/test_n02_typing_preview.py`. Each test marks REQ-N-02, and
its docstring names its row (`verified` by reading the file; line numbers are those of the `def` lines). This unit ran
none of them, so a statement that they pass is `not tested`.

| ID | Row | Test | Steps and pass |
|---|---|---|---|
| UI-36 | N02-1 | `test_n02_1_and_2_typing_previews_once_after_300_ms_and_return_commits_without_a_second_compute` (l.108) | Focus the field, select all, type "11.48" at 50 ms per key, then wait 600 ms. Exactly one compute call, 300 ms ± 50 ms after the last key, with r_inner 11.48 mm. The undo stack length, the `param-r-inner-prov` chip text and the autosave file are unchanged |
| UI-37 | N02-2 | the test of UI-36 | After N02-1, press Return. No new compute call. The undo stack grows by one. The chip reads `user` |
| UI-38 | N02-3 | `test_n02_3_return_before_the_timer_computes_at_once_and_only_once` (l.140) | Type "11.49", then press Return 100 ms after the last key. One compute call, starting within 50 ms of Return. No second call after 300 ms |
| UI-39 | N02-4 | `test_n02_4_text_that_is_no_number_never_computes_and_shows_its_message_only_at_commit` (l.155; also marks REQ-F-37) | Type "abc", wait 600 ms, then press Return. No compute call. While waiting, `param-r-inner-error` is hidden. After Return it shows the catalogue text of the issue code `INVALID_TYPE` and the field has `invalid=true` |
| UI-40 | N02-5 | `test_n02_5_esc_before_the_timer_puts_the_committed_text_back_and_keeps_focus` (l.173) | Type "12", press Esc after 100 ms. No compute call. The text is "11.47" again. Focus stays in the field |
| UI-41 | N02-6 | `test_n02_6_esc_after_a_preview_brings_the_committed_results_back` (l.189) | Type "12", wait 600 ms (one preview), press Esc. The results show the committed outcome again. `res-ke-value`, the card of `ke_phase_v_s_per_rad`, equals its text before the typing. The undo stack is unchanged |
| UI-42 | N02-7 | `test_n02_7_a_keystroke_cancels_the_preview_in_flight_at_once` (l.208) | Use a `compute_fn` that blocks until its token is cancelled. Type "12", wait 400 ms, type "3". The first request's `CancelToken` is cancelled within 50 ms of the "3" key. One more call starts 300 ms ± 50 ms after it |
| UI-43 | N02-8 | `test_n02_8_a_choice_control_commits_and_computes_at_once_without_a_timer` (l.235; two cases) | Focus a `QComboBox` field row and press Down. Focus a check box field and press Space. Each starts one compute call within 50 ms. No timer is running afterwards. The cases are `param-modulation` on `tab-board` of D08 (Down) and `param-fillet-max` on `tab-coil` of `serpentine_16p_example` (Space) |
| UI-44 | N02-9 | `test_n02_9_toolstrip_save_while_a_field_holds_typed_text_saves_the_typed_value` (l.256). A second test, `test_n02_9_compute_and_undo_from_the_toolstrip_commit_the_typed_text_first` (l.274), adds Compute and Undo (DEF-US11-03) | Save the design once to a path under `tmp_path`. Type "11.5" into the field, then click the toolstrip Save button without leaving the field. The file at that path holds 11.5 mm |
| UI-45 | N02-10 | `test_n02_10_keystroke_echo_while_a_preview_result_arrives` (l.291; marked `slow`) | Use a `compute_fn` that returns after 200 ms. Type "11.6", wait 450 ms, then type five keys at 50 ms. Measure the largest gap between 10 ms GUI timer ticks, as UI-05 does. The row reports the gap. It passes at 100 ms or less (REQ-N-02 input echo, `assumption`). A fail goes to the stall work of U-M8a, not to the debounce |

The stepping rows have no test on main eea9757. A grep for `Key_Up` in `tests/` finds no match (`verified` by running it).
Agent 3 builds them (`fix_wave_f2.md`, "Requests to other owners"). A step is an uncommitted edit like typing, so S-1,
S-3 and S-12 also check the 300 ms rule of UX-AC-22. The step of each field comes from `FieldSpec.step`, in the unit the
form shows, and Shift moves ten steps. `param-r-inner` steps by 0.5 mm (`src/embodic/model/fields.py` l.110, `verified` by reading).

| ID | Row | Test | Steps and pass |
|---|---|---|---|
| UI-46 | S-1 | none yet | Focus `param-r-inner`, press Up. Text "11.97". No compute call within 250 ms. One call 300 ms ± 50 ms after the key, with r_inner 11.97 mm. The undo stack and the vertical scroll value of `tab-coil` are unchanged |
| UI-47 | S-2 | none yet | Press Shift+Down from 11.47. Text "6.47" |
| UI-48 | S-3 | none yet | Press Up five times with `QTest.keyClick` at 50 ms, then wait 600 ms. Text "13.97". Exactly one compute call |
| UI-49 | S-4 | none yet | Press Up, then Return. The undo stack grows by one, the chip reads `user` and the committed value is 11.97 mm |
| UI-50 | S-5 | none yet | Press Up twice, then Esc. Text "11.47", no undo entry, focus stays in the field |
| UI-51 | S-6 | none yet | Type "0.02" into `param-coil-gap` and press Down. Type "0.3" into `param-r-inner` and press Down. The texts are "0" and "0.3" |
| UI-52 | S-7 | none yet | Type "0.07" into `param-air-gap` (low 0.05) and press Down twice. Type "60" (high 50), press Up, then Down. The first field reads "0.05" after both Downs. The second reads "60" after Up and "50" after Down |
| UI-53 | S-8 | none yet | Type "abc" into `param-r-inner` and press Up. Clear the field and press Up. The texts are "abc", then "". No compute call |
| UI-54 | S-9 | none yet | Read the text t of `param-first-coil-angle`, press Up, then Return. The text is t + 1 and the committed value is t + 1 degrees in radians |
| UI-55 | S-10 | none yet | Press Up in `param-poles` (10). The text is "12" |
| UI-56 | S-11 | none yet | Press Down on `param-rotor-kind`. Add two patterns with `btn-screw-add`, select a cell of the first row and press Down. The combo commits one choice (UI-43). The table moves to the next row and no value changes |
| UI-57 | S-12 | none yet | Press Up in `param-board-thickness`, wait 600 ms, then press Return. No compute call before Return. The thickness rises by 0.1 mm after it |

### 5.4 Static, language and accessibility gates

| ID | Gate |
|---|---|
| MT-01 | Amended: import-linter contracts C1 to C4 of `package_layout.md` §3 (core layers with generators above io, outcome, physics and drc; no Qt outside the Qt adapter modules; UI-internal layers; no KiCad or other GUI toolkits) |
| MT-04 | Amended 2026-10-17 (U-D21, D-056f; REQ-N-09). Phase 1 text kept (`docs/phase1/architecture/test_plan_draft.md` l.381): a docstring check that public physics functions give parameter units and an EQ-ID. A parameter or return value of dimension one names its unit `dimensionless`, and the unit-token check in `tests/static/test_n09_parameter_units.py` accepts that word in place of a unit token. D-056f cites the BIPM SI Brochure, 9th edition 2019, quantities of dimension one, as the reason (this unit did not read it). The question that the test file records at l.87 is answered |
| MT-07 | Scope guard for D-009: no `kipy` or `pcbnew` import, no `.kicad_pcb` writer, no KiCad option in CLI choices, and no "KiCad" in the string catalogue |
| MT-08 | New 2026-10-05 (U-M1y): no package folder under `tests/` or `src/` whose name becomes a top-level module name shadows a standard-library or installed module (`sys.stdlib_module_names`, `importlib.metadata.packages_distributions()`), and no two such folders share a name (`tests/static/test_mt08_no_stdlib_shadowing.py`; naming rule in package_layout.md §1) |
| LG-01 | Amended 2026-10-04 (U-M1a deviation, ratified in part). From M1: every string literal in `src` holds only printable ASCII, tab, newline and the allowed unit symbols (U-M1a's character-class check). From M4: every word in the string catalogue and report templates is in an English word list plus the glossary allow-list. The word list has no source yet (no dictionary package in package_layout.md §5): `unresolved`; U-M4b proposes one through Fable before M4 exit. Revision 2026-10-09 (U-D11, D-040 a and c): one module may add characters of its own. `MODULE_SYMBOLS` (`tests/static/test_lg_language.py` l.12) maps a module name to them. `embodic.results.labels` admits η, δ and Δ, the Greek letters of the equation-specification symbols, and no other module may hold them (`test_lg01_admits_the_spec_greek_letters_in_the_label_module_only`, l.81). D-040 c adds U+00A0 for `embodic.results.formatting` only, which U-M4e-1b builds; `MODULE_SYMBOLS` has no such entry on main 9776555. Revision 2026-10-17 (U-D20, D-055; REQ-L-01): the M4 word-list clause is withdrawn, because no English word list exists in the repository (U-M7d L-01). LG-01 keeps the character rule. It adds one function that returns the sorted distinct words of the string catalogues and the report templates, and one command that prints them. A test asserts that the list holds a word planted in a catalogue value, which catches a list that scans nothing. The reviewer reads the printed list and writes a manual record (interfaces.md §3.2) that names the commit |
| LG-03 | Restated 2026-10-17 (U-D18). Phase 1 text kept: no "measured" applied to a computed value in a string, a template or an export, and the allow-list admits "reference (paper, measured)". Scan class `measur` over the three corpora of §5.8.1, with the allow-list of §5.8.2. Tests `tests/static/test_lg_wording.py` and `tests/unit/embodic_io/exporters/test_lg_exports.py`, marker REQ-T-10 |
| LG-04 | Restated 2026-10-17 (U-D18). Phase 1 text kept: no balance, torque or efficiency claim phrased from geometry alone, against a reviewed phrase list. Scan class `balanc`, `torque`, `efficien` over the same corpora, with the allow-list of §5.8.3, marker REQ-T-11. The reviewer clause of REQ-T-11 is a manual record (§5.8.3) |
| LG-05 | Restated 2026-10-17 (U-D18). Phase 1 text kept: 0 occurrences of "xcoil", ignoring case, in user-facing strings and generated files. U-D18 adds the other program names of D-051c as a second class. Allow-list of §5.8.4, marker REQ-L-03 |
| LG-06 | Restated 2026-10-17 (U-D18). Phase 1 text kept: brand asset checksums, and a personal-data scan of 0 hits. Two tests with the designs of §5.8.5, marker REQ-L-05 |
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
| TR-01 | Restated 2026-10-17 (U-D17, D-051e): trace gate with manual records (REQ-T-09, REQ-N-10) | `tools/trace_matrix.py` on a fixture REQ report and a fixture requirements file (interfaces.md §3.2). With the flag `--fail-untested-through` set to `M5`, the script exits 1 and lists a live must row of milestone M5 or earlier that has no passing test and no manual record with result `passed`. It exits 0 when each such row has one or the other. A row whose only record has result `failed` is listed. A should row, a could row and a withdrawn row are not listed. Without the flag, no row is listed. With `--manual-records`, the script exits 1 and names the record when a `result` is neither `passed` nor `failed`, when a `req` is not a row of the requirements file, or when a `record` path does not exist. The summary line prints the manual count apart from the test count ("manual: 1"). In `tools/ci.py`, `gates_for` gives the release profile a trace-matrix gate named "trace matrix (TR-01, TR-02)" whose arguments hold `--fail-untested-through` with the value `M5` and `--manual-records` with the path `docs/phase3/verification/manual_records.json`. For the commit and nightly profiles it gives a gate named "trace matrix (TR-02)" with neither argument. The flag is on from the 0.0.2 release gate (§7). The value `M5`, the manual-record keys and the place of the index are proposed and wait for Fable (interfaces.md §3.2) |
| TR-03 | Restated 2026-10-17 (U-D20, D-055b): release gate for `verified` equations (REQ-T-05) | `record_main` with `--profile release` on fixture REQ reports and the packaged registry. A report that carries every linked test ID of every `verified` equation, each in passed records only, exits 0 and writes the file. The same report with the only carrier of one such ID marked `skipped` exits 1, writes nothing and names that equation on stderr. The same report without that carrier, so the ID is carried by no test, gives the same refusal. A `verified` equation with two linked IDs, one passed and one not carried, is refused, which catches the reading "at least one linked test passed". A linked ID of an `inferred` equation that did not pass refuses nothing, which catches a gate on every equation. When two equations are refused, stderr names both in ascending ID order. The strict xfail `test_a_verified_equation_whose_only_linked_test_did_not_pass_stops_the_release` (`tests/unit/results/test_record_passed_tests_gate.py` l.30) becomes a plain test |
| TR-05 | Evidence writer (REQ-T-05), U-M5b | on fixture REQ reports, `passed_registry_tests` passes an ID only when at least one record carries it and every carrying record passed; one skipped carrier keeps it out; an unknown eqt ID raises ValueError. `record_main` exits 1 and writes nothing for `--profile commit`, a missing report, a report with one failed record, or an unknown ID. On a valid report it writes a file that `parse_passed_tests` reads back with the same `passed_tests`, sorted keys, a `platform` value equal to `platform.platform()` and no key or value that holds `platform.node()` or the home folder path. Revision 2026-10-17 (U-D20, D-055b): the valid report of the write case carries every linked test ID of every `verified` equation of the packaged registry, because TR-03 refuses one that does not. `test_tr05_record_main_writes_a_file_the_reader_parses_back` (`tests/unit/results/test_record_passed_tests.py` l.85) passes the three EQ-10 IDs only and would then exit 1, and its summary-line assertion (l.116) changes with the counts |
| TR-06 | New 2026-10-17 (U-D19, D-053b): coverage checker (REQ-N-29), Phase 5 | Not part of any Phase 2 or Phase 3 gate, because no milestone exit in §7 names it. The design is option A of §5.8.7. The release profile's pytest gate adds `--cov --cov-report=json:build/coverage.json`, and `tools/coverage_check.py` reads `totals` from that file. `tests/unit/base/test_coverage_check.py` carries the marker REQ-N-29. 89.9 % statements fails and 90.0 % passes. 79.9 % branches fails and 80.0 % passes. A missing `percent_branches_covered` key fails. A file that is not JSON fails. A gate named "coverage (REQ-N-29)" runs after the pytest gate. The thresholds are an `assumption`, and the cost of tracing in the gate is `not tested` (§5.8.7) |
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

Revision 2026-10-13 (U-D15, claude-sonnet-5-5; main 5e74acc, `verified` by reading the files; the two tests were not
re-run, so the Result column above stays U-D14's). Both tests sit at the lines in the table: `test_evidence.py` l.202
and `test_pk03_reproducible_wheel.py` l.67. `tests/conftest.py` l.42-71 and `build_wheel` (`tests/packaging/support.py`
l.30-44) are as described above. The table needs no new ID. The first test extends the evidence reader of UT-RES-08 and
carries the marker REQ-T-05 that UT-RES-08 names. The second extends PK-03 and carries REQ-N-06, the marker the matrix
gives PK-03 (`inferred` from the markers and the rows). The PK-03 row of the next table names it. Whether either test
gets an ID of its own stays Fable's decision.

Where each packaging test runs. This container is Linux x86-64 with CPython 3.10 to 3.13 in `/usr/bin` and uv
0.8.17 (`verified` by listing, 2026-10-12). `unshare -rn` gives a process with no network (`verified`: a socket connect
returned 101, network unreachable). Anything that needs Windows is `not tested` here. The route for it is
`.github/workflows/ci.yml` with `workflow_dispatch` and the profile `release`, run by Fable. Nothing is published
without the user's approval.

| ID | Here (Linux container) | Needs Windows or the CI matrix | Owner |
|---|---|---|---|
| PK-01 | the Linux cells for 3.11, 3.12 and 3.13, with `tools/ci.py --profile commit` in one venv per version | the Windows cells. `ci.yml` lacks 3.13 and installs `.[dev]` only (interfaces.md §13 point 12) | U-M5b |
| PK-02 | yes: a clean venv per Python version installs from `requirements/py3xx.txt` with `--require-hashes`, then the wheel with `--no-deps` | the Windows resolve of the same files | U-M5b |
| PK-03 | yes: two wheel builds give the same member list and the same SHA-256 per `.py` member. The session wheel is built without the evidence file (D-045f), so the criterion has nothing to leave out; the release profile's own wheel carries the file and PK-10 checks it. Revision 2026-10-13 (U-D15): `test_pk03_the_session_wheel_leaves_out_evidence_a_release_run_left_in_the_tree` (`tests/packaging/test_pk03_reproducible_wheel.py` l.67) pins the first part | none | U-M5b |
| PK-04 | no: it compares Windows JSON with Linux JSON. The rule for hashes and arrays is below the table (revision 2026-10-17, U-D17, D-051f) | yes; `not tested` here | U-M5b sets it up, CI runs it |
| PK-05 | no: the bundle smoke test (start, compute the default example, export SVG) needs the Windows folder | yes; `not tested` here. The Linux smoke of the spec is `tests/bundle/test_bundle_smoke.py` (6 tests, labelled as a smoke of the spec only). D-046h records `6 passed` and a frozen `embodic-cli selftest` of 45 of 45 on U-M5c's Linux folder. This unit did not run them against a folder: in a tree without `build/bundle/embodic` the 6 tests skip under the commit and nightly profiles, and fail under the release profile (revision 2026-10-19, U-D24; D-068, U-M8q). `tools/ci.py` builds the folder first and sets `EMBODIC_REQUIRE_BUNDLE=1` (l.85-86 and l.104-105), and `require_bundle` in `tests/bundle/bundle_gate.py` calls `pytest.fail` when the variable is set and `embodic-cli` is missing (`verified` by reading) | U-M5c |
| PK-06 | yes, on Linux: Agent 4 follows README.md from a clean venv and times each step to a first computed example | the timed walkthrough on a clean Windows machine (REQ-N-07 acceptance), Agent 4 or the user; `not tested` here | U-V5 |
| PK-07 | yes: `unshare -rn python tools/ci.py --profile commit` passes; a static test finds no `socket`, `http.client` or `urllib.request` import in `src` | none | U-M5b |
| PK-08 | yes: the runtime closure read with `importlib.metadata` (numpy, PySide6-Essentials, shiboken6) matches the licences of §5 of `package_layout.md`; `THIRD_PARTY_LICENSES.md` has one section per runtime dependency and bundled font and the LGPL-3.0 and GPL-3.0 texts; the wheel listing shows it under `dist-info/licenses/`. pip-audit is not a dependency (§5 needs Fable's approval to add one), so the audit part is `not tested` | none | U-M5b |
| PK-10, PK-11 | yes | none | U-M5b, U-M5d |

PK-07 guard (revision 2026-10-17, U-D20, D-055d). The autouse fixture `_no_network` (`tests/conftest.py` l.45-52)
replaces `socket.socket.connect` and `socket.create_connection` with a function that raises AssertionError. On
Windows, CPython builds `socket.socketpair()` from a loopback listen and connect (D-055d), so the guard refused that
connect, and `test_n17_local_socket_pairs_still_work` failed in Windows gate 3 (D-055e). The guard admits the
connection inside `socketpair` only. The tests of `tests/static/test_n17_network_guard.py` assert four things.

1. `socket.socketpair()` returns a pair that carries bytes (l.25, exists).
2. `socket._fallback_socketpair()`, the pure-Python path that Windows uses, does the same when the test calls it
   directly. Where the module lacks that private name, the test skips and says why. CPython 3.10.20, 3.11.15 and
   3.13.13 in this container have it, and 3.12.3 lacks it. With today's guard the call raises the guard's
   AssertionError, which reproduces the Windows failure on Linux (`verified (run)`, CPython 3.11.15, 2026-10-17, a
   probe outside the repository).
3. A connect from test code to 127.0.0.1 raises the guard's AssertionError, both to a closed port (l.13, exists) and to
   a port on which the test itself listens. The second case is new and catches a guard that admits every loopback
   listener.
4. `socket.create_connection` stays refused (l.19, exists).

PK-04 rule (revision 2026-10-17, U-D17, D-051f; `docs/phase3/verification/checks/pk04_compare.py` on main 0547f20,
`verified` by reading). PK-04 compares the outcome JSON that `embodic-cli compute --json` writes for one example on two
platforms. The script refuses to compare two folders whose manifests name different embodic sources, NumPy versions or
embodic versions (l.53-56), so the comparison tests the platform and nothing else. The rule has six parts.

1. `/design_hash` compares exactly. It hashes the design only (interfaces.md §9.1), so no computed float enters it.
2. `/boards/stack_hash` and `/boards/layout_hashes` are left out. They are same-platform identities (interfaces.md §5).
3. An array compares element by element at 1e-9 relative to the largest absolute value in that array. A pair of
   elements passes when abs(a - b) is at most 1e-9 times the larger of the two arrays' largest absolute values. An
   element whose true value is 0 then passes against rounding noise that is small beside the array. An array is a JSON
   list whose elements are all numbers. A list of lists or of objects is walked element by element, and each numeric
   list inside it is an array of its own. The array definition and the scale are proposed wording of D-051f, and Fable
   confirms them.
4. A float outside an array compares at 1e-9 relative to the larger magnitude of the two values, as before.
5. Integers, other strings, booleans, null, keys and list lengths compare exactly (`pk04_compare.py` docstring l.6-9).
   The one pointer allowed to differ is `/versions/python`.
6. The DRC violation lists compare by index. Both are in the canonical order of interfaces.md §7, so the 186 wave
   violations that came out in another order on Windows (D-051f, DEF-W-01) line up.

`pk04_compare.py` applies the pair rule of part 4 to every float (l.33) and compares every string exactly (l.28-29). It
needs parts 1 to 3 and part 6. It is Agent 4's file, so the request goes through Fable (interfaces.md §13 point 14). No
unit test pins the canonical order on one platform, so part 6 is checked only by a Windows run.

Performance (PF-01 to PF-05, Phase 1 rows and §5.4) run in the release profile on this container and write
`tests/performance/baseline.json` with the machine data of `package_layout.md` §5.2. A number measured here describes a
2-CPU container and is no target for the user's laptop.

### 5.8 Rows that fail TR-01 under the release flag (revision 2026-10-17, U-D18)

`tools/ci.py` on main 7d34543 gives the release profile `untested_through="M5"` and the manual-record path (l.47 and
l.77-79, `verified` by reading), and `docs/phase3/verification/manual_records.json` holds `[]` (`verified`). A live must
row of milestone M5 or earlier with no passing test and no `passed` record therefore fails the release gate.

Reproduction. `find_untested(requirements, tests, "M5")` of `tools/trace_matrix.py`, run on the 0.0.1 release report
(`/home/claude/release_0.0.1/req_report.json`, 3125 records, main 5e74acc) and this tree's `requirements.md`, returns
REQ-N-07, REQ-N-10, REQ-T-10, REQ-T-11, REQ-L-03 and REQ-L-05. With every record under `tests/packaging` and
`tests/performance` removed, it also returns REQ-N-05 (`verified` by running it on 2026-10-17). Of the six, only REQ-T-10
carries a marker on main 7d34543, in `tests/unit/api/test_compute.py` l.192 (`verified` by grep over `tests` and
`tools`). That this test passes is `not tested` here.

| Row | Prio, M | Plan | Kind | Builds it |
|---|---|---|---|---|
| REQ-T-10 | must, M4 | LG-03 (§5.8.2). The marked JSON test is not a wording scan | product test | Agent 3 |
| REQ-T-11 | must, M4 | LG-04 (§5.8.3) and a reviewer record | product test, manual record | Agent 3; Agent 1 reviews |
| REQ-L-03 | must, M4 | LG-05 (§5.8.4) | product test | Agent 3 |
| REQ-L-05 | must, M4 | LG-06 (§5.8.5) | two product tests | Agent 3; Agent 1 names the brand files |
| REQ-N-07 | must, M5 | PK-06 record (§5.8.6) | manual record | Fable writes the record; Agent 4 adds the index entry |
| REQ-N-10 | must, M2 | option A or B (§5.8.7) | product test and gate, or a split row | Fable decides |
| REQ-N-05 | must, M5 | none (§5.8.8) | none | none |

A product test fits a row when a script can read the whole acceptance, as a string scan or a hash table does. A manual
record fits a row when the acceptance needs a person or a machine that the container lacks. REQ-N-07 needs a clean
Windows machine. The reviewer clause of REQ-T-11 needs a reader. Where a row has both, TR-01 counts the product test,
and Agent 4's `checks` ruling needs the record (interfaces.md §3.2). TR-01 stays a floor and never says `verified`.

### 5.8.1 One scanner for LG-03 to LG-06

Data shapes. A `Text` is one string that a user or a file could show. It has a corpus, a kind (`literal`, `identifier`,
`json-key`, `json-value`, `text-line` or `export-text`), a place and the text. An `AllowRule` has a class, regular
expressions over place, kind and text, a reason and one status label. The rules are data in
`tests/static/lg_allowlist.toml`, so a reviewer reads each reason beside the hit it admits. A hit is a `Text` that
matches a class pattern and no rule. A test fails with one line per hit that names the place and the text. The class
patterns are those of `tests/independent/m7/v3_14_scan.py` l.60-69, including the word-start rule that finds `MEASURED`
inside `INVALID_MEASURED_SOURCE_EMPTY` (DEF-US9-01). The product tests do not import Agent 4's file, because the
instruments stay independent (standing order 12).

Three corpora.

1. Source. Every string constant of `src/embodic/**/*.py` except bare string statements, which are docstrings. The scan
   skips the mapping keys of the string catalogues, because `"hint-combination.balanced"` is a key and not shown text
   (`ui/strings/design.py` l.218 and l.225, `inferred`). A lower-case literal with no space is an `identifier`. LG-03
   and LG-04 admit identifiers, except as a mapping value in `embodic.ui.strings`, where a one-word label such as
   "efficiency" would be shown. V3-14 admits identifiers for every class, and this plan narrows that.
2. Resources. Every text file under `resources/`: JSON by key and by value, and md, qss, svg and toml by line.
3. Exports. For each of the five packaged examples: the SVG, the three DXF files, the PDF text read with pypdf, the
   README, the ZIP bundle with each member, and `outcome_to_json` (`src/embodic/api.py` l.331). The writers are those
   that UT-EXP-01 to UT-EXP-05 call, run in `tmp_path`.

Scans 1 and 2 live in `tests/static/test_lg_wording.py`. Scan 3 lives in
`tests/unit/embodic_io/exporters/test_lg_exports.py`. Both import the scanner from `tests/static/lg_scan.py`, as the
tests under `tests/packaging` import `support.py`.

Registry text has two methods. Method (a) scans the JSON files and allows every path that the views do not show. V3-14
does this, and each "not shown" call is `inferred`. Method (b) scans the output of `equation_topic` for every equation
(`src/embodic/ui/viewmodels/results.py` l.699) and of `disclosure` for every result row of the five examples (l.220). A
registry field that no view renders is not user-facing and needs no rule. This plan proposes (b) for the two registry
files and keeps corpus 2 for every other resource. Method (a) is the fallback if rendering needs Qt, which
interfaces.md §11 says it does not (`inferred`). The disclosure draws its sources from the evidence IDs of each result
(`_source_lines`, l.190), and this unit did not trace those (`not tested`).

Controls. A scanner that skips one kind of file passes on that kind without checking it. Each class has unit tests that
plant a hit in a `.py` literal, a catalogue mapping value, a JSON key, a JSON value, an identifier word after `_` and in
camelCase, a text line, an SVG, a DXF comment, a PDF page and a ZIP member. Each class also plants an admitted text that
must pass. Each test docstring names the defect it catches.

Counts. `python3 -I docs/phase2/architecture/checks/lg_wording_probe.py` on main 7d34543 (`verified` by running it,
2026-10-17) scans the non-docstring literals of `src`, the text of `resources/` and the registry fields that the
equation guide renders. It scans no export and skips no mapping key.

| Class | src literal | src identifier | resources | guide fields |
|---|---|---|---|---|
| `measur` | 16 | 12 | 24 | 1 |
| `balanc`, `torque`, `efficien` | 11 | 38 | 30 | 5 |
| `xcoil` | 1 | 0 | 38 | 0 |
| other program name | 0 | 0 | 48 | 0 |
| e-mail address | 0 | 0 | 0 | 0 |
| home path with an account name | 0 | 0 | 3 | 0 |

### 5.8.2 LG-03 (REQ-T-10)

The acceptance is a "wording scan of strings and templates", so the scan covers all of it. The class is `measur`. The
allow-list below holds the three reasons the probe's hits fall under.

| Admitted | Where | Reason | Status |
|---|---|---|---|
| The provenance word of an input: "Measured: {source}", "Mark as measured...", "Mark as measured", "Source of the measured value (...)", "property not measured", three messages of the error catalogue, and the codes `INVALID_MEASURED_SOURCE_EMPTY` and `INVALID_MEASURED_DESIGN_FIELD` | `ui/strings/design.py` l.202 and l.267-269; `ui/strings/results.py` l.50; `errors/catalogue/base.py` l.10-12; `model/provenance.py` l.114 and l.116; `ui/viewmodels/session.py` l.846-853; `resources/themes/dark.qss` and `light.qss` l.146 | REQ-T-06 and D-007 give the word one meaning, an input that the user marked with a named source | `verified` by reading the hits |
| Advice to compare with a measurement | `io/readme_writer.py` l.21 ("Check them with a field simulation or a measurement before you build or order boards.") | advice about the user's own check, not a claim about a computed value | `verified` |
| A measurement in a cited paper, or the source of a constant | registry fields that no view renders. Under method (a): `tolerance`, `constants[].basis`, `reference_case`, `notes`, `input_provenance_*` and `assumptions_tag_rule` in `equations.v1.json`, and `entries[].applies` in `evidence.v1.json` | the Phase 1 entry "reference (paper, measured)" | `inferred` (V3-14) |

Two hits that no entry admits. The first LG-03 run reports both, and the plan admits neither.

- The name of EQ-30, "DRC clearance measurement and acceptance", at `resources/evidence/equations.v1.json` l.2847. The
  guide shows it as a title, and the probe's guide corpus holds it. The source `docs/phase2/engineering/equation_registry.json`
  l.2847 has the same text (`verified` by grep). `docs/phase3/architecture/v3_contract_rulings.md` §1 gives the change
  to Agent 2.
- `resources/fonts/FONTS.md` l.24 and l.25 ("measured with `sha256sum`", "`verified` by measuring"). The same ruling gives
  the change to Agent 3 with Agent 5.

LG-03 fails until both change. The tests catch DEF-UV8-03: a planted "Measured (mm)" catalogue value and a planted
`measured_min_mm` key in an outcome copy each produce a hit. The JSON test at `test_compute.py` l.192 stays. It checks
one document, and it gives REQ-T-10 its TR-01 test on this tree (`inferred`, not run).

### 5.8.3 LG-04 (REQ-T-11)

The class is `balanc`, `torque`, `efficien`, `imbalanc` and `unbalanc`. The scan proves one thing. Every string that
names balance, torque or efficiency is on a reviewed list. It does not prove that a sentence is true (`inferred`). D-051b
removed the claim "Balanced." and renamed two codes, and `phase-balance-status.balanced` now reads "Symmetric 3-phase
pattern." (`ui/strings/design.py` l.225, `verified`). The tests keep the claim out: a planted "Balanced." catalogue value
is a hit (DEF-UV8-04). Entries match whole strings, so a new sentence such as "Delivers high torque" is a hit.

| Admitted | Where | Reason | Status |
|---|---|---|---|
| Names of computed results: "Torque", "Torque constant per line current, rms", "Efficiency, electromagnetic only", "Torque-speed envelope", "Torque-speed", "Torque constant, star", "Torque constant, delta", `TorqueSpeedEstimate`, "The torque-speed estimate needs a DC-link voltage (Board and rotor, operating point)." | `results/labels.py` l.17, l.24, l.32, l.47; `results/__init__.py` l.46; `ui/strings/results.py` l.13, l.95, l.106; `selftest/catalogue.py` l.305, l.315 | the UI shows each result with a unit, an EQ-ID and a status badge (REQ-T-01), so the value carries its own status | `inferred` |
| A test node ID | `selftest/catalogue.py` l.235 (`...::test_cf09_patterns_and_balance`) | the name of a test function. Whether the Tests dialog shows it is `not tested` | `inferred` |
| Guide text that names a quantity or defines a pattern property | the names of EQ-09, EQ-20 and EQ-26, the validity rule of EQ-05 (it lists Ke, EMF and torque as the quantities that the add-on covers), and the formula of EQ-08 ("balance = signed angle sets of B and C equal ...") | a name or a definition, not a claim about the user's design. The word in EQ-08 is an open point (§5.8.9) | `inferred` |
| Keys and report rows of computed results in the exports | JSON keys such as `torque` and `efficiency`; PDF rows such as "Torque T ... unit status" | each belongs to a Traceable with a status label | `inferred` (V3-14) |
| Icon documentation | `resources/icons/ICONS.md` l.50 ("Torque-speed") | it names a tab of the UI, the `unresolved` torque-speed estimate (REQ-F-20) | `inferred` |

Reviewer record. The acceptance adds a "reviewer check". Agent 1 reads each admitted string where the UI shows it (the
results table, the guide and the PDF report) and records that none claims balance, torque or efficiency from geometry or
phase angles alone. The record is Markdown. It names the build and the SHA-256 of `lg_allowlist.toml`, so a change to the
list makes it stale (`assumption`). TR-01 does not need the record. Agent 4's ruling does. Interfaces.md §3.2 names Agent
4's folder and Fable's, and not Agent 1's, so the path is open.

### 5.8.4 LG-05 (REQ-L-03)

There are two classes. The first is `xcoil`, ignoring case. The second is the other program names of V3-14: kicad,
kimotor, magnetless, femm, elmer, matlab, ansys, comsol, motor-cad and pcbnew. REQ-L-03 names only Xcoil. D-051c widens
the ban to every program name in a user-facing string, so the second class makes the test stricter than the row text.
Whether `requirements.md` gets the wider wording is open (§5.8.9). Neither class admits identifiers, because a lower-case
literal "xcoil" would still be a name.

The guide corpus holds no hit in either class (probe, `verified`). The probe's guide corpus includes the `document` and
the `location` of every evidence entry that an equation cites, so no cited entry names a program either. U-E14 moved the
program name out of the formulas of EQ-14, EQ-20 and EQ-27 into `source_notes` (`equations.v1.json` `notes`, `verified`
by reading). One entry, EV-R1, holds a container path in its location, and the same corpus shows that no equation cites
it.

| Admitted | Where | Reason | Status |
|---|---|---|---|
| Board-dump schema text `name: 'xcoil-v3'` | `io/board_dump.py` l.39 | the format of the golden harness (REQ-F-40). No CLI format or UI export writes a board dump | `inferred` (V3-14) |
| The `source_note` of an example | `/example/source_note` in `resources/examples/serpentine_16p_example.embodic.json` and `wave_16p_example.embodic.json` | the code says it is never shown (`io/examples.py` l.39, `verified`). The exports corpus has to show 0 hits for all five examples before the entry stands | `inferred` until the export scan runs |
| Registry fields that no view renders, and the sources they cite | under method (a): `equations.v1.json` `notes`, `golden_tolerance_default`, `tolerance`, `source_notes`, `changes`, `constants[].basis`, `reference_case`; `evidence.v1.json` `topology_vocabulary`, `documents`, `entries[].claim`, `entries[].source` and `entries[].applies` | not rendered. The 38 `xcoil` and 48 other-program hits of the probe all sit here or in the two example files | `inferred` (V3-14) |

### 5.8.5 LG-06 (REQ-L-05)

The acceptance is "asset checksums; personal-name scan = 0". Two tests in `tests/static/test_lg_brand_and_names.py`
implement it, one for each half.

Brand assets.

- `tests/static/brand_assets.sha256` lists the SHA-256 and the file name of each brand original. It holds hashes only, and
  no asset is copied. The test never reads `/mnt/user-data/uploads`, because CI and the Windows laptop lack it. Regenerate
  the table with `sha256sum` over the brand folder.
- The rule is V3-14's `brand_check`, applied to every tracked image file of the checkout. An image whose hash is in the
  table passes. An image whose stem equals a brand stem, or matches `logo`, `wordmark` or `embodic-symbol`, and whose
  hash is in no row fails.
- The brand folder holds 8 files on 2026-10-17. Five are embodic images, two are `exec-*.png` and one is named `logo`
  with no extension. The four brand PNGs under `docs/phase1/design/mockups/brand/` have the same SHA-256 as their
  originals (`verified` by `sha256sum` over both folders), so the scan of the real tree has four files to check. A search
  of `src`, `resources` and `packaging` for `.png`, `.ico`, `.icns` and `.jpg` finds only
  `resources/icons/_contact_sheet.png` (`verified`), so the shipped package holds no brand image. The planted controls,
  one exact copy and one modified copy, show that the test can fail.
- Which of the eight files are brand assets is open. `docs/PROJECT_BRIEF.md` l.39 lists the logo, the white variants, the
  symbol, the wordmark and the sub-brand logo. V3-14 hashes all eight. Until Agent 1 names them, the table lists the five
  embodic images.

Personal data.

- Two patterns. An e-mail address, and a home path (`C:\Users\<name>`, `/home/<name>` or `/Users/<name>`) whose name is
  not a placeholder (`user`, `username`, `you`, `name`, `runner`, `me`) and not the build account `claude`.
  `%USERPROFILE%` and `<user>` never match (`v3_14_scan.py` l.77-79).
- Tokens come from the run environment: the committer name and address of the checkout (`git config user.name` and
  `user.email`) and the OS account (`getpass.getuser()`), less the placeholders, at least 3 characters, matched as whole
  words ignoring case. No token is written into the repository (standing order 7).
- With no token, the release profile fails and the other profiles skip. The test cannot tell the release profile from
  the nightly one, because both set `EMBODIC_HYPOTHESIS_PROFILE=nightly` (`tools/ci.py` l.46-47). The release profile
  needs its own environment variable for this. `v3_contract_rulings.md` §2 calls the whole design an `assumption` that
  Agents 3 and 4 settle.
- The corpus is the code (`src`, `tools`, `tests`, `packaging`), `resources/` and the exports. REQ-L-05 lists "code, UI,
  logs or outputs". The log test UT-LOG-01 is not built (REQ-N-20, `not tested`), so logs are outside this test.
- The probe finds no e-mail address and three home paths, all `/home/claude/embodic-ref/...` in `evidence.v1.json`: two
  document paths and the location of EV-R1. `claude` is the build account and not a person (V3-14 `BUILD_ACCOUNTS`), so
  the allow-list admits it with that reason (`inferred`).
- A token scan finds only the names that the machine knows. A name that appears elsewhere, such as the one in the pitch
  deck (`docs/PROJECT_BRIEF.md` l.40), stays a reviewer's job (`inferred`).

### 5.8.6 REQ-N-07: manual record of PK-06

The record is manual. The acceptance reads "timed walkthrough on a clean Windows machine by Agent 4 or the user". No
script runs that machine, and the Linux walkthrough of §5.7 is not it. The elapsed time also depends on the user's
network, which `windows_campaign_w1.md` l.9-10 measured at about 0.03 MB/s.

The record file is `docs/phase3/fable/windows_campaign_w1.md`. It holds no account name (`verified` by reading; it uses
`%USERPROFILE%`). Interfaces.md §3.2 puts a campaign record by Fable under `docs/phase3/fable/`. The entry for
`docs/phase3/verification/manual_records.json`, which Agent 4 owns, has the five keys of §3.2. Fable supplies `result`.

```json
[
	{
		"req": "REQ-N-07",
		"test_id": "PK-06",
		"record": "docs/phase3/fable/windows_campaign_w1.md",
		"embodic_version": "0.0.1",
		"result": "passed or failed, by Fable's ruling"
	}
]
```

What the record says, `verified` by reading it. Run 1 reached the first computed example after 4154.54 s, of which the
lock-file step took 4137.15 s, 99.6 % (l.29 and l.33). Without the download the steps took about 17 s (l.38-39). Run 2
used a warm pip cache, a new folder and a new venv, and reached the example after 21.57 s (l.64-67). Python 3.11.9 came
from the NuGet package first, in 58.1 s (l.13).

The file does not say `passed` or `failed` in one line. Three readings are open.

1. `failed`. Run 1 is closer to a clean run, since only numpy came from the user's pip cache (l.29), and it missed 10
   minutes. The row stays red until a clean Windows run meets the time. The 0.0.2 gate then waits for that run.
2. `passed` on run 2. The time is met, but the pip cache was warm, so the machine was not clean. This changes the
   acceptance without saying so, and the plan does not offer it.
3. Change the acceptance in the open: "less than 10 minutes, not counting the time pip spends downloading, which the
   record reports apart". Both runs then pass. The change needs a revision note in `requirements.md`, and Fable decides.

Three gaps in the file against §3.2, all in Fable's own file. It names no wheel SHA-256 (it gives the package source
hash `cfefe405…baae` at l.44, and the V3-14 header gives the release wheel hash `f114a6e7…dcd0`, `verified` by reading).
It has no verdict line. Its performer is Fable on the user's laptop, and the acceptance names Agent 4 or the user. The
script counts the record whatever the performer and whatever `embodic_version` it names (interfaces.md §13 point 14).
INSTALL.md changes in 0.0.2 (DEF-W-04, D-051g), so a 0.0.1 record certifies a guide that is about to change. A 0.0.2
re-run on the laptop would close that, and Fable decides whether the gate needs it.

### 5.8.7 REQ-N-10: coverage or acceptance text

Facts.

- The statement has two clauses. The first sets coverage at 90 % lines and 80 % branches, both thresholds an `assumption`.
  The second says that every REQ-ID has a test. Phase 1 maps the row to TR-01 alone (`test_plan_draft.md` l.393), and
  TR-01 reads only the second clause. No test carries REQ-N-10 (`verified` by grep over `tests` and `tools`), and Agent 4's
  audit rules the row `does not check` (`docs/phase3/verification/req_audit.md`).
- `coverage` 7.16.2 and `pytest-cov` 7.1.0 are hash-pinned in `requirements/py311-dev.txt` (l.76 and l.841) and at the same
  lines of `py312-dev.txt` and `py313-dev.txt`. `pyproject.toml` l.28 allows `pytest-cov>=7,<8` (`verified` by reading).
  `[tool.coverage.run]` sets `source = ["embodic"]` and `branch = true`, and omits `ui/views/*`, `ui/app.py` and
  `ui/workers.py` (l.102-105). No `[tool.coverage.report]` section exists, and no gate passes `--cov` (`tools/ci.py`
  l.63-65).
- The row does not define "core". The omit list is the only definition in the tree (`inferred`). coverage.py counts
  statements, and the row says lines.
- In coverage.py 7.16.2, `percent_covered` is (executed statements + executed branches) / (statements + branches)
  (`coverage/results.py` l.377-381), so one `fail_under` cannot hold two thresholds. The JSON report always has
  `totals.percent_statements_covered`, and it has `totals.percent_branches_covered` only when branch data exist
  (`coverage/jsonreport.py` l.45-100). Both are `verified` by reading the copy in `/home/claude/embodic/.venv`. The
  statement in `v3_contract_rulings.md` §2 point 5 was an `assumption`, and it holds.
- D-051e puts the coverage step in Phase 5, and interfaces.md §3.2 adds no coverage gate. D-052a records a commit gate that
  the container's memory limit killed at 4.5 GB after 2.7 h, where earlier gates took about an hour. The cost of tracing
  is `not tested`.
- The acceptance asks for "0 untested live REQs", and TR-01 checks must rows only. On the 0.0.1 report, 12 of 93 live rows
  have no passing test: the six above and REQ-F-30, REQ-N-20, REQ-T-12, REQ-L-02, REQ-L-06 and REQ-L-09 (`verified` by
  running the parser functions of `tools/trace_matrix.py` over every live row, 2026-10-17).

Option A lands the coverage step now.

1. The release profile's pytest gate adds `--cov --cov-report=json:build/coverage.json`. The config already sets `source`
   and `branch`.
2. `tools/coverage_check.py` reads `totals` and exits 1 below 90 % statements or below 80 % branches. It also exits 1 when
   `percent_branches_covered` is missing, so a run without branch data cannot pass.
3. `tests/unit/base/test_coverage_check.py`, marker REQ-N-10. 89.9 % statements fails and 90.0 % passes. 79.9 % branches
   fails and 80.0 % passes. A missing branch key fails. A file that is not JSON fails.
4. A gate named "coverage (REQ-N-10)" runs after the pytest gate.

Option A makes the first clause measured and enforced. It overrules D-051e. The first run may miss a threshold that is only an
`assumption`, and the 0.0.2 gate would then wait on a number nobody has measured (`not tested`). The gate also grows in
time and memory after it hit the container's limit. The unit test proves the checker, and only the gate proves the
numbers.

Option B splits the row now and lands coverage in Phase 5.

1. REQ-N-10 keeps the second clause. Proposed statement: "Every REQ-ID has at least one automated test or documented
   manual test." Proposed acceptance: "0 untested live must REQs (TR-01); the matrix lists the untested should and could
   rows."
2. A new row, `should`, holds the first clause with its thresholds labelled `assumption`. It needs a test ID defined in
   this plan, and U-D18 allocates none, because Fable has not chosen B. The next free ID in the TR series is TR-06.
3. The marker REQ-N-10 goes on the tests of `tests/unit/base/test_tr01_release_gate.py` that exercise the second clause.
   They already carry REQ-T-09, and a test may carry several markers, as PK-02 carries REQ-N-05 and REQ-N-06. The three
   candidates are `test_tr01_flag_lists_a_live_must_row_that_has_neither_a_passing_test_nor_a_manual_record`,
   `test_tr01_release_gate_fails_on_an_untested_must_row` and
   `test_tr01_release_gate_passes_when_a_manual_record_covers_the_row`.
4. `tools/trace_matrix.py` prints the untested should and could rows, with a unit test marked REQ-N-10.

Option B leaves D-051e alone and keeps the gate inside its resources, and no row claims coverage that nobody measured. It
cuts a must requirement to a should for its coverage clause, so Fable decides whether the user must approve it
(`assumption`).

Option C is a marker on any test. It makes TR-01 pass over an unmeasured clause, and the plan rejects it.

This unit proposes B now and A in Phase 5 with the four pieces above, so that unit has no design left. Fable decides.

Decided 2026-10-17 (D-053b, written in by U-D19). Option B. REQ-N-10 keeps the second clause with the acceptance "0 untested
live must REQs (TR-01)", and REQ-N-29 holds the coverage clause for Phase 5 with TR-06 as its test. Option A's four pieces
are the design of TR-06 and need no new decision. Option B item 3, the marker REQ-N-10 on the TR-01 gate tests, and item
4, the printout of untested should and could rows, are code work that this unit did not do. Item 4 is not in the
acceptance (requirements.md revision of U-D19).

### 5.8.8 REQ-N-05

`tests/packaging/test_pk02_clean_install.py` carries REQ-N-05 (l.23 and l.32). The release profile ignores only
`tests/packaging/evidence` (`tools/ci.py` l.47), so it runs PK-02 and the row has passing tests. The commit and nightly
profiles ignore `tests/packaging` (l.29, l.45 and l.46), and they do not pass the flag, so they never judge the row.
`test_tr01_commit_and_nightly_gates_leave_an_untested_must_row_unlisted`
(`tests/unit/base/test_tr01_release_gate.py` l.251) pins that. The row needs no new test and no record. The flag has to
stay out of the commit and nightly profiles, because turning it on there lists REQ-N-05 (§5.8, reproduction). The Windows
cells of PK-01 stay `not tested` (§7), and PK-02 on Linux is what TR-01 counts.

### 5.8.9 Open for Fable

1. REQ-N-10: decided, option B (D-053b, §5.8.7). Open: option B item 4 and the Phase 5 value of the milestone column.
2. REQ-N-07: the `result` value, whether run 1 or run 2 counts or the acceptance changes, whether a 0.0.2 re-run is
   needed, and whether Fable's run meets "by Agent 4 or the user" (§5.8.6).
3. Which of the eight brand files are brand assets, and the environment variable that makes the personal-data test fail
   without a token in the release profile (§5.8.5).
4. Where Agent 1's reviewer record for REQ-T-11 lives, and whether Agent 2 rewords "balance" in the EQ-08 formula to
   "symmetry" (§5.8.3).
5. Whether REQ-L-03 in `requirements.md` names the other programs of D-051c (§5.8.4).
6. Whether the registry is scanned as rendered text (method (b)) or by path (method (a)) (§5.8.1).

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

From the 0.0.2 release gate on, the release profile enforces TR-01 through M5 (revision 2026-10-17, U-D17, D-051e; TR-01
in §5.7). The commit and nightly profiles do not. A must row that has no passing test and no `passed` manual record then
fails the gate.

Revision 2026-10-17 (U-D18). The M5 exit counts the PK-06 walkthrough on Windows through a manual record in
`docs/phase3/verification/manual_records.json`, and not through a test (§5.8.6). The M4 exit already names every LG test,
so LG-03 to LG-06 add no ID to it. Fable chose option B of §5.8.7 for REQ-N-10 (D-053b, U-D19 revision), and TR-01 counts its must half. Until each row of
§5.8 has a passing test or a `passed` record, the release gate fails on it.

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
| REQ-F-05 | amended | must | M2 | embodic.generators.spiral | UT-GEO-13, UT-PHY-11, PR-01, UT-GEN-06 |
| REQ-F-06 | carried | must | M2 | embodic.generators.spiral | UT-GEO-07, UT-GEO-08, UT-GEO-09, UT-GEO-17, UT-GEO-18, UT-GEO-25, OR-04 |
| REQ-F-07 | carried | must | M2 | embodic.physics | UT-PHY-01, UT-PHY-02, UT-PHY-04, UT-PHY-14 |
| REQ-F-08 | carried | must | M2 | embodic.generators.spiral | UT-PHY-09, UT-WND-07 |
| REQ-F-09 | carried | should | M2 | embodic.geometry | UT-GEO-14, UT-DRC-06, UT-EXP-02 |
| REQ-F-10 | carried | must | M1 | embodic.drc | UT-DRC-01, UT-DRC-02, UT-DRC-03, UT-DRC-04, UT-DRC-05, UT-DRC-08, PR-01, PR-02, PR-13, GR-18 |
| REQ-F-11 | carried | must | M2 | embodic.physics | UT-PHY-05, UT-PHY-06, UT-PHY-10, UT-PHY-12, UT-PHY-15, UT-PHY-16, UT-PHY-17, UT-PHY-18, UT-PHY-19, GR-02, GR-03, GR-04, GR-09, GR-11, GR-13, OR-01, OR-11, OR-12, UT-PHY-22, UI-07 |
| REQ-F-12 | carried | must | M2 | embodic.physics | UT-PHY-08, UT-PHY-20, GR-05 |
| REQ-F-13 | carried | must | M4 | embodic.ui.views | UI-02, UI-03, UI-04, UI-06 |
| REQ-F-14 | amended | must | M2 | embodic.model | PR-05, BV-01, BV-02, BV-03, BV-05, BV-06, BV-21, UT-DRC-09, UI-14 |
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
| REQ-L-01 | amended | must | M4 | embodic.ui.strings | LG-01, LG-08 |
| REQ-L-02 | amended | should | M4 | embodic.ui.strings | LG-02 |
| REQ-L-03 | carried | must | M4 | embodic.ui.strings | LG-05 |
| REQ-L-04 | amended | must | M4 | resources/themes | AX-01, AX-05, AX-08 |
| REQ-L-05 | carried | must | M4 | resources/icons | LG-06 |
| REQ-L-06 | carried | should | M4 | embodic.ui.strings | LG-07 |
| REQ-L-07 | carried | must | M2 | embodic.results | UT-UNI-03 |
| REQ-L-08 | carried | must | M4 | embodic.ui.views | UI-34 |
| REQ-L-09 | amended | should | M4 | embodic.ui.strings | LG-07 |
| REQ-N-01 | carried | must | M5 | embodic.api | PF-01, PF-04 |
| REQ-N-02 | amended | must | M4 | embodic.ui.workers | UI-05, UI-02, UI-36, UI-37, UI-38, UI-39, UI-40, UI-41, UI-42, UI-43, UI-44, UI-45 |
| REQ-N-03 | carried | should | M5 | embodic.api | PF-02 |
| REQ-N-04 | carried | must | M2 | embodic.physics | PR-09, PK-04, MT-06 |
| REQ-N-05 | carried | must | M5 | pyproject.toml | PK-01, PK-02 |
| REQ-N-06 | amended | must | M5 | pyproject.toml | PK-03, PK-05, PK-10, PK-11 |
| REQ-N-07 | amended | must | M5 | docs | PK-06 |
| REQ-N-08 | amended | must | M1 | pyproject.toml | MT-01, MT-02, MT-03 |
| REQ-N-09 | carried | must | M2 | embodic.physics | MT-04 |
| REQ-N-10 | amended | must | M2 | tools/trace_matrix.py | TR-01 |
| REQ-N-11 | carried | must | M4 | resources/themes | AX-01 |
| REQ-N-12 | carried | must | M4 | embodic.ui.views | AX-02, AX-03, UI-46, UI-47, UI-48, UI-49, UI-50, UI-51, UI-52, UI-53, UI-54, UI-55, UI-56, UI-57 |
| REQ-N-13 | carried | must | M4 | embodic.ui.views | AX-04 |
| REQ-N-14 | carried | must | M4 | embodic.ui.views | AX-05 |
| REQ-N-15 | amended | must | M4 | embodic.ui.views | UI-09 |
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
| REQ-N-29 | new | should | M5 | tools/coverage_check.py | TR-06 |
| REQ-T-01 | carried | must | M4 | embodic.ui.views | UI-06, AX-02 |
| REQ-T-02 | carried | must | M2 | embodic.results | UT-RES-01 |
| REQ-T-03 | carried | must | M2 | embodic.results | UT-RES-02, UT-RES-05 |
| REQ-T-04 | carried | must | M2 | embodic.results | UT-RES-03, TR-04 |
| REQ-T-05 | amended | must | M2 | embodic.results | TR-03, UT-RES-02, UT-RES-08, UT-RES-09, TR-05 |
| REQ-T-06 | amended | must | M2 | embodic.model | UT-RES-06, UT-MOD-05 |
| REQ-T-07 | amended | must | M4 | embodic.io | UT-IO-06 |
| REQ-T-08 | amended | must | M2 | embodic.physics | UT-PHY-13, UT-PHY-21 |
| REQ-T-09 | carried | must | M1 | tools/trace_matrix.py | TR-01, TR-02 |
| REQ-T-10 | carried | must | M4 | embodic.ui.strings | LG-03 |
| REQ-T-11 | carried | must | M4 | embodic.ui.strings | LG-04 |
| REQ-T-12 | carried | should | M4 | embodic.ui.views | UI-13 |
| REQ-T-13 | carried | must | M4 | embodic.ui.views | UI-06 |
| REQ-T-14 | amended | must | M4 | embodic.io | UT-IO-06, UI-32 |
| REQ-T-15 | new | must | M2 | embodic.model | UT-MOD-04, UT-IO-07, PR-12 |
| REQ-T-16 | new | must | M2 | embodic.results | UT-RES-07, UI-33 |

<!-- matrix:end -->
