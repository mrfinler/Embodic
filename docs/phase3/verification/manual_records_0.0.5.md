Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5 (unit U-V20)

# Manual records for release 0.0.5 (D-061d, D-083c), 2026-10-21

D-061d rules that a manual record counts for a later release when the files its subject depends on are unchanged since
the build it names; otherwise the check is redone before that release gate. Since D-083c and D-084a, TR-01 counts a
record only when its `embodic_version` is the version under test as a whole token. On main every entry still reads
"0.0.4 (release c25d8a9)", so TR-01 lists all six as stale for 0.0.5. This note judges the six entries of the index on
main 2cedac6 against the 0.0.5 candidate 99d355d, and lists the index that replaces them.

Lever: `python -I tests/independent/m7/v14_record_currency.py --index <index of 2cedac6> --target 99d355d --verbose`,
run with the dev venv. U-V20 adds the six subjects of the c25d8a9 records, with the same paths and imported modules as
their c0f4894 forerunners. The full output, every file compared and every changed line count, is
`manual_records_0.0.5_currency.txt` beside this note (`verified` by running it).

What changed between 0.0.4 and 0.0.5 in the files any subject reads (`git diff --stat c25d8a9 99d355d -- README.md
docs/install requirements pyproject.toml resources src tests/static/lg_allowlist.toml
docs/phase2/engineering/oracle_cases.json`, read): the version strings (`src/embodic/__init__.py`, the wheel name and
`embodic 0.0.5` in README.md and INSTALL.md, `app_version` and `engine_version` of the five examples), the docstrings
of `FieldTable.at` (`physics/emf.py`) and `InterconnectResistance.total_ohm` (`physics/interconnect.py`), and the test ID
`DRC_SOURCE` in `selftest/catalogue.py`. The lock file, pyproject.toml, the themes, the evidence registry, the oracle
cases, the allow-list and `src/embodic/ui` are unchanged.

## The six entries of 2cedac6

| # | Row, test | Record (result) | Build named | `git diff --stat` to 99d355d | Verdict | New entry |
|---|---|---|---|---|---|---|
| 0 | REQ-N-07 PK-06 | `tests/independent/m5/records/PK-06_walkthrough_c25d8a9.md` (passed) | release wheel 9bca49d8 of c25d8a9 | 11 files changed, 43 insertions(+), 19 deletions(-) | does not stand | Agent 4, `tests/independent/m5/records/PK-06_walkthrough_99d355d.md` (passed, 32.5 s to 75.7 s) |
| 1 | REQ-N-14 AX-05 | `tests/independent/m4/records/AX-05_c25d8a9.md` (passed) | main 705c1cb = c25d8a9 | 8 files changed, 37 insertions(+), 13 deletions(-) | does not stand | Agent 4, `tests/independent/m4/records/AX-05_99d355d.md` (passed, 48 of 48) |
| 2 | REQ-F-11 OR-11 | `tests/independent/m6/records/OR-11_OR-12_c25d8a9.md` (passed) | release wheel 9bca49d8 of c25d8a9 | 3 files changed, 27 insertions(+), 3 deletions(-) | does not stand | Agent 4, `tests/independent/m6/records/OR-11_OR-12_99d355d.md` (passed, embodic values bit-identical) |
| 3 | REQ-F-11 OR-12 | same record (passed) | same | same | does not stand | Agent 4, same new record |
| 4 | REQ-L-01 LG-01 | `tests/independent/m4/records/LG-01_word_review_c25d8a9.md` (passed) | main 705c1cb = c25d8a9 | no change | stands | restamped, record file unchanged |
| 5 | REQ-T-11 LG-04 | `tests/independent/m4/records/LG-04_T-11_reviewer_c25d8a9.md` (passed) | main 705c1cb = c25d8a9 | 8 files changed, 37 insertions(+), 13 deletions(-) | does not stand | Agent 4, `tests/independent/m4/records/LG-04_T-11_reviewer_99d355d.md` (passed, listing identical) |

