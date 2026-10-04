Prepared by: Agent 6 - Software Architecture Specialist - model: claude-opus-5-5

# ADR-0005: Application type (Phase 2 amendment: PySide6 desktop approved, plugin removed)

**Status:** Accepted (D-010, user, 2026-10-04), amended for Phase 2. Amends the Phase 1 proposal
`docs/phase1/architecture/decisions/ADR-0005-application-type.md`.
**Date:** 2026-10-04
**Deciders:** User (D-010); Fable 5.1; consulted: Agent 1, Agent 3

## Context

Phase 1 proposed option C-A of `docs/phase1/architecture/app_type_comparison.md`: a PySide6 desktop front-end, plus a
UI-less KiCad IPC plugin and a `.kicad_pcb` writer. The user approved the desktop application and removed everything
KiCad (D-009, D-010). Phase 2 also adds a MATLAB-style toolstrip (D-012), light and dark themes (D-011) and a new-design
flow (D-014), all of which live in the UI.

## Decision

1. The deliverable is a Python 3.11+ desktop application built on **PySide6-Essentials** 6.11.x (LGPL-3.0-only OR
   GPL-2.0-only OR GPL-3.0-only, PyPI read 2026-10-04), Windows primary, Linux for development and CI. No Addons, no
   QtWebEngine.
2. The C-A parts that served KiCad are removed: no plugin, no compact plugin window, no IPC launcher (ADR-0004).
3. The UI follows MVVM with a hard seam: view-models (`embodic.ui.viewmodels`), theme tokens, the toolstrip table and the
   string catalogue are plain Python and import no Qt (contracts C2 and C3). Qt widgets in `embodic.ui.views` subscribe to
   `Observable` values and call view-model commands. Computation runs in `embodic.ui.workers` off the GUI thread.
4. UI tests run with pytest-qt on the `offscreen` Qt platform; view-model tests need no Qt at all.

## Options considered

### Option C-A minus plugin: PySide6 desktop (chosen by the user)

| Dimension | Assessment |
|---|---|
| Complexity | Medium: one toolkit, native 2-D canvas (QGraphicsView) |
| Cost | LGPL obligations when bundling (dynamic linking, replaceable libraries), `inferred`, not legal advice |
| Scalability | About 10^4 primitives per view drawn as one item per (layer, phase, width run), Phase 1 §11 |
| Team familiarity | Medium |

**Pros:** offline, one language, native accessibility for built-in widgets, file dialogs, toolstrip feasible with
standard widgets.
**Cons:** custom canvas needs its own accessible interface; Qt stubs vary between versions, so the Qt modules are typed
non-strictly.

### Option C-B1: local web UI (FastAPI plus TypeScript front-end)

**Pros:** could reuse Xcoil's HTML ideas.
**Cons:** two languages, a local server and a browser; not chosen by the user.

### Qt view-models versus Qt-free view-models (sub-decision of this amendment)

| Dimension | Qt view-models (QObject, signals) | Qt-free view-models (chosen) |
|---|---|---|
| Testability | needs a QApplication in every test | plain pytest; state machine tested directly |
| Interface depth | signals spread across widgets | one `SessionState` union and a command list |
| Cost | none extra | a 30-line `Observable` and a thin binding in each view |

## Trade-off analysis

The user settled the toolkit. The sub-decision on view-models trades a small binding layer for tests that run without a
display and a session model whose states are explicit (`SessionEmpty`, `SessionDrafting`, `SessionComputed`). The
new-design flow is a state machine, so that trade pays for itself.

## Consequences

- Easier: UI logic is tested without Qt; the toolstrip and themes are data the tests can enumerate.
- Harder: every view needs a small subscription block; reviewers check that no view keeps state of its own.
- Revisit: if a Qt-specific behaviour cannot be expressed through `Observable` (for example drag and drop on the
  canvas), keep it inside the view and document it there.

## Action items

1. [ ] U-M1a: contracts C2 and C3 in `pyproject.toml`.
2. [ ] U-M4b: `Observable`, outcome and appearance view-models, worker, shell.
3. [ ] U-M4c, U-M4d: session, results and export view-models with their views.
