Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5 (unit U-V25, 2026-10-22, redone for release
0.0.6 by unit U-V30, 2026-10-22)

# Phase 4 acceptance plan: the user accepts one named build

Phase 4 is the user's acceptance of one build of embodic. The candidate is release 0.0.6 (D-096). This plan says what
the user does, what the user decides, what carries over from Phase 3 without a rerun, and when Phase 4 ends. Fable can
start it on the day Phase 3 closes.

Every claim carries one status: `verified` (checked against a record, or run by me in this unit), `inferred`,
`assumption`, `unresolved` or `not tested`. A claim that cites a decision row or a record and carries no label is
`verified` by reading that record. My own runs were on Linux in the cloud container. None of them is a Windows result
(order 8).

## What the user does and decides

The user does three things, on the user's Windows laptop, with the named build installed:

1. Follows the walkthrough of Agent 1, `docs/phase4/design/uat_walkthrough.md` (U-S17, U-S20). It includes the
   Narrator check AX-06 that the user still owes on 0.0.6 (D-097c). The W6 rows run in two parts: a scripted part from
   a launcher that Fable prepares at the start of the UAT session, and a human part in walkthrough parts 0 to 3, 6
   and 7 (D-100c).
2. Runs the nine engineering checks E-01 to E-09 of section 3. Each check has an expected result and a box for pass,
   fail, or accept with a note. Examples are a DXF of an example board opened in the user's own CAD tool, a comparison
   with Xcoil v3 on a case the user picks, and a review of the PDF report.
3. Decides the 13 items of the decision sheet in section 4: three licence items, code signing, the GitHub repository's
   visibility and what is pushed, four known limits to accept by name, the PDF content, the order of the Phase 5
   backlog, and the acceptance verdict itself.

The walkthrough and the checks together take about 1.5 to 2 hours (`assumption`: Agent 1's brief targets 45 to 60
minutes for the walkthrough, and the checks need a CAD tool and Xcoil v3 open).

Phase 4 ends when every check and walkthrough step has a result, every failed step has a defect row with a ruling, and
the decisions are in the decision log in the user's own words (section 5).

## 0. The named build

The plan treats the build as a parameter. Today it has these values:

| Field | Value | Source | Status |
|---|---|---|---|
| Version | 0.0.6 | D-096 | `verified` |
| Tag and commit | `v0.0.6` on 2bfca49 | `git rev-parse v0.0.6^{commit}` in this worktree | `verified` |
| Wheel | `embodic-0.0.6-py3-none-any.whl`, SHA-256 `fdb89189161d14b71433c4e35861d4e4d56fc6a7e64383f96ba13e27ba450101` | `sha256sum /home/claude/release_0.0.6/embodic-0.0.6-py3-none-any.whl` | `verified` |
| Evidence `source_sha256` | `db089e71…75cb`, equal to main's package source hash at the release gate | D-096 | `verified` (record) |
| Audit of the build | `docs/phase3/verification/req_audit.md` | `req_audit.py --target 0.0.6 --check`: "req_audit.md is current" on U-V30's branch | `verified` |
| Carry-over table | `docs/phase4/verification/carry_over_0.0.6.md` | `docs/phase4/verification/checks/carry_over.py --check` | `verified` |
| Product files on main | `src/`, `resources/`, `pyproject.toml`, `requirements/` and `README.md` of main 2174f1b equal those of 2bfca49. `docs/install/INSTALL.md` gained 7 lines, the `python -m` route of D-098b | `git diff --stat 2bfca49 2174f1b -- <those>` | `verified` |

A change to `src/` makes a new release with a new version (D-082, D-084c). If the build changes, redo these steps
before the user starts:

1. Fable's release gate on the new commit, and the Windows checks the D-061d ruling names.
2. A new target in `docs/phase3/verification/checks/req_audit.py` (Agent 4), the audit, and the record currency run
   `tests/independent/m7/v14_record_currency.py --target <commit>`.
3. `carry_over.py` with the new build and commit. It refuses an audit of another build, and it fails while a row that
   is not `verified` has no Phase 4 handling, so the table cannot carry over by accident.
4. The table above, and every expected value in section 3 that quotes an output of 0.0.6.

### What must hold before the user starts

Phase 4 starts on the build for which `verification_plan.md` section 4 holds, or for which Fable rules each point that
does not hold. D-100 rules points 1 to 4 on 0.0.6 (`docs/phase3/verification/phase3_report.md`). These items are open
(`verified` by reading the records named):

