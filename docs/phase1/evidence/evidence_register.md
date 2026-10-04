Prepared by: Agent 5 — Research & Evidence Specialist — model: claude-opus-5-5

# Evidence register (Phase 1 draft, 2026-10-04)

Path aliases: **B1** = `/mnt/user-data/uploads/paper/`; **B2** = `/mnt/user-data/uploads/Desktop/Fantastic Creature/FC-Smart_Actuator/papers/`.
Page numbers are **PDF page indices** (1-based); a printed journal/thesis page is added where it differs.
`Status` refers to whether Agent 5 read the claim in the source (`verified`) — it does **not** mean the claim is
physically correct or that it transfers to embodic; transfer is judged in the "Applies" column (that judgement is
always `inferred`). Equations were read from the rendered page (Read tool) where marked "(img)"; otherwise from
text extraction.

## A. Source documents (20 files, 18 unique)

| Doc | File(s) | Title | Authors | Venue / year (first page) | Topology studied |
|---|---|---|---|---|---|
| D01 | B1/`IET Electric Power Appl - 2019 - Salim - Multiphysics analysis….pdf` | Multiphysics analysis of printed circuit board winding for high-speed axial flux permanent magnet motor | N. Salim, S.P. Nikam, S. Pal, A.K. Wankhede, B.G. Fernandes | IET Electr. Power Appl. 13(6) 805–811, 2019, doi 10.1049/iet-epa.2018.5752 | Distributed multilayer PCB winding (12 layers), Halbach rotor, single-sided, 4-pole |
| D02 | B1/`2021IEEEECCEUKSPARKWaveWindingPCBStatorCorelessAFPMMachine.pdf` = B2/`Design-Optimization-and-Experimental-Study-…-Wave-Winding-PCB-Stators.pdf` (identical, md5 953a2284…) | Design Optimization and Experimental Study of Coreless Axial-flux PM Machines with Wave Winding PCB Stators | P. Han, D. Lawhorn, Y. Chulaee, D. Lewis, G. Heins, D.M. Ionel | Venue not printed in PDF; filename says 2021 IEEE ECCE; PDF created 2021-08-24 → `unresolved` | Continuous wave winding, stacked PCBs, double rotor; reviews spiral winding |
| D03 | B1/`Design Optimization of Coreless Axial-Flux PM Machines with Litz.pdf` | Design Optimization of Coreless Axial-Flux PM Machines with Litz Wire and PCB Stator Windings | M.G. Kesgin, P. Han, N. Taran, D. Lawhorn, D. Lewis, D.M. Ionel | 2020 IEEE ECCE pp. 22–26, doi 10.1109/ECCE44975.2020.9236194 (accepted manuscript, UKnowledge) | 2-phase wave (Litz and PCB), 3-phase FSCW |
| D04 | B1/`energies-11-03383 (1).pdf` | Winding Design and Analysis for a Disc-Type Permanent-Magnet Synchronous Motor with a PCB Stator | X. Wang, H. Lu, X. Li | Energies 11, 3383, 2018 | Spiral vs distributed vs "improved" PCB windings, 12 layers |
| D05 | B1/`actuators-14-00424-v2 (1).pdf` = B2/`actuators-14-00424-v2.pdf` (identical, md5 bf5d706e…) | A Study on Reducing Loss in PCB Motor Stator Using Multi-Via Structure | S.-B. Jeon, D.-H. Choi, H.-S. Han, Y.-H. Song, W.-H. Kim | Actuators 14, 424, 2025 | Distributed 3-phase 2-turn 6-layer PCB stator **with laminated stator back yoke**; vias |
| D06 | B1/`compare.pdf` | Performance Comparison Between PCB-stator and Laminated-core-stator Based Designs of AFPM Motors for High-speed Low-power Applications | Neethu S., S.P. Nikam, S. Pal, A.K. Wankhede, B.G. Fernandes | IEEE Trans. Ind. Electron., accepted article, DOI 10.1109/TIE.2019.2931503 (2019) | Same distributed PCB motor family as D01 vs toroidal-core motor |
| D07 | B1/`Revised_manuscript_Final.pdf` | A Comparative Analysis of Wave Winding Topologies and Performance Characteristics in Ultra-thin PCB AFPM Machine | S. Paul, M. Farshadnia, A. Pouramin, J. Fletcher, J. Chang | IET Electr. Power Appl. — revised manuscript, doi placeholder; year `unresolved` (PDF created 2019-03-26) | Overlapping parallel / non-overlapping radial / overlapping radial wave windings, 2 layers |
| D08 | B2/`799354017-Pcb-stator-thesis.pdf` | Design and prototyping of PCB stator electric motor with FDM 3D printed parts | E. Collijs, R. Vereecken (supervisor P. Sergeant) | Master's dissertation, Ghent University, 2020–2021 | **Concentrated spiral trapezoidal coils**, 12 coils/side, 10 poles, double rotor |
| D09 | B2/`EPA-2020-0622-FINAL.pdf` | Comparison of PCB winding topologies for axial-flux permanent magnet synchronous machines | F. Tokgöz, G. Çakal, O. Keysan | IET Electr. Power Appl., accepted 28 Oct 2020, doi 10.1049/iet-epa.2020.0622 (vol 14 no 13 pp 2577–2586 per D08 ref [6]) | Concentric (spiral-like), radial, arc, parallel, UEW windings; 16 poles, 2 layers |
| D10 | B2/`Electromagnetic_Design_and_Analysis_of_…Unequal-Width_PCB_Winding.pdf` | Electromagnetic Design and Analysis of Axial Flux Permanent Magnet Generator With Unequal-Width PCB Winding | X. Wang, W. Pang, P. Gao, X. Zhao | IEEE Access 7, 2019, doi 10.1109/ACCESS.2019.2952893 | **Concentric spiral** PCB winding, unequal width, 12 layers (2 × 6 parallel) |
| D11 | B2/`Performance_Improvement_by_Pattern_Optimization_of_PCB_Winding_in_Coreless_AFPM_Motor.pdf` | Performance Improvement by Pattern Optimization of PCB Winding in Coreless Axial Flux Permanent Magnet Motor | C. Li, X. Wang, H. Lv | 2021 IEEE 4th CIEEC, doi 10.1109/CIEEC50170.2021.9510731 | **Non-overlapping concentrated** (hexagonal) PCB coils, 12 slots/14 poles, Halbach |
| D12 | B2/`SCI_Volume 29_Issue 6_Pages 3326-3337.pdf` | Design optimization of a low-speed small-scale modular AFPM synchronous generator for urban wind turbine application | H. Saneie, A. Daniar, Z. Nasiri-Gheidari | Scientia Iranica D 29(6) 3326–3337, 2022 | Coreless, **wire-wound** non-overlapping concentrated coils (not PCB) |
| D13 | B2/`actuators-15-00087.pdf` | Magnetic Equivalent Circuit-Based Performance Evaluation of Modular PCB AFPM Motor for Electric Water Pumps | D.-H. Choi, W.-H. Kim, H. Jang | Actuators 15, 87, 2026 | 10/30 distributed PCB, 6 layers, stator back yoke 35PN300 |
| D14 | B2/`actuators-15-00327.pdf` | A Printed Circuit Board Stator Pattern for Loss Trade-Off Mitigation in Slotless AFPM Motors | J.-W. Moon, H.-S. Han, J.-H. Lee, D.-H. Choi, W.-H. Kim | Actuators 15, 327, 2026 | PCB **concentrated** winding pattern, slotless with stator 35PN230 |
| D15 | B2/`electronics-15-00777.pdf` | Design and Performance Enhancement of a PCB-Based Axial-Flux Stepper Motor | Y. Pan, H. Zhang, J. Xu, C. Zhu, C. Wu, H. Li | Electronics 15, 777, 2026 | **Spiral** (trapezoid + circular) coils, 8 layers, 2-phase stepper, double rotor |
| D16 | B2/`energies-18-02538-v2.pdf` | Design for Loss Reduction in a Compact AFPM Electric Water Pump with a PCB Motor | D.-H. Choi, H.-S. Han, M.-K. Hong, D.-H. Jung, W.-H. Kim | Energies 18, 2538, 2025 | Single-rotor PCB AFPM with stator yoke, 12 V EWP |
| D17 | B2/`energies-19-01060-v2.pdf` | A Study on the Mitigation of Back-EMF Imbalance in Axial Flux Motors with PCB Stators | M.-S. Youn, M.-K. Hong, S.-H. Ko, D.-W. Nam, W.-H. Kim | Energies 19, 1060, 2026 | 8P24S SSSR PCB stator, stator yoke 35PN230; end-turn layouts |
| D18 | B2/`engproc-87-00013.pdf` | The Utilization of Printed Circuit Boards (PCBs) in Axial Flux Machines: A Systematic Review | I. Shuaibu, E.H.T. Wei, R. Kannan, Y.A. Samaila | Eng. Proc. 87, 13, 2025 | Review (38 papers 2019–2024) |

