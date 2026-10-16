Prepared by: Agent 6 - Software Architecture Specialist - model: claude-opus-5-5

# Contract rulings for the U-V8 findings (proposals for Fable)

Unit U-D16, 2026-10-17, on main 3440241 (worktree `/home/claude/wt/U-D16`). Every ruling below is a proposal. Fable
decides, and nothing here changes a decision, a requirement or a contract file. The sources are Agent 4's records
`tests/independent/m7/records/defects.md`, `V3-01.md` and `V3-14.md` (read in `/home/claude/embodic`), the contract
files of this checkout, and the release run's REQ report `/home/claude/release_0.0.1/req_report.json`.

Every claim carries one status word of standing order 2. `verified` means read in the named file at the named line, or
reproduced by running the named command. This unit ran no test suite. The one script it ran reads the release REQ
report through the functions of `tools/trace_matrix.py` (section 2).

| Item | Proposal in one line | Unblocks |
|---|---|---|
| 1. DEF-UV8-03 | Call the DRC distance "clearance" everywhere. Rename the JSON keys to `clearance_mm` and `least_clearance_mm`, give the outcome JSON its own `format` and `format_version` 2, and leave the project schema at 1 | LG-03, REQ-T-10 |
| 2. DEF-UV8-02 | The release profile passes `--fail-untested-through M5` from the 0.0.2 release gate on, after the six rows have tests or a manual record. Commit and nightly do not | REQ-T-09, REQ-N-10 |
| 3. DEF-UV8-06 | Write both UT-PHY-07 and GR-07. Specifications for Agent 3 are in section 3 | REQ-F-03, REQ-F-04 |
| 4. DEF-UV8-07 | A row is `verified` only with Agent 4's row ruling `checks`, pinned to the source hash of every test it cites | every must row |
| 5. U-S9 list | Not arrived when this unit finished. Section 5 is the place for it | none yet |

## 1. DEF-UV8-03: the computed DRC distance is a clearance, not a measurement

### What the product does today

- The DRC computes each clearance from the generated geometry. `src/embodic/drc/engine.py` l.336 copies the kernel's
  `m.clearance_mm[i]` into `DrcViolation.measured_mm` (`verified` by reading). Nothing is measured on a board.
- D-007 gives the word one meaning in this product. "An input gains the `measured` provenance only when the user marks
  it as measured and names the source" (`docs/decision_log.md` l.13, `verified`). REQ-T-06 restates it
  (`requirements.md` l.168), and so does standing order 5.
- The same window shows both meanings. The inspector has the chip "measured" and the command "Mark as measured..."
  (`src/embodic/ui/strings/design.py` l.201 and l.261). The DRC table has the column "Measured (mm)"
  (`src/embodic/ui/strings/results.py` l.85). All `verified` by reading.
- The same JSON document holds both meanings. `outcome_to_json` writes `/provenance` with the value `"measured"` and
  `/drc` with `measured_mm` and `measured_min_mm` (`src/embodic/api.py` l.345 and l.349, `verified`).
- The JSON keys occur only in the `compute --json` output. Of the 233 `json-key` rows of `V3-14.md`, 186
  `measured_mm` and 47 `measured_min_mm`, every one sits in an `<example>/outcome.json` (`verified` by counting the
  rows). The bundle holds the drawings, the project JSON and the PDF report (interfaces.md l.3993), and the project
  JSON holds the design only (interfaces.md l.2958). In the bundle, only the PDF text says "measured" (V3-14).
- Nothing in the product reads the outcome JSON. `outcome_to_json` is called by `src/embodic/cli/commands.py` l.150
  and by tests, and `src/embodic` has no reader for it. The only published schema is `project.v1.schema.json`
  (`verified` by grep and by listing `src/embodic/io/schema/`).
- PK-04 compares two outcome folders only when their source hashes are equal (`pk04_compare.py` l.53-56,
  `verified`). A 0.0.2 build writes new Linux references in any case.
