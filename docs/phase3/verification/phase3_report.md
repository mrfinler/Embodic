Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5 (unit U-V22, 2026-10-22, brought in line with
D-100 by unit U-V30, 2026-10-22)

# Phase 3 report: verification of release 0.0.6

This is the English Phase 3 report that `verification_plan.md` section 4 asks for. Fable gives the user a Thai summary
of it. The named build is release 0.0.6. Releases 0.0.4 and 0.0.5 came before it, and this report replaces their
records where they differ. U-V30 applied D-100, Fable's ruling of the list that U-V22 gave: the Windows records of
0.0.6 are in the manual-record index, the audit applies the `NEEDS` rule of D-100b, and V3-14 ran on the release wheel.

Every claim carries one status: `verified`, `inferred`, `assumption`, `unresolved` or `not tested`. A claim that cites a
decision row or a record and carries no label is `verified` by reading that row or record. I ran my own checks on Linux
in the cloud container. Every Windows result in this report is Fable's, from `docs/phase3/fable/windows_campaign_w1.md`,
`docs/phase3/fable/windows_campaign_w2.md`, `docs/phase3/fable/PK-06_windows_0.0.6.md` or the decision row they name. I
ran nothing on Windows (order 8).

## The exit criteria after D-100

| Point of section 4 | Holds on 0.0.6 | Why, in one line |
|---|---|---|
| 1. Every live must row `verified`, except the rows of point 3 | not yet: REQ-N-16 and REQ-N-24 wait for AX-06 | The audit gives 67 of 73. D-100b names REQ-N-01 and REQ-N-02 as exceptions and closes REQ-N-05 and REQ-N-06 by name, which the audit keeps `failed` through the W7 and W8 records |
| 2. The Windows campaign and the campaigns verified by a run with a record | not yet: W6 waits for the UAT session | W4 and W5 hold, D-100c accepts W7 and W8 by name, and V3-14 passes on the 0.0.6 wheel |
| 3. Items that may stay `not tested`, each with its reason | yes, except AX-06 | OR-11c joins the list (D-100b). AX-06 may stay `not tested` only if the user declines it |
| 4. Every Phase 3 DEF row closed, accepted by name, or moved to Phase 5 | yes, by D-100d | DEF-W-16 and DEF-US18-01 are accepted by name, DEF-UE16-02 is fixed, and DEF-W-10 and DEF-W-11 are retired IDs with no record |

D-100b lets Phase 4 start with REQ-N-16 and REQ-N-24 `partial`. No verdict A-1 is given before AX-06 has run or the
user has declined it. D-100c gives W6 a scripted part at the start of the UAT session and a human part in the
walkthrough, and A-1 waits for both.

No DEF row that is open, accepted by name or moved to Phase 5 reports a wrong computed value (`verified` by reading
every row of section 4). In the cloud the release gate passed 11 of 11. On Windows PK-04 matched the Linux reference at
1e-9 on all five examples (D-098a), and PK-06 passed in runs 11 and 12 (D-100a).

Decisions that Phase 4 needs, by owner:

- Fable:
  1. REQ-N-05 and REQ-N-06 are `failed` in the audit. The W7 record (PK-01) and the W8 records (PK-02 and PK-11)
     failed, and the audit gives `fail` evidence to every ID that a failed record names, accepted or not. That rule
     also keeps REQ-N-01 `failed` (D-091a). D-100b closes both rows by name, and D-100 names no audit exception for an
     accepted record, so I applied none. Confirm that the exit rests on the name ruling, or rule an audit rule.
  2. The latency failure of W8 (the N02-10 cancel case, DEF-W-12) has no index entry. An entry would make REQ-N-02
     `failed`, and D-100b keeps the row at its status. This is my reading of the brief (`inferred`). Confirm it, or add
     the entry.
  3. W6. Prepare the launcher for the scripted part at the start of the UAT session (D-100c).
  4. V3-14 hashed 5 of the 8 brand originals of the 0.0.1 run, because the user's brand folder is not in the container
     (section 3). Copy the folder into the container for a full rerun, or accept the 5.
- The user:
  1. Run AX-06 (Narrator) on 0.0.6, or decline it. It is a step of the walkthrough (D-097c).
  2. Decide S-1 for DEF-W-16: code signing, or `python -m` as the documented Windows route (D-100d). Signing also
     covers the bundle (DEF-W-14).
  3. Decide whether to build the canvas keys of DEF-US18-01 or remove them from the keyboard map (walkthrough step
     3.10).
  4. Accept by name the known limits K-1 (DEF-W-12) and K-2 (DEF-W-15), or ask for fixes before acceptance.

## The named build

| Field | Value | Status |
|---|---|---|
| Version and tag | 0.0.6, tag `v0.0.6` on 2bfca49 (D-096) | `verified` (`git rev-parse v0.0.6^{}`) |
| Release gate | 11 of 11 gates, pytest 4439 passed, 3 skipped, 9 deselected, 3 xfailed, latency gate 8 passed | `verified` (`gate_release_2bfca49.log` l.798, l.817, l.868) |
| Wheel | `embodic-0.0.6-py3-none-any.whl`, SHA-256 `fdb89189161d14b71433c4e35861d4e4d56fc6a7e64383f96ba13e27ba450101` | `verified` (`sha256sum`) |
| Package source hash | `db089e71…75cb` in the wheel's evidence, in the unpacked wheel, and in main 0abe719's `src/embodic` | `verified` (`package_source_sha256` on both trees, U-V22) |
| Change from 0.0.5 | `src/embodic/__init__.py` (the version) and 7 files under `src/embodic/ui/` | `verified` (`git diff --stat v0.0.5 v0.0.6 -- src`) |

Main 2174f1b is release 0.0.6 plus 40 changed files: 26 under `docs/`, 12 under `tests/`, `tools/build_bundle.py` and
`CHANGELOG.md` (`verified`, `git diff --name-only v0.0.6 2174f1b`). No file under `src/` changed (`git diff v0.0.6
2174f1b -- src` is empty), so V3-13 holds on it.

## 1. The requirement audit of 0.0.6 (V3-15)

