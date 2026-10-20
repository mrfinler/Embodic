Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5

# PK-04 Linux reference

## DEF-UV10-01 tested (U-V20, 2026-10-21)

D-085 records the Windows run of the 0.0.4 wheel: four examples pass, and the wave fails on one value,
`/drc/0/summaries/0/pairs_checked` 3461 (Linux) against 3462 (Windows). The release 0.0.1 section below gave the cause
as a guess: a candidate pair at the broad-phase limit that float noise moves in or out. U-V20 tested that premise on
Linux with the 0.0.4 wheel venv. Each line below is `verified` by running it, unless it carries another label.

The probe. `checks/drc_pairs_probe.py` computes the wave example and replays the pair loop of `run_drc` with the
engine's own functions. Its Linux output is `drc_pairs_linux_0.0.4.json.gz` (gzip, one JSON object). The replay gives
the same counts as `run_drc` for every pair kind (trace_trace 3461) and the same pair set per layer group. Two runs
gave the same JSON.

The premise is false as stated. The near test of `candidate_pairs` (`src/embodic/drc/engine.py` l.149) keeps a piece
pair when `|mid_p - mid_q| <= span_p + span_q + rule_mm + 1e-9`. Over every trace_trace pair within 0.05 mm of that
cutoff, the kept pair nearest it lies 2.502e-3 mm inside it, and the left-out pair nearest it lies 3.658e-3 mm outside
it. Float noise between two platforms is about 1e-13 mm, which is 10 orders of magnitude smaller. Disabling NumPy's
AVX-512 and AVX2 kernels (`NPY_DISABLE_CPU_FEATURES`) changed no slack value at all, so the dispatch did not change
these floats on this machine.

What does move the count is the piece split. `_pieces` (l.87) cuts an item into `ceil(length / 0.5 mm)` pieces. Twelve
trace primitives of the wave board are 1.0 mm long, so the ratio is 2 within 1e-14. On Linux, six round down to 2
pieces and six up to 3 (for example `path:93/prim:0`, ratio 2.000000000000004, 3 pieces). The probe moves each one
across the integer by 1e-13 relative inside `_pieces` only and reruns `run_drc`. Six of the twelve flips change the
trace_trace count by one (four to 3462, two to 3460). Each flip adds or removes one pair at clearance 0.4488 mm against the 0.2 mm
rule. All twelve flips keep 186 violations. Flipping all twelve gives 3463. Which item rounds the other way on Windows
is `not tested`. The probe below names it.

The margin. The count is a diagnostic, because no pair the broad phase leaves out can violate a rule. For every piece
of an item, every point of the item's copper lies within `span = reach + half width` of the piece midpoint (l.81 and
l.102-106, read). So a pair's clearance is at least `|mid_p - mid_q| - span_p - span_q` for the closest pieces. That
bound held for all 4072 pairs near the cutoff: clearance minus bound is at least 4.4e-16 mm. A left-out pair therefore
has a clearance above `rule_mm + 1e-9`, where `rule_mm` is the largest pair rule plus `DRC_EPSILON_MM` (l.239). A
violation needs a clearance below `required_k - DRC_EPSILON_MM` (`report.py` l.56). The margin is
`(max rule - required_k) + 2 x 1e-6 + 1e-9` mm. That is at least 2.001e-6 mm for the pair kind with the largest rule,
and 0.100002001 mm for trace_trace on the wave rules (0.2 mm, largest 0.3 mm). The grid cell of l.121 is
`2 x max span + rule_mm + 1e-9`, no smaller than the near threshold of any piece pair, so a violating pair sits in the
same or an adjacent cell with the same margin to spare (read; the replay found the grid's pairs). Any piece count keeps the bound, so the margin is the same for every split. The
exhaustive pass of the probe measured all 1,511,143 left-out pairs of the wave board (trace_trace 1,060,944): no
violation, and the least left-out trace_trace clearance is 0.448812 mm.

The rule in the tool. D-052b stands: `pairs_checked` of a pair kind is a same-platform diagnostic. `pk04_compare.py`
now leaves out `/drc/*/summaries/*/pairs_checked` for the seven pair kinds and lists it under "not compared". It still
compares `pairs_checked` of `min_width`, `min_drill` and `annular_ring`, which count objects. The self-test has two new
cases. A trace_trace count changed by 1 passes. A min_width count changed by 1 fails and names the pointer. All 10
cases pass. Two seeded faults each fail one case: a tool without the rule fails the first case, and a tool that leaves
out every `pairs_checked` fails the second. A fresh Linux run of the 0.0.4 wheel against `linux/` passes, and all six
files are byte-identical. With the wave's trace_trace count set to 3462 in a copy, the 2cedac6 tool prints the D-085
line and fails, and this tool passes. Whether the Windows folder now passes is Fable's run on the laptop (`not tested`
here).

Spec text. test_plan.md "PK-04 rule" part 5 still says that integers compare exactly and that `/versions/python` is the
one pointer allowed to differ. The text does not carry D-052b or the hash parts. That part is Agent 6's to amend.

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
