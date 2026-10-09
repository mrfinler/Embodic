Prepared by: Agent 1 (UX/UI Expert Designer) - model: claude-opus-5-5; sections 4 and 5: claude-sonnet-5-5 (U-S4f)

# Second M4 design review and rulings (U-S4e)

Date 2026-10-09, on main fd190c1. Reviewed: the 8 shots in `/mnt/user-data/outputs/m4c3/`, the 9 in
`/mnt/user-data/outputs/m4f/`, and my own grabs on fd190c1 in `/mnt/user-data/outputs/s4e/`
(`tools/design/layout_probe.py --fonts --shots`). A finding is `verified` by looking at the shot named, or by the probe
output quoted, unless it says otherwise. Rulings change `screens.md`, `design_spec.md`, `acceptance_criteria.md` and
`screenshot_checklist.md` (revision 2026-10-09 (U-S4e)).

The m4c3 and m4f shots, except `shell_fonts_light.png`, render in the fallback font: no capture lever calls
`register_fonts` (`verified`, `grep -rn register_fonts tests/ui src/embodic/ui/app.py`). The probe measures both.

## 1. Review table

| # | Screen (shot) | UX-AC / REQ | Result | Finding |
|---|---|---|---|---|
| R1 | Canvas D08, light and dark | UX-AC-05, UX-AC-27 | pass | 12 labels "A1+" to "C4+" with U+2212; legend with bar, eye swatch and name; eye fills. |
| R2 | Canvas serpentine | UX-AC-27 | pass | "A", "B", "C" four times each. |
| R3 | Canvas wave, fit zoom | UX-AC-27, UX-AC-05 | finding, moderate | Every label reads "+": placement skipped every other belt, and the belts alternate sign (the 3x shot shows "A−", "B−", "C−"). Ruling h. |
| R4 | Canvas wave, 3x | UX-AC-27 | pass | Labels of all three phases with both signs in view. The open question (a phase with copper in view but no label) is ruling h. |
| R5 | Layers tab, D08 | UX-AC-21, REQ-N-15 | finding, moderate | Kind elides to "Cop…" and "Diel…"; Rotation is cut. With Inter at 327 px the five columns need 315 px of a 297 px viewport (probe). Ruling c. |
| R6 | Examples gallery | UX-AC-03 | finding, major | The serpentine title names Xcoil (strict xfail). Titles repeat "Example:", and "(default)" reuses the provenance chip word. Ruling g. |
| R7 | Examples gallery, selected item | UX-AC-08, WCAG 1.4.3 | finding, moderate | Note text #666666 on the #151515 selection measures 3.18:1 (needs 4.5:1, pixels read from the shot). Ruling h. |
| R8 | New design | UX-AC-13, WCAG 1.4.11 | pass | Topology buttons show icon and boundary (F14 closed). |
| R9 | Greyscale SVG v2, D08 | UX-AC-05, REQ-N-14 | pass | 12 labels with halos, clipped eye hatches, legend, footer intact. |
| R10 | Colour SVG v2, wave | UX-AC-05 | pass | Belt labels alternate sign; legend; footer intact. |
| R11 | PDF v2 page 1 | UX-AC-18, P1 | pass, with finding minor | µH, mΩ, mV·s/rad print. Headings are faux bold (ruling e2); number and unit use a full space (ruling e1). |
| R12 | PDF v2 page 4 | UX-AC-05 | pass | Greyscale labels and eyes. Label size on paper `not tested`. |
| R13 | Rail at 960 x 540 | UX-AC-21 | finding, major | The rail tab clips nothing, but the canvas is 112 px tall (probe: canvas/results = [112, 276]). Ruling b. |
| R14 | Rail at 1280 x 800 | UX-AC-21 | finding, major | Canvas 124 of 648 px; after a resize the ring stays 40 px wide (probe shot `d08-layers-results_1280x800.png`). Rulings b and h. |
| R15 | Results card grid | UX-AC-21 (DEF-1) | finding, moderate | Fits at 1280 with Inter; scrolls sideways 46 px at 960 x 540 (probe). Ruling d. |
| R16 | DRC tab, 1280 and 960 | UX-AC-21, REQ-N-15 (DEF-2) | finding, major | Measured is cut, Required and Layer are off screen. The seven columns need 724 px of a 564 px viewport at 1280 (probe). Ruling d. |
| R17 | Shell with fonts | design_spec 4 | finding, moderate | Weight 600 is lost: "Key results" and "Issues" render at body weight. The inspector tab bar fits at 327 px but scrolls at 300 px with Inter (probe). Rulings e2 and h. |
| R18 | Status bar, serpentine and wave | screens 14 | finding, minor | `st-counts` reads "3 coils" and "96 coils" for topologies without coils. Ruling h. |
| R19 | Toolstrip, every shot | UX-AC-09 | finding, moderate | Open is still disabled (F21, carried). |

