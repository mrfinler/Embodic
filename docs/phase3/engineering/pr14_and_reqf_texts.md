Author model: claude-opus-5-5 (Agent 2, Motor design, unit U-E16, 2026-10-17). Worktree based on main b78dd90.

# PR-14 on Windows is a chord-count flip, and three REQ-F acceptance texts

This document answers brief U-E16. Part 1 explains the two PR-14 failures on Fable's Windows gate (Python 3.11.9, UCRT
maths, main 7d34543) and gives a derived bound. Part 2 gives the acceptance texts for REQ-F-03 (b), REQ-F-05 and
REQ-F-06 (b), which Agent 4 reported as contradicted by the product (`tests/independent/m7/records/V3-01_gaps_a.md`
l.178-189). Agent 6 edits `requirements.md` from part 2.

## Rulings in brief

- Both Windows values are a chord-count flip, not a non-invariance. With the chord counts held equal, the base and the
  rotated board give the same Ke to 6e-16 relative (serpentine) and bit for bit (wave). `verified` (probe, section 1.3).
- The current tolerances are not bounds. `KE_REL_TOL = 1e-8` (D-036c) covers about one net flip. The serpentine
  counter-example has 84 lines that can flip, and their envelope is 7.8e-7 relative. The wave case has 54, envelope
  2.8e-7. The tests pass on Linux because of where its last bits fall. Defect DEF-UE16-01 (section 1.6).
- Proposed test change. Hold the chord counts equal in both builds, then compare Ke at the round-off bound
  `2 (N + 10) u kappa`, which is 1.3e-12 for these boards. Section 1.5 derives it. The product code does not change.
- REQ-F-03 (b): one shared pair rotation builds; pairs at two rotations are refused. REQ-F-05: the via count is
  Q·v·(2k + 1). REQ-F-06 (b): U-E5 ruling, as recorded in D-033a: each fillet's length change within 1e-6 mm of the
  closed form, and the total within 1e-6 relative of the reference model. No 1 % bound.

## 1. PR-14 rotation invariance on Windows

### 1.1 The two failures

| Test | Quantity | Windows base | Windows rotated | rel. change | Tolerance |
| --- | --- | --- | --- | --- | --- |
| `test_serpentine_properties.py::test_pr_14_counter_example_sharp_corners_with_one_turn` | mean phase Ke peak | 0.016274993452848437 | 0.016274993132285004 | −1.97e-8 | 1e-8 (`KE_REL_TOL`) |
| `test_wave_properties.py::test_pr_14_rotating_..._unchanged[1.0-overlap]` | `ke_phase_v_s_per_rad` | 0.008100672544949162 | 0.008100672442611895 | −1.26e-8 | 1e-9 |

