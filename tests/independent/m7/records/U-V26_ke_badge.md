Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5

# U-V26: the D08 Ke badge of release 0.0.5

Date 2026-10-22, unit U-V26, branch `unit/U-V26` on main 358673d. The release is
`/home/claude/release_0.0.5` (commit 42074f2, build `0.0.5+g42074f28cead.20261020T232950Z`).
`git diff --stat 42074f2 358673d -- src tests/conftest.py tests/unit/physics/test_oracles_m5.py` is empty.

## Question

The D08 card "Line back-EMF constant, peak" (`ke_line_peak_v_s_per_rad`) reads `not tested` on the 0.0.5 wheel. Its
value is within 0.4 % of D08's measured 0.031 V·s/rad (OR-01, D-030). U-S17 gave the reason "the tests of EQ-06 and
EQ-05 did not pass in this build". Is the badge correct by the contract, or is it a defect?

## Method

`uv26_ke_badge_trace.py` (this folder) runs on the unpacked wheel
(`python -m zipfile -e embodic-0.0.5-py3-none-any.whl <dir>`, then `PYTHONPATH=<dir> python -P -s ...`). It imports the
wheel's own code and resources, so the packaged evidence file applies as it does in an install. The script computes the
packaged D08 example and reads the card's badge, chain and reasons. For each registry test ID of each equation in the
chain, it compares the gate's REQ report (`req_report.json`) with the evidence file. Output is in
`U-V26_ke_badge_run.txt`. Exit 0.

## Trace

1. The card. The value is 0.030877 V·s/rad (−0.40 % from 0.031, as D-030 states). The badge is `not tested` and the
   chain is EQ-18, EQ-07, EQ-06, EQ-05. The reasons are "EQ-18 inferred; EQ-07 inferred; EQ-06 inferred; EQ-06 tests
   not passed in this build; EQ-05 inferred; EQ-05 tests not passed in this build".
2. The registry. EQ-05 and EQ-06 are `inferred`. D-057c moved EQ-06 to `inferred` and kept all five of its links,
   because the OR-07 failure is F-OR07. EQ-05 links six IDs and EQ-06 links five.
3. The gate. The REQ report has 4434 records and 0 failed. The writer's rule is that an ID passes when at least one
   record carries it and every record that carries it passed (`tools/record_passed_tests.py` l.59-71). By that rule
   the gate admits 5 of 6 EQ-05 IDs and 4 of 5 EQ-06 IDs. The two IDs it does not admit are EQT-05-O2 and EQT-06-O2.
   Both are carried by `test_or07_d09_phase_emf_within_the_registry_band[A]` and `[B]`, which the report records as
   `skipped`. These two cases are `xfail(strict=True, raises=AssertionError)` with reason F-OR07 at 42074f2. The gate
   log summary is "4419 passed, 3 skipped, 9 deselected, 3 xfailed". A rerun of the two cases on 358673d prints
   `XFAIL ... F-OR07` for both. EQT-05-O2 is also carried by OR-08, which passed. One failing carrier is enough to keep
   the ID out.
4. The evidence. The wheel's `passed_tests.v1.json` is byte-identical to the release-dir copy. It lists 58 IDs. For
   every linked ID of EQ-05, EQ-06, EQ-07 and EQ-18, "in evidence" equals "gate admits". No ID shows a mismatch.
5. The rule. `Registry.tests_passed` is True only when every linked ID is in `passed_tests` (interfaces.md §3.1). The
   badge is the weakest of the chain's evidence statuses, the test state and the validity cap (`result_badge_rule`,
   D-007). `derive_badge` adds `not tested` for each link whose tests did not all pass. `not tested` is weaker than
   `inferred` in `status_order_weakest_first`. REQ-T-05 refuses only `verified` equations, so it does not stop the
   release. REQ-T-16 marks OR-07 as dependent on the D09 calibration source.

## Verdict

The badge is correct by the contract. The evidence path has no defect, because the gate and the evidence agree on
every ID. U-S17's wording is too broad. Nine of the eleven linked IDs passed. Only the D09 oracle OR-07 (O2) did not,
and it is a strict expected failure (F-OR07).

Line for the user's UAT step 4.11: "Ke reads `not tested` because the registry links the D09 oracle OR-07 to EQ-05 and
EQ-06, and OR-07 is a known expected failure (F-OR07). The badge counts an equation as tested only when every linked
test passes. The D08 oracle OR-01 passed (−0.4 %)."

Not a defect, an observation for Fable: the in-app reason "EQ-06 tests not passed in this build" does not say that only
one of five links failed, or which one. That wording is how U-S17 came to its broad claim.