| Item | State | Owner | Source |
|---|---|---|---|
| AX-06 Narrator on 0.0.6 | not run. Phase 4 starts with REQ-N-16 and REQ-N-24 `partial`, and A-1 waits for AX-06 or the user's decline | the user, inside the walkthrough | D-097c, D-100b |
| W6 scripted part on the real display | not run. Fable prepares the launcher for the start of the UAT session, and Agent 1 reviews the shots | Fable, Agent 1 | D-100c |
| The Thai summary of the Phase 3 report | Fable writes it | Fable | D-100e |
| The push of main, `v0.0.4`, `v0.0.5` and `v0.0.6` | planned at the Phase 3 close and approved by the user. If the repository is public, the push publishes everything G-1 lists, so I recommend that Fable asks G-1 first | Fable, from the laptop | D-065b, D-091d, D-097c |

## 1. Scope: what the user accepts

The user accepts the Phase 2 scope that the user approved on 2026-10-04 (`docs/PROJECT_BRIEF.md` section 5, D-008 to
D-015), as Phase 3 verified it.

In scope (`verified` by reading the rows named):

- A Python 3.11+ desktop application on PySide6, Windows first, Linux for development (D-010).
- Spiral coils (new, primary), and the serpentine and interleaved-wave generators ported from Xcoil v3 with golden
  regression (D-013, REQ-F-34, REQ-F-35).
- Multi-layer stack-ups, three phases, star, delta and open connections (brief section 5).
- Light and dark themes, white, grey and black chrome, red, blue and green phases with a greyscale and hatch mode, and
  a toolstrip with original icons (D-011, D-012).
- A blank "New design" at start, with the team's parameter sets shipped only as labelled examples (D-014).
- Exports: SVG, DXF (complete, outline, screws), the JSON project file, the PDF report and the README, and a ZIP bundle
  (D-009, REQ-F-16, REQ-F-29).
- Traceability: unit, equation ID, evidence, assumptions and a status badge on every result (D-007, REQ-T-01 to
  REQ-T-16).

Out of scope, so the user does not test it:

- KiCad: no plugin and no `.kicad_pcb` export (D-009). The engine stays UI-agnostic so a plugin can come later.
- A 3-D view (D-015).
- Spiral option M4 (one phase per pair) and more than one via per transition: both are refused today and belong to
  Phase 5 (D-054c, D-054d).
- A Windows bundle that needs no Python. It was a stretch goal (D-015). On 0.0.6 the bundle ran and passed on the
  laptop (D-099a), but the policy's decisions are not uniform (D-099c), so signing stays decision S-1.

The requirement set is `docs/phase2/architecture/requirements.md`: 110 rows, of which 73 live must rows, 17 live should
rows, 4 live could rows and 16 withdrawn KiCad rows (`verified` by parsing the table). On 0.0.6 the must rows are 67
`verified`, 2 `partial` and 4 `failed` (V3-15 on 0.0.6, `docs/phase3/verification/req_audit.md`, U-V30). The failed
rows are REQ-N-01 (DEF-W-15) and REQ-N-02 (DEF-W-12), each through its failed run on the laptop, and REQ-N-05 and
REQ-N-06 through their accepted W7 and W8 records. D-100b names the first two as exceptions and closes the other two by
name, and the exit rests on those rulings (D-101). No should row is `verified`, because V3-01 rules must rows only
(`verified`, `verification_plan.md` section 3). The seven campaigns of D-092 (mutation, property and own-model checks)
ran on sources whose tested modules 0.0.6 does not change, and found no survivor and no new defect. V3-14 passed on the
0.0.6 wheel (U-V30).

## 2. What carries over without a rerun

The rule is D-061d: a record counts for a later build when the files its subject depends on are unchanged since the
build it names. Under the release profile a manual record also has to name the version under test (D-083c, D-084a).

`docs/phase4/verification/carry_over_0.0.6.md` gives every live must and should row with its status on the build, the
evidence that carries over, and its Phase 4 handling. `docs/phase4/verification/checks/carry_over.py` generates it from
the audit and the manual-record index, and runs the currency tool against 2bfca49. Its `--self-test` passes 5 of 5
controls: the real inputs raise no problem, and four seeded faults are each reported or listed (a row without a
handling entry, a stale entry for a `verified` row, a passed record that does not stand, and a failed record that does
not stand, which is listed in its row and does not fail the run). `verified` by running.

What carries over, in short:

