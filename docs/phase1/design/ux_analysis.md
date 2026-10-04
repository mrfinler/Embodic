Prepared by: Agent 1 — UX/UI Expert Designer — model: claude-opus-5-5

# UX analysis of Xcoil v3 (reference tool for embodic) — Phase 1 draft, 2026-10-04

Scope: the user interface of Xcoil v3 as built in `/home/claude/serpentine/dist/xcoil.html` (source:
`src/body.html`, `style.css`, `ui.js`, `ui-panels.js`, `ui-main.js`, `ui-content.js`). The calculation engine is out of
scope here (Agent 2 reviews it). Reference material was only read, never modified.

Status labels follow PROJECT_BRIEF §3: `verified` (checked in code or reproduced by measurement), `inferred` (reasoned;
reason given), `assumption` (design opinion without evidence), `unresolved`, `not tested`.

Method (`verified` = actually done):
- Code reading of the six UI files (line numbers below refer to the files in `/home/claude/serpentine/src/`).
- Playwright/Chromium screenshots at 1440×900 (desktop), 1024×768 (tablet) and 420×800 (phone), plus a 360 px
  width check; script in my scratchpad, outputs in `xcoil_screens/` (19 PNGs) and measured numbers in
  `xcoil_screens/ui_metrics.json` (hit sizes, font sizes, keyboard tab order, ARIA attributes, scroll sizes).
- WCAG 2.x contrast computed from the CSS tokens (sRGB relative luminance formula); colour-vision-deficiency (CVD)
  separation of the phase colours computed with the dataviz skill validator (Machado 2009 simulation, OKLab ΔE×100).
- Limitation: the egress proxy blocked Google Fonts, so all screenshots render with fallback fonts (DejaVu/Liberation)
  instead of IBM Plex (`verified`: `curl` to fonts.googleapis.com → 403). Widths of text therefore differ slightly from
  the user's machine; layout conclusions are unaffected (`inferred`: the grid uses fixed pane widths, style.css:37).

Screenshot index (all in `xcoil_screens/`):

| File | Content |
|---|---|
| d01_desktop_default_serpentine.png | Default serpentine design, desktop |
| d02_desktop_sector_results.png | Sector coils topology, Results tab |
| d03_desktop_sector_inspector_crop.png | Inspector column in sector mode (disabled fields visible) |
| d04 … d07 | DRC, Back-EMF, Stack-up, Torque–speed tabs (sector mode) |
| d08_desktop_sector_power_view_crop.png | "Power · efficiency · current" chart (three units on one axis) |
| d09, d10 | Compare tab after "Save as reference" and turns 4 → 3 |
| d11_desktop_reference_formulas.png | Reference (formula) tab |
| d12_desktop_invalid_input.png | Invalid input state (poles = 15) |
| d13_desktop_focus_ring_toolstrip_crop.png | Keyboard focus ring on the KiCad button |
| t01, t02 | Tablet viewport and full page (sector) |
| p01, p02, p03 | Phone viewport, full page (sector), results area |

---

## 1. Information architecture

### 1.1 Regions (desktop ≥ 1241 px)

`verified` (body.html, style.css:37): a CSS grid with fixed columns 318 px | fluid | 400 px and rows title | toolstrip |
panes | status.

| Region | Element | Content | Evidence |
|---|---|---|---|
| Title bar | `header.titlebar` | Xcoil logo, `h1` "Xcoil", version badge `v3.0`, blue accent background | body.html:41–43, style.css:38 |
| Toolstrip (ribbon) | `nav#toolstrip` | 9 labelled sections: File (New/Open/Save), Preset (select), Topology (Serpentine / Sector coils / 3-Phase Wave + wave-structure select), Connection (Star/Delta/Open), View (2D/3D, Fit, Zoom, Terminals, Magnets, Labels, Current, Board), Export (SVG, DXF, KiCad, Outline DXF, Screws DXF, All ZIP, Report PDF), Compare (Save as reference, Compare, Torque-speed), Verify (Run tests, Design guide) | body.html:45–121 |
| Property inspector | `aside#params` | 14 collapsible `<details>` groups generated from `GROUPS`, 86 inputs/selects | ui.js:16–139, metrics `inputs_total` = 86 |
| Figure pane | `main.figure` | "Figure 1 — Winding layout", SVG plan view (pan/zoom), optional WebGL 3-D, rotor-angle slider, layer chips | body.html:128–155 |
| Results pane | `section.results` | Summary strip (6 key numbers), 10 tabs: Results, DRC, Back-EMF, Torque–speed, Stack-up, Mechanical, Compare, Reference, Guide, Tests | body.html:157–188 |
| Status bar | `footer#statusbar` | compute time, DRC pass/fail, layer/via/primitive counts, cursor coordinates | body.html:190–196, ui-panels.js:356–366 |
| Overlays | `dialog#dlg-text`, `div#toast` | copy-text fallback dialog for saving, 3.2 s toast | body.html:199–205, ui.js:176 |