Brief labelling corrections (verified from first pages): `EPA-2020-0622-FINAL.pdf` is **Tokgöz, Çakal, Keysan**
(not "Paul et al."); the Paul et al. paper is batch-1 `Revised_manuscript_Final.pdf`. The "pattern optimisation"
CIEEC paper is by **Li, Wang, Lv**; Moon et al. is `actuators-15-00327.pdf`.

## B. Register

| EV-ID | Claim or equation | Source | Location | Applies to spiral coil / coreless AFPM? | Status |
|---|---|---|---|---|---|
| EV-01 | Spiral winding = spiral coils, each two complementary spirals (top and bottom layer, same direction) joined by vias; suited to high-polarity machines; coils in one layer may belong to one phase or several | D02 Han et al. | B2/Design-Optimization-…pdf p.1 §I, Fig. 1b p.2 | yes — defines the embodic topology | verified |
| EV-02 | Concentrated spiral trapezoidal coil modelled as closed concentric loops; w_d = w_tr + w_s (3.5); flux per loop/slice Φ_l,q = B̄ t_sl r (φ_max−φ_min) (3.6–3.11); Φ_l = ΣΦ_l,q (3.12); ψ_coil = ΣΦ_l (3.13) | D08 Collijs & Vereecken | B2/799354017-Pcb-stator-thesis.pdf p.32–35 (printed 27–30) §3.1.2 | yes — direct spiral-coil flux-linkage integration | verified |
| EV-03 | Axial field between two back plates: Fourier series with sinh/cosh terms (3.1), τ_P(r) = rπ/p (3.2), rectangular-magnet angular width τ_M(r) (3.3); assumes infinite back-plate permeability; source Vansompel 2013 | D08 | p.30–32 (printed 25–27) §3.1.1, Table 3.1, Fig. 3.3 | yes (double rotor, coreless) — compared with FEM at r = 40 mm only | verified |
| EV-04 | Back-EMF per coil E = −(dψ/dθ_m)·ω (3.14); phase EMF = signed sum of coils per winding table (12-slot/10-pole, Bavaria tool) | D08 | p.36 (printed 31) §3.1.3 | yes | verified |
| EV-05 | Torque per wire section T = I·B·L·cos α·r (3.19–3.21), summed over sections/loops/coils (3.22–3.23); only straight (radial) sections produce torque | D08 | p.38–40 (printed 33–35) §3.2 | yes | verified |
| EV-06 | Max turns per trapezoidal spiral coil: N_c < ½((r_o−r_i)/w_d + 1) (3.24) and trapezoid/triangle split (3.25–3.26), after Noh et al. AIM 2019 | D08 | p.43 (printed 38) §3.3 | yes (single-layer geometry rule) | verified |
| EV-07 | Spiral coil track length = Σ over loops of outer arc + inner arc + 2 straight segments, coil span θ_cs = π/p (3.27–3.36) | D08 | p.44–45 (printed 39–40) §3.4 | yes (ignores vias, corner rounding). Re-check 2026-10-04: θ_cs = π/p is the pole pitch; it equals the geometric coil pitch 2π/Q only when Q = 2p. For D08's own 12 coils/10 poles, 12 × 36° > 360°, so non-overlapping coils must use 2π/Q = 30° (inferred; agrees with Agent 2 EQ-01/C7). Residual check (DEF-15, re-run of `verification/checks/v3_geometry_resistance.py` on 2026-10-04): D08 Table 4.5 p.54 states a **50 °C** track temperature; at 50 °C the π/p variant gives 0.439 Ω (+12.7 %) and 2π/Q gives 0.381 Ω (−2.3 %) against D08 Table 4.6's 0.39 Ω (π/p reaches 0.393 Ω only at 20 °C, which contradicts the stated 50 °C). The residual therefore favours 2π/Q; which span the thesis model actually used is undetermined | verified (as printed); correction inferred |
| EV-08 | ρ_T = ρ_20(1 + α_c(T − 20 °C)) (3.37); R_phase = ρ_T L_tot /(w_tr t_tr) (3.38); no numeric α_c or ρ_20 given | D08 | p.45 (printed 40) | yes (DC only) | verified |
| EV-09 | Copper-loss budget method: 4 W total copper loss per PCB, phase current from Ohm's law with the two PCB sides in series (4.3, extracted text reads "√(4 (3 W)/R_tot,series)", i.e. probably (4 W/3)/R per phase — reading inferred); design sweep w_tr 0.16–3.5 mm and r_i, r_o | D08 | p.53–54 (printed 48–49) §4.2, Table 4.5 | yes (method) | verified (text); formula reading inferred |
| EV-10 | Area-utilisation coefficient (w_tr·l_total)/(π(r_si + r_so)) (2.1), attributed to Tokgöz et al. | D08 | p.23 (printed 18) §2.2.2 | doubtful — dimension is length, not a ratio (see gaps G9) | verified (as printed) |
| EV-11 | Thermal: layer resistances R = l/(kA) (7.1), convection R = 1/(hA) (7.2), h correlation after Osczevski (7.3–7.4), network R_total = 5.11 K/W (7.5) for 4 W per side | D08 | p.81–83 (printed 76–78) §7 | partly (motor-specific network) | verified |
| EV-12 | Concentric winding: high induced voltage from large flux-linking area and long radial paths, but long end connections → higher resistance and losses | D09 Tokgöz et al. | B2/EPA-2020-0622-FINAL.pdf p.1 §1, p.1–2 §2.1.1 | yes (concentric ≈ spiral) | verified |
| EV-13 | Analytical open-circuit field by magnetic scalar potential (eq. 1), <1 % fundamental error vs FEA at mean radius; misses radial edge leakage → Br(r) curve-fitted from FEA | D09 | p.3–4 §3.1, Table 3, Figs 5–7 | partly — needs radial correction | verified |
| EV-14 | Flux linkage by area integration over each loop region: φ = ∫∫ k_w B_r(r) B_max sin(ωt + pθ) r dθ dr with r-dependent limits; V = −N dφ/dt (eqs 5–11); any loop shape via integration limits | D09 | p.5 §3.2 | yes — method transfers to spiral loops | verified |
| EV-15 | Torque via f = J×B integrated over copper volume (eqs 2–4); simplified f = J_rms B_avg B_r(r) cos α, v = N l w t (12–14) | D09 | p.4, p.6 §3.2 (img) | partly | verified |
| EV-16 | PCB cost: >6 layers increases cost sharply; 35→70 µm copper large cost step, 70→105 µm almost none; 1000-piece cost 13 % of 10-piece cost (for their supplier) | D09 | p.3 §2.2, Fig. 3 | yes (manufacturing context, supplier-specific) | verified |
| EV-17 | In spiral-type PCB windings only radial tracks produce back-EMF/torque; concentric (circumferential) tracks are a "passive conduction path" adding Joule loss and occupying active area | D07 Paul et al. | B1/Revised_manuscript_Final.pdf p.3 §2.1 | yes | verified |
| EV-18 | Line current density A_m(r) = m₁√2 N₁ I_a /(p τ(r)) (1); dT = 2π α_i k_w1 A(r) B_mg r² dr (3) | D07 | p.2–3 | partly (radius-dependent loading) | verified |
| EV-19 | Coreless PCB inductances are µH-range because the effective air gap is large and turns are few | D07 | p.7 §3 | yes | verified |
| EV-20 | Multilayer parallel layers: R_eff = R/(N/2) (1); circulating-current loss P_c = V_d²/(R₁+R₂+R_c) (2); 24 layers: V_d = 14 V, P_c ≈ 12 W; 12 layers: ≈ 0.5 W | D01 Salim et al. | B1/IET…Salim….pdf p.2–3 (journal 806–807) §2, Fig. 2–3 | yes for parallel layer connection (layers at different distance from magnets see different EMF) | verified |
| EV-21 | Skin depth δ = 1/√(πfμσ) (4); R_sk = ρl/(w t_eff), t_eff = δ(1 − e^(−t/δ)) (5); proximity effect negligible for their 12 × 50-conductor model at 1 kHz | D01 | p.3–4 (journal 807–808) §3 | yes (general conductor physics) | verified |
| EV-22 | Thermal: θ = L/(K·A_c) (6), ΔT_cond = P·θ (7), ΔT_conv = P/(h_t A_PCB) (8), h_t = 10 W/m²K "widely used"; K: copper 355, FR4 0.25, solder mask 0.21, air 0.0275 W/mK (Table 3); stack-up prepreg 0.07, laminate 0.13/0.15 mm (Table 4) | D01 | p.4 (journal 808) §4 | yes (lumped thermal) | verified |
| EV-23 | Eddy loss in a conducting support disc P_e = 1.65 V_e B_m² d² f²/ρ; ≈ 5 W at 3000 rpm with stainless steel → use non-conducting support (nylon) | D01; D06 | D01 p.3 eq (3); D06 B1/compare.pdf p.3 eq (4) (img) | yes (mechanical/material rule) | verified |
| EV-24 | EMF E_f = π√2 p N₁ K_w N_s Φ_f /60, Φ_f = πB_g(R_mo² − R_mi²)/(2p) (3); torque T_d = m₁E_f I_a·60/(2πN_s) (2) | D06 Neethu et al. | B1/compare.pdf p.3 §III-A (img) | partly (sinusoidal, distributed) | verified |
| EV-25 | Spiral winding (concentric circle coils per phase in series): inner coils have shorter effective length and smaller pitch coefficient; more copper, lower efficiency than distributed | D04 Wang, Lu, Li | B1/energies-11-03383 (1).pdf p.3 §2.1, Fig. 3a | yes (qualitative) | verified |
| EV-26 | Winding/distribution factor k_wν = k_qν = sin(qα₁ν/2)/(q sin(α₁ν/2)) (1); Φ, E₀ = √2πfNk_w1Φ (2–4); r_s = ρΣl_n/S_n (7) | D04 | p.5–6 §3.1–3.3 | partly (distributed-winding factor) | verified |
| EV-27 | Eddy loss ΔP = (π²/3ρ) f² w_L³ b L (B_mtλ² + B_maλ²) η_d² (9), η_d distortion factor (10); loss ∝ f² and w³; symbol "L" undefined | D04 | p.7 §3.4 (img) | partly — coefficient conflicts with EV-36/EV-39 (gaps G4) | verified |
| EV-28 | Concentric spiral PCB winding with unequal-width active conductors; D_mo = D_max − 2N(w_oc + d_oc) (2); w_oe = πD_mo/(2mpN) − d_L (3); 12 layers = 2 groups of 6 parallel layers in series | D10 Wang, Pang, Gao, Zhao | B2/Electromagnetic_Design_…pdf p.2–3 §II-A, Fig. 2–3, Table 1 (img) | yes (spiral coil geometry rules) | verified |
| EV-29 | Conductor EMF E_c = ΩB_av(D_mo² − D_mi²)/8 (4); E_φ = √2πfN₁k_w1Φ_m (6); Φ_m = (π/8p)α_iB_m(D_mo² − D_mi²) (7); r₀ = ρΣL_n/S_L (8) | D10 | p.3–4 §III-A,B (img) | yes/partly (sinusoidal fundamental) | verified |
| EV-30 | Eddy loss p_v = (1/ρ_L)(π²/3ρ) f² w_L² m_c (B_mt1² + B_ma1²) η_d² (10) | D10 | p.4 §III-B (img) | partly — see gaps G4 | verified |
| EV-31 | Armature-reaction inductance: F₁ = (m√2/π)N₁k_w1I₁ (11); B_m1 = (µ₀/δ′)(√2m/2)(N₁k_w1/p)I₁ (12); ψ₁ (13); L₁ = (3µ₀/πδ′)(N₁k_w1/2p)²(D_mo² − D_mi²) (14), δ′ = δ + 2h_m | D10 | p.4–5 §III-C (img) | partly — magnetising term only. Revised 2026-10-04: printed (14) is consistent with the standard MMF amplitude F̂₁ = (m√2/π)(N₁k_w1/p)I₁ and with (13); the inconsistent step is (12), which uses √2m/2 instead of √2m/π (and (11) omits 1/p) — see gaps G1 | verified (as printed); consistency inferred |
| EV-32 | IPC-2221 recommends a minimum 0.13 mm gap between traces "at our intended voltage"; 0.15 mm minimum trace width chosen; literature widths: 1.2 mm (25 Hz), 0.2–0.3 mm with 0.23–0.3 mm gap (33.3 Hz), 0.3 mm with 0.3 mm gap (1 kHz) | D03 Kesgin et al. | B1/Design Optimization…Litz.pdf p.4 (paper p.2) §II | yes (manufacturing/voltage rule; secondary citation of IPC-2221) | verified |
| EV-33 | Max Litz strand diameter ≈ δ/3 | D03 | p.3 §II | partly (Litz) | verified |
| EV-34 | PCB macro-coil fill factor 0.303 (D03) and 0.2286 (D02, 16 traces in substrate) | D03; D02 | D03 p.5 §IV; D02 p.2 Fig. 3 | partly (depends on stack-up) | verified |
| EV-35 | Trace-by-trace model: OC voltage larger in layers closer to the PMs and rows nearer the coil centre-line; with all traces of a turn in parallel the peak circulating current is 1.44 A vs 0.315 A applied per trace at 3050 r/min; speed limited to 1400 r/min | D02 | p.4–5 §IV, Fig. 11 (img) | yes for any parallel-connected traces/layers | verified |
| EV-36 | PCB trace eddy loss (rectangular): P_eddy = σL_cN_cN_tN_s ω² (B_az² w² + B_aφ² h²) w h /24 (2); Litz (1) | D03 | p.5 §III (img) | yes (straight traces, uniform sinusoidal field, end coils neglected) | verified |
| EV-37 | Via barrel area A = π(r² − (r−t)²) ≈ 2πrt (3–5); R_via = ρ l/(2πrt) (6); plating 25 µm | D05 Jeon et al. | B2/actuators-14-00424-v2.pdf p.6, p.8 §2.2–3 | yes (vias in any PCB stator) | verified |
| EV-38 | Current crowding at vias raises phase resistance; multi-via (two 0.30 mm vias at inner 1st position + outer 0.40/0.30 mm) lowers phase resistance and peak current density ≈ 20.7 % (0.106 → ≈ 0.084 Ω; 42.19 → 33.45 A/mm²), copper loss 50.08 → 39.70 W — **FEA only** | D05 | p.3, p.12–15 §4 | partly (distributed winding with stator yoke) | verified |
| EV-39 | Rectangular conductor eddy loss per volume P_ec = c²ω²B_m²/(24ρ) (3); reduce/split effective width | D14 Moon et al. | B2/actuators-15-00327.pdf p.5 §2.2 | yes (planar concentrated pattern) | verified |
| EV-40 | Concentrated PCB pattern current path: outer → inner on one layer, via to next layer, inner → outer | D14 | p.4 §2.1, Fig. 2 | yes (describes spiral coil layer pairing) | verified |
| EV-41 | Narrow effective conductor (α = 0.53) + two parallel conductors via-connected: phase R −11.82 %, DC −12.1 %, AC −15.09 %, total −12.48 %, efficiency 81.53 → 83.5 % — **FEA only**; Cu σ = 5.8 × 10⁷ S/m, Br 1.43 T (Table 1) | D14 | p.1 abstract, p.11 Table 1 | partly (stator core) | verified |
| EV-42 | Layers closer to magnets see higher B and dB/dt → AC loss concentrates there; "pyramid" layer-dependent trace width; MEC within ≈ 5 % of 3D FEA and prototype | D13 Choi, Kim, Jang | B2/actuators-15-00087.pdf p.3 §1, p.15 §5 | yes (layer-dependent field); MEC partly (yoke) | verified |
| EV-43 | Spiral multilayer coils: via current is axial (parallel to field) → no torque; "flux linked by coil units at the same angle on different layers is essentially the same" → torque = single-layer torque × layers | D15 Pan et al. | B2/electronics-15-00777.pdf p.8 §2.3 (img) | yes, but the equal-flux assumption conflicts with EV-20/EV-35/EV-42 (gaps G3) | verified |
| EV-44 | Spiral resistance r = ρΣL_i/(w·d) (10); inductance L = m(µ₀/δ)(Nk_w1)²(D_out² − D_in²)/(8p²) (14), δ = air gap + two magnet thicknesses | D15 | p.7–8 §2.2.3 (img) | partly (magnetising term). Revised: (14) follows from its eq. (12), which carries the same √2m/2 coefficient as D10 (12); with √2m/π it would be π/2 smaller, i.e. D10's (14) (inferred, G1) | verified (as printed) |
| EV-45 | Pole-arc coefficient α_i = 2/π for sinusoidal flux (p.7) but α_i = π/2 "under a sinusoidal flux density distribution" (p.8) | D15 | p.7 below eq. (7); p.8 below eq. (15) (img) | internal inconsistency (gaps G15) | verified |
| EV-46 | Non-overlapping concentrated coils: outer-bridge connection balances MMF, lowest pull force (0.026 N vs 0.68/0.65 N inner bridge); Halbach B_z model (8)–(9) citing Bumby & Martin; per-turn flux (10)–(12); E = 4√2 f S_c N_l q p Σφ_i (13); S_c (14) | D11 Li, Wang, Lv | B2/Performance_Improvement_….pdf p.3–4 §III–IV (img) | yes (planar concentrated coils, coreless) | verified |
| EV-47 | Coreless modular AFPM (wire-wound concentrated coils): 2-D vector-potential model at a given radius + 3-D correction; self/mutual inductance eqs (38)–(41); validated only by 3-D TSFEM (no prototype) | D12 Saneie et al. | B2/SCI_Volume 29….pdf p.3–9 §2–5 | partly (coreless concentrated, not PCB) | verified |
| EV-48 | End-turn layout of PCB stator causes back-EMF imbalance between phases; BCAACB layout gives lowest average resistance and phase-resistance variance (FEA) | D17 Youn et al. | B2/energies-19-01060-v2.pdf p.1 abstract, p.6–7 §3 | partly (yoke stator, distributed) — relevant to 3-phase balance checks | verified |
| EV-49 | Design current density limited to 30 A/mm² for manufacturability; PCB permits 4–5× conventional current density, limited to 2× for stability (FEA) | D16 Choi et al. | B2/energies-18-02538-v2.pdf p.16–17 | partly | verified |
| EV-50 | Review: follow IPC-2221 for trace width/spacing; use many vias for interlayer connections; FR4 Tg ≥ 170 °C | D18 Shuaibu et al. | B2/engproc-87-00013.pdf p.10 §3.5 | yes (secondary source) | verified |
| EV-51 | Review claims spiral windings give "reduced harmonic distortions" | D18 | p.8 | conflicts with measured O2 (D09 Table 7: concentric THD 5.7 %, highest) — gaps G16 | verified (claim exists) |
| EV-52 | PCB stators operate at current densities 3–4× wound machines (citing [15]) | D05 | p.3 §2.1 | partly (secondary) | verified |