| Evidence | Carries over for 0.0.6 | Status |
|---|---|---|
| The release gate on 2bfca49: pytest 4439 passed, latency gate 8 of 8, bundle built, TR-01 and TR-02 passed | yes, it ran on the build | `verified` (D-096) |
| 20 of the 21 manual records of the index: PK-06 Linux, AX-05, OR-11, OR-12, LG-01, LG-04, and the Windows records PK-04, PK-05, PK-06, PK-02, PK-11, W7 (PK-01), W8 (PK-02, PK-11, UI-45) and the five latency runs (UI-45) | yes, they stand against 2bfca49 | `verified` (currency run in U-V30) |
| PF-01 on the laptop at checkout bbeed84 (failed, DEF-W-15) | no by D-061d: its files differ from 2bfca49 in the version strings only. D-100b keeps REQ-N-01 `failed`, so the failure carries as `inferred` | `verified` (currency run), `inferred` |
| Campaigns V3-02 to V3-07 and V3-10 on base ed64fdf | yes, 0.0.6 changes no module they test | `verified` (`phase3_report.md` section 3) |
| V3-14 on the 0.0.6 release wheel | yes, it ran on the build | `verified` (`tests/independent/m7/records/V3-14_0.0.6.md`) |
| AX-06 Narrator of 2026-10-20 on the 0.0.3 source | no: U-M8x changed the view and the legend | `verified` (D-082b) |
| The Windows gates of 0.0.4 and 0.0.5 | no: other builds. They stay platform evidence for those builds | `inferred` from D-061d |

The rows that need an action in Phase 4 are the 6 must rows that are not `verified` and the 17 should rows:

| Row | Status on 0.0.6 | Phase 4 handling |
|---|---|---|
| REQ-N-01 | failed | Known limit DEF-W-15, for the user to accept by name (K-2) |
| REQ-N-02 | failed | The W8 latency gate and three of five latency runs failed on the laptop (DEF-W-12, D-101). Known limit K-1. Check E-08 |
| REQ-N-05 | failed | Closed by name in D-100b: PK-02 by PK-06 runs 11 and 12, PK-01 by W7 (accepted by name, D-100c). The exit rests on that ruling (D-101) |
| REQ-N-06 | failed | Closed by name in D-100b: PK-05 (D-099a), PK-11 by run 11. W8's PK-11 failure is DEF-W-16 (S-1). The exit rests on that ruling (D-101) |
| REQ-N-16, REQ-N-24 | partial | The AX-06 record from the walkthrough closes both rows (R-1) |
| 11 should rows `partial` (REQ-F-09, F-22, F-24 to F-29, F-31, N-03, N-26) | partial | Tests pass. The user sees the behaviour in the walkthrough |
| 6 should rows `not tested` (REQ-N-20, N-29, T-12, L-02, L-06, L-09) | not tested | Allowed by `verification_plan.md` section 4 point 3. REQ-N-29 is Phase 5 (D-053b) |

## 3. The user acceptance test

### 3.1 The walkthrough

The walkthrough is `docs/phase4/design/uat_walkthrough.md` (Agent 1, U-S17). Its brief asks for the blank new-design
flow, the five examples with the D08 layer cue, typing previews and keyboard navigation, the result cards and badges,
the equation register, every export, the three themes, and AX-06. It names three points where the user judges rather
than ticks: whether the D08 view still reads as joined, whether the PDF report suits the user, and whether units and
wording read naturally. This plan does not repeat those steps.

### 3.2 The engineering checks

