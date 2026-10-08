"""GR-20: serpentine layouts against Xcoil's raw layouts, board by board (REQ-F-34)."""

import math
from collections import Counter
from collections.abc import Mapping
from dataclasses import astuple
from itertools import groupby
from typing import Any

import pytest
from harness import KERNEL_MM, GoldenCase, compare_scalar, compare_sequence, load_area

from embodic.errors import Unbuildable
from embodic.generators import build_layout
from embodic.geometry.layout import BoardStack
from embodic.model.design import DesignParameters
from embodic.results import Registry, load_registry

from .design_map import design_from_xcoil
from .layout_compare import (
    SAMPLED_MM,
    Z_MM,
    board_layers,
    compare_points,
    compare_streams,
    merge_ring_cuts,
    xcoil_via_role,
)

pytestmark = pytest.mark.req("REQ-F-34")

AREA = load_area("serpentine")
LAYOUT_CASES = [c for c in AREA.values() if c.case_id.startswith("layout-")]
BUILT = [c for c in LAYOUT_CASES if "layers" in c.calls[0].output]
REFUSED = [c for c in LAYOUT_CASES if "layers" not in c.calls[0].output]
PHASE_LETTERS = "ABC"


def _raw(case: GoldenCase) -> Mapping[str, Any]:
    (call,) = case.calls
    return call.output


def _design(raw: Mapping[str, Any]) -> DesignParameters:
    return design_from_xcoil(
        raw["params"], raw.get("rMinAll", raw["params"]["rIn"]), raw.get("rMaxAll", raw["params"]["rOut"])
    )


@pytest.fixture(scope="module")
def registry() -> Registry:
    """Return the shipped equation registry."""
    return load_registry()


_STACKS: dict[str, BoardStack] = {}


def _stack(case: GoldenCase, registry: Registry) -> BoardStack:
    """Build each case once per run; the generator is pure, so tests may share the stack."""
    if case.case_id not in _STACKS:
        result = build_layout(_design(_raw(case)), registry)
        assert not isinstance(result, Unbuildable), result
        _STACKS[case.case_id] = result
    return _STACKS[case.case_id]


def test_gr20_covers_the_brief_case_set() -> None:
    """Catches a case list that drops a stack mode, a pair connection, a layer order, a corner style or a refusal."""
    params = [c.calls[0].output["params"] for c in BUILT]
    assert {p["stackMode"] for p in params} == {"single", "perPhase"}
    assert {p["pairConnection"] for p in params} == {"series", "parallel"}
    assert {p["layerOrder"] for p in params} == {"grouped", "interleaved"}
    assert {p["cornerStyle"] for p in params} == {"round", "sharp"}
    assert {p["layersPerPhase"] for p in params} >= {1, 2, 4}
    assert {p["phases"] for p in params} == {1, 2, 3}
    assert {p["interconnect"] for p in params} == {True, False}
    assert {p["connection"] for p in params} == {"star", "delta", "open"}
    assert {p["boardGap"] for p in params if p["stackMode"] == "perPhase"} >= {0.1, 0.5}
    assert {c.calls[0].output["errors"][0] for c in REFUSED} == {
        "R_TOO_SMALL",
        "BUNDLE_TOO_WIDE",
        "GEOMETRY",
        "ACUTE_CORNER",
    }
    assert len(BUILT) >= 40


@pytest.mark.parametrize("case", REFUSED, ids=lambda c: c.case_id)
def test_gr20_refusal_matches_xcoil_error(case: GoldenCase, registry: Registry) -> None:
    """Catches a build that returns copper where Xcoil refuses, or refuses with another reason."""
    raw = _raw(case)
    result = build_layout(_design(raw), registry)
    assert isinstance(result, Unbuildable)
    assert [i.code for i in result.issues] == [f"UNBUILDABLE_SERPENTINE_{raw['errors'][0]}"]


