Prepared by Agent 2 (Motor Design), model claude-opus-5-5. Unit U-E18, 2026-10-17, decision D-056 a.

# Fix wave F2: REQ-T-05 rulings for EQ-06 and EQ-22, and the EQ-17 and EC-05 texts

REQ-T-05 now refuses a release when a `verified` equation has a linked test that did not pass
(`Registry.tests_passed`, `src/embodic/results/registry.py` l.150-153; `tools/record_passed_tests.py` l.145-152). On the
0.0.1 evidence it names EQ-06 and EQ-22. This document rules on both, and writes the two registry texts that U-E17 left
as Follow-up 1 (`docs/phase3/engineering/fix_wave_f1.md` l.306-311, item 1).

## How to rerun

```
PYTHONPATH=src:.:tests/golden python3 docs/phase3/engineering/checks/f2_req_t05.py --evidence PATH
```

PATH is a `passed_tests.v1.json` from a release build. This unit used the copy inside the 0.0.1 wheel, build
`0.0.1+g5e74acc4e79b.20261012T212510Z` (git 5e74acc, not dirty, 52 passed IDs). The script runs no test suite. It
reads test decorators, applies the REQ-T-05 predicate, recomputes EQT-22-GR, and computes the D08 example under four
registry variants. It took about 7 s.

## Summary

| Item | Ruling | Registry change | Status |
|---|---|---|---|
| EQ-06 | Status `verified` to `inferred`. All five test links stay. | `status` | inferred (ruling); the facts it rests on are verified (ran or read) |
| EQ-22 | Status and link stay. The missing carrier exists on main. | none | verified (ran) |
| EQ-17 | `P_loss` and `A_board` texts per D-056 i | `variables[0]`, `variables[2]` | verified (read: D-056 i, fix_wave_f1.md §C) |
| EC-05 | New field `consequences_basis` names the Phase 1 segment set | `consequences_basis` | verified (read: fix_wave_f1.md §B) |
| Chains | DEF-UE18-01: EMF-derived results omit EQ-05 and EQ-07 from their chain | none (code) | verified (ran) for the badges |

## A. EQ-06: the status moves to `inferred`, the links stay

### A.1 What REQ-T-05 sees

Script output, Parts 1 and 2 (`verified`, ran):

```
EQT-06-O2: tests/unit/physics/test_oracles_m5.py::test_or07_d09_phase_emf_within_the_registry_band l.246 gated by ['xfail']
Part 2. evidence 0.0.1+g5e74acc4e79b.20261012T212510Z, 52 passed IDs; REQ-T-05 refuses ["EQ-06 (not passed: ['EQT-06-O2'])", "EQ-22 (not passed: ['EQT-22-GR'])"]
```

