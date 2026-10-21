Prepared by: Agent 1 (UX/UI Expert Designer) - model: claude-opus-5-5

# embodic design specification v1 (Phase 2, PySide6 desktop)

Date 2026-10-04, revised 2026-10-09 (U-S4d: sections 3.3, 3.4, 5 and 8 follow the rulings of `m4_review.md`),
revised 2026-10-09 (U-S4e: sections 3.3, 4 and 5 follow rulings b, e, f and h of `m4_review_2.md`),
revised 2026-10-12 (U-S4h: sections 3.1, 5 and 8 follow rulings m and n of `m4_review_2.md` section 8),
revised 2026-10-20 (U-S16: section 3.3.1 adds the layer cue and the land shapes, DEF-UV16-02 and DEF-UV16-03),
revised 2026-10-22 (U-S18, D-094b: section 10 drops Ctrl+, and section 6 drops the Help button Settings, because no
settings window is in scope and the ruling keeps keys that the app does not bind out of the keyboard map).
Supersedes `docs/phase1/design/design_spec_draft.md` for everything Phase 2 builds. Companion files:

- `screens.md` gives every screen with its widget table and state rules.
- `acceptance_criteria.md` lists the UX acceptance criteria UX-AC v1.
- `resources/themes/tokens.json` is the single source. `tools/design/build_themes.py` generates `light.qss`, `dark.qss`,
  the glyphs in `resources/themes/{light,dark}/` and the ThemeTokens files `light.json` and `dark.json`
  (interfaces.md section 11) from it. These are what Agent 3 loads.
- `resources/icons/*.svg`, `ICONS.md` and `_contact_sheet.png` hold the icon set.
- `theme_smoke_light.png` and `theme_smoke_dark.png` are both QSS files rendered by real Qt (PySide6 6.11.2, offscreen).

Every claim carries one status label (standing order 2). A design choice without evidence is `assumption`. Example
numbers in figures are examples.

## 1. Inputs and rulings

| Ruling | Source | Effect on this spec |
|---|---|---|
| PySide6 desktop app, Windows primary | D-010 | Qt widgets, QSS, QSvgRenderer. No HTML. |
| Phase A red, B blue, C green. Light and dark themes. Chrome white, grey, black. Greyscale and hatching mode stays. | D-011 | Section 3. Red and green never carry identity alone. |
| MATLAB-style toolstrip with original monochrome SVG icons | D-012 | Sections 6 and 7. |
| Spiral (primary), serpentine and interleaved wave topologies | D-013 | Topology section in the toolstrip; per-topology field sets in `screens.md`. |
| New-design flow: blank design, the user enters values; team sets are examples | D-014 | `screens.md` section 1. Provenance chips. |
| KiCad out of scope | D-009 | No KiCad screen, icon or string. Phase 1 KiCad ids are withdrawn (section 9). |
| Compact density, British spelling, star default connection, no 3-D view | D-015 | Applied. |
| Result badge is calculation trust; assumptions are a separate count | D-007 | Result card anatomy (`screens.md` section 6). |

## 2. Design principles

| # | Principle | What it means in the UI | Status |
|---|---|---|---|
| P1 | Honest numbers | No number without unit, EQ-ID (or `input`/`derived`/`count` tag), trust badge and "n assumptions" tag. Estimates say "estimate". | assumption (brief rules 3, 5, 6; D-007) |
| P2 | Nothing computes from a blank form | The new design starts empty. Results stay empty until every required field is valid. | user decision D-014 |
| P3 | Show only what applies | A field that does not apply to the active topology or option is hidden. A field that is temporarily blocked by a sibling option is disabled and shows the reason. | assumption |
| P4 | Monochrome chrome, colour for data | Chrome uses the neutral tokens. Colour appears only on phase marks, phase legends and status text. | user decision D-011 |
| P5 | Never colour alone | Phases carry letter labels, line style and coil-eye hatch in every mode. Status carries a glyph and a word. | user decision D-011; verified need (section 3.3) |
| P6 | The machine never silently changes input | Any automatic change shows "Changed from X to Y: reason" with Undo. | assumption (Phase 1 P8) |
| P7 | Keyboard first-class | Every command has a keyboard path. Every toolstrip button names its shortcut in the tooltip. | assumption |
| P8 | Calm density | 13 px body, 32 px controls, one primary button per view. | assumption (D-015 compact) |

## 3. Colour

### 3.1 Neutral and status tokens

Machine-readable values: `resources/themes/tokens.json` > `themes.<theme>.color`. Contrast for all 76 foreground and
background pairs is in appendix A. All pass (`verified`, computed with the WCAG 2.x relative-luminance formula by the
token generator).

| Token | Light | Dark | Use |
|---|---|---|---|
| `bg-app` | `#f7f7f7` | `#0f0f0f` | Window background, disabled field fill |
| `surface` | `#ffffff` | `#171717` | Toolstrip, inspector, results rail, cards, inputs |
| `surface-sunken` | `#efefef` | `#232323` | Hover, table header, EQ chip, inline notice |
| `surface-selected` | `#e4e4e4` | `#2e2e2e` | Selected row, checked tool button, pressed |
| `surface-inverse` | `#141414` | `#f2f2f2` | Primary button, tooltip, verified badge, measured chip |
| `canvas` | `#ffffff` | `#171717` | Geometry view and chart plot area |
| `board-fill` | `#f7f7f7` | `#202020` | PCB fill in the geometry view |
| `divider` | `#dcdcdc` | `#2e2e2e` | Decorative separators only, never a control boundary |
| `grid-line` | `#e6e6e6` | `#2a2a2a` | Chart grid, solid hairline |
| `border-control` | `#858585` | `#7d7d7d` | Every input, combo, checkbox and button boundary; scrollbar handle; badge outline on a stale card |
| `border-strong`, `focus-ring` | `#141414` | `#f2f2f2` | Focus 2 px, checked tool button, selected tab underline |
| `text-1` | `#141414` | `#f2f2f2` | Primary text, icons |
| `text-2` | `#454545` | `#c8c8c8` | Secondary text, tab labels |
| `text-3` | `#666666` | `#a0a0a0` | Hints, units, captions; value, unit and badge text of a stale result card (U-S4h ruling m) |
| `text-disabled` | `#9a9a9a` | `#6e6e6e` | Disabled text and icons (exempt from SC 1.4.3) |
| `text-inverse` | `#ffffff` | `#141414` | Text on `surface-inverse` |
| `status-pass` | `#2f6a47` | `#6fb38a` | Pass glyph and word |
| `status-fail` | `#a6332c` | `#e2776d` | Fail glyph and word, invalid field border |
| `status-warn` | `#875400` | `#d9a440` | Warning glyph and word |

