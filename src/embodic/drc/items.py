"""A Layout flattened into one table of DRC items, plus the pairs that connectivity exempts (interfaces.md section 7).

An item is a centreline (a line or an arc row) with a half width: a trace primitive, a via or round land (a point),
a board edge piece (half width 0) or a screw hole (a point with the hole radius). Pads keep their own kernel
(``pad_closest``); their row is the pad centre with the circumscribed radius, which only the broad phase reads.
"""

import math
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from enum import IntEnum

import numpy as np
from numpy.typing import NDArray

from embodic.drc.kernels import D, pad_bounding_radius_mm, pad_closest
from embodic.geometry.layout import Layout, Pad, ViaRole
from embodic.geometry.paths import COINCIDENCE_MM, CopperPath
from embodic.geometry.primitives import Arc, Line, Primitive, PrimitiveRole
from embodic.units import FloatArray

IntArray = NDArray[np.int64]
EVERY_LAYER = -1
NO_INDEX = -1
_CORNER_ROLES = frozenset({PrimitiveRole.FILLET, PrimitiveRole.TAPER})


class ItemClass(IntEnum):
    """What an item is; the pair of classes picks the check kind."""

    TRACE = 0
    VIA = 1
    PAD = 2
    EDGE = 3
    HOLE = 4


@dataclass(frozen=True, slots=True, kw_only=True)
class Items:
    """Struct of arrays, one row per item; ``path`` and ``slot`` are NO_INDEX for anything but traces."""

    rows: FloatArray  # (n, 6): line (x1, y1, x2, y2, 0, 0) or arc (cx, cy, r, start, sweep, 0)
    is_arc: NDArray[np.bool_]
    half_width_mm: FloatArray
    item_class: IntArray
    layer: IntArray  # index into Layout.copper_layers, EVERY_LAYER for through vias, through pads, edges, holes
    path: IntArray  # CopperPath.id
    slot: IntArray  # 2 * main index; a fillet or taper takes 2 * main index + 1 of the main before it
    pad: IntArray  # index into Layout.pads
    centre_mm: FloatArray  # (n, 2) land centre for pad-to-pad and pad-to-via checks
    land_radius_mm: FloatArray  # circumscribed land radius for those checks
    labels: tuple[str, ...]

    def __len__(self) -> int:
        """Return the item count."""
        return len(self.labels)


@dataclass
class _Builder:
    rows: list[list[float]]
    is_arc: list[bool]
    half_width_mm: list[float]
    item_class: list[int]
    layer: list[int]
    path: list[int]
    slot: list[int]
    pad: list[int]
    centre_mm: list[tuple[float, float]]
    land_radius_mm: list[float]
    labels: list[str]

    def add(
        self,
        label: str,
        item_class: ItemClass,
        prim: Primitive,
        *,
        half_width_mm: float,
        layer: int,
        path: int = NO_INDEX,
        slot: int = NO_INDEX,
        pad: int = NO_INDEX,
    ) -> int:
        if isinstance(prim, Line):
            self.rows.append([prim.x1_mm, prim.y1_mm, prim.x2_mm, prim.y2_mm, 0.0, 0.0])
            centre = ((prim.x1_mm + prim.x2_mm) / 2, (prim.y1_mm + prim.y2_mm) / 2)
        else:
            self.rows.append([prim.cx_mm, prim.cy_mm, prim.r_mm, prim.start_rad, prim.sweep_rad, 0.0])
            centre = (prim.cx_mm, prim.cy_mm)
        self.is_arc.append(isinstance(prim, Arc))
        self.half_width_mm.append(half_width_mm)
        self.item_class.append(item_class)
        self.layer.append(layer)
        self.path.append(path)
        self.slot.append(slot)
        self.pad.append(pad)
        self.centre_mm.append(centre)
        self.land_radius_mm.append(half_width_mm)
        self.labels.append(label)
        return len(self.labels) - 1


def _point(x_mm: float, y_mm: float) -> Line:
    return Line(x1_mm=x_mm, y1_mm=y_mm, x2_mm=x_mm, y2_mm=y_mm, width_mm=0.0, role=PrimitiveRole.OUTLINE)


def main_indices(prims: Sequence[Primitive]) -> list[int]:
    """Xcoil ``mi`` (engine.js drcObjects l.1697): fillets and tapers belong to the corner they shape."""
    out, index = [], -1
    for p in prims:
        if p.role not in _CORNER_ROLES:
            index += 1
        out.append(max(0, index))
    return out


