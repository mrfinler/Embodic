"""U-S16 lever: render layer-cue candidates for the geometry view offscreen, and measure them.

    PYTHONPATH=src QT_QPA_PLATFORM=offscreen /home/claude/embodic/.venv/bin/python \
        docs/phase3/design/checks/u_s16/u_s16_layer_cue_renders.py docs/phase3/design/checks/u_s16

Throwaway prototype, not product code. Each candidate is a subclass of the product's GeometryView that replaces only
the copper drawing, so the board, eyes, labels and legend are the product's own. Scenes: the user's D08 region
(x -41.0..50.6 mm, y -1.2..56.1 mm at 6 px/mm), the D08 ring-over-leg crossing at 24 px/mm, and the serpentine example
(6 copper layers) at fit scale and at 4x. Modes: colour and greyscale, dark theme (the user's screenshot), plus the
light theme in greyscale. Writes one contact sheet per scene and prints the measurements as JSON.
"""

import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPainterPath, QPainterPathStroker, QPen, QTransform
from PySide6.QtWidgets import QApplication, QGraphicsPathItem

from embodic.api import compute_project
from embodic.geometry.layout import Layout
from embodic.io.exporters import pad_outline
from embodic.ui.theme import load_theme
from embodic.ui.viewmodels.appearance import PhaseRenderMode
from embodic.ui.viewmodels.outcome import eyes_shown, geometry_scene
from embodic.ui.views.geometry_view import GeometryView, _disc, primitive_path

EXAMPLES = Path("resources/examples")
OPACITY_EVEN, OPACITY_ODD = 0.95, 0.62  # Xcoil v3 source/src/ui.js l.318
OUTLINE_PX = 1.5  # lower-layer outline, cosmetic
CASING_PX = 2.0  # board-coloured gap around an upper layer's copper