Status colours never appear on the geometry canvas. In the light theme `status-fail` and `phase-a` are only ΔE 6.5
apart (deutan 6.3), so a red DRC marker would read as phase A copper (`verified`, computed). Canvas DRC markers are
drawn in `text-1` with a 2 px `canvas` halo, the `check-fail` glyph and the issue number. Selecting a DRC item dims
copper to 35 %.

### 3.2 Phase colours

| Phase | Light | OKLCH (L, C, h) | vs canvas / board | Dark | OKLCH (L, C, h) | vs canvas / board |
|---|---|---|---|---|---|---|
| A red | `#941328` | 0.43, 0.16, 20 | 8.81 / 8.23 | `#c43b10` | 0.55, 0.18, 36 | 3.40 / 3.09 |
| B blue | `#0032e2` | 0.45, 0.26, 264 | 8.22 / 7.67 | `#005bfc` | 0.54, 0.25, 262 | 3.33 / 3.03 |
| C green | `#579f03` | 0.63, 0.18, 134 | 3.30 / 3.08 | `#0eb16a` | 0.67, 0.16, 156 | 6.42 / 5.83 |

How they were chosen (`verified`, search run in the scratchpad, `phase_search.py`). A grid search over OKLCH kept every
colour inside its hue family (red 20 to 36 degrees, blue 240 to 268, green 132 to 156), inside the validator's
lightness band for the mode, at chroma 0.16 or more so each reads as a named colour, and at 3:1 or more against both the
canvas and the board fill of its theme. Among those it maximised the worst all-pairs protan and deutan ΔE, with the
normal-vision floor of 15 as a hard gate. The search makes green the lightest phase and red the darkest in light mode.
That lightness gap is what keeps red and green apart for deutan readers.

Validator runs (dataviz `validate_palette.js`, `--pairs all`, `verified`):

```
light, surface #ffffff and #f7f7f7: ALL CHECKS PASS. CVD worst #579f03-#941328 ΔE 19.9 (deutan), tritan 16.4,
  normal-vision worst 34.9, contrast all >= 3:1
dark, surface #171717 and #202020: ALL CHECKS PASS. CVD worst #0eb16a-#c43b10 ΔE 12.2 (deutan), tritan 12.5,
  normal-vision worst 31.8, contrast all >= 3:1
```

Colour-blind simulation per pair (OKLab ΔE x100, Machado 2009 severity 1.0, `verified`):

| Set | Pair | Normal | Protan | Deutan | Tritan |
|---|---|---|---|---|---|
| light | A-B | 36.2 | 30.8 | 30.8 | 27.4 |
| light | A-C | 34.9 | 32.9 | 19.9 | 30.7 |
| light | B-C | 44.0 | 38.3 | 39.3 | 16.4 |
| dark | A-B | 39.7 | 34.0 | 35.4 | 32.6 |
| dark | A-C | 31.8 | 25.1 | 12.2 | 36.2 |
| dark | B-C | 35.5 | 32.4 | 31.9 | 12.5 |
| Xcoil v3 (reference) | A-C | 28.9 | 14.3 | 1.4 | 32.8 |

The weakest pair is A-C (red-green) under deuteranopia in both themes. It clears the validator target of 8, but dark
mode has less margin (12.2), and the simulation does not cover anomalous trichromacy at partial severity or thin 1 px
copper at low zoom (`unresolved`, not tested with readers). The non-colour cues below are therefore mandatory in every
mode, not only in greyscale mode.

### 3.3 Mandatory non-colour cues (all modes)

| Cue | Phase A | Phase B | Phase C | Where |
|---|---|---|---|---|
| Letter label | spiral `A1+`, `A2−`; wave `A+`, `A−` per phase belt; serpentine `A` | `B1+` ... | `C1+` ... | Geometry view, SVG and PDF, both modes. Placement rules below. The Labels toggle adds terminal and net labels and never removes a phase label. Minus is U+2212. |
| Coil-eye fill (inside the innermost turn only) | solid tint 10 % | 45 degree hatch | 135 degree hatch | Geometry view, SVG and PDF, both modes, clipped to the eye disc. Hatch never crosses copper, so it cannot be read as a trace (Phase 1 finding). On screen the hatch is a pattern in screen space (about 4 px pitch) so it shows at fit zoom; in files the pitch is 0.4 mm. |
| Chart line style | solid 2 px | dashed 6/3 | dotted 1.5/3 | Back-EMF, torque-speed, compare charts |
| Legend | drawing: solid copper bar in the phase ink, eye swatch, "Phase A"; chart: line sample, "Phase A" | same | same | Always present for two or more phases, on the canvas and in every drawing file. A drawing legend never shows a dashed line, because copper is never dashed. |
| Copper | solid | solid | solid | Copper is never dashed: a dashed trace reads as an open circuit (assumption). While two or more copper layers are visible, the layers below the top visible layer are drawn as outlines (section 3.3.1). An outline is a continuous line, never a dash. |

Machine-readable form: `tokens.json` > `phase_style`.

Label placement (U-S4d ruling b, `assumption` until U-M4c-2 tests it). Labels place in priority order: the first coil
of each phase, then every coil in index order. A label whose box, grown by 2 px, meets a placed label, a terminal pad
or the view edge is skipped; the first label of each phase always places, with a leader outside the ring if its own
spot is taken. Placement reruns after each zoom or resize step, and a skipped label shows in the hover tooltip of its
copper. Serpentine phases get 4 labels at fit zoom, one per quadrant, on the outermost end turn. Files use the fit-zoom
set at page scale. The canvas, the SVG and the PDF take labels and eye discs from one module, so they cannot differ.

Label placement additions (U-S4e ruling h, `assumption` until U-M4c-4 tests them):

- The forced labels are the first label of each phase and sign, not of each phase: A+, A−, B+, B−, C+, C− for wave and
  the first positive and first negative coil of each phase for spiral. At fit zoom the wave example placed every other
  belt label, so all visible labels read "+" while the belts alternate (`verified` by comparing
  `u-m4c-3_canvas_wave_light.png` with the 3x shot, where "A−", "B−" and "C−" show). Serpentine has no sign and keeps
  one forced label per phase.
- Every phase whose copper shows in the view has a label inside the view. When none of its anchors is in the view,
  the label goes on that phase's visible copper nearest the view centre, with no leader.
- A leader and its label box lie inside the view, grown inward by 2 px. When the leader target is outside, the label
  takes the nearest free in-view spot on the same phase's copper.
- The canvas keeps fit zoom through a resize, a splitter drag and a tab switch until the user zooms or pans; Fit (F)
  returns to it. On main fd190c1 a resize after load left the D08 ring 40 px wide in a 598 x 124 px canvas
  (`verified`, `tools/design/layout_probe.py --fonts --shots`).

### 3.3.1 Copper layers and lands in the geometry view (U-S16, DEF-UV16-02, DEF-UV16-03)

