Prepared by: Agent 5 — Research & Evidence Specialist — model: claude-opus-5-5

# Evidence gaps, conflicts and missing information (Phase 1 draft, 2026-10-04)

References use the document IDs (D01–D18) and EV-IDs of `evidence_register.md`; repository facts refer to
`repo_survey.md`; KiCad items to `kicad_plugin_evidence.md`. Every "proposal" is a suggestion (`assumption`
about the best way forward), not a result.

## 1. Engineering gaps

### G1 — No validated closed-form inductance for multi-layer planar spiral coils in a coreless air gap — `unresolved`
- Available: two "armature-reaction" (sinusoidal-MMF, magnetising) formulas — D10 eq. (14) p.5 and D15 eq. (14)
  p.8 (EV-31, EV-44). Neither includes slot/end-turn/leakage inductance, layer-to-layer spacing, finite coil
  span of concentrated coils, or spiral turn-area variation.
- Conflict 1 (inferred, Agent 5 algebra): substituting D10's own (12) into (13) gives
  L₁ = mµ₀(N₁k_w1)²(D_mo² − D_mi²)/(8δ′p²), which equals D15's (14), but D10's printed (14) is
  3µ₀(N₁k_w1)²(D²)/(4πδ′p²) — a factor 2/π smaller. One of the printed forms is inconsistent with its derivation.
- Conflict 2 (verified): D15 prints analytic phase inductances 16.5 mH and 15.2 mH (p.10) but FEA 16.71 µH
  (p.13) and 16.7 µH (p.14) for the same motor — a 1000× unit discrepancy.
- Measured magnitudes for coreless PCB windings: 14.8 µH (D09 concentric, 2 layers, Table 6 p.7), 22.3 µH
  self / −8.55 µH mutual (D07 Table 4 p.8), 0.1 mH (D06 FEA, Table II p.3).
- Proposal: (a) implement the corrected magnetising formula only as a first estimate; (b) add a filament model
  (Neumann mutual-inductance sum over straight/arc segments of every turn and layer, with back-iron treated by
  images — `assumption` to be justified); (c) validate both against D09 Table 6 and D07 Table 4 by re-creating
  their geometry (missing turn counts for D09 must first be obtained, see G2); (d) cross-check with an open
  magnetostatic FEM (e.g. FEMM 2-D at mean radius, or a 3-D solver) and, finally, LCR-meter measurement of a
  prototype.

### G2 — No complete measured reference case for a 3-phase multi-layer spiral PCB stator — `unresolved`
- Best available oracles (register §C): O1 thesis (spiral, 2 sides, measured K_e only, air gap ambiguous
  2.8 vs 1.4 mm), O2 Tokgöz (concentric, 2 layers, measured R/L/EMF/torque, but turns per coil and coil count
  not tabulated), O3 Wang 2019 (concentric spiral, 12 layers, measured R only as a number; EMF in figures),
  O4 Pan (spiral, 8 layers, 2-phase stepper, measured torque only).
- No source gives a >2-layer **3-phase** spiral stator with full geometry plus measured back-EMF, R and L.
- Proposal: (1) use O1 for back-EMF-constant regression and O2 for R/L/EMF/torque after extracting turn data from
  D09 Fig. 2/11 (image measurement) or asking the authors; (2) digitise D10 Fig. 18 (EMF vs speed) for O3;
  (3) build and measure one embodic reference board (R at known temperature, L at 1–10 kHz, K_e by spin test)
  as the first in-house oracle.

### G3 — Layer-dependent EMF in multi-layer stacks: conflicting assumptions — `unresolved`
- D15 p.8 assumes the same flux linkage for coils on all layers (EV-43).
- D01 p.2–3 (EV-20), D02 p.4–5 Fig. 11 (EV-35) and D13 p.3 (EV-42) show EMF/flux density varying with the layer's
  axial position (e.g. 14 V difference top–bottom in a 24-layer board, D01), causing circulating currents when
  layers are paralleled.
- Proposal: evaluate the field model at each layer's z-position (D08 eq. 3.1 already has z); flag parallel
  connections with ΔV between parallel paths; verify with 3-D FEA on one case. Series connection of layers sums
  the per-layer EMFs (inferred), which also needs per-layer evaluation.

### G4 — Eddy (AC) loss formulas in traces disagree — `unresolved`
- Per unit volume, uniform sinusoidal field of peak B: D03 eq. (2) and D14 eq. (3) give σω²B²w²/24 (EV-36, EV-39).
- D04 eq. (9) and D10 eq. (10) use π²f²/(3ρ) = ω²/(12ρ) — twice the /24 coefficient (inferred algebra) — and
  apply the width w² to both axial and tangential components, whereas D03 uses h² for the tangential component
  (physically the tangential field drives loops across the thickness — inferred). D04 eq. (9) also contains a
  symbol "L" that is not defined (p.7).
