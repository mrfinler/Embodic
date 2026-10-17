Prepared by: Agent 1 (UX/UI Expert Designer) - model: claude-opus-5-5

# Fix wave F2 rulings (U-S12)

Date 2026-10-17. Main b977621. Decisions D-056g and D-056k. This document rules the inspector width defect
(DEF-U-M7c-02, REQ-N-15) and Up, Down and Shift stepping (DEF-US11-04), and records the UX-AC-22 edit. Each section
gives the decision, its sources and an acceptance that Agent 3 can run offscreen (`QT_QPA_PLATFORM=offscreen`).

Every claim carries one status label. `verified` means read in the named source or reproduced by running something
here. The probes of this unit ran with `/home/claude/embodic/.venv/bin/python` (PySide6 6.11.2) on the worktree
source, with the bundled fonts registered by `qt_application()`. They monkeypatch candidate layouts at import time and
are not committed. Their output is quoted where a ruling rests on it.

## (a) DEF-U-M7c-02, REQ-N-15: every inspector form fits its viewport

### What is too wide

REQ-N-15 asks for "no clipping, no overlap, no horizontal scroll in forms" (`docs/phase2/architecture/requirements.md`
l.189, `verified` by reading). `FieldPanel` turns the horizontal scroll bar off (`coil_panel.py` l.364), so a body wider
than the viewport is cut at the right edge. Measured on b977621 (`verified` by running, body width / viewport width):

| Example | 960 x 540 | 1280 x 800 | 1920 x 1080 |
|---|---|---|---|
| `spiral_12c10p_d08` | Board 327 / 258 | Board 327 / 298 | Board 327 / 298 |
| `serpentine_16p_example` | Coil 262 / 258, Layers 306 / 258, Board 327 / 258 | Layers 306 / 298, Board 327 / 298 | Layers 306 / 298, Board 327 / 298 |

Three things set those widths (D08 at 960 x 540, `verified` by running):

1. A combo row. `param-rotor-kind` needs 273 px: combo 134, unit column 63, chip 72, spacing 4. `_align_units` gives
   every unit label of the tab the width of the widest unit, `W/(m²·K)` (`coil_panel.py` l.402 to l.407). The Rotor and
   Drive group boxes need 309 px, and the body adds 9 + 9 px.
2. The Fasteners buttons. "Add pattern" (103 px) and "Remove pattern" (128 px) sit on one line, so the Fasteners box
   needs 273 px. This limit shows only after the combo rows are fixed.
3. The serpentine `param-stack-mode` segment, "Single board" and "One board per phase", needs 252 px on one line.
   This is DEF-US12-01; the strict xfail test loads D08 only, so it does not see it.

At 960 x 540 a group box gets 258 − 18 − 36 = 204 px for its rows. With the chip on the control line, a line edit row
with the `W/(m²·K)` unit needs 72 + 63 + 72 + 4 = 211 px. So no unit or combo change alone fits while the chip stays
on the control line.

### Decision

1. **Chip on the label line.** Every field row puts its provenance chip at the right end of the label line, as segment
   rows already do (`coil_panel.py` l.193 to l.194). The control line holds the input and its unit only. The chip keeps
   its reserved width when hidden (`setRetainSizeWhenHidden`), so a label wraps the same with or without a chip and
   nothing moves when a chip appears.
2. **Unit column per section.** `_align_units` aligns the unit labels of one section, meaning the group box or the
   untitled section widget that holds the rows, instead of the whole tab. Inside a box every line edit keeps one right
   edge, which is what ruling g 2 and F16 asked for (`docs/phase2/design/m4_review.md` l.136). Edges may differ between
   boxes. A tab with one section (Coil, Phases, Layers) keeps one edge.
3. **Short screw buttons.** `btn-screw-add` reads "Add" and `btn-screw-remove` reads "Remove". Their accessible names are
   "Add screw pattern" and "Remove screw pattern". Each name starts with the visible label, so a speech-input user can
   say the word on the button. That this meets WCAG SC 2.5.3 Label in Name is an `assumption`: the W3C page was not
   reachable from this unit. The buttons sit directly under `screw-table` in the Fasteners box, so the short words keep
   their meaning.
4. **Stacked stack mode.** `param-stack-mode` stacks its two buttons, one per line, at the row's width. Both choices
   stay visible, which a combo box would hide. Up and Down move between them like Left and Right.

