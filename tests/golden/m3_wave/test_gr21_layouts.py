"""GR-21: `generate_wave` against Xcoil's raw wave layouts, object for object (REQ-F-35).

Each case is one `compute()` of Xcoil with `topology: wave`, mapped through `tools/golden/param_map/wave.json` to an
embodic design. The expected Layout is the GR-19 mapping of Xcoil's own output (`m1_layout/xcoil_map.py`).
"""

from functools import cache
from typing import Any

import pytest
from harness import INTEGRATED, GoldenCase, Tolerance, compare_prims, compare_scalar, compare_sequence, load_area
from m1_layout.xcoil_map import layout_from_xcoil

from embodic.generators.wave import generate_wave
from embodic.geometry.layout import Layout
from embodic.geometry.primitives import path_length_mm
from embodic.results import load_registry

from .param_map import design_from_xcoil

pytestmark = pytest.mark.req("REQ-F-35")

# test_plan.md GR-21 takes the GR-20 criterion: path distance at most 1e-6 mm. This test keeps 1e-9 mm. The arcs of an
# involute spline are rebuilt from three nearly collinear points, so one-ULP differences between V8 and glibc in
# cos/sin/tan reach 2e-12 mm in the arc centre and radius (measured, 10 cases); 1e-9 mm stays 500 times above that.
LAYOUT_MM = Tolerance("layout_mm", rel=0.0, abs=1e-9)

CASES = {cid: c for cid, c in load_area("wave").items() if c.fn == "waveRawLayout"}
STYLES = ("involute", "jog", "chord", "overlap")


def _raw(case: GoldenCase) -> Any:
    (call,) = case.calls
    return call.output


@cache
def _generated(case_id: str) -> tuple[Layout, Layout]:
    """(embodic layout, Xcoil layout mapped to embodic objects) of one case."""
    raw = _raw(CASES[case_id])
    stack = generate_wave(design_from_xcoil(raw["params"]), load_registry())
    assert not hasattr(stack, "issues"), f"{case_id}: Unbuildable {getattr(stack, 'issues', None)}"
    return stack.boards[0], layout_from_xcoil(raw)


def test_gr21_covers_every_style_with_two_four_and_six_layers_and_one_to_three_phases() -> None:
    """Catches a case list that drops a style, a layer count or a phase count (test_plan.md GR-21)."""
    params = [_raw(c)["params"] for c in CASES.values()]
    assert {p["waveStyle"] for p in params} == set(STYLES)
    for style in STYLES:
        styled = [p for p in params if p["waveStyle"] == style]
        assert {p["waveLayers"] for p in styled} >= {2, 4, 6}
        assert {p["phases"] for p in styled} >= {1, 2, 3}


@pytest.mark.parametrize("case_id", CASES)
def test_gr21_objects_have_xcoils_layer_net_phase_and_primitive_count(case_id: str) -> None:
    """Catches a dropped, duplicated or misordered track, link or interconnect object."""
    layout, expected = _generated(case_id)
    key = [(layout.copper_layers.index(p.layer), p.net, p.phase, p.element, len(p.primitives)) for p in layout.paths]
    golden = [
        (expected.copper_layers.index(p.layer), p.net, p.phase, p.element, len(p.primitives)) for p in expected.paths
    ]
    assert key == golden


@pytest.mark.parametrize("case_id", CASES)
def test_gr21_every_primitive_matches_xcoil(case_id: str, golden_report: Any) -> None:
    """Catches a wrong end-turn, fillet, taper or link: geometry, direction, width and role within 1e-12 mm."""
    layout, expected = _generated(case_id)
    golden = [q for p in expected.paths for q in p.primitives]
    actual = [q for p in layout.paths for q in p.primitives]
    assert [q.role for q in actual] == [q.role for q in golden]
    golden_report.check(case_id, compare_prims(golden, actual, LAYOUT_MM))


@pytest.mark.parametrize("case_id", CASES)
def test_gr21_copper_length_per_layer_matches_xcoil(case_id: str, golden_report: Any) -> None:
    """Catches a primitive of the wrong sweep: copper length per layer within 1e-9 relative."""
    layout, _ = _generated(case_id)
    for index, layer in enumerate(_raw(CASES[case_id])["layers"]):
        prims = [q for p in layout.paths if layout.copper_layers.index(p.layer) == index for q in p.primitives]
        golden_report.check(
            f"{case_id}/{layer['name']}", compare_scalar(layer["length"], path_length_mm(prims), INTEGRATED)
        )


@pytest.mark.parametrize("case_id", CASES)
def test_gr21_vias_pads_envelope_and_layer_heights_match_xcoil(case_id: str, golden_report: Any) -> None:
    """Catches a via or pad on the wrong ring angle, a missing terminal and a wrong copper envelope or layer z."""
    layout, expected = _generated(case_id)
    raw = _raw(CASES[case_id])
    xy = lambda items: [[i.x_mm, i.y_mm] for i in items]  # noqa: E731
    golden_report.check(f"{case_id}/vias", compare_sequence(xy(expected.vias), xy(layout.vias), LAYOUT_MM))
    assert [v.net for v in layout.vias] == [v.net for v in expected.vias]
    assert [v.role.value == "terminal" for v in layout.vias] == [v["terminal"] for v in raw["vias"]]
    golden_report.check(f"{case_id}/pads", compare_sequence(xy(expected.pads), xy(layout.pads), LAYOUT_MM))
    assert [(p.net, p.label, p.shape, p.drill_mm, p.layer is None) for p in layout.pads] == [
        (p.net, p.label, p.shape, p.drill_mm, p.layer is None) for p in expected.pads
    ]
    golden_report.check(
        f"{case_id}/envelope", compare_sequence([raw["rMinAll"], raw["rMaxAll"]], list(layout.envelope_mm), LAYOUT_MM)
    )
    z = [layout.copper_z_mm[n] for n in layout.copper_layers]
    golden_report.check(f"{case_id}/z", compare_sequence([layer["z"] for layer in raw["layers"]], z, LAYOUT_MM))


REFUSALS = {cid: c for cid, c in load_area("wave").items() if c.fn == "waveRefusal"}
REFUSAL_CODE = {
    "WAVE_MIN_POLES": "UNBUILDABLE_WAVE_MIN_POLES",
    "WAVE_SLOT_PITCH": "UNBUILDABLE_WAVE_SLOT_PITCH",
    "WAVE_OUTER_TIGHT": "UNBUILDABLE_WAVE_OUTER_TIGHT",
    "WAVE_INNER_TIGHT": "UNBUILDABLE_WAVE_INNER_TIGHT",
}


@pytest.mark.parametrize("case_id", REFUSALS)
def test_gr21_refuses_where_xcoil_reports_an_error(case_id: str) -> None:
    """Catches a refusal Xcoil does not make, a missed one, or another cause: same error codes as `compute()`."""
    (call,) = REFUSALS[case_id].calls
    assert call.output["ok"] is False and call.output["errors"]
    defaults = _raw(CASES["wave-involute-l2-m3-p16-t2"])["params"]
    result = generate_wave(design_from_xcoil({**defaults, **call.inputs["params"]}), load_registry())
    assert not hasattr(result, "boards"), f"{case_id}: built a board Xcoil refuses"
    assert [i.code for i in result.issues] == [REFUSAL_CODE[e["code"]] for e in call.output["errors"]]
