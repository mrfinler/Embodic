Prepared by: Agent 6 — Software Architecture Specialist — model: claude-opus-5-5

# ADR-0007: Project file format — versioned JSON with published schema, migrations, canonical hash and provenance

**Status:** Proposed
**Date:** 2026-10-04
**Deciders:** Fable 5.1 — consulted: Agent 3, Agent 1 (what UI state is persisted)

## Context

- Users must save/load designs reproducibly (user wish: reproducible; REQ-F-15); results and exports must be traceable to
  their inputs (REQ-T-07).
- Defaults are `assumption` (A2-TOP §5.2) and must stay marked until edited (REQ-T-06) → per-field provenance must persist.
- The KiCad plugin reads the project (ADR-0004) in KiCad's venv; the core may depend only on stdlib + NumPy (ADR-0008).
- The schema will evolve (serpentine/wave later, REQ-F-19; Halbach; new options).

## Decision

- Format: UTF-8 JSON, file name `<name>.embodic.json`, top-level `format`, `schema_version` (integer), `app_version`,
  `saved_utc`, `design_hash`, `design`, `provenance`, `kicad`, `ui` (sketch in architecture_draft.md §14).
- Topology-specific parameters as tagged unions (`"kind": "spiral" | "serpentine" | "wave"`), so later generators add
  kinds without breaking old files.
- Hash: SHA-256 over the canonical JSON of `design` only (sorted keys, compact separators, shortest round-trip float repr,
  UTF-8); `provenance`, `kicad`, `ui` excluded.
- Loader: hand-written typed loader with JSON-pointer issue paths (no runtime schema dependency); published JSON Schema
  (Draft 2020-12) kept in step by tests using `jsonschema` (test-only).
- Migrations: chained `migrate_vN_to_vN+1` pure functions with tests per step; newer versions refused; migration reported
  as an info issue; never auto-overwrite.
- Angles stored as `_deg` in the file for readability, converted once on load (ADR-0009).

## Options Considered

### Option A: JSON + schema + migrations (chosen)
| Dimension | Assessment |
|---|---|
| Complexity | Low/medium |
| Cost | No runtime dependency (`json` in stdlib) |
| Scalability | High — tagged unions, versioned migrations |
| Team familiarity | High |

**Pros:** stdlib read/write; diff-able in git; tool-independent; exact float round trip via `repr` (`inferred`, Python's
float repr is shortest round-trip). **Cons:** no comments in files; verbose.

### Option B: TOML
| Dimension | Assessment |
|---|---|
| Complexity | Medium (arrays of nested tables for layer lists) |
| Cost | Python 3.11 `tomllib` reads only; writing needs a third-party package (`inferred` from stdlib docs, not re-fetched) |
| Scalability | Medium |
| Team familiarity | Medium |

**Pros:** comments, human-friendly. **Cons:** write dependency; awkward deep nesting.

### Option C: YAML
**Cons:** third-party parser, implicit typing pitfalls (`inferred`). Rejected.

### Option D: Binary/SQLite or pickle
**Cons:** not diff-able; pickle executes code on load (unsafe for shared files). Rejected.

## Trade-off Analysis

JSON meets every requirement with zero dependencies; readability gaps are mitigated by stable key names, unit suffixes
and the published schema.

## Consequences

- Easier: reproducible designs, review in git, plugin reading without extra packages.
- Harder: schema discipline — every model change needs a schema update, a migration and a test (UT-IO-04).
- Revisit: if users need comments, add an optional `notes` field rather than changing format.

## Action Items

1. [ ] Agent 3: `canonical.py`, `project.py`, `migrations.py`, schema v1, UT-IO-01…06.
2. [ ] Agent 1: list UI state to persist under `ui` (not hashed).
3. [ ] Agent 4: property test PR-08 (hash changes iff design changes).
