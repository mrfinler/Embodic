Prepared by: Agent 2 — Motor Design Expert — model: claude-opus-5-5

# Spiral-coil generator: algorithm specification v1.0 (Phase 2, 2026-10-04)

This document states the geometry rules of the spiral-coil generator, step by step, for one coil and for the full stator.
It is a specification, not code. `checks/spiral_reference.py` is a reference model of steps G1 to G9. It prints every
number in the two worked examples. The equations it uses are EQ-01, EQ-02, EQ-03, EQ-08, EQ-10 and EQ-25 of
`equation_specification.md`. Status of every rule: `inferred` (derived from D08 geometry and the Xcoil sector code)
unless marked otherwise.

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
  left side d_t+1): centre c and radius ρ solve n_R·c − d_t = ρ, n_L·c − d_t+1 = ρ, |c| − ρ = R_in,t. Status
  `not tested`; no worked example.

### G3 Turn limit (loop rule)

Spiral turn t is the path: outer arc at R_out,t from the left line d_t to the right line d_t; right side down to the inner
end; inner end from the right line d_t to the left line d_t+1; left side d_t+1 up to the outer arc of turn t + 1.

Turn t exists when all of these hold:

1. The outer arc exists: d_t < R_out,t sin h.
2. The inner end lies inside the outer arc. Trapezoidal turn: the arc at R_in,t from the right line d_t to the left line
   d_t+1 exists (R_in,t > d_t+1 and the arc angle is positive). Otherwise triangular turn: the apex of the right line d_t
   and the left line d_t+1 has radius < R_out,t.
3. The right side is at least `min_side_length` long.
4. For t > 0, R_out,t is larger than the radius of the previous turn's inner end.

The generator stops at the first turn that fails. Cross-check (information only): D08 eq. 3.24 radial bound
N < ½((R_o0 − R_i0)/w_d + 1).

### G4 Path of layer X

Append, for t = 0 to N − 1: outer arc, right side, inner end (arc, or nothing at an apex), and the left side to the next
outer arc. After the last turn the lead of G5 follows. Record per turn: type, d_t, R_out,t, R_in,t or the apex radius,
the span at mean radius σ_t = θ_cp − 2 asin(d_t/r_mean) (EQ-08 per-turn pitch factor), and the side, end and turn lengths.

### G5 Centre via and lead (EQ-25)

The centre via sits on the coil centre line, the only locus that layer X and its mirror Y both reach.

- One centre via (single pair, or all pairs in parallel): r_lo = max((d_N−1 + w/2 + s + pad/2)/sin h,
  R_in,N−1 + w_in/2 + s + pad/2 if the last turn is trapezoidal); r_hi = R_out,N−1 − w_out/2 − s − pad/2.
- k centre vias (k series groups): the side bound uses d_N instead of d_N−1, because the leads of the other groups lie on
  the line d_N. Vias are spaced radially at pitch max(pad, w)/2 + pad/2 + s, centred on r_v.
- The eye fits when r_hi − r_lo ≥ (k − 1)·pitch. Via radius r_v = (r_lo + r_hi)/2.
- Lead on layer X: along the left line d_N from the last inner end up to radius r_v, then an arc at r_v to the centre
  line. Layer Y holds the mirror image.
- If the eye does not fit, reduce N until it fits and report `turn_limit.limiting_reason = "eye"`.

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
  ρ by 0.7 and retry, at most 12 times; report `rho_used`. Triangular apexes stay sharp in v1 (round caps keep the copper
  outline smooth).
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
| `turn_table` | per turn: type, d_t, R_out,t, R_in,t or apex radius, σ_t, lengths |
| derived geometry | per-coil track length per layer (body, lead, stub), EQ-03 closed form beside it, envelope r_min_cu, r_max_cu, copper area per layer, smallest clearance |

## Worked example 1: default 12/16 (example values)

Inputs: Q 12, 2p 16, r 18.0 to 38.0 mm, w 0.5, s 0.2, gap 0.2, via pad 0.6, bus width 1.0 mm (Xcoil `viaPad` and
`busWidth`), 34.8 µm copper, 20 °C, one layer pair. Output of `python3 checks/spiral_reference.py`:

- G1: w_d 0.7 mm; θ_cp 30°; R_o0 37.75 mm; R_i0 18.25 mm; d_0 0.35 mm.
- G7: pattern ACBACBACBACB, t = gcd(12, 8) = 4, balanced exactly, 0 coils on belt edges, k_d1 = 1.0 (k_p1 = sin(120°) =
  0.866).
