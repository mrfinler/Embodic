Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5

# REQ-T-11 reviewer record redone for 0.0.6 (LG-04 reviewer clause)

Date 2026-10-21 UTC, unit U-V27, worktree `unit/U-V27`, whose `src/`, `resources/` and `tests/static/` equal the 0.0.6
candidate main 6d50d0b (the unit changes only `tests/independent` and `docs/phase3/verification`). embodic 0.0.6, run
from the source tree (`PYTHONPATH=src`). Reviewer: Agent 4 (Independent Verificator), model claude-opus-5-5.

## Why it is redone

D-061d: the record `LG-04_T-11_reviewer_99d355d.md` names the 0.0.5 sources (99d355d). Its subject is
`tests/static/lg_allowlist.toml`, `resources/examples`, `resources/evidence` and the 135 modules that `embodic.api`,
`embodic.io.report`, `embodic.results.registry` and `embodic.ui.viewmodels.results` import. `git diff --stat 99d355d
6d50d0b -- <those files>` gives `9 files changed, 15 insertions(+), 14 deletions(-)`: the version lines of the five
examples, `src/embodic/__init__.py`, the allow-list pattern of the changed message, `ui/strings/results.py` (the message
`chart.no-dc-link`) and `ui/viewmodels/results.py` (the constant `KEYS_TOPIC`)
(`tests/independent/m7/v14_record_currency.py --target 6d50d0b --verbose`, entry 5). The record does not stand for
0.0.6.

## Method

The method of the earlier records, unchanged: `QT_QPA_PLATFORM=offscreen PYTHONPATH=src python
tests/independent/m7/v14_t11_review.py`. Its output on 6d50d0b is `LG-04_T-11_listing_6d50d0b.txt` beside this record
(221 lines, 10.6 s).

`diff` of `LG-04_T-11_listing_99d355d.txt` and `LG-04_T-11_listing_6d50d0b.txt` gives one line: the allow-list SHA-256
on line 1 (`856a9bf3…9785` against `7424606e…0873`), because the allow-list now matches the new message (`verified` by
running it). Every card with its value, status, assumption count, EQ chain and Inputs, the Torque-speed tab, the
equation guide and the PDF rows of all five examples print the same text as on 0.0.5.

The lister prints the Torque-speed tab of three examples as "no chart (the message chart.no-dc-link)" and does not print
the message itself, so I read it in `src/embodic/ui/strings/results.py` l.105 on 6d50d0b: "The torque-speed estimate
needs a DC-link voltage (Board tab, Drive group)." It names a computed result and the input it waits for, and claims no
torque value. Against 0.0.5 only its last words changed, from "(Board and rotor, operating point)".

## Verdict

`passed` for 0.0.6: no text that the results table, the Torque-speed tab, the equation guide or the PDF report shows
claims balance, torque or efficiency from geometry or phase angles alone. The reading of the 99d355d record holds line
for line, and the changed message is not such a claim. The judgement that each text is not a claim is the reviewer's
(`inferred`). A reading on a desktop session is `not tested`. U-M9e (in flight, D-094b) edits the guide text in
`ui/strings/results.py`; once it merges, this record is superseded by the same rule and is redone.

## Rerun

```
QT_QPA_PLATFORM=offscreen PYTHONPATH=src python tests/independent/m7/v14_t11_review.py > listing.txt
diff tests/independent/m4/records/LG-04_T-11_listing_6d50d0b.txt listing.txt
```
