Prepared by: Agent 6 — Software Architecture Specialist — model: claude-opus-5-5

# ADR-0009: Units convention — millimetres for lengths, SI otherwise, unit-suffixed names, conversion at boundaries

**Status:** Proposed
**Date:** 2026-10-04
**Deciders:** Fable 5.1 — consulted: Agent 2 (formula units), Agent 3

## Context

- Agent 2's equations mix mm (geometry inside formulas where marked) and SI (A2-EQ preamble: "Units: SI unless stated;
  geometry in mm inside formulas where marked"); the Xcoil engine works in mm and converts (e.g. Ke from T·mm² × 1e-6,
  EQ-06) (`verified` reading).
- KiCad's IPC API uses nanometre integers (A5-KI §5 item 5, `verified`); `.kicad_pcb`, DXF (`$INSUNITS 4`) and SVG
  exports of Xcoil use mm (engine.js l.2798, l.2844, `verified`).
- Unit mistakes are a classic source of silent errors; the user requires units shown with every result.
- Pint 0.26 requires Python ≥ 3.12 (PyPI, `verified`); the minimum here is 3.11.

## Decision

Rules U1–U7 of architecture_draft.md §6: mm for all lengths (float64), radians inside the core, SI for everything else,
unit suffix on every dimensional field and argument, conversions only through `embodic.units`, mm→nm only in the KiCad
adapter, closed unit vocabulary on `Traceable`, no runtime unit library, dimensional consistency verified by scaling
property tests (PR-06) and by a lint rule against bare power-of-ten literals in `embodic.physics`.

## Options Considered

### Option A: mm/SI with suffix naming + boundary conversion + scaling tests (chosen)
| Dimension | Assessment |
|---|---|
| Complexity | Low |
| Cost | No runtime overhead |
| Scalability | High |
| Team familiarity | High (matches Xcoil and PCB practice) |

**Pros:** readable, fast, no dependency. **Cons:** relies on naming discipline + tests, not on the type system.

### Option B: Runtime unit objects (Pint) everywhere
| Dimension | Assessment |
|---|---|
| Complexity | Medium |
| Cost | Overhead in inner loops (`inferred`); Python ≥ 3.12 for current Pint |
| Scalability | Medium |
| Team familiarity | Medium |

**Pros:** automatic dimensional checking. **Cons:** version conflict with 3.11; slower kernels; serialisation friction.

### Option C: SI metres everywhere (geometry in m)
**Pros:** one system. **Cons:** unnatural for PCB geometry and exports (constant ×1000 at every boundary); Xcoil port
friction. Rejected.

### Option D: Static unit types (`typing.NewType("Millimetre", float)`) checked by mypy
**Pros:** zero runtime cost. **Cons:** arithmetic decays to `float`, so protection is limited to function boundaries
(`inferred`). Could be added later on public signatures as a complement to A.

## Trade-off Analysis

A gives most of the safety at no runtime cost when combined with property tests that would expose a wrong scale
(e.g. R ∝ 1/t, Ke ∝ B_r, length scaling).

## Consequences

- Easier: direct mapping to PCB tools; fast kernels.
- Harder: reviewers must enforce suffixes; MT-05 lint rule needed.
- Revisit: Option D for public API signatures in P3 if reviews find unit slips.

## Action Items

1. [ ] Agent 3: `embodic/units.py` (conversions, `Unit` vocabulary, display forms) + UT-UNI-01…03.
2. [ ] Agent 4: PR-06 scaling properties.
