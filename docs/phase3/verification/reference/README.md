Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5

# PK-04 Linux reference

## Release 0.0.4 (U-V18, 2026-10-20)

`linux/` is the output of `pk04_reference.py` for release 0.0.4 (tag v0.0.4, commit c25d8a9). Release 0.0.3 was not
released (D-078f). 0.0.4 changes `src/` against 0.0.2 (`git diff --stat 0a74974 c25d8a9 -- src`: 11 files, 425
insertions, 67 deletions), so the 0.0.2 reference no longer compares. Each line below was `verified` by running it.

- The wheel is `/home/claude/release_0.0.4/embodic-0.0.4-py3-none-any.whl`, SHA-256
  `9bca49d895aee779be71cda8b939b67f86414ef8f711d7090b9c01215a6de579` (`sha256sum`), the value D-081 records.
- It went into a fresh venv `/home/claude/wheelvenv-0.0.4` (`/usr/bin/python3.11 -m venv`, CPython 3.11.17) by the two
  commands of `requirements/README.md`: `pip install --require-hashes -r requirements/py311.txt`, then
  `pip install --no-deps <wheel>`. `pip freeze` lists embodic 0.0.4 (the wheel, with its sha256), numpy 2.4.6,
  PySide6_Essentials 6.11.2 and shiboken6 6.11.2, nothing else.
- The installed sources hash to `c40e8ce744ba6840db25134bc66c8213b393b8ce174265461165e5b93b9cc63d`
  (`package_source_sha256`). The wheel's evidence file `_resources/evidence/passed_tests.v1.json` is byte-identical to
  `/home/claude/release_0.0.4/passed_tests.v1.json` (`cmp`) and names the same `source_sha256`, git commit c25d8a9,
  `git_dirty` false, profile `release`, Python 3.11.17 and 58 passed test IDs. `src/embodic` of main 705c1cb hashes to
  the same value, and `git diff c25d8a9 705c1cb -- src` is empty.
- Command: `QT_QPA_PLATFORM=offscreen /home/claude/wheelvenv-0.0.4/bin/python -I
  docs/phase3/verification/checks/pk04_reference.py --out <folder>`. `-I` keeps the worktree's `src/` off the path.
  Four examples exit 0. The wave example exits 2 with 186 DRC violations, as D-034 expects. One run takes about 8 s.
- Two runs into two scratch folders gave six byte-identical files each (`cmp`). The committed files are the first run.
- `pk04_compare.py --self-test docs/phase3/verification/reference/linux` passes all 8 cases (exit 0). Comparing this
  folder with the second run prints `PK-04 passed at rel 1e-09`, every file byte-identical (exit 0). Comparing the
  0.0.2 reference with this one is refused (exit 2) on `embodic_source_sha256`, as designed.

What changed against the 0.0.2 reference. I compared the two folders with `pk04_compare.diff`, file by file, past the
manifest refusal. Each example differs in exactly two places: `/versions/embodic` (0.0.2 to 0.0.4) and one DRC
`pairs_checked` count. `trace_trace` rises by 12 on the four spiral and serpentine examples (serpentine 3405 to 3417,
D08 662 to 674, 12c14p 2894 to 2906, 12c16p 2902 to 2914), and `trace_via` rises by 3 on the wave (597 to 600). No
violation, `least_clearance_mm`, status field, EMF value or design hash changed, and the five CLI stdout blocks and exit
codes are equal. More pairs reach the clearance measurement because U-D25 narrows the rule 5 and rule 2 exemptions to
one primitive (D-079b, D-080a); that link is `inferred` from the rulings, not traced pair by pair.

Windows comparison for 0.0.4 has not run here. It is Fable's W5 step on the laptop, against this folder.

## Release 0.0.2 (U-V15, 2026-10-19, history)

`linux/` was the output of `pk04_reference.py` for release 0.0.2 (in git at a9f9bb7). Each line below was `verified` by
running it.

- The wheel is `embodic-0.0.2-py3-none-any.whl`, SHA-256 `60d3cd112479632ef0e95f6845bfc5abf66cbdd59b014c0a4bfeda47833d0f07`
  (`sha256sum`), the value D-070 records.
- It went into a fresh venv `/home/claude/wheelvenv-0.0.2` (CPython 3.11.17) by the two commands of
  `requirements/README.md`: `pip install --require-hashes -r requirements/py311.txt`, then `pip install --no-deps <wheel>`.
  `pip freeze` lists embodic 0.0.2, numpy 2.4.6, PySide6_Essentials 6.11.2 and shiboken6 6.11.2, nothing else.
