Prepared by: Agent 6 — Software Architecture Specialist — model: claude-opus-5-5

# ADR-0005: Application type — hybrid: PySide6 desktop front-end + UI-less KiCad IPC plugin + file export

**Status:** Proposed — pending user approval (UD-01); amended 2026-10-04 with Agent 1 reconciliation
**Date:** 2026-10-04
**Deciders:** User (approval), Fable 5.1 — consulted: Agent 1 (UX), Agent 3 (software)

## Context

- Full comparison with evidence: `app_type_comparison.md` (sources S1–S20).
- Fixed regardless of the choice: Python core (ADR-0001), file writer + IPC plugin (ADR-0004), Windows + Python 3.11+ user.
- Needs: 2-D vector coil view with zoom/pan (≈10⁴ primitives), forms/tables, results with status details, white/grey/black
  theme, WCAG 2.2 AA (REQ-N-11…16), offline, reproducible install, maintainable code.

## Decision (proposed)

Option **C-A**: standalone front-end in **PySide6** (Qt for Python, LGPL-3.0 use, depending on `PySide6-Essentials` only),
plus the UI-less KiCad IPC plugin (ADR-0004) and the `.kicad_pcb` writer. Second choice **C-B1** (local web UI with
FastAPI + hand-written TypeScript/SVG front-end).

## Options Considered

### Option C-A: Hybrid with PySide6 desktop (proposed)
| Dimension | Assessment |
|---|---|
| Complexity | Medium |
| Cost | ≈ 77 MB wheel (PySide6-Essentials 6.11.2, PyPI, `verified`); LGPL compliance tasks |
| Scalability | High — 3-D later via add-ons; front-end replaceable (ADR-0001) |
| Team familiarity | Medium/high (Python only) |

**Pros:** one language; no network listener; in-process calls; mature retained-mode 2-D scene; Qt widgets implement
accessibility (https://doc.qt.io/qt-6/accessible-qwidget.html, `verified` statement). **Cons:** large download; LGPL
obligations (notice, relinkable Qt, source offer — https://www.qt.io/licensing/open-source-lgpl-obligations, `verified`);
weaker automated accessibility tooling than browsers (`inferred`).

### Option C-B1: Hybrid with local web UI (FastAPI + TS/SVG)
| Dimension | Assessment |
|---|---|
| Complexity | Medium/high — two languages, HTTP contract |
| Cost | Small Python deps (FastAPI MIT, uvicorn BSD-3; PyPI, `verified`) |
| Scalability | High |
| Team familiarity | Medium (Xcoil UI precedent in HTML/SVG, `verified`) |

**Pros:** WCAG is web-native and axe-core automates audits; Xcoil's SVG approach proven; light enough to run inside KiCad's
plugin venv. **Cons:** second language and API versioning; local server security (loopback binding, origin checks,
token — `inferred`); browser variance.

### Option A2: wxPython desktop
**Pros:** wxWindows licence with binary exception (https://www.wxwidgets.org/about/licence/, `verified`); 18.5 MB wheel.
**Cons:** custom-drawing ecosystem smaller (`inferred`); SWIG-era advantage (wx inside KiCad) irrelevant for IPC.

### Options A3 Tkinter, A4 Dear PyGui, B2 NiceGUI, B3 Streamlit
Not recommended — rendering/theming/accessibility limits (A3), accessibility (A4), dependency surface (B2: ≈ 25 direct
dependencies, PyPI `verified`), execution model (B3). Details in app_type_comparison.md §4.

## Trade-off Analysis

C-A optimises maintainability (single language), robustness (no server) and offline use; C-B1 optimises accessibility
automation and in-KiCad hosting. Because the plugin is UI-less and the core is UI-agnostic, the choice is reversible at the
cost of rewriting only `embodic.ui` (`inferred` from ADR-0001).

## Consequences

- Easier: one toolchain; packaging with PyInstaller one-folder (PyInstaller licence allows any licence for bundles,
  https://pyinstaller.org/en/stable/license.html, `verified`).
- Harder: LGPL compliance in releases; accessibility verified partly manually (AX-06).
- Revisit: after the Phase 2 rendering spike (L8 in app_type_comparison.md §7) and if the user wants the full UI inside
  KiCad.

## Action Items

1. [ ] User: approve C-A or choose C-B1/other; state the intended embodic licence.
2. [ ] Agent 3: 2-day rendering spike (default layout in QGraphicsView; frame time, memory).
3. [ ] Agent 1: map the screen design to Qt widgets and theme tokens; confirm keyboard model of the geometry view.
4. [ ] Fable: record the user's decision in decision_log.md and set this ADR to Accepted or Superseded.

## Amendment 1 — reconciliation round 1 (2026-10-04)

- Agent 1's six screens/steps are mapped to Qt views (architecture_draft.md §10.1); mockups are HTML but specify
  behaviour and tokens that map to Qt widgets and QSS.
- With C-A, **phone layouts are out of scope** (Agent 1 mockup 06, UX-AC-11 "no horizontal scroll at 360 px", 44 px coarse
  targets). What remains: a minimum window of **960 × 540** device-independent px (1920 × 1080 at 200 %), three panes
  ≥ 1280 px, two panes with a collapsible results panel at 960–1279 px (Agent 1's tablet pattern), no horizontal scrolling
  of form panels (REQ-N-15). If the user values phone/tablet use, that is an argument for C-B1.
- Agent 1's web-phrased acceptance tests (DOM, axe-core) translate to the Qt widget tree with `objectName` = Agent 1's
  element ids (architecture_draft.md §19) and the token-based contrast script.
