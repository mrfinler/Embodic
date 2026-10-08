"""DXF R12 ASCII drawings: complete board, outline only, screws only (interfaces.md section 9.3).

Structure after Xcoil DxfWriter (engine.js l.2823-2876): LINE, ARC and CIRCLE in millimetres, y up, centred on the
shaft axis. Copper is written as centre lines; the layer name ends with the trace width in micrometres (``_W400`` is a
0.40 mm trace), so a CAD user can rebuild the copper. The REQ-T-07 stamp is a run of 999 comments at the top.
"""

import math
import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from embodic.geometry.layout import Layout
from embodic.geometry.primitives import Arc, Line, Primitive, primitive_length_mm
from embodic.io.exporters import (
    ExportKind,
    ExportMetadata,
    ExportRefused,
    ExportSummary,
    export_metadata,
    exportable_boards,
    is_full_circle,
    metadata_fields,
    no_screws,
    pad_outline,
)
from embodic.outcome import ComputeOutcome

DxfPart = Literal["complete", "outline", "screws"]
_KIND: dict[DxfPart, ExportKind] = {
    "complete": ExportKind.DXF_COMPLETE,
    "outline": ExportKind.DXF_OUTLINE,
    "screws": ExportKind.DXF_SCREWS,
}
DEGENERATE_MM = 1e-9


