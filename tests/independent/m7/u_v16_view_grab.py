"""U-V16: grab the product's geometry view of D08 offscreen and list what it draws.

usage: PYTHONPATH=src QT_QPA_PLATFORM=offscreen python tests/independent/m7/u_v16_view_grab.py OUT_DIR

Builds the shell as tests/ui/qt_shell/conftest.py does (create_shell, a throwaway settings file, dark theme, a
1280 x 800 window), opens the D08 example, waits for the result, then writes:

- ``U-V16_view_D08_fit.png``: the canvas at fit zoom, all layers;
- ``U-V16_view_D08_region_all.png``, ``..._region_L1.png``, ``..._region_L2.png``: the screenshot region
  (x -41.0..50.6 mm, y -1.2..56.1 mm) with all layers, L1 alone and L2 alone (the layer checkboxes' model);
- ``U-V16_view_items.json``: every scene item of the all-layer drawing grouped by kind, layer, phase, pen width in
  scene millimetres, pen cap, fill and z order.
"""

import json
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

from PySide6.QtCore import QRectF, QSettings, QStandardPaths, Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from embodic.ui.app import QSettingsStore, create_shell
from embodic.ui.viewmodels.outcome import OutcomeReady
from embodic.ui.views.geometry_view import DATA_KIND, DATA_LAYER, DATA_PHASE
from embodic.ui.views.main_window import ShellPaths

REGION = QRectF(-41.0, -56.1, 91.6, 57.3)  # scene y is -y
ARGB = QColor.NameFormat.HexArgb


def settle(app: QApplication, seconds: float) -> None:
    """Run the event loop for a while."""
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        app.processEvents()
        time.sleep(0.01)


def items_table(scene) -> list[dict]:
    """Scene items grouped by what the view tagged on them and how they are painted."""
    rows: Counter = Counter()
    for item in scene.items():
        kind, layer, phase = item.data(DATA_KIND), item.data(DATA_LAYER), item.data(DATA_PHASE)
        if not kind:
            continue
        pen = item.pen() if hasattr(item, "pen") else None
        brush = item.brush() if hasattr(item, "brush") else None
        width = round(pen.widthF(), 6) if pen is not None and pen.style() != Qt.PenStyle.NoPen else None
        rows[(
            kind, layer, phase,
            None if pen is None or pen.style() == Qt.PenStyle.NoPen else pen.color().name(ARGB),
            width,
            None if pen is None else pen.capStyle().name,
            None if pen is None else pen.isCosmetic(),
            None if brush is None or brush.style() == Qt.BrushStyle.NoBrush else brush.color().name(ARGB),
            item.zValue(),
            type(item).__name__,
        )] += 1  # fmt: skip
    keys = ["kind", "layer", "phase", "pen_colour", "pen_width_mm", "cap", "cosmetic", "fill", "z", "item_class"]
    return [dict(zip(keys, k, strict=True)) | {"count": n} for k, n in sorted(rows.items(), key=str)]


def main(argv: list[str]) -> int:
    """Write the grabs and the item table into argv[0]."""
    out = Path(argv[0])
    out.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    QStandardPaths.setTestModeEnabled(True)
    with tempfile.TemporaryDirectory() as tmp:
        store = QSettingsStore(QSettings(str(Path(tmp) / "settings.ini"), QSettings.Format.IniFormat))
        window, worker = create_shell(
            store, ShellPaths(recovery_dir=Path(tmp) / "recovery"), prefers_dark=lambda: True,
            prefers_high_contrast=lambda: False, system_palette=QPalette,
        )  # fmt: skip
        window.resize(1280, 800)
        window.show()
        settle(app, 1.0)
        window.outcome.open_example("spiral_12c10p_d08")
        deadline = time.monotonic() + 120
        while not isinstance(window.outcome.state.value, OutcomeReady):
            if time.monotonic() > deadline:
                raise TimeoutError("D08 result did not arrive")
            settle(app, 0.05)
        settle(app, 1.0)
        canvas = window.canvas
        canvas.grab().save(str(out / "U-V16_view_D08_fit.png"))
        table = items_table(canvas.scene())
        layers = tuple(window.outcome.state.value.scene.layers)
        for name, hidden in (("all", frozenset()), *((layer, frozenset(layers) - {layer}) for layer in layers)):
            window.outcome.hidden_layers.set(hidden)
            settle(app, 0.5)
            canvas.fitInView(REGION, Qt.AspectRatioMode.KeepAspectRatio)
            settle(app, 0.5)
            canvas.grab().save(str(out / f"U-V16_view_D08_region_{name}.png"))
        summary = {
            "layers": list(layers),
            "theme_dark": True,
            "canvas_px": [canvas.viewport().width(), canvas.viewport().height()],
            "region_scale_px_per_mm": canvas.transform().m11(),
            "items": table,
        }
        (out / "U-V16_view_items.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
        print(json.dumps(summary)[:3000])
        worker.shutdown()
        window.close()
        settle(app, 0.5)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