- Proposal: derive the thin-conductor low-frequency expression from first principles with explicit peak/RMS
  convention, keep the D03 form (axial ↔ width, tangential ↔ thickness) as the candidate, and check it with a
  2-D FEM of one trace in a uniform sinusoidal field; add a validity limit w, h ≪ skin depth (D01 eq. 4).

### G5 — IPC-2221 current/temperature limits not in the corpus — `unresolved`
- Only spacing guidance is quoted: 0.13 mm minimum gap "at our intended voltage" (D03 p.4, EV-32) and generic
  "follow IPC-2221" (D18 p.10). No paper gives the IPC-2221 (or IPC-2152) current-capacity relation or its
  validity range; the standards themselves are not available to the team (paywalled).
- Thermal evidence that exists: D10 12 A/mm² → 110.2 °C at 27 °C ambient (p.10); D09 concentric ≈ 44 °C after 5 min
  at 2 A (p.7); D13 13.6 A/mm² with 32.5 °C housing (p.14); D01 lumped equations (6)–(8); D08 network (7.1–7.5).
- Proposal: obtain IPC-2152 (preferred, newer) or IPC-2221B through a licensed copy and cite clause/figure; until
  then label any IPC-based current limit `assumption`; implement a lumped thermal network and validate it against
  D10's measured 83 K rise.

### G6 — Copper resistivity and temperature coefficient values not given in the corpus — `unresolved`
- D08 eq. (3.37) gives the linear law without numbers (EV-08); D14 Table 1 gives σ = 5.8 × 10⁷ S/m only.
  kimotor uses α = 3.99 × 10⁻² /°C (EV-R5), which appears 10× too high (inferred).
- Proposal: cite an authoritative standard/handbook (e.g. IEC 60028 annealed-copper standard or a recognised
  materials handbook) after obtaining it; record the chosen ρ₂₀ and α₂₀ with source; note that PCB electrodeposited
  copper may differ from annealed wire (needs a manufacturer source or a 4-wire coupon measurement).

### G7 — Via resistance and current crowding: FEA-only, different topology — `unresolved`
- D05 provides R_via = ρl/(2πrt) (EV-37) and FEA crowding results (EV-38) for a distributed winding with a
  laminated stator yoke; no measurement; 25 µm plating assumed.
- Proposal: include R_via in the phase-resistance sum with plating thickness as an explicit input; validate with
  a 4-wire measurement of a via-chain test coupon; for spiral coils the inner-end via of each layer pair is the
  likely crowding point (inferred from EV-40 current path).

### G8 — Bumby-type magnet field model: original not in the corpus — `unresolved`
- Bumby & Martin, "Axial-flux permanent-magnet air-cored generator for small-scale wind turbines", IEE Proc.
  Electr. Power Appl. 152(5) 1065–1075, 2005 is only cited (D10 ref [25] p.12; D11 ref [14] p.6). Field models
  actually present: D08 eq. (3.1) (after Vansompel 2013), D09 eq. (1) (scalar potential), D11 eqs. (8)–(9)
  (Halbach, attributed to Bumby), D12 vector potential.
- Proposal: obtain the 2005 paper and verify the parallel-magnetised, back-iron version of the model; compare
  D08 (3.1) and D11 (8)–(9) numerically against FEMM at mean radius for one geometry; document radial-edge
  limitations noted by D09 p.4.

## 2. Source-internal inconsistencies and conflicts

