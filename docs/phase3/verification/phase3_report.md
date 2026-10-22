Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5 (unit U-V22, 2026-10-22)

# Phase 3 report: verification of release 0.0.6

This is the English Phase 3 report that `verification_plan.md` section 4 asks for. Fable gives the user a Thai summary
of it. The named build is release 0.0.6. Releases 0.0.4 and 0.0.5 came before it, and this report replaces their
records where they differ.

Every claim carries one status: `verified`, `inferred`, `assumption`, `unresolved` or `not tested`. A claim that cites a
decision row or a record and carries no label is `verified` by reading that row or record. I ran my own checks on Linux
in the cloud container. Every Windows result in this report is Fable's, from `docs/phase3/fable/windows_campaign_w1.md`,
`docs/phase3/fable/windows_campaign_w2.md` or the decision row they name. I ran nothing on Windows (order 8).

## The exit criteria do not all hold on 0.0.6

| Point of section 4 | Holds on 0.0.6 | Why not, in one line |
|---|---|---|
| 1. Every live must row `verified` | no | 9 of 73 must rows are not: 8 `partial`, and REQ-N-01 `failed` |
| 2. The Windows campaign and the campaigns verified by a run with a record | no | W4 (PK-06), W6, W7 and W8 have no passing run on 0.0.6, and V3-14 ran on 0.0.1 only |
| 3. Items that may stay `not tested`, each with its reason | yes, except AX-06 | AX-06 may stay `not tested` only if the user declines it, and the user has not declined |
| 4. Every Phase 3 DEF row closed, accepted by name, or moved to Phase 5 | no | DEF-W-16, DEF-US18-01 and DEF-UE16-02 are open, and DEF-W-10 and DEF-W-11 have no record |

The open items are Windows runs, one Windows install defect (DEF-W-16), decisions, and record keeping. No DEF row that
is open or moved to Phase 5 reports a wrong computed value (`verified` by reading every row of section 4). In the
cloud the release gate passed 11 of 11. Every mutant of V3-02 to V3-06 was killed on the 0.0.5 sources, and 0.0.6
does not change the modules they mutate. On Windows PK-04 matched the Linux reference at 1e-9 on all five examples
(D-098a).

Decisions that Phase 4 needs, by owner:

- Fable:
  1. Rule point 1 for REQ-F-11, REQ-N-04, REQ-N-05 and REQ-N-06. The audit keeps every row that plans a Windows or FEA
     test ID `partial`, whatever record exists (`NEEDS` in `checks/req_audit.py`). PK-04 and PK-05 passed on Windows on
     0.0.6 (D-098a, D-099a), but no index entry holds those runs.
  2. Rule whether point 1 admits REQ-N-01 and REQ-N-02, whose Windows fixes the user moved to Phase 5 (DEF-W-15 by
     D-091a, DEF-W-12 by D-076d). Point 1 names no such exception.
  3. W7. Rerun the Windows commit gate without the leftover 0.0.5 bundle, or rule that the release run's 6 of 6
     `tests/bundle` result replaces the failed test (D-098c).
  4. DEF-W-16. Land the INSTALL.md change that D-098b rules (the `python -m` form), then add the PK-06 rerun results
     (runs 9 and 10) and rule PK-02 and PK-11 on Windows.
  5. W6. Rule whether the Phase 4 walkthrough replaces the W6 rows. D-097c plans AX-06 inside it.
  6. V3-14. Answer question Q-3 of `docs/phase4/verification/acceptance_plan.md`. Accept the product tests LG-03 to
     LG-06 in place of a rerun, or brief a rerun.
  7. Point 4. Close or accept by name DEF-US18-01, DEF-UE16-02 and DEF-W-16, and say what DEF-W-10 and DEF-W-11 were.
  8. Brief the redo of the Phase 4 carry-over for 0.0.6. It still names 0.0.5 (see "How to check this report").
