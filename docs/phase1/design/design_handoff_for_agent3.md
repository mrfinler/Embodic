Prepared by: Agent 1 — UX/UI Expert Designer — model: claude-opus-5-5

# Design handoff for Agent 3 (Senior Software Engineer) — Phase 1 draft, 2026-10-04

Read with `design_spec_draft.md` (rationale) and the mockups in `mockups/` (open the `.html` files; PNG renders in
`mockups/png/`). Everything here is a draft for Phase 2; numbers in mockups are examples, drawings are illustrative.
Status labels per PROJECT_BRIEF §3.

## 1. Tokens

Tier 1 → tier 2 names as used in the mockups (`:root` in every mockup file). Contrast values computed (`verified`).

| Token | Light | Dark (provisional) | Use |
|---|---|---|---|
| `--surface` | `#ffffff` | `#171717` | panels, inputs, canvas |
| `--bg-app` / `--board-fill` | `#f7f7f7` | `#0f0f0f` | app background, PCB fill in drawings |
| `--surface-sunken` | `#efefef` | `#232323` | hover, table head, EQ chip |
| `--surface-selected` | `#e4e4e4` | `#2e2e2e` | selected row |
| `--surface-inverse` | `#141414` | `#f2f2f2` | primary button, selected segment |
| `--text-1` | `#141414` (18.42:1) | `#f2f2f2` | primary text |
| `--text-2` | `#454545` (9.59:1) | `#c8c8c8` | secondary text |
| `--text-3` | `#666666` (5.74:1; 4.99 on sunken) | `#a0a0a0` | hints, units, captions |
| `--text-disabled` | `#9a9a9a` | `#6e6e6e` | disabled only |
| `--border-control` | `#858585` (3.69:1) | `#7d7d7d` | every control boundary; only on surface / bg-app / sunken |
| `--border-strong`, `--focus-ring` | `#141414` | `#f2f2f2` | focus 2 px + 2 px offset |
| `--divider` | `#dcdcdc` | `#2e2e2e` | decorative separators |
| `--grid-line` | `#e6e6e6` | `#2a2a2a` | chart grid (solid hairline) |
| `--phase-a` | `#5c4383` | `#73599e` | phase A (data only) |
| `--phase-b` | `#87660c` | `#9b7928` | phase B (data only) |
| `--phase-c` | `#438ebf` | `#539dcf` | phase C (data only) |
| `--phase-a/b/c-grey` | `#262626` / `#5e5e5e` / `#8a8a8a` | `#7a7a7a` / `#a8a8a8` / `#e0e0e0` | greyscale mode, + coil-eye fill none / 45° / 135° hatch (full list: `tokens.json`) |
| `--status-pass` | `#2f6a47` (6.42:1) | `#6fb38a` | ✓ Pass glyph + word |
| `--status-fail` | `#a6332c` (6.71:1) | `#e2776d` | ✕ Fail glyph + word, DRC marker, fail count |
| `--font-ui` | `"Segoe UI", "Noto Sans", "Liberation Sans", system-ui, sans-serif` | | 14 px base, 16 px on touch/phone |
| `--font-mono` | `"Cascadia Mono", "JetBrains Mono", Consolas, "Liberation Mono", "DejaVu Sans Mono", monospace` | | numbers, units, codes; tabular figures |
| `--fs-*` | 12 / 13 / 14 / 16 / 20 / 24 / 32 px | | 12 px minimum |
| `--sp-1 … --sp-8` | 2 / 4 / 8 / 12 / 16 / 24 / 32 / 48 px | | spacing |
| `--radius-s/m/l` | 4 / 6 / 10 px | | controls / cards / dialogs |
| `--control-h` | 32 px (44 px when `pointer: coarse`) | | control height |

Phase set validated with the dataviz validator (all pairs, light: CVD ΔE 17.8, normal 20.9; dark: CVD 14.6) — `verified`.
Fonts are not bundled in the mockups; licences of Noto/Liberation/Cascadia/JetBrains Mono (SIL OFL 1.1) are `inferred` —
check LICENSE files before bundling. No runtime CDN font requests.

## 2. Components and behaviour notes

