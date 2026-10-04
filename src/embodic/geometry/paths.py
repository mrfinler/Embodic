"""Continuous copper chains and the continuity check (UT-GEO-01, REQ-N-21 coincidence tolerance)."""

from collections.abc import Sequence
from dataclasses import dataclass
from itertools import pairwise
from typing import Literal

from embodic.geometry.primitives import Primitive, hypot_mm
from embodic.model.vocabulary import Phase

COINCIDENCE_MM = 1e-6


@dataclass(frozen=True, slots=True, kw_only=True)
class CopperPath:
    """Continuous chain on one copper layer, ordered in current direction."""

    id: int
    layer: str
    net: str
    primitives: tuple[Primitive, ...]
    phase: Phase | None  # None for neutral and interconnect copper
    element: int | None  # coil index (spiral), track or strand index (serpentine, wave)
    polarity: Literal[1, -1, 0]


def joint_gaps_mm(prims: Sequence[Primitive]) -> tuple[float, ...]:
    """Return the distance from the end of primitive i to the start of primitive i + 1, for every joint."""
    gaps: list[float] = []
    for before, after in pairwise(prims):
        (x1_mm, y1_mm), (x2_mm, y2_mm) = before.end_point(), after.start_point()
        gaps.append(hypot_mm(x2_mm - x1_mm, y2_mm - y1_mm))
    return tuple(gaps)


def is_continuous(prims: Sequence[Primitive], tolerance_mm: float = COINCIDENCE_MM) -> bool:
    """Return whether every joint closes within ``tolerance_mm`` (Xcoil GEO-01: 1e-6 mm)."""
    return all(gap_mm <= tolerance_mm for gap_mm in joint_gaps_mm(prims))
