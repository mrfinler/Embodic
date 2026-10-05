Prepared by: Agent 2 — Motor Design Expert — model: claude-opus-5-5

# Spiral-coil generator: algorithm specification v1.0 (Phase 2, 2026-10-04)

This document states the geometry rules of the spiral-coil generator, step by step, for one coil and for the full stator.
It is a specification, not code. `checks/spiral_reference.py` is a reference model of steps G1 to G9. It prints every
number in the two worked examples. The equations it uses are EQ-01, EQ-02, EQ-03, EQ-08, EQ-10 and EQ-25 of
`equation_specification.md`. Status of every rule: `inferred` (derived from D08 geometry and the Xcoil sector code)
unless marked otherwise.

Revision 2026-10-05 (U-E3, D-028 and DEF-M2d-01): G3, G4, G5, the outputs and both worked examples are rewritten. Both
sides of turn t now lie on offset d_t, the pitch advance happens in an outer end-turn jog, and the lead is one arc at
the via radius. `checks/spiral_r2_check.py` prints the flux-linkage ratios and the lead clearance tables.

## Conventions

- Canonical coil: centred on the +x axis, half-angle h = π/Q. The left sector edge is at +h (y > 0), the right edge at −h.
- View from the F.Cu side (layer L1, facing rotor 1); x right, y up, θ counter-clockwise; coil k (shown as k + 1) is
  centred at θ₀ + k·2π/Q (answers_to_agents.md §1.4).
- Positive coil: positive phase current circulates clockwise in this view. Layer X spirals inward clockwise. Layer Y is
  the mirror of X about the coil centre line, traversed outward, so it circulates the same way.
- Radii r_inner and r_outer are copper edges. Centre-line radii are R_o0 = r_outer − w_out/2 and R_i0 = r_inner + w_in/2.

## Inputs

Names follow `docs/phase1/engineering/answers_to_agents.md` §3.2. Example values carry provenance `example` (D-014);
nothing has a hidden default in the new-design flow.

| Name | Unit | Rule |
|---|---|---|
| `coil_count` Q | 1 | balanced per G7; Q ≠ 2p for all phases on one layer |
| `poles` 2p | 1 | even, ≥ 2 |
| `r_inner_mm`, `r_outer_mm` | mm | copper edges of the coil body |
| `trace_width_mm` w, `clearance_mm` s | mm | > 0 |
| `coil_gap_mm` | mm | copper-to-copper gap between neighbouring coils; used value max(gap, s) |
| `turns` N | 1 | 1 to the limit of G3 and G5, or "maximum" |
| `side_style` | none | `parallel` or `radial` |
| `end_style` | none | `arc`, `straight` or `stadium` |
| `corner_radius_mm` | mm | ≥ 0; reduced automatically (G9) |
| `end_width_outer_mm`, `end_width_inner_mm` | mm | ≥ w, or equal to w |
| `first_coil_angle_rad` θ₀ | rad | any |
| `via_pad_mm`, `via_drill_mm` | mm | pad > drill |
| `min_side_length_mm` | mm | default 2w (`assumption`) |
| `bus_width_mm` bw | mm | > 0 |
| layer plan | none | layer pairs, grouped into series groups of parallel pairs; per pair a rotation (0 or π/Q) |

## Steps for one coil

### G1 Derived quantities

w_d = w + s; w_d,out = w_out + s; w_d,in = w_in + s; θ_cp = 2π/Q; side offset d_t = gap/2 + w/2 + t·w_d (parallel
sides); outer end radius R_out,t = R_o0 − t·w_d,out; inner end radius R_in,t = R_i0 + t·w_d,in. The turn pitch is w + s
on the sides and w_end + s on the ends.

### G2 Coil footprint

- Parallel sides: side t lies on the line parallel to the sector edge at perpendicular offset d_t. A point on the right
  line at axial parameter λ is λ(cos h, −sin h) + d(sin h, cos h); at radius R, λ = √(R² − d²). The left line is the
  mirror.
