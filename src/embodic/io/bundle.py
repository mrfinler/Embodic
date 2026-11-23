"""ZIP bundle of the selected exports plus README.txt (interfaces.md section 9.3, stdlib zipfile).

Members are named after the bundle: ``motor.zip`` holds ``motor.svg``, ``motor.dxf``, ``motor_outline.dxf``, ...
"""

import dataclasses
import tempfile
import zipfile
from collections.abc import Sequence
from pathlib import Path

from embodic.io.dxf_writer import write_dxf
from embodic.io.examples import list_examples, load_example
from embodic.io.exporters import ExportKind, ExportRefused, ExportSummary, export_metadata, exportable_boards
from embodic.io.project import ProjectFile, encode_project, project_document
from embodic.io.readme_writer import write_readme
from embodic.io.report import write_report_pdf
from embodic.io.svg_writer import write_svg
from embodic.model.provenance import ExampleRef, ExampleValue, MeasuredValue, Measurement, derive_provenance
from embodic.outcome import ComputeOutcome

SUFFIX: dict[ExportKind, str] = {
    ExportKind.SVG: ".svg",
    ExportKind.DXF_COMPLETE: ".dxf",
    ExportKind.DXF_OUTLINE: "_outline.dxf",
    ExportKind.DXF_SCREWS: "_screws.dxf",
    ExportKind.PROJECT_JSON: ".embodic.json",
    ExportKind.PDF_REPORT: "_report.pdf",
}


def _packaged_origin(outcome: ComputeOutcome) -> ExampleRef | None:
    """Return an origin that reproduces recorded example provenance, or an exact packaged match."""
    example_ids = {value.example_id for value in outcome.provenance.values() if isinstance(value, ExampleValue)}
    if not example_ids:
        refs = (load_example(info.example_id)[0] for info in list_examples())
        return next((ref for ref in refs if ref.example_sha256 == outcome.design_hash), None)
    if len(example_ids) != 1:
        return None
    try:
        example = load_example(next(iter(example_ids)))
    except KeyError:
        return None
    measurements = tuple(
        Measurement(pointer=pointer, source=value.source)
        for pointer, value in outcome.provenance.items()
        if isinstance(value, MeasuredValue)
    )
    return example[0] if derive_provenance(outcome.design, example, measurements) == outcome.provenance else None


def write_project_export(outcome: ComputeOutcome, path: Path) -> ExportSummary:
    """Write the computed design and its provenance as a project file."""
    project = ProjectFile(design=outcome.design, origin=_packaged_origin(outcome))
    document = project_document(
        project,
        outcome.provenance,
        saved_utc=export_metadata(outcome).generated_utc,
        registry_version=outcome.versions.registry,
    )
    path.write_text(encode_project(document), encoding="utf-8", newline="\n")
    return ExportSummary(
        kind=ExportKind.PROJECT_JSON, path=path, lines=0, arcs=0, circles=0, vias=0, pads=0, holes=0, pages=0
    )


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
            return write_project_export(outcome, path)
        case ExportKind.README:
            raise ValueError("README.txt is always added; it is not a selectable member")


def write_bundle(
    outcome: ComputeOutcome, kinds: Sequence[ExportKind], path: Path, *, allow_drc_errors: bool = False
) -> tuple[ExportSummary, ...] | ExportRefused:
    """ZIP of the selected exports plus README.txt; the summaries name members by their path inside the ZIP.

    Nothing is written when the DRC gate or any selected writer refuses; that refusal is returned.
    """
    gate = exportable_boards(outcome, allow_drc_errors=allow_drc_errors)
    if isinstance(gate, ExportRefused):
        return gate
    selected = list(dict.fromkeys(k for k in kinds if k is not ExportKind.README))
    with tempfile.TemporaryDirectory() as work:
        folder = Path(work)
        written: list[ExportSummary] = []
        for kind in selected:
            result = _write(outcome, kind, folder / f"{path.stem}{SUFFIX[kind]}", allow_drc_errors)
            if isinstance(result, ExportRefused):
                return result
            written.append(result)
        written.append(write_readme(outcome, written, folder / "README.txt"))
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for summary in written:
                archive.write(summary.path, arcname=summary.path.name)
    return tuple(dataclasses.replace(s, path=Path(s.path.name)) for s in written)
