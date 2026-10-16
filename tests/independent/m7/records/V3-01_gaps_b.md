Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5 (unit U-V12b, 2026-10-17, main 8a4a8a1)

# V3-01 union gaps for the REQ-N, REQ-T and REQ-L rows

Each section is the missing assertion of one row that `tests/independent/m7/v3_01_rulings_ntl.py` rules `partial` or
`does not check`. The union of a row is every test that carries its REQ marker or names a planned ID
(`tests/independent/m7/v3_01_union.py` over `pytest --collect-only --req-report` of main 8a4a8a1, 3202 tests). A part
is called missing when a search of every union file for its terms found no assertion (`inferred`). Each spec gives
inputs, the expected value and its source, the tolerance, and the defect it catches. Specs for Agent 3 unless marked
"manual record", which a person or Agent 4 runs and indexes in `docs/phase3/verification/manual_records.json`.

REQ-T-01, T-02, T-05, T-07, T-13 and T-14 were ruled in the U-V12b continuation (sections T-01 to T-14 below).

## N-01 (REQ-N-01)

Manual record plus test. On the user's laptop run PF-01 (20 warm recomputes of `spiral_12c16p_default`). Assert p95 of
the full recompute < 1.0 s and the per-stage p95 geometry < 0.2 s, DRC < 0.4 s, physics < 0.3 s (requirements.md
REQ-N-01). No tolerance: the bounds are strict. Catches a regression that the current `p95 > 0` assertion
(tests/performance/test_pf_baseline.py:70) cannot fail on.

## N-02 (REQ-N-02)

Qt test. Type five characters into one inspector field at 50 ms intervals, then wait. Assert exactly one compute
request starts, and it starts 300 ms ± 50 ms after the last key (requirements.md REQ-N-02 "300 ms debounce"; the
UX-AC-22 timing of the design spec). Catches a compute per keystroke or a missing debounce.

## N-04 (REQ-N-04)

Manual record. Re-run PK-04 on Windows with the D-051f rule: each outcome array at 1e-9 relative to its largest
absolute value, other floats at 1e-9 relative, `design_hash` exact, `layout_hash`, `stack_hash` and `pairs_checked`
left out (D-051f, D-052b). Fable's W1 run failed as written (docs/phase3/fable/windows_campaign_w1.md l.59). Catches a
cross-platform numeric drift that the same-platform PR-09 cannot see.

## N-05 (REQ-N-05)

Manual record. A clean venv on Windows 11 x64 with Python 3.11 installs from the lock file and runs `embodic-cli
selftest` with exit 0; the same on Linux with Python 3.12 and 3.13 (requirements.md REQ-N-05). Catches a lock file
or wheel that resolves only on Linux 3.11, the one cell PK-02 covers.

## N-06 (REQ-N-06)

Gate change, then record. Build the PyInstaller folder in the release profile and run tests/bundle/test_bundle_smoke.py
against it; on Windows run PK-05 on the folder. Expected: every bundle test passes, none skipped (requirements.md
REQ-N-06 "the bundle smoke test runs"). Catches a release whose bundle tests are skipped and so never ran.

## N-07 (REQ-N-07)

Manual record. A cold PK-06 walkthrough on a clean Windows machine on a network of at least 1 MB/s. Expected: the first
computed example under 600 s (requirements.md REQ-N-07; Fable's cold run took 4154.5 s at 0.03 MB/s,
windows_campaign_w1.md l.9, l.33). Catches an install guide or lock file that is slow for reasons other than the user's
network.

## N-09 (REQ-N-09)

Static test beside tests/static/test_mt04_physics_docstrings.py. Plant a physics function whose Parameters entry reads
`width : float` with the description "Trace width." and no unit. Expected: the checker reports it. Then the same with
"Trace width in mm." Expected: no report. Unit tokens from `embodic.units.Unit`. Catches a docstring that names a
parameter but no unit, which the checker passes today (it only matches `name:`, l.21).

## N-10 (REQ-N-10)

Phase 5 (D-053b). Run the core suite under pytest-cov in CI. Assert line coverage of `embodic` without `embodic.ui`
at least 90 % and branch coverage at least 80 % (requirements.md REQ-N-10). Catches an untested core module. Until the
requirements row is split, this clause keeps the row `partial`.

## N-12 (REQ-N-12)

Qt test. With D08 open at 1280 x 800, press Tab from the first stop until focus returns. Record each stop's top-left in
window coordinates. Expected: inside each region, stops sort by (y, x) with a 4 px row band; regions follow the F6 order
of tests/ui/qt_shell/test_keyboard_map.py:85. Catches a Tab order that jumps against the visual order.

## N-15 (REQ-N-15)

Qt test, one process per `QT_SCALE_FACTOR` of 1, 1.5 and 2, window at 960 x 540, 1280 x 800 and full screen.
Expected: the clipped-text check of tests/independent/m4/test_ui_behaviour.py:241 finds nothing; no two visible
sibling widgets' geometries intersect; every form's horizontal scroll bar is hidden or has maximum 0. Catches clipping
or overlap that only a scale factor above 1 shows.

