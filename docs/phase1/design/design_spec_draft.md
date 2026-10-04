Prepared by: Agent 1 — UX/UI Expert Designer — model: claude-opus-5-5

# embodic — design specification (Phase 1 draft, 2026-10-04)

Scope: user interface of the embodic tool for 3-phase, multi-layer spiral-coil PCB stators — standalone app and KiCad
plugin dialog. Technology-neutral: tokens are given as CSS custom properties because the mockups are HTML, but every
token maps 1:1 to a Qt/wx colour or a stylesheet value if Agent 6 chooses a native toolkit.

Companion files: `ux_analysis.md` (findings on Xcoil v3), `mockups/*.html` + `mockups/png/*.png` (six screens),
`design_handoff_for_agent3.md` (tokens, element ids, acceptance criteria).

Status labels (PROJECT_BRIEF §3) are given for claims. Design choices without evidence are `assumption`.
Numbers in the mockups are **examples**; drawings are **illustrative, not computed**.

---

## 1. Design principles

| # | Principle | What it means in the UI | Status |
|---|---|---|---|
| P1 | **Honest numbers** | No result without unit, equation id and validation status; estimates look like estimates. Never imply magnetic balance, torque or efficiency from geometry alone (brief rule 6). | assumption (derived from brief rules 3, 5, 6) |
| P2 | **One place per parameter** | Each engine parameter lives in exactly one step; other places show it read-only with a link. | assumption (fixes ux_analysis C6) |
| P3 | **Workflow order is visible** | Coil → Phases → Layers → Board & rotor → Results → Export. The order is a guide, not a lock: every step stays reachable. | assumption (fixes C7) |
| P4 | **Show only what applies** | Fields that do not apply are hidden; a field that is temporarily inapplicable because of a sibling option in the same section may be disabled **with a visible reason**. | assumption (fixes C1) |
| P5 | **Monochrome chrome, colour for data** | White / grey / black for everything; colour only for phase identity and pass/fail. | user decision 2026-10-04 (brief §1) |
| P6 | **Never colour alone** | Phases also carry labels, lightness steps and hatching; status carries glyph + text. | verified need (ux_analysis C5, A8) |
| P7 | **Keyboard first-class** | Every action reachable in visual order; the drawing is focusable and pannable by keys. | assumption (fixes A1, A2) |
| P8 | **The machine never silently changes user input** | Any automatic change shows old → new value next to the field with Undo, and is announced. | assumption (fixes C2) |
| P9 | **Calm density** | Engineering density (14 px base, 32 px controls) without ribbon clutter; one primary action per view. | assumption |

---

## 2. Information architecture

### 2.1 Regions (desktop)

| Region | Id | Content |
|---|---|---|
| Top bar | `#app-topbar` | embodic logo (black lockup), design name + save state, Undo/Redo, Open, Save, overflow menu, primary **Export** |
| Step navigation | `#step-nav` | 6 steps with number, label and state (✓ done, “1 fail”); `aria-current="step"` |
| Step panel | `#panel-step` | parameters of the current step; sticky footer with Back / Next |
| Figure | `#figure` | view toolbar, focusable canvas, layer chips, legend |
| Results rail | `#rail-results` | DRC card + key results (value, unit, status, EQ-ID) or step-specific checks |
| Status bar | `#statusbar` | compute state + engine version, DRC summary, counts, units, cursor |

Overflow menu (`#btn-more`): Start from example…, Set as reference / Compare, Design guide, Equation register, Run
self-tests (developer), Keyboard shortcuts, About (versions, licences).

### 2.2 Where Xcoil v3 parameters go (`GROUPS`, ui.js:16–139)

| Xcoil group | embodic step › section | Notes |
|---|---|---|
| Machine (topology, wave structure, poles, phases) | Coil › Winding combination (poles); phases fixed at 3 | Topology choice removed: spiral coils only (user decision). Serpentine/wave not offered (`assumption`, confirm). |
| Winding geometry (rIn, rOut, turns, traceWidth, clearance, cornerStyle, fillet, startAngle) | Coil › Annulus, Turns and copper, Coil shape | `strands` (parallel strands per turn) for spiral coils: `unresolved` — ask Agent 2 |
| Sector coils (sectors, coilSides, coilEnds, coilGap, coilLayers) | Coil (Q, sides, ends, gap); Layers (count) | renamed “Coils per layer Q” |
| End-turn copper width | Coil › Advanced (disclosure) | unequal-width option S5 later (Agent 2 §3.1) |
| Layers and vias | Layers | adds series/parallel pairs and pair rotation (new) |
| Phase connection, Terminal pads | Phases › Connection, Terminals | |
| Board outline, Fasteners, Stack-up, Rotor and magnets, Operating point, Drive, Cooling | Board & rotor (one section each) | manufacturing limits (min trace/space, via) added here |
| Results tabs: Results, DRC, Back-EMF, Torque–speed, Stack-up, Mechanical, Compare | Results › Summary, Electrical, Losses and thermal, Back-EMF waveform, Torque–speed, Stack-up and field, Mechanical, Checks (DRC), Compare | |
| Reference (formulas), Guide, Tests tabs | per-result “How was this computed”; overflow menu (register, guide, self-tests) | |

### 2.3 User flow

