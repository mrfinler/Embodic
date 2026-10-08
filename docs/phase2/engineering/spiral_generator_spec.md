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

Revision 2026-10-05 (U-E3b): G5 gains the half closing (the last turn ends on the centre via where its side meets the
coil centre line). D08 now builds its three turns. G3, G4, G9, the outputs, worked example 2 and the acceptance checks
change with it. Worked example 1 is unchanged.

Revision 2026-10-08 (U-E5): G2 gives the stadium-end construction with its jog and clearance proof, and confirms the
straight-end chord levels. G3 gives the final `TURNS_EXCEED_LIMIT` texts. G9 gives the per-corner fillet length change
and the filleted CF-11 and CF-10 lengths. The acceptance tolerance for fillets changes. `checks/spiral_reference.py`
prints the per-corner table (`--corners`) and the stadium frame.

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

### G2 Coil footprint (revision 2026-10-08 (U-E5))

- Parallel sides: side t lies on the line parallel to the sector edge at perpendicular offset d_t. A point on the right
  line at axial parameter λ is λ(cos h, −sin h) + d(sin h, cos h); at radius R, λ = √(R² − d²). The left line is the
  mirror.
- Radial sides: side t lies on the ray at angle ±(h − δ_t) with δ_t = asin(d_t/R_i0). Because asin is convex, the gap
  between neighbouring rays at R_i0 is at least w_d and grows outward. Radial sides never meet, so a radial coil has no
  triangular turns.
- Arc ends: concentric arcs at R_out,t and R_in,t.
- Straight ends (revision 2026-10-08 (U-E5), `inferred`): chords perpendicular to the coil centre line. The outer chord
  of turn t lies at x = R_o0 cos h − t·w_d,out. Its centreline ends on the circle R_o0 at the sector edges and lies
  inside it everywhere else, so the copper stays inside r_outer. The inner chord of turn t lies at x = R_i0 + t·w_d,in.
  It touches the circle R_i0 on the centre line and lies outside it everywhere else, so the copper stays outside
  r_inner (G9 rim rule). U-M2d-3's inner chord at x = R_i0 is correct, and so is the generator's outer level R_o0 cos h
  (`generators/spiral/turns.py` `CoilFrame.of`). Xcoil differs (`engine.js` l.2255, l.2256). Its inner chord at
  r_inner cos h + w_in/2 puts copper r_inner(1 − cos h) = 0.613 mm inside r_inner on the CF-11 centre line. Its outer
  chord at r_outer cos h − w_out/2 differs from R_o0 cos h by (w_out/2)(1 − cos h) = 0.0085 mm on CF-11.
