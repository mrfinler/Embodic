Prepared by: Agent 1 (UX/UI Expert Designer) - model: claude-opus-5-5

# M4 design review and rulings (U-S4d)

Date 2026-10-09, on main 3acb044. Reviewed: the 5 shots in `/mnt/user-data/outputs/m4/`, the 21 shots in
`/mnt/user-data/outputs/m4c/`, and my own grabs on 3acb044 (960 x 540 and 1280 x 800 per example and theme, greyscale
canvas at fit and at 3x, D08 colour and greyscale SVG rendered with QSvgRenderer, PDF page 1 with pdftoppm). Every
finding below was seen in one of those images (`verified` by looking) unless it says otherwise. The rulings change
`design_spec.md`, `screens.md` and `acceptance_criteria.md` (revision 2026-10-09 (U-S4d)).

## 1. Review table

Severity: major blocks an acceptance criterion; moderate breaks a spec rule; minor is polish.

| # | Screen (shot) | UX-AC / REQ | Result | Finding |
|---|---|---|---|---|
| F1 | SVG and PDF drawing, D08 colour and greyscale | UX-AC-05, REQ-N-14, REQ-N-23 | finding, major | No coil label and no coil-eye fill on the copper in either mode. In greyscale the polarity of a coil cannot be read at all, and the phase rests on one cue (grey level). Ruling a. |
| F2 | SVG legend (`export_wave_greyscale`, D08 greyscale) | UX-AC-05 | finding, moderate | The legend draws dashed and dotted line samples, but copper is solid (design_spec 3.3). Phase A has no eye swatch and the phase C swatch box is empty. Ruling a. |
| F3 | SVG footer, wave greyscale (m4 shot) | UX-AC-18 | finding, minor | The footer is cut at the right edge: "DRC FAILE". |
| F4 | Geometry view, all examples | UX-AC-05, design_spec 3.3 | finding, moderate | No phase legend on the canvas. The spec requires one whenever two or more phases show. |
| F5 | Geometry view, wave (`inspector-layers_wave_light`) | UX-AC-05 | finding, major | 96 labels at fit zoom overlap each other and the copper ("C12+R10+10+"); none can be read. Ruling b. |
| F6 | Geometry view, serpentine | UX-AC-05 | finding, major | Only "A1+" shows; phases B and C carry no label, and "A1+" overlaps a terminal pad. Ruling b. |
| F7 | Geometry view, greyscale, D08 | UX-AC-05, UX-AC-07 | finding, moderate | At fit zoom the 45 and 135 degree hatches are 3 hairlines in a 10 px disc, and the label halo covers most of them. They show at 3x only. |
| F8 | Results rail, wave | UX-AC-15 | finding, moderate | "Design: Problems found" sits beside "Issues: No issues.". The two read as a contradiction. Ruling e. |
| F9 | Results rail, Design and DRC cards | design_spec P5 | finding, minor | Status shows a word and colour but no `check-*` glyph. |
| F10 | Shell at 960 x 540, D08 and wave, both themes | UX-AC-21, UX-AC-17, REQ-N-15 | finding, major | Result values and badges are cut in half vertically; units read "mr"; the inspector is about 180 px wide and its tabs scroll. Ruling f. |
| F11 | Layers tab, D08 and wave | REQ-N-15 | finding, moderate | Header "ickness (µr" is clipped and the form scrolls sideways. Ruling g1. |
| F12 | Examples gallery | UX-AC-03 | finding, major | Item text contains "Xcoil", "engine.js l.19-97" and a repository path. |
| F13 | Examples gallery | design_spec 4 | finding, minor | Title and source note have the same weight and colour; the list has no hierarchy. |
| F14 | New design dialog | design_spec 3.1, screens 1, WCAG 1.4.11 | finding, moderate | Unchecked topology buttons have no boundary and no icon; they read as plain text. |
| F15 | Inspector, every tab | design_spec 5 | finding, minor | Provenance chips are 30 px tall beside inputs and 16 px beside a checkbox. At input height they look like buttons. |
| F16 | Inspector, Coil tab | design_spec 5 | finding, minor | Input right edges are ragged (fields without a unit run into the unit column), and a field widens when its chip goes away. |
| F17 | Inspector, Phases, Layers, Board | screens conventions | finding, minor | "Assignment", "Copper layers" and "Centre bore" put the label beside the control; every other field puts it above. |
| F18 | Inspector, same three controls | UX-AC-14 | finding, moderate | No provenance chip on `param-phase-assign-mode`, `param-layer-count` and `param-bore`. |
| F19 | Phases tab, D08 | screens 3 | finding, moderate | `phase-pattern-string` "AabBCcaABbcC" shows with no caption and no key to the case rule. |
| F20 | Blank spiral | UX-AC-13 | finding, minor | The canvas shows L1 and L2 toggles for layers that do not exist and no empty-state sentence. |
| F21 | Toolstrip, every shot | UX-AC-09, design_spec 6 | finding, moderate | Open is disabled; the spec enables it always. |
| F22 | Geometry view labels | UX-AC-05 | finding, minor | Negative polarity uses the hyphen "A2-"; at 12 px it is half the width of "+". |
| F23 | PDF page 1, D08 | UX-AC-18, P1 | finding, major | "1.34  H" drops the µ, so the value reads as 1.34 henry. Ω is spelt "ohm", the middle dot is dropped ("mV s/rad"). |
| P1 | Toolstrip, both themes, 1280 | UX-AC-04, UX-AC-06, UX-AC-09 | pass | Neutral chrome, icons rebuilt per theme, label under every large button. |
| P2 | Inspector tabs, focused | UX-AC-11 | pass | 2 px ring on the current tab (FocusRingTabBar today; QSS template from U-S4d, ruling d). |
| P3 | Coil, Phases, Layers, Board tabs, three examples | UX-AC-16 | pass | Only the active topology's fields show; "Gap between boards" is disabled with its reason. |
| P4 | Blank spiral | UX-AC-13 | pass | Empty required fields with the unit placeholder and "Required"; "37 required fields left"; Go to first missing field. |
| P5 | New design dialog | UX-AC-13 | pass (name state not tested) | Name, topology, example picker, Create as the primary button. The capture typed "Stator A", so the empty-name state (S11) has no shot. |
| P6 | Geometry view, colour, D08, both themes | UX-AC-05 (labels) | pass | All 12 labels "A1+" ... "C4+" with a board-coloured halo. |
| P7 | Theme smoke, both themes | UX-AC-08 | pass | 76 contrast pairs, 0 failures (`contrast.py`). |

