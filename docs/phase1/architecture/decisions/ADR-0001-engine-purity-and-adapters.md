Prepared by: Agent 6 — Software Architecture Specialist — model: claude-opus-5-5

# ADR-0001: Pure Python engine core with thin adapters (ports and adapters)

**Status:** Proposed
**Date:** 2026-10-04
**Deciders:** Fable 5.1 (coordinator) — consulted: Agent 3 (software), Agent 4 (verification)

## Context

- The calculation and geometry engines must be Python (BRIEF §1) and must serve a standalone UI and a KiCad 9.x plugin
  (decision_log D-004: "Architecture must keep the engines UI-agnostic so a plugin host and a standalone UI share them").
- KiCad 9.x IPC plugins run as separate processes with KiCad's bundled Python and a per-plugin venv (A5-KI §3,
  `verified`); the standalone app runs in the user's Python 3.11+ (BRIEF §1). The same engine code must import cleanly
  in both interpreters without UI toolkits or KiCad modules present.
- Golden regression, oracle and property tests must run headless in CI (ADR-0006).
- Xcoil v3 already separates `engine.js` (UMD, runs in Node and browser) from the UI files (`ui*.js`), which is what made
  its 131 Node-run tests possible (`/home/claude/serpentine/run-tests.js`; A2-REV C0 "131/131 passed", `verified`).

## Decision

Adopt a ports-and-adapters structure:
- **Core** (`embodic.units`, `errors`, `results`, `model`, `winding`, `geometry`, `drc`, `physics`, `io`) = pure Python +
  NumPy; no I/O except in `embodic.io` writers/loaders that take explicit paths; no global mutable state; frozen dataclasses.
- **Facade** `embodic.api.compute()` is the single entry point for adapters.
- **Adapters**: `embodic.ui` (standalone front-end, ADR-0005), `embodic.cli` (headless), `embodic_kicad_plugin` (IPC,
  ADR-0004). Adapters own threading, logging configuration, file dialogs and KiCad calls.
- Enforce the layering with import-linter contracts in CI (architecture_draft.md §4).

## Options Considered

### Option A: Pure core + thin adapters with enforced import contracts (chosen)
| Dimension | Assessment |
|---|---|
| Complexity | Medium — layering discipline, contracts in CI |
| Cost | Low — one extra facade module and contract config |
| Scalability (more front-ends / topologies) | High — new adapters and generators plug in |
| Team familiarity | High — common Python packaging pattern (`inferred`) |

**Pros:** one engine for UI, CLI, plugin; headless tests; front-end replaceable (ADR-0005 stays reversible); the plugin
venv needs no GUI toolkit. **Cons:** adapters must translate events and types; discipline required for "no UI in core".

### Option B: Monolithic desktop application (UI and calculations interleaved)
| Dimension | Assessment |
|---|---|
| Complexity | Low at first, high later |
| Cost | Low initially |
| Scalability | Low — plugin would need the UI toolkit or a fork |
| Team familiarity | High |

**Pros:** fastest first screen. **Cons:** violates D-004; engine untestable headless; plugin duplicates logic.

### Option C: Plugin-first (engine lives inside the KiCad plugin; standalone wraps it)
| Dimension | Assessment |
|---|---|
| Complexity | High — KiCad process model drives everything |
| Cost | Medium |
| Scalability | Low — KiCad version churn propagates into the engine |
| Team familiarity | Low |

**Pros:** tight KiCad integration. **Cons:** IPC needs a running KiCad GUI (A5-KI §3) → engine unusable without KiCad;
contradicts "engine in Python, runnable on the user's Python 3.11+" (A5-KI §5 item 1).

### Option D: Engine as a local service (HTTP/RPC), UI and plugin as clients
| Dimension | Assessment |
|---|---|
| Complexity | High — protocol, versioning, process lifecycle |
| Cost | Medium |
| Scalability | High |
| Team familiarity | Medium |

**Pros:** language-independent clients. **Cons:** network surface and lifecycle management for a single-user desktop
tool; unnecessary when all clients are Python (`inferred`).

## Trade-off Analysis

A gives the reuse and testability of D without a network protocol, and avoids B's and C's coupling. The cost is a thin
translation layer in each adapter, which is small compared with duplicated physics or untestable UI code (`inferred`).

## Consequences

- Easier: headless golden/oracle/property tests; swapping the front-end; running the engine inside KiCad's venv.
- Harder: adapters cannot reach into engine internals; long-running work must use the facade's cancellation token.
- Revisit: if a non-Python client appears (e.g. a web front-end, ADR-0005 option C-B1), add an HTTP adapter on top of
  `embodic.api` — the core remains unchanged.

## Action Items

1. [ ] Agent 3: create the package skeleton and import-linter contracts (P2 start).
2. [ ] Agent 4: add MT-01 (contract check) to the CI gate.
3. [ ] Keep `embodic.api` signatures stable; changes require a note in CHANGELOG.