1. **Coil** — Q, 2p (balance check inline), shape, turns, trace width/spacing, annulus. Feasibility rail.
2. **Phases** — automatic star-of-slots assignment (or manual), sequence, polarity/direction per coil, connection,
   terminals.
3. **Layers** — number of layers, pair connection (series/parallel), pair rotation, vias, stack list.
4. **Board & rotor** — outline, holes, stack-up and manufacturing limits, rotor/magnets, operating point, drive, cooling.
5. **Results** — every number traceable; Checks (DRC) list with Locate.
6. **Export** — KiCad placement (plugin) or files; pre-flight checklist; confirmation if checks fail.

Recompute is live (debounced, §7.5). Results and DRC are always visible in the rail, so the order is advisory.

---

## 3. Colour system

### 3.1 Neutral tokens (light mode)

| Token | Value | Use | Contrast (computed, WCAG 2.x) |
|---|---|---|---|
| `--n-0` / `--surface` | `#ffffff` | panels, canvas, inputs | — |
| `--n-50` / `--bg-app`, `--board-fill` | `#f7f7f7` | app background, PCB fill in drawings | — |
| `--n-100` / `--surface-sunken` | `#efefef` | table header, EQ chip, hover | — |
| `--n-200` / `--surface-selected` | `#e4e4e4` | selected row | — |
| `--n-300` / `--divider` | `#dcdcdc` | decorative separators only (not a control boundary) | 1.37:1 on white (decorative, exempt) |
| `--n-400` / `--text-disabled` | `#9a9a9a` | disabled text (exempt from 1.4.3) | 2.81:1 on white |
| `--n-500` / `--border-control` | `#858585` | input, select, seg, chip borders | **3.69:1** on white, 3.44 on n-50, 3.21 on n-100 (use only on these three) |
| `--n-600` / `--text-3` | `#666666` | hints, captions, units | **5.74:1** white, 5.36 n-50, 4.99 n-100, 4.52 n-200 |
| `--n-700` / `--text-2` | `#454545` | secondary text | **9.59:1** white |
| `--n-900` / `--text-1`, `--border-strong`, `--focus-ring`, `--surface-inverse` | `#141414` | primary text, focus ring, primary button, selected segment | **18.42:1** white; white on it 18.42:1 |
| `--n-1000` | `#000000` | brand logo only | — |
| `--grid-line` | `#e6e6e6` | chart gridlines (hairline, solid) | decorative |

All contrast values `verified` (computed with the WCAG relative-luminance formula; script in my scratchpad,
`contrast.py`). Brand black/white comes from the logo files (`embodic_logo.png` is black on transparent;
`embodic-*-white.png` white on transparent — `verified`, pixel inspection).

### 3.2 Functional colours (data semantics only)

Allowed **only** for: phase identity in the geometry view, phase swatches in legends/tables, phase series in charts,
pass/fail glyph + label, DRC markers, the failure count badge. Never for chrome, buttons, headings or text other than
pass/fail labels. Text next to a phase swatch stays in text tokens.

| Token | Value | OKLCH (L, C, h) | Role | Justification | Contrast |
|---|---|---|---|---|---|
| `--phase-a` | `#5c4383` plum | 0.44, 0.105, 300 | Phase A strokes/fills | darkest step of a lightness ladder A → C; hue far from status red/green | 8.12:1 white, 7.58 n-50 |
| `--phase-b` | `#87660c` ochre | 0.53, 0.105, 85 | Phase B | middle step | 5.34:1 white, 4.98 n-50 |
| `--phase-c` | `#438ebf` steel | 0.62, 0.105, 240 | Phase C | lightest step | 3.58:1 white, 3.34 n-50 (≥ 3:1 for graphics) |
| `--status-pass` | `#2f6a47` | 0.48, 0.084, 155 | ✓ Pass glyph + label | desaturated green, AA as text | 6.42:1 white |
| `--status-fail` | `#a6332c` | 0.49, 0.152, 28 | ✕ Fail glyph + label, DRC marker, fail count | the single alarm hue; kept stronger than the rest on purpose | 6.71:1 white; white on it 6.71:1 |
| (warning) | `--text-1` | — | ▲ Warning glyph + label in ink | no third status hue: keeps the palette minimal and avoids a clash with ochre phase B | 18.42:1 |

Validation of the phase set with the dataviz skill validator (`node validate_palette.js "#5c4383,#87660c,#438ebf"
--mode light --pairs all`): lightness band PASS, chroma floor PASS (all ≥ 0.10), **CVD worst pair ΔE 17.8 (deutan)**,
tritan 12.2, normal-vision floor ΔE 20.9, contrast ≥ 3:1 — `verified` (validator run). For comparison the Xcoil phase set
fails with ΔE 1.4 (A red vs C green, deutan) — `verified`.

“Desaturated”: chroma 0.105 vs 0.13–0.18 in Xcoil (`#cf3f52` C = 0.180, `#2f9455` C = 0.133) — `verified` (computed).
The validator’s chroma floor (0.10) is the lower bound at which a hue still reads as a hue; going lower makes the phases
read as greys (dataviz skill, color-formula §checks).

