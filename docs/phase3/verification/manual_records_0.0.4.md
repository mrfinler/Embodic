Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5 (unit U-V18)

# Manual records for release 0.0.4 (D-061d), 2026-10-20

D-061d rules that a manual record counts for a later release when the files its subject depends on are unchanged since
the build it names; otherwise the check is redone before that release gate. This note judges the seven entries that
`docs/phase3/verification/manual_records.json` held on main 705c1cb against release 0.0.4 (tag v0.0.4, commit
c25d8a9), and lists the index that now replaces them.

Lever: `python -I tests/independent/m7/v14_record_currency.py --index <index> --target c25d8a9 --verbose`, run with the
dev venv (the AX-06 subject imports `embodic.ui.app`, which needs PySide6), on the 705c1cb index
(`git show 705c1cb:docs/phase3/verification/manual_records.json`). It runs `git diff --stat <build> c25d8a9` over each
subject's fixed paths and the embodic modules its instrument imports. U-V18 adds the AX-06 subject: the paths
`pyproject.toml`, `resources/examples`, `resources/themes` and `src/embodic/ui`, and the modules that `embodic.ui.app`
imports (181). Its full output, every file compared and every changed line count, is
`manual_records_0.0.4_currency.txt` beside this note (`verified` by running it).

## The seven entries of 705c1cb

| # | Row, test | Record (result) | Build named | `git diff --stat` to c25d8a9 | Verdict | Redone by, new record |
|---|---|---|---|---|---|---|
| 0 | REQ-N-07 PK-06 | `tests/independent/m5/records/PK-06_walkthrough_c0f4894.md` (passed) | wheel cb4e51c2 of c0f4894 | 33 files changed, 635 insertions(+), 147 deletions(-) | does not stand | Agent 4, `tests/independent/m5/records/PK-06_walkthrough_c25d8a9.md` (passed, 26.5 s to 32.5 s) |
| 1 | REQ-N-14 AX-05 | `tests/independent/m4/records/AX-05_c0f4894.md` (passed) | main c0f4894 | 16 files changed, 138 insertions(+), 68 deletions(-) | does not stand | Agent 4, `tests/independent/m4/records/AX-05_c25d8a9.md` (passed, 48 of 48) |
| 2 | REQ-F-11 OR-11 | `tests/independent/m6/records/OR-11_OR-12_c0f4894.md` (passed) | wheel cb4e51c2 of c0f4894 | 10 files changed, 115 insertions(+), 42 deletions(-) | does not stand | Agent 4, `tests/independent/m6/records/OR-11_OR-12_c25d8a9.md` (passed, values equal) |
| 3 | REQ-F-11 OR-12 | same record (passed) | same | same | does not stand | Agent 4, same new record |
| 4 | REQ-L-01 LG-01 | `tests/independent/m4/records/LG-01_word_review.md` (passed) | main 260191f | 2 files changed, 14 insertions(+), 5 deletions(-) | does not stand | Agent 4, `tests/independent/m4/records/LG-01_word_review_c25d8a9.md` (passed, 805 words, one new: `top`) |
| 5 | REQ-T-11 LG-04 | `tests/independent/m4/records/LG-04_T-11_reviewer.md` (passed) | main c0f4894, allow-list a19b5c80 | 20 files changed, 158 insertions(+), 79 deletions(-) | does not stand | Agent 4, `tests/independent/m4/records/LG-04_T-11_reviewer_c25d8a9.md` (passed) |
| 6 | REQ-N-16 AX-06 | `docs/phase3/fable/AX-06_narrator_0.0.3.md` (passed, the user) | 0.0.3 source, main 2fb2ec6 | 11 files changed, 379 insertions(+), 65 deletions(-) | does not stand | the user, on the laptop; not redone |

The files behind each count, for the rulings the brief asks to name:

- Entry 0: README.md and INSTALL.md (the wheel name 0.0.4), pyproject.toml, the evidence registry and manifest, the five
  examples, and 23 files under `src/embodic` (api, drc/items, io/canonical, io/report, io/svg_writer, model/validate,
  physics/circuit, the geometry view, the layer cue and others).
- Entry 1: the five examples and 11 imported modules, among them `io/svg_writer.py` (27 lines) and `geometry/labels.py`
  (19 lines).
- Entries 2 and 3: `resources/evidence/equations.v1.json` (27 lines) and 9 imported modules, among them
  `physics/circuit.py`, `api.py` and `io/canonical.py`.
- Entry 4: `src/embodic/io/report.py` (17 lines, code only) and `src/embodic/ui/strings/shell.py` (two legend strings).
- Entry 5: `tests/static/lg_allowlist.toml` (8 lines removed: the EQ-08 "balance" rule, D-064a), the evidence registry
  and manifest, the five examples and 12 imported modules.
- Entry 6: the five examples (version strings only), `src/embodic/__init__.py` (version), `src/embodic/drc/items.py`
  (U-M8w), and the four UI files of U-M8x: `ui/views/geometry_view.py` (189 lines), the new `ui/views/layer_cue.py`
  (174 lines), `ui/views/checks_view.py` (3 lines) and `ui/strings/shell.py` (the legend rows "{layer} on top" and
  "Layers below").

No entry stands. Every Agent 4 redo gave the result of its old record: the Linux walkthrough passes (the spread is the
proxy's download rate), the AX-05 readings, truths and margins are equal, the FEA comparator values are bit-identical
(43 FEA `centre_t` values moved within 2 ulp in the rebuilt FEA venv), the word list gained one English word, and the
T-11 listing lost only the EQ-08 "balance" line that the rewording removed.

## AX-06: what the user must redo

The AX-06 record does not stand for 0.0.4. Its walkthrough (the Narrator on five inputs and three result cards of D08)
does not touch the geometry view by its steps, and in the U-M8x diff the canvas's accessible name and description lines
are unchanged (`setAccessibleName` l.189 and `setAccessibleDescription` l.570 of `geometry_view.py`, read). The legend
rows are painted on the canvas, not widgets, so Narrator cannot read them (`inferred` from `_draw_legend`). That reading
does not replace the rule: the walkthrough runs the whole app, and the app's files changed.

The user repeats the five steps of `docs/phase3/fable/AX-06_narrator_0.0.3.md` on the 0.0.4 build (the laptop checkout
at v0.0.4, or the 0.0.4 wheel in a clean venv) with the same pass criterion (REQ-N-16: inputs announce label, value,
unit; results announce value, unit, status), and Fable records it as a new AX-06 record naming that build. The user can
do it in the same session as the look at the layer cue that D-081 asks for.

## Windows records (Fable's, listed, not ruled here)

- PK-06 Windows (REQ-N-07): D-071e records the laptop walkthrough of the 0.0.2 build (cold 471 s to the first example,
  warm 20 s, selftest 45 of 45). The index holds no Windows PK-06 entry, and D-081 lists a warm run on the 0.0.4 wheel
  as still to do.
- PK-04 Windows (REQ-N-04): no Windows comparison of the 0.0.2 or the 0.0.4 build is recorded (D-073 to D-081). The
  0.0.4 Linux reference is new (`reference/README.md`, U-V18); the 0.0.2 reference no longer compares (exit 2 on the
  source hash).

## The index for 0.0.4

`manual_records.json` now holds six entries, each one a record made on the 0.0.4 build: PK-06 Linux, AX-05, OR-11 and
OR-12 (one record), LG-01 and LG-04. AX-06 left the index; its file stays, and so do all the superseded records.
`embodic_version` reads "0.0.4 (release c25d8a9)". `req_audit.py` follows `REDONE` from each record a ruling cites to
the redo that the index holds.