### 1.2 Data structures behind the form (`verified`, ui.js)

- `GROUPS` (ui.js:16–139): array of `{id, title, open, only?, fields[]}`. Each field is
  `{k, label, unit?, step?, min?, options?, num?, check?, json?, only?, labels?}` or a hint placeholder `{hint: 'fit'}`.
  - `k` maps 1:1 to an engine parameter (`E.DEFAULTS`) and to the DOM id `#p-<k>` (ui.js:187; test UI-01 checks this).
  - `only` = string of topology codes for which the field applies: `s` serpentine, `w` wave, `c` sector coils
    (comment at ui.js:13; mapping `TOPO_CODE` at ui.js:159). Example: `strands` `only: 's'` (ui.js:27),
    `sectors` `only: 'c'` (ui.js:39), `waveLayers` `only: 'w'` (ui.js:56).
  - `labels` = per-topology label override, e.g. `turns` → "Turns per coil" in sector mode (ui.js:26, applied at
    ui.js:229).
  - `options` = `[[value, text], …]`; `num: true` casts the select value to a number (ui.js:219).
  - `check` = checkbox; `json` = hidden input holding a JSON value (the custom stack-up list, ui.js:108, 188).
  - Hints: `{hint: 'fit'|'sector'|'endw'|'pads'|'outline'|'screws'|'stack'|'drive'}` become `<p class="hint">`
    rows filled after each compute with derived numbers (ui-panels.js:30–55).
- Group-level `only` hides the whole group (`d.hidden`, ui.js:230) — used only by the "Sector coils" group (ui.js:38).
  Field-level `only` merely **disables** the field (`setOff`, ui.js:225, 229).
- Further cross-field rules are hard-coded in `syncDisabled()` (ui.js:226–247): magnets auto radius, fillet vs sharp
  corners, layer order only for single board, pads only with interconnect, custom stack-up disables copper weight, etc.
- `PRESETS` (ui.js:140–156): 15 named parameter overrides (serpentine, wave after Paul et al., sector 12/10 and 9/8,
  SPARK-style, miniature …), selected from the toolstrip.
- State object `state` (ui.js:158): params, result, `lastGood` (last valid layout), view, hidden layers, display
  toggles, rotor angle, active tab, 2D/3D mode, reference design.
- Persistence: `localStorage` keys `xcoil.params.v3`, `xcoil.reference.v3` (ui.js:7).

### 1.3 User flow as implemented

`verified` by code reading and screenshots:

1. **Choose topology** — toolstrip segmented buttons (body.html:58–62) *or* the inspector select `#p-topology`
   (ui.js:18). On change, `onTopologyChange()` may silently rewrite the user's `turns` or `sectors` value to the
   largest that fits / nearest balanced count and reports it only in a 3.2 s toast (ui-main.js:77–86, ui.js:176).
2. **Set parameters** — 14 groups; every `input` event schedules a recompute after 140 ms (ui.js:251,
   ui-main.js:237). The figure, the summary strip, the hints and all tabs re-render.
3. **Read DRC** — summary cell "Design rules PASS/Fail · n" (ui-panels.js:20), DRC tab with a badge count
   (ui-panels.js:113–136), status bar "DRC: pass" (ui-panels.js:361). Each issue with a location has a "Locate"
   button that zooms the figure (ui-panels.js:120, 135). Red circles mark issue positions on the canvas (ui.js:339).
4. **Inspect results** — Results tab (key/value tables), Back-EMF (waveform + harmonic table), Torque–speed,
   Stack-up (section drawing + editable table), Mechanical, Compare (needs a saved reference first).