| ID | Issue | Location | Status | Proposal |
|---|---|---|---|---|
| G9 | D08 "area utilisation" (w_tr·l_total)/(π(r_si + r_so)) has the dimension of length, not a ratio | D08 p.23 eq. (2.1) (EV-10) | inferred (dimensional check) | Do not reuse; check D09's original definition |
| G10 | D08 air gap 2.8 mm (Table 3.2 p.35) vs 1.4 mm (Table 4.5 p.54); Table 4.1 "magnets per rotor" counts (20/40) seem to count both rotors (Fig. 4.1 p.49 shows 10 bars for config a) | D08 | inferred | Treat 2.8 mm as total and 1.4 mm per side only as `assumption`; sensitivity study in the O1 oracle test |
| G15 | D15 α_i = 2/π (p.7) vs α_i = π/2 (p.8) for "sinusoidal" flux | D15 | verified | Use α_i = 2/π (average/peak of a sine), labelled inferred |
| G16 | Review D18 p.8 says spiral windings reduce harmonic distortion; measured D09 Table 7 p.8 shows concentric THD 5.7 % (highest of five) | D18 vs D09 | verified (both statements) | Prefer the measured primary source |
| G17 | Same high-speed motor family: stator outer diameter 131 mm (D01 Table 1 p.2) vs 140 mm max (D06 Table I p.3) | D01 vs D06 | verified | Do not mix values across the two papers |
| G19 | D02 Table II trace isolation 0.025 mm looks implausibly small next to 0.20 mm width | D02 p.5 | inferred | Do not use as a manufacturing rule |
| G20 | D07 text mentions winding resistance 0.48 Ω (p.8) while Table 4 reports measured 0.43 Ω | D07 p.8 | verified | Use Table 4 values |
| G22 | D04 measured back-EMF (21/28.5 V) speed not stated; Fig. 18 time axis suggests ≈ 2 ms period (≈ 7500 rpm for 4 pole pairs) | D04 p.12–13 | inferred | Use only with this caveat |

## 3. Applicability limits

- G18 — D05, D13, D14, D16, D17 (Gachon group) use a **stator back yoke** of laminated electrical steel
  (35PN230/35PN300) with a single rotor, i.e. not the coreless double-rotor topology; their loss, inductance and
  MEC results do not transfer directly (verified from their Table 1s / p.2, p.4, p.7). D12 is coreless but
  wire-wound. Only D08, D09, D10, D11, D15 (and partially D02, D07) study planar spiral/concentrated or radial PCB
  coils in coreless machines.
- Wave-winding sources (D02, D03, D07, magnetless_motor) inform manufacturing, eddy loss and parallel-path issues,
  but their winding factors and EMF expressions should not be applied to spiral coils without re-derivation.

## 4. Repository and brief gaps

- G11 — magnetless_motor contains no electrical data or connection table; three terminal lands imply internal star
  or delta (`unresolved`); stack-up fields may be template defaults (`repo_survey.md` §1.5–1.7).
  Proposal: trace copper connectivity through the 617 vias with the Gerber parser (graph of segment end-points
  and via positions per layer) to recover phases, series/parallel paths and per-phase length → resistance; this is
  a useful geometry-engine regression test but not an electrical oracle.
- G12 — The Instagram spiral-coil concept could not be fetched (brief §1); the spiral layout remains `assumption`
  until the user's screenshot arrives.
- G14 — Venue/year `unresolved` for D02 (filename "2021 IEEE ECCE", not printed) and D07 (IET EPA revised manuscript,
  doi placeholder). Proposal: look up DOIs on IEEE Xplore / IET Digital Library.
- G21 — Brief labelling: `EPA-2020-0622-FINAL.pdf` is Tokgöz/Çakal/Keysan (not Paul et al.); CIEEC pattern paper is
  Li/Wang/Lv (not Moon et al.); two batch-2 files duplicate batch-1 files (D02, D05) → 18 unique documents.
- Brief Gerber summary corrections: "~1050 line segments per layer" = 351–389 lines + 674–696 arcs; "outline vertex
  radius ≈ 47.95 mm" = tangent point of flats to R3 corner arcs (max extent 48.0 mm) (`repo_survey.md` §1.4).

## 5. KiCad gaps (detail in `kicad_plugin_evidence.md` §4)

- G13 — `unresolved`: bundled Python version of KiCad 9.x on Windows; SWIG plugin folders for 9.0 on Windows;
  whether numpy installs into the bundled interpreter / IPC venv offline; DRC from SWIG or IPC; external-interpreter
  connection to KiCad on Windows; which `kicad-python` version matches the user's 9.0.x; creation of footprints/pads
  from scratch through IPC in 9.x. Proposal: smoke tests T1–T5 run by the user (≈ 20 lines each, Phase 2).

## 6. Information searched for and not found

- IPC-2221/IPC-2152 current-capacity equation and charts (G5).
- Numeric copper ρ₂₀/α₂₀ in any corpus paper (G6).
- Any measured inductance of a **multi-layer spiral** coreless stator (G1/G2).
- Measured via resistance in PCB motor stators (G7).
- The Bumby & Martin 2005 paper itself (G8).
- In magnetless_motor: code, equations, test data, rotor drawing (verified absent).
- On official KiCad pages read: KiCad 9.x Windows bundled Python version; complete IPC capability list for 9.0.x
  (only the kipy source gives method-level version notes).