- The user:
  1. Run AX-06 (Narrator) on 0.0.6, or decline it. It is a step of the walkthrough (D-097c).
  2. Decide code signing (S-1). It now covers the bundle (DEF-W-14) and the pip launchers (DEF-W-16, D-098b).
  3. Decide whether to build the canvas keys of DEF-US18-01 or remove them from the keyboard map (walkthrough step
     3.10).
  4. Accept by name the known limits K-1 (DEF-W-12) and K-2 (DEF-W-15), or ask for fixes before acceptance.

## The named build

| Field | Value | Status |
|---|---|---|
| Version and tag | 0.0.6, tag `v0.0.6` on 2bfca49 (D-096) | `verified` (`git rev-parse v0.0.6^{}`) |
| Release gate | 11 of 11 gates, pytest 4439 passed, 3 skipped, 9 deselected, 3 xfailed, latency gate 8 passed | `verified` (`gate_release_2bfca49.log` l.798, l.817, l.868) |
| Wheel | `embodic-0.0.6-py3-none-any.whl`, SHA-256 `fdb89189161d14b71433c4e35861d4e4d56fc6a7e64383f96ba13e27ba450101` | `verified` (`sha256sum`) |
| Package source hash | `db089e71…75cb` in the wheel's evidence, in the unpacked wheel, and in main 0abe719's `src/embodic` | `verified` (`package_source_sha256` on both trees) |
| Change from 0.0.5 | `src/embodic/__init__.py` (the version) and 7 files under `src/embodic/ui/` | `verified` (`git diff --stat v0.0.5 v0.0.6 -- src`) |

Main 0abe719 is release 0.0.6 plus 21 changed files under `docs/` and `tests/independent/` (`verified`, `git diff
--stat v0.0.6 0abe719`). No file under `src/` changed, so V3-13 holds on it.

## 1. The requirement audit of 0.0.6 (V3-15)

`python3 docs/phase3/verification/checks/req_audit.py --target 0.0.6` writes `docs/phase3/verification/req_audit.md`.
That file is the full table, one row per requirement with its evidence. The 0.0.5 audit moved to `req_audit_0.0.5.md`.
The inputs are the two REQ reports and the log of Fable's release gate on 2bfca49, copied gzipped into `inputs/`
(byte-identical after `gunzip`, `verified`), the test sources of `git archive 2bfca49 tests`, the V3-01 rulings v13 to
v21, and the manual-record index `manual_records.json` as it stands on 0abe719. The two reports hold 4454 records: 4447
passed, 6 skipped, and 1 not run in either process, the manual PF-01 test (`verified`).

The index holds 7 entries. Six passed and count: PK-06 Linux, AX-05, OR-11, OR-12, LG-01 and LG-04. One is the Windows
PF-01 record (failed, accepted by D-091). The index holds no other Windows record. The Windows PK-04 and PK-05 runs of
0.0.6 are in Fable's Windows record only, and the audit's `NEEDS` rule keeps their rows `partial` even if they were
indexed.

Counts (`verified` by running, with CPython 3.11.17 and 3.13.16, byte-identical output):

| Rows | verified | partial | failed | not tested | withdrawn |
|---|---|---|---|---|---|
| all 110 | 64 | 22 | 1 | 7 | 16 |
| must 73 | 64 | 8 | 1 | 0 | 0 |

Planned-test evidence: eqt 17, fail 1, file 32, gate 9, name 200, none 22, record 6.

Against the 0.0.5 audit no row changed status (`verified` by a row-by-row diff). Five rows gained passing marked
records (REQ-F-20, REQ-N-10, REQ-N-12, REQ-N-24, REQ-T-09), and the D-061d chains of REQ-N-14, REQ-T-11 and REQ-L-01
now end at the records that U-V28 and U-V29 made for 0.0.6. No `verified` row lost its ruling. No Ruling note names a
changed source or a superseded record. `req_audit.py --self-test` passes 5 of 5 on the 0.0.6 target.

The rows by status:

