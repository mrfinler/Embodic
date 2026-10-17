Prepared by: Agent 1 (UX/UI Expert Designer) - model: claude-opus-5-5

# Fix wave F1 rulings (U-S11)

Date 2026-10-17. Main e68d5ff. Decision D-055f. This document rules four items for the second UI unit of fix wave F1.
Each section gives the decision, its sources and an acceptance that Agent 3 can run offscreen
(`QT_QPA_PLATFORM=offscreen`). Tab order and Board-tab clipping are out of scope (U-M8a, REQ-N-12, REQ-N-15).

Every claim carries one status label. `verified` means read in the named source or reproduced by running something
here. The probes of this unit ran with `/home/claude/embodic/.venv/bin/python` (PySide6 6.11.2, Qt 6.11.2) on the
worktree source. They are not committed. Their output is quoted where a ruling rests on it.

## (a) REQ-N-02: typing previews after 300 ms, and Enter or leaving the field commits at once

### Decision

Typing in a field row restarts one 300 ms timer. When the timer fires, the app computes the typed value as a
preview. A preview changes the drawing and the results, and nothing else. Enter, Tab and leaving the field commit the
value and compute at once. Esc drops the typed text and the preview. A choice control (combo box, check box, segment)
commits and computes at once, with no timer. A newer edit always cancels the compute in flight.

Why preview and not commit on the timer. A commit writes an undo entry, sets the `user` chip and autosaves. Typing
"120" with two pauses would leave three undo entries and a recovery file holding "1". The preview keeps one undo entry
per committed edit and keeps Esc meaningful (design_spec.md section 10, "Esc ... in a field, revert the uncommitted
value"). This is the principle experience first. The drawing follows the typing as it did in Xcoil (F-08, 140 ms
debounce, `docs/phase1/software/feature_inventory.md` l.84, `verified` by reading), and undo stays clean.

### Behaviour on main e68d5ff

- A field row's `QLineEdit` commits on `editingFinished` (`src/embodic/ui/views/coil_panel.py` l.229), a combo box on
  `activated` (l.221), a check box on `clicked` (l.225), a segment on its button click (l.134). Every commit goes to
  `DesignSession.edit` and `_refresh`, which submits a compute at once (`session.py` l.712, l.1027 to l.1048).
  `verified` by reading.
