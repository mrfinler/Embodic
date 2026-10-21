"""Agent 4's V3-01 re-rulings on release 0.0.5 (42074f2, U-V21), applied on top of v13, v14, v18, v19 and v20.

Four rows, each read against the Acceptance cell of requirements.md on the 42074f2 sources:

- REQ-F-05, REQ-F-13 and REQ-T-05, which U-V19 ruled `partial` with the tests U-M8y and U-D26 then added as their
  missing piece (U-V19_id_map.md EXTRA F05, F13_VIEW, F13_CUE and T05; UT-PHY-11 half (1); the spiral brute sweep).
- REQ-N-01, whose PF-01 run on the reference laptop failed (docs/phase3/fable/PF-01_windows_0.0.5.md, D-087).

PINS (records/V3-01_pins_42074f2_v21.json) holds the 42074f2 SHA-256 of each non-gate cite, in the form of req_audit.py
`cite_hash`, written by `v21_rerule.py --write`. `v21_rerule.py --check` shows that every cite ran with the row's
marker and passed in Fable's 0.0.5 release run. Every ruling is `verified` by reading the cited sources on 42074f2
unless its reason labels a part `inferred`, `read` or `assumption`.
"""

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_v13 = _load("v3_01_rulings_v13")
Ruling = _v13.Ruling

BASE = "42074f2"
PIN_FILE = HERE / "records/V3-01_pins_42074f2_v21.json"

U, UI = "tests/unit", "tests/ui"
PAIRS = f"{U}/generators/test_spiral_pairs.py"
FAN = f"{U}/generators/test_spiral_series_fan.py"
EVERY = f"{U}/generators/test_every_topology_refuses.py"
SWEEP = f"{U}/property/test_spiral_brute_sweep.py"
BARRELS = f"{U}/physics/test_via_barrels.py"
KERN = f"{U}/physics/test_kernels.py"
CUE = f"{UI}/qt_shell/test_layer_cue.py"
GATE = f"{U}/results/test_record_passed_tests_gate.py"
RECORD = f"{U}/results/test_record_passed_tests.py"

