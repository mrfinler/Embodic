"""Board outline, bore and fastener inputs (interfaces.md section 2.1)."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal


class ScrewFit(StrEnum):
    """Clearance-hole fit class."""

    CLOSE = "close"
    NORMAL = "normal"
    LOOSE = "loose"


@dataclass(frozen=True, slots=True, kw_only=True)
class ScrewPattern:
    """Clearance holes from a fastener table (REQ-F-24). Table values need a cited source (Agent 3 F-20)."""

    size: str
    fit: ScrewFit
    count: int
    pitch_radius_mm: float
    angle_offset_rad: float = 0.0


@dataclass(frozen=True, slots=True, kw_only=True)
class CircleOutline:
    """Circular outline."""

    shape: Literal["circle"] = "circle"
    radius_mm: float


@dataclass(frozen=True, slots=True, kw_only=True)
class PolygonOutline:
    """Regular polygon outline measured across flats."""

    shape: Literal["polygon"] = "polygon"
    sides: int
    across_flats_mm: float
    corner_radius_mm: float = 0.0
    rotation_rad: float = 0.0


@dataclass(frozen=True, slots=True, kw_only=True)
class OutlineSpec:
    """Board edge, optional bore and screw patterns."""

    board: CircleOutline | PolygonOutline
    bore: CircleOutline | PolygonOutline | None
    screws: tuple[ScrewPattern, ...] = ()
