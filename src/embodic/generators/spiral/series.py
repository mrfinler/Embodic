"""Canonical coil of k series groups (spiral_generator_spec.md G5 k centre vias, G6 series groups and terminal fan).

Group g runs from ring via g to its centre via on layer X and back out to ring via g + 1 on layer Y. Ring via i sits on
the terminal ring at the CCW side for even i and the CW side for odd i, fan level i // 2 at a_V - level 2 asin((pad + s)
/ (2 r_T)), so ring vias that share a side keep pad + s between centres. Even groups enter at A_0 like the single-group
coil; odd groups enter at the right side of turn 0 and skip the first outer arc. Status `unresolved` (D-020): the
board is DRC-checked and refused when a rule fails.
"""

import math
from collections.abc import Mapping
from dataclasses import dataclass

from embodic.generators.spiral.artwork import CoilArtwork, coil_artwork, sharp_artwork
from embodic.generators.spiral.fillets import Corner, CornerKind
from embodic.generators.spiral.turns import CoilFrame, FullClosing, Point, group_closing
from embodic.geometry.primitives import Line, Primitive, PrimitiveRole
from embodic.geometry.transforms import mirror, reverse_path

_SAME_POINT_MM = 1e-9


@dataclass(frozen=True, slots=True, kw_only=True)
class GroupCopper:
    """Layer X (ring via g to centre via) and layer Y (centre via to ring via g + 1) of one series group."""

    x: tuple[Primitive, ...]
    y: tuple[Primitive, ...]
    centre_via: Point


@dataclass(frozen=True, slots=True, kw_only=True)
class SeriesCoil:
    """The k groups in current order and the k + 1 ring vias: 0 is the coil entry, k its exit, the rest transfers."""

    groups: tuple[GroupCopper, ...]
    ring_vias: tuple[Point, ...]


def _mirrored(p: Point) -> Point:
    return (p[0], -p[1])


def ring_via(frame: CoilFrame, terminal: Point, transition: int) -> Point:
    """Ring via ``transition``: side by parity, fan level transition // 2 toward the coil axis (G6)."""
    level = transition // 2
    if level == 0:
        point = terminal
    else:
        r_t = math.hypot(*terminal)
        step = 2 * math.asin((frame.via_pad_mm + frame.clearance_mm) / (2 * r_t))
        a_rad = math.atan2(terminal[1], terminal[0]) - level * step
        point = (r_t * math.cos(a_rad), r_t * math.sin(a_rad))
    return point if transition % 2 == 0 else _mirrored(point)


def _stub(a: Point, b: Point, width_mm: float) -> Line:
    return Line(x1_mm=a[0], y1_mm=a[1], x2_mm=b[0], y2_mm=b[1], width_mm=width_mm, role=PrimitiveRole.STUB)


def _group(art: CoilArtwork, group: int, entry: Point, exit_: Point, width_mm: float) -> GroupCopper:
    """Re-stub the single-group artwork for ``group``: odd groups drop the first outer arc and its corner fillet."""
    stub, body = art.primitives[0], art.primitives[1:]
    if group % 2 == 1:
        body = body[next(i for i, p in enumerate(body) if p.role is PrimitiveRole.SIDE) :]
    start = body[0].start_point() if group % 2 == 1 else stub.end_point()
    x = (stub if group == 0 else _stub(entry, start, width_mm), *body)
    y = reverse_path(mirror(x, 0.0))
    if math.dist(y[-1].end_point(), exit_) > _SAME_POINT_MM:  # odd groups exit one fan level further in
        y = (*y[:-1], _stub(y[-1].start_point(), exit_, width_mm))
    return GroupCopper(x=x, y=y, centre_via=art.centre_via)


def series_coil(
    frame: CoilFrame, closing: FullClosing, bus_width_mm: float, groups: int,
    filleted: Mapping[tuple[CornerKind, int], Corner],
) -> SeriesCoil | None:  # fmt: skip
    """Canonical coil of ``groups`` series groups; None when a fillet does not fit a group's lead (G9)."""
    terminal = sharp_artwork(frame, closing, bus_width_mm).terminal
    rings = tuple(ring_via(frame, terminal, i) for i in range(groups + 1))
    built = []
    for g in range(groups):
        own = group_closing(frame, closing, g)
        art = coil_artwork(frame, own, bus_width_mm, filleted) if filleted else sharp_artwork(frame, own, bus_width_mm)
        if art is None:
            return None
        built.append(_group(art, g, rings[g], rings[g + 1], frame.trace_width_mm))
    return SeriesCoil(groups=tuple(built), ring_vias=rings)
