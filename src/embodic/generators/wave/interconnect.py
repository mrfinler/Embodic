"""Star or delta interconnect of the wave winding (engine.js l.1225-1335, ``buildInterconnect``, wave options).

The wave builders call Xcoil's routine with ``neck: true`` and no stub layer: the tap stubs share the ring object, the
ring layer is the last copper layer, the line stubs sit on layer 0, and a delta mesh closes in the order A, C, B. Only
that path is ported; the sector and serpentine options belong to their own builders.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from embodic.generators.wave.build import Terminal
from embodic.generators.wave.xprim import XArc, XLine, XPrim, ang_norm, polar

DELTA_PAIRS = ((0, 2), (2, 1), (1, 0))
LINE_NETS = ("U", "V", "W")
ItemKind = Literal["line", "ring", "neutral_pad"]


@dataclass(frozen=True, slots=True, kw_only=True)
class PadSpec:
    """Terminal pad inputs: round pad of width ``size`` (the pad reach is its radius)."""

    size: float
    drill: float


@dataclass(frozen=True, slots=True, kw_only=True)
class RingLink:
    """One neutral ring or delta link: net, angular span, the terminals it taps and its ring level."""

    net: str
    a1: float
    a2: float
    taps: tuple[Terminal, ...]
    level: int
    layer_index: int = 0
    unroutable: bool = False  # crosses a link on every ring layer; placed on layer 0 above all others


@dataclass(frozen=True, slots=True, kw_only=True)
class IcItem:
    """One interconnect object on one copper layer (Xcoil ``ic.items`` entry)."""

    kind: ItemKind
    layer: int
    net: str
    prims: tuple[XPrim, ...]
    touch: tuple[int, ...]
    phase: int | None = None  # line items
    link: RingLink | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class IcPad:
    """A terminal pad on copper layer ``layer``; ``phase`` is -1 for the neutral pad."""

    x: float
    y: float
    net: str
    phase: int
    layer: int


@dataclass(frozen=True, slots=True, kw_only=True)
class Interconnect:
    """Xcoil's ``ic`` result: items, pads, links, the outer pad radius and the outermost copper radius."""

    items: tuple[IcItem, ...]
    pads: tuple[IcPad, ...]
    links: tuple[RingLink, ...]
    r_pad: float
    r_edge: float
    n_levels: int
    unroutable: bool


def _angle(t: Terminal) -> float:
    return math.atan2(t.y, t.x)


def _terminal(terms: Sequence[Terminal], phase: int, sign: int) -> Terminal:
    return next(t for t in terms if t.phase == phase and t.sign == sign)


def _star_link(terms: Sequence[Terminal]) -> RingLink:
    minus = [_terminal(terms, ph, -1) for ph in range(3)]
    a = [ang_norm(_angle(t)) for t in minus]
    order = sorted(range(3), key=lambda k: a[k])
    gaps = [ang_norm(a[order[(k + 1) % 3]] - a[order[k]]) for k in range(3)]
    big = gaps.index(max(gaps))
    first = order[(big + 1) % 3]
    seq = [first, order[(big + 2) % 3], order[big]]
    a1 = a[first]
    return RingLink(net="N", a1=a1, a2=a1 + ang_norm(a[seq[2]] - a1), taps=tuple(minus[k] for k in seq), level=0)


def _relation(lo1: float, hi1: float, a1: float, a2: float, margin: float) -> Literal["disjoint", "encloses", "cross"]:
    rel: Literal["disjoint", "encloses", "cross"] = "disjoint"
    for wrap in (-1, 0, 1):
        lo2 = min(a1, a2) - margin + wrap * 2 * math.pi
        hi2 = max(a1, a2) + margin + wrap * 2 * math.pi
        if hi2 < lo1 or lo2 > hi1:
            continue
        if lo2 > lo1 and hi2 < hi1:
            rel = "encloses"
        else:
            return "cross"
    return rel


