Prepared by: Agent 6 - Software Architecture Specialist - model: claude-opus-5-5

# U-D26: UT-GEO-19, UT-PHY-11, the scope of REQ-N-09 and the TR-01 currency rule (D-083)

Unit U-D26, 2026-10-20, on main fcd050b (worktree `/home/claude/wt/U-D26`, branch `unit/U-D26`). The contract text is
in `docs/phase2/architecture/test_plan.md` (the revision note of 2026-10-20, §5.1 UT-GEO-19 and UT-PHY-11, §5.4 MT-04)
and in `docs/phase2/architecture/interfaces.md` §3.2 (currency of a manual record). This file gives the reasons, the
measurements and the questions for Fable. `requirements.md` does not change. No code or test changed.

Status words follow standing order 12. `verified` means read at the named line on main fcd050b, or reproduced by running
a probe on this Linux container (CPython 3.11.17 and numpy 2.4.6 of the dev venv of `/home/claude/embodic`, with
`PYTHONPATH=src` from the worktree, so `embodic` imports from the worktree; the probe gave the same values on the system
CPython 3.13.16). Nothing here ran on Windows. No test suite ran, so any statement that a test passes is `not tested`.

| Item | Ruling in one line |
|---|---|
| 1a. UT-GEO-19 | Restated. Phase 2 criterion is the M4 refusal of REQ-F-03 (d); the Phase 1 build criterion returns in Phase 5. |
| 1b. UT-PHY-11 | Kept live. Half (1) gets an oracle, the via term of the 20 °C phase resistance per mm of board thickness. |
| 2. REQ-N-09 | A public method of a public physics class is a physics function. Two methods are in scope, and both miss parts. |
| 3. TR-01 | D-083c written into interfaces.md §3.2 as stated. Three weak points for Fable in section 4. |

## 1. UT-GEO-19 and UT-PHY-11 (rows (c) of `tests/independent/m7/records/U-V19_id_map.md`)

### 1a. UT-GEO-19

The Phase 1 criterion is the option M4 build (`docs/phase1/architecture/test_plan_draft.md` l.56). D-054c moves that
build to Phase 5, and REQ-F-03 (d) states what Phase 2 does instead, a refusal with
`UNBUILDABLE_SPIRAL_OPTION_NOT_IMPLEMENTED`. Two choices were open. The ID could leave the live row for Phase 5, or it
could carry the Phase 2 refusal.

The ruling restates it. Clause (d) of REQ-F-03 is live and has no other planned ID, so moving UT-GEO-19 out would leave a
must clause with a test and no ID. UT-GEO-11 set the precedent: its Phase 1 build criterion for two rotations was
withdrawn and the ID now names the refusal (`test_ut_geo_11_pairs_rotated_against_each_other_are_refused`). The
restatement does not loosen anything. The refusal is what REQ-F-03 (d) asks for today, and the Phase 1 build text stays
in the row as the Phase 5 criterion.

The test that checks it as written is `tests/unit/generators/test_spiral_pairs.py::test_m4_one_phase_per_pair_is_refused_until_phase_5`
(l.211, cases 16-16 and 12-16). It asserts the exact list `[("UNBUILDABLE_SPIRAL_OPTION_NOT_IMPLEMENTED",
("/winding/layers/pairs",))]`, which is the row's criterion (`verified` by reading). Agent 3 renames it to
`test_ut_geo_19_m4_one_phase_per_pair_is_refused_until_phase_5` with the body unchanged, and Agent 4 re-pins REQ-F-03
(U-V13 cites the old name). The U-D19 note in `requirements.md` that UT-GEO-19 stays "as the Phase 5 test" is now half
of the story. The ID is the Phase 2 refusal test and the Phase 5 build test. The Tests column does not change, so the
requirements file needs no edit.

### 1b. UT-PHY-11, half (1)

Half (1) said "the analysis gives every via one barrel" with no expected value. U-V19 offered two fixes, an oracle with a
tolerance, or a move to Phase 5 with the count. A move would drop a live clause that a real defect can break. A count of
2 or 0 passed to `via_resistance_ohm` halves the via term or makes it infinite. The UT-PHY-11 row records that nothing
in `tests/unit` reads the via term of a built board. The physics goldens map Xcoil boards with `via_ids=()`
(`tests/golden/m2_physics/test_analyse_layouts.py` l.48, which `test_analysis_golden.py` imports), and no serpentine
golden reads a phase resistance (`verified` by grep). Only the wave has such a check, GR-22. So the ruling keeps the
clause and states an oracle that needs no Xcoil.

