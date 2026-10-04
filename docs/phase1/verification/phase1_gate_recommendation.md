Prepared by: Agent 4 — Independent Verificator — model: claude-opus-5-5

# Phase 1 gate recommendation to Fable (2026-10-04)

## Recommendation

**Yes — the Phase 1 draft is fit to present to the user for approval**, on two conditions:

1. The Thai summary states the limitations listed below plainly, including what "verified" means in these documents.
2. The two major defects are recorded as decisions to take at the start of Phase 2, before the affected code is written:
   - **DEF-01** — DRC acceptance rule: embodic must not inherit Xcoil's 0.004 mm slack; "DRC never under-reports" must be
     the single rule for requirements, port tolerances and tests.
   - **DEF-02** — status rule: with the current rule almost every physics result shows `assumption` permanently, and a
     re-typed default can raise a status without new evidence. My proposed fix: badge = method status, plus a separate
     "n assumptions" tag, plus a `measured` input provenance (report §f.3).

Basis: the evidence locations I opened (14 register rows, the O1 table and the KiCad pages) are correct. Every
recomputation I ran reproduces the draft's numbers: star of slots and winding factors, the Xcoil `starOfSlots` defect,
D08 turn limits and loop lengths, the field model's 1-D limit, the resistance cases, and the D10-vs-D15 inductance
decision. Reference material is unchanged and the Xcoil tests pass (131/131). I found no fabricated number and no claim of
balance, torque or efficiency drawn from geometry alone. **No blocker.** There are 15 minor defects (see
`defect_list.md`).

## Limitations that must be stated honestly in the Thai summary

1. **Render topology unresolved.** The Instagram render cannot be decoded: it fits concentrated spiral coils, and it fits a
   wave winding with nested end-turns like the GitHub board. The reference repository board is a wave winding (I confirmed
   this from its Gerbers). The spiral approach is the user's decision. The render is used as a style reference only
   (UD-13).
2. **KiCad not tested.** None of the KiCad behaviour has been run. Still open (T0–T6): whether KiCad 9.x opens the
   `.kicad_pcb` format, KiCad's bundled Python version (this sets the Python floor inside the plugin), the matching
   kicad-python version, what the IPC API can do on the user's 9.0.x, and offline installation of the plugin's
   dependencies. The SWIG route is deprecated (verified), so the plugin depends on the IPC API, which needs the PCB editor
   to be running.
3. **No measured oracle for the target machine.** No published case is a 3-phase, multi-layer (more than 2 layers) spiral
   stator with measured R, L and EMF. The closest cases have gaps:
   - O1 (D08: 2 layers, 12/10, measured Ke) depends on an air-gap reading (1.4 mm vs 2.8 mm) and on a two-magnets-per-pole
     model.
   - O2 (D09: 2 layers, 12/16) has an unknown turn count (my inversion gives 7 or 8 and cannot decide), and its measured
     inductance has no stated method.
   Inductance (EQ-14), the IPC current guideline (EQ-15) and torque–speed (EQ-20) are unvalidated estimates. Per-layer EMF
   and field accuracy against 3-D FEA are not tested.
4. **Patent review needed.** The ECM patents have claims on serpentine/spiral windings and on layers joined in series with
   vias outside the active area. An attorney should review before any release (UD-22). The current default keeps its vias
   inside the coil eyes.
5. **Meaning of the labels.** "verified" in the evidence register means "read in the source". For equations it means
   "derived or reproduced". It never means "confirmed by experiment". All numbers in the documents are computed, from
   formulas or from the unvalidated Xcoil engine; the engine's ranking of candidates is indicative only, not a performance
   claim.
6. **Status badges.** Under the present rule nearly every result of the default design will show `assumption`. A fix is
   proposed (DEF-02); the user should know this when approving the results/traceability concept.
7. **Unsourced inputs that dominate results:**
   - magnet recoil permeability µ_r (no datasheet value found);
   - "PCB copper = IACS copper" and the finished copper thickness;
   - the convection coefficient h (10 vs 30 W/m²K between sources);
   - IPC-2221/2152 (not in the corpus; the paywalled standard is needed).
   The copper constants themselves are sourced; I confirmed NBS Handbook 100, p.2–4.
8. **Mockups are static.** Contrast, language, overflow, keyboard order and the result-card format were checked
   automatically. Responsiveness, screen-reader output, the high-contrast mode and recompute latency can only be checked
   after implementation. Mockup 01 overflows at the 960 px minimum because of an annotation, and some example badges
   contradict the agreed status rule.
9. **Performance not measured.** A literal Python port of the hot loops was measured about 45× slower than the JS engine.
   Vectorised kernels are needed to meet the < 1 s recompute target, which is an assumption until measured on the user's
   laptop.
10. **Licences.** The two reference repositories (GPL-2.0 and GPL-3.0) were used for reference only, and no code exists yet
    to compare against. The embodic licence itself is a user decision (UD-02); it affects whether the plugin can be listed
    in KiCad's add-on manager.

## Items the user should be asked to decide or supply (already in `architecture/user_decisions_needed.md`)

- App type: UD-01.
- Licence: UD-02.
- Phase colours vs pure greyscale: UD-05.
- Rotor (UD-09, UD-10) and operating targets (UD-12).
- Render role: UD-13.
- Smoke tests on the user's PC: UD-21.
- Patent review: UD-22.
- Reference board measurement: UD-24.
- Contacting the D09 authors: UD-25.

I additionally recommend asking for FEMM (free, Windows) on the user's machine, or accepting that field validation (IT-27)
waits until Phase 3.
