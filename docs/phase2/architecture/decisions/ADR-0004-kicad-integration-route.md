Prepared by: Agent 6 - Software Architecture Specialist - model: claude-opus-5-5

# ADR-0004: KiCad integration route (Phase 2 status: superseded, KiCad out of scope)

**Status:** Superseded by decision D-009 (user, 2026-10-04). Replaces the Phase 1 proposal
`docs/phase1/architecture/decisions/ADR-0004-kicad-integration-route.md`.
**Date:** 2026-10-04
**Deciders:** User (D-009); recorded by Fable 5.1; written by Agent 6

## Context

Phase 1 proposed a `.kicad_pcb` writer as baseline, a KiCad 9 IPC plugin as the plugin route and no SWIG
(Phase 1 ADR-0004, evidence in `docs/phase1/evidence/kicad_plugin_evidence.md`). The user then removed KiCad from Phase 2
twice: first the plugin, then the `.kicad_pcb` export (D-009). D-004's rule that the engines stay UI-agnostic is kept, so
a later phase can add an integration without touching the core.

## Decision

Phase 2 ships no KiCad code at all: no plugin, no IPC client, no `.kicad_pcb` writer, no mm to nm conversion, no KiCad
layer map in the project file and no "imported from KiCad" provenance. All REQ-K requirements are withdrawn
(`requirements.md` §3). Test MT-07 and import contract C4 fail the build if `kipy` or `pcbnew` is imported, if a
`.kicad_pcb` writer appears, or if "KiCad" shows up in the string catalogue or CLI choices.

## Options considered

### Option A: remove KiCad completely, guard the removal (chosen)

| Dimension | Assessment |
|---|---|
| Complexity | Low: two packages and a project-file section disappear |
| Cost | None now; a later integration re-reads Phase 1 §9 |
| Scalability | Unchanged; the core stays UI-agnostic |
| Team familiarity | High |

**Pros:** smallest code base; no unverified KiCad 9 file-format or IPC behaviour in the product (Phase 1 smoke tests T0 to
T6 were never run); the scope guard makes the decision visible in CI.
**Cons:** users who want a board in KiCad import the DXF by hand.

### Option B: keep only the `.kicad_pcb` writer

**Pros:** the Xcoil writer is small and was validated with kiutils in Xcoil.
**Cons:** contradicts D-009, where the user removed the `.kicad_pcb` export explicitly (quoted in `docs/decision_log.md`); KiCad 9 format version `unresolved`.

### Option C: keep the plugin design dormant in the tree

**Pros:** faster restart later.
**Cons:** dead code that no test exercises; it rots and misleads the next contributor.

## Trade-off analysis

Option A costs nothing that the user asked to keep. The one thing worth preserving for a later phase is the knowledge,
and that lives in the Phase 1 documents, not in dormant code.

## Consequences

- Easier: smaller dependency list (no kicad-python, protobuf, pynng), no nm rounding rules, simpler project file.
- Harder: nothing in Phase 2.
- Revisit: if the user re-opens KiCad, start from Phase 1 ADR-0004 and architecture §9, add an adapter package above
  `embodic.api`, and re-activate the REQ-K IDs (they keep their numbers).

## Action items

1. [ ] U-M1a: MT-07 scope guard and contract C4 in place from the first commit.
2. [ ] U-M2f: project file schema v1 without a `kicad` section.