5. **Export** — single-file buttons (SVG, DXF, KiCad `.kicad_pcb`, outline DXF, screws DXF, JSON), ZIP of everything,
   PDF report (ui-main.js:52–69). No pre-export confirmation, even when the DRC fails (`verified`: `need()` only checks
   that a valid layout exists, ui-main.js:53).

---

## 2. What works well (keep in embodic)

| # | Strength | Evidence | Status |
|---|---|---|---|
| W1 | Live recompute with the **last valid figure kept and dimmed** when input is invalid, plus an error pill and a flagged field — the user never loses the drawing. | ui.js:257–259, 303; d12 | verified |
| W2 | Stable, data-driven form: one declarative `GROUPS` model, ids `#p-<key>`, tested round trip (UI-01, UI-02). A good pattern to port. | ui.js:16–139, ui-main.js:108–109 | verified |
| W3 | Derived-value **hint rows** right under the inputs ("4 turns per coil (max. 11) · 12 coils of 30.00° …") give immediate feasibility feedback. | ui-panels.js:30–55; d02 | verified |
| W4 | DRC issues are **locatable** on the figure. | ui-panels.js:120, 135 | verified |
| W5 | Units are shown next to every numeric input (mm, °, T, rpm …). | ui.js:198; d01 | verified |
| W6 | Per-layer visibility chips, "Top layer only", terminal labels, rotor-angle slider: good inspection tools for a multi-layer board. | ui.js:361–374; d02 | verified |
| W7 | Compare against a saved reference with parameter diff and overlaid curves. | ui-panels.js:291–318; d09 | verified |
| W8 | Equations and sources are available in the app (Reference tab) and in the PDF report. | ui-content.js:6–26, 48 | verified |
| W9 | Native `<dialog>` and `<details>`; toast has `role="status"`; `prefers-reduced-motion` stops the current-flow animation; dark mode tokens exist. | body.html:199, 205; style.css:10–25, 112 | verified |
| W10 | Keyboard focus ring exists (2 px accent outline) and the tab order follows the visual order of the toolstrip and inspector. | style.css:33; metrics `tab_order_first45`; d13 | verified |
| W11 | All visible text is English (built-in test UI-12). | ui-main.js:159 | verified |

---

## 3. What is confusing (specific findings)

Severity: **H** blocks or misleads, **M** slows down or risks misreading, **L** polish.

