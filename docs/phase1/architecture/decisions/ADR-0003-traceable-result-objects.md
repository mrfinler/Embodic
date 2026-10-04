Prepared by: Agent 6 — Software Architecture Specialist — model: claude-opus-5-5

# ADR-0003: Traceable result objects — calculation-trust badge plus separate assumed-input tag

**Status:** Accepted — status rule decided by Fable as decision_log **D-007** (2026-10-04); this version supersedes the
earlier "weakest of equations, inputs and assumptions" rule and its Amendment 1 (Agent 4 DEF-02).
**Date:** 2026-10-04
**Deciders:** Fable 5.1 (D-007) — consulted: Agent 2 (EQ statuses, dominant assumptions), Agent 4 (DEF-02), Agent 1 (badge
design), Agent 5 (EV registry)

## Context

- Coordinator constraint: every computed result carries value, unit, EQ-ID(s), evidence IDs, assumptions used and a status
  label (`verified / inferred / assumption / unresolved / not tested`).
- BRIEF §3: every claim carries a reference (rule 2) and one status label (rule 3); computed results are never "measured"
  (rule 5); no balance/torque/efficiency claims from geometry alone (rule 6).
- Agent 2's equation registry (`docs/phase1/engineering/equation_registry_draft.json`) gives each EQ a gate verdict and a
  Phase 1 evidence `status`, read 2026-10-04: EQ-01, 04, 06, 09, 10, 13, 21, 22 `verified`; EQ-02, 03, 05, 07, 08, 11, 12,
  18, 19 `inferred`; EQ-16, 17 `assumption`; EQ-14, 15, 20 `unresolved` (`cannot verify yet`). Constants ρ₂₀ = 1.7241e-8
  Ω·m, α = 0.00393 /K and copper density 8.89 g/cm³ are sourced to EV-53 (IACS, NBS Handbook 100; Agent 4 confirmed the
  pages, DEF-05); "PCB copper = IACS copper" remains an equation-level assumption (G6).
- Agent 4 (DEF-02, `verification/phase1_verification_report.md` §f.3) showed that the previous rule (input statuses feed
  the result status) made every R/Ke/torque/loss result `assumption` permanently, let re-typing a default raise a status,
  confused "read in the source" with "applies", and contradicted the default-marker requirements.
- Fable decided D-007: the badge expresses the **calculation's** trust (gate × evidence × test state); assumptions are a
  separate "n assumptions" tag with an expandable list; `measured` provenance only when the user marks an input as measured
  and names the source; re-typing a default changes nothing; `assumption` remains the label for individual inputs and for
  results whose equation itself is an engineering assumption.

## Decision

1. **Traceable results.** Every computed quantity is a `Traceable[T]` (architecture_draft.md §7.7) with `quantity`,
   `value`, `unit`, `eq_ids` (or kind tag `input` / `derived` / `count`), `evidence_ids`, `status` (badge),
   `status_reasons`, `assumed_inputs` (tag list), `validity` flags, `tolerance`, `inputs`. Kernels return plain numbers;
   `traced(...)` builds the record from the registry (code declares EQ-IDs, never copies EV-IDs).