Known collision, mitigated: under deuteranopia fail red vs phase B ochre ΔE 4.0 — `verified` (computed). Mitigation
(design rule): DRC markers are never identified by colour alone — ring + ✕ + number with a 1.3 mm white halo; when a
DRC item is selected, copper dims to 35 % so the marker dominates. Pass vs fail ΔE 6.0 (deutan): always glyph + word.

Provenance of the hue order: the phase colours were found by a grid search over OKLCH (L 0.45–0.65, C 0.09–0.13, hue
excluded near status red 0–40° and green 130–160°), maximising all-pairs CVD separation; the A-dark/B-mid/C-light ladder
was chosen so the same order survives in greyscale — `verified` (search run; script `phase_search*.py` in scratchpad).
Phase naming convention (which phase is “A”) is not standardised in the sources read — `unresolved`; an IEC wiring
colour convention exists for mains conductors but was not checked in this session and is not used.

### 3.3 Greyscale fallback (colour-free drawing)

Activated by the view toggle “Greyscale”, automatically in print/PDF and in Windows high-contrast (forced-colors) mode.

| Phase | Stroke | Coil-footprint fill | Chart line | Label |
|---|---|---|---|---|
| A | `#262626` (15.1:1) | 8 % ink, no hatch | solid 2 px | `A1+` … |
| B | `#5e5e5e` (6.48:1) | 45° hatch, 2.6 mm pitch | dashed 6/3 | `B1+` … |
| C | `#8a8a8a` (3.45:1) | 135° hatch | dotted 1.5/3 | `C1+` … |

Copper traces stay **solid** in every mode: dashed copper would read as an open circuit (`assumption`, domain
reasoning). The ladder validates as an ordinal ramp (monotone L, ΔL ≥ 0.06, light end 3.45:1) — `verified` (validator
`--ordinal`). Hatching follows the dataviz texture rule (45° / 135° only). See `mockups/png/03_phase_and_layers.png`,
rail “Greyscale check”.

### 3.4 Drawing colours

Board fill `--n-50` with 1 px ink outline; bore and holes white with ink outline; vias white with ink ring; terminal pads
white squares with ink outline and mono labels U/V/W/N; magnets (when shown) N = `--n-200` fill + “N”, S = white + `--n-500`
outline + “S”; dimension lines `--text-2` dashed hairline; selection = 2 px ink outline + white halo; stale geometry
(invalid input) = 35 % opacity + stamp “Last valid layout”.

### 3.5 Dark mode (provisional, not mocked — open question Q1)

| Token | Dark value | Contrast (computed) |
|---|---|---|
| bg / panel / sunken | `#0f0f0f` / `#171717` / `#232323` | — |
| text-1 / text-2 / text-3 | `#f2f2f2` / `#c8c8c8` / `#a0a0a0` | 16.0 / 10.7 / 6.86 on panel |
| border-control | `#7d7d7d` | 4.36 on panel |
| phase A / B / C | `#73599e` / `#9b7928` / `#539dcf` | 3.12 / 4.40 / 6.05 on panel; validator (dark, all pairs) PASS, CVD ΔE 14.6 |
| pass / fail | `#6fb38a` / `#e2776d` | 7.25 / 6.06 on panel |

Implement with `color-scheme: light dark` + `light-dark()` or token swap under `prefers-color-scheme`, plus a manual
toggle (modern-web-guidance “dark-mode”). Values `verified` (computed) but untested on screens.

### 3.6 Forced colours (Windows high contrast)

Chrome uses system colours automatically; the geometry canvas uses `forced-color-adjust: none` **and** switches to the
greyscale+hatch mode so phase identity survives; focus ring uses `outline` (survives forced colours) — per
modern-web-guidance “css” §Forced Colors Mode.

---

## 4. Typography

| Role | Stack | Size / weight | Licence (status) |
|---|---|---|---|
| UI text | `"Segoe UI", "Noto Sans", "Liberation Sans", system-ui, sans-serif` | 14 px (0.875 rem) / 400; 16 px on coarse pointers and phone | Segoe UI: Windows system font, **not bundled** (proprietary, used in place); Noto Sans, Liberation Sans: SIL OFL 1.1 — `inferred` (prior knowledge, verify LICENSE files before bundling) |
| Numbers, units, codes | `"Cascadia Mono", "JetBrains Mono", Consolas, "Liberation Mono", "DejaVu Sans Mono", monospace`, `font-variant-numeric: tabular-nums` | 13–14 px | Cascadia Mono and JetBrains Mono: SIL OFL 1.1 — `inferred`; Consolas system font, not bundled |
| Headings | UI stack, 600 | 16 / 20 / 24 px | — |
| Optional brand display (report cover, About) | `"Manrope"` | 600–700 | SIL OFL 1.1 — `inferred`; the company deck uses Manrope Bold (pdffonts lists `ManropeV5-Bold`, not embedded) — `verified` |

Scale: 12 (captions, badges, chart ticks — minimum), 13, 14 (body), 16, 20, 24, 32 px; line-height 1.45; sentence case
everywhere, no uppercase micro-labels (Xcoil used 10 px uppercase, ux_analysis A7). Hero numbers in result cards use
proportional figures (dataviz rule); columns use tabular figures. No runtime web-font request (offline KiCad use; Xcoil
fetched IBM Plex from Google Fonts — ux_analysis B10).

