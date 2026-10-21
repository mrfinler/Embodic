Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5 (unit U-V21)

# Manual records for the 0.0.5 release (D-061d, D-083c), 2026-10-21

Release 0.0.5 is tag v0.0.5 on 42074f2 (D-089), wheel `embodic-0.0.5-py3-none-any.whl` SHA-256
`a56eaebb9f3e2d7c62b87dda9f8baabd1980451157914c2a0431550f80946096`. U-V20 stamped the six records for the candidate
(99d355d, `manual_records_0.0.5.md`). This note rules whether each stands for the release, and indexes Fable's PF-01
record. Every line is `verified` by running or reading it, unless it carries another label.

## What differs between the candidate and the release

- Sources. `git diff --stat 99d355d 42074f2` changes, of the files any subject reads, only
  `docs/install/INSTALL_TH.md` (the Thai guide, which no record's subject names). `src/`, `resources/`,
  `pyproject.toml`, the lock files, `README.md`, `docs/install/INSTALL.md`, `tests/static/lg_allowlist.toml` and
  `oracle_cases.json` are unchanged. The release wheel's installed sources hash to `08d25a78…83df`
  (`package_source_sha256`), the value of its evidence file and of main.
- The wheel. `tests/independent/m7/v21_wheel_diff.py` compares the candidate wheel 0dbac116 (Agent 4's build of
  99d355d, U-V20) with the release wheel: 274 members each, none only in one, two with other bytes,
  `embodic-0.0.5.dist-info/RECORD` and `embodic/_resources/evidence/passed_tests.v1.json`. In the evidence file
  `build_id`, `generated_utc` and `git_commit` differ; the passed test IDs (58), `source_sha256`, `gate_profile`,
  `git_dirty`, Python and NumPy are equal. git cannot see this file, because it is a build product.
- Who reads the evidence file. `compute_project` loads it through `load_registry` (`src/embodic/api.py` l.246), and the
  self-test report carries its `build_id` as `evidence_build_id` (`src/embodic/selftest/runner.py` l.103). The PK-04
  outcome files of the two wheels are byte-identical for all five examples (`reference/README.md`, release 0.0.5), so
  the three differing fields reach no computed value (`verified` for those outputs).

The rule applied. D-061d compares the files a subject depends on with the build the record names. For a record made
on a wheel, that build is the wheel, and its members are the files. For a record made on a source tree, the build is
the commit, and git compares it. `tests/independent/m7/v14_record_currency.py --target 42074f2` gains the subjects of
the 99d355d records, the PF-01 record and the two new records; its full output and the wheel comparison are in
`manual_records_0.0.5_release_currency.txt`.

## The six entries of U-V20, and PF-01

| # | Row, test | Record of U-V20 | Build named | Git subject 99d355d to 42074f2 | Wheel | Verdict | Entry now |
|---|---|---|---|---|---|---|---|
| 0 | REQ-N-07 PK-06 | `PK-06_walkthrough_99d355d.md` (passed) | wheel 0dbac116 | no change | evidence file differs and is read (steps 5b, 6) | does not stand | Agent 4, `tests/independent/m5/records/PK-06_walkthrough_42074f2.md` (passed, 15.7 to 19.9 s) |
| 1 | REQ-N-14 AX-05 | `AX-05_99d355d.md` (passed) | source tree equal to 99d355d | no change | none used | stands | restamped |
| 2 | REQ-F-11 OR-11 | `OR-11_OR-12_99d355d.md` (passed) | wheel 0dbac116 | no change | evidence file differs and is read (`compute_project`) | does not stand | Agent 4, `tests/independent/m6/records/OR-11_OR-12_42074f2.md` (passed, embodic values bit-identical) |
| 3 | REQ-F-11 OR-12 | same | same | same | same | does not stand | same new record |
| 4 | REQ-L-01 LG-01 | `LG-01_word_review_c25d8a9.md` (passed) | source tree equal to c25d8a9 | no change (c25d8a9 to 42074f2) | none used | stands | restamped |
| 5 | REQ-T-11 LG-04 | `LG-04_T-11_reviewer_99d355d.md` (passed) | source tree equal to 99d355d | no change | none used | stands | restamped |
| 6 | REQ-N-01 PF-01 | `docs/phase3/fable/PF-01_windows_0.0.5.md` (failed), not indexed before | laptop checkout bbeed84, editable install | no change (bbeed84 to 42074f2) | none used | stands | indexed, `failed` |

The two redos gave the old results. PK-06: three cold runs on the release wheel, every guide output equal to the
guide, self-test 45 of 45; the totals are lower than the candidate's because pip downloaded at 12.8 to 21.7 MB/s
against 1.6 to 8.0 MB/s (`inferred` from pip's progress lines). OR-11 and OR-12: of 310 leaves of
`embodic_reference.json`, only `embodic_file` changed. A redo is not a claim that the evidence fields could change
these results; it is what the rule asks when a file the check reads changed.

Restamps. Entries 1, 4 and 5 keep their record files, as interfaces.md section 3.2 asks, and their
`embodic_version` now reads `0.0.5 (record of candidate 99d355d stands for release 42074f2 under D-061d, <this
note>)`, or for LG-01 `0.0.5 (LG-01 record of c25d8a9 stands for release 42074f2 under D-061d: corpus unchanged;
<this note>)`. `req_audit.py` follows `REDONE` from each 99d355d wheel record to its 42074f2 redo.

PF-01. Fable ran it on the reference laptop on the checkout bbeed84, whose `src/`, `resources/`, `pyproject.toml` and
`tests/performance/` equal 42074f2 (`git diff --stat bbeed84 42074f2 -- <those>`, empty), so the record stands for
the release. It is indexed with its real result, `failed`: physics p95 0.617 to 0.663 s against 0.3 s, full recompute
p95 0.913 to 1.003 s against 1.0 s (DEF-W-15, D-087). I did not rerun it; it needs the laptop.

## How TR-01 treats a failed record

Read in `tools/trace_matrix.py` and run on the release reports (`verified`):

- `parse_manual_records` accepts `"failed"` as a valid result, so the record is not invalid.
- `counted_records` counts only `passed` records, and lists as stale only `passed` records of another version. A
  `failed` record is neither counted nor listed. TR-01 prints nothing about it.
- `find_untested` takes coverage from passing tests and counted records. A failed record covers no row.

Runs with `--fail-untested-through M5` on the release reports of 42074f2:

| Index | Summary line | Exit |
|---|---|---|
| the release index | `manual: 6; invalid manual records: 0; ... untested due: 0` | 0 |
| the release index plus the failed PF-01 entry | the same line, PF-01 not named | 0 |
| the same, on a copy of the reports with every REQ-N-01 marker removed | `untested due: 1`, REQ-N-01 listed (and 9 unmarked tests, from the removal) | 1 |

So the 0.0.5 release gate passes TR-01 with the failed PF-01 record in the index, because 20 Linux tests that carry
REQ-N-01 passed: the budget logic of `test_n01_pf01_budgets.py` and the Linux PF-01 baseline. The gate log does not
show the failure. interfaces.md section 3.2 also says that a stale record is listed "whatever its result", and the
code lists only passed ones. Both are DEF-UV21-01 (`tests/independent/m7/records/defects.md`). The audit shows the
failure: `req_audit.py` now gives a planned ID with a failed record `fail` evidence and its row the status `failed`,
so REQ-N-01 reads `failed` in `req_audit.md` (rule in the script's docstring, control in `--self-test`).
