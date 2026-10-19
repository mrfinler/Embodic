Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5

# U-V8 defects (V3-01 and V3-14, release 0.0.1 wheel and main 3cb23e5)

Each row was reproduced on 2026-10-17 in the worktree venv (`.venv`: the release wheel, numpy 2.4.6, pypdf 6.20.0).
`$S` is any empty scratch folder. Statuses follow standing order 2.

## DEF-UV8-01 (REQ-L-03, must): two engine messages that the UI shows name Xcoil

`src/embodic/model/validate.py` l.120 and l.125 give the suggestion reason "Xcoil clamps to the supported range.", and
l.134 and l.189 give "Xcoil rounds up to an even count." The session shows the reason in its notice. The product test
`tests/unit/ui/session/test_session_state_machine.py::test_ui15_out_of_range_value_stays_until_apply_then_notice_and_undo`
(l.182 at 5e74acc) asserts the notice text "Changed from 60 to 50: Xcoil clamps to the supported range.", so it pins
the defect. Status `verified` (reproduced, wheel and main).

```
.venv/bin/python -I -c "
from embodic.model.validate import check_value
from embodic.model.fields import field_specs
from embodic.model.vocabulary import TopologyKind
spec = next(s for s in field_specs(TopologyKind.SPIRAL) if s.pointer == '/rotor/air_gap_mm')
(i,) = check_value(spec, '/rotor/air_gap_mm', 60.0)
print(i.code, '|', i.suggestion.reason)"
```

Output: `RANGE_ABOVE_SUPPORTED | Xcoil clamps to the supported range.`

## DEF-UV8-02 (REQ-T-09 and REQ-N-10, must): the gate never enforces TR-01

The release gate runs `tools/trace_matrix.py` without `--fail-untested-through` (gate log l.428; `tools/ci.py` l.75-82 at
5e74acc and on main 3cb23e5). Without the flag the script skips the TR-01 check and prints `untested due: 0`. With the
flag, the release REQ report has 6 live must rows without a passing test, and the script exits 1. The pytest gate also
runs without pytest-cov (no `--cov` in `tools/ci.py` or `addopts`), so REQ-N-10's coverage clause is not checked
either. Status `verified` (reproduced).

```
git archive 5e74acc tools/trace_matrix.py docs/phase2/architecture/requirements.md | tar -x -C $S && cd $S
python3 -I tools/trace_matrix.py --report=/home/claude/release_0.0.1/req_report.json --out=$S/a.md
python3 -I tools/trace_matrix.py --report=/home/claude/release_0.0.1/req_report.json --out=$S/b.md --fail-untested-through M5
```

Output: the first prints `... untested due: 0` and exits 0. The second prints `untested due: 6`, then REQ-N-07,
REQ-N-10, REQ-T-10, REQ-T-11, REQ-L-03 and REQ-L-05, and exits 1.

## DEF-UV8-03 (REQ-T-10, must): the computed DRC clearance is called "measured"

The DRC clearance is computed from the generated geometry. The product calls it measured in these places:

- UI strings: `{message} {layer}: {measured} measured, {required} required.`, the accessible text `Error. {code}.
  {message} Measured {measured}, required {required}, layer {layer}.`, the column headers `Measured (mm)` and
  `Least measured`, and the note `the check measured no track pair`.
- The PDF report: the DRC table header `Check Least measured Required Pairs`, in all 5 reports and the 5 bundle copies.
- The JSON outputs: 186 `measured_mm` and 47 `measured_min_mm` keys in `compute --json` and the bundles.
- The equation registry name `DRC clearance measurement and acceptance` (`equations.v1.json` l.2844), which the
  equation guide shows.
- Minor: `_resources/fonts/FONTS.md` l.24-25 call a SHA-256 'measured' with `sha256sum`.

The contract uses the same word. The REQ-F-10 statement says "whenever the measured clearance is below rule", and
interfaces.md names `measured_mm`. Fable rules whether DRC distances join the LG-03 allow-list or the product renames
them (for example "clearance found", "least clearance"). Status `verified` (reproduced by
`tests/independent/m7/v3_14_scan.py`; the record lists each location).

