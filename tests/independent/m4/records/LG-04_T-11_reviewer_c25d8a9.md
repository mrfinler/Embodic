Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5

# REQ-T-11 reviewer record redone for release 0.0.4 (LG-04 reviewer clause)

Date 2026-10-20, worktree `unit/U-V18` on main 705c1cb, whose `src/`, `resources/` and `tests/static/` equal release
0.0.4 (tag v0.0.4, commit c25d8a9; `git diff c25d8a9 705c1cb -- src resources tests/static` is empty). embodic 0.0.4,
run from the source tree (`PYTHONPATH=src`). Reviewer: Agent 4 (Independent Verificator), model claude-opus-5-5.

## Why it is redone

D-061d: the record `LG-04_T-11_reviewer.md` names main c0f4894 and the allow-list SHA-256 `a19b5c80…7164`. Its subject
is `tests/static/lg_allowlist.toml`, `resources/examples`, `resources/evidence` and the 135 modules that
`embodic.api`, `embodic.io.report`, `embodic.results.registry` and `embodic.ui.viewmodels.results` import.
`git diff --stat c0f4894 c25d8a9 -- <those files>` gives `20 files changed, 158 insertions(+), 79 deletions(-)`, among
them `tests/static/lg_allowlist.toml` (8 lines removed), `resources/evidence/equations.v1.json` and
`src/embodic/io/report.py` (`tests/independent/m7/v14_record_currency.py --target c25d8a9 --verbose`, entry 5). The
record does not stand for 0.0.4.

## Method

The method of the c0f4894 record, unchanged: `QT_QPA_PLATFORM=offscreen PYTHONPATH=src python
tests/independent/m7/v14_t11_review.py`, Agent 4's own word pattern (balanc, imbalanc, unbalanc, torque, efficien), over
the result cards with their disclosure, the Torque-speed tab, the equation guide and the PDF report of the five packaged
examples. Its output on 0.0.4 is `LG-04_T-11_listing_c25d8a9.txt` beside this record (221 lines).

To see what changed, I ran the same lister on an export of c0f4894 (`git archive c0f4894`, the lister copied in). It
printed 222 lines, the count the c0f4894 record gives. `diff` of the two outputs (`verified` by running) has two hunks
only:

- Line 1, the allow-list SHA-256: `a19b5c80…7164` on c0f4894,
  `856a9bf3335baeb13385a947075e529d53eefdd3b3bdb88611ed0b01a0219785` on 0.0.4. The file lost one `claim` rule, the one that admitted "balance" in the EQ-08 formula (D-064a), so eight
  `claim` rules remain.
- The guide line `EQ-08 [Formula] ... balance = signed angle sets ...` is gone. The 0.0.4 registry formula of EQ-08 ends
  "symmetric 3-phase pattern (a property of the coil pattern only) = signed angle sets of B and C equal those of A
  shifted by 4Q and 8Q units" (`resources/evidence/equations.v1.json`, read), so the pattern no longer matches. This is
  the rewording that finding F-UV14-01 asked for (D-063a).

Every other line, the cards, their values, statuses, assumption counts, EQ chains and Inputs, the Torque-speed tab and
the PDF rows of all five examples, is identical to the c0f4894 output that the earlier record read line by line. I read
the diff and the 0.0.4 listing.

## Verdict

`passed` for 0.0.4: no text that the results table, the Torque-speed tab, the equation guide or the PDF report shows
claims balance, torque or efficiency from geometry or phase angles alone. The table of the c0f4894 record holds
unchanged, except its EQ-08 row, which no longer exists. F-UV14-01 is closed by the rewording (`verified`, read). The
judgement that each text is not a claim is the reviewer's (`inferred`). A reading on a desktop session is `not tested`.
The two new strings of 0.0.4 (the layer-cue legend rows "{layer} on top" and "Layers below") hold none of the words.