- Must, `verified` (64): REQ-F-01, REQ-F-02, REQ-F-03, REQ-F-04, REQ-F-05, REQ-F-06, REQ-F-07, REQ-F-08, REQ-F-10,
  REQ-F-12, REQ-F-13, REQ-F-14, REQ-F-15, REQ-F-16, REQ-F-18, REQ-F-19, REQ-F-21, REQ-F-23, REQ-F-32, REQ-F-33,
  REQ-F-34, REQ-F-35, REQ-F-36, REQ-F-37, REQ-F-38, REQ-F-39, REQ-F-40, REQ-N-08, REQ-N-09, REQ-N-10, REQ-N-11,
  REQ-N-12, REQ-N-13, REQ-N-14, REQ-N-15, REQ-N-17, REQ-N-18, REQ-N-19, REQ-N-21, REQ-N-23, REQ-N-25, REQ-N-27,
  REQ-N-28, REQ-T-01, REQ-T-02, REQ-T-03, REQ-T-04, REQ-T-05, REQ-T-06, REQ-T-07, REQ-T-08, REQ-T-09, REQ-T-10,
  REQ-T-11, REQ-T-13, REQ-T-14, REQ-T-15, REQ-T-16, REQ-L-01, REQ-L-03, REQ-L-04, REQ-L-05, REQ-L-07, REQ-L-08.
- Must, `partial` (8): REQ-F-11, REQ-N-02, REQ-N-04, REQ-N-05, REQ-N-06, REQ-N-07, REQ-N-16, REQ-N-24.
- Must, `failed` (1): REQ-N-01.
- Should, `partial` (11): REQ-F-09, REQ-F-22, REQ-F-24, REQ-F-25, REQ-F-26, REQ-F-27, REQ-F-28, REQ-F-29, REQ-F-31,
  REQ-N-03, REQ-N-26.
- Should, `not tested` (6): REQ-N-20, REQ-N-29, REQ-T-12, REQ-L-02, REQ-L-06, REQ-L-09.
- Could, `partial` (3): REQ-F-17, REQ-F-20, REQ-N-22.
- Could, `not tested` (1): REQ-F-30.
- Withdrawn (16): REQ-K-01 to REQ-K-16 (D-009).

The must rows that are not `verified`:

