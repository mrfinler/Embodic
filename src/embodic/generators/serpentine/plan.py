"""Layer order, layer copper, vias, series links and the copper envelope (Xcoil buildLayout, engine.js l.667-753).

``plan_stack`` returns the whole stack as plain records; ``generate`` turns them into one Layout per board. A layer
holds the canonical pattern of its phase, mirrored for a Y layer, rotated by the phase and pair shift, and reversed for
an X layer so that current flows T1 -> X -> V -> Y -> T2 (Xcoil l.704).
"""

import math
from dataclasses import dataclass
from typing import Literal

from embodic.generators.serpentine.canonical import Canon, CanonFailure, build_canonical
from embodic.generators.serpentine.frame import Frame, far_r
from embodic.geometry.primitives import Arc, Primitive, PrimitiveRole
from embodic.geometry.transforms import Transform, reverse_path, transform, transform_angle_rad, transform_point
from embodic.model.vocabulary import Phase
from embodic.model.winding_specs import LayerOrder, StackMode

Role = Literal["X", "Y"]
ViaKind = Literal["V", "T1", "T2"]
PHASES = (Phase.A, Phase.B, Phase.C)
TWO_PI = 2 * math.pi


@dataclass(frozen=True, slots=True, kw_only=True)
class Slot:
    """One copper layer of the stack: the phase and layer pair it carries and whether it is X or Y."""

    phase: int
    pair: int
    role: Role


