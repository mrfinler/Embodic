"""GR-20 DRC: Xcoil's clearance verdicts and exact-kernel values against embodic run_drc (D-006, EQ-30)."""

import math
from collections.abc import Mapping
from typing import Any

import pytest
from harness import (
    EXPECTED_DIFFS_DIR,
    XCOIL_DRC_SLACK_MM,
    Comparison,
    Diff,
    DiffKind,
    GoldenCase,
    apply_allow_list,
    compare_drc,
    load_allow_list,
    load_area,
)

from embodic.drc import DrcCheckKind, run_drc
from embodic.errors import Unbuildable
from embodic.generators import build_layout
from embodic.geometry.layout import Layout
from embodic.results import Registry, load_registry

from .design_map import design_from_xcoil

pytestmark = pytest.mark.req("REQ-F-34", "REQ-F-10")

AREA = load_area("serpentine")
BUILT = [c for c in AREA.values() if c.case_id.startswith("layout-") and "layers" in c.calls[0].output]
ALLOW = load_allow_list(EXPECTED_DIFFS_DIR / "serpentine.toml")
CLEARANCE_CODES = {"VIA_GAP", "TRACE_CLEARANCE", "PAD_CLEARANCE", "LINK_CLEARANCE", "PAD_PAD", "INTERCONNECT_CLEARANCE"}
XCOIL_QUANTITIES = ("traceClearance", "padClearance", "padPadClearance", "interconnectClearance", "linkClearance")
CLEARANCE_KINDS = (
    DrcCheckKind.TRACE_TRACE,
    DrcCheckKind.TRACE_VIA,
    DrcCheckKind.VIA_VIA,
    DrcCheckKind.PAD_TRACE,
    DrcCheckKind.PAD_PAD,
)


@pytest.fixture(scope="module")
def registry() -> Registry:
    """Return the shipped equation registry."""
    return load_registry()


def _raw(case: GoldenCase) -> Mapping[str, Any]:
    (call,) = case.calls
    return call.output


_REPORTS: dict[str, list[tuple[Layout, Any]]] = {}


def _reports(case: GoldenCase, registry: Registry) -> list[tuple[Layout, Any]]:
    if case.case_id not in _REPORTS:
        raw = _raw(case)
        design = design_from_xcoil(raw["params"], raw["rMinAll"], raw["rMaxAll"])
        stack = build_layout(design, registry)
        assert not isinstance(stack, Unbuildable)
        _REPORTS[case.case_id] = [(b, run_drc(b, design.drc_rules)) for b in stack.boards]
    return _REPORTS[case.case_id]


def _clearance_min(report: Any, kinds: tuple[DrcCheckKind, ...] = CLEARANCE_KINDS) -> float:
    values = [s.measured_min_mm for s in report.summaries if s.kind in kinds and s.measured_min_mm is not None]
    return min(values, default=math.inf)


def _clearance_violations(report: Any) -> int:
    return sum(v.kind in CLEARANCE_KINDS for v in report.violations)


def _xcoil_min(raw: Mapping[str, Any]) -> float:
    values = [raw["drc"][q] for q in XCOIL_QUANTITIES if raw["drc"].get(q) is not None]
    return min((v for v in values if math.isfinite(v)), default=math.inf)


def _verdict(case: GoldenCase, registry: Registry) -> Comparison:
    """Compare Xcoil's clearance verdict with embodic's under the band rule.

    Value diffs are dropped: Xcoil measures arcs by chords (sagitta up to 0.001 mm), so only the exact kernels are
    compared by value (below). Inside Xcoil's slack band the verdict is indeterminate, but embodic's value must still
    lie within the band's width of Xcoil's, so a gross disagreement cannot hide in the band.
    """
    raw = _raw(case)
    x_pass = not CLEARANCE_CODES & {i["code"] for i in raw["drc"]["issues"] if i["sev"] == "error"}
    e_min = min(_clearance_min(report) for _, report in _reports(case, registry))
    x_min = _xcoil_min(raw)
    path = "$.verdict"
    result = compare_drc(x_min, e_min, rule_mm=raw["params"]["clearance"], golden_pass=x_pass, path=path)
    diffs = [d for d in result.diffs if d.kind is not DiffKind.VALUE]
    if result.indeterminate and abs(x_min - e_min) > XCOIL_DRC_SLACK_MM:
        diffs.append(
            Diff(path, DiffKind.PASS_FAIL, x_min, e_min, "inside Xcoil's band, but embodic's value is far away")
        )
    return Comparison(diffs=tuple(diffs), indeterminate=result.indeterminate)


@pytest.mark.eqt("EQT-30-GR")
@pytest.mark.parametrize("case", BUILT, ids=lambda c: c.case_id)
def test_gr20_drc_verdict_matches_xcoil_outside_the_slack_band(
    case: GoldenCase, registry: Registry, golden_report: Any
) -> None:
    """Catches a generator whose board breaks a clearance rule Xcoil's board keeps, or the reverse, outside the band."""
    golden_report.check(case.case_id, apply_allow_list(_verdict(case, registry), case.case_id, ALLOW))


@pytest.mark.eqt("EQT-30-GR")
@pytest.mark.parametrize("case", BUILT, ids=lambda c: c.case_id)
def test_gr20_via_to_via_clearance_equals_xcoil_exactly(
    case: GoldenCase, registry: Registry, golden_report: Any
) -> None:
    """Catches a via at a shifted position: pad-to-pad distance is exact geometry in both tools (1e-6 mm)."""
    raw = _raw(case)
    rule = raw["params"]["clearance"]
    for board, (_, report) in enumerate(_reports(case, registry)):
        mine = _clearance_min(report, (DrcCheckKind.VIA_VIA,))
        if math.isfinite(mine) and raw["nBoards"] == 1:
            golden_report.check(
                f"{case.case_id}/board{board}/via-via",
                compare_drc(
                    raw["drc"]["padPadClearance"], mine, rule_mm=rule, golden_pass=raw["drc"]["padPadClearance"] >= rule
                ),
            )


def test_gr20_the_default_preset_passes_drc_in_both_tools(registry: Registry) -> None:
    """Catches the star ring (cut at its middle tap) or any stub being reported against the ring."""
    case = AREA["layout-default"]
    ((_, report),) = _reports(case, registry)
    assert _raw(case)["drc"]["ok"] and report.passed and not _clearance_violations(report)


def test_gr20_every_allow_listed_case_still_disagrees(registry: Registry) -> None:
    """Catches a stale allow-list entry: each listed case must still differ from Xcoil, else the entry is deleted."""
    listed = {e.case for e in ALLOW}
    for case in BUILT:
        if case.case_id in listed:
            assert _verdict(case, registry).diffs, f"{case.case_id} agrees with Xcoil now; remove its entry"
    assert listed <= {c.case_id for c in BUILT}
