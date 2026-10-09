Prepared by: Agent 1 (UX/UI Expert Designer) - model: claude-opus-5-5

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
