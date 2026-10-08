"""Canonical coil of k series groups (spiral_generator_spec.md G5 k centre vias, G6 series via fan, revision U-E6).

Group g runs from ring via g to its centre via on layer X and back out to ring via g + 1 on layer Y. Ring via i sits on
the terminal ring r_T at the CCW side for even i and the CW side for odd i, fan level i // 2. Level 0 keeps the
straight terminal stub to the corner; level l >= 1 enters or leaves on a radial stub at its fan angle, joined to outer
arc 0 cut at that angle. Odd groups start at the right side of turn 0. Status `unresolved` (D-020): the board is
DRC-checked and refused when a rule fails.
"""

import dataclasses
import math
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from embodic.generators.spiral.artwork import CoilArtwork, coil_artwork, sharp_artwork
from embodic.generators.spiral.fillets import Corner, CornerKind
from embodic.generators.spiral.turns import CoilFrame, FullClosing, Point, group_closing
from embodic.geometry.primitives import Arc, Line, Primitive, PrimitiveRole
from embodic.geometry.transforms import mirror, reverse_path
from embodic.model.winding_specs import SideStyle


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


class SeriesFailure(StrEnum):
    """Why the canonical series coil cannot be drawn."""

    FILLET = "fillet"  # a fillet trims a group's lead or its cut outer arc past its other end (G9)
    FAN = "fan"  # the innermost ring vias of the two sides are closer than the fan pitch (G6 step 6)


@dataclass(frozen=True, slots=True, kw_only=True)
class RingVia:
    """Ring via i of the G6 fan: ``side`` +1 (CCW) for even i, -1 (CW) for odd i, at fan level i // 2."""

    side: int
    level: int
    level_rad: float  # a_level
    radius_mm: float  # r_T

    @property
    def angle_rad(self) -> float:
        """Signed angle of the via: +a_level on the CCW side, -a_level on the CW side."""
        return self.side * self.level_rad

    @property
    def point(self) -> Point:
        """Via centre in the canonical coil frame."""
        return (self.radius_mm * math.cos(self.angle_rad), self.radius_mm * math.sin(self.angle_rad))


def fan_angles(frame: CoilFrame, terminal: Point, start_corner: Point, bus_width_mm: float, levels: int) -> list[float]:
    """G6 step 3: a_0 = a_V, a_1 = min(a_V - da, foot bound), a_l = a_1 - (l - 1) da; da = asin(c_f / r_T).

    The foot bound keeps a radial stub at a_1 w + s from the side that ends at the corner on the same layer:
    h - asin((d_0 + w + s) / R_o0) for parallel sides, the side ray minus asin((w + s) / R_o0) for radial sides.
    """
    w, s, pad = frame.trace_width_mm, frame.clearance_mm, frame.via_pad_mm
    r_t, a_v = math.hypot(*terminal), math.atan2(terminal[1], terminal[0])
    r_o0 = frame.r_outer_mm - frame.end_width_outer_mm / 2
    da = math.asin((max(pad, w, bus_width_mm) + s) / r_t)
    if frame.side_style is SideStyle.PARALLEL:
        foot_rad = frame.half_angle_rad - math.asin((frame.offset_mm(0) + w + s) / r_o0)
    else:
        foot_rad = math.atan2(start_corner[1], start_corner[0]) - math.asin((w + s) / r_o0)
    a_1 = min(a_v - da, foot_rad)
    return [a_v] + [a_1 - (level - 1) * da for level in range(1, levels)]