Why this and not the other options. The principle is experience first. Measured on D08 at 960 x 540 (`verified` by
running):

| Option | Board body / viewport | Verdict |
|---|---|---|
| main b977621 | 327 / 258 | cut |
| Unit column per section only | 291 / 258 | cut (combo and buttons) |
| Chip on label line, unit column per tab, short buttons | 258 / 258 | fits with 5 px to spare; the combo sits at its 134 px minimum |
| Chip on label line, unit column per section, short buttons (chosen) | 258 / 258 | fits with 43 px to spare (widest box 197 px of 240); `param-rotor-kind` is 186 px wide |

The 5 px option breaks on the first longer choice text, so it is rejected. A horizontal scroll bar is ruled out by
REQ-N-15. Splitting `W/(m²·K)` over two lines reads as two units and is rejected. Moving fields to another tab does not
change the width of a row.

Cost. Forms grow taller, because a label line with a chip is as tall as the 24 px chip (`CHIP_PX`, `inferred` from
`coil_panel.py` l.53). The Board body
on D08 at 960 x 540 grows from 2287 px to 2543 px, and the Coil body from 862 px to 942 px (`verified` by running). Panels
already scroll vertically, as REQ-N-15 allows.

Result with all four parts (`verified` by running). Every tab of every packaged example fits at all three sizes:
`spiral_12c10p_d08`, `spiral_12c14p`, `spiral_12c16p_default`, `wave_16p_example` and `serpentine_16p_example`. No
visible combo box with a choice is narrower than its size hint. `screw-table` has a horizontal scroll bar maximum of 0.
No visible label is narrower than its minimum size hint.

### Changes for Agent 3

- `coil_panel.py` l.194: always add the chip to `head`.
- `FieldPanel._align_units`: group the unit labels by `editor.parentWidget()` and align each group.
- `strings/design.py` l.265 and l.266: "Add" and "Remove". Set the two accessible names in `board_rotor_panel.py`.
- `Segment` gains a vertical layout, used only for `param-stack-mode`.
- `tests/ui/qt_design/test_ruling_g.py` l.106 to l.115: collect the line edit right edges per section, not per tab.
  This is a deliberate rule change, not a test relaxation: the test still fails when two rows of one box differ.

screens.md conventions and the rows `param-stack-mode`, `btn-screw-add` and `btn-screw-remove` carry this ruling
(revision 2026-10-17, U-S12).

### Acceptance (offscreen, Qt test)

| Id | Steps | Pass |
|---|---|---|
| N15-1 | `tests/ui/qt_shell/test_n15_inspector_fits.py`: remove the strict xfail, add (1920, 1080) and parametrize over the five packaged examples. | `wider == {}` for all 15 cases. |
| N15-2 | Same windows. For every visible `QComboBox` in an inspector tab with a current item, compare `width()` with `sizeHint().width()`. | Never narrower. |
| N15-3 | D08 at 960 x 540. For each visible `FieldEditor` with a shown chip, compare the chip's top with the input's top, mapped to the panel. | The chip lies above the input, on the label line. |
| N15-4 | `test_ruling_g.py` g2 test with per-section edges. | One right edge per section; labels above controls; chips `CHIP_PX` tall. |
| N15-5 | Serpentine example, Layers tab at 960 x 540. | `param-stack-mode-single` lies above `param-stack-mode-one_board_per_phase`; both are visible; the body fits. |
| N15-6 | Board tab. | `btn-screw-add` text "Add", accessible name "Add screw pattern"; `btn-screw-remove` text "Remove", accessible name "Remove screw pattern". |
| N15-7 | The existing UX-AC-17 and N-24 tests. | Pass unchanged: every `<id>-unit` is visible and in the accessible description (REQ-N-24). |

## (b) DEF-US11-04: Up, Down and Shift stepping in numeric fields

### Decision

In a numeric field, Up adds one step and Down subtracts one. Shift+Up and Shift+Down move ten steps
(`design_spec.md` section 10, `screens.md` conventions). A step is an uncommitted edit, like typing. It previews after
300 ms and commits on Enter, Tab or leaving the field.

Stepping applies to every field row `QLineEdit` whose `FieldSpec.value_type` is FLOAT or INT, and to the two stack-up
generator inputs. That is 57 widget ids in `FIELDS` outside the four tables (`verified` by listing). It does not apply to
`param-design-name`, combo boxes, segments, check boxes or table cells. In a table, arrow keys move between cells
(`design_spec.md` section 10, row "Toolstrip, tabs, tables").

