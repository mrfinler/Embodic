"""Inputs of the serpentine builders and the quantities Xcoil ``derive`` computes from them (engine.js l.163-189).

``Params`` holds exactly the Xcoil parameters (``p``) that the canonical build and the layout read, in embodic units.
``Frame`` is Xcoil's ``D``. Every formula keeps Xcoil's operation order so the port reproduces its floating point.
"""

import math
from dataclasses import dataclass
from enum import StrEnum

from embodic.model.winding_specs import CornerStyle, LayerOrder, PairConnection, SideStyle, StackMode, TerminalSide


class CornerType(StrEnum):
    """Xcoil ``'int'`` (fillet internally tangent to the end arc) or ``'ext'`` (externally tangent)."""

    INT = "int"
    EXT = "ext"


@dataclass(frozen=True, slots=True, kw_only=True)
class Params:
    """Xcoil ``p`` for the serpentine builders; a width of 0 means "same as the trace width" as in Xcoil."""

    poles: int
    phases: int
    r_in: float
    r_out: float
    turns: int
    strands: int
    trace_width_mm: float
    clearance_mm: float
    end_width_outer_mm: float
    end_width_inner_mm: float
    style: SideStyle
    corner_style: CornerStyle
    fillet_radius_mm: float
    fillet_max: bool
    terminal_side: TerminalSide
    start_angle_rad: float
    layers_per_phase: int
    pair_connection: PairConnection
    layer_order: LayerOrder
    stack_mode: StackMode
    via_pad: float


@dataclass(frozen=True, slots=True, kw_only=True)
class Frame:
    """Xcoil ``D``: the derived geometry of one serpentine winding."""

    p: Params
    pp: int
    tau: float
    n: int
    j: int
    nt: int
    w: float
    s: float
    pitch_mm: float
    w_out: float
    w_in: float
    bundle: float
    theta0: float
    theta_g: float
    outer: bool
    sg: int
    type_near: CornerType
    type_far: CornerType
    w_near: float
    w_far: float
    p_near: float
    p_far: float
    w_min: float
    w_max: float
    n_pairs: int
    has_y: bool
    series: bool
    phase_shift: float
    bus_step: int
    d_alpha: float
    r_ref: float

    def w_fillet(self, w_end: float) -> float:
        """Xcoil ``wFillet``: a fillet is never wider than the trace."""
        return min(self.w, w_end)


def derive(p: Params) -> Frame:
    """Xcoil ``derive`` (engine.js l.163)."""
    pp = p.poles // 2
    tau = math.pi / pp
    n = p.turns * p.strands
    w = p.trace_width_mm
    s = p.clearance_mm
    pitch_mm = w + s
    w_out = p.end_width_outer_mm if p.end_width_outer_mm > 0 else w
    w_in = p.end_width_inner_mm if p.end_width_inner_mm > 0 else w
    outer = p.terminal_side is TerminalSide.OUTER
    w_near, w_far = (w_out, w_in) if outer else (w_in, w_out)
    p_near, p_far = w_near + s, w_far + s
    n_pairs = 1 if p.layers_per_phase == 1 else p.layers_per_phase // 2
    series = p.pair_connection is PairConnection.SERIES
    bus_step = (
        math.ceil((p.via_pad + s) / p_near)
        if p.stack_mode is StackMode.SINGLE and p.phases > 1 and series and n_pairs > 1
        else 0
    )
    r_ref = p.r_in - (n - 1) * p_far if outer else p.r_in - (n + (p.phases - 1) * bus_step) * p_near
    radial = p.style is SideStyle.RADIAL
    return Frame(
        p=p,
        pp=pp,
        tau=tau,
        n=n,
        j=p.strands,
        nt=p.turns,
        w=w,
        s=s,
        pitch_mm=pitch_mm,
        w_out=w_out,
        w_in=w_in,
        bundle=(n - 1) * pitch_mm,
        theta0=p.start_angle_rad,
        theta_g=p.start_angle_rad - tau / 2,
        outer=outer,
        sg=1 if outer else -1,
        type_near=CornerType.INT if outer else CornerType.EXT,
        type_far=CornerType.EXT if outer else CornerType.INT,
        w_near=w_near,
        w_far=w_far,
        p_near=p_near,
        p_far=p_far,
        w_min=min(w, w_out, w_in),
        w_max=max(w, w_out, w_in),
        n_pairs=n_pairs,
        has_y=p.layers_per_phase > 1,
        series=series,
        phase_shift=tau / 2 if p.phases == 2 else 2 * tau / p.phases,
        bus_step=bus_step,
        d_alpha=math.asin(pitch_mm / r_ref) if radial and r_ref > pitch_mm else 0.0,
        r_ref=r_ref,
    )


def near_r(d: Frame, level: float) -> float:
    """Xcoil ``nearR``: radius of the near-end arc at a nesting level."""
    return d.p.r_out + level * d.p_near if d.outer else d.p.r_in - level * d.p_near


def far_r(d: Frame, level: float) -> float:
    """Xcoil ``farR``: radius of the far-end arc at a nesting level."""
    return d.p.r_in - level * d.p_far if d.outer else d.p.r_out + level * d.p_far