- No timer exists, so typed keys never compute and Enter computes at once (U-M7c report, N-02: "4 typed keys → 0
  computes"). `verified` by U-M7c running it, not rerun here.
- No `QSpinBox` or `QDoubleSpinBox` exists in `src/embodic/ui`, and no field handles Up, Down or Esc. `verified` by
  grep for `SpinBox`, `Key_Up` and `Key_Escape`. The keyboard map promises Up, Down and Esc in a field
  (design_spec.md section 10), so those rows are unbuilt today.
- Clicking a toolstrip button does not move focus out of a line edit, so `editingFinished` does not fire and the
  action runs on the committed design. A plain `QToolBar` probe shows it (`verified`). Typing "9" into "11.47"
  and clicking a toolbar action logged `['triggered, focus=QLineEdit']` and no `editingFinished`. The embodic
  toolstrip sets `TabFocus` (`toolstrip_bar.py` l.144), which also does not take focus on a click, so the same holds
  in the app (`inferred`). See DEF-US11-03.

Qt signal facts the contract uses (Qt 6.11.2, `verified` by an offscreen probe of real widgets):

| Input | Signals, in order |
|---|---|
| Typing ".5" into "12" | `textEdited("12.")`, `textEdited("12.5")` |
| Return | `returnPressed`, `editingFinished` |
| Typing, then focus out | `textEdited`, `editingFinished` |
| Focus in and out, no change | none |
| Esc in a bare `QLineEdit` | none, and the text stays |
| Down on a closed combo box | `currentIndexChanged(1)`, `activated(1)` |
| Space on a check box | `toggled(True)`, `clicked(True)` |

### Contract per widget kind

One timer per window, `DEBOUNCE_MS = 300`, single shot. `QTimer.start()` restarts a running timer ("Starts or
restarts the timer with the timeout specified in interval", https://doc.qt.io/qt-6.11/qtimer.html, Qt 6.11.2,
`verified`). The default `Qt.CoarseTimer` may fire up to 5 % early, 15 ms at 300 ms (same page, `verified`). The
300 ms value is REQ-N-02's and stays an `assumption` until a user study or the Windows timing run measures it.

| Widget kind | Starts or restarts the timer | Commits and computes at once | Notes |
|---|---|---|---|
| Field row `QLineEdit` (numeric or text) | `textEdited` | `editingFinished` (Enter, Return, Tab, focus out with changed text) | `textChanged` is never used, because `setText` from the session would start a preview of the shown value. |
| Up and Down stepping in a numeric field, or a spin box, once built | each user step (`valueChanged` caused by a key or a button) | Enter, Tab, focus out | A held key auto-repeats, so the timer restarts on each step and one preview runs after the last. The wheel never steps a field without focus (design_spec.md section 10). |
| `QComboBox` field | none | `activated` | `currentIndexChanged` is never used for commits, because the session sets the index when it shows a row. Down, Down, Down gives three commits and three requests; each cancels the one before it. |
| Check box field | none | `clicked` | |
| Segment field | none | its button `clicked` | |
| Stack-up generator inputs (`board_rotor_panel.py` l.77) and table cells (screw table, layer pairs) | none | the existing commit (`editingFinished`, cell editor close, `activated`) | No preview. One typed stack-up input does not map to one design value; the stack-up is written only when all three inputs hold values (`session.py` `set_stackup_input`). |

### What the typed text does

The timer fires on the text in the field at that moment. Earlier keystrokes never compute.

| Text when the timer fires | Preview | Message under the field |
|---|---|---|
| Equal to the committed value (after trimming) | none; the committed outcome stays or comes back | none |
| Empty, or not a number in a numeric field ("-", "1e", "12,5", "abc") | none | none until commit |
| A number, but the draft with it does not parse to `DesignParameters` | none | none until commit |
| A number, and the draft parses | yes | none until commit |

The preview computes exactly the design and provenance that committing the same text would produce, so a commit after
a preview finds the same `(design, provenance)` and starts no second request (the equality check in
`DesignSession._refresh` already does this). Messages, the `<id>-error` label, `invalid=true`, the Checks list, the
chip, `new-required-count`, the undo stack and the autosave change only on commit. This keeps screens.md's rule
"Validation runs on commit" (screens.md l.44, `verified` by reading). Errors are still identified in text, as SC 3.3.1
asks, at commit ("If an input error is automatically detected, the item that is in error is identified and the error
is described to the user in text", https://www.w3.org/WAI/WCAG22/Understanding/error-identification, `verified`).

A preview changes content, not context. Focus stays in the field, so SC 3.2.2 On Input is met ("This success
criterion is automatically met if changes in content are not also changes of context",
https://w3c.github.io/wcag/understanding/on-input.html, editor's draft, `verified` by reading).

### Enter, Tab, focus out and Esc

- Enter, Return, Tab and focus out stop the timer and commit. The compute starts at once, unless a preview of the same
  design and provenance is shown or in flight.
- Esc in a field with uncommitted text stops the timer, puts the committed text back and keeps focus in the field. If
  a preview ran, the committed outcome comes back, because the session submits the committed design again (the
  stage cache makes this cheap, `inferred`). Esc writes no undo entry. Esc in a field without uncommitted text does
  what it does today.
- Every command that reads the design commits the focused field's uncommitted text first: Compute (F5), Save, Save as,
  Export, Report, New, Open, Examples, Undo and Redo, from the toolstrip or a shortcut. Undo after that commit returns
  the field to its value before the typing.

### How the timer meets the worker

1. A keystroke cancels the request in flight at once when that request is a preview of the same field. It does not
   wait for the next timer expiry. `ComputeWorker.submit` already cancels the run it supersedes
   (`workers.py` l.58 to l.63); a keystroke needs a cancel without a submit.
2. The worker keeps one request in flight; the view-model drops any result whose request id is not the latest (UI-02,
   `test_worker_and_errors.py` l.21). Previews and commits share that one id sequence.
3. "Updating" and the 60 % dim keep their present rule. They start 300 ms after a compute starts
   (`results_view.py` l.67, `set_computing`). The timer adds no indicator while the user types.
4. Result arrival runs on the GUI thread. A D08 result cost about 330 ms there after U-M6a (CHECKPOINT, U-M6a line,
   `verified` by reading, not rerun). A preview that lands while the user types again delays keystroke echo past
   REQ-N-02's 100 ms. U-M8a works on that stall now. The acceptance below measures the echo during an arrival, so
   this unit's ruling does not hide the stall.

UX-AC-22 changes so that its clock starts when an edit takes effect, not at the first keystroke. New text for
`docs/phase2/design/acceptance_criteria.md` (Agent 1 file; Fable applies it or dispatches the edit):

> UX-AC-22. Recompute. An edit takes effect at a commit, at a choice, or 300 ms after the last keystroke in a field.
> Within 300 ms after that, the results update for the default example or show "Updating" with the previous values
> dimmed. The N02 rows of `docs/phase3/design/fix_wave_f1.md` section (a) test it.

### Acceptance (offscreen, Qt test)

Use the `make_shell` fixture with its counting `compute_fn` (`tests/ui/qt_shell/conftest.py` l.45). Load D08
(`spiral_12c10p_d08`), wait for the first result, then clear the call list. Field `param-r-inner` (committed 11.47 mm,
`ux_verification_plan.md` N-05). Times use `QElapsedTimer`.

| Id | Steps | Pass |
|---|---|---|
| N02-1 | Focus the field, select all, type "11.48" with `QTest.keyClicks` and a 50 ms delay, then wait 600 ms. | Exactly one compute call. It starts 300 ms ± 50 ms after the last key. Its design has r_inner 11.48 mm. The undo stack length, the `param-r-inner-prov` chip text and the autosave file are unchanged. |
| N02-2 | After N02-1, press Return. | No new compute call. The undo stack grows by one. The chip reads `user`. |
| N02-3 | Type "11.49", then press Return 100 ms after the last key. | One compute call, starting within 50 ms of Return. No second call after 300 ms. |
| N02-4 | Type "abc", wait 600 ms. Then press Return. | No compute call. While waiting, `param-r-inner-error` is hidden. After Return, it shows the catalogue text of the issue code (R14) and the field has `invalid=true`. |
| N02-5 | Type "12", press Esc after 100 ms. | No compute call. The text is "11.47" again. Focus stays in the field. |
| N02-6 | Type "12", wait 600 ms (one preview), press Esc. | The results show the committed outcome again (`res-ke-value`, the card of `ke_phase_v_s_per_rad`, equals its text before N02-6). The undo stack is unchanged. |
| N02-7 | Use a `compute_fn` that blocks until its token is cancelled. Type "12", wait 400 ms, type "3". | The first request's `CancelToken` is cancelled within 50 ms of the "3" key. One more call starts 300 ms ± 50 ms after it. |
| N02-8 | Focus a `QComboBox` field row (candidates `param-rotor-kind`, `param-modulation`), press Down. Focus the check box field `param-fillet-max` where it is shown, press Space. | Each starts one compute call within 50 ms. No timer is running afterwards. |
| N02-9 | Save the design once to a path under `tmp_path`. Type "11.5" into the field, then click the toolstrip Save button without leaving the field. | The file at that path holds 11.5 mm. |
| N02-10 | Use a `compute_fn` that returns after 200 ms. Type "11.6", wait 450 ms, then type five keys at 50 ms. Measure the largest gap between 10 ms GUI timer ticks, as UI-05 does. | Report the gap. It passes at 100 ms or less (REQ-N-02 input echo, `assumption`). A fail goes to U-M8a's stall work, not to this ruling. |

The candidates of N02-8 are the `CHOICE` fields outside `SEGMENT_WIDGETS` and the one `BOOL` field of `FIELDS`
(`verified` by listing `FIELDS`). Which of them D08 shows is not checked here. Agent 3 picks one of each that D08 or
another packaged example shows, and records the ids.

## (b) REQ-N-23: Windows high contrast

### Decision

When the system reports high contrast, the app does three things. The chrome takes the system colours. The geometry
view, its legend, the charts and the board picker swatches switch to the greyscale and hatch mode. The theme of the
drawing follows the lightness of the system window colour while the choice is System. Sizes, paddings, the 2 px
focus ring, labels, eye fills and line styles stay as they are. When high contrast turns off, the app returns to its
theme and to the render mode the user had chosen.

### Detection

The app reads `QGuiApplication.styleHints().accessibility().contrastPreference()` and compares it with
`Qt.ContrastPreference.HighContrast`. It listens to `contrastPreferenceChanged` on the same object.

- The API exists in the installed PySide6. An offscreen import printed `PySide6 6.11.2 Qt 6.11.2`,
  `QStyleHints: ['accessibility', 'colorScheme', ...]`, `contrastPreference read-only notify
  contrastPreferenceChanged(Qt::ContrastPreference)` and `ContrastPreference ['HighContrast', 'NoPreference']`.
  Offscreen it returns `NoPreference`. `verified` by running.
- Qt documents it: "Since: Qt 6.10" and "This property holds the contrast mode set by the system"
  (https://doc.qt.io/qt-6.11/qaccessibilityhints.html, Qt 6.11.2, `verified`). Qt's blog lists "On Windows 11, a
  Contrast theme is applied" as one condition (https://www.qt.io/blog/high-contrast-mode-in-qt-6.10, 2025-09-15,
  `verified` by reading).
- On Windows, Qt answers from `SPI_GETHIGHCONTRAST` and `HCF_HIGHCONTRASTON` (`qwindowstheme.cpp` l.675 to l.678 and
  l.1273 to l.1279 at tag v6.11.2, https://raw.githubusercontent.com/qt/qtbase/v6.11.2/src/plugins/platforms/windows/qwindowstheme.cpp,
  `verified` by reading). A theme change runs `QStyleHintsPrivate::update`, which calls `updateContrastPreference`
  and emits the signal on a change (`qstylehints.cpp` l.735 to l.740, `qaccessibilityhints.cpp` l.9 to l.16, same tag,
  `verified` by reading). That turning a contrast theme on sends one of the messages Qt watches (`WM_THEMECHANGED`,
  `WM_SYSCOLORCHANGE`, `qwindowstheme.cpp` l.511 to l.522) is `inferred`. The Windows run W4 confirms it.
- Under high contrast Qt reports `colorScheme()` as `Unknown` (`qwindowstheme.cpp` l.656 to l.660, `verified` by
  reading). `os_prefers_dark()` (`app.py` l.102) then returns False, so today a black contrast theme gets the light
  theme. The theme rule below fixes this.

### What changes under high contrast

| Part | Normal | High contrast |
|---|---|---|
| Application palette | `palette_for(tokens)` (`style.py`) | the system palette: `app.setPalette(system_palette())`, where the default `system_palette` returns an empty `QPalette()` |
| Style sheet | `<theme>.qss` | the same template rendered with system colours (token map below), set again on every system palette change |
| Indicator glyphs (`check.svg`, `chevron-down.svg`, `chevron-down-disabled.svg`) | theme folders | written at apply time in the mapped colours, in a folder the `theme:` search path points to |
| Toolstrip and dialog icons | `icon_color` of the theme | WindowText for normal and checked, Disabled WindowText for disabled |
| Phase render mode | the user's choice | `GREYSCALE_HATCH`. View > Greyscale and G show it checked and are disabled. The tooltip ends with "On while Windows high contrast is on." |
| Geometry view, legend, charts, board picker swatches, canvas text | theme tokens | theme tokens, greyscale ladder (design_spec.md 3.4). The drawing keeps its own colours, as CSS `forced-color-adjust: none` does (Phase 1 design spec 3.6). |
| Theme of the drawing | `resolve_theme(choice, os_prefers_dark())` | the same call, with "OS prefers dark" read as: the relative luminance of the system Window colour is below 0.179 |
| Exports (SVG, PDF, DXF) | unchanged | unchanged. High contrast is a screen setting. |

Applying an empty `QPalette()` restores the platform palette with resolve mask 0. An offscreen probe shows it
(`verified`). After a custom palette, `setPalette(QPalette())` printed the platform colours again and
`resolveMask after reset: 0`. Qt then keeps the palette in step with the system by itself (`inferred` from the zero
mask).

The threshold 0.179 is where a colour has equal contrast against black and white: (L + 0.05) / 0.05 = 1.05 / (L + 0.05)
gives L = 0.179 (`verified` by computing). A theme with a black window gets the dark drawing. A theme with a cream
window gets the light drawing. An explicit Light or Dark choice still wins over it.

The style sheet is rendered from text, not from `palette(<role>)` references, for two measured reasons. In an offscreen
probe, `QLabel:disabled` with `color: palette(window-text)` painted the Active colour `#ffffff`, not the Disabled
`#a6a6a6`. After the palette changed, a label styled with `palette()` kept its old colours until the sheet was set
again. Both `verified` by running. So the app renders the template with hex values taken from the current system
palette, and renders it again when the palette changes. Rendering is idempotent. The same palette gives the same text,
and `apply_theme` already skips a sheet equal to the one applied (`style.py` l.86 to l.97), so the app's own
`setPalette` cannot loop.

### Token to palette map

The high-contrast sheet differs from `<theme>.qss` only in colour values. Build-time work (Agent 3): `build_themes.py`
also writes the template with `@dir` and `@focus-ring-px` filled and the colour tokens left as `@<token>`, so the app
can fill them at run time.

| Token | System colour (QPalette group, role) | Why |
|---|---|---|
| `bg-app`, `surface`, `surface-sunken`, `surface-selected` | Active Window | One background. Hover and selection tints have no system pair; borders carry the states. |
| `text-1`, `text-2`, `text-3` | Active WindowText | One text colour. Hierarchy comes from size and weight. |
| `divider`, `grid-line`, `border-control`, `border-strong`, `focus-ring` | Active WindowText | WindowText on Window is the text pair of the contrast theme (`inferred`). The focus ring keeps 2 px. |
| `surface-inverse` | Active WindowText | Inverted pair for the primary button, the verified badge, the checked check box and selections. |
| `text-inverse` | Active Window | The other half of the inverted pair. |
| `text-disabled` | Disabled WindowText | Qt fills it from `COLOR_GRAYTEXT` under high contrast (`qwindowstheme.cpp` l.766 to l.769, `verified` by reading). |
| `status-pass`, `status-fail`, `status-warn` | Active WindowText | Status already has a glyph and a word (design_spec.md 3.1); the invalid field keeps its 2 px border against the 1 px normal one. |
| `canvas` | the theme value | The drawing keeps its own colours. |

The map avoids Highlight on purpose. Under high contrast Qt sets Highlight to the accent colour from `UISettings` when
the build has `cpp_winrt`, and to `COLOR_HIGHLIGHT` otherwise, while HighlightedText is always `COLOR_HIGHLIGHTTEXT`
(`qwindowstheme.cpp` l.115 to l.136 and l.326 to l.340, `verified` by reading). Whether the two make a readable pair in
the shipped build is `unresolved`. The inverted Window and WindowText pair is readable in every contrast theme by
construction (`inferred`). Cost, as an `assumption`: selections and buttons do not take the user's Highlight and
Button colours. W4 records whether reviewers accept that.

### Test seam

`create_shell` gains two parameters next to `prefers_dark` (`app.py` l.114 to l.139):

- `prefers_high_contrast: Callable[[], bool]`. The default reads the Qt property above.
- `system_palette: Callable[[], QPalette]`. The default returns `QPalette()`.

`create_shell` connects `QGuiApplication.styleHints().accessibility().contrastPreferenceChanged` to a new slot
`MainWindow.on_os_contrast_changed()`, which reapplies the theme. The window also reapplies on
`QEvent.Type.ApplicationPaletteChange` while high contrast is on. The property is read-only and has no setter (probe
output above), so a test cannot flip it. It flips the injected callable and calls the slot.

`make_shell` gains `high_contrast=False` and `system_palette=None` and passes them on. The test palette is an
example, not a Windows theme reading: Window `#000000`, WindowText `#ffffff`, Base `#000000`, Text `#ffffff`, Button
`#000000`, ButtonText `#ffffff`, Disabled WindowText `#a6a6a6`.

### Acceptance (offscreen, Qt test)

| Id | Steps | Pass |
|---|---|---|
| N23-1 | `make_shell(high_contrast=True, system_palette=<example>)`, load D08. | `appearance` reports `GREYSCALE_HATCH`; `act-greyscale` is checked and disabled; its tooltip ends with "On while Windows high contrast is on." |
| N23-2 | Same window. Read `QApplication.styleSheet()`. | Every `#rrggbb` in it is one of the example palette colours or the dark theme's `canvas`. With every colour value replaced by one placeholder, it equals `dark.qss` with the same replacement. |
| N23-3 | Grab `main-window`. Sample the text pixels of `st-units` and the 2 px ring of a focused `param-r-inner`. | The background of `st-units` is `#000000` and the lightest pixel of its text run is `#ffffff`. The ring pixels are `#ffffff`. |
| N23-4 | Grab `fig-canvas`. | The theme is dark (the example Window is black). Copper pixels lie on the dark `phase-*-grey` ladder. The 12 labels with phase and sign and one eye fill per coil exist, as UX-AC-05 checks. |
| N23-5 | Flip the callable to False and call `window.on_os_contrast_changed()`. | `QApplication.styleSheet()` equals the theme's `.qss` file text, the palette equals `palette_for(tokens)`, and the render mode is the user's choice from before N23-1 (colour by default; greyscale when the test toggled it first). |
| N23-6 | With high contrast on, replace the system palette with a second example (Window `#ffffff`, WindowText `#000000`) and send `ApplicationPaletteChange`. | The sheet now holds the second palette's colours, and the drawing theme is light. A second identical event leaves `styleSheet()` unchanged. |

W4 in `ux_verification_plan.md` stays the Windows check. The reviewer turns on two contrast themes and records
whether the canvas switches and whether any text is clipped or invisible.

## (c) DEF-UM7d-02, REQ-T-16, UI-33: OR-07 and OR-08 dependency note

### Copy

One line per validity check that lists dependent oracles. It is built from the registry fields `id`,
`dependent_oracles` and `independent_oracles` (`resources/evidence/equations.v1.json`, EC-05: `["OR-07", "OR-08"]` and
`["OR-01"]`, `verified` by reading). For EC-05 the line reads:

> OR-07 and OR-08 are not independent of EC-05. They compare with data from the source that calibrates EC-05, so they
> cannot confirm EC-05. OR-01 is the independent check.

The claim rests on the registry: "D09 is both the calibration source and oracle O2: O2 cannot validate EC-05" (EC-05
`independence`), and OR-07 and OR-08 are the D09 EMF and B oracles (`docs/phase2/engineering/oracle_tests_spec.md`
l.77 and l.78). `verified` by reading. The line does not name D09. The registry has no structured field for the
calibration source, and the EQ-05 register entry already lists "EV-13: D09" under Sources.

String keys in `src/embodic/ui/strings/results.py`:

| Key | English text |
|---|---|
| `results.how.oracles.dependent-many` | `{oracles} are not independent of {code}. They compare with data from the source that calibrates {code}, so they cannot confirm {code}.` |
| `results.how.oracles.dependent-one` | `{oracles} is not independent of {code}. It compares with data from the source that calibrates {code}, so it cannot confirm {code}.` |
| `results.how.oracles.independent-many` | ` {oracles} are the independent checks.` |
| `results.how.oracles.independent-one` | ` {oracles} is the independent check.` |
| `guide.eq.oracles` | `Oracles` |

`{oracles}` joins IDs as "A", "A and B", or "A, B, and C". The independent sentence is appended only when
`independent_oracles` is not empty. A check with no `dependent_oracles` gets no line. The phrase "not independent of
EC-05" is lowercase, because `test_oracle_dependency_note.py` matches it exactly.

### Placement

1. The "How was this computed" disclosure of every result row whose Traceable carries the EC-05 flag. The line goes
   directly after the line that states the check. That is Limitations when the effect is a limitation, and Validation
   state after "EC-05 caps the badge: ..." when the effect is a cap. On D08 that is 14 rows, from
   `ke_phase_v_s_per_rad` to `edge_leakage_fraction` (`verified` by printing the disclosures). Copy trace carries it,
   because `trace_text` reads the disclosure.
2. The equation register entry of EQ-05, as a row labelled "Oracles" directly after its "Validity checks" row for
   EC-05.
3. Not on the result cards, the rail or the PDF. The PDF report prints no EC-05 line today (grep of `src/embodic/io`
   finds no `EC-05`, `verified`); see open question Q2.

### Acceptance (UI-33 addition)

| Id | Check | Pass |
|---|---|---|
| T16-1 | `tests/unit/ui/results/test_oracle_dependency_note.py` | Remove the strict xfail. Both parameters pass. |
| T16-2 | D08 and the packaged registry. For each row, find the line that starts with "EC-05 " in Limitations or Validation state. | The next line equals the EC-05 copy above, character for character. |
| T16-3 | `equation_topic("EQ-05", registry).rows` | The row after the EC-05 "Validity checks" row is `("Oracles", <EC-05 copy>)`. |
| T16-4 | A registry fixture whose check has `dependent_oracles=("OR-07",)` and no independent oracles. | The line is "OR-07 is not independent of EC-05. It compares with data from the source that calibrates EC-05, so it cannot confirm EC-05." with no third sentence. |
| T16-5 | A check with empty `dependent_oracles`. | No oracle line and no "Oracles" row. |
| T16-6 | Qt. Expand `res-ke-how` (the card of `ke_phase_v_s_per_rad`, `result_key` maps it to `ke`) and read its labels. | One label holds the EC-05 copy. |

## (d) REQ-T-14(b), UX-AC-17, UI-32: the version stamp on the geometry view

### Decision

Inside the app, the geometry view is the only engine drawing that carries the version stamp and design hash. The
charts do not. Every exported file keeps its stamp (REQ-T-07).

The Phase 1 design put the stamp on the canvas: "'Illustrative, not computed' stamp until the engine draws it (then
'Computed · engine vX.Y')" (`docs/phase1/design/design_spec_draft.md` l.241, `verified` by reading). Phase 1 UX-AC-17
read "engine drawings and exports carry the engine version stamp" (`design_handoff_for_agent3.md` l.132). The Phase 2
list renumbered UX-AC-17 to units and dropped the stamp clause, while REQ-T-14 still cites "Agent 1 UX-AC-17". That
is why U-M7d found "UX-AC-17 assigns no stamp to the drawing" (DEF-US11-02).

Why the canvas only. The canvas is the picture people screenshot to discuss a design, and a stale canvas can show an
older design than the inspector. The stamp tells a reader which design they look at. The charts plot the same outcome,
and each chart already carries its badge, EQ chip and assumptions tag; a second line of codes under each chart adds
clutter and no new fact (principle experience first). A chart-only screenshot carries no stamp. That is an accepted
limit.

### Copy and placement

- Text: `embodic {embodic} | design {hash12}`, where `{embodic}` is `outcome.versions.embodic` and `{hash12}` is the
  first 12 hex digits of `outcome.design_hash` after the `sha256:` prefix. For D08 on e68d5ff it reads
  "embodic 0.0.1 | design 327919a0eef5" (example; `verified` by computing D08, hash
  `sha256:327919a0eef55ce2c458635f6160047af7654ebd0a04e818ee225fd5f69615d8`). The separator matches the SVG footer
  (`svg_writer.py` l.302), so a reader can match the canvas with an exported file.
- String key `shell.canvas.stamp`, in `src/embodic/ui/strings/shell.py`.
- Place. The bottom left of the canvas viewport, inset 8 px, drawn in `drawForeground` like the legend. JetBrains Mono
  12 px in `text-3` on a `canvas` plate with 4 px padding, so copper never runs behind the text. Contrast of `text-3` on
  `canvas` is 5.74:1 light and 6.86:1 dark (`verified` by computing #666666 on #ffffff and #a0a0a0 on #171717).
- The stamp box joins the label obstacles, as the legend does (`geometry_view.py` l.319 to l.321).
- It names the drawn outcome. While the canvas shows the last valid drawing, the stamp keeps that drawing's hash.
- It is hidden while the canvas has no drawing (`canvas_blank` shown).
- Accessible text. The canvas accessible description ends with the stamp text, so a screen reader can read it.
- Seam: `GeometryView.stamp() -> str | None` and `GeometryView.stamp_rect() -> QRectF`, as `ChartWidget.stamp()` does
  for the illustrative stamp (`charts.py` l.141 to l.143).

### UI-32 acceptance text

New row for `docs/phase2/architecture/test_plan.md` UI-32 (Agent 6 file):

> UI-32. Drawing stamps. (a) A chart model with `computed=False` shows "Illustrative, not computed"; an engine chart
> shows no such stamp. (b) With D08 open, `fig-canvas` `stamp()` equals "embodic " + `versions.embodic` + " | design "
> + the first 12 hex digits of `design_hash`, and its rectangle lies inside the viewport's bottom-left 50 % by 25 %.
> (c) A grab of the canvas differs inside `stamp_rect()` from a grab with the stamp switched off, and the darkest text
> pixel in the plate reaches 4.5:1 on the plate. (d) After an invalid edit makes the drawing stale, `stamp()` is
> unchanged. After loading `spiral_12c14p`, `stamp()` names that outcome's hash. (e) At fit zoom no phase label box
> meets `stamp_rect()`. (f) The canvas accessible description ends with the stamp text.

Clause (a) is the present test (`tests/ui/qt_results/test_charts_compare_guide_export.py` l.78). Clauses (b) to (f)
are new.

## Defects found

| Id | Severity | Defect | Reproduce | Status |
|---|---|---|---|---|
| DEF-US11-01 | minor | The export checklist prints 5 hex digits of the design hash with its prefix: "design sha256:32791" (`src/embodic/ui/viewmodels/export.py` l.158 slices `design_hash[:12]`, and the hash starts with "sha256:"). | Compute D08 and format `export.check.stamp` as `ExportViewModel.checklist` does. Output on e68d5ff: "Stamp: embodic 0.0.1, registry v1+af64e8c1cbca.c01a66176ad6, design sha256:32791". | `verified` by running. Fix: use the same `{hash12}` as the canvas stamp. |
| DEF-US11-02 | major (traceability) | REQ-T-14 cites "Agent 1 UX-AC-17", but Phase 2 UX-AC-17 is the unit rule. The stamp clause has no Phase 2 UX-AC source. | Read `requirements.md` l.223 and `acceptance_criteria.md` UX-AC-17. | `verified` by reading. Fix: Agent 6 cites this document's section (d) and UX-AC-18. |
| DEF-US11-03 | major | A toolstrip command run while a field holds typed text acts on the committed design. Save would write the old value. | Type a new value into `param-r-inner` and click the toolstrip Save without leaving the field; open the saved file. | `inferred` from the plain-Qt probe in (a); not run in the app. Fix: the commit-first rule in (a), test N02-9. |
| DEF-US11-04 | minor | Esc in a field and Up and Down stepping are in the keyboard map (design_spec.md section 10) but not built. | Grep `src/embodic/ui` for `Key_Escape` and `Key_Up`: no field handles them. | `verified` by grep. Esc is fixed by (a). Stepping stays a follow-up. |
| DEF-US11-05 | major | Under Windows high contrast the System theme always resolves to light, because Qt reports `colorScheme()` as `Unknown`. | Read `qwindowstheme.cpp` l.656 to l.660 at v6.11.2 and `app.py` l.102. | `inferred` from source; not run on Windows. Fix: the theme rule in (b). |

## Requests to other owners (through Fable)

- Agent 6 amends REQ-T-14 to "Drawings not produced by the engine shall carry 'Illustrative, not computed'; the
  geometry view and every export shall carry the version stamp and design hash", with this document's section (d)
  as source. Agent 6 replaces UI-32 in `test_plan.md` with the text above and adds UX-AC-22's new text as the
  acceptance of REQ-N-02.
- Agent 3, in the second UI unit of F1, builds (a) to (d) and DEF-US11-01, 03 and 04 (Esc only), and runs every
  acceptance row above.
- Fable applies the UX-AC-22 text to `docs/phase2/design/acceptance_criteria.md`, or dispatches an Agent 1 edit.
  This unit writes only this file.

## Open questions for Fable

- Q1. Stepping. Up, Down and Shift steps are in the keyboard map and unbuilt. Build them in F1 with the timer rule of
  (a), or leave them for a later wave? Default used: later wave.
- Q2. The PDF report prints no EC-05 limitation, so REQ-T-16's note does not reach the report. Should "Key results"
  in the PDF carry each row's limitations? Default used: no change in F1.
- Q3. The high-contrast map gives up the user's Highlight and Button colours for a guaranteed pair. If the W4 reviewers
  reject that, the fallback is Highlight and HighlightedText for selections only, after W4 measures their contrast in
  the shipped build.