23 findings (6 major, 9 moderate, 8 minor), 7 passes.

## 2. Rulings

### a. Greyscale and print mode in exports

Legend-only does not meet REQ-N-14, REQ-N-23 or UX-AC-05 (principle: experience first; the reviewer of a printed
report has no hover and no zoom). REQ-N-23 names "hatch inside the coil eye only, labels" for the PDF default, and
the rendered D08 greyscale SVG shows neither. Dashing the copper is not the fix: design_spec 3.3 rules copper solid,
because a dashed trace reads as an open circuit. The exports must draw what the canvas draws:

1. Every coil label of ruling b, as SVG `<text>` with a halo in the board fill (`paint-order: stroke`), in both modes.
2. The coil-eye fill of design_spec 3.3 inside the eye disc: tint for A, 45 degree hatch for B, 135 degree hatch for
   C, clipped to the disc (`clipPath`), in both modes. Hatch spacing 0.4 mm at 1:1 print scale.
3. One source for labels and eyes. The coil numbering and the eye disc live in `ui/viewmodels/outcome.py` today, which
   the exporters may not import. They move to a module both the canvas and the exporters import (Agent 6 picks the
   place), so canvas and file cannot differ.
4. The drawing legend shows, per phase, a solid copper bar in the phase ink, the eye swatch and "Phase A". Line-style
   samples belong to chart legends only.