### Rows added 2026-10-04 (coordinator follow-up)

| EV-ID | Claim or equation | Source | Location | Applies to spiral coil / coreless AFPM? | Status |
|---|---|---|---|---|---|
| EV-53 | International Annealed Copper Standard: volume conductivity exactly 58 m/(Ω·mm²) at 20 °C, i.e. ρ₂₀ = 0.017241 Ω·mm²/m = 1.7241 × 10⁻⁸ Ω·m (mass resistivity 0.15328 Ω·g/m²); temperature coefficient 0.00393 per °C at 20 °C; density 8.89 g/cm³; adopted by the IEC in 1913, IEC Publication 28 (rev. 1925) reproduced as Appendix 5 | U.S. National Bureau of Standards, *Copper Wire Tables*, Handbook 100, 1966 | https://nvlpubs.nist.gov/nistpubs/Legacy/hb/nbshandbook100.pdf p.2 (resistivity), p.3 (0.00393), p.4 (density), p.39 (App. 5) — page numbers from WebFetch extract | yes for annealed copper; PCB electrodeposited copper may differ (G6) | verified (extract; re-check pages) |
| EV-54 | Sintered NdFeB, Arnold catalog Rev. 181031: Br typical/min — N35 1.21/1.17 T, N38 1.26/1.22, N40 1.285/1.25, N42 1.315/1.28, N45 1.35/1.32, N48 1.40/1.37, N50 1.425/1.39, N52 1.45/1.42 T; α(Br) −0.12 %/°C | Arnold Magnetic Technologies, NdFeB catalog | https://www.arnoldmagnetics.com/wp-content/uploads/2017/10/Catalog-151021.pdf (table) | yes (magnet input data) | verified (extract; numbers must be re-checked in the PDF — a second datasheet extract (Eclipse) returned implausible values and was rejected) |
| EV-55 | Arnold N42 datasheet Rev. 210607: Br nominal 1315 mT, min 1280 mT, HcB 955 kA/m, BHmax 334 kJ/m³, α(Br) −0.12 %/°C; **no recoil permeability stated**. Apparent recoil slope Br/(µ₀HcB) = 1.315/(4π×10⁻⁷ × 955×10³) ≈ 1.10 (Agent 5 arithmetic) | Arnold Magnetic Technologies | https://www.arnoldmagnetics.com/wp-content/uploads/2017/11/N42-151021.pdf | yes; µ_r ≈ 1.05 **not found** in sources accessed (G23) | verified (extract); 1.10 inferred |
| EV-56 | Coil/pole relation for the coreless concentrated-coil generator: N_c/N_pm = m/(m+1) (eq. 1) | D12 Saneie et al. | B2/SCI_Volume 29….pdf p.3 §2 (img) | yes (e.g. 12 coils/16 poles, 3 phases); one rule among others, not a general FSCW feasibility test | verified |
| EV-57 | Pole number chosen so that GCD(N_c, N_m) = 2K to minimise torque pulsation (core-type AFPM) | D06 | B1/compare.pdf p.2 §II | partly (cogging context; coreless has no cogging) | verified |
| EV-58 | Slotted-machine winding relations (star of slots, Liwschitz wave method) apply to slotless PCB windings with "slot" replaced by "coil side" | D07 | B1/Revised_manuscript_Final.pdf p.3 §2.2 | yes (method) | verified |
| EV-59 | PCB pitch factor as average of per-turn pitch factors: K_pν = (1/N) Σ sin(((β − 2α_i)/β)(π/2)ν) (eq. 6) | D15 | B2/electronics-15-00777.pdf p.7 (img) | yes (spiral coils with turns of different span) | verified |
| EV-60 | M. Dai Pré, N. Bianchi, "Use of the star of slots in designing fractional-slot single-layer synchronous motors", IEE Proc. Electr. Power Appl. 153(3) 459–466, 2006, ISSN 1350-2352 (author order as listed by Dialnet) — full text not available there | Dialnet record | https://dialnet.unirioja.es/servlet/articulo?codigo=1979238 | yes (FSCW feasibility/winding factor) | bibliographic verified; content **not accessed** |
| EV-61 | J. Pyrhönen, T. Jokinen, V. Hrabovcová, *Design of Rotating Electrical Machines* (Wiley) — winding-factor chapter | textbook | — | yes | **not accessed** (edition/section not verified) |
| EV-62 | D09 concentric board: 12 non-overlapping trapezoidal spiral coils per layer, each with a via at its inner end; 2 layers (Table 2); 6 terminals at the top; turns per coil ≈ 6–7 per layer (count from embedded raster, low resolution); cross-check: 3244 mm/8 coil-layers ≈ 405 mm per coil-layer and a mean loop of ≈ 50–55 mm → ≈ 7–8 turns | D09 Tokgöz et al. | B2/EPA-2020-0622-FINAL.pdf p.2 Fig. 1a (img, 600–1200 dpi render), p.3 Tables 1–2, p.7 Fig. 11a | yes — oracle O2 geometry | coil count verified; turn count inferred → `unresolved` |
| EV-63 | J.R. Bumby, R. Martin, "Axial-flux permanent-magnet air-cored generator for small-scale wind turbines", IEE Proc.-Electr. Power Appl. 152(5) 1065–1075, Sept. 2005, DOI 10.1049/ip-epa:20050094; no open copy found (IET page 403 to the fetcher) | D10 ref [25]; IET Digital Library | B2/Electromagnetic_Design_…pdf p.12 ref [25]; https://digital-library.theiet.org/doi/10.1049/ip-epa:20050094 | yes (field model) | bibliographic verified; content not accessed |
| EV-64 | ECM US 10,170,953 B2: radial conductors + inner/outer end turns in serpentine pattern, parallel layers via blind/buried vias (FIG. 3), serpentine encircles centre three times (FIG. 9), subassemblies in series; independent claims 1, 9, 14, 15, 17 | E-Circuit Motors (Shaw) | https://patents.google.com/patent/US10170953 ; https://patents.justia.com/patent/10170953 | partly — wave/serpentine prior art and patent-risk reference (`ecm_pcb_stator_evidence.md` R1–R4) | verified (extract) |
| EV-65 | ECM US 11,336,130 B1: all inter-layer vias on one radial side outside the active region, layers in series; dep. cl. 3 serpentine, cl. 4 **spiral**; FIG. 10 16-pole three-turn single-phase connection | E-Circuit Motors (Shaw, Milheim) | https://patents.justia.com/patent/11336130 | yes — patent-risk item R5 | verified (extract) |
| EV-66 | ECM US 9,800,109 / US 10,256,690: end-turn corner geometry ("Corner Equation", continuously varying curvature), slit end turns for eddy-loss reduction (FIGS. 9–11) | E-Circuit Motors (Shaw) | https://patents.justia.com/patent/9800109 ; …/10256690 | partly — patent-risk item R6 | verified (extract) |
| EV-67 | ECM US 10,211,694: thermal-only copper elements inside/outside the active radii, thermally but not electrically connected | E-Circuit Motors (Shaw) | https://patents.justia.com/patent/10211694 cl. 1 | partly — patent-risk item R7 | verified (extract) |
| EV-68 | ECM US 12,424,901 B2: stator segments with different winding characteristics; Y/delta/separate terminal schemes (FIGS. 8A–8C) | E-Circuit Motors (Shaw, Milheim) | https://patents.justia.com/patent/12424901 | partly | verified (extract) |
| EV-69 | ECM site: >90 % efficiency, 66 % weight and 70 % axial-length reduction, up to 80 % less copper, zero cogging, "continuous coil design", PrintStator outputs Gerbers | pcbstator.com | https://pcbstator.com/overviews/printed-circuit-board-stator-electric-motor/ ; https://pcbstator.com/pcb-stator-technology/ | context only | **marketing claim** |
| EV-70 | User images: Instagram render shows dense radial conductors with nested outer/inner end-turn groups (8 + 8 positions), via rows, 8 rim holes; ECM board shows fine radial traces and 9 terminal pads (3 × 3) | user screenshots | `reference_images/` (see `ecm_pcb_stator_evidence.md` §1) | illustrative only | inferred from image |
| EV-71 | magnetless_motor end turns: outer nested caps of 6 radii (13.5–16.4 mm) centred at r = 26 mm on 12 axes per layer (G1 0° + k·30°, G3 15° + k·30°); inner arcs concentric with the board, radii 14.3–17.2 mm, 4–6° spans at ≈20°/25° mod 30° → wave-like series path, not concentrated spiral coils | gouldpa00/magnetless_motor | `…/gerbers/mini_wave-bb.G1`, `.G3` (Agent 5 parse) | partly | verified (parse); interpretation inferred |

