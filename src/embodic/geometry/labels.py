"""Phase labels of a drawing and their collision-free placement (m4_review.md ruling b, design_spec.md section 3.3).

Pure and Qt-free: the geometry view and the exporters call the same functions with their own scale, viewport and text
measure, so a label shows the same text at the same board point everywhere. Coordinates are board millimetres, y up;
boxes are measured in viewport pixels, so the 2 px gap holds at every zoom.
"""

import math
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from itertools import groupby

from embodic.geometry.layout import Layout
from embodic.geometry.marks import coil_marks, top_layer_of_each_phase
from embodic.geometry.paths import CopperPath
from embodic.geometry.primitives import Arc, Line, Primitive, PrimitiveRole, primitive_length_mm
from embodic.model.vocabulary import Phase, TopologyKind

MINUS = "−"  # the width of "+", unlike the hyphen (F22)
GAP_PX = 2.0
SERPENTINE_QUADRANTS = 4
LEADER_STEPS = 8  # candidate spots outside the ring, each one label height further out
SPOT_PITCH_MM = 1.0  # spacing of the copper spots a moved label may take


@dataclass(frozen=True, slots=True, kw_only=True)
class LabelAnchor:
    """One label ruling b asks for: its text and the board point it names."""

    phase: Phase
    text: str  # spiral "A1+", "A2−"; wave "A+" per belt; serpentine "A"
    x_mm: float
    y_mm: float
    forced: bool  # the first of its phase and sign: always placed, inside the view (U-S4e ruling h)


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
    seen: set[tuple[Phase, int]] = set()
    for mark in sorted(coil_marks(layout), key=lambda m: m.number):
        if layers.get(mark.phase) == mark.layer:
            group = (mark.phase, mark.polarity)
            yield LabelAnchor(
                phase=mark.phase,
                text=f"{mark.phase.value}{mark.number}{_sign(mark.polarity)}",
                x_mm=mark.cx_mm,
                y_mm=mark.cy_mm,
                forced=group not in seen,
            )
            seen.add(group)


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
    seen: set[tuple[Phase, int]] = set()
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
                phase=phase,
                text=f"{phase.value}{_sign(polarity)}",
                x_mm=x,
                y_mm=y,
                forced=(phase, polarity) not in seen,
            )
            seen.add((phase, polarity))


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
            yield LabelAnchor(phase=phase, text=phase.value, x_mm=x, y_mm=y, forced=quadrant == 0)


_BY_TOPOLOGY = {TopologyKind.SPIRAL: _spiral, TopologyKind.WAVE: _wave, TopologyKind.SERPENTINE: _serpentine}


def label_anchors(layout: Layout) -> tuple[LabelAnchor, ...]:
    """Return the labels of one board in priority order: the first of each phase and sign, then the rest in order.

    Each phase is labelled on the top layer that carries it (``top_layer_of_each_phase``).
    """
    anchors = list(_BY_TOPOLOGY[layout.topology](layout, top_layer_of_each_phase(layout)))
    return tuple(a for a in anchors if a.forced) + tuple(a for a in anchors if not a.forced)


CopperSpots = Mapping[Phase, Sequence[tuple[float, float]]]  # points on each phase's copper, board mm


def _along(q: Primitive) -> Iterator[tuple[float, float]]:
    steps = max(2, math.ceil(primitive_length_mm(q) / SPOT_PITCH_MM))
    for k in range(steps + 1):
        t = k / steps
        if isinstance(q, Line):
            yield q.x1_mm + t * (q.x2_mm - q.x1_mm), q.y1_mm + t * (q.y2_mm - q.y1_mm)
        else:
            assert isinstance(q, Arc)
            yield q.point_at(q.start_rad + t * q.sweep_rad)


def copper_spots(layout: Layout) -> dict[Phase, tuple[tuple[float, float], ...]]:
    """Return points 1 mm apart along each phase's copper on the layer it is labelled on: where a label may move."""
    layers = top_layer_of_each_phase(layout)
    spots: dict[Phase, list[tuple[float, float]]] = {}
    for path in layout.paths:
        if path.phase is not None and layers.get(path.phase) == path.layer:
            for q in path.primitives:
                spots.setdefault(path.phase, []).extend(_along(q))
    return {phase: tuple(points) for phase, points in spots.items()}


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


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


Point = tuple[float, float]


