"""GR-17: every M1 geometry fixture from Xcoil v3 against the embodic kernel that ports it."""

import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

import pytest
from harness import (
    EXACT,
    EXPECTED_DIFFS_DIR,
    KERNEL,
    KERNEL_MM,
    Comparison,
    GoldenCase,
    apply_allow_list,
    compare_prims,
    compare_scalar,
    compare_sequence,
    load_allow_list,
    load_area,
    near_threshold,
)
from m1_layout.xcoil_map import ROLE_BY_XCOIL_KIND, prim_from_record

from embodic.geometry.discretise import (
    DEFAULT_MAX_ANGLE_RAD,
    DEFAULT_MAX_SAGITTA_MM,
    DEFAULT_MAX_SEGMENT_MM,
    discretise_path,
    piece_ratios,
)
from embodic.geometry.distance import point_segment_distance_mm, segment_segment_distance_mm
from embodic.geometry.grid import grid_query, make_grid
from embodic.geometry.primitives import path_length_mm, primitive_length_mm
from embodic.geometry.transforms import Transform, reverse_path, transform_point, transform_primitive

pytestmark = pytest.mark.req("REQ-N-21")

CASES = load_area("m1")
ALLOW = load_allow_list(EXPECTED_DIFFS_DIR / "m1.toml")

# Pad clearance is DRC logic (U-M1c, GR-18); this unit ports no pad kernel.
NOT_GEOMETRY = frozenset({"padSegClearance", "padsClearance"})


@dataclass(frozen=True, slots=True)
class _XY:
    x1_mm: float
    y1_mm: float
    x2_mm: float
    y2_mm: float


def _chord(record: Mapping[str, Any]) -> _XY:
    return _XY(record["x1"], record["y1"], record["x2"], record["y2"])


def _xcoil_tf(tf: Mapping[str, Any], theta_g: float) -> Transform:
    return Transform(rotation_rad=tf["rot"], mirror_axis_rad=theta_g if tf["mirror"] else None)


def _or_default(value: float | None, default: float) -> float:
    """Xcoil's ``x || default``: 0, NaN and a missing value all take the default."""
    return default if value is None or value == 0 or math.isnan(value) else value


def _discretise_args(x: Mapping[str, Any]) -> tuple[float, float, float]:
    return (
        _or_default(x.get("hMax"), DEFAULT_MAX_SEGMENT_MM),
        _or_default(x.get("dAngMax"), DEFAULT_MAX_ANGLE_RAD),
        _or_default(x.get("sagTol"), DEFAULT_MAX_SAGITTA_MM),
    )


def _compare_discretise(x: Mapping[str, Any], golden: list[dict[str, Any]]) -> Comparison:
    prims = [prim_from_record(r) for r in x["prims"]]
    args = _discretise_args(x)
    actual = [
        {"x1": g.x1_mm, "y1": g.y1_mm, "x2": g.x2_mm, "y2": g.y2_mm, "s": g.s_mm, "len": g.length_mm}
        | {"w": g.width_mm, "pi": g.prim_index, "kind": g.role.value}
        for g in discretise_path(prims, *args)
    ]
    expected = [g | {"kind": ROLE_BY_XCOIL_KIND[g["kind"]].value} for g in golden]
    result = compare_sequence(expected, actual, KERNEL_MM)
    if len(expected) != len(actual):
        near = [i for i, p in enumerate(prims) if any(_on_integer(r) for r in piece_ratios(p, *args))]
        if near:
            return Comparison(indeterminate=(f"piece count of primitives {near} sits on a ceil boundary",))
    return result


def _on_integer(ratio: float) -> bool:
    """Whether a ratio that piece_count takes ceil of lies within 1e-9 rel. of an integer (test_plan.md 3)."""
    return ratio > 0 and near_threshold(ratio, float(math.floor(ratio + 0.5)))


