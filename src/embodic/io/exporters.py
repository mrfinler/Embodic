"""Export vocabulary shared by every writer (interfaces.md section 9.3) and the rules they all apply.

Every writer draws in millimetres in a y-up frame centred on the shaft axis, the frame of the Layout itself.
"""

import datetime
import json
import math
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Literal

from embodic.drc import DrcReport
from embodic.errors import IssueCategory, Severity, ValidationIssue, message_for
from embodic.geometry.layout import Layout, Pad
from embodic.geometry.primitives import Arc, Line, Primitive, PrimitiveRole
from embodic.model.vocabulary import Phase
from embodic.outcome import ComputeOutcome
from embodic.paths import resource_root


class ExportKind(StrEnum):
    """One file of the D-009 export set."""

    SVG = "svg"
    DXF_COMPLETE = "dxf_complete"
    DXF_OUTLINE = "dxf_outline"  # board outline and bore only
    DXF_SCREWS = "dxf_screws"  # screw clearance holes only
    PROJECT_JSON = "project_json"
    PDF_REPORT = "pdf_report"
    README = "readme"


class PhaseRenderMode(StrEnum):
    """How a drawing tells the phases apart."""

    COLOUR = "colour"  # red / blue / green plus labels and line style (D-011)
    GREYSCALE_HATCH = "greyscale_hatch"  # lightness + hatch + labels (REQ-N-23)


@dataclass(frozen=True, slots=True, kw_only=True)
class ExportMetadata:
    """The REQ-T-07 stamp every export carries."""

    embodic_version: str
    engine_version: str
    registry_version: str
    design_hash: str
    generated_utc: str
    drc_passed: bool


@dataclass(frozen=True, slots=True, kw_only=True)
class ExportSummary:
    """What one writer wrote: the file and the number of each entity in it."""

    kind: ExportKind
    path: Path
    lines: int
    arcs: int
    circles: int
    vias: int
    pads: int
    holes: int
    pages: int  # PDF only, else 0


@dataclass(frozen=True, slots=True, kw_only=True)
class ExportRefused:
    """Why a writer wrote nothing."""

    reason: Literal["drc_errors_not_confirmed", "no_layout", "no_screws"]
    issues: tuple[ValidationIssue, ...]


def drc_passed(outcome: ComputeOutcome) -> bool:
    """Return whether every board has a DRC report and every report passed; a DRC that did not run has not passed."""
    return outcome.drc is not None and all(report.passed for report in outcome.drc)


def export_metadata(outcome: ComputeOutcome) -> ExportMetadata:
    """Return the stamp of an export generated now.

    ``engine_version`` is an assumption: VersionInfo names no engine, so it records the runtime that computed the
    geometry and physics (the embodic package on its Python and NumPy).
    """
    versions = outcome.versions
    return ExportMetadata(
        embodic_version=versions.embodic,
        engine_version=f"embodic {versions.embodic} (CPython {versions.python}, numpy {versions.numpy})",
        registry_version=versions.registry,
        design_hash=outcome.design_hash,
        generated_utc=datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        drc_passed=drc_passed(outcome),
    )


def metadata_fields(metadata: ExportMetadata) -> tuple[tuple[str, str], ...]:
    """Return the stamp as (field name, text) pairs in contract order, for writers that print it."""
    return (
        ("embodic_version", metadata.embodic_version),
        ("engine_version", metadata.engine_version),
        ("registry_version", metadata.registry_version),
        ("design_hash", metadata.design_hash),
        ("generated_utc", metadata.generated_utc),
        ("drc_passed", "true" if metadata.drc_passed else "false"),
    )


def _issue(code: str, category: IssueCategory, **extra: float | int | str | None) -> ValidationIssue:
    return ValidationIssue(
        code=code, category=category, severity=Severity.ERROR, message=message_for(code), pointers=(), **extra
    )


def _drc_failures(reports: tuple[DrcReport, ...] | None) -> tuple[ValidationIssue, ...]:
    """Return the confirmation issue and one issue per failed check kind of each board, in board order."""
    if reports is None:
        return (_issue("EXPORT_DRC_ERRORS_NOT_CONFIRMED", IssueCategory.DRC, value="DRC did not run"),)
    total = sum(report.violation_count for report in reports)
    issues = [_issue("EXPORT_DRC_ERRORS_NOT_CONFIRMED", IssueCategory.DRC, value=total)]
    for board, report in enumerate(reports, start=1):
        failed = {violation.kind for violation in report.violations}
        for summary in report.summaries:
            if summary.kind in failed:
                issues.append(
                    _issue(
                        summary.kind.issue_code,
                        IssueCategory.DRC,
                        value=summary.measured_min_mm,
                        limit=summary.required_mm,
                        hint=f"board {board}",
                    )
                )
    return tuple(issues)


