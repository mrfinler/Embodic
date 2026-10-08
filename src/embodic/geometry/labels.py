"""Phase labels of a drawing and their collision-free placement (m4_review.md ruling b, design_spec.md section 3.3).

Pure and Qt-free: the geometry view and the exporters call the same functions with their own scale, viewport and text
measure, so a label shows the same text at the same board point everywhere. Coordinates are board millimetres, y up;
boxes are measured in viewport pixels, so the 2 px gap holds at every zoom.
"""

import math
from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import dataclass
from itertools import groupby

from embodic.geometry.layout import Layout
from embodic.geometry.marks import coil_marks, top_layer_of_each_phase
from embodic.geometry.paths import CopperPath
from embodic.geometry.primitives import Primitive, PrimitiveRole
from embodic.model.vocabulary import Phase, TopologyKind

MINUS = "−"  # the width of "+", unlike the hyphen (F22)
GAP_PX = 2.0
SERPENTINE_QUADRANTS = 4
LEADER_STEPS = 8  # candidate spots outside the ring, each one label height further out


@dataclass(frozen=True, slots=True, kw_only=True)
class LabelAnchor:
    """One label ruling b asks for: its text and the board point it names."""

    phase: Phase
    text: str  # spiral "A1+", "A2−"; wave "A+" per belt; serpentine "A"
    x_mm: float
    y_mm: float
    first_of_phase: bool  # always placed, with a leader when its own spot is taken


@dataclass(frozen=True, slots=True, kw_only=True)
class Viewport:
    """What the placement sees: the board rectangle on screen or page and its scale."""

    x_min_mm: float
    y_min_mm: float
    x_max_mm: float
    y_max_mm: float
    px_per_mm: float