- REQ-T-10 says "Computed values shall never be called 'measured'" (`requirements.md` l.172). Its test LG-03 does not
  exist (section 2).

### Proposed term

Use "clearance" for the distance of one pair and "least clearance" for the least distance of a check kind. In
REQ-F-10, where the contrast with a measurement is the point, write "computed clearance".

- The engine already uses the word for this value (`m.clearance_mm`, engine.py l.336). The board dump also names its
  DRC slot `rule: {clearance, epsilon}, values` (`src/embodic/io/board_dump.py` l.60). Both `verified`.
- `DrcRules` uses `trace_clearance_mm` and the like for the required value. Each new key sits in an object that also
  holds `required_mm`, so the object tells the reader which value is which. The UI shows "Clearance (mm)" next to
  "Required (mm)".
- "Actual clearance" was rejected. "Actual" suggests a built board, which is the same claim in a weaker form.
- "Computed clearance" was rejected as a key and a column name. Every engine output is computed, so the word adds
  length and no meaning there.

### Proposed JSON rule: rename, and version the outcome document on its own

Rename `DrcViolation.measured_mm` to `clearance_mm` and `DrcCheckSummary.measured_min_mm` to `least_clearance_mm`. The
JSON keys follow the field names, because `to_json` writes field names. Do not raise the project `schema_version`.
Add `"format": "embodic.outcome"` and `"format_version": 2` to the top level of `outcome_to_json`. A document without
`format` is version 1, the shape that embodic 0.0.1 writes. Interfaces.md §10 records the key map for version 1 to
version 2. Do not write a version 1 reader in the product.

Reasons:

1. Keeping the key and documenting it as "not provenance" does not work for this file. The document carries both
   meanings at once, and a JSON file travels without the contract text. It would also need a permanent LG-03
   allow-list entry for exactly the output that scripts read. REQ-T-10 says "never" (`requirements.md` l.172).
2. The project schema rule does not apply. The §9.1 rule covers the project file (interfaces.md l.2978-2984), and the
   project file holds no DRC value. A bump to 2 would make embodic 0.0.1 refuse every 0.0.2 project file with
   `INVALID_SCHEMA_VERSION_NEWER` (l.2960-2961), and the content of those files would not have changed.
   `VersionInfo.schema` in the outcome JSON (l.3424) is that project schema, so it stays 1.
3. A version 1 reader would have no caller. Nothing in the product reads the outcome JSON, and PK-04 never compares
   a 0.0.1 file with a 0.0.2 file. The key map in §10 is enough for an outside script. Whether the user has such a
   script is `unresolved`. D-048c makes embodic a personal project, and nobody asked the user.
4. The two other JSON documents that embodic writes for machines already carry `format` and `format_version`. These
   are the evidence file (interfaces.md l.1436-1437) and the board dump (`board_dump.py` l.168). The outcome JSON is
   the only one that cannot say which shape it has, and a key rename is the first change that needs it.
5. Rename in one wave and keep no alias property. Agent 4's readers in `tests/independent` use the attribute names
   (for example `tests/independent/m1/embodic_adapter.py`), so Agent 4 updates his own files in the same wave.

### REQ-F-10 text fix

Statement, `requirements.md` l.70, from "report a violation whenever the measured clearance is below rule minus
epsilon" to:

> The engine shall run DRC on the generated copper of every topology and report a violation whenever a computed
> clearance is below rule minus epsilon, epsilon at most 1e-6 mm, with no slack band.

The ID, acceptance and tests do not change. A revision note at the top of `requirements.md` names DEF-UV8-03. D-006
(`docs/decision_log.md` l.12) says "measured clearance" too. That file is Fable's, so a wording note there is Fable's
choice. Standing order 5 already writes "clearance" alone.

### Edits this ruling implies

Line numbers are on main 3440241, `verified` by reading or grep.

