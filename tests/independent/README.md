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
| `continuity.py` | first joint of an ordered path whose end-to-start gap exceeds 1e-6 mm (IT-21; REQ-N-21 revision 2026-10-05, `COINCIDENCE_MM`) | a generator or writer that breaks a path, reverses a primitive or emits NaN |
| `board_dump_reader.py` | parses `embodic.board-dump` v1 into own records; reports every missing field, duplicate id, unknown layer, end point that disagrees with its geometry, and primitive not owned by exactly one object | a writer that drops or renames fields, rounds end points, or orders paths by file position |
| `xcoil_oracle.py`, `xcoil_oracle.cjs` | third oracle: Xcoil `segSegDist`, `ptSegDist`, `drcObjects` under Node, read-only | a defect in the instrument itself |
| `mutants.py` | applies 18 named defects to a copy of the instruments and checks a test fails for each | a self-test that passes whatever the instrument does |
| `drc_universe.py` | every copper item of a board (traces, vias, pads, edges, holes) on its layers; the section 7 exemptions as D-022 and D-022c amend them, each pair labelled with its rule; brute pair sweep | a DRC that checks the wrong layer pairs, exempts too much or too little, or picks the wrong kind |
| `random_boards.py` | seeded boards: 1 to 3 layers, self-crossing line and arc paths, vias on and off path ends, pads, holes, edges | - |
| `embodic_adapter.py` | the only instrument that imports embodic: builds a `Layout` from items through public constructors | - |
| `gr19.py` | GR-19 raw layouts through U-M1b's mapper and embodic's writer, read back by `board_dump_reader.py`; prints the violation table | - |

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
| A 1 um (1e-3 mm) intrusion is a violation; rule - 0.9 nm is clean and rule - 1.1 nm a violation (epsilon 1e-6 mm), for lines, concentric arcs and arc-line | verified |
| Each of the 18 seeded defects in `mutants.py` fails a test | verified for the 5 continuity and exemption mutants on 69381b5 (U-V1b-fix); the other 13 last run in part 2 |
| Rounding stays below `FP_MARGIN_MM` | assumption |
| embodic's DRC agrees with this instrument | verified on main a138975 (part 2, table below) |
| Xcoil `drcObjects` differs from exact arc distances by at most 0.002 mm | inferred from `discretize` sagTol 0.001 (engine.js l.536-555); one concentric case verified |

## Known limits

- `drcObjects` (engine.js l.1693) skips pairs inside one object that are closer than `1.6 * (wMax + s)` along the path.
  That exemption is wider than D-006 allows. Compare it with embodic only for pairs between objects.
- `drcObjects` checks segments only within one grid cell of each other (`gridQuery` with radius 0). Far-apart objects
  return `Infinity`.
- `contract_exemptions` codes interfaces.md section 7 with D-022 and D-022c from the text, not from
  `embodic.drc.items`. `test_exemption_model.py` checks it on hand-worked cases. D-022c says a land on an interconnect
  centreline is "exempt from that path"; the model reads that as every primitive of the path (open question to Fable).
- The minima test brackets the pairs run_drc reports as well as its own violating pairs, so a pair the contract exempts
  but run_drc reports is caught by the exemption tests, not by the minima test.
- Pads other than round ones are not modelled. All GR-19 pads are round.
- Epsilon is 1e-6 mm = 1 nm. A 1 um intrusion is 1000 epsilon.

## M1 verdicts (part 2, against main a138975)

Run `pytest tests/independent/m1 -q` (about 1 min) and `python tests/independent/m1/gr19.py` (violation table).

| Area | Verdict | Evidence |
|---|---|---|
| D-006 epsilon | pass | `test_intrusion_is_decided_by_d006`: rule - 1.05e-6 mm reported, rule - 0.95e-6 mm not, on 6 geometries; 1 um and 4 um reported; same on real copper (`test_injected_intrusion_in_a_real_layout`) |
| Kernels exact | pass | every reported value lies in a 1e-10 mm bracket on 200 boards; a +2 nm bias in the line-line, line-arc or arc-arc kernel fails the test (seeded in process) |
| `run_drc` vs brute sweep | pass | 200 random boards, violation sets equal under the documented exemptions |
| Exemptions | pass with defects | DEF-M1V-01; contract text narrower than the code (DEF-M1V-01 note) |
| Symmetry shortcut | pass | 18 symmetric boards: method `symmetric+grid+exact`, same violations as the full check; a false claim falls back |
| CancelToken | pass | pre-cancelled and cancel at every poll return None; an idle token returns a report |
| Board dump | pass with defects | 3 layouts parse in the own reader; geometry equals raw Xcoil records; DEF-M1V-04 |
| GR-19 mapper | pass with defects | DEF-M1c-01 confirmed (closed by U-M1z, see U-V1b-fix), DEF-M1V-02, DEF-M1V-03 |
| GR-19 minima | pass | lo <= `measured_min_mm` <= hi for every pair kind on 3 layouts |
| Timing ~0.1 s | inferred | medians 90, 141, 103 ms over 7 warm runs (2 cores, load 0.8); limiter not profiled |