### Rows added 2026-10-04 (defect-fix round: fonts, colours, fasteners, KiCad format)

| EV-ID | Claim | Source | Location | Applies? | Status |
|---|---|---|---|---|---|
| EV-72 | Noto Sans (latin-greek-cyrillic): SIL Open Font License 1.1, "Copyright 2022 The Noto Project Authors"; no reserved font name listed. (The notofonts.github.io site repo itself is Apache-2.0 — code, not the fonts) | notofonts (official) | https://github.com/notofonts/latin-greek-cyrillic/blob/main/OFL.txt ; https://github.com/notofonts/notofonts.github.io/blob/main/LICENSE | yes (UI font licence) | verified (extract) |
| EV-73 | Liberation fonts: SIL OFL 1.1, "Digitized data copyright (c) 2010 Google Corporation", "Copyright (c) 2012 Red Hat, Inc.", **with Reserved Font Name Liberation** | liberationfonts (official) | https://github.com/liberationfonts/liberation-fonts/blob/main/LICENSE | yes — a modified/subsetted copy may not keep the name "Liberation" (OFL RFN rule; inferred) | verified (extract) |
| EV-74 | Cascadia Code: SIL OFL 1.1, "Copyright (c) 2019 - Present, Microsoft Corporation, **with Reserved Font Name Cascadia Code**" | microsoft/cascadia-code | https://github.com/microsoft/cascadia-code/blob/main/LICENSE | yes — RFN applies to modified versions (inferred) | verified (extract) |
| EV-75 | JetBrains Mono: SIL OFL 1.1, "Copyright 2020 The JetBrains Mono Project Authors"; no reserved name listed | JetBrains/JetBrainsMono | https://github.com/JetBrains/JetBrainsMono/blob/master/OFL.txt | yes | verified (extract) |
| EV-76 | Manrope: SIL OFL 1.1, "Copyright 2018 The Manrope Project Authors (https://github.com/sharanda/manrope)"; no reserved name listed (upstream repo path `OFL.txt` returned 404; copy read from the Google Fonts repository) | google/fonts (ofl/manrope) | https://github.com/google/fonts/blob/main/ofl/manrope/OFL.txt | yes | verified (extract, mirror of upstream) |
| EV-77 | Harmonised conductor colours: L1 brown, L2 black, L3 grey, N blue, PE green-and-yellow (citing BS EN 60446:2000, BS EN 60445:2000, HD 308 S2, BS 7671:2001 Amd 2:2004). IEC 60445 itself (webstore.iec.ch/en/publication/66712, 2021 ed.) and IEC 60757 (colour code designations) were **not accessed** (paywalled) | IET *Wiring Matters*, Spring 2004 | https://electrical.theiet.org/media/1720/harmonised-colours-and-alphanumeric-marketing.pdf | partly — an installation-wiring convention, not a rule for plot/UI phase colours; other regional practices (e.g. North American) `not found` | verified (extract, secondary IET source) |
| EV-78 | ISO 273:1979 "Fasteners — Clearance holes for bolts and screws", edition 1, 2 pages, ISO/TC 2/SC 7, status published, confirmed 2024-07-10; scope: hole diameters for fine, medium and coarse series for threads 1–150 mm; preview on ISO OBP. **Table values not accessed** | ISO | https://www.iso.org/standard/4183.html | yes (mounting-hole presets) | bibliographic/scope verified; values not accessed |
| EV-79 | KiCad board file `(layers (ORDINAL "CANONICAL_NAME" TYPE ["USER_NAME"]))`; ordinal "used to associate the layer stack ordering"; canonical names F.Cu, In1.Cu…In30.Cu, B.Cu; **no ordinal values or KiCad 9 change documented**. KiCad 8 baseline file writes 0 = F.Cu, 1…6 = In1…In6.Cu, 31 = B.Cu | dev-docs file formats; kimotor example board | https://dev-docs.kicad.org/en/file-formats/sexpr-pcb/ (Layers Section); `/home/claude/embodic-ref/kimotor/kimotor-project/kimotor-project.kicad_pcb` `(layers …)` | yes | docs verified (extract); KiCad 9 ordinals `unresolved` |