- Stadium ends (revision 2026-10-08 (U-E5); the shape reading is `inferred from image`, the construction `inferred`,
  the numbers `verified (by computation)` with `checks/spiral_reference.py` `stadium`). Each end is one circular arc
  tangent to the two side lines it joins. Xcoil has no stadium end for sector coils (`engine.js` `ends` is `arc` or
  `straight`), so no reference code exists.
  1. Outer ends carry the jog. The outer end of turn t ≥ 1 joins the left line d_t−1 to the right line d_t, as the
     arc-end jog of G3 does. Both lines are tangent to one circle with centre c_O = (x_O, y_O), y_O = w_d/(2 cos h),
     radius ρ_O,t = x_O sin h − d_t−1 − w_d/2. x_O solves |c_O| + ρ_O,1 = R_out,1. With K = R_out,1 + (d_0 + d_1)/2,
     x_O = (√(K² − y_O² cos² h) − K sin h)/cos² h. The circle for turn t + 1 is the same centre with radius
     ρ_O,t − w_d, so it is tangent to the lines d_t and d_t+1 and its outermost point is R_out,t+1.
  2. Turn 0 has no previous left side. Its outer end is the arc about c_O with radius ρ_O,0 = ρ_O,1 + w_d, from A_0 to
     its tangent point on the right line d_0. A_0 is the crossing of that circle with the left line d_0 on the side away
     from the coil centre, √((ρ_O,1 + w_d)² − ρ_O,1²) beyond the left tangent point of turn 1. A_0 is the start corner,
     and the stub of G6 lands there. A circle tangent to both lines d_0 fails: it touches the left line d_0 0.18 mm from
     turn 1's tangent point (CF-11), so turn 0's start would be 0.002 mm from turn 1.
  3. Inner ends carry no jog (both sides of turn t lie on d_t). The inner end of turn t is the arc about
     c_I = (x_I, 0), x_I = (R_i0 − d_0)/(1 − sin h), with radius ρ_I,t = x_I sin h − d_t. Its point nearest the origin
     is x_I − ρ_I,t = R_in,t. Below ρ_min = w_d/(2 cos h) the two sides of the turn would come closer than w_d. The
     inner end is then the apex-limited arc ρ_min about ((d_t + ρ_min)/sin h, 0), the stadium form of a triangular turn.
  4. Turn t is four primitives: the outer arc, the right side d_t between the two tangent points, the inner arc, and
     the left side d_t up to the left tangent point of turn t + 1. Every junction is tangent, so G9 fillets do not
     apply. The loop rule of G3 holds with these tangent points: the right side is at least `min_side_length` long, and
     the left side reaches the next outer tangent point.
  Clearance proof (`inferred`, closed form). Outer arcs of turns t ≥ 0 are concentric about c_O at radius steps w_d,
  so neighbouring outer arcs are exactly w_d apart (copper gap s). The same holds for the round inner ends about c_I.
  The left side d_t ends on the ray from c_O that also holds turn t's left tangent point, so its nearest copper on outer
  arc t is that arc's start, at distance √(w_d² + Δ²) ≥ w_d, where Δ is the distance along the line. An apex-limited
  inner end lies farther out than the concentric arc it replaces, so its gap to the previous inner end grows above
  w_d. Two sides of one turn meet the inner arc at tangent points 2ρ_I,t cos h ≥ w_d apart. The primitives that D-022
  rule 1 does not exempt (left side t − 1 against right side t, index difference 2) are therefore at least s apart.
  This argument is not yet a DRC run.
  Worked example (CF-11 inputs, `verified (by computation)` for the construction as written): x_O 29.9867, y_O
  0.3623, ρ_O,0 7.7611, ρ_O,1 7.0611; A_0 lies 3.2211 mm beyond turn 1's tangent point; x_I 24.1506, ρ_I,0 5.9006,
  ρ_min 0.3623 mm. Turns 0 to 7 have round inner ends at levels 18.25 to 23.15 mm; turns 8 and 9 are apex-limited
  (levels 24.0267 and 26.7313 mm). The right side is 5.5434 mm on every round turn (the feet of two fixed centres on
  parallel lines), against 19.5017 mm for arc ends. Turn 9's right side is 2.7007 mm. The closing (G5) and its eye
  bound with the stadium outer arc (|V − c_O| ≤ ρ_O,N−1 − w/2 − s − m) are `not tested`, so no turn count is given.
  `UNSUPPORTED_END_STYLE` (D-032 f). The generator refuses `end_style = stadium` while this construction is not
  implemented. After it is implemented, it still refuses stadium when any of these holds: radial sides (the side
  lines are not parallel, so no concentric family exists); w_out ≠ w or w_in ≠ w (the end pitch must equal the side
  pitch for concentric ends); more than one series group (k > 1; the closing is specified for k = 1 only); ρ_O,N−1 ≤
  w/2 + s + m with the full closing. Narrow sectors need no separate rule. The right side length (x_O cos h − y_O sin
  h) − x_I cos h does not depend on t, and the loop rule already stops the scan when that length is below
  `min_side_length`. In the catalogue today the refusal is `UNBUILDABLE_SPIRAL_OPTION_NOT_IMPLEMENTED` with pointer
  `/winding/coil/end_style` (`generators/spiral/generate.py` `_unsupported`).

### G3 Turn geometry and turn limit (revision 2026-10-05 (U-E3); revision 2026-10-08 (U-E5))

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