- The installed sources hash to `ccad3d7f7e68816d5dde3ecdb30f8739f697963d952a8d65f5b54dfa0d6ea44a`
  (`package_source_sha256`). The wheel's evidence file `_resources/evidence/passed_tests.v1.json` names the same
  `source_sha256`, git commit 0a74974 (tag v0.0.2), `git_dirty` false, profile `release` and 58 passed test IDs.
  `src/embodic` of main 6555588 hashes to the same value, and `git diff 0a74974 6555588 -- src` is empty.
- Command: `QT_QPA_PLATFORM=offscreen /home/claude/wheelvenv-0.0.2/bin/python -I
  docs/phase3/verification/checks/pk04_reference.py --out <folder>`. `-I` keeps the worktree's `src/` off the path.
  Four examples exit 0. The wave example exits 2 with 186 DRC violations, as D-034 expects.
- Two runs into two scratch folders gave six byte-identical files each (`cmp`). The committed files are byte-identical
  to both runs.
- `pk04_compare.py --self-test` passes all 8 cases on these files. Comparing this folder with a second run prints
  `PK-04 passed at rel 1e-09`. Comparing the 0.0.1 reference with this one is refused (exit 2) on the source hash,
  as designed.

What changed against the 0.0.1 reference. The design hashes and the CLI lines are unchanged. The status fields
changed. In 0.0.2 every EQ-05 and EQ-06 result carries "EQ-05 tests not passed in this build" or the EQ-06 one,
because the registry now links EQT-05-O2 and EQT-06-O2 to those equations and the release evidence holds neither.
EQ-14 (EQT-14-O2), EQ-28 (EQT-28-GR) and EQ-29 (EQT-29-GR) also miss a linked test. This list comes from
`load_registry()` in the wheel venv, comparing each equation's `tests` with `passed_tests`. That is the build's
behaviour, not a reference defect. Whether EQ-05 and EQ-06 should show `not tested` in the release is a ruling for
Agent 2 and Fable, outside this reference.

Windows comparison for 0.0.2 has not run here. It is Fable's W5 step.

## Release 0.0.1 (U-V10, history)

The 0.0.1 reference was the output of `pk04_reference.py` run with the Python of `/home/claude/wheelvenv`, which had
the 0.0.1 release wheel installed (embodic 0.0.1, NumPy 2.4.6, Python 3.11.15, source SHA-256 `cfefe405…baae`). All six
files were byte-identical to Fable's run in `/home/claude/pk04_linux_wheel` (`cmp`, `verified`). It is in git at
1939b13.

### Why the earlier reference differed

The earlier files (commit 0a5a351) differ from these in 294 places over the five examples. Every one of them is a
`status` or `status_reasons` field (`verified`, counted with pk04_compare.diff). The earlier files list
"EQ-nn tests not passed in this build" for every equation. I copied the installed package, deleted
`_resources/evidence/passed_tests.v1.json` from the copy and ran `pk04_reference.py` on it: all six output files are
byte-identical to the earlier reference (`verified`). The earlier reference therefore came from the same sources
without the build's evidence file. The file is a build product (`tools/record_passed_tests.py`) and is not in git, so a
source checkout lacks it (`inferred` from `git ls-files`).

### Comparison with the Windows output (W1)

`python3 -I docs/phase3/verification/checks/pk04_compare.py docs/phase3/verification/reference/linux <pk04_windows>`
exits 1 (`verified`):

```
not compared: /boards/layout_hashes, /boards/stack_hash, /versions/python
pass serpentine_16p_example.json: 0 differences, byte-identical False
pass spiral_12c10p_d08.json: 0 differences, byte-identical False
pass spiral_12c14p.json: 0 differences, byte-identical False
pass spiral_12c16p_default.json: 0 differences, byte-identical False
FAIL wave_16p_example.json: 831 differences, byte-identical False
  /drc/0/summaries/0/pairs_checked: 3461 != 3462
  /drc/0/violations/0/at_mm/0: 14.819969569209762 != 40.723443523579945 (abs 2.590e+01 > 1e-9 x array peak 40.7234)
PK-04 failed at rel 1e-09
```

All 831 wave differences lie under `/drc`. After sorting both violation lists by (kind, layer, objects), the 186
violations agree within the rules (0 differences, 186 unique keys on both sides, `verified`). That part is DEF-W-01.

One difference is not an order effect. The `trace_trace` summary counts `pairs_checked` 3461 on Linux and 3462 on
Windows (`verified`). `pairs_checked` is the number of pairs that reach the clearance measurement
(`src/embodic/drc/engine.py` l.318-325). A canonical violation order does not change this count, so PK-04 still fails
after DEF-W-01 is fixed (`inferred`). The cause, a candidate pair at the broad-phase limit that float noise moves in or
out, is a guess (`not tested`). This is DEF-UV10-01.