@dataclass(frozen=True, slots=True, kw_only=True)
class Box:
    """An axis-aligned rectangle in board millimetres."""

    x_min_mm: float
    y_min_mm: float
    x_max_mm: float
    y_max_mm: float

    def grown(self, by_mm: float) -> "Box":
        """Return the box grown by ``by_mm`` on every side."""
        return Box(
            x_min_mm=self.x_min_mm - by_mm,
            y_min_mm=self.y_min_mm - by_mm,
            x_max_mm=self.x_max_mm + by_mm,
            y_max_mm=self.y_max_mm + by_mm,
        )

    def meets(self, other: "Box") -> bool:
        """Return True when the boxes overlap or touch."""
        return not (
            self.x_max_mm < other.x_min_mm
            or other.x_max_mm < self.x_min_mm
            or self.y_max_mm < other.y_min_mm
            or other.y_max_mm < self.y_min_mm
        )

    def inside(self, view: Viewport) -> bool:
        """Return True when the box lies within the viewport."""
        return (
            view.x_min_mm <= self.x_min_mm
            and self.x_max_mm <= view.x_max_mm
            and view.y_min_mm <= self.y_min_mm
            and self.y_max_mm <= view.y_max_mm
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class PlacedLabel:
    """A label that shows: its text centred on (x, y) and, when moved off its anchor, the leader back to it."""

    phase: Phase
    text: str
    x_mm: float
    y_mm: float
    leader: tuple[tuple[float, float], tuple[float, float]] | None  # (anchor, label centre), board mm


TextSize = Callable[[str], tuple[float, float]]  # text -> (width, height) in viewport pixels


def _sign(polarity: int) -> str:
    return MINUS if polarity < 0 else "+"


def _spiral(layout: Layout, layers: dict[Phase, str]) -> Iterator[LabelAnchor]:
    for mark in coil_marks(layout):
        if layers.get(mark.phase) == mark.layer:
            yield LabelAnchor(
                phase=mark.phase,
                text=f"{mark.phase.value}{mark.number}{_sign(mark.polarity)}",
                x_mm=mark.cx_mm,
                y_mm=mark.cy_mm,
                first_of_phase=mark.number == 1,
            )


def _midpoint(p: Primitive) -> tuple[float, float]:
    (x1, y1), (x2, y2) = p.start_point(), p.end_point()
    return (x1 + x2) / 2, (y1 + y2) / 2


def _angle(point: tuple[float, float]) -> float:
    return math.atan2(point[1], point[0]) % math.tau


_Side = tuple[float, tuple[float, float], CopperPath]  # angle, midpoint, path


def _belt_key(side: _Side) -> tuple[Phase | None, int]:
    return side[2].phase, side[2].polarity


def _wave(layout: Layout, layers: dict[Phase, str]) -> Iterator[LabelAnchor]:
    """One label per phase belt: a run of angularly adjacent radial sides with the same phase and polarity."""
    seen: set[Phase] = set()
    for layer in dict.fromkeys(layers.values()):
        sides = sorted(
            (
                (_angle(_midpoint(q)), _midpoint(q), path)
                for path in layout.paths
                if path.layer == layer and path.phase is not None and layers[path.phase] == layer
                for q in path.primitives
                if q.role is PrimitiveRole.SIDE
            ),
            key=lambda side: side[0],
        )
        belts = [list(run) for _, run in groupby(sides, key=_belt_key)]
        if len(belts) > 1 and _belt_key(belts[0][0]) == _belt_key(belts[-1][0]):
            belts[0] = belts.pop() + belts[0]  # the belt that crosses angle 0
        for belt in sorted(belts, key=lambda b: min(side[2].id for side in b)):
            phase, polarity = _belt_key(belt[0])
            assert phase is not None
            x, y = belt[len(belt) // 2][1]
            yield LabelAnchor(
                phase=phase, text=f"{phase.value}{_sign(polarity)}", x_mm=x, y_mm=y, first_of_phase=phase not in seen
            )
            seen.add(phase)


def _serpentine(layout: Layout, layers: dict[Phase, str]) -> Iterator[LabelAnchor]:
    """Four labels per phase, one per 90 degree quadrant, on the outermost end turn nearest the quadrant's middle."""
    for phase, layer in layers.items():
        turns = [
            q
            for p in layout.paths
            if p.phase is phase and p.layer == layer
            for q in p.primitives
            if q.role is PrimitiveRole.END_TURN
        ]
        reach = max(math.hypot(*_midpoint(q)) for q in turns)
        outer = [q for q in turns if math.hypot(*_midpoint(q)) > reach - 1e-6 - 0.5 * q.width_mm]
        for quadrant in range(SERPENTINE_QUADRANTS):
            middle = (quadrant + 0.5) * math.tau / SERPENTINE_QUADRANTS
            best = min(outer, key=lambda q: abs((_angle(_midpoint(q)) - middle + math.pi) % math.tau - math.pi))
            x, y = _midpoint(best)
            yield LabelAnchor(phase=phase, text=phase.value, x_mm=x, y_mm=y, first_of_phase=quadrant == 0)


_BY_TOPOLOGY = {TopologyKind.SPIRAL: _spiral, TopologyKind.WAVE: _wave, TopologyKind.SERPENTINE: _serpentine}


def label_anchors(layout: Layout) -> tuple[LabelAnchor, ...]:
    """Return the labels of one board in priority order: the first of each phase, then every label in index order.

    Each phase is labelled on the top layer that carries it (``top_layer_of_each_phase``).
    """
    anchors = list(_BY_TOPOLOGY[layout.topology](layout, top_layer_of_each_phase(layout)))
    return tuple(a for a in anchors if a.first_of_phase) + tuple(a for a in anchors if not a.first_of_phase)


def pad_boxes(layout: Layout) -> tuple[Box, ...]:
    """Return the bounding box of every terminal pad, which labels keep clear of."""
    return tuple(
        Box(
            x_min_mm=pad.x_mm - max(pad.width_mm, pad.height_mm) / 2,
            y_min_mm=pad.y_mm - max(pad.width_mm, pad.height_mm) / 2,
            x_max_mm=pad.x_mm + max(pad.width_mm, pad.height_mm) / 2,
            y_max_mm=pad.y_mm + max(pad.width_mm, pad.height_mm) / 2,
        )
        for pad in layout.pads
    )


def _box(x_mm: float, y_mm: float, size_px: tuple[float, float], px_per_mm: float) -> Box:
    half_w, half_h = size_px[0] / 2 / px_per_mm, size_px[1] / 2 / px_per_mm
    return Box(x_min_mm=x_mm - half_w, y_min_mm=y_mm - half_h, x_max_mm=x_mm + half_w, y_max_mm=y_mm + half_h)


def _leader_spots(
    anchor: LabelAnchor, ring_outer_mm: float, size_px: tuple[float, float], px_per_mm: float
) -> Iterator[tuple[float, float]]:
    """Yield spots outside the ring along the anchor's own direction, each one label height further out."""
    angle = math.atan2(anchor.y_mm, anchor.x_mm)
    step_mm = (max(size_px) + 2 * GAP_PX) / px_per_mm
    for k in range(1, LEADER_STEPS + 1):
        r = ring_outer_mm + k * step_mm
        yield r * math.cos(angle), r * math.sin(angle)


def place_labels(
    anchors: Iterable[LabelAnchor],
    *,
    view: Viewport,
    text_size: TextSize,
    obstacles: Sequence[Box],
    ring_outer_mm: float,
) -> tuple[PlacedLabel, ...]:
    """Place labels in the given priority order and return those that show.

    A label whose box, grown by 2 px, meets a placed label, an obstacle or the viewport edge is skipped. The first
    label of each phase always places: when its spot is taken it moves outside the ring on its own direction, with a
    leader back to its anchor.
    """
    gap_mm = GAP_PX / view.px_per_mm
    taken = list(obstacles)
    placed: list[PlacedLabel] = []

    def free(box: Box) -> bool:
        grown = box.grown(gap_mm)
        return grown.inside(view) and not any(grown.meets(other) for other in taken)

    for anchor in anchors:
        size = text_size(anchor.text)
        box = _box(anchor.x_mm, anchor.y_mm, size, view.px_per_mm)
        leader = None
        if not free(box):
            if not anchor.first_of_phase:
                continue
            spots = list(_leader_spots(anchor, ring_outer_mm, size, view.px_per_mm))
            x, y = next((s for s in spots if free(_box(*s, size, view.px_per_mm))), spots[0])
            box = _box(x, y, size, view.px_per_mm)
            leader = ((anchor.x_mm, anchor.y_mm), (x, y))
        taken.append(box)
        x_mid, y_mid = (box.x_min_mm + box.x_max_mm) / 2, (box.y_min_mm + box.y_max_mm) / 2
        placed.append(PlacedLabel(phase=anchor.phase, text=anchor.text, x_mm=x_mid, y_mm=y_mid, leader=leader))
    return tuple(placed)