Closing half turn (revision 2026-10-05 (U-E3b)). With the half closing of G5, the last turn N − 1 has only primitives 1
and 2: the outer arc J → B with its jog, and the right side d_N−1 from B straight to P = (d_N−1/sin h, 0), the point
where the line d_N−1 meets the coil centre line. It has no inner end and no left side. The loop rule does not apply to
it; G5 states its own conditions.

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

Turn-limit refusal (revision 2026-10-08 (U-E4)). D-030 caps the turns per coil layer at `MAX_TURNS_PER_LAYER = 100`
(`assumption`). The generator returns `UNBUILDABLE_TURNS_EXCEED_LIMIT` with `{limit}` in four cases (read in
`generators/spiral/generate.py`, `_refusal` and `_closings`):

| Case | Requested turns | Cause | `{limit}` |
|---|---|---|---|
| 1 | above the cap | the request | the cap |
| 2 | any, or none | the loop-rule scan reaches the cap | the cap |
| 3 | any, or none | the best closing has more turns than the cap | the cap |
| 4 | above the turns that fit | the geometry | turns that fit (best closing) |

The current text, "The requested turn count exceeds the largest buildable count {limit}.", is false in cases 2 and 3
when the user asked for fewer turns or for none. Proposed catalogue text for Agent 3 (`errors/catalogue/generators.py`,
English, same code and placeholder):

"The requested turns, or the turns that fit between the radii, exceed the limit of {limit} per coil layer. Lower the
turn count, or change the trace width or clearance."

The text names both causes, so it is true in all four cases, and it gives a remedy that applies to each.

Final texts per cause (revision 2026-10-08 (U-E5), for Agent 3 to copy; English, code `UNBUILDABLE_TURNS_EXCEED_LIMIT`,
placeholder `{limit}` unchanged):

| Cause | Cases | Text |
|---|---|---|
| User cap: the request is above `{limit}` | 1, 4 | "The requested turn count is above the limit of {limit} turns per coil layer. Enter {limit} turns or fewer." |
| Loop rule: more turns fit than the cap `{limit}` | 2, 3 | "More turns fit between the radii than the limit of {limit} turns per coil layer. Enter {limit} turns or fewer, or increase the trace width or the clearance." |

In case 4, `{limit}` is the turns that fit, so "the limit" is the geometric one. `errors/catalogue/generators.py` maps
one text to one code. Two texts need either a second code or the cause passed with the issue. That choice belongs to
Agent 3 and Fable. Until it is made, the combined text above is the one to ship. Follow-up
(`inferred`, for Fable): in case 2 a request at or below the cap is refused only because the scan runs to the cap
before it reads the request (U-M2d-fix deviation). Scanning to min(request, cap) + 1 would build that request. This
is a generator change and needs its own unit and test.

### G4 Path of layer X (revision 2026-10-05 (U-E3))

Append the terminal stub (G6), then for t = 0 to N − 1 the four primitives of G3, then the lead of G5. Record per turn:
type, d_t, R_out,t, r_end,t, the jog length, the span at mean radius σ_t = θ_cp − 2 asin(d_t/r_mean) (EQ-08 per-turn
pitch factor), and the outer, right, inner and left lengths. The left length of the last turn ends at L.
Half closing (revision 2026-10-05 (U-E3b)): turns 0 to N − 2 as above, then the outer arc and right side of the closing
half turn; no lead. Its table row has type `half`, r_end = r_v, and no inner or left length.

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

Half closing (revision 2026-10-05 (U-E3b), `inferred`). The rule above is the full closing. The half closing ends the
path on the closing half turn of G3: the right side d_N−1 runs to P = (d_N−1/sin h, 0) and the centre via sits at
V = P, so r_v = d_N−1/sin h. P lies on the coil centre line and on the line d_N−1, so the last side itself lands on the
via and layer Y's mirrored side lands on the same point. There is no lead.

