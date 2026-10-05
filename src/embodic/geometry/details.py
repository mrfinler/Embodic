"""Generator-specific records carried by ``Layout.detail`` (interfaces.md section 5)."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal, TypeAlias

from embodic.model.vocabulary import Phase
from embodic.winding import SpiralWindingPlan


class TurnLimitReason(StrEnum):
    """What stopped the spiral turn count."""

    RADIAL = "radial"
    LATERAL = "lateral"
    EYE = "eye"
    USER = "user"


@dataclass(frozen=True, slots=True, kw_only=True)
class TurnLimit:
    """Turn bounds of one spiral coil (spiral_generator_spec.md G3 and G5)."""

    radial_bound: float  # D08 eq. 3.24, information only
    loops_trapezoidal: int
    loops_triangular: int
    eye_limit: int | None
    limiting_reason: TurnLimitReason


@dataclass(frozen=True, slots=True, kw_only=True)
class SpiralDetail:
    """Spiral generator record: plan, turns built and per-layer track length of one coil."""

    kind: Literal["spiral"] = "spiral"
    plan: SpiralWindingPlan
    turns_achieved: int
    turn_limit: TurnLimit
    track_length_per_coil_layer_mm: Mapping[str, float]  # "X", "Y"


@dataclass(frozen=True, slots=True, kw_only=True)
class SerpentineDetail:
    """Serpentine generator record."""

    kind: Literal["serpentine"] = "serpentine"
    max_turns_that_fit: int  # Xcoil F-10
    layer_phase: Mapping[str, Phase]  # one phase per copper layer
    canonical_frame_rad: float


@dataclass(frozen=True, slots=True, kw_only=True)
class WaveDetail:
    """Wave generator record."""

    kind: Literal["wave"] = "wave"
    tracks_per_layer: int
    stitch_vias_per_stack: int


TopologyDetail: TypeAlias = SpiralDetail | SerpentineDetail | WaveDetail
