Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5 (unit U-V27)

# Manual records for 0.0.6 (D-061d, D-083c, D-093c), 2026-10-21 UTC

The 0.0.6 candidate is main 6d50d0b (D-093d, D-094). Since D-083c, TR-01 counts a passed record only when its
`embodic_version` names the version under test, so every 0.0.5 entry of the index is stale for 0.0.6. This note rules
whether each of the seven entries stands for 6d50d0b and lists the index that replaces them. Every line is `verified`
by running or reading it, unless it carries another label.

## What changed between 0.0.5 and 6d50d0b

`git diff --stat 42074f2 6d50d0b -- README.md docs/install requirements pyproject.toml resources src tests/static`
(read): the version strings (`src/embodic/__init__.py`, the wheel name and `embodic 0.0.6` in README.md and
INSTALL.md, `app_version` and `engine_version` of the five examples), six files under `src/embodic/ui` (the unit labels
of Copper weight and Board thickness, the message `chart.no-dc-link`, the keys Ctrl+Shift+S, Ctrl+Shift+Z, Ctrl+P and
Ctrl+/, the constant `KEYS_TOPIC`), and the allow-list pattern of that message. The lock files, pyproject.toml, the
themes, the evidence registry and `oracle_cases.json` are unchanged.

Not in 6d50d0b: U-M9e (in flight, D-094b) edits the guide text in `src/embodic/ui/strings/results.py`. Records whose
subject holds that file (LG-01, LG-04, PK-06) will be superseded again when it merges; AX-05 and OR-11/OR-12 hold no
`src/embodic/ui` file and would stand if U-M9e changes only what its brief names (`inferred` from the brief, to be
checked with the lever on the merge commit).

## The rule and the lever

D-061d compares the files a subject depends on with the build the record names; for a wheel record the wheel's members
are the files (U-V21). Lever: `python -I tests/independent/m7/v14_record_currency.py --target 6d50d0b --verbose`, and
`tests/independent/m7/v21_wheel_diff.py` for the wheel. U-V27 adds the subjects of the five new 6d50d0b records to the
lever, and `docs/phase3/verification/checks/req_audit.py` follows `REDONE` from each superseded record to its redo.
Full outputs: `manual_records_0.0.6_currency.txt` beside this note.

## The seven entries

| # | Row, test | Record (result) | Build named | Changed files of the subject to 6d50d0b | Verdict | Entry now |
|---|---|---|---|---|---|---|
| 0 | REQ-N-07 PK-06 | `PK-06_walkthrough_42074f2.md` (passed) | release wheel a56eaebb | 14 files: README, INSTALL, 5 examples, `__init__.py`, 6 `ui` files; 13 wheel members | does not stand | redone, `tests/independent/m5/records/PK-06_walkthrough_6d50d0b.md` (passed, 28.6 to 64.2 s, self-test 45 of 45) |
| 1 | REQ-N-14 AX-05 | `AX-05_99d355d.md` (passed) | source tree = 99d355d | 6 files: 5 examples (version lines), `__init__.py` | does not stand | redone, `tests/independent/m4/records/AX-05_6d50d0b.md` (passed, 48 of 48) |
| 2 | REQ-F-11 OR-11 | `OR-11_OR-12_42074f2.md` (passed) | release wheel a56eaebb | 1 file: `__init__.py`; evidence file of the wheel | does not stand | redone, `tests/independent/m6/records/OR-11_OR-12_6d50d0b.md` (passed, comparator values bit-identical) |
| 3 | REQ-F-11 OR-12 | same | same | same | does not stand | same new record |
| 4 | REQ-L-01 LG-01 | `LG-01_word_review_c25d8a9.md` (passed) | source tree = c25d8a9 | 1 file: `ui/strings/results.py` (one message) | does not stand | redone, `tests/independent/m4/records/LG-01_word_review_6d50d0b.md` (passed, 806 words, one added: `tab`) |
| 5 | REQ-T-11 LG-04 | `LG-04_T-11_reviewer_99d355d.md` (passed) | source tree = 99d355d | 9 files: 5 examples, `__init__.py`, the allow-list, `ui/strings/results.py`, `ui/viewmodels/results.py` | does not stand | redone, `tests/independent/m4/records/LG-04_T-11_reviewer_6d50d0b.md` (passed, listing equal but for the allow-list hash) |
| 6 | REQ-N-01 PF-01 | `docs/phase3/fable/PF-01_windows_0.0.5.md` (failed, accepted D-091) | laptop checkout bbeed84 | 6 files: 5 examples (version lines), `__init__.py`; no `ui` file | does not stand | unchanged: `failed`, `accepted` D-091, `embodic_version` still 0.0.5 |

No entry stands, so none is restamped. Every redo gave the result of its old record. The changes behind entries 1, 2,
3 and 6 are version strings only, which would not change what those checks observe (`inferred`); that inference does
not replace the rule, as U-V20 wrote.

PF-01. Its redo needs the reference laptop, which this unit cannot reach. The entry keeps its real result and its
acceptance, and it keeps naming 0.0.5, because a restamp would claim that it stands. TR-01 lists a failed record that
`accepted` covers whatever its version, and lists as stale only passed records (`tools/trace_matrix.py`
`counted_records` and `unpassed_records`, read), so the entry neither counts nor blocks. A PF-01 run on 0.0.6 is Fable's.

## The candidate wheel

`embodic-0.0.6-py3-none-any.whl`, SHA-256 `5d891a268323fed9ce3414db3b042d27e51e5a27e33bba44df3cdc262d3ddec8`, 274
members, built from 6d50d0b as U-V20 built the 0.0.5 candidate (`record_passed_tests.py --profile=release`, then `pip
wheel --no-build-isolation --no-deps .`), with one difference: the REQ report came from the release tests that carry a
registry test ID (518 passed, 2 xfailed, 0 failed), not from the whole release-marker run, which takes about 1 h 51 min
here. The evidence file lists the same 58 passed registry test IDs and the same `realised_by` as the 0.0.5 release.
It is not Fable's release wheel; PK-06 and OR-11/OR-12 are redone on it (details in
`tests/independent/m5/records/PK-06_walkthrough_6d50d0b.md`, Inputs).

## The index for 0.0.6

`manual_records.json` holds seven entries. Six name a record made on 6d50d0b, and each of their `embodic_version`
values begins with the token `0.0.6`. PF-01 is unchanged. TR-01 on this index, with the 0.0.5 release REQ reports and
the version under test 0.0.6 read from this tree: `manual: 6; invalid manual records: 0; ... untested due: 0; manual
records not passed: 0 failing, 1 accepted`, exit 0. The 0.0.6 gate's own reports are not run here.
