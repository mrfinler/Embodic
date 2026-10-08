"""Items 1 and 3 (U-V3): embodic's serpentine and wave BoardStacks against Agent 4's own Xcoil dumps."""

import dataclasses
import math

import pytest
from cases import SERPENTINE, WAVE, all_cases, have_xcoil, xcoil_dumps
from layouts import compare_case
from own_map import Copper, Land, boards_from_embodic, boards_from_xcoil, compare_layer, match_lands
from subject import stack_for

pytestmark = [
    pytest.mark.req("REQ-F-34", "REQ-F-35"),
    pytest.mark.skipif(not have_xcoil(), reason="needs node and the read-only Xcoil engine"),
]

# GR-20 compares serpentine copper within 1e-6 mm (U-M3a); GR-21 wave copper within 1e-9 mm (D-035 f).
TOL_MM = {**dict.fromkeys(SERPENTINE, 1e-6), **dict.fromkeys(WAVE, 1e-9)}
# U-M3a deviation: the star ring is cut at the middle tap, one more ring arc than Xcoil, same length.
RING_CUT = {"s-radial-t4", "s-sharp-inner-4l-series"}
CASES = sorted(all_cases())


def test_xcoil_builds_every_case() -> None:
    """Catches a parameter set that Xcoil refuses, which would silently shrink the comparison."""
    refused = {k: d["errors"] for k, d in xcoil_dumps().items() if "layers" not in d}
    assert refused == {}


@pytest.mark.parametrize("case_id", CASES)
def test_boards_layers_and_z(case_id: str) -> None:
    """Catches a lost board of a per-phase stack, a missing layer, or a layer z off by a board pitch."""
    d = compare_case(case_id)
    assert d.boards[0] == d.boards[1]
    assert all(x == e for x, e in d.layers), d.layers
    assert d.z_max_mm <= 1e-9


@pytest.mark.parametrize("case_id", CASES)
def test_counts_and_lengths_by_role(case_id: str) -> None:
    """Catches a dropped end turn, fillet, stub, link or bus, and a primitive moved to another role."""
    d = compare_case(case_id)
    expected = {"ring": 1} if case_id in RING_CUT else {}
    assert d.count_diffs == expected
    assert d.length_max_mm <= 1e-9


@pytest.mark.parametrize("case_id", CASES)
def test_sampled_distance_widths_and_roles(case_id: str) -> None:
    """Catches copper moved, mirrored or rotated by more than the GR tolerance, and a width or role swapped."""
    d = compare_case(case_id)
    assert d.sampled_max_mm <= TOL_MM[case_id]
    assert (d.width_mismatches, d.role_mismatches) == (0, 0)


@pytest.mark.parametrize("case_id", CASES)
def test_vias_and_pads(case_id: str) -> None:
    """Catches a missing or extra via or pad, a land moved to another board, and a wrong pad diameter."""
    d = compare_case(case_id)
    assert d.vias[0] == d.vias[1] and d.pads[0] == d.pads[1]
    assert d.via_pos_mm <= TOL_MM[case_id] and d.pad_pos_mm <= TOL_MM[case_id]
    assert d.pad_dia_mm <= 1e-9


def test_per_phase_stack_board_by_board() -> None:
    """Item 3 (D-016): board k holds only phase k at z = k (t + gap) + local z; thickness equals Xcoil's 5.4 mm."""
    case_id = "s-perphase-3-t5-gap0p3"
    dump, stack = xcoil_dumps()[case_id], stack_for(case_id)
    assert len(stack.boards) == dump["nBoards"] == 3
    t, gap = stack.board_thickness_mm, stack.board_gap_mm
    assert (t, gap) == pytest.approx((1.6, 0.3), abs=1e-12)
    assert 3 * t + 2 * gap == pytest.approx(dump["statorThickness"], abs=1e-12)
    local = list(stack.boards[0].copper_z_mm.values())
    for k, layout in enumerate(stack.boards):
        assert {p.phase.value for p in layout.paths if p.phase is not None} == {"ABC"[k]}
        z = list(layout.copper_z_mm.values())
        assert z == pytest.approx([k * (t + gap) + zl for zl in local], abs=1e-12)


def test_comparator_detects_seeded_defects() -> None:
    """Self-test: each seeded defect on the embodic side must show in the comparison."""
    xs = boards_from_xcoil(xcoil_dumps()["w-chord-p8-l2-m2-t3"])
    es = boards_from_embodic(stack_for("w-chord-p8-l2-m2-t3"))
    layer_x, layer_e = xs[0].layers[0], es[0].layers[0]
    assert compare_layer(layer_x, layer_e).max_xcoil_to_own_mm < 1e-12
    dropped = compare_layer(layer_x, layer_e[1:])
    assert dropped.max_xcoil_to_own_mm > 1e-3
    first = layer_e[0]
    moved = [Copper(dataclasses.replace(first.prim, x1=first.prim.x1 + 2e-9), first.role), *layer_e[1:]]
    assert compare_layer(layer_x, moved).max_own_to_xcoil_mm > 1e-9
    wide = [Copper(dataclasses.replace(first.prim, width=first.prim.width + 0.01), first.role), *layer_e[1:]]
    assert compare_layer(layer_x, wide).width_mismatches > 0
    renamed = [Copper(first.prim, "bus"), *layer_e[1:]]
    assert compare_layer(layer_x, renamed).role_mismatches > 0
    via = es[0].vias[0]
    shifted = [Land(via.x + 2e-9, via.y, via.diameter, via.tag), *es[0].vias[1:]]
    assert match_lands(xs[0].vias, shifted)[0] > 1e-9
    assert math.isfinite(match_lands(xs[0].vias, es[0].vias)[0])
