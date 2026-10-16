Prepared by: Agent 5 (Research & Evidence Specialist), model: claude-opus-5-5. Unit U-S8, 2026-10-16.

# D09 concentric coil: turn count and geometry read from the paper's figures

This page reports what D09's own figures show about the concentric coil (gap G2, F-OR07). D09 is Tokgöz, Çakal,
Keysan, IET Electr. Power Appl. 2020, file
`/mnt/user-data/uploads/Desktop/Fantastic Creature/FC-Smart_Actuator/papers/EPA-2020-0622-FINAL.pdf`
(sha256 `727dbe63…a02ff1f`, 10 pages, read-only). Phase 1 register row D09 names it.

Every figure reading is `inferred`. Only values printed in D09 are `verified`. Each number below names its figure,
the pixel measurement and the status. Evidence rows are EV-127 to EV-133 in `evidence_register_phase3.md`.

## Result in one paragraph

Fig. 1a (the design drawing) shows **7 turns per coil** on the top layer. The count is the same on every side that
can be read: the inner side of all 12 coils and both lateral sides of all 12 coils (36 of 36 sides). The scale comes
from the turn pitch, which is the printed trace width plus clearance (0.8 + 0.2 = 1.0 mm, Table 2 p.3, `verified`).
The drawing then gives the outermost turn's centre lines at r ≈ 24.9 to 25.3 mm (inner side) and r ≈ 44.9 to
45.5 mm (outer side). The lateral sides are parallel offsets of the 30° sector edges, not radial lines. The Fig. 11a
photo shows 6 evenly spaced lines on the inner side of coil C2, which is 6 or 7 traces. So the photo agrees with 7
within ±1. Two things do not close. First, 7 measured turns × 8 coil-layers is 2.80 to 2.85 m against D09's 3244 mm
phase length (−12 % to −14 %). Second, the photo puts the inner turns about 1.5 mm further from the hole than the
drawing does.

## How to rerun

From `docs/phase3/evidence/d09_coil_geometry/`, with poppler `pdfimages` and system `python3` (numpy, scipy,
Pillow):

```
python3 -I measure_d09_figures.py "<D09 pdf>" <scratch dir>     # Fig. 1a counts, pitch, scale; Fig. 11a hole circle
python3 -I turn_loops_vs_table1.py                              # turn perimeters and areas vs D09 Table 1
python3 -I photo_profile_fig11a.py <scratch dir>/p7-000.png     # Fig. 11a coil C2 line profile
```

The outputs are in `d09_coil_geometry/logs/`. The scripts read the embedded images at their native resolution
(`pdfimages`, no resampling). Fig. 1 is page 2 image 0 (1927 × 1376 px, 300 ppi). Fig. 11 is page 7 image 0
(1952 × 1416 px, 300 ppi). Each panel `a` is the crop x 0–700, y 0–700 px.

## Method

1. The script finds the inner circle of Fig. 1a. It fits a circle to the centre of the black outline on 720 rays.
   Result: centre (299.10, 299.39) px, r = 128.34 px, residual rms 0.32 px.
2. It finds the coil windows as enclosed white regions of 500 to 3000 px. It finds 12. Their angles are 12.5° + k·30°.
   The spacing is 29.97° to 30.04°. The centroid radius is 184.37 to 184.68 px and the area is 756 to 767 px.
3. For each coil side it averages the green channel across the side. Red and blue copper are dark in green. Gaps and
   windows are bright. Lateral sides are averaged over the window's radial span, under two models: a line parallel
   to the sector edge, and a constant angle (radial). Inner and outer sides are averaged over ±5 px across the
   bisector, as a chord and as an arc.
4. It counts gap peaks of prominence ≥ 15 (green levels, 0 to 255) and the red bands between them.
5. It takes the median gap-to-gap spacing as the drawing's pitch. That is 1.0 mm per D09 Table 2.

## Turn count

