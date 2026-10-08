"""What the shell shows of one compute: state machine, summary strip and the drawable geometry. Qt-free.

Every compute request carries a growing id. The worker cancels the run it supersedes, and this view-model drops any
result whose id is not the latest, so a late result can never replace a newer one (latest wins, REQ-N-02).
"""

import math
from collections import defaultdict
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol, TypeAlias

from embodic.geometry.distance import point_segment_distance_mm
from embodic.geometry.layout import Layout
from embodic.geometry.paths import CopperPath
from embodic.geometry.primitives import Line, Primitive, PrimitiveRole
from embodic.io.examples import load_example
from embodic.io.project import ProjectFile, project_from_example, project_provenance, save_project
from embodic.model.design import DesignParameters
from embodic.model.provenance import ProvenanceMap
from embodic.model.vocabulary import Phase, TopologyKind
from embodic.outcome import ComputeOutcome
from embodic.results import Traceable
from embodic.results.formatting import format_value
from embodic.results.status import Status
from embodic.ui.strings import text
from embodic.ui.viewmodels.observable import Observable

# Hatch keeps this fraction of the free radius around the eye centre, so it never touches a trace edge.
EYE_MARGIN = 0.85
_TURN_ROLES = frozenset({PrimitiveRole.SIDE, PrimitiveRole.END_TURN})

CheckState: TypeAlias = Literal["pass", "fail"]


@dataclass(frozen=True, slots=True, kw_only=True)
class ComputeRequest:
    """One compute the worker runs; ``request_id`` grows with every request."""

    request_id: int
    design: DesignParameters
    provenance: ProvenanceMap


class ComputeSubmitter(Protocol):
    """Runs requests off the GUI thread; a new request cancels the one before it."""

    def submit(self, request: ComputeRequest) -> None:
        """Start a request and cancel the one still running."""


@dataclass(frozen=True, slots=True, kw_only=True)
class SummaryItem:
    """One cell of the summary strip."""

    key: str  # objectName of the cell
    label: str
    value_text: str
    state: CheckState | None  # check text with glyph and word
    status: Status | None  # trust badge from the data (D-007)
    assumed_count: int | None


@dataclass(frozen=True, slots=True, kw_only=True)
class CoilMark:
    """The letter label of one coil on one layer and, for a spiral coil, the free disc inside its innermost turn."""

    layer: str
    phase: Phase
    label: str  # "A1+", "B2-"
    cx_mm: float
    cy_mm: float
    eye_radius_mm: float  # 0.0 = label only, no eye fill