| File and line | From | To | Owner |
|---|---|---|---|
| `docs/phase2/architecture/requirements.md` l.70 | "the measured clearance" | "a computed clearance", plus the revision note | Agent 6 |
| `docs/phase2/architecture/interfaces.md` l.2490 | "violation when measured clearance <" | "violation when the clearance <" | Agent 6 |
| same, l.2660 and l.2669 | `measured_mm`, `measured_min_mm` | `clearance_mm`, `least_clearance_mm` | Agent 6 |
| same, l.2728 and l.2733 | "`measured_min_mm` ... the pairs the narrow phase measured", "counts measured pairs" | "`least_clearance_mm` ... the pairs the narrow phase computed", "counts the pairs it computed" | Agent 6 |
| same, §10 l.3475-3476 | docstring only | add `format`, `format_version` 2 and the version 1 key map | Agent 6 |
| same, §11 l.3900-3904 | column "Measured" | column "Clearance" | Agent 6 |
| same, §14 l.4229 | "the `trace_trace` `measured_min_mm`" | "`least_clearance_mm`" | Agent 6 |
| `docs/phase2/architecture/test_plan.md` l.158 and l.289 | "measured clearance v", `measured_min_mm` | "computed clearance v", `least_clearance_mm` | Agent 6 |
| `src/embodic/drc/report.py` l.54-56, l.68, l.79; `drc/engine.py` l.325, l.336, l.348, l.352, l.356 | field and parameter names | the new names | Agent 3 |
| `src/embodic/api.py` l.342 | no identity keys | `format`, `format_version` | Agent 3 |
| `src/embodic/io/report.py` l.137 | "Least measured" | "Least clearance" | Agent 3 (text by Agent 1) |
| `src/embodic/ui/strings/export.py` l.45 | "{measured} measured, {required} required." | "{clearance} clearance, {required} required." | Agent 1, then Agent 3 |
| `src/embodic/ui/strings/results.py` l.85 and l.87 | "Measured\n(mm)", "Measured {measured}" | "Clearance\n(mm)", "Clearance {clearance}" | Agent 1, then Agent 3 |
| `src/embodic/selftest/catalogue.py` l.183 | "the check measured no track pair" | "no track pair came within the check distance" | Agent 3 |
| `src/embodic/ui/views/checks_view.py` l.43, l.181; `ui/viewmodels/results.py` l.360; `ui/views/dialogs.py` l.31 | column id `measured`, `measured_text`, `measured=` | `clearance` | Agent 3 |
| `docs/phase2/engineering/equation_registry.json` l.2846 (EQ-30) | "DRC clearance measurement and acceptance" | "DRC clearance computation and acceptance" (the packaged copy follows through `tools/sync_registry.py`) | Agent 2 |
| `resources/fonts/FONTS.md` l.24-25 | "measured with `sha256sum`", "`verified` by measuring" | "computed with `sha256sum`", "`verified` by computing" | Agent 3, with Agent 5 |
| tests that use the old names, and Agent 4's readers | old names | new names | Agent 3; Agent 4 for `tests/independent` |

The check scripts under `docs/phase2/*/checks/` that use `measured_min_mm` (for example
`docs/phase2/architecture/checks/selftest_probe.py`) record runs on old commits. They stay as written.

## 2. DEF-UV8-02: the release gate enforces TR-01

### What the gate does today

- `tools/ci.py` l.74-82 runs `tools/trace_matrix.py` without `--fail-untested-through`, so `find_untested` never
  runs (`trace_matrix.py` l.119). The gate is still named "trace matrix (TR-01, TR-02)" (ci.py l.75). `req_audit.py`
  reads PASS lines of the gate log as evidence (l.110-112), and V3-01 l.38 and l.57 show that it counted TR-01 as
  `gate` evidence for that reason. All `verified` by reading.
