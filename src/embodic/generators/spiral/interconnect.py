"""Star or delta links and the U/V/W/N leads beyond the bus rings (spiral_generator_spec.md G8).

Port of Xcoil ``buildInterconnect`` (engine.js l.1225) for the sector layout: tap stubs on layer Y end on a via at
the link ring, ring arcs on layer X, leads on layer Y from each phase start to its terminal pad. Nets per D-022:
neutral ``N``, delta links ``D0``..``D2``, leads ``U``/``V``/``W``; every path here goes in
``Circuit.interconnect_path_ids``.
"""

import math
from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Literal

from embodic.generators.spiral.chain import norm_angle
from embodic.geometry.layout import Pad, Via, ViaRole
from embodic.geometry.paths import CopperPath
from embodic.geometry.primitives import Arc, Line, Primitive, PrimitiveRole
from embodic.model.connection import ConnectionSpec
from embodic.model.vocabulary import ConnectionTopology, Phase

LINE_NET: Mapping[Phase, str] = {Phase.A: "U", Phase.B: "V", Phase.C: "W"}  # D-019: phase A is U
DELTA_PAIRS = ((Phase.A, Phase.B), (Phase.B, Phase.C), (Phase.C, Phase.A))


@dataclass(frozen=True, slots=True, kw_only=True)
class PhaseEnd:
    """The ring via where a phase chain starts (sign +1) or ends (sign -1)."""

    phase: Phase
    sign: Literal[1, -1]
    via: Via

    @property
    def angle_rad(self) -> float:
        """Angle of the via centre."""
        return math.atan2(self.via.y_mm, self.via.x_mm)


@dataclass(frozen=True, slots=True, kw_only=True)
class RingLink:
    """One interconnect ring arc from ``start_rad`` sweeping ``sweep_rad``, with the phase ends it taps."""

    net: str
    start_rad: float
    sweep_rad: float
    taps: tuple[PhaseEnd, ...]
    level: int


@dataclass(frozen=True, slots=True, kw_only=True)
class Interconnect:
    """Paths, vias and pads to append; ``r_max_mm`` is the outermost copper radius (pad edge)."""

    paths: tuple[CopperPath, ...]
    vias: tuple[Via, ...]
    pads: tuple[Pad, ...]
    r_max_mm: float


def plan_links(topology: ConnectionTopology, ends: Mapping[tuple[Phase, int], PhaseEnd]) -> tuple[RingLink, ...] | None:
    """Links of a star (one neutral arc over the three phase ends) or a delta (three links on one ring layer).

    None when a delta needs crossing links, which one ring layer cannot carry; open phases have no link.
    """
    if topology is ConnectionTopology.STAR:
        minus = [ends[(phase, -1)] for phase in Phase]
        angles = [norm_angle(t.angle_rad) for t in minus]
        order = sorted(range(3), key=lambda k: angles[k])
        gaps = [norm_angle(angles[order[(k + 1) % 3]] - angles[order[k]]) for k in range(3)]
        big = gaps.index(max(gaps))
        seq = [order[(big + 1) % 3], order[(big + 2) % 3], order[big]]
        start = angles[seq[0]]
        sweep = norm_angle(angles[seq[2]] - start)
        return (RingLink(net="N", start_rad=start, sweep_rad=sweep, taps=tuple(minus[k] for k in seq), level=0),)
    if topology is ConnectionTopology.DELTA:
        return _delta_links(ends)
    return ()


def _delta_links(ends: Mapping[tuple[Phase, int], PhaseEnd]) -> tuple[RingLink, ...] | None:
    links = []
    for k, (a, b) in enumerate(DELTA_PAIRS):
        src, dst = ends[(a, -1)], ends[(b, 1)]
        d = norm_angle(dst.angle_rad - src.angle_rad)
        sweep = d if d <= math.pi else d - 2 * math.pi
        links.append(RingLink(net=f"D{k}", start_rad=src.angle_rad, sweep_rad=sweep, taps=(src, dst), level=0))
    placed: list[RingLink] = []
    for link in sorted(links, key=lambda x: abs(x.sweep_rad)):
        level = 0
        for other in placed:
            relation = _relation(link, other)
            if relation == "cross":
                return None
            if relation == "encloses":
                level = max(level, other.level + 1)
        placed.append(replace(link, level=level))
    return tuple(placed)


def _relation(link: RingLink, other: RingLink) -> Literal["disjoint", "encloses", "cross"]:
    lo1, hi1 = sorted((link.start_rad, link.start_rad + link.sweep_rad))
    result: Literal["disjoint", "encloses", "cross"] = "disjoint"
    for wrap in (-1, 0, 1):
        lo2, hi2 = (a + wrap * 2 * math.pi for a in sorted((other.start_rad, other.start_rad + other.sweep_rad)))
        if hi2 < lo1 or lo2 > hi1:
            continue
        if not (lo2 > lo1 and hi2 < hi1):
            return "cross"
        result = "encloses"
    return result


