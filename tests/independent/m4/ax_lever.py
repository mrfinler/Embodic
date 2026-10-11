"""AX-05 and AX-06 lever (Agent 4). Not a test: it writes the images and tables the manual records cite.

    python tests/independent/m4/ax_lever.py render OUT    # contact sheets of label crops, greyscale and deutan colour
    python tests/independent/m4/ax_lever.py truth         # phase and polarity of the copper under each crop centre
    python tests/independent/m4/ax_lever.py names OUT.md  # accessibleName / accessibleDescription of inputs and results

The deuteranopia simulation is a proxy for a human reviewer (status `inferred`). It applies the Machado, Oliveira and
Fernandes (2009) matrix for deuteranomaly at severity 1.0 (IEEE TVCG 15(6), pp. 1291-1298; Table 1 on
https://www.inf.ufrgs.br/~oliveira/pubs_files/CVD_Simulation/CVD_Simulation.html) to linear sRGB. The page does not
say linear or encoded RGB; linear is an `assumption`.
"""

import math
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from conftest import outcome_of

DEUTAN_MACHADO_2009_S10 = np.array(
    [
        [0.367322, 0.860646, -0.227968],
        [0.280085, 0.672501, 0.047413],
        [-0.011820, 0.042940, 0.968881],
    ]
)
PX_PER_MM = 12.0
CROP_MM = 14.0
SHEET_COLUMNS = 4
STEMS = {"d08": "spiral_12c10p_d08", "wave": "wave_16p_example"}
SVG = "{http://www.w3.org/2000/svg}"


def write_svgs(folder: Path) -> dict[tuple[str, str], Path]:
    """Write the greyscale and colour SVG of D08 and wave."""
    from embodic.io.exporters import PhaseRenderMode
    from embodic.io.svg_writer import write_svg

    out = {}
    for key, stem in STEMS.items():
        for mode in PhaseRenderMode:
            path = folder / f"{key}_{mode.value}.svg"
            write_svg(outcome_of(stem), path, mode=mode, allow_drc_errors=True)
            out[(key, mode.value)] = path
    return out


def label_centres(svg: Path, count: int) -> list[tuple[float, float]]:
    """Return board-mm centres of the first ``count`` coil labels (the drawing flips y)."""
    root = ET.parse(svg).getroot()
    labels = [e for e in root.iter() if e.get("class") == "coil-label"][:count]
    return [(float(e.get("x")), float(e.get("y"))) for e in labels]


def rasterise(svg: Path):
    """Render an SVG with QSvgRenderer to a QImage at PX_PER_MM, on white."""
    from PySide6.QtCore import QRectF
    from PySide6.QtGui import QColor, QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer

    renderer = QSvgRenderer(str(svg))
    box = renderer.viewBoxF()
    image = QImage(int(box.width() * PX_PER_MM), int(box.height() * PX_PER_MM), QImage.Format.Format_RGB32)
    image.fill(QColor("white"))
    painter = QPainter(image)
    renderer.render(painter, QRectF(0, 0, image.width(), image.height()))
    painter.end()
    return image, box


def deutan(image):
    """Return a copy of a QImage with the Machado 2009 deuteranopia matrix applied in linear sRGB."""
    from PySide6.QtGui import QImage

    rgb = image.convertToFormat(QImage.Format.Format_RGB888)
    width, height, stride = rgb.width(), rgb.height(), rgb.bytesPerLine()
    raw = np.frombuffer(rgb.constBits(), dtype=np.uint8).reshape(height, stride)[:, : width * 3]
    srgb = raw.reshape(height, width, 3) / 255.0
    linear = np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)
    sim = np.clip(linear @ DEUTAN_MACHADO_2009_S10.T, 0, 1)
    encoded = np.where(sim <= 0.0031308, sim * 12.92, 1.055 * sim ** (1 / 2.4) - 0.055)
    data = np.ascontiguousarray((encoded * 255).round().astype(np.uint8))
    return QImage(data.data, width, height, width * 3, QImage.Format.Format_RGB888).copy()


def contact_sheet(image, box, centres, out: Path) -> None:
    """Cut a square crop around each label centre and lay them out with an index above each."""
    from PySide6.QtCore import QRect
    from PySide6.QtGui import QColor, QFont, QImage, QPainter

    side = int(CROP_MM * PX_PER_MM)
    rows = math.ceil(len(centres) / SHEET_COLUMNS)
    sheet = QImage(SHEET_COLUMNS * (side + 10), rows * (side + 40), QImage.Format.Format_RGB32)
    sheet.fill(QColor("white"))
    painter = QPainter(sheet)
    painter.setFont(QFont("DejaVu Sans", 18))
    for i, (x, y) in enumerate(centres):
        px = (x - box.x()) * PX_PER_MM
        py = (y - box.y()) * PX_PER_MM
        crop = image.copy(QRect(int(px - side / 2), int(py - side / 2), side, side))
        col, row = i % SHEET_COLUMNS, i // SHEET_COLUMNS
        left, top = col * (side + 10), row * (side + 40)
        painter.setPen(QColor("black"))
        painter.drawText(left + 4, top + 26, f"#{i + 1}")
        painter.drawImage(left, top + 34, crop)
    painter.end()
    sheet.save(str(out))