- Evidence (`inferred from image`, D08 Fig. 4.8 p.52 of the PDF page 57, rendered at 400 dpi and measured on the pixel
  grid, scale 12.77 px/mm from the 45.03 mm copper edge). Front layer, coil at 0°: at r ≈ 34 mm the copper across the
  coil is two side tracks on one side (offsets ≈ 1.4 and 4.4 mm from the sector edge, so d_0 and d_1) and three on the
  other (≈ 1.3, 4.2 and 7.1 mm, so d_0, d_1 and d_2). The innermost outer-end strip (r ≈ 38.4 mm, R_out,2) joins the
  d_1 side at one corner (the outer-end jog) and the d_2 side at the other. The d_2 side runs inward into the eye, and
  its copper covers the centre line from r ≈ 25.3 to 30.4 mm. The small circle sits on that copper near the centre line
  at r ≈ 31 mm, at the eye's narrow (inner) end; the eye is open from r ≈ 30.6 to 37.3 mm. The coil at −90° and the
  back-layer coil at 0° carry the via the same way, at the eye's inner end (r ≈ 30.5 to 31 mm); their side counts
  were not measured. So D08's third turn is a half turn per layer:
  three outer arcs, five side tracks. This differs from the brief's reading (via near the eye's widest end, see the
  U-E3b report). The image resolution is about 0.1 mm per pixel with blur over 2 to 3 pixels; positions carry about
  ±1 mm.
- Why the via is not at the widest end with a jog (`verified (by computation)`, arithmetic on the D08 inputs). On the
  centre line inside turn 2 of a full closing, a lead end of width w needs r sin h − d_2 ≥ w/2 + s + w/2, so
  r ≥ (7.15 + 2.86)/sin 15° = 38.68 mm, outside the outer arc limit 35.42 mm. A via there with no lead is not reachable
  by the last side, which lies 2.2 mm off the centre line at r 36 mm. Only where the side copper covers the centre line
  can the side reach the via on its own, and the mirror condition (layer Y reaches the same via) puts that point at P.
- Conditions for the half closing with N turns (one centre via, k = 1):
  1. Turns 0 to N − 2 pass the loop rule of G3. The closing half turn may be turn N_loop itself, because it needs no
     inner end.
  2. Its outer arc exists: d_N−1 < R_out,N−1 sin h.
  3. Its right side |B P| ≥ `min_side_length`.
  4. Via pad inside the side copper: pad ≤ w. Then the side end cap (half-width w/2) is the outermost copper at V.
  5. Clear of the previous inner end: r_v − w/2 ≥ r_end,N−2 + w_in/2 + s (for N = 1: r_v − w/2 ≥ r_inner).
  6. Clear of its own outer arc: r_v + w/2 + s ≤ R_out,N−1 − w_out/2.
  The previous turn's sides need no condition. P lies on the lines d_N−1, which are w_d from the lines d_N−2, so the
  side end cap clears them by w_d − w = s exactly and the via pad by w_d − w/2 − pad/2 ≥ s.
- Choice. The generator computes N_full (largest N with the full closing) and N_half (largest N meeting conditions 1 to
  6), builds the half closing when N_half > N_full and the full closing otherwise (at equal N the full closing keeps the
  last left side), and reports `turn_limit.closing` (`full` or `half`). When neither closing fits N_loop turns it
  reports `limiting_reason = "eye"` with the N it built, as U-M2d does with `turn_limit`. Example: a 0.6 mm via in D08
  with the full closing builds N − 1 = 2 turns and reports `eye`; the half closing builds 3.
- Not covered (`not tested`): pad > w (the pad would cross the s band to the previous sides; a connector inside the pad
  would fix it but is not specified), and k > 1 series groups (k vias cannot share P; those keep the full closing).
- DRC: the last side ends at V and has V's net, so embodic's connectivity exemption (a via and the end group of a
  same-net path whose end point lies on it, `src/embodic/drc/items.py` `exempt_pairs`) covers it. No new exemption.
  Clearances of worked example 2 are in its table.

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

### G9 Fillets, tapers and clearances (revision 2026-10-08 (U-E5))

