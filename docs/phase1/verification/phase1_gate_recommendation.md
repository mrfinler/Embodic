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

## Re-verification 2026-10-04 (after the defect-fix round, commit 63716fc; decisions D-006 and D-007)

**The recommendation stands: the Phase 1 draft is fit to present to the user for approval.** Both conditions of the first
round are met:

- **DEF-01** is closed by D-006. The DRC rule is now one rule across REQ-F-10, the port tolerances and PR-01/UT-DRC-03:
  violation if the measured clearance is below rule − ε, with ε ≤ 1e-6 mm, and no slack.
- **DEF-02** is closed by D-007. The badge now shows calculation trust; assumptions appear in a separate tag;
  provenance is `measured` only when a source is named; re-typing a value changes nothing.

Of the 17 first-round defects, 15 are verified as closed. Two minor ones are reopened:

- **DEF-05**: one stale "source needed" remains, in `migration_mapping.md` F-29.
- **DEF-09**: REQ-F-06(b) and UT-GEO-07 still use the old −6 … 0 % band. With the now-verified true-spiral reference,
  that band would reject a correct generator for 18/16, N = 4 (−6.4 %).

The fixes exposed five new defects:

- **DEF-18 (major):** the EQ-05 edge-validity cap is binary.
  - Effect: Ke and torque are `unresolved` on the default design. The two oracle designs (D08, D09) are capped too,
    because their coils also span the magnet edges, so validation could never raise Ke.
  - My estimate: the edge-zone error is about 1–3 % of Ke, small next to the ±8 % oracle tolerance.
  - Verdict: the behaviour is correct under the rule as written. It is a defect neither of D-007 nor of the default
    design; it is an under-specified validity check.
  - Required before the results display and validity code are built: Agent 2 defines a quantified check (or an
    edge-corrected field with the residual listed as a limitation), and the mockups are aligned to it.
- **Minor:** DEF-19 (the O2 pre-registered geometry contradicts D09's published length; my true-spiral inversion favours
  N = 8), DEF-20 (an example count in mockup 03), DEF-21 (PR-12 wording), DEF-22 (tag-membership wording differs
  between the equation spec and ADR-0003).

Blockers: **none**. Open: 7 (1 major, 6 minor) — all are document corrections or Phase-2-start specifications.

### Residual limitations to state to the user (updates the list above)

1. Limitations 1–4, 5 (meaning of "verified"), 7, 9 and 10 above are unchanged.
2. **Status badges (replaces limitation 6).**
   - The badge rule is decided (D-007): the badge shows how trustworthy the calculation is, and an "n assumptions"
     list shows what the number rests on.
   - Today most physics results would still show `inferred` at best (no validation has been run).
   - Until DEF-18 is specified, Ke and torque of the default design show `unresolved`, because the coils reach the
     magnet edges, where the 2-D field model is not valid.
3. **DRC (D-006).** Embodic's check will be strict, with no 4 µm slack. Xcoil's own default design would fail it
   (0.19901 mm against a 0.20 mm rule). The new generator must therefore place copper with a margin.
4. **Oracle O2 turn count.** With the true-spiral length, the published D09 numbers favour 8 turns per coil per layer.
   7 turns remain possible if the published length includes about 330 mm of inter-coil links per phase. This is still
   `unresolved` until the D09 authors are contacted (UD-25).
5. **D08 phase resistance.** A true spiral of D08's geometry is about 19 % shorter than the concentric-loop model D08
   used (I confirmed this with my own construction). D08's 0.39 Ω is therefore a model value, not a target.
6. **Mockups.** They now pass my overflow, language, contrast and result-format checks at all stated widths, including
   the 880 × 600 KiCad window. They remain static, so behaviour (latency, screen reader, high contrast) can only be
   checked after implementation.

## Final re-verification 2026-10-04 (commit 1425e23)

**Final recommendation: present the Phase 1 draft to the user for approval.** All 22 defects from the earlier rounds are
closed (verified). They include the reopened DEF-05 and DEF-09 and the former major DEF-18. DEF-18 is now the graded
edge check EC-05. I reproduced it independently: my own digitisation of D09 Fig. 7 gives e_edge of 5.33 % (default
design), 4.21 % (D08) and 5.79 % (D09), the same as Agent 2's values.

One new minor defect is open:

- **DEF-23 — EC-05 labelling and basis.**
  - The calibration uses the magnitude of B from one FEA figure. That probably under-states the B_z edge deficit.
  - Transferring the fit to other rotors is an assumption.
  - The 10 % cap is defensible only as a labelled `assumption`; its stated reason is internally inconsistent.
  - D09 is both the calibration source and an oracle, so only D08 can test the edge rule independently.

**Open defects: 1 (minor), major 0, blockers 0.**

### Residual limitations to state to the user (final list)

1. **Topology of the render unresolved.** It is used as a style reference only (UD-13).
2. **KiCad not tested.** None of T0–T6 has been run: file format, bundled Python, kicad-python version, IPC
   capabilities, offline installation.
3. **No measured oracle for the target machine.** No case has a 3-phase stator with more than 2 layers. For the cases
   used:
   - O1 depends on D08's air-gap reading.
   - O2 assumes 8 turns per coil per layer, inferred from D09's published length; 7 turns is kept as variant B.
   - Inductance, the IPC guideline and torque–speed are unvalidated estimates.
4. **Radial edge leakage.**
   - The 2-D field model over-estimates EMF near the magnet ends. EC-05 estimates the over-estimate at about 5 % for the
     default design, from one FEA case.
   - Ke and torque therefore carry a one-sided "model may be high by up to e_edge" tolerance, and the calibration
     transfer is an assumption.
   - Designs with short magnets (under about 12 mm radially for D09-like rotors) get Ke `unresolved`.
5. **Status display (D-007).**
   - The badge shows calculation trust; the "n assumptions" list shows what each number rests on.
   - No equation is validated yet, so physics results will show `inferred` at best.
6. **DRC (D-006).** The check is strict with no slack, so Xcoil's default design would fail it. The generator must keep
   a margin.
7. **Lengths of spiral coils.** The concentric-loop formula over-estimates a true spiral by about 4–8 % for many turns
   and about 23 % for D08's 3-turn coil. D08's 0.39 Ω is a model value, not a target.
8. **Unchanged from the first round:**
   - meaning of "verified";
   - patent review needed;
   - unsourced dominant inputs: µ_r, PCB copper = IACS, h, IPC-2152;
   - Python performance not measured;
   - mockups are static;
   - embodic licence open.
