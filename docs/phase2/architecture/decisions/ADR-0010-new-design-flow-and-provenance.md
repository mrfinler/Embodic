Prepared by: Agent 6 - Software Architecture Specialist - model: claude-opus-5-5

# ADR-0010: New-design flow and per-field provenance

**Status:** Proposed (implements D-014 and D-007)
**Date:** 2026-10-04
**Deciders:** Fable 5.1; consulted: Agent 1 (form and chip design), Agent 2 (which fields are property inputs), Agent 4

## Context

D-014: the application opens on a blank "New design"; the user enters every parameter; nothing is computed until the
required fields are filled; the team's parameter sets ship only as labelled examples with `example` provenance, user
values carry `user`. D-007: the badge expresses calculation trust only; assumed inputs form a separate tag; `measured`
requires a named source; typing a value equal to a default does not change status. Phase 1 opened on a default design
and stored a per-field `default / user / imported_kicad / migrated / measured` source (Phase 1 architecture §7.1).

Three questions follow. How is "required field not filled yet" represented? Where does provenance come from? What do
optional settings start with?

## Decision

1. **Two types.** `DesignDraft` (topology plus a pointer-to-value mapping, values may be missing) is what the form edits.
   `DesignParameters` is always complete. `parse_draft()` is the only conversion and returns `DesignParameters` or
   `DraftIncomplete(missing, issues)`. Engine code never sees a partial design, so no engine function checks for missing
   values.
2. **Field table.** `field_specs(topology)` lists every field once with pointer, kind (`design` or `property`), unit,
   `required` and applicable topologies. It drives required-field checks, form generation, unit display, applicability
   (REQ-F-32) and the measured rule. Optional fields carry a neutral value written into a blank draft (for example
   `turns: null` = maximum feasible, `corner_radius_mm: 0`, side style `parallel`); these are geometric choices with an
   exact meaning, not physical assumptions. Property fields are always required: B_r, mu_r, finished copper thickness,
   plating, convection coefficient. Material constants (resistivity, temperature coefficient, densities) come from the
   registry with their EV status; a user override is a `PropertyValue`.
3. **Derived provenance.** Provenance is a function of state, not a stored flag that edits mutate:
   `derive_provenance(design, origin, measurements)` returns `measured` for a property field with a recorded measurement
   and source, `example` while the field equals its value in the origin example, `user` otherwise. Re-entering the
   current value changes nothing; setting a changed field back to the example value gives `example` again; a value change
   drops that field's measurement. The type is a tagged union (`UserValue | ExampleValue | MeasuredValue`), so a
   measured value without a source cannot be built.
4. **Persistence.** The project file stores `origin_example` (ID and SHA-256 of the example's canonical design), the
   derived per-field provenance map (readable, required by REQ-T-06) and the measurement sources. On load the map is
   checked against the derivation when the same example version is packaged. Drafts save and load too
   (`LoadedDraft`), so a half-entered design survives a restart.
5. **Examples.** Examples are ordinary project files in `resources/examples/`, one file each, titled with the word
   "Example". Loading one starts an unsaved design whose origin is that example; the first Save opens Save As.
6. **Assumed-inputs tag.** The tag lists inputs with `example` provenance, property inputs not marked measured, registry
   constants used, and equation-level assumptions (D-007 unchanged; the Phase 1 reason `default` becomes `example`).

   Revision 2026-10-05 (U-D3, D-023 b). The tag lists four kinds of entry and no other:
   - inputs whose value has `example` provenance;
   - property inputs (`FieldKind.PROPERTY`) not marked measured, whatever value they hold;
   - registry constants the chain uses;
   - the equation-level assumptions of the chain.

   A design or geometry input (`FieldKind.DESIGN`) that holds its documented default is not listed. The result is exact
   for that geometry, and the form already shows the `default` chip (D-019). D-007's word "defaults" therefore means
   property defaults. `src/embodic/results/traceable.py` `assumed_inputs_tag` implements this list (`verified` by
   reading its docstring and body, 2026-10-05).

   Pointer for ADR-0003. `docs/phase1/architecture/decisions/ADR-0003-traceable-result-objects.md` decision 3 is a
   read-only Phase 1 file. Where it says "defaults", read "property defaults" as defined here (D-023).

   Packaged evidence (D-023 a). The evidence copy that ships, `resources/evidence/evidence.v1.json`, is the
   `phase2_scope` filter of `docs/phase2/evidence/evidence_register.json`, not a byte copy: it keeps the entries Agent 5
   marks `phase2_scope` and the documents they cite (`tools/sync_registry.py` `phase2_scope`, l.30-42).

## Options considered

### Option A: nullable fields inside DesignParameters

| Dimension | Assessment |
|---|---|
| Complexity | Low to write, high to use: every engine function must handle `None` |
| Cost | Missing-value checks spread over winding, geometry, physics |
| Scalability | Each new field adds checks in several modules |
| Team familiarity | High |

**Pros:** one type. **Cons:** illegal states representable; the engine would need a "not ready" path everywhere.

### Option B: draft and complete design as separate types (chosen)

**Pros:** one parse step; the engine keeps its Phase 1 shape; the missing list comes from the field table.
**Cons:** a pointer-keyed draft is less typed than a dataclass; the field table must stay complete (UT-MOD-03 enumerates
every leaf).

### Option C (provenance): stored per-field flag updated by each edit

**Pros:** simple to explain. **Cons:** keystroke-dependent (re-typing changes provenance), conflicts with D-007 and
Phase 1 PR-12; the stored flag and the value can disagree.

### Option D (provenance): derived from origin example, value and measurement list (chosen)

**Pros:** provenance cannot disagree with values; re-entry invariance holds by construction; one pure function to test.
**Cons:** needs the origin example's values at hand; handled by packaging examples with a SHA-256 and checking on load.

## Trade-off analysis

B plus D move all "is this design ready, and where did each value come from" logic into two pure functions over one
table. The cost is a pointer-based draft, which the form needs anyway because it edits one field at a time. Rejected
option A would have pushed a "maybe missing" state into every calculation module.

## Consequences

- Easier: the engine contract from Phase 1 stays valid; required-field validation, applicability and units have one
  source; provenance tests are a truth table.
- Harder: the field table is a second description of DesignParameters and must be kept complete (UT-MOD-03 fails on a
  missing or extra leaf).
- Revisit: neutral values for optional fields are an `assumption` of this ADR; if Agent 1's design spec v1 wants
  optional fields blank too, `blank_draft` changes and nothing else does.

## Action items

1. [ ] U-M2a: `fields.py`, `draft.py`, `provenance.py` with UT-MOD-01 to UT-MOD-05.
2. [ ] U-M2f: project file v1 with `origin_example`, provenance map, drafts; spiral examples.
3. [ ] U-M4c: session state machine and New design dialog.
4. [ ] Agent 2: confirm the property-field list in decision 2.
