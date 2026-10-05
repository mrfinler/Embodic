Prepared by: Fable 5.1 — coordinator — model: claude-fable-5-1

# Fable investigations, 2026-10-05: OR-01 Ke shortfall and the serpentine eddy-loss difference

Both items were handed to Fable by the user ("OR-01 ให้ Fable เข้าไปจัดการ", "Eddy loss ฝาก Fable เช็ค"). Every number
below comes from a script in `docs/phase2/fable/checks/` run on main `270df35`; nothing was measured on hardware, so
the strongest label used here is `verified (by computation)`.

## 1. OR-01: embodic gives Ke_LL 0.02358 V·s/rad for UGent D08, measured 0.031 (−23.9 %)

### 1.1 What was ruled out

| Candidate | Check | Result |
|---|---|---|
| Field model EQ-05 too weak | `b1_peak_mid_radius_t` of the D08 run is 1.142 T; a magnetic-circuit estimate (two 5 mm N45SH magnets, 2.8 mm face-to-face gap, infinite iron) gives a fundamental of about 1.2 T; D08 Fig. 4.9 FEM (4 mm gap) peaks near 0.95 T flat-top | not the cause; if anything the model is slightly high because it assumes infinitely permeable back iron (D08 Table 4.8: a 3 mm plate behaves like B_rem 1.2 T instead of 1.38 T) |
| Circuit sum (polarity, distribution) | per-path flux-linkage phasors of phase A sum with k_d ≈ 0.966 as expected for 12/10; Ke_line = √3 · Ke_phase | not the cause |
| Path integral implementation (EQ-06) | re-implemented the segment sum independently from `integrate_path` on the same primitives: identical to 1e-16 | not the cause |
| Fundamental vs waveform peak | thd_line 0.0042; the peak differs from the fundamental by well under 1 % | not the cause |
| Air gap G 1.4 vs 2.8 mm (Phase 1 gap G10) | a larger gap lowers Ke further, the wrong direction | not the cause of a shortfall |

### 1.2 Root cause: the spiral advances its pitch on one side, which empties the inner turns

`docs/phase2/fable/checks/or01_turn_geometry.py` output (verified by computation):

```
embodic generated coil, one layer: p*flux = 0.00177 V*s/rad
concentric loops (both sides at offset (k+0.5) w_d, D08 Fig. 3.4): 0.00255 V*s/rad
spiral-equivalent loops (left side one pitch further in): 0.00182 V*s/rad
ratios: generated/concentric = 0.693; spiral/concentric = 0.713
```

The generated D08 coil (3 turns, w 2.06 mm, s 0.8 mm, pitch w_d 2.86 mm, 30° sector, r 12.5–44 mm) has its right-hand
sides at offsets 0.5, 1.5, 2.5 w_d from the sector edge and its left-hand sides at 1.5 and 2.5 w_d: every turn's left
side is one pitch further in than its right side, because the generator (spiral_generator_spec.md G4/G6/G7 as
implemented in U-M2d) steps inward along the side. In a sector this narrow the third turn then collapses to a 5 mm
triangle (r 33.15–38.28 mm) and the second to r 22.1–41.14 mm. D08's analytical model (thesis p.28–30, eq. 3.8–3.13,
Fig. 3.4) counts three concentric loops with both sides at offset (k + ½) w_d, and its measured Ke agrees with that
model within 8 % (p.93). The linkage ratio between the two constructions is 0.693, which is the whole shortfall:
0.02358 / 0.693 = 0.0340 V·s/rad.

Independent confirmation from resistance: D08 reports a phase resistance of 0.39 Ω at 50 °C (Table 4.6); embodic gives
0.289 Ω at 20 °C, 0.323 Ω at 50 °C, 17 % low, in the same direction and of the size the shorter inner turns imply.

### 1.3 What the number would be after the fix (inferred, not yet run)

With both sides of turn k at offset (k + ½) w_d, embodic's own field and integrator give 0.0340 V·s/rad (+9.6 %
against 0.031; the band is [−8 %, +8 % + e_edge 1.8 %] = [−8 %, +9.8 %]). The remaining excess is the infinitely
permeable back iron: D08 Table 4.8 gives B_rem 1.2 T equivalent for its 3 mm plate, which scales the model to
0.0296 V·s/rad (−4.6 %). D08's own model gives about 0.0285 (Table 4.6, 7.31 V phase at 6000 rpm read as RMS). So the
corrected geometry lands inside the band, and a back-iron saturation factor (today `back_iron: unresolved`) would
centre it. Neither claim is verified until U-M2d-2 runs OR-01 on the corrected generator.

### 1.4 Routing (D-028)

The construction rule is Agent 2's (spiral_generator_spec.md), so the fix is a spec revision, not a DRC or physics
change: the turn advance moves into an end-turn (a jog of one pitch where dr contributes almost nothing), and both
sides of each turn keep the same offset. This is also what D08's PCB (Fig. 4.8) shows, with slanted inner ends. The
spec revision goes with DEF-M2d-01 (lead route against the coil's own centre via) in U-E3; U-M2d-2 implements both.

## 2. DEF-M2e2-02: serpentine eddy loss 0.69 % above Xcoil

`docs/phase2/fable/checks/eddy_serpentine_vbus.py` output (verified by computation):

```
eddy loss by Xcoil object kind, W: {'strand': 0.101294289, 'vbus': 0.000707671, 'ic': 0.0}
all kinds / Xcoil pEddy = 1.006928
strand only at Xcoil rho / Xcoil pEddy - 1 = -1.887e-15
```

Cause: Xcoil's serpentine analysis integrates only objects of kind `strand` (engine.js l.889,
`if (o.kind !== 'strand') return;`); embodic integrates every copper path of the layout, so the layer-pair via bus
(`vbus`, 0.000708 W) is counted too. Sector and wave layouts have no `vbus` object, which is why they differ only by
the resistivity constant (embodic 1.7241e-8 Ω·m from the registry, Xcoil 1.724e-8; −5.8e-5 relative). The same
inclusion explains the +0.34 % phase resistance on the serpentine.

Ruling (D-029): embodic keeps counting all winding copper in the field, because the via bus carries the phase current
and sits inside the magnet span; the difference is recorded as an expected diff (EQ-12 eddy loss, EQ-10/EQ-11
resistance) with this decomposition as its test, so the golden comparison for serpentine compares the strand-only sum
exactly and the full sum within the documented margin. Status of the eddy-loss equation is unchanged.