- With the flag, the release report has 6 live must rows without a passing test. These are REQ-N-07, REQ-N-10,
  REQ-T-10, REQ-T-11, REQ-L-03 and REQ-L-05. This unit reproduced the list (`verified`) by calling
  `parse_requirements`, `parse_report` and `find_untested` of `tools/trace_matrix.py` on
  `/home/claude/release_0.0.1/req_report.json` (3125 records). The script is
  `/tmp/claude-0/-home-claude/f28a4cfe-cf25-5512-9052-c4c291ea667b/scratchpad/tr01_profiles.py`.
- No record in that report carries any of the six REQ IDs (`verified`, same run). LG-03, LG-04, LG-05 and LG-06 have
  no test at all. `test_plan.md` §5.4 lists only LG-01 and LG-08 (l.373-374), and `tests/static/test_lg_language.py`
  marks only REQ-L-01 (`verified` by grep). The Phase 1 definitions stand in `test_plan_draft.md` l.343-346.
- The Phase 1 TR-01 text accepts "≥ 1 passing test or a manual test record" (`test_plan_draft.md` l.393, `verified`).
  `trace_matrix.py` reads no manual record.
- pytest-cov is already a dev dependency (`pyproject.toml` l.28) with a licence row (`dependency_licences.md` l.43).
  `[tool.coverage.run]` sets `branch = true` (`pyproject.toml` l.102-105). No gate passes `--cov`, and nothing sets a
  threshold (`verified` by reading ci.py l.61-64 and `pyproject.toml`).

### Proposal

1. The release profile passes `--fail-untested-through M5`. Every milestone M1 to M5 is closed (D-047, D-048a), so M5
   is the only sensible value. Put it in the profile, not in the gate list. `Profile` (ci.py l.32-46) gains
   `untested_through: str | None`, set to `"M5"` for release and `None` for commit and nightly. `gates_for` adds the
   flag, and names the gate "trace matrix (TR-01, TR-02)" only when it passes the flag, and "trace matrix (TR-02)"
   otherwise. The gate name then never claims a check it skipped, so the gate log cannot give req_audit false
   evidence.
2. Commit and nightly do not pass the flag. They skip `tests/packaging` and `tests/performance` (ci.py l.28 and
   l.43-44). On the same report with those two folders left out, a seventh row fails, REQ-N-05, whose only tests are
   packaging tests (`verified`, same script). The commit profile also deselects `slow` tests, which the report does
   not record, so its true list can only be longer (`inferred`).
3. Turn the flag on when the six rows have their tests or a manual record. The 0.0.2 release gate (D-049g) is the
   first gate to run with it. Until then, the flag on the current tree only reports what is already known.
4. `trace_matrix.py` gains `--manual-records PATH`, a JSON list with one object per record: `req`, `test_id`,
   `record` (repository path), `embodic_version`, `result` (`passed` or `failed`). TR-01 counts a record whose result
   is `passed`. The summary line prints the manual count separately ("manual: 1"), so nobody reads a manual record as
   an automated test. The Phase 1 TR-01 text already allows it. Without this input, REQ-N-07 can never pass, because
   its acceptance needs a person on a clean Windows machine (`requirements.md` l.112).
5. Coverage runs in the release profile only. The pytest gate there adds `--cov` with a JSON report. A small check,
   `tools/coverage_check.py`, reads the totals and fails below 90 % of lines or 80 % of branches. These are the
   REQ-N-10 thresholds, labelled `assumption` there (l.115). The check needs its own script because coverage.py's
   single `fail_under` combines lines and branches when branch measurement is on. That statement is an `assumption`:
   this unit did not read the coverage.py documentation. The cost of tracing the gate is `not tested`, and the gate
   already takes about 75 minutes on 2 CPUs (D-047). The coverage of the tree is `not tested` too. If the first run
   is below a threshold, Fable decides between more tests and a different threshold. The gate does not lower it.