class _Placer:
    """The boxes taken so far in one view, and the labels placed."""

    def __init__(self, view: Viewport, text_size: TextSize, obstacles: Sequence[Box]) -> None:
        self.view, self.text_size = view, text_size
        self.gap_mm = GAP_PX / view.px_per_mm
        self.taken = list(obstacles)
        self.placed: list[PlacedLabel] = []

    def in_view(self, point: Point) -> bool:
        """Return True when the point lies in the view shrunk by the 2 px gap."""
        v, gap, (x, y) = self.view, self.gap_mm, point
        return v.x_min_mm + gap <= x <= v.x_max_mm - gap and v.y_min_mm + gap <= y <= v.y_max_mm - gap

    def free(self, text: str, spot: Point) -> bool:
        """Return True when the label's box, grown by 2 px, lies in the view and meets nothing taken."""
        grown = _box(*spot, self.text_size(text), self.view.px_per_mm).grown(self.gap_mm)
        return grown.inside(self.view) and not any(grown.meets(other) for other in self.taken)

    def first_free(self, text: str, spots: Iterable[Point]) -> Point | None:
        """Return the first spot where the label is free."""
        return next((spot for spot in spots if self.free(text, spot)), None)

    def place(self, phase: Phase, text: str, spot: Point, leader: tuple[Point, Point] | None = None) -> None:
        """Take the label's box and record the label."""
        box = _box(*spot, self.text_size(text), self.view.px_per_mm)
        self.taken.append(box)
        x_mid, y_mid = (box.x_min_mm + box.x_max_mm) / 2, (box.y_min_mm + box.y_max_mm) / 2
        self.placed.append(PlacedLabel(phase=phase, text=text, x_mm=x_mid, y_mm=y_mid, leader=leader))

    def place_forced(self, anchor: LabelAnchor, ring_outer_mm: float, copper: Sequence[Point]) -> None:
        """Place a forced label whose own spot is taken: a leader inside the view, else its phase's nearest copper."""
        own = (anchor.x_mm, anchor.y_mm)
        if self.in_view(own):
            size = self.text_size(anchor.text)
            out = self.first_free(anchor.text, _leader_spots(anchor, ring_outer_mm, size, self.view.px_per_mm))
            if out is not None:
                self.place(anchor.phase, anchor.text, out, (own, out))
                return
        near = self.first_free(anchor.text, sorted(copper, key=lambda spot: _distance(spot, own)))
        if near is not None:
            self.place(anchor.phase, anchor.text, near)
        elif self.in_view(own):
            self.place(anchor.phase, anchor.text, own)

    def name_unlabelled(self, phase: Phase, anchors: Sequence[LabelAnchor], copper: Sequence[Point]) -> None:
        """Label a phase that shows copper but no label, on the free copper spot nearest the view centre."""
        v = self.view
        centre = ((v.x_min_mm + v.x_max_mm) / 2, (v.y_min_mm + v.y_max_mm) / 2)
        for spot in sorted(copper, key=lambda point: _distance(point, centre)):
            text = min(anchors, key=lambda a: _distance((a.x_mm, a.y_mm), spot)).text
            if self.free(text, spot):
                self.place(phase, text, spot)
                return


def place_labels(
    anchors: Iterable[LabelAnchor],
    *,
    view: Viewport,
    text_size: TextSize,
    obstacles: Sequence[Box],
    ring_outer_mm: float,
    copper: CopperSpots | None = None,
) -> tuple[PlacedLabel, ...]:
    """Place labels in the given priority order and return those that show, every one inside the view.

    A label whose box, grown by 2 px, meets a placed label, an obstacle or the viewport edge is skipped. A forced label
    (the first of its phase and sign) always places: on its anchor when that is free, else outside the ring on its
    own direction with a leader when anchor and label both lie in the view, else on the free ``copper`` spot of its
    phase nearest its anchor. Last, every phase with a ``copper`` spot in the view but no label gets one, on the free
    spot nearest the view centre, named like its nearest anchor (U-S4e ruling h).
    """
    placer = _Placer(view, text_size, obstacles)
    ordered = list(anchors)
    visible = {phase: [p for p in points if placer.in_view(p)] for phase, points in (copper or {}).items()}
    for anchor in ordered:
        if placer.free(anchor.text, (anchor.x_mm, anchor.y_mm)):
            placer.place(anchor.phase, anchor.text, (anchor.x_mm, anchor.y_mm))
        elif anchor.forced:
            placer.place_forced(anchor, ring_outer_mm, visible.get(anchor.phase, ()))
    for phase, points in visible.items():
        own = [a for a in ordered if a.phase is phase]
        if points and own and not any(label.phase is phase for label in placer.placed):
            placer.name_unlabelled(phase, own, points)
    return tuple(placer.placed)
