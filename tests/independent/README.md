Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5

# Independent verification instruments

These instruments are Agent 4's own code. They are written from the contract (`docs/phase2/architecture/interfaces.md`
sections 5, 7 and 9.2, and `docs/phase1/software/calculation_flow_and_port_notes.md` section 7.5). They import nothing
from `embodic`, so a defect in embodic cannot also hide in the expected values (standing order 12).

## How to run

```bash
python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
pytest tests/independent/m1 -q              # self-tests; the Xcoil tests need node and /home/claude/serpentine
python tests/independent/m1/mutants.py      # seeded defects; every one must be killed
```

## M1 instruments (`m1/`)

| File | What it does | What it would catch |
|---|---|---|
| `records.py` | own `Line` and `Arc` records; a via or round pad is a zero-length `Line` whose width is the pad diameter | - |
| `brute_clearance.py` | certified bracket of the clearance between two primitives; rule D-006 verdict; O(n^2) pair sweep of one layer with a proven box cull (IT-12) | a DRC that misses a 1 um intrusion, uses Xcoil's 0.004 mm slack or epsilon 0, or under-reports arc pairs (PR-01, PR-13) |
| `continuity.py` | first joint of an ordered path whose end-to-start gap exceeds 1e-9 mm (IT-21) | a generator or writer that breaks a path, reverses a primitive or emits NaN |
| `board_dump_reader.py` | parses `embodic.board-dump` v1 into own records; reports every missing field, duplicate id, unknown layer, end point that disagrees with its geometry, and primitive not owned by exactly one object | a writer that drops or renames fields, rounds end points, or orders paths by file position |
| `xcoil_oracle.py`, `xcoil_oracle.cjs` | third oracle: Xcoil `segSegDist`, `ptSegDist`, `drcObjects` under Node, read-only | a defect in the instrument itself |
| `mutants.py` | applies 16 named defects to a copy of the instruments and checks a test fails for each | a self-test that passes whatever the instrument does |

## Why the bracket is certified

`centreline_bracket(p, q)` returns `lo <= D <= hi` for the true centreline distance `D`. The argument has three steps.

1. Line to line is exact. In 2-D the distance between points of two segments is a convex function of the two segment
   parameters. Its only interior minimum with a positive value would need the two lines to be closest at an interior
   point, which happens only where they cross. So two segments that do not properly cross are closest at an end point
   of one of them. The kernel returns 0 for a proper crossing, else the least of four point-to-segment distances.
   `verified` by running: it agrees with Xcoil `segSegDist` (engine.js l.563) on 200 seeded pairs within 1e-9 mm.
2. An arc piece is within its sagitta of its chord. Take a piece of radius `r` and sweep `theta <= pi`. A point of the
   piece at angle `phi` from the piece's middle (`|phi| <= theta / 2`) is `r cos(phi) - r cos(theta / 2)` from the chord
   line. That value lies in `[0, s]` with `s = r (1 - cos(theta / 2)) = 2 r sin^2(theta / 4)`. Its foot
   `r sin(phi)` lies inside the chord. The point of the arc above each chord point is at most `s` away as well. So the
   Hausdorff distance between the piece and its chord is at most `s`. For any sets, `|dist(A, B) - dist(A', B')| <=
   H(A, A') + H(B, B')`, so `D` lies in `[d_chord - s_p - s_q, d_chord + s_p + s_q]`.
3. Branch and bound keeps the minimiser. Arcs start as pieces of at most pi/2. Every pair whose lower end is below
   `min(threshold, best_hi - tol)` is split by halving the piece with the larger sagitta. A pair is dropped only when its
   lower end exceeds the best upper end found, so the pair that holds the true closest points is never dropped. The
   bracket is the least lower end over kept pairs and the best upper end.

Sampling step against tolerance. The sagitta shrinks with the square of the sweep, so a bracket of width `w` needs
pieces with `theta <= sqrt(2 w / r)` near the closest points. Example (illustrative numbers): `r = 20 mm` and
`w = 1e-10 mm` give `theta <= 3.2e-6 rad`. Uniform sampling of a whole end turn at that step would need about 1e5
pieces. The branch and bound refines only near the closest points, except on a plateau (concentric arcs), where every
angle of the overlap is a minimiser. The concentric-arc self-test therefore asks for `tol = 1e-8 mm`.

Rounding. Both ends carry an extra `FP_MARGIN_MM = 1e-12`. That margin is an `assumption`: for coordinates up to
1000 mm the kernels' rounding stays near 50 ulp of 1000. It is not proven.

Rule D-006. `verdict()` reports a violation when `clearance.hi < rule - 1e-6 mm`, clean when
`clearance.lo >= rule - 1e-6 mm`, and undecided otherwise. Undecided means the true value lies within `tol` of the
threshold, or the pair budget ran out. Clearance is signed: overlapping copper gives a negative value.

Box cull. `brute_violations` skips a pair only when the distance between its boxes reaches the centreline threshold
`rule - epsilon + (w_i + w_j) / 2`. An arc's box is the union of its pi/2 chords' boxes widened by their sagittas. By
step 2 that box contains the arc, so box distance is a lower bound of `D`.

## Status of each claim

| Claim | Status |
|---|---|
| Line kernel agrees with Xcoil `segSegDist` and `ptSegDist` within 1e-9 mm | verified (`test_against_xcoil_kernels.py`) |
| Brackets contain the closed-form values for parallel, crossing, tangent, concentric and arc-line cases | verified (`test_brute_clearance.py`) |
| Brackets overlap a dense point sampling with the 1-Lipschitz bound on 40 random arc pairs | verified (`test_bracket_contains_dense_point_sampling_on_random_arc_pairs`) |
| A 1 um intrusion is a violation and rule - 0.9 um is clean, for lines, concentric arcs and arc-line | verified |
| Each of the 16 seeded defects in `mutants.py` fails a test | verified (run `mutants.py`) |
| Rounding stays below `FP_MARGIN_MM` | assumption |
| embodic's DRC agrees with this instrument | not tested (part 2, after U-M1c merges) |
| Xcoil `drcObjects` differs from exact arc distances by at most 0.002 mm | inferred from `discretize` sagTol 0.001 (engine.js l.536-555); one concentric case verified |

## Known limits

- `drcObjects` (engine.js l.1693) skips pairs inside one object that are closer than `1.6 * (wMax + s)` along the path.
  That exemption is wider than D-006 allows. Compare it with embodic only for pairs between objects.
- `drcObjects` checks segments only within one grid cell of each other (`gridQuery` with radius 0). Far-apart objects
  return `Infinity`.
- Exemptions follow interfaces.md section 7: consecutive primitives of one path (`path_adjacent`) and the via or pad
  that terminates a path end. The via and pad part is not wired yet (part 2).
- Pads other than round ones are not modelled yet.
