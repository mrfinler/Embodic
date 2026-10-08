"""The compute facade: validate, plan and generate, check each board, analyse (interfaces.md section 10).

A failure the user can cause comes back as issues. An exception inside a stage is a programming error; it becomes an
INTERNAL_<STAGE>_FAILED issue whose `value` holds the traceback, and the stages that need its product do not run.
"""

import dataclasses
import hashlib
import platform
import time
import traceback
from collections import OrderedDict
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import Literal, TypeVar

import numpy as np

import embodic
from embodic.drc import CancelToken, DrcReport, run_drc
from embodic.errors import IssueCategory, Severity, Unbuildable, ValidationIssue, message_for
from embodic.generators import build_layout
from embodic.geometry.layout import BoardStack, Layout
from embodic.io.canonical import design_document, design_hash, dumps_canonical, file_pointer
from embodic.io.migrations import PROJECT_SCHEMA_VERSION
from embodic.io.project import LoadedDraft, load_project, project_provenance, provenance_document
from embodic.model.design import DesignParameters
from embodic.model.draft import DraftIncomplete, parse_draft
from embodic.model.provenance import ProvenanceMap
from embodic.model.schema import JsonValue
from embodic.model.validate import validate_design
from embodic.model.winding_specs import SpiralWindingSpec
from embodic.outcome import ComputeOptions, ComputeOutcome, Stage, VersionInfo
from embodic.physics import analyse
from embodic.physics.analyse import NON_FINITE_CODE
from embodic.results import AnalysisResult, Registry, load_registry
from embodic.results.analysis_result import to_json
from embodic.results.traceable import Traceable
from embodic.winding import plan_issues, plan_spiral_winding

__all__ = [
    "ComputeOptions",
    "ComputeOutcome",
    "StageCache",
    "VersionInfo",
    "compute",
    "compute_project",
    "outcome_to_json",
    "version_info",
]

CachedStage = Literal["geometry", "drc", "physics"]
STAGE_CACHE_ENTRIES = 8
DEFAULT_OPTIONS = ComputeOptions()
T = TypeVar("T")


class StageCache:
    """Per-stage LRU (8 entries per stage), keyed by the SHA-256 of the stage inputs.

    One instance per worker thread; never shared between threads (no lock needed).
    """

    def __init__(self) -> None:
        self._entries: dict[CachedStage, OrderedDict[str, object]] = {
            "geometry": OrderedDict(),
            "drc": OrderedDict(),
            "physics": OrderedDict(),
        }

    def get(self, stage: CachedStage, key: str) -> object | None:
        """Return the cached value and mark it most recently used, or None."""
        entries = self._entries[stage]
        if key not in entries:
            return None
        entries.move_to_end(key)
        return entries[key]

    def put(self, stage: CachedStage, key: str, value: object) -> None:
        """Store a value; the least recently used entry beyond 8 is dropped."""
        entries = self._entries[stage]
        entries[key] = value
        entries.move_to_end(key)
        while len(entries) > STAGE_CACHE_ENTRIES:
            entries.popitem(last=False)


@dataclass(frozen=True, slots=True)
class _Geometry:
    """Product of the geometry stage: the boards or the reason there are none, plus the winding plan warnings."""

    built: BoardStack | Unbuildable
    plan_warnings: tuple[ValidationIssue, ...]


class _Failed:
    """A stage raised; its INTERNAL issue is already recorded."""


class _Cancelled:
    """The cancel token stopped a stage."""


_FAILED, _CANCELLED = _Failed(), _Cancelled()


@dataclass
class _Run:
    """Timings and issues collected while the stages of one compute call run."""

    timings_s: dict[str, float] = field(default_factory=dict)
    issues: list[ValidationIssue] = field(default_factory=list)

    def stage(self, stage: Stage, work: Callable[[], T]) -> T | _Failed:
        started = time.perf_counter()
        try:
            return work()
        except Exception:
            self.issues.append(_internal(stage, traceback.format_exc()))
            return _FAILED
        finally:
            self.timings_s[stage.value] = self.timings_s.get(stage.value, 0.0) + time.perf_counter() - started


