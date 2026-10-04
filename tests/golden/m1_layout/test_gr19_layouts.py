"""GR-19: Xcoil's raw layout of each topology, mapped to a Layout and an embodic board dump (REQ-F-40)."""

from collections import Counter
from typing import Any

import pytest
from harness import INTEGRATED, KERNEL_MM, GoldenCase, compare_prims, compare_scalar, compare_sequence, load_area

from embodic.geometry.primitives import path_length_mm
from embodic.io.board_dump import decode_board_dump, dump_layout, encode_board_dump

from .xcoil_map import layout_from_xcoil

pytestmark = pytest.mark.req("REQ-F-40")

CASES = list(load_area("m1_layout").values())


def _raw(case: GoldenCase) -> Any:
    (call,) = case.calls
    return call.output


def test_gr19_covers_the_three_xcoil_topologies() -> None:
    """Catches a case list that drops a topology: GR-19 needs one layout per Xcoil builder."""
    assert sorted(_raw(c)["params"]["topology"] for c in CASES) == ["sector", "serpentine", "wave"]


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.case_id)
def test_gr19_dump_counts_equal_the_raw_layout(case: GoldenCase) -> None:
    """Catches a mapper or writer that drops or duplicates primitives, vias, pads or outline pieces."""
    raw = _raw(case)
    dump = dump_layout(layout_from_xcoil(raw), case_id=case.case_id)
    per_layer = Counter(p["layer"] for p in dump["primitives"])
    assert [per_layer[layer["index"]] for layer in raw["layers"]] == [
        sum(len(o["prims"]) for o in layer["objs"]) for layer in raw["layers"]
    ]
    assert len(dump["objects"]) == sum(len(layer["objs"]) for layer in raw["layers"])
    assert (len(dump["vias"]), len(dump["pads"])) == (len(raw["vias"]), len(raw["pads"]))
    assert len(dump["outline"]["board"]) == len(raw["mech"]["prims"])
    assert len(dump["outline"]["holes"]) == len(raw["mech"]["holes"])


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.case_id)
def test_gr19_copper_length_per_layer_matches_xcoil(case: GoldenCase, golden_report: Any) -> None:
    """Catches an arc length from the wrong sweep or radius: per-layer copper length within 1e-9 rel. of Xcoil's."""
    raw = _raw(case)
    layout = layout_from_xcoil(raw)
    for layer in raw["layers"]:
        prims = [p for path in layout.paths if path.layer == layer["name"] for p in path.primitives]
        golden_report.check(
            f"{case.case_id}/{layer['name']}", compare_scalar(layer["length"], path_length_mm(prims), INTEGRATED)
        )


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.case_id)
def test_gr19_every_primitive_matches_xcoil_geometry_and_end_points(case: GoldenCase, golden_report: Any) -> None:
    """Catches a sweep sign or start angle lost in mapping: geometry and dumped end points agree with Xcoil's.

    The end points in the dump are computed by embodic from start and sweep; the raw ones by Xcoil from a1 and a2.
    """
    raw = _raw(case)
    layout = layout_from_xcoil(raw)
    dump = dump_layout(layout, case_id=case.case_id)
    golden = [r for layer in raw["layers"] for o in layer["objs"] for r in o["prims"]]
    actual = [p for path in layout.paths for p in path.primitives]
    golden_report.check(case.case_id, compare_prims(golden, actual, KERNEL_MM))
    ends = [[r["start"], r["end"]] for r in golden]
    golden_report.check(
        f"{case.case_id}/ends", compare_sequence(ends, [[p["start"], p["end"]] for p in dump["primitives"]], KERNEL_MM)
    )


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.case_id)
def test_gr19_write_read_write_is_byte_identical(case: GoldenCase) -> None:
    """Catches number text that does not survive a read (-0.0, integers, long mantissas) or unsorted keys."""
    text = encode_board_dump(dump_layout(layout_from_xcoil(_raw(case)), case_id=case.case_id))
    assert encode_board_dump(decode_board_dump(text)) == text
