Prepared by: Agent 1 - UX/UI Expert Designer - model: claude-opus-5-5

# V3-14 copy: wording fixes for REQ-T-10, REQ-T-11 and REQ-L-03 (U-S9, 2026-10-17)

Agent 4's V3-14 scan (`tests/independent/m7/records/V3-14.md`) lists 287 findings on the release wheel and main
3cb23e5. REQ-T-10 has 260, REQ-T-11 has 16 and REQ-L-03 has 11. This document triages them by string source, gives the
replacement copy for every fix, hands the contract items to Agent 6 (U-D16), and lists the tests and documents that pin
a changed string so Agent 3 changes them in the same commit.

Every location below is on main 3440241 (this worktree). The lever `docs/phase3/design/checks/v3_14_copy_check.py`
finds each current string by search and prints its file:line. It also checks that no replacement matches a V3-14 word
class and that every old and new string appears in this file verbatim. Section 8 has the command and its output.

Status words follow standing order 2. `verified` means read in the source or reproduced by running something.

## 1. Counts

| Requirement | Findings | String sources | `fix` | `needs contract change` | `false positive` |
|---|---|---|---|---|---|
| REQ-T-10 | 260 | 9 | 7 sources, 27 findings | 2 sources, 233 findings | 0 |
| REQ-T-11 | 16 | 8 | 8 sources, 16 findings | 0 | 0 |
| REQ-L-03 | 11 | 5 | 5 sources, 11 findings | 0 | 0 |
| All | 287 | 22 | 20 sources, 54 findings | 2 sources, 233 findings | 0 |

The grouping is `verified`. A one-off grouping of the record's 287 rows by (class, location, text) gave these counts.
One string source counts once, whatever number of exports or corpora repeat it. The wheel and main src each count a
literal once, so most literals have 2 findings.

No finding is a false positive. Two placeholder names (`{measured}` in T10-1 and T10-3) are not text a person reads.
They are renamed anyway. If they stay, the scan still reports both lines and an allow-list rule would be needed.

The lever found two more user-facing hits that the record does not list. Section 6 hands them to Agent 6, and section 7
records the scan gap as a defect.

## 2. Triage by string source

| Source (main 3440241) | Class | Findings | Verdict | Reason |
|---|---|---|---|---|
| `src/embodic/ui/strings/export.py:45` `export.confirm.row` | REQ-T-10 | 4 | fix | Export confirmation list. It calls the computed DRC clearance measured. |
| `src/embodic/ui/strings/results.py:85` `drc.column.measured` | REQ-T-10 | 2 | fix | DRC table column header. |
| `src/embodic/ui/strings/results.py:87` `drc.row.description` | REQ-T-10 | 4 | fix | DRC row tooltip, accessible description and Ctrl+C copy (`checks_view.py:211` docstring). |
| `src/embodic/io/report.py:137` | REQ-T-10 | 12 (2 literal, 10 PDF) | fix | PDF report DRC table header, in 5 reports and 5 bundle copies. |
| `src/embodic/selftest/catalogue.py:183` | REQ-T-10 | 2 | fix | Self-test failure text. The runner shows it as `ValueError: ...` (`selftest/runner.py:44`). |
| EQ-30 `name` in the registry | REQ-T-10 | 1 | fix | The equation guide shows the name as a row and in the topic title (`ui/viewmodels/results.py:736` and `:750`). Owner Agent 2. |
| `resources/fonts/FONTS.md:24` and `:25` | REQ-T-10 | 2 | fix | Ships in the wheel as `embodic/_resources/fonts/FONTS.md`. A SHA-256 is computed, not measured. The app does not open the file (`inferred`: no `FONTS.md` in `src/`). |
| JSON key `measured_mm` | REQ-T-10 | 186 | needs contract change | `compute --json` output, DRC violations of the wave example. interfaces.md names the key. |
| JSON key `measured_min_mm` | REQ-T-10 | 47 | needs contract change | `compute --json` output, DRC summaries of all 5 examples. interfaces.md names the key. |
| `src/embodic/ui/strings/design.py:218` `hint-combination.balanced` | REQ-T-11 | 2 | fix | Balance claim from the coil and pole counts. |
| `src/embodic/ui/strings/design.py:219` `hint-combination.unbalanced` | REQ-T-11 | 2 | fix | Same check, fail case. |
| `src/embodic/ui/strings/design.py:225` `phase-balance-status.balanced` | REQ-T-11 | 2 | fix | DEF-UV8-04. |
| `src/embodic/ui/strings/design.py:226` `phase-balance-status.manual` | REQ-T-11 | 2 | fix | Balance claim. The stated reason is also incomplete (section 3.2). |
| `src/embodic/ui/strings/design.py:227` `phase-balance-status.choose` | REQ-T-11 | 2 | fix | Same check, fail case with the counts to choose. |
| `src/embodic/ui/strings/design.py:228` `phase-balance-status.unbalanced` | REQ-T-11 | 2 | fix | Same check, fail case with no count to offer. |
| `src/embodic/errors/catalogue/winding.py:7` `UNBUILDABLE_UNBALANCED_WINDING` message | REQ-T-11 | 2 | fix | Issue list text. |
| `src/embodic/errors/catalogue/winding.py:17` `RANGE_MANUAL_ASSIGNMENT_UNBALANCED` message | REQ-T-11 | 2 | fix | Issue list text. It also calls the unit-phasor sums "EMF phasor magnitudes". |
| `src/embodic/model/validate.py:120` and `:125` | REQ-L-03 | 4 | fix | DEF-UV8-01. The suggestion reason ends the "Changed from X to Y" notice. |
| `src/embodic/model/validate.py:134` and `:189` | REQ-L-03 | 4 | fix | DEF-UV8-01, the rounding reason. |
| EQ-14 `formula` in the registry | REQ-L-03 | 1 | fix | DEF-UV8-05. Main 3440241 already changed this formula since the wheel. It still names Xcoil. Owner Agent 2 (U-E14). |
| EQ-20 `formula` in the registry | REQ-L-03 | 1 | fix | DEF-UV8-05. Owner Agent 2 (U-E14). |
| EQ-27 `formula` in the registry | REQ-L-03 | 1 | fix | DEF-UV8-05. Owner Agent 2 (U-E14). |

