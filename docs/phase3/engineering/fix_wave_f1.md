Prepared by: Agent 2 (Motor Design Expert), model: claude-opus-5-5. Unit U-E17, 2026-10-17, worktree U-E17 from main e68d5ff.

# Fix wave F1 rulings: EQ-16 board area, the EC-05 values of REQ-T-08 (b), and the EQ-17 cooling area of a stack

This is a reference for Agent 3 and Agent 4, and a ruling for Fable (D-055f). Each section gives the ruling, the
references, the fix and a test specification with inputs, expected values, tolerances and the defect each test
catches. Every number below comes from one of three scripts in `docs/phase3/engineering/checks/`. Run them from the
repository root:

```
PYTHONPATH=src python3 docs/phase3/engineering/checks/f1_board_area.py
PYTHONPATH=src python3 docs/phase3/engineering/checks/f1_ec05_cases.py
PYTHONPATH=src:. python3 docs/phase3/engineering/checks/f1_thermal_stack.py
```

The expected values in the scripts come from closed forms, the registry text and Xcoil's source. The scripts import
embodic only to show what the current code returns. No engine output is used as an expected value.

| Item | Ruling | Status |
|---|---|---|
| A, DEF-M7b-01 | EQ-16 and EQ-17 take the exact area of the outline loops (Green's theorem per line and arc), not the area of their 0.5 mm chords. | verified |
| B, REQ-T-08 (b) | The three values are the Phase 1 values of `edge_zone_d09.js` on an idealised segment set. UT-PHY-21 pins the EC-05 kernel on that set, with values recomputed here from the registry formula: 5.328140 %, 4.208834 %, 5.788521 %. The acceptance text is reworded. | verified (values), inferred (cause of the layout-level difference) |
| C, EQ-17 stack | The cooling area of a stack is its two outer faces, 2 A_1 with A_1 the face area of one board, and P is the loss of all boards. Xcoil is right, embodic is wrong. | inferred (rests on one assumption, stated in C.2) |

## A. DEF-M7b-01: EQ-16 takes the exact outline area

### A.1 Ruling

`board_area_mm2` returns the exact area enclosed by the outline primitives. The board loop counts positive. Each
cutout loop and each round hole is subtracted. This is the area EQ-16 (laminate volume `A_board t_board`) and EQ-17
(cooling area) use. Status: verified. Xcoil computes the same area in closed form (read in the source), and
`f1_board_area.py` reproduces Xcoil's `boardArea` from the loop primitives to within 6.2e-16 relative.

Reasons:

- The laminate is the board as cut. Its edge is the outline that embodic exports. The DXF writer emits each outline
  arc as an ARC or CIRCLE entity (`src/embodic/io/dxf_writer.py` l.73-96, called from `_outline` at l.115-120), and
  the SVG writer emits SVG arcs (`src/embodic/io/svg_writer.py` l.101). The chords are a drawing approximation, so
  they are not the board.
- Xcoil, the reference implementation of EQ-16 (`golden_functions: massThermal`), uses the closed-form area
  (`/home/claude/serpentine/src/engine.js` l.1094-1098 `outlineArea`, l.1110 bore area, l.1144-1145 board area
  minus bore minus holes). The golden regression can only pass with the exact area.
- The chord error has no fixed sign. Chords inscribed in the board arc lose area, and chords inscribed in a circular
  bore lose bore area, which adds board area. Case C3 below is 8.1e-6 high, the three golden layouts are 5.6e-6 to
  7.5e-6 low. A test can therefore not bound the chord error by a one-sided band.

The engineering effect is small. The largest chord error measured here is 1.73e-5 relative (case C4), and EQ-16's
tolerance is ±10 % against a weighed board (registry EQ-16 `tolerance`). The fix matters for the golden regression
and for trust in the test, not for the mass a user reads.

### A.2 The number, explained

`_loop_area_mm2` (`src/embodic/physics/analyse.py` l.154-157) applies the shoelace formula to the chord end points of
`discretise(p, 0.5)`. Each arc of radius r is split into n chords by `piece_count` (`src/embodic/geometry/discretise.py`
l.57-64). Each chord of angle φ = |sweep| / n cuts off a circular segment of area r² (φ − sin φ) / 2. The segment
area is the sector area r² φ / 2 minus the triangle area r² sin φ / 2. The page "Circular segment"
(https://en.wikipedia.org/wiki/Circular_segment, read 2026-10-17) states this rule in words. The formula images did
not survive the fetch, so the two terms are written here from that rule. The script predicts the deficit from this
sum and compares it with the measured deficit:

| Layout (outline) | Xcoil `boardArea` (mm²) | exact loop area − Xcoil (rel) | chord area − Xcoil (rel) | exact − chords (mm²) | predicted segment sum (mm²) |
|---|---|---|---|---|---|
| sector-default (circle r 57.84, bore r 18.7, 8 × 3.4 holes) | 9338.872994612557 | 3.9e-16 | −5.6353e-6 | 0.052627076 | 0.052627076 |
| serpentine-default (circle r 55.92, bore r 17, 8 × 3.4) | 8843.35209863596 | 6.2e-16 | −6.7577e-6 | 0.059760394 | 0.059760394 |
| wave-turns-2 (circle r 55.530, bore r 15.341, 8 × 3.4) | 8875.335981185855 | 4.1e-16 | −7.5449e-6 | 0.066963954 | 0.066963954 |

The measured deficit equals the predicted segment sum to 1e-9 mm² on all three layouts, so the chord rule fully
explains the 5.6e-6 to 7.5e-6 of the strict xfail (`tests/golden/m2_physics/test_gr_f11_mass_thermal_current.py`
l.107-111). Status: verified (reproduced). The laminate mass inherits the same relative error because
`mass_g` multiplies the area by the board thickness (`src/embodic/physics/estimates.py` l.55).

### A.3 Fix

Replace `_loop_area_mm2` with an exact signed area per primitive, from Green's theorem A = ½ ∮ (x dy − y dx):

- A `Line` adds (x1 y2 − x2 y1) / 2.
- An `Arc` adds (x1 y2 − x2 y1) / 2 + r² (s − sin s) / 2. Here (x1, y1) and (x2, y2) are `start_point()` and
  `end_point()`, and s is the signed `sweep_rad`. A clockwise arc (s < 0) gives a negative segment term, which is
  correct for a clockwise loop.

The loop area is the absolute value of the sum. `board_area_mm2` stays |outer| − Σ |cutout| − Σ π d² / 4. The
arc term is the chord term plus the signed segment, so it equals the Green integral of the arc exactly. The script's
`green_loop` is a 15-line reference implementation of this rule.

This rule covers every outline the generators emit. `build_outline` (`src/embodic/geometry/outline.py` l.11-33)
emits a circle as two half arcs, a polygon as straight lines, and a bore of either kind as one cutout loop. Screw
holes are round `Hole` records (`src/embodic/geometry/layout.py` l.65-71). `BoardOutline` has no slot type
(l.75-80), so there are no slots to handle. Corner radii are not built yet (`outline.py` l.29). When they are built
as arcs, the same rule covers them. The Xcoil-mapped test layouts already contain a full-circle arc (sweep 2π), and
rounded Xcoil polygons contain corner arcs. Case C5 covers both.

The precondition is unchanged from today's code. Each loop must be chained, with the end of each primitive at the
start of the next. A reversed primitive breaks both the old and the new formula.

Do not compute the area from `OutlineSpec` parameters. The loops are what the board is cut along. A parameter formula
would also disagree with the loops today, because `PolygonOutline.corner_radius_mm` is ignored by `build_outline`.
That gap is a separate observation (see Follow-ups).

### A.4 Test specification

| Id | Test | Inputs | Expected | Tolerance and reason | Defect caught |
|---|---|---|---|---|---|
| T-A1 | Remove the strict xfail of `test_laminate_mass_of_the_mapped_layout_matches_xcoil_mass_thermal` (l.105-118). | The three mapped layouts, as today. | Xcoil `massLaminate` in `tests/golden/data/mass_thermal/mass-thermal-<tag>.json`: 27.287553101421075, 25.563329279667865, 25.964418691799764 g. | INTEGRATED, rel 1e-9, unchanged. The exact area matches Xcoil's to 6.2e-16. The copper volume term already passes at 1e-9 in `test_copper_mass_of_the_mapped_layout_matches_xcoil_mass_thermal`. | Chord area (5.6e-6 to 7.5e-6 low, about 5600× the tolerance). |
| T-A2 | New golden test in the same file: `board_area_mm2(layout_from_xcoil(raw))` against Xcoil `boardArea`, for the three tags. | `_raw(f"layout-{tag}")`. | 9338.872994612557, 8843.35209863596, 8875.335981185855 mm². | KERNEL, rel 1e-12. The measured difference is at most 6.2e-16, so the margin is 1600×. | Chord area. A bore or the holes left out (these change the area by 10 % or more). |
| T-A3 | Unit test of the area on `build_outline` loops (`tests/unit/physics/`). | C1: `CircleOutline(radius_mm=57.84)`, no bore. C2: `PolygonOutline(sides=12, across_flats_mm=93.0)`. C3: C2 with bore `CircleOutline(radius_mm=12.5)` and `ScrewPattern(size="M3", fit=NORMAL, count=6, pitch_radius_mm=42.0, hole_diameter_mm=3.4)`. C4: `CircleOutline(radius_mm=50.0)` with bore `PolygonOutline(sides=6, across_flats_mm=20.0, rotation_rad=0.3)`. | C1 π 57.84² = 10510.09015179737. C2 12 · 46.5² · tan(π/12) = 6952.477696010341. C3 12 · 46.5² · tan(π/12) − π 12.5² − 6 π 3.4²/4 = 6407.128627273689. C4 π 50² − 6 · 10² · tan(π/6) = 7507.571472460708 mm². | rel 1e-12. The formula and the closed form differ by rounding only: measured at most 1.4e-16. | Chord area (C1 −1.24e-5, C3 +8.1e-6, C4 −1.73e-5). A dropped segment term. The polygon circumradius taken as across-flats / 2 (C2). Bore or holes not subtracted (C3, C4). |
| T-A4 | Rounded polygon from Xcoil, plus orientation. Add a golden case that dumps `outlinePrims("polygon", 8, 50, 0, 5)` and `outlineArea("polygon", 8, 50, 5)` (both exported, `engine.js` l.2972) through `tools/golden/dump_xcoil.mjs`. Map the records with `prim_from_record`. | The 16 records (8 lines, 8 corner arcs). The same loop reversed (each arc's start moved to its end and the sweep negated, the order reversed). | 8279.968351327027 mm². Equals n a² tan(π/n) − n r_c² (tan(π/n) − π/n) with n 8, a 50, r_c 5 (`engine.js` l.1097). The reversed loop gives the same area. | rel 1e-12. Measured 2.2e-16. | Chord area on small corner arcs (−2.4e-6). A missing `abs` on a clockwise loop. A segment term of the wrong sign. |

## B. REQ-T-08 (b): where 5.3, 4.2 and 5.8 % come from, and what UT-PHY-21 pins

### B.1 Where the three values came from

The values are the output of the Phase 1 script `docs/phase1/engineering/checks/edge_zone_d09.js` (Agent 2,
DEF-18). Lines 34-37 define the three cases. Lines 45-56 apply the adopted EC-05 rule. Running it today
(`node docs/phase1/engineering/checks/edge_zone_d09.js`) prints:

```
ADOPTED rule | default 12/16 (blocks 20x6x2, magnets r 18-38, coil copper 18-38): e_edge = 5.33 %
ADOPTED rule | O1 D08 (magnets r 15.4-43.4, coil 12.5-44, G 1.4 assumed): e_edge = 4.21 %
ADOPTED rule | O2 D09 (magnets r 25-46, coil centre-lines 25.2-47.6, N = 8): e_edge = 5.79 %
```

Agent 4 reproduced them in Phase 1 with an independent implementation (5.33, 4.21 and 5.79 %,
`docs/phase1/verification/defect_list.md` l.94). They then travelled through four documents:

- the registry EC-05 field `consequences` with 0.053, 0.042 and 0.058 (`resources/evidence/equations.v1.json` and
  `docs/phase2/engineering/equation_registry.json`, l.603);
- the Phase 1 test plan UT-PHY-21 (`docs/phase1/architecture/test_plan_draft.md` l.100), which names "Agent 2's
  `checks/edge_zone_d09.js`";
- the Phase 2 test plan, "Phase 1 used 4.2 % and 5.8 %; UT-PHY-21 pins those values within 0.1 pp"
  (`docs/phase2/architecture/test_plan.md` l.226-229);
- the REQ-T-08 acceptance "EC-05 values within 0.1 pp of Agent 2" (`docs/phase2/architecture/requirements.md` l.217).

No Phase 2 or Phase 3 document carried the case inputs forward, so U-M7d could not find them. Status: verified
(the script, the registry and the four documents were read, and the script was run).

### B.2 Why analyse() gives other numbers

The Phase 1 values and analyse() apply the same metric to different segment sets.

- Phase 1 used one idealised radial line over the coil annulus clipped to the magnet span, evaluated at z = G. The
  script says so at l.47: "here: uniform radial coverage of the coil annulus within the magnet span". Every weight
  w = |B_z,1 r dr| from the inner to the outer magnet end counts once.
- analyse() sums the weights of the real EMF-producing chords of the generated layout at each copper layer's z
  (`src/embodic/physics/emf.py` l.151-167, `edge_leakage_fraction` l.209). U-M7d reports 1.738 % (D08) and 2.566 %
  (12c16p). The Phase 2 oracle spec reports D08 1.74 % and D09 A 2.59 % (`docs/phase2/engineering/oracle_tests_spec.md`
  l.324-325, question Q1).

The copper z does not explain the factor of about 0.4. Moving the field point from z = G to the magnet face changes
the Phase 1 values by +0.050, +0.011 and −0.003 pp (`f1_ec05_cases.py`, defect table below). The remaining difference
is the segment set. In a generated coil only part of the copper reaches the ends of the annulus. Inner turns stop
short of the magnet ends, so less weight sits inside the decay length c_e G. Status of this cause: inferred. This
unit did not compute it on a layout. Q1 of the oracle spec stays open for the OR-01 and OR-07 bands.

Neither number is wrong. The registry text defines the metric over "EMF-producing segments inside the magnet span",
which is what analyse() does. The Phase 1 values are that metric on a stated idealised segment set. They are the
right expected values for a kernel test. They are not the expected values for a generated layout.

### B.3 Ruling

UT-PHY-21 stays a kernel test on the Phase 1 segment set. The expected values are recomputed here from the registry
formula alone. The cap behaviour is tested on the Phase 1 short-magnet cases. The value of `edge_leakage_fraction` on
generated layouts is reported and labelled, not pinned, until an independent layout-level derivation exists.

Proposed REQ-T-08 acceptance, replacing "EC-05 values within 0.1 pp of Agent 2":

> UT-PHY-21: the EC-05 kernel (`integrate_path` and `edge_leakage_fraction`) returns e_edge within 0.1 pp of
> 5.328140 %, 4.208834 % and 5.788521 % on the three cases of `docs/phase3/engineering/fix_wave_f1.md` §B.4, and
> within 0.005 pp of the same values at 0.1 mm chords. A case above 0.10 caps the badge at `unresolved`.

The registry `consequences` field needs a label that says which segment set it describes. A proposed text is in
Follow-ups. The registry is outside this unit's write scope.

### B.4 Cases and expected values

The formulas are read from the registry (`resources/evidence/equations.v1.json`):

- EQ-05, n = 1: K_1 = (4 B_r / π) sin(π α_p / 2), u = p / r, B_z,1 = K_1 cosh(u (G − z)) / (cosh(u G) + μ_r coth(u l_m) sinh(u G)).
- EQ-04 for block magnets: α_p(r) = 2 p asin(w_PM / (2 r)) / π.
- EC-05: e_edge = Σ w D_e exp(−d / (c_e G)) / Σ w, w = |B_z,1(r, z) r dr|, d = min(r − r_A, r_B − r), D_e 0.47 and
  c_e 0.9 (read from the registry parameters).

The integral runs over r from max(r_A, r_coil,in) to min(r_B, r_coil,out) at z = G. `scipy.integrate.quad` gives the
reference value. The 4000-point midpoint sum of Phase 1 agrees within 6e-6 pp. Inputs come from `edge_zone_d09.js`
l.34-37:

| Case | Rotor (`RotorSpec`, rotor type DOUBLE) | G = z (mm) | Radial line (mm) | e_edge, registry formula | Phase 1 printed |
|---|---|---|---|---|---|
| default_12_16 | 16 poles, `BlockMagnet(width_mm=6, length_mm=20, r_center_mm=28, thickness_mm=2)`, B_r 1.315 T, μ_r 1.05 | 1.31 | 18 to 38 | 5.328140 % | 5.33 % |
| O1_D08 | 10 poles, `ArcMagnet(pole_arc_ratio=0.72, r_inner_mm=15.4, r_outer_mm=43.4, thickness_mm=5)`, B_r 1.38 T, μ_r 1.05 | 1.4 | 12.5 to 44 | 4.208834 % | 4.21 % |
| O2_D09_N8 | 16 poles, `ArcMagnet(pole_arc_ratio=0.8, r_inner_mm=25, r_outer_mm=46, thickness_mm=2)`, B_r 1.33 T, μ_r 1.05 | 1.5 | 25.2 to 47.6 | 5.788521 % | 5.79 % |
| cap, 10 mm magnet | 16 poles, `ArcMagnet(0.8, 30.5, 40.5, 2)`, B_r 1.33 T, μ_r 1.05 | 1.5 | 30.5 to 40.5 | 12.373846 %, capped | 12.37 % |
| cap, 12 mm magnet | as above, magnet 29.5 to 41.5 | 1.5 | 29.5 to 41.5 | 10.445833 %, capped | 10.45 % |
| no cap, 15 mm magnet | as above, magnet 28 to 43 | 1.5 | 28 to 43 | 8.420015 %, not capped | 8.42 % |

The B_r values cancel in the ratio. The air gap and back-iron fields of `RotorSpec` do not enter `field_table`,
which takes G and z directly. Use `air_gap_mm=1.0` and `back_iron_thickness_mm=5.0`; the cross-check below used
them. The G and B_r values for O1 rest on the D08 gap reading (registry EC-05 `independence`, gap G10). This is a
property of the oracle inputs, not of these kernel cases.

### B.5 Test specification (UT-PHY-21, `tests/unit/physics/`)

For each of the first three cases:

1. Build the rotor from the table and `table = field_table(rotor, G, G, (1,))`.
2. Build one `Line` from (r_lo, 0) to (r_hi, 0) with any width.
3. Compute `field = integrate_path([line], table, p, 0.5, c_e * G)` and
   `e = edge_leakage_fraction([field], D_e)`, with D_e and c_e read from `load_registry()`.
4. Assert |e − expected| ≤ 0.001 (0.1 pp).
5. Repeat with `max_segment_mm=0.1` and assert |e − expected| ≤ 0.00005 (0.005 pp).

For the three magnet-length cases, run the same steps and pass e to `evaluate_validity(check, "EQ-05", e)`. Assert
`ValidityEffect.CAP` for 10 and 12 mm and `ValidityEffect.LIMITATION` with `one_sided_addon == e` for 15 mm.

Tolerances and their reasons. The kernel's 0.5 mm midpoint chords and its 48-step field table make it read low. The
cross-check measured −0.038, −0.025 and −0.030 pp at 0.5 mm, and −0.0016, −0.0011 and −0.0013 pp at 0.1 mm. The
ratio between the two step sizes is 22 to 24, close to the 25 that a midpoint rule of order h² predicts, so the
difference is the kernel's quadrature, not a formula difference. 0.1 pp is the REQ-T-08 figure and holds the 0.5 mm
error with a margin of 2.6×. The 10 mm cap case reads −0.070 pp at 0.5 mm, which is still inside 0.1 pp. 0.005 pp at
0.1 mm holds the measured 0.0017 pp with a margin of about 3× (0.0028 pp on the 10 mm cap case) and catches two defects that 0.1 pp would miss.

Shift of e_edge under each defect (`f1_ec05_cases.py`, `defect_shifts`), in pp, for default_12_16, O1_D08 and
O2_D09_N8:

| Defect | Shift (pp) | Caught at 0.1 pp | Caught at 0.005 pp (0.1 mm) |
|---|---|---|---|
| decay length G instead of c_e G | +0.601, +0.468, +0.669 | yes | yes |
| d measured to the farther magnet end | −5.327, −4.209, −5.786 | yes | yes |
| weight without r | +0.155, −0.099, −0.138 | 2 of 3 cases | yes |
| α_p frozen at the mean radius (block magnet) | +0.192, 0, 0 | default case | default case |
| field at z = 0 (magnet face) instead of z | +0.050, +0.011, −0.003 | no | default and O1 |

A small error in D_e or c_e can stay inside 0.1 pp. The existing EQT-05-EC test pins both constants at rel 1e-12
(`tests/unit/physics/test_closed_forms_m2e2.py` l.253), and CF-03 (l.217) pins the z plane.

## C. EQ-17 on a stack of boards

### C.1 Ruling

The cooling area of a stack is its two outer faces, 2 A_1. A_1 is the face area of one board after fix A. P is the
total loss of all boards. Xcoil does this: `aCool = 2 * mech.area * 1e-6` with the area of one board
(`engine.js` l.1390), and `dT = losses / (p.hConv * aCool)` with the loss of the whole layout (l.1391, called at
l.2544 with `an.lossTotal`). embodic multiplies the area by the board count (`src/embodic/physics/analyse.py` l.429).
That multiplication is wrong for the stacks embodic builds. Status: inferred, from the two definitions and the gap
computation below, under the assumption in C.2.

EQ-16 is different. Laminate mass adds over boards, so `board_area * len(boards.boards)` at l.420 stays. Xcoil does
the same (`engine.js` l.1382, `mech.area * bt * nBoards`).

### C.2 References and reasoning

- D01 defines the area of the convection term. Eq. 8 is ΔT_conv = P / (h_t A_PCB), "where h_t is the heat transfer
  coefficient in W/m2K and APCB is the surface area of the PCB exposed to the ambient air"
  (`/mnt/user-data/uploads/paper/IET Electric Power Appl - 2019 - Salim - Multiphysics analysis of printed circuit board winding for high‐speed axial flux.pdf`,
  p.4, journal p.808, §4; EV-22).
- D08 eq. 7.2 is R = 1 / (h A), with A "the contact area with the previous layer", the surface between a solid layer
  and the air (D08, `/mnt/user-data/uploads/Desktop/Fantastic Creature/FC-Smart_Actuator/papers/799354017-Pcb-stator-thesis.pdf`,
  PDF p.82, printed p.77, §7.2; EV-11). D08 models one PCB, so it does not settle stacks
  directly.
- embodic stacks the boards of one-board-per-phase at a pitch of board thickness plus `board_gap_mm`
  (`src/embodic/generators/serpentine/generate.py` l.390). The gap defaults to 0.1 mm
  (`src/embodic/model/winding_specs.py` l.173, Xcoil `boardGap: 0.1` at `engine.js` l.54). Every board in the stack
  has the same outline (`generate.py` l.401).
- Per unit area, the 0.1 mm air gap conducts heat much better than a face loses it by convection. With k_air
  0.0275 W/(m K) (D01 Table 3, p.4), R_gap = t / k = 3.64e-3 m² K/W. With h 10 W/(m² K) (D01 p.4) or 30 W/(m² K)
  (embodic and Xcoil default, `engine.js` l.65, unsourced per the registry), 1/h is 27.5 or 9.2 times R_gap. With
  D08's k_air 0.02514 W/(m K) (PDF p.82), the ratios are 25.1 and 8.4 (`f1_thermal_stack.py`). Status: verified
  arithmetic on cited constants.

From these points: the inner faces of a stack are thermally tied to their neighbours. They are not separate paths
to the ambient air. Heat leaves through the two outer faces, which are the surface "exposed to the ambient air" in
D01's sense. Status: inferred. The step from "the gap conducts well" to "the inner faces do not cool" also needs the
gap to carry no airflow to the outside. That is an assumption. No source on flow in a 0.1 mm channel was read.

Limits of the ruling:

- At a 0.5 mm gap (several serpentine fixtures use it, for example
  `tests/golden/data/serpentine/layout-per-phase-3-gap-0p5.json`) the ratio 1/h to R_gap is still 1.7 to 5.5. The
  field allows gaps up to 10 mm (`src/embodic/model/fields.py` l.159). A wide, ventilated gap would add cooling, and
  the stack form then over-estimates ΔT. That error is on the safe side for a first-order warning.
- Neither form counts the rim. For the three-board example the outer rim is 9.9 % of 2 A_1, for one board 3.2 %
  (`f1_thermal_stack.py`, example values). Both are inside the ±30 % tolerance of EQ-17 (registry, `assumption`).

The effect today, measured on the serpentine example as one board per phase (three boards, 0.1 mm gap): analyse()
returns ΔT 3.4320 K for P 5.4631 W, and ΔT h 2 A_1 / P = 0.3333333333333333. The same example as a single board
returns 10.4211 K for 5.5294 W, with a ratio of exactly 1.0. Splitting the winding over three stacked boards cuts the
predicted rise by a factor of three. That cut is an artefact of the area, not physics.

### C.3 Fix

At `analyse.py` l.429, pass the face area of one board:
`d_t = temperature_rise_k(loss_total, board_area, op.convection_h_w_m2k)`. Keep `board_area * len(boards.boards)`
for `mass_g` at l.420. Update the docstring of `temperature_rise_k` (`src/embodic/physics/thermal.py` l.16) to say
"face area of the stack (one board outline)". EQ-17's text needs the same clarification. See Follow-ups.

### C.4 Test specification

| Id | Test | Inputs | Expected | Tolerance and reason | Defect caught |
|---|---|---|---|---|---|
| T-C1 | analyse() on a stack (`tests/golden/m2_physics/` or `tests/unit/physics/`). | `per_phase(example_design())` from `tests/unit/generators/serpentine/support.py`, built with `build_layout`. Preconditions, asserted: 3 boards, `board_gap_mm == 0.1`, `board_area_mm2` equal on all boards. | `temperature_rise_k.value == loss_total_w.value / (h * 2 * board_area_mm2(boards[0]) * 1e-6)` with h = `design.operating.convection_h_w_m2k`. | rel 1e-12. The two sides use the same numbers in a different order, so only rounding differs (measured 0 on the single board). | The n-board cooling area. Today the ratio is exactly 1/3. |
| T-C2 | The same relation on a single board. | `example_design()` (1 board). | As T-C1. | rel 1e-12. | A fix that divides by n, or that special-cases one board. |
| T-C3 | Optional golden against Xcoil. Add a `mass_thermal` case with the params of `tests/golden/data/serpentine/layout-per-phase-3-gap-0p1.json` (`stackMode` perPhase, nBoards 3). | Xcoil `massThermal` output. | Xcoil `massLaminate` (nBoards 3) and `tempRiseEst`, through the kernel route of `test_temperature_rise_kernel_matches_xcoil_mass_thermal` and `test_laminate_mass_kernel_matches_xcoil_on_xcoils_board_area`. | INTEGRATED, rel 1e-9, as the existing tests. | A laminate mass that counts one board of a stack. A kernel that takes n × A. |

T-C1 is the test that catches the defect. T-C3 pins the kernels on a multi-board case, and it passes before and after
the fix because the kernels are already right.

## Follow-ups

1. Registry text (owner Agent 2, write scope for a later unit). EQ-17 variables: A_board "face area of one board; a
   stack cools through its two outer faces"; P_loss "total loss of all boards". EC-05 `consequences`: add
   "Phase 1 idealised segment set: one radial line over the coil annulus within the magnet span at z = G
   (`docs/phase1/engineering/checks/edge_zone_d09.js` l.34-56); not the value on generated layouts".
2. REQ-T-08 acceptance (owner Agent 6). Replace the text as in §B.3.
3. Layout-level EC-05 (owner Agent 4 with Agent 2). An independent derivation of e_edge on one generated layout, from
   its exported chords and the registry formula, would let a test pin the layout values and close Q1 of the oracle
   spec. Status: unresolved.
4. `PolygonOutline.corner_radius_mm` is accepted by the model and ignored by `build_outline` (`outline.py` l.29).
   A user who sets a corner radius gets a sharp polygon in the exports and in the mass. Severity is for Fable to
   rate. I found no DEF row for it in this worktree.
5. Xcoil clamps the corner radius at `apothem * 0.999` in `outlinePrims` (`engine.js` l.1057) and at `apothem` in
   `outlineArea` (l.1096). The two agree below 0.999 a. Do not port the second clamp. With fix A the area follows
   the loop.
