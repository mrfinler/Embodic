"""Xcoil records to embodic geometry: the primitive-kind table, the record reader and the GR-19 layout mapper.

Xcoil's ``kind`` names (engine.js) map to ``PrimitiveRole`` as below. Serpentine's three end-turn variants ``far``,
``near`` and ``closing`` (engine.js l.471) are end turns, so they share ``END_TURN``.
"""

from collections.abc import Mapping
from typing import Any

from embodic.geometry.circuit import Circuit
from embodic.geometry.layout import BoardOutline, Hole, Layout, Pad, Via, ViaRole
from embodic.geometry.paths import CopperPath
from embodic.geometry.primitives import Arc, Line, Primitive, PrimitiveRole
from embodic.model.vocabulary import ConnectionTopology, Phase, TopologyKind, ViaSpan

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
    "bore": PrimitiveRole.OUTLINE,
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


PHASES = (Phase.A, Phase.B, Phase.C)
TOPOLOGY_BY_XCOIL: Mapping[str, TopologyKind] = {
    "serpentine": TopologyKind.SERPENTINE,
    "wave": TopologyKind.WAVE,
    "sector": TopologyKind.SPIRAL,  # Xcoil's concentrated sector coils; embodic's spiral generator is no port of it
}


def _phase(index: int | None) -> Phase | None:
    return PHASES[index] if index is not None and 0 <= index < len(PHASES) else None


def _paths(raw: Mapping[str, Any]) -> tuple[CopperPath, ...]:
    paths: list[CopperPath] = []
    for layer in raw["layers"]:
        for obj in layer["objs"]:
            phase = _phase(obj["phase"] if obj.get("phase") is not None and obj["phase"] >= 0 else layer["phase"])
            element = next((obj[k] for k in ("coil", "strand", "slot") if obj.get(k) is not None), None)
            paths.append(
                CopperPath(
                    id=len(paths),
                    layer=layer["name"],
                    net=obj.get("net") or (f"PHASE_{phase.value}" if phase else ""),
                    primitives=tuple(prim_from_record(r) for r in obj["prims"]),
                    phase=phase,
                    element=element,
                    polarity=0,
                )
            )
    return tuple(paths)


def layout_from_xcoil(raw: Mapping[str, Any]) -> Layout:
    """Map ``xcoilRawLayout`` output to a Layout: one CopperPath per Xcoil object, in Xcoil's order.

    Not mapped (Xcoil does not return them): the circuit's phase element lists, path polarity (0), via roles other
    than terminal (``TRANSFER``) and via layer spans (through, first to last layer).
    """
    names = tuple(layer["name"] for layer in raw["layers"])
    params = raw["params"]
    paths = _paths(raw)
    vias = tuple(
        Via(
            id=i,
            x_mm=v["x"],
            y_mm=v["y"],
            drill_mm=params["viaDrill"],
            pad_mm=params["viaPad"],
            role=ViaRole.TERMINAL if v["terminal"] else ViaRole.TRANSFER,
            span=ViaSpan.THROUGH,
            layer_from=names[0],
            layer_to=names[-1],
            net=_phase(v["phase"]).value if _phase(v["phase"]) else "",
        )
        for i, v in enumerate(raw["vias"])
    )
    pads = tuple(
        Pad(
            id=i,
            x_mm=p["x"],
            y_mm=p["y"],
            shape=p["shape"],
            width_mm=p["w"],
            height_mm=p["h"],
            rotation_rad=p["rot"],
            drill_mm=p["drill"],
            layer=names[p["layer"]] if p["smd"] else None,
            net=p["net"],
            label=p["label"],
        )
        for i, p in enumerate(raw["pads"])
    )
    mech = raw["mech"]
    outline = BoardOutline(
        outer=tuple(prim_from_record(r) for r in mech["prims"]),
        cutouts=(tuple(prim_from_record(r) for r in mech["borePrims"]),) if mech["borePrims"] else (),
        holes=tuple(
            Hole(x_mm=h["x"], y_mm=h["y"], diameter_mm=h["dia"], label=f"{h['size']} {h['ring']}")
            for h in mech["holes"]
        ),
    )
    interconnect = tuple(path.id for path, obj in zip(paths, _objects(raw), strict=True) if obj["kind"] == "ic")
    return Layout(
        topology=TOPOLOGY_BY_XCOIL[params["topology"]],
        copper_layers=names,
        copper_z_mm={layer["name"]: layer["z"] for layer in raw["layers"]},
        paths=paths,
        vias=vias,
        pads=pads,
        outline=outline,
        circuit=Circuit(
            phases=(), topology=ConnectionTopology(params["connection"]), interconnect_path_ids=interconnect
        ),
        symmetry=None,
        envelope_mm=(raw["rMinCu"], raw["rMaxCu"]),
    )


def _objects(raw: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [obj for layer in raw["layers"] for obj in layer["objs"]]