Values from the brief (Fable's Windows run). `verified` as quoted; not reproduced on Windows by this unit.

### 1.2 What a rotation can change in Ke

Ke comes from the flux linkage of every path. `integrate_path` (`src/embodic/physics/emf.py` l.151-161) sums one
midpoint term `B_z(r_m) r_m (c2 − c1) exp(−j n p theta_m)` per chord. The chords come from `discretise_path`
(`src/embodic/geometry/discretise.py` l.67-108). A line of length L gets `max(1, ceil(L / max_segment_mm))` equal chords,
with `max_segment_mm` 0.5 (l.19, l.47, l.64). `verified` by reading.

Every other step of the sum is continuous in the coordinates. The field table interpolates linearly, so it is
continuous across its nodes (`FieldTable.at`, l.57-66). The `atan2` wrap branch at l.158 gives the same angle modulo
2 pi on both sides, and `exp(−j n p theta)` has period 2 pi for integer n p. `inferred` from reading.

So the only discrete decision is the chord count. A rotation recomputes every coordinate through sin and cos. If a
line's L / 0.5 is an integer m by design, its computed ratio lands a few ulp above or below m. Then `ceil` gives m or
m + 1 chords. Both are valid discretisations of the same copper. They differ by the midpoint-rule error of that line,
which is of order 1e-8 of Ke per line here.

### 1.3 Probe results on Linux

`docs/phase3/engineering/checks/pr14_chord_flip_probe.py` wraps `embodic.geometry.discretise.piece_count`. It finds
every primitive whose ratio lies within 1e-9 relative of an integer and can force those counts to m ("down") or m + 1
("up"). It also rotates by a few ulp more or less than one electrical period, which stands in for another platform's
sin and cos. Output, run 2026-10-17 on this worktree:

```
== serpentine
Linux Ke base 0.016274993314785175 rotated 0.01627499345284843 rel +8.483e-09
Windows Ke base 0.016274993452848437 rotated 0.016274993132285004 rel -1.970e-08
base: 84 near-integer line or arc lengths, distance in ulp [-2.0, -1.0, 0.0, 1.0, 2.0, 3.0], chord counts [36, 37]
rotated: 84 near-integer line or arc lengths, distance in ulp [-1.0, 0.0, 1.0, 2.0, 3.0], chord counts [36, 37]
base forced down: Ke 0.01627499616098922 rel to Linux base +1.749e-07
base forced up: Ke 0.016274983524270672 rel to Linux base -6.016e-07
rotated forced down: Ke 0.01627499616098921 rel to Linux base +1.749e-07
rotated forced up: Ke 0.016274983524270665 rel to Linux base -6.016e-07
flip envelope (max - min) / Ke = 7.764e-07
Windows values inside the flip envelope: True
rotation  1 ulp off (1.1e-16 rad): rel -1.923e-08 -3.440e-08
rotation  2 ulp off (2.2e-16 rad): rel -1.798e-09 -3.393e-08
rotation  4 ulp off (4.4e-16 rad): rel +7.018e-08 +2.775e-08
rotation  8 ulp off (8.9e-16 rad): rel +8.048e-08 +4.881e-08
== wave-overlap
Linux Ke base 0.008100672493535611 rotated 0.008100672494025445 rel +6.047e-11
Windows Ke base 0.008100672544949162 rotated 0.008100672442611895 rel -1.263e-08
base: 54 near-integer line or arc lengths, distance in ulp [-6.5, -5.5, -3.5, -1.0, 0.0, 1.0, 9.0, 23.0], chord counts [2, 4, 5, 36, 37]
base forced down: Ke 0.008100672699189808 rel to Linux base +2.539e-08
base forced up: Ke 0.008100670395866587 rel to Linux base -2.589e-07
rotated forced down: Ke 0.008100672699189808 rel to Linux base +2.539e-08
rotated forced up: Ke 0.008100670395866587 rel to Linux base -2.589e-07
flip envelope (max - min) / Ke = 2.843e-07
Windows values inside the flip envelope: True
rotation  1 ulp off (1.4e-14 deg): rel +2.419e-10 -6.286e-09
rotation  4 ulp off (5.7e-14 deg): rel -1.874e-08 +1.281e-08
rotation  8 ulp off (1.1e-13 deg): rel -2.533e-08 -4.413e-08
```

The output is trimmed to the lines the argument uses. The script prints the rest. What the numbers show, each
`verified` by this run:

- **The rotation itself is invariant.** With the counts forced, the base and the rotated board agree to 1e-17
  absolute (6e-16 relative, about 3 ulp) on the serpentine and bit for bit on the wave.
- **Windows sits on the same discrete set.** The Windows base serpentine Ke equals the Linux rotated Ke to 7e-18
  absolute, which is 2 ulp of 0.0163. So the Windows base board most likely has the same chord counts as the Linux
  rotated board (`inferred`). All four Windows values lie inside the flip envelopes (`verified`).
- **A few ulp reproduce the Windows magnitudes.** A rotation 1 ulp off moves the Linux serpentine Ke by 1.9e-8 and
  3.4e-8. A rotation 1 to 4 ulp off moves the wave Ke by 2.4e-10 to 1.9e-8. Windows saw 2.0e-8 and 1.3e-8.
- **The near-integer set is clean.** Every ratio inside the 1e-9 window lies within 23 ulp of its integer, which is at
  most 5.1e-15 relative (23 × 2^-52). No ratio falls between 23 ulp and the window edge (about 5e6 ulp at m = 36).

The Linux wave rotation moves Ke by 6.0e-11, which is above the round-off bound of section 1.5 and below 1e-9. That
change is a flip of a primitive with a small share of the flux, because the forced counts remove it. `verified`.

### 1.4 What the platform maths promises

- CPython: "The math module consists mostly of thin wrappers around the platform C math library functions"
  (Python documentation, `math`, read at <https://docs.python.org/3.3/library/math>). The same sentence in the 3.11
  page is `inferred`, not read. So `math.sin`, `math.cos` and `math.atan2` differ between glibc and UCRT. `verified`
  for 3.3 by reading.
- glibc: the manual says the library "does not aim for correctly rounded results" for most maths functions and lists
  known maximum errors in ulp per function and architecture. It states "Vector versions of functions in the x86_64
  libmvec library have a maximum error of 4 ulps" (glibc manual, section 19.7, "Known Maximum Errors in Math
  Functions", snapshot at
  <https://snapshots.sourceware.org/glibc/trunk/2024-06-17_14-18_1718633881/manual/html_node/Errors-in-Math-Functions.html>).
  `verified` by reading. The scalar x86_64 sin and cos rows were not in the part of the table this unit read:
  `unresolved`.
- UCRT: no published ulp bound for `sin` or `cos` was found. `unresolved`.

The bound below does not need a libm error figure. It needs only two facts. A libm result can differ between
platforms in its last bits, which both sources allow. A designed integer ratio then lands on either side of the
integer, which the probe shows.

### 1.5 The bound a rotation can move Ke on any platform

Two terms make up the change of Ke between a board and the same board rotated by one electrical period.

1. **Chord-count flips.** Let F be the set of primitives whose ratio L / max_segment_mm lies within the platform's
   rounding of an integer m. Any subset of F can take m + 1 chords on one board and m on the other. The change is then
   at most the flip envelope `E = (max − min) / Ke` over the forced-down and forced-up builds. E is a property of the
   design, not of the platform: 7.8e-7 for the serpentine counter-example and 2.8e-7 for the wave overlap case.
   `verified` (probe). For one flip of an N-chord line the midpoint-rule error changes by about 2/N of its value, so E
   is about (2 / m) of the quadrature error that the flippable lines carry. `inferred` (midpoint rule error h²,
   standard result). No fixed constant bounds E for every design. A design with more lines on exact integer ratios
   has a larger E.

2. **Round-off with the counts equal.** The fundamental is a recursive sum of N chord terms. Its forward error is at
   most `gamma_N kappa |sum|`, with `gamma_N = N u / (1 − N u)`, `u = 2^-53` and
   `kappa = sum |term| / |sum|` (Higham, *Accuracy and Stability of Numerical Algorithms*, 2nd ed., SIAM 2002,
   section 4.2; `inferred`, cited from memory of the text, not re-read this unit). Each term is a product of four
   rounded factors plus `exp` and a linear interpolation. Ten more units of u cover those (`assumption`, about 1 to 2 u
   per operation). Both boards carry the error, which gives a factor 2. The rotated coordinates move each chord end
   by a few ulp of the radius (about 1e-14 mm at 40 mm). A common rotation leaves |sum| unchanged, so this term enters
   only at second order. `inferred`.

   `docs/phase3/engineering/checks/pr14_roundoff_inputs.py` measures N and kappa on the real boards:

   ```
   serpentine sharp 1 turn: chords on the board 6001, largest path 974, largest path kappa 70.077, board kappa 1.000, gamma_N(board) 6.66e-13, gamma_N(board) * board kappa 6.66e-13
   wave overlap: chords on the board 5389, largest path 143, largest path kappa 1.000, board kappa 1.000, gamma_N(board) 5.98e-13, gamma_N(board) * board kappa 5.98e-13
   ```

   The board kappa is `sum edge_weight / sum |flux_linkage[0]|`. It is the right ratio when the paths of one phase add
   in phase, which series coils of one phase do (`inferred`). The path with kappa 70 links almost no flux, so its
   absolute error is small. The round-off bound is `2 (N + 10) u kappa`: 1.33e-12 (serpentine) and 1.20e-12 (wave).
   The measured round-off is 6e-16 and 0, inside it.

**Bound.** On any platform, |ΔKe| / Ke ≤ E + 2 (N + 10) u kappa. With the counts held equal, E = 0.

**Are the Windows values inside a justified bound?** Yes. −1.97e-8 is inside 7.8e-7 + 1.3e-12, and −1.26e-8 is inside
2.8e-7 + 1.2e-12. Neither is inside the tolerance the tests use, because 1e-8 and 1e-9 are not derived from this
bound.

### 1.6 Defect and proposed tolerance

**DEF-UE16-01 (test defect, PR-14, not a product defect).** The PR-14 Ke tolerances, 1e-8 relative for the serpentine
(`KE_REL_TOL`, D-036c, `test_serpentine_properties.py` l.39) and 1e-9 for the wave (`test_wave_properties.py` l.90),
cover at most about one net chord flip. The flip envelope is 7.8e-7 (84 lines) and 2.8e-7 (54 primitives). The
outcome depends on last-bit libm rounding, so the tests pass on Linux and fail on Windows on the same commit.
Reproduce: `PYTHONPATH=src:. .venv/bin/python docs/phase3/engineering/checks/pr14_chord_flip_probe.py` and read the
"rotation 1 ulp off" lines. D-036c named the right mechanism but took the Linux observation (one flip, 8.5e-9) as the
tolerance.

The wave test asserts `ke_phase_v_s_per_rad` first, then `ke_line_v_s_per_rad`, `resistance_phase_20c_ohm` and
`loss_eddy_w` in one loop. Windows stopped at the first. The eddy sums use the same chords (`emf.py` l.162-164), so
`loss_eddy_w` can flip in the same way. `inferred`, `not tested`.

**Proposed change (Agent 3 owns the tests; this unit edits no test).** Make PR-14 test the property it names, which is
that no copper position or physics term depends on the start angle. Take the chord-count decision out of the
comparison.

1. In both builds of `_check_rotation` and of the wave PR-14 test, patch `embodic.geometry.discretise.piece_count`
   with `pytest.MonkeyPatch` so that a length ratio within `eta = 1e-9` relative of an integer m gives exactly m
   chords. Other ratios keep `ceil`.
2. Compare Ke, `ke_line` and `loss_eddy_w` at `rel = 2 (N + 10) u kappa`. The test computes N from `discretise_path`
   on the base board. Take kappa = 1 unless the test measures it. For the two named cases this is 1.3e-12 and 1.2e-12.
   A fixed constant is acceptable only with its N range stated: `rel = 1e-10` holds for every board with N ≤ 4.5e5
   chords at kappa = 1.
3. Keep the phasor angle, R and the DRC checks as they are. They did not fail and are outside this brief.

Why eta = 1e-9 relative. On Linux the designed integers land at most 23 ulp, 5.1e-15 relative, from the integer.
Windows landed on the same discrete set (section 1.3). So eta is 2e5 times the measured rounding noise. A ratio
outside the window keeps `ceil` on both boards, and rounding noise of 5e-15 cannot move it across an integer that is
more than 1e-9 away. So eta snaps every designed integer and leaves every other count as the product computes it.
`verified` for these two boards by the probe. For Hypothesis designs it is `inferred`. How close the nearest
generic ratio sits to the window edge is `not tested`, and it does not matter for the argument. A snapped line can differ from the product's own count by one chord, which changes Ke by about 1e-8. That
is the flip the test removes on purpose. It is not a defect the test then fails to see, because the snapped count is
applied to both boards.

**Not proposed: a product change.** Snapping inside the product's `piece_count` would make Ke the same on every
platform, but it departs from Xcoil's `ceil` (engine.js l.543, D-013 faithful port). The golden effect is
`not tested`. One flip moves Ke by about 1e-8, and the whole flip envelope of these designs is below 8e-7. That call
is Fable's.

**Not proposed: widening the tolerance to the envelope.** A tolerance of 7.8e-7 would be derived. It would also hide
any start-angle defect below 7.8e-7, and it would need recomputing per design.

## 2. REQ-F acceptance texts that match the decided behaviour

Each text replaces only the named criterion. Agent 6 writes the row.

### REQ-F-03 (b): pair rotation

Current text: "pi/Q rotation places vias in gaps" (`docs/phase2/architecture/requirements.md` l.72).

Proposed criterion (b): "One rotation pi/Q shared by every layer pair (option M3) builds a board whose path end points
equal, within 1e-9 mm, those of the board built with first coil angle theta_0 + pi/Q and no pair rotation. Pairs at two different
rotations, in series or in parallel, return Unbuildable with `UNBUILDABLE_PAIRS_ROTATED_APART` at
`/winding/layers/pairs`." Tests: `test_m3_a_rotation_every_pair_shares_turns_the_whole_winding` and
`test_ut_geo_11_pairs_rotated_against_each_other_are_refused` (`tests/unit/generators/test_spiral_pairs.py` l.168 and
l.192-205).

Rests on: `spiral_generator_spec.md` G6, "Pairs rotated against each other" (l.382-394, revision U-E6). A pair rotated
by pi/Q has no coil at the other pairs' coil positions, and its shift is p·pi/Q electrical (120° on CF-11, 75° on D08),
so a coil-level join would connect different phases (`verified (by computation)` arithmetic in the spec; the
prohibition is `inferred`). The test plan leaves open whether the Phase 1 build criterion for two rotations is
withdrawn (`test_plan.md` UT-GEO-11 row). This text withdraws it. Fable records that in a decision row. Until then the
status is `unresolved`.

### REQ-F-05: via count

Current text: "Default via counts 60 (M2) and 36 (M1) per Agent 2's formula (UT-GEO-13)" (`requirements.md` l.74).

Proposed criterion: "The winding via count is Q·v·(2k + 1) for Q coils, v vias per transition and k series groups.
Each coil has k centre vias, k − 1 transfer vias and 2 terminal vias (UT-GEO-13). Every through via clears foreign
copper (PR-01). Via resistance uses the count per transition (UT-PHY-11)."

Rests on: `spiral_generator_spec.md` G6 via plan (l.296-300, revision U-E6). The v1.0 formula
Q·v·(2k − 1 + [n_1 > 1] + [n_k > 1]) left out the terminal vias of end groups with one pair, and the generator places
them in every case. Tests: `test_ut_geo_13_series_coil_has_2k_plus_1_winding_vias`
(`tests/unit/generators/test_spiral_series_fan.py` l.77-90) and `test_ut_geo_13_parallel_pairs_need_36_winding_vias`
(`tests/unit/generators/test_spiral_pairs.py` l.68).

Effect on the old numbers, for a 12-coil design with v = 1 (`inferred`, arithmetic; that M1 is one parallel group and
M2 is three pairs in series is read from `docs/phase1/verification/defect_list.md` DEF-20). M1 (k = 1) stays at 36.
M2 (k = 3) changes from 60 to 84. The requirement text should state the formula, not the two counts, because the
counts depend on Q, v and k.

### REQ-F-06 (b): production-mode length, and the U-E5 ruling

Current text: "generated length vs true-spiral reference 1e-6 mm (reference mode), 1 % (production mode)"
(`requirements.md` l.75).

**U-E5 ruling (this unit restates it; D-033a recorded it on 2026-10-08).** With fillets on, no percentage bound
against the sharp or true-spiral length holds, and none should. G9 fillets nested corners concentrically. The radius
grows by one pitch per turn, so the outer corners of CF-11 carry radii up to 6.8 mm. The length change is a designed
consequence of the corner radius, not an error: −52.8389 mm, −12.718 % on CF-11 at rho 0.5 mm, and −10.1058 mm,
−6.305 % on CF-10 at rho 1.0 mm (`spiral_generator_spec.md` G9, l.419-439, `verified (by computation)` with
`checks/spiral_reference.py --corners`). The bound that holds is a per-corner one, because the generator and the
reference build the same tangent circles and only rounding separates them (`inferred`, spec acceptance checks
l.591-594).

Proposed criterion (b): "With sharp corners, the track length of each coil layer equals the reference construction
(`docs/phase2/engineering/checks/spiral_reference.py`) within 1e-6 relative. With fillets on, each corner's length
change equals the closed form of G9 at the generator's `rho_used` within 1e-6 mm, and the total length equals the
reference model's filleted length within 1e-6 relative (CF-11 at rho 0.5 mm: 362.6419 mm; CF-10 at rho 1.0 mm:
150.1692 mm)." Tests: `test_ut_geo_07_sharp_track_length_equals_the_reference_construction`
(`tests/unit/generators/test_spiral_length.py` l.48) and the three `test_def_m2d3_02_*` tests
(`tests/unit/generators/test_spiral_fillet_length.py` l.122-152).

Two notes for Agent 6. The old "1e-6 mm (reference mode)" is absolute, and the spec and the test use 1e-6 relative.
The proposed text uses relative. The phrase "true-spiral reference" predates U-E3. The reference is now the G1 to G9
construction in `spiral_reference.py`.

**DEF-UE16-02 (minor, test text).** `tests/unit/generators/test_spiral_length.py` l.9-11 says the fillet bound "waits
for Agent 2's U-E5 ruling". D-033a recorded that ruling on 2026-10-08. The docstring should cite D-033a and the
per-corner criterion. Reproduce: read l.9-11 against `docs/decision_log.md` D-033 (a).

## 3. Reproduce

```
cd /home/claude/wt/U-E16
PYTHONPATH=src:. /home/claude/embodic/.venv/bin/python docs/phase3/engineering/checks/pr14_chord_flip_probe.py
PYTHONPATH=src:. /home/claude/embodic/.venv/bin/python docs/phase3/engineering/checks/pr14_roundoff_inputs.py
```

The first takes about 8 s on one core and the second about 3 s. Neither changes any file.

## 4. Sources

- `src/embodic/physics/emf.py` l.115-168; `src/embodic/geometry/discretise.py` l.1-108;
  `src/embodic/physics/analyse.py` l.253-300 (read on this worktree).
- `tests/unit/property/serpentine/test_serpentine_properties.py` l.39, l.156-207;
  `tests/unit/property/wave/test_wave_properties.py` l.72-93.
- `docs/decision_log.md` D-032 (f, g), D-033 (a), D-036 (c); `docs/phase2/architecture/test_plan.md` PR-14 row
  (l.311) and UT-GEO-11 row (l.267).
- `docs/phase2/engineering/spiral_generator_spec.md` G6 (l.290-394), G9 (l.413-446), acceptance checks (l.586-600).
- `docs/phase2/engineering/equation_specification.md` EQ-02 tolerance (l.86).
- Python documentation, `math`: <https://docs.python.org/3.3/library/math>.
- glibc manual, "Known Maximum Errors in Math Functions":
  <https://snapshots.sourceware.org/glibc/trunk/2024-06-17_14-18_1718633881/manual/html_node/Errors-in-Math-Functions.html>.
- N. J. Higham, *Accuracy and Stability of Numerical Algorithms*, 2nd ed., SIAM, 2002, section 4.2 (cited from
  memory, not re-read: `inferred`).