@dataclass(frozen=True, slots=True, kw_only=True)
class IcRole:
    """What an interconnect path is for; the path id exists only once the board is assembled."""

    kind: Literal["line", "link", "ring", "neutral"]
    phase: int = -1
    tap_vias: tuple[int, ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class PathSpec:
    """A path before it has an id. ``kind`` is Xcoil's object kind; ``ic`` is set for interconnect copper."""

    kind: Literal["strand", "vbus", "tbus", "link", "ic"]
    net: str
    prims: tuple[Primitive, ...]
    phase: int = -1
    element: int | None = None
    ic: IcRole | None = None


@dataclass(slots=True, kw_only=True)
class LayerPlan:
    """A copper layer in stack order with the paths on it."""

    index: int
    board: int
    index_in_board: int
    slot: Slot
    tf: Transform
    paths: list[PathSpec]


@dataclass(frozen=True, slots=True, kw_only=True)
class ViaPlan:
    """A via of the winding. ``terminal`` vias carry a phase terminal."""

    phase: int
    pair: int
    kind: ViaKind
    x: float
    y: float
    terminal: bool


@dataclass(slots=True, kw_only=True)
class StackPlan:
    """Xcoil ``buildLayout`` result without errors."""

    layers: list[LayerPlan]
    vias: list[ViaPlan]
    canon: list[Canon]
    n_boards: int
    per_board: int
    r_min_cu: float
    r_max_cu: float


def phase_net(phase: int) -> str:
    """Net of phase copper and its vias (D-022)."""
    return f"PHASE_{PHASES[phase].value}"


def layer_order(d: Frame) -> list[Slot]:
    """Order of copper layers in the stack (Xcoil l.680-685)."""
    p = d.p
    roles: tuple[Role, ...] = ("X", "Y") if d.has_y else ("X",)
    if p.stack_mode is StackMode.ONE_BOARD_PER_PHASE or p.layer_order is LayerOrder.GROUPED:
        return [Slot(phase=k, pair=q, role=r) for k in range(p.phases) for q in range(d.n_pairs) for r in roles]
    return [Slot(phase=k, pair=q, role=r) for q in range(d.n_pairs) for k in range(p.phases) for r in roles]


def _canonicals(d: Frame) -> list[Canon] | CanonFailure:
    out: list[Canon] = []
    for k in range(d.p.phases):
        built = build_canonical(d, k * d.bus_step) if k == 0 or d.bus_step > 0 else out[0]
        if isinstance(built, CanonFailure):
            return built
        out.append(built)
    return out


def _slot_transform(d: Frame, slot: Slot) -> Transform:
    rot = slot.phase * d.phase_shift + (slot.pair * 2 * d.tau if d.series else 0)
    return Transform(rotation_rad=rot, mirror_axis_rad=d.theta_g if slot.role == "Y" else None)


def _layer_paths(d: Frame, slot: Slot, tf: Transform, canon: Canon) -> list[PathSpec]:
    paths = []
    for obj in canon.objs:
        prims = transform(obj.prims, tf)
        if slot.role == "X":  # canonical build order is V -> T, current flows T1 -> X -> V -> Y -> T2
            prims = reverse_path(prims)
        paths.append(PathSpec(kind=obj.kind, net=phase_net(slot.phase), prims=prims, phase=slot.phase,
                              element=obj.strand))  # fmt: skip
    return paths


def _via(k: int, q: int, kind: ViaKind, tf: Transform, xy: tuple[float, float], terminal: bool) -> ViaPlan:
    x, y = transform_point(tf, *xy)
    return ViaPlan(phase=k, pair=q, kind=kind, x=x, y=y, terminal=terminal)


def _winding_vias(d: Frame, canon: list[Canon]) -> list[ViaPlan]:
    vias: list[ViaPlan] = []
    for k in range(d.p.phases):
        site_v, site_t = canon[k].pad_v, canon[k].pad_t
        for q in range(d.n_pairs):
            if not d.series and q > 0:
                break  # parallel pairs share one set of vias
            rot = k * d.phase_shift + (q * 2 * d.tau if d.series else 0)
            tf_x = Transform(rotation_rad=rot)
            is_first, is_last = q == 0 or not d.series, q == d.n_pairs - 1 or not d.series
            vias.append(_via(k, q, "V", tf_x, site_v.xy, terminal=not d.has_y))
            vias.append(_via(k, q, "T1", tf_x, site_t.xy, terminal=is_first))
            if d.has_y and is_last:
                tf_y = Transform(rotation_rad=rot, mirror_axis_rad=d.theta_g)
                vias.append(_via(k, q, "T2", tf_y, site_t.xy, terminal=True))
    return vias


def _series_link(d: Frame, canon: Canon, k: int, q: int) -> Arc:
    """Link on layer Y_q from the +theta end of the T2 bus to the pad of T1_(q+1) (Xcoil l.730)."""
    rot = k * d.phase_shift + q * 2 * d.tau
    tf_y = Transform(rotation_rad=rot, mirror_axis_rad=d.theta_g)
    a1 = transform_angle_rad(tf_y, canon.pad_t.t_a1)  # mirrored tA1 becomes the +theta end
    a2 = transform_angle_rad(Transform(rotation_rad=rot + 2 * d.tau), canon.pad_t.ang)
    sweep = (a2 - a1) % TWO_PI
    if sweep < 0:
        sweep += TWO_PI
    a2 = a1 + sweep
    return Arc(cx_mm=0.0, cy_mm=0.0, r_mm=canon.r_bus, start_rad=a1, sweep_rad=a2 - a1, width_mm=d.w_near,
               role=PrimitiveRole.LINK)  # fmt: skip


def _envelope(d: Frame, canon: list[Canon]) -> tuple[float, float]:
    r_max, r_min = 0.0, math.inf
    for cn in canon:
        if d.outer:
            deepest = max(cn.pad_t.r + d.p.via_pad / 2, cn.r_bus + d.w_near / 2)
        else:
            deepest = min(cn.pad_t.r - d.p.via_pad / 2, cn.r_bus - d.w_near / 2)
        far_deep = far_r(d, d.n - 1) - d.sg * d.w_far / 2
        r_max = max(r_max, deepest if d.outer else far_deep)
        r_min = min(r_min, far_deep if d.outer else deepest)
    return r_min, r_max


def plan_stack(d: Frame) -> StackPlan | CanonFailure:
    """Order the layers, build their copper, place the vias and the series links (Xcoil ``buildLayout``)."""
    canon = _canonicals(d)
    if isinstance(canon, CanonFailure):
        return canon
    p = d.p
    per_phase = p.stack_mode is StackMode.ONE_BOARD_PER_PHASE
    order = layer_order(d)
    per_board = p.layers_per_phase if per_phase else len(order)
    layers: list[LayerPlan] = []
    for idx, slot in enumerate(order):
        tf = _slot_transform(d, slot)
        layers.append(
            LayerPlan(
                index=idx,
                board=slot.phase if per_phase else 0,
                index_in_board=idx - slot.phase * per_board if per_phase else idx,
                slot=slot,
                tf=tf,
                paths=_layer_paths(d, slot, tf, canon[slot.phase]),
            )
        )
    if d.series and d.has_y:
        for k in range(p.phases):
            for q in range(d.n_pairs - 1):
                target = next(lp for lp in layers if lp.slot.phase == k and lp.slot.pair == q and lp.slot.role == "Y")
                target.paths.append(PathSpec(kind="link", net=phase_net(k), phase=k,
                                             prims=(_series_link(d, canon[k], k, q),)))  # fmt: skip
    r_min, r_max = _envelope(d, canon)
    return StackPlan(
        layers=layers,
        vias=_winding_vias(d, canon),
        canon=canon,
        n_boards=p.phases if per_phase else 1,
        per_board=per_board,
        r_min_cu=r_min,
        r_max_cu=r_max,
    )
