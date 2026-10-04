"""Per-layer NumPy view of a Layout for DRC and physics (interfaces.md section 5, LayoutArrays)."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from embodic.geometry.paths import CopperPath
from embodic.geometry.primitives import Line
from embodic.units import FloatArray

if TYPE_CHECKING:
    from embodic.geometry.layout import Via


@dataclass(frozen=True, slots=True, kw_only=True)
class LayoutArrays:
    """Per-layer NumPy view for DRC and physics. Rows map back through path_index and prim_index.

    ``path_index[layer]`` and ``prim_index[layer]`` hold the line rows first, then the arc rows: row ``i`` of
    ``lines[layer]`` is entry ``i``, row ``j`` of ``arcs[layer]`` is entry ``len(lines[layer]) + j``. The path index
    is ``CopperPath.id``; the primitive index is the position in ``CopperPath.primitives``.
    """

    lines: Mapping[str, FloatArray]  # (N, 5): x1, y1, x2, y2, width
    arcs: Mapping[str, FloatArray]  # (M, 6): cx, cy, r, start, sweep, width
    path_index: Mapping[str, NDArray[np.int64]]
    prim_index: Mapping[str, NDArray[np.int64]]
    vias: FloatArray  # (K, 4): x, y, pad, drill


def layout_arrays(copper_layers: Sequence[str], paths: Sequence[CopperPath], vias: Sequence["Via"]) -> LayoutArrays:
    """Build the arrays layer by layer, in path order and primitive order."""
    lines: dict[str, FloatArray] = {}
    arcs: dict[str, FloatArray] = {}
    path_index: dict[str, NDArray[np.int64]] = {}
    prim_index: dict[str, NDArray[np.int64]] = {}
    for layer in copper_layers:
        line_rows: list[tuple[float, ...]] = []
        arc_rows: list[tuple[float, ...]] = []
        line_refs: list[tuple[int, int]] = []
        arc_refs: list[tuple[int, int]] = []
        for path in paths:
            if path.layer != layer:
                continue
            for k, p in enumerate(path.primitives):
                if isinstance(p, Line):
                    line_rows.append((p.x1_mm, p.y1_mm, p.x2_mm, p.y2_mm, p.width_mm))
                    line_refs.append((path.id, k))
                else:
                    arc_rows.append((p.cx_mm, p.cy_mm, p.r_mm, p.start_rad, p.sweep_rad, p.width_mm))
                    arc_refs.append((path.id, k))
        lines[layer] = np.array(line_rows, dtype=np.float64).reshape(-1, 5)
        arcs[layer] = np.array(arc_rows, dtype=np.float64).reshape(-1, 6)
        refs = np.array(line_refs + arc_refs, dtype=np.int64).reshape(-1, 2)
        path_index[layer], prim_index[layer] = refs[:, 0], refs[:, 1]
    via_rows = [(v.x_mm, v.y_mm, v.pad_mm, v.drill_mm) for v in vias]
    return LayoutArrays(
        lines=lines,
        arcs=arcs,
        path_index=path_index,
        prim_index=prim_index,
        vias=np.array(via_rows, dtype=np.float64).reshape(-1, 4),
    )