def ring_vias(
    frame: CoilFrame, terminal: Point, start_corner: Point, bus_width_mm: float, groups: int
) -> tuple[RingVia, ...]:
    """Return the k + 1 ring vias of a coil of ``groups`` series groups (G6 step 1)."""
    angles = fan_angles(frame, terminal, start_corner, bus_width_mm, groups // 2 + 1)
    r_t = math.hypot(*terminal)
    sides = [1 if i % 2 == 0 else -1 for i in range(groups + 1)]
    return tuple(
        RingVia(side=side, level=i // 2, level_rad=angles[i // 2], radius_mm=r_t) for i, side in enumerate(sides)
    )


def _line(a: Point, b: Point, width_mm: float) -> Line:
    return Line(x1_mm=a[0], y1_mm=a[1], x2_mm=b[0], y2_mm=b[1], width_mm=width_mm, role=PrimitiveRole.STUB)


def _radial(a_rad: float, r_from_mm: float, r_to_mm: float, width_mm: float) -> Line:
    unit = (math.cos(a_rad), math.sin(a_rad))
    return _line((r_from_mm * unit[0], r_from_mm * unit[1]), (r_to_mm * unit[0], r_to_mm * unit[1]), width_mm)


def _clockwise(arc: Arc) -> Arc | None:
    """Return the cut arc, or None when the cut angle lies outside the arc (a fillet took that part)."""
    return arc if arc.sweep_rad < 0 else None


def _entry(art: CoilArtwork, group: int, via: RingVia, width_mm: float) -> tuple[Primitive, ...] | None:
    """Layer X of ``group`` from its entry ring via to its centre via."""
    body = art.primitives[1:]
    if via.level == 0 and group == 0:
        return art.primitives
    if via.level == 0:  # odd group at the CW terminal: straight stub to the right side of turn 0
        side = body[next(i for i, p in enumerate(body) if p.role is PrimitiveRole.SIDE) :]
        return (_line(via.point, side[0].start_point(), width_mm), *side)
    arc0 = body[0]
    assert isinstance(arc0, Arc)  # series groups are refused for straight ends (generate._unsupported)
    end_rad = arc0.start_rad + arc0.sweep_rad
    cut = _clockwise(dataclasses.replace(arc0, start_rad=via.angle_rad, sweep_rad=end_rad - via.angle_rad))
    return None if cut is None else (_radial(via.angle_rad, via.radius_mm, arc0.r_mm, width_mm), cut, *body[1:])


def _exit(art: CoilArtwork, x: tuple[Primitive, ...], via: RingVia, width_mm: float) -> tuple[Primitive, ...] | None:
    """Layer Y of a group from its centre via to its exit ring via: the mirror of the body, re-stubbed at level >= 1."""
    if via.level == 0:
        return reverse_path(mirror(x, 0.0))
    core = reverse_path(mirror(art.primitives[1:], 0.0))
    last = core[-1]  # outer arc 0, run clockwise from the A_0 side
    assert isinstance(last, Arc)
    cut = _clockwise(dataclasses.replace(last, sweep_rad=via.angle_rad - last.start_rad))
    return None if cut is None else (*core[:-1], cut, _radial(via.angle_rad, last.r_mm, via.radius_mm, width_mm))


def series_coil(
    frame: CoilFrame, closing: FullClosing, bus_width_mm: float, groups: int,
    filleted: Mapping[tuple[CornerKind, int], Corner],
) -> SeriesCoil | SeriesFailure:  # fmt: skip
    """Canonical coil of ``groups`` series groups, or why it cannot be drawn."""
    sharp = sharp_artwork(frame, closing, bus_width_mm)
    rings = ring_vias(frame, sharp.terminal, closing.start_corner, bus_width_mm, groups)
    pitch_mm = max(frame.via_pad_mm, frame.trace_width_mm, bus_width_mm) + frame.clearance_mm
    if 2 * rings[-1].radius_mm * math.sin(rings[-1].level_rad) < pitch_mm:
        return SeriesFailure.FAN
    built = []
    for g in range(groups):
        own = group_closing(frame, closing, g)
        art = coil_artwork(frame, own, bus_width_mm, filleted) if filleted else sharp_artwork(frame, own, bus_width_mm)
        x = None if art is None else _entry(art, g, rings[g], frame.trace_width_mm)
        y = None if art is None or x is None else _exit(art, x, rings[g + 1], frame.trace_width_mm)
        if art is None or x is None or y is None:
            return SeriesFailure.FILLET
        built.append(GroupCopper(x=x, y=y, centre_via=art.centre_via))
    return SeriesCoil(groups=tuple(built), ring_vias=tuple(r.point for r in rings))
