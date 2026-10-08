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
    """Clearance holes of one fastener pattern (REQ-F-24, D-031a).

    The user enters the hole diameter. `size` and `fit` label the holes and pick no value; fastener-table values ship
    only as labelled example values with a cited source.
    """

    size: str
    fit: ScrewFit
    count: int
    pitch_radius_mm: float
    hole_diameter_mm: float
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