Spec change: design_spec 3.3 and 3.4, UX-AC-05. Change requests U-M4a-fix 1 to 4.

### b. Label density and serpentine labels

Principle: experience first (a label that cannot be read is noise; every phase must still be named). Spec change:
design_spec 3.3 label row, new UX-AC-27.

- Placement is collision-free. The view places labels in priority order and skips a label whose box, grown by 2 px,
  meets a placed label, a terminal pad or the view edge. Priority: the first coil of each phase, then every coil in
  index order. The first label of each phase always places (with a leader outside the ring when its own spot is taken),
  so each phase letter shows at every zoom.
- Placement reruns at the end of a zoom or resize step. Zooming in shows more labels; a skipped label still shows in
  the hover tooltip of its copper.
- Exports use the fit-zoom label set at the page scale.
- Spiral labels read phase, coil number and polarity, "A1+", "A2−", because `phase-table` lists coils by number.
- Wave labels read phase and polarity, "A+", "A−", once per phase belt. A wave has no coil a user picks by number.
- Serpentine labels read the phase letter only, "A", "B", "C": a serpentine phase is one ribbon with no coil number and
  no coil polarity. Each phase gets 4 labels at fit zoom, one per 90 degree quadrant, on its outermost end turn, so
  no conductor is more than 45 degrees from its letter. With one board per phase and "All boards", the letter is also
  the board name (screens 4.1).
- Negative polarity uses U+2212 "−", the width of "+" (F22).

### c. New objectNames from U-M4c

Principle: model the domain (one widget per field, so Go to first missing field focuses the input that is empty).
All six are ratified; `param-bore` is narrowed. Spec change: screens.md sections 1, 5 and 14a (new); section 16 is unchanged and still matches `--table`.
`screens_coverage.py` now fails when the UI code sets a literal objectName that no screens.md table defines.

| objectName | Ruling |
|---|---|
| `param-topology-spiral`, `-serpentine`, `-wave` | Ratified: the three buttons of the `param-topology` group. |
| `param-bore` | Narrowed to the bore shape control (`/outline/bore`, `/outline/bore/shape`). |
| `param-bore-radius`, `-sides`, `-across-flats`, `-corner-radius`, `-rotation` | Ratified, one per bore pointer. `FieldSpec.widget_id` must follow (change request U-M4c-2 4). |
| `issues-list` | Ratified. It is the list screens.md called "the Checks list". |
| `fig-stale` | Ratified: the "Last valid drawing" stamp on the canvas. |
| `dlg-examples` | Ratified; its list is `examples-list`, one item `example-<id>` per packaged example. |
| `dlg-recovery` | Ratified. |

### d. Tab focus ring

Principle: encode lessons in structure (one style source; the check fails when the rule goes). The QSS template now
rings the current tab of a focused tab bar, the whole checkbox (indicator and text, so a checked box shows it too) and
focused list, tree and table views. `qss_smoke.py` focuses each and fails without a ring; deleting the tab rule makes it
exit 1. Agent 3 deletes `FocusRingTabBar`, `SHELL_QSS` and the `issues-list` style sheet in code. Spec change:
design_spec 8, UX-AC-11.

### e. DRC state in the rail until the DRC tab exists

Principle: experience first (two cards must not contradict each other). The "Design" card goes. The rail shows two
status cards with glyph and word: "Inputs" (validation issues of the draft) and "DRC" (`check-pass` "Passed" or
`check-fail` "186 failures", a link that opens `tab-drc` once U-M4d builds it). The Issues list title becomes "Input
issues"; its empty text "No input issues.". The status bar keeps `st-drc`. Spec change: screens.md section 6.1 (new).

### f. Results rail below 1280 px