def build_items(layout: Layout) -> tuple[Items, dict[int, int]]:
    """Flatten a Layout; also return the first item index of each path (its items follow in primitive order)."""
    b = _Builder([], [], [], [], [], [], [], [], [], [], [])
    layer_index = {name: i for i, name in enumerate(layout.copper_layers)}
    first_item: dict[int, int] = {}
    for path in layout.paths:
        first_item[path.id] = len(b.labels)
        for k, (prim, main) in enumerate(zip(path.primitives, main_indices(path.primitives), strict=True)):
            b.add(
                f"path:{path.id}/prim:{k}",
                ItemClass.TRACE,
                prim,
                half_width_mm=prim.width_mm / 2,
                layer=layer_index[path.layer],
                path=path.id,
                slot=2 * main + (prim.role in _CORNER_ROLES),
            )
    for via in layout.vias:
        b.add(
            f"via:{via.id}", ItemClass.VIA, _point(via.x_mm, via.y_mm), half_width_mm=via.pad_mm / 2, layer=EVERY_LAYER
        )
    for i, pad in enumerate(layout.pads):
        layer = EVERY_LAYER if pad.layer is None else layer_index[pad.layer]
        radius_mm = pad_bounding_radius_mm(pad)
        b.add(f"pad:{pad.id}", ItemClass.PAD, _point(pad.x_mm, pad.y_mm), half_width_mm=radius_mm, layer=layer, pad=i)
    loops = [("outer", layout.outline.outer)] + [(f"cutout{c}", loop) for c, loop in enumerate(layout.outline.cutouts)]
    for name, loop in loops:
        for k, prim in enumerate(loop):
            b.add(f"edge:{name}/prim:{k}", ItemClass.EDGE, prim, half_width_mm=0.0, layer=EVERY_LAYER)
    for i, hole in enumerate(layout.outline.holes):
        point = _point(hole.x_mm, hole.y_mm)
        b.add(f"hole:{i}", ItemClass.HOLE, point, half_width_mm=hole.diameter_mm / 2, layer=EVERY_LAYER)
    items = Items(
        rows=np.array(b.rows, dtype=np.float64).reshape(-1, 6),
        is_arc=np.array(b.is_arc, dtype=np.bool_),
        half_width_mm=np.array(b.half_width_mm, dtype=np.float64),
        item_class=np.array(b.item_class, dtype=np.int64),
        layer=np.array(b.layer, dtype=np.int64),
        path=np.array(b.path, dtype=np.int64),
        slot=np.array(b.slot, dtype=np.int64),
        pad=np.array(b.pad, dtype=np.int64),
        centre_mm=np.array(b.centre_mm, dtype=np.float64).reshape(-1, 2),
        land_radius_mm=np.array(b.land_radius_mm, dtype=np.float64),
        labels=tuple(b.labels),
    )
    return items, first_item


@dataclass(frozen=True, slots=True)
class _PathEnd:
    path: CopperPath
    point: tuple[float, float]
    group: tuple[int, ...]  # item indices of the terminating main primitive and its fillets and tapers


def _path_ends(layout: Layout, first_item: dict[int, int]) -> Iterator[_PathEnd]:
    for path in layout.paths:
        if not path.primitives:
            continue
        mains = main_indices(path.primitives)
        base = first_item[path.id]
        for k, point in ((0, path.primitives[0].start_point()), (-1, path.primitives[-1].end_point())):
            yield _PathEnd(path, point, tuple(base + i for i, m in enumerate(mains) if m == mains[k]))


def _inside_pad(pad: Pad, x_mm: float, y_mm: float) -> bool:
    return bool(pad_closest(pad, np.array([[x_mm, y_mm, x_mm, y_mm, 0.0]]), False)[D][0] <= 0)


def exempt_pairs(layout: Layout, items: Items, first_item: dict[int, int]) -> IntArray:
    """Sorted keys ``i * n + j`` (i < j) of item pairs that connectivity exempts.

    Exempt: a via or pad and the end group of a same-net path whose end point lies on that via or pad; the end groups
    of different paths that meet at one via, pad or coincident end point (a node); a pad and a same-net via whose
    centre lies inside it. An interconnect path ending on a terminal via or a pad joins it whatever the nets (D-022 a).
    Primitives adjacent in one path are exempted in the engine from ``path`` and ``slot``.
    """
    ends = list(_path_ends(layout, first_item))
    via_base = int(np.count_nonzero(items.item_class == ItemClass.TRACE))
    pad_base = via_base + len(layout.vias)
    interconnects = frozenset(layout.circuit.interconnect_path_ids)
    pairs: set[tuple[int, int]] = set()
    nodes: list[tuple[int | None, list[_PathEnd]]] = []
    for v, via in enumerate(layout.vias):
        any_net = interconnects if via.role is ViaRole.TERMINAL else frozenset()
        on_via = [
            e
            for e in ends
            if (e.path.net == via.net or e.path.id in any_net)
            and math.dist(e.point, (via.x_mm, via.y_mm)) <= via.pad_mm / 2
        ]
        nodes.append((via_base + v, on_via))
    for p, pad in enumerate(layout.pads):
        on_pad = [
            e
            for e in ends
            if (e.path.net == pad.net or e.path.id in interconnects)
            and pad.layer in (None, e.path.layer)
            and _inside_pad(pad, *e.point)
        ]
        nodes.append((pad_base + p, on_pad))
        pairs.update(
            (pad_base + p, via_base + v)
            for v, via in enumerate(layout.vias)
            if via.net == pad.net and _inside_pad(pad, via.x_mm, via.y_mm)
        )
    nodes += [(None, node) for node in _coincident_ends(ends)]
    for land, node in nodes:
        if land is not None:
            pairs.update((land, i) for e in node for i in e.group)
        for x, e in enumerate(node):
            pairs.update((i, j) for f in node[x + 1 :] if f.path.id != e.path.id for i in e.group for j in f.group)
    n = len(items)
    keys = [min(a, c) * n + max(a, c) for a, c in pairs]
    return np.unique(np.array(keys, dtype=np.int64))


def _coincident_ends(ends: list[_PathEnd]) -> list[list[_PathEnd]]:
    """Return the groups of same-net path ends on one layer that meet at one point (within COINCIDENCE_MM)."""
    groups = []
    for i, e in enumerate(ends):
        meet = [
            f
            for f in ends[i + 1 :]
            if f.path.layer == e.path.layer
            and f.path.net == e.path.net
            and math.dist(f.point, e.point) <= COINCIDENCE_MM
        ]
        if meet:
            groups.append([e, *meet])
    return groups
