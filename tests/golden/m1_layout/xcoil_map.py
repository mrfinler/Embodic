"""Xcoil records to embodic geometry: the primitive-kind table and the board-dump record reader.

Xcoil's ``kind`` names (engine.js) map to ``PrimitiveRole`` as below. Serpentine's three end-turn variants ``far``,
``near`` and ``closing`` (engine.js l.471) are end turns, so they share ``END_TURN``.
"""

from collections.abc import Mapping
from typing import Any

from embodic.geometry.primitives import Arc, Line, Primitive, PrimitiveRole

ROLE_BY_XCOIL_KIND: Mapping[str, PrimitiveRole] = {
    "side": PrimitiveRole.SIDE,
    "endturn": PrimitiveRole.END_TURN,
    "far": PrimitiveRole.END_TURN,
    "near": PrimitiveRole.END_TURN,
    "closing": PrimitiveRole.END_TURN,
    "lead": PrimitiveRole.LEAD,
    "fillet": PrimitiveRole.FILLET,
    "taper": PrimitiveRole.TAPER,
    "leg": PrimitiveRole.LEG,
    "ring": PrimitiveRole.RING,
    "stub": PrimitiveRole.STUB,
    "bus": PrimitiveRole.BUS,
    "link": PrimitiveRole.LINK,
    "outline": PrimitiveRole.OUTLINE,
}


def prim_from_record(record: Mapping[str, Any]) -> Primitive:
    """Board-dump primitive record (Xcoil ``a1``/``a2``) to a Line or Arc; the sweep is Xcoil's ``a2 - a1``."""
    role = ROLE_BY_XCOIL_KIND[record["kind"]]
    if record["type"] == "line":
        return Line(
            x1_mm=record["x1"],
            y1_mm=record["y1"],
            x2_mm=record["x2"],
            y2_mm=record["y2"],
            width_mm=record["width"],
            role=role,
        )
    return Arc(
        cx_mm=record["cx"],
        cy_mm=record["cy"],
        r_mm=record["r"],
        start_rad=record["a1"],
        sweep_rad=record["a2"] - record["a1"],
        width_mm=record["width"],
        role=role,
    )