6. REQ-N-10's acceptance and TR-01 disagree. The acceptance says "0 untested live REQs" (l.115), and TR-01 checks
   only must rows (`trace_matrix.py` l.95). On the release report, 12 live rows have no passing test: the 6 must rows
   above and REQ-F-30, REQ-N-20, REQ-T-12, REQ-L-02, REQ-L-06 and REQ-L-09 (`verified`, same script). Proposal: amend
   the REQ-N-10 acceptance to "0 untested live must REQs; the matrix lists the untested should and could rows", and
   make `trace_matrix.py` print that list. A could row may legitimately stay unbuilt in a release, and then no
   passing test for it can exist. This unit did not check which of the six are built.

### The six rows

| REQ | Planned test | Why no passing test exists | What it needs | Waits on | Owner |
|---|---|---|---|---|---|
| REQ-N-07 (M5) | PK-06 | The acceptance is a timed walkthrough on a clean Windows machine. Agent 4's Linux walkthrough (U-V5) is not that | The Windows W4 record of the campaign, entered through `--manual-records` | Windows campaign W4 (`docs/phase3/verification/verification_plan.md`) | Agent 4 or the user for the record; Agent 3 for the input |
| REQ-N-10 (M2) | TR-01 | No test carries REQ-N-10, and no coverage step exists | Item 5 above, plus a unit test of `coverage_check.py` marked REQ-N-10 that fails a total of 89.9 % lines | The first coverage run | Agent 3 |
| REQ-T-10 (M4) | LG-03 | LG-03 is not implemented | A scan of catalogue strings, report templates and generated exports for "measur". The allow-list holds the paper reference ("reference (paper, measured)", Phase 1 LG-03) and input provenance `measured` (REQ-T-06). V3-14's classes are the starting list | Section 1. Without the rename, LG-03 fails at the seven places V3-14 lists outside its allow-list (l.139-148), or needs a DRC exception | Agent 6 writes the §5.4 row, Agent 3 implements |
| REQ-T-11 (M4) | LG-04 | LG-04 is not implemented, and the acceptance includes a reviewer check | A scan against a reviewed phrase list, and the reviewer's record through `--manual-records` | Fable's ruling on DEF-UV8-04 ("Balanced.") | Agent 3; Agent 1 for the review |
| REQ-L-03 (M4) | LG-05 | LG-05 is not implemented | A case-insensitive "xcoil" scan of user-facing strings, the registry fields the UI shows, and generated exports, with V3-14's allow-list classes (evidence test IDs, board-dump schema text, fields the UI does not show, `source_note`) | Fixes of DEF-UV8-01 and DEF-UV8-05. UI-15 pins the old notice text and changes with the fix | Agent 3; Agent 2 for EQ-14, EQ-20 and EQ-27 |
| REQ-L-05 (M4) | LG-06 | LG-06 is not implemented | A committed list of brand-asset SHA-256 values (hashes only, no asset), and a personal-name scan whose tokens come from the run environment and never from the repository (standing order 7). With no token, the test fails instead of skipping in the release profile, because a skip would hide the gap. That design is an `assumption` for Agent 3 and Agent 4 to settle | None. V3-14 found 0 hits | Agent 3 |

### Edits this ruling implies

- `test_plan.md` §5.4 gains rows LG-03 to LG-06 with the content above (Agent 6). §7 gets a line that states the
  release gate enforces TR-01 through M5 from 0.0.2.
- `test_plan.md` gets a TR-01 row in Phase 2 wording, with the manual-record rule (Agent 6).
- `requirements.md` REQ-N-10 acceptance (l.115) if Fable accepts item 6 (Agent 6).
- `tools/ci.py`, `tools/trace_matrix.py`, the new `tools/coverage_check.py` and their unit tests (Agent 3).

## 3. DEF-UV8-06: write UT-PHY-07 and GR-07

Both tests stay. Neither has a reason to be withdrawn. Each checks a claim that a must row makes about code that ships.

### UT-PHY-07: the series chain EMF is the phasor sum of the pair EMFs, each at its own z