Mockup rendering note: this container has no Segoe UI/Cascadia; the PNGs show Liberation Sans / Liberation Mono
(metric-compatible with Arial / Courier New) — `verified`.

---

## 5. Spacing, shape, layout grid

- Spacing scale (4 px base): 2, 4, 8, 12, 16, 24, 32, 48 px (`--sp-1 … --sp-8`). Section padding 12/16 px; field gap 4 px;
  label-to-control gap smaller than group gap (forms guidance, Gestalt proximity).
- Radius: 4 px controls, 6 px cards, 10 px dialogs, pill for chips/badges. Shadows only on overlays (dialog, toast, menu).
- Control heights: 32 px desktop (≥ 24 px WCAG 2.5.8), **44 px** on `pointer: coarse` and in the phone layout; icon buttons
  32×32 / 44×44. Checkboxes are 18 px glyphs inside a ≥ 32 px label hit area.

| Layout | Breakpoint (container width) | Grid | Notes |
|---|---|---|---|
| Desktop | ≥ 1280 px | `340px | minmax(0,1fr) | 360px`; rows 52 / 48 / 1fr / 28 px | Results step uses 280 px navigation + content + 360 px traceability rail (mockup 04) |
| Tablet | 768–1279 px | `300px | minmax(0,1fr)`; rail becomes a collapsible bottom sheet (“Key results”, 2-row summary strip always visible above the status bar) | step labels may shorten to numbers + icons below 900 px; no horizontal scroll |
| Phone | < 768 px | single column: top bar 56 px → figure (aspect 1:1, max 60 svh) → DRC banner → key-result tiles (2 columns) → current step fields (label above input) → sticky bottom step bar (6 × ≥ 60 px) | mockup 06; verified no horizontal scroll at 420 and 360 px (scrollWidth = viewport) |
| KiCad plugin dialog | fixed min 880 × 600 px, resizable | tabs for steps; `380px | 1fr` (form | 2-D preview); footer with Cancel / Back / primary | §11 |

Use container queries for components that live in different panes (result cards, tables), media queries only for the
app shell (modern-web-guidance “css-layout” §4). At 200 % browser zoom on a 1440 px screen the tablet layout applies; at
400 % the phone layout (WCAG 1.4.10 reflow; the drawing and wide tables are 2-D content allowed to scroll in their own
container).

---

## 6. Component inventory

| Component | Anatomy | Behaviour notes |
|---|---|---|
| Top bar | logo · design name (button: rename) · save-state chip · Undo · Redo · Open · Save · More · **Export** | one primary button per view; Undo covers parameter edits, auto-changes and placements made from embodic |
| Step navigation | `<nav>` with ordered links; number badge (inverted when current), label, state text | `aria-current="step"`; state “✓” when the step has no open check; “n fail” for failures; never blocks navigation |
| Step panel | sticky head (icon, title, one-line purpose) · sections (`<section>` + `<h2>`) · sticky footer (Back · “Step n of 6” · Next) | Advanced options in a disclosure at the end of a section |
| Numeric field | label (+ symbol in text-3) · input with unit suffix · hint · error · notice | `<input inputmode="decimal">` (not `type=number`: no wheel changes, no locale surprises); `aria-describedby` = unit + hint (+ error first); ↑/↓ = ±step, Shift = ×10; Enter commits; Esc reverts; validate on blur, clear error on input (forms guidance) |
| Select | native `<select>` | for ≥ 6 options only; fewer → segmented control |
| Segmented control | `<fieldset>` + `<legend>` + radio inputs styled as segments | selected = inverted (ink fill, white text, 600); arrow keys native |
| Picker cards | radio cards with a 44 px shape drawing + label | coil sides × ends; 2 px ink border when selected |
| Checkbox | 18 px native box (`accent-color: #141414`) inside a ≥ 32 px label | |
| Hint row | ⓘ + text-3 text; derived numbers in mono bold | linked via `aria-describedby`; above the input on phone |
| Inline notice | 4 px ink left border, message “Changed from 8 to 7: …”, **Undo** | `role="status"`; created whenever the engine changes a user value (P8) |
| Error message | ✕ + fail-red text under the field; field border 2 px fail red | `aria-invalid="true"`; also listed in Checks; the last valid drawing stays (dimmed + stamp) |
| Derived list | grey box with key/value rows (`<dl>`) | feasibility results; pass/fail glyph + word |
| Buttons | primary (ink fill), secondary (ink outline), ghost (no border), icon (32/44 square, `aria-label`), small (28 px) | hover = sunken fill; disabled toolbar buttons use `aria-disabled` so they stay focusable with a reason in the tooltip/description |
| View toolbar | Colour/Greyscale segment · labels toggle (`aria-pressed`) · fit · zoom in/out · step-specific tools | `role="toolbar"`, arrow-key navigation inside |
| Geometry canvas | SVG/canvas with `role="img"`, title + description, “Illustrative, not computed” stamp until the engine draws it (then “Computed · engine vX.Y”), scale bar | `tabindex="0"`; keys in §8.2; pinch/drag on touch with `touch-action: pan-y` so the page still scrolls |
| Layer chips | checkbox chips L1…Ln; checked = sunken fill + ink border + check mark; unchecked = dashed border + strike-through | group label “Layers”; “All” / “Top pair only” quick actions |
| Legend | swatch + text per phase; via, terminal symbols | always present for phases (≥ 2 series) |
| Key result row (rail) | label + symbol · value + unit · status badge · EQ link · “example” marker while mocked | click → opens Results at that card with the expander open |
| Result card | title + symbol · hero value + unit · meta row (status badge, EQ links, tags “n assumptions”, “n limitations”, “input”, “derived”, “count”) · optional one-line limitation · disclosure “How was this computed” | §10.4 |
| Status badge | glyph + word, pill; monochrome **line-continuity code**: verified = solid ink fill (✓), inferred = solid outline (≈), assumption = dashed outline (◇), unresolved = dotted outline on grey (?), not tested = hairline grey outline (○) | non-interactive; “Status:” prefix in visually-hidden text |
| EQ link | mono chip “EQ-10”, 24 px high | opens the equation register entry (Agent 2 ids) |
| DRC card | title · pass/fail summary · top issue (measured vs required, units) · warning count · Locate · Open checks | |
| DRC list item | severity glyph · rule code (mono) · message · measured / required · layer · Locate | fail rows get a 4 px fail-red start border |
| Tables | `<table>` with caption, `th scope`, sticky header, numeric columns right-aligned, row header sticky on scroll | wide tables scroll inside `.table-wrap`; on phone they stack (modern-web-guidance “responsive-table”) |
| Charts | §9 | |
| Tabs | WAI-ARIA tabs: roving `tabindex`, ←/→/Home/End, `aria-controls`, panels `aria-labelledby` | used for result density, plugin steps |
| Dialog | native `<dialog>` with `showModal()`; title, body, footer (secondary left of primary) | initial focus on the safe action (“Review failures”); Esc closes; no custom focus trap needed (modern-web-guidance “accessibility” §11) |
| Toast | `popover="manual"` container, `role="status"`, ink background, optional action | transient **echo** only — the inline notice or Checks list carries the information; 6 s, pauses on hover/focus |
| Menu | overflow menu (`aria-haspopup="menu"`), popover, arrow keys | |
| Status bar | compute state + engine version · DRC · counts · units · cursor (mono) | polite live region announces “Results updated, DRC: 1 failure” at most once per second |
| Empty / loading / stale | empty: one sentence + action; computing: rail values at 60 % with “Updating…” chip after 300 ms; stale: 35 % geometry + stamp | no skeleton flashes; keep the previous frame (dataviz “refetch keeps the frame”) |