| # | Sev | Finding | Evidence | Status |
|---|---|---|---|---|
| C1 | H | **Irrelevant fields stay visible but disabled.** In sector mode 23 fields that do not apply (wave structure, parallel strands, active conductors, terminal side, layers per phase, layer-pair connection, board arrangement, layer order, copper layers (wave), …) remain on screen greyed out, and they push the actually relevant "Sector coils" group (coil count Q) below the fold at 1440×900. | ui.js:225, 229 (`setOff` disables only); metrics `sector_disabled_visible_fields` (23); d02, d03 | verified |
| C2 | H | **Silent value rewrite on topology change.** Switching topology may change the user's turns or coil count; the only notice is a 3.2 s toast. No undo, nothing near the field. | ui-main.js:81–84, ui.js:176 | verified |
| C3 | H | **Results carry no validation status.** Efficiency (η 72.2 %), torque, inductance, ΔT etc. are shown with the same visual weight as exact geometry (pole pitch). Nothing says which numbers are first-order estimates, which equations are unverified (Agent 2 gates EQ-14, EQ-15, EQ-20 as "cannot verify yet"). The only caveat is a sentence in the exported README. Efficiency is shown in the always-visible summary strip. | ui-panels.js:24, 88; ui-main.js:50; `docs/phase1/engineering/equation_specification_draft.md` gate summary | verified |
| C4 | H | **Formulas are disconnected from the numbers.** Equations live in a separate "Reference" tab (19 entries) with no link from a result to its equation, inputs or source. Traceability needs a per-result "how was this computed". | ui-content.js:6–26, 48; d11 | verified |
| C5 | H | **Phase colours collapse for deuteranopia.** Phase A red `#cf3f52` vs phase C green `#2f9455`: CVD ΔE 1.4 (target ≥ 8). Phases are distinguished only by colour on the figure and in the chips; layers of the same phase only by opacity 0.95 / 0.62. | style.css:6; ui.js:318; validator run (dataviz skill) | verified |
| C6 | M | **Duplicate controls for the same parameter.** Topology, connection and wave structure can each be set in the toolstrip and in the inspector; two sources of truth for one value. | body.html:58–72 vs ui.js:18–19, 61 | verified |
| C7 | M | **Two-row ribbon of 30+ commands** at 1440 px; export, compare and verify buttons sit at the same level as the topology choice. The main task flow (topology → parameters → check → export) is not visible as an order. | body.html:45–121; d01 (toolstrip 2 rows) | verified |
| C8 | M | **Truncated labels and values.** Selects cut their text ("Default: 16-pole se…", "Serpentine (phas…", "Parallel (constan…"); summary keys and sub-lines use ellipsis ("KT PER LINE AMP…", "min. clearance 0.199 …"). | style.css:67, 86, 140, 143; d01, d02 | verified |
| C9 | M | **Mixed units on one chart axis.** The "Power · efficiency · current" view plots W, % and A on one unlabelled y axis; the Compare chart labels its axis "mN·m / W". Readers cannot read values; violates the one-axis rule of the dataviz guidance. | ui-panels.js:265, 308; d08 | verified |
| C10 | M | **Compare colours encode sign, not quality.** Any increase is green and any decrease red (e.g. turns −1 shown red), regardless of whether higher is better (resistance up = worse). | ui-panels.js:300; style.css:240–241; d10 | verified |
| C11 | M | **Integer counts printed with decimals** in Compare ("Poles 16.00", "Turns 3.000", "Vias 63.00"). | ui-panels.js:311 (`sig(v, 4)`); d10 | verified |
| C12 | M | **Compare table overflows** the 400 px pane: the Δ % column needs horizontal scrolling inside the panel. | style.css:249–250; d10 | verified |
| C13 | M | **Error messaging is colour + code first.** Invalid fields get only a pink background and an inset bar (`.field.bad`), no message next to the field; the message appears in the Results tab and status bar with an internal code (`POLES_ODD`) as the first word. | style.css:98; ui.js:258; ui-panels.js:8; d12 | verified |
| C14 | M | **Export ignores the DRC verdict.** KiCad/ZIP export proceeds silently with DRC errors. | ui-main.js:53–61 | verified |
| C15 | L | Group summaries concatenate the title and a note without a separator in the accessible name ("Machinesector coils", "Stack-upauto"). | ui.js:183; metrics `groups` | verified |
| C16 | L | Mechanical terms are inconsistent: "Sector coils" (topology) vs "Coils (slots) Q" vs "Turns per coil"; "Figure 1 — Winding layout" style titles are report language inside an app. | ui.js:39, 26; body.html:129 | verified |
| C17 | L | The torque–speed vertical axis is clipped to the drive torque and the pull-out curve is cut off; explained only in a note under the chart. | ui-panels.js:263–264; d07 | verified |
| C18 | L | "Run tests" (131-test engine suite) is a primary toolstrip action; useful for developers, noise for most users. | body.html:117 | inferred (user-goal reasoning) |

---

## 4. Accessibility gaps (WCAG 2.2 AA lens)