19 rows: 8 pass (R11 with a minor finding), 11 findings (4 major, 6 moderate, 1 minor).

## 2. Rulings

a. Principle model-the-domain (one table row per name). `screens.md` 14a declares the 26 names with the part each
names; none needed a rename. `screens_coverage.py` exits 0.

b. Principle experience-first (the canvas is the thing being designed). `design_spec.md` 5: canvas 60 %, results 40 %,
set explicitly; minimums 240 px and 180 px; under 620 px client height the canvas becomes the first results tab,
"Drawing"; the canvas share is stored per user as a fraction. UX-AC-21.

c. Principle model-the-domain (a pair spans two layers, so it is its own row). `screens.md` 4 and 5: `layer-list`
keeps Layer, Kind, Thickness; new `pair-list` holds Pair, Layers, Rotation, Delete and the series-group menu.
`screw-table` keeps Size, Count, Pitch radius; new `param-screw-fit` and `param-screw-angle-offset` join the hole
diameter field. Inspector widths stay 300 and 340 px (design_spec 5). UX-AC-21.

d. Principle experience-first (the numbers decide a DRC fix). `screens.md` 7: glyph, Message (stretch, at least
200 px, two lines), Measured (mm), Required (mm), Layer; code and severity word go to the tooltip and accessible
text. `screens.md` 6: card columns from the viewport width after the scroll bar, minimum 280 px.

e. Principle experience-first. e1: U+00A0 between number and unit in every single string; never drop the space. e2:
bundle static Inter Regular and SemiBold (same release, OFL), remove the variable file; the PDF embeds the same two.
`design_spec.md` 4.

f. Principle laziness-protocol (one line, not a footer per page). One colophon line ends the PDF. OFL condition 5 keeps
documents outside the licence; the condition 2 reading of a whole embedded file stays with Agent 5. `design_spec.md` 4.

g. Principles laziness-protocol (one source) and experience-first. Edit the five `example.title` values in the files
rather than add a `display_title` table: "Spiral, 12 coils, 16 poles", "Spiral, 12 coils, 14 poles",
"Spiral, 12 coils, 10 poles (D08)", "Serpentine, 16 poles", "Wave, 16 poles, involute". No "Example", no
"default", and the wave title drops "2 turns" because the field reads "Slots per phase belt". UX-AC-03.

h. Principle experience-first. Forced labels per phase and sign; a label in view for every phase in view; leaders stay
inside the view; fit zoom survives a resize (`design_spec.md` 3.3, UX-AC-27). A selected gallery item draws title and
note in `text-inverse` (UX-AC-08; no colour value changes). `st-counts` names coils for spiral only and reads
"3 phases" for serpentine and wave. The inspector tab bar must fit at 300 px with Inter: U-M4e first lowers the
inspector tab padding in the template to 8 px a side and verifies with `layout_probe.py --fonts`; if it still
scrolls, the tab becomes "Board" with the group boxes unchanged. Captures register the fonts.

## 3. Change requests

