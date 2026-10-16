"""PDF design report (interfaces.md section 9.3; page structure after Xcoil buildReport, report.js l.230-352).

Pages: the stamp and "Key results" (every scalar result with value, unit and status word), the DRC summary, the
inputs with their provenance, then one vector drawing of each board. The report has no DRC confirmation in its
signature, so it never refuses for DRC; it states the DRC result instead.
"""

import dataclasses
import json
import math
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from pathlib import Path

from embodic.geometry.labels import Viewport, label_anchors, pad_boxes, place_labels
from embodic.geometry.layout import Layout
from embodic.geometry.marks import eye_marks, hatch_chords
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
from embodic.io.pdf_writer import PAGE_H, PAGE_W, PdfDocument, arc_bezier, circle_ops, rgb
from embodic.model.fields import field_for
from embodic.model.schema import design_values
from embodic.model.vocabulary import Phase
from embodic.outcome import ComputeOutcome
from embodic.results import AnalysisResult
from embodic.results.formatting import UNIT_SPACE, format_quantity
from embodic.results.labels import quantity_title
from embodic.results.traceable import Traceable
from embodic.units import Unit

MARGIN = 50.0
ROW = 11.0
DIMENSIONLESS = "dimensionless"  # the word the result cards print (D-042d)
INK = "#141414"
LAND = "#666666"
DRILL = "#ffffff"
PAPER = "#ffffff"  # the drawing leaves the board unfilled, so label halos take the paper's colour
LABEL_PT = 6.5
LABEL_HALO_PT = 1.6
HATCH_PITCH_PT = 0.4 * 72 / 25.4  # 0.4 mm on paper (design_spec.md section 3.3)
HATCH_STROKE_PT = 0.3
EYE_TINT = 0.1
SWATCH_R_PT = 4.0
COLOPHON = "Set in Inter and JetBrains Mono, SIL Open Font License 1.1."  # design_spec.md section 4, ruling f


def value_text(value: float, unit: Unit, *, significant: int = 3) -> str:
    """Return a value with its unit; a dimensionless value says so, a missing number keeps its unit."""
    symbol = unit.display() or DIMENSIONLESS
    if not math.isfinite(value):
        return f"n/a{UNIT_SPACE}{symbol}"
    text = format_quantity(value, unit, significant=significant)
    return text if unit.display() else f"{text}{UNIT_SPACE}{DIMENSIONLESS}"


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

    def row(self, cells: Sequence[tuple[float, str]], *, bold: bool = False, mono: Collection[int] = ()) -> None:
        self.need(ROW)
        self.doc.row(self.y, cells, bold=bold, mono=mono)
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
            ],
            mono=(1,),
        )


