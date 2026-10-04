Prepared by: Agent 5 (Research & Evidence Specialist), model: claude-opus-5-5

# Source gaps that still affect Phase 2 results

Each row names a gap that changes a computed number or its label. The application shows the "Assumptions tag text"
in the result's assumptions tag (D-007) whenever the result uses the listed equation. Gap ids continue those of
`docs/phase1/evidence/evidence_gaps.md`. EV ids resolve in `evidence_register.json`. Searches for this unit ran on
2026-10-04 through WebSearch and WebFetch. Direct downloads from arnoldmagnetics.com, advancedmagnets.com, mit.edu and
uark.edu were refused by the session's egress policy (proxy answer 403). gnu.org refused WebFetch (robots.txt).

## Gaps named in the brief

| Gap | Affects | Current best value | Label | Assumptions tag text | What would close it |
|---|---|---|---|---|---|
| G23: NdFeB recoil permeability | EQ-05 field model (µ_r term), so EMF, torque constant, THD | µ_r = 1.05 for sintered NdFeB (EV-80 manufacturer sheet, EV-81 Arnold slides). Alternative from the N42 datasheet: Br/(µ₀HcB) ≈ 1.10 (EV-55, derived). Bonded NdFeB: 1.1–1.7 by grade (EV-81) | `inferred`. The value is read in two manufacturer sources. Applying a typical value to the user's grade is an inference | "Recoil permeability 1.05, typical for sintered NdFeB (EV-80, EV-81); not grade-specific" | A grade-specific datasheet that states µ_rec, or a measured demagnetisation curve. The user can enter a value with `measured` provenance |
| G5: IPC-2221 current formula | EQ-15 current-capacity guideline | I = k·ΔT^0.44·A^0.725, A in mil², ΔT in K, k = 0.048 external and 0.024 internal (EV-82 university thesis, EV-83 PCB manufacturer page). Both attribute it to IPC-2221 §6.2 | `unresolved` (EQ-15 gate "cannot verify yet"). Coefficients `verified` as stated by two secondary sources. Origin in the standard's text `inferred`. Validity range `unresolved` | "IPC-2221 chart-fit, coefficients from secondary sources (EV-82, EV-83); standard text not read; validity range unknown; guideline (unverified)" | A licensed copy of IPC-2221B §6.2 (figure and any equation) |
| G5: IPC-2152 | none in Phase 2 (no IPC-2152 mode) | no value | `unresolved` (not accessed) | Do not offer an IPC-2152 option | A licensed copy of IPC-2152 |
| G8: Bumby & Martin 2005 | EQ-05 Halbach variant (D11 eqs. 8–9 cite it) | No value from the paper. EQ-05 uses D08 eq. 3.1 (after Vansompel 2013) with Agent 2's closed form | `unresolved` for any Bumby-based model. EQ-05 itself stays `inferred` (registry) | "Field model after D08 eq. 3.1; Bumby & Martin 2005 not accessed (EV-63)" | IET Digital Library or library access to DOI 10.1049/ip-epa:20050094 |
| G24: Dai Pré & Bianchi 2006 | EQ-08 coil/pole feasibility and winding factor | No rule from the paper. EQ-08 computes star-of-slots EMF phasors directly. Corpus rules: N_c/N_pm = m/(m+1) (EV-56), star of slots with "coil side" for "slot" (EV-58) | `assumption` for any closed feasibility rule. The explicit phasor computation carries EQ-08's own status | "Coil/pole feasibility checked by explicit star-of-slots phasors; textbook rule not accessed (EV-60, EV-61)" | Library access to IEE Proc. EPA 153(3) 459–466, or Pyrhönen et al. with edition and section |
| G2: D09 turns per coil | Oracle O2 (Agent 4 tests). Any D09-based example preset | 6–8 turns per coil per layer: 6–7 counted in the low-resolution Fig. 1a, 7–8 from the 3244 mm phase length (EV-62) | `unresolved` | For a D09 example preset: "Turns per coil not stated by the source; 6–8 estimated (EV-62)" | Ask the authors (address printed on D09 p.1), or measure Fig. 11a with a scale reference. Run O2 for N = 6, 7, 8 against R = 1.07 Ω |

The IPC-2221 (1998) copy hosted at snebulos.mit.edu was tried once. The WebFetch extract reached only the table of
contents (§6.2 "Conductive Material Requirements"), so whether the 1998 standard prints the equation or only the
charts is undetermined. The copy is not an IPC distribution and its redistribution status is unknown. It is not used
as evidence.

## Other open gaps that change a number

| Gap | Affects | Current best value | Label | Assumptions tag text |
|---|---|---|---|---|
| G6: PCB copper vs IACS | EQ-10 resistance, EQ-16 mass | ρ₂₀ = 1.7241 × 10⁻⁸ Ω·m, α₂₀ = 0.00393 /K, density 8.89 g/cm³ (EV-53, NBS Handbook 100; page numbers from an extract) | `inferred` for PCB copper | "Annealed-copper (IACS) values used for PCB copper (EV-53)" |
| G7: via plating | EQ-11 via resistance | plating 25 µm as in D05 (EV-37) | `assumption` (input default) | "Via plating 25 µm (D05 value, EV-37)" |
| G1: inductance | EQ-14 | magnetising term only, D10 eq. (14) form (EV-31) | `unresolved` (estimate) | "Inductance first estimate; no end-turn or leakage terms (EQ-14)" |
| G4: trace eddy-loss coefficient | EQ-12 | D03 form σω²(B_z²w² + B_φ²h²)/24 per volume (EV-36) | `inferred` | "Eddy loss uses the D03 thin-conductor form; sources disagree by 2× (G4)" |
| G3: layer-dependent EMF | EQ-07 | field evaluated at each layer's z (EQ-05) | `inferred` | "Per-layer EMF from the 2-D field model; not FEA-checked (G3)" |
| G28: ISO 273 hole sizes | mounting-hole presets | no table values read (EV-78) | `assumption` | "Clearance-hole preset is a team assumption; ISO 273 values not read" |
| G23 (second part): NdFeB Br values | magnet examples (D-015 example rotor) | N35–N52 Br typical and minimum (EV-54), read through an extract | `verified (extract)`; the PDF itself not re-read | "Br from the Arnold catalog via extract (EV-54)" |

## Not found this round

- A manufacturer datasheet that states µ_rec for one specific sintered NdFeB grade. Both sources give a typical value
  for the class (EV-80, EV-81).
- An open application note from a semiconductor or PCB manufacturer that quotes IPC-2221 §6.2 with its validity range.
  The manufacturer statement found is a calculator web page (EV-83).
- The IPC-2221 and IPC-2152 texts, Bumby & Martin 2005, and Dai Pré & Bianchi 2006 (paywalled; not accessed).
