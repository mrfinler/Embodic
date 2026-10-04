"""Rotor and magnet inputs (interfaces.md section 2.1)."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal, TypeAlias


class RotorType(StrEnum):
    """Rotor arrangement: magnets on both sides, one side with a yoke, or one side open."""

    DOUBLE = "double"
    SINGLE_YOKE = "single_yoke"
    SINGLE_OPEN = "single_open"


@dataclass(frozen=True, slots=True, kw_only=True)
class ArcMagnet:
    """Arc-segment magnet described by its pole-arc ratio and radial extent."""

    kind: Literal["arc"] = "arc"
    pole_arc_ratio: float
    r_inner_mm: float
    r_outer_mm: float
    thickness_mm: float


@dataclass(frozen=True, slots=True, kw_only=True)
class BlockMagnet:
    """Rectangular block magnet centred at a radius."""

    kind: Literal["block"] = "block"
    width_mm: float
    length_mm: float
    r_center_mm: float
    thickness_mm: float


MagnetGeometry: TypeAlias = ArcMagnet | BlockMagnet


@dataclass(frozen=True, slots=True, kw_only=True)
class RotorSpec:
    """Pole count, magnet geometry and the magnetic property inputs."""

    poles: int  # 2p, even
    rotor_type: RotorType
    magnet: MagnetGeometry
    remanence_t: float
    recoil_permeability: float
    air_gap_mm: float  # per side, magnet face to board surface
    back_iron_thickness_mm: float
    magnet_offset_rad: float = 0.0
