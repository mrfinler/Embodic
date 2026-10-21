Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5 (unit U-V28)

# Manual records for 0.0.6 on candidate 672297e (D-061d, D-083c, D-093c), 2026-10-21 UTC

The 0.0.6 candidate is now main 672297e, which merges U-M9e (D-094b) on top of 6d50d0b. U-V27 stamped the seven
entries of `manual_records.json` for 6d50d0b (`manual_records_0.0.6.md`). This note rules whether each stands for
672297e and lists the index that replaces them. Every line is `verified` by running or reading it, unless it carries
another label.

## What changed between 6d50d0b and 672297e

`git diff --stat 6d50d0b 672297e` (read): of the product, only `src/embodic/ui/strings/results.py`, two rows of the
guide's key table (`KEYBOARD_MAP`): "F1, Ctrl+/, Ctrl+," with "Guide, Shortcuts, Settings" became "F1, Ctrl+/" with
"Guide, Shortcuts", and "Inspector tabs Coil, Phases, Layers, Board and rotor" lost "and rotor". The rest is U-M9e's
test `tests/ui/qt_shell/test_guide_keys_are_bound.py`, one quote in `docs/phase2/architecture/test_plan.md`, U-S18's
`docs/phase2/design/design_spec.md` and U-V27's own files. `resources/`, `pyproject.toml`, the lock files,
`README.md`, `docs/install/INSTALL.md`, `tests/static/` and `oracle_cases.json` are unchanged.

## The rule and the lever

As in `manual_records_0.0.6.md`: D-061d compares the files a subject depends on with the build the record names, and
for a wheel record the wheel's members are the files (U-V21). Lever: `python -I
tests/independent/m7/v14_record_currency.py --target 672297e --verbose`, and `tests/independent/m7/v21_wheel_diff.py`
for the wheel. U-V28 adds the subjects of the four new records to the lever, and
`docs/phase3/verification/checks/req_audit.py` follows `REDONE` from each superseded 6d50d0b record to its 672297e
redo (`--self-test` passed). Full outputs: `manual_records_0.0.6_672297e_currency.txt` beside this note.

## The seven entries

| # | Row, test | Record of U-V27 (result) | Build named | Git subject 6d50d0b to 672297e | Wheel | Verdict | Entry now |
|---|---|---|---|---|---|---|---|
| 0 | REQ-N-07 PK-06 | `PK-06_walkthrough_6d50d0b.md` (passed) | wheel 5d891a26 | 1 file: `ui/strings/results.py` | 3 members differ, among them that file and the evidence file | does not stand | redone, `tests/independent/m5/records/PK-06_walkthrough_672297e.md` (passed, 31.5 to 116.0 s, self-test 45 of 45) |
| 1 | REQ-N-14 AX-05 | `AX-05_6d50d0b.md` (passed) | source tree = 6d50d0b | no change | none used | stands | restamped, record file unchanged |
| 2 | REQ-F-11 OR-11 | `OR-11_OR-12_6d50d0b.md` (passed) | wheel 5d891a26 | no change | evidence file differs and is read (`compute_project`) | does not stand | redone, `tests/independent/m6/records/OR-11_OR-12_672297e.md` (passed, comparator values bit-identical) |
| 3 | REQ-F-11 OR-12 | same | same | same | same | does not stand | same new record |
| 4 | REQ-L-01 LG-01 | `LG-01_word_review_6d50d0b.md` (passed) | source tree = 6d50d0b | 1 file: `ui/strings/results.py` | none used | does not stand | redone, `tests/independent/m4/records/LG-01_word_review_672297e.md` (passed, 805 words, one removed: `settings`) |
| 5 | REQ-T-11 LG-04 | `LG-04_T-11_reviewer_6d50d0b.md` (passed) | source tree = 6d50d0b | 1 file: `ui/strings/results.py` | none used | does not stand | redone, `tests/independent/m4/records/LG-04_T-11_reviewer_672297e.md` (passed, listing byte-identical) |
| 6 | REQ-N-01 PF-01 | `docs/phase3/fable/PF-01_windows_0.0.5.md` (failed, accepted D-091) | laptop checkout bbeed84 | 6 files: 5 examples (version lines), `__init__.py` | none used | does not stand | unchanged: `failed`, `accepted` D-091, `embodic_version` still 0.0.5 |

Entries 0, 4 and 5 are the three that `manual_records_0.0.6.md` said U-M9e would make stale. Entries 2 and 3 are
redone too. Their git subject is unchanged, but they were made on the wheel 5d891a26, and a new candidate wheel
carries a new evidence file that `compute_project` reads. U-V21 and U-V27 ruled such a wheel record superseded, and I
keep that ruling here, so the brief's "restamp the rest" applies to AX-05 only. A redo is not a claim that the evidence
fields could change OR-11 or OR-12; it is what the rule asks when a file the check reads changed. Every redo gave the
result of its old record. LG-01 and LG-04 ran on the source tree of 672297e as their earlier records did; LG-04 also
ran on the files the candidate wheel installed (same bytes out), and the 21 LG-01 corpus files equal their wheel
members.

Restamp. Entry 1 keeps its record file, as interfaces.md section 3.2 asks, and its `embodic_version` now reads `0.0.6
(AX-05 record of 6d50d0b stands for candidate 672297e under D-061d: subject unchanged, U-V28; <this note>)`.

PF-01. Unchanged from U-V27, as D-091 and the brief say: its redo needs the reference laptop, which this unit cannot
reach. The entry keeps its real result, its acceptance and the version it names. A restamp would claim that it stands.

## The candidate wheel

`embodic-0.0.6-py3-none-any.whl`, SHA-256 `ad9e02c073c45668938621ebeea8f8ca9b42cae9036c869a0871de3da2802aaa`, 274
members, built from 672297e as U-V27 built the 6d50d0b candidate: `record_passed_tests.py --profile=release` on the
REQ report of the release tests that carry a registry test ID (518 passed, 2 xfailed, 0 failed, 141 s), in a clone at
672297e (`git_dirty` false), then `pip wheel --no-build-isolation --no-deps .`. Against wheel 5d891a26, 3 members
differ: `embodic/ui/strings/results.py`, the evidence file (`build_id`, `generated_utc`, `git_commit`,
`source_sha256`; the passed test IDs and `realised_by` equal) and `RECORD`. It is not Fable's release wheel.

## The index for 672297e

`manual_records.json` holds seven entries. Five name a record made on 672297e, AX-05 names its 6d50d0b record with the
restamp, and PF-01 is unchanged. The six passed entries' `embodic_version` values begin with the token `0.0.6`. TR-01
on this index, with the 0.0.5 release REQ reports and the version under test 0.0.6 read from this tree: `manual: 6;
invalid manual records: 0; ... untested due: 0; manual records not passed: 0 failing, 1 accepted`, exit 0. The 0.0.6
gate's own reports are not run here. `req_audit.md` (target 0.0.5) reads as stale with `--check` on this index, as it
already did on 672297e before this unit: a committed audit of an earlier target is the snapshot of the index its
writer had (the script's docstring).

## Also checked: the toolstrip has no Settings button

`tests/independent/m7/v28_canvas_keys.py` (output `tests/independent/m7/records/U-V28_canvas_keys.txt`) lists every
visible toolstrip button on each of the five tabs of the offscreen main window: 22 buttons (Home 6, Design 5,
Analysis 3, Export 4, View 4), none named or labelled Settings, and no action of the window names settings
(`verified` by running). The same run gives DEF-US18-01 (`tests/independent/m7/records/defects.md`).
