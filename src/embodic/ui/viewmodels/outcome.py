"""What the shell shows of one compute: state machine, summary strip and the drawable geometry. Qt-free.

Every compute request carries a growing id. The worker cancels the run it supersedes, and this view-model drops any
result whose id is not the latest, so a late result can never replace a newer one (latest wins, REQ-N-02).
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal, Protocol, TypeAlias

from embodic.geometry.labels import (
    MINUS,
    Box,
    CopperSpots,
    LabelAnchor,
    PlacedLabel,
    TextSize,
    Viewport,
    copper_reach_mm,
    copper_spots,
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
from embodic.model.vocabulary import Phase, TopologyKind
from embodic.outcome import ComputeOutcome
from embodic.results import Traceable
from embodic.results.formatting import format_value
from embodic.results.status import Status
from embodic.ui.strings import text
from embodic.ui.viewmodels.observable import Observable


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
    status: Status | None  # trust badge from the data (D-007)
    assumed_count: int | None


@dataclass(frozen=True, slots=True, kw_only=True)
class BoardMarks:
    """What the view draws over one board's copper, from the module the exports use too (ruling a 3, ruling b).

    ``label_of_path`` names the label of each labelled copper path, so a label the placement skips still shows in the
    hover tooltip of its copper.
    """

    anchors: tuple[LabelAnchor, ...]  # priority order of embodic.geometry.labels
    coils: tuple[CoilMark, ...]  # every coil on every layer, with its eye disc
    pads: tuple[Box, ...]  # labels keep clear of these
    label_of_path: Mapping[int, str]
    copper: CopperSpots  # where a label may move when its anchor or leader would leave the view
    copper_reach_mm: float  # how far drawn copper reaches past its nearest copper spot


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
        self.board: Observable[int | None] = Observable(None)  # board picker: None is "All boards" (screens.md 4.1)

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
        if self.board.value is not None and self.board.value >= len(board_letters(ready.scene)):
            self.board.set(None)
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

    def _scene(self) -> GeometryScene | None:
        ready = shown_result(self.state.value)
        return None if ready is None else ready.scene

    def select_board(self, index: int | None) -> None:
        """Pick the board the canvas draws, or None for all boards; a design with one board always draws it."""
        count = len(board_letters(self._scene()))
        self.board.set(index if index is not None and index < count else None)

    def step_board(self, delta: int) -> None:
        """Page Up and Page Down on the canvas: the previous or next picker item, stopping at the ends."""
        count = len(board_letters(self._scene()))
        if count:
            picked = -1 if self.board.value is None else self.board.value  # -1 is the item "All boards"
            picked = min(max(picked + delta, -1), count - 1)
            self.select_board(None if picked < 0 else picked)

    def step_layer_solo(self, delta: int) -> None:
        """`[` and `]` on the canvas: solo the previous or next layer of the drawn boards; all layers lie between."""
        scene = self._scene()
        if scene is None:
            return
        layers = scene_of_board(scene, self.board.value).layers
        visible = [layer for layer in layers if layer not in self.hidden_layers.value]
        stops = [None, *layers]
        here = stops.index(visible[0]) if len(visible) == 1 and len(layers) > 1 else 0
        solo = stops[(here + delta) % len(stops)]
        self.hidden_layers.set(frozenset() if solo is None else frozenset(scene.layers) - {solo})


def _traceable_item(key: str, label_key: str, t: Traceable[float] | None) -> SummaryItem:
    return SummaryItem(
        key=key,
        label=text(label_key),
        value_text=text("shell.sum.no-value") if t is None else format_value(t),
        status=None if t is None else t.status,
        assumed_count=None if t is None else len(t.assumed_inputs),
    )


def summarise(outcome: ComputeOutcome) -> tuple[SummaryItem, ...]:
    """Return the summary strip: Ke line peak and R phase with their trust badges."""
    analysis = outcome.analysis
    return (
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


def board_marks(board: Layout) -> BoardMarks:
    """Return the labels, eye fills and pad boxes of one board; the worker calls this (the eye search is slow)."""
    anchors = label_anchors(board)
    return BoardMarks(
        anchors=anchors,
        coils=tuple(coil_marks(board)),
        pads=pad_boxes(board),
        label_of_path=_label_of_path(board, anchors),
        copper=copper_spots(board),
        copper_reach_mm=copper_reach_mm(board),
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


def _group(anchor: LabelAnchor) -> tuple[Phase, str]:
    """Return the phase and sign a label names; serpentine labels have no sign."""
    sign = anchor.text[-1] if anchor.text[-1] in ("+", MINUS) else ""
    return anchor.phase, sign


def place_in_view(
    anchors: Sequence[LabelAnchor],
    *,
    view: Viewport,
    text_size: TextSize,
    obstacles: Sequence[Box],
    ring_outer_mm: float,
    copper: CopperSpots,
    copper_reach_mm: float,
) -> tuple[PlacedLabel, ...]:
    """Place labels so that each phase with copper in view names itself inside the view, at every zoom and pan.

    The forced label of each phase and sign is its first anchor in view, so a zoomed view names the copper it shows.
    A group with no anchor in view keeps its own forced label, which `place_labels` moves onto the phase's copper in
    view; `place_labels` also names a phase that shows copper but no anchor (U-S4e ruling h).
    """
    seen = [a for a in anchors if _inside(view, a.x_mm, a.y_mm)]
    groups = {_group(a) for a in seen}
    firsts = {id(next(a for a in seen if _group(a) == group)) for group in groups}
    forced = [replace(a, forced=True) for a in seen if id(a) in firsts]
    forced += [a for a in anchors if a.forced and _group(a) not in groups]
    rest = [
        replace(a, forced=False) for a in anchors if id(a) not in firsts and not (a.forced and _group(a) not in groups)
    ]
    return place_labels(
        forced + rest,
        view=view,
        text_size=text_size,
        obstacles=obstacles,
        ring_outer_mm=ring_outer_mm,
        copper=copper,
        copper_reach_mm=copper_reach_mm,
    )


def _layers_of(boards: Sequence[Layout]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(layer for board in boards for layer in board.copper_layers))


def geometry_scene(outcome: ComputeOutcome) -> GeometryScene | None:
    """Return what the geometry view draws, or None when no board was built."""
    if outcome.boards is None:
        return None
    boards = outcome.boards.boards
    return GeometryScene(boards=boards, layers=_layers_of(boards), marks=tuple(board_marks(board) for board in boards))


def board_letters(scene: GeometryScene | None) -> tuple[Phase, ...]:
    """Return the phase letter of each board when the design has more than one, else ().

    Board k of a per-phase stack holds phase k (interfaces.md section 5), so the letters are the first phases.
    """
    return () if scene is None or len(scene.boards) < 2 else tuple(Phase)[: len(scene.boards)]


def scene_of_board(scene: GeometryScene, board: int | None) -> GeometryScene:
    """Return what the canvas draws for a picker choice: every board, or board ``board`` alone (screens.md 4.1)."""
    if board is None:
        return scene
    boards = (scene.boards[board],)
    return GeometryScene(boards=boards, layers=_layers_of(boards), marks=(scene.marks[board],))


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


def counts_text(scene: GeometryScene, topology: TopologyKind) -> str:
    """Return `st-counts`: layers, then coils for spiral or phases otherwise, then vias; a stack counts its boards."""
    vias = sum(len(board.vias) for board in scene.boards)
    phases = len({p.phase for board in scene.boards for p in board.paths if p.phase is not None})
    if len(scene.boards) > 1:
        return text(
            "shell.st-counts.stack", boards=len(scene.boards), layers=len(scene.layers), phases=phases, vias=vias
        )
    if topology is TopologyKind.SPIRAL:
        return text("shell.st-counts.spiral", layers=len(scene.layers), coils=coil_count(scene), vias=vias)
    return text("shell.st-counts.phases", layers=len(scene.layers), phases=phases, vias=vias)


def ready_state(outcome: ComputeOutcome) -> OutcomeReady:
    """Build what the shell shows of an outcome; the worker calls this off the GUI thread."""
    return OutcomeReady(outcome=outcome, summary=summarise(outcome), scene=geometry_scene(outcome))
