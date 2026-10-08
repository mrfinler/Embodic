"""Star or delta links and the U/V/W/N leads beyond the winding envelope (Xcoil buildInterconnect, engine.js l.1225).

Port for the serpentine call (``compute``, engine.js l.2527): line stubs on layer 0, link rings on the lower layers,
no stub layer and no neck. Xcoil makes one object per link (its tap stubs and the ring arc together) and one per lead.
"""

import math
from dataclasses import dataclass, replace
from itertools import pairwise
from typing import Literal

from embodic.generators.serpentine.corners import Point
from embodic.geometry.primitives import Arc, Line, PrimitiveRole, hypot_mm
from embodic.model.connection import ConnectionSpec
from embodic.model.vocabulary import ConnectionTopology

LINE_NETS = ("U", "V", "W")
DELTA_PAIRS = ((0, 1), (1, 2), (2, 0))
TWO_PI = 2 * math.pi


@dataclass(frozen=True, slots=True, kw_only=True)
class Terminal:
    """A winding end on a terminal via: phase index, sign (+1 phase start T1, -1 phase end T2), position, via index."""

    phase: int
    sign: Literal[1, -1]
    x: float
    y: float
    via: int

    @property
    def angle(self) -> float:
        """Polar angle of the via centre."""
        return math.atan2(self.y, self.x)

    @property
    def radius(self) -> float:
        """Radius of the via centre."""
        return hypot_mm(self.x, self.y)


@dataclass(frozen=True, slots=True, kw_only=True)
class Link:
    """One ring arc from ``a1`` to ``a2`` (signed) with the terminals it taps; ``layer_idx`` indexes the link layers."""

    net: str
    a1: float
    a2: float
    taps: tuple[Terminal, ...]
    level: int = 0
    layer_idx: int = 0


@dataclass(frozen=True, slots=True, kw_only=True)
class RingItem:
    """Xcoil item with ``link``: the tap stubs and the ring, one object there. ``radius`` is the ring radius.

    ``arcs`` is Xcoil's single ring arc cut at every tap between its ends, so each cut is the end node of the tap
    stub and of both arcs (D-006 rule 3). A delta link has two taps and keeps one arc.
    """

    layer: int
    link: Link
    stubs: tuple[Line, ...]
    arcs: tuple[Arc, ...]
    radius_mm: float


@dataclass(frozen=True, slots=True, kw_only=True)
class LeadItem:
    """Xcoil item with ``line``: the stub from a phase start to its line pad."""

    layer: int
    net: str
    phase: int
    stub: Line


@dataclass(frozen=True, slots=True, kw_only=True)
class NeutralLeadItem:
    """Xcoil ``neutralPad`` item: the stub from the star ring to the N pad."""

    layer: int
    stub: Line


IcItem = RingItem | LeadItem | NeutralLeadItem


@dataclass(frozen=True, slots=True, kw_only=True)
class PadSite:
    """A terminal pad: position, net, phase index (-1 for N) and the layer of an SMD pad."""

    x: float
    y: float
    net: str
    phase: int
    angle_rad: float
    layer: int


@dataclass(frozen=True, slots=True, kw_only=True)
class Interconnect:
    """Xcoil ``buildInterconnect`` result."""

    items: tuple[IcItem, ...]
    pads: tuple[PadSite, ...]
    links: tuple[Link, ...]
    r_pad: float
    r_edge: float
    n_levels: int


def _norm(a: float) -> float:
    """Xcoil ``angNorm``: angle in [0, 2 pi)."""
    a = a % TWO_PI
    return a + TWO_PI if a < 0 else a


def _polar(r: float, a: float) -> Point:
    return (r * math.cos(a), r * math.sin(a))


def _terminal(terms: tuple[Terminal, ...], phase: int, sign: int) -> Terminal:
    return next(t for t in terms if t.phase == phase and t.sign == sign)


def _star_link(terms: tuple[Terminal, ...]) -> Link:
    minus = [_terminal(terms, k, -1) for k in range(3)]
    a = [_norm(t.angle) for t in minus]
    order = sorted(range(3), key=lambda k: a[k])
    gaps = [_norm(a[order[(k + 1) % 3]] - a[order[k]]) for k in range(3)]
    big = gaps.index(max(gaps))
    first = order[(big + 1) % 3]
    seq = (first, order[(big + 2) % 3], order[big])
    a1 = a[first]
    return Link(net="N", a1=a1, a2=a1 + _norm(a[seq[2]] - a1), taps=tuple(minus[k] for k in seq))


def _delta_links(terms: tuple[Terminal, ...]) -> list[Link]:
    links = []
    for src, dst in DELTA_PAIRS:
        start, end = _terminal(terms, src, -1), _terminal(terms, dst, 1)
        a_from = start.angle
        d = _norm(end.angle - a_from)
        a2 = a_from + d if d <= math.pi else a_from - (TWO_PI - d)
        links.append(Link(net=f"D{src}", a1=a_from, a2=a2, taps=(start, end)))
    return sorted(links, key=lambda lk: abs(lk.a2 - lk.a1))