| Row | Status | Evidence on 0.0.6 | What keeps it from `verified` |
|---|---|---|---|
| REQ-N-01 | failed | PF-01 `fail` (Fable's laptop record, 0.0.5 source), PF-04 `file` | PF-01 on the laptop failed: physics p95 0.617 to 0.663 s against 0.3 s (D-087). DEF-W-15, moved to Phase 5 by the user (D-091a). The compute code is unchanged since 0.0.5, so the failure carries to 0.0.6 (`inferred`) |
| REQ-F-11 | partial | 18 IDs with `name`, `file` or `eqt`, OR-11 and OR-12 `record` (U-V29 on the 0.0.6 wheel) | Only the `NEEDS` rule: OR-11 and OR-12 are FEA IDs. My V3-01 ruling of the row is `checks`. The FEA side is the c25d8a9 GetDP run, carried because every embodic value is bit-identical (`inferred`). OR-11c (3-D) is `not tested` (D-050d) |
| REQ-N-02 | partial | UI-05 and UI-02 `name`, UI-36 to UI-45 `none` | The tests of UI-36 to UI-45 are named N02-1 to N02-10, so the text rule finds none. The V3-01 ruling (v18) finds every clause asserted on Linux. On Windows DEF-W-12 fails intermittently (D-099b) and is in Phase 5 (D-076d) |
| REQ-N-04 | partial | PR-09 and MT-06 `name`, PK-04 `none` | PK-04 is a Windows ID. It passed on the laptop on 0.0.6 (D-098a). No index entry holds it |
| REQ-N-05 | partial | PK-02 `name`, PK-01 `none` | The Windows commit gate of 0.0.6 ended 5 of 6 (D-098c). In the Windows release run PK-02 failed, because Application Control blocked the pip launcher (DEF-W-16, D-099a) |
| REQ-N-06 | partial | PK-03 and PK-11 `name`, PK-05 `file`, PK-10 `gate` | PK-05 passed on Windows on 0.0.6, `tests/bundle` 6 of 6 (D-099a). PK-11 failed in that run (DEF-W-16) |
| REQ-N-07 | partial | PK-06 `record` (U-V29, Linux, 0.0.6 wheel) | PK-06 on Windows, run 8 on 0.0.6, did not pass (DEF-W-16, D-098b). The rerun both ways is pending (D-099d) |
| REQ-N-16 | partial | AX-06 `file` | AX-06 (Narrator) has no run on 0.0.6. The 0.0.3 record does not stand (D-082b) |
| REQ-N-24 | partial | UT-MOD-03 `file`, AX-06 `none` | The same AX-06 run as REQ-N-16 |

## 2. The Windows record

The machine is the user's laptop: Windows 11 Home Single Language, build 26300, 18 logical CPUs, 15.4 GB RAM,
PowerShell 5.1, CPython 3.11.9 from the python.org NuGet package inside `%USERPROFILE%\Desktop\embodic\.python`.
Fable ran every step through the Claude desktop app, except the 0.0.5 and 0.0.6 gate chains, which the user started
(D-093a, D-098). The logs are in the git-excluded folder `_campaign` on the laptop. I did not read them. I read
Fable's two records and the decision rows.

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
| 0.0.6 | Commit profile | 5 of 6, pytest 1 failed (`tests/bundle` against the 0.0.5 bundle), 4181 passed. The colophon tests pass | D-098c |
| 0.0.6 | Release profile (09:30 to 11:45 with the latency runs) | 6 of 8. Bundle built in 65.2 s. Pytest 3 failed (PK-02 twice and PK-11, launcher blocked, DEF-W-16), 4349 passed. `tests/bundle` 6 of 6, the first PK-05 pass on Windows. Latency gate failed 1 test (N02-10 cancel case 153 ms). TR-01 and TR-02 pass | D-099a |
| 0.0.6 | Latency tests alone, five runs | 2 of 5 pass, N02-10 arrival 114, 199 and 258 ms in the others (DEF-W-12) | D-099b |
| 0.0.6 | PK-06 rerun, as INSTALL.md writes it and with `python -m embodic.cli` | pending (`run_0.0.6_pk06.cmd`, logs `pk06_run9.log` and `pk06_run10.log`). Fable adds the result after this unit | D-099d |

### Which Windows rows count for 0.0.6

0.0.6 changes `src`, so its Windows checks run again on the 0.0.6 wheel (D-095d). These rows count for 0.0.6:

- The sync, PK-04 (passed), the commit profile (5 of 6), the release profile (6 of 8, PK-05 passed), and the five
  latency runs (2 of 5) of the 0.0.6 table.
- PK-06 run 8 counts as a result that did not pass. The rerun replaces it when Fable adds it.
- PF-01 counts as failed. It ran on the 0.0.5 source, its compute code is unchanged in 0.0.6 (`verified` by the diff),
  and the 0.0.6 gate lists it as accepted by D-091 and does not count it (`verified`, gate log l.820-821).

No 0.0.4 or 0.0.5 run counts as a pass for 0.0.6. These have no Windows run on 0.0.6: AX-06, the W6 real-display rows,
the PK-06 cold run (none since 0.0.2), and Windows high contrast with the layer cue (D-083b).

## 3. The V3 campaigns

| ID | Verdict | Status on 0.0.6 | Record |
|---|---|---|---|
| V3-01 | Must-row rulings: 65 rows `checks` (the 64 `verified` rows and REQ-F-11), REQ-N-01 `fails`, the other 7 `partial` with a named gap (U-V13 to U-V21) | stands: the audit finds every pinned test source unchanged at 2bfca49 (`verified`) | `tests/independent/m7/records/V3-01_U-V21.md` and earlier |
| V3-02 | DRC mutants: 14 of 14 killed on 0.0.5 | stands: `src/embodic/drc` and its suites are unchanged in 0.0.6 (`verified`, `git diff`) | `V3-02_0.0.5.md` |
| V3-03 | Spiral generator and geometry mutants: 5 of 5 killed on 0.0.5 | stands: subject and suites unchanged (`verified`) | `V3-03_0.0.5.md` |
| V3-04 | Physics mutants: 5 of 5 killed on 0.0.5 | stands: subject and suites unchanged (`verified`) | `V3-04_0.0.5.md` |
| V3-05 | Exporter mutants: 4 of 4 killed on 0.0.5 | stands: the exporters are unchanged. The only suite change is the colophon test (DEF-UV27-01), and every mutant also has a killer in `tests/unit/embodic_io/exporters` (`verified`, `V3-05_0.0.5_run.json`) | `V3-05_0.0.5.md` |
| V3-06 | Instrument mutants: 33 of 33 killed on 0.0.5 | stands: `tests/independent/m1` unchanged (`verified`) | `V3-06_0.0.5.md` |
| V3-07 | Hypothesis, nightly profile, seeds 1 to 10: 0 failing on 0.0.5 | stands: properties and subject unchanged (`verified`) | `V3-07_0.0.5.md` |
| V3-08 | PK-04 Linux reference from the 0.0.6 wheel, two runs byte-identical | done for 0.0.6 (U-V29). `pk04_compare.py --self-test` passes 10 of 10 (`verified`, rerun in this unit) | `reference/README.md` |
| V3-09 | Lock files against PyPI's Windows wheels: 44 of 44 | stands: `requirements/` has not changed since 2026-10-12 (`verified`, `git log`). PyPI today is `not tested` | `verification_plan.md` W0 |
| V3-10 | Own models against the product: all five examples equal to the 0.0.2 run to the last bit, DRC sets equal (wave 186) | stands: physics, generators, geometry and DRC unchanged (`verified`). Serpentine and wave star and k_w stay `not tested` by my own model, accepted by name (D-071c) | `V3-10_0.0.5.md` |
| V3-11 | OR-11, EQ-05 field against GetDP 2-D: within band (−0.07 % b1, −0.18 % peak, D-050d) | passed on the 0.0.6 wheel, embodic values bit-identical (U-V29). The FEA side is carried (`inferred`). OR-11c (3-D) `not tested` | `tests/independent/m6/records/OR-11_OR-12_2bfca49.md` |
| V3-12 | OR-12, EQ-12 eddy loss against FEA: within band | passed on the 0.0.6 wheel, same record and limits as V3-11 | same record |
| V3-13 | Release evidence applies to main | holds: `db089e71…75cb` on the wheel, its evidence and main 0abe719 (`verified`, run in this unit) | this report |
| V3-14 | Wording, name and brand scans: 316 findings on the 0.0.1 wheel, which became DEF-UV8-01, -03, -04 and -05 | `not tested` on any later build. The scan hard-codes the 0.0.1 wheel, and the brand originals it hashes are not in this container (`verified`, `ls`). The product tests LG-03 to LG-06 pass at the 0.0.6 gate (`name` evidence in `req_audit.md`) | `V3-14.md` |
| V3-15 | The audit on 0.0.6: must rows 64 `verified`, 8 `partial`, 1 `failed` | point 1 not met | section 1, `V3-15_0.0.6.md` |

## 4. The DEF list

This list holds every DEF row opened in Phase 3, from 2026-10-16 (D-048) to D-099. The sources are the decision log,
`tests/independent/m7/records/defects.md`, the unit files under `docs/phase3`, `CHANGELOG.md`, and the commit messages
for DEF-W-05 to DEF-W-09. The states are the four of point 4, plus `unresolved` for an ID with no record. Where the
state rests on a later run, the evidence names it.

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
| DEF-UV8-03 | the DRC clearance was called measured | closed | D-051a. REQ-T-10 `verified` on 0.0.6 |
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
| DEF-W-10 | no record | `unresolved` | no file and no commit message of this checkout names it (`verified`, `grep` and `git log --all --grep`) |
| DEF-W-11 | no record | `unresolved` | as DEF-W-10 |
| DEF-W-12 | intermittent Windows GUI latency against 100 ms | moved to Phase 5 by the user | D-076d. Still fails on 0.0.6: 3 of 5 runs (D-099b) |
| DEF-W-13 | CRLF checkouts broke byte comparisons | closed | D-086b, commit a756799. Holds on Windows (D-094c, D-095b, D-098a) |
| DEF-W-14 | Application Control blocked the unsigned bundle | closed by Fable as not a product defect | D-086c. The bundle ran and passed on 0.0.6 (D-099a). Signing is the user's S-1 |
| DEF-W-15 | REQ-N-01 not met on the laptop | moved to Phase 5 by the user | D-091a. PF-01 record accepted by D-091 |
| DEF-W-16 | Application Control blocks pip's `embodic.exe` and `embodic-cli.exe` | open | D-098b rules the fix, but INSTALL.md at 0abe719 has no `python -m` form (`verified`, `grep`). PK-06 rerun pending (D-099d) |
| DEF-UV10-01 | `pairs_checked` differed by 1 across platforms | closed | D-086a: no left-out pair violates, the tool follows D-052b. Self-test case passes (`verified`) |
| DEF-U-M6h-01 | GR-07 case 3, a board thinner than its copper | closed | D-053a, `CHANGELOG.md` 0.0.2. GR-07 `name` evidence on 0.0.6 |
| DEF-UE16-01 | PR-14 tolerance flipped by one chord count | closed, a test defect | D-054a |
| DEF-UE16-02 | a docstring waits for a ruling that D-033a gave | open | `tests/unit/generators/test_spiral_length.py` l.9-11 still says it (`verified`, reading). Minor, test text |
| DEF-M7a-01 | a screw radius of 1e30 mm overflowed the DRC grid | closed | D-054e, `CHANGELOG.md` 0.0.2 |
| DEF-M7a-02 | `vias_per_transition` above 1 silently ignored | closed | D-054d, `CHANGELOG.md` 0.0.2. Parallel vias are a Phase 5 feature |
| DEF-US11-01 | the export stamp printed 5 hex digits | closed | `CHANGELOG.md` 0.0.2 |
| DEF-US11-02 | REQ-T-14 cited the wrong UX-AC | closed | requirements.md revision of 2026-10-17 (U-D21) |
| DEF-US11-03 | a toolstrip command ignored typed text | closed | test N02-9 (`tests/ui/qt_shell/test_n02_typing_preview.py` l.201) |
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
| DEF-US9-01 | the V3-14 scan missed words inside identifiers | closed | the scan's word-start pattern (`tests/independent/m7/v3_14_scan.py`) |
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
| DEF-UV21-01 | TR-01 silent on a failed manual record | closed | D-093c, D-094a. The 0.0.6 gate prints "0 failing, 1 accepted" (`verified`, gate log l.820) |
| DEF-US17-01 | two inputs gave no unit to a screen reader | closed on Linux | D-094a. How Narrator speaks it is `not tested` |
| DEF-US17-02 | the guide listed five unbound keys | closed | D-094a, D-094b. U-M9e is in `v0.0.6` (`verified`, `git merge-base`) |
| DEF-US17-03 | the torque-speed message named a missing place | closed | D-094a, D-094b |
| DEF-UV27-01 | the colophon test needed `pdftotext` | closed | D-098c: passes on Windows |
| DEF-US18-01 | nine canvas keys of the keyboard map do nothing | open | `CHANGELOG.md` 0.0.6 known limit. The user decides at walkthrough step 3.10. No decision row |

Counts: 93 rows. 81 closed (2 of them on Linux only, DEF-US11-05 and DEF-US17-01), 6 moved to Phase 5 (4 by Fable,
DEF-U-M6a-01, DEF-U-M8a-02, DEF-M6b-01 and DEF-U-M8o-01, and 2 by the user, DEF-W-12 and DEF-W-15), 1 closed by
Fable as not a product defect (DEF-W-14), 3 open (DEF-W-16, DEF-UE16-02, DEF-US18-01), 2 `unresolved` (DEF-W-10,
DEF-W-11). No row is accepted by name by Fable while it stays open. DEF-W-10 and DEF-W-11 are on the list because the
DEF-W numbers run from 01 to 16 and these two are the only gaps.

These IDs appear in the Phase 3 record but were opened before 2026-10-16, so they are not on the list: DEF-M1c3-01,
DEF-M3a-01, DEF-M3b-03, DEF-U-M5h-01 and DEF-UV5-04. Each is named in a decision row before D-048 (`verified` by
`checks/phase3_report_check.py`).

DEF-U-M5h-01 continues as DEF-U-M6a-01 (D-050a).

## 5. What stays not tested, and why

| Item | Why | Point 3 allows it |
|---|---|---|
| EQT-14-O2 and the F-OR07 closure that needs a measurement | no built board (D-048f, K-4) | yes |
| PK-01 Windows cells for Python 3.12 and 3.13 | D-048d names Python 3.11 only | yes |
| OR-11c, EQ-05 in 3-D | only the 2-D GetDP case exists (D-050d) | not named in point 3. Rides on REQ-F-11, see section 6 |
| A fresh FEA run on 0.0.6 | its inputs are unchanged since c25d8a9, and the embodic values are bit-identical (U-V29) | not needed, `inferred` |
| AX-06 Narrator on 0.0.6 | not run. It is a walkthrough step (D-097c) | only if the user declines |
| W6 real-display rows (screenshots, Agent 1's rows, AX-02, the DEF-U-M5h-01 first paint) on 0.0.4 or later | nobody has run them on Windows since the 0.0.1 smoke (Windows record, "What is not tested") | no |
| Windows high contrast with the layer cue | tested offscreen on Linux only (D-083b) | no, but no row plans it on Windows |
| PK-06 cold on Windows after 0.0.2 | the network gave 8.5 kB/s in the 0.0.4 try (D-084e). The cold results that exist are 4154.5 s on 0.0.1 (failed, 99.6 % download at 0.03 MB/s) and 471 s on 0.0.2 (passed) | warm runs cover REQ-N-07, and the cold result is reported (D-053c) |
| The `python -m` route of INSTALL.md on Windows | the PK-06 rerun is pending (D-099d) | no |
| REQ-F-30 (could), REQ-N-20, REQ-T-12, REQ-L-02, REQ-L-06 and REQ-L-09 (should) | no test exists for UI-20, UT-LOG-01, UI-13, LG-02 and LG-07, and no V3-01 ruling or Fable assignment found one | yes |
| REQ-N-29 (should, TR-06) | the coverage step moved to Phase 5 (D-053b) | not named, but it is a should row, so point 1 does not need it |
| V3-14 on any build after 0.0.1 | see section 3 | no, it is a point 2 item |
| Serpentine and wave star and k_w by my own model | accepted by name (D-071c), GR-22 compares their EMF with Xcoil | yes, by D-071c |
| How Narrator speaks the units of DEF-US17-01 | needs the user's Narrator run | with AX-06 |

## 6. Exit criteria, point by point

### Point 1: every live must row `verified`, except the rows of point 3. Not held.

The audit gives 64 of 73 must rows `verified` (section 1). The 9 others, with what is missing and whose decision it is:

| Row | Missing | Decision |
|---|---|---|
| REQ-N-01 | a passing PF-01 on the laptop. The user moved the fix to Phase 5 (D-091a), and point 1 has no exception for it | Fable rules the exception. The user accepts K-2 |
| REQ-N-02 | a passing Windows latency run (DEF-W-12, Phase 5 by the user, D-076d), and test names for UI-36 to UI-45, a tests-only change | Fable rules the exception or briefs the rename. The user accepts K-1 |
| REQ-N-04 | an index entry for the Windows PK-04 run of 0.0.6 (D-098a), and a ruling that it closes the row, because the audit cannot | Fable |
| REQ-N-05 | a Windows commit gate of 0.0.6 at 6 of 6, or a ruling that the stale-bundle failure is the environment (D-098c), and PK-02 on Windows, which DEF-W-16 blocks | Fable. The user for S-1 if signing is the fix |
| REQ-N-06 | PK-11 on Windows (DEF-W-16), and an index entry for the PK-05 pass (D-099a) | Fable. The user for S-1 |
| REQ-N-07 | the PK-06 rerun on 0.0.6 (D-099d) | Fable adds it. If the INSTALL.md route still fails, DEF-W-16 needs its fix first |
| REQ-N-16 | the user's Narrator run on 0.0.6 | the user runs or declines it. Fable rules whether Phase 4 may start with it inside the walkthrough |
| REQ-N-24 | the same run | as REQ-N-16 |
| REQ-F-11 | a ruling that the OR-11 and OR-12 records close the FEA part, with OR-11c and EQT-14-O2 left `not tested`. Every other ID has evidence, and my V3-01 ruling is `checks` | Fable |

### Point 2: the items verified by a run with a record. Not held.

| Item | On 0.0.6 | Evidence |
|---|---|---|
| W4: PK-06 under 10 minutes, self-test 45 of 45 | not held. Run 8 did not pass, rerun pending | D-098b, D-099d |
| W5: `PK-04 passed` | held | D-098a |
| W7: `6 of 6 gates passed` | not held: 5 of 6, the failed test compared the 0.0.5 bundle | D-098c |
| W8: release profile, all gates, PF baseline | not held: 6 of 8 (DEF-W-16, DEF-W-12). PF-01 failed and is accepted (D-091) | D-099a, D-087 |
| W6: screenshots and Agent 1's rows | not held: no run since 0.0.1 | Windows record |
| V3-01 to V3-07 and V3-10 | held: every mutant killed, 0 Hypothesis failures, the rulings stand | section 3, D-092 |
| V3-14 | not held: 0.0.1 only. Its DEF rows are closed | section 3 |
| V3-11 and V3-12: each has a verdict | held: both in band (2-D) | D-050d, U-V29 record |

### Point 3: what may stay `not tested`. Held, except AX-06.

Section 5 gives each item with its reason. The items point 3 names are there. AX-06 qualifies only if the user
declines the walkthrough step, and the user plans to run it (D-091c, D-097c). PK-05 no longer needs point 3, because
it passed on Windows on 0.0.6 (D-099a).

### Point 4: every Phase 3 DEF row closed, accepted by name, or moved to Phase 5 with a reason. Not held.

Section 4 lists 93 rows. Three are open, and two have no record:

| Row | Missing | Decision |
|---|---|---|
| DEF-W-16 | the INSTALL.md and Thai guide change of D-098b, and the PK-06 rerun | Fable. The user for S-1 |
| DEF-US18-01 | a decision row: close it, accept it by name for the Phase 3 exit, or move it to Phase 5 | Fable for the exit. The user chooses build or remove at step 3.10 |
| DEF-UE16-02 | a one-line docstring fix in a test file, or acceptance by name | Fable |
| DEF-W-10, DEF-W-11 | any record of what they were | Fable, who numbers the DEF-W rows |

## How to check this report

- `python3 docs/phase3/verification/checks/req_audit.py --target 0.0.6 --check` exits 0 when `req_audit.md` is current,
  and `--self-test` passes 5 of 5.
- `python3 docs/phase3/verification/checks/phase3_report_check.py` checks this file against `req_audit.md` (counts and
  every row list), checks that every DEF ID of the Phase 3 record has a row in section 4 or a place in the
  pre-Phase-3 list, and checks every decision row, REQ ID and path with `docs/phase4/verification/checks/plan_refs.py`.
  `--self-test` plants faults and expects each to fail.
- `python3 docs/phase3/verification/checks/pk04_compare.py --self-test` passes 10 of 10.

The Phase 4 carry-over still names 0.0.5. `docs/phase4/verification/checks/carry_over.py --check` already exited 1 at
main 0abe719, before this unit, and it now also refuses `req_audit.md` as the audit of another build. Its docstring
asks for that, because the carry-over of a new build is redone first. That is a Phase 4 unit for Fable to brief.
The record is `tests/independent/m7/records/V3-15_0.0.6.md`.