Why write it. REQ-F-03 criterion (c) says "series EMF = phasor sum (1e-9 rel.)" (`requirements.md` l.63). Series pairs
now build. UT-GEO-26 shows series boards with 0 DRC violations (V3-01 Part B l.73, `verified` by reading the record).
The parallel two-member identity of UT-PHY-08 does not cover a series sum. A wrong z has happened before in this code.
DEF-M3a-01 added k times the pitch to a z that already held it (D-035c), so the "own z" clause is worth a test.

Specification for Agent 3. Marker `@pytest.mark.req("REQ-F-03")`. The test name holds `ut_phy_07`. Compare complex
values with a relative tolerance of 1e-9 and `abs=0.0`, because the default absolute tolerance of `pytest.approx`
voids a relative claim (D-050b).

1. Closed form, on `solve_phase_circuit` (`src/embodic/physics/circuit.py` l.53; interfaces.md l.2812-2814). Build a
   `Circuit` whose phase A is a chain of two series members with one path each. Give the two paths flux linkages of
   equal magnitude, 90 degrees apart. The expected phase EMF is the sum of the EMFs of two circuits that each hold one
   of the members alone. Assert that the magnitude of the sum is the square root of 2 times one member's magnitude,
   within 1e-9 relative. A scalar sum would give 2 times, so the case tells a phasor sum from a scalar sum. Add one
   case with a member of negative polarity, whose EMF must enter with its sign.
2. Generated board. Use the CF-11 series spiral with k = 2 series pairs that
   `tests/unit/generators/test_spiral_series_fan.py` already builds (`CASES`, l.27, `verified` by reading). For each member, compute its flux linkage with `field_table` at
   that member's copper z and `integrate_path` over its paths (`src/embodic/physics/emf.py` l.69 and l.115). Then get
   the member's EMF from a one-member circuit. Assert that the fundamental of `analyse()`'s phase EMF equals the sum of
   the member EMFs for every phase, within 1e-9 relative. Assert first that the members' copper z values differ,
   because a case with equal z cannot detect a wrong z. As a control, the same sum with every member evaluated at the
   first member's z must differ from `analyse()` by more than 1e-6 relative.

The test checks the arithmetic of the chain. It does not say that a series pair behaves this way on a real board. That
stays `unresolved` under D-020 until a board exists (D-048f).

### GR-07: the even stack-up helper against Xcoil `stackupFor`

Why write it. `generate_even_stackup` (`src/embodic/model/stackup.py` l.55-93) says it builds layers "like Xcoil
stackupFor in auto mode (engine.js l.1156-1176)". The UI session uses it to derive the stack-up a user starts from
(`src/embodic/ui/viewmodels/session.py` l.921), and the serpentine and wave golden mappers use it to build the golden
designs (`tests/golden/m3_serpentine/design_map.py` l.72, `tests/golden/m3_wave/param_map.py` l.24). All `verified` by
reading. GR-07 is the only direct check of that claim. GR-22 compares EMF on the mapped copper, so it would see a wrong
z only through the EMF (`inferred`).

What this unit read in Xcoil (`/home/claude/serpentine/src/engine.js` l.1156-1176, read only, `verified`):

- Auto mode places copper i at `tOuter / 2 + i * (boardThickness - tOuter) / (nCu - 1)`, or at `tOuter / 2` for one
  layer. Outer layers take `copperOzOuter`, inner layers `copperOzInner`. A dielectric is the gap between two copper
  layers, never below 0, and the board thickness stays the input value.
- Custom mode takes the entry list as given, raises each thickness to at least 0.001 mm, and stacks z from the sums.
- The embodic helper takes one copper thickness for every layer (stackup.py l.55-56). With equal inner and outer
  copper, its z values follow the same formula (`inferred` from the algebra of l.84-92). Every one of the 74 golden
  parameter sets uses 2 oz inner and outer (`verified` by grep over `tests/golden/data`), so no golden case exercises
  a difference.

