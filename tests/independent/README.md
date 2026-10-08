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

## M2 instruments and verdicts (U-V2, against main 24b33f2)

Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5

Run `pytest tests/independent/m2 -q` (about 20 s), `python tests/independent/m2/or01.py` (OR-01 numbers) and
`python tests/independent/m2/series_fan_brute.py` (series fan, about 1 min). The `own_*.py` files import nothing from
embodic. `or01.py`, `series_fan_brute.py` and the tests import embodic only to build the subject through the public
API (`build_layout`, `compute`, `analyse`, `save_project`, `load_project`) and to read its output.

| File | What it does | What it would catch |
|---|---|---|
| `own_winding.py` | star of slots with exact `Fraction` angles, half-open 60 degree belts in EQ-08 order; k_d,n from signed phasors, k_p,n = abs(sin(n p pi / Q)) for a one-slot-pitch coil | a belt edge rounded the wrong way, a lost polarity, k_p from the mechanical span |
| `own_emf.py` | EQ-05 cosh/sinh form evaluated exactly at every chord (no table), EQ-06 flux linkage on 0.05 mm chords clipped to the magnet span, line waveform peak over one electrical period | a field, z, clip or phase-sum change in embodic |
| `or01.py` | OR-01 from `oracle_cases.json` O1-D08 inputs and the own field, on the subject's D08 layout | see `test_or01.py` |
| `own_spiral.py` | G1 to G5 turn table, loop rule, full and half closing with the G5 choice, centre via radius, G9 fillet corner closed form (families B, C, D, J, concentric radii) | a turn off by a pitch, a wrong closing, a constant fillet radius |
| `series_fan_brute.py` | series-group board through embodic's dump writer, M1's own reader and M1's certified pair sweep under the contract exemptions | a fan stub or via closer than s |

