"""Overlapping radial wave winding (engine.js l.2095-2230: ``buildWaveOverlap``, layout half of ``computeWaveOverlap``).

On the T layers the radial conductors sit under the even poles and the end-turns are concentric arcs at the outer rim
sweeping one pole pitch; the B layers hold the odd poles with their arcs at the inner rim. Every via sits at the
foot of a radial conductor of the other layer. Terminals leave on rim stubs: a star ring inside the inner arcs, line
leads on layer 1 beyond the outer arcs, and the minus terminals of an open winding inside the inner arcs.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Literal

from embodic.generators.wave.assemble import (
    Obj,
    SeriesElement,
    WaveBuild,
    build_in_layer_order,
)
from embodic.generators.wave.build import MINUS, PHASE_NAMES, Terminal, WaveVia
from embodic.generators.wave.derive import WaveFrame
from embodic.generators.wave.fillet import fillet_path, taper_junctions
from embodic.generators.wave.interconnect import IcItem, IcPad, RingLink
from embodic.generators.wave.xprim import XArc, XLine, XPrim, ang_norm, polar, reverse_prims, rotate_prims
from embodic.model.design import DesignParameters
from embodic.model.vocabulary import ConnectionTopology

NetKind = Literal["T", "B"]
SPREAD_ITERATIONS = 80


@dataclass(frozen=True, slots=True, kw_only=True)
class OverlapTrack:
    """One track of the overlapping winding, in the direction of positive phase current."""

    kind: NetKind
    slot: int
    phase: int
    sign: int
    special: Literal["shift"] | None
    prims: tuple[XPrim, ...]
    end_via: int  # slot of the via the track ends on, in current direction


@dataclass(frozen=True, slots=True, kw_only=True)
class OverlapChain:
    """Phase belt ``belt`` of an even pole and whether its tracks chain as T or B."""

    phase: int
    belt: int
    sign: int
    chain: NetKind


class _Canon:
    """Canonical T and B tracks at slot angle 0 for each nesting level, with their cache."""

    def __init__(self, frame: WaveFrame) -> None:
        self.frame = frame
        self.rho = frame.p.fillet_radius_mm if frame.p.rounded else 0.0
        self._cache: dict[tuple[NetKind, int, bool], list[XPrim]] = {}

    def get(self, kind: NetKind, level: int, shift: bool) -> list[XPrim]:
        key = (kind, level, shift)
        if key not in self._cache:
            self._cache[key] = self._t(level, shift) if kind == "T" else self._b(level, shift)
        return self._cache[key]

    def _finish(self, prims: list[XPrim], end_width_mm: float) -> list[XPrim]:
        prims = fillet_path(prims, self.rho, None)
        return taper_junctions(prims) if end_width_mm != self.frame.w else prims

    def _t(self, level: int, shift: bool) -> list[XPrim]:
        f = self.frame
        p = f.p
        sweep = f.tau - f.d_theta if shift else f.tau
        ro = f.rho_out(level)
        prims: list[XPrim] = [
            XLine(x1=f.rho_in(level), y1=0.0, x2=p.r_in, y2=0.0, w=f.w, kind="leg"),
            XLine(x1=p.r_in, y1=0.0, x2=p.r_out, y2=0.0, w=f.w, kind="side"),
            XLine(x1=p.r_out, y1=0.0, x2=ro, y2=0.0, w=f.w, kind="leg"),
            XArc(cx=0.0, cy=0.0, r=ro, a1=0.0, a2=sweep, w=f.w_out, kind="endturn"),
        ]
        if shift:
            e1, e2 = polar(ro, sweep), polar(f.rho_out(level + 1), sweep)
            prims.append(XLine(x1=e1[0], y1=e1[1], x2=e2[0], y2=e2[1], w=f.w, kind="leg"))
        return self._finish(prims, f.w_out)

    def _b(self, level: int, shift: bool) -> list[XPrim]:
        f = self.frame
        p = f.p
        sweep = f.tau - f.d_theta if shift else f.tau
        ri = f.rho_in(level)
        prims: list[XPrim] = [
            XLine(x1=f.rho_out(level), y1=0.0, x2=p.r_out, y2=0.0, w=f.w, kind="leg"),
            XLine(x1=p.r_out, y1=0.0, x2=p.r_in, y2=0.0, w=f.w, kind="side"),
            XLine(x1=p.r_in, y1=0.0, x2=ri, y2=0.0, w=f.w, kind="leg"),
            XArc(cx=0.0, cy=0.0, r=ri, a1=0.0, a2=sweep, w=f.w_in, kind="endturn"),
        ]
        if shift:
            e1, e2 = polar(ri, sweep), polar(f.rho_in(level + 1), sweep)
            prims.append(XLine(x1=e1[0], y1=e1[1], x2=e2[0], y2=e2[1], w=f.w, kind="leg"))
        return self._finish(prims, f.w_in)


@dataclass(frozen=True, slots=True, kw_only=True)
class OverlapGeometry:
    """Xcoil's ``G`` of buildWaveOverlap."""

    tracks: tuple[OverlapTrack, ...]
    vias: tuple[WaveVia, ...]
    terms: tuple[Terminal, ...]