def _delta_links(terms: Sequence[Terminal], layer_links: Sequence[int], base: float, bus_width: float,
                 clearance: float) -> list[RingLink]:  # fmt: skip
    """Delta links, shorter spans first; a link may enclose earlier ones on a layer but not partly overlap them."""
    raw = []
    for src, dst in DELTA_PAIRS:
        frm, to = _terminal(terms, src, -1), _terminal(terms, dst, 1)
        a_f = _angle(frm)
        d = ang_norm(_angle(to) - a_f)
        a2 = a_f + d if d <= math.pi else a_f - (2 * math.pi - d)
        raw.append((f"D{src}", a_f, a2, (frm, to)))
    raw.sort(key=lambda x: abs(x[2] - x[1]))
    margin = (bus_width + clearance) / max(1.0, abs(base))
    placed: list[RingLink] = []
    for net, a1, a2, taps in raw:
        lo1, hi1 = min(a1, a2) - margin, max(a1, a2) + margin
        chosen: tuple[int, int] | None = None
        for c in range(len(layer_links)):
            on_layer = [o for o in placed if o.layer_index == c]
            rels = [_relation(lo1, hi1, o.a1, o.a2, margin) for o in on_layer]
            if "cross" in rels:
                continue
            level = 0
            for o, rel in zip(on_layer, rels, strict=True):
                if rel == "encloses":
                    level = max(level, o.level + 1)
            chosen = (c, level)
            break
        placed.append(RingLink(net=net, a1=a1, a2=a2, taps=taps, level=chosen[1] if chosen else len(placed),
                               layer_index=chosen[0] if chosen else 0, unroutable=chosen is None))  # fmt: skip
    return placed


def build_interconnect(
    terms: Sequence[Terminal], *, connection: Literal["star", "delta"], base: float, bus_width: float,
    clearance: float, via_pad: float, pad: PadSpec, link_layers: Sequence[int], line_layer: int,
) -> Interconnect:  # fmt: skip
    """Xcoil buildInterconnect with ``neck`` and no stub layer, outward from copper radius ``base``."""
    bw, s = bus_width, clearance
    if connection == "star":
        links = [_star_link(terms)]
    else:
        links = _delta_links(terms, link_layers, base, bw, s)
    n_levels = max(lk.level for lk in links) + 1
    ring_half = bw / 2
    pitch = 2 * ring_half + s

    def r_ring(j: int) -> float:
        return base + (s + ring_half + j * pitch)

    def stub_prims(t: Terminal, r_end: float) -> list[XPrim]:
        a = _angle(t)
        e = polar(r_end, a)
        wn, r_n = min(bw, via_pad), r_ring(0)
        if wn >= bw - 1e-9:
            return [XLine(x1=t.x, y1=t.y, x2=e[0], y2=e[1], w=bw, kind="stub")]
        n = polar(r_n, a)
        out: list[XPrim] = [XLine(x1=t.x, y1=t.y, x2=n[0], y2=n[1], w=wn, kind="stub")]
        if r_end - r_n > 1e-9:
            out.append(XLine(x1=n[0], y1=n[1], x2=e[0], y2=e[1], w=bw, kind="stub"))
        return out

    pad_r = pad.size / 2
    r_pad = base + (s + n_levels * pitch + pad_r)
    items: list[IcItem] = []
    pads: list[IcPad] = []
    for lk in links:
        radius = r_ring(lk.level)
        prims: list[XPrim] = []
        for t in lk.taps:
            prims.extend(stub_prims(t, radius))
        prims.append(XArc(cx=0.0, cy=0.0, r=radius, a1=lk.a1, a2=lk.a2, w=bw, kind="ring"))
        items.append(IcItem(kind="ring", layer=link_layers[lk.layer_index], net=lk.net, prims=tuple(prims),
                            touch=tuple(t.via for t in lk.taps), link=lk))  # fmt: skip
    for phase in range(3):
        tp = _terminal(terms, phase, 1)
        a = _angle(tp)
        pe = polar(r_pad, a)
        items.append(IcItem(kind="line", layer=line_layer, net=LINE_NETS[phase], prims=tuple(stub_prims(tp, r_pad)),
                            touch=(tp.via,), phase=phase))  # fmt: skip
        pads.append(IcPad(x=pe[0], y=pe[1], net=LINE_NETS[phase], phase=phase, layer=line_layer))
    if connection == "star":
        tn = links[0].taps[2]
        a = _angle(tn)
        pe, rr = polar(r_pad, a), polar(r_ring(0), a)
        layer = link_layers[0]
        items.append(IcItem(kind="neutral_pad", layer=layer, net="N",
                            prims=(XLine(x1=rr[0], y1=rr[1], x2=pe[0], y2=pe[1], w=bw, kind="stub"),),
                            touch=()))  # fmt: skip
        pads.append(IcPad(x=pe[0], y=pe[1], net="N", phase=-1, layer=layer))
    return Interconnect(
        items=tuple(items), pads=tuple(pads), links=tuple(links), r_pad=r_pad, r_edge=r_pad + pad_r,
        n_levels=n_levels, unroutable=any(lk.unroutable for lk in links),
    )  # fmt: skip
