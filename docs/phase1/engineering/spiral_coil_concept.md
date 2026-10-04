Prepared by: Agent 2 — Motor Design Expert — model: claude-opus-5-5

# Spiral-coil stator concept drawing — notes (Phase 1 draft, 2026-10-04)

File: `spiral_coil_concept.svg` (900 × 730 px, black/grey/white only, English labels, legend included).

**This is a concept drawing, not computed geometry.** I authored the SVG by hand with a short coordinate helper for
regular angular spacing; it was *not* produced by the Xcoil v3 engine or any embodic geometry engine. Coil shapes, turn
counts (three nested outlines are only a symbol for "spiral"), radii, via positions, ring radii and terminal positions are
schematic. No dimension, field, EMF, resistance or other electrical value may be read from it (status of the whole drawing:
`assumption` — design concept).

## What the drawing shows

| Panel | Content | Basis | Status |
|---|---|---|---|
| A — coil plan | 12 concentrated spiral coils on one layer pair, 30° coil pitch, labelled A1+ … C4+ in the order A C B A C B …; all coils positive with the same circulation (CW arrows for positive current); a centre via in each coil eye; two outer terminals per coil; dashed phase rings outside r_o; U, V, W and star point N on the outer rim; inner reference ring of 16 rotor poles (N black, S white) | Star-of-slots pattern for 12/16 from `checks/kw.py` ("ACBACBACBACB", k_w1 = 0.866); 16 poles from the repository rotor (README); terminals on the outer rim as in Xcoil v3 and the repository (EV-R2) | pattern `verified (reproduced)`; layout `assumption` |
| B — layer stack | Six layers as three X/Y pairs P1–P3 connected in series (option M2): L1 spirals in → centre via Vc1 → L2 spirals out (mirrored artwork, same circulation) → outer transfer via Vt1 → L3 in → Vc2 → L4 out → Vt2 → L5 in → Vc3 → L6 out. Through vias drawn over the full height (grey) with black dots on the two layers they join. Hatched P2 = option M3 (pair rotated by half a coil pitch, 15° for Q = 12) | D02 p.1 EV-01 (complementary spirals, vias); D14 p.4 EV-40 (outer → inner, via, inner → outer); series layers per D11 p.4; through-via-only constraint from the repository drill report (EV-R2) | path logic `inferred`; via arrangement `assumption` |
| C — connection | U → A1 → A2 → A3 → A4 → N, same for V/B and W/C (series coils, star) | `topology_analysis.md` §3.4 | `assumption` (star default) |
| D — polarity example | 12/10 pattern "AabBCcaABbcC": uppercase = positive coil (CW), lowercase = reversed (CCW); reversal realised by entering the coil at its other outer terminal | D08 p.36 Fig. 3.7 (reproduced by `checks/kw.py`); entry-terminal polarity as in Xcoil v3 `buildSector` | pattern `verified (reproduced)` |

Notes:
- For 12/16 no coil is reversed; panel D is included only to show how CW/CCW polarity appears in combinations that need it
  (12/10, 12/14, 18/16).
- The A–C–B order around the stator follows the 60° phase-belt convention of `checks/kw.py`; swapping the B and C labels
  corresponds to the opposite rotation direction (`inferred`).
- Option M3 (hatched pair) is drawn as an option only; for 12/16 a half-pitch rotation equals 120° el. and merely permutes
  phases between pairs (k_w unchanged), while for 12/10 and 12/14 it lowers k_w11/k_w13 (`topology_analysis.md` §4.2).

## What the computed geometry (Phase 2, Python geometry engine) will add

1. True spiral paths per layer (turn-by-turn, side offsets d_t, inner end-turns moved outward when the sides converge —
   EQ-02/EQ-03), with selectable side style (radial / parallel), end style (arc / straight / stadium) and fillets.
2. Exact radii from user inputs (r_i, r_o, w, s, coil gap), the magnet footprint (EQ-04) and the outline (bore, polygon,
   mounting holes).
3. Via placement: centre vias per series pair inside each coil eye, transfer vias at the rim, pad/clearance checks on all
   layers a through via passes; multi-via transitions (EQ-11).
4. Phase rings, ring levels, line terminals, neutral, and their resistance (Xcoil v3 `chainCoils`/interconnect logic as a
   reference).
5. Layer stack z-positions from the stack-up (custom mode), per-layer field evaluation and per-pair EMF (EQ-05–EQ-07).
6. DRC results (trace/trace, trace/via, pad/pad clearances) and KiCad export (tracks, arcs, vias, zones) through the chosen
   plugin route (Agent 3/6).
7. Computed Ke, R, L (estimate), losses and thermal estimate for the drawn copper, each with its EQ status label.
