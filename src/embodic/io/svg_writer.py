"""SVG drawing of the boards (interfaces.md section 9.3; structure after Xcoil exportSvg, engine.js l.2796-2812).

Coordinates are the Layout's own: millimetres, y up, centred on the shaft axis. One ``scale(1,-1)`` group turns them
into SVG's y-down space, so every number in the file is a Layout number. Each copper layer holds one ``<g>`` per phase
with class and label; vias, pads and holes have a class each so a reader can count them.
"""

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from itertools import groupby
from pathlib import Path
from xml.sax.saxutils import quoteattr

from embodic.geometry.layout import Layout, Pad
from embodic.geometry.paths import CopperPath
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
    is_full_circle,
    metadata_fields,
    pad_outline,
    phase_inks,
)
from embodic.model.vocabulary import Phase
from embodic.outcome import ComputeOutcome

MARGIN_MM = 2.0
LEGEND_ROW_MM = 4.0
FONT_MM = 2.5
DRILL_FILL = "#ffffff"
LAND_FILL = "#666666"
OUTLINE_STROKE = "#141414"
DASH_ARRAY = {"solid": None, "dash": "1.2 0.6", "dot": "0.3 0.6"}  # legend samples, mm


def _n(value: float) -> str:
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


@dataclass(slots=True)
class _Counts:
    lines: int = 0
    arcs: int = 0
    circles: int = 0
    vias: int = 0
    pads: int = 0
    holes: int = 0


@dataclass(slots=True)
class _Svg:
    counts: _Counts = field(default_factory=_Counts)
    out: list[str] = field(default_factory=list)

    def path_data(self, prims: Sequence[Primitive], *, close: bool = False) -> str:
        """Return ``d`` for a chain; a gap above 1e-6 mm starts a new subpath."""
        parts: list[str] = []
        here: tuple[float, float] | None = None
        for q in prims:
            start = q.start_point()
            if here is None or math.dist(here, start) > 1e-6:
                parts.append(f"M {_n(start[0])} {_n(start[1])}")
            if isinstance(q, Line):
                parts.append(f"L {_n(q.x2_mm)} {_n(q.y2_mm)}")
                self.counts.lines += 1
            else:
                parts.extend(_arc_commands(q))
                self.counts.arcs += 1
            here = q.end_point()
        if close:
            parts.append("Z")
        return " ".join(parts)

    def circle(self, cls: str, x: float, y: float, r: float, fill: str) -> None:
        self.out.append(f'<circle class="{cls}" cx="{_n(x)}" cy="{_n(y)}" r="{_n(r)}" fill="{fill}" stroke="none"/>')
        self.counts.circles += 1


def _arc_commands(arc: Arc) -> list[str]:
    """SVG arcs in the y-up frame: sweep flag 1 is counter-clockwise; a full circle is drawn as two halves."""
    sweep_flag = 1 if arc.sweep_rad > 0 else 0
    r = _n(arc.r_mm)
    if is_full_circle(arc):
        mid, end = arc.mid_point(), arc.end_point()
        return [f"A {r} {r} 0 0 {sweep_flag} {_n(p[0])} {_n(p[1])}" for p in (mid, end)]
    large = 1 if abs(arc.sweep_rad) > math.pi else 0
    x, y = arc.end_point()
    return [f"A {r} {r} 0 {large} {sweep_flag} {_n(x)} {_n(y)}"]


def _bounds(boards: Sequence[Layout]) -> tuple[float, float, float, float]:
    xs: list[float] = []
    ys: list[float] = []
    for board in boards:
        for q in board.outline.outer:
            if isinstance(q, Line):
                xs += [q.x1_mm, q.x2_mm]
                ys += [q.y1_mm, q.y2_mm]
            else:
                xs += [q.cx_mm - q.r_mm, q.cx_mm + q.r_mm]
                ys += [q.cy_mm - q.r_mm, q.cy_mm + q.r_mm]
    return min(xs), min(ys), max(xs), max(ys)


def _phase_key(path: CopperPath) -> int:
    return -1 if path.phase is None else list(Phase).index(path.phase)