2. **Badge = calculation trust** = weakest of
   - the evidence `status` of every EQ in the chain (registry; gate `cannot verify yet` ⇒ `unresolved`; an equation whose
     status is `assumption`, e.g. EQ-16 mass, EQ-17 thermal, makes the badge `assumption`);
   - the implementation **test state**: `not tested` until all tests linked to those EQs pass in the current build (an
     oracle that has not been run does not produce `not tested`; it only prevents raising the EQ's evidence status);
   - the **validity cap**: any violated validity limit of an EQ in the chain ⇒ `unresolved`.
   Order: `unresolved` < `not tested` < `assumption` < `inferred` < `verified`. **Inputs never enter the badge.**
3. **Assumed-input tag** ("n assumed inputs", expandable, dominant ones first using the registry's
   `dominant_assumptions`): for the inputs the kernel actually uses, list
   - every input whose **value equals its default** (provenance "default"; design and property inputs alike);
   - every **physical-property input not marked `measured`** (B_r, µ_r, finished copper thickness, plating, h, densities …)
     with its label: `assumption`, or for a sourced constant min(EV read status, applicability) — typically `inferred`;
   - every **equation-level assumption** of the chain (e.g. "PCB copper = IACS copper" for EQ-10, unsaturated back iron for
     EQ-05) unless a `measured` input replaces it.
   Design inputs (geometry, layer configuration, operating point) whose value differs from the default are the user's design
   and are not listed.
4. **Provenance** per input: `default`, `user`, `imported_kicad`, `measured` (+ `source_ref`, mandatory), `migrated`.
   Membership in the tag depends on **values and the `measured` mark only**, never on keystrokes: re-typing a default or the
   current value changes neither the badge nor the tag (PR-12).
5. **Gate enforcement**: an EQ may carry evidence status `verified` only if the registry links ≥ 1 validation test that
   passed in the current CI run (TR-03); `cannot verify yet` outputs carry the label "estimate" / "guideline (unverified)".
6. **Display**: badge (shape-coded, Agent 1) + EQ link + "n assumed inputs" tag on every number; the disclosure lists
   `status_reasons` (e.g. "EQ-07 inferred; tests passed; no validity limit exceeded") and the assumed inputs with value,
   unit, provenance and label (REQ-T-01, T-03, T-13). Exports and reports carry both the badge and the list.

### Worked example — default design (Agent 2 §5.2), assuming the linked unit/regression tests pass

Registry statuses as read 2026-10-04; geometry 12/16, 3 pairs in series, w/s 0.5/0.2 mm, 1 oz, r 18–38 mm, double rotor,
blocks 20 × 6 × 2 mm centred at r = 28 mm, gap 1.0 mm, operating point 1000 rpm (example values, `assumption`).

| Result | EQ chain (evidence status) | Validity check | Badge | Assumed-input tag (dominant first) |
|---|---|---|---|---|
| Phase resistance at operating temperature | EQ-10 (`verified`), EQ-11 (`inferred`), EQ-07 (`inferred`); track length = exact sum of generated primitives | EQ-13: δ ≈ 5.72 mm at 133.3 Hz (A2 C9) ≫ w = 0.5 mm, t = 0.035 mm → no cap | **`inferred`** (`not tested` before the tests pass) | finished copper thickness (default), winding temperature (default), PCB copper = IACS (equation-level), ρ₂₀ and α (sourced EV-53 → `inferred`), via plating (default), trace width, annulus, clearance, coil gap (defaults) |
| Phase Ke, line Ke, torque at the operating point | EQ-04 (`verified`), EQ-05 (`inferred`), EQ-06 (`verified`), EQ-07 (`inferred`), EQ-09 (`verified`) | EQ-05 is not valid within about one magnetic gap of the magnet's radial ends (A2-EQ EQ-05; here G = (0.62 + 2·1.0)/2 = 1.31 mm). The default coil annulus 18–38 mm coincides with the block span 18–38 mm → conductors lie in the edge zone → cap | **`unresolved`** on the default design; **`inferred`** for a design whose EMF-producing conductors stay ≥ G inside the magnet span, or once Agent 2's radial edge correction (EQ-05 change) is implemented and validated | B_r, µ_r (defaults; µ_r unsourced, G23), magnet thickness, air gap, magnet shape (defaults), unsaturated back iron and linear magnets (equation-level); torque adds the line current (default) |
| Copper mass | EQ-16 (`assumption`) | — | **`assumption`** (equation itself an assumption) | laminate density, copper density (sourced → `inferred`) |
| Inductance estimate | EQ-14 (`unresolved`, cannot verify yet) | — | **`unresolved`**, label "estimate" | δ′, k_w1, missing end-turn terms (equation-level) |

Reaching `verified`: R needs EQ-07 and EQ-11 raised to `verified` by validation (e.g. OR-02/OR-03 or a via-chain coupon);
Ke/torque need EQ-05 and EQ-07 validated (OR-01, OR-11) and, on this geometry, the edge correction. The badge then rises
without any change to the inputs, and the tag still shows every default and assumed property — which is the intended
separation. Marking the copper thickness as `measured` (with a coupon record) removes it from R's tag but does not change
R's badge.

Observation for Agent 2 (not a defect of the rule): with a strict validity cap, every design whose coil annulus equals the
magnet span shows `unresolved` for Ke and torque. Agent 2 should define the EQ-05 `validity_checks` entry precisely (e.g.
cap only if the share of EMF-producing radial length inside the edge zone exceeds a stated fraction, otherwise a listed
limitation) — `assumption` until specified.

## Options Considered

### Option A: Calculation-trust badge + separate assumed-input tag (chosen, D-007)
| Dimension | Assessment |
|---|---|
| Complexity | Medium — two outputs per result, provenance model with `measured` |
| Cost | Small runtime overhead (metadata per result, not per segment) (`inferred`) |
| Scalability | High — new equations add registry entries; validation raises badges centrally |
| Team familiarity | Medium |

**Pros:** badge discriminates (can reach `inferred`/`verified`); no keystroke dependence; assumptions always visible;
measured data can retire assumptions. **Cons:** two indicators to read; the tag can be long for default designs (mitigated
by dominant-first ordering and the count).

### Option B: One weakest-link status over equations, inputs and assumptions (previous proposal)
**Pros:** single label. **Cons:** collapses to `assumption` for every physics result, depends on who typed a value,
mixes evidence, provenance and implementation state (Agent 4 DEF-02). Rejected (D-007).

### Option C: Plain floats + a separate metadata table keyed by result name
**Pros:** simple. **Cons:** metadata drifts from values; per-design assumptions and validity flags cannot be expressed.
Rejected.

### Option D: Units-library quantities (e.g. Pint) without trace metadata
**Pros:** dimensional safety. **Cons:** solves units, not traceability; Pint 0.26 requires Python ≥ 3.12 (PyPI metadata,
`verified`). Rejected for runtime (ADR-0009).

## Trade-off Analysis

The decisive requirement is honest, discriminating traceability. Separating "how trustworthy is the method as implemented"
from "what does this number rest on" keeps both visible without letting one mask the other.

## Consequences

- Easier: honest badges that improve as validation progresses; reports that list every assumption; no status gaming by
  re-typing values.
- Harder: provenance with `measured` + `source_ref` in the model and project file; registry must list equation-level
  assumptions; Agent 2 must specify `validity_checks` precisely.
- Revisit: whether reports also need one combined "overall" label (Agent 4 fix (c)); not part of D-007, so not adopted.

## Action Items

1. [ ] Agent 2: per-EQ `dominant_assumptions` and equation-level assumption list; precise `validity_checks` (EQ-05 edge
       zone).
2. [ ] Agent 5: `evidence.v1.json` with `applies` judgement so sourced constants can carry min(EV, applicability).
3. [ ] Agent 3: `results/` (badge, tag, provenance incl. `measured`) with UT-RES-01…06 before physics.
4. [ ] Agent 1: badge + tag + disclosure in mockup 04 per this rule (Agent 4 DEF-06).
5. [ ] Agent 4: re-check the worked example against the implementation in Phase 2.

## Revision 2026-10-04 (defect fixes)

Rewritten per decision_log D-007 — addresses DEF-02 (and the ADR-0003 part of DEF-05: constants now cited to EV-53).