The 233 JSON-key findings are only in `compute --json` output. The bundled project files carry none. A count over the
five exports Agent 4 wrote today gave outcome.json 10, 9, 9, 9 and 196 keys and 0 in every `bundle.embodic.json`
(`verified`). The keys are still user-facing output, so they are not false positives.

## 3. Fixes

Each row gives the exact current text as it stands in the file, the exact replacement and where it sits. A row marked
"call site" is code that must change with the string, because `text()` fills placeholders with `str.format` and a
renamed placeholder raises `KeyError` otherwise (`src/embodic/ui/strings/__init__.py:22-25`, `verified` by reading).

### 3.1 REQ-T-10: the computed DRC clearance

The DRC clearance is computed from the generated copper (EQ-30 formula, `verified` by reading the registry). The UI
term becomes "clearance". The table pairs it
with "Required", so a row reads as the clearance found against the clearance required. If Agent 6 picks another term
for the JSON keys, the UI copy can stay as below.

| ID | Location | Current | Replacement |
|---|---|---|---|
| T10-1 | `src/embodic/ui/strings/export.py:45` | `{message} {layer}: {measured} measured, {required} required.` | `{message} {layer}: {clearance} clearance, {required} required.` |
| T10-1a | `src/embodic/ui/views/dialogs.py:31` (call site) | `measured=drc_length_text(v.measured_mm),` | `clearance=drc_length_text(v.measured_mm),` |
| T10-2 | `src/embodic/ui/strings/results.py:85` | `"Measured\n(mm)"` | `"Clearance\n(mm)"` |
| T10-3 | `src/embodic/ui/strings/results.py:87` | `Error. {code}. {message} Measured {measured}, required {required}, layer {layer}.` | `Error. {code}. {message} Clearance {clearance}, required {required}, layer {layer}.` |
| T10-3a | `src/embodic/ui/views/checks_view.py:217` (call site) | `measured=row.measured_text,` | `clearance=row.measured_text,` |
| T10-4 | `src/embodic/io/report.py:137` | `(MARGIN + 130, "Least measured")` | `(MARGIN + 130, "Least clearance")` |
| T10-5 | `src/embodic/selftest/catalogue.py:183` | `the check measured no track pair` | `the check found no track pair` |
| T10-6 | `docs/phase2/engineering/checks/build_registry.py:169`, `docs/phase2/engineering/equation_registry.json:2846`, `resources/evidence/equations.v1.json:2846`, `docs/phase2/engineering/equation_specification.md:574` (owner Agent 2) | `DRC clearance measurement and acceptance` | `DRC clearance computation and acceptance` |
| T10-7 | `resources/fonts/FONTS.md:24` | ``each SHA-256 above is the one measured with `sha256sum` after download`` | ``each SHA-256 above is the one computed with `sha256sum` after download`` |
| T10-7b | `resources/fonts/FONTS.md:25` | ``(`verified` by measuring;`` | ``(`verified` by computing each hash;`` |

Rendered examples use the first violation of the wave example. The values come from
`test_charts_compare_guide_export.py:187` and `test_results_and_checks.py:190`.

- Export confirmation row. "A trace is closer to a via than the via clearance rule. L1: 0.199965 mm clearance,
  0.200000 mm required."
- DRC table headers. "Message", "Clearance (mm)", "Required (mm)", "Layer".
- Row tooltip. "Error. DRC_TRACE_VIA. A trace is closer to a via than the via clearance rule. Clearance 0.199965 mm,
  required 0.200000 mm, layer L1." The required value uses the same formatter as the export row
  (`ui/viewmodels/results.py:361`), so its six figures are `inferred`, not read from a run.
- PDF table header. "Check", "Least clearance", "Required", "Pairs".
- Self-test failure. "ValueError: the check found no track pair".

**Fit.** In the PDF, "Least clearance" is 61.2 pt wide in Inter SemiBold 8 pt against 61.8 pt for "Least measured". The
cell is 110 pt (`verified` by the lever from the bundled font's advance widths). A PDF written from a patched copy
reads back "Check Least clearance Required Pairs" and shows no overlap on page 1 (`verified` by
`checks/v3_14_render_patched.py` and by viewing the page). In the DRC table, "Clearance" is 1.2 % wider than
"Measured" in Inter SemiBold and 1.3 % in Inter Regular (`verified` the same way). The Message column stretches, so
the screenshot row S37 (no sideways scroll at 1280 x 800) should hold. That is `inferred` and `not tested` in Qt.

**Left as they are.** `drc.column.measured`, the column id `measured` (`checks_view.py:43`) and `DrcRow.measured_text`
are identifiers nobody reads. Renaming them belongs with the JSON-key ruling, not with this copy change.

### 3.2 REQ-T-11: what the star-of-slots check establishes (pending Agent 2)

The check reads the coil count, the pole count and, in manual mode, the phase assignment. It passes when the signed
phasor sets of the other two phases equal phase A's set rotated by 120° and 240° electrical
(`src/embodic/winding/star_of_slots.py:61-79`). With one phase per layer pair it passes when Q = 2p
(`src/embodic/winding/feasibility.py:37-39`). Both are `verified` by reading. Neither reads the copper, the layer
positions or the interconnect. So the check establishes a symmetric 3-phase coil pattern. It does not establish balance
of the built winding, torque or efficiency.

The copy says "symmetric 3-phase pattern" everywhere. "Pattern" matches the "Coil pattern" field next to the status
(`design.py:223`). "Symmetric" names the property the check computes. The copy does not say "star of slots", because
the one-phase-per-pair mode does not use it (Agent 2's draft, section 1 item 5).

All rows in this section are pending Agent 2 (U-E14). Agent 2's draft `balance_statement.md` (worktree U-E14,
01:23) gives the hint copy for T11-1 and T11-2 word for word as below, and its three conditions in section 3 hold for
every row here.

| ID | Location | Current | Replacement |
|---|---|---|---|
| T11-1 | `src/embodic/ui/strings/design.py:218` | `Balanced: q = {q}, periodicity t = {t}.` | `Symmetric 3-phase pattern: q = {q}, periodicity t = {t}.` |
| T11-2 | `src/embodic/ui/strings/design.py:219` | `Not balanced for {coils} coils and {poles} poles.` | `No symmetric 3-phase pattern for {coils} coils and {poles} poles.` |
| T11-3 | `src/embodic/ui/strings/design.py:225` | `"Balanced."` | `"Symmetric 3-phase pattern."` |
| T11-4 | `src/embodic/ui/strings/design.py:226` | `Not balanced: each phase needs the same number of coils.` | `Not a symmetric 3-phase pattern: the other two phases must repeat phase A at 120° and 240° electrical.` |
| T11-5 | `src/embodic/ui/strings/design.py:227` | `Not balanced: choose {counts} coils.` | `No symmetric 3-phase pattern: choose {counts} coils.` |
| T11-6 | `src/embodic/ui/strings/design.py:228` | `"Not balanced."` | `"No symmetric 3-phase pattern."` |
| T11-7 | `src/embodic/errors/catalogue/winding.py:7` | `The star of slots gives no balanced 3-phase winding for this coil count and pole count.` | `No symmetric 3-phase pattern exists for this coil count and pole count.` |
| T11-8 | `src/embodic/errors/catalogue/winding.py:17` | `The manual phase assignment is not balanced; the value is the spread of the phase EMF phasor magnitudes.` | `The manual phase assignment is not a symmetric 3-phase pattern; the value is the relative spread of the three phase phasor sums, each coil counted as a unit phasor.` |

One addition, also pending Agent 2. The status label has pass styling (`phase_panel.py:82-85`), so a reader can still
take "Symmetric 3-phase pattern." for a verdict on the motor. A tooltip defines the term and says what the check
reads. It is true in the pass and in the fail state, because the label keeps one tooltip.

| ID | Location | New key | Text |
|---|---|---|---|
| A-1 | `src/embodic/ui/strings/design.py`, after l.228 | `"phase-balance-status.tooltip"` | `A symmetric 3-phase pattern has its three phases 120° electrical apart. The check reads only the coil count, the pole count and the phase assignment. It does not look at the copper or the layer positions.` |
| A-1a | `src/embodic/ui/views/phase_panel.py`, after l.59 `self.balance.setWordWrap(True)` (call site) | | `self.balance.setToolTip(text("phase-balance-status.tooltip"))` |

The reasons behind three of the replacements:

- T11-4. The old reason, "each phase needs the same number of coils", is necessary but not sufficient. A manual
  assignment with equal counts still fails when the phase angles do not repeat (`star_of_slots.py:75-79`, `verified`
  by reading). The new text states the condition the check applies. "Electrical" is there because the inspector also
  shows the layer-pair rotation, a mechanical angle (`pair-list.rotation` for `/winding/layers/pairs/*/rotation_rad`;
  `inferred`, a rotation of copper about the shaft axis).
- T11-7. The same code fires in the one-phase-per-pair mode, where the star of slots is not the method
  (`winding/plan.py:57-58` with `feasibility.py:37-39`). The new text names no method.
- T11-8. The value is (max - min)/max of the sums of unit phasors per phase (`winding/plan.py:129-136`). Every coil has
  weight 1 and no field enters, so "EMF" overstates it. The new text says what is summed.

Two points for Agent 2 and Fable on the draft balance statement. Its pass sentence ends "not a measured balance of the
motor". The word "measured" in user copy would be a new REQ-T-10 finding, so the copy above does not use it. Its pass
sentence also says "(star of slots)", which the draft's own item 5 rules out for the one-phase-per-pair mode.

### 3.3 REQ-L-03: program names

The clamp and rounding reasons end the inline notice "Changed from {old} to {new}: {reason}" (`design.py:204`). The new
reasons state the rule as one sentence, in the style of the existing reason at `validate.py:239` ("The generator uses
the trace spacing when the gap is smaller.").

| ID | Location | Current | Replacement |
|---|---|---|---|
| L03-1 | `src/embodic/model/validate.py:120` and `:125` | `Xcoil clamps to the supported range.` | `Values outside the supported range move to the nearest limit.` |
| L03-2 | `src/embodic/model/validate.py:134` and `:189` | `Xcoil rounds up to an even count.` | `Odd counts round up to the next even count.` |
| L03-3 | EQ-14 `formula`: `build_registry.py:68`, `equation_registry.json:1609`, `resources/evidence/equations.v1.json:1609` (owner Agent 2) | `(form (a) only; Xcoil's current-sheet model is not ported, D-049 d)` | `(form (a) only; the current-sheet model is not included, D-049 d)` |
| L03-4 | EQ-20 `formula`: `build_registry.py:83`, `equation_registry.json:2146`, `resources/evidence/equations.v1.json:2146` (owner Agent 2) | `pull-in T_pi = T_po - J omega f_e (Xcoil estimate)` | `pull-in T_pi = T_po - J omega f_e (estimate)` |
| L03-5 | EQ-27 `formula`: `build_registry.py:138`, `equation_registry.json:2640`, `resources/evidence/equations.v1.json:2640` (owner Agent 2) | `over the magnet span) (Xcoil 'kw1'); serpentine` | `over the magnet span); serpentine` |

**Rendered notices.** "Changed from 60 to 50: Values outside the supported range move to the nearest limit." and "Changed
from 7 to 8: Odd counts round up to the next even count." For a 60 mm air gap the patched `check_value` returns the
code `RANGE_ABOVE_SUPPORTED` with the new clamp reason (`verified` by `checks/v3_14_render_patched.py`). The notice
around the reason comes from the `design.py:204` template (`inferred`). The issue messages above the notice already
name the limit ("The value is above the supported maximum of {limit}{unit}.", `errors/catalogue/model.py:18`), so the
reason does not repeat the number.

L03-3 to L03-5 are copy proposals only. Agent 2 owns the formula text in U-E14 and may move the program names to a
field the guide does not show instead. Either way the displayed `formula` must end up without "Xcoil". The lever
re-scans every field the guide shows (`ui/viewmodels/results.py:735-747`) on this tree. It finds only these three
formulas and the EQ-30 name. The Xcoil mentions in the constants' `basis` text are not shown, because
`RegistryConstant` keeps only name, value, unit, source and status (`results/registry.py:85-92`, `verified` by reading
and by calling `equation_topic` on EQ-13 to EQ-30).

## 4. Tests and documents that pin a changed string

Agent 3 changes these in the same commit as the strings. The lever found them by searching `tests/`, `.claude/skills/`
and `docs/phase2/design/` for the rendered text.

| Test (file:line) | Function | Pins |
|---|---|---|
| `tests/unit/ui/session/test_session_state_machine.py:196` | `test_ui15_out_of_range_value_stays_until_apply_then_notice_and_undo` | L03-1. New expected text: `Changed from 60 to 50: Values outside the supported range move to the nearest limit.` |
| `tests/ui/qt_design/test_editing.py:106` | `test_ui15_no_silent_rewrite_the_suggestion_applies_only_on_apply_with_notice_and_undo` | L03-1, same text. |
| `tests/ui/qt_design/test_editing.py:142` and `:151` | `test_ui19_feasibility_hints_follow_the_winding_plan_after_each_recompute` | T11-1: `Symmetric 3-phase pattern: q = 2/5, periodicity t = 1.` and `Symmetric 3-phase pattern: q = 3/10, periodicity t = 1.` |
| `tests/ui/qt_design/test_inspector_widgets.py:175` and `:192` | `test_phase_balance_status_and_manual_assignment_follow_the_winding_plan` | T11-3: `Symmetric 3-phase pattern.` |
| `tests/ui/qt_design/test_inspector_widgets.py:188` | same | T11-4: `Not a symmetric 3-phase pattern: the other two phases must repeat phase A at 120° and 240° electrical.` |
| `tests/ui/qt_design/test_inspector_widgets.py:195` | same | T11-5: `No symmetric 3-phase pattern: choose 9, 12 or 15 coils.` |
| `tests/unit/ui/session/test_inspector_commands.py:120` | `test_phase_balance_status_follows_the_engine_and_names_balanced_coil_counts` | T11-3. |
| `tests/unit/ui/session/test_inspector_commands.py:124` | same | T11-5, same text as l.195 above. |
| `tests/ui/qt_results/test_charts_compare_guide_export.py:187` | `test_ui29_export_with_drc_failures_lists_them_with_focus_on_cancel` | T10-1: `{message} L1: 0.199965\u00a0mm clearance, 0.200000\u00a0mm required.` |
| `tests/ui/qt_results/test_results_and_checks.py:184` | `test_ruling_d_drc_table_shows_glyph_message_measured_required_layer_without_sideways_scroll` | T10-2: header list `["", "Message", "Clearance (mm)", "Required (mm)", "Layer"]`. |
| `tests/ui/qt_results/test_results_and_checks.py:190` | same | T10-3: `"Clearance 0.199965\u00a0mm, required" in tooltip`. |

No test pins T10-4 to T10-7, T11-2, T11-6 to T11-8, L03-2 or L03-3 to L03-5 (`verified` by the lever's search; the
search covers literal text, so a test that builds the text from `text()` keys keeps passing).

Only the strings above had a test. Three more are worth one in the same commit, because a regression there would put
a banned word back on screen. The first gap is the PDF DRC header (T10-4). The second is
the manual-mode reason text (T11-4). The third is the A-1 tooltip.

These files are not tests, but they pin the old text and need the same edit:

- `.claude/skills/verify/features/results_and_checks.md:12` says "failures with Measured and Required" (T10-2).
- `docs/phase2/design/screens.md:123` gives the example "Not balanced: choose 12, 18 or 24 coils" (T11-5).
- `docs/phase2/design/screens.md:366` gives the header "Measured (mm)" and the accessible-description example (T10-2,
  T10-3).
- `docs/phase2/design/screenshot_checklist.md:74` names the header "Measured (mm)" in S37 (T10-2).
- `docs/phase2/design/m4_review_2.md:55` and `:276` are a dated review record. Leave them.

The screens.md and checklist edits are Agent 1's, outside this unit's write scope. Fable routes them.

`tests/independent/m7/v3_01_rulings.py:60` quotes the old notice inside a ruling's reason text. It asserts nothing.
Agent 4 decides whether to update it.

## 5. Owners

| Rows | Files | Owner |
|---|---|---|
| T10-1 to T10-5, T11-1 to T11-8, A-1, L03-1, L03-2, and the tests in section 4 | `src/embodic/**`, `tests/**`, `.claude/skills/verify/**` | Agent 3 |
| T10-6, L03-3 to L03-5 | `docs/phase2/engineering/**`, then the packaged copy `resources/evidence/equations.v1.json` | Agent 2 |
| T10-7 | `resources/fonts/FONTS.md` | Fable routes (resources) |
| screens.md, screenshot_checklist.md | `docs/phase2/design/**` | Agent 1 |

## 6. Needs contract change (for Agent 6, U-D16)

| ID | Item | Where | Copy proposal | Why it needs a ruling |
|---|---|---|---|---|
| K-1 | JSON key `measured_mm` of a DRC violation, 186 findings | `src/embodic/drc/report.py:68`, written by `compute --json` | `clearance_mm` | interfaces.md names the key. A rename changes the output schema. |
| K-2 | JSON key `measured_min_mm` of a DRC summary, 47 findings | `src/embodic/drc/report.py:79`, also read at `io/report.py:143`, `io/exporters.py:145`, `selftest/catalogue.py:181` | `least_clearance_mm`, matching the PDF header "Least clearance" | Same. |
| K-3 | REQ-F-10 statement "whenever the measured clearance is below rule" | `docs/phase2/architecture/requirements.md:70`; D-006 uses the same words (`docs/decision_log.md:12`) | "whenever the clearance computed from the generated copper is below rule minus epsilon" | Requirement text. D-006 is Fable's record. |
| K-4 | Issue codes `UNBUILDABLE_UNBALANCED_WINDING` and `RANGE_MANUAL_ASSIGNMENT_UNBALANCED` | `errors/catalogue/winding.py:6` and `:16`; used at `winding/plan.py:58`, `:96` and `ui/viewmodels/session.py:617` | `UNBUILDABLE_NO_SYMMETRIC_WINDING` and `RANGE_MANUAL_ASSIGNMENT_ASYMMETRIC` | The issue list shows the code as the item tooltip (`ui/views/main_window.py:558`, `verified` by reading), so a person reads "UNBALANCED". Codes are stable contract ids. The V3-14 scan misses them (section 7). |

A design alternative for K-4, if Agent 6 keeps the codes. The issue-list tooltip could show the message's fix hint
instead of the code, and the code could stay in Ctrl+C copy only. That is a screens.md change I would make in a later
Agent 1 unit. I prefer the rename, because the CLI prints the code before every issue message (`cli/commands.py:64`,
`verified` by reading).

Two codes the lever also lists are not findings. `INVALID_MEASURED_SOURCE_EMPTY` and `INVALID_MEASURED_DESIGN_FIELD`
(`errors/catalogue/base.py:10-11`) refuse a `measured` input provenance. They use the word in D-007's sense, so they
fall under the existing allow-list reason for input provenance.

## 7. Defect found

**DEF-US9-01 (REQ-T-11, scan gap, minor).** The V3-14 scan patterns start with `\b`
(`tests/independent/m7/v3_14_scan.py:59-61`). Inside an UPPER_SNAKE code the word after an underscore has no word
boundary, so `UNBALANCED` in `UNBUILDABLE_UNBALANCED_WINDING` never matches. The UI shows codes as tooltips
(`main_window.py:558`). Status `verified` (reproduced).

```
python3 -I -c "import re; p = re.compile(r'\b(?:balanc\w*|unbalanc\w*)', re.I); print(p.search('UNBUILDABLE_UNBALANCED_WINDING'), p.search('UNBUILDABLE UNBALANCED WINDING'))"
```

The output is `None <re.Match object; span=(12, 22), match='UNBALANCED'>`. A fix for Agent 4 is to split codes on `_`
before the class search, as the lever's `hidden_codes` does.

## 8. How to re-check

```
cd <worktree>
python3 -I -B docs/phase3/design/checks/v3_14_copy_check.py
/home/claude/embodic/.venv/bin/python -I docs/phase3/design/checks/v3_14_render_patched.py . <new scratch folder>
```

`v3_14_copy_check.py` is stdlib only. It loads the class patterns, the literal extractor and the allow-list from Agent
4's `v3_14_scan.py`, and the font parser from `src/`. It exits 1 when a current string is missing, a text replacement
matches a class, this file lacks an old or new string, or a patched copy still has a finding. Its output on main
3440241 ends as follows (exit 0):

```
== all fixes and additions applied to a copy of the touched files
   resources/fonts/FONTS.md: V3-14 findings {'REQ-T-10': 2} -> 0
   src/embodic/errors/catalogue/winding.py: V3-14 findings {'REQ-T-11': 2} -> 0
   src/embodic/io/report.py: V3-14 findings {'REQ-T-10': 1} -> 0
   src/embodic/model/validate.py: V3-14 findings {'REQ-L-03': 4} -> 0
   src/embodic/selftest/catalogue.py: V3-14 findings {'REQ-T-10': 1} -> 0
   src/embodic/ui/strings/design.py: V3-14 findings {'REQ-T-11': 6} -> 0
   src/embodic/ui/strings/export.py: V3-14 findings {'REQ-T-10': 2} -> 0
   src/embodic/ui/strings/results.py: V3-14 findings {'REQ-T-10': 3} -> 0
   src/embodic/ui/views/checks_view.py: V3-14 findings 0 -> 0
   src/embodic/ui/views/dialogs.py: V3-14 findings 0 -> 0
   src/embodic/ui/views/phase_panel.py: V3-14 findings 0 -> 0
   resources/evidence/equations.v1.json: guide-shown REQ-T-10 and REQ-L-03 hits after: 0
   export.confirm.row: placeholders ['clearance', 'layer', 'message', 'required'], call keywords [...] at src/embodic/ui/views/dialogs.py: True
   drc.row.description: placeholders ['clearance', 'code', 'layer', 'message', 'required'], call keywords [...] at src/embodic/ui/views/checks_view.py: True
   phase-balance-status.tooltip: placeholders [], call keywords [] at src/embodic/ui/views/phase_panel.py: True
== header widths
   PDF 'Least measured': 61.8 pt of a 110 pt cell
   PDF 'Least clearance': 61.2 pt of a 110 pt cell
OK
```

The 21 main-src findings before the patch match the record's main-src rows (REQ-T-10 7, REQ-T-11 8, REQ-L-03 4) plus
the 2 FONTS.md lines, which the record lists under the installed package. The 233 JSON-key findings stay until the
K-1 and K-2 ruling. The 10 PDF findings follow the `report.py` literal, as the render lever shows.

`v3_14_render_patched.py` copies `src/` and `resources/` into a new folder, applies the fixes there, writes one PDF
report with the CLI and runs `check_value`. Output on main 3440241:

```
export exit 0
PDF DRC header: ['Check Least clearance Required Pairs']
clamp reason: RANGE_ABOVE_SUPPORTED | Values outside the supported range move to the nearest limit.
```

Not run in this unit are the Qt tests, the e2e walkthroughs and the full V3-14 scan. Fable's gate shares the two CPUs, and the
standing orders forbid test suites in this unit.
