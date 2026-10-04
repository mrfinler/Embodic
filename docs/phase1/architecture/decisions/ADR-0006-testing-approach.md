Prepared by: Agent 6 — Software Architecture Specialist — model: claude-opus-5-5

# ADR-0006: Testing approach — unit + function-level golden regression vs the JS engine + oracle cases + property/fuzz tests, linked to requirements

**Status:** Proposed — amended 2026-10-04 (Agent 2/3 refinements)
**Date:** 2026-10-04
**Deciders:** Fable 5.1 — consulted: Agent 4 (independent verification), Agent 2 (tolerances), Agent 3

## Context

- Coordinator constraint: golden regression against the JS engine (JSON dumps compared in Python) for every equation
  marked `reuse`.
- Agent 2: "the Python port must re-run C1–C9 as regression tests with the same tolerances (EQ tables) before Phase 2
  sign-off" (A2-REV §4); gate verdicts: `reuse` EQ-01, 06, 09, 10, 12, 13, 18, 22; `reuse with change` EQ-05, 07, 11, 16,
  17, 19; `replace` EQ-02, 08; `cannot verify yet` EQ-14, 15, 20 (A2-EQ gate summary).
- Xcoil v3 has 131 engine tests, a v1 golden check of 1 417 numbers at rel. 1e-9 with one documented deviation (eddy loss
  within 3 %), export validation with ezdxf/kiutils/pypdf and seeded fuzzers (`TEST_PLAN.md` header; `golden-check.js`
  l.23–25; `verified` reading).
- The Python spiral generator intentionally differs from Xcoil's sector generator (EQ-02 `replace`; triangular turns,
  series pairs, rotation — A2-TOP K7). Whole-design golden comparisons would therefore fail by design (`inferred`).
- Candidate oracles O1–O9 with published numbers (A5-REG §C); tolerances partly set by Agent 2 (EQ-06 ±8 % vs O1, EQ-10
  ±8 %), others pending (EQ-14 none).

## Decision

A layered strategy (details and IDs in `test_plan_draft.md`):
1. **Unit tests** per module, written first for geometry invariants, winding rules (incl. the 12/14 star-of-slots
   regression) and physics kernels vs closed forms.
2. **Function-level golden regression**: a Node script reads `/home/claude/serpentine/src/engine.js` read-only, evaluates
   the `reuse` (and the unchanged parts of `reuse with change`) functions on a fixed input set — including fixed primitive
   lists exported from Xcoil's own builders — and writes JSON with the engine file's SHA-256. Python tests feed identical
   inputs to the embodic functions and compare at rel. 1e-9 (Xcoil's own golden tolerance), with every deviation
   documented in the test (e.g. Xcoil v1→v2 eddy edge case).
3. **Oracle tests** against published cases (O1 D08 K_e, O2 D09 R, O3 D10 R; closed-form references from A2-EQ) with
   tolerances owned by Agent 2/4; failures block the `verified` status of the EQ (ADR-0003).
4. **Property/fuzz tests** (Hypothesis, test-only, MPL-2.0 per PyPI, `verified`): DRC never under-reports; continuity,
   mirror and rotation invariants; balanced winding → equal phase Ke; scaling laws; no exception/NaN on random input;
   project round trip; nm rounding keeps connectivity.
5. **Boundary/invalid-input tests**, **headless UI tests**, **export validation with independent parsers**, **language and
   accessibility checks**, **performance baseline**, **packaging tests**, and **manual KiCad smoke tests** on the user's
   machine.
6. **Traceability**: every test carries `@pytest.mark.req(...)` (and `eq(...)` where relevant); CI generates the
   requirements-to-tests matrix and fails on untested must-requirements.
7. **Independence**: Agent 4 writes an independent second implementation for selected checks (brute-force DRC, star of
   slots, field at a point) and black-box tests from the requirements without reading embodic code.

## Options Considered

### Option A: Translate the Xcoil test suite 1:1
| Dimension | Assessment |
|---|---|
| Complexity | Low |
| Cost | Low |
| Scalability | Low — tests encode Xcoil's sector behaviour, including the defects to be replaced |
| Team familiarity | High |

**Pros:** fast coverage. **Cons:** would preserve `starOfSlots` bug and 0-turn limit (A2-REV C5, C6).

### Option B: Layered strategy with function-level golden + oracles + properties (chosen)
| Dimension | Assessment |
|---|---|
| Complexity | Medium/high |
| Cost | Medium — harness and fixtures |
| Scalability | High |
| Team familiarity | Medium |

**Pros:** proves reuse where intended, frees replaced parts from false baselines, adds physical evidence, catches
geometry/DRC defects generically. **Cons:** golden harness maintenance; oracle tolerances depend on unresolved gaps
(G1, G2, G10).

### Option C: Validation-only (oracles + manual review)
**Pros:** physically meaningful. **Cons:** too few oracles (G2), no regression safety for refactoring. Rejected.

## Trade-off Analysis

B costs more upfront but is the only option that matches the equation gate: `reuse` → golden, `replace` → specification
tests + oracles, `cannot verify yet` → labelled estimate tests only. Function-level golden avoids comparing intentionally
different geometry.

## Consequences

- Easier: refactoring with confidence; honest status labels backed by passing tests.
- Harder: Node.js is needed to regenerate golden files (not to run the Python tests; JSON is committed).
- Revisit: when an in-house measured reference board exists (A5-GAP G2 proposal 3), add it as oracle O-EMB-1.

## Action Items

1. [ ] Agent 3: golden harness (`tools/golden_js/dump_reference.mjs`) + JSON fixtures, P2 week 1.
2. [ ] Agent 2/4: tolerance table for OR-01…OR-06; decide G10 handling for O1.
3. [ ] Agent 4: independent checkers (DRC, star of slots, field point values).
4. [ ] Fable: CI gate = unit + golden + oracle + property (fast profile) + MT + TR checks on every commit.

## Amendment 1 — reconciliation round 1 (2026-10-04)

- Golden comparisons inject Xcoil-compatible constants (ρ₂₀ 1.724e-8 Ω·m, copper density 8.96 g/cm³) or compare at
  function level, because embodic adopts ρ₂₀ = 1.7241e-8 (EV-53) and 8.89 g/cm³ (Agent 2 `answers_to_agents.md` §2.1);
  known Xcoil defects are not ported bug-for-bug and appear in the expected-differences list.
- Two gates per function where both apply (Agent 2/3): port equivalence (golden) and engineering validity (EQ gate +
  oracles); `replace` and new items (spiral generator, EQ-04, EQ-21) have engineering tests only, using Agent 2's
  closed-form cases G1–G3 (`checks/eq02_eq03_reference.py`).
- Agent 1's UX-AC-01…22 become UI/AX test cases (requirements_draft.md §9).