@dataclass(frozen=True, slots=True, kw_only=True)
class GeometryScene:
    """Every board of the outcome and the marks drawn over its copper."""

    boards: tuple[Layout, ...]
    layers: tuple[str, ...]  # copper layer names in stack order, each once
    marks: tuple[CoilMark, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class OutcomeEmpty:
    """No design open; New design and Examples are offered (UI-23)."""

    state: Literal["empty"] = "empty"


@dataclass(frozen=True, slots=True, kw_only=True)
class OutcomeReady:
    """The latest compute finished."""

    state: Literal["ready"] = "ready"
    outcome: ComputeOutcome
    summary: tuple[SummaryItem, ...]
    scene: GeometryScene | None


@dataclass(frozen=True, slots=True, kw_only=True)
class OutcomeComputing:
    """A compute runs; the previous result stays on screen."""

    state: Literal["computing"] = "computing"
    previous: OutcomeReady | None


@dataclass(frozen=True, slots=True, kw_only=True)
class OutcomeFailed:
    """The engine raised; the log entry carries ``correlation_id`` (UI-12)."""

    state: Literal["failed"] = "failed"
    correlation_id: str
    previous: OutcomeReady | None


OutcomeState: TypeAlias = OutcomeEmpty | OutcomeComputing | OutcomeReady | OutcomeFailed


def shown_result(state: OutcomeState) -> OutcomeReady | None:
    """Return the result on screen in a state: the latest, or the one kept while computing or after a crash."""
    if isinstance(state, OutcomeReady):
        return state
    return None if isinstance(state, OutcomeEmpty) else state.previous


class OutcomeViewModel:
    """The open project, its compute requests and what the shell shows of the latest outcome."""

    def __init__(self, submitter: ComputeSubmitter) -> None:
        self._submitter = submitter
        self._latest_id = 0
        self.project: ProjectFile | None = None
        self.state: Observable[OutcomeState] = Observable(OutcomeEmpty())
        self.hidden_layers: Observable[frozenset[str]] = Observable(frozenset())

    def open_example(self, example_id: str) -> None:
        """Open a packaged example and compute it."""
        self.open_project(project_from_example(load_example(example_id)))

    def open_project(self, project: ProjectFile) -> None:
        """Show a complete project and compute it."""
        self.project = project
        self.compute_now()

    def compute_now(self) -> None:
        """Compute the open project again; does nothing while no project is open."""
        if self.project is None:
            return
        self._latest_id += 1
        self.state.set(OutcomeComputing(previous=shown_result(self.state.value)))
        request = ComputeRequest(
            request_id=self._latest_id, design=self.project.design, provenance=project_provenance(self.project)
        )
        self._submitter.submit(request)

    def save_project(self, path: Path) -> str:
        """Write the open project; return its design hash."""
        if self.project is None:
            raise RuntimeError("no project is open")
        return save_project(path, self.project)

    def on_finished(self, request_id: int, ready: OutcomeReady | None) -> None:
        """Take a worker result built by `ready_state`; a superseded or cancelled one is dropped."""
        if request_id != self._latest_id or ready is None:
            return
        self.state.set(ready)

    def on_failed(self, request_id: int, correlation_id: str) -> None:
        """Take a worker crash report for the latest request."""
        if request_id != self._latest_id:
            return
        self.state.set(OutcomeFailed(correlation_id=correlation_id, previous=shown_result(self.state.value)))

    def set_layer_visible(self, layer: str, visible: bool) -> None:
        """Show or hide one copper layer in the geometry view."""
        hidden = self.hidden_layers.value
        self.hidden_layers.set(hidden - {layer} if visible else hidden | {layer})


def _traceable_item(key: str, label_key: str, t: Traceable[float] | None) -> SummaryItem:
    return SummaryItem(
        key=key,
        label=text(label_key),
        value_text=text("shell.sum.no-value") if t is None else format_value(t),
        state=None,
        status=None if t is None else t.status,
        assumed_count=None if t is None else len(t.assumed_inputs),
    )


def _drc_item(outcome: ComputeOutcome) -> SummaryItem:
    state: CheckState | None = None
    value = text("shell.sum-drc.not-run")
    if outcome.drc is not None:
        failures = sum(report.violation_count for report in outcome.drc)
        value = text("shell.sum-drc.pass") if failures == 0 else text("shell.sum-drc.fail", count=failures)
        state = "pass" if failures == 0 else "fail"
    return SummaryItem(
        key="sum-drc", label=text("shell.sum-drc.label"), value_text=value, state=state, status=None, assumed_count=None
    )


def summarise(outcome: ComputeOutcome) -> tuple[SummaryItem, ...]:
    """Return the summary strip: ok, DRC verdict, Ke line peak and R phase with their trust badges."""
    analysis = outcome.analysis
    ok = SummaryItem(
        key="sum-ok",
        label=text("shell.sum-ok.label"),
        value_text=text("shell.sum-ok.pass" if outcome.ok else "shell.sum-ok.fail"),
        state="pass" if outcome.ok else "fail",
        status=None,
        assumed_count=None,
    )
    return (
        ok,
        _drc_item(outcome),
        _traceable_item("sum-ke", "shell.sum-ke.label", analysis.ke_line_peak_v_s_per_rad if analysis else None),
        _traceable_item(
            "sum-r-phase", "shell.sum-r-phase.label", analysis.resistance_phase_operating_ohm if analysis else None
        ),
    )


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


def _marks(layout: Layout) -> Iterator[CoilMark]:
    numbers = _coil_number(layout.paths)
    for layer in layout.copper_layers:
        on_layer = [p for p in layout.paths if p.layer == layer]
        copper = [prim for p in on_layer for prim in p.primitives]
        coils: dict[tuple[Phase, int, int], list[Primitive]] = defaultdict(list)
        for path in on_layer:
            if path.phase is not None and path.element is not None:
                coils[(path.phase, path.element, path.polarity)].extend(path.primitives)
        for (phase, element, polarity), prims in sorted(coils.items()):
            label = f"{phase.value}{numbers[(phase, element)]}{'-' if polarity < 0 else '+'}"
            turns = [p for p in prims if p.role in _TURN_ROLES] or prims
            if layout.topology is TopologyKind.SPIRAL:
                cx, cy, radius = _eye(turns, copper)
            else:
                (cx, cy), radius = prims[0].start_point(), 0.0
            yield CoilMark(layer=layer, phase=phase, label=label, cx_mm=cx, cy_mm=cy, eye_radius_mm=radius)


def geometry_scene(outcome: ComputeOutcome) -> GeometryScene | None:
    """Return what the geometry view draws, or None when no board was built."""
    if outcome.boards is None:
        return None
    boards = outcome.boards.boards
    layers = tuple(dict.fromkeys(layer for board in boards for layer in board.copper_layers))
    return GeometryScene(boards=boards, layers=layers, marks=tuple(mark for board in boards for mark in _marks(board)))


def ready_state(outcome: ComputeOutcome) -> OutcomeReady:
    """Build what the shell shows of an outcome; the worker calls this off the GUI thread."""
    return OutcomeReady(outcome=outcome, summary=summarise(outcome), scene=geometry_scene(outcome))
