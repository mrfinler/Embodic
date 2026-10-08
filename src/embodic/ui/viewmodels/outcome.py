"""What the shell shows of one compute: state machine, summary strip and the drawable geometry. Qt-free.

Every compute request carries a growing id. The worker cancels the run it supersedes, and this view-model drops any
result whose id is not the latest, so a late result can never replace a newer one (latest wins, REQ-N-02).
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal, Protocol, TypeAlias

from embodic.geometry.labels import (
    Box,
    LabelAnchor,
    PlacedLabel,
    TextSize,
    Viewport,
    label_anchors,
    pad_boxes,
    place_labels,
)
from embodic.geometry.layout import Layout
from embodic.geometry.marks import CoilMark, coil_marks, point_primitive_distance_mm, top_layer_of_each_phase
from embodic.io.examples import load_example
from embodic.io.project import ProjectFile, project_from_example, project_provenance, save_project
from embodic.model.design import DesignParameters
from embodic.model.provenance import ProvenanceMap
from embodic.model.vocabulary import Phase
from embodic.outcome import ComputeOutcome
from embodic.results import Traceable
from embodic.results.formatting import format_value
from embodic.results.status import Status
from embodic.ui.strings import text
from embodic.ui.viewmodels.observable import Observable

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
class BoardMarks:
    """What the view draws over one board's copper, from the module the exports use too (ruling a 3, ruling b).

    ``label_of_path`` names the label of each labelled copper path, so a label the placement skips still shows in the
    hover tooltip of its copper.
    """

    name: str  # the phase letter of a per-phase board (screens.md 4.1), "" for a board with every phase
    anchors: tuple[LabelAnchor, ...]  # priority order of embodic.geometry.labels
    coils: tuple[CoilMark, ...]  # every coil on every layer, with its eye disc
    pads: tuple[Box, ...]  # labels keep clear of these
    label_of_path: Mapping[int, str]


@dataclass(frozen=True, slots=True, kw_only=True)
class GeometryScene:
    """Every board of the outcome and the marks drawn over its copper."""

    boards: tuple[Layout, ...]
    layers: tuple[str, ...]  # copper layer names in stack order, each once
    marks: tuple[BoardMarks, ...]  # one per board, in board order


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


def _label_of_path(board: Layout, anchors: tuple[LabelAnchor, ...]) -> dict[int, str]:
    """Return, per copper path, the text of the label anchored on it or, for a spiral eye, inside its innermost turn."""
    layers = top_layer_of_each_phase(board)
    named: dict[int, str] = {}
    for anchor in anchors:
        candidates = [p for p in board.paths if p.phase is anchor.phase and p.layer == layers[anchor.phase]]
        nearest = min(
            candidates,
            key=lambda p: min(point_primitive_distance_mm(anchor.x_mm, anchor.y_mm, q) for q in p.primitives),
        )
        named[nearest.id] = anchor.text
    return named


def _board_name(board: Layout, per_phase: bool) -> str:
    phases = {p.phase for p in board.paths if p.phase is not None}
    return next(iter(phases)).value if per_phase and len(phases) == 1 else ""


def board_marks(board: Layout, per_phase: bool) -> BoardMarks:
    """Return the labels, eye fills and pad boxes of one board; the worker calls this (the eye search is slow)."""
    anchors = label_anchors(board)
    return BoardMarks(
        name=_board_name(board, per_phase),
        anchors=anchors,
        coils=tuple(coil_marks(board)),
        pads=pad_boxes(board),
        label_of_path=_label_of_path(board, anchors),
    )


def eyes_shown(board: Layout, marks: BoardMarks, hidden: frozenset[str]) -> tuple[CoilMark, ...]:
    """Return the eye fills a view draws: those on the top visible layer of each phase.

    With no layer hidden this is `embodic.geometry.marks.eye_marks`, the set the exports fill.
    """
    carried = {(p.layer, p.phase) for p in board.paths if p.phase is not None}
    top: dict[Phase, str] = {}
    for layer in (name for name in board.copper_layers if name not in hidden):
        for phase in Phase:
            if (layer, phase) in carried:
                top.setdefault(phase, layer)
    return tuple(m for m in marks.coils if m.eye_radius_mm > 0 and top.get(m.phase) == m.layer)


def _inside(view: Viewport, x_mm: float, y_mm: float, size_px: tuple[float, float] = (0.0, 0.0)) -> bool:
    half_w, half_h = size_px[0] / 2 / view.px_per_mm, size_px[1] / 2 / view.px_per_mm
    return (
        view.x_min_mm <= x_mm - half_w
        and x_mm + half_w <= view.x_max_mm
        and view.y_min_mm <= y_mm - half_h
        and y_mm + half_h <= view.y_max_mm
    )


def place_in_view(
    anchors: Sequence[LabelAnchor],
    *,
    view: Viewport,
    text_size: TextSize,
    obstacles: Sequence[Box],
    ring_outer_mm: float,
) -> tuple[PlacedLabel, ...]:
    """Place labels so that each phase with copper in view names itself inside the view, at every zoom and pan.

    `place_labels` always places the first label of a phase, moving it outside the ring when its spot is taken; in a
    zoomed or short view that spot can lie beyond the view edge. The first label of each phase is therefore the first
    of its anchors (in ruling b's priority) that lies in view, and the next one is tried while it lands outside. A label
    outside the view is not returned: its copper's tooltip still names it.
    """
    candidates = {
        phase: [a for a in anchors if a.phase is phase and _inside(view, a.x_mm, a.y_mm)]
        for phase in dict.fromkeys(a.phase for a in anchors)
    }
    choice = dict.fromkeys(candidates, 0)
    placed: tuple[PlacedLabel, ...] = ()
    for _ in range(max((len(c) for c in candidates.values()), default=0) or 1):
        firsts = {id(c[choice[phase]]) for phase, c in candidates.items() if c}
        ordered = [replace(a, first_of_phase=True) for a in anchors if id(a) in firsts]
        ordered += [replace(a, first_of_phase=False) for a in anchors if id(a) not in firsts]
        placed = place_labels(ordered, view=view, text_size=text_size, obstacles=obstacles, ring_outer_mm=ring_outer_mm)
        placed = tuple(p for p in placed if _inside(view, p.x_mm, p.y_mm, text_size(p.text)))
        named = {p.phase for p in placed}
        lost = [phase for phase, c in candidates.items() if c and phase not in named and choice[phase] + 1 < len(c)]
        if not lost:
            break
        for phase in lost:
            choice[phase] += 1
    return placed


def geometry_scene(outcome: ComputeOutcome) -> GeometryScene | None:
    """Return what the geometry view draws, or None when no board was built."""
    if outcome.boards is None:
        return None
    boards = outcome.boards.boards
    layers = tuple(dict.fromkeys(layer for board in boards for layer in board.copper_layers))
    per_phase = len(boards) > 1
    return GeometryScene(boards=boards, layers=layers, marks=tuple(board_marks(b, per_phase) for b in boards))


def phases_drawn(boards: Sequence[Layout]) -> tuple[Phase, ...]:
    """Return the phases whose copper the boards carry, in phase order: the rows of the canvas legend."""
    found = {p.phase for board in boards for p in board.paths if p.phase is not None}
    return tuple(phase for phase in Phase if phase in found)


def coil_count(scene: GeometryScene) -> int:
    """Return the number of coils of the scene: one per phase, element and polarity, whatever the layer count."""
    return len(
        {
            (p.phase, p.element, p.polarity)
            for board in scene.boards
            for p in board.paths
            if p.phase is not None and p.element is not None
        }
    )


def ready_state(outcome: ComputeOutcome) -> OutcomeReady:
    """Build what the shell shows of an outcome; the worker calls this off the GUI thread."""
    return OutcomeReady(outcome=outcome, summary=summarise(outcome), scene=geometry_scene(outcome))