| Unit | # | Request | Ruling |
|---|---|---|---|
| U-M4e | 1 | Vertical split of `centre-split` and the compact-height "Drawing" tab; store `layout/canvas_share`. | b |
| U-M4e | 2 | Start widths 340 and 360 px at 1280 (327 and 347 today). | c |
| U-M4e | 3 | `pair-list` split out of `layer-list` (Delete, series-group menu, via tooltip, rotation chip, `param-pair-rotation` selection); Kind in full. Through Fable: `FieldSpec.widget_id` of the pair pointers to `pair-list`. Flip the layer-list xfail to a pass. | c |
| U-M4e | 4 | Screw table of three columns plus `param-screw-fit` and `param-screw-angle-offset`; through Fable, `widget_id` of the two pointers. Flip the screw xfail. | c |
| U-M4e | 5 | DRC column budget; card grid columns from the viewport after the scroll bar (DEF-1, DEF-2). | d |
| U-M4e | 6 | U+00A0 between number and unit; flip the two U+202F xfails to assert U+00A0. | e1 |
| U-M4e | 7 | Static Inter Regular and SemiBold bundled, variable file removed, FONTS.md hashes; PDF embeds both; Agent 5 updates EV-106. | e2 |
| U-M4e | 8 | PDF colophon line. | f |
| U-M4e | 9 | Retitle the five example files; flip the UX-AC-03 xfail; scan each example's exported JSON. | g |
| U-M4e | 10 | Gallery selection text in `text-inverse`; `st-counts` wording; inspector tab bar fit; `register_fonts` in every capture lever and the UI test fixtures; recapture S36 to S38. | h |
| U-M4e | 11 | Enable Open (F21, carried from U-S4d). | carried |
| U-M4c-4 | 1 | Forced labels per phase and sign; in-view label per phase; leaders inside the view; fit kept through resize. | h |

## 4. Verification of the change requests (U-S4f)

Date 2026-10-09, on main 9776555. Reviewed: the 8 shots of U-M4e-1 in `/mnt/user-data/outputs/m4e1/`, taken by
`tests/ui/qt_shell/capture_u_m4e.py`. Numbers come from `checks/shot_measure.py`, which reads pixels. The PDF is not in
that folder, so I ran the same lever into a scratch folder and read the file with `pdffonts` and `pdftotext`. A finding is
`verified` by looking at the shot named or by the output quoted. What a still image cannot show is `not tested`.

```
$ QT_QPA_PLATFORM=offscreen .venv/bin/python docs/phase2/design/checks/shot_measure.py /mnt/user-data/outputs/m4e1
1280 x 800 panes: {'inspector': 340, 'rail': 360}, canvas share 0.601 (target 0.59 to 0.61)
gallery selected title: background (21, 21, 21), text (255, 255, 255), contrast 18.26:1 (needs 4.5:1)
gallery selected note: background (20, 20, 20), text (255, 255, 255), contrast 18.42:1 (needs 4.5:1)
gallery unselected note: background (255, 255, 255), text (102, 102, 102), contrast 5.74:1 (needs 4.5:1)
no findings
$ pdffonts u-m4e_report_d08.pdf
Inter-Regular, JetBrainsMono-Regular, Inter-SemiBold: CID TrueType, embedded yes, subset no (3 fonts)
```

### 4.1 Screens

