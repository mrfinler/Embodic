"""From Xcoil-shaped objects to an embodic Layout (interfaces.md section 5), one object per CopperPath.

The builders hand over the objects in Xcoil's order: layer by layer, tracks first, then the group links (layer 0), then
the interconnect items. Nets follow D-022: phase copper and vias are ``PHASE_<name>``, interconnect keeps its
circuit net.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

from embodic.generators.wave.build import WaveVia
from embodic.generators.wave.interconnect import IcItem, IcPad
from embodic.generators.wave.xprim import XPrim, to_primitive
from embodic.geometry.circuit import (
    Circuit,
    InterconnectRole,
    LineLead,
    Member,
    NeutralLead,
    NeutralRing,
    ParallelGroup,
    PhaseCircuit,
    PhaseLink,
)
from embodic.geometry.details import WaveDetail
from embodic.geometry.layout import Layout, Pad, Via, ViaRole
from embodic.geometry.outline import build_outline
from embodic.geometry.paths import CopperPath
from embodic.model.design import DesignParameters
from embodic.model.vocabulary import Phase, TopologyKind, ViaSpan
from embodic.model.winding_specs import WaveWindingSpec
from embodic.results import Registry
from embodic.results.traceable import InputRef, KindTag, Traceable, traced
from embodic.units import Unit

PHASES = (Phase.A, Phase.B, Phase.C)
ObjKind = Literal["track", "link", "ic"]


@dataclass(frozen=True, slots=True, kw_only=True)
class Obj:
    """One Xcoil ``objs[]`` entry: its layer, kind, phase (None for interconnect), element number and primitives."""

    layer: int
    kind: ObjKind
    prims: tuple[XPrim, ...]
    phase: int | None
    net: str | None = None  # interconnect only
    element: int | None = None  # slot of a track
    polarity: Literal[1, -1, 0] = 0
    end_via: int | None = None  # index in WaveBuild.vias of the via the track ends on, in current direction
    ic: IcItem | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class SeriesElement:
    """One series element of a phase: the objects (same track position on every layer of its type) in parallel."""

    phase: int
    objects: tuple[int, ...]  # creation numbers before build_in_layer_order, indices into WaveBuild.objects after


@dataclass(frozen=True, slots=True, kw_only=True)
class WaveBuild:
    """Everything a builder returns for the assembler."""

    objects: tuple[Obj, ...]
    vias: tuple[WaveVia, ...]
    pads: tuple[IcPad, ...]
    elements: tuple[SeriesElement, ...]
    r_min_cu: float
    r_max_cu: float
    r_min_all: float
    r_max_all: float


def build_in_layer_order(
    objects: Sequence[Obj], elements: Sequence[SeriesElement], vias: tuple[WaveVia, ...], pads: tuple[IcPad, ...], *,
    r_min_cu: float, r_max_cu: float, r_max_all: float,
) -> WaveBuild:  # fmt: skip
    """Order the objects layer by layer, keeping creation order inside a layer, as Xcoil's ``layer.objs`` lists do.

    Elements name objects by creation number; the result names them by their place in the ordered list.
    """
    order = sorted(range(len(objects)), key=lambda i: (objects[i].layer, i))
    place = {created: placed for placed, created in enumerate(order)}
    return WaveBuild(
        objects=tuple(objects[i] for i in order), vias=vias, pads=pads,
        elements=tuple(SeriesElement(phase=e.phase, objects=tuple(place[i] for i in e.objects)) for e in elements),
        r_min_cu=r_min_cu, r_max_cu=r_max_cu, r_min_all=r_min_cu, r_max_all=r_max_all,
    )  # fmt: skip


def phase_net(phase: int | None) -> str:
    """Net of phase copper and of the vias of that phase (D-022)."""
    return "" if phase is None else f"PHASE_{PHASES[phase].value}"


def _role(item: IcItem, path_id: int) -> InterconnectRole:
    if item.kind == "line":
        assert item.phase is not None
        return LineLead(path_id=path_id, phase=PHASES[item.phase])
    if item.kind == "neutral_pad":
        return NeutralLead(path_id=path_id)
    assert item.link is not None
    if item.link.net == "N":
        return NeutralRing(path_id=path_id, tap_via_ids=tuple(t.via for t in item.link.taps))
    return PhaseLink(path_id=path_id, phase=PHASES[int(item.link.net[1:])])


def _member(obj: Obj, path_id: int) -> Member:
    """One layer copy of a series element: its track and the via it ends on (Xcoil adds one rVia per element)."""
    return Member(path_ids=(path_id,), via_ids=() if obj.end_via is None else (obj.end_via,))


def _derived(
    design: DesignParameters, build: WaveBuild, tracks_per_layer: Mapping[str, int], registry: Registry
) -> tuple[Traceable[float], ...]:  # fmt: skip
    spec = design.winding
    assert isinstance(spec, WaveWindingSpec)
    values: dict[str, tuple[float, Unit]] = {
        "/winding/r_inner_mm": (spec.r_inner_mm, Unit.MM),
        "/winding/r_outer_mm": (spec.r_outer_mm, Unit.MM),
        "/winding/turns": (spec.turns, Unit.ONE),
        "/winding/trace_width_mm": (spec.trace_width_mm, Unit.MM),
        "/winding/clearance_mm": (spec.clearance_mm, Unit.MM),
        "/vias/pad_mm": (design.vias.pad_mm, Unit.MM),
    }
    inputs = tuple(
        InputRef(pointer=pointer, value=value, unit=unit, provenance=None, kind=None, label=None)
        for pointer, (value, unit) in values.items()
    )
    rows: tuple[tuple[str, float, Unit, KindTag], ...] = (
        ("tracks_per_layer_t", float(tracks_per_layer["T"]), Unit.ONE, "count"),
        ("tracks_per_layer_b", float(tracks_per_layer["B"]), Unit.ONE, "count"),
        ("stitch_vias", float(len(build.vias)), Unit.ONE, "count"),
        ("copper_r_min_mm", build.r_min_all, Unit.MM, "derived"),
        ("copper_r_max_mm", build.r_max_all, Unit.MM, "derived"),
    )
    return tuple(
        traced(quantity, value, unit, eq_ids=(), inputs=inputs, registry=registry, kind_tag=kind)
        for quantity, value, unit, kind in rows
    )


def assemble_layout(design: DesignParameters, build: WaveBuild, registry: Registry) -> Layout:
    """Layout of one wave board: paths in Xcoil's object order, vias, pads, circuit and outline."""
    copper = design.stackup.copper_layers()
    names = tuple(layer.name for layer in copper)
    copper_z = design.stackup.copper_z_mm()
    paths = tuple(
        CopperPath(
            id=i,
            layer=names[o.layer],
            net=o.net if o.net is not None else phase_net(o.phase),
            primitives=tuple(to_primitive(q) for q in o.prims),
            phase=None if o.phase is None else PHASES[o.phase],
            element=o.element,
            polarity=o.polarity,
        )
        for i, o in enumerate(build.objects)
    )
    via_spec = design.vias
    vias = tuple(
        Via(
            id=i, x_mm=v.x, y_mm=v.y, drill_mm=via_spec.drill_mm, pad_mm=via_spec.pad_mm,
            role=ViaRole.TERMINAL if v.terminal else ViaRole.STITCH, span=ViaSpan.THROUGH,
            layer_from=names[0], layer_to=names[-1], net=phase_net(v.phase),
        )
        for i, v in enumerate(build.vias)
    )  # fmt: skip
    conn = design.connection
    pads = tuple(
        Pad(
            id=i, x_mm=p.x, y_mm=p.y, shape="round", width_mm=conn.terminal_pad_mm, height_mm=conn.terminal_pad_mm,
            rotation_rad=0.0, drill_mm=conn.terminal_drill_mm,
            layer=None if conn.terminal_drill_mm > 0 else names[p.layer], net=p.net, label=p.net,
        )
        for i, p in enumerate(build.pads)
    )  # fmt: skip
    ic_ids = tuple(i for i, o in enumerate(build.objects) if o.kind == "ic")
    roles = tuple(_role(o.ic, i) for i, o in enumerate(build.objects) if o.kind == "ic" and o.ic is not None)
    phases = sorted({e.phase for e in build.elements})
    circuit = Circuit(
        phases=tuple(
            PhaseCircuit(
                phase=PHASES[ph],
                groups=tuple(
                    ParallelGroup(members=tuple(_member(build.objects[i], i) for i in e.objects))
                    for e in build.elements
                    if e.phase == ph
                ),
                terminal_net=phase_net(ph),
            )
            for ph in phases
        ),
        topology=conn.topology,
        interconnect_path_ids=ic_ids,
        interconnect_roles=roles,
    )
    envelope = (build.r_min_all, build.r_max_all)
    t_count = sum(1 for o in build.objects if o.kind == "track" and o.layer == 0)
    b_count = sum(1 for o in build.objects if o.kind == "track" and o.layer == 1)
    return Layout(
        topology=TopologyKind.WAVE,
        copper_layers=names,
        copper_z_mm=MappingProxyType({n: copper_z[n] for n in names}),
        paths=paths,
        vias=vias,
        pads=pads,
        outline=build_outline(design.outline, envelope),
        circuit=circuit,
        symmetry=None,
        envelope_mm=envelope,
        detail=WaveDetail(tracks_per_layer=t_count, stitch_vias_per_stack=len(build.vias)),
        derived=_derived(design, build, {"T": t_count, "B": b_count}, registry),
    )
