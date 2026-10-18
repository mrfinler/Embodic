Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5 (unit U-V14)

# Manual records for the 0.0.2 release gate (D-061d), 2026-10-18

D-061d rules that a manual record counts for a later release when the files its subject depends on are unchanged since
the build it names; otherwise the check is redone before that release gate. This note judges the seven entries of
`docs/phase3/verification/manual_records.json` on main c0f4894 and lists the index that the 0.0.2 gate reads.

Lever: `python3 -I tests/independent/m7/v14_record_currency.py --index <index> [--target c0f4894]`. It runs
`git diff --stat <build>..c0f4894` over each subject's fixed paths and the embodic modules its instrument imports, and
`--verbose` lists every file and every changed line count (798 lines on the c0f4894 index). Its
output on the c0f4894 index (`git show c0f4894:docs/phase3/verification/manual_records.json`) gives the first three
columns below (`verified` by running it).

## The seven entries of c0f4894

| # | Row, test | Record (result) | Build named | `git diff --stat` to c0f4894 | Verdict | Redone by, new record |
|---|---|---|---|---|---|---|
| 0 | REQ-N-07 PK-06 | `tests/independent/m5/records/PK-06_walkthrough.md` (passed) | wheel f114a6e7 of 5e74acc | 83 files changed | superseded | Agent 4, `tests/independent/m5/records/PK-06_walkthrough_c0f4894.md` (passed, 17.4 s to 26.8 s) |
| 1 | REQ-N-07 PK-06 | `docs/phase3/fable/windows_campaign_w1.md` (passed, warm cache) | the 0.0.1 wheel | 83 files changed | superseded | the user: timed walkthrough on the Windows laptop, not redone |
| 2 | REQ-N-07 PK-06 | `docs/phase3/fable/windows_campaign_w1.md` (failed, cold) | the 0.0.1 wheel | 83 files changed | superseded | the user, with entry 1 |
| 3 | REQ-N-14 AX-05 | `tests/independent/m4/records/AX-05.md` (passed) | main 4fda98d | 47 files changed | superseded | Agent 4, `tests/independent/m4/records/AX-05_c0f4894.md` (passed, 48 of 48) |
| 4 | REQ-F-11 OR-11 | `tests/independent/m6/records/OR-11_OR-12.md` (passed) | wheel f114a6e7 of 5e74acc | 34 files changed | superseded | Agent 4, `tests/independent/m6/records/OR-11_OR-12_c0f4894.md` (passed, values identical) |
| 5 | REQ-F-11 OR-12 | same record (passed) | same | 34 files changed | superseded | Agent 4, same new record |
| 6 | REQ-L-01 LG-01 | `tests/independent/m4/records/LG-01_word_review.md` (passed) | main 260191f | no change | stands | none |

The import closure is a superset of what a subject reads, so a superseded verdict means only that a rerun is needed.
Each of the three Agent 4 reruns gave the result of its old record: the FEA values and the AX-05 readings are
identical, and the Linux walkthrough passes in the same 17 s to 28 s band.

## The index for the 0.0.2 gate

`manual_records.json` now holds six entries, each one that stands for c0f4894: the three redone records (four entries,
OR-11 and OR-12 share one record), LG-01 (stands), and the new REQ-T-11 reviewer record
`tests/independent/m4/records/LG-04_T-11_reviewer.md` (test ID LG-04, passed). The superseded entries 0 to 5 left the
index; their files stay in the repository, and this note records them. `embodic_version` reads "0.0.1 (main c0f4894)"
for the new entries, because the version string on c0f4894 is still 0.0.1 (`src/embodic/__init__.py` l.3).

## Checks only a person can do (for the user)

- REQ-N-07: the timed PK-06 walkthrough of the 0.0.2 build on the clean Windows laptop, cold and warm pip cache
  (replaces entries 1 and 2). Until it runs, TR-01 counts REQ-N-07 through the Linux record alone, while the
  acceptance asks for a clean Windows machine; the main audit keeps the row `partial`.
- REQ-N-16 (AX-06): the Narrator check on Windows (`requirements.md` REQ-N-16).
- The Windows rows of the audit's Needs column: PK-01, PK-04 and PK-05 (`req_audit.py` NEEDS).
- AX-05 by a person with deuteranopia, and the window step 4 of PK-06 on a desktop: `not tested` by Agent 4's proxies.

## Release trace gate on main (brief item d)

Report. `tests/independent/m7/v14_main_report.py` built one REQ report of c0f4894 (stored as
`inputs/req_report_c0f4894.json.gz`, 4095 tests): node IDs and markers from a collect-only run of c0f4894 under the
release selection (`-m "not manual" --ignore=tests/packaging/evidence`); outcomes from Fable's commit gate on 5099401
(`inputs/gate_commit_5099401.log`, 6 of 6 gates, 3872 passed) for 4035 tests, because src, resources, tools,
pyproject.toml and requirements are identical between 5099401 and c0f4894 and the test files are unchanged; outcomes
from Agent 4's run on c0f4894 for 40 tests (the three PK-02 tests and the two test files U-V13 changed, `40 passed in
34.98s`). 184 tests stay `not run`: 164 slow tests and 20 performance and packaging tests.

Command and output (`verified` by running it):

```
python tools/trace_matrix.py --report req_report_c0f4894.json --fail-untested-through M5 \
    --manual-records docs/phase3/verification/manual_records.json
trace matrix: 110 requirements, 4095 tests, 99 requirements with a passing test; manual: 6; invalid manual records: 0; TR-02 unmarked tests: 0; unknown REQ IDs: 0; untested due: 1
  REQ-N-10
```

The release profile would refuse REQ-N-10 only, with the 0.0.2 index and with the c0f4894 index alike. On the commit
gate report alone it also lists REQ-N-05, whose only tests are the PK-02 tests under `tests/packaging`; the release
profile runs that folder, and the PK-02 tests pass on c0f4894. Not tested here: the 184 `not run` tests and the other
gates of the release profile (nightly Hypothesis, evidence, wheel, PK-10), which can fail the release without a TR-01
refusal.

## Requirement audit regenerated

`python3 docs/phase3/verification/checks/req_audit.py --target main` writes `req_audit.md` for main c0f4894 from the
report above, U-V13's re-ruling (`v3_01_rulings_v13.py`, pins of 260191f), U-V14's two re-rulings on top
(`v3_01_rulings_v14.py`: REQ-T-11 `checks` with the reviewer record, REQ-N-07 `partial` with the Windows walkthrough
missing) and this index. Must rows: verified 44, partial 28, not tested 1 (REQ-N-10). U-V13 ruled 51 rows `checks`;
the audit keeps 8 of them `partial` because its text rule also needs evidence for every planned test ID of the row
(REQ-F-03, REQ-F-34, REQ-N-12, REQ-N-19, REQ-N-21, REQ-N-27, REQ-T-15) or because the row needs Windows (REQ-N-07, PK-06
in NEEDS); 51 − 8 = 43, plus REQ-T-11 gives 44 (`verified` by a count over both files). `--target 0.0.1` writes the
0.0.1 release audit to `req_audit_0.0.1.md`; on the same inputs it reproduces the c0f4894 script's output except for
the command line in its header (`verified` by running both).
