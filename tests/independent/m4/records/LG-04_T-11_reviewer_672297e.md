Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5

# REQ-T-11 reviewer record redone for 0.0.6 on candidate 672297e (LG-04 reviewer clause)

Date 2026-10-21 UTC, unit U-V28, worktree `unit/U-V28`, whose `src/`, `resources/` and `tests/static/` equal the 0.0.6
candidate main 672297e (the unit changes only `tests/independent` and `docs/phase3/verification`). embodic 0.0.6, run
twice: from the source tree (`PYTHONPATH=src`), and from the files that Agent 4's candidate wheel ad9e02c0 of 672297e
installed in the PK-06 run 1 venv (`PYTHONPATH=<that venv's site-packages>`, with pypdf from the project venv, because
the lister reads the PDF and pypdf is a dev dependency). Reviewer: Agent 4 (Independent Verificator), model
claude-opus-5-5.

## Why it is redone

D-061d: the record `LG-04_T-11_reviewer_6d50d0b.md` names the 6d50d0b sources. Its subject is
`tests/static/lg_allowlist.toml`, `resources/examples`, `resources/evidence` and the 135 modules that `embodic.api`,
`embodic.io.report`, `embodic.results.registry` and `embodic.ui.viewmodels.results` import. `git diff --stat 6d50d0b
672297e -- <those files>` gives `1 file changed, 2 insertions(+), 2 deletions(-)`: two rows of the guide's key table in
`ui/strings/results.py` (U-M9e, D-094b; `tests/independent/m7/v14_record_currency.py --target 672297e --verbose`,
entry 5). The record does not stand for 672297e.

## Method

The method of the earlier records, unchanged: `QT_QPA_PLATFORM=offscreen PYTHONPATH=src python
tests/independent/m7/v14_t11_review.py`. Its output on the wheel is `LG-04_T-11_listing_672297e.txt` beside this record
(221 lines, 11.8 s; SHA-256 `024f3a43…7f47`).

- The source-tree run and the wheel run print the same bytes (`cmp`, equal; `verified`).
- The listing is byte-identical to `LG-04_T-11_listing_6d50d0b.txt` (`cmp`, equal; `verified`), the allow-list hash
  line included: `tests/static/lg_allowlist.toml` did not change. Every card with its value, status, assumption count,
  EQ chain and Inputs, the Torque-speed tab, the equation guide and the PDF rows of all five examples print the same
  text as on 6d50d0b.
- The lister does not print the guide's key table, so I read the two changed rows in
  `src/embodic/ui/strings/results.py` on 672297e: "Inspector tabs Coil, Phases, Layers, Board" and "F1, Ctrl+/" with
  "Guide, Shortcuts". They name tabs and keys and claim no result.

## Verdict

`passed` for 0.0.6 on candidate 672297e: no text that the results table, the Torque-speed tab, the equation guide or
the PDF report shows claims balance, torque or efficiency from geometry or phase angles alone. The reading of the
6d50d0b record holds line for line, and the changed rows are not such a claim. The judgement that each text is not a
claim is the reviewer's (`inferred`). A reading on a desktop session is `not tested`.

## Rerun

```
QT_QPA_PLATFORM=offscreen PYTHONPATH=src python tests/independent/m7/v14_t11_review.py > listing.txt
cmp tests/independent/m4/records/LG-04_T-11_listing_672297e.txt listing.txt
```