- Radial sides: side t lies on the ray at angle ±(h − δ_t) with δ_t = asin(d_t/R_i0). Because asin is convex, the gap
  between neighbouring rays at R_i0 is at least w_d and grows outward. Radial sides never meet, so a radial coil has no
  triangular turns.
- Arc ends: concentric arcs at R_out,t and R_in,t.
- Straight ends: chords perpendicular to the coil centre line at x = R cos h (Xcoil `outerR`/`innerR` with
  `ends = straight`).
- Stadium ends (`assumption`, interpretation of the reference render, `inferred from image`): each end is a circular arc
  tangent to both side lines of that end. Outer end of turn t (both sides at offset d_t, apex x_a = d_t/sin h on the
  centre line): centre x_c = (R_out,t + x_a sin h)/(1 + sin h), radius ρ = (x_c − x_a) sin h. Inner end (right side d_t,
  left side d_t, revision 2026-10-05 (U-E3)): the mirror of the outer construction about the inner side, tangent to both
  lines d_t with its innermost point at r_end,t. Status `not tested`; no worked example.

### G3 Turn geometry and turn limit (revision 2026-10-05 (U-E3))

Turn t of layer X, in current direction (clockwise in the F.Cu view), is four primitives:

1. Outer end: one arc at R_out,t from J_t to B_t. B_t is on the right line d_t. J_0 = A_0, the start corner on the left
   line d_0. For t ≥ 1, J_t is on the left line d_t−1, at the top of the previous turn's left side. The part of the arc
   from J_t to A_t (left line d_t) is the jog: the pitch advance of one w_d, made at constant radius.
2. Right side: line d_t from B_t down to C_t.
3. Inner end: arc from C_t (right line d_t) to D_t (left line d_t). Trapezoidal turn: the arc lies at R_in,t. Triangular
   turn: the arc lies at the apex-limit radius ρ_t, where the two side lines d_t are w_d apart (|y| = w_d/2):
   x_c = (d_t + (w_d/2) cos h)/sin h, ρ_t = √(x_c² + (w_d/2)²). The turn is trapezoidal when R_in,t ≥ ρ_t. So
   r_end,t = max(R_in,t, ρ_t), and C_t and D_t are always at least w_d apart, which keeps s between the right and
   left side of the same turn (they are not adjacent primitives, so DRC rule 1 does not exempt them).
4. Left side: line d_t from D_t up to J_t+1, at radius R_out,t+1 = R_out,t − w_d,out. For the last turn, up to L at r_v (G5).

Why the jog is at the outer end (`inferred`, checked by `checks/spiral_r2_check.py`). The path enters at the start corner
A_0 on the outer end. A turn that starts there and stops one end pitch below it, on the same left line, closes a full
loop with both sides on d_t. A step at any other corner leaves one side set shifted by one pitch. The v1.0 rule stepped
at the inner end (the inner end ran from d_t to d_t+1), so every left side sat on d_t+1. That is the D-028 defect
(per-coil linkage 0.693 of the loop model, `docs/phase2/fable/investigations_2026-10-05.md` §1.2).