- Fillets: nested corners are filleted concentrically. The innermost turn takes the set radius ρ; each turn further out
  adds one pitch. This is valid only when the end pitch equals the side pitch (w_out = w_in = w) or the corner is square;
  otherwise corners stay sharp and width steps are tapered (Xcoil `taperJunctions`). If any fillet does not fit, multiply
  ρ by 0.7 and retry, at most 12 times; report `rho_used`. The inner end of a triangular turn is an arc of chord w_d at ρ_t (G3, revision 2026-10-05 (U-E3)).
- Fillet length change per corner (revision 2026-10-08 (U-E5), `verified (by computation)`; the closed form is plane
  geometry, `inferred`). Corner families (`generators/spiral/fillets.py` `_family`): B (outer arc t into right side t,
  every turn with an outer arc), C and D (right side into inner end and inner end into left side, trapezoids only), and
  J (left side t into outer arc t + 1, every turn but the last of a full closing). Corner t of a family takes
  r = ρ + (t_inner − t)·w_d, where t_inner is the family's last turn. Xcoil uses the same radii (`engine.js` l.2306).
  - Between two straight lines with interior angle φ (straight ends; φ = π/2 − h at the outer chord, π/2 + h at the
    inner chord): ΔL = r(π − φ) − 2r cot(φ/2). At φ = 90° this is −0.4292 r.
  - Between a side line at offset d and an end arc of radius R about the origin (arc ends): let σ = −1 when the fillet
    lies inside the arc (B, J) and σ = +1 when it lies outside (C, D). With R_c = R + σr, β_0 = asin(d/R),
    β_c = asin((d + r)/R_c), λ_0 = √(R² − d²) and λ_c = √(R_c² − (d + r)²):
    ΔL = r(π/2 − σβ_c) − σ(λ_c − λ_0) − R(β_c − β_0).
    The three terms are the fillet arc, the line cut and the end-arc cut. The sharp corner has φ = π/2 + σβ_0.
    For R → ∞ and d = 0 the form gives r(π/2 − 2), the straight-line value at φ = 90°.
  - Totals, from `.venv/bin/python checks/spiral_reference.py` (`--corners` prints every row). CF-11 at ρ 0.5 mm:
    35 corners (B 10, C 8, D 8, J 9), radii 0.5 to 6.8 mm, Σr 113.4 mm. ΔL B −22.0519, C −6.7070, D −6.7070,
    J −17.3730, total −52.8389 mm, so 415.4808 becomes 362.6419 mm (−12.718 %). CF-10 at ρ 1.0 mm: 7 corners,
    ΔL −10.1058 mm, so 160.2750 becomes 150.1692 mm (−6.305 %).
  - Why −12.7 % and not about −2 %. The −2 % estimate puts ρ on every corner: −7.7572 mm (−1.867 %) for CF-11. That is
    not the G9 rule. With concentric radii the outer turns carry fillets up to 6.8 mm, and the change is roughly
    −0.43 Σr. U-M2d-3 measured 362.64 mm on the generator, which matches this reference. DEF-M2d3-02 is therefore a
    spec defect: the old acceptance line "±1 % when fillets are on" contradicted G9. The generator is not at fault.
- Half closing (revision 2026-10-05 (U-E3b)): the last side ends at P with a round end cap and is not filleted there;
  its clearance to the lines d_N−2 is exactly s, so a fillet or taper must not widen it.
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
| `turns_achieved`, `turn_limit` | N built; radial bound, loop-rule count, eye-limited count, `closing` (`full`, `half`; revision 2026-10-05 (U-E3b)), `limiting_reason` (`loop`, `eye`, `min_side`, `user`) |
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

## Worked example 2: D08 12/10 (revision 2026-10-05 (U-E3b))