These checks ask for the user's own eyes and tools. U-V25 took the expected results from runs of the 0.0.5 release
wheel (SHA-256 `a56eaebb…6096`) in a scratch venv on Linux, unless the row names another source. U-V30 checked E-01,
E-05, E-06, E-07 and E-09 on the exports of the 0.0.6 release wheel (`fdb89189…0101`, V3-14's venv). For the other
values, U-V29 found that the 0.0.6 outcome files differ from those of 0.0.5 only in the version and the source hash
(D-097a), so they carry (`inferred`). PK-04 shows that the five examples compute the same values on the laptop at rel
1e-9 (D-098a), so these values should read the same on Windows (`inferred`). Mark each box: `[ ] pass`, `[ ] fail`, or `[ ] accept with note`.

| ID | What the user does | Expected result | Status of the expected result | Result |
|---|---|---|---|---|
| E-01 | Build identity. In PowerShell, run `Get-FileHash` on the wheel, then `pip list` in the venv, then `embodic-cli selftest`. | The hash equals the wheel SHA-256 of section 0 (PowerShell prints it in upper case). `pip list` shows `embodic 0.0.6`. The self-test prints `45 tests: 45 passed, 0 failed`. If the policy blocks `embodic-cli.exe` (DEF-W-16), run `python -m embodic.cli selftest`. | `verified` on the laptop for the 0.0.6 wheel (PK-06 runs 11 and 12, D-100a) and on Linux by U-V30 | [ ] pass [ ] fail [ ] accept with note |
| E-02 | Export the DXF ("complete board") of "Spiral, 12 coils, 16 poles" and open or import it in the CAD tool the user uses for board outlines. Measure the outline and the bore. | Units are millimetres. The outline is a 12-sided polygon 93.000 mm across flats. The bore is a circle of 25.000 mm diameter, drawn as two arcs. Copper is drawn as centre lines on layers named like `CU1_L1_PH_A_W500`, where `W500` is a 0.50 mm trace. Other layers are `BOARD_OUTLINE`, `CUTOUT`, `VIA_PAD`, `VIA_DRILL`, `PAD` and `PAD_DRILL`. | `verified` on Linux with ezdxf. `not tested` in any CAD tool or in KiCad (out of scope, D-009) | [ ] pass [ ] fail [ ] accept with note |
| E-03 | Export the DXF of "Spiral, 12 coils, 10 poles (D08)". In the CAD tool, measure the closest copper gaps on one layer. The edge gap is the centre-line distance minus the trace width that the layer name gives. | No two copper paths on one layer come closer than the 0.8 mm rule unless the design joins them. The gaps A2−/A1+, A2−/B1− and ring A to the A1+ stub are 0.800 mm. The phase rings are on L1 (`W1000`) and the legs on L2 (`W600`), so they cross only in plan view. This answers the user's report that D08 looks shorted. | `verified` on Linux. U-V16 measured the 0.0.3 export (D-078b), and the D08 DXF of the 0.0.5 wheel equals that file byte for byte after the stamp lines (my comparison in this unit) | [ ] pass [ ] fail [ ] accept with note |
| E-04 | Xcoil comparison. The user picks one serpentine or wave design and enters it in Xcoil v3 and in embodic, or loads the packaged serpentine or wave example, which are Xcoil's presets (D-016). Compare the copper, Ke, phase resistance, eddy loss and the DRC count. | The copper matches Xcoil's layout (GR-20, GR-21). Ke, R and eddy loss agree to 1e-9 rel. where both integrate the same copper (GR-22), so they read equal at the app's 3 significant figures (REQ-L-07). The recorded differences are the exceptions: on the default serpentine embodic's eddy loss is +0.699 % and its phase R +0.347 %, because embodic also counts the via-bus copper (XD-PHY-002, XD-PHY-003, D-029). In the overlap wave embodic counts interconnect copper that Xcoil leaves out: the tap stubs of a star connection (XD-WAVE-001, +48.2 % interconnect loss on that case) and the line leads of a delta (XD-WAVE-002). Xcoil's kw1 is phase A only. embodic shows the utilisation factor k_u instead (D-063a, D-063b). A spiral design has no Xcoil counterpart. | `verified` by the golden tests in the 0.0.5 release gate (REQ-F-34, REQ-F-35 `verified`) and by the rows of `tests/golden/expected_diffs/*.toml`. Agent 4's sign-off on those rows is still `pending` (Q-6) | [ ] pass [ ] fail [ ] accept with note |
| E-05 | Open the D08 example. Read "Line back-EMF constant, peak" and its badge, and compare it with the UGent thesis (D08). | 30.9 mV·s/rad, against the thesis's measured 0.031 V·s/rad. The OR-01 band is −8 % to +8 % + e_edge (`tests/unit/physics/test_oracles.py` l.93). The badge reads `not tested`. So do the other results built on the field and the EMF, such as Ke, Kt, K_v, torque, eddy loss and efficiency. In the registry of 0.0.5 and 0.0.6 EQ-05 and EQ-06 lack only one passed test each, EQT-05-O2 and EQT-06-O2, which is the D09 oracle OR-07 (F-OR07, D-047, decision K-3). R_ph reads `inferred`. J, δ and the interconnect loss read `verified`. The inductance reads `unresolved (estimate)` (decision K-4). | `verified` on Linux from the 0.0.5 release wheel: the PDF report and `load_registry()`. The value and its badge read the same in the D08 PDF of the 0.0.6 wheel (U-V30). That every field and EMF result inherits the badge is `inferred` from REQ-T-03 | [ ] pass [ ] fail [ ] accept with note |
| E-06 | Export the PDF report of D08 and of "Spiral, 12 coils, 16 poles". Read it as the user would use it (D-056g Q2). | Four pages. A header with `embodic_version 0.0.6`, `engine_version`, `registry_version`, `design_hash`, `generated_utc` and `drc_passed`. A "Key results" table with quantity, value and status. A "DRC summary" with the least clearance and the rule per check. An "Inputs" table with each field's provenance. A board drawing in mm. The report holds no EC-05 limitation text and no equation IDs (U-S11 Q2). The user judges whether that content is enough (decision P-1). | `verified` on Linux from the release wheel | [ ] pass [ ] fail [ ] accept with note |
| E-07 | Open "Wave, 16 poles, involute" and try to export its DXF, then its PDF. Open the same preset in Xcoil v3. | The DRC reports 186 violations. The PDF's "DRC summary" gives a least clearance of 0.199965 mm against the 0.200000 mm rule, for trace to trace and for trace to via. Xcoil shows the preset clean, because its DRC allows a 4 µm slack that embodic's rule D-006 removes (`engineering_verification_plan.md` l.285, D-034). The DXF export asks for a confirmation that lists the failures, with the focus on Cancel (REQ-F-33). The PDF and the README are written without it. The README prints `DRC: FAILED, 186 violations`, and the PDF prints `Board 1: FAILED, 186 violations` (D-045e). U-V25 wrote "Design rule check" here, which neither file prints. | `verified` on Linux from the release wheel (CLI exit 2 with `DRC_EXPORT_NOT_CONFIRMED` and the clearance value, then the PDF line). The dialog is `verified` by offscreen UI tests only. Xcoil's clean result is from the record, `not tested` by me | [ ] pass [ ] fail [ ] accept with note |
| E-08 | Feel the two known speed limits. Open the serpentine example, type in a field while it computes, and change a value of the default spiral several times. | The app may lag. On this laptop the team measured GUI gaps up to 255 ms on 0.0.4 and up to 258 ms on 0.0.6 against the 100 ms bound, in some runs and not in others (DEF-W-12, D-086d, D-099b). A full recompute of the default spiral takes 0.91 to 1.00 s p95 against 1.0 s, and its physics stage 0.62 to 0.66 s against 0.3 s (DEF-W-15, D-087). The user judges whether 0.0.6 is usable with these limits until Phase 5 (decisions K-1, K-2). | `verified` on the laptop (records named) | [ ] pass [ ] fail [ ] accept with note |
| E-09 | Pick one example. Find the design hash in the app, in the saved project file, in the SVG and DXF exports (open them in a text editor), in the PDF header and in the README. | The same `sha256:…` value everywhere. For "Spiral, 12 coils, 16 poles" it is `sha256:ac4fab5d…9c09`. This ties every output to one design (REQ-T-07, REQ-T-14). | `verified` on Linux from the release wheel's bundle export and `embodic-cli compute` | [ ] pass [ ] fail [ ] accept with note |

### 3.3 The records that the UAT produces

| ID | Record | Who writes it | What it closes |
|---|---|---|---|
| R-1 | AX-06 Narrator record on 0.0.6, with `embodic_version` 0.0.6 and `Windows laptop` as the platform, so that TR-01 counts it (D-083c) and the audit's `NEEDS` rule counts it (D-100b), indexed in `manual_records.json` | Fable, from the user's result in the walkthrough | REQ-N-16 and REQ-N-24 |
| R-2 | The UAT record: the build, the date, the laptop, and the result and note of every walkthrough step and every check E-01 to E-09 | Fable, from the user's boxes | the acceptance verdict A-1 |
| R-3 | Optional: a timed cold PK-06 walkthrough, if the user installs into an empty folder on a normal network | Fable | the Windows half of REQ-N-07 |

## 4. The decision sheet

Every item below belongs to the user. Where the decision log already holds a user decision, the sheet shows it, and
the Phase 4 question is whether it still holds for the accepted build. No option below is chosen in this plan. A cost
marked `unresolved` was not measured or researched in any record I read.

### Licences (D-069, D-081)

| ID | Decision | Options | What each option costs | Decision row |
|---|---|---|---|---|
| L-1 | The written offer for the Qt 6.11.2 and PySide6 6.11.2 source | (a) Keep it deferred: embodic stays a personal project used at the office, and no copy of the wheel or the bundle goes to another person (D-048c). (b) Prepare it now for the bundle: write the offer and keep the two source archives with the release (`dependency_licences.md` R5, R6). (c) Share only the wheel. pip then downloads Qt from PyPI, not from the embodic project. (d) Buy a commercial Qt licence. | (a) Nothing now. The offer is needed before the first copy goes to someone else (Fable's reading, `inferred`, not legal advice). (b) One docs and tools unit, storage for the archives (size `unresolved`), and a duty to keep the source available "for as long as needed" (GPL-3.0 section 6 d, Q13). Agent 5 recommends a lawyer's review. (c) The receiver needs Python and a network. The obligations then fall on the PyPI copy (`inferred`, `dependency_licences.md`). (d) Money (`unresolved`, not researched). | D-048c, D-069 |
| L-2 | The Qt third-party notices for the bundled modules | (a) Defer with L-1, because nothing is distributed. (b) Fetch Qt's list (`https://doc.qt.io/qt-6/licenses-used-in-qt.html`, refused by the cloud proxy) from a machine that reaches it, and write the list. (c) Read the `qt_attribution.json` file of every bundled module at tag v6.11.2 (six were read). | (a) Nothing now. (b) One evidence unit, and network access the cloud lacks. (c) A larger evidence unit. Whether the PyPI binaries hold each library stays `unresolved` without Qt's own statement. | D-069 |
| L-3 | embodic's own licence | (a) Keep the current state: no licence chosen, all rights reserved (D-048b). (b) MIT. (c) Apache-2.0. (d) GPL-3.0. (e) A proprietary licence. | (a) Nobody else may reuse the code (`inferred`, not legal advice). (b), (c) and (d) need no change to the Qt plan. (d) also gives every receiver the embodic source. (e) needs a clause that lets the user replace and debug the Qt files, and a lawyer (`dependency_licences.md`, "The embodic licence", all `inferred`). Any option: the bundle carries embodic's own source (`tools/build_bundle.py` CHECKLIST, "source"), so whoever gets the bundle gets the code. | D-015, D-048b |

### Code signing (DEF-W-14, DEF-W-16)

| ID | Decision | Options | What each option costs | Decision row |
|---|---|---|---|---|
| S-1 | How Windows starts embodic where Application Control blocks unsigned programs: the PyInstaller bundle (DEF-W-14) and the launchers `embodic.exe` and `embodic-cli.exe` that pip writes (DEF-W-16). D-100d names two fixes of DEF-W-16: code signing, or `python -m` as the documented Windows route | (a) No signing. `python -m embodic.cli` and `python -m embodic.ui.app` become the documented Windows route, because they run through the signed `python.exe` (D-098b). The bundle stays unsigned. (b) Buy a code-signing certificate and sign the bundle in `tools/build_bundle.py` and the launchers. (c) The user changes the policy on the user's own machine. (d) Decide at the first distribution, with L-1. | (a) A docs unit: INSTALL.md and the Thai guide name `python -m` first on Windows. INSTALL.md at 2174f1b already gives it as the fallback (D-100a). `python -m embodic.cli` passed steps 5 and 6 on the laptop (run 12, D-100a). `python -m embodic.ui.app` was not opened on Windows (`not tested`). The bundle ran on 0.0.6 (D-099a), but the policy's decisions are not uniform (D-099c). (b) The certificate price and the identity check (`unresolved`), and one tools unit. pip writes the launchers at install time on the user's machine, so how to sign them is `unresolved`. Whether a signed file passes the laptop's policy is `unresolved`, because the record does not name the policy. (c) Less protection on that machine. Fable changes no security setting (D-086c). (d) Nothing now. DEF-W-16 stays open as a known limit (D-100d). | D-086c, D-098b, D-100d, new row |

### The GitHub repository (D-064, D-065, order 9)

| ID | Decision | Options | What each option costs | Decision row |
|---|---|---|---|---|
| G-1 | The visibility of github.com/mrfinler/Embodic | (a) Private. (b) Public. | Today's visibility is not in any record (`unresolved`). The cloud sessions have no GitHub access to the repository (D-065b). (a) Nothing. Others need an invitation. (b) Anyone can read and clone all 1731 tracked files and the whole history (`verified`, `git ls-files`, 0593feb). That includes the decision log with the user's chat answers, two frames of a third-party Instagram post and an ECM board image in `docs/phase1/evidence/reference_images/` (reuse rights `unresolved`), Xcoil screenshots, the brand assets, and the author name and address of 1096 of 1101 commits (`verified`, `git log`). Removing a file from the history afterwards needs a history rewrite and a force push. The licence L-3 decides what readers may reuse. Order 9 forbids public publishing without the user's approval. | D-065b, new row |
| G-2 | What is pushed | (a) As planned: main and the tags `v0.0.4`, `v0.0.5` and `v0.0.6`, unit branches stay local (D-065b, D-091d, D-097c). (b) Also publish the wheel as a GitHub release. (c) Push nothing more until L-3 and G-1 are decided. | (a) Nothing extra. (b) That is distribution: it brings L-1 (c) and L-3 forward. (c) The laptop and the cloud stay the only full copies of `v0.0.4`, `v0.0.5` and `v0.0.6` (`inferred` from D-091d). A changed author address would rewrite every commit hash, and the records that name commits (D-061d) would no longer match (`inferred`). | D-065b, D-091d |

### Known limits that the user accepts by name

| ID | Limit | What the user sees in 0.0.6 | Options | What each option costs | Decision row |
|---|---|---|---|---|---|
| K-1 | DEF-W-12: Windows GUI latency, intermittent | REQ-N-02 is `failed` through the Windows latency runs of 0.0.6 (D-099b, D-101). Gaps up to 258 ms against the 100 ms bound in some runs (D-086d, D-099b), `inferred` cause: the worker and the GUI thread share the GIL (D-076c). Check E-08 | (a) Accept by name. The fix stays in Phase 5 as the user decided (D-076d). (b) Fix it before acceptance: a compute process separate from the GUI (D-076d, D-084d). | (a) The user lives with the lag until Phase 5. (b) A design unit, an implementation unit, a new release and the Windows reruns (`unresolved` size). Phase 4 restarts on the new build. | D-076d |
| K-2 | DEF-W-15: REQ-N-01 not met on the laptop | Physics p95 0.62 to 0.66 s against 0.3 s, and the full recompute at its 1.0 s bound (D-087). REQ-N-01 stays `failed` | (a) Accept by name. Phase 5's first unit ports the physics kernels (U-D27 option B), as the user decided (D-091a). (b) Fix it before acceptance. | (a) The user lives with about 1 s per recompute. (b) The same unit as (a), done now, then a new release, PF-01 again on the laptop, and a restart of Phase 4. | D-087, D-091a |
| K-3 | OR-07 and gap G2: the D09 phase EMF oracle is out of band | OR-07 is +18.7 % on variant A and stays a strict expected failure. Variant C read from the D09 figure gave −4.79 to −5.09 %, recorded as evidence and not as a pass (D-045a, D-050c). G2 (D09's Table 1 length against its drawing) has no source (D-049b). Every back-EMF result shows `not tested` (check E-05) | (a) Accept by name. (b) The user supplies a source that closes G2. (c) A measured board (see K-4). | (a) The back-EMF badges stay `not tested`. (b) An evidence unit and an oracle unit, then a registry change, so a new release (`inferred`). (c) As K-4. | D-045a, D-049b, D-050c |
| K-4 | EQT-14-O2: no built board | The inductance shows `unresolved (estimate)`. The F-OR07 closure that needs a measurement stays `not tested` (D-048f) | (a) Accept by name. (b) Build a board and measure it with the plan of `docs/phase3/engineering/engineering_verification_plan.md` section 3 (rows M1 to M5). | (a) Nothing. (b) A board, the instruments that plan lists, and the evidence and oracle units after the measurement (`unresolved` cost). | D-048f |

The changelog lists more known limits that 0.0.6 carries from 0.0.2 to 0.0.5 (`CHANGELOG.md`, "Known
limits"): the serpentine build at near-zero clearance (DEF-M6b-01), the one-off update of about 330 ms at example open
(DEF-U-M6a-01), EQ-28 and EQ-29 without a port, via drills not drawn, and the layer cue's drawing cost, which is not
measured on Windows. The wave example's 186 violations (check E-07) wait for new example values in Phase 5
(`engineering_verification_plan.md` l.285). Fable has ruled each of them already. The user can raise any of them
during the walkthrough.

### The report, the backlog and the verdict

| ID | Decision | Options | What each option costs | Decision row |
|---|---|---|---|---|
| P-1 | The PDF report's content (U-S11 Q2, ruled "reviewed at Phase 4 acceptance") | (a) Keep the content of check E-06. (b) Add each row's limitations, such as the EC-05 note of REQ-T-16, to "Key results". | (a) Nothing. (b) An Agent 1 ruling, a code change in `src/`, so a new release and a rerun of the affected checks. | D-056g |
| B-1 | The order of the Phase 5 backlog after its first unit | The first unit is decided: the physics kernels (D-091a). For the rest, see the list below. One possible order follows the records: speed first (D-084d, D-087). Another puts features first, or robustness first. | No record estimates the size of any item (`unresolved`), except "one gated unit each" for the Rust kernels (D-084d). | D-076, D-084, D-088, D-091 |
| A-1 | The acceptance verdict on the named build | (a) Accept. (b) Accept with notes: each note becomes a known limit or a Phase 5 item. (c) Do not accept: section 5 applies. | (a) and (b) close Phase 4. (c) A fix wave and a new release. | new row |

The Phase 5 items in the decision log, in the order they were recorded (`verified` by reading each row):

1. DEF-M6b-01: the serpentine build at near-zero clearance takes 15 to 17.5 s against 10 s (D-050b).
2. DEF-U-M6a-01 and DEF-U-M8a-02: the one-off update at example open and the off-CPU part of the open gap (D-050a,
   D-056k, D-066a).
3. REQ-N-29: the coverage step (D-053b).
4. REQ-F-03 (d) option M4, and more than one via per transition (D-054c, D-054d).
5. DEF-U-M8o-01: GUI-thread float arithmetic about 5 times slower after an example opens (D-067b).
6. `save_project` and `outcome_to_json` of a design that has no file form, reachable from the Python API only (D-072).
7. DEF-W-12: a compute process separate from the GUI process (D-076d).
8. Via drills drawn in the geometry view (D-079c Q3).
9. REQ-N-09 for dataclasses, as a requirement proposal (D-084a).
10. Rust kernels behind the Python API for `discretise_path`, the coil-eye search and the serpentine fit, and the GUI
    worker's repeated coil-eye search (D-084d).
11. Qt objects without a parent in reference cycles in the product (D-088).
12. DEF-W-15: the physics kernels, gated, with PF-01 rerun on the laptop. This is the first unit (D-091a).

## 5. Exit from Phase 4 to Phase 5, and what a failed step does

Phase 4 ends on one named build when all of these hold:

1. Every walkthrough step and every check E-01 to E-09 has a result: pass, or accept with a note.
2. Record R-1 (AX-06) is in the index and counted by TR-01 for the build, or the user declined the walkthrough step and
   the reason is recorded (`verification_plan.md` section 4 point 3).
3. Every failed step has a defect row with a ruling, as below. No failed step is left without one.
4. The user's answers to L-1 to L-3, S-1, G-1, G-2, K-1 to K-4, P-1, B-1 and A-1 are in the decision log, quoted in the
   user's words.
5. Fable writes the decision row "Phase 4 accepted on build X" and the UAT record R-2.
6. Every push after the acceptance follows G-1 and G-2 (order 9).

A failed step goes through these steps:

1. The user notes what they saw, with a screenshot or the log file that the walkthrough names.
2. Fable opens a defect row `DEF-UAT-nn` in the UAT record R-2. The row names the check, the build and what was
   expected.
3. Fable rules the row into one of four kinds:
   - A product defect that needs a change in `src/` or `resources/`. A fix wave follows, then a new release with a new
     version (D-082), its release gate and the Windows checks that its D-061d ruling names. Section 0's steps run, and
     the user repeats E-01 and every check whose subject files changed.
   - A defect in tests, tools or documents only. It is fixed without a new release, because the package source hash
     stays the same (D-082). The user repeats only the affected check.
   - A limit the user accepts. It joins section 4 as a named limit and the Phase 5 list.
   - A wrong expectation in this plan. The expected value is corrected with its source. A bound or a rule is never
     loosened to make a step pass (order 11).
4. Phase 4 restarts on the new build only for a product defect. The other three kinds keep the build.

## How to check this plan

- `python3 docs/phase4/verification/checks/plan_refs.py` checks that every decision row, requirement, DEF ID, XD ID and
  repository path in this file resolves in the checkout, and that the prose has no semicolon, long dash or curly quote.
  It reports 0 problems on this file, and its `--self-test` finds 7 of 7 planted faults (`verified` by running).
- `python3 docs/phase4/verification/checks/carry_over.py --check` and `--self-test` prove the carry-over table.
- `python3 docs/phase3/verification/checks/req_audit.py --target 0.0.6 --check` proves the audit current.

## Open questions for Fable

- Q-1. The brief cites "D-063 Q2" for the PDF review. D-063 has no Q2. The ruling is D-056g: "U-S11 ... Q2: the PDF
  keeps its F1 content, reviewed at Phase 4 acceptance" (`docs/phase3/design/fix_wave_f1.md` l.399). This plan uses
  D-056g.
- Q-2. GitHub. No record states the repository's visibility. D-067c records a push of main at 080c2c7, and Fable's
  checkpoint of 2026-10-21 says GitHub holds main 6555588 and `v0.0.2`. Which is current, and is the repository
  private?
- Q-3. Answered by D-100c: V3-14 is rerun on the 0.0.6 wheel. U-V30 ran it: every class finds its plant, 0 findings
  (`tests/independent/m7/records/V3-14_0.0.6.md`).
- Q-4. Answered: DEF-UV21-01 is closed (D-093c, D-094a). TR-01 lists the failed records of the index as accepted.
- Q-5. Answered by D-100b: U-V30 indexed the Windows records of 0.0.6. REQ-N-04 and REQ-N-07 are now `verified`.
- Q-6. Check E-04 relies on `tests/golden/expected_diffs/*.toml`. Its rows carry `agent4_signoff = "pending"`, and
  XD-PHY-001 to XD-PHY-010 also carry `agent2_signoff = "pending"`. A unit for both sign-offs would make E-04's
  expected result rest on reviewed rows.
- Q-7. The team has never opened an embodic DXF in KiCad or another CAD tool. E-02 and E-03 are the first such runs.
  If the user's tool rejects the R12 file, is that a product defect (REQ-F-16) or a limit of the user's tool?
