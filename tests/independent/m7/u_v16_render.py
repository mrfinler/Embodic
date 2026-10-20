"""U-V16: render the D08 copper of the screenshot region per layer at true track width, from the DXF export.

usage: PYTHONPATH=src QT_QPA_PLATFORM=offscreen python tests/independent/m7/u_v16_render.py OUT_DIR

The shapes come from ``u_v16_copper.read_copper`` (own DXF reader), not from the product's view code. Each trace is a
QPainter stroke of its own width with round caps; vias and pads are discs of their land diameter. Colours: phase A red,
B blue, C green, interconnect grey, lands light grey. Writes, for each scale:

- ``U-V16_D08_L1_<scale>.png`` and ``U-V16_D08_L2_<scale>.png``: one copper layer each, lands on both;
- ``U-V16_D08_L1+L2_overlaid_<scale>.png``: both layers in the same phase colours, L1 painted over L2, as one plane.

Region: x -41.0..50.6 mm, y -1.2..56.1 mm, the area of the user's screenshot (hub of radius 10 mm about 60 px wide
there, so 5.97 px/mm). The hub close-up of spot 1 is x -8..2 mm, y 9..17 mm.
"""

import math
import sys
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter, QPainterPath, QPen

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from u_v16_copper import EXAMPLES, check_example  # noqa: E402

sys.path.insert(0, str(HERE.parent / "m1"))
from records import Arc  # noqa: E402

COLOUR = {"PH_A": "#c8401a", "PH_B": "#1a66f0", "PH_C": "#15a860", "IC": "#a0a0a0", "": "#d8d8d8"}
BACKGROUND = "#1e1e1e"
REGIONS = {
    "screenshot_6pxmm": ((-41.0, 50.6, -1.2, 56.1), 5.97),
    "screenshot_20pxmm": ((-41.0, 50.6, -1.2, 56.1), 20.0),
    "hub_spot1_80pxmm": ((-8.0, 2.0, 9.0, 17.0), 80.0),
}


def stroke(painter: QPainter, shape, to_px, scale: float) -> None:
    """Paint one shape at its true width."""
    p = shape.prim
    colour = QColor(COLOUR[shape.group])
    if shape.kind != "trace":
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(colour)
        r = p.width / 2 * scale
        painter.drawEllipse(to_px(p.x1, p.y1), r, r)
        return
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(QPen(colour, p.width * scale, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    path = QPainterPath()
    if isinstance(p, Arc):
        n = max(8, int(abs(p.sweep) * p.r * scale / 2))
        pts = [to_px(p.cx + p.r * math.cos(p.start + p.sweep * k / n), p.cy + p.r * math.sin(p.start + p.sweep * k / n))
               for k in range(n + 1)]  # fmt: skip
    else:
        pts = [to_px(p.x1, p.y1), to_px(p.x2, p.y2)]
    path.moveTo(pts[0])
    for q in pts[1:]:
        path.lineTo(q)
    painter.drawPath(path)


def render(shapes, layers: tuple[str, ...], region, scale: float, target: Path) -> None:
    """Paint the traces of ``layers`` (last first, so the first lies on top) and every land."""
    x0, x1, y0, y1 = region
    img = QImage(round((x1 - x0) * scale), round((y1 - y0) * scale), QImage.Format.Format_RGB32)
    img.fill(QColor(BACKGROUND))
    painter = QPainter(img)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    def to_px(x: float, y: float) -> QPointF:
        return QPointF((x - x0) * scale, (y1 - y) * scale)

    painter.setPen(QPen(QColor("#555555"), 1))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawEllipse(to_px(0, 0), 10 * scale, 10 * scale)
    for layer in reversed(layers):
        for s in shapes:
            if s.kind == "trace" and s.layer == layer:
                stroke(painter, s, to_px, scale)
    for s in shapes:
        if s.kind != "trace":
            stroke(painter, s, to_px, scale)
    painter.setPen(QColor("#ffffff"))
    painter.drawText(
        QRectF(8, 4, 900, 24), f"D08 from DXF export, layers {'+'.join(layers)}, true width, {scale} px/mm"
    )
    painter.end()
    img.save(str(target))


def main(argv: list[str]) -> int:
    """Write the PNG set into argv[0]."""
    out = Path(argv[0])
    out.mkdir(parents=True, exist_ok=True)
    _app = QGuiApplication.instance() or QGuiApplication([])
    shapes = check_example(EXAMPLES / "spiral_12c10p_d08.embodic.json", None)["_shapes"]
    for name, (region, scale) in REGIONS.items():
        render(shapes, ("L1",), region, scale, out / f"U-V16_D08_L1_{name}.png")
        render(shapes, ("L2",), region, scale, out / f"U-V16_D08_L2_{name}.png")
        render(shapes, ("L1", "L2"), region, scale, out / f"U-V16_D08_L1+L2_overlaid_{name}.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