def _special(frame: WaveFrame, chains: Sequence[OverlapChain]) -> dict[int, Literal["removed", "shift"]]:
    special: dict[int, Literal["removed", "shift"]] = {}
    for z in chains:
        for j in range(frame.q):
            slot = z.belt * frame.q + j + (0 if z.chain == "T" else frame.mq)
            special[slot] = "removed" if j == 0 else "shift"
    return special


def _terminals(frame: WaveFrame, chains: Sequence[OverlapChain], vias: list[WaveVia]) -> list[Terminal]:
    q, mq = frame.q, frame.mq
    terms: list[Terminal] = []
    for z in chains:
        a0, aq = z.belt * q, z.belt * q + q - 1
        if z.chain == "T":
            outer, inner = (aq + mq) % frame.n_slots, a0
        else:
            outer, inner = (a0 + mq) % frame.n_slots, (aq + 2 * mq) % frame.n_slots
        name = PHASE_NAMES[z.phase]
        vias[outer] = replace(vias[outer], terminal=True, kind="T1", label=name + "+")
        vias[inner] = replace(vias[inner], terminal=True, kind="T2", label=name + MINUS)
        terms.append(Terminal(phase=z.phase, sign=1, x=vias[outer].x, y=vias[outer].y, via=outer))
        terms.append(Terminal(phase=z.phase, sign=-1, x=vias[inner].x, y=vias[inner].y, via=inner))
    return terms