- G3: radial bound 14.43; loop rule 11 turns (8 trapezoids, 3 triangles).
- G5: N = 11 fails (r_lo 31.2960 > r_hi 30.0000). N = 10 fits: r_lo 28.5914 (side bound), r_hi 30.7000, r_v 29.6457 mm.
  Result N = 10, `limiting_reason = "eye"`. With three series groups the eye allows 9 turns.
- G4 turn table, N = 10 (lengths in mm):

| t | type | d_t | R_out | R_in or apex | outer | right | inner |
|---|---|---|---|---|---|---|---|
| 0 | trapezoid | 0.35 | 37.75 | 18.25 | 19.0658 | 19.5017 | 8.1551 |
| 1 | trapezoid | 1.05 | 37.05 | 18.95 | 17.2991 | 18.1142 | 7.1192 |
| 2 | trapezoid | 1.75 | 36.35 | 19.65 | 15.5315 | 16.7359 | 6.0800 |
| 3 | trapezoid | 2.45 | 35.65 | 20.35 | 13.7624 | 15.3637 | 5.0366 |
| 4 | trapezoid | 3.15 | 34.95 | 21.05 | 11.9912 | 13.9948 | 3.9881 |
| 5 | trapezoid | 3.85 | 34.25 | 21.75 | 10.2169 | 12.6264 | 2.9340 |
| 6 | trapezoid | 4.55 | 33.55 | 22.45 | 8.4386 | 11.2560 | 1.8740 |
| 7 | trapezoid | 5.25 | 32.85 | 23.15 | 6.6550 | 9.8809 | 0.8077 |
| 8 | triangle | 5.95 | 32.15 | 24.3440 | 4.8647 | 7.9889 | 0 |
| 9 | triangle | 6.65 | 31.45 | 27.0484 | 3.0660 | 4.5208 | 0 |

- Path per coil-layer: outer 110.8913 + right 129.9834 + inner 35.9946 + left 119.4789 = body 396.3481 mm; lead
  3.0233 mm; stub 0.7877 mm; total 400.1591 mm. EQ-03 closed form for N = 10: 416.8085 mm (+5.16 % over the body).
- G6: r_T 38.5 mm; terminal angle 14.107° (start corner 14.469°). Vias: single pair 12; three parallel pairs 36; three
  series groups 60.
- G8: bus ring radii 39.5, 40.7, 41.9 mm for levels 0 to 2.
- EQ-10: 0.396502 Ω per coil-layer at 20 °C; 4 coils × 2 layers in series = 3.172020 Ω per phase before links.

## Worked example 2: D08 12/10

Inputs: Q 12, 2p 10, centre-lines 12.5 and 44.0 mm (D08 p.55, so copper edges 11.47 and 45.03 mm), w 2.06 mm (Table 4.6
p.57), s 0.8 mm (Table 4.5 p.54), gap 0.8 mm (`inferred`), via pad 0.6 mm (`unresolved`, not in D08), 34.8 µm, 50 °C.

- G1: w_d 2.86 mm; d_0 1.43 mm.
- G7: pattern AabBCcaABbcC = D08 Fig. 3.7 p.36 (`verified (reproduced)`). Six of twelve coils sit exactly on a belt edge,
  so the half-open belt rule decides them; floating-point floors do not.
- G3: radial bound 6.007; loop rule 3 turns (trapezoid, triangle, triangle) = D08 Table 4.6 p.57 (3 loops).
- G5: N = 3 fits at pad 0.6 mm: r_lo 35.8552, r_hi 36.1500, r_v 36.0026 mm; `limiting_reason = "loop"`. At pad 1.2 mm
  the eye allows 2 turns.
- G4: turn 0 trapezoid (outer 20.1778, right 31.5588, inner 0.7328); turn 1 triangle, apex radius 22.1499 (outer
  12.9452, right 19.1852); turn 2 triangle, apex radius 33.1836 (outer 5.6589, right 5.2022). Body 141.2781 mm, lead
  2.2270 mm, stub 2.1300 mm, total 145.6351 mm. EQ-03 closed form 177.2331 mm (+25.45 %).
- EQ-10: 0.039155 Ω per coil-layer at 50 °C; 4 coils × 2 layers = 0.313238 Ω per phase before links. D08 prints 0.39 Ω
  from the loop model (Table 4.6 p.57, calculated, not measured), so this is no validation.

## Acceptance checks for the implementation

- Turn counts exactly as above (CF-10, CF-11), and the concentric test mode of EQ-02 (3, 11, 8).
- Lengths within 1e-6 relative of the reference model for the same rules; within ±1 % when fillets are on.
- Pattern strings exactly as CF-09.
- The implementation's DRC (EQ-30) reports no violation for both examples. The reference model does not run a DRC, so
  this criterion is `not tested` until Agent 3's generator exists.