Inputs: Q 12, 2p 10, centre-lines 12.5 and 44.0 mm (D08 p.55, so copper edges 11.47 and 45.03 mm), w 2.06 mm (Table 4.6
p.57), s 0.8 mm (Table 4.5 p.54), gap 0.8 mm (`inferred`), 34.8 µm, 50 °C. Centre via: drill 0.3 mm, pad 0.6 mm
(`assumption`; D08 gives no via size; pad = Xcoil `viaPad`; the drill enters no rule here except pad > drill). The
small circle in Fig. 4.8 measures about 1.3 mm across (`inferred from image`); the sensitivity run at pad 1.2 mm gives
the same turns. Numbers from `.venv/bin/python checks/spiral_reference.py` and `checks/spiral_r2_check.py`
(`verified (by computation)` for the rules as written; the rules are `inferred`).

- G1: w_d 2.86 mm; d_0 1.43 mm.
- G7: pattern AabBCcaABbcC = D08 Fig. 3.7 p.36 (`verified (reproduced)`). Six of twelve coils sit exactly on a belt edge,
  so the half-open belt rule decides them; floating-point floors do not.
- G3: loop rule 3 turns (trapezoid, triangle, triangle). Total = D08 Table 4.6 p.57 (3 loops) and eq. 3.24 to 3.26
  (bounds 6.007, 2.526 so N_c1 = 2, 1.059 so N_c2 = 1; D08 counts two trapezoids where this rule counts one).
- G5: the full closing fits N = 2 only (turn 2: r_lo 38.68 > r_hi 35.42 mm; a 2.06 mm lead needs 2.86 mm from the right
  side on the centre line). The half closing fits N = 3: P = d_2/sin 15° = 7.15/0.258819, r_v 27.6255 mm. Conditions:
  side |B P| 10.9222 ≥ 4.12 mm; pad 0.6 ≤ w 2.06 mm; previous inner end r_end,1 + w/2 + s = 21.9587 + 1.03 + 0.8 =
  23.7887 ≤ r_v − w/2 = 26.5955 mm; own outer arc r_v + w/2 + s = 29.4555 ≤ 37.25 mm. Result N = 3, `closing = "half"`,
  `limiting_reason = "loop"`. The image places the via near r 31 mm on the same side copper (see G5 evidence); the
  model's P is 3.4 mm further in, inside the band where the side copper covers the centre line (24.8 to 30.5 mm for
  a 0.6 mm pad).
- G3/G4 per-turn table, N = 3 (mm; left of turn 1 ends at J_2, the start of the last jog):

| t | type | d_t | R_out | r_end | jog | outer | right | inner | left |
|---|---|---|---|---|---|---|---|---|---|
| 0 | trapezoid | 1.43 | 44.00 | 12.5000 | 0 | 20.1778 | 31.5588 | 3.6787 | 28.6972 |
| 1 | triangle | 4.29 | 41.14 | 21.9587 | 2.8675 | 15.8128 | 19.3801 | 2.8620 | 16.5033 |
| 2 | half | 7.15 | 38.28 | 27.6255 (r_v) | 2.8932 | 8.5521 | 10.9222 | none | none |

- Path per coil-layer: outer 44.5427 (jogs 5.7607) + right 61.8611 + inner 6.5407 + left 45.2005 = body 158.1450 mm;
  lead 0; stub 2.1300 mm; total 160.2750 mm (160.5750 mm at pad 1.2 mm, a longer stub). EQ-03 closed form for three
  full loops: 177.2331 mm (+12.07 % over the body: it counts the inner end and left side of turn 2, and no jogs).
- Flux linkage (D08 design of `tests/unit/physics/test_oracles.py`, embodic field and integrator): layer X 0.002405
  V·s/rad; X and Y in series, per layer 0.002344 V·s/rad; D08's three concentric loops 0.001639 + 0.000814 + 0.000130
  = 0.002583. Ratio 0.908 (series pair) and 0.931 (layer X alone) against three loops (`verified (by computation)`).
  Why 0.908 and not about 0.97 as in CF-11 (`inferred`): the two jogs cost 7.8 % here (U-E3, N = 2: 0.922 of two loops),
  because each jog removes w_d = 2.86 mm from left sides only 16.5 and 28.7 mm long; the closing half turns add about
  0.00008 per layer, against 0.000130 for a whole loop 3. X alone exceeds the pair because the two half turns lie on opposite sides
  on X and Y, so their phasors add at an angle.
