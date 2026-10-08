"""Agent 4's own mapper from an Xcoil raw layout and an embodic BoardStack to one comparable shape (U-V3).

Both sides become ``Board`` records: per copper layer, the primitives with a role from one vocabulary, plus via and
pad discs. The Xcoil side reads only Node output of ``xcoil_dump.cjs``; the embodic side reads only public fields of
``BoardStack``. Nothing here imports tests/golden.
"""

import math
import sys
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "m1"))

from records import Arc, Line, Prim

# Xcoil primitive kind -> embodic PrimitiveRole value. far, near and closing are the three end-turn arcs of a
# serpentine strand (engine.js buildCanonical); endturn is the wave name for the same thing.
ROLE_OF_XCOIL_KIND = {
    "side": "side", "fillet": "fillet", "far": "end_turn", "near": "end_turn", "closing": "end_turn",
    "endturn": "end_turn", "bus": "bus", "stub": "stub", "ring": "ring", "link": "link", "leg": "leg",
    "taper": "taper", "lead": "lead",
}  # fmt: skip


@dataclass(frozen=True, slots=True)
class Copper:
    """One copper primitive with its role."""

    prim: Prim
    role: str


@dataclass(frozen=True, slots=True)
class Land:
    """A via or pad disc."""

    x: float
    y: float
    diameter: float
    tag: str


@dataclass(slots=True)
class Board:
    """One board: copper per layer (top first), the z of each layer, via and pad discs."""

    layers: list[list[Copper]] = field(default_factory=list)
    z_mm: list[float] = field(default_factory=list)
    vias: list[Land] = field(default_factory=list)
    pads: list[Land] = field(default_factory=list)


def _xcoil_prim(q: Mapping[str, Any]) -> Prim:
    if q["t"] == "L":
        return Line(q["x1"], q["y1"], q["x2"], q["y2"], q["w"])
    return Arc(q["cx"], q["cy"], q["r"], q["a1"], q["a2"] - q["a1"], q["w"])


def boards_from_xcoil(dump: Mapping[str, Any]) -> list[Board]:
    """Map Xcoil's layers (grouped by ``board``, in index order), vias (board = phase in a per-phase stack), pads."""
    n = dump["nBoards"]
    boards = [Board() for _ in range(n)]
    for layer in sorted(dump["layers"], key=lambda ly: ly["index"]):
        b = boards[layer["board"]]
        b.z_mm.append(layer["z"])
        b.layers.append(
            [Copper(_xcoil_prim(q), ROLE_OF_XCOIL_KIND[q["kind"]]) for o in layer["objs"] for q in o["prims"]]
        )
    pad_dia = dump["params"]["viaPad"]
    for v in dump["vias"]:
        boards[v["phase"] if n > 1 else 0].vias.append(Land(v["x"], v["y"], pad_dia, str(v["type"])))
    for p in dump["pads"]:
        boards[p["phase"] if n > 1 else 0].pads.append(Land(p["x"], p["y"], p["dia"], p["net"]))
    return boards


def _own_prim(q: Any) -> Prim:
    if hasattr(q, "x1_mm"):
        return Line(q.x1_mm, q.y1_mm, q.x2_mm, q.y2_mm, q.width_mm)
    return Arc(q.cx_mm, q.cy_mm, q.r_mm, q.start_rad, q.sweep_rad, q.width_mm)


def boards_from_embodic(stack: Any) -> list[Board]:
    """Map every board of a BoardStack through its public fields."""
    out = []
    for layout in stack.boards:
        b = Board()
        for name in layout.copper_layers:
            b.z_mm.append(layout.copper_z_mm[name])
            prims = [(q, path) for path in layout.paths if path.layer == name for q in path.primitives]
            b.layers.append([Copper(_own_prim(q), q.role.value) for q, _ in prims])
        b.vias = [Land(v.x_mm, v.y_mm, v.pad_mm, v.role.value) for v in layout.vias]
        b.pads = [Land(p.x_mm, p.y_mm, p.width_mm, p.net) for p in layout.pads]
        out.append(b)
    return out


def length(p: Prim) -> float:
    """Centreline length."""
    if isinstance(p, Line):
        return math.hypot(p.x2 - p.x1, p.y2 - p.y1)
    return abs(p.sweep) * p.r


def point_at(p: Prim, t: float) -> tuple[float, float]:
    """Point at fraction ``t`` of the primitive in its own direction."""
    if isinstance(p, Line):
        return (p.x1 + t * (p.x2 - p.x1), p.y1 + t * (p.y2 - p.y1))
    a = p.start + t * p.sweep
    return (p.cx + p.r * math.cos(a), p.cy + p.r * math.sin(a))


def _in_sweep(p: Arc, phi: float) -> bool:
    s = p.sweep
    d = (phi - p.start) % (2 * math.pi) if s >= 0 else (p.start - phi) % (2 * math.pi)
    return d <= abs(s) + 1e-15


