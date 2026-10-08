"""The open design as a state machine (interfaces.md section 11): empty, drafting, computed. Qt-free.

One `SessionDocument` holds everything a design hash and a provenance map derive from: the draft values, the origin
example and the measurements. Every edit replaces the document, and the undo history stores whole documents, so undo
restores the identical hash and provenance by construction (UT-SES-02). The state is derived from the document by
`parse_draft`; nothing computes until it returns a design (REQ-F-36).

Computes go through the shell's `OutcomeViewModel` (U-M4b), which owns the worker requests and drops superseded
results. This view-model keeps the last outcome that drew a board, so an incomplete or invalid edit leaves that drawing
on screen marked outdated (REQ-F-27).
"""

import dataclasses
import logging
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeAlias

from embodic.errors import Suggestion, ValidationIssue
from embodic.geometry.details import SerpentineDetail, SpiralDetail, WaveDetail
from embodic.io.examples import list_examples, packaged_example
from embodic.io.examples import load_example as load_packaged_example
from embodic.io.project import LoadedDraft, ProjectFile, load_project, project_provenance, save_project
from embodic.model.design import DesignParameters
from embodic.model.draft import DesignDraft, DraftIncomplete, blank_draft, derive_layer_pairs, draft_from_design
from embodic.model.draft import parse_draft as parse
from embodic.model.fields import FIELD_BY_KEY, FieldGroup, FieldKind, FieldSpec, field_for, field_specs
from embodic.model.provenance import (
    DefaultValue,
    ExampleRef,
    ExampleValue,
    FieldProvenance,
    MeasuredValue,
    Measurement,
    UserValue,
)
from embodic.model.provenance import mark_measured as mark_design_measured
from embodic.model.schema import JsonValue, ValueType, flatten, pattern_of, to_json
from embodic.model.stackup import generate_even_stackup
from embodic.model.validate import issue, validate_design
from embodic.model.vocabulary import TopologyKind
from embodic.outcome import ComputeOutcome
from embodic.ui.strings import text
from embodic.ui.viewmodels.observable import Observable
from embodic.ui.viewmodels.outcome import OutcomeReady, OutcomeState, OutcomeViewModel, shown_result
from embodic.units import MM_PER_COPPER_OZ, Unit, copper_oz_to_mm, deg_to_rad, rad_to_deg

logger = logging.getLogger(__name__)

UNDO_LIMIT = 50
AUTOSAVE_NAME = "autosave.embodic.json"
STACKUP_POINTER = "/stackup/layers"
BORE_POINTER = "/outline/bore"
ASSIGNMENT_POINTER = "/winding/assignment"


@dataclass(frozen=True, slots=True, kw_only=True)
class SessionEmpty:
    """App start: no design open. The New design dialog and the Examples gallery are offered (D-014)."""

    state: Literal["empty"] = "empty"


@dataclass(frozen=True, slots=True, kw_only=True)
class SessionDrafting:
    """Required fields missing: form editable, nothing computed, results area shows the missing list."""

    state: Literal["drafting"] = "drafting"
    draft: DesignDraft
    missing: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class SessionComputed:
    """A complete design. `outcome` is None while the first compute runs; `stale` marks a kept last valid layout."""

    state: Literal["computed"] = "computed"
    design: DesignParameters
    provenance: Mapping[str, FieldProvenance]
    outcome: ComputeOutcome | None
    stale: bool
    computing: bool


SessionState: TypeAlias = SessionEmpty | SessionDrafting | SessionComputed


