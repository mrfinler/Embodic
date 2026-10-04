Prepared by: Agent 1 (UX/UI Expert Designer) - model: claude-opus-5-5

# UX acceptance criteria v1 (UX-AC, Phase 2 desktop)

Date 2026-10-04. Replaces the Phase 1 list in `docs/phase1/design/design_handoff_for_agent3.md` section 4. Phone and
KiCad criteria are dropped (D-009, D-010). Each criterion names a test that drives the PySide6 app (offscreen
`QT_QPA_PLATFORM=offscreen` is acceptable unless the row says Windows). Agent 6 maps them to requirement ids; Agent 4
writes the independent tests.

| Id | Criterion | How to test |
|---|---|---|
| UX-AC-01 | Every numeric result shows value, unit (or "–" with accessible text "dimensionless"), exactly one trust badge (D-007) and one "n assumptions" tag. | Walk every `res-card-*`: children `-value`, `-unit`, `-badge` (one), `-asm` exist and are visible. |
| UX-AC-02 | Every computed result has an EQ-ID link or an `input`, `derived` or `count` tag, and a "How was this computed" section with equation, inputs with units and provenance, assumptions, limitations, validation and sources. | Expand each `res-<key>-how`; assert the six parts are non-empty. |
| UX-AC-03 | No visible string contains "Xcoil", "KiCad", Thai characters or a personal name. | Collect `text()`, `toolTip()`, `windowTitle()`, `accessibleName()` of all widgets and the exported files; regex scan. |
| UX-AC-04 | Chrome uses only neutral tokens; colour appears only on phase marks, legends, charts and status text. | Parse the loaded style sheet: every hex outside status and phase hooks is a neutral token in `tokens.json`; grab the window in both themes and check non-grey pixels lie inside the canvas, charts, badges or status labels. |
| UX-AC-05 | Phases stay distinguishable without colour in every mode: letter label on every coil, coil-eye fill pattern (tint, 45 degree, 135 degree hatch), chart line style (solid, dashed, dotted), legend. | Render the default example in colour and greyscale; check labels per coil from the scene items and the pen dash pattern per phase. |
| UX-AC-06 | Theme switch: View > Theme and Ctrl+Shift+T switch light and dark without restart, keep the current tab, selection and zoom, rebuild every icon in the new icon colour, and persist the choice. | Switch theme; compare `QApplication.styleSheet()` with `dark.qss`; sample an icon pixel equals `icon_color.normal`; restart reads the saved theme. |
| UX-AC-07 | Greyscale mode: View > Greyscale and G on the canvas switch phases to the greyscale ladder with hatching; the PDF report offers the same mode. | Toggle; sample copper pixel colours equal `phase-*-grey` of the theme. |
| UX-AC-08 | Text contrast is 4.5:1 or more, control boundaries, focus ring and phase strokes 3:1 or more, in both themes. | Recompute `tokens.json` > `contrast_pairs`; no pair below its minimum. |
| UX-AC-09 | Every toolstrip button has an icon, a visible label (or an accessible name when collapsed), and a tooltip "Label (Shortcut). Sentence."; a disabled button's tooltip names why. | Iterate `#toolstrip` QToolButtons; assert `icon()` not null, `toolTip()` matches the pattern, shortcut text equals `design_spec.md` section 6. |
| UX-AC-10 | Keyboard map in `design_spec.md` section 10 works; every command is reachable without a mouse; F6 cycles the regions; single-letter keys act only while the canvas has focus. | `QTest.keyClick` per row; assert the action fired; assert "L" in a text field types "L". |
| UX-AC-11 | Visible focus indicator on every focusable widget (2 px `focus-ring`). | Tab through the window; grab each focused widget; ring pixels equal `focus-ring`. |
| UX-AC-12 | No silent value rewrite: when the engine changes a user value, an inline notice "Changed from X to Y: reason" with Undo appears beside the field and is announced; Undo restores X. Re-typing a default value changes no status (D-007). | Scripted clamp case; assert notice text, then Undo; assert badge and assumption count unchanged after re-typing a default. |
| UX-AC-13 | New-design flow: the app opens on a blank design; required fields start empty; **Create design** stays disabled and its tooltip lists missing fields until all required fields are valid; nothing computes before that. | Start app; assert empty fields, disabled button, no compute call (spy on the worker). Fill fields one by one; button enables after the last. |
| UX-AC-14 | Examples load with `example` chips; editing a field turns its chip to `user`; marking measured needs a named source. | Load an example; check chips; edit; check chip; "Mark as measured" without a source is refused. |
| UX-AC-15 | Required-field and range validation: invalid input sets `invalid=true`, shows the message under the field and in Checks; the last valid geometry and results stay dimmed with "Last valid" stamps. | Enter out-of-range values per field; assert property, message text from `screens.md`, stale stamps. |
| UX-AC-16 | Fields that do not apply to the active topology or option are hidden; a temporarily blocked field is disabled with its reason. | Config matrix: three topologies x end style x rotation mode x stack mode; assert visibility per `screens.md`. |
| UX-AC-17 | Every input shows its unit and the unit is in the accessible description. | For each `param-*` with a unit, assert `<id>-unit` visible and `accessibleDescription()` contains it. |
| UX-AC-18 | Export with DRC failures requires a confirmation that lists the failures; focus starts on Cancel. Exported files carry embodic version, engine version and parameter hash. | Scripted export; assert dialog, focus, file headers. |
| UX-AC-19 | Charts: one unit per y axis; legend and direct labels for two or more series; data table available; crosshair reachable by keyboard. | Chart audit per `chart-*`. |
| UX-AC-20 | Counts show as integers; compare deltas use sign plus glyph, never red or green. | Formatting test on `compare-table`. |
| UX-AC-21 | Window minimum 960 x 540 px; two panes from 960 px, three panes from 1280 px; no clipped toolstrip button at 960 px (small buttons may collapse to icons with accessible names). | Resize to 960, 1280, 1920 px; assert layout and that every toolstrip button is visible or in the overflow. |
| UX-AC-22 | Recompute: results update within 300 ms of the last edit for the default example, or show "Updating" with previous values dimmed. | Timing test (`unresolved` target until the Python engine is measured). |
| UX-AC-23 | No animation runs by default; current-flow arrows are static. | Inspect timers and `QPropertyAnimation` instances after start. |
| UX-AC-24 | High-DPI and Windows: the UI renders without clipped text at 100 %, 150 % and 200 % scaling and in Windows high contrast. | Manual check on Windows (`not tested` until Phase 3). |

Changes from Phase 1: dropped phone (old UX-AC-10 touch targets and the 360 px layout) and KiCad (old UX-AC-16 place,
UX-AC-21 plugin dialog); added theme switch (06), greyscale mode (07), icon tooltips (09), keyboard map (10), new-design
flow and examples (13, 14), required-field validation (15), window layout (21), high-DPI (24). UX-AC-12 keeps the no
silent rewrite rule and adds the D-007 re-typing check.