| # | Screen (shot) | UX-AC | Result | Finding |
|---|---|---|---|---|
| V1 | Canvas 60/40, D08, 1280 x 800 (`canvas-60-40`) | UX-AC-21, 05, 27 | pass | Inspector 340, rail 360, canvas page 0.601 of the centre height (392 of 652 px), results 259 px. 12 labels with sign, legend whole, ring fills the canvas. `st-counts` reads "12 coils". |
| V2 | Drawing tab, light, 960 x 540 | UX-AC-21 | pass | "Drawing" is the first and current tab; canvas 314 px tall (rows 203 to 517); inspector 300 px with "Coil Phases Layers Board" and no scroll arrows; seven centre tabs fit. |
| V3 | Drawing tab, dark, 960 x 540 | UX-AC-21, 08 | pass | Same geometry in the dark theme; focus ring is white. Label contrast on the dark canvas `not tested`. |
| V4 | Layers tab, D08 and 12c14p, 960 x 540 | UX-AC-21 | finding, minor | `layer-list` shows Layer, Kind ("Copper", "Dielectric" in full), Thickness; `pair-list` shows Pair, Layers, Rotation. No sideways bar. F1 and F2 below. |
| V5 | Board tab and DRC tab, wave, 1280 x 800 | UX-AC-21, 27, 08 | finding, moderate | `screw-table` has three columns; fit and hole diameter fields show; the angle offset field is below the fold. DRC shows glyph, Message (two lines), Measured, Required, Layer with numbers right-aligned in mono; no sideways bar. Wave fit zoom shows A+, B+, C+ and A−, B−, C− with leaders inside the view. F1 and F3. |
| V6 | Gallery, second item selected | UX-AC-08, 03 | finding, major | Selection text is 18.3:1 (pass). The five titles are the old ones: "Example: 16-pole serpentine (Xcoil default)", "Example: UGent D08 12-coil 10-pole spiral", "Example: 12-coil 14-pole spiral", "Example: 12-coil 16-pole spiral (default)", "Example: 16-pole wave winding (involute, 2 turns)". UX-AC-03 fails on "Xcoil", "Example", "default" and the institution name. Ruling g is request 9. |
| V7 | PDF page 1 | UX-AC-18, 05 | pass | µH, mΩ, mV·s/rad, Ω, η, δ, ΔT, A/mm² and √W print; headings read as SemiBold, values in JetBrains Mono. |
| V8 | All eight shots | UX-AC-11, checklist Focus | finding, moderate | The 2 px focus ring sits on the toolstrip Home tab in every shot. The Focus cell of S36 to S38 (`pair-list`, `fig-canvas`) is unmet. F4. |

8 rows: 4 pass, 4 findings (1 major, 2 moderate, 1 minor). Section 4.2 lists the six distinct findings.

### 4.2 Findings

| Id | Severity | Finding | Fix | Unit |
|---|---|---|---|---|
| F1 | minor | `layer-list`, `pair-list` and `screw-table` end in an empty header cell and leave a blank band under the last row (crops of V4 and V5). | Ruling j: the last column takes the remaining width. | UI worker |
| F2 | minor | The `example` chip in `pair-list` draws a solid black border and black text. `_value_with_chip` (`layer_panel.py` lines 330 to 343) sets `class` but not `provenance`, so `QLabel[class="prov-chip"]` (`theme_template.qss` line 108) applies and the dashed `example` rule (line 109) does not. `verified` by reading code and looking. | Set the `provenance` property from the row's chip, as `coil_panel.py` line 301 does. | UI worker |
| F3 | moderate | "Add pattern" and "Remove pattern" read as plain text. They are `QToolButton`, whose rule has a transparent border (`theme_template.qss` line 8). UX-AC-08 asks 3:1 for control boundaries. | Ruling i. | UI worker |
| F4 | moderate | Focus ring on the Home tab in all shots. | Checklist rule "Focus" (`screenshot_checklist.md`). | U-M4e-2 |
| F5 | major | Request 9 is not in this build. | U-M4e-1b carries it (D-041a). | U-M4e-1b |
| F6 | minor | At 1280 the rail says "No input issues" twice, once in `rail-inputs` and once in the empty `issues-list`. Section 6.1 specifies both texts, so this is a proposal only: hide `issues-list` and its title while `rail-inputs` passes. No spec text changed. | Fable decides. | none yet |

### 4.3 Status of the change requests 1 to 12