---

## 7. States

| State | Visual | Programmatic |
|---|---|---|
| Default | ink text, `--border-control` border | — |
| Hover | `--surface-sunken` background (buttons, segments, rows) | — |
| Focus (keyboard) | 2 px `--focus-ring` outline, 2 px offset (white gap shows the surface) | `:focus-visible`; ring contrast 18.4:1 on white, ≥ 14:1 on any neutral surface (computed) |
| Pressed / selected | inverted: ink fill, white text, weight 600 | `aria-pressed` / `aria-selected` / `:checked` / `aria-current` |
| Disabled (contextual) | text `--text-disabled`, divider border, reason in hint (“Not used with straight ends”) | `disabled` for inputs; `aria-disabled` for toolbar buttons |
| Error | 2 px fail-red border, ✕ + message under the field | `aria-invalid`, `aria-describedby` → error id first |
| Auto-changed | inline notice with Undo | `role="status"` |
| Computing | “Updating…” chip, values dimmed to 60 % (≥ 300 ms) | `aria-busy="true"` on the rail |
| Stale (invalid input) | geometry 35 %, stamp “Last valid layout” | announced once (polite) |

### 7.5 Recompute timing

Desktop: debounce 300 ms after the last keystroke, immediate on Enter/blur/selection change. If a compute takes > 1 s
(Python engine, large stacks — `unresolved` until Agent 3 measures), show a determinate or indeterminate progress line
under the top bar and keep editing possible; cancel stale computations. Announcements debounced (A14).

---

## 8. Accessibility requirements (WCAG 2.2 AA)

### 8.1 Contrast (computed, `verified`)

Text: text-1 18.42, text-2 9.59, text-3 5.74 (white) / 4.99 (n-100) — all ≥ 4.5:1. Control boundaries: border-control
3.69 (white) / 3.21 (n-100) ≥ 3:1. Focus ring 18.42:1. Phase strokes ≥ 3.34:1 on board fill. Pass/fail text ≥ 5.99:1 on
n-50. Badges: ink outline on white 18.42:1; verified (white on ink) 18.42:1; not-tested hairline uses border-control 3.69:1.

### 8.2 Keyboard map

| Scope | Keys | Action |
|---|---|---|
| Global | Ctrl+O / Ctrl+S / Ctrl+Shift+S | Open / Save / Save as |
| Global | Ctrl+Z / Ctrl+Shift+Z (Ctrl+Y) | Undo / Redo |
| Global | Alt+1 … Alt+6 | Go to step 1 … 6 |
| Global | Ctrl+E | Go to Export |
| Global | F6 / Shift+F6 | Cycle regions: top bar → step nav → step panel → figure → rail → status bar |
| Global | F1 or ? (outside text fields) | Keyboard shortcuts dialog |
| Global | Esc | Close dialog / menu / popover; in a field: revert uncommitted value |
| Numeric field | ↑ / ↓, Shift+↑ / Shift+↓ | ± step, ± 10 × step |
| Figure (focused) | ← ↑ → ↓ (Shift = ×5) | Pan |
| Figure | + / − / 0 | Zoom in / out / fit |
| Figure | L, G | Toggle labels, colour/greyscale |
| Figure | [ / ] | Previous / next layer solo |
| Figure | A, B, C, Esc | Highlight phase, clear |
| Figure (Phases, manual) | Arrow keys between coils, Enter | Select coil, open its phase/polarity editor |
| Tabs, toolbars, menus, radio groups | ←/→ (↑/↓), Home/End | Move within the widget; Tab leaves it |

