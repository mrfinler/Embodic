"""Seeded random boards for the run_drc agreement test: continuous paths of lines and arcs, vias, pads, holes, edges.

Paths are random walks inside a small box, so they cross themselves and each other: same-net non-adjacent pairs and
overlaps occur in most boards. Some vias sit on a path end of the same net, some on another net, some anywhere.
"""

import math
import random
from dataclasses import dataclass

from drc_universe import Cls, Item
from records import Arc, Line, Prim, disc, end_point, start_point

BOX_MM = 8.0


@dataclass(frozen=True, slots=True)
class Board:
    """Items of one random board, its copper layer count and the uniform clearance rule."""

    items: tuple[Item, ...]
    layers: int
    rule_mm: float


def _walk(rng: random.Random, width: float, count: int) -> list[Prim]:
    x, y = rng.uniform(0, BOX_MM), rng.uniform(0, BOX_MM)
    heading = rng.uniform(-math.pi, math.pi)
    prims: list[Prim] = []
    for _ in range(count):
        w = width if rng.random() < 0.7 else rng.uniform(0.1, 0.5)
        if rng.random() < 0.45:
            r = rng.uniform(0.3, 3.0)
            sweep = rng.choice((1, -1)) * rng.uniform(0.2, 2.5)
            side = 1.0 if sweep > 0 else -1.0
            cx, cy = x - side * r * math.sin(heading), y + side * r * math.cos(heading)
            start = math.atan2(y - cy, x - cx)
            arc = Arc(cx, cy, r, start, sweep, w)
            prims.append(arc)
            x, y = end_point(arc)
            heading += sweep
        else:
            length = rng.uniform(0.3, 3.0)
            nx, ny = x + length * math.cos(heading), y + length * math.sin(heading)
            prims.append(Line(x, y, nx, ny, w))
            x, y = nx, ny
            heading += rng.uniform(-1.2, 1.2)
    return prims


def random_board(seed: int) -> Board:
    """Return the board for ``seed``; same seed, same board."""
    rng = random.Random(seed)
    layers = rng.randint(1, 3)
    items: list[Item] = []
    ends: list[tuple[float, float, str, int | None]] = []
    path_id = 0
    for layer in range(layers):
        for _ in range(rng.randint(2, 4)):
            net = rng.choice(("A", "B", "C"))
            prims = _walk(rng, rng.uniform(0.15, 0.4), rng.randint(3, 8))
            for k, p in enumerate(prims):
                items.append(Item(f"path:{path_id}/prim:{k}", Cls.TRACE, p, layer, net, path_id, k))
            sx, sy = start_point(prims[0])
            ex, ey = end_point(prims[-1])
            ends += [(sx, sy, net, layer), (ex, ey, net, layer)]
            path_id += 1
    vias = 0
    for _ in range(rng.randint(0, 4)):
        roll = rng.random()
        if roll < 0.5 and ends:
            x, y, net, _layer = rng.choice(ends)
            net = net if roll < 0.35 else "OTHER"
        else:
            x, y, net = rng.uniform(0, BOX_MM), rng.uniform(0, BOX_MM), rng.choice(("A", "B"))
        items.append(Item(f"via:{vias}", Cls.VIA, disc(x, y, rng.uniform(0.4, 0.8)), None, net))
        vias += 1
    if rng.random() < 0.3:
        x, y, net, _layer = rng.choice(ends)
        items.append(Item("pad:0", Cls.PAD, disc(x, y, rng.uniform(1.0, 2.0)), None, net))
    if rng.random() < 0.4:
        items.append(Item("hole:0", Cls.HOLE, disc(rng.uniform(0, BOX_MM), rng.uniform(0, BOX_MM), 1.0), None))
    if rng.random() < 0.4:
        lo, hi = -0.3, BOX_MM + 0.3
        corners = [(lo, lo), (hi, lo), (hi, hi), (lo, hi)]
        for k in range(4):
            (x1, y1), (x2, y2) = corners[k], corners[(k + 1) % 4]
            items.append(Item(f"edge:outer/prim:{k}", Cls.EDGE, Line(x1, y1, x2, y2, 0.0), None))
    return Board(tuple(items), layers, round(rng.uniform(0.1, 0.3), 3))
