Prepared by: Agent 5 (Research & Evidence Specialist), model: claude-opus-5-5. Created in U-S8 (2026-10-16).

# Source gaps: Phase 3 updates

This file records Phase 3 changes to the gaps in `docs/phase1/evidence/evidence_gaps.md`. It keeps the Phase 1 gap
ids. Status labels follow the standing orders.

## G2: D09 coil turn count and geometry, narrowed

**Verdict: narrowed, not closed.** Read the detail in `d09_coil_geometry.md` and rows EV-127 to EV-133 in
`evidence_register_phase3.md`.

What is now known (`inferred`, figure readings):

- D09 Fig. 1a p.2 shows 7 turns per coil on the top layer. All 36 readable sides of the 12 coils give 7 (EV-128).
- The drawing's scale is 5.200 px/mm, from the printed 1.0 mm pitch. The drawn inner circle is then 49.36 mm, 1.3 %
  under the printed 50 mm (EV-129).
- The lateral sides are parallel offsets of the sector edges (EV-130).
- The outermost turn's centre lines are at r 24.9 to 25.3 mm and 44.9 to 45.5 mm (EV-131).
- The Fig. 11a photo shows 6 or 7 traces on the inner side of coil C2 at the same 1.0 mm pitch (EV-133).

Why G2 stays open:

- Figure readings cannot be `verified`. D09 prints no turn count, no turn radii and no coil drawing with dimensions.
- The bottom layer is hidden in Fig. 1a. That it also has 7 turns is an `assumption`.
- 7 measured turns × 8 coil-layers give 2804 to 2848 mm, 12 % to 14 % under D09's 3244 mm (EV-132). The remainder is
  not measured.
- The photo puts the inner turns about 1.4 to 1.5 mm further from the hole than the drawing (EV-133). So the as-built
  radii are `unresolved`.

What would close it:

1. Measure the photo's outer side and lateral sides of all 12 coils with the same profile method. This would show
   whether the built coil is the drawing shifted outward or a different coil.
2. Measure the rim connection traces and the via leads in Fig. 1a to test whether they make up the 396 to 440 mm.
3. Ask the authors for the layout (METU, `keysan@metu.edu.tr` is printed on D09 p.1). This is the only route to a
   `verified` value.
