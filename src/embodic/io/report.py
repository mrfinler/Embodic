"""PDF design report (interfaces.md section 9.3; page structure after Xcoil buildReport, report.js l.230-352).

Pages: the stamp and "Key results" (every scalar result with value, unit and status word), the DRC summary, the
inputs with their provenance, then one vector drawing of each board. The report has no DRC confirmation in its
signature, so it never refuses for DRC; it states the DRC result instead.
"""

import dataclasses
import json
import math
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from embodic.geometry.layout import Layout
from embodic.geometry.primitives import Arc, Line, Primitive
from embodic.io.exporters import (
    ExportKind,
    ExportMetadata,
    ExportRefused,
    ExportSummary,
    PhaseInk,
    PhaseRenderMode,
    export_metadata,
    exportable_boards,
    metadata_fields,
    pad_outline,
    phase_inks,
)
from embodic.io.pdf_writer import PAGE_H, PAGE_W, PdfDocument, arc_bezier
from embodic.model.fields import field_for
from embodic.model.schema import design_values
from embodic.model.vocabulary import Phase
from embodic.outcome import ComputeOutcome
from embodic.results import AnalysisResult
from embodic.results.formatting import format_quantity
from embodic.results.labels import quantity_title
from embodic.results.traceable import Traceable
from embodic.units import Unit

MARGIN = 50.0
ROW = 11.0
DIMENSIONLESS = "(dimensionless)"
INK = "#141414"
LAND = "#666666"
DRILL = "#ffffff"


def value_text(value: float, unit: Unit, *, significant: int = 3) -> str:
    """Return a value with its unit; a dimensionless value says so, a missing number keeps its unit."""
    symbol = unit.display() or DIMENSIONLESS
    if not math.isfinite(value):
        return f"n/a {symbol}"
    text = format_quantity(value, unit, significant=significant)
    return text if unit.display() else f"{text} {DIMENSIONLESS}"


def key_results(analysis: AnalysisResult) -> tuple[tuple[str, Traceable[float]], ...]:
    """Return every scalar result of an analysis in field order, each with its AnalysisResult field name."""
    named = ((f.name, getattr(analysis, f.name)) for f in dataclasses.fields(analysis))
    return tuple((name, v) for name, v in named if isinstance(v, Traceable) and isinstance(v.value, float))


@dataclass(slots=True)
class _Flow:
    """Top-down text flow that starts a new page when the current one is full."""

    doc: PdfDocument
    title: str
    y: float = 0.0

    def page(self) -> None:
        self.doc.new_page()
        self.doc.text(MARGIN, PAGE_H - 30, self.title, size=8, bold=True, grey=0.3)
        self.y = PAGE_H - MARGIN - 10

    def need(self, height: float) -> None:
        if self.y - height < MARGIN:
            self.page()

    def heading(self, text: str) -> None:
        self.need(3 * ROW)
        self.y -= ROW / 2
        self.doc.text(MARGIN, self.y, text, size=11, bold=True)
        self.y -= 1.5 * ROW

    def row(self, cells: Sequence[tuple[float, str]], *, bold: bool = False) -> None:
        self.need(ROW)
        self.doc.row(self.y, cells, bold=bold)
        self.y -= ROW


def _stamp(flow: _Flow, metadata: ExportMetadata) -> None:
    flow.heading("embodic design report")
    for name, value in metadata_fields(metadata):
        flow.row([(MARGIN, name), (MARGIN + 110, value)])


def _key_results(flow: _Flow, analysis: AnalysisResult | None) -> None:
    flow.heading("Key results")
    if analysis is None:
        flow.row([(MARGIN, "No analysis result: physics did not run for this design.")])
        return
    flow.row([(MARGIN, "Quantity"), (MARGIN + 200, "Value"), (MARGIN + 330, "Status")], bold=True)
    for name, t in key_results(analysis):
        status = t.status.value + (f" ({t.label})" if t.label else "")
        flow.row(
            [
                (MARGIN, quantity_title(name)),
                (MARGIN + 200, value_text(t.value, t.unit)),
                (MARGIN + 330, status),
            ]
        )


