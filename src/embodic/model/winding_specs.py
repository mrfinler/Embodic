"""Winding inputs, one spec per topology (interfaces.md section 2.2, ADR-0012).

Serpentine and wave specs carry exactly the inputs Xcoil's builders read (engine.js l.163-753 and l.1449-2230).
"""

import math
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal, TypeAlias

from embodic.model.layers import LayerConfig
from embodic.model.vocabulary import Phase


class SideStyle(StrEnum):
    """Coil sides along radii or parallel to the coil axis."""

    RADIAL = "radial"
    PARALLEL = "parallel"


class EndStyle(StrEnum):
    """Shape of the spiral coil's end turns."""

    ARC = "arc"
    STRAIGHT = "straight"
    STADIUM = "stadium"


class InnerTurnMode(StrEnum):
    """Whether the innermost spiral turn stays fixed or moves with the turn count."""

    FIXED = "fixed"
    MOVING = "moving"


class Sense(StrEnum):
    """Rotation sense."""

    CW = "cw"
    CCW = "ccw"


class LeadStyle(StrEnum):
    """Route of the spiral lead from the centre via to the terminal."""

    RADIAL_THEN_ARC = "radial_then_arc"
    STRAIGHT = "straight"


class PhaseSequence(StrEnum):
    """Phase order around the stator."""

    ABC = "abc"
    ACB = "acb"


class PairConnection(StrEnum):
    """How layer pairs of one phase join."""

    SERIES = "series"
    PARALLEL = "parallel"


class CornerStyle(StrEnum):
    """Corner treatment of serpentine and wave traces."""

    ROUND = "round"
    SHARP = "sharp"


class TerminalSide(StrEnum):
    """Rim that carries the serpentine terminals."""

    OUTER = "outer"
    INNER = "inner"


class LayerOrder(StrEnum):
    """Order of serpentine phase layers in the stack."""

    GROUPED = "grouped"
    INTERLEAVED = "interleaved"


class WaveStyle(StrEnum):
    """Xcoil wave track shapes."""

    INVOLUTE = "involute"
    JOG = "jog"
    CHORD = "chord"
    OVERLAP = "overlap"


@dataclass(frozen=True, slots=True, kw_only=True)
class CoilAssignmentInput:
    """A manual phase and polarity for one spiral coil."""

    coil_index: int
    phase: Phase
    polarity: Literal[1, -1]


@dataclass(frozen=True, slots=True, kw_only=True)
class SpiralCoilSpec:
    """Geometry of one spiral coil; radii are copper edges (spiral_generator_spec.md, Inputs)."""

    coil_count: int
    r_inner_mm: float
    r_outer_mm: float
    trace_width_mm: float
    clearance_mm: float
    coil_gap_mm: float
    turns: int | None = None  # None = maximum feasible
    side_style: SideStyle = SideStyle.PARALLEL
    end_style: EndStyle = EndStyle.ARC
    inner_turn_mode: InnerTurnMode = InnerTurnMode.MOVING
    corner_radius_mm: float = 0.0
    end_width_outer_mm: float | None = None
    end_width_inner_mm: float | None = None
    first_coil_angle_rad: float = math.pi / 2
    x_inward_sense: Sense = Sense.CW
    lead_style: LeadStyle = LeadStyle.RADIAL_THEN_ARC
    terminal_offset_mm: float | None = None
    min_side_length_mm: float | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class SpiralWindingSpec:
    """Spiral coils on layer pairs; `assignment` None means the star of slots decides."""

    kind: Literal["spiral"] = "spiral"
    coil: SpiralCoilSpec
    layers: LayerConfig
    assignment: tuple[CoilAssignmentInput, ...] | None = None
    phase_sequence: PhaseSequence = PhaseSequence.ABC
    parallel_paths: int = 1


@dataclass(frozen=True, slots=True, kw_only=True)
class SerpentineWindingSpec:
    """Xcoil 'serpentine': one phase per layer group.

    Xcoil's stackMode 'perPhase' (one board per phase) is not ported: a Layout is one board (requirements.md Q-3).
    """

    kind: Literal["serpentine"] = "serpentine"
    r_inner_mm: float  # Xcoil rIn
    r_outer_mm: float  # Xcoil rOut
    turns: int  # Xcoil turns (traces per pole)
    strands: int = 1  # Xcoil strands
    trace_width_mm: float  # Xcoil traceWidth
    clearance_mm: float  # Xcoil clearance
    end_width_outer_mm: float | None = None  # Xcoil endWidthOuter (0 there = None here)
    end_width_inner_mm: float | None = None  # Xcoil endWidthInner
    side_style: SideStyle = SideStyle.PARALLEL  # Xcoil style
    corner_style: CornerStyle = CornerStyle.ROUND  # Xcoil cornerStyle
    fillet_radius_mm: float = 0.4  # Xcoil filletRadius
    fillet_max: bool = False  # Xcoil filletMax
    terminal_side: TerminalSide = TerminalSide.OUTER  # Xcoil terminalSide
    start_angle_rad: float = 0.0  # Xcoil startAngleDeg
    layers_per_phase: int  # Xcoil layersPerPhase: 1 or even
    pair_connection: PairConnection = PairConnection.SERIES  # Xcoil pairConnection
    layer_order: LayerOrder = LayerOrder.GROUPED  # Xcoil layerOrder


@dataclass(frozen=True, slots=True, kw_only=True)
class WaveWindingSpec:
    """Xcoil 'wave': all phases on every layer, via-stitched T/B track pairs."""

    kind: Literal["wave"] = "wave"
    r_inner_mm: float
    r_outer_mm: float
    turns: int  # Xcoil turns (tracks per phase and pole pair)
    trace_width_mm: float
    clearance_mm: float
    end_width_outer_mm: float | None = None
    end_width_inner_mm: float | None = None
    corner_style: CornerStyle = CornerStyle.ROUND
    fillet_radius_mm: float = 0.4
    wave_style: WaveStyle = WaveStyle.INVOLUTE  # Xcoil waveStyle
    bus_width_mm: float  # Xcoil busWidth


WindingSpec: TypeAlias = SpiralWindingSpec | SerpentineWindingSpec | WaveWindingSpec
