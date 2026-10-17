Prepared by: Agent 6 - Software Architecture Specialist - model: claude-opus-5-5

# embodic Phase 2 requirements (build contract v1, 2026-10-04)

This file is the final requirement set for Phase 2. It carries, amends or withdraws every requirement of
`docs/phase1/architecture/requirements_draft.md` (98 IDs) and adds the requirements of the approved Phase 2 scope
(`docs/PROJECT_BRIEF.md` §5, `docs/decision_log.md` D-008 to D-015). Full Phase 1 wording, sources and sub-criteria stay in
the Phase 1 file; a row here that says "Phase 1 criteria" means criteria (a), (b), ... of the same ID there, unchanged.

Revision 2026-10-11 (U-D12, claude-sonnet-5-5; D-041a and D-041b; main 4fda98d read for every item). The acceptance text of
REQ-F-38 no longer requires "Example" in gallery titles, because `project.v1.schema.json` no longer requires it in
`example.title` and the five packaged titles do not hold it (`test_ut_io_08_examples_are_packaged_with_the_ruling_g_display_titles`,
`tests/unit/embodic_io/project/test_examples.py` l.44). The statement of the row is unchanged. No ID is new, and the
test IDs of the row are unchanged.

Revision 2026-10-17 (U-D17, claude-sonnet-5-5; D-051a and D-051f, `docs/decision_log.md` l.57; main 0547f20 read for
every item). Two rows change. REQ-F-10 says "a computed clearance" where it said "the measured clearance". The DRC
distance comes from the generated geometry (`src/embodic/drc/engine.py` l.336), and `measured` is reserved for an input
that has a named source (D-007, REQ-T-06). The acceptance of REQ-N-04 now says how two platforms are compared. PK-04
compares each array of the outcome JSON at 1e-9 relative to the largest absolute value in that array, so an element
whose true value is 0 does not fail on rounding noise. `layout_hash` and `stack_hash` are same-platform identities that
the cross-platform comparison leaves out (interfaces.md §5). The statement of REQ-N-04 is unchanged. No ID is new, and
the test IDs of both rows are unchanged.

## How to read the table

- **Disp.** `carried` = unchanged; `amended` = changed by a Phase 2 decision (the statement here wins); `withdrawn` =
  out of scope, guarded by the scope test MT-07; `new` = added in Phase 2.
- **Prio** `must` / `should` / `could` as in Phase 1. **M** = the milestone whose done predicate requires the criterion
  (`work_breakdown.md`). **Owner module** = the package that implements it. **Tests** = test IDs from
  `docs/phase1/architecture/test_plan_draft.md` (carried) or `test_plan.md` (new or amended).
- Thresholds marked `assumption` in Phase 1 stay `assumption` until measured. No row claims torque, balance or efficiency
  from geometry alone (brief rule 6).
- `checks/check_contract.py` verifies: IDs unique, every Phase 1 ID dispositioned, every row has a test ID that exists and
  is not withdrawn (for live rows), and the matrix in `test_plan.md` matches this table.

Disposition summary: 33 functional, 26 non-functional, 16 KiCad, 14 traceability and 9 language requirements came from
Phase 1. All 16 REQ-K rows are withdrawn (D-009). New rows: REQ-F-34 to REQ-F-40, REQ-N-27 to REQ-N-29, REQ-T-15,
REQ-T-16. The check script prints the exact counts.

Revision 2026-10-04 (U-D1): REQ-N-21 acceptance amended. "Unit round trips exact" cannot hold in float64: 25,126 of
200,000 random values in [-1e4, 1e4] did not survive `math.degrees(math.radians(x))` unchanged, with a worst error of
1 ulp (`verified (run)`, CPython 3.11.15, `random.seed(1)`, 2026-10-04). The criterion is now at most 2 ulp, the bound U-M1a's
UT-UNI-01 implements. The quantiser named in the row follows interfaces.md §1 (JS `Math.round` semantics, DEF-M1a-02).
No ID changed.

Revision 2026-10-05 (U-D2): REQ-N-21 names its continuity bound for every checker. Agent 4's instrument used 1e-9 mm
(`tests/independent/m1/continuity.py`) while this row, REQ-F-01, UT-GEO-01 and Xcoil's GEO-01 use 1e-6 mm; the
requirement bound wins (interfaces.md §5). The row also lists the new UT-GEO-22 and UT-GEO-23 (test_plan.md §5.1),
whose merged tests already carry the REQ-N-21 marker. No ID changed.

Revision 2026-10-05 (U-D3, D-016): REQ-F-34 now covers Xcoil's one-board-per-phase serpentine stack
(`stack_mode`, `board_gap_mm`; interfaces.md §2.2 and §5) and lists the new UT-GEN-05. REQ-F-19 says that a
generator returns a stack of one or more boards. Open question Q-3 is closed by D-016. No ID changed.

Revision 2026-10-08 (U-D4, D-031): REQ-F-24 is amended, because the user now enters the hole diameter (D-031a).
REQ-F-20 covers every phase count (D-031f). REQ-F-03, REQ-F-06, REQ-F-11 and REQ-F-20 list the new tests UT-GEO-24,
UT-GEO-25, UT-PHY-22 and UT-PHY-23 (test_plan.md §5.1). No ID changed.

Revision 2026-10-08 (U-D5, D-033g): REQ-F-03 lists the new test UT-GEO-26 for series layer pairs (test_plan.md §5.1).
No ID changed.

Revision 2026-10-12 (U-D13, D-034, D-042a): the Tests column of REQ-F-18, REQ-F-25, REQ-N-06 and REQ-T-05 lists the
M5 tests of test_plan.md §5.7. No statement, acceptance or ID changed.

Revision 2026-10-17 (U-D19, claude-sonnet-5-5; D-053b, D-054b, D-054c, D-054d; main b026fa3 read for every item).
The acceptance of REQ-F-03, REQ-F-05 and REQ-F-06 changes, REQ-N-10 is split, and REQ-N-29 is new. The Tests column
of REQ-F-05 gains UT-GEN-06, that of REQ-F-14 gains BV-21 and UT-DRC-09, and that of REQ-N-29 is TR-06. The three
new unit rows and TR-06 are in test_plan.md §5.1 and §5.7. The Tests columns of REQ-F-03, REQ-F-06 and REQ-N-10 are
unchanged.

- The acceptance of REQ-F-03 (b), REQ-F-05 and REQ-F-06 (b) follows `docs/phase3/engineering/pr14_and_reqf_texts.md` part 2
  (l.207-276) word for word. One typographic change: "k - 1" has an ASCII hyphen. One shared pair rotation builds, and
  pairs at two rotations return `UNBUILDABLE_PAIRS_ROTATED_APART` (`src/embodic/generators/spiral/generate.py` l.142-143,
  `verified` by reading). The Phase 1 build criterion for two rotations is withdrawn (D-054b). Tests:
  `test_m3_a_rotation_every_pair_shares_turns_the_whole_winding` (`tests/unit/generators/test_spiral_pairs.py` l.168)
  and `test_ut_geo_11_pairs_rotated_against_each_other_are_refused` (l.192).