| Component | Must do |
|---|---|
| Numeric field | text input `inputmode="decimal"`; unit suffix element with id, referenced by `aria-describedby` together with hint (+ error first when invalid); ↑/↓ ± step, Shift ×10; Enter commits, Esc reverts; validate on blur, clear on input; integers shown without decimals |
| Segmented control | radio group in `<fieldset>`/`<legend>`; selected = inverted; never more than 5 options (else `<select>`) |
| Picker cards | radio cards with shape drawing; same semantics as segmented control |
| Inline notice | shown whenever the engine changes a user value: “Changed from X to Y: reason” + Undo; `role="status"`; toast may echo it but never replaces it |
| Error | `aria-invalid="true"`, message under the field, entry in Checks; last valid geometry stays at 35 % with stamp |
| Step navigation | links with `aria-current="step"`, state text (✓ / “n fail”); Alt+1…6 |
| View toolbar | `role="toolbar"`, Colour/Greyscale (also automatic in print and forced colours), labels toggle (`aria-pressed`), fit/zoom |
| Geometry canvas | focusable, `role="img"` + title/description; keys: arrows pan, + − 0 zoom/fit, L, G, [ ], A/B/C, Esc (only while focused); stamp “Illustrative, not computed” → “Computed · engine vX.Y” |
| Layer chips | checkbox chips; unchecked = dashed + strike-through (not colour/opacity only) |
| Status badge | five values: verified (ink fill ✓), inferred (outline ≈), assumption (dashed ◇), unresolved (dotted, grey fill ?), not tested (hairline ○); hidden “Status:” prefix |
| Result card / key result row | value + unit + status badge + EQ link(s) + tags; disclosure “How was this computed” (equation, inputs with units/origin/status, assumptions, limitations, validation, sources, Copy trace) |
| DRC list item | glyph, rule code, message, measured vs required with units, layer, Locate (zooms canvas, dims copper to 35 %) |
| Tabs | roving tabindex, ←/→/Home/End, `aria-controls`, panels `aria-labelledby` (Xcoil lacked all of these) |
| Dialog | native `<dialog>.showModal()`; initial focus on the safe action; Esc closes |
| Toast | `popover="manual"`, `role="status"`, 6 s, pauses on hover/focus, optional action |
| Status bar | compute state + engine version; polite announcement after recompute (≤ 1 per s) |
| Charts | one unit per y axis; legend + direct labels; crosshair tooltip also by keyboard; “Data table” disclosure; status badge + EQ links |

## 3. Element ids per screen

Ids are stable contracts for tests (Agent 4) and for porting. Reconciliation round: the canonical ids proposed in
`architecture/architecture_draft.md` §19 (derived from model field names) are **accepted** and used below and in the
re-rendered mockups; the old→new list and the engine bindings are in `screen_to_view_map.md`. In mockups 03 (frame B) and 05 the repeated shell is
prefixed (`fb-` in 03 frame B); in the app each id is unique.

**Shell (all desktop screens):** `#app-topbar`, `#doc-name`, `#doc-state`, `#btn-undo`, `#btn-redo`, `#btn-open`,
`#btn-save`, `#btn-more`, `#btn-export`, `#step-nav`, `#step-coil`, `#step-phases`, `#step-layers`, `#step-board`,
`#step-results`, `#step-export`, `#engine-state`, `#panel-step`, `#panel-title`, `#figure`, `#fig-title`, `#fig-toolbar`,
`#fig-canvas`, `#fig-layer-chips`, `#fig-legend`, `#rail-results`, `#rail-drc`, `#statusbar`, `#st-compute`, `#st-drc`,
`#st-counts`, `#st-units`, `#st-cursor`. Figure tools: `#btn-labels`, `#btn-fit`, `#btn-zoom-in`, `#btn-zoom-out`;
`#btn-drc-locate`.

**01 Overview / 02 Coil:** `#param-coil-count` (Q), `#param-poles` (2p), `#hint-combination`, `#param-side-style`
(radial | parallel), `#param-end-style` (arc | straight | stadium), `#param-corner-radius`, `#param-turns`,
`#param-turns-notice`, `#param-trace-width`, `#param-clearance` (+ `-error`), `#param-x-inward-sense` (cw | ccw),
`#param-r-inner`, `#param-r-outer`, `#param-coil-gap`, `#param-first-coil-angle`; rail key results `#res-r-phase`, `#res-ke`,
`#res-kt`, `#res-ls`, `#res-dt` each with `-value`, `-unit`, `-eq`; `#toast-demo`.

**03 Phases:** `#param-connection` (star | delta | open), `#param-phase-assign-mode` (auto | manual),
`#param-phase-sequence` (abc | acb), `#phase-pattern-string`, `#phase-balance-status`, `#param-terminal-location`,
`#param-terminal-u|v|w|n`, `#phase-ring`, `#phase-table` (row per coil; manual mode adds `#coil-<n>-phase`,
`#coil-<n>-polarity`, `#coil-<n>-direction`).

**03 Layers:** `#param-layer-count` (2 | 4 | 6 | 8), `#param-pair-connection` (series | parallel), `#param-rotation-mode`
(none | alt | custom), `#param-pair-rotation` (°), `#param-via-drill`, `#param-via-pad`, `#param-vias-per-transition`,
`#layer-list`, `#layer-1 … #layer-n`, `#layer-path-diagram`, `#layer-overlay`.

**04 Results:** `#results-nav`, `#res-filter-status`, `#btn-export-trace`, cards `#res-card-<key>` with
`#res-<key>-value`, `#res-<key>-unit`, `#<key>-how` (disclosure); keys used: `r-phase`, `ke`, `ls`, `j`;
`#chart-backemf`, `#chart-backemf-table`.

**05 Export:** `#export-targets`, `#btn-export-zip`, `#kicad-connection-status`, `#btn-kicad-connect`,
`#kicad-layer-map`, `#kicad-map-L1 … L6`, `#param-kicad-origin-x`, `#param-kicad-origin-y`, `#param-kicad-rotation`,
`#kicad-net-names`, `#export-checklist`, `#btn-kicad-place`, `#btn-save-kicad-file`, `#kicad-preview-counts`,
`#dlg-place-confirm`. Plugin dialog: `#kicad-plugin-dialog`, `#plg-tab-coil|phases|layers|board|place`,
`#plg-origin-x`, `#plg-origin-y`, `#plg-btn-place`.