RULINGS = {
    "REQ-F-05": Ruling(
        "checks",
        "Amended acceptance (D-054b, D-054d; UT-PHY-11 restated by U-D26 1b, D-084a). (1) Count Q*v*(2k + 1): 36 "
        "centre and terminal vias for M1, and per series coil k centre, k - 1 transfer and 2 terminal vias "
        "(UT-GEO-13, as U-V13 ruled). (2) Every through via clears foreign copper (PR-01): on the default, D08, 12c14p "
        "and CF-11 k3 spiral boards run_drc and Agent 4's brute sweep (tests/independent/m1) agree pair for pair, the "
        "swept pairs include a via against copper of another net, and a passing report leaves the sweep no violation; "
        "all four boards pass (run_drc on 42074f2: violation_count 0 on each, with 63, 63, 63 and 111 vias; U-V21 "
        "run). The M1 "
        "pairs pass DRC with trace_via least clearance 0.2 mm. (3) One via per transition is built on every topology "
        "(UT-GEN-06 control) and analysed: each example computes with no ERROR issue and a finite R_ph,20 above 0 "
        "(F05), and one extra mm of board raises R_ph,20 by the mean one-barrel EQ-11 term of the phases at 1e-9 "
        "relative on the spiral, serpentine and wave examples (UT-PHY-11 half (1)). (4) Values 2 and 3 are refused on "
        "all three topologies with their own NOT_IMPLEMENTED code at /vias/vias_per_transition (UT-GEN-06); 'every "
        "other value' rests on the refusal condition `vias_per_transition != 1` in the three generators (read: "
        "spiral/generate.py l.94, serpentine l.119, wave l.81) and on validation refusing values below 1 (fields.py "
        "l.170, POS). Seeded fault (v21_seeded_faults.py): a via analysed as two barrels fails all three UT-PHY-11 "
        "cases (0.00798 against 0.01597 ohm on the first).",
        (
            f"{PAIRS}::test_ut_geo_13_parallel_pairs_need_36_winding_vias",
            f"{FAN}::test_ut_geo_13_series_coil_has_2k_plus_1_winding_vias",
            f"{PAIRS}::test_parallel_pairs_pass_drc",
            f"{SWEEP}::test_pr_01_pr_13_spiral_boards_agree_with_the_brute_sweep_including_every_through_via",
            f"{EVERY}::test_ut_gen_06_one_via_per_transition_still_builds_every_example",
            f"{EVERY}::test_f05_one_via_per_transition_is_analysed_on_every_topology",
            f"{BARRELS}::test_ut_phy_11_every_phase_via_of_an_example_is_analysed_as_one_barrel",
            f"{KERN}::test_cf04_and_ut_phy_11_via_barrel_resistance",
            f"{EVERY}::test_ut_gen_06_parallel_vias_per_transition_are_refused_by_every_topology",
        ),
    ),
    "REQ-F-13": Ruling(
        "checks",
        "Each view of the statement is visible after at most 2 interactions from the D08 start view (F13-1); zoom "
        "reaches 0.1x and 200x as literals (F13-2) and copper pens of the top visible layer stay in mm at every zoom "
        "(UI-03), as U-V13 ruled. The U-V18 gap is closed (U-M8y): lower-layer copper, which the layer cue paints, "
        "keeps its trace width at both ends of the range. At 200x a 1280 x 800 D08 view grab across leg 24 (L2, 0.6 "
        "mm) spans 0.6 mm x the view scale within 1.5 px (721.8 px expected); the cue item painted alone strokes "
        "0.6 mm at 0.1x (0.36 px, ink summed per column, within 0.04 px) and at 200x (span within 1.5 px). Seeded "
        "fault (v21_seeded_faults.py): cue strokes 0.1 mm thinner fail all three cases (601.75 against 721.82 px).",
        (
            *_v13.RULINGS["REQ-F-13"].cites,
            f"{CUE}::test_ui03_lower_layer_copper_the_cue_paints_keeps_its_trace_width_at_200x",
            f"{CUE}::test_ui03_the_cue_strokes_lower_copper_at_its_trace_width_at_0_1x_and_200x",
        ),
    ),
    "REQ-T-05": Ruling(
        "checks",
        "Amended acceptance (U-D20). In the release profile record_main exits 1 and writes no evidence file when a "
        "verified equation's only linked test or one of several did not pass, and passes a run in which every linked "
        "test of every verified equation passed (the control). stderr alone names a refused equation with the "
        "registry test IDs of it that passed, and '(passed: none)' when none did. The U-V19 gap DEF-UV19-01 is closed "
        "(U-M8y): T05 asserts the exact set of equations named on stderr, with their passed IDs, in two cases whose "
        "expected sets derive from the packaged registry: no registry test passed (every verified equation), and "
        "the last linked test of each multi-test equation skipped. u_v19_t05_mutants.py --commit 42074f2: 15 "
        "passed on the tool, and the unproven[:4] mutant, which all 13 earlier tests pass, fails both T05 cases "
        "([:1] fails 4 tests, [:2] 3). The 'links no test' branch is Registry.tests_passed returning False for an "
        "empty link list (read: registry.py l.150-153); the control shows that no packaged verified equation links "
        "no test, so that branch cannot fire on 0.0.5.",
        (
            f"{GATE}::test_a_report_that_passes_every_linked_test_of_every_verified_equation_records_the_evidence",
            f"{GATE}::test_a_verified_equation_whose_only_linked_test_did_not_pass_stops_the_release",
            f"{GATE}::test_a_verified_equation_missing_one_of_several_linked_tests_stops_the_release",
            f"{GATE}::test_stderr_alone_names_the_equation_and_the_registry_tests_of_it_that_passed",
            f"{GATE}::test_stderr_names_a_refused_equation_none_of_whose_linked_tests_passed",
            f"{GATE}::test_t05_stderr_names_every_refused_equation_with_its_passed_tests",
            f"{RECORD}::test_tr05_record_main_refuses_and_writes_nothing",
            f"{RECORD}::test_tr05_a_report_without_eqt_keys_is_refused_and_writes_nothing",
        ),
    ),
    "REQ-N-01": Ruling(
        "fails",
        "PF-01 on the reference laptop failed (Fable's record docs/phase3/fable/PF-01_windows_0.0.5.md, checkout "
        "bbeed84, whose src, resources and pyproject.toml equal 42074f2): physics p95 0.617 to 0.663 s against 0.3 s "
        "in all four sets, full recompute p95 0.913 to 1.003 s against 1.0 s (one set at or above its bound), "
        "geometry 0.019 to 0.024 s and DRC 0.282 to 0.302 s inside their budgets (DEF-W-15, D-087). The budget logic "
        "is tested on Linux (test_n01_pf01_budgets.py: a p95 equal to its bound is a finding; a case inside every "
        "budget has none), and the Linux PF-01 baseline passes, but the acceptance names the reference laptop, where "
        "the requirement is not met. Order 11: the budgets stay.",
        missing="A physics stage that meets 0.3 s p95 on the reference laptop, and a PF-01 rerun there; or the user "
        "moves DEF-W-15 to Phase 5 (D-087, decision pending).",
        kind="defect",
        owner="the user (DEF-W-15 decision); then Agent 3 and Fable",
    ),
}

PINS = json.loads(PIN_FILE.read_text(encoding="utf-8")) if PIN_FILE.is_file() else {}
