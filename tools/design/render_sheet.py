"""Render the icon contact sheet ``resources/icons/_contact_sheet.png`` with Qt's QSvgRenderer, as the app does.

Usage, from the repository root::

    QT_QPA_PLATFORM=offscreen python tools/design/render_sheet.py

Each icon appears at 48 px, 24 px, 16 px (stroke-width 2, the loader rule) and 24 px disabled, in the light theme
(top) and the dark theme (bottom). Exit code 1 when QSvgRenderer rejects an icon.
"""

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QByteArray, QRectF, Qt, qInstallMessageHandler
from PySide6.QtGui import QColor, QFont, QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

REPO = Path(__file__).resolve().parents[2]
ICONS = REPO / "resources" / "icons"
TOKENS = REPO / "resources" / "themes" / "tokens.json"
COLS, CELL_W, CELL_H = 6, 220, 70


def svg_bytes(path: Path, colour: str, size: int) -> QByteArray:
    """Return the icon recoloured and, at 16 px or less, with the thicker stroke, as the loader prepares it."""
    text = path.read_text(encoding="utf-8").replace("currentColor", colour)
    if size <= 16:
        text = text.replace('stroke-width="1.5"', 'stroke-width="2"')
    return QByteArray(text.encode())


def main() -> int:
    """Render the sheet; return 1 when an icon does not parse."""
    messages: list[str] = []
    qInstallMessageHandler(lambda _mode, _ctx, msg: messages.append(msg))
    app = QGuiApplication(sys.argv)
    themes = json.loads(TOKENS.read_text(encoding="utf-8"))["themes"]
    files = sorted(ICONS.glob("*.svg"))
    rows = (len(files) + COLS - 1) // COLS
    img = QImage(COLS * CELL_W, rows * CELL_H * 2 + 40, QImage.Format.Format_ARGB32)
    img.fill(QColor("#ffffff"))
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setFont(QFont("DejaVu Sans", 8))
    bad = []
    for band, theme in enumerate(("light", "dark")):
        c = themes[theme]["color"]
        y0 = 40 + band * rows * CELL_H
        p.fillRect(0, y0, img.width(), rows * CELL_H, QColor(c["surface"]))
        for i, f in enumerate(files):
            x, y = (i % COLS) * CELL_W + 8, y0 + (i // COLS) * CELL_H + 8
            cells = ((48, 0, c["text-1"]), (24, 56, c["text-1"]), (16, 88, c["text-1"]), (24, 112, c["text-disabled"]))
            for size, dx, colour in cells:
                r = QSvgRenderer(svg_bytes(f, colour, size))
                if not r.isValid():
                    bad.append(f.name)
                r.render(p, QRectF(x + dx, y + (48 - size) / 2, size, size))
            p.setPen(QColor(c["text-2"]))
            align = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextWordWrap
            p.drawText(x + 140, y + 4, 76, 44, align, f.stem)
    p.setPen(QColor("#141414"))
    p.setFont(QFont("DejaVu Sans", 10))
    p.drawText(
        8,
        26,
        f"embodic icons ({len(files)}): 48 px preview, 24 px, 16 px (stroke-width 2), 24 px disabled. "
        "Top light theme, bottom dark theme. Rendered by QSvgRenderer.",
    )
    p.end()
    img.save(str(ICONS / "_contact_sheet.png"))
    del app
    print("icons", len(files), "invalid", sorted(set(bad)), "qt messages", messages[:5])
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
