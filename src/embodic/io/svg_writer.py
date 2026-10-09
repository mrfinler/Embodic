"""SVG drawing of the boards (interfaces.md section 9.3; structure after Xcoil exportSvg, engine.js l.2796-2812).

Coordinates are the Layout's own: millimetres, y up, centred on the shaft axis. One ``scale(1,-1)`` group turns them
into SVG's y-down space, so every number in the file is a Layout number. Each copper layer holds one ``<g>`` per phase
with class and label; vias, pads and holes have a class each so a reader can count them.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from itertools import groupby
from pathlib import Path
from xml.sax.saxutils import quoteattr

from embodic.geometry.labels import PlacedLabel, Viewport, label_anchors, pad_boxes, place_labels
from embodic.geometry.layout import Layout, Pad
from embodic.geometry.marks import eye_marks, hatch_chords
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
from embodic.io.pdf_writer import SANS_FILE, bundled_font
from embodic.model.vocabulary import Phase
from embodic.outcome import ComputeOutcome

MARGIN_MM = 2.0
LEGEND_ROW_MM = 4.0
FONT_MM = 2.5
FONT_FAMILY = "Inter, 'Segoe UI', sans-serif"
LABEL_MM = 2.2
LABEL_HALO_MM = 0.5
LEADER_MM = 0.15
CSS_PX_PER_MM = 96 / 25.4  # the 1:1 page scale at which labels are placed
HATCH_PITCH_MM = 0.4  # at 1:1 print scale (design_spec.md section 3.3)
HATCH_STROKE_MM = 0.08
EYE_TINT = 0.1
SWATCH_R_MM = 1.3
PAPER = "#ffffff"  # the drawing leaves the board unfilled, so the halo takes the paper's colour
DRILL_FILL = "#ffffff"
LAND_FILL = "#666666"
INK = "#141414"


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
        label = f"Copper {layer} (z = {_n(board.copper_z_mm[layer])}\u00a0mm)"
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
    svg.out.append(f'<g class="outline" data-label="Board outline" stroke="{INK}" stroke-width="0.1">')
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
    svg.out.append("</g>")
    svg.out.append(f'<g id="{prefix}-eyes" class="eyes" data-label="Coil eyes">')
    for k, mark in enumerate(eye_marks(board)):
        ink = inks[mark.phase]
        colour = ink.grey_hex if grey else ink.colour_hex
        disc = (mark.cx_mm, mark.cy_mm, mark.eye_radius_mm)
        svg.out += _eye("eye", f"{prefix}-eye-{k}", mark.phase, disc, colour, ink.hatch_deg)
    svg.out.append("</g></g>")


def _eye(
    cls: str, clip_id: str, phase: Phase, disc: tuple[float, float, float], colour: str, hatch_deg: int
) -> list[str]:
    """Return the eye fill of a coil: a 10 % tint (phase A) or 0.4 mm hatch (B 45, C 135 degrees), clipped to it.

    The chords are in the frame of the enclosing group: y up inside the board drawing, y down in the legend, where the
    caller passes the angle mirrored so the hatch leans the same way on the page.
    """
    x, y, r = disc
    out = [f'<defs><clipPath id="{clip_id}"><circle cx="{_n(x)}" cy="{_n(y)}" r="{_n(r)}"/></clipPath></defs>']
    out.append(f'<g class="{cls}" data-phase="{phase.value}" clip-path="url(#{clip_id})">')
    if hatch_deg == 0:
        out.append(
            f'<circle cx="{_n(x)}" cy="{_n(y)}" r="{_n(r)}" fill="{colour}" fill-opacity="{_n(EYE_TINT)}" '
            'stroke="none"/>'
        )
    else:
        d = " ".join(
            f"M {_n(a[0])} {_n(a[1])} L {_n(b[0])} {_n(b[1])}"
            for a, b in hatch_chords(x, y, r, hatch_deg, HATCH_PITCH_MM)
        )
        out.append(f'<path class="hatch" d="{d}" fill="none" stroke="{colour}" stroke-width="{_n(HATCH_STROKE_MM)}"/>')
    out.append("</g>")
    return out


def _text_size_px(text: str) -> tuple[float, float]:
    """Width and height of a label at the 1:1 page scale, measured with the bundled Inter's advance widths."""
    return bundled_font(SANS_FILE).width_pt(text, LABEL_MM) * CSS_PX_PER_MM, LABEL_MM * CSS_PX_PER_MM


def _board_labels(board: Layout, view: Viewport) -> tuple[PlacedLabel, ...]:
    """Return the labels a drawing of ``board`` shows: ruling b's set, placed at the 1:1 page scale."""
    return place_labels(
        label_anchors(board),
        view=view,
        text_size=_text_size_px,
        obstacles=pad_boxes(board),
        ring_outer_mm=board.envelope_mm[1],
    )


