# Prepared by: Agent 1 (UX/UI Expert Designer) - model: claude-sonnet-5-5; acceptance-set names: claude-opus-5-5 (U-S4g)
"""Read pane geometry and text contrast from the U-M4e-1 or U-M4e-2 screenshots; every number comes from pixels.

    QT_QPA_PLATFORM=offscreen .venv/bin/python docs/phase2/design/checks/shot_measure.py /mnt/user-data/outputs/m4e1
    QT_QPA_PLATFORM=offscreen .venv/bin/python docs/phase2/design/checks/shot_measure.py /mnt/user-data/outputs/m4accept

The 1280 x 800 canvas shot gives the inspector and rail widths and the canvas share of the centre pane. The gallery shot
gives the contrast of the selected item's title and note, and of an unselected note. A text colour is the pixel that
differs most from the background of its band, so anti-aliased glyphs read slightly lighter than the true colour.
Exit code 1 when a measured value misses its criterion (UX-AC-08, UX-AC-21, design_spec 5).
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

from PySide6.QtGui import QImage

Rgb = tuple[int, int, int]
# U-M4e-1 names first, then the acceptance-set rows (S22: canvas frame without a focus ring; S39: gallery).
CANVAS = ("u-m4e_canvas-60-40_spiral_12c10p_d08_1280x800.png", "S22_light_1280x800.png")
GALLERY = ("u-m4e_gallery-selected_light.png", "S39_light_dialog.png")
TEXT_MIN = 4.5
SHARE = (0.59, 0.61)
WIDTHS = {"inspector": 340, "rail": 360}
WIDTH_TOLERANCE_PX = 2
PANE_LINE_Y = 300
HANDLE_PX = 4
FRAME_BORDER = (197, 197, 197)


def pixel(image: QImage, x: int, y: int) -> Rgb:
    """Return the RGB of one pixel."""
    colour = image.pixelColor(x, y)
    return colour.red(), colour.green(), colour.blue()


def luminance(rgb: Rgb) -> float:
    """Return the WCAG relative luminance."""

    def linear(channel: int) -> float:
        value = channel / 255
        return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4

    r, g, b = (linear(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: Rgb, b: Rgb) -> float:
    """Return the WCAG contrast ratio of two colours."""
    high, low = sorted((luminance(a), luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def band_contrast(image: QImage, x0: int, x1: int, y0: int, y1: int) -> tuple[Rgb, Rgb, float]:
    """Return the background, the pixel farthest from it, and their contrast, for one rectangle of text."""
    pixels = [pixel(image, x, y) for y in range(y0, y1) for x in range(x0, x1)]
    background = Counter(pixels).most_common(1)[0][0]
    ink = max(pixels, key=lambda p: abs(luminance(p) - luminance(background)))
    return background, ink, contrast(background, ink)


def transitions(image: QImage, y: int) -> list[tuple[int, Rgb]]:
    """Return each x of one row where the colour changes, with the new colour."""
    found, previous = [], None
    for x in range(image.width()):
        current = pixel(image, x, y)
        if current != previous:
            found.append((x, current))
            previous = current
    return found


def pane_widths(image: QImage) -> dict[str, int]:
    """Return the pane widths from the canvas frame borders, which sit one splitter handle inside each neighbour."""
    borders = [x for x, p in transitions(image, PANE_LINE_Y) if p == FRAME_BORDER]
    return {"inspector": borders[0] - HANDLE_PX, "rail": image.width() - (borders[-1] + 1 + HANDLE_PX)}


def canvas_share(image: QImage) -> float:
    """Canvas page height over centre height: from the toolstrip divider to the splitter, and to the status bar."""
    column = [pixel(image, 630, y) for y in range(image.height())]
    top = next(y for y in range(100, 160) if column[y] == (220, 220, 220)) + 1
    bottom = max(y for y in range(700, image.height()) if column[y] == (220, 220, 220))
    frame_bottom = max(y for y in range(500, 525) if column[y] == FRAME_BORDER)
    split = frame_bottom + 4
    return (split - top) / (bottom - top)


def shot(folder: Path, names: tuple[str, ...]) -> QImage:
    """Return the first of ``names`` present in ``folder``."""
    path = next((folder / n for n in names if (folder / n).is_file()), None)
    if path is None:
        sys.exit(f"none of {names} in {folder}")
    print(f"reading {path.name}")
    return QImage(str(path))


def main(folder: Path) -> int:
    """Print the measurements and return 1 when one misses its criterion."""
    findings: list[str] = []
    canvas = shot(folder, CANVAS)
    widths = pane_widths(canvas)
    share = canvas_share(canvas)
    print(f"1280 x 800 panes: {widths}, canvas share {share:.3f} (target {SHARE[0]} to {SHARE[1]})")
    findings += [
        f"{name} width {widths[name]} px, want {want}"
        for name, want in WIDTHS.items()
        if abs(widths[name] - want) > WIDTH_TOLERANCE_PX
    ]
    if not SHARE[0] <= share <= SHARE[1]:
        findings.append(f"canvas share {share:.3f} outside {SHARE}")
    gallery = shot(folder, GALLERY)
    bands = {
        "selected title": (28, 285, 98, 116),
        "selected note": (28, 520, 118, 150),
        "unselected note": (28, 520, 192, 204),
    }
    for name, (x0, x1, y0, y1) in bands.items():
        background, ink, ratio = band_contrast(gallery, x0, x1, y0, y1)
        print(f"gallery {name}: background {background}, text {ink}, contrast {ratio:.2f}:1 (needs {TEXT_MIN}:1)")
        if ratio < TEXT_MIN:
            findings.append(f"gallery {name} contrast {ratio:.2f}:1")
    print("\n".join(findings) if findings else "no findings")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1] if len(sys.argv) > 1 else "/mnt/user-data/outputs/m4e1")))