Jog geometry (`inferred`). The jog is the arc from J_t (left line d_t−1) to A_t (left line d_t) at R_out,t. Its radial
length is 0, so it adds no EMF of its own: in an axial-flux machine only the radial component of a conductor links the
rotating field. Its price is the missing top of each left side: from R_out,t+1 to R_out,t the left line d_t carries no
copper, while the loop model of D08 Fig. 3.4 (p.33) has its left side up to R_out,t. Clearances of the jog (all at the
pitch, so the copper gap is exactly s): to the outer arc of turn t−1, R_out,t−1 − R_out,t = w_d,out; the corner J_t+1 to
the outer arc of turn t, w_d,out (J_t+1 lies inside the arc's angle range); the left side d_t to the left side d_t−1,
w_d. These hold when w_out ≥ w, as the inputs require.

Turn t exists when all of these hold (loop rule):

1. The outer arc exists: d_t < R_out,t sin h.
2. The right side is at least `min_side_length` long.
3. The left side reaches the next jog: r_end,t < R_out,t+1.

The v1.0 rule 4 (outer arc above the previous inner end) follows from the nesting: r_end,t ≥ r_end,t−1 + w_d,in and
R_out,t < R_out,t−1. The generator stops at the first turn that fails. Cross-checks (information only, D08 p.38):
eq. 3.24 N_c < ½((R_o0 − R_i0)/w_d + 1); eq. 3.25 N_c1 < R_i0 sin(θ_cs/2)/(w_d(1 − sin(θ_cs/2))) + 1; eq. 3.26
N_c2 < (1/(1 + csc(θ_cs/2)))((R_o0 − R_i0)/w_d − csc(θ_cs/2) − 2N_c1 + 2), with θ_cs = θ_cp. D08's split into
trapezoids and triangles uses its own trapezoid test, so only the total is compared (worked examples).

### G4 Path of layer X (revision 2026-10-05 (U-E3))

Append the terminal stub (G6), then for t = 0 to N − 1 the four primitives of G3, then the lead of G5. Record per turn:
type, d_t, R_out,t, r_end,t, the jog length, the span at mean radius σ_t = θ_cp − 2 asin(d_t/r_mean) (EQ-08 per-turn
pitch factor), and the outer, right, inner and left lengths. The left length of the last turn ends at L.

### G5 Centre via and lead (EQ-25) (revision 2026-10-05 (U-E3))

The centre via sits on the coil centre line, the only locus that layer X and its mirror Y both reach. It lies inside
turn N − 1. The left side of turn N − 1 ends at L, the point of the left line d_N−1 at radius r_v. The lead is one arc
at r_v from L to the via centre V = (r_v, 0); on layer Y the mirror arc leaves V for the right line d_N−1. No lead runs
on the line d_N any more. That line caused DEF-M2d-01: on CF-11 it passed 0.3229 mm from V (r_v sin h − d_N =
7.6729 − 7.35 mm), clearance −0.2271 mm against 0.2 mm.

The via pad and the lead-arc end share V, so each bound below uses m = max(pad, w)/2:

- r_lo = max((d_N−1 + w/2 + s + m)/sin h, r_end,N−1 + w_in/2 + s + m). The first term keeps the via pad and the lead-arc
  end clear of both side lines d_N−1 (the lead arc is not adjacent to the right side, so rule 1 does not exempt it).
- r_hi = R_out,N−1 − w_out/2 − s − m (via and lead arc clear the outer arc of the last turn).
- One centre via (single pair, or all pairs in parallel): the eye fits when r_hi ≥ r_lo; r_v = r_hi. The top of the
  window makes the last left side as long as it can be; the lead arc has no radial length, so r_v changes the EMF only
  through that side.
- k centre vias (k series groups): vias on the centre line from r_hi downward at pitch max(pad, w)/2 + pad/2 + s; the
  eye fits when r_hi − r_lo ≥ (k − 1)·pitch. Group g's last left side ends at its own via radius, and its lead arc meets
  the other vias only at the pitch. Status `not tested` (D-020: series pairs stay `unresolved`).
- If the eye does not fit, reduce N until it fits and report `turn_limit.limiting_reason = "eye"`.
- DRC rule 2 exempts the lead arc from the via it lands on, and the stub from its terminal via. No other exemption is
  needed or proposed: every other lead-to-via and lead-to-turn distance is at least s (worked examples).

### G6 Terminals, layer pairs and the via plan

- Terminal via ring: r_T = r_outer + s + pad/2. The entry terminal of layer X sits at angle
  a_V = min(angle of the start corner, h − asin((max(pad, bw) + s)/(2r_T))), so terminals of neighbouring coils stay
  max(pad, bw) + s apart (Xcoil `sectorCoilX`). A straight stub joins the start corner to the terminal via. Layer Y ends
  at the mirror terminal (angle −a_V).
- Via plan (answers_to_agents.md §3.1, through vias only per D-015, v vias per transition): k series groups, group g with
  n_g parallel pairs. Per coil: k centre vias, k − 1 transfer vias, plus one stitch via at an end group with n > 1.
  Total N_via = Q·v·(2k − 1 + [n₁ > 1] + [n_k > 1]).
- Parallel pairs (one group): all X layers identical, all Y layers identical, one shared centre via, stitch vias at the
  two terminals.
- Series groups (k > 1): the exit of group g is the entry of group g + 1. Group g + 1 starts at the corner where group g
  ended, so its X layer is the layer-X path without its first outer arc, and the two corners alternate. Through vias of
  different groups at the same corner need separate positions (terminal fan: level ℓ at angle a_V − ℓ·2 asin((pad + s)/(2r_T))).
  Status `unresolved`: no worked example; the fan must pass G9 DRC. This is an open question in the report.
- Rotated layer groups: a pair with rotation π/Q places its coils between the coils of the unrotated pairs (Phase 1 M3).
  Coil angles become θ₀ + (k + ½)·2π/Q for that pair. The phase assignment G7 is computed per pair from its own angles.

### G7 Phase assignment from the exact star of slots (EQ-08)

Integer arithmetic only. For coil k: a_k = 12(kp mod Q) in units of 360°/(12Q); belt b = ⌊(a_k + Q)/(2Q)⌋ mod 6
(half-open belts, so a coil on a belt edge always goes to the belt that starts there); b → (phase, sign) by
0: A+, 1: C−, 2: B+, 3: A−, 4: C+, 5: B−. Accept the combination only if the signed angle sets of B and C equal the set
of A shifted by 4Q and 8Q units (exact balance). The feasibility rule Q mod 3 = 0 and (Q/t) mod 3 = 0, t = gcd(Q, p), is
a pre-check only.

### G8 Polarity, chaining and star/delta links outside r_outer

- A positive coil is entered at its CCW-side terminal (+a_V) and circulates clockwise. A negative coil is the same copper
  entered at the CW side (−a_V).
- Coils of one phase are chained in series outside r_outer: radial legs on layer Y from each coil terminal to a ring via,
  ring arcs on layer X at bus level radii r_ring(ℓ) = r_T + max(pad, w)/2 + s + max(bw, pad)/2 + ℓ·(max(bw, pad) + s),
  level ℓ = phase + m·l (Xcoil `buildSector`, `chainCoils`). A ring arc never passes over a ring via of its own level.
- Star or delta connection of the phase ends: Xcoil `buildInterconnect` beyond the outermost bus ring (EQ-23 for its
  resistance). Open phases leave six terminals.

### G9 Fillets, tapers and clearances

- Fillets: nested corners are filleted concentrically. The innermost turn takes the set radius ρ; each turn further out
  adds one pitch. This is valid only when the end pitch equals the side pitch (w_out = w_in = w) or the corner is square;
  otherwise corners stay sharp and width steps are tapered (Xcoil `taperJunctions`). If any fillet does not fit, multiply
  ρ by 0.7 and retry, at most 12 times; report `rho_used`. The inner end of a triangular turn is an arc of chord w_d at ρ_t (G3, revision 2026-10-05 (U-E3)).
- Neighbour coils: the first side offset gap/2 + w/2 gives a copper gap of max(gap, s) along the shared sector edge
  (parallel sides) or at R_i0 (radial sides).
- Rims: r_inner ≥ bore radius + edge clearance; the outermost bus ring + bw/2 + edge clearance ≤ board outline radius.
- Every primitive list goes through the DRC of EQ-30 (no slack, D-006), including clearance between turns of the same
  coil and between the centre vias and every layer.

## Full stator

1. Validate the inputs and the balance (G7).
2. Build the canonical layer-X path (G1 to G5) and its mirror Y.
3. Rotate copies to θ₀ + k·2π/Q (plus π/Q for rotated pairs).
4. Place vias (G5, G6), chain each phase and route the links (G8).
5. Run the DRC (EQ-30) and report the smallest clearance.

## Outputs

| Output | Content |
|---|---|
| primitives per layer | lines and arcs with width and kind (`side`, `endturn`, `lead`, `stub`, `leg`, `ring`, `ic`), net and coil index |
| via list | position, kind (`centre`, `terminal`, `transfer`, `stitch`, `ring`), net, drill, pad, layers joined |
| electrical element list | one element per coil: phase, sign, members {layer, prims} per layer, series group; the format `analyzeElements` consumes |
| `turns_achieved`, `turn_limit` | N built; radial bound, loop-rule count, eye-limited count, `limiting_reason` (`loop`, `eye`, `min_side`, `user`) |
| `turn_table` | per turn: type, d_t, R_out,t, r_end,t (R_in,t or ρ_t), jog length, σ_t, lengths (revision 2026-10-05 (U-E3)) |
| derived geometry | per-coil track length per layer (body, lead, stub), EQ-03 closed form beside it, envelope r_min_cu, r_max_cu, copper area per layer, smallest clearance |

## Worked example 1: default 12/16 (example values, revision 2026-10-05 (U-E3))

Inputs: Q 12, 2p 16, r 18.0 to 38.0 mm, w 0.5, s 0.2, gap 0.2, via pad 0.6, bus width 1.0 mm (Xcoil `viaPad` and
`busWidth`), 34.8 µm copper, 20 °C, one layer pair. Numbers from `.venv/bin/python checks/spiral_reference.py` and
`.venv/bin/python checks/spiral_r2_check.py` (`verified (by computation)` for the rules as written; the rules are `inferred`):

- G1: w_d 0.7 mm; θ_cp 30°; R_o0 37.75 mm; R_i0 18.25 mm; d_0 0.35 mm.
- G7: pattern ACBACBACBACB, t = gcd(12, 8) = 4, balanced exactly, 0 coils on belt edges, k_d1 = 1.0 (k_p1 = sin(120°) =
  0.866).
- G3: loop rule 11 turns (8 trapezoids, 3 triangles). D08 eq. 3.24 bound 14.43; eq. 3.25 bound 10.10 (N_c1 = 10);
  eq. 3.26 bound 1.23 (N_c2 = 1); total 11 = loop rule.
- G5: N = 11 does not fit. N = 10 fits: r_lo 28.5914 (side bound), r_hi 30.7000, r_v 30.7000 mm. Result N = 10,
  `limiting_reason = "eye"`. Three series groups: 10 (eye width 2.1086 mm ≥ 2 × 0.8 mm).
- G3/G4 per-turn table, N = 10 (mm; r_end = R_in,t or ρ_t; left of turn 9 ends at L):

| t | type | d_t | R_out | r_end | jog | outer | right | inner | left |
|---|---|---|---|---|---|---|---|---|---|
| 0 | trapezoid | 0.35 | 37.75 | 18.2500 | 0 | 19.0658 | 19.5017 | 8.8556 | 18.8017 |
| 1 | trapezoid | 1.05 | 37.05 | 18.9500 | 0.7001 | 17.9992 | 18.1142 | 7.8211 | 17.4139 |
| 2 | trapezoid | 1.75 | 36.35 | 19.6500 | 0.7005 | 16.2320 | 16.7359 | 6.7841 | 16.0351 |
| 3 | trapezoid | 2.45 | 35.65 | 20.3500 | 0.7012 | 14.4637 | 15.3637 | 5.7433 | 14.6620 |
| 4 | trapezoid | 3.15 | 34.95 | 21.0500 | 0.7023 | 12.6935 | 13.9948 | 4.6980 | 13.2919 |
| 5 | trapezoid | 3.85 | 34.25 | 21.7500 | 0.7037 | 10.9206 | 12.6264 | 3.6475 | 11.9218 |
| 6 | trapezoid | 4.55 | 33.55 | 22.4500 | 0.7056 | 9.1442 | 11.2560 | 2.5913 | 10.5493 |
| 7 | trapezoid | 5.25 | 32.85 | 23.1500 | 0.7079 | 7.3629 | 9.8809 | 1.5292 | 9.1716 |
| 8 | triangle | 5.95 | 32.15 | 24.2978 | 0.7109 | 5.5756 | 8.0366 | 0.7000 | 7.3240 |
| 9 | triangle | 6.65 | 31.45 | 27.0021 | 0.7145 | 3.7805 | 4.5685 | 0.7000 | 3.8007 |

- Path per coil-layer: outer 117.2380 (jogs 6.3467) + right 130.0788 + inner 43.0702 + left 122.9721 = body 413.3590 mm;
  lead 1.3341 mm; stub 0.7877 mm; total 415.4808 mm. EQ-03 closed form for N = 10: 416.8085 mm (+0.84 % over the body,
  v1.0 +5.16 %).
- Flux linkage (embodic field table and `integrate_path`, example rotor of `tests/unit/model/designs.py`): layer X
  0.003297 V·s/rad; concentric loops with the same radii, first 10: 0.003402, all 11: 0.003406. Ratio 0.969 against
  10 loops: the jog loss is 3.1 % (`verified (by computation)`).
- Lead clearance table (copper edge to edge, mm, rule s 0.2; own coil and both neighbours, both layers, all vias through):

| Lead | Nearest via (not landed on) | Nearest own turn | Nearest neighbour copper |
|---|---|---|---|
| X stub (entry) | 0.5880 (neighbour Y terminal) | 0.2000 (left side 0) | 0.2000 (neighbour right side 0) |
| X lead arc (to centre via) | 9.9030 (own X terminal) | 0.2000 (left side 8) | 6.5000 (neighbour right side 0) |
| Y lead arc (from centre via) | 9.9030 (own Y terminal) | 0.2000 (left side 8, mirrored) | 6.5000 |
| Y stub (exit) | 0.5880 (neighbour X terminal) | 0.2000 (left side 0, mirrored) | 0.2000 |

  Smallest clearance over all non-adjacent copper pairs 0.2000 mm (outer arc 1 to left side 1); smallest trace-to-via
  0.2000 mm (outer arc 0 to its own terminal via). The v1.0 value was −0.2271 mm (DEF-M2d-01).
- G6: r_T 38.5 mm; terminal angle 14.107° (start corner 14.469°). Vias: single pair 12; three parallel pairs 36; three
  series groups 60.
- G8: bus ring radii 39.5, 40.7, 41.9 mm for levels 0 to 2.
- EQ-10: 0.411684 Ω per coil-layer at 20 °C; 4 coils × 2 layers in series = 3.293473 Ω per phase before links.

## Worked example 2: D08 12/10 (revision 2026-10-05 (U-E3))

Inputs: Q 12, 2p 10, centre-lines 12.5 and 44.0 mm (D08 p.55, so copper edges 11.47 and 45.03 mm), w 2.06 mm (Table 4.6
p.57), s 0.8 mm (Table 4.5 p.54), gap 0.8 mm (`inferred`), via pad 0.6 mm (`unresolved`, not in D08), 34.8 µm, 50 °C.

- G1: w_d 2.86 mm; d_0 1.43 mm.
- G7: pattern AabBCcaABbcC = D08 Fig. 3.7 p.36 (`verified (reproduced)`). Six of twelve coils sit exactly on a belt edge,
  so the half-open belt rule decides them; floating-point floors do not.
- G3: loop rule 3 turns (trapezoid, triangle, triangle). Total = D08 Table 4.6 p.57 (3 loops) and eq. 3.24 to 3.26
  (bounds 6.007, 2.526 so N_c1 = 2, 1.059 so N_c2 = 1; D08 counts two trapezoids where this rule counts one).
- G5: N = 3 does not fit: turn 2 has R_out 38.28 and d_2 7.15 mm, so r_lo = (7.15 + 1.03 + 0.8 + 1.03)/sin 15° =
  38.68 > r_hi = 35.42 mm. Inside that 5 mm triangle the side centre lines are 2.17 mm from the centre line at r 36 mm,
  and a 2.06 mm lead needs 2.86 mm. N = 2 fits: r_lo 27.6255, r_hi 38.2800, r_v 38.2800 mm; `limiting_reason = "eye"`.
  v1.0 reached N = 3 only by running the lead on d_3 = 10.01 mm, which at r_v 36.0026 mm lies 0.69 mm past the centre
  line (r_v sin h − d_3 = 9.318 − 10.01): the same defect as DEF-M2d-01, with clearance −0.64 mm (`verified (by
  computation)`, arithmetic on the v1.0 numbers).
- G3/G4 per-turn table, N = 2 (mm; left of turn 1 ends at L):

| t | type | d_t | R_out | r_end | jog | outer | right | inner | left |
|---|---|---|---|---|---|---|---|---|---|
| 0 | trapezoid | 1.43 | 44.00 | 12.5000 | 0 | 20.1778 | 31.5588 | 3.6787 | 28.6972 |
| 1 | triangle | 4.29 | 41.14 | 21.9587 | 2.8675 | 15.8128 | 19.3801 | 2.8620 | 16.5033 |

  Not built: turn 2 (triangle, d_2 7.15, R_out 38.28, ρ_2 33.0 mm).
- Path per coil-layer: body 138.6707 mm (jog 2.8675), lead 5.7226 mm, stub 2.1300 mm, total 146.5234 mm. EQ-03 closed
  form for N = 2: 149.7299 mm.
- Flux linkage (D08 design of `tests/unit/physics/test_oracles.py`, embodic field and integrator): layer X 0.002262
  V·s/rad; concentric loops with the same radii 0.001639, 0.000814, 0.000130 (first 2: 0.002453, all 3: 0.002583).
  Ratio 0.922 against 2 loops (jog loss 7.8 %, larger than CF-11 because w_d is 2.86 mm on sides of 19 to 32 mm) and
  0.874 against D08's 3 loops (`verified (by computation)`). The v1.0 generated coil was 0.00177 (Fable's lever).