The user read D08 as shorted because the view drew L2 and then L1, both opaque, in one ink per phase. Copper on
different layers looked like one piece, although every same-layer gap is at the 0.8 mm rule (U-V16, `verified` there).
The rule below makes the layer of each piece of copper visible. The comparison of four candidates, the renders and the
measurements are in `docs/phase3/design/u_s16_layer_cue.md`.

Layer cue. It applies while two or more copper layers are visible, on every board the view draws. With one visible
layer the view draws that layer solid, as before.

| Rule | What the view draws |
|---|---|
| Order | The visible copper layers in reverse stack order, so the top visible layer is drawn last. The top visible layer is the first visible layer in stack order (L1 unless it is hidden). |
| Top visible layer | Solid, at true width, in the phase ink (section 3.2, or the grey of section 3.4). No alpha. |
| Every visible layer below it | An outline of the copper shape in the phase ink, 1.5 px wide, drawn inside the true edge, so the drawn copper is never wider than the true copper. The inside of the shape is empty: the board and the layers below show through. A shape narrower than 4 px on screen therefore looks solid. The outline follows the union of the layer's copper of one ink, so copper that joins on that layer shows one edge and no seam. |
| Casing | Before each visible layer except the bottom one, a band in `board-fill` 2 px wide on screen around that layer's copper, over the layers already drawn. Copper of a lower layer therefore stops 2 px short of the copper of every layer above it, at any zoom. |
| Widths | The outline, the casing and the 4 px limit are screen pixels at every zoom, like the eye hatch (section 3.3). Copper widths stay model millimetres (UI-03). |
| Colour | The cue adds no colour and changes no lightness. It uses only the phase ink and `board-fill`, so the phase colours, the greyscale ladder of section 3.4 and the deutan lightness gap of section 3.2 are unchanged. Windows high contrast uses the greyscale ladder (`fix_wave_f1.md` (b)), and the cue works there unchanged. |
| Lands | Vias and pads join layers, so the view draws them after all copper, once per land that spans a visible layer, solid, in the colours they have now (`text-3` via, `text-2` pad). The cue never outlines or cases a land. |
| Legend | While the cue applies, the canvas legend adds two rows under the phase rows. Row 1 is a solid bar 20 x 6 px in `text-1` and the text "{layer} on top", where {layer} is the name of the top visible layer. Row 2 is the same bar as a 1.5 px `text-1` outline with an empty inside and the text "Layers below". The rows use `text-1` because they describe layers, not phases. The legend panel grows to fit them. |
| Exports | Unchanged. SVG, DXF and PDF draw each layer separately. |

Why this rule (`verified` by the U-S16 renders, `docs/phase3/design/checks/u_s16/`). Copper on two layers then differs in
form, solid against empty, and a gap separates them. Neither cue depends on hue or lightness, so it reads the same in
colour, in greyscale and for colour-blind readers. The top layer keeps its true width and its own gaps stay clear: the
casing removes the lower copper that filled the 0.8 mm channels of L1 in the user's view. To check a lower layer at
true width, the user solos it with `[` and `]` (section 10) or hides the layers above it. Whether the user reads the
drawing correctly with the cue is `not tested` with users.

Lands (DEF-UV16-03). A pad is drawn as the exporters draw it (`dxf_writer.py` l.139 to 142, `svg_writer.py` l.156 to
159, `report.py` l.255 to 258, `verified` by reading). A pad with `shape` "round" is a circle of diameter `width_mm`.
A pad with `shape` "square", "rect" or "oblong" is the closed shape that `pad_outline(pad)` returns
(`io/exporters.py` l.215), filled as the SVG writer fills it. `pad_outline` already applies `rotation_rad`. A pad with `drill_mm` greater than 0 shows its drill as
a `canvas` disc of diameter `drill_mm` on top, as all three exporters do. Vias keep their pad disc.

### 3.4 Accessibility mode (greyscale and hatching)

Greyscale mode keeps every cue of section 3.3: labels and eye fills are what identify phase and polarity; the grey
ladder is the third cue, never the only one (REQ-N-14, REQ-N-23; legend-only exports do not pass, U-S4d ruling a).

Toggle: View > Greyscale (G on the canvas). It also applies automatically in the PDF report when the user picks
"Greyscale print" and when Windows high contrast is on (`QStyleHints.colorScheme` does not report high contrast; Agent 3
reads `QPalette` and the Windows `HighContrast` setting, `unresolved` until tested on Windows).

| Phase | Light stroke | Contrast on canvas | Dark stroke | Contrast on canvas | Fill and line |
|---|---|---|---|---|---|
| A | `#262626` | 15.13 | `#e0e0e0` | 13.58 | solid tint, solid line |
| B | `#5e5e5e` | 6.48 | `#a8a8a8` | 7.54 | 45 degree hatch, dashed line |
| C | `#8a8a8a` | 3.45 | `#7a7a7a` | 4.18 | 135 degree hatch, dotted line |

Phase A is the strongest step in both themes. Validator `--ordinal` passes both ladders (monotone lightness, adjacent
ΔL of 0.06 or more, light end 3.45:1 and 4.18:1), `verified`.

## 4. Typography

