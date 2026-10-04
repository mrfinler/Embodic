"""Uniform-grid broad phase over chords (Xcoil makeGrid and gridQuery, engine.js l.580-596).

Each chord is binned by its midpoint only, so a query must widen its radius by the longest chord it can miss; Xcoil
adds one cell ring for that (``ceil(radius / cell) + 1``).
"""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from embodic.geometry.distance import Chord


@dataclass(frozen=True, slots=True, kw_only=True)
class ChordGrid:
    """Chord indices binned by the cell of each chord's midpoint."""

    cell_mm: float
    cells: Mapping[tuple[int, int], tuple[int, ...]]  # in first-use order, as Xcoil's Map


def make_grid(chords: Sequence[Chord], cell_mm: float) -> ChordGrid:
    """Bin every chord by ``floor(midpoint / cell)``."""
    cells: dict[tuple[int, int], list[int]] = {}
    for index, g in enumerate(chords):
        key = (math.floor((g.x1_mm + g.x2_mm) / 2 / cell_mm), math.floor((g.y1_mm + g.y2_mm) / 2 / cell_mm))
        cells.setdefault(key, []).append(index)
    return ChordGrid(cell_mm=cell_mm, cells={key: tuple(v) for key, v in cells.items()})


def grid_query(grid: ChordGrid, x_mm: float, y_mm: float, radius_mm: float) -> tuple[int, ...]:
    """Chord indices of every cell within ``ceil(radius / cell) + 1`` cells, in Xcoil's visiting order."""
    rings = math.ceil(radius_mm / grid.cell_mm) + 1
    cx, cy = math.floor(x_mm / grid.cell_mm), math.floor(y_mm / grid.cell_mm)
    visited: list[int] = []
    for ix in range(cx - rings, cx + rings + 1):
        for iy in range(cy - rings, cy + rings + 1):
            visited.extend(grid.cells.get((ix, iy), ()))
    return tuple(visited)