### Repositories and KiCad documentation

| EV-ID | Claim | Source | Location | Applies? | Status |
|---|---|---|---|---|---|
| EV-R1 | magnetless_motor README: 6-layer, 1 oz, 0.5 mm radial traces, wave winding, 3 phases, 16 coils-equivalent/phase, layer groups 3+3, Ø25 mm hole, 93 mm flats, 16 magnets 20×6×2 | gouldpa00/magnetless_motor @c6ec327e (2026-03-28) | `/home/claude/embodic-ref/magnetless_motor/README.md` lines 1–12 | partly — wave, not spiral | verified |
| EV-R2 | Gerber parse: 144 radial conductors/layer r 18–38 mm at 2.5°; 617 Ø0.3/0.5 vias (576 on 4 rings + 41 in clusters); 3 terminal lands; R3 corners on 93.0 mm flats | same | `…/gerbers/` (.GTL…GBL, .TXT, .DRR, .GM1); details `repo_survey.md` §1.4 | partly — manufacturing example | verified (parse) |
| EV-R3 | Licence GPL-3.0 | same | `LICENSE` lines 1–2 | reference only | verified |
| EV-R4 | kimotor: SWIG `pcbnew.ActionPlugin` + wxPython + NumPy; PCM metadata `kicad_version` "6.0"; GPL-2.0-only SPDX headers, no LICENSE file; last commit 2024-06-09 | cooked/kimotor @dc6cac3a | `/home/claude/embodic-ref/kimotor/` `kimotor_action.py` l.24, `metadata.json`, file headers | architecture reference only | verified |
| EV-R5 | kimotor `stats_rlc` temperature coefficient 3.99e-2 /°C (≈10× typical copper value) | same | `kimotor_action.py` `stats_rlc` ≈ l.1520–1530 | do not reuse | verified value; judgement inferred |
| EV-K1 | SWIG bindings deprecated as of KiCad 9.0, removal planned 11.0; unstable between major versions | KiCad dev-docs "PCB Python Bindings" | https://dev-docs.kicad.org/en/apis-and-binding/pcbnew/ §Deprecation notice, §Introduction | yes (plugin route) | verified |
| EV-K2 | IPC API in 9.0: PCB editor only (9 and 10), running GUI required, no plotting/export, standalone plugin processes, plugins in `${KICAD_DOCUMENTS_HOME}/<version>/plugins`, per-plugin venv in `${KICAD_CACHE_HOME}/python-environments/<id>`, bundled Python on Windows by default | KiCad dev-docs "For Add-on Developers" | https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/for-addon-developers/ | yes | verified |
| EV-K3 | PCM metadata.json required fields; code packages must use a GPL-compatible open-source licence; `runtime` "ipc"/"swig" (9.0.1+, default swig); archive layout `plugins/` (files directly inside; 24×24 toolbar icon), `resources/icon.png` 64×64; schema v1 = KiCad 6.0+, v2 = KiCad 10.0+ (so v1 for KiCad 9) | KiCad dev-docs "KiCad Addons" | https://dev-docs.kicad.org/en/addons/ | yes | verified |
| EV-K4 | kicad-python: MIT, Python ≥ 3.9, protobuf/pynng/jsonschema; requires running KiCad with API enabled (Preferences > Plugins); 0.4–0.6 ↔ KiCad 9.0.3–9.0.8 | PyPI + wheel 0.8.0 | https://pypi.org/project/kicad-python/; `kipy/board.py` version notes | yes | verified |
| EV-K5 | kipy Board: commit API, create/update/remove items, Track/ArcTrack/Via/Zone/FootprintInstance/Pad, get_stackup, refill_zones, save; no DRC-run method | kicad-python 0.8.0 wheel | `kipy/board.py` l.584–1417; `kipy/board_types.py` | yes | verified (source read) |
| EV-K6 | KiCad source licensed GPL v3 or later | kicad.org | https://www.kicad.org/about/licenses/ | yes (licensing) | verified |