- REQ-F-03 (d), option M4 (16/16, one phase per pair), moves to Phase 5 (D-054c). The spiral generator refuses a pair
  `phases` value today with `UNBUILDABLE_SPIRAL_OPTION_NOT_IMPLEMENTED` at `/winding/layers/pairs` (`generate.py` l.85
  and l.148, `verified` by reading). No test in `tests/unit/generators` pins that refusal (`not tested`; grep for
  `phases=` finds none). UT-GEO-19 stays in the Tests column as the Phase 5 test.
- REQ-F-05 states the formula and no totals, because the totals depend on Q, v and k. D-054d refuses every
  `vias_per_transition` other than 1 until Phase 5 (UT-GEN-06). The statement still says "an optional number of vias per
  transition", and whether it needs a Phase 5 qualifier is open for Fable.
- REQ-F-06 (b) drops the 1 % bound, because no percentage bound against the sharp length holds with fillets on
  (D-033a, D-054b). The reference is the G1 to G9 construction in `spiral_reference.py`, and the unit is relative.
- REQ-N-10 keeps its second clause (D-053b, U-D18 option B, `test_plan.md` §5.8.7): every REQ-ID has a test, and the
  matrix lists 0 untested live must rows (TR-01). Its disposition becomes `amended`. REQ-N-29 takes the coverage
  clause and moves it to Phase 5. REQ-N-29 is `should` as option B item 2 proposes, with the thresholds still an
  `assumption`. The milestone column allows M1 to M5 only, so REQ-N-29 shows M5. TR-01 skips a `should` row, so the
  value does not put the row into the M5 gate, and the acceptance names Phase 5. A Phase 5 value for the column is open
  for Fable. "Core" stays undefined, as it is in REQ-N-10. Option B item 4 (the matrix prints untested should and could
  rows) is not in the acceptance, because D-053b names the must half and `tools/trace_matrix.py` lists must rows only
  (l.144). It is open for Fable.
- REQ-T-05 is not reworded. Agent 4's U-V12b note (`tests/independent/m7/records/V3-01_gaps_b.md` l.143-153) asks for a
  failure of `tools/record_passed_tests.py` in the release profile, with exit 1 and the equation named, when a `verified`
  equation's only linked test ID is carried by no passing test. Today `record_main` exits 0 and prints the count of IDs
  carried by no test (`tests/unit/results/test_record_passed_tests.py` l.96 and l.116, `verified` by reading). The note also
  names the alternative: the acceptance says that the badge downgrade (`not tested`) is the mechanism. D-051e and D-053b
  cover requirement rows and `tools/trace_matrix.py`. Neither covers the test IDs of equations, so the choice between
  the two readings is open for Fable.

Revision 2026-10-17 (U-D20, claude-opus-5-5; D-055; main e68d5ff read for every item). The acceptance of REQ-T-05,
REQ-T-07 and REQ-L-01 changes. REQ-T-05 and REQ-L-01 become `amended`. No statement, ID or Tests column changes.

- REQ-T-05 (D-055b). The release gate fails, and the badge downgrade is not the mechanism. The predicate is
  `Registry.tests_passed` (`src/embodic/results/registry.py` l.150-153): the equation links at least one test and every
  linked test passed. The badge uses the same predicate through `test_state` (l.155-157), so the gate fails exactly
  when the shipped build would show a `verified` equation as `not tested`. D-055b says "has no linked test passing".
  For an equation with two linked IDs of which one passed, that reading lets the release pass and the badge drop, so
  this row takes the stricter predicate. The packaged registry has 11 `verified` equations, and each links 1 to 5 test
  IDs (`verified (run)`, `load_registry()` on main e68d5ff). TR-03 and TR-05 in test_plan.md §5.7 hold the test
  criteria.
- REQ-T-07 (DEF-UM7d-01). The project JSON gains `engine_version` and `registry_version`, and its format version
  becomes 2 (interfaces.md §9.1).
