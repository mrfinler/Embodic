"""Board dump v1 (REQ-F-40): content of an embodic dump, the number encoding and write-read-write identity."""

import math
from pathlib import Path

import pytest

from embodic.geometry.circuit import Circuit, Member, ParallelGroup, PhaseCircuit
from embodic.geometry.layout import BoardOutline, Hole, Layout, Pad, Via, ViaRole
from embodic.geometry.paths import CopperPath
from embodic.geometry.primitives import Arc, Line, PrimitiveRole
from embodic.io.board_dump import (
    BOARD_DUMP_SCHEMA,
    decode_board_dump,
    dump_layout,
    encode_board_dump,
    read_board_dump,
    write_board_dump,
)
from embodic.model.vocabulary import ConnectionTopology, Phase, TopologyKind, ViaSpan

pytestmark = pytest.mark.req("REQ-F-40")

LINE = Line(x1_mm=-0.0, y1_mm=0.0, x2_mm=5.0, y2_mm=0.0, width_mm=0.2, role=PrimitiveRole.SIDE)
ARC = Arc(
    cx_mm=5.0, cy_mm=1.0, r_mm=1.0, start_rad=-math.pi / 2, sweep_rad=math.pi, width_mm=0.2, role=PrimitiveRole.END_TURN
)


def _layout() -> Layout:
    paths = (
        CopperPath(id=3, layer="L1", net="A", primitives=(LINE, ARC), phase=Phase.B, element=4, polarity=1),
        CopperPath(id=9, layer="L2", net="N", primitives=(LINE,), phase=None, element=None, polarity=0),
    )
    via = Via(
        id=0, x_mm=5.0, y_mm=2.0, drill_mm=0.3, pad_mm=0.6, role=ViaRole.TERMINAL, span=ViaSpan.THROUGH,
        layer_from="L1", layer_to="L2", net="A",
    )  # fmt: skip
    pad = Pad(
        id=0, x_mm=40.0, y_mm=0.0, shape="oblong", width_mm=2.4, height_mm=1.2, rotation_rad=0.5, drill_mm=0.0,
        layer="L2", net="A", label="U",
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
    group = ParallelGroup(members=(Member(path_ids=(3,), via_ids=(0,)),))
    return Layout(
        topology=TopologyKind.SPIRAL,
        copper_layers=("L1", "L2"),
        copper_z_mm={"L1": 0.0174, "L2": 1.5826},
        paths=paths,
        vias=(via,),
        pads=(pad,),
        outline=BoardOutline(outer=outer, cutouts=(), holes=(Hole(x_mm=45.0, y_mm=0.0, diameter_mm=3.4, label="M3"),)),
        circuit=Circuit(
            phases=(PhaseCircuit(phase=Phase.B, groups=(group,), terminal_net="A"),),
            topology=ConnectionTopology.STAR,
            interconnect_path_ids=(9,),
        ),
        symmetry=None,
        envelope_mm=(0.0, 6.0),
    )


def test_board_dump_write_read_write_is_byte_identical(tmp_path: Path) -> None:
    """Catches a writer whose output depends on key order or that loses -0.0 or an integer on the way back."""
    path = tmp_path / "case.json"
    write_board_dump(_layout(), path, case_id="unit-case")
    first = path.read_bytes()
    assert encode_board_dump(read_board_dump(path)).encode("utf-8") == first
    assert b'"x1": -0.0' in first


def test_board_dump_records_every_primitive_with_its_object_layer_and_phase() -> None:
    """Catches a primitive written without its owner, a wrong layer index, or a phase written by name."""
    dump = dump_layout(_layout(), case_id="unit-case")
    prims = dump["primitives"]
    assert isinstance(prims, list)
    assert [(p["id"], p["object"], p["seq"], p["layer"], p["phase"], p["coil"]) for p in prims] == [
        (0, 3, 0, 0, 1, 4),
        (1, 3, 1, 0, 1, 4),
        (2, 9, 0, 1, None, None),
    ]
    arc = prims[1]
    assert (arc["type"], arc["kind"], arc["a1"], arc["a2"]) == ("arc", "end_turn", -math.pi / 2, math.pi / 2)
    assert arc["start"] == pytest.approx([5.0, 0.0], abs=1e-15)
    assert arc["end"] == pytest.approx([5.0, 2.0], abs=1e-15)
    assert dump["objects"][0]["primitive_ids"] == [0, 1]
    assert dump["vias"][0]["terminal"] is True
    assert dump["pads"][0]["smd"] is True and dump["pads"][0]["layer"] == 1
    assert dump["circuits"] == [
        {"phase": 1, "elements": [{"members": [{"object": 3, "layer": 0, "direction": 1}], "vias": [0]}],
         "terminals": {"plus": None, "minus": None}}
    ]  # fmt: skip
    assert {key.removesuffix("[]") for key in BOARD_DUMP_SCHEMA} == set(dump)


def test_board_dump_tags_non_finite_numbers_and_rejects_bare_tokens() -> None:
    """Catches Python's non-standard Infinity token and a reader that turns -0.0 into the integer 0."""
    text = encode_board_dump({"format": "embodic.board-dump", "format_version": 1, "v": [math.inf, -math.inf, -0.0]})
    assert '"$f": "inf"' in text and '"$f": "-inf"' in text
    back = decode_board_dump(text)["v"]
    assert back[:2] == [math.inf, -math.inf]
    assert math.copysign(1.0, back[2]) == -1.0
    with pytest.raises(ValueError, match="non-standard"):
        decode_board_dump('{"format": "embodic.board-dump", "format_version": 1, "v": NaN}')