## N-16 (REQ-N-16)

Manual record. Narrator on Windows with D08 open: each input announces label, value and unit; each result card
announces value, unit and status (requirements.md REQ-N-16). The Linux proxy (tests/independent/m4/records/AX-06.md
l.9) says Narrator is `not tested`. Catches names that Qt exposes but Narrator does not read.

## N-17 (REQ-N-17)

Gate change. Run the commit suite with a conftest fixture that replaces `socket.socket.connect` and
`socket.create_connection` with a function that raises. Expected: the suite result equals the run without it. Catches
a dependency or a code path that opens a connection at run time, which the import scan cannot see.

## N-21 (REQ-N-21)

Unit test. Write the D08 and wave examples to SVG and DXF. Parse every copper path back, and for each pair of end
points that were one shared coordinate in the Layout (within 1e-6 mm), assert the written points are equal
(requirements.md REQ-N-21 "continuity holds after SVG and DXF quantisation"). Catches a writer that rounds each end
of a joint on its own and leaves a 1-digit gap.

## N-23 (REQ-N-23)

Qt test. Start the app with a forced-colours (high-contrast) palette: QPalette with system colours and the Windows
high-contrast flag emulated through the theme loader. Expected: phase identity stays readable through labels, dash and
hatch, and no chrome token is drawn instead of the system colour (requirements.md REQ-N-23 "forced-colours run").
Catches a canvas that loses its non-colour cues under forced colours.

## N-24 (REQ-N-24)

Qt test driven by the field table. For every input widget of every `field_specs` entry with a unit, assert
`accessibleDescription()` contains the unit symbol and the visible unit label equals it (requirements.md REQ-N-24).
Expected values from `embodic.model.fields`. Catches an input whose unit is shown but not announced.

## N-25 (REQ-N-25)

Qt test. On the serpentine example, open Torque and Power. For each chart, toggle the data table. Expected: the table
row count equals the chart's x count and its headers carry the units "N·m" and "W"; the single series has a direct end
label. Catches a chart with no data-table alternative.

## N-27 (REQ-N-27)

Qt test. Switch light to dark at runtime with D08 open. Walk every visible widget and read its palette and resolved
style-sheet colours. Expected: none equals a light-theme token hex that differs from the dark one. Catches a widget
with a hard-coded colour that the region check (tests/ui/qt_shell/test_theme_and_geometry.py:36) does not visit.

## N-28 (REQ-N-28)

Unit test. Run Agent 1's palette validator (design_spec.md sections 3.2 and 3.4) on both theme files: each pair of
phase colours and each adjacent step of the greyscale ladder must meet the separation that section 3.4 states.
Catches a theme edit that keeps 3:1 on the canvas but makes two phases or two grey steps indistinguishable.

## T-01 (REQ-T-01)