def _n(value: float) -> str:
    text = f"{value:.9f}".rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def _layer_name(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", text).upper()


@dataclass(slots=True)
class DxfDrawing:
    """Entities and the layers they use, in first-use order."""

    layers: list[str] = field(default_factory=list)
    body: list[str] = field(default_factory=list)
    lines: int = 0
    arcs: int = 0
    circles: int = 0

    def _tags(self, *pairs: tuple[int, str]) -> None:
        for code, value in pairs:
            self.body += [str(code), value]

    def _use(self, layer: str) -> str:
        if layer not in self.layers:
            self.layers.append(layer)
        return layer

    def circle(self, layer: str, x: float, y: float, r: float) -> None:
        """Write a circle of radius ``r`` about (x, y)."""
        self._tags((0, "CIRCLE"), (8, self._use(layer)), (10, _n(x)), (20, _n(y)), (30, "0"), (40, _n(r)))
        self.circles += 1

    def prim(self, layer: str, q: Primitive) -> None:
        """Write a line, an arc, or a circle for an arc that closes on itself; skip a zero-length primitive."""
        if primitive_length_mm(q) < DEGENERATE_MM:
            return
        if isinstance(q, Line):
            self._tags(
                (0, "LINE"), (8, self._use(layer)), (10, _n(q.x1_mm)), (20, _n(q.y1_mm)), (30, "0"),
                (11, _n(q.x2_mm)), (21, _n(q.y2_mm)), (31, "0"),
            )  # fmt: skip
            self.lines += 1
            return
        if is_full_circle(q):
            self.circle(layer, q.cx_mm, q.cy_mm, q.r_mm)
            return
        self._arc(layer, q)

    def _arc(self, layer: str, q: Arc) -> None:
        """DXF arcs run counter-clockwise from code 50 to code 51, so a clockwise sweep swaps its ends."""
        a1, a2 = sorted((q.start_rad, q.start_rad + q.sweep_rad))
        start_deg, end_deg = (math.degrees(a) % 360.0 for a in (a1, a2))
        self._tags(
            (0, "ARC"), (8, self._use(layer)), (10, _n(q.cx_mm)), (20, _n(q.cy_mm)), (30, "0"), (40, _n(q.r_mm)),
            (50, _n(start_deg)), (51, _n(end_deg)),
        )  # fmt: skip
        self.arcs += 1

    def text(self, metadata: ExportMetadata) -> str:
        """Return the whole file: stamp comments, header, layer table, entities."""
        head = ["999", "embodic export (DXF R12, millimetres, y up, centred on the shaft axis)"]
        for name, value in metadata_fields(metadata):
            head += ["999", f"{name}={value}"]
        head += ["0", "SECTION", "2", "HEADER", "9", "$ACADVER", "1", "AC1009", "9", "$INSUNITS", "70", "4"]
        head += ["0", "ENDSEC", "0", "SECTION", "2", "TABLES"]
        head += ["0", "TABLE", "2", "LTYPE", "70", "1"]
        head += ["0", "LTYPE", "2", "CONTINUOUS", "70", "0", "3", "Solid line", "72", "65", "73", "0", "40", "0.0"]
        head += ["0", "ENDTAB", "0", "TABLE", "2", "LAYER", "70", str(len(self.layers))]
        for i, name in enumerate(self.layers):
            head += ["0", "LAYER", "2", name, "70", "0", "62", str(i % 7 + 1), "6", "CONTINUOUS"]
        head += ["0", "ENDTAB", "0", "ENDSEC", "0", "SECTION", "2", "ENTITIES"]
        return "\n".join([*head, *self.body, "0", "ENDSEC", "0", "EOF"]) + "\n"


def _outline(dxf: DxfDrawing, prefix: str, board: Layout) -> None:
    for q in board.outline.outer:
        dxf.prim(f"{prefix}BOARD_OUTLINE", q)
    for loop in board.outline.cutouts:
        for q in loop:
            dxf.prim(f"{prefix}CUTOUT", q)


def _screws(dxf: DxfDrawing, prefix: str, board: Layout) -> None:
    for hole in board.outline.holes:
        dxf.circle(f"{prefix}SCREW_{_layer_name(hole.label)}", hole.x_mm, hole.y_mm, hole.diameter_mm / 2)


def _copper_and_lands(dxf: DxfDrawing, prefix: str, board: Layout) -> None:
    index = {layer: i for i, layer in enumerate(board.copper_layers, start=1)}
    for path in board.paths:
        group = "IC" if path.phase is None else f"PH_{path.phase.value}"
        for q in path.primitives:
            layer = f"{prefix}CU{index[path.layer]}_{path.layer}_{group}_W{round(q.width_mm * 1000)}"
            dxf.prim(_layer_name(layer), q)
    for via in board.vias:
        dxf.circle(f"{prefix}VIA_PAD", via.x_mm, via.y_mm, via.pad_mm / 2)
        dxf.circle(f"{prefix}VIA_DRILL", via.x_mm, via.y_mm, via.drill_mm / 2)
    for pad in board.pads:
        if pad.shape == "round":
            dxf.circle(f"{prefix}PAD", pad.x_mm, pad.y_mm, pad.width_mm / 2)
        else:
            for q in pad_outline(pad):
                dxf.prim(f"{prefix}PAD", q)
        if pad.drill_mm > 0:
            dxf.circle(f"{prefix}PAD_DRILL", pad.x_mm, pad.y_mm, pad.drill_mm / 2)


def dxf_drawing(boards: Sequence[Layout], part: DxfPart) -> DxfDrawing:
    """Return the entities of one part; layer names gain a ``B<k>_`` prefix only on a stack of several boards."""
    dxf = DxfDrawing()
    for k, board in enumerate(boards, start=1):
        prefix = f"B{k}_" if len(boards) > 1 else ""
        if part in ("complete", "outline"):
            _outline(dxf, prefix, board)
        if part in ("complete", "screws"):
            _screws(dxf, prefix, board)
        if part == "complete":
            _copper_and_lands(dxf, prefix, board)
    return dxf


def write_dxf(
    outcome: ComputeOutcome, path: Path, part: DxfPart, *, allow_drc_errors: bool = False
) -> ExportSummary | ExportRefused:
    """Write one DXF part; refuse without a layout, with an unconfirmed failed DRC, or for screws on a board without."""
    boards = exportable_boards(outcome, allow_drc_errors=allow_drc_errors)
    if isinstance(boards, ExportRefused):
        return boards
    holes = sum(len(b.outline.holes) for b in boards)
    if part == "screws" and holes == 0:
        return no_screws()
    dxf = dxf_drawing(boards, part)
    path.write_text(dxf.text(export_metadata(outcome)), encoding="ascii", newline="\n")
    complete = part == "complete"
    return ExportSummary(
        kind=_KIND[part],
        path=path,
        lines=dxf.lines,
        arcs=dxf.arcs,
        circles=dxf.circles,
        vias=sum(len(b.vias) for b in boards) if complete else 0,
        pads=sum(len(b.pads) for b in boards) if complete else 0,
        holes=0 if part == "outline" else holes,
        pages=0,
    )
