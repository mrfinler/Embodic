Prepared by: Agent 5 (Research & Evidence Specialist), model: claude-opus-5-5. Revisions 2026-10-08 (U-S3b, U-S3c) by Agent 5, model: claude-sonnet-5-5.

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
| G28: ISO 273 hole sizes | mounting-hole presets | M2 to M6 drill sizes (close / normal / loose) from a JIS B 1001 table (EV-87) and an ASME B18.2.8 table (EV-88), both read through extracts and identical for M2 to M6. ISO 273 table values not read (EV-78 holds the scope only) | `inferred`. The values are read as printed. Reading them as the ISO 273 fine / medium / coarse series is inferred from order | "Clearance-hole preset from JIS B 1001 and ASME B18.2.8 tables (EV-87, EV-88); ISO 273 text not read" |
| G23 (second part): NdFeB Br values | magnet examples (D-015 example rotor) | N35–N52 Br typical and minimum (EV-54), read through an extract | `verified (extract)`; the PDF itself not re-read | "Br from the Arnold catalog via extract (EV-54)" |

## Not found this round

- A manufacturer datasheet that states µ_rec for one specific sintered NdFeB grade. Both sources give a typical value
  for the class (EV-80, EV-81).
- An open application note from a semiconductor or PCB manufacturer that quotes IPC-2221 §6.2 with its validity range.
  The manufacturer statement found is a calculator web page (EV-83).
- The IPC-2221 and IPC-2152 texts, Bumby & Martin 2005, and Dai Pré & Bianchi 2006 (paywalled; not accessed).

## Revision 2026-10-08 (U-S3b): requests from the equation specification

Source: the "Source and unit gaps" table in `docs/phase2/engineering/equation_specification.md` and the U-E2, U-E3 and U-E3b reports. New entries are EV-84 to EV-93 in `evidence_register.json`. Web pages were read through WebFetch extracts. Direct downloads from physics.nist.gov and bipm.org were refused (proxy answer 403) and were not worked around. This unit did not edit the equation registry, so no EQ entry cites the new EV ids yet. The engineering owner decides which constants and `sources` lists change.

| Request | Result | EV ids | What remains |
|---|---|---|---|
| µ0 (EQ-13, EQ-14) and ε0 (EQ-29) | Closed as evidence. The 2022 CODATA adjustment gives µ0 = 1.256 637 061 27 × 10⁻⁶ N A⁻² (u = 0.20 × 10⁻¹⁵) and ε0 = 8.854 187 8188 × 10⁻¹² F m⁻¹. The SI brochure says µ0 is no longer exact | EV-84, EV-85, EV-86 | Registry constants hold 4π × 10⁻⁷ (differs by 1.3e-10 relative, 0.83 standard uncertainties) and 8.854e-12 (differs by -2.1e-5 relative). Both numbers were computed in this unit. Whether to change the constants is an engineering call |
| Screw clearance holes (U-M2d) | Two tables read for M2 to M6, with identical drill sizes. No ISO 273 table opened | EV-87, EV-88 (scope: EV-78) | G28 stays open for the ISO 273 text. The fine / medium / coarse mapping is inferred. The NBK page has no M2.5 row |
| EQ-08 feasibility, Q/(m·t) an integer | Stated for three phases as Z / (3 × GCD(Z, p)) in a journal paper. The definition t = GCD(Q, p) is in a conference presentation | EV-89, EV-90 | Neither is a textbook. Pyrhönen et al. (EV-61) and Dai Pré and Bianchi (EV-60) stay unopened |
| EQ-08 parallel paths dividing the periodicity | Gap G30. No opened source states the rule | none | Opened without a statement of the rule: the Leoben six-phase paper, Tessarolo 2019, the Alberti and Bianchi slides, the Emetor "number of parallel paths" page. A search hit from Nagasaki University (ICEMS 2011) redirected to a signed URL on another host and was not opened |
| IPC-2221 constants (G5) | No change. EQ-15 already cites EV-82 and EV-83 | EV-82, EV-83 | Unchanged from the G5 row above |
| EQ-18 THD | Oracle values read. D09 defines THD on no page of its text layer. Table 7 and the text differ by 0.1 point for radial (1.2 vs 1.3) and arc (2.8 vs 2.9) | EV-91 | Gap G31: a citable THD definition. No definition source was searched in this unit |
| EQ-19 triplen circulating current in a delta winding | Gap G32. One search returned only forum threads and a blog page, none opened as evidence | none | A textbook or standard that states the triplen path |
| EQ-20 SPWM, SVPWM, six-step, PMSM pull-out torque | Partly closed. An application note states the SVPWM and sine PWM linear limits (line-to-line VDC and √3/2 × VDC) | EV-92 | Gap G33: six-step fundamental and PMSM pull-out torque. The note covers induction motors and is not a textbook |
| EQ-23, EQ-24, EQ-26 involute property | Gap G37, not searched in the timebox | none | A textbook entry for the involute property. Whether the register needs a `kind` for a reproduction is a schema decision for Agent 2 and Fable, so this unit did not touch it |
| EQ-25, EQ-30 | No external source applies. Both are project rules (`spiral_generator_spec.md` G5 and G6, decision D-006) | none | Nothing for Agent 5 |
| EQ-28 densities | NdFeB density range read | EV-93 | Gap G34: rotor steel density, not searched. The registry holds 7.85 g/cm³ as an `assumption` |
| EQ-29 ε_r per dielectric | Gap G35, not searched. ε0 is closed by EV-85 | none | A datasheet for each laminate dielectric |
| EQ-16 laminate density | Gap G36, not searched | none | An FR-4 datasheet that states density. The registry holds 1.85 g/cm³ as an `assumption` |

### New gaps