| Coil side (Fig. 1a, top layer) | Sides read | Red bands found | Status |
|---|---|---|---|
| Inner side, hole to window, chord and arc models | 12 | 7 on all 12 | inferred |
| Lateral sides, parallel model | 24 | 7 on all 24 | inferred |
| Lateral sides, radial model | 24 | 3 to 9, no common value | inferred (model rejected) |
| Outer side, window to copper edge | 12 | 8 to 12 (7 turns + rim traces) | inferred |

The outer side holds more bands than the coil has turns. A visual check on the coil at 102.5° (polar unwrap,
3× zoom) shows 7 turn corners stacked along each sector edge. Above the outermost corner, 2 more bands cross the
sector edge into the next coil. These are circumferential connection traces along the rim, not turns. The rim bands
reach r = 252.09 px median (p10 241.34, p90 252.84 px), which is 48.48 mm at the pitch scale.

Example gap peaks (coil at 12.5°, from `logs/measure_d09_figures.log`):

```
peaks 12.5 cw parallel: [0.1, 5.9, 11.0, 16.2, 21.3, 26.6, 31.8] window edge 37.2
peaks 12.5 inner chord: [132.3, 137.5, 142.6, 147.9, 153.3, 158.5]
```

The first lateral peak (0.1 px) is the gap between two coils. Six turn gaps and the window edge bound 7 bands. The
inner side has six turn gaps between the hole outline (128.3 px) and the window edge (163.6 px), so 7 bands.

The figure shows only the top layer (red). The bottom layer (blue) is hidden under it. Its turn count cannot be read.
That both layers have 7 turns is an `assumption`. D09 Table 2 gives 2 layers, and Phase 1 EV-62 gives 8 coil-layers
per phase.

## Scale

| Quantity | Value | Method | Status |
|---|---|---|---|
| Trace pitch in D09 | 1.0 mm | Table 2 p.3: trace width 0.8 mm, clearance 0.2 mm | verified |
| Pitch in Fig. 1a | 5.200 px median | 289 gap-to-gap spacings, 3–8 px, best model per side; mean 5.292, sd 0.267, p5 5.10, p95 5.70 px | inferred |
| Drawing scale | 5.200 px/mm | 5.200 px / 1.0 mm | inferred |
| Inner circle diameter at that scale | 49.36 mm | 2 × 128.34 px / 5.200 | inferred |
| Alternative scale | 5.134 px/mm | inner circle = 50 mm (Table 2 "inner diameter") | inferred |

The two scales differ by 1.3 %. So the drawn inner circle is the printed 50 mm within the reading error. The
uncertainty of each radius below is the spread between the two scales. The pitch spread (p5 to p95) covers the
coil-to-coil gaps, which are wider (5.8 to 5.9 px) than the turn gaps (5.0 to 5.4 px).

## Turn geometry

Band centres are the midpoints between gap peaks (`turn_loops_vs_table1.py`, coil at 12.5° and 42.5°). Radii are from
the inner-circle centre. The range is pitch scale to hole scale.

| Quantity | Pixels | mm | Status |
|---|---|---|---|
| Outermost turn, inner-side centre line | 129.70 | 24.94 to 25.26 | inferred |
| Outermost turn, outer-side centre line | 233.60 | 44.92 to 45.50 | inferred |
| Innermost turn, inner-side centre line | 161.10 | 30.98 to 31.38 | inferred |
| Innermost turn, outer-side centre line | 202.50 | 38.94 to 39.45 | inferred |
| Outermost turn, lateral offset from sector edge | 2.95 | 0.57 | inferred |
| Innermost turn, lateral offset from sector edge | 34.50 | 6.63 to 6.72 | inferred |
| Window, radial span on the bisector | 163.6–164.2 to 199.4–200.1 | 31.5 to 38.5 (pitch scale) | inferred |
| Coils per layer | 12 windows | 30.00° ± 0.04° apart | inferred |

The lateral sides are parallel to the sector edge. The parallel model finds 7 bands on all 24 sides. On the coils at 12.5° and 42.5°
the turn gaps are 5.1 to 5.3 px apart along the whole side. The radial model finds 3 to 9 bands. Chord and arc give the same counts on the inner and
outer sides, so this reading cannot tell them apart.