@dataclass(frozen=True, slots=True, kw_only=True)
class SessionDocument:
    """One undoable state of the open design: what its hash and provenance derive from."""

    draft: DesignDraft
    origin: ExampleRef | None
    measurements: tuple[Measurement, ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class EditNotice:
    """The inline notice of an applied suggestion (REQ-F-23); it hides at the next change."""

    pointer: str
    text: str


@dataclass(frozen=True, slots=True, kw_only=True)
class StackupInputs:
    """The three inputs of the stack-up generator (screens.md section 4, R3); None while not entered."""

    copper_count: int | None = None
    copper_oz: float | None = None
    board_thickness_mm: float | None = None


# Inspector tab of each form group; groups without an inspector widget (name, materials, analysis) are absent.
TAB_OF_GROUP: Mapping[FieldGroup, str] = {
    FieldGroup.COIL: "tab-coil",
    FieldGroup.PHASES: "tab-phases",
    FieldGroup.LAYERS: "tab-layers",
    FieldGroup.STACKUP: "tab-layers",
    FieldGroup.OUTLINE: "tab-board",
    FieldGroup.FASTENERS: "tab-board",
    FieldGroup.ROTOR: "tab-board",
    FieldGroup.OPERATING: "tab-board",
    FieldGroup.DRIVE: "tab-board",
    FieldGroup.COOLING: "tab-board",
    FieldGroup.MANUFACTURING: "tab-board",
}
TAB_OF_WIDGET: Mapping[str, str] = {"param-poles": "tab-coil"}  # screens.md section 2 places the pole count there
_SCALAR_TYPES = frozenset({ValueType.INT, ValueType.FLOAT, ValueType.BOOL, ValueType.TEXT, ValueType.CHOICE})


@dataclass(frozen=True, slots=True, kw_only=True)
class OptionRule:
    """A field that a sibling option hides or disables (screens.md state rules, REQ-F-32)."""

    widget_id: str
    topologies: frozenset[TopologyKind]
    pointer: str  # the option it depends on
    values: frozenset[JsonValue]  # option values that trigger the effect
    effect: Literal["hide", "disable"]
    hint_key: str | None = None


_ALL = frozenset(TopologyKind)
OPTION_RULES: tuple[OptionRule, ...] = (
    OptionRule(
        widget_id="param-phase-count",
        topologies=frozenset({TopologyKind.SPIRAL}),
        pointer="/winding/kind",
        values=frozenset(),
        effect="hide",
    ),
    OptionRule(
        widget_id="param-corner-radius",
        topologies=frozenset({TopologyKind.SPIRAL}),
        pointer="/winding/coil/end_style",
        values=frozenset({"straight"}),
        effect="disable",
        hint_key="design.hint.straight-ends",
    ),
    OptionRule(
        widget_id="param-corner-radius",
        topologies=frozenset({TopologyKind.SERPENTINE}),
        pointer="/winding/fillet_max",
        values=frozenset({True}),
        effect="hide",
    ),
    OptionRule(
        widget_id="param-board-gap",
        topologies=frozenset({TopologyKind.SERPENTINE}),
        pointer="/winding/stack_mode",
        values=frozenset({"single"}),
        effect="disable",
        hint_key="design.hint.board-gap",
    ),
    OptionRule(
        widget_id="param-layer-order",
        topologies=frozenset({TopologyKind.SERPENTINE}),
        pointer="/winding/stack_mode",
        values=frozenset({"one_board_per_phase"}),
        effect="disable",
        hint_key="design.hint.layer-order",
    ),
)
_STATIC_HINTS: Mapping[tuple[str, TopologyKind | None], str] = {
    ("param-terminal-drill", None): "design.hint.terminal-drill",
    ("param-turns", TopologyKind.SPIRAL): "design.hint.turns-maximum",
}


@dataclass(frozen=True, slots=True, kw_only=True)
class FieldRow:
    """What one inspector input shows: binding, applicability, value, provenance chip and message."""

    widget_id: str
    tab: str
    spec: FieldSpec
    visible: bool
    enabled: bool
    present: bool  # False = missing (required) or absent (optional at its default)
    value: JsonValue
    provenance: FieldProvenance | None
    issue: ValidationIssue | None
    hint: str

    @property
    def pointer(self) -> str:
        """Return the concrete pointer the input writes."""
        return self.spec.pointer


def is_inspector_input(spec: FieldSpec) -> bool:
    """Return True for a field the inspector edits with its own scalar widget (tables and helpers aside)."""
    return (
        spec.widget_id is not None
        and spec.group in TAB_OF_GROUP
        and spec.value_type in _SCALAR_TYPES
        and "*" not in spec.pointer
        and not spec.pointer.startswith(BORE_POINTER)
    )


def bore_widget_id(spec: FieldSpec) -> str:
    """Return the objectName of one bore input ("/outline/bore/across_flats_mm" -> "param-bore-across-flats")."""
    leaf = spec.pointer.rsplit("/", 1)[1].removesuffix("_mm").removesuffix("_rad")
    return f"param-bore-{leaf.replace('_', '-')}"


def _tag_value(spec: FieldSpec, values: Mapping[str, JsonValue]) -> JsonValue:
    parent = spec.pointer.rsplit("/", 1)[0]
    for tag in ("kind", "shape"):
        if f"{parent}/{tag}" in FIELD_BY_KEY:
            return values.get(f"{parent}/{tag}")
    return None


def current_value(values: Mapping[str, JsonValue], pointer: str, topology: TopologyKind) -> JsonValue:
    """Return a draft value, or the neutral value an absent optional field falls back to."""
    if pointer == "/winding/kind":
        return topology.value
    if pointer in values:
        return values[pointer]
    spec = FIELD_BY_KEY.get(pattern_of(pointer))
    return None if spec is None else spec.neutral_value


def _rule_applies(rule: OptionRule, topology: TopologyKind, values: Mapping[str, JsonValue]) -> bool:
    if topology not in rule.topologies:
        return False
    return not rule.values or current_value(values, rule.pointer, topology) in rule.values


def _first_issue(pointer: str, issues: tuple[ValidationIssue, ...]) -> ValidationIssue | None:
    return next((found for found in issues if pointer in found.pointers), None)


def _row(
    spec: FieldSpec,
    widget_id: str,
    visible: bool,
    draft: DesignDraft,
    chips: Mapping[str, FieldProvenance],
    issues: tuple[ValidationIssue, ...],
) -> FieldRow:
    topology, values = draft.topology, draft.values
    enabled, hint = True, ""
    for rule in OPTION_RULES:
        if rule.widget_id == widget_id and _rule_applies(rule, topology, values):
            visible = visible and rule.effect != "hide"
            enabled = rule.effect != "disable"
            hint = text(rule.hint_key) if rule.hint_key else ""
    static = _STATIC_HINTS.get((widget_id, topology)) or _STATIC_HINTS.get((widget_id, None))
    present = spec.pointer in values
    provenance = chips.get(spec.pointer)
    if not present and not spec.required:
        provenance = DefaultValue()
    return FieldRow(
        widget_id=widget_id,
        tab=TAB_OF_WIDGET.get(widget_id, TAB_OF_GROUP.get(spec.group, "")),
        spec=spec,
        visible=visible,
        enabled=enabled,
        present=present,
        value=current_value(values, spec.pointer, topology),
        provenance=provenance,
        issue=_first_issue(spec.pointer, issues),
        hint=hint or (text(static) if static else ""),
    )


def form_rows(
    draft: DesignDraft, chips: Mapping[str, FieldProvenance], issues: tuple[ValidationIssue, ...]
) -> tuple[FieldRow, ...]:
    """Return one row per inspector input of the draft's topology, in form order (REQ-F-32).

    A widget shared by two union members (board radius or across flats) binds to the member the tag selects. The bore
    rows follow the bore choice: none hides them all.
    """
    rows: dict[str, FieldRow] = {}
    values = draft.values
    bore = values.get(BORE_POINTER, {}) if BORE_POINTER in values else {}
    for spec in field_specs(draft.topology):
        if spec.pointer.startswith(BORE_POINTER + "/") and spec.pointer != f"{BORE_POINTER}/shape":
            widget_id = bore_widget_id(spec)
            chosen = bore is not None and values.get(f"{BORE_POINTER}/shape") == spec.variant
            rows[widget_id] = _row(spec, widget_id, chosen, draft, chips, issues)
            continue
        if not is_inspector_input(spec):
            continue
        assert spec.widget_id is not None
        applies = spec.variant is None or _tag_value(spec, values) == spec.variant
        if spec.widget_id in rows and rows[spec.widget_id].visible and not applies:
            continue
        rows[spec.widget_id] = _row(spec, spec.widget_id, applies, draft, chips, issues)
    return tuple(rows.values())


def bore_choice(values: Mapping[str, JsonValue]) -> str | None:
    """Return "none", "circle", "polygon", or None while the bore is not chosen yet."""
    if values.get(BORE_POINTER, "") is None:
        return "none"
    shape = values.get(f"{BORE_POINTER}/shape")
    return shape if isinstance(shape, str) else None


def widget_for_pointer(pointer: str, draft: DesignDraft) -> str | None:
    """Return the objectName that fills a pointer: what "Go to first missing field" and issue links focus."""
    if pointer.startswith((STACKUP_POINTER, "/winding/layers/")):  # spiral pairs derive from the copper count (D-024)
        return "param-wave-layers" if draft.topology is TopologyKind.WAVE else "param-layer-count"
    if pointer in (BORE_POINTER, f"{BORE_POINTER}/shape"):
        return "param-bore"
    try:
        spec = field_for(pointer, draft.values)
    except KeyError:
        return None
    if pointer.startswith(BORE_POINTER + "/"):
        return bore_widget_id(spec)
    return spec.widget_id


def tab_of_widget(widget_id: str, topology: TopologyKind) -> str:
    """Return the inspector tab that holds a widget."""
    helpers = {
        "param-layer-count": "tab-layers",
        "param-wave-layers": "tab-layers",
        "layer-list": "tab-layers",
        "param-copper-weight": "tab-board",
        "param-board-thickness": "tab-board",
        "param-bore": "tab-board",
        "param-phase-assign-mode": "tab-phases",
    }
    if widget_id in helpers or widget_id.startswith("param-bore-"):
        return helpers.get(widget_id, "tab-board")
    if widget_id in TAB_OF_WIDGET:
        return TAB_OF_WIDGET[widget_id]
    spec = next((s for s in field_specs(topology) if s.widget_id == widget_id), None)
    return "" if spec is None else TAB_OF_GROUP.get(spec.group, "")


def display_text(spec: FieldSpec, value: JsonValue) -> str:
    """Return a value as the form shows it: angles in degrees, floats to 12 significant digits, None empty."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, float | int) and spec.value_type is ValueType.FLOAT:
        number = rad_to_deg(value) if spec.unit is Unit.RAD else value
        return f"{number:.12g}"
    return str(value)


def parse_text(spec: FieldSpec, typed: str) -> JsonValue:
    """Parse form text into a draft value; text that is no number stays text so validation reports it (R14)."""
    stripped = typed.strip()
    if not stripped:
        return None
    if spec.value_type is ValueType.FLOAT:
        try:
            number = float(stripped)
        except ValueError:
            return stripped
        return deg_to_rad(number) if spec.unit is Unit.RAD else number
    if spec.value_type is ValueType.INT:
        for convert in (int, float):
            try:
                return convert(stripped)
            except ValueError:
                continue
        return stripped
    return stripped


def _measurable(spec: FieldSpec) -> bool:
    return spec.kind is FieldKind.PROPERTY and spec.value_type is ValueType.FLOAT


def draft_chips(document: SessionDocument, origin_design: DesignParameters | None) -> dict[str, FieldProvenance]:
    """Return the provenance of every draft value by the rules of interfaces.md section 2.4.

    `derive_provenance` takes a complete design; a draft needs the same four rules over its values. For a complete
    draft the result equals `project_provenance` (tests/unit/ui/session checks it), including its rule that an origin
    no longer packaged gives `user` instead of `default`.
    """
    values = document.draft.values
    origin_values = draft_from_design(origin_design).values if origin_design is not None else {}
    sources = {m.pointer: m.source for m in document.measurements}
    blank_origin = document.origin is None
    chips: dict[str, FieldProvenance] = {}
    for pointer, value in values.items():
        spec = field_for(pointer, values)
        if pointer in sources and _measurable(spec):
            chips[pointer] = MeasuredValue(source=sources[pointer])
        elif document.origin is not None and pointer in origin_values and origin_values[pointer] == value:
            chips[pointer] = ExampleValue(example_id=document.origin.example_id)
        elif blank_origin and not spec.required and value == spec.neutral_value:
            chips[pointer] = DefaultValue()
        else:
            chips[pointer] = UserValue()
    return chips


def _with_value(values: Mapping[str, JsonValue], pointer: str, value: JsonValue) -> dict[str, JsonValue]:
    """Replace a pointer's value or subtree; None empties a field that cannot hold null (it becomes missing)."""
    kept = {p: v for p, v in values.items() if p != pointer and not p.startswith(pointer + "/")}
    try:
        nullable = field_for(pointer, values).nullable
    except KeyError:
        nullable = False
    if value is None and not nullable:
        return kept
    return kept | flatten(value, pointer)


def stackup_from_values(values: Mapping[str, JsonValue]) -> StackupInputs:
    """Read the generator inputs back from a stack-up: copper count, copper weight and total thickness."""
    copper: list[float] = []
    total = 0.0
    position = 0
    while (kind := values.get(f"{STACKUP_POINTER}/{position}/kind")) is not None:
        thickness = values.get(f"{STACKUP_POINTER}/{position}/thickness_mm")
        if isinstance(thickness, int | float):
            total += thickness
            if kind == "copper":
                copper.append(thickness)
        position += 1
    if not copper:
        return StackupInputs()
    return StackupInputs(
        copper_count=len(copper), copper_oz=copper[0] / MM_PER_COPPER_OZ, board_thickness_mm=round(total, 9)
    )


def feasibility_hints(outcome: ComputeOutcome) -> dict[str, str]:
    """Return the hint texts next to the inputs, from the generator record of the first board (REQ-F-28)."""
    if outcome.boards is None or not outcome.boards.boards:
        return {}
    detail = outcome.boards.boards[0].detail
    match detail:
        case SpiralDetail(plan=plan, turns_achieved=turns, turn_limit=limit):
            f = plan.feasibility
            combination = (
                text("hint-combination.balanced", q=str(f.q), t=f.periodicity)
                if f.balanced
                else text("hint-combination.unbalanced", coils=f.coils, poles=f.poles)
            )
            return {
                "hint-combination": combination,
                "param-turns-hint": text("hint-turns.spiral", turns=turns, reason=limit.limiting_reason.value),
                "phase-pattern-string": plan.pattern,
            }
        case SerpentineDetail(max_turns_that_fit=turns):
            return {"param-turns-hint": text("hint-turns.serpentine", turns=turns)}
        case WaveDetail(tracks_per_layer=tracks):
            return {"param-turns-hint": text("hint-turns.wave", tracks=tracks)}
    return {}


def example_title(example_id: str) -> str:
    """Return the gallery title of a packaged example, or its id when it is no longer packaged."""
    return next((info.title for info in list_examples() if info.example_id == example_id), example_id)


class DesignSession:
    """Implements DesignSessionViewModel (interfaces.md section 11). Every command returns at once."""

    def __init__(self, outcome: OutcomeViewModel, autosave_path: Path | None = None) -> None:
        self._outcome = outcome
        self._autosave_path = autosave_path
        self.state: Observable[SessionState] = Observable(SessionEmpty())
        self.can_undo: Observable[bool] = Observable(False)
        self.can_redo: Observable[bool] = Observable(False)
        self.notice: Observable[EditNotice | None] = Observable(None)
        self.issues: Observable[tuple[ValidationIssue, ...]] = Observable(())
        self.document: SessionDocument | None = None
        self._undo: list[SessionDocument | None] = []
        self._redo: list[SessionDocument | None] = []
        self._drawn: OutcomeReady | None = None
        self._origins: dict[ExampleRef, DesignParameters | None] = {}
        self._stackup_pending = StackupInputs()
        outcome.state.subscribe(self._on_outcome)

    def new_design(self, topology: TopologyKind) -> None:
        """Open a blank draft: required fields missing, optional fields at their neutral value (D-014)."""
        self._commit(SessionDocument(draft=blank_draft(topology), origin=None))

    def load_example(self, example_id: str) -> None:
        """Open a packaged example as a new design whose fields carry `example` provenance (REQ-F-38)."""
        ref, design = load_packaged_example(example_id)
        self._origins[ref] = design
        self._commit(SessionDocument(draft=draft_from_design(design), origin=ref))

    def open_project(self, path: Path) -> tuple[ValidationIssue, ...]:
        """Open a project file, complete or a draft; return its load issues."""
        loaded, issues = load_project(path)
        if loaded is None:
            return issues
        draft = draft_from_design(loaded.design) if isinstance(loaded, ProjectFile) else loaded.draft
        self._commit(SessionDocument(draft=draft, origin=loaded.origin, measurements=loaded.measurements))
        return issues

    def save_project(self, path: Path) -> str:
        """Write the open design or draft; return its design hash ('' for a draft)."""
        project = self._project()
        if project is None:
            raise RuntimeError("no design is open")
        return save_project(path, project)

    def edit(self, pointer: str, value: JsonValue) -> None:
        """Set a value; re-entering the current value is a no-op (no undo entry, no recompute, PR-12)."""
        document = self.document
        if document is None:
            return
        draft = DesignDraft(topology=document.draft.topology, values=_with_value(document.draft.values, pointer, value))
        if pointer.startswith(STACKUP_POINTER):
            draft = derive_layer_pairs(draft)
        if draft.values == document.draft.values:
            return
        old, new = document.draft.values, draft.values
        measurements = tuple(
            m for m in document.measurements if m.pointer in new and new[m.pointer] == old.get(m.pointer)
        )
        self._commit(dataclasses.replace(document, draft=draft, measurements=measurements))

    def set_topology(self, topology: TopologyKind) -> None:
        """Switch the topology; values typed for another topology stay in the draft and come back on a switch back."""
        document = self.document
        if document is None or document.draft.topology is topology:
            return
        values = {**blank_draft(topology).values, **document.draft.values}
        self._commit(dataclasses.replace(document, draft=DesignDraft(topology=topology, values=values)))

    def mark_measured(self, pointer: str, source: str) -> ValidationIssue | None:
        """Mark a property field measured with its source, or return why not (D-007)."""
        document = self.document
        if document is None:
            return issue("INVALID_MEASURED_DESIGN_FIELD", [pointer])
        parsed = parse(document.draft)
        if isinstance(parsed, DesignParameters):
            result = mark_design_measured(parsed, document.measurements, pointer, source)
        elif not source.strip():
            result = issue("INVALID_MEASURED_SOURCE_EMPTY", [pointer])
        elif pointer not in document.draft.values or not _measurable(field_for(pointer, document.draft.values)):
            result = issue("INVALID_MEASURED_DESIGN_FIELD", [pointer])
        else:
            kept = tuple(m for m in document.measurements if m.pointer != pointer)
            result = (*kept, Measurement(pointer=pointer, source=source.strip()))
        if isinstance(result, ValidationIssue):
            return result
        if result != document.measurements:
            self._commit(dataclasses.replace(document, measurements=result))
        return None

    def apply_suggestion(self, suggestion: Suggestion) -> None:
        """Apply with an inline notice 'Changed from X to Y: reason' and an Undo entry (REQ-F-23)."""
        document = self.document
        if document is None:
            return
        spec = field_for(suggestion.pointer, document.draft.values)
        old = document.draft.values.get(suggestion.pointer)
        self.edit(suggestion.pointer, suggestion.proposed_value)
        if self.document is document:
            return
        empty = text("design.notice.empty-value")
        notice = text(
            "design.notice.changed",
            old=display_text(spec, old) or empty,
            new=display_text(spec, suggestion.proposed_value),
            reason=suggestion.reason,
        )
        self.notice.set(EditNotice(pointer=suggestion.pointer, text=notice))

    def undo(self) -> None:
        """Restore the document before the last change."""
        if self._undo:
            self._redo.append(self.document)
            self._commit(self._undo.pop(), record=False)

    def redo(self) -> None:
        """Restore the document the last undo left."""
        if self._redo:
            self._undo.append(self.document)
            self._commit(self._redo.pop(), record=False)

    def compute_now(self) -> None:
        """Compute the open design again; does nothing while the design is incomplete."""
        project = self._project()
        if isinstance(project, ProjectFile):
            self._outcome.open_project(project)

    def stackup_inputs(self) -> StackupInputs:
        """Return the stack-up generator inputs: read back from the stack-up, overlaid with the ones being entered."""
        if self.document is None:
            return StackupInputs()
        derived = stackup_from_values(self.document.draft.values)
        pending = self._stackup_pending
        return StackupInputs(
            copper_count=pending.copper_count if pending.copper_count is not None else derived.copper_count,
            copper_oz=pending.copper_oz if pending.copper_oz is not None else derived.copper_oz,
            board_thickness_mm=pending.board_thickness_mm
            if pending.board_thickness_mm is not None
            else derived.board_thickness_mm,
        )

    def set_stackup_input(self, **change: float | int | None) -> None:
        """Enter one generator input; once all three hold a value, write `/stackup/layers` as one undoable edit."""
        self._stackup_pending = dataclasses.replace(self._stackup_pending, **change)
        inputs = self.stackup_inputs()
        if inputs.copper_count is None or inputs.copper_oz is None or inputs.board_thickness_mm is None:
            return
        stackup = generate_even_stackup(
            inputs.copper_count, copper_oz_to_mm(inputs.copper_oz), inputs.board_thickness_mm
        )
        data = to_json(stackup)
        assert isinstance(data, dict)
        self._stackup_pending = StackupInputs()
        self.edit(STACKUP_POINTER, data["layers"])

    def chips(self) -> Mapping[str, FieldProvenance]:
        """Return the provenance chip of every value the open design holds."""
        state = self.state.value
        if isinstance(state, SessionComputed):
            return state.provenance
        if self.document is None:
            return {}
        return draft_chips(self.document, self._origin_design(self.document.origin))

    def rows(self) -> tuple[FieldRow, ...]:
        """Return the inspector rows of the open design."""
        if self.document is None:
            return ()
        return form_rows(self.document.draft, self.chips(), self.issues.value)

    def drawn(self, latest: OutcomeState) -> tuple[OutcomeReady | None, bool]:
        """Return the result the canvas draws and whether it is outdated (REQ-F-27).

        Without an open document the shell shows its own latest result (projects opened by the shell directly).
        """
        state = self.state.value
        if isinstance(state, SessionEmpty):
            return shown_result(latest), False
        if isinstance(state, SessionDrafting):
            return self._drawn, self._drawn is not None
        return self._drawn or shown_result(latest), state.stale and not state.computing

    def title(self) -> str:
        """Return the window title: the design name, with the example it came from (screens.md section 1)."""
        if self.document is None:
            return text("shell.window.title")
        name = str(self.document.draft.values.get("/name") or "")
        origin = self.document.origin
        if origin is None:
            return text("design.window.title", name=name)
        return text("design.window.title-example", name=name, example=example_title(origin.example_id))

    def has_user_values(self) -> bool:
        """Return True when the open design holds a value the user typed (the New design dialog asks first)."""
        return any(isinstance(chip, UserValue | MeasuredValue) for chip in self.chips().values())

    def discard_autosave(self) -> None:
        """Remove the autosave file after a clean exit, so the next start offers no recovery."""
        if self._autosave_path is not None:
            self._autosave_path.unlink(missing_ok=True)

    def _origin_design(self, origin: ExampleRef | None) -> DesignParameters | None:
        if origin is None:
            return None
        if origin not in self._origins:
            self._origins[origin] = packaged_example(origin)
        return self._origins[origin]

    def _project(self) -> ProjectFile | LoadedDraft | None:
        document = self.document
        if document is None:
            return None
        parsed = parse(document.draft)
        if isinstance(parsed, DesignParameters):
            return ProjectFile(design=parsed, origin=document.origin, measurements=document.measurements)
        return LoadedDraft(draft=document.draft, origin=document.origin, measurements=document.measurements)

    def _commit(self, document: SessionDocument | None, *, record: bool = True) -> None:
        if record:
            self._undo = [*self._undo, self.document][-UNDO_LIMIT:]
            self._redo = []
        if document is None or self.document is None or document.draft.topology is not self.document.draft.topology:
            self._stackup_pending = StackupInputs()
        self.document = document
        self.notice.set(None)
        self.can_undo.set(bool(self._undo))
        self.can_redo.set(bool(self._redo))
        self._refresh()
        self._autosave()

    def _refresh(self) -> None:
        document = self.document
        if document is None:
            self.issues.set(())
            self.state.set(SessionEmpty())
            return
        parsed = parse(document.draft)
        if isinstance(parsed, DraftIncomplete):
            self.issues.set(parsed.issues)
            self.state.set(SessionDrafting(draft=document.draft, missing=parsed.missing))
            return
        project = ProjectFile(design=parsed, origin=document.origin, measurements=document.measurements)
        provenance = project_provenance(project)
        current = self.state.value
        if isinstance(current, SessionComputed) and (current.design, current.provenance) == (parsed, provenance):
            return
        self.issues.set(validate_design(parsed))
        kept = self._drawn.outcome if self._drawn is not None else None
        self.state.set(
            SessionComputed(design=parsed, provenance=provenance, outcome=kept, stale=kept is not None, computing=True)
        )
        self._outcome.open_project(project)

    def _on_outcome(self, latest: OutcomeState) -> None:
        ready = latest if isinstance(latest, OutcomeReady) else None
        if ready is not None and ready.scene is not None:
            self._drawn = ready
        state = self.state.value
        if not isinstance(state, SessionComputed):
            return
        if ready is None:
            computing = latest.state == "computing"
            self.state.set(dataclasses.replace(state, computing=computing))
            return
        if ready.outcome.design != state.design:
            return
        self.issues.set(ready.outcome.issues)
        if ready.scene is not None:
            self.state.set(dataclasses.replace(state, outcome=ready.outcome, stale=False, computing=False))
            return
        kept = self._drawn.outcome if self._drawn is not None else ready.outcome
        self.state.set(dataclasses.replace(state, outcome=kept, stale=self._drawn is not None, computing=False))

    def _autosave(self) -> None:
        path = self._autosave_path
        if path is None:
            return
        if self.document is None:
            path.unlink(missing_ok=True)
            return
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            self.save_project(path)
        except OSError:
            logger.warning("autosave to the recovery folder failed", exc_info=True)