### Step per field

The step comes from `FieldSpec.step` (`src/embodic/model/fields.py` l.81 and the `_ROWS` table l.104 to l.274,
`verified` by reading), in the unit the form shows. Every numeric row has a step except six. This unit decides those, as
`assumption`:

| Field | Step (Shift: ten steps) | Why |
|---|---|---|
| `param-first-coil-angle`, `param-outline-rotation`, `param-bore-rotation`, `param-pair-rotation`, `param-screw-angle-offset` | 1° (10°) | The form shows degrees; the table stores radians and gives no step. |
| `param-screw-hole-diameter` | 0.1 mm (1 mm) | The same step as `param-terminal-drill` (`fields.py` l.174). |
| `param-copper-weight` (helper, no `FieldSpec`) | 0.5 oz (5 oz) | No source in the repository gives a step. |
| `param-board-thickness` (helper, no `FieldSpec`) | 0.1 mm (1 mm) | No source in the repository gives a step. |

Request to the field-table owner through Fable: write these steps into `_ROWS`, and change the `step` comment to "Up
and Down increment in the unit the form shows". The six rows then come from the table like the rest.

### Arithmetic and bounds

The new value is the number in the field plus or minus n × step, with n = 1 or 10. It is written with `display_text`
(12 significant digits, `session.py` l.395 to l.404), so 0.1 + 0.2 shows "0.3". A step does not snap to a multiple of
the step: 11.47 + 0.5 gives 11.97.

Bounds come from `Limits`. The sign is validity: POSITIVE means above 0, NON_NEGATIVE means 0 or more. `low` and `high`
are the supported range and include their ends (`src/embodic/model/validate.py` l.111 to l.136, `verified` by reading).
Angles compare in degrees, so ±2π rad is ±360°. A bound is `low`, `high`, or 0 for NON_NEGATIVE.

1. If the result is valid and in range, the field shows it.
2. If not, and a valid bound lies strictly between the current number and the result, the field shows the bound.
   Example:
   `param-coil-gap` (NON_NEGATIVE) at 0.02 mm, Down gives 0.
3. If not, the field does not change. Example: `param-r-inner` (spiral, POSITIVE, no `low`) at 0.3 mm, Down gives 0.3.
   `param-dc-link` (POSITIVE, `low` 0) at 0.5 V, Down gives 0.5, because 0 V is not valid.
4. A number already outside the range moves to the nearest bound on a step toward the range. A step away from the
   range does not change it.

A step never writes a message. Messages still appear at commit (screens.md "Validation runs on commit").

### Text that is not a number

A step reads the text in the field, typed or committed. If `parse_text` gives no finite number (empty, "-", "1e",
"12,5", "abc", "nan"), Up and Down change nothing and the text stays. An empty optional field (spiral `param-turns`
means "Maximum", `param-dc-link` means no estimate) stays empty.

### The keys are always consumed

Up and Down in a numeric field are accepted even when the value does not change. Today Down in `param-r-inner` scrolls
the inspector by 20 px and leaves "11.47" unchanged (DEF-US12-02, `verified` by running the app).

### How a step meets the 300 ms rule

The view writes the step result with `selectAll()` and `insert(text)`, not `setText`. An offscreen probe of a plain
`QLineEdit` showed why (`verified` by running): `insert` emitted `textEdited("12.47")` and left `isModified()` True,
`setText` left it False, and Ctrl+Z in the line edit brought back the text from before the step.

- `textEdited` starts or restarts the one 300 ms timer of `fix_wave_f1.md` (a). A held key auto-repeats, so each repeat
  restarts it, and one preview runs 300 ms after the last step. That is row 2 of the f1 contract table.
- `_show_value` keeps a focused, modified text (`coil_panel.py` l.295), so a preview result does not overwrite the
  stepped text. With `setText` the arriving result would put the committed value back.