def luminance(image: QImage) -> np.ndarray:
    """WCAG relative luminance of every pixel of an RGB32 image."""
    raw = np.frombuffer(image.constBits(), dtype=np.uint8).reshape(image.height(), image.bytesPerLine() // 4, 4)
    rgb = raw[:, : image.width(), 2::-1].astype(float) / 255.0
    lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    return lin @ np.array([0.2126, 0.7152, 0.0722])


def contrast_to(image: QImage, colour: QColor) -> np.ndarray:
    """Contrast ratio of every pixel of ``image`` against one colour."""
    one = QImage(1, 1, QImage.Format.Format_RGB32)
    one.fill(colour)
    lum, ref = luminance(image), luminance(one)[0, 0]
    return (np.maximum(lum, ref) + 0.05) / (np.minimum(lum, ref) + 0.05)


def contrast(a: QColor, b: QColor) -> float:
    """WCAG 2.x contrast ratio of two opaque colours."""

    def lum(c: QColor) -> float:
        def ch(v: float) -> float:
            return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

        return 0.2126 * ch(c.redF()) + 0.7152 * ch(c.greenF()) + 0.0722 * ch(c.blueF())

    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def stroked(prims, extra_mm: float = 0.0) -> QPainterPath:
    """Return the true-width copper shapes of ``prims`` (each grown by ``extra_mm``) as one WindingFill path."""
    out = QPainterPath()
    for p in prims:
        st = QPainterPathStroker()
        st.setWidth(p.width_mm + extra_mm)
        st.setCapStyle(Qt.PenCapStyle.RoundCap)
        st.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        out.addPath(st.createStroke(primitive_path(p)))
    out.setFillRule(Qt.FillRule.WindingFill)
    return out


class InsetOutline(QGraphicsPathItem):
    """A copper shape drawn as its edge only, inside the true edge: the pen is clipped to the shape."""

    def __init__(self, shape: QPainterPath, colour: QColor) -> None:
        super().__init__(shape)
        self.fill_shape, self.ink = shape, colour

    def paint(self, painter, option, widget=None) -> None:
        """Stroke the shape's edge at twice the outline width, clipped to the shape."""
        painter.save()
        painter.setClipPath(self.fill_shape)
        pen = QPen(self.ink, 2 * OUTLINE_PX)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(self.fill_shape)
        painter.restore()


class Candidate(GeometryView):
    """The product view with one copper-drawing rule replaced; ``variant`` names the rule."""

    def __init__(self, variant: str, px_per_mm: float) -> None:
        super().__init__()
        self.variant, self.px_per_mm = variant, px_per_mm
        self.union_s = 0.0

    def _rebuild(self) -> None:
        scene = self.scene()
        scene.clear()
        self._label_items = []
        self._extent = QRectF()
        if self._geometry is None or self._tokens is None:
            return
        shown = self._shown()
        for board, _ in shown:
            self._draw_board(board)
        layers = self._geometry.layers
        visible = [layer for layer in layers if layer not in self._hidden]
        for layer in reversed(visible):
            for board, marks in shown:
                if self.variant == "now":
                    self._draw_copper(board, marks, layer)
                else:
                    self._draw_layer(board, layer, visible, layers.index(layer))
        if self.variant != "now":
            for board, _ in shown:
                self._draw_lands(board, visible)
        for board, marks in shown:
            for mark in eyes_shown(board, marks, self._hidden):
                self._draw_eye(mark)
        b = self._extent
        scene.setSceneRect(b.adjusted(-b.width(), -b.height(), b.width(), b.height()))

    def _groups(self, board: Layout, layer: str):
        groups: dict[str, list] = {}
        for path in (p for p in board.paths if p.layer == layer):
            groups.setdefault(self._copper_colour(path.phase).name(), []).extend(path.primitives)
        return groups

    def _draw_layer(self, board: Layout, layer: str, visible: list[str], index: int) -> None:
        many, top, bottom = len(visible) > 1, layer == visible[0], layer == visible[-1]
        board_fill = QColor(self._tokens.colours["board-fill"])
        no_pen = QPen(Qt.PenStyle.NoPen)
        groups = self._groups(board, layer)
        cased = many and self.variant in ("casing", "hybrid") and not bottom
        if cased:
            gap_mm = 2 * CASING_PX / self.px_per_mm
            casing = QPainterPath()
            for prims in groups.values():
                casing.addPath(stroked(prims, gap_mm))
            casing.setFillRule(Qt.FillRule.WindingFill)
            self._tag(self.scene().addPath(casing, no_pen, board_fill), "casing", layer)
        for name, prims in groups.items():
            colour = QColor(name)
            shape = stroked(prims)
            if self.variant == "opacity" and many:
                colour.setAlphaF(OPACITY_EVEN if index % 2 == 0 else OPACITY_ODD)
                item = self.scene().addPath(shape, no_pen, colour)
            elif self.variant in ("outline", "hybrid") and many and not top:
                started = time.perf_counter()
                union = shape.simplified()
                self.union_s += time.perf_counter() - started
                item = InsetOutline(union, colour)
                self.scene().addItem(item)
            else:
                item = self.scene().addPath(shape, no_pen, colour)
            self._tag(item, "copper", layer)

    def _draw_lands(self, board: Layout, visible: list[str]) -> None:
        no_pen = QPen(Qt.PenStyle.NoPen)
        via_fill = QColor(self._tokens.colours["text-3"])
        pad_fill = QColor(self._tokens.colours["text-2"])
        canvas = QColor(self._tokens.colours["canvas"])
        order = list(self._geometry.layers)
        for via in board.vias:
            span = order[order.index(via.layer_from) : order.index(via.layer_to) + 1]
            if any(layer in visible for layer in span):
                self._tag(self.scene().addEllipse(_disc(via.x_mm, via.y_mm, via.pad_mm / 2), no_pen, via_fill), "via")
        for pad in board.pads:
            if pad.layer is not None and pad.layer not in visible:
                continue
            if pad.shape == "round":
                item = self.scene().addEllipse(_disc(pad.x_mm, pad.y_mm, pad.width_mm / 2), no_pen, pad_fill)
            else:
                outline = QPainterPath()
                for q in pad_outline(pad):
                    seg = primitive_path(q)
                    if outline.elementCount() == 0:
                        outline.addPath(seg)
                    else:
                        outline.connectPath(seg)
                outline.closeSubpath()
                item = self.scene().addPath(outline, no_pen, pad_fill)
            self._tag(item, "pad")
            if pad.drill_mm > 0:
                self._tag(self.scene().addEllipse(_disc(pad.x_mm, pad.y_mm, pad.drill_mm / 2), no_pen, canvas), "drill")


def render(scene, tokens, mode, variant: str, centre_mm, px_per_mm: float, size_px, hidden=frozenset()) -> QImage:
    """Draw one candidate at a fixed scale around ``centre_mm`` and return the viewport image."""
    view = Candidate(variant, px_per_mm)
    view.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # the focus ring would draw over the viewport edge
    view.resize(*size_px)
    view.show()
    view.show_geometry(scene, tokens, mode, hidden)
    view.setTransform(QTransform.fromScale(px_per_mm, px_per_mm))
    view.centerOn(QPointF(centre_mm[0], -centre_mm[1]))
    view.place_labels()
    QApplication.processEvents()
    image = view.viewport().grab().toImage().convertToFormat(QImage.Format.Format_RGB32)
    transform = (view.transform(), view.mapFromScene(QPointF(0, 0)))
    boxes = [view.legend_rect(), view.stamp_rect()]
    for item in view._label_items:
        boxes.append(item.deviceTransform(view.viewportTransform()).mapRect(item.boundingRect()).adjusted(-3, -3, 3, 3))
    transform = (*transform, boxes)
    union_s = view.union_s
    view.close()
    view.deleteLater()
    return image, transform, union_s


def to_px(transform, x_mm: float, y_mm: float) -> tuple[float, float]:
    """Model millimetres to viewport pixels for a render made by ``render``."""
    t, origin = transform[0], transform[1]
    return origin.x() + t.m11() * x_mm, origin.y() + t.m22() * -y_mm


def sheet(cells: list[list[tuple[str, QImage]]], title: str) -> QImage:
    """Lay the cells out in a grid with a caption over each cell."""
    pad, cap = 8, 18
    w = max(img.width() for row in cells for _, img in row)
    h = max(img.height() for row in cells for _, img in row)
    cols = max(len(row) for row in cells)
    out = QImage(pad + cols * (w + pad), 26 + len(cells) * (h + cap + pad), QImage.Format.Format_RGB32)
    out.fill(QColor("#ffffff"))
    p = QPainter(out)
    font = QFont()
    font.setPixelSize(13)
    p.setFont(font)
    p.setPen(QColor("#141414"))
    p.drawText(pad, 18, title)
    for r, row in enumerate(cells):
        for c, (caption, img) in enumerate(row):
            x, y = pad + c * (w + pad), 26 + r * (h + cap + pad)
            p.drawText(x, y + 13, caption)
            p.drawImage(x, y + cap, img)
    p.end()
    return out


def leg_crossing_probe(image, transform, upper, lower, at_mm, board_hex: str, clear_r_mm: float) -> dict:
    """Measure where an upper-layer track crosses a lower-layer track of the same phase.

    The lower track is followed outward (increasing radius) from the crossing ``at_mm``. ``edge_contrast``: the largest
    contrast between the upper copper's pixel at the crossing and the pixels on the lower track's centre line 1 to 4 px
    beyond the upper track's edge. At radius ``clear_r_mm``, where the lower track is clear of other copper:
    ``lower_centre_px`` is the pixel on its centre line and ``lower_extent_px`` the span across it of pixels that differ
    from the board (contrast above 1.3), against ``lower_true_width_px``; ``lower_edge_ink_contrast`` is the largest
    contrast to the board on each side of the centre line (the outline's ink).
    """

    def tangent(p, x, y):
        if hasattr(p, "x1_mm"):
            d = (p.x2_mm - p.x1_mm, p.y2_mm - p.y1_mm)
        else:
            a = math.atan2(y - p.cy_mm, x - p.cx_mm)
            d = (-math.sin(a), math.cos(a))
        n = math.hypot(*d)
        return d[0] / n, d[1] / n

    def px(x, y) -> QColor:
        u, v = to_px(transform, x, y)
        return image.pixelColor(math.floor(u), math.floor(v))

    x0, y0 = at_mm
    tu, tl = tangent(upper, x0, y0), tangent(lower, x0, y0)
    if x0 * tl[0] + y0 * tl[1] < 0:
        tl = (-tl[0], -tl[1])
    sin_t = abs(tu[0] * tl[1] - tu[1] * tl[0])
    edge_mm = upper.width_mm / 2 / max(sin_t, 1e-6)
    scale = transform[0].m11()
    upper_c = px(x0, y0)
    board = QColor(board_hex)
    band = [px(x0 + (edge_mm + k / scale) * tl[0], y0 + (edge_mm + k / scale) * tl[1]) for k in range(1, 5)]
    proj = x0 * tl[0] + y0 * tl[1]
    s_clear = -proj + math.sqrt(proj**2 - (x0**2 + y0**2 - clear_r_mm**2))
    cx, cy = x0 + s_clear * tl[0], y0 + s_clear * tl[1]
    nx, ny = -tl[1], tl[0]
    across = {k: contrast(px(cx + nx * k / (4 * scale), cy + ny * k / (4 * scale)), board) for k in range(-60, 61)}
    hits = [k for k, c in across.items() if c > 1.3]
    return {
        "upper_px": upper_c.name(),
        "edge_band_px": [c.name() for c in band],
        "edge_contrast": round(max(contrast(upper_c, c) for c in band), 2),
        "lower_centre_px": px(cx, cy).name(),
        "lower_extent_px": (hits[-1] - hits[0] + 1) / 4 if hits else 0,
        "lower_edge_ink_contrast": [
            round(max(c for k, c in across.items() if k < 0), 2),
            round(max(c for k, c in across.items() if k > 0), 2),
        ],
        "lower_true_width_px": round(lower.width_mm * scale, 2),
    }


def band_violations(view_state, image: QImage, scene, hidden=frozenset()) -> tuple[int, int]:
    """Pixels of ink in the band 0.75 to 1.5 px outside each visible layer's copper, except the bottom one.

    The band leaves out the copper of the layers above that layer, every land, and the legend, stamp and label boxes.
    A pixel counts when its contrast to the board fill is above 1.1. Zero means no lower-layer copper touches the
    copper of a layer above it on screen. Returns (violations, band pixels).
    """
    transform, origin, boxes, board_hex, scale = view_state
    board_fill = QColor(board_hex)
    visible = [layer for layer in scene.layers if layer not in hidden]
    violations = band_px = 0
    for k, layer in enumerate(visible[:-1]):
        mask = QImage(image.size(), QImage.Format.Format_RGB32)
        mask.fill(QColor("#000000"))
        p = QPainter(mask)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        p.setTransform(QTransform(transform.m11(), 0, 0, transform.m22(), origin.x(), origin.y()))
        p.setPen(Qt.PenStyle.NoPen)
        for board in scene.boards:
            mine = [q for path in board.paths if path.layer == layer for q in path.primitives]
            p.setBrush(QColor("#ffffff"))
            p.drawPath(stroked(mine, 2 * 1.5 / scale))
            p.setBrush(QColor("#000000"))
            p.drawPath(stroked(mine, 2 * 0.75 / scale))
            above = [q for path in board.paths if path.layer in visible[:k] for q in path.primitives]
            p.drawPath(stroked(above, 2 * 1.0 / scale))
            for via in board.vias:
                p.drawEllipse(_disc(via.x_mm, via.y_mm, via.pad_mm / 2 + 2.0 / scale))
            for pad in board.pads:
                r = max(pad.width_mm, pad.height_mm) / 2 + 2.0 / scale
                p.drawEllipse(_disc(pad.x_mm, pad.y_mm, r))
        for board, marks in zip(scene.boards, scene.marks, strict=True):
            for mark in eyes_shown(board, marks, hidden):
                p.drawEllipse(_disc(mark.cx_mm, mark.cy_mm, mark.eye_radius_mm + 1.0 / scale))
        p.resetTransform()
        for box in boxes:
            p.drawRect(box)
        p.end()
        inside = luminance(mask) > 0.5
        band_px += int(np.count_nonzero(inside))
        violations += int(np.count_nonzero(inside & (contrast_to(image, board_fill) > 1.1)))
    return violations, band_px


def main(argv: list[str]) -> int:
    """Render every candidate in every scene and mode into argv[0], with the measurements."""
    out = Path(argv[0])
    out.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    themes = {"dark": load_theme("dark"), "light": load_theme("light")}
    modes = [
        ("dark colour", "dark", PhaseRenderMode.COLOUR),
        ("dark greyscale", "dark", PhaseRenderMode.GREYSCALE_HATCH),
        ("light greyscale", "light", PhaseRenderMode.GREYSCALE_HATCH),
    ]
    variants = [("now", "0.0.3 as shipped"), ("opacity", "A: per-layer opacity (Xcoil)"),
                ("outline", "B: top layer solid, lower layers outlined"),
                ("casing", "C: every layer cased over the ones below"),
                ("hybrid", "D = B + C: outlined and cased")]  # fmt: skip
    d08 = geometry_scene(compute_project(EXAMPLES / "spiral_12c10p_d08.embodic.json"))
    serp = geometry_scene(compute_project(EXAMPLES / "serpentine_16p_example.embodic.json"))
    board = d08.boards[0]
    ring = next(p for p in board.paths if p.id == 32)
    leg = next(p for p in board.paths if p.id == 24)
    at = (-11.01, 47.19)
    upper = min(ring.primitives, key=lambda q: _dist(q, at))
    lower = min(leg.primitives, key=lambda q: _dist(q, at))
    scenes = [
        ("d08_region", d08, (4.8, 27.45), 6.0, (560, 352)),
        ("d08_crossing", d08, at, 24.0, (420, 300)),
        ("serpentine_fit", serp, (0.0, 0.0), 5.0, (480, 480)),
        ("serpentine_4x", serp, (0.0, 33.0), 20.0, (480, 320)),
    ]
    record: dict = {
        "d08_crossing_note": "ring A path 32 (L1, 1.0 mm) over leg 24 (L2, 0.6 mm) at (-11.01, 47.19), clear r 49.36",
        "d08_crossing": {},
        "union_seconds": {},
        "band_violations": {},
    }
    for name, scene, centre, scale, size in scenes:
        rows = []
        for variant, caption in variants:
            row = []
            for mode_name, theme, mode in modes:
                image, transform, union_s = render(scene, themes[theme], mode, variant, centre, scale, size)
                row.append((f"{caption}, {mode_name}", image))
                key = f"{variant} | {mode_name}"
                board_hex = themes[theme].colours["board-fill"]
                if name != "d08_crossing":
                    state = (transform[0], transform[1], transform[2], board_hex, scale)
                    record["band_violations"][f"{name} | {key}"] = band_violations(state, image, scene)
                if union_s:
                    record["union_seconds"][f"{name} | {key}"] = round(union_s, 3)
                if name == "d08_crossing":
                    record["d08_crossing"][key] = leg_crossing_probe(
                        image, transform, upper, lower, at, board_hex, clear_r_mm=49.36
                    )
            rows.append(row)
        title = f"U-S16 layer cue candidates: {name.replace('_', ' ')} ({scale:g} px/mm), all copper layers visible"
        sheet(rows, title).save(str(out / f"u_s16_{name}.png"))
    (out / "u_s16_measurements.json").write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=1))
    app.processEvents()
    return 0


def _dist(q, at) -> float:
    x, y = at
    if hasattr(q, "x1_mm"):
        ax, ay, bx, by = q.x1_mm, q.y1_mm, q.x2_mm, q.y2_mm
        t = max(0.0, min(1.0, ((x - ax) * (bx - ax) + (y - ay) * (by - ay)) / ((bx - ax) ** 2 + (by - ay) ** 2)))
        return math.hypot(x - ax - t * (bx - ax), y - ay - t * (by - ay))
    return abs(math.hypot(x - q.cx_mm, y - q.cy_mm) - q.r_mm)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