def exportable_boards(outcome: ComputeOutcome, *, allow_drc_errors: bool) -> tuple[Layout, ...] | ExportRefused:
    """Return the boards to draw, or the refusal: no layout, or a DRC that did not pass without confirmation."""
    if outcome.boards is None:
        return ExportRefused(reason="no_layout", issues=(_issue("EXPORT_NO_LAYOUT", IssueCategory.UNBUILDABLE),))
    if not drc_passed(outcome) and not allow_drc_errors:
        return ExportRefused(reason="drc_errors_not_confirmed", issues=_drc_failures(outcome.drc))
    return outcome.boards.boards


def no_screws() -> ExportRefused:
    """Return the refusal of a screws drawing for a board without screw holes."""
    return ExportRefused(reason="no_screws", issues=(_issue("EXPORT_NO_SCREWS", IssueCategory.INVALID),))


@dataclass(frozen=True, slots=True, kw_only=True)
class PhaseInk:
    """How a drawing marks one phase; the fields match ``embodic.ui`` PhaseStyle (interfaces.md section 11)."""

    phase: Phase | None  # None for neutral and interconnect copper
    colour_hex: str
    grey_hex: str
    hatch_deg: Literal[0, 45, 135]  # 0 = no hatch
    dash: Literal["solid", "dash", "dot"]
    label: str


_DASH = {"solid": "solid", "dashed": "dash", "dotted": "dot"}


def phase_inks() -> dict[Phase | None, PhaseInk]:
    """Return the light-theme ink of each phase and of interconnect copper.

    The one place exporters read theme data. It reads ``resources/themes/tokens.json`` (``phase_style`` and
    ``themes.light.color``) until ``resources/themes/light.json`` lands; swapping the source changes only this function.
    """
    tokens = json.loads((resource_root() / "themes" / "tokens.json").read_text(encoding="utf-8"))
    colours = tokens["themes"]["light"]["color"]
    inks: dict[Phase | None, PhaseInk] = {}
    for phase in Phase:
        style = tokens["phase_style"][phase.value]
        key = f"phase-{phase.value.lower()}"
        inks[phase] = PhaseInk(
            phase=phase,
            colour_hex=colours[key],
            grey_hex=colours[f"{key}-grey"],
            hatch_deg=style["hatch_deg"] or 0,
            dash=_DASH[style["line"]],  # type: ignore[arg-type]
            label=f"Phase {style['label']}",
        )
    inks[None] = PhaseInk(
        phase=None,
        colour_hex=colours["text-2"],
        grey_hex=colours["text-2"],
        hatch_deg=0,
        dash="solid",
        label="Interconnect",
    )
    return inks


def pad_outline(pad: Pad) -> tuple[Primitive, ...]:
    """Return the closed edge of a square, rect or oblong pad as width-0 primitives (a round pad is a circle)."""
    half_w, half_h = pad.width_mm / 2, pad.height_mm / 2
    cos_r, sin_r = math.cos(pad.rotation_rad), math.sin(pad.rotation_rad)

    def at(u: float, v: float) -> tuple[float, float]:
        return (pad.x_mm + u * cos_r - v * sin_r, pad.y_mm + u * sin_r + v * cos_r)

    def line(a: tuple[float, float], b: tuple[float, float]) -> Line:
        return Line(x1_mm=a[0], y1_mm=a[1], x2_mm=b[0], y2_mm=b[1], width_mm=0.0, role=PrimitiveRole.OUTLINE)

    if pad.shape != "oblong":
        corners = [at(-half_w, -half_h), at(half_w, -half_h), at(half_w, half_h), at(-half_w, half_h)]
        return tuple(line(corners[i], corners[(i + 1) % 4]) for i in range(4))
    long_axis_u = half_w >= half_h
    r = min(half_w, half_h)
    reach = (half_w if long_axis_u else half_h) - r
    axis = 0.0 if long_axis_u else math.pi / 2
    centres = [at(reach, 0.0), at(-reach, 0.0)] if long_axis_u else [at(0.0, reach), at(0.0, -reach)]
    prims: list[Primitive] = []
    for k, (cx, cy) in enumerate(centres):
        start = pad.rotation_rad + axis - math.pi / 2 + k * math.pi
        cap = Arc(
            cx_mm=cx, cy_mm=cy, r_mm=r, start_rad=start, sweep_rad=math.pi, width_mm=0.0, role=PrimitiveRole.OUTLINE
        )
        other_x, other_y = centres[1 - k]
        end_x, end_y = cap.end_point()
        prims += [cap, line((end_x, end_y), (end_x + other_x - cx, end_y + other_y - cy))]
    return tuple(prims)


def is_full_circle(arc: Arc) -> bool:
    """Return whether an arc closes on itself (a whole circle)."""
    return abs(arc.sweep_rad) >= 2 * math.pi - 1e-9