GR-19 violation classes (rule 0.2 mm everywhere, Xcoil's `clearance`):

| Class | sector | serpentine | wave |
|---|---|---|---|
| `run_drc` violation_count | 133 | 23 | 576 |
| trace_via: DEF-M1c-01 artefact (via net `A`, path net `PHASE_A`) | 114 | 12 | 372 |
| trace_via: real D-006, near rule (0.199965 mm, hidden by Xcoil's 4 um slack) | 0 | 0 | 180 |
| trace_trace: real D-006, near rule (0.199965 mm) | 0 | 0 | 6 |
| trace_via: overlap, both report (DEF-M1V-02 junctions) | 13 | 6 | 12 |
| trace_trace: overlap, both report (DEF-M1V-02 junctions, DEF-M1V-03 `ic` objects) | 6 | 5 | 6 |
| trace_trace: contract would report, engine exempts by a documented rule | 132 | 187 | 373 |

## U-V1b-fix verdicts (against main 69381b5)

`pytest tests/independent -q` passes except the strict xfails for DEF-M1V-03 (2 layouts). DEF-M1c3-01 closed by U-M1c-fix2 (merged 2026-10-05).
The two xfails for closed defects are removed and their tests still fail on the old behaviour: the hairpin test fails
on the engine of 2f80dc8^1 (before U-M1c-fix), and renaming the via nets back to `A` makes run_drc report 114 / 12 / 378
rule-2 pairs that `test_no_trace_via_violation_where_the_via_ends_a_same_phase_path` rejects.

GR-19 violation classes (`python tests/independent/m1/gr19.py`, rule 0.2 mm):

| Class | sector | serpentine | wave |
|---|---|---|---|
| `run_drc` violation_count | 7 | 6 | 193 |
| trace_via: DEF-M1c3-01, contract exempts by the D-022c waiver, engine reports (before U-M1c-fix2; 0 after) | 7 | 2 | 2 |
| trace_via: real D-006, near rule (0.199965 mm) | 0 | 0 | 180 |
| trace_trace: real D-006, near rule (0.199965 mm) | 0 | 0 | 6 |
| trace_trace: real D-006, overlap, both report | 0 | 4 | 5 |
| any class marked OTHER (a disagreement with the contract) | 0 | 0 | 0 |

Board-dump case ids of a multi-board stack (Agent 6, D-016, U-D3). Preferred form: `<case_id>-board<k>` with `k` the
zero-based board index in stack order, plain decimal, no padding (`layout-serpentine-stack-board0`), and no suffix on a
one-board stack, so the existing GR-19 case ids stay as they are. This matches interfaces.md section 5 (l.1546).

## Defects (part 2, statuses as of U-V1b-fix)

| ID | Severity | Reproduce | Expected vs actual | Owner | Status |
|---|---|---|---|---|---|
| DEF-M1c3-01 | medium | `pytest tests/independent/m1/test_gr19_drc.py -k touches_an_interconnect --runxfail` | no trace_via violation between an interconnect path and a via its end lies on or that lies on its centreline (D-022c); sector 7 (4 N ends on transfer vias 60-62, 3 taps), serpentine 2 and wave 2 (N path 15 / 192 over terminal vias) | Agent 3 (U-M1c-fix2) | closed 2026-10-05 (xfail and `DEF_M1C3_01` class removed by Fable at merge; test active) |
| DEF-M1c-01 | medium | `pytest tests/independent/m1/test_gr19_drc.py -k same_phase_path --runxfail` | no trace_via violation where a via ends a same-phase path; 114 / 12 / 372 reported | U-M1z (mapper) | closed by U-M1z; xfail removed |
| DEF-M1V-01 | low | `pytest tests/independent/m1/test_drc_agreement.py -k two_steps_back --runxfail` | a fillet is exempt only from its neighbours; `abs(main) <= 1` also exempts it from the main primitive two steps back, so a 0.104 mm same-net clearance goes unreported. Same rule as Xcoil drcObjects l.1697, which applies it only to `cornerOk` objects. Also: interfaces.md section 7 must name the fillet, coincident-end and pad-via rules, or a literal reading reports every tight fillet corner | U-M1c owner; contract text: Fable | closed by U-M1c-fix (D-022b); xfail removed |
| DEF-M1V-02 | medium | `python tests/independent/m1/gr19.py` | phase copper (`PHASE_A`), leads (`U`), neutral (`N`) and vias (`A`) use four net names for joined copper, so star-point and lead junctions show as overlaps; sampled, not every pair attributed (inferred) | U-M1z (mapper) | superseded by D-022 (nets stay, interconnect waiver) |
| DEF-M1V-03 | medium | `pytest tests/independent/m1/test_gr19_drc.py -k continuous --runxfail` | one continuous chain per CopperPath; Xcoil `ic` objects map to one path with gaps of 11.28 mm (serpentine path 15) and 22.11 mm (wave path 192) | U-M1z (mapper) | open; strict xfail still fails on 69381b5 |
| DEF-M1V-04 | low | read `src/embodic/io/board_dump.py` l.8-11, l.108 | interfaces.md 9.2 says v1 has no field changes; the writer omits the layer PCB-tool name (D-009, MT-07) and always writes via `phase` null | interfaces.md owner (Fable) | open; `src/embodic/io/board_dump.py` l.11-12 and l.108 unchanged on 69381b5 |
| DEF-M1V-05 | low | `grep -n "edge:" src/embodic/drc/report.py src/embodic/drc/items.py` | report.py documents ids `edge:0/prim:5`; items.py emits `edge:outer/prim:5` | U-M1c owner | closed; `report.py` l.63 now documents `edge:outer/prim:5` |
