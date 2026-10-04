"""Hand-built Layouts for DRC tests: one helper per object kind, everything else empty."""

import math
from collections.abc import Sequence

from embodic.geometry.circuit import Circuit
from embodic.geometry.layout import BoardOutline, Hole, Layout, Pad, RotationalSymmetry, Via, ViaRole
from embodic.geometry.paths import CopperPath
from embodic.geometry.primitives import Arc, Line, Primitive, PrimitiveRole
from embodic.model.drc_rules import DrcRules
from embodic.model.vocabulary import ConnectionTopology, TopologyKind, ViaSpan

RULES = DrcRules(
    trace_clearance_mm=0.2,
    via_clearance_mm=0.2,
    edge_clearance_mm=0.3,
    hole_clearance_mm=0.4,
    min_trace_width_mm=0.15,
    min_drill_mm=0.3,
    min_annular_ring_mm=0.1,
)
LAYERS = ("F.Cu", "B.Cu")


def line(x1: float, y1: float, x2: float, y2: float, w: float = 0.2, role: PrimitiveRole = PrimitiveRole.SIDE) -> Line:
    """Return a straight trace, width 0.2 mm unless given."""
    return Line(x1_mm=x1, y1_mm=y1, x2_mm=x2, y2_mm=y2, width_mm=w, role=role)


def arc(cx: float, cy: float, r: float, start: float, sweep: float, w: float = 0.2) -> Arc:
    """Return an end-turn arc, width 0.2 mm unless given."""
    return Arc(cx_mm=cx, cy_mm=cy, r_mm=r, start_rad=start, sweep_rad=sweep, width_mm=w, role=PrimitiveRole.END_TURN)


def path(pid: int, prims: Sequence[Primitive], layer: str = "F.Cu", net: str = "A") -> CopperPath:
    """Return one CopperPath on ``layer`` with net ``net``."""
    return CopperPath(id=pid, layer=layer, net=net, primitives=tuple(prims), phase=None, element=None, polarity=0)


def via(vid: int, x: float, y: float, net: str = "A", pad: float = 0.6, drill: float = 0.3) -> Via:
    """Return a through via spanning every layer."""
    return Via(
        id=vid,
        x_mm=x,
        y_mm=y,
        drill_mm=drill,
        pad_mm=pad,
        role=ViaRole.TRANSFER,
        span=ViaSpan.THROUGH,
        layer_from=LAYERS[0],
        layer_to=LAYERS[-1],
        net=net,
    )


def pad(pid: int, x: float, y: float, shape: str = "round", w: float = 1.0, h: float = 1.0, **kw: object) -> Pad:
    """Return an SMD-drill-free pad on every layer unless ``layer`` is given."""
    fields: dict[str, object] = {"rotation_rad": 0.0, "drill_mm": 0.0, "layer": None, "net": "N", "label": "N"}
    fields.update(kw)
    return Pad(id=pid, x_mm=x, y_mm=y, shape=shape, width_mm=w, height_mm=h, **fields)  # type: ignore[arg-type]


def layout(
    paths: Sequence[CopperPath] = (),
    vias: Sequence[Via] = (),
    pads: Sequence[Pad] = (),
    outer: Sequence[Primitive] = (),
    holes: Sequence[Hole] = (),
    symmetry: RotationalSymmetry | None = None,
    layers: tuple[str, ...] = LAYERS,
) -> Layout:
    """Return a Layout with only the given objects; circuit empty, symmetry as given."""
    return Layout(
        topology=TopologyKind.SPIRAL,
        copper_layers=layers,
        copper_z_mm={name: 0.035 * i for i, name in enumerate(layers)},
        paths=tuple(paths),
        vias=tuple(vias),
        pads=tuple(pads),
        outline=BoardOutline(outer=tuple(outer), cutouts=(), holes=tuple(holes)),
        circuit=Circuit(phases=(), topology=ConnectionTopology.STAR, interconnect_path_ids=()),
        symmetry=symmetry,
        envelope_mm=(0.0, 50.0),
    )


def circle_outline(r: float) -> tuple[Arc, ...]:
    """Return a closed circular board edge of radius ``r``."""
    return (Arc(cx_mm=0, cy_mm=0, r_mm=r, start_rad=0, sweep_rad=2 * math.pi, width_mm=0, role=PrimitiveRole.OUTLINE),)