`python3 docs/phase3/verification/checks/req_audit.py --target 0.0.6` writes `docs/phase3/verification/req_audit.md`.
That file is the full table, one row per requirement with its evidence. The 0.0.5 audit is in `req_audit_0.0.5.md`.
The inputs are the two REQ reports and the log of Fable's release gate on 2bfca49, copied gzipped into `inputs/`
(byte-identical to `/home/claude/release_0.0.6/` after `gunzip`, `verified` with `cmp`), the test sources of `git
archive 2bfca49 tests`, the V3-01 rulings v13 to v21 and v30, and the manual-record index `manual_records.json` of
U-V30. The two reports hold 4454 records: 4447 passed, 6 skipped, and 1 not run in either process, the manual PF-01
test (`verified`).

The index holds 15 entries (`docs/phase3/verification/manual_records_0.0.6_windows.md`). Eleven passed and name 0.0.6:
PK-06 Linux, AX-05, OR-11, OR-12, LG-01, LG-04, and the Windows records PK-04, PK-05, PK-06, PK-02 and PK-11. Four
failed and carry `accepted`: PF-01 (D-091, 0.0.5), and PK-01 (W7), PK-02 (W8) and PK-11 (W8) (D-100). The note of
each `embodic_version` now names the platform first.

The `NEEDS` rule of D-100b. A `NEEDS` ID counts when the index holds a current passed record of it from the machine
that `NEEDS` names. Current means that the version is that of the audited commit, as TR-01 reads it (D-083c, D-084a).
The machine is the first item of the note: `Windows laptop`, or an item that names the `FEA`. The self-test plants a
record from the wrong machine (PK-04 and the OR records moved to `Linux container`), a stale record (PK-04 stamped
0.0.5), and the Linux PK-06 record alone. Each leaves its ID blocked and its row `partial`, and the real index does not
(`verified`, `--self-test` passes 12 of 12). PK-01 stays blocked, because its only Windows record failed.

