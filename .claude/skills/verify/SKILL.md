---
name: verify
description: Drive the embodic desktop app (PySide6) offscreen and prove UI behaviour. Runs a doctor check, the three topology walkthroughs, AX-02 keyboard-only, AX-04 target size, UI-09 scaling and the 41 rows of docs/phase2/design/screenshot_checklist.md, then writes PNGs and report.json to build/verify/<UTC timestamp>/. Use after a UI change, before calling a UI unit done, or to retake the acceptance screenshots.
---

# Verify embodic

The surface is the desktop window of `embodic` (PySide6). There is no server and no port. Every drive starts its own
offscreen Qt process, so runs never share an instance and two runs can go side by side.

## Launch

From the repository root, with the project's virtual environment:

```
.venv/bin/python .claude/skills/verify/verify.py --acceptance
```

That is the whole run, about 5 minutes. It starts each child with `QT_QPA_PLATFORM=offscreen` and `PYTHONPATH` set to
this checkout's `src` and root, so you set nothing yourself. The last line printed is the path of `report.json`.
Exit code 0 means the doctor passed, every e2e test passed or was a strict xfail, and every captured row has files.

- `--rows S04 S07` captures only those checklist rows (the e2e tests still run).
- Without `--acceptance` the shots stay in `build/verify/<timestamp>/shots/` only.

The app itself, for a manual look: `.venv/bin/python -m embodic.ui.app` (a window), or
`.venv/bin/python -m embodic.ui.app --smoke` (open D08, compute, quit with 0).

## Doctor

```
.venv/bin/python .claude/skills/verify/verify.py --doctor
```

Read-only. It checks that `embodic` imports from this checkout's `src`, PySide6 imports, the bundled Inter and
JetBrains Mono files exist, and `pdftoppm`, `pdftotext`, `pdffonts` and `pdfinfo` are on PATH. Run it first whenever
something looks off. A failed doctor stops the run and its reasons are in `report.json`.

## Drive

Two levers do the driving. Both find widgets by objectName (the names of `docs/phase2/design/screens.md` 14a and the
`widget_id` column of `src/embodic/model/fields.py`), never by coordinates.

- `tests/ui/qt_e2e/` is pytest-qt. `test_walkthroughs.py` holds one table row per topology (spiral D08, serpentine,
  wave): open from the Examples gallery or New design, type three inputs, F5-equivalent recompute through
  `act-compute`, open `res-r-phase-how`, the DRC tab, export SVG and PDF, save through `act-save`, edit, reopen
  through `act-open`, and compare the design hash. `test_ax02_keyboard_only.py` sends keys only to the focused
  widget. `support.py` has the user actions (`run_action`, `type_value`, `press`, `tab_until`).
- `tests/ui/qt_shell/capture_acceptance.py` has one function per checklist row in `ROWS`. Each row gets a fresh window,
  sets the theme, size and example the row names, gives focus to the row's Focus widget, and grabs. Run one row by
  hand with `QT_QPA_PLATFORM=offscreen PYTHONPATH=src:. .venv/bin/python -m tests.ui.qt_shell.capture_acceptance
  build/tmp S20`.

The feature map in `features/README.md` lists what each lever covers and how to drive it.

## Evidence

`build/verify/<timestamp>/` holds `shots/*.png` named `<ID>_<theme>_<width>x<height>[_<part>].png`,
`shots/S40_report_d08.pdf` and `S40_pdffonts.txt`, `scaling/UI09_*.png` at 1, 1.5 and 2, `e2e_junit.xml`,
`e2e_pytest.txt`, `shot_measure_input/` and `report.json`. `report.json` has the doctor results, every e2e test's
outcome, every row's files, notes and status (`passed`, `not tested`, `failed`), the `shot_measure.py` output, and
the `not_tested` list with a reason per item.

Proof standards for this app:

- Exercise the user path: toolstrip buttons, dialogs and fields by objectName. Do not call view-model setters to make
  a test pass. The capture lever sets state through the session where a row only needs a starting state.
- Check side effects, not only pixels: the walkthrough reads the exported SVG as XML, the PDF header, and the saved
  file's design hash.
- A shot shows what it shows. U+00A0, a tooltip's look (offscreen Qt draws none) and text clipping at 150 % and
  200 % are `not tested` by a machine; `report.json` says so.
- Numbers in a shot (pane widths, contrast) come from `docs/phase2/design/checks/shot_measure.py`, which the driver
  runs on S22 and S39.

## Cleanup

Each child process exits when its drive ends, and the lever deletes its scratch folder (it doubles as HOME, so
dialogs show `%USERPROFILE%` or relative names, never a user's folder). Nothing else to stop. Evidence stays in
`build/verify/` and `build/screens/acceptance/` until you delete it. If a run hangs, stop only the process you started,
by its PID; never kill by name.

## Helpers

- `verify.py`: the driver above. `--doctor`, `--rows`, `--acceptance`.
- `tests/ui/qt_shell/capture_acceptance.py OUT [ROW ...] [--scaling]`: the shots; prints one JSON line per row.
- `docs/phase2/design/checks/shot_measure.py FOLDER`: pane widths, canvas share, gallery contrast.

Keep the feature map honest as the app changes with `/maintain-verification-skill`.