EQT-06-O2 has one carrier, OR-07. It is a strict xfail on the pre-registered builds A and B (+18.7 % and −7.4 %
against D09's 6.21 V, D-045 a). The report records an xfail as `skipped`, so the ID never passes
(`docs/phase2/engineering/eqt_map_review.md` §d). Variant C, read from D09 Fig. 1a, is out of band by 0.09 points
against the measured 6.22 V (D-050 c; `docs/phase3/engineering/engineering_verification_plan.md` l.140-186). The band is
never widened (D-045 a).

### A.2 Why the link stays

- The registry links a literature oracle to each equation it exercises. OR-01 (D08) carries EQT-05-O1, EQT-06-O1 and
  EQT-09-O1 (`tests/unit/physics/test_oracles.py` l.90). OR-07 (D09) carries EQT-05-O2 and EQT-06-O2
  (`test_oracles_m5.py` l.238). OR-07's own docstring names the EMF chain EQ-05, EQ-06 and EQ-09 as what it catches.
- D-046 c makes a marker an all-or-nothing claim, and U-E10 found this marker correct: "The markers are right and stay"
  (`eqt_map_review.md` §d).
- Unlinking EQT-06-O2 alone would keep the passing D08 oracle on EQ-06 and drop the failing D09 oracle. That selects
  evidence by its outcome. I reject it.

### A.3 Why the status moves

An equation is not `verified` by a case that fails (brief U-E18, D-050). With the link kept, the only status that is
true to the evidence is the next one down.

What still supports EQ-06 (`verified`, read in the registry and the 0.0.1 evidence):
- EQT-06-CF02 and EQT-06-CF03 pass. The kernel reproduces the closed form at 1e-9 and the EQ-05 field case at 1e-5
  (`docs/phase2/engineering/equation_specification.md` l.169-172).
- EQT-06-GR passes against Xcoil at 1e-9. EQT-06-O1 passes against D08's measured Ke.
- The F-OR07 diagnosis found the chain arithmetic exact (H1) and the field side worth at most 3 points. The geometry
  levers move the result by 5 to 13 points (`engineering_verification_plan.md` l.51, l.111-114).

So the cause of F-OR07 most likely lies in the D09 coil geometry, not in the EQ-06 kernel. That cause is `inferred`, not
shown. The second literature case still fails, and `inferred` says exactly that.

EQ-06 returns to `verified` when OR-07 passes on a build that matches D09 and Agent 3 removes the xfail
(`eqt_map_review.md` §d, "What closes F-OR07"). DEF-UE18-01 must be fixed first (section A.5).

### A.4 Effect on the badges

Part 4 computes the D08 example (`resources/examples/spiral_12c10p_d08.embodic.json`). The passed IDs are the 0.0.1
evidence plus EQT-22-GR. Every result whose chain holds EQ-06 is printed (`verified`, ran). Excerpt:

```
  V0 0.0.1 registry | V1 ruling: inferred, O2 linked | V2 verified, O2 unlinked | V3 V0 once OR-07 passes
  emf_phase_rms            [EQ-06,EQ-07] not tested | not tested | inferred | inferred
  ke_phase_v_s_per_rad     [EQ-06,EQ-07,EQ-05] not tested | not tested | not tested | inferred
  kt                       [EQ-09,EQ-06] not tested | not tested | verified | verified
  torque                   [EQ-09,EQ-06] not tested | not tested | verified | verified
  V1 ruling: inferred, O2 linked: 0 of 19 badges differ from V0
  V2 verified, O2 unlinked: 13 of 19 badges differ from V0
  V3 V0 once OR-07 passes: 14 of 19 badges differ from V0
```

The ruling (V1) changes no badge: EQ-06's test state stays `not tested` while EQT-06-O2 fails. With the ruled registry
and EQT-22-GR passed, REQ-T-05 refuses no equation (Part 2, second line: "REQ-T-05 refuses none"). The rejected
alternative (V2) would show `verified` on `ke_line`, `kt`, `kv`, `output_power` and `torque`.

### A.5 Defect found: EMF-derived results omit EQ-05 and EQ-07 (DEF-UE18-01)

`analyse()` forms `ke1` from the phase EMF phasors that `solve_phase_circuit` assembles (EQ-07) from the flux linkage of
each path (EQ-06 in the EQ-05 field), then derives `ke_line`, `kt` and `kv` from `ke1` (`src/embodic/physics/analyse.py`
l.288-303, `verified`, read). `ke_phase` lists the chain EQ-06, EQ-07, EQ-05 (l.431). `ke_line`, `kt`, `kv` and
`torque` list only EQ-09 and EQ-06, and `output_power` lists EQ-26, EQ-09 and EQ-06 (l.524-563). ADR-0003's worked
example, pinned in `tests/unit/results/test_traceable.py` l.45, gives Ke the chain EQ-06, EQ-04, EQ-05, EQ-07, EQ-09.
The `traced` docstring says the tag of a result covers its whole chain (`src/embodic/results/traceable.py` l.110-112).

Consequence (V3, `verified`, ran): once OR-07 passes, those five results read `verified` while EQ-05 and EQ-07 are
`inferred`. A `verified` torque badge would then rest on an `inferred` field model. Today EQ-06's `not tested` state
hides it. That this is a defect against the badge rule is `inferred`, because `result_badge_rule` does not say whether
"the chain" includes the equations of intermediate results.

| ID | Defect | Reproduce | Owner |
|---|---|---|---|
| DEF-UE18-01 (major, latent) | On the D08 example 18 of the 19 results with EQ-06 in `eq_ids` lack EQ-05 (all but `ke_phase`), and 12 of them also lack EQ-07 (`kt`, `kv`, `torque`, `ke_line`, `ke_line_peak`, `output_power`, `motor_constant`, `thd_phase`, `thd_line`, `emf_waveform`, `loss_delta_circulating`, `utilisation_factor_k_u`). Their badge ignores both `inferred` equations | Run the script; Part 4 column V3 shows `kt`, `torque`, `kv`, `ke_line`, `output_power` as `verified` | Agent 3 (chains in analyse.py), Agent 6 (state in `result_badge_rule` that a chain includes the chains of the intermediate results it uses) |

Test spec for Agent 3 (UT, `tests/unit/physics/`): compute the D08 example; for every Traceable whose `eq_ids` holds
EQ-06, assert that `eq_ids` also holds EQ-05 and EQ-07. Defect caught: DEF-UE18-01. A second assertion with
`with_all_tests_passed` asserts that `torque.status` is not `verified` while EQ-05 is `inferred`.

### A.6 A paired change outside this unit's write scope

`docs/phase2/engineering/checks/check_consistency.py` compares the specification's status table with the registry. After
this change it prints (`verified`, ran):

```
FAIL
  - EQ-06: status table 'verified' vs registry 'inferred'
```

Two lines of `docs/phase2/engineering/equation_specification.md` need the same ruling: the status table row "06, 10"
(l.669) splits into "10 | verified" and EQ-06 joins the `inferred` row with the reason "D09 oracle OR-07 fails (F-OR07)",
and the EQ-06 section (l.174, "Status: verified") reads "Status: inferred". That file is Agent 2's, but this brief limited writes to two
files.

## B. EQ-22: status and link stay

The 0.0.1 evidence was built on 5e74acc on 2026-10-12. U-M7b added the EQT-22-GR carrier later, under V3-01 gap F11-1
(`tests/independent/m7/records/V3-01_gaps_a.md` l.63-77; `/root/.claude/orchestrate/embodic/reports/U-M7b.md`: "14 pass + 3 strict xfails"). On main b977621
the carrier is `test_current_density_of_the_mapped_layout_matches_xcoil` in
`tests/golden/m2_physics/test_gr_f11_mass_thermal_current.py` l.147-157, with no xfail or skip (Part 1).

Part 3 reproduces its comparison without pytest (`verified`, ran):

```
  sector-default: embodic 28.73563218390805 A/mm2, Xcoil 28.73563218390805 A/mm2, rel 0.00e+00 (pass)
  serpentine-default: embodic 28.73563218390805 A/mm2, Xcoil 28.73563218390805 A/mm2, rel 0.00e+00 (pass)
  wave-turns-2: embodic 28.73563218390805 A/mm2, Xcoil 28.73563218390805 A/mm2, rel 0.00e+00 (pass)
```

The test spec, already met by the existing test:

| Field | Value |
|---|---|
| Inputs | The params of the m1_layout fixtures `layout-sector-default`, `layout-serpentine-default` and `layout-wave-turns-2`, mapped into embodic and run through `analyse()` |
| Expected | Xcoil's `currentDensity` from `tests/golden/data/mass_thermal/connection-<tag>.json` (dumped by `tools/golden/dump_xcoil.mjs`, star connection) |
| Derivation | J = I_ph/(a·w·t) (EQ-22, a definition, EV-49). The registry reference case gives 1.0/(1·0.5·0.0348) = 57.4712643678 A/mm² (arithmetic, `verified`) |
| Tolerance | rel 1e-12, the KERNEL class (`tests/golden/harness/compare.py` l.37). Same formula and operands, so only rounding differs |
| Defect caught | J from the wrong width or thickness, or from the line current instead of the phase current |

The 0.0.2 evidence must come from a release run on a tree that holds this file. No registry change is needed.

Observation (`inferred`, not tested): the three cases give the same J. If their tracks have one width, the cases do not
separate the narrowest width from another width. A fourth case with unequal widths would. This is a suggestion for
Agent 4, not a defect.

## C. EQ-17 variable texts

D-056 i rules that a stack cools through its two outer faces (2·A_1), with the status `inferred` and the assumption of an
unventilated board gap. The registry variables now read:

- `P_loss` (W): "total loss of all boards" (was "total loss").
- `A_board` (m²): "face area of one board; a stack cools through its two outer faces" (was "board area per face").

The formula, status, gate, tests and tolerance of EQ-17 are unchanged. The specification line l.396 still reads
"A_board [m²]" without the clarification. That is a follow-up for the same reason as A.6.

## D. EC-05 `consequences_basis`

The `consequences` values 0.053, 0.042 and 0.058 are the Phase 1 values of `docs/phase1/engineering/checks/edge_zone_d09.js`
on an idealised segment set (`fix_wave_f1.md` §B.2, `verified` for the values). The numbers stay in `consequences` so the
field keeps its number type. A new sibling field, named like `threshold_basis` and `transfer_basis`, says what they
describe:

> Phase 1 idealised segment set: one radial line over the coil annulus within the magnet span at z = G
> (docs/phase1/engineering/checks/edge_zone_d09.js l.34-56); recomputed from the metric 0.05328140, 0.04208834,
> 0.05788521 (docs/phase3/engineering/fix_wave_f1.md section B.4); not the value on generated layouts, which sum the
> chords of the built coil at each copper layer

`_parse_check` reads neither field (`src/embodic/results/registry.py` l.443-477), so the product does not change.

## Registry revision and checks

A structural diff of the edited `docs/phase2/engineering/equation_registry.json` against
`resources/evidence/equations.v1.json` shows exactly five changes (`verified`, ran):

```
key /equations/4/validity_checks/0/consequences_basis only in new
val /equations/5/status 'verified' -> 'inferred'
val /equations/16/variables/0/meaning 'total loss' -> 'total loss of all boards'
val /equations/16/variables/2/meaning 'board area per face' -> 'face area of one board; a stack cools through its two outer faces'
len /notes 12 13
```

`load_registry` on a copy of the edited file returns EQ-06 `inferred` with its five tests, EQ-22 `verified` with
EQT-22-GR, and the same eight `INTERNAL_REGISTRY_EQUATION_UNSOURCED` issues as the shipped copy (`verified`, ran). The
new note is "v1.0 rev. U-E18". Fable runs `tools/sync_registry.py` after the merge, which also regenerates the examples
(D-056 b).

## Follow-ups

1. Agent 3: fix DEF-UE18-01 and add the test of A.5 before any ruling returns EQ-06 to `verified`.
2. Agent 6: state in `result_badge_rule` that a chain includes the chains of the intermediate results it uses.
3. Agent 2 (a later unit with write scope): the `equation_specification.md` lines of A.6 and section C, so that
   `check_consistency.py` passes again.
4. Agent 4: a fourth EQT-22-GR case with unequal track widths (section B observation).

## Open questions for Fable

1. Do you accept `inferred` for EQ-06 over the rejected alternative (V2)? V2 would require Agent 3 to drop EQT-06-O2
   from the OR-07 marker, or `record_main` refuses the run ("carries 'EQT-06-O2', which the registry does not link",
   `tools/record_passed_tests.py` l.65). It would also show five `verified` badges until DEF-UE18-01 is fixed.
2. Should the A.6 specification edit join this merge, so that main never holds a failing `check_consistency.py`?
