Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5 (unit U-V30)

# Windows records of release 0.0.6 in the manual-record index (D-100), 2026-10-22 UTC

This note says what U-V30 added to `manual_records.json` and why. `tests/independent/m7/v30_index.py --write` writes
the index from U-V29's index (8e4159d), so a reviewer can rerun it. Every Windows result below is Fable's, read from
the record file and the decision row that each entry names. I read no laptop log, because the logs hold the Windows
account name and stay on the laptop (order 6). I ran nothing on Windows (order 8).

## The platform in each entry

D-100b rules that a `NEEDS` ID counts when a current record from the machine that `NEEDS` names exists.
`checks/req_audit.py` reads the machine from the note of `embodic_version`: the platform is the first item of the note,
before the first comma or semicolon. TR-01 reads only the version token (D-083c, D-084a), so the platform changes
nothing there.

- The eight new entries start their note with `Windows laptop`.
- The Linux PK-06 entry now starts with `Linux container`. U-V29 ran it in the cloud container.
- The OR-11 and OR-12 entries now start with `GetDP FEA of c25d8a9 on the Linux container`. Their FEA half is the
  GetDP run of c25d8a9, and U-V29 redid the embodic half on the release wheel (`OR-11_OR-12_2bfca49.md`).
- The other four entries keep their text.

## The new entries

| Row, test | Record | Result | What the record holds | Row |
|---|---|---|---|---|
| REQ-N-04 PK-04 | `docs/phase3/fable/windows_campaign_w2.md` | passed | all five examples pass at rel 1e-9 against U-V29's reference | D-098a |
| REQ-N-06 PK-05 | `docs/phase3/fable/windows_campaign_w2.md` | passed | the release run built the bundle and `tests/bundle` passed 6 of 6 | D-099a |
| REQ-N-07 PK-06 | `docs/phase3/fable/PK-06_windows_0.0.6.md` | passed | runs 11 and 12: 22.3 s and 19.3 s to the first computed example, self-test 45 of 45 | D-100a |
| REQ-N-05 PK-02 | `docs/phase3/fable/PK-06_windows_0.0.6.md` | passed | runs 11 and 12: hashed lock file and wheel in a clean venv | D-100a |
| REQ-N-06 PK-11 | `docs/phase3/fable/PK-06_windows_0.0.6.md` | passed | run 11: `embodic-cli selftest` 45 of 45 in a clean venv with only the lock file and the wheel | D-100a |
| REQ-N-05 PK-01 | `docs/phase3/fable/windows_campaign_w2.md` | failed, `accepted` D-100 | W7, the commit profile: 5 of 6, `tests/bundle` against the 0.0.5 bundle | D-098c, D-100c |
| REQ-N-05 PK-02 | `docs/phase3/fable/windows_campaign_w2.md` | failed, `accepted` D-100 | W8, the release profile: 6 of 8, the PK-02 tests could not start the launcher (DEF-W-16) | D-099a, D-100c |
| REQ-N-06 PK-11 | `docs/phase3/fable/windows_campaign_w2.md` | failed, `accepted` D-100 | W8: the PK-11 test could not start the launcher (DEF-W-16) | D-099a, D-100c |

The release wheel is `fdb89189…0101` of tag v0.0.6 on 2bfca49. The laptop checkout 6ac95ac differs from 2bfca49 only
in `docs/` and in records, references and results under `tests/independent/` (`verified`, `git diff --name-only
2bfca49 6ac95ac`). Runs 9 and 10 are not indexed, because no embodic command ran in them (D-100a).

## W8 as two entries

The interface gives each entry one planned test ID (`interfaces.md` section 3.2). The brief names W7 by its ID, the
PK-01 cell. It names W8 only as "the release run", and no planned test ID stands for the whole release profile. D-100c
accepts the three failed pytest tests of W8 by name as DEF-W-16's launcher block. Those tests are PK-02 (two tests) and
PK-11 (one test) (D-099a), so W8 has one entry for each ID. PK-05 passed in the same run and has its own passed entry.

The latency failure of W8 (the N02-10 cancel case, DEF-W-12) has no entry. D-100b keeps REQ-N-02 at its status, and
an entry that names UI-45 would make the row `failed` in the audit. No Windows latency run has been indexed before
(D-076c, D-095c, D-099b). This is my reading of the brief (`inferred`), and Fable can add the entry.

## TR-01 on this index

`python3 -I tools/trace_matrix.py --report /home/claude/release_0.0.6/req_report.json
/home/claude/release_0.0.6/req_report_latency.json --fail-untested-through M5 --manual-records
docs/phase3/verification/manual_records.json`, on this worktree (`__version__` 0.0.6), prints:

```
trace matrix: 110 requirements, 4454 tests, 102 requirements with a passing test; manual: 11; invalid manual records: 0; TR-02 unmarked tests: 0; unknown REQ IDs: 0; untested due: 0; manual records not passed: 0 failing, 4 accepted
```

It exits 0 (`verified`). The four accepted records are PF-01 (D-091), PK-01, PK-02 and PK-11 (D-100). All 11 passed
entries name 0.0.6, so none is stale.

## What the audit does with the failed entries

The audit gives `fail` evidence to every planned ID that a failed entry names, accepted or not (U-V21, the rule that
keeps REQ-N-01 `failed`, D-091a). With W7 and W8 indexed, REQ-N-05 (PK-01 and PK-02) and REQ-N-06 (PK-11) are
`failed` in `req_audit.md`. D-100b says that REQ-N-06 closes when U-V30 indexes the Windows records, and it closes
REQ-N-05 with PK-02 and W7. Indexed as D-100c and D-093c rule, neither row can close in the audit. D-100 names no audit exception for an accepted record, so I applied none.
D-100b and D-100c close both rows for point 1 by name, and `phase3_report.md` section 6 says so.