def build_overlap_geometry(frame: WaveFrame) -> OverlapGeometry:
    """Xcoil buildWaveOverlap: tracks, the one via per slot, and the terminals."""
    q, mq, m, n_slots = frame.q, frame.mq, frame.m, frame.n_slots
    chains = [
        OverlapChain(phase=frame.belt_phase(b), belt=b, sign=frame.belt_sign(b),
                     chain="T" if frame.belt_sign(b) > 0 else "B")
        for b in range(m)
    ]  # fmt: skip
    special = _special(frame, chains)
    canon = _Canon(frame)
    tracks: list[OverlapTrack] = []
    vias: list[WaveVia] = []
    for k in range(n_slots):
        level = mq - 1 - k % mq
        ang = frame.slot_angle(k)
        beta = (k // q) % (2 * m)
        phase, sgn = frame.belt_phase(beta), frame.belt_sign(beta)
        is_t = (k % n_slots) // mq % 2 == 0
        pv = polar(frame.rho_in(level) if is_t else frame.rho_out(level), ang)
        vias.append(WaveVia(ring="inner" if is_t else "outer", idx=k, phase=phase, kind="W", x=pv[0], y=pv[1],
                            terminal=False, label=""))  # fmt: skip
        kind = special.get(k)
        if kind == "removed":
            continue
        shifted = kind == "shift"
        pr = rotate_prims(canon.get("T" if is_t else "B", level, shifted), ang)
        forward = sgn > 0 if is_t else sgn < 0
        far = (k + mq - (1 if shifted else 0)) % n_slots  # the via at the other end of the track
        tracks.append(OverlapTrack(kind="T" if is_t else "B", slot=k, phase=phase, sign=sgn,
                                   special="shift" if shifted else None,
                                   prims=tuple(pr if forward else reverse_prims(pr)),
                                   end_via=far if forward else k))  # fmt: skip
    terms = _terminals(frame, chains, vias)
    return OverlapGeometry(tracks=tuple(tracks), vias=tuple(vias), terms=tuple(terms))


@dataclass(slots=True)
class _PadDef:
    term: Terminal
    a: float
    ap: float = 0.0


def spread_pad_angles(defs: Sequence[_PadDef], r_pad: float, pad_r: float, s: float) -> bool:
    """Xcoil spreadPadAngles: move pads that sit closer than their size apart along the circle; True when any moved."""
    need = 2 * math.asin(min(1.0, (2 * pad_r + s) / (2 * r_pad)))
    ordered = sorted(defs, key=lambda d: ang_norm(d.a))
    for d in ordered:
        d.ap = ang_norm(d.a)
    if len(ordered) > 1:
        for _ in range(SPREAD_ITERATIONS):
            moved = False
            for k, a in enumerate(ordered):
                b = ordered[(k + 1) % len(ordered)]
                gap = ang_norm(b.ap - a.ap)
                if gap < need - 1e-9:
                    delta = (need - gap) / 2
                    a.ap -= delta
                    b.ap += delta
                    moved = True
            if not moved:
                break
    return any(abs(ang_norm(d.ap - d.a + math.pi) - math.pi) > 1e-9 for d in defs)


def corridor_prims(
    start: tuple[float, float], a: float, ap: float, r_cor: float, r_pad: float, w: float, rho: float
) -> list[XPrim]:  # fmt: skip
    """Xcoil corridorPrims: a stub straight to the pad, or radial to the corridor, along it, and radial again."""
    pe = polar(r_pad, ap)
    d_a = ang_norm(ap - a + math.pi) - math.pi
    if abs(d_a) < 1e-9:
        return [XLine(x1=start[0], y1=start[1], x2=pe[0], y2=pe[1], w=w, kind="stub")]
    c1, c2 = polar(r_cor, a), polar(r_cor, a + d_a)
    path: list[XPrim] = [
        XLine(x1=start[0], y1=start[1], x2=c1[0], y2=c1[1], w=w, kind="stub"),
        XArc(cx=0.0, cy=0.0, r=r_cor, a1=a, a2=a + d_a, w=w, kind="stub"),
        XLine(x1=c2[0], y1=c2[1], x2=pe[0], y2=pe[1], w=w, kind="stub"),
    ]
    return fillet_path(path, min(w, rho or 0.0), w)


def _star_ring(
    frame: WaveFrame, design: DesignParameters, terms: Sequence[Terminal], r_min_cu: float, pad_r: float
) -> tuple[IcItem, IcPad, float]:  # fmt: skip
    """Neutral ring inside the inner arcs on layer 0, joining the three minus terminals; the N pad sits inside it."""
    bw, s = frame.p.bus_width_mm, frame.s
    r_n = r_min_cu - s - bw / 2
    wn = min(bw, frame.pad)
    taps = tuple(t for t in terms if t.sign < 0)
    ang = [ang_norm(math.atan2(t.y, t.x)) for t in taps]
    order = sorted(range(3), key=lambda k: ang[k])
    gaps = [ang_norm(ang[order[(k + 1) % 3]] - ang[order[k]]) for k in range(3)]
    big = gaps.index(max(gaps))
    first, last = order[(big + 1) % 3], order[big]
    a1 = ang[first]
    a2 = a1 + ang_norm(ang[last] - a1)
    prims: list[XPrim] = [XArc(cx=0.0, cy=0.0, r=r_n, a1=a1, a2=a2, w=bw, kind="ring")]
    for t in taps:
        e = polar(r_n, math.atan2(t.y, t.x))
        prims.append(XLine(x1=t.x, y1=t.y, x2=e[0], y2=e[1], w=wn, kind="stub"))
    an = (a1 + a2) / 2
    r_pad_n = r_n - bw / 2 - s - pad_r
    pn, rr = polar(r_pad_n, an), polar(r_n, an)
    prims.append(XLine(x1=rr[0], y1=rr[1], x2=pn[0], y2=pn[1], w=bw, kind="stub"))
    seq = (first, order[(big + 2) % 3], last)
    ring = RingLink(net="N", a1=a1, a2=a2, taps=tuple(taps[k] for k in seq), level=0)
    item = IcItem(kind="ring", layer=0, net="N", prims=tuple(prims), touch=tuple(t.via for t in taps), link=ring)
    return item, IcPad(x=pn[0], y=pn[1], net="N", phase=-1, layer=0), r_pad_n - pad_r


def _leads(
    frame: WaveFrame, design: DesignParameters, terms: Sequence[Terminal], sign: int, r_base: float, pad_r: float,
    open_winding: bool,
) -> tuple[list[IcItem], list[IcPad], float]:  # fmt: skip
    """Line leads (plus side, layer 1) or the minus-terminal pads of an open winding (minus side, layer 0)."""
    bw, s = frame.p.bus_width_mm, frame.s
    listed = [t for t in terms if t.sign == sign]
    w_s = bw if sign > 0 else min(bw, frame.pad)
    defs = [_PadDef(term=t, a=math.atan2(t.y, t.x)) for t in listed]
    r_pad0 = r_base + sign * (s + pad_r)
    r_cor = r_base + sign * (s + w_s / 2)
    r_pad_c = r_cor + sign * (w_s / 2 + s + pad_r)
    moved = spread_pad_angles(defs, min(r_pad0, r_pad_c), pad_r, s)
    r_pad = r_pad_c if moved else r_pad0
    rho = frame.p.fillet_radius_mm if frame.p.rounded else 0.0
    layer = 1 if sign > 0 else 0
    items: list[IcItem] = []
    pads: list[IcPad] = []
    for d in defs:
        t = d.term
        net = PHASE_NAMES[t.phase] + ("+" if t.sign > 0 else "-") if open_winding else ("U", "V", "W")[t.phase]
        pe = polar(r_pad, d.ap)
        prims = corridor_prims((t.x, t.y), d.a, d.ap, r_cor, r_pad, w_s, rho)
        items.append(IcItem(kind="line", layer=layer, net=net, prims=tuple(prims), touch=(t.via,), phase=t.phase))
        pads.append(IcPad(x=pe[0], y=pe[1], net=net, phase=t.phase, layer=layer))
    edge = r_pad + pad_r if sign > 0 else r_pad - pad_r
    return items, pads, edge


def build_overlap(design: DesignParameters, frame: WaveFrame) -> WaveBuild:
    """Xcoil computeWaveOverlap up to the layout: objects per layer, vias, terminal pads and the copper envelope."""
    geometry = build_overlap_geometry(frame)
    r_max_cu = frame.rho_out(frame.mq - 1) + max(frame.w_out, frame.pad, frame.w) / 2
    r_min_cu = frame.rho_in(frame.mq - 1) - max(frame.w_in, frame.pad, frame.w) / 2
    conn = design.connection
    three = frame.m == 3
    star = three and conn.draw_interconnect and conn.topology is ConnectionTopology.STAR
    open_winding = not three or conn.topology is ConnectionTopology.OPEN
    wants_ic = conn.draw_interconnect and three and not open_winding
    pad_r = conn.terminal_pad_mm / 2
    r_min_all, r_max_all = r_min_cu, r_max_cu
    items: list[IcItem] = []
    pads: list[IcPad] = []
    if star:
        item, pad, edge = _star_ring(frame, design, geometry.terms, r_min_cu, pad_r)
        items.append(item)
        pads.append(pad)
        r_min_all = min(r_min_all, edge)
    if wants_ic or open_winding:
        plus_items, plus_pads, edge = _leads(frame, design, geometry.terms, 1, r_max_cu, pad_r, open_winding)
        items += plus_items
        pads += plus_pads
        r_max_all = max(r_max_all, edge)
        if open_winding:
            minus_items, minus_pads, edge = _leads(frame, design, geometry.terms, -1, r_min_cu, pad_r, True)
            items += minus_items
            pads += minus_pads
            r_min_all = min(r_min_all, edge)
    objects, elements = _objects(frame, geometry, items)
    build = build_in_layer_order(objects, elements, geometry.vias, tuple(pads), r_min_cu=r_min_cu, r_max_cu=r_max_cu,
                                 r_max_all=r_max_all)  # fmt: skip
    return replace(build, r_min_all=r_min_all)


def _objects(
    frame: WaveFrame, geometry: OverlapGeometry, items: Sequence[IcItem]
) -> tuple[list[Obj], list[SeriesElement]]:
    objects: list[Obj] = []
    by_slot: dict[tuple[str, int], list[int]] = {}
    for layer in range(frame.layers):
        kind: NetKind = "T" if layer % 2 == 0 else "B"
        for t in (t for t in geometry.tracks if t.kind == kind):
            by_slot.setdefault((kind, t.slot), []).append(len(objects))
            objects.append(Obj(layer=layer, kind="track", prims=t.prims, phase=t.phase, element=t.slot,
                               polarity=1 if t.sign > 0 else -1, end_via=t.end_via))  # fmt: skip
    for item in items:
        objects.append(Obj(layer=item.layer, kind="ic", prims=item.prims, phase=item.phase, net=item.net, ic=item))
    elements = [SeriesElement(phase=t.phase, objects=tuple(by_slot[(t.kind, t.slot)])) for t in geometry.tracks]
    return objects, elements


__all__ = ["build_overlap", "build_overlap_geometry", "corridor_prims", "spread_pad_angles"]