Principle: experience first. The 960 x 540 shot is not acceptable: values and badges are clipped and units cut
(REQ-N-15, UX-AC-21). design_spec 5 stands: below 1280 px the rail becomes the "Key results" tab of `results-tabs`
beside the canvas, and the inspector keeps 300 px. U-M4d owns it, since it builds `results-tabs`. Until then, the rail
sits in a `QScrollArea` and no card shrinks below its size hint. Spec change: design_spec 5, UX-AC-21.

### g. Other rulings

Principle for all: experience first (get the details right).

1. `layer-list` fits the inspector with no sideways scroll. Columns: Layer, Kind, Thickness (µm), and for spiral Pair
   and Rotation (°). Group moves to the row's context menu; joins-via moves to the row tooltip; the "show" column goes,
   because the canvas layer toggles own visibility. Columns size to their header. screens.md 4.
2. Every control in the inspector puts its label above it (F17), and every field reserves its unit and chip columns,
   so edges align and nothing moves when a chip changes (F16). Chips are 20 px tall, centred on the control (F15).
   screens.md conventions.
3. Topology buttons in the New design dialog show their icon and a `border-control` boundary when unchecked (F14).
   screens.md 1.
4. Example items show the title in `text-1` weight 600 and the note in `text-3` 12 px. Example notes shown to users
   name no other program and no repository path (UX-AC-03); the provenance stays in the example file (F12, F13).
5. `phase-pattern-string` gets the caption "Coil pattern" and the hint "Upper case +, lower case −." (F19).
6. The canvas shows the layer toggles only when a layout exists, and a blank design shows "The drawing appears when
   every required field is valid." (F20).
7. The PDF writes units exactly as the UI does (µH, mΩ, mV·s/rad). A glyph the PDF font lacks fails the export test;
   it is never dropped (F23). The font is the bundled Inter or JetBrains Mono subset (design_spec 4).

## 3. Change requests

| Unit | # | Request | Finding |
|---|---|---|---|
| U-M4a-fix | 1 | Draw every coil label of ruling b in SVG and PDF, both modes. | F1 |
| U-M4a-fix | 2 | Draw the eye tint and hatches inside the eye disc, clipped, both modes. | F1, F7 |
| U-M4a-fix | 3 | Take labels and eye discs from the shared module of ruling a 3. | F1 |
| U-M4a-fix | 4 | Drawing legend: solid copper bar, eye swatch, "Phase A"; fix the empty C swatch and the missing A swatch. | F2 |
| U-M4a-fix | 5 | Footer never clipped: widen the viewBox to the footer text or wrap it. | F3 |
| U-M4a-fix | 6 | PDF units equal the UI units; a missing glyph fails the test. | F23 |
| U-M4c-2 | 1 | Label placement of ruling b in the geometry view, U+2212 for minus. | F5, F6, F22 |
| U-M4c-2 | 2 | Canvas legend; eye hatch drawn with a screen-space pattern brush so it shows at fit zoom. | F4, F7 |
| U-M4c-2 | 3 | Ruling g 1 to 6 in the inspector, dialogs and canvas. | F11, F13 to F20 |
| U-M4c-2 | 4 | Through Fable to the model owner: `FieldSpec.widget_id` of the bore pointers per ruling c. | c |
| U-M4c-2 | 5 | Example notes free of "Xcoil" and paths in the text the UI shows. | F12 |
| U-M4d | 1 | Rail becomes the Key results tab below 1280 px; rail in a `QScrollArea` until then. | F10 |
| U-M4d | 2 | Rail status cards "Inputs" and "DRC" with glyphs (ruling e). | F8, F9 |
| U-M4d | 3 | Delete `FocusRingTabBar`, `SHELL_QSS` and the `issues-list` style sheet; the template rules replace them. | d |
| U-M4e | 1 | Enable Open (design_spec 6), or name the unit that owns it. | F21 |
| U-M4e | 2 | Recapture S11 with an empty name, and the 960 x 540 rows of the checklist. | P5, F10 |