@dataclass(frozen=True, slots=True, kw_only=True)
class _Rings:
    base_mm: float
    half_mm: float
    pitch_mm: float

    def radius_mm(self, level: int) -> float:
        return self.base_mm + self.half_mm + level * self.pitch_mm


def build_interconnect(
    connection: ConnectionSpec, ends: Mapping[tuple[Phase, int], PhaseEnd], links: tuple[RingLink, ...],
    base_mm: float, clearance_mm: float, ring_layer: str, stub_layer: str, first_path_id: int, first_via_id: int,
    first_pad_id: int,
) -> Interconnect:  # fmt: skip
    """Copper of ``links`` beyond ``base_mm`` (outermost bus copper) and the line (and neutral) leads with pads."""
    bw, s, template = connection.ring_width_mm, clearance_mm, next(iter(ends.values())).via
    pad_mm = template.pad_mm
    half = max(bw, pad_mm) / 2  # vias sit on the link rings
    rings = _Rings(base_mm=base_mm + s, half_mm=half, pitch_mm=2 * half + s)
    n_levels = max((lk.level for lk in links), default=-1) + 1
    pad_reach = connection.terminal_pad_mm / 2
    r_pad = base_mm + s + n_levels * rings.pitch_mm + pad_reach
    paths: list[CopperPath] = []
    vias: list[Via] = []
    stub_of: dict[tuple[Phase, int], tuple[int, Line]] = {}

    def add(layer: str, net: str, prims: tuple[Primitive, ...]) -> int:
        paths.append(CopperPath(id=first_path_id + len(paths), layer=layer, net=net, primitives=prims, phase=None,
                                element=None, polarity=0))  # fmt: skip
        return len(paths) - 1

    def radial(end: PhaseEnd, r_end_mm: float) -> Line:
        a, r0 = end.angle_rad, math.hypot(end.via.x_mm, end.via.y_mm) + max(0.0, (bw - pad_mm) / 2)
        return Line(x1_mm=r0 * math.cos(a), y1_mm=r0 * math.sin(a), x2_mm=r_end_mm * math.cos(a),
                    y2_mm=r_end_mm * math.sin(a), width_mm=bw, role=PrimitiveRole.LINK)  # fmt: skip

    for link in links:
        r_mm = rings.radius_mm(link.level)
        for tap in link.taps:
            stub = radial(tap, r_mm)
            vias.append(replace(template, id=first_via_id + len(vias), x_mm=stub.x2_mm, y_mm=stub.y2_mm,
                                role=ViaRole.RING, net=link.net))  # fmt: skip
            stub_of[(tap.phase, tap.sign)] = (add(stub_layer, link.net, (stub,)), stub)
        arc = Arc(cx_mm=0.0, cy_mm=0.0, r_mm=r_mm, start_rad=link.start_rad, sweep_rad=link.sweep_rad, width_mm=bw,
                  role=PrimitiveRole.RING)  # fmt: skip
        add(ring_layer, link.net, (arc,))

    leads = [(ends[(phase, 1)], LINE_NET[phase]) for phase in Phase]
    if connection.topology is ConnectionTopology.STAR and connection.neutral_pad:
        leads.append((links[0].taps[2], "N"))
    pads: list[Pad] = []
    for end, net in leads:
        a = end.angle_rad
        tapped = stub_of.get((end.phase, end.sign))
        if tapped is None:
            add(stub_layer, net, (radial(end, r_pad),))
        else:  # the lead continues the tap stub beyond its ring via, one path (Xcoil: same object)
            index, stub = tapped
            extension = Line(x1_mm=stub.x2_mm, y1_mm=stub.y2_mm, x2_mm=r_pad * math.cos(a), y2_mm=r_pad * math.sin(a),
                             width_mm=bw, role=PrimitiveRole.LINK)  # fmt: skip
            paths[index] = replace(paths[index], net=net, primitives=(stub, extension))
        pads.append(
            Pad(
                id=first_pad_id + len(pads), x_mm=r_pad * math.cos(a), y_mm=r_pad * math.sin(a), shape="round",
                width_mm=connection.terminal_pad_mm, height_mm=connection.terminal_pad_mm, rotation_rad=0.0,
                drill_mm=connection.terminal_drill_mm, layer=None if connection.terminal_drill_mm > 0 else stub_layer,
                net=net, label=net,
            )
        )  # fmt: skip
    return Interconnect(paths=tuple(paths), vias=tuple(vias), pads=tuple(pads), r_max_mm=r_pad + pad_reach)