Single-character shortcuts work only while the figure has focus (WCAG 2.1.4). Shortcuts are listed in the dialog and in
tooltips (no `title` attribute as the only carrier; use a popover hint).

### 8.3 Focus order

Skip link “Skip to parameters” → top bar (rename, Undo, Redo, Open, Save, More, Export) → step links 1–6 → step panel
fields in visual order → panel footer (Back, Next) → view toolbar → canvas → layer chips → rail (DRC actions, result
links) → status bar links. DOM order equals visual order; no positive `tabindex`; no CSS reordering of interactive
content.

### 8.4 Other requirements

- Names: every control has a visible label; units are part of the accessible description; icon-only buttons have
  `aria-label`; badges include visually hidden “Status:”.
- Landmarks: `header`, `nav` (steps), `aside` (panel, rail), `main` (figure/results), `footer`; headings in order.
- Live regions: one polite (status bar), one assertive reserved for blocking errors (e.g. KiCad connection lost).
- Reduced motion: no animation by default; transitions ≤ 150 ms opacity only; with `prefers-reduced-motion: reduce`
  none; current-flow display uses static arrows (Xcoil animated it, style.css:110).
- Target size: ≥ 24×24 px desktop, ≥ 44×44 px touch; chips/EQ links 24–28 px with ≥ 4 px spacing.
- Text resize 200 % without loss; reflow at 320 CSS px except the drawing and wide tables.
- Charts: data table alternative; tooltip content reachable by keyboard focus on points.
- Language: `lang="en"`; English only (UX-AC-17).

---

## 9. Charts (dataviz rules applied)

- One quantity per y axis — never mix units (fixes Xcoil “Power · efficiency · current”, ui-panels.js:265, and the
  Compare chart “mN·m / W”, :308). Use small multiples sharing the x axis instead.
- Phases use the phase tokens; ≥ 2 series → legend + direct labels at the line ends; 2 px lines, 8 px end markers with a
  2 px surface ring; gridlines solid hairline `--grid-line`; axis text 12 px text-2; title states quantity and
  operating point.
- Hover/focus: crosshair snapping to the nearest sample; one tooltip lists all series (value first, series second);
  keyboard: focus the plot, ←/→ moves the crosshair.
- Every chart has a “Data table” disclosure and a status badge + EQ links like a result card (mockup 04).
- Compare: deltas in ink with ▲/▼ and the words “better”/“worse” only when Engineering defines the preferred direction;
  otherwise sign only. No red/green for increase/decrease (fixes C10). Integers without decimals (fixes C11).

---

## 10. Screen specifications

### 10.1 Spiral coil setup (step 1) — `mockups/02_spiral_setup.html`

Sections: **Winding combination** (Q `#param-coil-count`, 2p `#param-pole-count`; inline balance result: “Balanced” /
“Not balanced — choose 12, 18 or 24”, coils per phase, Q/2p; clickable list of balanced coil counts); **Coil shape**
(sides: radial / parallel to sector edge; ends: arc / straight / stadium — Agent 2 options S1–S3; corner fillet);
**Turns and copper** (turns per coil per layer N, trace width w, spacing s, spiral sense of layer X); **Annulus and
placement** (r_i, r_o, gap between coils, centre angle of coil 1); **Advanced** (end-turn widths, unequal width — later).

Figure: “Coil detail” (one coil, dimension lines for r_i, r_o, coil pitch, gap, w/s magnifier, turn numbering, centre
via) ↔ “Ring” toggle; mini-map highlighting the coil. Rail “Feasibility”: radial limit (EQ-02, cross-check) next to the
constructive limit from the generator, coil pitch and pole pitch (EQ-01), k_w1 (EQ-08), track length (EQ-03); step
checks (fail/warn/pass) with “Go to field”. Shows notice + Undo, focus, error and toast states.

### 10.2 Phase assignment (step 2) — `mockups/03_phase_and_layers.html` frame A

Panel: connection (star / delta / open, with the k_w3 warning rule from Agent 2 §3.4), method (automatic star of slots /
manual), phase sequence (A→B→C / A→C→B; note that swapping B and C reverses rotation), derived pattern string, balance,
k_w1, k_w3; terminals (outer/inner rim, names U V W N, pad options in Advanced).

Figure: ring of Q coils labelled `A1+` (phase, index within phase, polarity), a circulation arrow per coil (+ = clockwise
for positive current — **convention to be confirmed**, Q3), phase highlight filter, colour/greyscale. Rail: phasor star,
coil table (coil, mechanical angle, EMF angle, phase, polarity, direction; editable in manual mode with live balance
check), greyscale preview. Mock data follow the 12/16 pattern “A C B …” reported by Agent 2 (topology_analysis §3.4,
`verified (reproduced)` there); in the mockup it is illustrative.