```
.venv/bin/embodic-cli compute .venv/lib/python3.11/site-packages/embodic/_resources/examples/wave_16p_example.embodic.json --json $S/o.json
grep -c '"measured_mm"' $S/o.json
```

## DEF-UV8-04 (REQ-T-11, must, needs a ruling): "Balanced." is a balance claim from phase angles

`src/embodic/ui/strings/design.py` l.218 and l.225 to l.228 show "Balanced: q = {q}, periodicity t = {t}.", "Balanced."
and "Not balanced ..." from the star of slots, which reads only coil and pole counts. Brief rule 6 says "Never claim
magnetic balance, torque or efficiency from geometry or phase angles alone". REQ-F-02 also calls these windings
"balanced", in the sense of a symmetric winding. Fable rules whether winding symmetry is in the scope of rule 6. If it
is, a wording such as "Symmetric 3-phase winding (star of slots)" avoids the claim. If not, the phrases join the LG-04
reviewed list. Status `verified` that the strings ship (scan record); the scope is `unresolved`.

## DEF-UV8-05 (REQ-L-03, must): three registry formulas that the guide shows name Xcoil

The `formula` of EQ-14 ("alternative: Xcoil current-sheet model"), EQ-20 and EQ-27 ("(Xcoil 'kw1')") name Xcoil. The
equation guide shows `formula` (`ui/viewmodels/results.py` l.737), and every result's disclosure shows
`{eq}: {name}. {formula}` (l.226). Status `verified` (reproduced through the view model, no Qt needed).

```
.venv/bin/python -I -c "
from embodic.ui.viewmodels.results import equation_topic
from embodic.results import load_registry
r = load_registry()
print({eq: [k for k, v in equation_topic(eq, r).rows if 'Xcoil' in v] for eq in ('EQ-14', 'EQ-20', 'EQ-27')})"
```

Output: `{'EQ-14': ['Formula'], 'EQ-20': ['Formula'], 'EQ-27': ['Formula']}`.

## DEF-UV8-06 (REQ-F-03 and REQ-F-04, must): two planned tests do not exist

UT-PHY-07 ("series chain = phasor sum of pair EMFs at own z", rel. 1e-9) and GR-07 (`stackupFor` auto and custom
against Xcoil, 1e-12 mm) have no test in the release tree under any label I could find. The searches are in
`v3_01_rulings.py` (CAUSE_B_RULINGS). Status `verified` that the searches find none; that no test exists is `inferred`
from them.

```
git archive 5e74acc tests | tar -x -C $S
grep -rn -i -E 'phasor sum|series chain|def test.*series' $S/tests/unit/physics $S/tests/golden/m2_physics
grep -rn -i -E 'stackupFor|stackup_for|even.spac|auto.mode' $S/tests --include=*.py | grep -v independent
```

## DEF-UV8-07 (audit, must rows): a name match does not mean the test checks the criterion

req_audit.py marks a row `verified` when a passing test names each planned ID. V3-01 read one sampled test per
`verified` must row (50 rows): 6 check the Acceptance text, 32 check part of it, 12 check none of it. The 12 are
REQ-F-13, F-18, F-37, F-40, N-01, N-10, N-13, N-15, N-17, T-13, L-01 and L-07. Several of these test a control (a
planted violation) rather than the product. With the rulings applied, `verified` must rows drop from 50 to 42
(lenient) or 10 (strict), and 11 of the 20 cause-B IDs exist under another REQ marker. Status `verified` (reading;
`python3 tests/independent/m7/v3_01_sample.py`). The audit rule lives in Agent 4's U-V6 script, which this unit may not
edit. A follow-up decides whether req_audit.py reads the V3-01 rulings.

# U-V13 defects (V3-01 re-ruling, V3-15, REQ-L-01 review; main 260191f, 2026-10-18)

Reproduced in the worktree `unit/U-V13` with `/home/claude/embodic/.venv/bin/python` and
`PYTHONPATH=<worktree>/src`. `$S` is any empty scratch folder. Statuses follow standing order 2.

## DEF-UV13-03 (REQ-N-10, must, M2; high: blocks the 0.0.2 release gate): no test carries REQ-N-10