def _copper(svg: _Svg, prefix: str, board: Layout, inks: dict[Phase | None, PhaseInk], grey: bool) -> None:
    for layer in board.copper_layers:
        on_layer = sorted((p for p in board.paths if p.layer == layer), key=_phase_key)
        label = f"Copper {layer} (z = {_n(board.copper_z_mm[layer])} mm)"
        svg.out.append(
            f'<g id="{prefix}-cu-{layer}" class="layer" data-layer={quoteattr(layer)} data-label={quoteattr(label)}>'
        )
        for phase, members in groupby(on_layer, key=lambda p: p.phase):
            ink = inks[phase]
            name = "none" if phase is None else phase.value
            stroke = ink.grey_hex if grey else ink.colour_hex
            svg.out.append(
                f'<g class="phase phase-{name.lower()}" data-phase="{name}" data-label={quoteattr(ink.label)} '
                f'stroke="{stroke}">'
            )
            for path in members:
                svg.out.append(f'<g class="copper" data-path-id="{path.id}" data-net={quoteattr(path.net)}>')
                for width, run in groupby(path.primitives, key=lambda q: q.width_mm):
                    svg.out.append(f'<path stroke-width="{_n(width)}" d="{svg.path_data(list(run))}"/>')
                svg.out.append("</g>")
            svg.out.append("</g>")
        svg.out.append("</g>")


def _pad(svg: _Svg, pad: Pad) -> None:
    if pad.shape == "round":
        svg.circle("pad", pad.x_mm, pad.y_mm, pad.width_mm / 2, LAND_FILL)
    else:
        d = svg.path_data(pad_outline(pad), close=True)
        svg.out.append(f'<path class="pad" d="{d}" fill="{LAND_FILL}" stroke="none"/>')
    svg.counts.pads += 1
    if pad.drill_mm > 0:
        svg.circle("pad-drill", pad.x_mm, pad.y_mm, pad.drill_mm / 2, DRILL_FILL)


def _board(svg: _Svg, index: int, board: Layout, inks: dict[Phase | None, PhaseInk], grey: bool) -> None:
    prefix = f"b{index}"
    svg.out.append(f'<g id="board-{index}" class="board" data-label="Board {index}">')
    svg.out.append(f'<g class="outline" data-label="Board outline" stroke="{OUTLINE_STROKE}" stroke-width="0.1">')
    svg.out.append(f'<path class="outline-outer" d="{svg.path_data(board.outline.outer, close=True)}"/>')
    for loop in board.outline.cutouts:
        svg.out.append(f'<path class="cutout" d="{svg.path_data(loop, close=True)}"/>')
    for hole in board.outline.holes:
        svg.out.append(
            f'<circle class="hole" data-label={quoteattr(hole.label)} cx="{_n(hole.x_mm)}" cy="{_n(hole.y_mm)}" '
            f'r="{_n(hole.diameter_mm / 2)}"/>'
        )
        svg.counts.circles += 1
        svg.counts.holes += 1
    svg.out.append("</g>")
    _copper(svg, prefix, board, inks, grey)
    svg.out.append(f'<g id="{prefix}-vias" class="vias" data-label="Vias">')
    for via in board.vias:
        svg.circle("via", via.x_mm, via.y_mm, via.pad_mm / 2, LAND_FILL)
        svg.circle("via-drill", via.x_mm, via.y_mm, via.drill_mm / 2, DRILL_FILL)
        svg.counts.vias += 1
    svg.out.append("</g>")
    svg.out.append(f'<g id="{prefix}-pads" class="pads" data-label="Terminal pads">')
    for pad in board.pads:
        _pad(svg, pad)
    svg.out.append("</g></g>")


def _hatch_defs(inks: Iterable[PhaseInk]) -> list[str]:
    out = ["<defs>"]
    for ink in inks:
        if ink.hatch_deg and ink.phase is not None:
            out.append(
                f'<pattern id="hatch-{ink.phase.value}" patternUnits="userSpaceOnUse" width="0.8" height="0.8" '
                f'patternTransform="rotate({ink.hatch_deg})"><line x1="0" y1="0" x2="0" y2="0.8" '
                f'stroke="{ink.grey_hex}" stroke-width="0.25"/></pattern>'
            )
    out.append("</defs>")
    return out