### 10.3 Layer configuration (step 3) — frame B

Panel: number of copper layers (2/4/6/8 → pairs), **pair connection** cards (series: pair EMFs add, centre via per pair +
transfer vias; parallel: lower R, circulating current if layer EMFs differ, EQ-07), **pair rotation** (none / alternate
½ coil pitch / custom; offset per pair in degrees; hint explains via placement), vias (drill, pad, vias per transition,
plating badge “assumption”).

Main: **stack list** table (layer, KiCad layer, artwork X-in / Y-out mirrored, pair, rotation, joins via, copper µm,
content A·B·C, show); **section + current path** diagram (U in → L1 → Vc1 → L2 → Vt1 → … → next coil) with through-via
columns and dots on the joined layers; **pair rotation overlay** (solid vs dashed footprints). Rail: layer checks (e.g.
rotated vias need gap ≥ pad + 2 × clearance; whole X/Y pairs), vias per coil, per-layer B_z spread (EQ-05/07), stator
thickness, series turns per phase. Options M1–M4 follow Agent 2 §4.2.

### 10.4 Results with traceability (step 5) — `mockups/04_results_traceability.html`

Left: section navigation with counts, status filter (five checkboxes), “Export traceability table (CSV)”, “Include in
PDF report”. Centre: result cards. Each card: **value + unit**, **EQ-ID link(s)**, **status badge**, tags
(“n assumptions”, “n limitations”, “input”, “derived”, “count”), optional one-line limitation, and the disclosure
**How was this computed** with: equation (EQ title + formula), inputs table (quantity, value + unit, origin, status),
assumptions, limitations, validation (tolerance, oracle, run state), sources (register entry + paper/page as given by
Agent 2), actions (Copy trace, Open EQ). Right rail: status definitions, assumed inputs of this design, oracle table
(O1–O3 from the evidence register, “not tested”).

Status of a computed result (proposal — needs confirmation by Agents 2, 4, 6; Q5):
1. `verified` — equation gate passed **and** the result matched a validation oracle within its stated tolerance; also
   exact identities/counts (pole pitch, series turns).
2. `inferred` — equation gate “reuse” / “reuse with change” implemented and unit-tested; no oracle match yet.
3. `assumption` — the result is dominated by an input/coefficient chosen without evidence (flagged by Engineering, e.g.
   film coefficient h for ΔT). Ordinary assumed inputs appear as “n assumptions” tags and in the inputs table.
4. `unresolved` — equation gate “cannot verify yet” (EQ-14, EQ-15, EQ-20) or conflicting sources.
5. `not tested` — implementation or validation step not run.
The badge shows the weakest applicable status. Efficiency is not shown in the summary rail (P1); it appears only in
Losses with its status.

### 10.5 Board & rotor (step 4) — no mockup in Phase 1

Sections: Outline (circle/polygon, sides, size ratio or absolute size, rotation, corner radius, bore); Fasteners (ISO 273
fit, outer/inner patterns); Stack-up and manufacturing (copper weights, board thickness, dielectric, custom list editor,
**min trace / min space / min via** limits used by checks); Rotor and magnets (double/single, Br, µr, thickness, pole-arc
or block-magnet geometry, air gap; poles shown read-only from Coil); Operating point (speed, current, copper temperature);
Drive (DC link, modulation, current limit); Cooling (h, ambient — h flagged as assumption).

### 10.6 KiCad export / plugin panel (step 6) — `mockups/05_export_kicad.html`

Targets: KiCad board (plugin), KiCad file (`.kicad_pcb`), DXF, SVG, PDF report, JSON, ZIP. KiCad target:
1. **Connection card** — not connected / connected (board name, KiCad version, copper layer count read from the board);
   guidance: open board in PCB editor, enable API server in Preferences › Plugins, start from the plugin toolbar
   (Agent 5 kicad_plugin_evidence §3, `verified` on official pages; real-board behaviour `not tested`, tests T2–T4).
2. **Layer mapping + stack-up comparison** — embodic L1…Ln → KiCad layer selects; copper and board thickness side by side;
   mismatch = warning, missing layers = blocking error with options (“Change design to 4 layers” / “Cancel”), never a
   silent remap.
3. **Placement** — centre X/Y, rotation, group as “embodic stator”, lock, replace previous group (feasibility
   `unresolved`), net names U/V/W/N.
4. **Before placing** checklist — engine stamp, embodic DRC result, stack-up warnings, “run KiCad DRC after placement”
   (no DRC call found in the 9.x API — Agent 5, `unresolved`, T5).
5. Actions — **Place on board…** (opens confirmation when checks fail), **Save .kicad_pcb file…**; note “one placement =
   one KiCad undo step” (`inferred` from begin/push commit in kipy; to confirm in T2).
Rail: preview + item counts (tracks, arcs, vias, pads, outline), unit note (KiCad internal units nm — Agent 5 §5).

---

## 11. KiCad plugin dialog vs standalone app