def render(out: Path) -> None:
    """Write the full drawings and the contact sheets the AX-05 record cites."""
    from embodic.ui.app import qt_application

    qt_application()
    out.mkdir(parents=True, exist_ok=True)
    svgs = write_svgs(out)
    for key, count in (("d08", 12), ("wave", 12)):
        centres = label_centres(svgs[(key, "greyscale_hatch")], count)
        grey, box = rasterise(svgs[(key, "greyscale_hatch")])
        grey.save(str(out / f"{key}_greyscale_full.png"))
        contact_sheet(grey, box, centres, out / f"{key}_greyscale_sheet.png")
        colour, box = rasterise(svgs[(key, "colour")])
        simulated = deutan(colour)
        simulated.save(str(out / f"{key}_colour_deutan_full.png"))
        contact_sheet(simulated, box, centres, out / f"{key}_colour_deutan_sheet.png")
        print(key, "crop centres (svg x, y):", [(round(x, 2), round(y, 2)) for x, y in centres])


def nearest_copper(layout, x_mm: float, y_mm: float) -> list[tuple[float, str, int]]:
    """Return (distance, phase, polarity) per phase and polarity of top-layer copper, nearest first."""
    top = layout.copper_layers[0]
    best: dict[tuple[str, int], float] = {}
    for path in layout.paths:
        if path.layer != top or path.phase is None:
            continue
        for prim in path.primitives:
            for t in np.linspace(0.0, 1.0, 33):
                if hasattr(prim, "r_mm"):
                    a = prim.start_rad + t * prim.sweep_rad
                    px, py = prim.cx_mm + prim.r_mm * math.cos(a), prim.cy_mm + prim.r_mm * math.sin(a)
                else:
                    px, py = prim.x1_mm + t * (prim.x2_mm - prim.x1_mm), prim.y1_mm + t * (prim.y2_mm - prim.y1_mm)
                key = (path.phase.value, path.polarity)
                best[key] = min(best.get(key, math.inf), math.hypot(px - x_mm, py - y_mm))
    return sorted((d, phase, polarity) for (phase, polarity), d in best.items())


def truth() -> None:
    """Print the phase and polarity of the copper nearest each crop centre, from the Layout."""
    with tempfile.TemporaryDirectory() as folder:
        svgs = write_svgs(Path(folder))
        for key, count in (("d08", 12), ("wave", 12)):
            layout = outcome_of(STEMS[key]).boards.boards[0]
            for i, (x, y) in enumerate(label_centres(svgs[(key, "greyscale_hatch")], count), start=1):
                (d, phase, polarity), (d2, phase2, polarity2) = nearest_copper(layout, x, -y)[:2]
                sign = {1: "+", -1: "\u2212", 0: "0"}
                print(
                    f"{key} #{i}: phase {phase} polarity {sign[polarity]} at {d:.2f} mm;"
                    f" next {phase2}{sign[polarity2]} at {d2:.2f} mm"
                )


def accessible_rows(window) -> list[tuple[str, str, str, str, str]]:
    """Return (objectName, kind, shown text, accessible name, accessible description) for inputs and results."""
    from PySide6.QtGui import QAccessible
    from PySide6.QtWidgets import QAbstractButton, QComboBox, QLabel, QLineEdit, QWidget

    rows = []
    for w in window.findChildren(QWidget):
        name = w.objectName()
        is_input = name.startswith("param-") and isinstance(w, (QLineEdit, QComboBox, QAbstractButton))
        is_result = name.startswith("res-card-") or (name.startswith("res-") and name.endswith("-value"))
        if not (is_input or is_result):
            continue
        iface = QAccessible.queryAccessibleInterface(w)
        acc_name = iface.text(QAccessible.Text.Name) if iface else ""
        acc_desc = iface.text(QAccessible.Text.Description) if iface else ""
        if isinstance(w, QLineEdit):
            shown = w.text()
        elif isinstance(w, QComboBox):
            shown = w.currentText()
        elif isinstance(w, (QLabel, QAbstractButton)):
            shown = w.text()
        else:
            shown = ""
        rows.append((name, type(w).__name__, shown, acc_name, acc_desc))
    return rows


def names(out: Path) -> None:
    """Write the AX-06 proxy table for the D08 example at 1280 x 800."""
    from ui_driver import close, load_example, open_window

    with tempfile.TemporaryDirectory() as folder:
        window = open_window(Path(folder))
        load_example(window, "spiral_12c10p_d08")
        rows = accessible_rows(window)
        close(window)

    def cell(text: str) -> str:
        return text.replace("|", "\\|").replace("\n", " / ").replace("\u00a0", "&#160;")[:120]

    lines = ["| objectName | class | shown | accessibleName | accessibleDescription |", "|---|---|---|---|---|"]
    lines += [f"| {' | '.join(cell(c) for c in row)} |" for row in sorted(rows)]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(rows)} rows -> {out}")


if __name__ == "__main__":
    command = sys.argv[1]
    if command == "render":
        render(Path(sys.argv[2]))
    elif command == "truth":
        truth()
    elif command == "names":
        names(Path(sys.argv[2]))
    else:
        raise SystemExit(f"unknown command {command}")
