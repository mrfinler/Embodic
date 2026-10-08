"""Tracks, via rings, terminals and group links of the T/B wave winding (engine.js l.1628-1708, ``buildWave``).

Odd layers carry the T tracks (inner via to outer via, sweeping +tau/2 at each end), even layers the mirror-image B
tracks; a through via at each track end stitches T to B. Slot 0 of every commutation belt is removed (its via becomes a
terminal) and the other slots of the belt use the shortened ``t_shift`` track.
"""

import itertools
import math
from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Literal

from embodic.generators.wave.derive import WaveFrame
from embodic.generators.wave.track import wave_track
from embodic.generators.wave.xprim import (
    XArc,
    XLine,
    XPrim,
    mirror_prims_x,
    polar,
    reverse_prims,
    rotate_prims,
)

PHASE_NAMES = ("A", "B", "C")
MINUS = "−"
MIN_LINK_RADIUS_MM = 0.5
LINK_SHRINK = 0.9
LINK_SHRINK_LIMIT = 40


@dataclass(frozen=True, slots=True, kw_only=True)
class Track:
    """One T or B track at one slot, in the direction of positive phase current."""

    kind: Literal["T", "B"]
    slot: int
    phase: int
    sign: int
    special: Literal["shift"] | None
    prims: tuple[XPrim, ...]
    via_out: int
    via_in: int


@dataclass(frozen=True, slots=True, kw_only=True)
class WaveVia:
    """A via of the outer or inner ring; ``kind`` is Xcoil's ``type`` (W, T1, T2 or E)."""

    ring: Literal["outer", "inner"]
    idx: int
    phase: int
    kind: str
    x: float
    y: float
    terminal: bool
    label: str


@dataclass(frozen=True, slots=True, kw_only=True)
class Zone:
    """Commutation belts of one phase: F (positive) and G (negative)."""

    phase: int
    beta_f: int
    beta_g: int