def _traceables(value: object) -> Iterator[Traceable[object]]:
    if isinstance(value, Traceable):
        yield value
    elif dataclasses.is_dataclass(value) and not isinstance(value, type):
        for f in dataclasses.fields(value):
            yield from _traceables(getattr(value, f.name))
    elif isinstance(value, tuple):
        for item in value:
            yield from _traceables(item)


def _non_finite_issues(analysis: AnalysisResult | _Failed) -> Iterator[ValidationIssue]:
    for result in _traceables(analysis):
        if any(flag.code == NON_FINITE_CODE for flag in result.validity):
            yield ValidationIssue(
                code=NON_FINITE_CODE,
                category=IssueCategory.UNSUPPORTED_RANGE,
                severity=Severity.WARNING,
                message=message_for(NON_FINITE_CODE),
                pointers=(),
                value=result.quantity,
            )


def _internal(stage: Stage, trace: str) -> ValidationIssue:
    code = f"INTERNAL_{stage.name}_FAILED"
    return ValidationIssue(
        code=code,
        category=IssueCategory.INTERNAL,
        severity=Severity.ERROR,
        message=message_for(code),
        pointers=(),
        value=trace,
    )


def _key(*parts: str | bytes) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part if isinstance(part, bytes) else part.encode())
        digest.update(b"\0")
    return digest.hexdigest()


def _cached(cache: StageCache, stage: CachedStage, key: str, work: Callable[[], T]) -> T:
    """Return the cached value or run `work` and store it; a cancelled run (None) is not stored."""
    hit = cache.get(stage, key)
    if hit is not None:
        return hit  # type: ignore[return-value]  # the key names the stage, so the value has its type
    value = work()
    if value is not None:
        cache.put(stage, key, value)
    return value


def _geometry(design: DesignParameters, registry: Registry) -> _Geometry:
    warnings: tuple[ValidationIssue, ...] = ()
    if isinstance(design.winding, SpiralWindingSpec):
        plan = plan_spiral_winding(design, design.winding, registry)
        if isinstance(plan, Unbuildable):
            return _Geometry(built=plan, plan_warnings=())
        warnings = plan_issues(plan, design)
    return _Geometry(built=build_layout(design, registry), plan_warnings=warnings)


def _drc(
    layout: Layout, design: DesignParameters, options: ComputeOptions, cache: StageCache, cancel: CancelToken | None
) -> DrcReport | None:
    key = _key(layout.layout_hash, dumps_canonical(to_json(design.drc_rules)), str(options.use_symmetry))
    work = partial(run_drc, layout, design.drc_rules, use_symmetry=options.use_symmetry, cancel=cancel)
    return _cached(cache, "drc", key, work)


def _check_boards(
    run: _Run,
    boards: BoardStack,
    design: DesignParameters,
    options: ComputeOptions,
    cache: StageCache,
    cancel: CancelToken | None,
) -> tuple[DrcReport, ...] | _Cancelled | None:
    """One report per board; None when a board's check raised (its INTERNAL issue is recorded)."""
    reports = [run.stage(Stage.DRC, partial(_drc, layout, design, options, cache, cancel)) for layout in boards.boards]
    if any(report is None for report in reports):
        return _CANCELLED
    checked = [report for report in reports if isinstance(report, DrcReport)]
    return tuple(checked) if len(checked) == len(reports) else None


def _versions(registry: Registry) -> VersionInfo:
    return VersionInfo(
        embodic=embodic.__version__,
        schema=PROJECT_SCHEMA_VERSION,
        registry=registry.version,
        python=platform.python_version(),
        numpy=np.__version__,
    )


def version_info() -> VersionInfo:
    """Versions of this installation, with the packaged registry."""
    return _versions(load_registry())


