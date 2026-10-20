"""U-V19 item 3: the width of the lower-layer copper that the layer cue paints, at zoom 0.1x and 200x (REQ-F-13).

    QT_QPA_PLATFORM=offscreen python3 tests/independent/m7/u_v19_f13_width.py

Prints the two measurements that the REQ-F-13 width tests of U-V19_id_map.md specify, on the 0.0.4 package:

- view, 200x: a 1280 x 800 GeometryView of D08 (dark, colour), fitted, then zoomed by 1.25 forty times to 200x and
  centred on leg 24 (L2, under ring 32 of L1) at the clear point of UI-58; the contrast to the board fill along the
  leg's normal at quarter-pixel steps; the span of samples above 1.3:1 against 0.6 mm times the view scale.
- cue item, 0.1x and 200x: one LayerCueItem level with a casing and an outline (a lower layer) of one 0.6 mm stroke,
  400 px long, rendered at 0.1 and 200 times that fit scale; per column the ink fraction summed across the stroke,
  and at 200x the span of pixels above an ink fraction of 0.1 in the middle column. At 0.1x the stroke is narrower
  than SOLID_BELOW_PX, so it is solid and its column sum is its width in pixels.
"""

import math
import sys
from pathlib import Path

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath
from PySide6.QtWidgets import QApplication, QGraphicsScene

APP = QApplication.instance() or QApplication([])

from embodic.api import compute_project  # noqa: E402 (a QApplication must exist first)
from embodic.ui.theme import load_theme  # noqa: E402
from embodic.ui.viewmodels.appearance import PhaseRenderMode  # noqa: E402
from embodic.ui.viewmodels.outcome import geometry_scene  # noqa: E402
from embodic.ui.views.geometry_view import GeometryView  # noqa: E402
from embodic.ui.views.layer_cue import LayerCueItem, Level, Part, Strokes  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
D08 = REPO / "resources/examples/spiral_12c10p_d08.embodic.json"
CROSSING_MM, CLEAR_R_MM = (-11.01, 47.19), 49.36  # test_layer_cue.py, UI-58
SIZE = (1280, 800)
INK = QColor("#c43b10")  # the dark colour run's phase ink of test_layer_cue.py RUNS


def _contrast(a: QColor, b: QColor) -> float:
    def lum(c: QColor) -> float:
        def ch(v: float) -> float:
            return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

        return 0.2126 * ch(c.redF()) + 0.7152 * ch(c.greenF()) + 0.0722 * ch(c.blueF())

    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def view_at_200x() -> float:
    """Measure leg 24 at 200x in the real view; return the fit scale in px/mm."""
    theme = load_theme("dark")
    fill = QColor(theme.colours["board-fill"])
    scene = geometry_scene(compute_project(D08))
    leg = next(p for p in scene.boards[0].paths if p.id == 24)
    (line,) = leg.primitives
    view = GeometryView()
    view.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    view.resize(*SIZE)
    view.show()
    view.show_geometry(scene, theme, PhaseRenderMode.COLOUR, frozenset())
    QApplication.processEvents()
    view.fit_view()
    QApplication.processEvents()
    fit = view.transform().m11()
    for _ in range(40):
        view.zoom_by(1.25)
    d = (line.x2_mm - line.x1_mm, line.y2_mm - line.y1_mm)
    tl = (d[0] / math.hypot(*d), d[1] / math.hypot(*d))
    x0, y0 = CROSSING_MM
    if x0 * tl[0] + y0 * tl[1] < 0:
        tl = (-tl[0], -tl[1])
    proj = x0 * tl[0] + y0 * tl[1]
    s = -proj + math.sqrt(proj**2 - (x0**2 + y0**2 - CLEAR_R_MM**2))
    cx, cy = x0 + s * tl[0], y0 + s * tl[1]
    view.centerOn(QPointF(cx, -cy))
    view.place_labels()
    QApplication.processEvents()
    image = view.viewport().grab().toImage().convertToFormat(QImage.Format.Format_RGB32)
    scale, origin = view.transform().m11(), view.mapFromScene(QPointF(0, 0))
    nx, ny = -tl[1], tl[0]

    def px(x: float, y: float) -> QColor:
        return image.pixelColor(math.floor(origin.x() + scale * x), math.floor(origin.y() + scale * -y))

    hits = [
        k
        for k in range(-4 * 420, 4 * 420 + 1)
        if _contrast(px(cx + nx * k / (4 * scale), cy + ny * k / (4 * scale)), fill) > 1.3
    ]
    span = (hits[-1] - hits[0] + 1) / 4
    print(
        f"view: fit {fit:.6f} px/mm, zoom {view.zoom_factor():.6f}x, scale {scale:.4f} px/mm; leg 24 width "
        f"{line.width_mm} mm; span {span} px against {line.width_mm * scale:.4f} px "
        f"({span - line.width_mm * scale:+.3f})"
    )
    view.close()
    return fit


def cue_item(fit: float) -> None:
    """Measure one isolated lower-layer cue stroke of 0.6 mm at 0.1x and 200x of the fit scale."""
    fill = QColor(load_theme("dark").colours["board-fill"])
    width = 0.6
    for factor in (0.1, 200.0):
        s = factor * fit
        for offset_px in (0.0, 0.13, 0.25, 0.5, 0.77):
            length = 400.0 / s
            centre = QPainterPath(QPointF(0.0, offset_px / s))
            centre.lineTo(length, (offset_px + 3.0) / s)
            strokes = Strokes.of([Part.of(width, centre)])
            scene = QGraphicsScene()
            scene.addItem(LayerCueItem([Level(casing=strokes, outlines=((INK, strokes),))], fill))
            half_h = max(20.0 / s, 2 * width)
            source = QRectF(length * 0.25, -half_h, length * 0.5, 2 * half_h)
            w_px, h_px = round(source.width() * s), round(source.height() * s)
            image = QImage(w_px, h_px, QImage.Format.Format_RGB32)
            image.fill(fill)
            painter = QPainter(image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            scene.render(painter, QRectF(0, 0, w_px, h_px), source, Qt.AspectRatioMode.IgnoreAspectRatio)
            painter.end()
            raw = np.frombuffer(image.constBits(), dtype=np.uint8).reshape(h_px, image.bytesPerLine() // 4, 4)
            bgr = raw[:, :w_px, :3].astype(float)
            f = np.array([fill.blue(), fill.green(), fill.red()], float)
            k = np.array([INK.blue(), INK.green(), INK.red()], float)
            alpha = ((bgr - f) @ (k - f)) / ((k - f) @ (k - f))
            columns = alpha.sum(axis=0)
            middle = np.nonzero(alpha[:, w_px // 2] > 0.1)[0]
            print(
                f"cue {factor}x: s {s:.4f} px/mm, offset {offset_px} px: true {width * s:.4f} px, column sum mean "
                f"{columns.mean():.4f} (min {columns.min():.4f}, max {columns.max():.4f}), middle-column span "
                f"{middle[-1] - middle[0] + 1 if middle.size else 0} px"
            )


if __name__ == "__main__":
    cue_item(view_at_200x())
    sys.exit(0)