## C. Reference calculation cases with published numbers (candidate test oracles for Agents 2 and 4)

Ranked by closeness to embodic (3-phase spiral/concentrated planar coils, coreless double rotor). "Meas." = the
paper reports it as measured; "calc."/"FEA" = analytical/simulated in the paper. Embodic results must never be
called measured (brief rule 5).

**O1 — D08 thesis (spiral trapezoidal, 3-phase, 12 coils per PCB side, 10 poles, double rotor) — best topology match.**
Geometry: r_i = 12.5 mm, r_o = 44.0 mm, w_tr = 2.06 mm, w_s = 0.8 mm, 3 turns per coil, t_tr = 34.8 µm, 2 PCB sides in
series, PCB 0.6 mm (Table 7.1; column mapping inferred) — p.55, 57 Table 4.6, p.54 Table 4.5, p.81 Table 7.1. Magnets N45(SH) 18 × 10 × 5 mm,
B_rem 1.38 T, r_i,PM 15.4 mm, r_o,PM 43.4 mm (two magnets per pole, T-arrangement, configuration b) — p.35 Table 3.2,
p.49 Table 4.1/Fig. 4.1. Air gap: 2.8 mm (Table 3.2 p.35) vs 1.4 mm (Table 4.5 p.54) → `unresolved`, probably total
vs per side (inferred).
Calc.: phase back-EMF 7.31 V at 6000 rpm, phase current 1.84 A, torque 63.85 mN·m, phase resistance 0.39 Ω, power
40.12 W (Table 4.6 p.57). **Meas.**: line-line peak back-EMF constant K_e = 0.031 V·s/rad, K_v = 32.32 rad/(V·s);
data 454 rpm 1.47 V, 1009 rpm 3.26 V, 1559 rpm 5.08 V, 2045 rpm 6.56 V, 2514 rpm 8.18 V, 2877 rpm 9.35 V (peak L-L)
(Table 9.1 p.98, printed 93); analytical model within max 8 % (p.98). Torque/efficiency tests include ESC and bearing
losses (Tables 9.2–9.3 p.102) → not usable as motor-only oracle. No measured R or L.

