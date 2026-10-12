"""Xcoil records to embodic geometry: the primitive-kind table, the record reader and the GR-19 layout mapper.

Xcoil's ``kind`` names (engine.js) map to ``PrimitiveRole`` as below. Serpentine's three end-turn variants ``far``,
``near`` and ``closing`` (engine.js l.471) are end turns, so they share ``END_TURN``.
"""

from collections.abc import Mapping
from itertools import pairwise
from typing import Any

from embodic.geometry.circuit import Circuit
from embodic.geometry.layout import BoardOutline, Hole, Layout, Pad, Via, ViaRole
from embodic.geometry.paths import COINCIDENCE_MM, CopperPath, joint_gaps_mm
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


def _phase_net(phase: Phase | None) -> str:
    return f"PHASE_{phase.value}" if phase else ""


def _chains(prims: tuple[Primitive, ...]) -> list[tuple[Primitive, ...]]:
    """Cut a primitive run at every joint wider than COINCIDENCE_MM, so each piece is one continuous chain."""
    cuts = [k + 1 for k, gap_mm in enumerate(joint_gaps_mm(prims)) if gap_mm > COINCIDENCE_MM]
    bounds = [0, *cuts, len(prims)]
    return [prims[start:stop] for start, stop in pairwise(bounds)]


def _paths(raw: Mapping[str, Any]) -> tuple[tuple[CopperPath, ...], tuple[int, ...]]:
    """(paths, interconnect path ids): one path per Xcoil object, and one per continuous chain of an ``ic`` object."""
    paths: list[CopperPath] = []
    interconnect: list[int] = []
    for layer in raw["layers"]:
        for obj in layer["objs"]:
            phase = _phase(obj["phase"] if obj.get("phase") is not None and obj["phase"] >= 0 else layer["phase"])
            element = next((obj[k] for k in ("coil", "strand", "slot") if obj.get(k) is not None), None)
            prims = tuple(prim_from_record(r) for r in obj["prims"])
            is_ic = obj["kind"] == "ic"
            for chain in _chains(prims) if is_ic else [prims]:
                if is_ic:
                    interconnect.append(len(paths))
                paths.append(
                    CopperPath(
                        id=len(paths),
                        layer=layer["name"],
                        net=obj["net"] if is_ic else _phase_net(phase),
                        primitives=chain,
                        phase=phase,
                        element=element,
                        polarity=0,
                    )
                )
    return tuple(paths), tuple(interconnect)


def layout_from_xcoil(raw: Mapping[str, Any]) -> Layout:
    """Map ``xcoilRawLayout`` output to a Layout: one CopperPath per Xcoil object or ``ic`` chain, in Xcoil's order.

    An ``ic`` object becomes one CopperPath per continuous chain (a CopperPath is one chain, interfaces.md section 5):
    Xcoil's star item holds the neutral ring and its stubs in one object, as the embodic serpentine and wave ports split
    it (D-035b, DEF-M1V-03).

    Nets follow Xcoil's board export (engine.js l.2888-2907): phase copper, its links included, and every via are
    ``PHASE_<name>`` of their phase index; interconnect objects keep Xcoil's net (N, U, V, W, D0...).

    Not mapped (Xcoil does not return them): the circuit's phase element lists, path polarity (0), via roles other
    than terminal (``TRANSFER``) and via layer spans (through, first to last layer).
    """
    names = tuple(layer["name"] for layer in raw["layers"])
    params = raw["params"]
    paths, interconnect = _paths(raw)
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
            net=_phase_net(_phase(v["phase"])),
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
