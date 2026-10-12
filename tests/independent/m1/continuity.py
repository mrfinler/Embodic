"""Independent continuity check for M1 (IT-21): consecutive primitives of an ordered path must meet end to start."""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from itertools import pairwise

from records import Point, Prim, end_point, start_point

CONTINUITY_TOL_MM = 1e-6  # REQ-N-21 (revision 2026-10-05, U-D2): COINCIDENCE_MM


@dataclass(frozen=True, slots=True)
class Gap:
    """The end of ``path[index]`` does not meet the start of ``path[index + 1]``."""

    index: int
    end: Point
    next_start: Point
    distance_mm: float


def first_gap(path: Sequence[Prim], tol_mm: float = CONTINUITY_TOL_MM) -> Gap | None:
    """Return the first joint whose end-to-start distance exceeds ``tol_mm``, or None for a continuous path."""
    for index, (here, there) in enumerate(pairwise(path)):
        end, nxt = end_point(here), start_point(there)
        distance = math.dist(end, nxt)
        if not distance <= tol_mm:
            return Gap(index, end, nxt, distance)
    return None


def chains(path: Sequence[Prim], tol_mm: float = CONTINUITY_TOL_MM) -> list[range]:
    """Split an ordered path at every joint wider than ``tol_mm``: the index range of each continuous run, in order."""
    runs, start = [], 0
    while (gap := first_gap(path[start:], tol_mm)) is not None:
        runs.append(range(start, start + gap.index + 1))
        start += gap.index + 1
    runs.append(range(start, len(path)))
    return runs