The drawn innermost trace touches the inner circle: its centre line is 1.36 px (0.26 mm) outside the circle, less
than half the 0.8 mm trace width. So the drawn circle is probably the design boundary, not a cut board edge
(`inferred`).

## Check against D09 Table 1

D09 Table 1 p.3 prints, for the concentric phase, a trace length of 3244 mm and a covered area of 171 mm² for "the
loop in the middle of the number of turns" (both `verified`). `turn_loops_vs_table1.py` builds the 7 measured centre
lines and sums them.

```
pitch scale, chord sides: sum 350.5 mm per coil-layer; x 8 coil-layers = 2804 mm (Table 1: 3244 mm, -13.6%)
         middle (4th of 7) 149.5 mm^2 (Table 1: 171 mm^2, -12.6%)
hole scale, arc sides:    sum 356.0 mm per coil-layer; x 8 coil-layers = 2848 mm (Table 1: 3244 mm, -12.2%)
         middle (4th of 7) 158.7 mm^2 (Table 1: 171 mm^2, -7.2%)
```

The turns explain 2804 to 2848 mm. That leaves 396 to 440 mm unexplained. The rim connection traces and the
bottom-layer leads from each via are candidates, but this unit did not measure them (`unresolved`). The mid-turn
area is 7 % to 13 % below 171 mm². If D09 measured the area to the outer edge of the trace, the area would grow by
about perimeter × 0.4 mm ≈ 20 mm² (to about 170 to 179 mm²). That is a possible reading of Table 1, not a finding
(`assumption`).

## Fig. 11a photo

The photo shows 12 coil labels: A8, C2, B2, A2, C4, B4, A4, C6, B6, A6, C8 and B8 (read by eye, `inferred`).

| Quantity | Value | Method | Status |
|---|---|---|---|
| Hole edge circle | centre (307.25, 309.66) px, r 132.84 px, residual rms 0.79 px | fit to the edge of the white hole region | inferred |
| Hole diameter by direction | 263.9 (0°), 264.4 (45°), 266.4 (135°), 267.1 (90°) px | mean of edge radii within ±3° | inferred |
| Coil C2 inner side, bright lines | 6, at r 145.0, 150.3, 155.7, 161.0, 166.2, 171.5 px | luminance averaged over ±4 px across the bisector at 291.2° | inferred |
| Line spacing | 5.2 to 5.4 px | differences of the above | inferred |
| Photo scale if the hole is 50 mm | 5.31 px/mm, so the line spacing is 1.00 mm | 2 × 132.84 / 50 | inferred |

The hole is round to 1.2 % (263.9 to 267.1 px), so the perspective is small. The 6 lines match the 1.0 mm pitch.
They are 7 traces if the lines are the gaps, or 6 if they are the trace bodies. The photo alone gives 6 or 7.

The photo and the drawing disagree on position. In the photo the first line is at 145.0 px, which is 27.29 mm at
the photo's hole scale. In the drawing the first inner gap is at 132.3 px, which is 25.77 mm at the drawing's hole
scale. The last lines differ by the same amount (171.5 px = 32.27 mm against 158.5 px = 30.87 mm). So the inner
side of the built coil sits about 1.4 to 1.5 mm further from the hole than in Fig. 1a. This unit did not measure the
photo's outer side. The C2 window centre (380, 122) px was picked by eye.

## What this changes for F-OR07

- The turn count 7 per coil-layer now has a direct figure reading (36 of 36 sides) instead of only the Table 1
  consistency argument. It agrees with the engineering plan's result that every Table 1 match has N = 7
  (`docs/phase3/engineering/engineering_verification_plan.md` §1).
- The drawing's outermost centre lines (24.9 to 25.3 mm and 44.9 to 45.5 mm) are inside variant A's 25.2 and
  47.6 mm. The outer radius differs by 2.1 to 2.7 mm.
- The side construction in the drawing is parallel offsets of the sector edge, with 7 turns. This is a figure
  reading. Whether it equals the product's "parallel" side style is for Agent 3 to decide.
- The photo's outward shift and the 12 % to 14 % length shortfall leave the exact radii `unresolved`.