- Enter, Tab and leaving the field commit at once. Esc puts back the committed text and drops every uncommitted step.
- A step cancels the preview of the same field in flight, as a keystroke does (f1 (a), "How the timer meets the
  worker", item 1).
- The stack-up generator inputs have no preview (f1 (a) table). A step changes their text; `editingFinished` commits.
- For UX-AC-22 a step counts as a keystroke.

### Acceptance (offscreen, Qt test)

Use `make_shell` with its counting `compute_fn`. Load D08, wait for the first result, clear the call list. Field
`param-r-inner` holds 11.47 mm.

| Id | Steps | Pass |
|---|---|---|
| S-1 | Focus `param-r-inner`, press Up. | Text "11.97". No compute call within 250 ms; one call 300 ms ± 50 ms after the key, with r_inner 11.97 mm. Undo stack unchanged. `tab-coil` vertical scroll value unchanged. |
| S-2 | Press Shift+Down from 11.47. | Text "6.47". |
| S-3 | Press Up five times with `QTest.keyClick` at 50 ms, then wait 600 ms. | Text "13.97". Exactly one compute call. |
| S-4 | Press Up, then Return. | Undo stack grows by one; the chip reads `user`; the committed value is 11.97 mm. |
| S-5 | Press Up twice, then Esc. | Text "11.47"; no undo entry; focus stays in the field. |
| S-6 | Type "0.02" into `param-coil-gap`, press Down. Type "0.3" into `param-r-inner`, press Down. | "0" and "0.3". |
| S-7 | Type "0.07" into `param-air-gap` (low 0.05), press Down twice. Type "60" (high 50), press Up, then Down. | "0.05" after both Downs. "60" after Up, "50" after Down. |
| S-8 | Type "abc" into `param-r-inner`, press Up. Clear the field, press Up. | "abc", then "". No compute call. |
| S-9 | Read the text t of `param-first-coil-angle`, press Up, then Return. | Text is t + 1; the committed value is t + 1 degrees in radians. |
| S-10 | Press Up in `param-poles` (10). | "12". |
| S-11 | Press Down on `param-rotor-kind`. Add two patterns with `btn-screw-add`, select a cell of the first row and press Down. | The combo commits one choice (N02-8). The table moves to the next row and no value changes. |
| S-12 | Press Up in `param-board-thickness`, wait 600 ms, then press Return. | No compute call before Return; the thickness rises by 0.1 mm after it. |

## (c) UX-AC-22 applied

`docs/phase2/design/acceptance_criteria.md` now holds the UX-AC-22 text of `fix_wave_f1.md` (a), with a revision note
dated 2026-10-17 (U-S12). `docs/phase2/design/screens.md` carries (a), (b) and DEF-US12-03 under the same date: the
field-row convention, the stepping convention, the `param-stack-mode` and screw button rows, and the new
`param-board-thickness-error` row.

## Defects found

| Id | Severity | Defect | Reproduce | Status |
|---|---|---|---|---|
| DEF-US12-01 | major | The serpentine Layers tab is 306 px in a 258 or 298 px viewport at every size, and the serpentine Coil tab is 262 px in 258 at 960 x 540, so both are cut at the right edge (REQ-N-15). `param-stack-mode` needs 252 px; the `param-active-style` combo row needs 226 px. The N-15 test loads D08 only. | Load `serpentine_16p_example`, resize to 960 x 540, compare `panel.widget().width()` with `panel.viewport().width()` for `tab-layers` and `tab-coil`. | `verified` by running on b977621. Fixed by (a), parts 1 and 4; N15-1 covers it. |
| DEF-US12-02 | minor | Up or Down in a numeric field scrolls the inspector by 20 px and changes nothing. | Load D08, focus `param-r-inner`, press Down, read `tab-coil` `verticalScrollBar().value()`: 0 then 20. | `verified` by running. Fixed by (b). |
| DEF-US12-03 | minor (docs) | `screens_coverage.py` exited 1: "UI code sets an objectName no screens.md table defines: param-board-thickness-error". The row was also missing from the main checkout's screens.md. | Run `docs/phase2/design/checks/screens_coverage.py` from the repository root. | `verified` by running. Fixed here: screens.md section 5 defines the row; the check now prints "no findings" and exits 0. |

## Requests to other owners (through Fable)

- Agent 3 builds (a) and (b) and runs every acceptance row above.
- The field-table owner adds the six steps of (b) to `_ROWS` and rewords the `step` comment.
- Agent 6 adds `serpentine_16p_example` and the other packaged examples to the UI-09 rows of REQ-N-15.

## Open questions for Fable

- Q1. "Add" and "Remove" replace the U-S4f ruling i labels "Add pattern" and "Remove pattern". The alternative keeps
  the labels and stacks the two buttons, which costs one more line. Default used: the short labels.
- Q2. Should a step snap to a multiple of the step (11.47 then 11.5)? Default used: no snap, so a step always moves by
  exactly the step shown in the shortcut list.
