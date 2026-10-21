Prepared by: Fable (coordinator), model id claude-opus-5-5. Windows campaign, part 2 (W4 to W9 of
docs/phase3/verification/verification_plan.md), run 2026-10-18 to 2026-10-21 on the user's laptop through the Claude
desktop app. Part 1 is windows_campaign_w1.md.

# Windows campaign W2: releases 0.0.2 to 0.0.5

The machine is the one W1 describes: Windows 11 Home Single Language, build 26300, 18 logical CPUs, 15.4 GB RAM,
PowerShell 5.1, and CPython 3.11.9 from the NuGet package in `%USERPROFILE%\Desktop\embodic\.python`. Logs are in
`%USERPROFILE%\Desktop\embodic\_campaign` (git-excluded). Each row below is `verified` by the log it names unless it says
otherwise. Decision rows hold the rulings.

## Releases 0.0.2 and 0.0.3 (superseded, kept for the record)

| Check | Result | Log | Row |
|---|---|---|---|
| PK-06 cold, 0.0.2 wheel | 471 s to the first example, self-test 45 of 45 | pk06_run3.log | D-071e |
| PK-06 warm, 0.0.2 wheel | 20 s, self-test 45 of 45 | pk06_run4.log | D-071e |
| Release profile, 0.0.2, run 1 | ended by a user logoff and sleep, not by the product | w8_release_gate_0.0.2.log | D-071e |
| Release profile, 0.0.2, run 2 | 6 of 7; pytest 4103 passed, 3 failed (PR-08 negative zero, two latency tests) | w8_release_gate_0.0.2_run2.log | D-073 |
| Latency tests alone, 0.0.2 sources | 5 of 5 runs pass | w8_timing_probe.log | D-074 |
| Release profile, 5f814d4 (0.0.3 sources) | main pytest gate passes (4198 passed); latency gate 2 of 6 fail | w8_release_gate_0.0.3.log | D-076 |
| Latency tests alone, ten runs | UI-05 over 100 ms in 1 of 10, N02-10 arrival in 4 of 10 (up to 218 ms) | w8_ui05_probe_10.log | D-076 |
| Cancel-test fix (U-M8v), 2fb2ec6 | 10 of 10 alone; latency gate 5 of 5 | w8_cancel_fix_10.log, w8_latency_gate_5.log | D-077 |
| Narrator (AX-06), 0.0.3 sources | the user reported it passed; it does not stand for 0.0.4 or 0.0.5 | AX-06_narrator_0.0.3.md | D-078, D-082 |

## Release 0.0.4 (wheel 9bca49d8…e579, checkout 94bd54d)

| Check | Result | Log | Row |
|---|---|---|---|
| PK-06 cold | stopped at step 3a: the network gave 8.5 kB/s (numpy 12.6 MB in about 25 min); not a product result | pk06_run5\ABORTED.txt | D-084e |
| PK-06 warm | 26.3 s to the first example, total 35.8 s, self-test 45 of 45 | pk06_run6.log | D-085 |
| PK-04 | four examples pass; the wave differs in `pairs_checked` only, a diagnostic per D-052b; with U-V20's tool all five pass | pk04_0.0.4_compare.log | D-085, D-086 |
| Commit profile (PK-01 cell) | 5 of 6; pytest 9 failed, 4089 passed | w7_commit_gate_0.0.4.log | D-086 |
| Release profile (W8) | 6 of 8; bundle built (71.6 s); pytest 11 failed, 4255 passed; latency gate failed | w8_release_gate_0.0.4.log | D-086 |
| Cause of 8 pytest failures | CRLF checkout (`core.autocrlf=true`, no .gitattributes), DEF-W-13; fixed in 0.0.5 | same | D-086 |
| tests/bundle | the unsigned `embodic-cli.exe` was blocked: `WinError 4551`, Application Control policy, DEF-W-14 | w8_release_gate_0.0.4.log | D-086 |
| Latency tests alone after the release gate | 3 of 5 runs fail (N02-10 arrival 225 to 255 ms) | w8_latency_0.0.4_run1-5.log | D-086 |
| Latency A/B, 2fb2ec6 against 94bd54d | 10 of 10 pass; arrival median 40 ms without the layer cue, 41 ms with it | w9_latency_ab.txt | D-086 |
| DRC pairs probe | wave path:95/prim:0 splits into 2 pieces on Windows and 3 on Linux; no left-out pair violates | drc_pairs_windows_0.0.4.json | D-086 |

## Release 0.0.5 (wheel a56eaebb…6096, checkout 513e872)

| Check | Result | Log | Row |
|---|---|---|---|
| Line ends after the sync to bbeed84 | 0 files checked out with CRLF, 1622 with LF (`git ls-files --eol`) | session record | - |
| PF-01 (source of 0.0.5, checkout bbeed84) | full recompute p95 0.913 to 1.003 s against 1.0 s; physics p95 0.617 to 0.663 s against 0.3 s; REQ-N-01 not met, DEF-W-15 | pf01_0.0.5.log, pf01_numbers_0.0.5.txt | D-087 |
| PK-06 warm | 21.2 s to the first example, `embodic 0.0.5`, self-test 45 of 45 | pk06_run7.log | D-090 |
| PK-04 | all five examples pass at rel 1e-9 against U-V21's reference | pk04_0.0.5_compare.log | D-090 |
| DRC pairs probe | the same split tie as 0.0.4; no left-out pair violates | drc_pairs_windows_0.0.5.json | D-090 |
| Commit profile (PK-01 cell) | stopped at 32 % when the Claude desktop app updated itself at 07:42; no result; rerun later (user) | w7_commit_gate_0.0.5.log | D-091 |
| Release profile (W8, PK-05) | not started; rerun later (user) | - | D-091 |
| Latency tests alone, five runs | not started; rerun later (user) | - | D-091 |
| PK-06 cold | not run since D-084e; it waits for a normal network | - | - |
| Narrator (AX-06) on 0.0.5 | the user runs it later | - | D-091 |

## What is not tested on Windows

- The real display (W6): the user saw the 0.0.3 view of D08 and reported the layer misreading of D-078. Nobody has
  looked at the 0.0.4 and 0.0.5 views on Windows yet.
- Windows high contrast with the layer cue: tested offscreen on Linux only (D-083b).
- The PyInstaller bundle could not run on this laptop (DEF-W-14).
