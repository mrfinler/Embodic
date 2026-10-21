Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5 (unit U-V29)

# Manual records for the 0.0.6 release (D-096), 2026-10-22 UTC

Release 0.0.6 is tag v0.0.6 on 2bfca49 (D-096), wheel `embodic-0.0.6-py3-none-any.whl` SHA-256
`fdb89189161d14b71433c4e35861d4e4d56fc6a7e64383f96ba13e27ba450101`. U-V28 made or stamped the seven entries of
`manual_records.json` for the candidate 672297e (`manual_records_0.0.6_672297e.md`). This note applies the D-096 rule
to PK-06, OR-11 and OR-12, the three entries made on U-V28's candidate wheel. Every line is `verified` by running or
reading it, unless it carries another label. Full outputs: `manual_records_0.0.6_release_currency.txt` beside this
note.

## The rule

D-096 refines D-061d. A record made on a candidate wheel stands for the release wheel when both hold:

1. the two wheels differ only in `RECORD` and in the evidence file's `build_id`, `generated_utc` and `git_commit`;
2. the evidence lists the same passed test IDs.

If the rule holds, the entry is restamped to the release. If it does not hold, the record is redone.

## The comparison

`tests/independent/m7/v21_wheel_diff.py` compared the candidate wheel ad9e02c0 (U-V28's build of 672297e, the file in
U-V28's scratch folder, SHA-256 `ad9e02c073c45668938621ebeea8f8ca9b42cae9036c869a0871de3da2802aaa`, not rebuilt) with
the release wheel, member by member:

- 274 members each, none only in one wheel.
- 3 members with other bytes: `embodic-0.0.6.dist-info/RECORD`, `embodic/_resources/evidence/passed_tests.v1.json` and
  `embodic/_resources/icons/ICONS.md`.
- In the evidence file, `build_id`, `generated_utc` and `git_commit` differ. `passed_tests` (58 IDs), `source_sha256`,
  `realised_by`, `gate_profile`, `git_dirty`, Python and NumPy are equal.
- `ICONS.md` differs in one table row. The use of `settings.svg` changed from "Toolstrip Help > Settings (Ctrl+,)" to
  "Not used; no settings window is in scope (D-094b)". In git this is `resources/icons/ICONS.md` and
  `tools/design/build_icons.py`, changed between 672297e and 2bfca49. It is the only file of `README.md`,
  `docs/install/INSTALL.md`, `requirements/`, `pyproject.toml`, `src/`, `resources/`, `tests/static/` and
  `oracle_cases.json` that changed (`git diff --stat 672297e 2bfca49`).

Ruling. Clause 2 holds. Clause 1 does not, because `ICONS.md` is a third member with other bytes. The rule does not
hold, so PK-06, OR-11 and OR-12 are redone on the release wheel, not restamped. No file under `src/embodic` names
`ICONS.md` (`grep`), so the difference reaches no computed value (`inferred`; the redos below agree). The rule as
written still admits no exception for a documentation member, and I did not add one.

## The redos

| # | Row, test | Record of U-V28 | Redo on the release wheel | Result |
|---|---|---|---|---|
| 0 | REQ-N-07 PK-06 | `PK-06_walkthrough_672297e.md` (passed) | `tests/independent/m5/records/PK-06_walkthrough_2bfca49.md` | passed: three cold runs, 22.9 to 50.9 s against 10 minutes, every guide output equal to the guide, self-test 45 of 45 |
| 2 | REQ-F-11 OR-11 | `OR-11_OR-12_672297e.md` (passed) | `tests/independent/m6/records/OR-11_OR-12_2bfca49.md` | passed: of 310 leaves of `embodic_reference.json`, only `embodic_file` changed |
| 3 | REQ-F-11 OR-12 | same | same | same |

Every redo gave the result of its old record. The release wheel ran in each PK-06 run folder (hash checked in each)
and, for OR-11 and OR-12, in the fresh venv `/home/claude/wheelvenv-0.0.6` that also produced the PK-04 reference
(`reference/README.md`, release 0.0.6). The installed evidence file was byte-identical to
`/home/claude/release_0.0.6/passed_tests.v1.json` in all four venvs.

## The other four entries

Nothing else changes, as the brief says. AX-05, LG-01 and LG-04 keep their records and stamps. Their git subjects do
not change between their builds and 2bfca49 (`v14_record_currency.py --target 2bfca49` on the U-V28 index: entries
1, 4 and 5 stand). PF-01 stays `failed`, accepted by D-091, and still names 0.0.5. Its redo needs the reference
laptop.

LG-04 named the candidate wheel as well as the source tree. Its stamp still names ad9e02c0, so I ran the lister once
on the files the release wheel installed (`PYTHONPATH=/home/claude/wheelvenv-0.0.6/lib/python3.11/site-packages`, the
project venv's Python for pypdf). Its output is byte-identical to `LG-04_T-11_listing_672297e.txt` (`cmp`). The entry
is unchanged, as the brief orders, and that output was not committed.

## The index for the release

`manual_records.json` holds seven entries. PK-06, OR-11 and OR-12 name the 2bfca49 records, and their
`embodic_version` reads `0.0.6 (release wheel fdb89189 of tag v0.0.6 on 2bfca49, D-096, U-V29; <this note>)`. The
other four are unchanged. `checks/req_audit.py` follows `REDONE` from each 672297e wheel record to its 2bfca49 redo
(`--self-test` passed; `last_redo` of the 6d50d0b PK-06 record and of the 42074f2 OR record ends at 2bfca49).

TR-01 on this index with the release gate's two REQ reports (`/home/claude/release_0.0.6/req_report.json` and
`req_report_latency.json`), `--fail-untested-through=M5`, prints the release gate's line: `manual: 6; invalid manual
records: 0; TR-02 unmarked tests: 0; unknown REQ IDs: 0; untested due: 0; manual records not passed: 0 failing, 1
accepted`, exit 0.

Limits. `tests/independent/m7/v14_record_currency.py` has no subject for the two new records and prints `no subject
defined here` for entries 0, 2 and 3 of this index. That file is outside this unit's scope, so its next user adds the
two subjects (the 672297e subjects with the build 2bfca49 and the release wheel). `req_audit.py --target 0.0.1
--self-test` did not run, because its inputs in `/home/claude/release_0.0.1/` are not on this machine.
