"""The Export dialog's logic: format choices, preflight checklist, DRC confirmation and the run. Qt-free.

The writers of `embodic.io` do the work (D-038d/e). This module decides which files a run writes and names only the
files that exist afterwards (screens.md section 11).
"""

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeAlias

from embodic.drc import DrcViolation
from embodic.io.bundle import SUFFIX, write_bundle
from embodic.io.canonical import design_hash
from embodic.io.dxf_writer import write_dxf
from embodic.io.examples import list_examples, load_example
from embodic.io.exporters import (
    ExportKind,
    ExportRefused,
    ExportSummary,
    drc_passed,
    export_metadata,
    exportable_boards,
)
from embodic.io.project import ProjectFile, encode_project, project_document
from embodic.io.readme_writer import write_readme
from embodic.io.report import write_report_pdf
from embodic.io.svg_writer import write_svg
from embodic.outcome import ComputeOutcome
from embodic.ui.strings import text
from embodic.ui.viewmodels.results import result_rows

BUNDLE: Literal["zip"] = "zip"
ExportFormat: TypeAlias = ExportKind | Literal["zip"]
CheckState: TypeAlias = Literal["pass", "fail", "warn"]


@dataclass(frozen=True, slots=True, kw_only=True)
class FormatOption:
    """One format check box of the dialog."""

    widget_id: str
    choice: ExportFormat
    label: str


FORMAT_OPTIONS: tuple[FormatOption, ...] = (
    FormatOption(widget_id="export-format-svg", choice=ExportKind.SVG, label=text("export.format.svg")),
    FormatOption(
        widget_id="export-format-dxf-complete", choice=ExportKind.DXF_COMPLETE, label=text("export.format.dxf-complete")
    ),
    FormatOption(
        widget_id="export-format-dxf-outline", choice=ExportKind.DXF_OUTLINE, label=text("export.format.dxf-outline")
    ),
    FormatOption(
        widget_id="export-format-dxf-screws", choice=ExportKind.DXF_SCREWS, label=text("export.format.dxf-screws")
    ),
    FormatOption(widget_id="export-format-json", choice=ExportKind.PROJECT_JSON, label=text("export.format.json")),
    FormatOption(widget_id="export-format-pdf", choice=ExportKind.PDF_REPORT, label=text("export.format.pdf")),
    FormatOption(widget_id="export-format-readme", choice=ExportKind.README, label=text("export.format.readme")),
    FormatOption(widget_id="export-format-zip", choice=BUNDLE, label=text("export.format.zip")),
)

# The toolstrip command that opens the dialog decides what is checked first ("All files" checks everything).
PRESETS: dict[str, frozenset[ExportFormat]] = {
    "export_svg": frozenset({ExportKind.SVG}),
    "export_dxf": frozenset({ExportKind.DXF_COMPLETE}),
    "export_pdf": frozenset({ExportKind.PDF_REPORT}),
    "export_bundle": frozenset(o.choice for o in FORMAT_OPTIONS),
}
# The PDF report and the README document the DRC state and the project file is the design itself, not a fabrication
# drawing, so none of them waits for the DRC confirmation (D-038d, D-045e, D-046a).
UNGATED: frozenset[ExportFormat] = frozenset({ExportKind.PDF_REPORT, ExportKind.README, ExportKind.PROJECT_JSON})


@dataclass(frozen=True, slots=True, kw_only=True)
class ExportPreflight:
    """DRC state before an export; with failures the dialog asks first, focus on Cancel (REQ-F-33)."""

    drc_passed: bool
    failures: tuple[DrcViolation, ...]
    needs_confirmation: bool


@dataclass(frozen=True, slots=True, kw_only=True)
class ChecklistItem:
    """One line of the export checklist: what the files will say about the design."""

    key: Literal["stamp", "drc", "stale", "assumptions"]
    text: str
    state: CheckState


