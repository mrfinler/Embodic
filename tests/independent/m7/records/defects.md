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