The files behind each count:

- Entry 0: README.md and INSTALL.md (the wheel name and the `pip list` line), the five examples, and four files under
  `src/embodic`: `__init__.py`, `physics/emf.py`, `physics/interconnect.py` and `selftest/catalogue.py`.
- Entries 1 and 5: the five examples, and `__init__.py`, `physics/emf.py` and `physics/interconnect.py` among the
  imported modules (125 for AX-05, 135 for LG-04).
- Entries 2 and 3: `__init__.py`, `physics/emf.py` and `physics/interconnect.py` among the 120 imported modules.
  `equations.v1.json` and `oracle_cases.json` are unchanged.
- Entry 4: the corpus is `src/embodic/ui/strings`, `src/embodic/errors/catalogue`, `src/embodic/io/report.py` and
  `src/embodic/io/readme_writer.py`. None of the four changed, so the c25d8a9 word review stands for 0.0.5.

The rule is applied to files, as U-V18 applied it. A version string and two docstrings would not change what any of
these checks observes (`inferred`), and every redo below gave the result of its old record. That inference does not
replace the rule.

Restamp. Entry 4 now reads `"embodic_version": "0.0.5 (LG-01 record of c25d8a9 stands, D-061d: corpus unchanged;
U-V20 manual_records_0.0.5.md)"`. The record file is unchanged, because the REQ-L-01 ruling of U-V19 pins its SHA-256.

## AX-06: which build the user runs

AX-06 (REQ-N-16, the Narrator walkthrough) is the user's, and no AX-06 record is in the index. The user has not redone
it on 0.0.4. The laptop's checkout is 94bd54d (D-085). Its `src/`, `resources/` and `pyproject.toml` equal release
0.0.4 (`git diff --stat 94bd54d c25d8a9 -- src resources pyproject.toml`, empty; `verified`).

- The geometry view is unchanged between c25d8a9 and 99d355d: `git diff --stat c25d8a9 99d355d -- src/embodic/ui` is
  empty (`verified`). So is the rest of `src/embodic/ui`.
- A run on 94bd54d does not stand for 0.0.5 all the same. The AX-06 subject (U-V18: `pyproject.toml`,
  `resources/examples`, `resources/themes`, `src/embodic/ui` and the 181 modules that `embodic.ui.app` imports) changes
  between 94bd54d and 99d355d in 9 files, 38 insertions and 14 deletions: the five examples (version lines),
  `__init__.py`, `physics/emf.py`, `physics/interconnect.py` and `selftest/catalogue.py`. All four modules are in the
  import closure of `embodic.ui.app` (`verified`, `import_closure` of the lever). A record of that run would name
  0.0.4, and TR-01 would list it as stale for 0.0.5.
- The build to run. The user runs the five steps of `docs/phase3/fable/AX-06_narrator_0.0.3.md` on the 0.0.5 release
  wheel that Fable's gate builds from 99d355d, installed in a new venv by INSTALL.md steps 2 to 6. A laptop checkout
  moved to 99d355d (or a later main commit whose `src/`, `resources/` and `pyproject.toml` equal it) with its editable
  install also stands. Fable records the run as a new AX-06 entry whose `embodic_version` starts with `0.0.5 `.

## Windows records (Fable's, not ruled here)

- PK-06 Windows (REQ-N-07): D-085a records the warm run of the 0.0.4 wheel. The index holds no Windows PK-06 entry.
- PK-04 (REQ-N-04): D-085b records the 0.0.4 comparison. U-V20 implements D-052b in `checks/pk04_compare.py`
  (`reference/README.md`, DEF-UV10-01). The comparison of the Windows folder with the new tool is Fable's.

## The index for 0.0.5

`manual_records.json` holds six entries. Five name a record made on the 0.0.5 sources, and LG-01 names the c25d8a9
record that stands. Each `embodic_version` begins with the token `0.0.5`. `req_audit.py` follows `REDONE` from each
c25d8a9 record to its 99d355d redo.