@pytest.mark.parametrize("case", BUILT, ids=lambda c: c.case_id)
def test_gr20_board_count_and_stack_thickness(case: GoldenCase, registry: Registry) -> None:
    """Catches a wrong board count, board gap or stack thickness (Xcoil nBoards and statorThickness, l.689)."""
    raw = _raw(case)
    stack = _stack(case, registry)
    assert len(stack.boards) == raw["nBoards"]
    assert stack.board_gap_mm == (raw["params"]["boardGap"] if raw["nBoards"] > 1 else 0.0)
    assert not compare_scalar(raw["statorThickness"], stack.stack_thickness_mm, KERNEL_MM).diffs


def _xcoil_layers(raw: Mapping[str, Any], board: int) -> list[Mapping[str, Any]]:
    return [layer for layer in raw["layers"] if layer["board"] == board]


@pytest.mark.parametrize("case", BUILT, ids=lambda c: c.case_id)
def test_gr20_copper_matches_xcoil_layer_by_layer(case: GoldenCase, registry: Registry, golden_report: Any) -> None:
    """Catches a changed primitive count, role, width or position (sampled path distance within 1e-6 mm)."""
    raw = _raw(case)
    for board, layout in enumerate(_stack(case, registry).boards):
        mine = board_layers(layout)
        xcoil = _xcoil_layers(raw, board)
        assert len(mine) == len(xcoil)
        for li, (layer, prims) in enumerate(zip(xcoil, mine, strict=True)):
            golden = [rec for obj in layer["objs"] for rec in obj["prims"]]
            golden_report.check(
                f"{case.case_id}/board{board}/{layer['name']}", compare_streams(golden, merge_ring_cuts(prims), "$")
            )
            z = layout.copper_z_mm[layout.copper_layers[li]]
            assert not compare_scalar(layer["z"], z, Z_MM).diffs, (layer["name"], layer["z"], z)


def _phase_net(layer: Mapping[str, Any]) -> str:
    return f"PHASE_{PHASE_LETTERS[layer['phase']]}"


@pytest.mark.parametrize("case", BUILT, ids=lambda c: c.case_id)
def test_gr20_paths_keep_xcoil_objects_and_nets(case: GoldenCase, registry: Registry) -> None:
    """Catches a lost strand or bus path, a phase net on interconnect copper or an interconnect net on phase copper."""
    raw = _raw(case)
    for board, layout in enumerate(_stack(case, registry).boards):
        for layer in _xcoil_layers(raw, board):
            name = layout.copper_layers[layer["indexInBoard"]]
            mine = [p for p in layout.paths if p.layer == name]
            phase_objs = [o for o in layer["objs"] if o["kind"] != "ic"]
            phase_paths = [p for p in mine if p.net.startswith("PHASE_")]
            assert [len(p.primitives) for p in phase_paths] == [len(o["prims"]) for o in phase_objs]
            assert {p.net for p in phase_paths} <= {_phase_net(layer)}
            xcoil_ic = [o["net"] for o in layer["objs"] if o["kind"] == "ic"]
            mine_ic = [p.net for p in mine if not p.net.startswith("PHASE_")]
            assert [n for n, _ in groupby(mine_ic)] == [n for n, _ in groupby(xcoil_ic)]
        assert {p.id for p in layout.paths if p.net.startswith("PHASE_")}.isdisjoint(
            layout.circuit.interconnect_path_ids
        )


@pytest.mark.parametrize("case", BUILT, ids=lambda c: c.case_id)
def test_gr20_vias_match_xcoil(case: GoldenCase, registry: Registry, golden_report: Any) -> None:
    """Catches a via at the wrong place, with the wrong role or net, or on the wrong board."""
    raw = _raw(case)
    for board, layout in enumerate(_stack(case, registry).boards):
        golden = [v for v in raw["vias"] if raw["nBoards"] == 1 or v["phase"] == board]
        assert [xcoil_via_role(v) for v in golden] == [v.role for v in layout.vias]
        assert [f"PHASE_{PHASE_LETTERS[v['phase']]}" for v in golden] == [v.net for v in layout.vias]
        golden_report.check(
            f"{case.case_id}/board{board}/vias",
            compare_points([(v["x"], v["y"]) for v in golden], [(v.x_mm, v.y_mm) for v in layout.vias], "$"),
        )
        assert {(v.drill_mm, v.pad_mm) for v in layout.vias} <= {(raw["params"]["viaDrill"], raw["params"]["viaPad"])}
        names = layout.copper_layers
        assert {(v.layer_from, v.layer_to) for v in layout.vias} <= {(names[0], names[-1])}