| # | Gap | Measurement / evidence | WCAG SC | Status |
|---|---|---|---|---|
| A1 | **Tabs are not keyboard tabs.** `role="tab"` without `aria-controls`, without roving `tabindex`, and arrow keys do nothing (focus stayed on "Results" after ArrowRight). Panels lack `aria-labelledby`. | body.html:159–170; ui-main.js:231–235, 244; metrics `tabs_arrow_key_moves_focus` = "calc", `tab_aria` all null | 2.1.1, 4.1.2 | verified |
| A2 | **Figure not operable by keyboard.** The SVG canvas is not focusable (`tabIndex` −1); pan is pointer-only; the cursor read-out is pointer-only. Zoom buttons exist (partial alternative). | ui.js:375–399; metrics `canvas_focusable` = −1 | 2.1.1 | verified |
| A3 | **Hints and units not linked to inputs.** 0 of 86 controls have `aria-describedby`; the unit `<span>` sits inside the `<label>` but after the input, so it is not part of the accessible name in a predictable way; hint rows are separate paragraphs. | ui.js:186, 193–199; metrics `inputs_with_describedby` = 0 | 1.3.1, 3.3.2 | verified (code) / screen-reader output `not tested` |
| A4 | **Errors not exposed programmatically.** No `aria-invalid`; no live announcement of "Invalid input"; error shown by background colour on the field. | ui.js:258; metrics `aria_invalid_count` = 0; style.css:98 | 3.3.1, 4.1.3, 1.4.1 | verified |
| A5 | **Small hit targets.** Minimums measured at 1440 px: checkboxes 14×14 px, number inputs 23 px high, selects 23 px, tabs 25 px, small toolstrip buttons 24 px, layer chips 21 px high. 14 px and 21 px fail the 24×24 px minimum. | metrics `hit_sizes`; style.css:92, 97, 125 | 2.5.8 | verified |
| A6 | **Low non-text contrast of control borders.** Input/select border `--rule` `#c4cdd6` on white = 1.61:1 (needs 3:1). | style.css:3, 92; computed | 1.4.11 | verified |
| A7 | **Small, low-contrast secondary text.** Base 13 px; 10 px uppercase labels (toolstrip section titles, summary keys), 10 px chart text, 11 px status bar. Muted `#586674` on `--chrome-2` `#d6dde4` (status bar, inactive tabs) = 4.29:1 at 11 px (needs 4.5:1). Pill "PASS" `#1d7f47` on `#d9f0e2` = 4.19:1 at 11 px. | metrics `font_sizes_px`; style.css:49, 140, 147, 171, 200; computed | 1.4.3 (contrast); size is not an SC but hurts 1.4.4 at 200 % zoom (`not tested`) | verified (contrast) |
| A8 | **Colour as the only differentiator** for phases (figure, layer chips, stack-up section), and for compare up/down rows. | style.css:6, 240–241; ui.js:318, 370 | 1.4.1 | verified |
| A9 | **Charts are pointer-only and have generic names** ("Back-EMF waveforms over one electrical period"); the crosshair tooltip responds to `pointermove` only; no table alternative for the torque–speed curves (Back-EMF has a harmonic table). | ui-panels.js:146, 168–174, 245 | 1.1.1, 2.1.1 | verified |
| A10 | Toolstrip is a `<nav>` labelled "Toolstrip" but contains commands, not navigation; no `role="toolbar"` arrow-key model; 31 toolstrip tab stops before the inspector. | body.html:45; metrics `tab_order_first45` (first group toggle = stop 33, first parameter `#p-topology` = stop 34) | 2.4.1, 2.4.3 | verified |
| A11 | No skip link / landmark shortcut to the inspector, figure or results. | body.html | 2.4.1 | verified |
| A12 | Focus ring uses the blue accent with 1 px offset; on the pressed (light-blue) button it measures 4.77:1 — passes, but will be lost when the accent becomes monochrome unless redesigned. | style.css:33, 57; computed | 2.4.7, 2.4.11 | verified |
| A13 | Disabled fields rely on `opacity .45` (2.80:1 for input text). Disabled controls are exempt from 1.4.3, but combined with C1 the screen is full of unreadable grey content. | style.css:88, 95; computed | — (usability) | verified |
| A14 | Recompute results are not announced; the status bar text changes silently (fine for sighted users; screen-reader users get no feedback that numbers changed). | ui-panels.js:356–366 | 4.1.3 | verified (code) |

Positive notes: `lang="en"`, native `<details>`/`<dialog>`/`<select>`, labels wrap their inputs (implicit association),
a `prefers-reduced-motion` rule, and `role="status"` on the toast (`verified`, dist/xcoil.html:2, body.html:205,
style.css:112).

---

## 5. Responsiveness findings