def _drc(flow: _Flow, outcome: ComputeOutcome) -> None:
    flow.heading("DRC summary")
    if outcome.drc is None:
        flow.row([(MARGIN, "DRC did not run.")])
        return
    for board, report in enumerate(outcome.drc, start=1):
        verdict = "passed" if report.passed else f"FAILED, {report.violation_count} violations"
        flow.row([(MARGIN, f"Board {board}: {verdict} (method {report.method}, epsilon {report.epsilon_mm} mm)")])
        flow.row(
            [(MARGIN, "Check"), (MARGIN + 130, "Least measured"), (MARGIN + 240, "Required"), (MARGIN + 330, "Pairs")],
            bold=True,
        )
        for s in report.summaries:
            # six figures, so a measured 0.19997 mm against a 0.2 mm rule does not print as 0.200 mm
            measured = (
                "none checked" if s.measured_min_mm is None else value_text(s.measured_min_mm, Unit.MM, significant=6)
            )
            flow.row(
                [
                    (MARGIN, s.kind.value),
                    (MARGIN + 130, measured),
                    (MARGIN + 240, value_text(s.required_mm, Unit.MM, significant=6)),
                    (MARGIN + 330, str(s.pairs_checked)),
                ]
            )


def _inputs(flow: _Flow, outcome: ComputeOutcome) -> None:
    flow.heading("Inputs")
    flow.row([(MARGIN, "Input"), (MARGIN + 230, "Value"), (MARGIN + 380, "Provenance")], bold=True)
    values = design_values(outcome.design)
    for pointer in sorted(values):
        value = values[pointer]
        unit = field_for(pointer, values).unit
        text = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
        if unit is not None and isinstance(value, int | float) and not isinstance(value, bool):
            text = f"{text} {unit.display() or DIMENSIONLESS}"
        entry = outcome.provenance.get(pointer)
        provenance = entry.provenance.value if entry is not None else "not recorded"
        flow.row([(MARGIN, pointer), (MARGIN + 230, text[:60]), (MARGIN + 380, provenance)])


@dataclass(frozen=True, slots=True)
class _Frame:
    """Board millimetres to page points: centred, y up in both."""

    x0: float
    y0: float
    scale: float

    def x(self, x_mm: float) -> float:
        return self.x0 + x_mm * self.scale

    def y(self, y_mm: float) -> float:
        return self.y0 + y_mm * self.scale


def _segments(prims: Sequence[Primitive], frame: _Frame) -> list[str]:
    ops: list[str] = []
    for k, q in enumerate(prims):
        sx, sy = q.start_point()
        if k == 0 or math.dist(prims[k - 1].end_point(), (sx, sy)) > 1e-6:
            ops.append(f"{frame.x(sx):.3f} {frame.y(sy):.3f} m")
        if isinstance(q, Line):
            ops.append(f"{frame.x(q.x2_mm):.3f} {frame.y(q.y2_mm):.3f} l")
        else:
            assert isinstance(q, Arc)
            for c in arc_bezier(q.cx_mm, q.cy_mm, q.r_mm, q.start_rad, q.sweep_rad):
                ops.append(
                    f"{frame.x(c[0]):.3f} {frame.y(c[1]):.3f} {frame.x(c[2]):.3f} {frame.y(c[3]):.3f} "
                    f"{frame.x(c[4]):.3f} {frame.y(c[5]):.3f} c"
                )
    return ops