**O2 — D09 Tokgöz (concentric, 3-phase, 16 poles, 2 layers, double rotor).**
Table 2 p.3: 2000 rpm, 266.67 Hz, air gap 1 mm, Br 1.33 T, magnet 2 mm, rotor OD 92 / ID 50 mm (PCB inner/outer diameters equal for
all windings), PCB 1 mm, rotor core 5 mm, trace width 0.8 mm, clearance 0.2 mm, copper 70 µm; field-model rotor:
distance between rotor cores 7 mm, magnet/pole-pitch 0.8 (Table 3 p.4). Concentric: phase trace length 3244 mm,
mid-turn loop area 171 mm², calc. phase R 1.04 Ω (Table 1 p.3). Calc. 6.21 V, 182 mN·m (Table 4 p.6); FEA 6.20 V,
178 mN·m (Table 5 p.6); **meas.** R 1.07 Ω, L 14.8 µH (Table 6 p.7); **meas.** full load 2 A: 6.22 V, 175 mN·m, copper
loss 12.8 W, output 24.5 W, THD 5.7 % (Table 7 p.8); stator ≈ 44 °C after 5 min full load (p.7). Voltages are RMS
(inferred: Fig. 15 p.8 shows ≈ 8.8 V peak). Other windings (radial 6.29/6.30/6.21 V, 0.86 Ω, 12.2 µH …) usable as
cross-checks. Concentric board (EV-62): **12** non-overlapping trapezoidal spiral coils per layer, 2 layers, 6 terminals,
via at each coil's inner end (Fig. 1a p.2, read from the rendered figure) — 12 coils/16 poles; turns per coil ≈ 6–7 per layer
from the low-resolution figure, ≈ 7–8 from the 3244 mm phase length → exact turn count still `unresolved`.
Table 6 p.7 reports "phase inductance" (and resistance) as "measured" without stating the method (LCR meter, frequency,
single-phase vs line-line/2, rotor present or removed) → the quantity is `unresolved` (DEF-08); compare it only with a
model quantity once the definition is known, not directly with a synchronous (magnetising + mutual) inductance.