def _drc(flow: _Flow, outcome: ComputeOutcome) -> None:
    flow.heading("DRC summary")
    if outcome.drc is None:
        flow.row([(MARGIN, "DRC did not run.")])
        return
    for board, report in enumerate(outcome.drc, start=1):
        verdict = "passed" if report.passed else f"FAILED, {report.violation_count} violations"
        epsilon = f"{report.epsilon_mm}{UNIT_SPACE}mm"
        flow.row([(MARGIN, f"Board {board}: {verdict} (method {report.method}, epsilon {epsilon})")])
        flow.row(
            [(MARGIN, "Check"), (MARGIN + 130, "Least measured"), (MARGIN + 240, "Required"), (MARGIN + 330, "Pairs")],
            bold=True,
        )
        for s in report.summaries:
            # six figures, so a measured 0.19997 mm against a 0.2 mm rule does not print as 0.200 mm
            measured = (
                "none checked"
                if s.least_clearance_mm is None
                else value_text(s.least_clearance_mm, Unit.MM, significant=6)
            )
            flow.row(
                [
                    (MARGIN, s.kind.value),
                    (MARGIN + 130, measured),
                    (MARGIN + 240, value_text(s.required_mm, Unit.MM, significant=6)),
                    (MARGIN + 330, str(s.pairs_checked)),
                ],
                mono=(1, 2, 3),
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
            text = f"{text}{UNIT_SPACE}{unit.display() or DIMENSIONLESS}"
        entry = outcome.provenance.get(pointer)
        provenance = entry.provenance.value if entry is not None else "not recorded"
        flow.row([(MARGIN, pointer), (MARGIN + 230, text[:60]), (MARGIN + 380, provenance)], mono=(0, 1))


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


def tint_hex(colour_hex: str, fraction: float) -> str:
    """Return ``colour_hex`` laid over white paper at ``fraction`` coverage (the 10 % eye tint, opaque)."""
    channels = (int(colour_hex[i : i + 2], 16) for i in (1, 3, 5))
    return "#" + "".join(f"{round(255 - fraction * (255 - c)):02x}" for c in channels)


def _eye(doc: PdfDocument, x: float, y: float, r: float, colour: str, hatch_deg: int) -> None:
    """Fill an eye disc in page points: the phase A tint, or the B / C hatch clipped to the disc."""
    if hatch_deg == 0:
        doc.circle(x, y, r, fill_hex=tint_hex(colour, EYE_TINT))
        return
    chords = [
        f"{a[0]:.3f} {a[1]:.3f} m {b[0]:.3f} {b[1]:.3f} l" for a, b in hatch_chords(x, y, r, hatch_deg, HATCH_PITCH_PT)
    ]
    doc.op(f"q {circle_ops(x, y, r)} W n {rgb(colour)} RG {HATCH_STROKE_PT} w 0 J {' '.join(chords)} S Q")


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
    for mark in eye_marks(board):
        ink = inks[mark.phase]
        x, y, r = frame.x(mark.cx_mm), frame.y(mark.cy_mm), mark.eye_radius_mm * frame.scale
        _eye(doc, x, y, r, ink.grey_hex if grey else ink.colour_hex, ink.hatch_deg)
    _labels(doc, board, frame, reach * 1.04)
    _legend(doc, inks, grey)


def _labels(doc: PdfDocument, board: Layout, frame: _Frame, half_mm: float) -> None:
    """Coil labels of ruling b at the page scale (one point per viewport pixel), each over a paper halo."""
    view = Viewport(x_min_mm=-half_mm, y_min_mm=-half_mm, x_max_mm=half_mm, y_max_mm=half_mm, px_per_mm=frame.scale)
    placed = place_labels(
        label_anchors(board),
        view=view,
        text_size=lambda text: (doc.width(text, LABEL_PT), LABEL_PT),
        obstacles=pad_boxes(board),
        ring_outer_mm=board.envelope_mm[1],
    )
    for label in placed:
        if label.leader is not None:
            (ax, ay), (bx, by) = label.leader
            ops = [f"{frame.x(ax):.3f} {frame.y(ay):.3f} m", f"{frame.x(bx):.3f} {frame.y(by):.3f} l"]
            doc.stroke_path(ops, width=0.4, colour_hex=INK)
        doc.haloed_text(
            frame.x(label.x_mm),
            frame.y(label.y_mm),
            label.text,
            size=LABEL_PT,
            fill_hex=INK,
            halo_hex=PAPER,
            halo=LABEL_HALO_PT,
        )


def _legend(doc: PdfDocument, inks: dict[Phase | None, PhaseInk], grey: bool) -> None:
    """Phase key: a solid copper bar in the phase ink, the eye swatch and "Phase A" (copper is never dashed)."""
    y = MARGIN + 60
    for phase in Phase:
        ink = inks[phase]
        colour = ink.grey_hex if grey else ink.colour_hex
        doc.stroke_path([f"{MARGIN:.1f} {y:.1f} m", f"{MARGIN + 30:.1f} {y:.1f} l"], width=2.0, colour_hex=colour)
        _eye(doc, MARGIN + 42, y, SWATCH_R_PT, colour, ink.hatch_deg)
        doc.circle(MARGIN + 42, y, SWATCH_R_PT, fill_hex=None, stroke_hex=colour)
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
    doc.row(MARGIN, [(MARGIN, COLOPHON)])
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