@dataclass(frozen=True, slots=True, kw_only=True)
class Link:
    """Group link of one phase on layer 0: stub, ring arc, stub; ``touch`` lists the inner vias it ends on."""

    phase: int
    net: str
    touch: tuple[int, int]
    prims: tuple[XPrim, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class Terminal:
    """A phase terminal: sign +1 at the F belt, -1 at the G belt; ``via`` indexes ``WaveGeometry.vias``."""

    phase: int
    sign: int
    x: float
    y: float
    via: int


@dataclass(frozen=True, slots=True, kw_only=True)
class WaveGeometry:
    """Xcoil's ``G`` of buildWave."""

    t0: tuple[XPrim, ...]
    b0: tuple[XPrim, ...]
    t_shift: tuple[XPrim, ...] | None
    tracks_t: tuple[Track, ...]
    tracks_b: tuple[Track, ...]
    vias: tuple[WaveVia, ...]
    zones: tuple[Zone, ...]
    links: tuple[Link, ...]
    terms: tuple[Terminal, ...]
    r_link: float
    special: dict[int, Literal["removed", "shift"]]
    link_width_mm: float
    link_room: bool


def _tracks(
    frame: WaveFrame, t0: list[XPrim], b0: list[XPrim], t_shift: list[XPrim] | None, special: Mapping[int, str]
) -> tuple[list[Track], list[Track]]:  # fmt: skip
    """T and B track of every slot; slot 0 of a commutation belt has no T track and the others use ``t_shift``."""
    tracks_t: list[Track] = []
    tracks_b: list[Track] = []
    n_slots, mq = frame.n_slots, frame.mq
    for k in range(n_slots):
        beta = k // frame.q
        phase, sgn, ang = frame.belt_phase(beta), frame.belt_sign(beta), frame.slot_angle(k)
        kind = special.get(k)
        if kind != "removed":
            source = t_shift if kind == "shift" else t0
            assert source is not None
            pr_t = rotate_prims(source, ang)
            tracks_t.append(Track(kind="T", slot=k, phase=phase, sign=sgn, special="shift" if kind else None,
                                  prims=tuple(pr_t if sgn > 0 else reverse_prims(pr_t)),
                                  via_out=(k - 1) % n_slots if kind == "shift" else k, via_in=k))  # fmt: skip
        pr_b = rotate_prims(b0, ang)  # canonical B runs outer via to inner via
        tracks_b.append(Track(kind="B", slot=k, phase=phase, sign=sgn, special=None,
                              prims=tuple(pr_b if sgn < 0 else reverse_prims(pr_b)),
                              via_out=(k - mq) % n_slots, via_in=(k + mq) % n_slots))  # fmt: skip
    return tracks_t, tracks_b


def _via_rings(frame: WaveFrame) -> list[WaveVia]:
    """Outer via k at slot angle + tau/2 (end of T_k), inner via k at slot angle - tau/2; outer is 2k, inner 2k + 1."""
    vias: list[WaveVia] = []
    for k in range(frame.n_slots):
        vo = polar(frame.r_vo, frame.slot_angle(k) + frame.tau / 2)
        vi = polar(frame.r_vi, frame.slot_angle(k) - frame.tau / 2)
        phv = frame.belt_phase(k // frame.q)
        vias.append(WaveVia(ring="outer", idx=k, phase=phv, kind="W", x=vo[0], y=vo[1], terminal=False, label=""))
        vias.append(WaveVia(ring="inner", idx=k, phase=phv, kind="W", x=vi[0], y=vi[1], terminal=False, label=""))
    return vias


@dataclass(frozen=True, slots=True, kw_only=True)
class _LinkRing:
    """Radius and width of the group-link ring, and whether it fits at all."""

    r_link: float
    width_mm: float
    room: bool


def _link_ring(frame: WaveFrame) -> _LinkRing:
    """Fit the m group links on one radius inside the inner via ring; the bus narrows until the links keep clearance."""
    bw = frame.p.bus_width_mm
    end_gap = max(frame.pad, frame.w_in, frame.w if frame.style == "chord" else 0.0) / 2 + frame.s

    def r_link_for(b: float) -> float:
        return min(frame.r_vi, frame.r_track_min or frame.r_vi) - (end_gap + b / 2)

    def fits(b: float) -> bool:
        rl = r_link_for(b)
        return rl > MIN_LINK_RADIUS_MM and 2 * rl * math.sin(frame.tau / (2 * frame.m)) - b >= frame.s - 1e-9

    room = True
    if not fits(bw):
        b_min, b2 = min(bw, frame.pad), bw
        for _ in range(LINK_SHRINK_LIMIT):
            if fits(b2) or not b2 > b_min:
                break
            b2 = max(b_min, b2 * LINK_SHRINK)
        bw, room = (b2, True) if fits(b2) else (b_min, False)
    return _LinkRing(r_link=r_link_for(bw), width_mm=bw, room=room)


def _link(frame: WaveFrame, ring: _LinkRing, from_via: WaveVia, touch: tuple[int, int], phase: int) -> Link:
    """Stub, ring arc, stub from the inner via of the F belt over one pole pitch; stubs are no wider than the pad."""
    a1 = math.atan2(from_via.y, from_via.x)
    a2 = a1 + frame.tau
    wn = min(ring.width_mm, frame.pad)
    s1, e1 = polar(frame.r_vi, a1), polar(ring.r_link, a1)
    s2, e2 = polar(frame.r_vi, a2), polar(ring.r_link, a2)
    prims: tuple[XPrim, ...] = (
        XLine(x1=s1[0], y1=s1[1], x2=e1[0], y2=e1[1], w=wn, kind="stub"),
        XArc(cx=0.0, cy=0.0, r=ring.r_link, a1=a1, a2=a2, w=ring.width_mm, kind="ring"),
        XLine(x1=e2[0], y1=e2[1], x2=s2[0], y2=s2[1], w=wn, kind="stub"),
    )
    return Link(phase=phase, net=f"L{phase}", touch=touch, prims=prims)


def build_wave(frame: WaveFrame) -> WaveGeometry:
    """Xcoil buildWave."""
    q, m, n_slots = frame.q, frame.m, frame.n_slots
    t0 = wave_track(frame, None)
    b0 = reverse_prims(mirror_prims_x(t0))
    t_shift = wave_track(frame, frame.tau / 2 - frame.d_theta) if q > 1 else None
    zones = []
    for ph in range(m):
        beta_f = (2 * ph if m == 3 else ph) + (2 * m if ph == 1 and m > 1 else 0)
        zones.append(Zone(phase=ph, beta_f=beta_f, beta_g=beta_f + m))
    special: dict[int, Literal["removed", "shift"]] = {}
    for z in zones:
        for b, i in itertools.product((z.beta_f, z.beta_g), range(q)):
            special[(b * q + i) % n_slots] = "removed" if i == 0 else "shift"
    tracks_t, tracks_b = _tracks(frame, t0, b0, t_shift, special)
    vias = _via_rings(frame)
    ring = _link_ring(frame)
    links: list[Link] = []
    terms: list[Terminal] = []
    for z in zones:
        s_f, s_g = 2 * ((z.beta_f * q + q - 1) % n_slots), 2 * ((z.beta_g * q + q - 1) % n_slots)
        e_f, e_g = 2 * ((z.beta_f * q) % n_slots) + 1, 2 * ((z.beta_g * q) % n_slots) + 1
        name = PHASE_NAMES[z.phase]
        vias[s_f] = replace(vias[s_f], terminal=True, label=name + "+", kind="T1")
        vias[s_g] = replace(vias[s_g], terminal=True, label=name + MINUS, kind="T2")
        vias[e_f], vias[e_g] = replace(vias[e_f], kind="E"), replace(vias[e_g], kind="E")
        terms.append(Terminal(phase=z.phase, sign=1, x=vias[s_f].x, y=vias[s_f].y, via=s_f))
        terms.append(Terminal(phase=z.phase, sign=-1, x=vias[s_g].x, y=vias[s_g].y, via=s_g))
        links.append(_link(frame, ring, vias[e_f], (e_f, e_g), z.phase))
    return WaveGeometry(t0=tuple(t0), b0=tuple(b0), t_shift=None if t_shift is None else tuple(t_shift),
                        tracks_t=tuple(tracks_t), tracks_b=tuple(tracks_b), vias=tuple(vias), zones=tuple(zones),
                        links=tuple(links), terms=tuple(terms), r_link=ring.r_link, special=special,
                        link_width_mm=ring.width_mm, link_room=ring.room)  # fmt: skip