def compute(
    design: DesignParameters,
    provenance: ProvenanceMap,
    *,
    options: ComputeOptions = DEFAULT_OPTIONS,
    cache: StageCache | None = None,
    cancel: CancelToken | None = None,
    registry: Registry | None = None,
) -> ComputeOutcome | None:
    """Validate -> build_layout -> run_drc per board -> analyse. Physics runs even with DRC violations.

    None only when cancelled. An ERROR issue from validation or an Unbuildable stops before the stages that need a
    board; an internal error in DRC still lets physics run, because physics needs the boards only.
    """
    registry = registry if registry is not None else load_registry()
    cache = cache if cache is not None else StageCache()
    run = _Run()
    hash_ = design_hash(design)

    def outcome(
        boards: BoardStack | None = None,
        drc: tuple[DrcReport, ...] | None = None,
        analysis: AnalysisResult | None = None,
    ) -> ComputeOutcome:
        return ComputeOutcome(
            design=design,
            design_hash=hash_,
            provenance=provenance,
            issues=tuple(run.issues),
            boards=boards,
            drc=drc,
            analysis=analysis,
            timings_s=dict(run.timings_s),
            versions=_versions(registry),
        )

    def stopped() -> bool:
        return cancel is not None and cancel.cancelled

    validated = run.stage(Stage.VALIDATE, lambda: validate_design(design))
    if isinstance(validated, _Failed):
        return outcome()
    run.issues.extend(validated)
    if stopped():
        return None
    if any(i.severity is Severity.ERROR for i in validated):
        return outcome()

    geometry_key = _key(hash_, registry.version)
    geometry = run.stage(
        Stage.GEOMETRY, lambda: _cached(cache, "geometry", geometry_key, lambda: _geometry(design, registry))
    )
    if isinstance(geometry, _Failed):
        return outcome()
    run.issues.extend(geometry.plan_warnings)
    if isinstance(geometry.built, Unbuildable):
        run.issues.extend(geometry.built.issues)
        return outcome()
    boards = geometry.built

    drc = _check_boards(run, boards, design, options, cache, cancel) if options.run_drc else None
    if isinstance(drc, _Cancelled) or stopped():
        return None

    physics_key = _key(hash_, boards.stack_hash, dumps_canonical(provenance_document(provenance)), registry.version)
    analysis = run.stage(
        Stage.PHYSICS,
        lambda: _cached(
            cache, "physics", physics_key, lambda: analyse(design, boards, provenance, registry, cancel=cancel)
        ),
    )
    if analysis is None:
        return None
    run.issues.extend(_non_finite_issues(analysis))
    return outcome(boards, drc, None if isinstance(analysis, _Failed) else analysis)


def compute_project(path: Path) -> ComputeOutcome | tuple[ValidationIssue, ...]:
    """Load + compute. Returns the issues when the file is missing, unreadable or holds an incomplete draft."""
    project, issues = load_project(path)
    if project is None:
        return issues
    if isinstance(project, LoadedDraft):
        parsed = parse_draft(project.draft)
        missing = parsed.missing if isinstance(parsed, DraftIncomplete) else ()
        code = "MISSING_DESIGN_INCOMPLETE"
        incomplete = ValidationIssue(
            code=code,
            category=IssueCategory.MISSING,
            severity=Severity.ERROR,
            message=message_for(code),
            pointers=tuple(file_pointer(p) for p in missing),
        )
        return (*issues, incomplete)
    computed = compute(project.design, project_provenance(project))
    assert computed is not None, "compute without a cancel token never returns None"
    return computed


def outcome_to_json(outcome: ComputeOutcome) -> dict[str, JsonValue]:
    """Results JSON of embodic-cli compute --json; non-finite numbers encoded as {"$f": "inf"}.

    Timings are left out, so the same design gives byte-identical JSON (PR-09).
    """
    boards: JsonValue = None
    if outcome.boards is not None:
        boards = {
            "stack_hash": outcome.boards.stack_hash,
            "layout_hashes": [b.layout_hash for b in outcome.boards.boards],
        }
    return {
        "design": design_document(outcome.design),
        "design_hash": outcome.design_hash,
        "provenance": provenance_document(outcome.provenance),
        "issues": to_json(list(outcome.issues)),
        "ok": outcome.ok,
        "boards": boards,
        "drc": None if outcome.drc is None else to_json(list(outcome.drc)),
        "analysis": None if outcome.analysis is None else outcome.analysis.to_json(),
        "versions": to_json(outcome.versions),
    }