def _labels(placed: Sequence[PlacedLabel]) -> list[str]:
    """Return the coil labels with a paper-coloured halo, in SVG's y-down space (text must not be mirrored).

    The halo is its own stroked ``<text>`` under the label: renderers without ``paint-order`` (QSvgRenderer) would
    otherwise paint the stroke over the letters.
    """
    font = bundled_font(SANS_FILE)
    lift = font.cap_height / font.units_per_em * LABEL_MM / 2
    out = [
        f'<g class="labels" font-family="{FONT_FAMILY}" font-size="{_n(LABEL_MM)}" text-anchor="middle" fill="{INK}">'
    ]
    for label in placed:
        if label.leader is not None:
            (ax, ay), (bx, by) = label.leader
            out.append(
                f'<line class="leader" x1="{_n(ax)}" y1="{_n(-ay)}" x2="{_n(bx)}" y2="{_n(-by)}" stroke="{INK}" '
                f'stroke-width="{_n(LEADER_MM)}"/>'
            )
        at = f'x="{_n(label.x_mm)}" y="{_n(-label.y_mm + lift)}"'
        out.append(
            f'<text class="coil-label-halo" {at} fill="none" stroke="{PAPER}" stroke-width="{_n(LABEL_HALO_MM)}" '
            f'stroke-linejoin="round">{label.text}</text>'
        )
        out.append(f'<text class="coil-label" data-phase="{label.phase.value}" {at}>{label.text}</text>')
    out.append("</g>")
    return out


def _legend(
    x0: float, y0: float, inks: dict[Phase | None, PhaseInk], grey: bool, metadata: ExportMetadata
) -> list[str]:
    """Phase key and version stamp below the board, in SVG's y-down space (text must not be mirrored).

    Per phase: a solid copper bar in the phase ink (copper is never dashed), the eye swatch and "Phase A".
    """
    out = [f'<g id="legend" font-family="{FONT_FAMILY}" font-size="{_n(FONT_MM)}" fill="{INK}">']
    for row, phase in enumerate(Phase):
        ink = inks[phase]
        y = y0 + row * LEGEND_ROW_MM
        colour = ink.grey_hex if grey else ink.colour_hex
        out.append(
            f'<line class="legend-copper" x1="{_n(x0)}" y1="{_n(y)}" x2="{_n(x0 + 6)}" y2="{_n(y)}" '
            f'stroke="{colour}" stroke-width="0.6"/>'
        )
        mirrored = (180 - ink.hatch_deg) % 180  # the legend is y down
        out += _eye("legend-eye", f"legend-eye-{phase.value}", phase, (x0 + 8.5, y, SWATCH_R_MM), colour, mirrored)
        out.append(
            f'<circle class="legend-eye-edge" cx="{_n(x0 + 8.5)}" cy="{_n(y)}" r="{_n(SWATCH_R_MM)}" fill="none" '
            f'stroke="{colour}" stroke-width="0.1"/>'
        )
        out.append(f'<text x="{_n(x0 + 11)}" y="{_n(y + 0.9)}">{ink.label}</text>')
    out.append(f'<text class="stamp" x="{_n(x0)}" y="{_n(y0 + 3 * LEGEND_ROW_MM + 0.9)}">{stamp_text(metadata)}</text>')
    out.append("</g>")
    return out


def stamp_text(metadata: ExportMetadata) -> str:
    """Return the footer line of a drawing: version, design hash and DRC verdict."""
    drc = "passed" if metadata.drc_passed else "FAILED"
    return f"embodic {metadata.embodic_version} | {metadata.design_hash} | DRC {drc}"


def svg_document(boards: Sequence[Layout], mode: PhaseRenderMode, metadata: ExportMetadata) -> tuple[str, _Counts]:
    """Return the SVG text of the boards and what it holds; pure, so the caller supplies the stamp."""
    inks = phase_inks()
    grey = mode is PhaseRenderMode.GREYSCALE_HATCH
    x_min, y_min, x_max, y_max = _bounds(boards)
    footer_mm = bundled_font(SANS_FILE).width_pt(stamp_text(metadata), FONT_MM)
    width = max(x_max - x_min, footer_mm) + 2 * MARGIN_MM
    legend_mm = 4 * LEGEND_ROW_MM + MARGIN_MM
    height = y_max - y_min + 2 * MARGIN_MM + legend_mm
    top = -(y_max + MARGIN_MM)
    view = Viewport(
        x_min_mm=x_min - MARGIN_MM,
        y_min_mm=y_min - MARGIN_MM,
        x_max_mm=x_max + MARGIN_MM,
        y_max_mm=y_max + MARGIN_MM,
        px_per_mm=CSS_PX_PER_MM,
    )
    stamp_attrs = " ".join(f"{name}={quoteattr(text)}" for name, text in metadata_fields(metadata))
    svg = _Svg()
    svg.out += [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:embodic="urn:embodic:export:1" width="{_n(width)}mm" '
        f'height="{_n(height)}mm" viewBox="{_n(x_min - MARGIN_MM)} {_n(top)} {_n(width)} {_n(height)}" '
        f'data-render-mode="{mode.value}">',
        "<title>embodic board drawing (mm, y up, centred on the shaft axis)</title>",
        f"<metadata><embodic:export {stamp_attrs}/></metadata>",
        '<g id="drawing" transform="scale(1,-1)" fill="none" stroke-linecap="round" stroke-linejoin="round">',
    ]
    for index, board in enumerate(boards, start=1):
        _board(svg, index, board, inks, grey)
    svg.out.append("</g>")
    for board in boards:
        svg.out += _labels(_board_labels(board, view))
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