def distance(x: float, y: float, p: Prim) -> float:
    """Exact distance from a point to a primitive's centreline."""
    if isinstance(p, Line):
        dx, dy = p.x2 - p.x1, p.y2 - p.y1
        n2 = dx * dx + dy * dy
        t = 0.0 if n2 == 0 else min(1.0, max(0.0, ((x - p.x1) * dx + (y - p.y1) * dy) / n2))
        return math.hypot(x - p.x1 - t * dx, y - p.y1 - t * dy)
    if _in_sweep(p, math.atan2(y - p.cy, x - p.cx)):
        return abs(math.hypot(x - p.cx, y - p.cy) - p.r)
    return min(math.dist((x, y), point_at(p, 0.0)), math.dist((x, y), point_at(p, 1.0)))


def box(p: Prim) -> tuple[float, float, float, float]:
    """Exact bounding box of the centreline."""
    if isinstance(p, Line):
        return (min(p.x1, p.x2), min(p.y1, p.y2), max(p.x1, p.x2), max(p.y1, p.y2))
    pts = [point_at(p, 0.0), point_at(p, 1.0)]
    for k in range(4):
        phi = k * math.pi / 2
        if _in_sweep(p, phi):
            pts.append((p.cx + p.r * math.cos(phi), p.cy + p.r * math.sin(phi)))
    xs, ys = zip(*pts, strict=True)
    return (min(xs), min(ys), max(xs), max(ys))


class Index:
    """Uniform grid over primitive boxes; ``nearest`` falls back to a full scan beyond the 3 x 3 neighbourhood."""

    def __init__(self, items: Sequence[Copper], cell: float = 2.0) -> None:
        self.items, self.cell = items, cell
        self.grid: dict[tuple[int, int], list[int]] = defaultdict(list)
        for i, c in enumerate(items):
            x0, y0, x1, y1 = box(c.prim)
            for gx in range(math.floor(x0 / cell), math.floor(x1 / cell) + 1):
                for gy in range(math.floor(y0 / cell), math.floor(y1 / cell) + 1):
                    self.grid[(gx, gy)].append(i)

    def nearest(self, x: float, y: float, tie_mm: float = 1e-9) -> tuple[float, list[int]]:
        """Least distance and every item within ``tie_mm`` of it (coincident copper gives ties)."""
        gx, gy = math.floor(x / self.cell), math.floor(y / self.cell)
        cand = {i for dx in (-1, 0, 1) for dy in (-1, 0, 1) for i in self.grid.get((gx + dx, gy + dy), ())}
        found = [(distance(x, y, self.items[i].prim), i) for i in cand]
        if min(found, default=(math.inf, -1))[0] > self.cell:
            found = [(distance(x, y, c.prim), i) for i, c in enumerate(self.items)]
        best = min(d for d, _ in found)
        return best, [i for d, i in found if d <= best + tie_mm]


@dataclass(frozen=True, slots=True)
class LayerDiff:
    """Sampled distance in both directions and the samples whose nearest primitive has another width or role."""

    max_xcoil_to_own_mm: float
    max_own_to_xcoil_mm: float
    width_mismatches: int
    role_mismatches: int
    samples: int


SAMPLE_T = (0.0, 0.25, 0.5, 0.75, 1.0)
INTERIOR_T = (0.25, 0.5, 0.75)


def _one_way(src: Sequence[Copper], dst: Sequence[Copper]) -> tuple[float, int, int, int]:
    index = Index(dst)
    worst, widths, roles, n = 0.0, 0, 0, 0
    for c in src:
        for t in SAMPLE_T:
            d, ties = index.nearest(*point_at(c.prim, t))
            worst, n = max(worst, d), n + 1
            if t in INTERIOR_T:
                widths += all(abs(dst[j].prim.width - c.prim.width) > 1e-9 for j in ties)
                roles += all(dst[j].role != c.role for j in ties)
    return worst, widths, roles, n


def compare_layer(xcoil: Sequence[Copper], own: Sequence[Copper]) -> LayerDiff:
    """Sample every primitive at five points and measure the distance to the other side's nearest centreline."""
    a, wa, ra, na = _one_way(xcoil, own)
    b, wb, rb, nb = _one_way(own, xcoil)
    return LayerDiff(a, b, wa + wb, ra + rb, na + nb)


def role_counts(items: Iterable[Copper]) -> Counter[str]:
    """Primitive count by role."""
    return Counter(c.role for c in items)


def role_lengths(items: Iterable[Copper]) -> dict[str, float]:
    """Centreline length by role."""
    out: dict[str, float] = defaultdict(float)
    for c in items:
        out[c.role] += length(c.prim)
    return dict(out)


def match_lands(xcoil: Sequence[Land], own: Sequence[Land]) -> tuple[float, float]:
    """Worst distance from any land to the nearest land on the other side, and the worst diameter difference."""
    worst, dia = 0.0, 0.0
    for src, dst in ((xcoil, own), (own, xcoil)):
        for p in src:
            q = min(dst, key=lambda q, p=p: math.dist((p.x, p.y), (q.x, q.y)))
            worst = max(worst, math.dist((p.x, p.y), (q.x, q.y)))
            dia = max(dia, abs(p.diameter - q.diameter))
    return worst, dia