Qt test. Load D08 and walk all 30 result cards. Expected: each card shows an EQ chip whose text lists the row's
`eq_ids`, or a kind tag when `eq_ids` is empty, and never neither; for each card, Tab to it and press Space; the
"How was this computed" panel of that card becomes visible (requirements.md REQ-T-01 "details reachable in one
interaction"). Catches a card with no EQ link or tag, or a card whose details the keyboard cannot open.

## T-02 (REQ-T-02)

Unit test. For every packaged example, compute the outcome and walk its real `AnalysisResult` (fields, layers,
phases, torque-speed). Expected: every number is a `Traceable`; each one's `eq_ids` resolve in the packaged registry
or it carries a kind tag; every `evidence_ids` entry resolves (requirements.md REQ-T-02 "for every example").
Catches an engine path that emits an unknown EQ-ID or a bare number for one topology.

## T-05 (REQ-T-05)

Gate test, or an acceptance rewording by Agent 6. Run `tools/record_passed_tests.py` (release profile) on a report
where a `verified` equation's only linked EQT ID is carried by no passing test. Expected by the acceptance: exit 1 and
the equation named. Today record_main exits 0 and prints the ID as "carried by no test"
(tests/unit/results/test_record_passed_tests.py:85-117). Catches a release that ships a `verified` equation whose
tests did not run. If the badge downgrade (`not tested`) is the intended mechanism, the acceptance text needs that
wording instead.

The badge half is asserted (tests/unit/results/test_traceable.py:154-160): no verified badge without a passing
linked test. Only the "CI fails" clause is missing.

## T-07 (REQ-T-07)

Unit tests. (a) Save a project and read the JSON: it holds embodic version, engine version, registry version, design
hash and a generation date in UTC (requirements.md REQ-T-07). (b) In the PDF text, a `generated_utc` value matching
`\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ`. (c) In README.txt, `embodic_version`, `engine_version` and `generated_utc`
lines with the outcome's values. Catches an export that drops a stamp field.

## T-13 (REQ-T-13)

Unit test. For every one of the 30 result rows of D08 and of the wave example: the disclosure has the six sections
Equation, Inputs, Assumptions, Limitations, Validation state, Sources; each Inputs line names the provenance word
(`user`, `example`, `measured` or `default`); the Assumptions count equals the row's tag count; `copy_trace(row)`
holds every disclosure line (requirements.md REQ-T-13 "Content check per result row"). Catches one row whose
disclosure drops a section or an input.

## T-14 (REQ-T-14)

Unit and Qt tests. (a) README.txt contains `embodic_version: <outcome.versions.embodic>`. (b) With D08 open, the
geometry view or its status line shows the design hash prefix and the embodic version of the drawn outcome, if the
design spec (UX-AC-17) assigns the stamp to the on-screen drawing; otherwise Agent 6 narrows the statement to
exports. Catches an export or an engine drawing without its version stamp.

## T-06 (REQ-T-06)

Unit test. Mark B_r (`/rotor/magnet/remanence_t` or the pointer `BR` of tests/unit/model/test_provenance.py) measured
with a named source and compute the EMF Traceable. Expected: B_r is absent from `assumed_inputs` and the count drops by
one; without a source the mark is refused with INVALID_MEASURED_SOURCE_EMPTY (requirements.md REQ-T-06). Catches a
magnet property that the retirement rule skips.

## T-08 (REQ-T-08)

Unit tests. (a) A trace width of 0.4 × delta at 133 Hz (delta 5.72 mm, tests/unit/physics/test_kernels.py:151):
expected ISSUE RANGE_SKIN_DEPTH and the R and eddy Traceables carry the validity flag. (b) e_edge for Agent 2's three
cases equals 5.3 %, 4.2 % and 5.8 % within 0.1 percentage point (test plan UT-PHY-21). Catches an unchecked validity
limit and an EC-05 value drift.

## T-09 (REQ-T-09)

Unit test beside tests/unit/base/test_trace_matrix.py. Run `tools/trace_matrix.py` main on a report with one test that
has no REQ marker. Expected: exit 1 and the node id in the output. Catches a gate that finds unmarked tests but still
exits 0.

## T-10 (REQ-T-10)

Product test LG-03 (test_plan.md l.393, §5.8.2): scan class `measur` over the three corpora of §5.8.1 with the
allow-list of §5.8.2. Expected: 0 hits outside the allow-list. Catches "measured" applied to a computed value in a
string, a template or an export.

## T-11 (REQ-T-11)

Product test LG-04 (test_plan.md l.394, §5.8.3): scan classes `balanc`, `torque`, `efficien` with the §5.8.3
allow-list. Expected: 0 hits. Plus a reviewer manual record (§5.8.3). Catches a balance, torque or efficiency claim
from geometry alone.

## T-16 (REQ-T-16)

Unit test. Read the OR-07 and OR-08 entries that the UI shows. Expected: each carries the note that it is not
independent of EC-05 (requirements.md REQ-T-16; test_plan.md REQ-T-12 acceptance "OR-07 and OR-08 flagged as not
independent of EC-05"). Catches an oracle row presented as independent evidence.

## L-01 (REQ-L-01)

Static test. Tokenise every string literal of src, resources and templates into words. Expected: each word is in the
English allow-list (test plan LG-01) or is an identifier the allow-list admits. Catches a non-English word written in
ASCII (for example a romanised Thai word), which the per-character scan passes.

## L-03 (REQ-L-03)

Product test LG-05 (test_plan.md l.395, §5.8.4): 0 occurrences of "xcoil", ignoring case, in user-facing strings and
generated files, plus the D-051c program names. Catches the old product name in a string, export or report.

## L-04 (REQ-L-04)

Unit test. Read both theme files. Expected: every chrome token has R = G = B (white, grey or black), and the only
saturated colours are the phase tokens and the status tokens (requirements.md REQ-L-04, D-011). Catches a tinted
chrome colour.

## L-05 (REQ-L-05)

Product test LG-06 (test_plan.md l.396, §5.8.5): SHA-256 of each brand asset equals the recorded value, and a
personal-data scan finds 0 hits. Catches an edited logo or a user name in code, logs or outputs.

## Manual records added in this unit

`docs/phase3/verification/manual_records.json` now holds six records, each from a record file that exists:

- REQ-N-07 PK-06 passed: tests/independent/m5/records/PK-06_walkthrough.md (Agent 4, U-V5, Linux cold, 19.2 s to 27.7 s).
- REQ-N-07 PK-06 passed: docs/phase3/fable/windows_campaign_w1.md (Fable, Windows warm cache, 21.57 s, l.64-66).
- REQ-N-07 PK-06 failed: docs/phase3/fable/windows_campaign_w1.md (Fable, Windows cold, 4154.54 s, l.33-38).
- REQ-N-14 AX-05 passed: tests/independent/m4/records/AX-05.md (Agent 4, 48 of 48 readings, l.83).
- REQ-F-11 OR-11 and OR-12 passed: tests/independent/m6/records/OR-11_OR-12.md (Agent 4, U-V7, both in band).

The five-key format has no observer key; the observer is the author named on line 1 of each record file. AX-06
(tests/independent/m4/records/AX-06.md) is not indexed, because it is a Linux proxy and says Narrator is `not tested`.
