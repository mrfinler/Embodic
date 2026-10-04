"""Build the embodic input for a universe of Agent 4 items, through embodic's public constructors only.

This is the one instrument module that imports embodic: it turns test inputs into a ``Layout``. Expected values never
come from here. Labels follow the ids ``run_drc`` reports (interfaces.md section 7: ``path:17/prim:4``, ``via:33``).
"""

from collections.abc import Sequence

from drc_universe import Cls, Item, disc_centre
from records import Arc as OwnArc
from records import Line as OwnLine

from embodic.drc import DrcReport
from embodic.geometry.circuit import Circuit
from embodic.geometry.layout import BoardOutline, Hole, Layout, Pad, RotationalSymmetry, Via, ViaRole
from embodic.geometry.paths import CopperPath
from embodic.geometry.primitives import Arc, Line, Primitive, PrimitiveRole
from embodic.model.drc_rules import DrcRules
from embodic.model.vocabulary import ConnectionTopology, TopologyKind, ViaSpan


def layer_name(index: int) -> str:
    """Return the copper layer name used for layer ``index``."""
    return f"L{index}"


def to_primitive(p: OwnLine | OwnArc, role: PrimitiveRole) -> Primitive:
    """Convert an own record to an embodic primitive."""
    if isinstance(p, OwnLine):
        return Line(x1_mm=p.x1, y1_mm=p.y1, x2_mm=p.x2, y2_mm=p.y2, width_mm=p.width, role=role)
    return Arc(cx_mm=p.cx, cy_mm=p.cy, r_mm=p.r, start_rad=p.start, sweep_rad=p.sweep, width_mm=p.width, role=role)


def to_layout(items: Sequence[Item], layers: int, symmetry: RotationalSymmetry | None = None) -> Layout:
    """Build a Layout whose ``run_drc`` labels equal the item labels."""
    paths: dict[int, list[Item]] = {}
    vias, pads, edges, holes = [], [], [], []
    for it in items:
        if it.cls is Cls.TRACE:
            assert it.path is not None and it.label == f"path:{it.path}/prim:{len(paths.get(it.path, []))}"
            paths.setdefault(it.path, []).append(it)
        elif it.cls is Cls.VIA:
            x, y = disc_centre(it)
            assert it.label == f"via:{len(vias)}"
            vias.append(
                Via(id=len(vias), x_mm=x, y_mm=y, drill_mm=it.prim.width / 2, pad_mm=it.prim.width,
                    role=ViaRole.TRANSFER, span=ViaSpan.THROUGH, layer_from=layer_name(0),
                    layer_to=layer_name(layers - 1), net=it.net)
            )  # fmt: skip
        elif it.cls is Cls.PAD:
            x, y = disc_centre(it)
            assert it.label == f"pad:{len(pads)}"
            pads.append(
                Pad(id=len(pads), x_mm=x, y_mm=y, shape="round", width_mm=it.prim.width, height_mm=it.prim.width,
                    rotation_rad=0.0, drill_mm=it.prim.width / 2, layer=None, net=it.net, label="U")
            )  # fmt: skip
        elif it.cls is Cls.EDGE:
            assert it.label == f"edge:outer/prim:{len(edges)}"
            edges.append(to_primitive(it.prim, PrimitiveRole.OUTLINE))
        else:
            x, y = disc_centre(it)
            assert it.label == f"hole:{len(holes)}"
            holes.append(Hole(x_mm=x, y_mm=y, diameter_mm=it.prim.width, label="M3 normal"))
    copper = tuple(
        CopperPath(
            id=pid,
            layer=layer_name(prims[0].layer or 0),
            net=prims[0].net,
            primitives=tuple(
                to_primitive(it.prim, PrimitiveRole.FILLET if it.corner else PrimitiveRole.SIDE) for it in prims
            ),
            phase=None,
            element=None,
            polarity=0,
        )
        for pid, prims in sorted(paths.items())
    )
    return Layout(
        topology=TopologyKind.SPIRAL,
        copper_layers=tuple(layer_name(i) for i in range(layers)),
        copper_z_mm={layer_name(i): float(i) for i in range(layers)},
        paths=copper,
        vias=tuple(vias),
        pads=tuple(pads),
        outline=BoardOutline(outer=tuple(edges), cutouts=(), holes=tuple(holes)),
        circuit=Circuit(phases=(), topology=ConnectionTopology.OPEN, interconnect_path_ids=()),
        symmetry=symmetry,
        envelope_mm=(0.0, 100.0),
    )


def uniform_rules(clearance_mm: float) -> DrcRules:
    """One clearance for every pair kind (the Xcoil convention) and minima of 0, so only pair checks can fail."""
    return DrcRules(
        trace_clearance_mm=clearance_mm,
        via_clearance_mm=clearance_mm,
        edge_clearance_mm=clearance_mm,
        hole_clearance_mm=clearance_mm,
        min_trace_width_mm=0.0,
        min_drill_mm=0.0,
        min_annular_ring_mm=0.0,
    )


PAIR_KINDS = frozenset({"trace_trace", "trace_via", "via_via", "pad_trace", "pad_pad", "copper_edge", "copper_hole"})


def pair_violations(report: DrcReport) -> dict[frozenset[str], tuple[str, float]]:
    """Map each reported pair violation to (kind, measured_mm); fails if the report truncated its list."""
    assert report.violation_count == len(report.violations), "report truncated; use a smaller layout"
    out: dict[frozenset[str], tuple[str, float]] = {}
    for v in report.violations:
        if v.kind.value in PAIR_KINDS:
            key = frozenset(v.objects)
            assert key not in out, f"pair reported twice: {sorted(key)}"
            out[key] = (v.kind.value, v.measured_mm)
    return out