| # | Request | Status | Evidence |
|---|---|---|---|
| 1 | Vertical split, Drawing tab, stored share, fit through resize | done for what a shot shows | `verified`: share 0.601, minimums met, "Drawing" first at 960 x 540. `not tested`: `layout/canvas_share` restored after restart, fit after a resize (S41). |
| 2 | Start widths 340 and 360 | done | `verified` from pixels: 340 and 360 at 1280, 300 at 960. |
| 3 | `pair-list` split out | done for layout | `verified`: two tables, Kind in full. `not tested`: Delete, series-group menu, via tooltip, `param-pair-rotation` selection, `widget_id`. F2 open. |
| 4 | Screw table of three columns and two fields | partly seen | `verified`: three columns, fit and hole diameter visible. `not tested`: `param-screw-angle-offset` (below the fold), `widget_id`. F3 open. |
| 5 | DRC column budget and card grid | done at 1280 | `verified`: DRC columns fit without a sideways bar; at 1280 the card grid shows one column that ends inside the scroll bar (`inferred`: two columns need 568 px, the viewport has about 550). `not tested`: card grid at 960 and 1600 x 900, DRC at 960. |
| 6 | U+00A0 between number and unit | `not tested` from shots | A still image and `pdftotext` cannot tell U+00A0 from a space. Source line `UNIT_SPACE = chr(0x00A0)` in `results/formatting.py` line 22 is `verified` by reading. Agent 4 tests it. |
| 7 | Static Inter, no variable file, PDF embeds both | done | `verified`: UI headings and table headers render at SemiBold; `pdffonts` lists Inter-Regular, Inter-SemiBold, JetBrainsMono-Regular, embedded, no variable font. `not tested`: `FONTS.md` hashes, EV-106 (Agent 5). |
| 8 | PDF colophon line | done | `verified`: `pdftotext` finds "Set in Inter and JetBrains Mono, SIL Open Font License 1.1." once, on page 3 after the last table, and on no other page. |
| 9 | Retitle the five examples | not done in this build | `verified` by looking at V6. U-M4e-1b. |
| 10 | Gallery text, `st-counts`, tab bar fit, fonts in levers, recapture S36 to S38 | done, recapture partial | `verified`: 18.3:1 selection text; "12 coils" (spiral) and "3 phases" (wave); four inspector tabs fit at 300 px; all six levers call `qt_application()`. `not tested`: "3 boards" for a stack. Recapture: S36 and S38 shots exist, S37 only inside the Board tab shot; Focus unmet (F4). |
| 11 | Enable Open | seen enabled | `verified`: Open draws at text colour while Redo is grey, in every shot. `not tested`: opening a file. |
| 12 | Label rules of ruling h | done at fit | `verified`: D08 shows 12 labels; wave shows both signs of each phase. `not tested`: 3x zoom, a label per phase in view, resize (S07, S41). |

Request 12 is also change request U-M4c-4 1 of section 3.

## 5. Rulings from the verification (U-S4f)

i. Principle experience-first (a control shows its boundary). `screens.md` 5: `btn-screw-add` and `btn-screw-remove` are
`QPushButton` with the secondary boundary of `btn-drc-locate`. UX-AC-08. The objectNames stay.

j. Principle experience-first (get the details right). `screens.md` 4 and 5: the last column of `layer-list`, `pair-list`
and `screw-table` takes the remaining width, so no header cell is empty. UX-AC-21.

## 6. Change requests from the verification

| Unit | Request | Finding or ruling |
|---|---|---|
| UI worker before the recapture (Fable names it) | `provenance` property on the `pair-list` chip; `QPushButton` for the two screw buttons; last-column stretch in the three tables. Test each: chip style, button class, empty header cell. | F2, i, j |
| U-M4e-1b | Retitle the five examples, flip the UX-AC-03 xfails. | F5, g |
| U-M4e-2 | Take the 41 rows of `screenshot_checklist.md` with focus set, fonts registered through `qt_application()`, and the 16 missing levers written. Show `param-screw-angle-offset` in S20. Add the last text page of the PDF and `pdffonts` to S40. Run `shot_measure.py` on S36, S38, S39. | F4, V5, V7 |
| Agent 4 | Test what is `not tested` above: requests 1 (stored share, resize), 3 (Delete, menu, tooltip), 4 (`widget_id`), 5 (960 and 1600 x 900), 6, 10 (stack count), 11, 12. | section 4.3 |
| Agent 5 | EV-106 after the static fonts (request 7). | request 7 |