- Predicted Ke_LL with three turns (`inferred`, until U-M2d-2 runs OR-01 on the generator output): 0.02358 ×
  0.002344/0.00177 = 0.0312 V·s/rad (+0.7 % against the measured 0.031, D08 Table 9.1 p.98), from Fable's v1.0 lever
  (Ke 0.02358 at 0.00177); or 0.0340 × 0.908 = 0.0309 (−0.5 %) from Fable's loop-model value. Both lie inside the OR-01
  band [−8 %, +9.8 %]. With the back-iron factor of D08 Table 4.8 (1.2 T for 1.38 T) as well, about 0.027 (−12 % to
  −13 %), outside the band; that factor stays `unresolved` (`back_iron: unresolved`).
- Lead and via clearance table (copper edge to edge, mm, rule s 0.8 for trace-trace and trace-via; own coil and both
  neighbours, both layers, all vias through):

| Track or via | Nearest via (not landed on) | Nearest own copper | Nearest neighbour copper |
|---|---|---|---|
| X stub (entry) | 1.6669 (neighbour Y terminal) | 0.8016 (left side 0) | 0.8000 (neighbour right side 0) |
| X last side (turn 2, lands on the centre via) | 8.8763 (own Y terminal) | 0.8000 (left side 1) | 6.5200 (neighbour right side 0) |
| Y last side (mirror) | 8.8763 (own X terminal) | 0.8000 (left side 1, mirrored) | 6.5200 |
| Y stub (exit) | 1.6669 (neighbour X terminal) | 0.8016 (left side 0, mirrored) | 0.8000 (neighbour outer arc 0) |
| Centre via pad 0.6 mm, layers X and Y | none | 1.5300 (left side 1) | not nearer |

  At pad 1.2 mm the centre via clearance is 1.2300 mm. Smallest clearance over all non-adjacent copper pairs 0.8000 mm
  (outer arc 1 to left side 1); smallest trace-to-via 0.8000 mm (outer arc 0 to its own terminal via). No exemption
  beyond the existing connectivity rule.
- EQ-10: 0.043091 Ω per coil-layer at 50 °C; 4 coils × 2 layers = 0.344727 Ω per phase before links. D08 prints 0.39 Ω
  from the loop model (Table 4.6 p.57, calculated, not measured), so this is no validation. Revision 2026-10-08 (U-E4):
  the full generated phase is 0.485162 Ω at 50 °C, because the series chain and vias add 0.140435 Ω. The comparison
  basis is in equation_specification.md EQ-10, "What D08's 0.39 Ω phase resistance includes".

## Acceptance checks for the implementation (revision 2026-10-08 (U-E5))

- Turn counts exactly as above (CF-11: loop 11, full closing 10; CF-10: loop 3, half closing 3 at pad 0.6 and 1.2 mm),
  and the concentric test mode of EQ-02 (3, 11, 8). Revision 2026-10-05 (U-E3b): the CF-10 count returns from 2 to 3
  with `closing = "half"`, r_v 27.6255 mm.
- Lengths within 1e-6 relative of the reference model for the same rules. Revision 2026-10-08 (U-E5): with fillets on,
  each corner's ΔL within 1e-6 mm of `filleted_path` at the generator's `rho_used`, and the total within 1e-6 relative
  (CF-11 at ρ 0.5: 362.6419 mm; CF-10 at ρ 1.0: 150.1692 mm). The generator and the reference build the same tangent
  circles, so only rounding separates them (`inferred`).
- Pattern strings exactly as CF-09.
- The implementation's DRC (EQ-30) reports no violation for both examples. `checks/spiral_r2_check.py` measures the
  clearances with embodic's DRC distance kernels on the reference geometry (smallest = s in both examples); the
  generator's own DRC run is `not tested` until U-M2d-2.
- Per-coil flux linkage at least 0.96 of the concentric loops with the same radii for CF-11 (layer X), and at least 0.90
  of D08's three loops for CF-10 (series pair per layer; revision 2026-10-05 (U-E3b)).