def _drawing(doc: PdfDocument, index: int, board: Layout, inks: dict[Phase | None, PhaseInk], grey: bool) -> None:
    doc.new_page()
    doc.text(MARGIN, PAGE_H - 30, f"Board {index} drawing (mm, y up, centred on the shaft axis)", size=10, bold=True)
    reach = max(
        q.r_mm + math.hypot(q.cx_mm, q.cy_mm)
        if isinstance(q, Arc)
        else max(map(abs, (*q.start_point(), *q.end_point())))
        for q in board.outline.outer
    )
    frame = _Frame(x0=PAGE_W / 2, y0=PAGE_H / 2 + 40, scale=(PAGE_W - 2 * MARGIN) / (2 * reach * 1.04))
    doc.stroke_path([*_segments(board.outline.outer, frame), "h"], width=0.6, colour_hex=INK)
    for loop in board.outline.cutouts:
        doc.stroke_path([*_segments(loop, frame), "h"], width=0.6, colour_hex=INK)
    for path in board.paths:
        ink = inks[path.phase]
        colour = ink.grey_hex if grey else ink.colour_hex
        for q in path.primitives:
            doc.stroke_path(_segments([q], frame), width=max(0.25, q.width_mm * frame.scale), colour_hex=colour)
    for hole in board.outline.holes:
        doc.circle(
            frame.x(hole.x_mm), frame.y(hole.y_mm), hole.diameter_mm / 2 * frame.scale, fill_hex=None, stroke_hex=INK
        )
    for via in board.vias:
        doc.circle(frame.x(via.x_mm), frame.y(via.y_mm), via.pad_mm / 2 * frame.scale, fill_hex=LAND)
        doc.circle(frame.x(via.x_mm), frame.y(via.y_mm), via.drill_mm / 2 * frame.scale, fill_hex=DRILL)
    for pad in board.pads:
        if pad.shape == "round":
            doc.circle(frame.x(pad.x_mm), frame.y(pad.y_mm), pad.width_mm / 2 * frame.scale, fill_hex=LAND)
        else:
            doc.stroke_path([*_segments(pad_outline(pad), frame), "h"], width=0.6, colour_hex=LAND)
        if pad.drill_mm > 0:
            doc.circle(frame.x(pad.x_mm), frame.y(pad.y_mm), pad.drill_mm / 2 * frame.scale, fill_hex=DRILL)
    _legend(doc, inks, grey)


def _legend(doc: PdfDocument, inks: dict[Phase | None, PhaseInk], grey: bool) -> None:
    """Phase key: line sample, hatch swatch (greyscale mode) and the label; hatch angles per REQ-N-23."""
    y = MARGIN + 60
    for phase in Phase:
        ink = inks[phase]
        colour = ink.grey_hex if grey else ink.colour_hex
        doc.stroke_path([f"{MARGIN:.1f} {y:.1f} m", f"{MARGIN + 30:.1f} {y:.1f} l"], width=2.0, colour_hex=colour)
        if grey and ink.hatch_deg:
            x, step = MARGIN + 38, 3.0
            dx = math.cos(math.radians(ink.hatch_deg)) * 20
            dy = math.sin(math.radians(ink.hatch_deg)) * 20
            lines = [
                f"{x + i * step - dx:.2f} {y - dy:.2f} m {x + i * step + dx:.2f} {y + dy:.2f} l" for i in range(-3, 7)
            ]
            doc.op(f"q {x:.1f} {y - 5:.1f} 10 10 re W n")
            doc.stroke_path(lines, width=0.5, colour_hex=colour)
            doc.op("Q")
        doc.text(MARGIN + 54, y - 3, ink.label, size=9)
        y -= 16


def write_report_pdf(
    outcome: ComputeOutcome, path: Path, *, mode: PhaseRenderMode = PhaseRenderMode.GREYSCALE_HATCH
) -> ExportSummary | ExportRefused:
    """Own dependency-free writer (port of Xcoil report.js, team's own code). Every value with unit and status."""
    boards = exportable_boards(outcome, allow_drc_errors=True)
    if isinstance(boards, ExportRefused):
        return boards
    metadata = export_metadata(outcome)
    doc = PdfDocument()
    flow = _Flow(doc=doc, title=f"embodic {metadata.embodic_version} design report | {metadata.design_hash}")
    flow.page()
    _stamp(flow, metadata)
    _key_results(flow, outcome.analysis)
    _drc(flow, outcome)
    _inputs(flow, outcome)
    inks = phase_inks()
    for index, board in enumerate(boards, start=1):
        _drawing(doc, index, board, inks, mode is PhaseRenderMode.GREYSCALE_HATCH)
    info = {
        "Title": "embodic design report",
        "Producer": f"embodic {metadata.embodic_version}",
        "CreationDate": "D:" + metadata.generated_utc.replace("-", "").replace(":", "").replace("T", "")[:-1] + "Z",
        **{name.title().replace("_", ""): value for name, value in metadata_fields(metadata)},
    }
    path.write_bytes(doc.to_bytes(info))
    return ExportSummary(
        kind=ExportKind.PDF_REPORT,
        path=path,
        lines=0,
        arcs=0,
        circles=0,
        vias=sum(len(b.vias) for b in boards),
        pads=sum(len(b.pads) for b in boards),
        holes=sum(len(b.outline.holes) for b in boards),
        pages=len(doc.pages),
    )