| Item | Verdict | Evidence (`verified` = reproduced by running) |
|---|---|---|
| 1 Winding: phases and k_w for 12/16, 12/10, 12/14, 9/8, 24/22 | pass | `test_winding.py`: every coil's phase and polarity equals the own star; k_w,n (n 1, 5, 7) equals own k_d k_p within 1e-12. Own k_w1: 0.866025, 0.933013, 0.933013, 0.945214, 0.949469. 12/10 equals the published double-layer 0.933 (Emetor glossary "Concentrated winding" Fig. 2, https://www.emetor.com/glossary/concentrated-winding/); the other four have no external value read (`inferred` from the own formula). A belt-edge mutant in `star_of_slots.py` failed 3 tests |
| 2 Physics closed forms and EC-05 | pass | `test_physics_closed_forms.py`: EQ-05 at z = 0 equals K_n l_m / (l_m + mu_r G) within 1e-9 relative at r = 1e7 mm and rises to it monotonically; the own limit reproduces CF-01 1.162077823 T; EQ-06 sector loop in a uniform field equals B_1 (r_b^2 - r_a^2) sin(p sigma / 2) within 1e-12. `integrate_path` with abs(dr) failed 4 tests. The loop is a sector loop through the public `integrate_path` kernel, not a hand-built `Layout` through `analyse()` (deviation). EC-05 (`test_ec05.py`): own e_edge 0.017406 vs embodic 0.017380 on the D08 example and 0.27472 vs 0.27418 with the magnet span cut to 28 to 31 mm (0.14 % and 0.20 %); Ke_LL carries the reason "EC-05 validity limit exceeded" and status unresolved only in the second case (rule e_edge > 0.10) |
| 3 Spiral generator, CF-11 and D08 | pass | `test_spiral.py`: own plan N 10 full (CF-11) and N 3 half (D08) as the worked examples; every coil-layer's end-arc radii equal own R_out,t and r_end,t within 1e-9; one centre via per coil at own r_v (30.7 and 27.625479 mm) within 1e-9; joints within 1e-6; layer Y is the reversed mirror of X within 1e-9; CF-11 fillet change at rho 0.5 mm: generator -52.838874602741 mm, own closed form -52.838874602741 mm (equal within 1e-9). Series fan (`series_fan_brute.py`, rule s on every copper pair kind, contract exemptions): 0 violations for CF-11 k = 2 and 3 and D08 k = 2 and 3 (22.1, 28.7, 3.3, 4.5 s); every near pair's bracket starts at 0.199999 (CF-11) or 0.799999 mm (D08), a lower bound, not refined. A first run that refined every bracket to 1e-10 mm did not finish CF-11 k = 2 in 5.5 min; plateau pairs (concentric arcs) are the likely limiter (`inferred`, not profiled) |
| 4 OR-01 with an own field | pass | own Ke_LL peak 0.0308780 V s/rad, embodic 0.0308768 (-3.83e-5 relative), D08 measured 0.031 (own -0.39 %). Chord step 0.5 to 0.02 mm moves own Ke by 2.4e-7 relative; an own 48-step linear table gives -2.45e-5, so the table accounts for 1.4e-5 of the gap and 2.5e-5 is unexplained (`unresolved`) |
| 5 Provenance truth table through `compute()` | pass | `test_provenance.py`: property (`/rotor/remanence_t`) listed for user, example, default, not for measured; design (`/rotor/air_gap_mm`) listed only for example (D-023b); status and value equal in all 8 cells (D-007) |
| 6 Project file | pass | `test_project_round_trip.py`: 3 examples save and reload with equal design, origin and measurements; stored hash equals `compute()`'s; files validate against `project.v1.schema.json`; a re-save differs only in `saved_utc`; an edited value loads as `user`, an untouched one as `example` |
| 7 DEF-M2e3-01 | pass (cause found, no embodic defect) | `def_m2e3_01.py`, `test_def_m2e3_01.py`: the mapped GR-19 layouts get Xcoil's members (sector: coil objects, `computeSector` engine.js l.2471-2475; wave: track objects, l.2211-2214; one layer pair, so one member per element). Sector: embodic phase R 1.271697 vs Xcoil phaseRtrace 1.271623 ohm (+5.8e-5); with `_series_circuit` +3.3 % to +4.2 %, so rings and legs were the gap. Wave: 1.373037 vs 1.460601 ohm (-6.0 %) with Xcoil's members and -5.8 % with `_series_circuit`; the gap is 62 via barrels that Xcoil adds into Rtrace (`R += e.R + rVia` l.2034, `Rtrace: R` l.2062): 62 x own rVia 1.41359e-3 ohm = 0.087643 against the gap 0.087564 ohm (within 0.1 %). The physics.toml reasons that say Rtrace omits the via barrels are wrong for the wave case (DEF-UV2-02) |
| 8 XD-M1-002 by dense sampling | pass with defects | `test_xd_m1_002.py`: embodic's distance lies in the certified bracket on all 1000 calls; exactly 19 goldens are false 0s, largest true value 13.084767 mm, inside the 13.1 mm allow-list tolerance; dense sampling (20001 points per segment) agrees with the bracket within 1e-3. DEF-UV2-01 |
| 9 Gate stability and section 5.5 | pass (report) | `test_cancel_from_another_thread_stops_a_long_run` is Agent 3's (tests/unit/drc/test_run_drc.py l.295): a 0.05 s timer and an absolute 2.0 s bound break rules 1 and 2. `test_cancel_without_clock.py` is the rule 1 form: a token that turns true at its k-th read; run_drc returns None after exactly k reads for k = 1, the middle and the last read of a full run |
| 10 `-board<k>` | not applicable | M2 writes no multi-board dump; `series_fan_brute.py` dumps one board as `CF-11-k2` with no suffix, as the rule says |

