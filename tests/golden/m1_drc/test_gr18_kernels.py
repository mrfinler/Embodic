"""GR-18: Xcoil segSegDist, padSegClearance and padsClearance fixtures against embodic.drc (kernel class, 1e-12 mm).

Xcoil has no arc distance helper (it discretises arcs, engine.js drcObjects l.1698), so the arc kernels have no golden
counterpart; UT-DRC-02 checks them against closed forms and dense sampling.
"""

import math
from collections.abc import Mapping
from dataclasses import replace
from typing import Any

import numpy as np
import pytest
from harness import (
    EXPECTED_DIFFS_DIR,
    KERNEL_MM,
    Comparison,
    GoldenCase,
    apply_allow_list,
    compare_scalar,
    load_allow_list,
    load_area,
)

from embodic.drc import DrcCheckKind, min_distance_line_line, run_drc
from embodic.drc.kernels import D, pad_closest
from embodic.geometry.circuit import Circuit
from embodic.geometry.layout import BoardOutline, Layout, Pad, Via, ViaRole
from embodic.model.drc_rules import DrcRules
from embodic.model.vocabulary import ConnectionTopology, TopologyKind, ViaSpan

# segsegdist-inf-coordinate feeds Infinity on purpose; NumPy warns where Xcoil's JS silently yields NaN.
pytestmark = [pytest.mark.req("REQ-F-10"), pytest.mark.filterwarnings("ignore:invalid value:RuntimeWarning")]

CASES = load_area("m1")
ALLOW = load_allow_list(EXPECTED_DIFFS_DIR / "m1.toml")
DRC_FUNCTIONS = ("segSegDist", "padSegClearance", "padsClearance")
RULES = DrcRules(
    trace_clearance_mm=0.2,
    via_clearance_mm=0.2,
    edge_clearance_mm=0.2,
    hole_clearance_mm=0.2,
    min_trace_width_mm=0.1,
    min_drill_mm=0.2,
    min_annular_ring_mm=0.1,
)

# run_drc measures only pairs within reach of its largest rule; Xcoil padsClearance measures every pair.
WIDE_REACH = replace(RULES, via_clearance_mm=20.0)


def _pad(record: Mapping[str, Any], pid: int, net: str) -> Pad:
    """Xcoil pad record to a Pad: no shape means round, whose diameter is ``dia`` (engine.js padSegClearance)."""
    shape = record.get("shape") or "round"
    w, h = (record["dia"], record["dia"]) if shape == "round" else (record["w"], record["h"])
    return Pad(
        id=pid,
        x_mm=record["x"],
        y_mm=record["y"],
        shape=shape,
        width_mm=w,
        height_mm=h,
        rotation_rad=record.get("rot") or 0.0,
        drill_mm=0.0,
        layer=None,
        net=net,
        label="U",
    )


def _row(seg: Mapping[str, Any]) -> np.ndarray:
    return np.array([[seg["x1"], seg["y1"], seg["x2"], seg["y2"], 0.0]])


def _pads_layout(x: Mapping[str, Any]) -> Layout:
    """Build a layout of pads and vias; a pad's ``viaIndex`` via gets the pad's net, which makes it the pad's own."""
    pads = [_pad(p, i, f"PAD{i}") for i, p in enumerate(x["pads"])]
    owner = {p["viaIndex"]: i for i, p in enumerate(x["pads"]) if p.get("viaIndex") is not None}
    vias = [
        Via(
            id=i,
            x_mm=v["x"],
            y_mm=v["y"],
            drill_mm=0.3,
            pad_mm=x["viaPad"],
            role=ViaRole.TERMINAL,
            span=ViaSpan.THROUGH,
            layer_from="F.Cu",
            layer_to="B.Cu",
            net=f"PAD{owner[i]}" if i in owner else f"VIA{i}",
        )
        for i, v in enumerate(x["vias"])
    ]
    return Layout(
        topology=TopologyKind.SPIRAL,
        copper_layers=("F.Cu", "B.Cu"),
        copper_z_mm={"F.Cu": 0.0, "B.Cu": 1.6},
        paths=(),
        vias=tuple(vias),
        pads=tuple(pads),
        outline=BoardOutline(outer=(), cutouts=(), holes=()),
        circuit=Circuit(phases=(), topology=ConnectionTopology.STAR, interconnect_path_ids=()),
        symmetry=None,
        envelope_mm=(0.0, 50.0),
    )


def _pads_clearance(x: Mapping[str, Any], golden: Mapping[str, Any]) -> Comparison:
    """Compare the clearance only: Xcoil's ``at`` is the first pad's centre, embodic's the closest-point midpoint."""
    report = run_drc(_pads_layout(x), WIDE_REACH)
    assert report is not None
    least = {s.kind: s.measured_min_mm for s in report.summaries}.get(DrcCheckKind.PAD_PAD)
    return compare_scalar(golden["clearance"], math.inf if least is None else least, KERNEL_MM, path="$.clearance")


PORTS = {
    "segSegDist": lambda x, g: compare_scalar(
        g, float(min_distance_line_line(_row(x["a"]), _row(x["b"]))[0]), KERNEL_MM
    ),
    "padSegClearance": lambda x, g: compare_scalar(
        g, float(pad_closest(_pad(x["pad"], 0, "P"), _row(x["seg"]), False)[D][0]), KERNEL_MM
    ),
    "padsClearance": _pads_clearance,
}


def test_gr18_covers_the_nine_pad_fixtures_and_the_segment_fixtures() -> None:
    """Catches a pad fixture that no test compares (it would pass GR-18 by being skipped)."""
    pad_cases = [c for c in CASES.values() if c.fn in ("padSegClearance", "padsClearance")]
    assert len(pad_cases) == 9
    assert any(c.fn == "segSegDist" for c in CASES.values())


@pytest.mark.eqt("EQT-30-GR")
@pytest.mark.parametrize("case", [c for c in CASES.values() if c.fn in DRC_FUNCTIONS], ids=lambda c: c.case_id)
def test_gr18_drc_kernel_matches_xcoil(case: GoldenCase, golden_report: Any) -> None:
    """Catches drift from Xcoil's segment and pad kernels beyond 1e-12 mm, or a wrong own-via exemption."""
    for i, call in enumerate(case.calls):
        result = apply_allow_list(PORTS[case.fn](call.inputs, call.output), case.case_id, ALLOW)
        golden_report.check(f"{case.case_id}[{i}]", result)
