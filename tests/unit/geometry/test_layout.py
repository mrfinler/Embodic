"""Layout container: the hash is derived and deterministic (Phase 1 UT-GEO-15), the arrays map back to primitives."""

import dataclasses
import math

import pytest

from embodic.geometry.circuit import Circuit, Member, ParallelGroup, PhaseCircuit
from embodic.geometry.layout import BoardOutline, BoardStack, Layout, Via, ViaRole
from embodic.geometry.paths import CopperPath
from embodic.geometry.primitives import Arc, Line, PrimitiveRole
from embodic.model.vocabulary import ConnectionTopology, Phase, TopologyKind, ViaSpan

pytestmark = pytest.mark.req("REQ-N-04")


def _layout(via_x_mm: float = 5.0) -> Layout:
    line = Line(x1_mm=0.0, y1_mm=0.0, x2_mm=5.0, y2_mm=0.0, width_mm=0.2, role=PrimitiveRole.SIDE)
    arc = Arc(
        cx_mm=5.0,
        cy_mm=1.0,
        r_mm=1.0,
        start_rad=-math.pi / 2,
        sweep_rad=math.pi,
        width_mm=0.2,
        role=PrimitiveRole.END_TURN,
    )
    paths = (
        CopperPath(id=7, layer="L1", net="A", primitives=(line, arc), phase=Phase.A, element=0, polarity=1),
        CopperPath(id=8, layer="L2", net="A", primitives=(line,), phase=Phase.A, element=0, polarity=-1),
    )
    via = Via(
        id=0, x_mm=via_x_mm, y_mm=2.0, drill_mm=0.3, pad_mm=0.6, role=ViaRole.CENTRE, span=ViaSpan.THROUGH,
        layer_from="L1", layer_to="L2", net="A",
    )  # fmt: skip
    outer = (
        Arc(
            cx_mm=0.0,
            cy_mm=0.0,
            r_mm=50.0,
            start_rad=0.0,
            sweep_rad=2 * math.pi,
            width_mm=0.0,
            role=PrimitiveRole.OUTLINE,
        ),
    )
    member = Member(path_ids=(7, 8), via_ids=(0,))
    circuit = Circuit(
        phases=(PhaseCircuit(phase=Phase.A, groups=(ParallelGroup(members=(member,)),), terminal_net="A"),),
        topology=ConnectionTopology.STAR,
        interconnect_path_ids=(),
    )
    return Layout(
        topology=TopologyKind.SPIRAL,
        copper_layers=("L1", "L2"),
        copper_z_mm={"L1": 0.0174, "L2": 1.5826},
        paths=paths,
        vias=(via,),
        pads=(),
        outline=BoardOutline(outer=outer, cutouts=(), holes=()),
        circuit=circuit,
        symmetry=None,
        envelope_mm=(0.0, 6.0),
    )


def test_ut_geo_15_two_builds_give_the_same_hash() -> None:
    """Catches a hash over object identity or unordered data: equal layouts must hash equal."""
    assert _layout().layout_hash == _layout().layout_hash
    assert _layout().layout_hash.startswith("sha256:")


def test_layout_hash_changes_with_one_ulp_of_copper_or_via() -> None:
    """Catches a hash that rounds coordinates or leaves the vias out."""
    base = _layout()
    assert _layout(via_x_mm=math.nextafter(5.0, 6.0)).layout_hash != base.layout_hash
    moved = dataclasses.replace(base.paths[1], net="B")
    assert dataclasses.replace(base, paths=(base.paths[0], moved)).layout_hash != base.layout_hash


def test_layout_arrays_rows_map_back_to_their_primitive() -> None:
    """Catches arc rows indexed as if they followed no lines, or a path index that is a position, not the id."""
    arrays = _layout().arrays()
    assert arrays.lines["L1"].shape == (1, 5)
    assert arrays.arcs["L1"].shape == (1, 6)
    assert arrays.path_index["L1"].tolist() == [7, 7]
    assert arrays.prim_index["L1"].tolist() == [0, 1]
    assert arrays.arcs["L1"][0].tolist() == [5.0, 1.0, 1.0, -math.pi / 2, math.pi, 0.2]
    assert arrays.path_index["L2"].tolist() == [8]
    assert arrays.vias.tolist() == [[5.0, 2.0, 0.6, 0.3]]


def test_board_stack_thickness_matches_xcoil_stator_thickness() -> None:
    """Defect caught: gap counted n times instead of n - 1 (Xcoil engine.js l.689: 3 * 1.6 + 2 * 0.5 = 5.8 mm)."""
    stack = BoardStack(boards=(_layout(), _layout(6.0), _layout(7.0)), board_thickness_mm=1.6, board_gap_mm=0.5)
    assert stack.stack_thickness_mm == pytest.approx(5.8, rel=1e-15)
    assert BoardStack(boards=(_layout(),), board_thickness_mm=1.6, board_gap_mm=0.0).stack_thickness_mm == 1.6


def test_board_stack_rejects_no_board_and_a_gap_on_one_board() -> None:
    """Defect caught: an empty stack, or a one-board stack with a gap, would give a wrong symmetry plane."""
    with pytest.raises(ValueError, match="at least one board"):
        BoardStack(boards=(), board_thickness_mm=1.6, board_gap_mm=0.0)
    with pytest.raises(ValueError, match="no board gap"):
        BoardStack(boards=(_layout(),), board_thickness_mm=1.6, board_gap_mm=0.2)


def test_board_stack_hash_follows_board_order_copper_and_gap() -> None:
    """Defect caught: a hash that ignores board order or the gap lets two different stacks share a cache key."""
    a, b = _layout(5.0), _layout(6.0)
    base = BoardStack(boards=(a, b), board_thickness_mm=1.6, board_gap_mm=0.5)
    assert base.stack_hash == BoardStack(boards=(a, b), board_thickness_mm=1.6, board_gap_mm=0.5).stack_hash
    assert base.stack_hash.startswith("sha256:")
    assert base.stack_hash != BoardStack(boards=(b, a), board_thickness_mm=1.6, board_gap_mm=0.5).stack_hash
    assert base.stack_hash != BoardStack(boards=(a, b), board_thickness_mm=1.6, board_gap_mm=0.6).stack_hash