**06 Phone:** same parameter ids; `#app-topbar`, `#fig-canvas`, `#rail-drc`, `#panel-step`, `#step-nav` (bottom bar).

Naming rule (architecture §19, accepted): `#param-` + kebab-case of the model field name without its unit suffix
(`trace_width_mm` → `#param-trace-width`), `#res-<quantity>` for results, `#btn-<action>` for commands.

## 4. UX acceptance criteria (for Agent 6 → requirement ids, Agent 4 → tests)

| Id | Criterion | How to test |
|---|---|---|
| UX-AC-01 | Every numeric result shows value, unit and exactly one of the five status labels. | DOM: each `[id^=res-][id$=-value]` has sibling unit + badge |
| UX-AC-02 | Every computed result links to an EQ-ID (or is tagged `input` / `derived` / `count`) and has a “How was this computed” disclosure listing formula, inputs with units, assumptions, limitations, validation and sources. | DOM + content check per result |
| UX-AC-03 | No visible string “Xcoil”, no Thai characters, no personal names; embodic logo present in top bar and exports. | text scan (like Xcoil UI-12/UI-14) |
| UX-AC-04 | UI chrome uses only neutral tokens; functional colours appear only on phase marks/legends/charts and pass/fail elements. | computed-style scan for non-grey colours outside allowed selectors |
| UX-AC-05 | Phases distinguishable without colour: greyscale mode shows A/B/C by lightness + hatch + labels; colour is never the only cue for state. | screenshot in greyscale mode; forced-colors emulation |
| UX-AC-06 | Text contrast ≥ 4.5:1 (≥ 3:1 large), control boundaries and focus indicator ≥ 3:1. | axe-core + token check |
| UX-AC-07 | All controls reachable by keyboard in visual order; no keyboard trap; F6 cycles the six regions; tabs/toolbars use arrow keys. | scripted Tab/Shift+Tab walk, compare with DOM order |
| UX-AC-08 | Visible focus indicator on every focusable element. | screenshot per focus stop |
| UX-AC-09 | The geometry canvas is focusable and can be panned and zoomed by keyboard; single-key shortcuts act only while it has focus. | keyboard test |
| UX-AC-10 | Hit targets ≥ 24×24 px on desktop and ≥ 44×44 px on coarse pointer / phone. | bounding-box scan |
| UX-AC-11 | No horizontal page scroll at 360 px width; wide tables and the drawing scroll inside their own containers. | `scrollWidth == clientWidth` at 360 px |
| UX-AC-12 | Fields that do not apply to the current configuration are hidden; a temporarily inapplicable field shows its reason. | config matrix test |
| UX-AC-13 | When the engine changes a user value, an inline notice with old → new value and Undo appears next to the field and is announced politely; Undo restores the value. | scripted clamp case |
| UX-AC-14 | Invalid input: field gets `aria-invalid` and an inline message; Checks lists it; the last valid geometry stays visible, dimmed, with a “Last valid layout” stamp. | scripted invalid case |
| UX-AC-15 | Every input shows its unit and the unit is in the accessible description. | DOM check |
| UX-AC-16 | Placing on a KiCad board or exporting with DRC failures requires an explicit confirmation listing the failures; focus starts on the safe action. | scripted export |
| UX-AC-17 | Drawings not produced by the engine carry “Illustrative, not computed”; engine drawings and exports carry the engine version stamp. | DOM / file content check |
| UX-AC-18 | Charts: one unit per y axis; legend for ≥ 2 series plus direct labels; data table available; tooltip reachable by keyboard. | chart audit |
| UX-AC-19 | Counts (coils, turns, poles, vias, layers) are shown as integers; compare deltas use sign + glyph, not red/green. | formatting test |
| UX-AC-20 | `prefers-reduced-motion: reduce` disables all transitions; no animation runs by default. | emulation |
| UX-AC-21 | KiCad plugin dialog fits 880 × 600 px with the Place button visible without scrolling; reads the board’s copper layer count and blocks placement when layers are missing (no silent remap). | plugin smoke test (with Agent 5 T2) |
| UX-AC-22 | Recompute: results update ≤ 300 ms after the last edit for the default design, or show “Updating…” with previous values dimmed; a polite announcement summarises the result. | timing test (`unresolved` target until the Python engine is measured) |

## 5. Notes for implementation

- Port the declarative form model idea from Xcoil (`GROUPS`, ui.js:16–139) but split by step, drop the topology `only`
  codes (spiral only) and replace “disable when not applicable” with hide (ux_analysis C1).
- Keep the “last valid layout” behaviour (ux_analysis W1).
- The status label of each result must come from data (equation register + validation results), not be hard-coded in
  the UI (`assumption`, needs the register format from Agents 2/6).
- Mockup generator scripts live in my scratchpad only; the HTML files are self-contained (inline CSS + SVG sprite),
  reference only `brand/*.png`, and load no external resources.