def _legend(
    x0: float, y0: float, inks: dict[Phase | None, PhaseInk], grey: bool, metadata: ExportMetadata
) -> list[str]:
    """Phase key and version stamp below the board, in SVG's y-down space (text must not be mirrored)."""
    out = [f'<g id="legend" font-family="Helvetica, Arial, sans-serif" font-size="{_n(FONT_MM)}" fill="#141414">']
    for row, phase in enumerate(Phase):
        ink = inks[phase]
        y = y0 + row * LEGEND_ROW_MM
        colour = ink.grey_hex if grey else ink.colour_hex
        dash = DASH_ARRAY[ink.dash]
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        out.append(
            f'<line x1="{_n(x0)}" y1="{_n(y)}" x2="{_n(x0 + 6)}" y2="{_n(y)}" stroke="{colour}" stroke-width="0.6"'
            f"{dash_attr}/>"
        )
        if grey and ink.hatch_deg:
            out.append(
                f'<rect x="{_n(x0 + 7)}" y="{_n(y - 1.5)}" width="3" height="3" fill="url(#hatch-{phase.value})" '
                f'stroke="{colour}" stroke-width="0.1"/>'
            )
        out.append(f'<text x="{_n(x0 + 11)}" y="{_n(y + 0.9)}">{ink.label}</text>')
    drc = "passed" if metadata.drc_passed else "FAILED"
    stamp = f"embodic {metadata.embodic_version} | {metadata.design_hash} | DRC {drc}"
    out.append(f'<text x="{_n(x0)}" y="{_n(y0 + 3 * LEGEND_ROW_MM + 0.9)}">{stamp}</text>')
    out.append("</g>")
    return out


def svg_document(boards: Sequence[Layout], mode: PhaseRenderMode, metadata: ExportMetadata) -> tuple[str, _Counts]:
    """Return the SVG text of the boards and what it holds; pure, so the caller supplies the stamp."""
    inks = phase_inks()
    grey = mode is PhaseRenderMode.GREYSCALE_HATCH
    x_min, y_min, x_max, y_max = _bounds(boards)
    width = x_max - x_min + 2 * MARGIN_MM
    legend_mm = 4 * LEGEND_ROW_MM + MARGIN_MM
    height = y_max - y_min + 2 * MARGIN_MM + legend_mm
    top = -(y_max + MARGIN_MM)
    stamp_attrs = " ".join(f"{name}={quoteattr(text)}" for name, text in metadata_fields(metadata))
    svg = _Svg()
    svg.out += [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:embodic="urn:embodic:export:1" width="{_n(width)}mm" '
        f'height="{_n(height)}mm" viewBox="{_n(x_min - MARGIN_MM)} {_n(top)} {_n(width)} {_n(height)}" '
        f'data-render-mode="{mode.value}">',
        "<title>embodic board drawing (mm, y up, centred on the shaft axis)</title>",
        f"<metadata><embodic:export {stamp_attrs}/></metadata>",
        *(_hatch_defs(inks.values()) if grey else []),
        '<g id="drawing" transform="scale(1,-1)" fill="none" stroke-linecap="round" stroke-linejoin="round">',
    ]
    for index, board in enumerate(boards, start=1):
        _board(svg, index, board, inks, grey)
    svg.out.append("</g>")
    svg.out += _legend(x_min, -(y_min - MARGIN_MM) + LEGEND_ROW_MM, inks, grey, metadata)
    svg.out.append("</svg>")
    return "\n".join(svg.out) + "\n", svg.counts


def write_svg(
    outcome: ComputeOutcome,
    path: Path,
    *,
    mode: PhaseRenderMode = PhaseRenderMode.COLOUR,
    allow_drc_errors: bool = False,
) -> ExportSummary | ExportRefused:
    """Write the SVG drawing of every board; refuse without a layout or with an unconfirmed failed DRC."""
    boards = exportable_boards(outcome, allow_drc_errors=allow_drc_errors)
    if isinstance(boards, ExportRefused):
        return boards
    text, counts = svg_document(boards, mode, export_metadata(outcome))
    path.write_text(text, encoding="utf-8", newline="\n")
    return ExportSummary(
        kind=ExportKind.SVG,
        path=path,
        lines=counts.lines,
        arcs=counts.arcs,
        circles=counts.circles,
        vias=counts.vias,
        pads=counts.pads,
        holes=counts.holes,
        pages=0,
    )
