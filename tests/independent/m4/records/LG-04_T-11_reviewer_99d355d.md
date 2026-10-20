Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5

# REQ-T-11 reviewer record redone for release 0.0.5 (LG-04 reviewer clause)

Date 2026-10-21, unit U-V20, worktree `unit/U-V20` on main 2cedac6, whose `src/`, `resources/` and `tests/static/`
equal the 0.0.5 candidate 99d355d (`git diff --stat 99d355d -- src resources tests/static`, empty). embodic 0.0.5, run
from the source tree (`PYTHONPATH=src`). Reviewer: Agent 4 (Independent Verificator), model claude-opus-5-5.

## Why it is redone

D-061d: the record `LG-04_T-11_reviewer_c25d8a9.md` names release 0.0.4 (c25d8a9). Its subject is
`tests/static/lg_allowlist.toml`, `resources/examples`, `resources/evidence` and the 135 modules that `embodic.api`,
`embodic.io.report`, `embodic.results.registry` and `embodic.ui.viewmodels.results` import. `git diff --stat c25d8a9
99d355d -- <those files>` gives `8 files changed, 37 insertions(+), 13 deletions(-)`: the `app_version` and
`engine_version` lines of the five examples, `src/embodic/__init__.py` (the version) and the docstrings of
`FieldTable.at` and `InterconnectResistance.total_ohm` (`tests/independent/m7/v14_record_currency.py --target 99d355d
--verbose`, entry 5; `docs/phase3/verification/manual_records_0.0.5_currency.txt`). The record does not stand for 0.0.5.

## Method

The method of the c25d8a9 record, unchanged: `QT_QPA_PLATFORM=offscreen PYTHONPATH=src python
tests/independent/m7/v14_t11_review.py`. Its output on 0.0.5 is `LG-04_T-11_listing_99d355d.txt` beside this record
(221 lines, 10.4 s).

`diff` of `LG-04_T-11_listing_c25d8a9.txt` and `LG-04_T-11_listing_99d355d.txt` is empty (`verified` by running it).
The allow-list SHA-256 on line 1, every card with its value, status, assumption count, EQ chain and Inputs, the
Torque-speed tab, the equation guide and the PDF rows of all five examples print the same text as on 0.0.4. The new
docstrings of 0.0.5 sit in source code and appear on none of these surfaces. The version string appears on none of the
printed lines, because none of them matches the word pattern.

## Verdict

`passed` for 0.0.5: no text that the results table, the Torque-speed tab, the equation guide or the PDF report shows
claims balance, torque or efficiency from geometry or phase angles alone. The reading of the c25d8a9 record holds line
for line, because the listing is identical. The judgement that each text is not a claim is the reviewer's (`inferred`).
A reading on a desktop session is `not tested`.

## Rerun

```
QT_QPA_PLATFORM=offscreen PYTHONPATH=src python tests/independent/m7/v14_t11_review.py > listing.txt
diff tests/independent/m4/records/LG-04_T-11_listing_c25d8a9.txt listing.txt
```