@pytest.mark.parametrize("case", BUILT, ids=lambda c: c.case_id)
def test_gr20_pads_and_interconnect_match_xcoil(case: GoldenCase, registry: Registry, golden_report: Any) -> None:
    """Catches a missing or misplaced terminal pad, or interconnect copper on a one-board-per-phase stack."""
    raw = _raw(case)
    stack = _stack(case, registry)
    if raw["nBoards"] > 1:
        assert all(not b.pads and not b.circuit.interconnect_path_ids for b in stack.boards)
        return
    (layout,) = stack.boards
    assert [p.net for p in layout.pads] == [p["net"] for p in raw["pads"]]
    assert [p.label for p in layout.pads] == [p["label"] for p in raw["pads"]]
    golden_report.check(
        f"{case.case_id}/pads",
        compare_points([(p["x"], p["y"]) for p in raw["pads"]], [(p.x_mm, p.y_mm) for p in layout.pads], "$"),
    )
    for pad, g in zip(layout.pads, raw["pads"], strict=True):
        assert (pad.shape, pad.width_mm, pad.height_mm, pad.drill_mm) == (g["shape"], g["w"], g["h"], g["drill"])
        assert pad.layer == (layout.copper_layers[g["layer"]] if g["smd"] else None)
    xcoil_nets = Counter(o["net"] for layer in raw["layers"] for o in layer["objs"] if o["kind"] == "ic")
    assert set(Counter(layout.paths[i].net for i in layout.circuit.interconnect_path_ids)) == set(xcoil_nets)


@pytest.mark.parametrize("case", BUILT, ids=lambda c: c.case_id)
def test_gr20_envelope_matches_xcoil(case: GoldenCase, registry: Registry) -> None:
    """Catches an envelope that leaves out the interconnect pads or the series links (Xcoil rMinAll, rMaxAll)."""
    raw = _raw(case)
    for layout in _stack(case, registry).boards:
        golden = [raw["rMinAll"], raw["rMaxAll"]]
        # a one-board-per-phase board holds one phase; the envelope of the Xcoil layout covers all of them
        if raw["nBoards"] == 1:
            assert not compare_sequence(golden, list(layout.envelope_mm), SAMPLED_MM).diffs, layout.envelope_mm
        else:
            assert layout.envelope_mm[0] >= raw["rMinAll"] - 1e-6 and layout.envelope_mm[1] <= raw["rMaxAll"] + 1e-6


def test_gr20_ring_cut_is_the_only_primitive_difference(registry: Registry) -> None:
    """Catches a port that cuts rings elsewhere: only a star ring with a middle tap has one more arc than Xcoil."""
    extra = 0
    for case in BUILT:
        raw = _raw(case)
        for layout, board in zip(_stack(case, registry).boards, range(raw["nBoards"]), strict=True):
            mine = sum(len(p.primitives) for p in layout.paths)
            theirs = sum(len(o["prims"]) for layer in _xcoil_layers(raw, board) for o in layer["objs"])
            cut = 1 if raw["params"]["connection"] == "star" and raw["pads"] else 0
            assert mine - theirs == cut, case.case_id
            extra += mine - theirs
    assert extra > 0, "no case has a star ring, so the cut is not exercised"


def test_gr20_layout_is_deterministic(registry: Registry) -> None:
    """Catches hidden state: the same design built twice gives the same stack hash."""
    case = AREA["layout-default"]
    assert _stack(case, registry).stack_hash == _stack(case, registry).stack_hash


def test_gr20_every_coordinate_is_finite(registry: Registry) -> None:
    """Catches NaN or infinity in any coordinate of a built board (no silent NaN)."""
    for case in BUILT:
        for layout in _stack(case, registry).boards:
            values = [
                v for path in layout.paths for prim in path.primitives for v in astuple(prim) if isinstance(v, float)
            ]
            assert values
            assert all(math.isfinite(v) for v in values), case.case_id