- Predicted Ke_LL after the change: 0.02358 × 0.002262/0.00177 = 0.0301 V·s/rad (−2.8 % against 0.031), or 0.0340 ×
  0.874 = 0.0297 (−4.2 %) from Fable's loop-model value. Both are inside the OR-01 band [−8 %, +9.8 %]. Status `inferred`
  until U-M2d-2 runs OR-01. If the back-iron factor of D08 Table 4.8 (1.2 T for 1.38 T) is applied as well, the value
  falls to about 0.026 (−16 %), outside the band; that factor is `unresolved` (`back_iron: unresolved`).
- Lead clearance table (mm, rule s 0.8):

| Lead | Nearest via (not landed on) | Nearest own turn | Nearest neighbour copper |
|---|---|---|---|
| X stub (entry) | 1.6669 (neighbour Y terminal) | 0.8016 (left side 0) | 0.8000 (neighbour right side 0) |
| X lead arc (to centre via) | 7.2059 (own X terminal) | 0.8000 (outer arc 1) | 3.6600 (neighbour right side 0) |
| Y lead arc (from centre via) | 7.2059 (own Y terminal) | 0.8000 (outer arc 1, mirrored) | 3.6600 |
| Y stub (exit) | 1.6669 (neighbour X terminal) | 0.8016 (left side 0, mirrored) | 0.8000 (neighbour outer arc 0) |

  Smallest clearance over all non-adjacent copper pairs 0.8000 mm; smallest trace-to-via 0.8000 mm.
- EQ-10: 0.039394 Ω per coil-layer at 50 °C; 4 coils × 2 layers = 0.315149 Ω per phase before links. D08 prints 0.39 Ω
  from the loop model (Table 4.6 p.57, calculated, not measured), so this is no validation.

## Acceptance checks for the implementation

- Turn counts exactly as above (CF-11: loop 11, eye 10; CF-10: loop 3, eye 2 at pad 0.6 mm), and the concentric
  test mode of EQ-02 (3, 11, 8). Revision 2026-10-05 (U-E3): the CF-10 eye count changes from 3 to 2.
- Lengths within 1e-6 relative of the reference model for the same rules; within ±1 % when fillets are on.
- Pattern strings exactly as CF-09.
- The implementation's DRC (EQ-30) reports no violation for both examples. `checks/spiral_r2_check.py` measures the
  clearances with embodic's DRC distance kernels on the reference geometry (smallest = s in both examples); the
  generator's own DRC run is `not tested` until U-M2d-2.
- Per-coil flux linkage of layer X at least 0.96 (CF-11) and 0.92 (CF-10, N = 2) of the concentric loops with the same
  radii (revision 2026-10-05 (U-E3)).
