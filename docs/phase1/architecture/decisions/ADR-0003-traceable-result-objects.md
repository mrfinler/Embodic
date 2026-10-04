Prepared by: Agent 6 — Software Architecture Specialist — model: claude-opus-5-5

# ADR-0003: Traceable result objects, equation/evidence registries and status combination

**Status:** Proposed — amended 2026-10-04 (status order confirmed by Agent 2; rule amended; Agent 4 review pending)
**Date:** 2026-10-04
**Deciders:** Fable 5.1 — consulted: Agent 2 (EQ statuses), Agent 4 (verification), Agent 5 (EV registry)

## Context

- Coordinator constraint: every computed result carries value, unit, EQ-ID(s), evidence IDs, assumptions used and a status
  label (`verified / inferred / assumption / unresolved / not tested`).
- BRIEF §3: every claim carries a reference (rule 2) and one status label (rule 3); computed results are never "measured"
  (rule 5); no balance/torque/efficiency claims from geometry alone (rule 6).
- Agent 2's gate verdicts (`reuse`, `reuse with change`, `cannot verify yet`, `replace`) apply per equation
  (A2-EQ gate summary); several constants are `assumption: standard value, source needed` (EQ-10, EQ-15, EQ-16; gaps G5, G6).
- Agent 5 maintains EV-IDs with document/page locations (A5-REG §B).

## Decision

1. Every engine output that is a computed quantity is a `Traceable[T]` (architecture_draft.md §7.7) with: `quantity`,
   `value`, `unit` (closed vocabulary), `eq_ids`, `evidence_ids`, `assumptions`, `inputs` (JSON pointers + provenance),
   `validity` flags, `tolerance`, `status`, `status_reasons`.
2. Physics kernels return plain numbers; only `physics.analyse()` (and `winding`/`geometry` for k_w and turn counts) wrap
   them through `traced(...)`, which pulls evidence IDs, base status and tolerance from the **equation registry** — code
   declares EQ-IDs, never copies EV-IDs.
3. Registries are packaged JSON files (`equations.v1.json`, `evidence.v1.json`), versioned with the app; their content is
   owned by Agents 2/4 (EQ) and 5 (EV); CI checks integrity (TR-03, TR-04).
4. **Status combination (proposal):** result status = weakest of {equation status(es), input statuses, assumption statuses,
   validity cap}, with the order `unresolved` < `not tested` < `assumption` < `inferred` < `verified`. Inputs entered by the
   user or imported from KiCad are neutral; defaults count as `assumption`; any violated validity limit caps the result
   at `unresolved`; an equation with gate `cannot verify yet` has status `unresolved` and its outputs are labelled
   "estimate". Rationale for placing `not tested` below `assumption`: an untested computation can be arbitrarily wrong,
   while an assumption is explicit and reviewable (`assumption` — this ordering needs Fable/Agent 4 agreement).
5. An equation may have status `verified` only if the registry links ≥ 1 test ID that passed in the current CI run.
6. The UI and reports show value, unit and status on every result and the full record in ≤ 1 interaction (REQ-T-01).

## Options Considered

### Option A: Traceable wrapper on every result, filled from registries (chosen)
| Dimension | Assessment |
|---|---|
| Complexity | Medium — wrapper type, registry loader, status rule |
| Cost | Small runtime overhead (metadata per result, not per segment) (`inferred`) |
| Scalability | High — new equations add registry entries |
| Team familiarity | Medium |

**Pros:** impossible to display a bare number; single source of EV references; testable status logic.
**Cons:** more verbose result types; registry content must be curated.

### Option B: Plain floats + a separate metadata table keyed by result name
| Dimension | Assessment |
|---|---|
| Complexity | Low |
| Cost | Low |
| Scalability | Medium |
| Team familiarity | High |

**Pros:** simple kernels and results. **Cons:** metadata drifts from values (e.g. a status not updated when inputs come from
defaults); per-design assumptions and validity flags cannot be expressed.

### Option C: Units-library quantities (e.g. Pint) without trace metadata
**Pros:** dimensional safety. **Cons:** solves units, not traceability; Pint 0.26 requires Python ≥ 3.12 (PyPI metadata,
`verified`) while the user's minimum is 3.11. Rejected for runtime (see ADR-0009).

## Trade-off Analysis

The constraint is first-class traceability; only A attaches design-specific facts (which inputs were defaults, which
validity limits were exceeded) to each value. Keeping kernels plain avoids paying the cost inside numerical loops.

## Consequences

- Easier: honest status display; reports that cite EQ/EV automatically; CI gate on over-claimed statuses.
- Harder: every new output needs a registry entry and a unit; Agents 2/4/5 must keep registries current.
- Revisit: the status order (item 4) after the first review; whether tolerances should be shown as intervals in the UI.

## Action Items

1. [ ] Agent 2: provide the per-EQ status and tolerance values for `equations.v1.json` (from A2-EQ).
2. [ ] Agent 5: export the EV register to `evidence.v1.json` (ID, claim, document, location, status).
3. [ ] Fable/Agent 4: confirm or amend the status order.
4. [ ] Agent 3: implement `results/` with UT-RES-01…04 before physics.

## Amendment 1 — reconciliation round 1 (2026-10-04)

- **Order confirmed** by Agent 2 (`docs/phase1/engineering/answers_to_agents.md` §1.1): `unresolved` < `not tested` <
  `assumption` < `inferred` < `verified`; also encoded in `equation_registry_draft.json` → `status_order_weakest_first`.
- **Rule amended** (replaces item 4 where different): result status = weakest of (a) the evidence status of every EQ in
  the chain, (b) the implementation status (`not tested` until the EQ's linked tests pass — an oracle that has not been run
  does **not** produce `not tested`), (c) the status of every input the kernel **actually uses** (user/KiCad-imported
  neutral; default or unsourced `assumption`; sourced constant = its EV status, e.g. ρ₂₀ from EV-53; the equation's own
  stated assumptions = `assumption` unless replaced by measured data), (d) validity cap → `unresolved`.
- `dominant_assumptions` (registry) only orders and explains the "n assumptions" tag; no run-time judgement of dominance
  (Agent 2), which resolves Agent 1's §10.4 item 3.
- Registry source format: Agent 2's `equation_registry_draft.json`, plus Phase 2 fields `tests`, `validity_checks`,
  `implementation`, `constants`, `label`, `registry_version` (architecture_draft.md §13). Evidence-register JSON export
  format defined in the same section (Agent 5, Phase 2).
- UI: every number shows a shape-coded badge and an EQ link or an `input`/`derived`/`count` tag (Agent 1 UX-AC-01/02;
  REQ-T-01, T-13).