Gate stability (`python tools/ci.py --profile commit`, 2 cores, shared with another unit's gate). Three runs on ca37728 (a `git archive` snapshot): 273.44 s, 220.40 s, 223.50 s wall, each 6 of 6; load average at start 1.70, 2.48, 1.33; the first run overlapped Agent 4's own series fan sweeps. Final head 900929b: 6 of 6, 1268 passed, 3 xfailed, 226.95 s (load 0.64). pytest is the limiter (about 99 % of each run). An earlier run on b2f528c failed TR-02 because the new M2 tests had no REQ marker; c7bfe3d added them. `test_cancel_from_another_thread_stops_a_long_run` passed in all four runs (`verified`), which shows only that this load did not trip it.

Defects (U-V2):

| ID | Severity | Reproduce | Expected vs actual | Owner | Status |
|---|---|---|---|---|---|
| DEF-UV2-01 | low | `pytest tests/independent/m2/test_xd_m1_002.py -k true_range --runxfail` | the XD-M1-002 reason (tests/golden/expected_diffs/m1.toml l.20), test_plan.md section 3 (l.84) and D-033c state the 19 true distances as 4.0001 to 13.0848 mm; they are 0.528833 to 13.084767 mm (4.000143 is call 18, not the least). The 13.1 mm tolerance still covers all 19 | allow-list owner (Agent 3), test_plan.md (Agent 6), decision log (Fable) | open; strict xfail |
| DEF-UV2-02 | low | `python tests/independent/m2/def_m2e3_01.py`; read tests/golden/expected_diffs/physics.toml l.49-89 | the wave entries name `_series_circuit` and omitted via barrels and links as the cause; with Xcoil's own members the -6.0 % stays, and it equals the 62 via barrels that Xcoil's wave Rtrace includes (engine.js l.2034, l.2062). The sector cause (rings and legs in the series circuit) is confirmed | golden harness owner (Agent 3) | open; reason text only, tolerances unaffected |

## M3 instruments and verdicts (U-V3, against main 72b3231)

Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5

Run `pytest tests/independent/m3 -q` (about 2.5 min with the DRC sweep; the sweep is marked `slow`, so the commit
gate skips it). Tables: `python tests/independent/m3/layouts.py`, `drc_m3.py`, `gr22_own.py`, `examples_m3.py`,
`ulp.py` (run from `tests/independent/m3`). Node and `/home/claude/serpentine/src/engine.js` (read-only) are needed.

| File | What it does | What it would catch |
|---|---|---|
| `xcoil_dump.cjs` | own Node dump of Xcoil `compute()`: layers with board, z and raw primitives, vias, pads, DRC issue count, analysis scalars, and V8 trig values | - |
| `cases.py` | 6 serpentine and 6 wave parameter sets, each mixing options the golden lists vary one at a time | - |
| `own_map.py` | both sides to one `Board` shape (copper per layer with one role vocabulary, z, via and pad discs); exact point-to-primitive distance; sampled distance both ways with ties resolved by role and width | a moved, dropped, re-widened or re-roled primitive; a moved via (self-test seeds each) |
| `subject.py` | embodic's BoardStack through `build_layout`; inputs through the harness's `design_from_xcoil` (deviation below) | - |
| `layouts.py` | item 1 table: boards, layers, z, counts and lengths by role, sampled distance, vias, pads, stack thickness | see `test_m3_layouts.py` |
| `drc_m3.py` | item 2: every board through embodic's dump writer, M1's reader and M1's certified sweep under the section 7 exemptions | a missed or false D-006 violation, an exemption wider or narrower than section 7 |
| `gr22_own.py` | items 3 and 4: Ke_LL peak from M2's own EQ-05/EQ-06 field on the ported layouts, z from `copper_z_mm` | a field, z or phase-sum change; a doubled board offset |
| `examples_m3.py` | item 5: the two examples through `embodic.api.compute` against Xcoil `compute()` | - |
| `ulp.py` | item 6: V8 against glibc on 1000 seeded angles (atan2 on 1000 equal coordinate pairs) | - |

Deviation. The Xcoil-to-design input map is the golden harness's `design_from_xcoil`. It maps inputs only. Every
expected value comes from the own dump and mapper, so a wrong input map shows as a disagreement. One effect: the wave
map keeps the base design's outline (bore radius 18.7 mm) while the copper of these sets reaches 17.3 to 17.7 mm, so
the wave boards carry copper_edge and copper_hole overlaps that Xcoil's own outline would not. Both checks report them
alike. The D-035 b T-junction rule is not modelled (in flight, U-M3-fix).

| Item | Verdict | Evidence (`verified` = reproduced by running) |
|---|---|---|
| 1 Object-by-object layouts | pass | 12 cases, 14 boards: board and layer counts equal; z within 8.9e-16 mm; counts by role equal except +1 ring arc on the two star serpentine cases (U-M3a deviation D-1, ring cut at the middle tap; lengths equal within 4.5e-13 mm); length by role within 1.0e-11 mm; sampled distance at most 1.5e-13 mm both ways over 201 k samples; 0 width and 0 role mismatches; vias 942/942 and pads 24/24 within 7.9e-15 mm |
| 2 Brute DRC vs run_drc | pass with defect | 13 of 14 boards: violation sets equal (serpentine 0; wave 250, 484, 0, 572, 216). w-overlap-p12-l4-m1: engine 53, brute 51; DEF-UV3-01 |
| 3 Per-phase stack (D-016) | pass with defect | board k holds only phase k; z = k (1.6 + 0.3) + local z within 1e-12; stack 5.4 mm on both sides. DEF-M3a-01 still present on 72b3231: own Ke 0.08409251, embodic 0.08840266 (+5.13 %); own with board k moved a further k x 1.90 mm gives 0.08840354 (1.0e-5 from embodic) |
| 4 GR-22 own field | pass | Ke_LL peak, own vs embodic: s-radial-t4 0.1080441 / 0.1080331 (-1.02e-4); w-involute-p20-l2-m3 0.06328063 / 0.06327935 (-2.0e-5). Limiter not isolated (own chords vs embodic table, `unresolved`) |
| 5 Examples vs Xcoil compute() | pass with defect | see table below; DEF-UV3-02 |
| 6 V8 vs glibc | pass (report) | node v22.22.2, CPython 3.11.15, glibc 2.39: worst 1 ulp for sin, cos, atan2, tan; differing calls 33, 40, 160, 27 of 1000; worst absolute 4.4e-16 |
| 7 Gate stability | pass (report) | see the line below the examples table |

Examples (item 5). Xcoil's `Ke1` and `keLinePk` are fundamentals; embodic's `ke_line_peak` is the waveform peak.

| Quantity | serpentine embodic / Xcoil | wave embodic / Xcoil | Named difference |
|---|---|---|---|
| DRC violations | 0 / 0 | 191 / 0 | wave: Xcoil's 4 um slack (D-035) and interconnect copper (in flight); none outside those two classes |
| Ke phase fundamental | 0.06426724 / 0.06426724 | 0.03087959 / 0.03087959 | none (rel 2e-15) |
| Ke line fundamental | 0.1113141 / 0.1113141 | 0.05348502 / 0.05348502 | none |
| Ke line waveform peak | 0.1093881 (-1.73 %) | 0.05300629 (-0.90 %) | fundamental vs peak |
| R phase, operating | 2.823589 / 2.81246 (+0.396 %) | 1.467715 / 1.463644 (+0.278 %) | serpentine: vbus copper (XD-PHY-003), `inferred`; wave: via length (D-035 e) |
| P_ic | 0.006104918 / 0.006104564 (+5.8e-5) | 0.002574557 / 0.01117442 (-77 %) | wave: none, DEF-UV3-02 |

Gate (`python tools/ci.py --profile commit`, 2 cores). Runs 1 and 2 on a `git archive` of 72b3231: 415.45 s and
425.80 s wall, 6 of 6, 2006 passed, 4 xfailed; load at start 0.61 and 1.88; both overlapped Agent 4's own sweeps.
pytest is the limiter (409.69 s of run 1).

Defects (U-V3):

| ID | Severity | Reproduce | Expected vs actual | Owner | Status |
|---|---|---|---|---|---|
| DEF-UV3-01 | low | `pytest tests/independent/m3/test_drc_m3.py -k overlap-p12 --runxfail` | rule 2 exempts a via and the end group of a path ending on it, and the end group holds the fillet before the terminating main (section 7 rules 1 and 2). `_path_ends` (src/embodic/drc/items.py l.173-180) takes the items whose main index equals the last main's, and a fillet carries the index of the main before it, so at a path's last end the preceding fillet is left out. w-overlap-p12-l4-m1: paths 0 and 25 end on stitch via 2 through a 0.302 mm leg; fillet 5 is reported at -0.198 mm. The first end is not affected (`inferred` from the code) | Agent 3 (DRC) | open; strict xfail |
| DEF-UV3-02 | medium | `cd tests/independent/m3 && python examples_m3.py`; `pytest tests/independent/m3/test_m3_physics.py -k wave_example_interconnect --runxfail` | wave example P_ic: Xcoil 0.01117442 W (star: line stubs, links and two neutral-ring segments at `busWidth`, engine.js l.1361-1374, l.1423), embodic 0.002574557 W. The serpentine example agrees within 5.8e-5. Cause `unresolved`; it may share the root of the wave star item (U-M3b Q3, in flight) | Agent 3 (physics, wave port) | open; strict xfail |
| DEF-M3a-01 | medium | `pytest tests/independent/m3/test_m3_physics.py -k board_z --runxfail` | confirmed on 72b3231 with the own field (item 3 row) | U-M3-fix | open; in flight |

Open question. `embodic.api.compute_project` on `resources/examples/serpentine_16p_example.embodic.json` returns
`INVALID_PROJECT_FILE`. The examples load through `embodic.io.examples.load_example`. Is a packaged example file meant
to open as a project?