| Width | Behaviour | Evidence | Status |
|---|---|---|---|
| 1440×900 | 3 panes fit; no page scroll (scrollHeight 900); toolstrip already wraps to **2 rows (≈150 px)**; inspector and results scroll independently. | metrics desktop_*; d01 | verified |
| 1024×768 | Breakpoint 1240 px: inspector + figure side by side, results move **below** (page height 1894 px). Toolstrip wraps to **3 rows = 227 px (30 % of the viewport)**; results summary only peeks at the bottom. | style.css:212–218; metrics tablet_*; t01, t02 | verified |
| 420×800 | Breakpoint 760 px: single column title → toolstrip → figure → inspector → results. **Toolstrip = 409 px**, the figure starts at y = 442 px; page height 3947 px (≈ 5 screens); reaching a result means scrolling past the full 86-field inspector. No horizontal scroll. | style.css:219–232; metrics phone_*; p01–p03 | verified |
| 360 px | No horizontal page scroll (scrollWidth = 360). | metrics `w360_scrollWidth` | verified |
| Tables | Wide tables use `.scroll-x` containers (good) but Compare and Stack-up columns still clip inside the 400 px pane on desktop. | style.css:162; d06, d10 | verified |
| Touch | Pinch-zoom and pan on the canvas are implemented with pointer events; `touch-action: none` on the canvas blocks page scroll when the finger starts on the figure (on phone the figure is 420 px tall). | ui.js:378–389; style.css:105 | verified (code) / on-device `not tested` |

---

## 6. Language and branding items to change

| # | Item | Where | Change for embodic | Status |
|---|---|---|---|---|
| B1 | Product name "Xcoil" in `h1`, document title, version badge | body.html:42; build.js:12 (`<title>Xcoil v3.0</title>`) | embodic logo (black lockup) + module name; title "<design name> — embodic" | verified |
| B2 | "Xcoil" in exported README and PDF metadata/footer | ui-main.js:39; report.js:1, 65, 238 | "embodic <version>"; report footer without legacy name | verified |
| B3 | Global/engine names `SerpentineEngine`, `XcoilReport`, storage keys `xcoil.*`, export file prefix `serpentine_` | ui.js:4, 7; ui-main.js:23, 25 | neutral names (e.g. `embodic_<design>`) — code concern for Agent 3 | verified |
| B4 | Tagline | — | already removed; test UI-14 asserts no `.tagline` (keep an equivalent test) | verified (ui-main.js:163) |
| B5 | Blue accent title bar, blue icons, light-blue pressed state, blue focus ring | style.css:4, 38, 53–57, 33 | monochrome: black/white/grey chrome; pressed = inverted (black fill, white text); focus = 2 px black ring with white gap | verified (current) / design in `design_spec_draft.md` |
| B6 | Green "accent" export icons (`.tbtn.accent`, `.sbtn.accent`) | style.css:54, 62, 245 | remove; colour reserved for data semantics | verified |
| B7 | Red/blue/green phases, gold vias, brown bus, green board fill | style.css:6–7 | desaturated, CVD-checked phase set + greyscale fallback; vias/bus/board in greys | verified (current) |
| B8 | Topology vocabulary "Serpentine / Sector coils / 3-Phase Wave" | body.html:59–61 | embodic scope is **spiral coils** (user decision 2026-10-04); serpentine and wave topologies are out of scope for the first release (`assumption` — confirm with Fable) | inferred from brief §1 |
| B9 | Icon `i-xcoil` (circle with spokes) | body.html:31 | embodic symbol (rounded triangle of three teardrops) — brand asset, not redrawn | verified |
| B10 | Font: IBM Plex from Google Fonts (external request at start-up) | dist/xcoil.html head | system UI font + bundled open-licence mono; no runtime CDN request (also needed for offline KiCad use) | verified (current) |

---

## 7. Implications for the embodic design (summary)

1. Replace the ribbon with a **step-ordered workflow** (Coil → Phases → Layers → Board & rotor → Results → Export) and
   one place per parameter (fixes C1, C6, C7) — `assumption` (design choice, specified in `design_spec_draft.md`).
2. Every result gets **unit + EQ-ID + status label + "how was this computed"** (fixes C3, C4) — required by the brief.
3. Phases: **CVD-validated desaturated colours + lightness ladder + labels/hatch fallback** (fixes C5, A8).
4. Accessibility baseline: real tabs, focusable figure with keyboard pan/zoom, linked hints/units/errors, 24 px
   minimum targets (44 px on touch), 3:1 control borders (fixes A1–A11).
5. Responsive: compact top bar instead of a 409 px toolstrip on phone; figure first; bottom step navigation.
6. Export: pre-flight checklist with explicit confirmation on DRC failures (fixes C14).