- REQ-L-01 (U-M7d L-01). "0 words outside the allow-list" needs an English word list, and the repository has none
  (test_plan.md LG-01). The new acceptance needs no data file. The character rule of LG-01 and LG-08 stays automatic.
  It admits ASCII and a short list of unit symbols and Greek letters only, so a word in Thai or in another non-Latin
  script cannot pass. A Latin-script word that is not
  English, for example a transliteration, passes the character rule. A reviewer's manual record covers that case, as
  for REQ-T-11 (test_plan.md §5.8.3). A probe of the non-docstring literals of `src` that hold a space found 1075
  distinct words (`verified (run)`, 2026-10-17; resources and templates not counted). An automatic word check needs a
  list such as SCOWL (Spell Checker Oriented Word Lists, http://wordlist.aspell.net/). Its licence was not read in
  this unit (`unresolved`), and adoption, a THIRD_PARTY_LICENSES.md entry and the data file are Fable's decision.

## 1. Functional requirements (REQ-F)

| ID | Disp. | Statement | Rationale | Prio | Acceptance | M | Owner module | Tests |
|---|---|---|---|---|---|---|---|---|
| REQ-F-01 | carried | The spiral generator shall build concentrated planar spiral coils per layer pair: X spirals inward to a centre via, Y spirals outward with mirrored artwork and the same circulation. | User decision (brief §1); A2-TOP §1.3, §4.1 | must | Phase 1 criteria (a) to (d): continuity 1e-6 mm, mirror 1e-9 mm, centre via 1e-9 mm, equal circulation. | M2 | embodic.generators.spiral | UT-GEO-01, UT-GEO-03, UT-GEO-04, UT-GEO-05, PR-03, PR-10 |
| REQ-F-02 | carried | The engine shall check 3-phase feasibility for any Q and 2p and assign phases and polarities by the star of slots with exact integer arithmetic. | EQ-08 `replace`; Xcoil belt-edge bug (A2-REV C6) | must | Phase 1 criteria (a) to (e): 12/10 and 12/16 patterns, 12/14, 24/14, 24/22, 24/26 balanced, 16/16 rule, k_w1 table. | M2 | embodic.winding | UT-WND-01, UT-WND-02, UT-WND-03, UT-WND-04, UT-WND-05, UT-WND-06 |
| REQ-F-03 | carried | The user shall configure multi-layer spiral windings: layer pairs, series chain of parallel groups, per-pair rotation and per-pair phase set. | A2-TOP §4.2 options M1 to M4; EQ-07 | must | Phase 1 criteria (a) and (c): M1 and M2 build; series EMF = phasor sum (1e-9 rel.). (b) One rotation pi/Q shared by every layer pair (option M3) builds a board whose path end points equal, within 1e-9 mm, those of the board built with first coil angle theta_0 + pi/Q and no pair rotation. Pairs at two different rotations, in series or in parallel, return Unbuildable with `UNBUILDABLE_PAIRS_ROTATED_APART` at `/winding/layers/pairs`. (d) Phase 5: option M4 (16/16, one phase per pair) is refused today with `UNBUILDABLE_SPIRAL_OPTION_NOT_IMPLEMENTED`; the build criterion moves to Phase 5. | M2 | embodic.generators.spiral | UT-GEO-10, UT-GEO-11, UT-GEO-19, UT-GEO-24, UT-GEO-26, UT-PHY-07 |
| REQ-F-04 | carried | The user shall define the stack-up as an explicit ordered list of copper and dielectric layers; copper z positions shall be derived from it. | A2-REV §1 `stackupFor`; gap G3 | must | z exact (UT-GEO-12); even-spacing helper equals Xcoil auto mode to 1e-12 mm (GR-07); board thickness = sum of layers. | M2 | embodic.model | UT-GEO-12, GR-07 |
| REQ-F-05 | amended | The spiral generator shall plan centre, transfer, terminal and ring vias as through vias, with an optional number of vias per transition; blind and buried vias are not built in Phase 2. | D-015 (through vias only); EQ-11 | must | The winding via count is Q·v·(2k + 1) for Q coils, v vias per transition and k series groups. Each coil has k centre vias, k - 1 transfer vias and 2 terminal vias (UT-GEO-13). Every through via clears foreign copper (PR-01). Via resistance uses the count per transition (UT-PHY-11). | M2 | embodic.generators.spiral | UT-GEO-13, UT-PHY-11, PR-01, UT-GEN-06 |
| REQ-F-06 | carried | The spiral generator shall support radial and parallel sides, arc, straight and stadium ends, a corner radius and moving inner turns. | A2-TOP §3.1; EQ-02 `replace` | must | Phase 1 criterion (a): D08 gives 3 loops (or 2 with eye limit reported). (b) With sharp corners, the track length of each coil layer equals the reference construction (`docs/phase2/engineering/checks/spiral_reference.py`) within 1e-6 relative. With fillets on, each corner's length change equals the closed form of G9 at the generator's `rho_used` within 1e-6 mm, and the total length equals the reference model's filleted length within 1e-6 relative (CF-11 at rho 0.5 mm: 362.6419 mm; CF-10 at rho 1.0 mm: 150.1692 mm). | M2 | embodic.generators.spiral | UT-GEO-07, UT-GEO-08, UT-GEO-09, UT-GEO-17, UT-GEO-18, UT-GEO-25, OR-04 |
| REQ-F-07 | carried | The rotor model shall support double, single-with-yoke and open single rotors, arc and block magnets, B_r, mu_r, thickness and air gap per side. | EQ-04, EQ-05 | must | Block alpha_p 0.853 / 0.547 / 0.402 at r = 18 / 28 / 38 mm (1e-3); 1-D limit to 1e-9 rel. | M2 | embodic.physics | UT-PHY-01, UT-PHY-02, UT-PHY-04, UT-PHY-14 |
| REQ-F-08 | carried | The engine shall build star (default), delta and open connections with phase rings and terminals U, V, W (+ optional N) and warn on delta with k_w3 not zero. | A2-TOP §3.4; EQ-09, EQ-19 | must | Ke,LL = sqrt(3) Ke,ph (star), = Ke,ph (delta); 12/14 delta raises RANGE_DELTA_TRIPLEN. | M2 | embodic.generators.spiral | UT-PHY-09, UT-WND-07 |
| REQ-F-09 | carried | The engine shall generate a board outline (circle or polygon with corner radius), a centre bore and screw holes. | Xcoil `buildMechanical` | should | Outline closed within 1e-9 mm; DXF outline end points shared by exactly two entities; copper-edge DRC applies. | M2 | embodic.geometry | UT-GEO-14, UT-DRC-06, UT-EXP-02 |
| REQ-F-10 | carried | The engine shall run DRC on the generated copper of every topology and report a violation whenever a computed clearance is below rule minus epsilon, epsilon at most 1e-6 mm, with no slack band. | D-006; Agent 4 DEF-01; D-051a | must | Phase 1 criteria (a) to (d): default spiral passes and packs within rule + 0.005 mm; brute-force soundness; 1 um intrusion detected; Xcoil values within 1e-6 mm. | M1 | embodic.drc | UT-DRC-01, UT-DRC-02, UT-DRC-03, UT-DRC-04, UT-DRC-05, UT-DRC-08, PR-01, PR-02, PR-13, GR-18 |
| REQ-F-11 | carried | The engine shall compute the quantities of Agent 2's equation list for every topology and label EQ-14, EQ-15 and EQ-20 results as estimates. | EQ-01 to EQ-22, gate summary | must | (i) registry reference cases and golden dumps within tolerance; (ii) FEA and oracle validation `xfail` until references exist (Phase 1 split, DEF-10). | M2 | embodic.physics | UT-PHY-05, UT-PHY-06, UT-PHY-10, UT-PHY-12, UT-PHY-15, UT-PHY-16, UT-PHY-17, UT-PHY-18, UT-PHY-19, GR-02, GR-03, GR-04, GR-09, GR-11, GR-13, OR-01, OR-11, OR-12, UT-PHY-22, UI-07 |
| REQ-F-12 | carried | The engine shall evaluate the field at each copper layer's z and report per-layer and per-pair results and the circulating loss of parallel members. | Gap G3; EQ-05 to EQ-07 | must | C1d per-layer B1 spread 1e-4 rel.; two-member identity to 1e-12. | M2 | embodic.physics | UT-PHY-08, UT-PHY-20, GR-05 |
| REQ-F-13 | carried | The desktop UI shall show the 2-D geometry (zoom, pan, layer visibility, phase identification), the phase assignment, the layer configuration and the results with value, unit and status. | User wish; Agent 1 screens | must | Each view reachable in at most 2 interactions; zoom 0.1x to 200x keeps stroke widths. | M4 | embodic.ui.views | UI-02, UI-03, UI-04, UI-06 |
| REQ-F-14 | amended | The engine shall classify every input problem as missing, invalid, unsupported range or unbuildable and return issues with stable code, severity, message, pointers, value, limit and hint; it shall never raise or return NaN or infinity for user input. | Phase 1 F-14 plus MISSING category for the new-design flow (D-014) | must | 1000 seeded random parameter sets per generator: 0 uncaught exceptions, 0 non-finite results; every BV case gives its documented code. | M2 | embodic.model | PR-05, BV-01, BV-02, BV-03, BV-05, BV-06, BV-21, UT-DRC-09, UI-14 |
| REQ-F-15 | amended | The user shall save and load designs and incomplete drafts as a versioned JSON project file with per-field provenance and a canonical design hash. | ADR-0007; D-014 drafts | must | Save, load, save is byte-identical; draft round trip keeps missing fields missing; hash changes iff a design field changes. | M2 | embodic.io | UT-IO-01, UT-IO-02, UT-IO-03, UT-IO-04, UT-IO-07, PR-08 |
| REQ-F-16 | amended | The application shall export SVG, DXF (complete board, outline only, screws only), the JSON project file, a PDF report and a README, all generated from one Layout. | D-009 (no .kicad_pcb); Xcoil export set (ui-main.js l.30) | must | Independent parsers open every export (ezdxf audit 0 errors, pypdf at least 1 page with "Key results", SVG parses); entity counts equal the Layout's counts. | M4 | embodic.io | UT-EXP-01, UT-EXP-02, UT-EXP-03, UT-EXP-04, UT-IO-06 |
| REQ-F-17 | carried | The user could compare two or more designs side by side. | Xcoil `compareResults` | could | Comparison values identical to the single-design results. | M4 | embodic.ui.views | UI-10 |
| REQ-F-18 | amended | A headless CLI shall compute, validate and export from a project file: `embodic-cli compute <project.embodic.json>` with exit codes 0 ok, 1 validation or missing fields, 2 DRC errors, 3 internal error. | Testability; brief U-S1 | must | `compute --json` output equals `outcome_to_json(compute_project(path))`; an incomplete draft exits 1 and lists the missing pointers; export with DRC errors needs `--allow-drc-errors`. | M5 | embodic.cli | UT-CLI-01, UT-CLI-02, UT-CLI-03 |
| REQ-F-19 | amended | The spiral, serpentine and wave generators shall share one plug-in interface: each maps DesignParameters to a BoardStack of one or more Layouts (copper, vias, pads, outline, electrical element list per board) or Unbuildable, and DRC, physics and exporters shall work on any Layout without topology branches. | D-013; ADR-0012 | must | A stub generator registered in a test passes DRC, analysis and all exporters unchanged; the C1 layer order forbids physics, DRC, io and outcome to import generators. | M2 | embodic.generators | UT-GEO-20, UT-GEN-01, UT-GEN-02, MT-01 |
| REQ-F-20 | carried | The engine could compute a torque-speed envelope, shown only as an `unresolved` estimate. | EQ-20 `cannot verify yet`; any phase count (D-031f) | could | Badge `unresolved`, label "estimate"; None without a DC link voltage; one-, two- and three-phase designs get an estimate. | M2 | embodic.physics | UI-07, UT-RES-02, UT-PHY-23 |
| REQ-F-21 | amended | The application shall open with no design loaded; it shall offer "New design" and "Examples", and shall show an "Example" provenance chip on every field whose value comes from a loaded example. | D-014 replaces "load the default design at start" | must | Fresh start shows the empty session; loading an example shows the chip on every field; editing removes it; setting the value back restores it; badges never change. | M4 | embodic.ui.viewmodels | UI-22, UI-23, PR-12 |
| REQ-F-22 | amended | The UI should provide undo and redo for parameter edits, suggestion applications and example loads. | Usability; REQ-F-23 needs Undo | should | 50-step undo restores the identical design hash and provenance map. | M4 | embodic.ui.viewmodels | UI-11, UT-SES-02 |
| REQ-F-23 | carried | The engine shall never change an input; the UI may apply a suggestion only with an inline notice and Undo. | Agent 1 C2, UX-AC-13 | must | Scripted clamp case shows old and new value with Undo; Undo restores value and hash; the engine never returns modified DesignParameters. | M4 | embodic.ui.viewmodels | UI-15 |
| REQ-F-24 | amended | The engine should place screw holes of the diameter the user enters for each pattern, with edge, pitch and copper keep-out checks. | Xcoil F-20; D-031a: no cited fastener table yet, ISO 273 values only as labelled examples after U-S3b | should | Holes at the specified radius, count and `hole_diameter_mm`; violations reported as DRC_COPPER_HOLE. | M2 | embodic.geometry | UT-GEO-21 |
| REQ-F-25 | amended | The application should ship the team's parameter sets only as examples: the default 12/16 spiral, the D08 and D09 oracle configurations, one serpentine and one wave example. | D-014 (team values are examples) | should | Each example loads, validates and computes without an ERROR issue; oracle tests use the same files. | M4 | resources/examples | UI-16, UT-IO-08, UT-SLF-01, UT-SLF-02, UT-SLF-03, UI-35 |
| REQ-F-26 | carried | The application should provide an equation reference view generated from the registry, linked from every result. | Agent 3 F-60; Agent 1 C4 | should | Every EQ-ID link opens its entry; the view content equals the registry JSON. | M4 | embodic.ui.views | UI-17 |
| REQ-F-27 | carried | The UI should keep the last valid geometry visible, marked as outdated, while the input is invalid or unbuildable. | Agent 1 W1 | should | Invalid input keeps the previous drawing marked "outdated" with the cause listed. | M4 | embodic.ui.viewmodels | UI-18 |
| REQ-F-28 | carried | The UI should show feasibility hints next to inputs. | Agent 1 W3; Agent 3 F-40 | should | Hints match the generator detail and Feasibility after each recompute. | M4 | embodic.ui.views | UI-19 |
| REQ-F-29 | amended | The application should export a ZIP bundle of the selected exports with README.txt, and could import Xcoil v3 parameter JSON for comparison. | Xcoil F-55, F-57; D-009 export list | should | The bundle holds every selected file plus README.txt; the import maps existing fields and reports dropped ones. | M4 | embodic.io | UT-EXP-05 |
| REQ-F-30 | carried | The geometry view could show a rotor-angle overlay of the magnets. | Xcoil F-45 | could | The overlay rotates with the slider and triggers no recompute. | M4 | embodic.ui.views | UI-20 |
| REQ-F-31 | carried | The desktop UI should autosave a recovery file in the user profile and remember the last project path. | Agent 3 F-04 | should | Kill after an edit: next start offers recovery with an identical hash (drafts included). | M4 | embodic.ui.app | UI-21 |
| REQ-F-32 | carried | Inputs that do not apply to the current topology or configuration shall be hidden; a temporarily inapplicable input shall show the reason. | Agent 1 UX-AC-12; Xcoil defect C1 | must | Configuration-matrix test driven by the field table (`field_specs`) for all three topologies. | M4 | embodic.ui.views | UI-28, UT-MOD-03 |
| REQ-F-33 | amended | Exporting a layout with DRC errors shall require an explicit confirmation that lists the failures, with initial focus on Cancel. | Agent 1 UX-AC-16; KiCad placement removed (D-009) | must | Scripted export with an injected DRC error shows the dialog focused on Cancel; the CLI needs `--allow-drc-errors`. | M4 | embodic.ui.views | UI-29, UT-EXP-05, UT-CLI-01 |
| REQ-F-34 | new | The serpentine generator shall be a faithful port of Xcoil v3's serpentine builder (one board or one board per phase with a board gap, 1 to 3 phases, series or parallel pairs, grouped or interleaved layer order). | D-013; D-016 (one board per phase, revision 2026-10-05) | must | Layout-level golden regression on the committed case set, board by board for a per-phase stack: equal primitive, via and pad counts, sampled path distance at most 1e-6 mm, DRC values within 1e-6 mm with the D-006 band rule; function-level cases for every ported helper; a per-phase stack has one board per phase at the Xcoil z offsets and no cross-board DRC pair. | M3 | embodic.generators.serpentine | GR-20, GR-23, UT-GEN-03, UT-GEN-05, PR-13, PR-14 |
| REQ-F-35 | new | The wave generator shall be a faithful port of Xcoil v3's interleaved wave builder in the styles involute, jog, chord and overlap. | D-013; reference board is a wave winding (A2-TOP K1) | must | Layout-level golden regression per style with the GR-20 criteria; EMF and resistance on the same copper compared with Xcoil (GR-22, tolerance set by Agent 2 and 4). | M3 | embodic.generators.wave | GR-21, GR-22, GR-23, UT-GEN-04, PR-13, PR-14 |
| REQ-F-36 | new | "New design" shall create a blank draft for the chosen topology in which every required field is empty and nothing is computed until all required fields have values. | D-014 | must | A blank draft has 0 required values and triggers 0 computes; filling the last required field triggers exactly one compute. | M4 | embodic.model | UT-MOD-01, UI-24, UT-SES-01 |
| REQ-F-37 | new | The engine shall validate a draft field by field and list every missing required field, in form order, separately from invalid values. | D-014 | must | `parse_draft` returns DraftIncomplete with the exact missing pointer list for each topology's field table; present fields get INVALID issues; complete drafts round-trip through `draft_from_design`. | M2 | embodic.model | UT-MOD-01, UT-MOD-02, UT-MOD-03 |
| REQ-F-38 | new | Examples shall be labelled "Example" wherever they appear, shall load as a new unsaved design whose fields carry `example` provenance, and shall never be overwritten by Save. | D-014; D-041a, D-041b | must | The `example` provenance chip marks every field loaded from an example and the Examples gallery names the list, so a title does not need the word "Example" (D-041a). The design `/name` of each packaged example equals its display title (D-041b). First Save after loading an example opens Save As; every field's provenance after load is `example`. | M4 | embodic.ui.viewmodels | UI-22, UT-IO-08 |
| REQ-F-39 | new | The desktop UI shall provide a MATLAB-style tabbed toolstrip in which every action has an original monochrome SVG icon, an English label, a tooltip and an accessible name, and is keyboard reachable. | D-012 | must | Every TOOLSTRIP entry resolves its command and icon file; arrow keys move within a tab; icons recolour with the theme. | M4 | embodic.ui.views | UI-25, AX-09 |
| REQ-F-40 | new | The engine shall write any Layout as an `embodic.board-dump` v1 JSON file for the golden harness and Agent 4's independent checks. | Agent 3 port notes §7.5; Agent 4 request | must | embodic and Xcoil dumps parse with one reader; write, read, write is identical; non-finite values encoded. | M1 | embodic.io | GR-19 |

## 2. Non-functional requirements (REQ-N)

| ID | Disp. | Statement | Rationale | Prio | Acceptance | M | Owner module | Tests |
|---|---|---|---|---|---|---|---|---|
| REQ-N-01 | carried | A full recompute of the default spiral design shall take less than 1.0 s (p95 of 20 warm runs) on the reference laptop. | Phase 1 measurement M-JS and Agent 3 kernel timings; threshold `assumption` | must | PF-01 with stage budgets geometry 0.2 s, DRC 0.4 s, physics 0.3 s; stays `assumption` until run on the user's laptop. | M5 | embodic.api | PF-01, PF-04 |
| REQ-N-02 | carried | The UI shall stay responsive during computation (input echo below 100 ms, 300 ms debounce, background worker, latest edit wins). | Agent 1 design spec §7.5 | must | Latency probe during a 3 s synthetic compute; UX-AC-22 timing. | M4 | embodic.ui.workers | UI-05, UI-02 |
| REQ-N-03 | carried | A large design (24 coils, 12 copper layers, 6 series pairs) should recompute in less than 5 s. | Headroom; `assumption` | should | PF-02 on the reference laptop. | M5 | embodic.api | PF-02 |
| REQ-N-04 | carried | Results shall be deterministic: byte-identical JSON on one platform, 1e-9 rel. across Windows, Linux and Python 3.11 to 3.13. | Golden regression; Python 3.12 sum() change; D-051f | must | Same-platform byte identity of the outcome JSON. Cross-platform, PK-04 compares each array of the outcome JSON at 1e-9 relative to the largest absolute value in that array, every other float at 1e-9 relative, and `design_hash` exactly. `layout_hash` and `stack_hash` are same-platform identities, and PK-04 leaves them out. No built-in sum() over floats in physics and DRC. | M2 | embodic.physics | PR-09, PK-04, MT-06 |
| REQ-N-05 | carried | Core and CLI shall run on Windows 10/11 x64 and Linux x86-64 with CPython 3.11, 3.12 and 3.13; the desktop UI on Windows (must) and Linux (should). | User has Python 3.11+ (brief §1); NumPy 2.4.x is the last line for 3.11 | must | CI matrix green; clean Python 3.11 venv resolves. | M5 | pyproject.toml | PK-01, PK-02 |
| REQ-N-06 | amended | Installation shall be reproducible: `pip install embodic` (core and CLI), extra `embodic[desktop]`, lock files with hashes per Python version, and a documented PyInstaller one-folder build attempt. | D-015 (pip/venv; bundle is a stretch goal); KiCad extra removed (D-009) | must | Two wheel builds give identical file lists and `.py` hashes; the bundle smoke test runs if the stretch unit lands. | M5 | pyproject.toml | PK-03, PK-05, PK-10, PK-11 |
| REQ-N-07 | amended | An English README and install guide shall give exact install, run, test and package commands for Windows PowerShell and Linux; Fable provides the Thai install guide from it; a new user with Python 3.11 shall reach a first computed example in less than 10 minutes. | User wish; brief §5 M5 (Thai guide); standing order 1 (only Fable writes Thai) | must | Timed walkthrough on a clean Windows machine by Agent 4 or the user. | M5 | docs | PK-06 |
| REQ-N-08 | amended | Engine packages and view-models shall not import Qt; public functions shall be fully typed; mypy strict on the core; ruff clean; McCabe at most 10; modules at most 600 lines unless justified. | Engine purity (D-004 rule kept in D-009); testable view-models | must | import-linter contracts C1 to C4, mypy --strict, ruff: 0 findings. | M1 | pyproject.toml | MT-01, MT-02, MT-03 |
| REQ-N-09 | carried | Every public function and dataclass shall have a docstring stating purpose, units, assumptions, validity limits and EQ-IDs. | User wish; brief rule 2 | must | Docstring checker: every physics function names units and an EQ-ID. | M2 | embodic.physics | MT-04 |
| REQ-N-10 | amended | Every REQ-ID shall have at least one automated test or documented manual test. | Linked requirements and tests; coverage clause split off as REQ-N-29 (D-053b) | must | Matrix generator lists 0 untested live must REQs (TR-01). | M2 | tools/trace_matrix.py | TR-01 |
| REQ-N-11 | carried | Colour contrast shall meet WCAG 2.2 AA in both themes: text at least 4.5:1, UI components and graphics at least 3:1. | WCAG 2.2 SC 1.4.3, 1.4.11 | must | Contrast script over every token pair of light and dark themes: 0 failures. | M4 | resources/themes | AX-01 |
| REQ-N-12 | carried | All functions shall be operable by keyboard with a visible focus indicator, region cycling with F6 and a focusable canvas. | WCAG 2.2 SC 2.1.1, 2.4.7, 2.4.11; Agent 1 keyboard map | must | Keyboard-only scenario; focus ring on every stop; Tab order equals visual order. | M4 | embodic.ui.views | AX-02, AX-03 |
| REQ-N-13 | carried | Pointer targets shall be at least 24 x 24 device-independent px at 100 % scaling. | WCAG 2.2 SC 2.5.8 | must | Widget enumeration checks clickable areas. | M4 | embodic.ui.views | AX-04 |
| REQ-N-14 | carried | Colour shall not be the only means of conveying phase, polarity, layer or status. | WCAG 2.2 SC 1.4.1; D-011 mitigation rule | must | Greyscale and deuteranopia renders: a reviewer identifies phase and polarity of 12 coils with 100 % accuracy. | M4 | embodic.ui.views | AX-05 |
| REQ-N-15 | carried | The desktop UI shall work from a 960 x 540 px window to full screen with three or two panes as specified. | Agent 1 breakpoints | must | Screenshots at three sizes and three scalings: no clipping, no overlap, no horizontal scroll in forms. | M4 | embodic.ui.views | UI-09 |
| REQ-N-16 | carried | Controls, results and status labels shall expose accessible names, roles and error states. | Qt accessibility; Agent 1 UX-AC-14 | must | Narrator check: inputs announce label, value, unit; results announce value, unit, status. | M4 | embodic.ui.views | AX-06 |
| REQ-N-17 | amended | The application shall work fully offline and shall not open any network connection. | Privacy; KiCad IPC socket removed (D-009) | must | Full suite passes with network disabled; no HTTP client import in src. | M5 | embodic | PK-07 |
| REQ-N-18 | carried | Unexpected internal errors shall be caught at the adapter, logged with a correlation ID and shown as an English message offering to save. | Robustness | must | Fault injection: message shown, project or draft saved, process alive. | M4 | embodic.ui.app | UI-12 |
| REQ-N-19 | carried | Every dependency shall have a recorded licence compatible with the embodic licence; no code from GPL references shall be copied. | Brief rule 7; D-003 | must | Licence report matches the allow-list in package_layout.md §5; THIRD_PARTY_LICENSES complete. | M5 | pyproject.toml | PK-08 |
| REQ-N-20 | carried | The application should write a rotating log without personal data. | Supportability; standing order 7 | should | Log holds no user name or home path; rotation 1 MB x 5 (`assumption`). | M4 | embodic.ui.app | UT-LOG-01 |
| REQ-N-21 | amended | Geometry shall use float64 and a coincidence tolerance of 1e-6 mm; writers that emit fixed decimals shall quantise connected end points from one shared coordinate with `embodic.units.quantise`. | Xcoil GEO-01; nm conversion removed with KiCad (D-009); Xcoil `fmt()` engine.js l.2762 | must | Every continuity check uses the gap bound 1e-6 mm (`COINCIDENCE_MM`, also Agent 4's IT-21; revision 2026-10-05); continuity holds after SVG and DXF quantisation; unit round trips within 2 ulp of the input (`math.ulp`); `js_round` equals JS `Math.round` on ties of both signs (revision 2026-10-04); transforms and discretisation meet UT-GEO-22 and UT-GEO-23. | M1 | embodic.geometry | UT-GEO-01, UT-GEO-22, UT-GEO-23, UT-UNI-01, UT-EXP-02 |
| REQ-N-22 | carried | Cold start to an interactive window could take less than 3 s. | Usability; `assumption` | could | PF-03. | M5 | embodic.ui.app | PF-03 |
| REQ-N-23 | carried | The geometry view and all phase legends shall offer a greyscale and hatch mode (lightness, hatch 0/45/135 deg inside the coil eye only, labels); it is the PDF default and is used under Windows high contrast. | Agent 1 UX-AC-05; D-011 | must | Greyscale screenshot; forced-colours run; hatch never crosses copper. | M4 | embodic.ui.views | UI-27, AX-05 |
| REQ-N-24 | carried | Every input shall show its unit and include it in its accessible description. | Agent 1 UX-AC-15; Xcoil gap A3 | must | Widget scan driven by the field table. | M4 | embodic.ui.views | AX-06, UT-MOD-03 |
| REQ-N-25 | carried | Charts shall use one unit per y axis, a legend plus direct labels, a data-table alternative and the status badge of the plotted quantity. | Agent 1 UX-AC-18 | must | Chart audit. | M4 | embodic.ui.views | UI-30 |
| REQ-N-26 | carried | No animation shall run by default; the OS reduce-animation setting shall disable all transitions. | Agent 1 UX-AC-20 | should | Emulated OS setting shows no transitions. | M4 | embodic.ui.views | UI-31 |
| REQ-N-27 | new | The desktop UI shall ship complete light and dark themes with white, grey and black chrome, selectable as light, dark or follow the system, switchable at runtime and remembered. | D-011 (both themes in Phase 2) | must | Every token exists in both theme files; runtime switch restyles every widget; the choice persists across restarts. | M4 | embodic.ui.theme | UI-26, AX-01 |
| REQ-N-28 | new | Phases A, B and C shall render red, blue and green in the geometry view and charts, always paired with labels, line style and the optional hatch; both theme palettes shall pass the colour-vision check Agent 1 used for tokens.json. | D-011; Agent 1 CVD risk note | must | Phase colours at least 3:1 against the canvas in both themes; the palette validator passes for both themes; labels present in colour and greyscale modes. | M4 | embodic.ui.theme | AX-08, UI-27 |
| REQ-N-29 | new | Core coverage shall be at least 90 % lines and 80 % branches. | Coverage clause of the Phase 1 REQ-N-10, split off in D-053b; thresholds `assumption` | should | Phase 5. The release gate runs pytest with coverage and branch data. `tools/coverage_check.py` exits 1 when the covered statements are below 90 %, when the covered branches are below 80 %, or when the branch figure is missing (TR-06). | M5 | tools/coverage_check.py | TR-06 |

## 3. KiCad requirements (REQ-K), all withdrawn

D-009 removes the plugin, the smoke tests and the `.kicad_pcb` export. The engine stays UI-agnostic, so a later phase can
re-open these IDs. MT-07 fails the build if KiCad code, imports, export options or user-facing "KiCad" strings appear.

| ID | Disp. | Statement | Rationale | Prio | Acceptance | M | Owner module | Tests |
|---|---|---|---|---|---|---|---|---|
| REQ-K-01 | withdrawn | Withdrawn: `.kicad_pcb` export. | D-009 | - | - | - | - | MT-07 |
| REQ-K-02 | withdrawn | Withdrawn: KiCad 9 IPC plugin. | D-009 | - | - | - | - | MT-07 |
| REQ-K-03 | withdrawn | Withdrawn: stack-up import from KiCad. | D-009 | - | - | - | - | MT-07 |
| REQ-K-04 | withdrawn | Withdrawn: re-apply replaces only embodic items. | D-009 | - | - | - | - | MT-07 |
| REQ-K-05 | withdrawn | Withdrawn as a KiCad rule; the import ban on `kipy` and `pcbnew` stays in MT-07. | D-009 | - | - | - | - | MT-07 |
| REQ-K-06 | withdrawn | Withdrawn: KiCad version check. | D-009 | - | - | - | - | MT-07 |
| REQ-K-07 | withdrawn | Withdrawn: plugin venv dependencies. | D-009 | - | - | - | - | MT-07 |
| REQ-K-08 | withdrawn | Withdrawn: mm to nm conversion (REQ-N-21 amended). | D-009 | - | - | - | - | MT-07 |
| REQ-K-09 | withdrawn | Withdrawn: KiCad nets per electrical node. | D-009 | - | - | - | - | MT-07 |
| REQ-K-10 | withdrawn | Withdrawn: launcher from the plugin. | D-009 | - | - | - | - | MT-07 |
| REQ-K-11 | withdrawn | Withdrawn: no SWIG dependency (nothing KiCad remains). | D-009 | - | - | - | - | MT-07 |
| REQ-K-12 | withdrawn | Withdrawn: kicad-cli DRC. | D-009 | - | - | - | - | MT-07 |
| REQ-K-13 | withdrawn | Withdrawn: PCM licence rule. | D-009; D-015 (no PCM listing) | - | - | - | - | MT-07 |
| REQ-K-14 | withdrawn | Withdrawn: no silent layer remap on placement. | D-009 | - | - | - | - | MT-07 |
| REQ-K-15 | withdrawn | Withdrawn: compact plugin window. | D-009 | - | - | - | - | MT-07 |
| REQ-K-16 | withdrawn | Withdrawn: plugin report file. | D-009 | - | - | - | - | MT-07 |

## 4. Traceability and evidence display (REQ-T)

| ID | Disp. | Statement | Rationale | Prio | Acceptance | M | Owner module | Tests |
|---|---|---|---|---|---|---|---|---|
| REQ-T-01 | carried | Every displayed number shall show value, unit, one status badge, the "n assumed inputs" tag and an EQ-ID link or kind tag, with details reachable in one interaction. | D-007; Agent 1 UX-AC-01/02 | must | Each result row has unit and badge; EQ link or tag; keyboard reachable details. | M4 | embodic.ui.views | UI-06, AX-02 |
| REQ-T-02 | carried | Every computed result shall be a Traceable carrying value, unit, quantity, EQ-IDs or kind tag, evidence IDs, assumptions, inputs and status; the UI takes status from data only. | ADR-0003 | must | Walk all AnalysisResult fields for every example: no bare float; all IDs resolve. | M2 | embodic.results | UT-RES-01 |
| REQ-T-03 | carried | The badge shall express calculation trust only (weakest of equation status, test state, validity cap); assumed inputs appear only in the tag. | D-007; DEF-02 | must | Truth table; tag lists exactly the assumed inputs used. | M2 | embodic.results | UT-RES-02, UT-RES-05 |
| REQ-T-04 | carried | The application shall ship the equation and evidence registries and every shown ID shall resolve. | A2-EQ, A5-REG | must | Registry integrity: no dangling EQ or EV IDs. | M2 | embodic.results | UT-RES-03, TR-04 |
| REQ-T-05 | amended | `cannot verify yet` equations shall give only `unresolved` estimates; an equation shows `verified` only with a linked test passing in this build. | Gate vocabulary; D-055b | must | CI fails when a `verified` EQ lacks a passing linked test: in the release profile, `record_main` of `tools/record_passed_tests.py` exits 1, writes no evidence file and names on stderr every equation of status `verified` for which `Registry.tests_passed` is false with the registry test IDs that passed in the run, because it links no test or one of its linked IDs did not pass (revision 2026-10-17, U-D20). | M2 | embodic.results | TR-03, UT-RES-02, UT-RES-08, UT-RES-09, TR-05 |
| REQ-T-06 | amended | Every input shall carry a provenance `user`, `example` or `measured`; `measured` shall be accepted only for property fields with a named source, and only it retires the field's assumption label. | D-007; D-014 vocabulary | must | Marking B_r measured with a source removes it from the tag; without a source or on a design field it is refused. | M2 | embodic.model | UT-RES-06, UT-MOD-05 |
| REQ-T-07 | amended | Every export shall contain the embodic version, engine version, registry version, design hash, generation date and the status labels of reported values. | Reproducibility | must | Metadata present in SVG `<metadata>`, DXF header comment, project JSON, PDF and README. The project JSON holds the top-level keys `app_version`, `engine_version`, `registry_version`, `design_hash` and `saved_utc` (interfaces.md §9.1, revision 2026-10-17, U-D20). | M4 | embodic.io | UT-IO-06 |
| REQ-T-08 | amended | Equation validity limits shall be evaluated and shown next to affected results; graded checks follow the registry `validity_checks`, with EC-05 labelled per REQ-T-16. | EQ-13 threshold, EC-05 (DEF-18, DEF-23) | must | w above delta/3 raises RANGE_SKIN_DEPTH and marks R and eddy results; EC-05 values within 0.1 pp of Agent 2. | M2 | embodic.physics | UT-PHY-13, UT-PHY-21 |
| REQ-T-09 | carried | Every automated test shall declare its REQ-IDs with a pytest marker, and CI shall generate the requirements-to-tests matrix. | User wish | must | 0 tests without REQ marker; 0 live must-REQs without a test. | M1 | tools/trace_matrix.py | TR-01, TR-02 |
| REQ-T-10 | carried | Computed values shall never be called "measured". | Brief rule 5 | must | Wording scan of strings and templates. | M4 | embodic.ui.strings | LG-03 |
| REQ-T-11 | carried | The UI shall not claim balance, torque or efficiency from geometry or phase angles alone. | Brief rule 6 | must | Wording scan and reviewer check. | M4 | embodic.ui.strings | LG-04 |
| REQ-T-12 | carried | Oracle comparisons should be viewable with paper reference, page and tolerance; this may slip to Phase 3 with Fable's approval. | A5-REG §C | should | O1 and O2 rows show source and tolerance; OR-07 and OR-08 flagged as not independent of EC-05. | M4 | embodic.ui.views | UI-13 |
| REQ-T-13 | carried | Each result shall have a "How was this computed" disclosure with equation, inputs (with provenance), assumptions, validity flags, validation and sources, plus "Copy trace". | Agent 1 UX-AC-02 | must | Content check per result row. | M4 | embodic.ui.views | UI-06 |
| REQ-T-14 | carried | Drawings not produced by the engine shall carry "Illustrative, not computed"; engine drawings and exports shall carry the version stamp and design hash. | Agent 1 UX-AC-17 | must | Widget and file-content check. | M4 | embodic.io | UT-IO-06, UI-32 |
| REQ-T-15 | new | Provenance shall be derived from values: `example` while a field equals the value in the design's origin example, `measured` for marked property fields, `user` otherwise; it shall be saved per field and checked on load. | D-007 value rule; D-014; ADR-0010 | must | Truth table over origin, value and measurement; re-entry invariance; back-to-example restores `example`; load reports a mismatch with the packaged example. | M2 | embodic.model | UT-MOD-04, UT-IO-07, PR-12 |
| REQ-T-16 | new | EC-05 shall be labelled as follows: e_edge is a lower bound with status `assumption` (calibration `inferred` from one D09 case, transfer to the current rotor `assumption`), the 10 % cap is an `assumption`, and OR-07 and OR-08 are marked as dependent on the calibration source. | DEF-23 (Agent 4); EC-05 registry entry | must | The registry entry carries the four fields of ValidityCheckSpec; the e_edge Traceable has status `assumption`; the disclosure says "at least"; OR-07/OR-08 carry the dependency note. | M2 | embodic.results | UT-RES-07, UI-33 |

## 5. Language and branding (REQ-L)

| ID | Disp. | Statement | Rationale | Prio | Acceptance | M | Owner module | Tests |
|---|---|---|---|---|---|---|---|---|
| REQ-L-01 | amended | All software-facing text shall be English. | Brief rule 8; standing order 1; D-055 | must | Scan finds 0 Thai characters in src, resources and templates (LG-08), and 0 string literals in `src` with a character outside printable ASCII, tab, newline, the allowed unit symbols and the symbols that `MODULE_SYMBOLS` admits for the module (LG-01). A manual record (interfaces.md §3.2) names the reviewer who read the sorted list of distinct words of the string catalogues and report templates that LG-01 prints, and found no word that is not English (revision 2026-10-17, U-D20). | M4 | embodic.ui.strings | LG-01, LG-08 |
| REQ-L-02 | amended | UI strings should be defined in per-area catalogue modules under `embodic.ui.strings`, not inline in widget code. | Reviewability; one catalogue file per unit avoids shared writes | should | AST lint: no string literal passed to a widget text setter outside the catalogue. | M4 | embodic.ui.strings | LG-02 |
| REQ-L-03 | carried | The product name shall be "embodic"; "Xcoil" shall not appear in user-facing text or outputs. | Brief §1 | must | 0 occurrences in strings, exports and report. | M4 | embodic.ui.strings | LG-05 |
| REQ-L-04 | amended | UI chrome shall be white, grey and black in both themes; red, blue and green are reserved for phases A, B, C and status semantics, always with a non-colour cue. | D-011 | must | Contrast check, greyscale test and token review. | M4 | resources/themes | AX-01, AX-05, AX-08 |
| REQ-L-05 | carried | Brand assets shall be used unmodified; no personal data shall appear in code, UI, logs or outputs. | Brief §2; standing order 7 | must | Asset checksums; personal-name scan = 0. | M4 | resources/icons | LG-06 |
| REQ-L-06 | carried | Engineering terms should follow one English glossary. | Consistency | should | Glossary check of the catalogue. | M4 | embodic.ui.strings | LG-07 |
| REQ-L-07 | carried | Number formatting shall be locale-independent with SI units, a space before the unit, 3 significant figures and the minus sign U+2212. | Agent 1 §13 | must | Identical output under German and Thai locale settings. | M2 | embodic.results | UT-UNI-03 |
| REQ-L-08 | carried | Counts shall be integers; comparison deltas shall use sign and glyph, never red or green alone. | Agent 1 UX-AC-19 | must | Formatting test. | M4 | embodic.ui.views | UI-34 |
| REQ-L-09 | amended | UI spelling shall be British ("centre", "colour"). | D-015 | should | Spelling check against the British list. | M4 | embodic.ui.strings | LG-07 |

## 6. DEF-23 closure: how EC-05 is labelled

Agent 4's DEF-23 found four labelling gaps in EC-05 (`docs/phase1/verification/defect_list.md` l.104). This contract
closes it as follows. Agent 2 owns the registry text; the fields below are the schema Agent 2 fills.

| DEF-23 item | Registry (`validity_checks` entry of EQ-05, `ValidityCheckSpec`) | Runtime (`ValidityFlag`, `Traceable`) | UI and report |
|---|---|---|---|
| (a) calibration quantity is the magnitude of B, so e_edge is probably a lower bound | `metric_bound: "lower_bound"`; `basis` names D09 Fig. 7 magnitude as the proxy | `ValidityFlag.metric_bound = LOWER_BOUND` | add-on text "model may be high by at least e_edge" |
| (b) transfer to other rotors is untested | `calibration_status: "inferred"` (one case), `transfer_status: "assumption"` | `edge_leakage_fraction` Traceable has status `assumption`; the transfer appears in every affected result's assumed-inputs tag as an equation assumption ("EC-05 calibration transferred to this rotor") | disclosure lists the calibration case and the word "assumption" |
| (c) threshold basis | `threshold: 0.10`, `threshold_status: "assumption"`; Agent 2 decides 10 % or 8 % (Q-4) | `ValidityFlag.threshold_status = ASSUMPTION` | "cap at 10 % (assumption)" next to the metric |
| (d) independent oracle | `independent_oracles: ["OR-01"]`, `dependent_oracles: ["OR-07", "OR-08"]` | not used at runtime | oracle view (REQ-T-12) and test report mark OR-07 and OR-08 "not independent of EC-05" |

The badge rule does not change: below the cap EC-05 adds a limitation and a one-sided tolerance, above it the badge is
capped at `unresolved` (DEF-18 resolution).

## 7. Open questions for Fable

- Q-1. Serpentine and wave examples: which parameter sets ship as examples (REQ-F-25)? Proposal: one Xcoil v3 preset per
  topology with its Xcoil name removed, labelled `assumption`. Agent 2 to confirm.
- Q-2. GR-22: if Xcoil's serpentine `analyze` path and the generic element path disagree on the same copper, which one
  is the golden reference? Proposal: the generic path, with the serpentine path difference recorded as an expected
  difference signed off by Agents 2 and 4.
- Q-3. Closed 2026-10-05 by D-016: the one-board-per-phase option is ported as a `BoardStack` of one Layout per board
  (interfaces.md §5, revision U-D3).
- Q-4. EC-05 cap: keep 10 % as a labelled `assumption` or lower to 8 % (DEF-23 c)? Agent 2 decides; the contract only
  needs the number and its status.
- Q-5. Who writes the English install guide that Fable translates: Agent 3 in U-M5b (proposed) or Agent 1?