def _compare_grid(x: Mapping[str, Any], golden: Any) -> Comparison:
    grid = make_grid([_chord(s) for s in x["segs"]], x["cell"])
    entries = [[f"{cx},{cy}", list(indices)] for (cx, cy), indices in grid.cells.items()]
    return compare_sequence([golden], [{"cell": grid.cell_mm, "entries": entries}], EXACT)


def _compare_query(x: Mapping[str, Any], golden: Any) -> Comparison:
    grid = make_grid([_chord(s) for s in x["segs"]], x["cell"])
    return compare_sequence(golden, list(grid_query(grid, x["x"], x["y"], x["radius"])), EXACT)


PORTS: Mapping[str, Callable[[Mapping[str, Any], Any], Comparison]] = {
    "primLength": lambda x, g: compare_scalar(g, primitive_length_mm(prim_from_record(x["prim"])), KERNEL),
    "primsLength": lambda x, g: compare_scalar(g, path_length_mm([prim_from_record(r) for r in x["prims"]]), KERNEL),
    "primStart": lambda x, g: compare_sequence(g, list(prim_from_record(x["prim"]).start_point()), KERNEL_MM),
    "primEnd": lambda x, g: compare_sequence(g, list(prim_from_record(x["prim"]).end_point()), KERNEL_MM),
    "reversePrims": lambda x, g: compare_prims(g, reverse_path([prim_from_record(r) for r in x["prims"]]), KERNEL_MM),
    "tfPoint": lambda x, g: compare_sequence(
        g, list(transform_point(_xcoil_tf(x["tf"], x["thetaG"]), x["x"], x["y"])), KERNEL_MM
    ),
    "tfPrim": lambda x, g: compare_prims(
        [g], [transform_primitive(_xcoil_tf(x["tf"], x["thetaG"]), prim_from_record(x["prim"]))], KERNEL_MM
    ),
    "discretize": _compare_discretise,
    "ptSegDist": lambda x, g: compare_scalar(
        g, point_segment_distance_mm(x["px"], x["py"], _chord(x["seg"])), KERNEL_MM
    ),
    "segSegDist": lambda x, g: compare_scalar(
        g, segment_segment_distance_mm(_chord(x["a"]), _chord(x["b"])), KERNEL_MM
    ),
    "makeGrid": _compare_grid,
    "gridQuery": _compare_query,
}


def test_gr17_every_m1_fixture_is_ported_or_owned_elsewhere() -> None:
    """Catches a fixture function that no test compares: it would pass GR-17 by being skipped silently."""
    assert {case.fn for case in CASES.values()} == set(PORTS) | NOT_GEOMETRY


# Registry test ids (interfaces.md section 3.1): EQ-03 track length and EQ-30 DRC distance and grid kernels.
EQT_GR_BY_FN = {
    "primLength": "EQT-03-GR",
    "primsLength": "EQT-03-GR",
    "discretize": "EQT-03-GR",
    "ptSegDist": "EQT-30-GR",
    "segSegDist": "EQT-30-GR",
    "makeGrid": "EQT-30-GR",
    "gridQuery": "EQT-30-GR",
}


def _param(case: GoldenCase) -> Any:
    marks = [pytest.mark.eqt(EQT_GR_BY_FN[case.fn])] if case.fn in EQT_GR_BY_FN else []
    return pytest.param(case, marks=marks, id=case.case_id)


@pytest.mark.parametrize("case", [_param(c) for c in CASES.values() if c.fn in PORTS])
def test_gr17_kernel_matches_xcoil(case: GoldenCase, golden_report: Any) -> None:
    """Catches any port drift from Xcoil: a different count, coordinate (1e-12 mm), length or visiting order."""
    port = PORTS[case.fn]
    for i, call in enumerate(case.calls):
        result = apply_allow_list(port(call.inputs, call.output), case.case_id, ALLOW)
        golden_report.check(f"{case.case_id}[{i}]", result)