**O3 — D10 Wang 2019 (concentric spiral UEW, 3-phase, 32 poles, 48 virtual slots, 12 layers).**
Table 1 p.3: 240 W, 300 r/min, PCB OD 222 mm, air gap 0.9 mm, PM 7.0 mm, copper 0.14 mm/layer, spacing 0.3 mm, PCB
winding 3.2 mm, 12 layers. Calc. reactance 0.259 Ω / impedance 2.017 Ω at 300 r/min (Table 2 p.5); air-gap fundamental
0.9 T, THD 13.6 % (p.5–6). **Meas.** phase R 2.15 Ω (sim. 2.00 Ω) (p.8); output 223 W at 4.1 A, efficiency 63.8 %
(p.10); 12 A/mm² → 110.2 °C at 27 °C ambient, natural cooling (p.10); R ∝ T (Fig. 25 p.10). Back-EMF vs speed only
in Fig. 18 (no table) → numbers would need digitising.

**O4 — D15 Pan 2026 (spiral, 8 layers, 2-phase stepper, 12 poles).**
Table 2 p.10: magnet OD 40 / ID 27 mm, 4 mm, gap 0.7 mm, stator 40/27 mm, conductor 0.3 mm, spacing 0.2 mm, 2 oz,
8 layers, 12 coils/phase, 4 turns/coil (p.8). Calc. back-EMF L-L fundamental 172.5 → 221.4 mV (p.10); FEA phase L
16.71 µH (p.13); R 5.5 Ω, L 16.7 µH (p.14); **meas.** average torque 46.4 mN·m at 1.5 A (p.22); max winding 63.4 °C
after 20 min (p.20). Caveat: analytic L printed as 16.5/15.2 **mH** (p.10) vs 16.71 **µH** FEA (gaps G1).

**O5 — D07 Paul (non-overlapping radial wave, 2 layers, 10 poles).** Table 1 p.2: magnet radii 33/66 mm, 3 mm, Br
1.17 T, air gap 1 mm, 4 oz, PCB 1.6 mm, 30 tracks/phase/layer. **Meas.** L_s 22.3 µH, L_m −8.55 µH, R_s 0.43 Ω
(sim. 21/−8 µH, 0.41 Ω) (Table 4 p.8); back-EMF fundamental 3.2 V at 600 rpm (−5.8 %) (p.7); torque 0.96 N·m at
full load (−15.5 %) (p.7–8). Useful as an inductance-magnitude oracle for coreless PCB windings.

**O6 — D04 Wang 2018 (distributed/"improved", 8 poles, 120 slots, 12 layers).** Tables 1–2 p.4: 7500 rpm, 10.4 A,
0.35 N·m, 280 W, 20 turns, conductor 0.64 mm wide, 1.26 mm thick, air gap 4 mm, magnet ID 44.8 / OD 77.4 mm, 2.9 mm.
**Meas.** phase R 0.078 Ω (distributed) / 0.0635 Ω (improved) (p.12); line back-EMF amplitude 21 V / 28.5 V vs sim.
21.43 / 29.16 V (p.8, p.13; speed of measurement not stated → `unresolved`); torque 0.45 N·m at 11.1 A, 3000 rpm vs
sim. 0.53 (p.13).

**O7 — D01/D06 Salim/Neethu (distributed, 12 layers, 4-pole Halbach).** **Meas.** AC resistance 1.6 Ω (12 Hz),
1.642 (0.5 kHz), 1.7 (1 kHz), 1.75 (1.5 kHz), 1.82 (2 kHz), 1.9 Ω (2.5 kHz) (D01 Table 7 p.6); PCB steady state ≈ 37 °C
(D01 p.6); FEA table: back-EMF 48 V peak/phase, R 1.8 Ω, L 0.1 mH, B_g 0.3 T, 9 A/mm² (D06 Table II p.3, img).

**O8 — D02 SPARK (wave).** Table II p.5 (img): rotor OD 270.4 / ID 182 mm, magnet 5 mm, back iron 10 mm, stator
144.5/304.9 mm, trace width/isolation 0.20/0.025 mm, thickness 0.07 mm, trace length 8 m, 5 active layers, 26 magnets.
**Meas.** OC back-EMF at 562 r/min, 1.5 mm air gap (Fig. 13 p.5): oscilloscope read-out ≈ 64 V p-p, ≈ 22.3 V RMS,
121.6 Hz — read from a low-resolution screenshot → `inferred` (121.6 Hz agrees with 13 pole pairs × 562/60 = 121.8 Hz).

**O9 — D11 Li/Wang/Lv (concentrated, 12 slots/14 poles, Halbach).** Table III p.5: 400 W, 375 r/min, D_in 104 / D_out
180 mm, 11 turns per coil per layer, armature 6.3 mm, gap 8 mm, magnet 6 mm. Calc. 59.5 V vs FEM 60 V back-EMF
amplitude (p.5); measured waveform shown (Fig. 11) but value not legible → `unresolved`.

Not oracles (FEA only or not PCB): D05, D12, D13 (prototype torque/temperature only, yoke stator), D14, D16, D17.

## Revision 2026-10-04 (defect fixes)

- DEF-15: EV-07 remark reworded — at D08's stated 50 °C (Table 4.5 p.54) π/p gives 0.439 Ω (+12.7 %) and 2π/Q 0.381 Ω
  (−2.3 %) vs 0.39 Ω (re-run of Agent 4's `v3_geometry_resistance.py`); residual favours 2π/Q, thesis choice undetermined.
- DEF-08: O2 now records that D09 Table 6 p.7 gives "phase inductance" without method, frequency or rotor condition
  (`unresolved`).
- EV-K3 corrected: PCM metadata schema v2 is KiCad 10.0+; KiCad 9 packages use v1.
- Added EV-72…EV-79 (font licences, conductor colours, ISO 273, KiCad layer ordinals) for Agents 1 and 3.