The oracle uses the one input that only the barrel term reads. `analyse` passes `board_thickness_mm` as the barrel length
to `_via_resistance` (`src/embodic/physics/analyse.py` l.191 and l.299-300). Path resistance does not read it. So raising
the thickness by Δ raises each phase resistance by its via term at length Δ, if the phase is one series chain. The three
packaged examples have no parallel coil group, so every phase is one chain (measured below).

Probe (scratchpad, not committed). For each example, `load_example`, `build_layout`, `analyse` as built and again with
`dataclasses.replace(stack, board_thickness_mm=t + Δ)`. Expected ΔR is the mean over the phases of the sum, over the via
IDs of that phase's members, of `via_resistance_ohm(drill_mm, plating_um, Δ, rho_20, 1)`, where rho_20 is
`copper_resistivity_20c_ohm_m` (1.7241e-8 ohm m in the registry). Results on fcd050b (`verified` by running):

| Example | Vias (in phase members) | Vias per phase | Parallel groups | ΔR at 1.0 mm (ohm) | Rel. deviation at 1.0 mm / 0.4 mm |
|---|---|---|---|---|---|
| spiral_12c16p_default | 63 (60) | 20 | 0 | 0.015965034902 | 8.7e-15 / 9.2e-14 |
| serpentine_16p_example | 9 (3) | 1 | 0 | 7.9825174512e-4 | 3.3e-13 / 8.8e-13 |
| wave_16p_example | 192 (186) | 62 | 0 | 0.049491608197 | 7.1e-15 / 7.2e-14 |

With two barrels per via, the increase is half of these values, so the relative deviation is 0.5. The tolerance is
1e-9 relative. The subtraction loses about log10(R / ΔR) digits, at most 3.5 (serpentine, R 2.44 ohm), so float64
leaves a margin of more than 1000 over the worst measured value. The test uses one Δ, 1.0 mm.

The tests that check UT-PHY-11 as written are the kernel test
`tests/unit/physics/test_kernels.py::test_cf04_and_ut_phy_11_via_barrel_resistance`, which gets REQ-F-05 from Agent 3,
the two UT-GEN-06 tests under their U-M8y names, and a new test,
`tests/unit/physics/test_via_barrels.py::test_ut_phy_11_every_phase_via_of_an_example_is_analysed_as_one_barrel`
(marker REQ-F-05, parametrised over the three examples). Until the new test exists, the one-barrel part stays
`not tested` above the kernel, as the row already says. U-V19's F05 test (`test_f05_one_via_per_transition_is_analysed_on_every_topology`)
checks the weaker "is analysed" of REQ-F-05 and does not replace it.

## 2. Scope of REQ-N-09

The acceptance reads "every physics function names units and an EQ-ID". MT-04 and the N-09 unit check read that as
public module-level functions, and U-V19 recorded the reading as an `assumption`. The ruling is that methods count.

- A method is "a function defined in a class namespace" (Python Library Reference, Built-in Types, section "Methods",
  read in `pydoc_data.topics` of CPython 3.13). The acceptance gives no reason to exclude a function by where it is
  defined.
- The contract publishes `FieldTable.at` as part of the physics API (interfaces.md §8, the `FieldTable` stub), and it
  computes a physics value, B_z and B_t in T at a radius in mm from the EQ-05 table. `InterconnectResistance.total_ohm`
  is the stub, link and ring sum in ohm that `interconnect_loss_w` multiplies by I_line² for a star (EQ-23,
  `interconnect.py` l.223). Leaving them out would exempt two unit-bearing values only because of where they are
  defined.
- A member of a `typing.Protocol` class is out of scope. `CancelToken.cancelled` (`analyse.py` l.105) has the body
  `...`. The function that runs is the implementer's, and the implementer is outside physics (`embodic.drc`). A
  cancellation flag has no EQ-ID to cite, and a forced citation would be a false reference (standing order 3).