| Role | Family | Licence (status) | Licence file to ship | Sizes |
|---|---|---|---|---|
| UI text | Inter | SIL OFL 1.1, `verified` (https://raw.githubusercontent.com/rsms/inter/master/LICENSE.txt) | `resources/fonts/Inter/LICENSE.txt` | 12 caption, 13 body, 14 section title, 16 dialog title |
| Numbers, units, codes, EQ-IDs | JetBrains Mono | SIL OFL 1.1, `verified` (https://raw.githubusercontent.com/JetBrains/JetBrainsMono/master/OFL.txt) | `resources/fonts/JetBrainsMono/OFL.txt` | 12 chip, 13 field, 20 result value, 24 hero |

- Agent 3 bundles the font files under `resources/fonts/` (outside my write scope) and registers them with
  `QFontDatabase.addApplicationFont` before the style sheet loads. Fallbacks: Segoe UI, then the platform sans; Cascadia
  Mono, Consolas, then monospace. No font is fetched at run time.
- Glyph coverage: µ, Ω, °, − and the middle dot print from the bundled fonts (`verified` by U-M4f with pypdf on the
  D08 report). JetBrains Mono 2.304 has no U+202F (U-M4f, two strict xfails). Status glyphs never depend on the font:
  they are SVG icons (`status-*`, `check-*`).
- Number and unit (U-S4e ruling e1). Every single-string form (PDF, SVG footer, tooltip, Copy trace, status bar) puts
  U+00A0 between a number and its unit: "1.34 µH" never breaks between number and unit, and both bundled fonts have
  the glyph. The space is never dropped, because "1.34µH" reads as one token. In the widgets the value and the unit are
  separate labels (`res-<key>-value`, `res-<key>-unit`), so no character is involved.
- Weights (U-S4e ruling e2). The style sheet uses 400 and 600 (five `font-weight: 600` rules in
  `tools/design/theme_template.qss`) and no 500. Qt ignores the `wght` axis of `InterVariable.ttf`, so 600 is
  synthetic or lost: in `shell_fonts_light.png` "Key results" and "Issues" render at body weight (`verified` by
  looking). Agent 3 bundles the static `Inter-Regular.ttf` and `Inter-SemiBold.ttf` of the same Inter 4.1 release (SIL
  OFL 1.1, the same `LICENSE.txt`; path in the release archive `extras/ttf/`, `inferred`, Agent 3 confirms and records
  the SHA-256 in `FONTS.md`) and removes `InterVariable.ttf`. The PDF embeds the same two files, so its headings use
  real SemiBold instead of faux bold.
- Font credit in the PDF (U-S4e ruling f). No per-page footer credit. The report ends with one colophon line, on its
  last page, after the drawing legend (U-S4g): "Set in Inter and JetBrains Mono, SIL Open Font License 1.1." The OFL says its conditions do not reach
  "any document created using the fonts" (`verified`, condition 5 as quoted in `dependency_licences.md` §Fonts), so the
  line is a courtesy, not a licence condition. Whether a whole embedded file makes the PDF a "copy" under condition 2
  stays a legal question for Agent 5 (`unresolved`).
- Every capture and layout test registers the bundled fonts first (`register_fonts`), because the fallback font is
  wider: the 277 px header widths of the U-M4c-3 xfails were measured in "Sans Serif", and with Inter the inspector tab
  bar fits at 327 px but not at 300 px (`verified`, `tools/design/layout_probe.py` with and without `--fonts`).
- Sentence case everywhere. No uppercase micro-labels.
- Body is 13 px instead of the Phase 1 14 px. Inter at 13 px has a larger x-height than Segoe UI at 14 px (assumption,
  not measured), and the toolstrip needs the width.

## 5. Spacing, shape and layout

- Spacing scale: 2, 4, 8, 12, 16, 24, 32, 48 px. Radius: 4 px controls, 6 px cards, 10 px dialogs, 8 px chips and badges.
  Control height 32 px. Hit targets 24 x 24 px or more, with no WCAG 2.5.8 exception claimed (U-S4g ruling k):
  clickable chips (`eq-chip`, `asm-tag`) and the badge beside them are 24 px tall; a check box or radio button
  accepts a click anywhere in its 32 px tall row, indicator and label together; scroll bars are 24 px wide.
- Qt ignores a border radius larger than half the widget height. Chips and badges therefore use 1 px vertical padding and
  an 8 px radius (`verified` in the smoke render: chips with 0 px padding drew square corners).

| Window width | Layout | Panes |
|---|---|---|
| 960 to 1279 px | Two panes | Inspector 300 px, centre (canvas or results tabs) fills. The results rail becomes the "Key results" tab beside the canvas (U-M4d builds it with `results-tabs`; U-S4d ruling f: the 960 x 540 shot with three panes clipped values, badges and units). No card ever shrinks below its size hint; a pane that runs out of height scrolls. |
| 1280 px and wider | Three panes | Inspector 340 px, centre fills, results rail 360 px. Splitters let the user resize; widths persist per user. On main fd190c1 the panes are 327, 598 and 347 px at 1280 x 800 (`verified`, `layout_probe.py --fonts`); the start widths are 340 and 360 (U-S4e ruling c). |
| Minimum | 960 x 540 px | `QMainWindow.setMinimumSize(960, 540)`. Below 1100 px toolstrip labels of small buttons collapse to icons, large buttons keep labels. At 540 px height the inspector and rail scroll inside their own `QScrollArea`. |

Rows from top: toolstrip (about 96 px with captions), quick-access row folded into the toolstrip's File section,
work area, status bar 24 px.

Vertical split of the centre pane (U-S4e ruling b). The canvas is what the user designs, so it gets the larger share.

| Rule | Value |
|---|---|
| Default | `centre-split` gives the canvas page 60 % and `results-tabs` 40 % of the height below the layer toggles. The view sets the sizes explicitly on first show and on each resize until the user drags the handle; the size hint of a results page never moves the split. On main fd190c1 the cards' size hint gives the results 524 of 648 px at 1280 x 800 and leaves the canvas 124 px (`verified`, `layout_probe.py --fonts`). |
| Minimums | Canvas page 240 px (legend 80 px plus a ring that holds the labels); results panel 180 px (tab bar plus one card row). Neither side collapses (`setCollapsible(False)`). |
| Compact height | When the window client area is under 620 px tall, both minimums do not fit (toolstrip 125, status bar 24, toggles 40, 240 + 180). The canvas page then becomes the first tab, "Drawing", of `results-tabs`, before "Key results", and `centre-split` holds only the tabs. "Drawing" is the current tab after a load. **Locate** in `tab-drc` switches to it. Resizing into compact height keeps the current tab of `results-tabs`; Drawing becomes current only when keyboard focus is inside the canvas page, so the focused widget stays visible (U-S4h ruling n). Leaving compact height removes Drawing; if it was current, the first remaining tab becomes current. This is the width rule turned on its side: below 1280 px wide the rail joins the tabs, below 620 px tall the canvas does. At 960 x 540 the Drawing tab gives the canvas about 320 px instead of 112 (`verified` for 112 on main). |
| Stored position | After a drag, the canvas share (0 to 1) is stored per user as `layout/canvas_share` and restored, clamped to the minimums. Pixels are not stored, because the window size changes. Nothing is stored in compact height. |

Region object names (stable): `toolstrip`, `inspector`, `inspector-tabs`, `fig-canvas`, `results-tabs`,
`results-rail`, `statusbar`. F6 and Shift+F6 cycle the regions in this order.

## 6. Toolstrip

A single `QToolBar#toolstrip`, not movable, holding one `QFrame[class="ts-section"]` per section with a
`QLabel[class="ts-caption"]` under its buttons, as in MATLAB and Xcoil v3. Large buttons: `QToolButton[class="ts-large"]`,
`ToolButtonTextUnderIcon`, 24 px icon. Small buttons: `QToolButton[class="ts-small"]`, `ToolButtonTextBesideIcon`,
16 px icon, stacked in a column of three. Every button has `objectName` `btn-<name>` and a tooltip of the form
"Label (Shortcut). One sentence." Disabled buttons stay visible and keep a tooltip that names the reason.

Enabled-state terms: "design valid" means every required field is filled and valid; "computed" means the last compute
succeeded for the current input; "has reference" means a reference design is stored.

| Section | objectName | Icon | Label | Size | Shortcut | Tooltip | Enabled when |
|---|---|---|---|---|---|---|---|
| File | `btn-new` | `new` | New | large | Ctrl+N | Create a blank design. | always |
| File | `btn-open` | `open` | Open | large | Ctrl+O | Open a project file (.json). | always |
| File | `btn-save` | `save` | Save | small | Ctrl+S | Save the project file. | always (first save asks for a name) |
| File | `btn-save-as` | `save-as` | Save as | small | Ctrl+Shift+S | Save the project under a new name. | always |
| File | `btn-examples` | `examples` | Examples | small | Ctrl+Shift+N | Load a team example. Its values are marked "example". | always |
| File | `btn-undo` | `undo` | Undo | small | Ctrl+Z | Undo the last change. | undo stack not empty |
| File | `btn-redo` | `redo` | Redo | small | Ctrl+Shift+Z, Ctrl+Y | Redo. | redo stack not empty |
| Design | `btn-tab-phases` | `phases` | Phases | small | Alt+2 | Phase assignment, sequence and terminals. | always |
| Design | `btn-tab-layers` | `layers` | Layers | small | Alt+3 | Copper layers, groups and rotation. | always |
| Design | `btn-tab-board` | `board` | Board and rotor | small | Alt+4 | Outline, fasteners, stack-up, rotor, operating point. | always |
| Design | `btn-tab-coil` | active topology | Coil | large | Alt+1 | Coil geometry for the active topology. | always |
| Topology | `btn-topology-spiral` | `topology-spiral` | Spiral | large | none | Concentrated planar spiral coils. | always (exclusive group) |
| Topology | `btn-topology-serpentine` | `topology-serpentine` | Serpentine | large | none | One phase per layer pair, continuous ribbon. | always (exclusive group) |
| Topology | `btn-topology-wave` | `topology-wave` | Wave | large | none | All phases interleaved on every layer. | always (exclusive group) |
| Connection | `btn-connection-star` | `connection-star` | Star | small | none | Star with neutral; terminals U, V, W, N. | topology supports it (exclusive group) |
| Connection | `btn-connection-delta` | `connection-delta` | Delta | small | none | Delta; terminals U, V, W. | topology supports it |
| Connection | `btn-connection-open` | `connection-open` | Open | small | none | Independent phases; six terminals. | topology supports it |
| View | `btn-zoom-fit` | `zoom-fit` | Fit | large | Ctrl+0 (0 on canvas) | Fit the drawing to the view. | geometry drawn |
| View | `btn-zoom-in` | `zoom-in` | Zoom in | small | Ctrl+= (+ on canvas) | Zoom in. | geometry drawn |
| View | `btn-zoom-out` | `zoom-out` | Zoom out | small | Ctrl+- (- on canvas) | Zoom out. | geometry drawn |
| View | `btn-zoom-terminals` | `terminals` | Terminals | small | T on canvas | Zoom to the terminal pads. | geometry drawn |
| View | `btn-show-labels` | `labels` | Labels | small | L on canvas | Show terminal and net labels. Phase letters always show. | geometry drawn (checkable) |
| View | `btn-show-current` | `current-flow` | Current | small | C on canvas | Show arrows for positive current. Static, no animation. | geometry drawn (checkable) |
| View | `btn-show-magnets` | `rotor` | Magnets | small | M on canvas | Show the rotor magnets over the stator. | rotor defined (checkable) |
| View | `btn-greyscale` | `greyscale` | Greyscale | small | G on canvas | Greyscale with hatching for phases. | always (checkable) |
| View | `btn-theme` | `theme` | Dark theme or Light theme | small | Ctrl+Shift+T | Switch the colour theme. | always; the label shows the theme it switches to |
| Export | `btn-export-svg` | `export-svg` | SVG | large | none | Vector drawing of every layer, in millimetres. | computed |
| Export | `btn-export-dxf` | `export-dxf` | DXF | large (split menu) | none | DXF: complete, outline only, or screws only. | computed; outline and screws need the board defined |
| Export | `btn-export-report` | `export-pdf` | Report | large | Ctrl+P | PDF design report with figures, results and checks. | computed |
| Export | `btn-export-all` | `export-all` | All files | small | Ctrl+E | SVG, DXF, JSON, PDF and README into one folder. | computed |
| Verify | `btn-results` | `results` | Results | large | Alt+5 | Results with units, status and equations. | always (empty state before compute) |
| Verify | `btn-drc` | `drc` | DRC | small | Alt+6 | Design rule checks and clearances. | always (empty state before compute) |
| Verify | `btn-back-emf` | `back-emf` | Back-EMF | small | none | Back-EMF waveform per phase. | always |
| Verify | `btn-torque-speed` | `torque-speed` | Torque-speed | small | none | Torque-speed characteristic. | always |
| Verify | `btn-compare` | `compare` | Compare | small | none | Compare the design with the stored reference. | always (empty state offers "Set current as reference") |
| Verify | `btn-tests` | `tests` | Tests | small | none | Run the built-in self-tests. | M5 only (U-S4g ruling l); absent before |
| Help | `btn-guide` | `guide` | Guide | large | F1 | Design guide and reference. | always |
| Help | `btn-equations` | `equations` | Equations | small | none | Equation register with sources. | always |
| Help | `btn-shortcuts` | `shortcuts` | Shortcuts | small | Ctrl+/ | Keyboard shortcuts. | always |

Rules:

- "Enabled when" is computed from view-model state, never by catching an exception after a click (assumption).
- The DXF split button: click runs "Complete DXF"; the arrow opens a `QMenu` with Complete (`export-dxf`), Outline only
  (`board`) and Screws only (`screws`).
- A connection that the active topology does not support is hidden, not disabled (P3). Which topologies support which
  connections comes from Agent 6 interfaces (`unresolved` until `docs/phase2/architecture/interfaces.md` exists).
- Toolstrip buttons use `Qt.TabFocus`: a click does not move focus away from a field. Keyboard users reach the toolstrip
  with F6 and move with the arrow keys.
- Export with failing DRC opens a confirmation dialog that lists the failures; focus starts on Cancel.

## 7. Icons

- 52 icons in `resources/icons/` (list in `ICONS.md`). All original work, licence project-owned. `compute`,
  `export-pdf` and `theme` were added in U-M4r for the interfaces.md section 11 `TOOLSTRIP` stems. `theme` fills one
  half of its disc so it reads apart from `greyscale` at 16 px (`verified` on `_contact_sheet.png`).
- `tools/design/build_icons.py` draws every icon and writes `ICONS.md`; `tools/design/render_sheet.py` renders the
  contact sheet; `tools/design/check_icons.py` exits 1 when a `TOOLSTRIP` stem has no file or an icon breaks the rules
  below.
- Grid 24 px, `viewBox="0 0 24 24"`, live area 20 px (2 px margin), stroke 1.5 px, round caps and joins,
  `stroke="currentColor"`, `fill="none"`. Small solid marks (nodes, vector handles) use `fill="currentColor"`.
- 16 px rendering: the loader replaces `stroke-width="1.5"` with `stroke-width="2"`, which renders 1.33 px.
  The contact sheet shows the 16 px column legible with this rule (`verified` by looking at `_contact_sheet.png`).
  Six icons were redrawn after the first sheet (phases, spiral, wave, rotor, DXF, terminals) because they merged at
  16 px.
- Colour: QtSvg does not take `currentColor` from the widget palette. The loader replaces the string `currentColor`
  with `tokens.json` > `themes.<theme>.icon_color.normal` and `.disabled`, renders a pixmap per `QIcon` mode, and
  rebuilds icons on theme change (`verified`: the smoke test does exactly this and the disabled Tests button renders in
  `text-disabled`).
- The embodic symbol is the app icon and logo, not part of this set.

## 8. Style sheets and hooks

- `light.qss` and `dark.qss` are generated from one template and the token table; each line names its tokens in a
  trailing comment and the file header lists every token value. Generated, not hand-edited. Generator:
  `tools/design/build_themes.py` with the template `tools/design/theme_template.qss`; the substitution rule is "replace
  `@<token>` with `themes.<theme>.color.<token>`, `@focus-ring-px` with `focus_ring_px`, and `@dir` with the theme
  name". Run it from the repository root; a second run changes nothing.
- `light.json` and `dark.json` carry the ThemeTokens fields only. `colours` holds 20 tokens: the 17 chrome tokens (grey
  only, REQ-L-04) and the three status tokens `status-pass`, `status-fail` and `status-warn` (coordinator ruling D-038a).
  The status tokens are the only chromatic entries, so the white, grey and black rule of REQ-L-04 names the chrome tokens.
  The phase tokens map into `phases`: `hatch_deg` null becomes 0, line `dashed` and `dotted` become `dash` and `dot`. The
  icon loader reads `colours["text-1"]` and `colours["text-disabled"]`, which equal `icon_color.normal` and `.disabled`.
  `check_theme_tokens.py` requires all 20 keys with the values of `tokens.json`. The interfaces.md section 11 comment on
  `ThemeTokens.colours` still says chrome tokens only. Agent 6 amends it in U-D9 (`unresolved` until then).
- Checks, each run from the repository root with the project venv: `check_theme_tokens.py` (contract fields read from
  interfaces.md), `contrast.py` (appendix A), `qss_smoke.py` (offscreen render and pixel samples, exit 1 on a mismatch),
  `check_checklist.py` (`screenshot_checklist.md` covers `screens.md` sections 1 to 14).
- Focus ring (U-S4d ruling d). The template owns every focus ring: the current tab of a focused `QTabBar`
  (`QTabBar::tab:selected:focus`), the whole `QCheckBox` (indicator and text, with a transparent border reserved so focus
  does not shift the layout; a ring on the indicator alone vanished on a checked box) and focused list, tree and table
  views. `qss_smoke.py` focuses a tab bar, two checkboxes and a list and fails when one gains fewer ring pixels than
  twice its shorter side. No focus styling lives in code.
- Loader contract for Agent 3: call `QDir.addSearchPath("theme", "<resources/themes>")`, register fonts, then
  `app.setStyleSheet(...)`. Use the Fusion style so unstyled parts follow a `QPalette` built from the same tokens.
- QSS has no CSS classes. The brief's `.result-card` maps to a dynamic property: `w.setProperty("class", "result-card")`
  and the selector `QFrame[class="result-card"]`. Variant properties: `status` (badge), `provenance` (chip), `state`
  (check text, DRC row), `invalid` (field), `stale` (card). After changing a property call
  `w.style().unpolish(w); w.style().polish(w)`.
- A stale card dims by token, never by opacity (U-S4h ruling m; stale results are content, so SC 1.4.3 applies): the
  card keeps `bg-app`, its value, unit, badge word and badge glyph use `text-3`, the badge outline uses
  `border-control`, and a verified badge drops its `surface-inverse` fill. Repolish the card's labels after setting
  `stale`. The drawing is not dimmed; the "Outdated" banner names its state, and phase colours keep 3:1.

| Hook | Widget | Purpose |
|---|---|---|
| `#toolstrip` | QToolBar | Toolstrip band |
| `[class="ts-section"]`, `[class="ts-caption"]`, `[class="ts-large"]`, `[class="ts-small"]` | QFrame, QLabel, QToolButton | Sections and buttons |
| `#inspector`, `#results-rail`, `#fig-canvas` | QWidget | Panes |
| `[class="result-card"]`, `[class="result-value"]`, `[class="result-unit"]`, `[class="eq-chip"]` | QFrame, QLabel | Result card |
| `[class="badge"][status=verified/inferred/assumption/unresolved/not-tested]` | QLabel | Trust badge: ink fill, solid, dashed, dotted on grey, grey hairline |
| `[class="asm-tag"]` | QToolButton | "n assumptions" expander |
| `[class="prov-chip"][provenance=user/example/default/measured]` | QLabel | Input provenance: solid, dashed, dotted, inverse fill |
| `[class="check-state"][state=pass/fail/warn]`, `[class="drc-row"][state=fail]` | QLabel, QFrame | Status text and DRC rows |
| `[class="hint"]`, `[class="unit"]`, `[class="field-error"]`, `[class="section-title"]`, `[class="notice"]` | QLabel, QFrame | Form parts |
| `[invalid="true"]` | QLineEdit, QAbstractSpinBox, QComboBox | 2 px `status-fail` border |
| `[class="primary"]` | QPushButton | The one primary action per view |

What the smoke test proved (`verified`, real Qt 6.11.2 offscreen, `tools/design/qss_smoke.py`): both files load
with no style-sheet warning (the only Qt message is the offscreen plugin's "does not support propagateSizeHints()");
sampled pixels equal the tokens for the result-card border and fill, the primary button fill and the invalid-field border
in both themes. Not verified here: Windows rendering, high-DPI scaling at 150 % and 200 %, and the high-contrast path.

## 9. Element ids: kept and renamed

Qt `objectName` equals the Phase 1 id without `#`. `param-*` ids are kept unchanged. Changes:

| Phase 1 id | Phase 2 objectName | Reason |
|---|---|---|
| `step-coil` ... `step-export` (step navigation) | `inspector-tabs` with tabs `tab-coil`, `tab-phases`, `tab-layers`, `tab-board`; results tabs `tab-results`, `tab-drc`, `tab-back-emf`, `tab-torque-speed`, `tab-compare`; dialogs `dlg-export`, `dlg-guide`, `dlg-tests` | The step bar is replaced by the toolstrip and tabs. |
| `app-topbar`, `btn-more` | `toolstrip`; overflow items moved to Help | Toolstrip replaces the top bar. |
| `btn-undo`, `btn-redo`, `btn-open`, `btn-save`, `btn-labels`, `btn-fit`, `btn-zoom-in`, `btn-zoom-out` | `btn-undo`, `btn-redo`, `btn-open`, `btn-save`, `btn-show-labels`, `btn-zoom-fit`, `btn-zoom-in`, `btn-zoom-out` | Toggles take `btn-show-*`; zoom commands take `btn-zoom-*`. |
| `btn-export` | `btn-export-svg`, `btn-export-dxf`, `btn-export-report`, `btn-export-all` | One button per format. |
| `rail-results`, `rail-drc` | `results-rail`, `rail-drc` | Region names lead with the region. |
| `res-r-phase`, `res-ke` ... | unchanged (`res-<key>`, `res-<key>-value`, `-unit`, `-eq`, `-badge`, `-asm`) | The brief's `result-*` reads as these `res-*` ids; I kept `res-` to match the Phase 1 handoff and the architecture section 19 rule. |
| `kicad-*`, `plg-*`, `btn-kicad-*`, `btn-save-kicad-file`, `dlg-place-confirm` | withdrawn | KiCad out of scope (D-009). |
| none | `param-topology`, `param-design-name`, `example-picker`, `btn-create-design`, provenance chips `<param-id>-prov` | New-design flow (D-014). |

## 10. Keyboard map

| Scope | Keys | Action |
|---|---|---|
| Global | Ctrl+N, Ctrl+O, Ctrl+S, Ctrl+Shift+S | New, Open, Save, Save as |
| Global | Ctrl+Shift+N | Examples |
| Global | Ctrl+Z, Ctrl+Shift+Z or Ctrl+Y | Undo, Redo |
| Global | Alt+1 ... Alt+4 | Inspector tabs Coil, Phases, Layers, Board and rotor |
| Global | Alt+5, Alt+6 | Results, DRC |
| Global | Ctrl+P, Ctrl+E | Report, Export all files |
| Global | Ctrl+Shift+T | Switch theme |
| Global | F1, Ctrl+/ | Guide, Shortcuts |
| Global | F6, Shift+F6 | Next or previous region |
| Global | Esc | Close dialog or menu; in a field, revert the uncommitted value |
| Numeric field | Up, Down, Shift+Up, Shift+Down | Plus or minus one step, ten steps |
| Numeric field | Enter, Tab | Commit |
| Canvas (focused) | Arrow keys (Shift x5) | Pan |
| Canvas | +, -, 0 | Zoom in, out, fit |
| Canvas | L, G, C, M, T | Labels, greyscale, current, magnets, terminals |
| Canvas | [ and ] | Previous or next layer solo |
| Canvas | Page Up, Page Down | Previous or next item of `board-picker`, one board per phase only (`screens.md` section 4.1, assumption) |
| Canvas | A, B, C (Shift), Esc | Highlight phase, clear. Shift+C highlights phase C because C alone toggles current arrows. |
| Toolstrip, tabs, tables | Arrow keys, Home, End | Move inside the widget; Tab leaves it |

D-094b rules that the guide and this map list only keys that the app binds. Ctrl+, (Settings) left the map under
that ruling, because no settings window is in scope (revision 2026-10-22, U-S18).

Single-letter keys work only while the canvas has focus (WCAG 2.1.4). The mouse wheel never changes a numeric field:
Agent 3 sets `Qt.StrongFocus` and ignores wheel events on `QAbstractSpinBox` and `QComboBox` unless they have focus
(assumption, Phase 1 finding that wheel edits change values by accident).

## 11. Open questions

| # | Question | Default used |
|---|---|---|
| Q1 | Phase naming: which phase is "A" relative to terminal U? | A = U, B = V, C = W (assumption) |
| Q2 | `InputSource` needs `example` (D-014); Phase 1 architecture has `user`, `default`, `measured`, `migrated`, `imported_kicad`. | Chips for `user`, `example`, `default`, `measured`; request to Agent 6 through Fable |
| Q3 | Which connections each topology supports, and whether 1- and 2-phase cases stay | Hide unsupported connection buttons |
| Q4 | Optional fields in a blank design: start empty or start at a documented default with a `default` chip? | Decided by D-019 and D-023: required fields start empty; optional fields start at `FieldSpec.neutral_value` with a `default` chip. A design or geometry input at its default is not counted in "n assumptions"; property inputs not marked measured are. B_r, mu_r and h are required (`screens.md` v2, R10). |

## Appendix A. Contrast of every text and background pair

Generated by `build_themes.py` (WCAG 2.x relative luminance). 76 pairs, 0 failures. Minimum is 4.5:1 for text, 3:1 for
non-text (borders, focus ring, phase strokes), none for disabled text.

| Theme | Foreground | Background | Ratio | Min | Result |
|---|---|---|---|---|---|
| light | `text-1` #141414 | `surface` #ffffff | 18.42:1 | 4.5 | pass |
| light | `text-1` #141414 | `bg-app` #f7f7f7 | 17.20:1 | 4.5 | pass |
| light | `text-1` #141414 | `surface-sunken` #efefef | 16.02:1 | 4.5 | pass |
| light | `text-1` #141414 | `surface-selected` #e4e4e4 | 14.49:1 | 4.5 | pass |
| light | `text-2` #454545 | `surface` #ffffff | 9.59:1 | 4.5 | pass |
| light | `text-2` #454545 | `bg-app` #f7f7f7 | 8.95:1 | 4.5 | pass |
| light | `text-2` #454545 | `surface-sunken` #efefef | 8.34:1 | 4.5 | pass |
| light | `text-2` #454545 | `surface-selected` #e4e4e4 | 7.54:1 | 4.5 | pass |
| light | `text-3` #666666 | `surface` #ffffff | 5.74:1 | 4.5 | pass |
| light | `text-3` #666666 | `bg-app` #f7f7f7 | 5.36:1 | 4.5 | pass |
| light | `text-3` #666666 | `surface-sunken` #efefef | 4.99:1 | 4.5 | pass |
| light | `text-3` #666666 | `surface-selected` #e4e4e4 | 4.52:1 | 4.5 | pass |
| light | `text-inverse` #ffffff | `surface-inverse` #141414 | 18.42:1 | 4.5 | pass |
| light | `status-pass` #2f6a47 | `surface` #ffffff | 6.42:1 | 4.5 | pass |
| light | `status-pass` #2f6a47 | `surface-sunken` #efefef | 5.58:1 | 4.5 | pass |
| light | `status-fail` #a6332c | `surface` #ffffff | 6.71:1 | 4.5 | pass |
| light | `status-fail` #a6332c | `surface-sunken` #efefef | 5.83:1 | 4.5 | pass |
| light | `status-warn` #875400 | `surface` #ffffff | 6.37:1 | 4.5 | pass |
| light | `status-warn` #875400 | `surface-sunken` #efefef | 5.54:1 | 4.5 | pass |
| light | `border-control` #858585 | `surface` #ffffff | 3.69:1 | 3 | pass |
| light | `border-control` #858585 | `bg-app` #f7f7f7 | 3.44:1 | 3 | pass |
| light | `border-control` #858585 | `surface-sunken` #efefef | 3.21:1 | 3 | pass |
| light | `focus-ring` #141414 | `surface` #ffffff | 18.42:1 | 3 | pass |
| light | `focus-ring` #141414 | `bg-app` #f7f7f7 | 17.20:1 | 3 | pass |
| light | `focus-ring` #141414 | `surface-sunken` #efefef | 16.02:1 | 3 | pass |
| light | `phase-a` #941328 | `canvas` #ffffff | 8.81:1 | 3 | pass |
| light | `phase-a` #941328 | `board-fill` #f7f7f7 | 8.23:1 | 3 | pass |
| light | `phase-b` #0032e2 | `canvas` #ffffff | 8.22:1 | 3 | pass |
| light | `phase-b` #0032e2 | `board-fill` #f7f7f7 | 7.67:1 | 3 | pass |
| light | `phase-c` #579f03 | `canvas` #ffffff | 3.30:1 | 3 | pass |
| light | `phase-c` #579f03 | `board-fill` #f7f7f7 | 3.08:1 | 3 | pass |
| light | `phase-a-grey` #262626 | `canvas` #ffffff | 15.13:1 | 3 | pass |
| light | `phase-a-grey` #262626 | `board-fill` #f7f7f7 | 14.13:1 | 3 | pass |
| light | `phase-b-grey` #5e5e5e | `canvas` #ffffff | 6.48:1 | 3 | pass |
| light | `phase-b-grey` #5e5e5e | `board-fill` #f7f7f7 | 6.05:1 | 3 | pass |
| light | `phase-c-grey` #8a8a8a | `canvas` #ffffff | 3.45:1 | 3 | pass |
| light | `phase-c-grey` #8a8a8a | `board-fill` #f7f7f7 | 3.22:1 | 3 | pass |
| light | `text-disabled` #9a9a9a | `surface` #ffffff | 2.81:1 | 0 | pass |
| dark | `text-1` #f2f2f2 | `surface` #171717 | 16.01:1 | 4.5 | pass |
| dark | `text-1` #f2f2f2 | `bg-app` #0f0f0f | 17.12:1 | 4.5 | pass |
| dark | `text-1` #f2f2f2 | `surface-sunken` #232323 | 14.04:1 | 4.5 | pass |
| dark | `text-1` #f2f2f2 | `surface-selected` #2e2e2e | 12.13:1 | 4.5 | pass |
| dark | `text-2` #c8c8c8 | `surface` #171717 | 10.72:1 | 4.5 | pass |
| dark | `text-2` #c8c8c8 | `bg-app` #0f0f0f | 11.46:1 | 4.5 | pass |
| dark | `text-2` #c8c8c8 | `surface-sunken` #232323 | 9.39:1 | 4.5 | pass |
| dark | `text-2` #c8c8c8 | `surface-selected` #2e2e2e | 8.12:1 | 4.5 | pass |
| dark | `text-3` #a0a0a0 | `surface` #171717 | 6.86:1 | 4.5 | pass |
| dark | `text-3` #a0a0a0 | `bg-app` #0f0f0f | 7.33:1 | 4.5 | pass |
| dark | `text-3` #a0a0a0 | `surface-sunken` #232323 | 6.01:1 | 4.5 | pass |
| dark | `text-3` #a0a0a0 | `surface-selected` #2e2e2e | 5.19:1 | 4.5 | pass |
| dark | `text-inverse` #141414 | `surface-inverse` #f2f2f2 | 16.46:1 | 4.5 | pass |
| dark | `status-pass` #6fb38a | `surface` #171717 | 7.25:1 | 4.5 | pass |
| dark | `status-pass` #6fb38a | `surface-sunken` #232323 | 6.35:1 | 4.5 | pass |
| dark | `status-fail` #e2776d | `surface` #171717 | 6.06:1 | 4.5 | pass |
| dark | `status-fail` #e2776d | `surface-sunken` #232323 | 5.31:1 | 4.5 | pass |
| dark | `status-warn` #d9a440 | `surface` #171717 | 7.97:1 | 4.5 | pass |
| dark | `status-warn` #d9a440 | `surface-sunken` #232323 | 6.99:1 | 4.5 | pass |
| dark | `border-control` #7d7d7d | `surface` #171717 | 4.36:1 | 3 | pass |
| dark | `border-control` #7d7d7d | `bg-app` #0f0f0f | 4.66:1 | 3 | pass |
| dark | `border-control` #7d7d7d | `surface-sunken` #232323 | 3.82:1 | 3 | pass |
| dark | `focus-ring` #f2f2f2 | `surface` #171717 | 16.01:1 | 3 | pass |
| dark | `focus-ring` #f2f2f2 | `bg-app` #0f0f0f | 17.12:1 | 3 | pass |
| dark | `focus-ring` #f2f2f2 | `surface-sunken` #232323 | 14.04:1 | 3 | pass |
| dark | `phase-a` #c43b10 | `canvas` #171717 | 3.40:1 | 3 | pass |
| dark | `phase-a` #c43b10 | `board-fill` #202020 | 3.09:1 | 3 | pass |
| dark | `phase-b` #005bfc | `canvas` #171717 | 3.33:1 | 3 | pass |
| dark | `phase-b` #005bfc | `board-fill` #202020 | 3.03:1 | 3 | pass |
| dark | `phase-c` #0eb16a | `canvas` #171717 | 6.42:1 | 3 | pass |
| dark | `phase-c` #0eb16a | `board-fill` #202020 | 5.83:1 | 3 | pass |
| dark | `phase-a-grey` #e0e0e0 | `canvas` #171717 | 13.58:1 | 3 | pass |
| dark | `phase-a-grey` #e0e0e0 | `board-fill` #202020 | 12.34:1 | 3 | pass |
| dark | `phase-b-grey` #a8a8a8 | `canvas` #171717 | 7.54:1 | 3 | pass |
| dark | `phase-b-grey` #a8a8a8 | `board-fill` #202020 | 6.85:1 | 3 | pass |
| dark | `phase-c-grey` #7a7a7a | `canvas` #171717 | 4.18:1 | 3 | pass |
| dark | `phase-c-grey` #7a7a7a | `board-fill` #202020 | 3.80:1 | 3 | pass |
| dark | `text-disabled` #6e6e6e | `surface` #171717 | 3.52:1 | 0 | pass |