@dataclass(frozen=True, slots=True, kw_only=True)
class ExportWritten:
    """The files a run wrote, each of which exists on disk."""

    folder: Path
    files: tuple[Path, ...]


def file_stem(design_name: str) -> str:
    """Return a file name stem from the design name: letters, digits, dot, hyphen and underscore only."""
    return re.sub(r"[^A-Za-z0-9._-]+", "_", design_name).strip("._") or "embodic_design"


def selection_problem(formats: frozenset[ExportFormat], folder: str) -> str | None:
    """Return why Run cannot start, or None: nothing chosen, README alone, ZIP alone, or no folder."""
    files = formats - {ExportKind.README, BUNDLE}
    if not formats:
        return text("export.nothing")
    if not files:
        return text("export.readme-alone")
    if not folder.strip():
        return text("export.no-folder")
    return None


def needs_drc_confirmation(preflight: ExportPreflight, formats: frozenset[ExportFormat]) -> bool:
    """Return True when the DRC failed and the selection holds an SVG, a DXF or the ZIP (REQ-F-33)."""
    return preflight.needs_confirmation and not formats <= UNGATED


class ExportViewModel:
    """Export of the outcome on screen; ``source`` returns it and whether it is stale."""

    def __init__(self, source: Callable[[], tuple[ComputeOutcome | None, bool]]) -> None:
        self._source = source

    def outcome(self) -> ComputeOutcome | None:
        """Return the outcome an export would write."""
        return self._source()[0]

    def unavailable(self) -> dict[ExportFormat, str]:
        """Return the formats this design cannot produce, with the reason (a board without screw holes)."""
        outcome = self.outcome()
        boards = outcome.boards.boards if outcome is not None and outcome.boards is not None else ()
        if not any(b.outline.holes for b in boards):
            return {ExportKind.DXF_SCREWS: text("export.format.no-screws")}
        return {}

    def preflight(self) -> ExportPreflight:
        """Return the DRC state of the outcome; a DRC that did not run needs confirmation too."""
        outcome = self.outcome()
        if outcome is None:
            return ExportPreflight(drc_passed=False, failures=(), needs_confirmation=False)
        passed = drc_passed(outcome)
        failures = tuple(v for report in outcome.drc or () for v in report.violations)
        return ExportPreflight(drc_passed=passed, failures=failures, needs_confirmation=not passed)

    def checklist(self) -> tuple[ChecklistItem, ...]:
        """Return engine stamp, DRC result, stale state and the number of assumptions behind the results."""
        outcome, stale = self._source()
        if outcome is None:
            return ()
        v = outcome.versions
        stamp = text("export.check.stamp", embodic=v.embodic, registry=v.registry, hash=outcome.design_hash[:12])
        if outcome.drc is None:
            drc = ChecklistItem(key="drc", text=text("export.check.drc-not-run"), state="fail")
        elif drc_passed(outcome):
            drc = ChecklistItem(key="drc", text=text("export.check.drc-pass"), state="pass")
        else:
            count = sum(r.violation_count for r in outcome.drc)
            drc = ChecklistItem(key="drc", text=text("export.check.drc-fail", count=count), state="fail")
        rows = result_rows(outcome.analysis) if outcome.analysis is not None else ()
        assumed = len({(a.item, a.value_text) for row in rows for a in row.traceable.assumed_inputs})
        return (
            ChecklistItem(key="stamp", text=stamp, state="pass"),
            drc,
            ChecklistItem(
                key="stale",
                text=text("export.check.stale" if stale else "export.check.current"),
                state="warn" if stale else "pass",
            ),
            ChecklistItem(
                key="assumptions",
                text=text("export.check.assumptions", count=assumed)
                if assumed
                else text("export.check.no-assumptions"),
                state="warn" if assumed else "pass",
            ),
        )

    def export(
        self, kinds: Sequence[ExportKind], folder: Path, *, confirmed_drc_errors: bool
    ) -> tuple[ExportSummary, ...] | ExportRefused:
        """Write each kind into ``folder``, README last; nothing is written when the DRC gate refuses."""
        outcome = self.outcome()
        if outcome is None:
            raise RuntimeError("no computed design to export")
        gate = exportable_boards(outcome, allow_drc_errors=confirmed_drc_errors)
        if isinstance(gate, ExportRefused):
            return gate
        stem = file_stem(outcome.design.name)
        written: list[ExportSummary] = []
        for kind in dict.fromkeys(k for k in kinds if k is not ExportKind.README):
            result = _write(outcome, kind, folder / f"{stem}{SUFFIX[kind]}", confirmed_drc_errors)
            if isinstance(result, ExportRefused):
                return result
            written.append(result)
        if ExportKind.README in kinds:
            written.append(write_readme(outcome, written, folder / "README.txt"))
        return tuple(written)

    def run(
        self, formats: frozenset[ExportFormat], folder: Path, *, confirmed_drc_errors: bool
    ) -> ExportWritten | ExportRefused:
        """Write the chosen files and, when chosen, the ZIP of the same kinds; return the files on disk.

        The PDF report, the README and the project file alone are written whatever the DRC verdict.
        """
        outcome = self.outcome()
        if outcome is None:
            raise RuntimeError("no computed design to export")
        folder.mkdir(parents=True, exist_ok=True)
        kinds = [o.choice for o in FORMAT_OPTIONS if o.choice in formats and isinstance(o.choice, ExportKind)]
        drc_errors_allowed = confirmed_drc_errors or formats <= UNGATED
        result = self.export(kinds, folder, confirmed_drc_errors=drc_errors_allowed)
        if isinstance(result, ExportRefused):
            return result
        files = [s.path for s in result]
        if BUNDLE in formats:
            zip_path = folder / f"{file_stem(outcome.design.name)}.zip"
            bundled = write_bundle(outcome, kinds, zip_path, allow_drc_errors=confirmed_drc_errors)
            if isinstance(bundled, ExportRefused):
                return bundled
            files.append(zip_path)
        return ExportWritten(folder=folder, files=tuple(p for p in files if p.is_file()))


