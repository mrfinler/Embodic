"""GR-18 band rule: embodic run_drc against Xcoil's drcObjects clearance and Xcoil's own pass/fail (D-006).

Each fixture holds the rule (Xcoil's ``p.clearance``), Xcoil's measured clearance and Xcoil's verdict. The cases are
straight traces, which Xcoil's discretisation keeps exact, so both tools measure the same distance.
"""

import os
import shutil
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest
from harness import DATA_DIR, XCOIL_DRC_SLACK_MM, GoldenCase, Verdict, compare_drc, d006_pass, load_area
from m1_layout.xcoil_map import prim_from_record

from embodic.drc import DrcCheckKind, run_drc
from embodic.geometry.circuit import Circuit
from embodic.geometry.layout import BoardOutline, Layout
from embodic.geometry.paths import CopperPath
from embodic.model.drc_rules import DrcRules
from embodic.model.vocabulary import ConnectionTopology, TopologyKind

pytestmark = pytest.mark.req("REQ-F-10")

REPO_ROOT = Path(__file__).resolve().parents[3]
DUMPER = REPO_ROOT / "tools" / "golden" / "dump_xcoil.mjs"
CASE_FILE = REPO_ROOT / "tools" / "golden" / "cases" / "m1_drc.json"
ENGINE = Path(os.environ.get("XCOIL_ENGINE", "/home/claude/serpentine/src/engine.js"))

CASES = load_area("m1_drc")
REGIONS = ("below-band", "in-band", "at-rule")
VERDICT_BY_REGION = {"below-band": Verdict.MATCH, "in-band": Verdict.INDETERMINATE, "at-rule": Verdict.MATCH}


def _region(case: GoldenCase) -> str:
    (region,) = case.tags & set(REGIONS)
    return region


def _in_region(region: str, value_mm: float, rule_mm: float) -> bool:
    if region == "below-band":
        return value_mm < rule_mm - XCOIL_DRC_SLACK_MM
    if region == "in-band":
        return rule_mm - XCOIL_DRC_SLACK_MM <= value_mm < rule_mm
    return value_mm >= rule_mm


def _layout(objs: list[Mapping[str, Any]]) -> Layout:
    """One copper path per Xcoil object on one layer, each on its own net, so no exemption applies."""
    paths = tuple(
        CopperPath(
            id=i,
            layer="F.Cu",
            net=f"OBJ{i}",
            primitives=tuple(prim_from_record(r) for r in obj["prims"]),
            phase=None,
            element=None,
            polarity=0,
        )
        for i, obj in enumerate(objs)
    )
    return Layout(
        topology=TopologyKind.SERPENTINE,
        copper_layers=("F.Cu",),
        copper_z_mm={"F.Cu": 0.0},
        paths=paths,
        vias=(),
        pads=(),
        outline=BoardOutline(outer=(), cutouts=(), holes=()),
        circuit=Circuit(phases=(), topology=ConnectionTopology.STAR, interconnect_path_ids=()),
        symmetry=None,
        envelope_mm=(0.0, 50.0),
    )


def _rules(clearance_mm: float) -> DrcRules:
    """Xcoil applies its one ``clearance`` to every pair (engine.js runDrc l.756)."""
    return DrcRules(
        trace_clearance_mm=clearance_mm,
        via_clearance_mm=clearance_mm,
        edge_clearance_mm=clearance_mm,
        hole_clearance_mm=clearance_mm,
        min_trace_width_mm=0.1,
        min_drill_mm=0.2,
        min_annular_ring_mm=0.1,
    )


def test_gr18_band_cases_cover_the_three_regions_of_the_band_rule() -> None:
    """Catches a case list that loses a region of the band rule.

    Also catches a case whose Xcoil value left its tagged region after an engine change, and a harness slack that no
    longer equals the slack Xcoil applied.
    """
    assert sorted(_region(c) for c in CASES.values()) == sorted(REGIONS)
    for case in CASES.values():
        (call,) = case.calls
        assert call.output["slack"] == XCOIL_DRC_SLACK_MM, case.case_id
        assert _in_region(_region(case), call.output["clearance"], call.inputs["clearance"]), case.case_id


@pytest.mark.eqt("EQT-30-GR")
@pytest.mark.parametrize("case", CASES.values(), ids=lambda c: c.case_id)
def test_gr18_run_drc_agrees_with_xcoil_outside_the_slack_band(case: GoldenCase, golden_report: Any) -> None:
    """Catches embodic's trace clearance drifting from Xcoil's beyond 1e-6 mm, or a pass/fail flip outside the band.

    Also catches run_drc reporting (or omitting) a violation against the D-006 verdict of its own measured value.
    """
    (call,) = case.calls
    rule_mm, golden = call.inputs["clearance"], call.output
    report = run_drc(_layout(call.inputs["objs"]), _rules(rule_mm))
    assert report is not None
    (summary,) = [s for s in report.summaries if s.kind is DrcCheckKind.TRACE_TRACE]
    assert summary.least_clearance_mm is not None
    comparison = compare_drc(
        golden["clearance"], summary.least_clearance_mm, rule_mm=rule_mm, golden_pass=golden["pass"]
    )
    assert comparison.verdict is VERDICT_BY_REGION[_region(case)], comparison.describe()
    golden_report.check(case.case_id, comparison)
    reported = any(v.kind is DrcCheckKind.TRACE_TRACE for v in report.violations)
    assert reported is not d006_pass(summary.least_clearance_mm, rule_mm)


@pytest.mark.skipif(shutil.which("node") is None or not ENGINE.is_file(), reason="needs Node and the Xcoil engine")
def test_m1_drc_fixtures_equal_a_fresh_dump(tmp_path: Path) -> None:
    """Catches fixtures that are stale against m1_drc.json or the engine, or a non-deterministic area module."""
    subprocess.run(["node", str(DUMPER), str(CASE_FILE), "--out", str(tmp_path)], check=True, capture_output=True)
    committed = sorted(p.name for p in (DATA_DIR / "m1_drc").glob("*.json"))
    assert sorted(p.name for p in tmp_path.glob("*.json")) == committed
    stale = [n for n in committed if (tmp_path / n).read_bytes() != (DATA_DIR / "m1_drc" / n).read_bytes()]
    assert stale == []