| Aspect | Standalone app | KiCad plugin dialog |
|---|---|---|
| Window | full window, 3 panes | modal-less dialog, min 880 × 600 px, resizable; remembers size |
| Navigation | step bar | tabs Coil · Phases · Layers · Board · Place (`role="tablist"`), Back / Next in footer |
| Figure | 2-D (3-D view optional, if Agent 6 keeps it) | **2-D only**, no 3-D, no animation, no current-flow display |
| Results | full Results step, charts, compare, report | key numbers (R_ph, Kt, DRC) with status badges; link “Open in the embodic app” for full results/report (if installed; `unresolved`) |
| Stack-up | from Board & rotor | **read from the open board** (copper layer count, thickness) and pre-filled; differences shown |
| Export | files + KiCad target | Place on board (commit), Save file; no PDF/DXF (keep the dialog small; optional) |
| DRC | embodic pre-check | embodic pre-check + instruction to run KiCad DRC |
| Errors | inline | connection states: API server disabled, KiCad version mismatch (kipy version), no board open, too few copper layers, placement failed (assertive message + no partial placement) |
| Fonts/colours | tokens | if wxPython/native: system font and native controls (best screen-reader support); map tokens to the nearest native colours; keep functional colours identical in the preview |
| Keyboard | §8.2 | Ctrl+Tab / Ctrl+Shift+Tab switch tabs; Enter activates the primary only on the Place tab; Esc = Cancel (asks if there are unsaved changes) |
| Persistence | design file | design parameters stored with the board? (`unresolved`, Agent 3/6) — at least “last used parameters” per board path |

Same engine, same parameter ids, same validation and the same status labels in both (`assumption`; consistency
requirement for Agents 3/6).

---

## 12. Icon set (monochrome, 24 px grid, 1.5 px stroke, round caps, `currentColor`)

Drawn for embodic as inline SVG in the mockups (own work, no third-party icon set; usable under the project licence).

| Icon id | Meaning | Used in |
|---|---|---|
| `coil` | spiral coil: trapezoid with nested loops + centre via | step Coil, export |
| `shape-radial-arc`, `shape-parallel-arc`, `shape-parallel-straight`, `shape-parallel-stadium`, `shape-radial-straight`, `shape-radial-stadium` | coil shape options | picker cards |
| `phase` | two offset sine waves | step Phases |
| `cw`, `ccw` | winding direction | phase ring, coil table |
| `layers` | three stacked sheets | step Layers |
| `layer-rotate` | stack with rotation arrow | pair rotation |
| `series`, `parallel` | pair connection | Layers cards |
| `via` | ring with drill | legend |
| `board` | polygon board with bore and holes | step Board & rotor |
| `rotor`, `magnet` | rotor / magnets | Board & rotor, view toggles |
| `results`, `compare` | line chart / overlaid lines | Results |
| `check`, `clearance` | DRC shield / clearance arrows | Checks, dimension toggle |
| `kicad-board` | generic board with arrow out (the KiCad logo is **not** used — trademark) | KiCad target |
| `report`, `file-dxf`, `file-svg`, `file-json`, `export`, `save`, `open` | files and actions | Export, top bar |
| `func`, `link`, `locate`, `info`, `pattern`, `fit`, `zoom-in`, `zoom-out`, `label`, `plug`, `menu`, `more`, `undo`, `redo` | utilities | various |
| `st-verified` ✓, `st-inferred` ≈, `st-assumption` ◇, `st-unresolved` ?, `st-not-tested` ○, `pass`, `fail`, `warn` | status glyphs | badges, checks |

The embodic symbol (three teardrops) is a brand mark, not an icon: used only as logo/app icon
(`brand/embodic-rounded-triangle-icon.png`).

---

## 13. Content and language

- English only, British spelling to match the engineering documents (“centre”, “colour”) — `assumption`; sentence case.
- Terminology: coil (not slot/sector), turn, coils per layer Q, poles 2p, layer pair (X/Y), pair connection, pair
  rotation, centre via, transfer via, phase A/B/C, terminal U/V/W/N, star/delta/open.
- Numbers: SI units always shown; space between value and unit; engineering prefixes (mΩ, µH); 3 significant figures by
  default; integers for counts; digit grouping with a narrow no-break space from 4 digits (1 500 rpm); minus sign “−”.
- Honesty markers: “example” on mock values; “Illustrative, not computed” stamp on drawings until the engine draws them;
  exports carry embodic version, engine version, parameter hash and the line “Verify with KiCad DRC before ordering”.
- No personal names anywhere in UI, files or reports (brief §2).

---

## 14. Open questions for the user (via Fable)

| # | Question | Default if no answer |
|---|---|---|
| Q1 | Dark mode wanted in the first release? | light only; tokens prepared (§3.5) |
| Q2 | Density: compact engineering (14 px, 32 px controls) or comfortable (16 px, 40 px)? | compact desktop, comfortable on touch |
| Q3 | Positive coil = clockwise circulation seen from the top layer — acceptable convention? | yes, shown in the legend |
| Q4 | Product name inside embodic (e.g. “embodic PCB stator”)? The deck mentions “Elysium by embodic” for configuration software. | “embodic” + design name only |
| Q5 | Status-derivation rule §10.4 — confirm with Engineering/Verification | as proposed |
| Q6 | Keep a 3-D view in the standalone app? | 2-D only in Phase 2 |
| Q7 | British or American spelling in the UI? | British |