def _relation(link: Link, other: Link, margin: float) -> Literal["disjoint", "encloses", "cross"]:
    lo1, hi1 = min(link.a1, link.a2) - margin, max(link.a1, link.a2) + margin
    result: Literal["disjoint", "encloses", "cross"] = "disjoint"
    for wrap in (-1, 0, 1):
        lo2 = min(other.a1, other.a2) - margin + wrap * TWO_PI
        hi2 = max(other.a1, other.a2) + margin + wrap * TWO_PI
        if hi2 < lo1 or lo2 > hi1:
            continue
        if not (lo2 > lo1 and hi2 < hi1):
            return "cross"
        result = "encloses"
    return result


def _place_delta(links: list[Link], layers: int, margin: float) -> list[Link]:
    """Shorter spans first. A link may enclose earlier links on its layer but must not partly overlap one."""
    placed: list[Link] = []
    for link in links:
        chosen = None
        for c in range(layers):
            on_layer = [o for o in placed if o.layer_idx == c]
            relations = [_relation(link, o, margin) for o in on_layer]
            if "cross" in relations:
                continue
            level = max((o.level + 1 for o, r in zip(on_layer, relations, strict=True) if r == "encloses"), default=0)
            chosen = replace(link, layer_idx=c, level=level)
            break
        placed.append(chosen if chosen is not None else replace(link, layer_idx=0, level=len(placed)))
    return placed


def _ring_arcs(link: Link, radius_mm: float, width_mm: float) -> tuple[Arc, ...]:
    """Return the ring arc from ``a1`` to ``a2`` cut at the taps between its ends (angles as Xcoil l.1366)."""
    cuts = [link.a1, *(link.a1 + _norm(t.angle - link.a1) for t in link.taps[1:-1]), link.a2]
    return tuple(
        Arc(
            cx_mm=0.0,
            cy_mm=0.0,
            r_mm=radius_mm,
            start_rad=a,
            sweep_rad=b - a,
            width_mm=width_mm,
            role=PrimitiveRole.RING,
        )
        for a, b in pairwise(cuts)
    )


def build_interconnect(
    connection: ConnectionSpec,
    clearance_mm: float,
    via_pad: float,
    terms: tuple[Terminal, ...],
    base: float,
    sg: int,
    layer_lines: int,
    link_layers: tuple[int, ...],
) -> Interconnect:
    """Rings or delta links, the line stubs and the terminal pads beyond ``base`` (outermost or innermost copper).

    ``terms`` are the terminal vias of all three phases; ``link_layers`` are the layers that may carry link rings,
    first choice first.
    """
    bw, s = connection.ring_width_mm, clearance_mm
    if connection.topology is ConnectionTopology.STAR:
        links = [_star_link(terms)]
    else:
        links = _place_delta(_delta_links(terms), len(link_layers), (bw + s) / max(1.0, abs(base)))
    n_levels = max(lk.level for lk in links) + 1
    ring_half = bw / 2
    pitch = 2 * ring_half + s

    def ring_radius(level: int) -> float:
        return base + sg * (s + ring_half + level * pitch)

    def stub(t: Terminal, r_end: float) -> Line:
        offset = max(0.0, (bw - via_pad) / 2)
        start = (t.x + sg * offset * t.x / t.radius, t.y + sg * offset * t.y / t.radius)
        end = _polar(r_end, t.angle)
        return Line(x1_mm=start[0], y1_mm=start[1], x2_mm=end[0], y2_mm=end[1], width_mm=bw, role=PrimitiveRole.STUB)

    pad_reach = connection.terminal_pad_mm / 2
    r_pad = base + sg * (s + n_levels * pitch + pad_reach)
    items: list[IcItem] = []
    for lk in links:
        r = ring_radius(lk.level)
        items.append(
            RingItem(
                layer=link_layers[lk.layer_idx],
                link=lk,
                stubs=tuple(stub(t, r) for t in lk.taps),
                arcs=_ring_arcs(lk, r, bw),
                radius_mm=r,
            )
        )
    pads: list[PadSite] = []
    for k in range(3):
        t = _terminal(terms, k, 1)
        x, y = _polar(r_pad, t.angle)
        items.append(LeadItem(layer=layer_lines, net=LINE_NETS[k], phase=k, stub=stub(t, r_pad)))
        pads.append(PadSite(x=x, y=y, net=LINE_NETS[k], phase=k, angle_rad=t.angle, layer=layer_lines))
    if connection.topology is ConnectionTopology.STAR and connection.neutral_pad:
        t = links[0].taps[2]
        start = _polar(ring_radius(0), t.angle)
        end = _polar(r_pad, t.angle)
        neutral = Line(x1_mm=start[0], y1_mm=start[1], x2_mm=end[0], y2_mm=end[1], width_mm=bw, role=PrimitiveRole.STUB)
        items.append(NeutralLeadItem(layer=link_layers[0], stub=neutral))
        pads.append(PadSite(x=end[0], y=end[1], net="N", phase=-1, angle_rad=t.angle, layer=link_layers[0]))
    return Interconnect(
        items=tuple(items),
        pads=tuple(pads),
        links=tuple(links),
        r_pad=r_pad,
        r_edge=r_pad + sg * pad_reach,
        n_levels=n_levels,
    )