def _write(outcome: ComputeOutcome, kind: ExportKind, path: Path, allow: bool) -> ExportSummary | ExportRefused:
    match kind:
        case ExportKind.SVG:
            return write_svg(outcome, path, allow_drc_errors=allow)
        case ExportKind.DXF_COMPLETE:
            return write_dxf(outcome, path, "complete", allow_drc_errors=allow)
        case ExportKind.DXF_OUTLINE:
            return write_dxf(outcome, path, "outline", allow_drc_errors=allow)
        case ExportKind.DXF_SCREWS:
            return write_dxf(outcome, path, "screws", allow_drc_errors=allow)
        case ExportKind.PDF_REPORT:
            return write_report_pdf(outcome, path)
        case ExportKind.PROJECT_JSON:
            return _write_project(outcome, path)
        case ExportKind.README:
            raise ValueError("README.txt is written last, from the other summaries")


def _write_project(outcome: ComputeOutcome, path: Path) -> ExportSummary:
    """Write the project file; a design identical to a packaged example keeps that example as its origin."""
    origin = next(
        (
            ref
            for ref, design in map(load_example, (i.example_id for i in list_examples()))
            if design_hash(design) == outcome.design_hash
        ),
        None,
    )
    document = project_document(
        ProjectFile(design=outcome.design, origin=origin),
        outcome.provenance,
        saved_utc=export_metadata(outcome).generated_utc,
        registry_version=outcome.versions.registry,
    )
    path.write_text(encode_project(document), encoding="utf-8", newline="\n")
    return ExportSummary(
        kind=ExportKind.PROJECT_JSON, path=path, lines=0, arcs=0, circles=0, vias=0, pads=0, holes=0, pages=0
    )