An AST scan of the public modules of `src/embodic/physics` (scratchpad script, `verified` by running) finds three public
methods on public top-level classes. Two are in scope, `FieldTable.at` (`emf.py` l.91) and
`InterconnectResistance.total_ohm` (`interconnect.py` l.27). Neither names an EQ-ID or has a Returns section, and `at`
has no Parameters entry for `radius_mm`. The third is the Protocol member.

The checker change for Agent 3 is in the MT-04 row of `test_plan.md` §5.4. Both checkers walk one set of functions.
The set is the public top-level functions as today, plus the public functions in the body of each public top-level
class whose bases do not name `Protocol`. The first positional parameter of a method needs no entry unless the method
is a `staticmethod`. A planted control reports an undocumented public method and leaves out a Protocol member and a
private method. Both checkers should share one walk, so that the two definitions of "physics function" cannot drift
apart again (today each file holds its own copy of the module and name filter).

Consequence. With the checker change, `test_mt04_physics_functions_are_documented` fails on the 0.0.4 source with the
two methods (`inferred` from the scan; the changed checker did not run). The fix is two docstrings, which is a `src`
change, so it makes a new release (D-082). U-M8y works with tests and tools only, so it must not add the checker change
alone. REQ-N-09 is `partial` on 0.0.4 until that unit lands. That is Agent 4's ruling to make, and this file only states
the cause.

## 3. TR-01 currency (D-083c)

interfaces.md §3.2 now holds the rule as D-083c states it. Under the release profile a manual record counts only when its
`embodic_version` begins with `embodic.__version__`. Otherwise TR-01 lists it as stale with its record path and D-061d
and does not count it. Agent 4 restamps a record that stands under D-061d with the new version and a reference to its
ruling. The text adds only what the rule leaves implicit:

- a stale record covers no row, but it does not fail the run by itself;
- "manual: N" counts only the counted records;
- the restamp reference goes after the version in `embodic_version`, and the record file keeps its text (standing
  order 7).

On fcd050b all six index entries read `"0.0.4 (release c25d8a9)"`, so all six count for 0.0.4 (`verified` by reading
`docs/phase3/verification/manual_records.json`). The section also settles the row "A manual record of an earlier build"
of interfaces.md §13 point 14. This unit's scope is §3.2 only, so that row is unchanged.

## 4. Weak points of the TR-01 rule (for Fable; the rule is not changed)

1. A prefix accepts a longer version. With 0.0.4 under test, a record stamped `0.0.40`, `0.0.4rc1`, `0.0.4.dev1` or
   `0.0.4.post1` counts. A PEP 440 pre-release or dev release comes before the final release, so a record of 0.0.4rc1
   would count for 0.0.4 without a D-061d ruling. No such record exists, and the project has used only 0.0.1 to 0.0.4
   (`verified` by `git log -L` of `src/embodic/__init__.py`). A stricter form would require the version followed by the
   end of the string or a space. Severity is low until a pre-release exists.
2. The check catches a version change, not a source change. The version changes only in the `chore(release)` commits
   (`verified`, four bumps in four release commits). A release-profile run on a later commit that changes `src` before
   the bump still counts the old records, although D-061d may say they do not stand. D-082's source-hash equality covers
   audits on a later commit. The gap is a gate run between a `src` change and the bump (`inferred`).
3. The version under test comes from the import. In this container the dev venv imports `embodic` from
   `/home/claude/embodic/src` whatever the working directory (`verified` by running `import embodic` with `-I`). A
   release-profile run from a worktree whose version differs from main would read main's version. The evidence's
   `embodic_version` in `tools/record_passed_tests.py` has the same input (`inferred`; no such run was made).

## 5. Questions for Fable

- Q1. REQ-N-09: which unit and release carry the checker change and the two docstrings (section 2)?
- Q2. REQ-N-09's statement covers every public function and dataclass, and its acceptance covers physics functions only.
  Five of the six public physics dataclasses name no EQ-ID (`MotorConstants`, `FieldTable`, `PathField`,
  `MassBreakdown`, `InterconnectResistance`; `CircuitSolution` does, `verified` by the AST scan). Should the acceptance
  grow? That is a scope decision, so this unit does not rule on it.
- Q3. TR-01: accept the three weak points of section 4, or narrow the rule?
