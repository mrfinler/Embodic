"""README.txt of an export set (interfaces.md section 9.3; content after Xcoil readme(), ui-main.js l.37-51)."""

from collections.abc import Sequence
from pathlib import Path

from embodic.io.exporters import ExportKind, ExportSummary, export_metadata, metadata_fields
from embodic.outcome import ComputeOutcome
from embodic.results.status import Status

DESCRIPTION: dict[ExportKind, str] = {
    ExportKind.SVG: "drawing of every board: outline, copper per layer and phase, vias, pads, screw holes",
    ExportKind.DXF_COMPLETE: "complete board: outline, cut-outs, screw holes, copper centre lines, vias, pads",
    ExportKind.DXF_OUTLINE: "board outline and inner cut-out only",
    ExportKind.DXF_SCREWS: "screw clearance holes only",
    ExportKind.PROJECT_JSON: "embodic project file: the design inputs and the provenance of each value",
    ExportKind.PDF_REPORT: "design report: key results with unit and status, inputs, DRC summary, board drawing",
    ExportKind.README: "this file",
}

CAVEAT = (
    "The analytical results are first-order estimates from a two-dimensional field model without end effects or "
    "armature reaction. Check them with a field simulation or a measurement before you build or order boards."
)


def readme_text(outcome: ComputeOutcome, files: Sequence[ExportSummary]) -> str:
    """Return the README text; pure apart from the generation time in the stamp."""
    metadata = export_metadata(outcome)
    boards = outcome.boards.boards if outcome.boards is not None else ()
    violations = sum(r.violation_count for r in outcome.drc) if outcome.drc is not None else None
    drc = "not run" if violations is None else ("passed" if metadata.drc_passed else f"FAILED, {violations} violations")
    lines = [
        f"embodic {metadata.embodic_version} export",
        "",
        *(f"{name}: {value}" for name, value in metadata_fields(metadata)),
        f"DRC: {drc}",
        f"Topology: {outcome.design.topology.value}, boards: {len(boards)}",
        *(f"Board {k} copper layers: {', '.join(b.copper_layers)}" for k, b in enumerate(boards, start=1)),
        "",
        "Files:",
        *(f"  {summary.path.name}: {DESCRIPTION[summary.kind]}" for summary in files),
        "  README.txt: this file",
        "",
        "Units: millimetres (mm).",
        "Frame: SVG and DXF coordinates are y up and centred on the shaft axis.",
        "DXF copper is written as centre lines. The layer name ends with the trace width in micrometres "
        "(_W400 = 0.40 mm trace); CU<n>_<layer>_PH_<phase> holds phase copper, CU<n>_<layer>_IC interconnect copper.",
        "",
        f"Status labels: each value in the report carries one of {', '.join(s.value for s in Status)}.",
        f"Estimate caveat: {CAVEAT}",
        "Run the DRC of your PCB tool before ordering boards.",
    ]
    return "\n".join(lines) + "\n"


def write_readme(outcome: ComputeOutcome, files: Sequence[ExportSummary], path: Path) -> ExportSummary:
    """Plain-text README.txt describing every exported file, units, frame and the estimate caveats."""
    path.write_text(
        readme_text(outcome, [f for f in files if f.kind is not ExportKind.README]), encoding="utf-8", newline="\n"
    )
    return ExportSummary(
        kind=ExportKind.README, path=path, lines=0, arcs=0, circles=0, vias=0, pads=0, holes=0, pages=0
    )