The UI-36 to UI-45 text (item 5 of U-V30's brief). U-M9f added the IDs to the docstrings of
`tests/ui/qt_shell/test_n02_typing_preview.py` in 4aa1629, after the release. `git diff 2bfca49 main` on that file
changes 20 lines and removes 9, and every changed line is inside a docstring (`verified`, reading the 103-line diff).
The audit removes every docstring from both versions and compares the two syntax trees (`same_code`). They are equal,
so the code that ran in the 0.0.6 gate is the code that now names the IDs. My ruling is that the text counts for 0.0.6
as `file` evidence. The audit reads that file at 4aa1629 and stops if `same_code` ever fails. UI-36 to UI-45 now have
`file` evidence, and REQ-N-02 stays `partial` through its V3-01 ruling (DEF-W-12 on Windows), as D-100b keeps it.

Counts (`verified` by running, with CPython 3.13.16 to write and CPython 3.11.17 for `--check`, byte-identical):

| Rows | verified | partial | failed | not tested | withdrawn |
|---|---|---|---|---|---|
| all 110 | 67 | 17 | 3 | 7 | 16 |
| must 73 | 67 | 3 | 3 | 0 | 0 |

Planned-test evidence: eqt 17, fail 4, file 42, gate 9, name 198, none 10, record 7.

Against U-V22's audit of 0.0.6, six rows changed status (`verified` by a row-by-row diff). REQ-F-11, REQ-N-04 and
REQ-N-07 became `verified`: the `NEEDS` rule clears OR-11, OR-12, PK-04 and PK-06, and V3-01 v30 re-rules REQ-N-04 and
REQ-N-07 on their Windows records. REQ-N-05 and REQ-N-06 became `failed` through the W7 and W8 records. REQ-N-02 kept
`partial` with new `file` evidence. No other row changed. No `verified` row lost its ruling. `req_audit.py
--self-test` passes 12 of 12 on the 0.0.6 target.

The rows by status:

- Must, `verified` (67): REQ-F-01, REQ-F-02, REQ-F-03, REQ-F-04, REQ-F-05, REQ-F-06, REQ-F-07, REQ-F-08, REQ-F-10,
  REQ-F-11, REQ-F-12, REQ-F-13, REQ-F-14, REQ-F-15, REQ-F-16, REQ-F-18, REQ-F-19, REQ-F-21, REQ-F-23, REQ-F-32,
  REQ-F-33, REQ-F-34, REQ-F-35, REQ-F-36, REQ-F-37, REQ-F-38, REQ-F-39, REQ-F-40, REQ-N-04, REQ-N-07, REQ-N-08,
  REQ-N-09, REQ-N-10, REQ-N-11, REQ-N-12, REQ-N-13, REQ-N-14, REQ-N-15, REQ-N-17, REQ-N-18, REQ-N-19, REQ-N-21,
  REQ-N-23, REQ-N-25, REQ-N-27, REQ-N-28, REQ-T-01, REQ-T-02, REQ-T-03, REQ-T-04, REQ-T-05, REQ-T-06, REQ-T-07,
  REQ-T-08, REQ-T-09, REQ-T-10, REQ-T-11, REQ-T-13, REQ-T-14, REQ-T-15, REQ-T-16, REQ-L-01, REQ-L-03, REQ-L-04,
  REQ-L-05, REQ-L-07, REQ-L-08.
- Must, `partial` (3): REQ-N-02, REQ-N-16, REQ-N-24.
- Must, `failed` (3): REQ-N-01, REQ-N-05, REQ-N-06.
- Should, `partial` (11): REQ-F-09, REQ-F-22, REQ-F-24, REQ-F-25, REQ-F-26, REQ-F-27, REQ-F-28, REQ-F-29, REQ-F-31,
  REQ-N-03, REQ-N-26.
- Should, `not tested` (6): REQ-N-20, REQ-N-29, REQ-T-12, REQ-L-02, REQ-L-06, REQ-L-09.
- Could, `partial` (3): REQ-F-17, REQ-F-20, REQ-N-22.
- Could, `not tested` (1): REQ-F-30.
- Withdrawn (16): REQ-K-01 to REQ-K-16 (D-009).

The must rows that are not `verified`:

| Row | Status | Evidence on 0.0.6 | What keeps it from `verified` | Point 1 after D-100b |
|---|---|---|---|---|
| REQ-N-01 | failed | PF-01 `fail` (Fable's laptop record, 0.0.5 source), PF-04 `file` | PF-01 on the laptop failed: physics p95 0.617 to 0.663 s against 0.3 s (D-087). DEF-W-15, moved to Phase 5 by the user (D-091a). The compute code is unchanged since 0.0.5, so the failure carries to 0.0.6 (`inferred`) | named exception, known limit K-2 |
| REQ-N-02 | partial | UI-05 and UI-02 `name`, UI-36 to UI-45 `file` | The V3-01 ruling (v18) finds every clause asserted on Linux. On Windows DEF-W-12 fails intermittently (D-099b) and is in Phase 5 (D-076d) | named exception, known limit K-1 |
| REQ-N-05 | failed | PK-01 `fail` (W7), PK-02 `fail` (W8) | W7 ended 5 of 6: `tests/bundle` compared the 0.0.5 bundle with the 0.0.6 source (D-098c). In W8 the PK-02 tests could not start the launcher (DEF-W-16, D-099a). PK-02 passed in runs 11 and 12 (D-100a) | closed by name: PK-02 by runs 11 and 12, PK-01 by W7 (D-100c) |
| REQ-N-06 | failed | PK-03 `name`, PK-05 `file`, PK-10 `gate`, PK-11 `fail` (W8) | In W8 the PK-11 test could not start the launcher (DEF-W-16). PK-11 passed in run 11, and PK-05 passed on Windows (D-099a) | closed by name: PK-05, PK-11 by run 11 |
| REQ-N-16 | partial | AX-06 `file` | AX-06 (Narrator) has no run on 0.0.6. The 0.0.3 record does not stand (D-082b) | waits for AX-06 |
| REQ-N-24 | partial | UT-MOD-03 `file`, AX-06 `none` | The same AX-06 run as REQ-N-16 | waits for AX-06 |

## 2. The Windows record

The machine is the user's laptop: Windows 11 Home Single Language, build 26300, 18 logical CPUs, 15.4 GB RAM,
PowerShell 5.1, CPython 3.11.9 from the python.org NuGet package inside `%USERPROFILE%\Desktop\embodic\.python`.
Fable ran every step through the Claude desktop app, except the 0.0.5 and 0.0.6 gate chains and the PK-06 rerun, which
the user started (D-093a, D-098, D-100a). The logs are in the git-excluded folder `_campaign` on the laptop. I did not
read them. I read Fable's three records and the decision rows.

### W1: install, self-test and PK-04 on the 0.0.1 wheel (2026-10-17)

| Step | Time | Output |
|---|---|---|
| Python 3.11.9 NuGet package, download | 58.1 s | 17,478,009 bytes, `venv` and `ensurepip` import |
| PK-06 run 1 (cold pip cache), steps 1 to 6 | 4154.5 s to the first computed example | step 3a took 4137.15 s at about 0.03 MB/s. Design hash `ac4fab5d…9c09`. Self-test `45 tests: 45 passed, 0 failed`. PK-06 failed on the network only |
| PK-06 run 2 (warm cache) | 21.57 s to the first computed example | self-test 45 of 45 in 9.26 s. PK-06's 10 minutes met |
| `embodic --smoke` on the real display | 6.83 s | the window opened, loaded D08, computed and exited 0 |
| PK-04 | - | failed as written: hashes over float bytes (DEF-W-02), a near-zero sample (DEF-W-03), and the violation order (DEF-W-01). The numbers agreed |
| Activate.ps1 under the Restricted policy | - | blocked (DEF-W-04) |

### W2: releases 0.0.2 to 0.0.6 (2026-10-18 to 2026-10-22)

| Release | Check | Result | Row |
|---|---|---|---|
| 0.0.2 | PK-06 cold and warm | 471 s and 20 s to the first example, self-test 45 of 45 both times | D-071e |
| 0.0.2 | Release profile, run 2 (2 h 31 min) | 6 of 7, pytest 4103 passed, 3 failed: PR-08 negative zero (a real defect, fixed in 0.0.3) and two latency tests | D-073 |
| 0.0.3 | Release profile of 5f814d4 | main gate 4198 passed, latency gate 2 of 6 failed | D-076a |
| 0.0.3 | Latency tests alone, ten runs | UI-05 over 100 ms in 1 of 10, N02-10 arrival in 4 of 10, up to 218 ms | D-076c |
| 0.0.3 | Narrator AX-06 | the user reported it passed. It does not stand for 0.0.4 or later | D-078a, D-082b |
| 0.0.4 | PK-06 warm (run 6) | 26.3 s to the first example, total 35.8 s, self-test 45 of 45 | D-085a |
| 0.0.4 | PK-04 | all five pass with U-V20's tool | D-086a |
| 0.0.4 | Commit and release profiles | 5 of 6 and 6 of 8. Eight failures came from CRLF checkouts (DEF-W-13), and `tests/bundle` was blocked (DEF-W-14) | D-086b, D-086c |
| 0.0.4 | Latency A/B, without and with the layer cue | 10 of 10 pass, arrival medians 40 and 41 ms | D-086d |
| 0.0.5 | PF-01 (source of 0.0.5) | failed: full recompute p95 0.913 to 1.003 s against 1.0 s, physics p95 0.617 to 0.663 s against 0.3 s (DEF-W-15) | D-087 |
| 0.0.5 | PK-06 warm (run 7) | 21.2 s to the first example, `embodic 0.0.5`, self-test 45 of 45 | D-090d |
| 0.0.5 | PK-04 | all five pass | D-090d |
| 0.0.5 | Commit profile | 5 of 6, pytest 3 failed: two colophon tests (DEF-UV27-01) and `tests/bundle` on the 0.0.4 bundle | D-095a |
| 0.0.5 | Release profile | 7 of 8, pytest 5 failed: two colophon tests and three `tests/bundle` tests blocked (DEF-W-14). Latency gate 8 of 8 | D-095b |
| 0.0.5 | Latency tests alone, five runs | 3 of 5 pass, N02-10 arrival 125 ms and UI-05 139 ms in the others | D-095c |
| 0.0.6 | Sync | head 6ac95ac, tag `v0.0.6` on 2bfca49, bundle and wheel SHA-256 match, 0 CRLF files | D-098a |
| 0.0.6 | PK-04 | all five examples pass at rel 1e-9 against U-V29's reference | D-098a |
| 0.0.6 | PK-06 warm (run 8) | steps 1 to 4 ran in 25.7 s. Every `embodic-cli` call failed to start: Application Control blocked the launcher (DEF-W-16). The old script logged exit 0 for those steps | D-098b |
| 0.0.6 | Commit profile (W7) | 5 of 6, pytest 1 failed (`tests/bundle` against the 0.0.5 bundle), 4181 passed. The colophon tests pass | D-098c |
| 0.0.6 | Release profile (W8, 09:30 to 11:45 with the latency runs) | 6 of 8. Bundle built in 65.2 s. Pytest 3 failed (PK-02 twice and PK-11, launcher blocked, DEF-W-16), 4349 passed. `tests/bundle` 6 of 6, the first PK-05 pass on Windows. Latency gate failed 1 test (N02-10 cancel case 153 ms). TR-01 and TR-02 pass | D-099a |
| 0.0.6 | Latency tests alone, five runs | 2 of 5 pass, N02-10 arrival 114, 199 and 258 ms in the others (DEF-W-12) | D-099b |
| 0.0.6 | PK-06 runs 9 and 10 | not valid: the PowerShell alias `cli` (Clear-Item) shadowed the helper `Cli` of Fable's script, so no embodic command ran | D-100a |
| 0.0.6 | PK-06 run 11, `embodic-cli` as INSTALL.md writes it | passed: 22.32 s to the first computed example, design rule check passed, SVG written, self-test 45 of 45 | D-100a |
| 0.0.6 | PK-06 run 12, `python -m embodic.cli` | passed: 19.29 s to the first computed example, self-test 45 of 45. `outcome.json` byte-identical to run 11, `board.svg` differs only in `generated_utc` | D-100a |

Runs 11 and 12 used a new folder and a new venv each, the hashed lock file `requirements\py311.txt`, and the wheel with
`--no-deps`. The pip cache was warm. The policy that blocked `embodic-cli.exe` in run 8 and in W8 let it run in run 11,
so its decisions are not uniform (cause `inferred`, D-100a).

### Which Windows rows count for 0.0.6

0.0.6 changes `src`, so its Windows checks run again on the 0.0.6 wheel (D-095d). These rows count for 0.0.6:

- The sync, PK-04 (passed), W7 (5 of 6, accepted by name), W8 (6 of 8, accepted by name, PK-05 passed), the five
  latency runs (2 of 5), and PK-06 runs 11 and 12 (passed). D-100a rules that runs 11 and 12 also meet the Windows
  cells of PK-02 and PK-11.
- PK-06 run 8 counts as a result that did not pass. Runs 9 and 10 count as nothing.
- PF-01 counts as failed. It ran on the 0.0.5 source, its compute code is unchanged in 0.0.6 (`verified` by the diff),
  and the index lists it as accepted by D-091 and does not count it (TR-01, `verified`).

No 0.0.4 or 0.0.5 run counts as a pass for 0.0.6. These have no Windows run on 0.0.6: AX-06, the W6 real-display rows,
the PK-06 cold run (none since 0.0.2), `python -m embodic.ui.app`, and Windows high contrast with the layer cue
(D-083b).

## 3. The V3 campaigns

| ID | Verdict | Status on 0.0.6 | Record |
|---|---|---|---|
| V3-01 | Must-row rulings: 67 rows `checks` (the 67 `verified` rows), REQ-N-01 `fails`, the other 5 `partial` with a named gap (U-V13 to U-V21, U-V30) | stands: the audit finds every pinned test source unchanged at 2bfca49 (`verified`). U-V30 re-ruled REQ-N-04 and REQ-N-07 on their indexed Windows records | `tests/independent/m7/v3_01_rulings_v30.py` and earlier |
| V3-02 | DRC mutants: 14 of 14 killed on 0.0.5 | stands: `src/embodic/drc` and its suites are unchanged in 0.0.6 (`verified`, `git diff`) | `V3-02_0.0.5.md` |
| V3-03 | Spiral generator and geometry mutants: 5 of 5 killed on 0.0.5 | stands: subject and suites unchanged (`verified`) | `V3-03_0.0.5.md` |
| V3-04 | Physics mutants: 5 of 5 killed on 0.0.5 | stands: subject and suites unchanged (`verified`) | `V3-04_0.0.5.md` |
| V3-05 | Exporter mutants: 4 of 4 killed on 0.0.5 | stands: the exporters are unchanged. The only suite change is the colophon test (DEF-UV27-01), and every mutant also has a killer in `tests/unit/embodic_io/exporters` (`verified`, `V3-05_0.0.5_run.json`) | `V3-05_0.0.5.md` |
| V3-06 | Instrument mutants: 33 of 33 killed on 0.0.5 | stands: `tests/independent/m1` unchanged (`verified`) | `V3-06_0.0.5.md` |
| V3-07 | Hypothesis, nightly profile, seeds 1 to 10: 0 failing on 0.0.5 | stands: properties and subject unchanged (`verified`) | `V3-07_0.0.5.md` |
| V3-08 | PK-04 Linux reference from the 0.0.6 wheel, two runs byte-identical | done for 0.0.6 (U-V29). `pk04_compare.py --self-test` passes 10 of 10 (`verified`, rerun by U-V22) | `reference/README.md` |
| V3-09 | Lock files against PyPI's Windows wheels: 44 of 44 | stands: `requirements/` has not changed since 2026-10-12 (`verified`, `git log`). PyPI today is `not tested` | `verification_plan.md` W0 |
| V3-10 | Own models against the product: all five examples equal to the 0.0.2 run to the last bit, DRC sets equal (wave 186) | stands: physics, generators, geometry and DRC unchanged (`verified`). Serpentine and wave star and k_w stay `not tested` by my own model, accepted by name (D-071c) | `V3-10_0.0.5.md` |
| V3-11 | OR-11, EQ-05 field against GetDP 2-D: within band (−0.07 % b1, −0.18 % peak, D-050d) | passed on the 0.0.6 wheel, embodic values bit-identical (U-V29). The FEA side is carried (`inferred`). OR-11c (3-D) `not tested`, allowed by point 3 (D-100b) | `tests/independent/m6/records/OR-11_OR-12_2bfca49.md` |
| V3-12 | OR-12, EQ-12 eddy loss against FEA: within band | passed on the 0.0.6 wheel, same record and limits as V3-11 | same record |
| V3-13 | Release evidence applies to main | holds: `db089e71…75cb` on the wheel, its evidence and main 0abe719 (U-V22), and no `src` change from 0abe719 to 2174f1b (`verified`, `git diff`) | this report |
| V3-14 | Wording, name and brand scans on the 0.0.6 release wheel: controls 82 of 83 rows find their plant, 0 findings outside the allow-list, 37 export files | passed (`verified` by running). A control counts a plant only when the allow-list does not admit it, and a run with an over-broad rule exits 2. Five allow-list rules with their reasons classify the 21 hits of the first run, none in an export. Deviation: 5 of the 8 brand originals were hashed, because the user's folder is not in the container (the other 3 `not tested` by hash) | `tests/independent/m7/records/V3-14_0.0.6.md` |
| V3-15 | The audit on 0.0.6: must rows 67 `verified`, 3 `partial`, 3 `failed` | point 1 not met by the audit alone | section 1 |

V3-14 ran as `tests/independent/m7/records/V3-14.md` describes, in a fresh venv: the release wheel with `--no-deps`,
then numpy 2.4.6 and pypdf 6.20.0 from the lock files with `--require-hashes`. The miss of the 83 control rows is the
raw-stream PDF row, which expects 0, as on 0.0.1. The scan hashed the four copies under
`docs/phase1/design/mockups/brand/`, which test_plan.md 5.8.5 records as byte-identical to the originals, and the
fifth hash of `tests/static/brand_assets.sha256` (`tests/independent/README.md`, section U-V30).

## 4. The DEF list

This list holds every DEF row opened in Phase 3, from 2026-10-16 (D-048) to D-100. The sources are the decision log,
`tests/independent/m7/records/defects.md`, the unit files under `docs/phase3` and `docs/phase4`, `CHANGELOG.md`, and
the commit messages for DEF-W-05 to DEF-W-09. The states are the outcomes of point 4, plus `unresolved` for an ID with
no record. Where the state rests on a later run, the evidence names it.

| ID | What | State | Evidence |
|---|---|---|---|
| DEF-U-S7-01 | F6, Alt+1 to Alt+4, Ctrl+Shift+T and Ctrl+Shift+N did nothing | closed | D-049g, `CHANGELOG.md` 0.0.2 |
| DEF-U-S7-02 | three Tab stops had no accessible name | closed | D-049g, `CHANGELOG.md` 0.0.2 |
| DEF-U-S7-03 | EQ chips had the role static text | closed | D-049g, `CHANGELOG.md` 0.0.2 |
| DEF-U-M6a-01 | the one-off GUI update at example open | moved to Phase 5 by Fable | D-050a, D-066a: the N02-10 stall was fixed, and the off-CPU part of the open gap stays `unresolved` for Phase 5 |
| DEF-U-M6a-02 | worker wall time in Agent 1's probe | closed, a probe artefact | D-050a |
| DEF-M6b-01 | serpentine build 15 to 17.5 s against 10 s at near-zero clearance | moved to Phase 5 by Fable | D-050b, D-055f: a strict xfail, output identical |
| DEF-M6b-02 | `pytest.approx` default abs voided rel 1e-12 claims | closed | D-050b |
| DEF-UV8-01 | two engine messages named Xcoil | closed | D-051c. REQ-L-03 `verified` on 0.0.6 |
| DEF-UV8-02 | the gate never enforced TR-01 | closed | D-051e. The 0.0.6 gate runs `--fail-untested-through=M5` (`verified`, gate log l.819) |
| DEF-UV8-03 | the DRC clearance was called measured | closed | D-051a. REQ-T-10 `verified` on 0.0.6, and V3-14 finds no such text on the 0.0.6 wheel |
| DEF-UV8-04 | "Balanced." claimed balance from phase angles | closed | D-051b. REQ-T-11 `verified` on 0.0.6 |
| DEF-UV8-05 | three registry formulas named Xcoil | closed | D-051c. REQ-L-03 `verified` on 0.0.6 |
| DEF-UV8-06 | UT-PHY-07 and GR-07 did not exist | closed | D-051e. Both have `name` evidence on 0.0.6 |
| DEF-UV8-07 | a name match was taken as evidence | closed | D-051e. `req_audit.py` applies the ruling rule, and its self-test passes |
| DEF-W-01 | the violation order differed on Windows | closed | D-051f, commit 9f117e5. PK-04 passes on Windows (D-086a, D-090d, D-098a) |
| DEF-W-02 | layout and stack hashes differ across platforms | closed, a contract ruling | D-051f, commit 1939b13 |
| DEF-W-03 | a near-zero sample failed a pure relative rule | closed, a criterion ruling | D-051f, commit 1939b13. The self-test case passes (`verified`) |
| DEF-W-04 | Activate.ps1 blocked under the Restricted policy | closed | D-064d |
| DEF-W-05 | the CLI Ctrl+C test on Windows | closed | commit f91e771 (test fix). Windows commit gate 6 of 6 later (D-064b) |
| DEF-W-06 | child output decoded with the locale code page | closed | commit 3d62a5b (test fix) |
| DEF-W-07 | a UI test removed its scratch folder while inside it | closed | commit 40f5060 (test fix) |
| DEF-W-08 | `embodic-cli` output not UTF-8 | closed | commit a170ac2, `CHANGELOG.md` 0.0.2 |
| DEF-W-09 | CRLF writes of the board dump, README and manifest | closed | commits e0e6dfa and 7512174, D-063c |
| DEF-W-10 | no record | `unresolved` | retired and never reused (D-100d). No file, commit, laptop folder or session record names it (D-100d, `verified` there by grep) |
| DEF-W-11 | no record | `unresolved` | as DEF-W-10 |
| DEF-W-12 | intermittent Windows GUI latency against 100 ms | moved to Phase 5 by the user | D-076d. Still fails on 0.0.6: 3 of 5 runs (D-099b) |
| DEF-W-13 | CRLF checkouts broke byte comparisons | closed | D-086b, commit a756799. Holds on Windows (D-094c, D-095b, D-098a) |
| DEF-W-14 | Application Control blocked the unsigned bundle | closed by Fable as not a product defect | D-086c. The bundle ran and passed on 0.0.6 (D-099a). Signing is the user's S-1 |
| DEF-W-15 | REQ-N-01 not met on the laptop | moved to Phase 5 by the user | D-091a. PF-01 record accepted by D-091 |
| DEF-W-16 | Application Control blocks pip's `embodic.exe` and `embodic-cli.exe` | accepted by name by Fable | D-100d: `python -m embodic.cli` works where the launchers are blocked (run 12), and the launchers ran in run 11. It stays open as a known limit of the Windows install. The fix is S-1: code signing, or `python -m` as the documented Windows route. INSTALL.md at 2174f1b gives the `python -m` form (`verified`, `grep`) |
| DEF-UV10-01 | `pairs_checked` differed by 1 across platforms | closed | D-086a: no left-out pair violates, the tool follows D-052b. Self-test case passes (`verified`) |
| DEF-U-M6h-01 | GR-07 case 3, a board thinner than its copper | closed | D-053a, `CHANGELOG.md` 0.0.2. GR-07 `name` evidence on 0.0.6 |
| DEF-UE16-01 | PR-14 tolerance flipped by one chord count | closed, a test defect | D-054a |
| DEF-UE16-02 | a docstring waited for a ruling that D-033a gave | closed | D-100d. U-M9f fixed it at 0d28d7f: the docstring of `tests/unit/generators/test_spiral_length.py` now cites D-033a and the per-corner tolerance (`verified`, `git show 0d28d7f`) |
| DEF-M7a-01 | a screw radius of 1e30 mm overflowed the DRC grid | closed | D-054e, `CHANGELOG.md` 0.0.2 |
| DEF-M7a-02 | `vias_per_transition` above 1 silently ignored | closed | D-054d, `CHANGELOG.md` 0.0.2. Parallel vias are a Phase 5 feature |
| DEF-US11-01 | the export stamp printed 5 hex digits | closed | `CHANGELOG.md` 0.0.2 |
| DEF-US11-02 | REQ-T-14 cited the wrong UX-AC | closed | requirements.md revision of 2026-10-17 (U-D21) |
| DEF-US11-03 | a toolstrip command ignored typed text | closed | test N02-9 (`tests/ui/qt_shell/test_n02_typing_preview.py` l.201 at 2bfca49) |
| DEF-US11-04 | Esc and Up, Down stepping not built | closed | D-056g, `CHANGELOG.md` 0.0.2 |
| DEF-US11-05 | high contrast resolved to light | closed on Linux | `CHANGELOG.md` 0.0.2. Windows high contrast `not tested` |
| DEF-UE17-01 | the polygon corner radius was ignored | closed | D-056h, D-057f |
| DEF-UE17-02 | EQ-17 cooled every board face | closed | D-056i, `CHANGELOG.md` 0.0.2 (EQ-17 stays `inferred`, unventilated gap `assumption`) |
| DEF-M7b-01 | EQ-16 took the chord area | closed | D-056j, `CHANGELOG.md` 0.0.2 |
| DEF-U-M7c-01 | Tab order | closed | D-056k |
| DEF-U-M8a-01 | Tab order | closed | D-056k |
| DEF-U-M8a-02 | off-CPU part of the example-open gap | moved to Phase 5 by Fable | D-056k, D-066a: inferred GIL contention, to measure on Windows |
| DEF-U-M7c-02 | Board tab overflow | closed | D-057e, `CHANGELOG.md` 0.0.2 |
| DEF-UE18-01 | EMF results omitted EQ-05 and EQ-07 from their chain | closed | D-058d, D-059b |
| DEF-US12-01 | serpentine Layers and Coil tabs cut at 960 x 540 | closed | D-057e, `CHANGELOG.md` 0.0.2 |
| DEF-US12-02 | Up and Down scrolled the inspector | closed | `docs/phase3/design/fix_wave_f2.md`, `CHANGELOG.md` 0.0.2 |
| DEF-US12-03 | a screens.md row was missing | closed | `docs/phase3/design/fix_wave_f2.md` |
| DEF-US13-01 | helper Down stepped below zero | closed | D-059c, D-060b (helper bounds) |
| DEF-UE20-01 | validity flags did not travel with `built_from` | closed | D-060c, commit dbb1e22, gate 6 of 6 (D-061a) |
| DEF-UE20-02 | a bound label travelled along the chain | closed | as DEF-UE20-01 |
| DEF-UE20-03 | a constant 0.0 loss took chains and a flag | closed | as DEF-UE20-01 |
| DEF-UE20-04 | `ke_line_peak` held EQ-09 | closed | as DEF-UE20-01 |
| DEF-UE20-05 | `loss_interconnect_w` lacked EQ-09 | closed | as DEF-UE20-01 |
| DEF-UE20-06 | `edge_leakage_fraction` lacked EQ-04 | closed | as DEF-UE20-01 |
| DEF-UE20-07 | `torque_speed.speed_rpm` took the whole envelope chain | closed | as DEF-UE20-01 |
| DEF-UE20-08 | used inputs missing from the assumed-inputs tag | closed | as DEF-UE20-01 |
| DEF-UV13-01 | LG-01 had no word printer | closed | D-061e, D-062a |
| DEF-UV13-02 | table cells carried their unit in the header only | closed | D-061c, D-062a |
| DEF-UV13-03 | no test carried REQ-N-10 | closed | D-062a. REQ-N-10 `verified` on 0.0.6 |
| DEF-UV13-04 | a clause tested only under another row's marker | closed | D-061e |
| DEF-UV13-05 | EQT-27-GR carried by no test | closed | D-064a |
| DEF-UE22-01 | the golden mapper counted 56 conductors, not 64 | closed, a test defect | D-063a, D-064a |
| DEF-UE22-02 | `winding_factor_1` labelled as k_w1 | closed | D-063b, D-064a |
| DEF-UE22-03 | EQ-27 did not define Ke1 | closed | `docs/phase3/engineering/fix_wave_f8.md` (registry text) |
| DEF-UM7d-02 | OR-07 and OR-08 dependency note | closed | `docs/phase3/design/fix_wave_f1.md` (c), `CHANGELOG.md` 0.0.2 |
| DEF-US9-01 | the V3-14 scan missed words inside identifiers | closed | the scan's word-start pattern (`tests/independent/m7/v3_14_scan.py`). Its controls pass on 0.0.6 |
| DEF-U-M8n-01 | a cancelled scene build ran on | closed | D-067a |
| DEF-U-M8n-02 | `label_anchors` recomputed coil marks | closed | D-067a |
| DEF-U-M8n-03 | N02-10 never saw a preview result arrive | closed | D-067a |
| DEF-U-M8o-01 | GUI float arithmetic 5 times slower after open | moved to Phase 5 by Fable | D-067b: no failing requirement, cause `unresolved` |
| DEF-U-M8o-02 | exports computed coil marks twice | closed | D-068, commit 2ed281c |
| DEF-UV15-01 | no test on the D-006 boundary | closed | D-072, D-092 |
| DEF-UV15-02 | the rule 2b band tested off its edge only | closed | D-072, D-092 |
| DEF-UV15-03 | serpentine properties ran 3 examples in every profile | closed | D-072, D-092 |
| DEF-UV15-04 | a finite rotation made compute raise | closed | D-072, D-092 |
| DEF-UV16-01 | rule 5 exempted a whole path | closed | D-079b, D-080a, D-080b. Mutant V3-02-12 killed (D-092) |
| DEF-UV16-02 | copper layers looked joined in the view | closed | D-080c (UI-58 to UI-61). The user has not looked at the new view on Windows (D-079c Q2) |
| DEF-UV16-03 | round pads drawn as squares | closed | D-080c |
| DEF-UD25-01 | a leading corner piece was exempt from rule 1 | closed | D-080a |
| DEF-UV18-01 | no two-path cross-net test | closed | D-092 |
| DEF-UV19-01 | no T-05 test of a partial refusal | closed | D-084b. REQ-T-05 `verified` on 0.0.6 |
| DEF-UV19-02 | UT-GEO-19 tests checked UT-GEO-26 | closed | D-084a, D-084b. UT-GEO-26 `name` evidence on 0.0.6 |
| DEF-UV21-01 | TR-01 silent on a failed manual record | closed | D-093c, D-094a. TR-01 on the U-V30 index prints "0 failing, 4 accepted" (`verified`, run on the release reports) |
| DEF-US17-01 | two inputs gave no unit to a screen reader | closed on Linux | D-094a. How Narrator speaks it is `not tested` |
| DEF-US17-02 | the guide listed five unbound keys | closed | D-094a, D-094b. U-M9e is in `v0.0.6` (`verified`, `git merge-base`) |
| DEF-US17-03 | the torque-speed message named a missing place | closed | D-094a, D-094b |
| DEF-UV27-01 | the colophon test needed `pdftotext` | closed | D-098c: passes on Windows |
| DEF-US18-01 | nine canvas keys of the keyboard map do nothing | accepted by name by Fable | D-100d: 0.0.6 has no handler for the canvas keys of design_spec.md section 10, and its guide does not list them (U-V28). The user chooses build or remove at walkthrough step 3.10 |

Counts: 93 rows. 82 closed (2 of them on Linux only, DEF-US11-05 and DEF-US17-01), 6 moved to Phase 5 (4 by Fable,
DEF-U-M6a-01, DEF-U-M8a-02, DEF-M6b-01 and DEF-U-M8o-01, and 2 by the user, DEF-W-12 and DEF-W-15), 1 closed by
Fable as not a product defect (DEF-W-14), 2 accepted by name by Fable (DEF-W-16 and DEF-US18-01), 0 open, 2
`unresolved` (DEF-W-10 and DEF-W-11). DEF-W-10 and DEF-W-11 are on the list because the DEF-W numbers run from 01 to
16 and D-100d retires these two. Among the decision rows only D-100d names them.

These IDs appear in the Phase 3 record but were opened before 2026-10-16, so they are not on the list: DEF-M1c3-01,
DEF-M3a-01, DEF-M3b-03, DEF-U-M5h-01 and DEF-UV5-04. Each is named in a decision row before D-048 (`verified` by
`checks/phase3_report_check.py`).

DEF-U-M5h-01 continues as DEF-U-M6a-01 (D-050a).

## 5. What stays not tested, and why

| Item | Why | Point 3 allows it |
|---|---|---|
| EQT-14-O2 and the F-OR07 closure that needs a measurement | no built board (D-048f, K-4) | yes |
| PK-01 Windows cells for Python 3.12 and 3.13 | D-048d names Python 3.11 only | yes |
| OR-11c, EQ-05 in 3-D | only the 2-D GetDP case exists (D-050d) | yes, by D-100b |
| A fresh FEA run on 0.0.6 | its inputs are unchanged since c25d8a9, and the embodic values are bit-identical (U-V29) | not needed, `inferred` |
| AX-06 Narrator on 0.0.6 | not run. It is a walkthrough step (D-097c) | only if the user declines |
| W6 real-display rows (screenshots, Agent 1's rows, AX-02, the DEF-U-M5h-01 first paint) on 0.0.4 or later | nobody has run them on Windows since the 0.0.1 smoke. D-100c puts the scripted part at the start of the UAT session and the human part in walkthrough parts 0 to 3, 6 and 7 | no. A-1 waits for both parts |
| Windows high contrast with the layer cue | tested offscreen on Linux only (D-083b) | no, but no row plans it on Windows |
| PK-06 cold on Windows after 0.0.2 | the network gave 8.5 kB/s in the 0.0.4 try (D-084e). The cold results that exist are 4154.5 s on 0.0.1 (failed, 99.6 % download at 0.03 MB/s) and 471 s on 0.0.2 (passed) | warm runs cover REQ-N-07, and the cold result is reported (D-053c) |
| `python -m embodic.ui.app` on Windows | not opened on Windows (PK-06 record). `python -m embodic.cli` passed in run 12 | no row plans it. The window opens in the W6 human part |
| The 3 brand originals of the 0.0.1 V3-14 run that have no copy or hash here | the user's brand folder is not in the container | not named in point 3. The name rule still flags a brand-named image |
| REQ-F-30 (could), REQ-N-20, REQ-T-12, REQ-L-02, REQ-L-06 and REQ-L-09 (should) | no test exists for UI-20, UT-LOG-01, UI-13, LG-02 and LG-07, and no V3-01 ruling or Fable assignment found one | yes |
| REQ-N-29 (should, TR-06) | the coverage step moved to Phase 5 (D-053b) | not named, but it is a should row, so point 1 does not need it |
| Serpentine and wave star and k_w by my own model | accepted by name (D-071c), GR-22 compares their EMF with Xcoil | yes, by D-071c |
| How Narrator speaks the units of DEF-US17-01 | needs the user's Narrator run | with AX-06 |

## 6. Exit criteria, point by point

### Point 1: every live must row `verified`, except the rows of point 3. Not yet held.

The audit gives 67 of 73 must rows `verified` (section 1). D-100b rules the 6 others:

| Row | Audit | D-100b | What is still missing |
|---|---|---|---|
| REQ-N-01 | failed | named exception: the user moved the fix to Phase 5 (D-091a). Known limit K-2 | the user accepts K-2 by name, or rejects it |
| REQ-N-02 | partial | named exception: DEF-W-12 is in Phase 5 (D-076d). Known limit K-1 | the user accepts K-1 by name, or rejects it |
| REQ-N-05 | failed | closed: PK-02 by runs 11 and 12, PK-01 by W7, which D-100c accepts by name | nothing for the exit. The audit keeps `failed` through the W7 and W8 records (Fable item 1) |
| REQ-N-06 | failed | closed: PK-05 (D-099a), PK-11 by run 11 | nothing for the exit. The audit keeps `failed` through the W8 record (Fable item 1) |
| REQ-N-16 | partial | waits for AX-06. Phase 4 starts with it `partial` | the user's Narrator run on 0.0.6, or the user declines it (then `not tested` by point 3) |
| REQ-N-24 | partial | the same AX-06 run | as REQ-N-16 |

REQ-F-11, REQ-N-04 and REQ-N-07 are now `verified` by the audit.

### Point 2: the items verified by a run with a record. Not yet held.

| Item | On 0.0.6 | Evidence |
|---|---|---|
| W4: PK-06 under 10 minutes, self-test 45 of 45 | held: runs 11 and 12, 22.3 s and 19.3 s, 45 of 45 | D-100a |
| W5: `PK-04 passed` | held | D-098a |
| W7: `6 of 6 gates passed` | accepted by name: 5 of 6, the failed test compared the 0.0.5 bundle, and the release run rebuilt the bundle and passed `tests/bundle` 6 of 6. U-M9f makes `tests/bundle` refuse a bundle of other source | D-098c, D-100c |
| W8: release profile, all gates, PF baseline | accepted by name: 6 of 8, the three failed pytest tests are DEF-W-16's launcher block, whose criteria runs 11 and 12 meet, and the latency gate is DEF-W-12 (Phase 5). PF-01 failed and is accepted (D-091a) | D-099a, D-100c |
| W6: screenshots and Agent 1's rows | not held yet: the scripted part (`--smoke --screenshot-dir` and the in-window rows of capture_acceptance on the real display) runs from Fable's launcher at the start of the UAT session, and Agent 1 reviews the shots. The human part is in walkthrough parts 0 to 3, 6 and 7 | D-100c |
| V3-01 to V3-07 and V3-10 | held: every mutant killed, 0 Hypothesis failures, the rulings stand | section 3, D-092 |
| V3-14 | held: rerun on the 0.0.6 release wheel, every class finds its plant, 0 findings | section 3, D-100c |
| V3-11 and V3-12: each has a verdict | held: both in band (2-D) | D-050d, U-V29 record |

### Point 3: what may stay `not tested`. Held, except AX-06.

Section 5 gives each item with its reason. The items point 3 names are there, and OR-11c is now one of them (D-100b).
AX-06 qualifies only if the user declines the walkthrough step, and the user plans to run it (D-091c, D-097c). PK-05 no
longer needs point 3, because it passed on Windows on 0.0.6 (D-099a).

### Point 4: every Phase 3 DEF row closed, accepted by name, or moved to Phase 5 with a reason. Held by D-100d.

Section 4 lists 93 rows. None is open. D-100d accepts DEF-W-16 and DEF-US18-01 by name, U-M9f closed DEF-UE16-02, and
D-100d retires DEF-W-10 and DEF-W-11. Those two IDs have no record, so no defect stands behind them that point 4 could
close (`inferred` from D-100d). The open choices are the user's: S-1 for DEF-W-16, and build or remove for
DEF-US18-01.

## How to check this report

- `python3 docs/phase3/verification/checks/req_audit.py --target 0.0.6 --check` exits 0 when `req_audit.md` is current,
  and `--self-test` passes 12 of 12.
- `python3 docs/phase3/verification/checks/phase3_report_check.py` checks this file against `req_audit.md` (counts and
  every row list), checks that every DEF ID of the Phase 3 record has a row in section 4 or a place in the
  pre-Phase-3 list, and checks every decision row, REQ ID and path with `docs/phase4/verification/checks/plan_refs.py`.
  An `unresolved` row must be a gap in the DEF-W numbers, or an ID that a decision clause retires and no other
  decision row names.
  `--self-test` plants faults and expects each to fail.
- `python3 tools/trace_matrix.py` with the two release reports, `--fail-untested-through M5` and the index prints
  `manual: 11` and `0 failing, 4 accepted`, and exits 0 (`docs/phase3/verification/manual_records_0.0.6_windows.md`).
- `python3 docs/phase3/verification/checks/pk04_compare.py --self-test` passes 10 of 10.
- `python3 docs/phase4/verification/checks/carry_over.py --check` exits 0 for 0.0.6
  (`docs/phase4/verification/carry_over_0.0.6.md`).