| Gap | Affects | Current best value | Label | Assumptions tag text |
|---|---|---|---|---|
| G30: parallel-path rule | EQ-08 (U-M2c question b) | The number of paths a must divide t = gcd(Q, p). Derived by Agent 2 in `equation_specification.md`, no source | `unresolved` | "Parallel-path rule derived in EQ-08; no source read (G30)" |
| G31: THD definition | EQ-18 | THD = √(Σ_{n>1} Ke_n²)/Ke_1 as written in the specification. D09 Table 7 values (EV-91) have an unstated basis | `unresolved` | "THD relative to the fundamental; the basis of the D09 oracle is not stated (G31)" |
| G32: triplen current in a delta winding | EQ-19 | Resistance-limited upper bound from the specification | `unresolved` | "Triplen circulating current is an upper bound; no source read (G32)" |
| G33: six-step and pull-out torque | EQ-20 | SPWM and SVPWM linear limits from EV-92. No value for six-step or pull-out torque | `unresolved` for six-step and pull-out torque. `verified (extract)` for the two linear limits | "Drive voltage limits partly from an application note (EV-92); six-step and pull-out torque unsourced (G33)" |
| G34: rotor steel density | EQ-28 | 7.85 g/cm³ | `assumption` | "Rotor steel density is an assumption (G34)" |
| G35: dielectric constant | EQ-29 | per-dielectric ε_r from the specification | `assumption` | "ε_r per dielectric is an assumption (G35)" |
| G36: laminate density | EQ-16 | 1.85 g/cm³ | `assumption` | "Laminate density is an assumption (G36)" |
| G37: involute property | EQ-23, EQ-24, EQ-26 | reproduced by CF-06, CF-08 and arithmetic | `verified` (reproduction), no textbook entry | none |

### Not found in U-S3b

- Any text of ISO 273. The ISO page shows the scope and a preview link, not the table.
- A textbook statement that the parallel paths of a concentrated winding divide t = gcd(Q, p).
- Searches that were not run: THD definition, rotor steel density, ε_r datasheets, FR-4 density, involute property. Each has a gap row above. They ran past the 30-minute timebox.

## Revision 2026-10-08 (U-S3c): gaps G31 and G34 to G37

New entries are EV-94 to EV-105 in `evidence_register.json`. Web pages were read through WebFetch extracts, so each row is `verified (extract)`. No EQ entry in the equation registry cites the new ids yet. The engineering owner decides which constants and `sources` lists change.

| Gap | Result | EV ids | Label now | What remains |
|---|---|---|---|---|
| G31: THD definition | Four definitions read. Wikipedia and the MATLAB `thd` page put harmonics over the fundamental, as EQ-18 does. The Analog Devices tutorial MT-003 puts the fundamental over the harmonics. None is IEEE 519 or IEC. None of the 12 local papers or the thesis defines THD | EV-101, EV-102, EV-103 (basis of the D09 numbers: EV-91) | The form √(Σ_{n>1} Ke_n²)/Ke_1 is `verified (extract)` as a common definition from a secondary page. The D09 basis stays `unresolved` | IEEE 519-2022 or IEC 61000-4-7 text, and the D09 authors' basis (harmonic range, phase or line voltage) |
| G34: rotor steel density | One datasheet read: AISI 1018 cold drawn, 7.87 g/cc. The registry holds 7.85, which is -0.25 % from it | EV-100 | `assumption` stays for the rotor steel. The 1018 value is `verified (extract)` for that grade only | The user's rotor steel grade, or a source that states 7.85 |
| G35: ε_r per dielectric | Read: RO4350B 3.48 at 10 GHz (EV-94), Kapton HN 3.4 to 3.5 at 1 kHz (EV-95), 370HR 4.04 to 4.24 across 100 MHz to 10 GHz (EV-96), G10/FR4 sheet 4.8 with no frequency (EV-97, EV-98), PTFE 2.1 with no frequency (EV-99). The Xcoil values are FR-4 4.4, FR-4 high-Tg 4.2, polyimide 3.5, RO4350B 3.48, PTFE 2.1 | EV-94 to EV-99 | `assumption` stays for plain FR-4 (4.4): no PCB-laminate datasheet read states 4.4, and ε_r depends on frequency and resin content. The other four entries have a datasheet value near the Xcoil value | A datasheet for the user's chosen FR-4 grade, and the frequency at which ε_r applies to the inter-layer capacitance |
| G36: laminate density | Read: FR-4 sheet stock specific gravity 1.85 (EV-97) and 1.89 (EV-98), no unit given. The Isola 370HR PCB laminate sheet states no density (EV-96). Related: RO4350B 1.86 g/cm3 (EV-94), Kapton HN 1.42 g/cc (EV-95), PTFE 2.13 to 2.22 (EV-99) | EV-94, EV-95, EV-97, EV-98, EV-99 | `assumption` stays for FR-4. The registry value 1.85 equals EV-97, but that is sheet stock and the two vendors differ by 0.04 | A PCB-laminate datasheet that states density for the stack-up material |
| G37: involute property | The property is read ("A perpendicular to the involute surface is always tangent to the base circle") and the parametric form is read (MathWorld). No textbook was opened. The rotated-copy normal spacing r_b Δφ is on neither page | EV-104, EV-105 | The property and the equation of P(t) are `verified (extract)`. The r_b Δφ spacing stays a derivation (CF-08 reproduces it) | A textbook entry (Beyer, Gray, Lawrence are cited by MathWorld and were not opened) |

Searches that did not give evidence: no PCB-laminate datasheet with a density was opened (370HR has none). A search for a PTFE manufacturer sheet returned distributors only. A search for a rotor-steel density of 7.85 returned the 1018 sheet at 7.87.
