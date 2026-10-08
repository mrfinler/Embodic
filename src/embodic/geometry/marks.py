"""Coil marks: the number of each coil within its phase and the free eye disc inside a spiral coil's innermost turn.

One source for the geometry view and the exporters (m4_review.md ruling a 3), so the canvas and a file cannot differ.
"""

import math
from collections import defaultdict
from collections.abc import Iterator, Sequence
from dataclasses import dataclass

from embodic.geometry.distance import point_segment_distance_mm
from embodic.geometry.layout import Layout
from embodic.geometry.paths import CopperPath
from embodic.geometry.primitives import Line, Primitive, PrimitiveRole
from embodic.model.vocabulary import Phase, TopologyKind

# Hatch keeps this fraction of the free radius around the eye centre, so it never touches a trace edge.
EYE_MARGIN = 0.85
_TURN_ROLES = frozenset({PrimitiveRole.SIDE, PrimitiveRole.END_TURN})


@dataclass(frozen=True, slots=True, kw_only=True)
class CoilMark:
    """One coil on one layer: its phase, number within the phase, polarity and, for a spiral coil, its eye disc."""

    layer: str
    phase: Phase
    number: int  # 1, 2, ... within the phase, in element order
    polarity: int  # +1, -1, or 0 for a coil without polarity
    label: str  # "A1+", "B2-": the geometry view's text until it places labels with embodic.geometry.labels
    cx_mm: float
    cy_mm: float
    eye_radius_mm: float  # 0.0 = label only, no eye fill


def point_primitive_distance_mm(x_mm: float, y_mm: float, p: Primitive) -> float:
    """Distance from a point to a primitive's centre line."""
    if isinstance(p, Line):
        return point_segment_distance_mm(x_mm, y_mm, p)
    angle = math.atan2(y_mm - p.cy_mm, x_mm - p.cx_mm)
    along = (angle - p.start_rad) % math.tau if p.sweep_rad >= 0 else (p.start_rad - angle) % math.tau
    if along <= abs(p.sweep_rad):
        return abs(math.hypot(x_mm - p.cx_mm, y_mm - p.cy_mm) - p.r_mm)
    return min(math.dist((x_mm, y_mm), p.start_point()), math.dist((x_mm, y_mm), p.end_point()))


def _free_radius_mm(x_mm: float, y_mm: float, copper: Sequence[Primitive]) -> float:
    return min(point_primitive_distance_mm(x_mm, y_mm, p) - p.width_mm / 2 for p in copper)


def _encloses(x_mm: float, y_mm: float, coil_points: Sequence[tuple[float, float]]) -> bool:
    """Return True when copper lies in each of eight 45 degree sectors around the point."""
    sectors = {int((math.atan2(py - y_mm, px - x_mm) + math.pi) / (math.tau / 8)) % 8 for px, py in coil_points}
    return len(sectors) == 8


def _samples(p: Primitive, count: int = 8) -> Iterator[tuple[float, float]]:
    for k in range(count + 1):
        f = k / count
        if isinstance(p, Line):
            yield (p.x1_mm + f * (p.x2_mm - p.x1_mm), p.y1_mm + f * (p.y2_mm - p.y1_mm))
        else:
            yield p.point_at(p.start_rad + f * p.sweep_rad)


def _eye(turns: Sequence[Primitive], copper: Sequence[Primitive]) -> tuple[float, float, float]:
    """Return the centre and radius of the largest disc inside the coil that no copper of the layer enters.

    The search on a 24 x 24 grid measures against the coil's own turns; the radius is then cut to the layer's copper.
    """
    points = [q for p in turns for q in _samples(p)]
    xs, ys = [x for x, _ in points], [y for _, y in points]
    steps = 24
    best = (sum(xs) / len(xs), sum(ys) / len(ys), 0.0)
    for i in range(1, steps):
        for j in range(1, steps):
            x = min(xs) + (max(xs) - min(xs)) * i / steps
            y = min(ys) + (max(ys) - min(ys)) * j / steps
            if _encloses(x, y, points) and (free := _free_radius_mm(x, y, turns)) > best[2]:
                best = (x, y, free)
    x, y, _ = best
    return x, y, EYE_MARGIN * max(0.0, _free_radius_mm(x, y, copper))


def _coil_number(paths: Sequence[CopperPath]) -> dict[tuple[Phase, int], int]:
    """Return the number of each coil within its phase, 1, 2, ... in element order."""
    elements: dict[Phase, set[int]] = defaultdict(set)
    for path in paths:
        if path.phase is not None and path.element is not None:
            elements[path.phase].add(path.element)
    return {(phase, e): i + 1 for phase, found in elements.items() for i, e in enumerate(sorted(found))}


def coil_marks(layout: Layout) -> Iterator[CoilMark]:
    """Yield the mark of every coil on every copper layer, layer by layer, coils by (phase, element, polarity)."""
    numbers = _coil_number(layout.paths)
    for layer in layout.copper_layers:
        on_layer = [p for p in layout.paths if p.layer == layer]
        copper = [prim for p in on_layer for prim in p.primitives]
        coils: dict[tuple[Phase, int, int], list[Primitive]] = defaultdict(list)
        for path in on_layer:
            if path.phase is not None and path.element is not None:
                coils[(path.phase, path.element, path.polarity)].extend(path.primitives)
        for (phase, element, polarity), prims in sorted(coils.items()):
            number = numbers[(phase, element)]
            label = f"{phase.value}{number}{'-' if polarity < 0 else '+'}"
            turns = [p for p in prims if p.role in _TURN_ROLES] or prims
            if layout.topology is TopologyKind.SPIRAL:
                cx, cy, radius = _eye(turns, copper)
            else:
                (cx, cy), radius = prims[0].start_point(), 0.0
            yield CoilMark(
                layer=layer,
                phase=phase,
                number=number,
                polarity=polarity,
                label=label,
                cx_mm=cx,
                cy_mm=cy,
                eye_radius_mm=radius,
            )


def top_layer_of_each_phase(layout: Layout) -> dict[Phase, str]:
    """Return, per phase, the first copper layer in stack order that carries copper of that phase.

    A drawing names each phase on the top layer that shows it: a spiral or wave board names all three on its top layer,
    a serpentine board with one phase per layer pair names each on its own pair's upper layer.
    """
    carried = {(p.layer, p.phase) for p in layout.paths if p.phase is not None}
    return {
        phase: next(layer for layer in layout.copper_layers if (layer, phase) in carried)
        for phase in Phase
        if any(phase == q for _, q in carried)
    }
