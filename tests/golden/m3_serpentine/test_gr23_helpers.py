"""GR-23: the serpentine helpers against Xcoil's, 200 seeded inputs each, 1e-12 relative (REQ-F-34)."""

import math
from collections.abc import Callable, Mapping
from typing import Any

import pytest
from harness import KERNEL, Comparison, compare_prims, compare_scalar, compare_sequence, load_area
from m1_layout.xcoil_map import ROLE_BY_XCOIL_KIND, prim_from_record

from embodic.generators.serpentine.corners import make_corner, side_line, taper_junctions
from embodic.generators.serpentine.fit import (
    fit_status,
    max_fillet,
    max_traces_fit,
    min_straight,
    min_sweep,
    start_radius,
)
from embodic.generators.serpentine.frame import CornerType, Frame, derive

from .xcoil_params import normalised, params_from_xcoil

pytestmark = pytest.mark.req("REQ-F-34")
AREA = load_area("serpentine")


def _items(case_id: str) -> list[Mapping[str, Any]]:
    (call,) = AREA[case_id].calls
    return call.output["items"]


def _frame(item: Mapping[str, Any]) -> Frame:
    return derive(params_from_xcoil(normalised(item["params"])))


def _check(golden_report: Any, case_id: str, results: list[Comparison]) -> None:
    for index, result in enumerate(results):
        golden_report.check(f"{case_id}[{index}]", result)


def test_gr23_every_helper_has_200_inputs_and_exercises_each_branch() -> None:
    """Catches a case file that shrinks (fewer than 200 inputs) or never reaches a fillet branch of make_corner."""
    for case_id in AREA:
        if case_id.startswith("gr23-") and "maxtraces" not in case_id:
            assert len(_items(case_id)) == 200, case_id
    corners = _items("gr23-makecorner-seeded")
    assert any(item["output"] is None for item in corners), "no input reaches the refusal branch"
    assert {item["type"] for item in corners} == {"int", "ext"}
    assert any(item["rho"] == 0 for item in corners) and any(item["rho"] > 0 for item in corners)
    assert {item["u"] for item in corners} == {1, -1}


def test_gr23_side_line_matches_xcoil(golden_report: Any) -> None:
    """Catches a wrong side direction, a wrong radial angle pitch or a lost lateral offset in side_line."""
    results = []
    for item in _items("gr23-sideline-seeded"):
        line = side_line(_frame(item), item["ju"], item["i"])
        results.append(compare_sequence([item["output"]["phi"], item["output"]["d"]], [line.phi, line.d], KERNEL))
    _check(golden_report, "side_line", results)


def test_gr23_make_corner_matches_xcoil(golden_report: Any) -> None:
    """Catches a swapped int/ext fillet centre, a flipped u sign or a lost fillet arc angle in make_corner."""
    results = []
    for item in _items("gr23-makecorner-seeded"):
        d = _frame(item)
        corner = make_corner(
            side_line(d, item["ju"], item["i"]), item["R"], item["u"], CornerType(item["type"]), item["rho"]
        )
        golden = item["output"]
        if golden is None:
            assert corner is None, item
            continue
        assert corner is not None, item
        keys = ["rho", "pL", "pC", "angC", "angL", "xL"] + (["cf", "aStart", "aEnd"] if golden["rho"] > 0 else [])
        actual = {
            "rho": corner.rho, "pL": corner.p_l, "pC": corner.p_c, "angC": corner.ang_c, "angL": corner.ang_l,
            "xL": corner.x_l, "cf": corner.cf, "aStart": corner.a_start, "aEnd": corner.a_end,
        }  # fmt: skip
        assert set(keys) == set(golden), item
        results.append(compare_sequence([golden[k] for k in keys], [actual[k] for k in keys], KERNEL))
    _check(golden_report, "make_corner", results)


def test_gr23_taper_junctions_matches_xcoil(golden_report: Any) -> None:
    """Catches a taper split in the wrong place, a lost narrow width or fillets not looked through."""
    results = []
    for item in _items("gr23-taperjunctions-seeded"):
        prims = [prim_from_record(r) for r in item["prims"]]
        out = taper_junctions(prims, item["through"])
        results.append(compare_prims(item["output"], out, KERNEL))
        roles = [ROLE_BY_XCOIL_KIND[r["kind"]] for r in item["output"]]
        assert [p.role for p in out] == roles
    _check(golden_report, "taper_junctions", results)


def _scalar_helper(case_id: str, function: Callable[[Frame, float], float], golden_report: Any) -> None:
    results = []
    for item in _items(case_id):
        results.append(compare_scalar(item["output"], function(_frame(item), item["rho0"]), KERNEL))
    _check(golden_report, case_id, results)


def test_gr23_min_sweep_matches_xcoil(golden_report: Any) -> None:
    """Catches a wrong critical U-turn set (far, near or closing) in min_sweep."""
    _scalar_helper("gr23-minsweep-seeded", min_sweep, golden_report)


def test_gr23_min_straight_matches_xcoil(golden_report: Any) -> None:
    """Catches a wrong closing level or a missing first-turn strand check in min_straight."""
    _scalar_helper("gr23-minstraight-seeded", min_straight, golden_report)


def test_gr23_start_radius_matches_xcoil(golden_report: Any) -> None:
    """Catches the inner-terminal branch of start_radius using the outer-terminal formula."""
    _scalar_helper("gr23-startradius-seeded", start_radius, golden_report)


def test_gr23_fit_status_and_max_fillet_match_xcoil(golden_report: Any) -> None:
    """Catches a wrong refusal reason, a wrong level-0 fillet radius or an end gap that is not checked."""
    results = []
    reasons = set()
    for item in _items("gr23-fitstatus-seeded"):
        d = _frame(item)
        golden, fit = item["output"], fit_status(d)
        assert fit.ok is golden["ok"], item
        assert (fit.reason.value if fit.reason else None) == golden["reason"], item
        reasons.add(golden["reason"])
        pairs = [
            ("rho0", fit.rho0),
            ("legGap", fit.leg_gap_mm),
            ("backGap", fit.back_gap_mm),
            ("endGap", fit.end_gap_mm),
        ]
        pairs += [("rho0max", fit.rho0_max)] if "rho0max" in golden else []
        for key, actual in pairs:
            if key in golden:
                results.append(compare_scalar(golden[key], actual, KERNEL, path=f"$.{key}"))
        results.append(compare_scalar(golden["maxFillet"], max_fillet(d), KERNEL, path="$.maxFillet"))
    assert {None, "BUNDLE_TOO_WIDE"} <= reasons, "the seeded set must contain fitting and refused windings"
    _check(golden_report, "fit_status", results)


def test_gr23_max_traces_fit_matches_xcoil() -> None:
    """Catches a search that stops at the first refusal or never reaches the 400 limit."""
    for item in _items("gr23-maxtracesfit-seeded"):
        assert max_traces_fit(params_from_xcoil(normalised(item["params"]))) == item["output"], item
    assert any(math.isfinite(i["output"]) and i["output"] > 0 for i in _items("gr23-maxtracesfit-seeded"))
