r"""U-M8x lever (DEF-UV16-02): wall time of the geometry view's redraw and open, for any tree of the repository.

Times, per example, median of ``--runs`` offscreen runs in one process, the examples alternating so that drift favours
none:

- open: a new ``GeometryView`` at 1280 x 800 shows D08, then its first paint is grabbed (fit zoom, labels placed).
- redraw: a view that already shows the serpentine example (6 copper layers, all visible) changes render mode, which
  rebuilds the scene, and the viewport is grabbed. ``rebuild`` is the ``show_geometry`` call alone, ``paint`` the grab.
- relayer: the same view hides L6 and shows it again, the grab included.
- zoom step, pan step: the serpentine view zooms by 1.25 and back, or pans by 100 px at 4x zoom, and the events the
  step posts run, its repaint and the label placement included. No view change, so a step rebuilds nothing.

Not a test. From the root of the tree under test, with the project's interpreter:

    PYTHONPATH=src QT_QPA_PLATFORM=offscreen python tests/ui/qt_shell/layer_cue_time.py [--runs 5]
"""

import argparse
import os
import statistics
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from embodic.api import compute_project
from embodic.ui.theme import load_theme
from embodic.ui.viewmodels.appearance import PhaseRenderMode
from embodic.ui.viewmodels.outcome import geometry_scene
from embodic.ui.views.geometry_view import GeometryView

EXAMPLES = Path("resources/examples")
SIZE = (1280, 800)


def _grab(view: GeometryView) -> None:
    QApplication.processEvents()
    view.viewport().grab()


def _median(values: list[float]) -> str:
    low, mid, high = (f * 1000 for f in (min(values), statistics.median(values), max(values)))
    return f"median {mid:.0f} ms, range {low:.0f} to {high:.0f} ms"


def main() -> None:
    """Time the open of D08 and the redraws of the serpentine example, and print the summary."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runs", type=int, default=5)
    runs = parser.parse_args().runs
    app = QApplication.instance() or QApplication([])
    tokens = load_theme("dark")
    d08 = geometry_scene(compute_project(EXAMPLES / "spiral_12c10p_d08.embodic.json"))
    serpentine = geometry_scene(compute_project(EXAMPLES / "serpentine_16p_example.embodic.json"))
    none = frozenset[str]()
    opens: list[float] = []
    for _ in range(runs):
        view = GeometryView()
        view.resize(*SIZE)
        view.show()
        started = time.perf_counter()
        view.show_geometry(d08, tokens, PhaseRenderMode.COLOUR, none)
        _grab(view)
        opens.append(time.perf_counter() - started)
        view.close()
        view.deleteLater()
        app.processEvents()
    view = GeometryView()
    view.resize(*SIZE)
    view.show()
    view.show_geometry(serpentine, tokens, PhaseRenderMode.COLOUR, none)
    _grab(view)
    modes = (PhaseRenderMode.GREYSCALE_HATCH, PhaseRenderMode.COLOUR)
    rebuilds, paints, relayers = [], [], []
    for k in range(runs):
        started = time.perf_counter()
        view.show_geometry(serpentine, tokens, modes[k % 2], none)
        middle = time.perf_counter()
        _grab(view)
        rebuilds.append(middle - started)
        paints.append(time.perf_counter() - middle)
        top = serpentine.layers[-1]
        started = time.perf_counter()
        view.show_geometry(serpentine, tokens, modes[k % 2], frozenset({top}))
        _grab(view)
        view.show_geometry(serpentine, tokens, modes[k % 2], none)
        _grab(view)
        relayers.append(time.perf_counter() - started)
    zooms, pans = [], []
    view.show_geometry(serpentine, tokens, PhaseRenderMode.COLOUR, none)
    _grab(view)
    for k in range(runs):
        started = time.perf_counter()
        view.zoom_by(1.25 if k % 2 == 0 else 0.8)
        app.processEvents()
        zooms.append(time.perf_counter() - started)
    view.zoom_by(4)
    app.processEvents()
    bar = view.horizontalScrollBar()
    for k in range(runs):
        started = time.perf_counter()
        bar.setValue(bar.value() + (100 if k % 2 == 0 else -100))
        app.processEvents()
        pans.append(time.perf_counter() - started)
    redraws = [a + b for a, b in zip(rebuilds, paints, strict=True)]
    print(f"== D08 open ({runs} runs): {_median(opens)}")
    print(f"== serpentine redraw ({runs} runs): {_median(redraws)}")
    print(f"   rebuild alone: {_median(rebuilds)}")
    print(f"   paint alone: {_median(paints)}")
    print(f"== serpentine hide L6 and show it again ({runs} runs, two redraws): {_median(relayers)}")
    print(f"== serpentine zoom step ({runs} runs): {_median(zooms)}")
    print(f"== serpentine pan step at 4x ({runs} runs): {_median(pans)}")


if __name__ == "__main__":
    main()
