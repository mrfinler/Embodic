Prepared by: Agent 6 - Software Architecture Specialist - model: claude-opus-5-5

# ADR-0011: Theming and colour policy

**Status:** Proposed (implements D-011 and D-012)
**Date:** 2026-10-04
**Deciders:** Fable 5.1; consulted: Agent 1 (tokens, icons, CVD validation)

## Context

D-011: phases A, B, C are red, blue and green in the geometry view and charts; UI chrome stays white, grey and black;
light and dark themes both ship in Phase 2; a greyscale and hatching mode stays available for accessibility; red-green
confusion is mitigated by labels, hatching and line style, never colour alone. D-012: a MATLAB-style toolstrip with an
original monochrome SVG icon set by Agent 1. Agent 1's `docs/phase1/design/tokens.json` already holds a light theme, a
provisional dark theme, a pure greyscale variant, CVD validation results and the greyscale and hatch mapping.

## Decision

1. **Tokens are data.** Agent 1 owns `resources/themes/light.json` and `dark.json`, derived from `tokens.json` with the
   same token names. `embodic.ui.theme.load_theme()` parses them into `ThemeTokens` (Qt-free); `embodic.ui.views.style`
   turns tokens into one Qt style sheet and a `QPalette`. No colour literal appears in Python code outside these files
   (lint in `tests/static`).
2. **Theme choice** is `light`, `dark` or `system` (follows the OS colour scheme), switchable at runtime, stored in user
   settings and in the project's `ui` block. Both theme files must define every token; a missing token is a startup error
   because the build ships both.
3. **Phase styles.** `PhaseStyle` per theme: colour (red, blue, green), grey level, hatch angle (none, 45, 135 degrees),
   dash pattern and label. Every phase drawing carries its label and dash pattern in both modes; colour is added on top.
4. **Render modes.** `PhaseRenderMode` is `colour` or `greyscale_hatch`. The user toggles it on the View tab. The PDF
   report defaults to `greyscale_hatch` (prints on monochrome printers); Windows high-contrast forces it. Hatching is drawn
   only inside the coil eye and never crosses copper (REQ-N-23).
5. **Icons.** Monochrome SVG files drawn with `currentColor`, one per `ToolstripAction.icon` stem. The view renders each
   icon with the theme's foreground token, so one file serves both themes. No icon fonts and no third-party icon sets.
6. **Checks.** `tools/contrast_check.py` computes WCAG ratios for every text and component token pair in both themes
   (AX-01), the phase colours against the canvas (AX-08) and icon foreground against toolstrip background (AX-09).
   Agent 1's palette validator runs on both theme files in U-M4r.

## Options considered

### Option A: token JSON at runtime, generated style sheet (chosen)

| Dimension | Assessment |
|---|---|
| Complexity | Low: one parser, one style generator |
| Cost | Agent 1 keeps editing JSON, as in Phase 1 |
| Scalability | A third theme is one more file |
| Team familiarity | High (Phase 1 tokens already in this form) |

**Pros:** designers edit data; tests enumerate tokens; the same tokens drive SVG and PDF exports.
**Cons:** style sheet generation must cover every widget type used.

### Option B: Qt palette only

**Pros:** native look. **Cons:** a palette cannot express phase styles, hatch rules or focus ring sizes; exports would
need a second colour source.

### Option C: hand-written `.qss` file per theme

**Pros:** no generator. **Cons:** two files drift; exports and contrast checks cannot read them as data.

## Trade-off analysis

A keeps one source of truth for colours across widgets, canvas, SVG and PDF, which is what AX-01, AX-08 and the export
tests need. The generator is small because the widget set is small.

## Consequences

- Easier: contrast and CVD checks are scripts over data; a dark-theme defect is a token fix.
- Harder: Agent 1 must keep both theme files complete; U-M4r's done predicate checks this.
- Revisit: if the user reports red-green confusion in practice, change the dash patterns or default to
  `greyscale_hatch`; no code change beyond tokens.

## Action items

1. [ ] U-M4r (Agent 1): final `light.json`, `dark.json`, icon set.
2. [ ] U-M4b: `theme.py`, `views/style.py`, toolstrip bar, `tools/contrast_check.py`.
3. [ ] U-M4a: SVG and PDF writers take `PhaseRenderMode` and read phase styles from the same tokens.