Specification for Agent 3. Marker `@pytest.mark.req("REQ-F-04")`. The test name holds `gr_07`. Write the Xcoil fixtures
with the function-level dumper (`tools/golden/dump_xcoil.mjs`, with `tools/golden/functions` and `cases`), as the M1
function fixtures under `tests/golden/data/m1` are written.

1. Auto mode. Copper counts 1, 2, 4, 6 and 8, board thickness 1.6 mm, copper 1 oz and 2 oz with inner equal to outer.
   Compare each copper z (`Stackup.copper_z_mm()` against Xcoil `z`), each copper thickness, each dielectric thickness
   and the board thickness, within 1e-12 mm absolute (the plan's tolerance, `test_plan_draft.md` l.165).
2. Custom mode. Two Xcoil custom lists, one symmetric and one with unequal dielectrics, against a `Stackup` built from
   the same entries. Compare copper z within 1e-12 mm.
3. One thin-board case where the gaps clamp to 0, for example 8 layers of 2 oz on a 0.4 mm board. Xcoil keeps the
   input board thickness. The embodic helper sums its layers, so the two may differ (`inferred`). Pin what happens.
   If the values differ, Agent 3 reports a DEF row. Agent 2 and Agent 4 then decide between an expected diff with its
   reason and a validation refusal. Nobody loosens the tolerance.

Out of scope for GR-07: unequal inner and outer copper, which the helper cannot express, and custom thicknesses below
0.001 mm, which Xcoil clamps. Both are open questions below.

### Edits this ruling implies

- `test_plan.md` §5.1 restates UT-PHY-07 and GR-07 with the cases above, so the Phase 2 plan holds their Phase 2
  wording (Agent 6).
- The two tests and the fixture cases (Agent 3).

## 4. DEF-UV8-07 and V3-01: a test name is not evidence that the acceptance is checked

### What req_audit does today

`req_audit.py` marks a row `verified` when every planned ID has `gate`, `name`, `file`, `eqt` or `record` evidence and
no ID needs another machine (l.21-24, l.115-159, `verified` by reading). `name` means a passing test that carries the
row's REQ marker has the ID in its name (l.119-126). The script says itself that it does not read whether a test checks
the acceptance (l.24). V3-01 read one sampled test for each of the 50 must rows that req_audit called `verified`. Six
check the acceptance, 32 check part of it, and 12 check none of it (V3-01 l.66, `verified` by reading the record).

Standing order 2 defines `verified` as "read in the source or reproduced by running something". A name match is
neither, so the current row status uses the word against the project's own definition.

### The data shape

The fact to record is a reviewer's reading of one row. The clauses of the row's acceptance, each mapped to the evidence
that asserts it:

```
AcceptanceRuling
  req_id        "REQ-F-36"
  ruling        checks | partial | does not check
  clauses       [ { text: quoted from the Acceptance cell,
                    evidence: [ { kind: test | gate | record,
                                  ref: pytest node ID | gate name | record path,
                                  line: int,
                                  sha256: hash of the cited source } ] } ]
  missing       the clauses no evidence asserts (empty for `checks`)
  reviewer, base_commit
```

`sha256` is the hash of the test function's source text (`ast.get_source_segment`) for a test, of the `Gate(...)`
entry in `tools/ci.py` for a gate, and of the whole file for a record.

### Proposed rule

A live row is `verified` only when all three hold:

1. Every planned ID has passing evidence, as today.
2. The row has an `AcceptanceRuling` with `ruling = checks`.
3. Every evidence entry of that ruling is current. Its hash equals the hash of the source in the audited tree, and a
   cited test passed in the audited run.

A row that meets 1 but not 2 or 3 is `partial`. A ruling whose hash no longer matches counts as absent, and the audit
lists it as stale. A cited test must carry the row's REQ marker. For the 11 cause-B IDs that V3-01 found under another
marker (`defects.md` l.112), Agent 3 adds the row's REQ ID to the existing marker. A test may already carry several,
as V3-01 Part B l.86 shows. Every other status rule of req_audit stays.

TR-01 in `trace_matrix.py` stays a floor: at least one passing test or manual record per live must row. Its output
never says `verified`. `trace_matrix.py` answers "does a test exist?", and req_audit answers "is the acceptance
checked?". The two stay separate.

Reasons:

- Verification separation (standing order 12). The ruling is Agent 4's reading of the test source. An `acceptance`
  argument on the marker would be the author's own claim, which is the self-report that standing order 12 keeps apart
  from verification. D-046c already rules that an EQT marker claims the whole criterion. This rule asks the
  independent verifier to read that claim at the row level.
- It is small. V3-01 already produces these rulings with line numbers (`tests/independent/m7/v3_01_rulings.py`).
  req_audit gains one input file and one condition, and no test in `src` or `tests` changes except the cause-B
  markers.
- The hash keeps a ruling from outliving a test. If someone weakens a test, its ruling goes stale and the row drops
  to `partial` until Agent 4 reads it again. A fixture or helper change does not move the hash. That limit is
  accepted and stated in the audit's header (`inferred`: the hash covers the function body only).
- One ruling per row, not per test, because most rows need several tests together. A per-test `checks` would rarely be
  reachable. V3-01's strict count gives 10 must rows (V3-01 l.104).

Effect on the counts. Six must rows have one sampled test that alone checks the whole acceptance. These are REQ-F-36,
REQ-N-08, REQ-N-11, REQ-N-14, REQ-N-18 and REQ-L-08 (V3-01 Part A). They are the first candidates for `verified`
under the new rule. The other must rows that req_audit called `verified` become `partial` until Agent 4 records a row
ruling (`inferred` from the rule; the new counts are `not tested`, because no ruling file exists yet).

### Edits this ruling implies

- `test_plan.md` gets a short section, "What `verified` means for a requirement row", with the rule and the data
  shape above (Agent 6).
- `docs/phase3/verification/checks/req_audit.py`, its ruling input file (for example
  `tests/independent/m7/acceptance_rulings.json`), and `verification_plan.md` (Agent 4, who owns all three).
- The cause-B marker additions (Agent 3).

## 5. Agent 1's "needs contract change" list (U-S9)

When this unit finished, the list had not arrived. `docs/phase3/design` in this worktree, in `/home/claude/embodic`
and in `/home/claude/wt/U-S9` holds only `ux_verification_plan.md` and `checks/` (`verified` by listing), and no file
there contains "contract change" (`verified` by grep). A later Agent 6 unit rules on each item here with the same
shape: the item, the contract text it touches (file and line), the proposal, the reasons, and the edits.

| Item | Contract text touched | Proposal | Reasons | Edits |
|---|---|---|---|---|
| (pending U-S9) | | | | |

## Open questions for Fable

1. Item 1: should the UI and PDF also say "least clearance" where they now print a summary minimum, or only where
   "measured" stands today? This proposal changes only the places that say "measured".
2. Item 2: does a manual record of the 0.0.1 Windows walkthrough satisfy TR-01 for REQ-N-07 in the 0.0.2 release gate?
   The proposal says yes, because TR-01 asks for a record, not a record of this build, and the summary prints the
   record's version. Fable may instead want a 0.0.2 walkthrough, which means the 0.0.2 gate cannot pass before the
   Windows campaign.
3. Item 2, point 6: amend REQ-N-10's acceptance to must rows, or make TR-01 check every live row?
4. Item 3: should `generate_even_stackup` take an inner copper thickness, as Xcoil's auto mode does? This is a product
   question for Agent 1 and Fable, because the user can always enter an explicit stack-up (REQ-F-04).
5. Item 3: Xcoil raises a custom layer thickness below 0.001 mm to 0.001 mm. Should embodic refuse such a layer
   instead (D-014: no invented input)? This unit did not check what `validate_design` does with it.