The amended REQ-N-10 reads "Matrix generator lists 0 untested live must REQs (TR-01)". The tests of that gate
(`tests/unit/base/test_tr01_release_gate.py`) carry other markers, and no collected test carries REQ-N-10, so the
release profile's `--fail-untested-through M5` lists REQ-N-10 itself as untested and exits 1. Reproduce:

```
pytest -p no:cacheprovider --collect-only -q --req-report $S/c.json tests      # 4071 tests collected
python3 -c "import json; print(sum('REQ-N-10' in r['req'] for r in json.load(open('$S/c.json'))))"   # 0
python3 tests/independent/m7/v3_01_rerule.py --report <gate report of main> --gate-log <its log> --collected $S/c.json
#   REQ-N-10: not tested; release: yes
```

Status `verified` (collection and the lever). Expected: at least one passing test with REQ-N-10, for example the
TR-01 release-gate tests (owner Agent 3, a marker change).

## DEF-UV13-01 (REQ-L-01, must; medium): LG-01 has no word printer

test_plan.md l.488 (revision U-D20) says LG-01 "adds one function that returns the sorted distinct words of the string
catalogues and the report templates, and one command that prints them", with a test that the list holds a planted
word. On main 260191f neither exists: `grep -rln "distinct" tests/static tools src --include=*.py` finds only a
docstring in `src/embodic/ui/viewmodels/results.py` l.495 (assumed inputs, not words), and
`tests/static/test_lg_language.py` has only the character rule (l.62-114). Status `verified` (reading and search). The
REQ-L-01 manual record (`tests/independent/m4/records/LG-01_word_review.md`) therefore reads Agent 4's own list
(`tests/independent/m7/l01_words.py`, 804 words), not the list the acceptance names. Expected: the function, the
command and the planted-word test (owner Agent 3); then a reviewer compares that list with the record.

## DEF-UV13-05 (REQ-F-11 (i), must; medium): EQT-27-GR is carried by no test

The registry links EQ-27 (k_u, status `inferred`) to EQT-27-GR, and no collected test carries that ID; EQ-27 feeds
`winding_factor_1` and `inductance_estimate_h` of every example. EQT-28-GR and EQT-29-GR are carried by no test either,
but EQ-28 and EQ-29 have no port in src (`docs/phase2/engineering/eqt_map_review.md` l.240-241). Reproduce:

```
python3 - <<'PY'
import json
eqs = json.load(open("resources/evidence/equations.v1.json"))["equations"]
carried = {e for r in json.load(open("$S/c.json")) for e in r["eqt"]}
print([(e["id"], t) for e in eqs for t in e["tests"] if t not in carried])
PY
# [('EQ-14', 'EQT-14-O2'), ('EQ-27', 'EQT-27-GR'), ('EQ-28', 'EQT-28-GR'), ('EQ-29', 'EQT-29-GR')]
```

Status `verified`. This corrects my U-V12a ruling of REQ-F-11, whose gap F11-1 named only EQT-16, 17, 19 and 22.
Expected: a dump of Xcoil's utilisation factor and a golden comparison (eqt_map_review.md l.239; owner Agent 3,
tolerance Agent 2).

## DEF-UV13-02 (REQ-N-24, must; low): table cells carry their unit only in the column header

`python3 tests/independent/m7/n24_table_cells.py` (offscreen) prints for the D08 and 12c16p `layer-list` the headers
`['Layer', 'Kind', 'Thickness\n(µm)']` and for cell (0,2) `display='34.8' text=None description=None widget=None`.
So the thickness input announces no unit of its own. `screw-table` has the unit in its 'Pitch radius (mm)' header; both
spiral examples have 0 screw rows, so its cells are `inferred` the same from the product test's docstring
(`tests/ui/qt_design/test_n24_unit_announcement.py` l.4-5). Whether Narrator reads the column header with a cell is
`not tested`. Status `verified` for the layer-list cell. Expected: Agent 1 rules whether the header satisfies
REQ-N-24 ("include it in its accessible description"); otherwise each cell gets an accessible description with the
unit and the test covers both tables.

## DEF-UV13-04 (REQ-F-08, F-10, F-12, F-14, T-08, T-14, must; low): the only test of a clause carries another row's marker

interfaces.md section 3.2 lets an acceptance ruling cite only tests that carry the row's REQ marker. Six clauses are
asserted only by tests marked for another row:

- REQ-F-08: Ke_LL in star and delta, CF-06 (`test_kernels.py::test_cf06_star_and_delta_constants`, REQ-F-11).
- REQ-F-10: the default spiral packs within rule + 0.005 mm, UT-DRC-01
  (`test_spiral_generate.py::test_default_example_passes_drc`, REQ-F-05).
- REQ-F-12: the two-member circulating identity, CF-07 (`test_closed_forms_m2e2.py`, REQ-F-11).
- REQ-F-14: BV-05 (`test_spiral_bounds.py::test_requested_turns_above_the_turns_that_fit_are_refused_as_the_users_request`,
  REQ-F-19).
- REQ-T-08: the `unresolved` badge above e_edge 0.10 (`test_traceable.py::test_traceable_adr_0003_worked_example`,
  REQ-T-03 and REQ-T-05).
- REQ-T-14: the SVG, DXF and project-file stamps (`test_svg.py`, `test_dxf.py`, the t07 tests of `test_stamp_fields.py`,
  `test_project_v2.py`; REQ-T-07 only).

Reproduce: cite one of these tests in a `checks` ruling of its row; `v3_01_rerule.py` prints "lacks the REQ-x marker".
Status `verified`. The rows keep other passing marked tests, so the release trace gate does not fail on them.
Expected: add the six markers (owner Agent 3, no new assertion).

# U-V15 defects (V3-02 to V3-07 and V3-10; main 6555588 = release 0.0.2 sources, 2026-10-19)

Each row was reproduced in the dev venv (`py311-dev.txt`, CPython 3.11.17) with `PYTHONPATH=src`. The mutation runs
use `tests/independent/m7/product_mutants.py`, which edits only a temporary copy of the checkout.

## DEF-UV15-01 (REQ-F-10, must, D-006; low): no test sits on the D-006 boundary, so a flipped comparison survives

Mutant V3-02-09 turns `clearance < required - DRC_EPSILON_MM` into `<=` in `src/embodic/drc/engine.py` l.340. It
survives its named test (`tests/independent/m1/test_drc_agreement.py::test_intrusion_is_decided_by_d006`) and the whole
V3-02 suite with the mutant applied: `tests/unit/drc`, both PR-13 tests, `tests/independent/m1` and
`tests/independent/m3` (the clean copy: 318 passed, 1 skipped; the mutant run took 659 s). It is not equivalent. `python tests/independent/m7/def_uv15_boundaries.py` builds two traces whose clearance is
`0.199999 == 0.2 - 1e-6` exactly. The product reports 0 violations there and 1 violation 8.9e-17 mm closer. The mutant
would report the exact case.

```
python tests/independent/m7/product_mutants.py V3-02 --only V3-02-09   # prints "survived V3-02-09 ..."
PYTHONPATH=src python tests/independent/m7/def_uv15_boundaries.py      # "D-006 k=+0: ... violations 0"
```

Status `verified`. Expected: a UT-DRC-03 case at the exact float boundary (the probe's geometry), asserting 0
violations, plus the 8.9e-17 mm closer case asserting 1. Owner Agent 3.

## DEF-UV15-02 (REQ-F-10, must, rule 2b of D-036a and D-037a; low): the rule 2b tap band is tested off its edge only

Mutant V3-02-10 turns the tap test `<= via.pad_mm / 2` into `<` in `src/embodic/drc/items.py` (`_taps`). It survives
`test_ut_drc_04_same_net_via_tap_band_is_half_the_via_pad` (offsets 0.29 and 0.31 mm) and the whole V3-02 suite (690 s).
The probe shows that a via exactly 0.3 mm (`pad_mm / 2`) off the centreline is exempt in the product (0 violations), as
interfaces.md section 7 rule 2b says ("within `pad_mm / 2`"). The mutant reports it.

```
python tests/independent/m7/product_mutants.py V3-02 --only V3-02-10   # prints "survived V3-02-10 ..."
PYTHONPATH=src python tests/independent/m7/def_uv15_boundaries.py      # "rule 2b offset 0.3: []"
```

Status `verified`. Expected: add the 0.3 mm offset to the UT-DRC-04 parametrisation with `reported=False`. Owner
Agent 3.
