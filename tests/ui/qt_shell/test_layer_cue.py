"""Layer cue and land shapes of the geometry view (design_spec.md 3.3.1, DEF-UV16-02, DEF-UV16-03; UI-58 to UI-61).

The pixel rows render the view offscreen at a fixed scale, as the U-S16 lever in `docs/phase3/design/checks/u_s16/`
does, and read the pixels it draws. Windows high contrast draws the greyscale ladder, so the greyscale runs stand for it
(REQ-N-23).
"""

import dataclasses
import math
from pathlib import Path

import numpy as np
import pytest
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPainterPathStroker, QTransform
from PySide6.QtWidgets import QApplication, QGraphicsEllipseItem, QGraphicsPathItem, QGraphicsView

from embodic.api import compute_project
from embodic.geometry.layout import Pad
from embodic.geometry.primitives import Line
from embodic.io.exporters import pad_outline
from embodic.ui.theme import load_theme
from embodic.ui.viewmodels.appearance import PhaseRenderMode
from embodic.ui.viewmodels.outcome import eyes_shown, geometry_scene
from embodic.ui.viewmodels.results import DrcRow
from embodic.ui.views import layer_cue
from embodic.ui.views.checks_view import locate_on_canvas
from embodic.ui.views.geometry_view import DATA_KIND, GeometryView, primitive_path

EXAMPLES = Path(__file__).resolve().parents[3] / "resources" / "examples"
RUNS = {
    "dark colour": ("dark", PhaseRenderMode.COLOUR, "#c43b10"),
    "dark greyscale": ("dark", PhaseRenderMode.GREYSCALE_HATCH, "#e0e0e0"),
    "light greyscale": ("light", PhaseRenderMode.GREYSCALE_HATCH, "#262626"),
}
COPPER_KINDS = ("copper", "copper-cue")
LAND_KINDS = ("via", "pad", "drill")
CROSSING_MM, CROSSING_CLEAR_R_MM = (-11.01, 47.19), 49.36


def _scene(example: str):
    scene = geometry_scene(compute_project(EXAMPLES / f"{example}.embodic.json"))
    assert scene is not None
    return scene


@pytest.fixture(scope="module")
def d08():
    """Return the D08 geometry scene."""
    return _scene("spiral_12c10p_d08")


@pytest.fixture(scope="module")
def serpentine():
    """Return the serpentine example's geometry scene (6 copper layers)."""
    return _scene("serpentine_16p_example")


def _draw(view, scene, run, hidden=frozenset()):
    theme, mode, _ = RUNS[run]
    view.show_geometry(scene, load_theme(theme), mode, hidden)


def _show(scene, run, size_px, hidden=frozenset()):
    """Return a shown, unfocused view of ``scene`` in one run of RUNS."""
    view = GeometryView()
    view.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    view.resize(*size_px)
    view.show()
    _draw(view, scene, run, hidden)
    return view


def _render(scene, run, centre_mm, px_per_mm, size_px, hidden=frozenset()):
    """Return (view, image) at a fixed scale around ``centre_mm``, labels placed. The caller closes the view."""
    view = _show(scene, run, size_px, hidden)
    return view, _place(view, centre_mm, px_per_mm)


def _place(view, centre_mm, px_per_mm) -> QImage:
    """Set the view to a fixed scale around ``centre_mm``, place the labels and return what it draws."""
    view.setTransform(QTransform.fromScale(px_per_mm, px_per_mm))
    view.centerOn(QPointF(centre_mm[0], -centre_mm[1]))
    view.place_labels()
    QApplication.processEvents()
    return view.viewport().grab().toImage().convertToFormat(QImage.Format.Format_RGB32)


def _board_fill(run) -> str:
    return load_theme(RUNS[run][0]).colours["board-fill"]


def _luminance(image: QImage) -> np.ndarray:
    raw = np.frombuffer(image.constBits(), dtype=np.uint8).reshape(image.height(), image.bytesPerLine() // 4, 4)
    rgb = raw[:, : image.width(), 2::-1].astype(float) / 255.0
    lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    return lin @ np.array([0.2126, 0.7152, 0.0722])


def _contrast_to(image: QImage, colour: QColor) -> np.ndarray:
    one = QImage(1, 1, QImage.Format.Format_RGB32)
    one.fill(colour)
    lum, ref = _luminance(image), _luminance(one)[0, 0]
    return (np.maximum(lum, ref) + 0.05) / (np.minimum(lum, ref) + 0.05)


def _contrast(a: QColor, b: QColor) -> float:
    def lum(c: QColor) -> float:
        def ch(v: float) -> float:
            return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

        return 0.2126 * ch(c.redF()) + 0.7152 * ch(c.greenF()) + 0.0722 * ch(c.blueF())

    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def _stroked(prims, extra_mm: float = 0.0) -> QPainterPath:
    """Return the true-width shapes of ``prims``, each grown by ``extra_mm``, as one WindingFill path."""
    out = QPainterPath()
    for p in prims:
        stroker = QPainterPathStroker()
        stroker.setWidth(p.width_mm + extra_mm)
        stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
        stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        out.addPath(stroker.createStroke(primitive_path(p)))
    out.setFillRule(Qt.FillRule.WindingFill)
    return out


def _tangent(p, x: float, y: float) -> tuple[float, float]:
    if isinstance(p, Line):
        d = (p.x2_mm - p.x1_mm, p.y2_mm - p.y1_mm)
    else:
        a = math.atan2(y - p.cy_mm, x - p.cx_mm)
        d = (-math.sin(a), math.cos(a))
    n = math.hypot(*d)
    return d[0] / n, d[1] / n


def _distance(q, at) -> float:
    x, y = at
    if isinstance(q, Line):
        ax, ay, bx, by = q.x1_mm, q.y1_mm, q.x2_mm, q.y2_mm
        t = max(0.0, min(1.0, ((x - ax) * (bx - ax) + (y - ay) * (by - ay)) / ((bx - ax) ** 2 + (by - ay) ** 2)))
        return math.hypot(x - ax - t * (bx - ax), y - ay - t * (by - ay))
    return abs(math.hypot(x - q.cx_mm, y - q.cy_mm) - q.r_mm)


def _crossing_measures(view, image, scene, run) -> dict:
    """Follow leg 24 outward from its crossing under ring 32 and read the pixels UI-58 names."""
    board = scene.boards[0]
    ring = next(p for p in board.paths if p.id == 32)
    leg = next(p for p in board.paths if p.id == 24)
    x0, y0 = CROSSING_MM
    upper = min(ring.primitives, key=lambda q: _distance(q, CROSSING_MM))
    lower = min(leg.primitives, key=lambda q: _distance(q, CROSSING_MM))
    scale, origin = view.transform().m11(), view.mapFromScene(QPointF(0, 0))

    def px(x: float, y: float) -> QColor:
        return image.pixelColor(math.floor(origin.x() + scale * x), math.floor(origin.y() + scale * -y))

    tu, tl = _tangent(upper, x0, y0), _tangent(lower, x0, y0)
    if x0 * tl[0] + y0 * tl[1] < 0:
        tl = (-tl[0], -tl[1])
    sin_t = abs(tu[0] * tl[1] - tu[1] * tl[0])
    edge_mm = upper.width_mm / 2 / max(sin_t, 1e-6)
    board_fill = QColor(_board_fill(run))
    beyond = [px(x0 + (edge_mm + k / scale) * tl[0], y0 + (edge_mm + k / scale) * tl[1]) for k in (1, 2)]
    proj = x0 * tl[0] + y0 * tl[1]
    s_clear = -proj + math.sqrt(proj**2 - (x0**2 + y0**2 - CROSSING_CLEAR_R_MM**2))
    cx, cy = x0 + s_clear * tl[0], y0 + s_clear * tl[1]
    nx, ny = -tl[1], tl[0]
    across = {
        k: _contrast(px(cx + nx * k / (4 * scale), cy + ny * k / (4 * scale)), board_fill) for k in range(-60, 61)
    }
    hits = [k for k, c in across.items() if c > 1.3]
    return {
        "crossing": px(x0, y0).name(),
        "beyond": [c.name() for c in beyond],
        "beyond_contrast": [_contrast(px(x0, y0), c) for c in beyond],
        "centre": px(cx, cy).name(),
        "side_contrast": (max(c for k, c in across.items() if k < 0), max(c for k, c in across.items() if k > 0)),
        "span_px": (hits[-1] - hits[0] + 1) / 4 if hits else 0.0,
        "true_width_px": lower.width_mm * scale,
    }


@pytest.mark.req("REQ-F-13", "REQ-N-23")
@pytest.mark.parametrize("run", RUNS)
def test_ui58_ring_over_leg_shows_the_ring_solid_a_board_gap_and_the_leg_as_an_outline(d08, run):
    """Catches 0.0.3, where ring A and leg 24 are one ink at the crossing (1.0:1), and an outline in the wrong ink."""
    ink, board_fill = RUNS[run][2], _board_fill(run)
    view, image = _render(d08, run, CROSSING_MM, 24.0, (420, 300))
    try:
        m = _crossing_measures(view, image, d08, run)
    finally:
        view.close()
    assert m["crossing"] == ink
    assert m["beyond"] == [board_fill, board_fill], m
    assert min(m["beyond_contrast"]) >= 3.0, m
    assert m["centre"] == board_fill, m
    assert min(m["side_contrast"]) >= 2.0, m
    assert m["span_px"] <= m["true_width_px"] + 1.5, m
    solo, image = _render(d08, run, CROSSING_MM, 24.0, (420, 300), hidden=frozenset({"L1"}))
    try:
        assert _crossing_measures(solo, image, d08, run)["centre"] == ink
    finally:
        solo.close()


def _screen_boxes(view) -> list[QRectF]:
    """Return the legend, the stamp and every label, leader and halo box in viewport pixels."""
    boxes = [view.legend_rect(), view.stamp_rect()]
    for item in view.scene().items():
        if item.data(DATA_KIND) in ("label", "label-halo", "leader"):
            boxes.append(item.deviceTransform(view.viewportTransform()).mapRect(item.boundingRect()))
    return boxes


def _band_mask(view, size, scene, visible, k, hidden) -> np.ndarray:
    """Return the pixels 0.75 to 1.5 px outside the copper of ``visible[k]``, less what UI-59 leaves out."""
    scale, origin = view.transform().m11(), view.mapFromScene(QPointF(0, 0))
    layer = visible[k]
    mask = QImage(size, QImage.Format.Format_RGB32)
    mask.fill(QColor("#000000"))
    p = QPainter(mask)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
    p.setTransform(QTransform(scale, 0, 0, scale, origin.x(), origin.y()))
    p.setPen(Qt.PenStyle.NoPen)
    for board in scene.boards:
        mine = [q for path in board.paths if path.layer == layer for q in path.primitives]
        p.setBrush(QColor("#ffffff"))
        p.drawPath(_stroked(mine, 2 * 1.5 / scale))
        p.setBrush(QColor("#000000"))
        p.drawPath(_stroked(mine, 2 * 0.75 / scale))
        above = [q for path in board.paths if path.layer in visible[:k] for q in path.primitives]
        p.drawPath(_stroked(above, 2 * 1.0 / scale))
        for x, y, reach in [(v.x_mm, v.y_mm, v.pad_mm / 2) for v in board.vias] + [
            (d.x_mm, d.y_mm, max(d.width_mm, d.height_mm) / 2) for d in board.pads
        ]:
            r = reach + 2.0 / scale
            p.drawEllipse(QRectF(x - r, -y - r, 2 * r, 2 * r))
    for board, marks in zip(scene.boards, scene.marks, strict=True):
        for mark in eyes_shown(board, marks, hidden):
            r = mark.eye_radius_mm + 1.0 / scale
            p.drawEllipse(QRectF(mark.cx_mm - r, -mark.cy_mm - r, 2 * r, 2 * r))
    p.resetTransform()
    for box in _screen_boxes(view):
        p.drawRect(box.adjusted(-3, -3, 3, 3))
    p.end()
    return _luminance(mask) > 0.5


def _band_violations(view, image, scene, board_hex, hidden=frozenset()):
    """Return (pixels of ink in the band outside each lower layer's copper, band pixels), as UI-59 words them."""
    board_fill = QColor(board_hex)
    visible = [layer for layer in scene.layers if layer not in hidden]
    violations = band_px = 0
    for k in range(len(visible) - 1):
        inside = _band_mask(view, image.size(), scene, visible, k, hidden)
        band_px += int(np.count_nonzero(inside))
        violations += int(np.count_nonzero(inside & (_contrast_to(image, board_fill) > 1.1)))
    return violations, band_px


BAND_SCENES = (
    ("d08", (4.8, 27.45), 6.0, (560, 352)),
    ("serpentine", (0.0, 0.0), 5.0, (480, 480)),
    ("serpentine", (0.0, 33.0), 20.0, (480, 320)),
)


@pytest.mark.req("REQ-F-13", "REQ-N-23")
@pytest.mark.parametrize("run", RUNS)
@pytest.mark.parametrize(("which", "centre", "px_per_mm", "size"), BAND_SCENES)
def test_ui59_no_lower_copper_touches_upper_copper_on_screen(d08, serpentine, run, which, centre, px_per_mm, size):
    """Catches 0.0.3, where 5 to 13 % of the band beside a lower layer's copper is ink, and a casing too thin."""
    scene = d08 if which == "d08" else serpentine
    view, image = _render(scene, run, centre, px_per_mm, size)
    try:
        violations, band_px = _band_violations(view, image, scene, _board_fill(run))
    finally:
        view.close()
    assert band_px > 5_000
    assert violations / band_px <= 0.01, (violations, band_px)


def _legend_row_pixels(view, image, row):
    bar, _, _ = view.legend_row_geometry(row)
    y = round(bar.center().y() - 0.5)
    return bar, y, [image.pixelColor(x, y).name() for x in range(round(bar.left()), round(bar.right()))]


@pytest.mark.req("REQ-F-13", "REQ-N-23")
@pytest.mark.parametrize("run", RUNS)
def test_ui60_legend_adds_a_solid_row_and_an_outlined_row_while_two_layers_show(d08, run):
    """Catches a cue the legend does not explain, and an outlined bar that is filled."""
    colours = load_theme(RUNS[run][0]).colours
    view = _show(d08, run, (1280, 800))
    try:
        phases = len(view.legend_phases())
        assert view.legend_layer_rows() == ("L1 on top", "Layers below")
        assert QRectF(view.viewport().rect()).contains(view.legend_rect())
        image = view.viewport().grab().toImage().convertToFormat(QImage.Format.Format_RGB32)
        solid, _, along = _legend_row_pixels(view, image, phases)
        assert (solid.width(), solid.height()) == (20, 6)
        assert set(along) == {colours["text-1"]}
        outlined, _, along = _legend_row_pixels(view, image, phases + 1)
        assert (outlined.width(), outlined.height()) == (20, 6)
        assert along[0] == colours["text-1"] and along[-1] == colours["text-1"]
        centre = outlined.center()
        assert image.pixelColor(int(centre.x()), int(centre.y())).name() == colours["surface"]
        with_rows = view.legend_rect()
        _draw(view, d08, run, frozenset({"L1"}))
        assert view.legend_layer_rows() == () and len(view.legend_phases()) == phases
        assert with_rows.height() - view.legend_rect().height() == 2 * 20
    finally:
        view.close()


@pytest.mark.req("REQ-F-13", "REQ-N-23")
def test_ui60_legend_names_the_top_visible_layer_and_stays_in_the_viewport(serpentine):
    """Catches a legend that says L1 when L1 is hidden, or one that grows past the viewport."""
    view = _show(serpentine, "dark colour", (1280, 800), frozenset({"L1"}))
    try:
        assert view.legend_layer_rows() == ("L2 on top", "Layers below")
        assert QRectF(view.viewport().rect()).contains(view.legend_rect())
        _draw(view, serpentine, "dark colour", frozenset(serpentine.layers[1:]))
        assert view.legend_layer_rows() == ()
    finally:
        view.close()


def _items(view, *kinds):
    return [item for item in view.scene().items() if item.data(DATA_KIND) in kinds]


def _extent(prims) -> tuple[float, float, float, float]:
    """Return x_min, y_min, x_max, y_max of closed-edge primitives, arcs included, from the analytic extremes."""
    xs, ys = [], []
    for q in prims:
        if isinstance(q, Line):
            xs += [q.x1_mm, q.x2_mm]
            ys += [q.y1_mm, q.y2_mm]
            continue
        angles = [q.start_rad, q.start_rad + q.sweep_rad]
        lo, hi = sorted(angles)
        angles += [k * math.pi / 2 for k in range(-8, 9) if lo < k * math.pi / 2 < hi]
        xs += [q.cx_mm + q.r_mm * math.cos(a) for a in angles]
        ys += [q.cy_mm + q.r_mm * math.sin(a) for a in angles]
    return min(xs), min(ys), max(xs), max(ys)


def _pad(label, shape, width, height, rotation_rad, x, y) -> Pad:
    return Pad(
        id=0,
        x_mm=x,
        y_mm=y,
        shape=shape,
        width_mm=width,
        height_mm=height,
        rotation_rad=rotation_rad,
        drill_mm=0.0,
        layer=None,
        net="N",
        label=label,
    )


def _centred_on(item, pad) -> bool:
    centre = item.rect().center()
    return (centre.x(), centre.y()) == pytest.approx((pad.x_mm, -pad.y_mm))


@pytest.mark.req("REQ-F-13")
def test_ui61_round_pads_are_circles_with_a_canvas_disc_for_the_drill(d08):
    """Catches a round pad drawn as its square (DEF-UV16-03) and a drill the exporters draw but the view does not."""
    view = _show(d08, "dark colour", (900, 700))
    colours = load_theme("dark").colours
    try:
        pads, drills = _items(view, "pad"), _items(view, "drill")
        assert len(pads) == len(drills) == 3
        assert all(isinstance(i, QGraphicsEllipseItem) for i in pads + drills)
        for pad in d08.boards[0].pads:
            here = [i for i in pads if _centred_on(i, pad)]
            assert len(here) == 1, pad.label
            rect = here[0].rect()
            assert (rect.width(), rect.height()) == pytest.approx((2.4, 2.4))
            assert not here[0].shape().contains(QPointF(pad.x_mm + 1.0, -pad.y_mm - 1.0))
            assert here[0].brush().color().name() == colours["text-2"]
            disc = [i for i in drills if _centred_on(i, pad)]
            assert len(disc) == 1 and disc[0].rect().width() == pytest.approx(1.2)
            assert disc[0].brush().color().name() == colours["canvas"]
    finally:
        view.close()


@pytest.mark.req("REQ-F-13")
def test_ui61_square_rect_and_oblong_pads_are_the_exporters_shape(d08):
    """Catches an oblong drawn as its bounding rectangle, and a rotation the view ignores."""
    oblong = _pad("U", "oblong", 3.0, 1.5, math.radians(30), 0.0, 20.0)
    rect = _pad("V", "rect", 2.0, 1.0, 0.0, 30.0, 20.0)
    board = dataclasses.replace(d08.boards[0], pads=(oblong, rect))
    scene = dataclasses.replace(d08, boards=(board,))
    view = _show(scene, "dark colour", (900, 700))
    try:
        by_x = sorted(_items(view, "pad"), key=lambda i: i.path().boundingRect().center().x())
        assert len(by_x) == 2 and all(isinstance(i, QGraphicsPathItem) for i in by_x)
        for pad, item in zip((oblong, rect), by_x, strict=True):
            x0, y0, x1, y1 = _extent(pad_outline(pad))
            box = item.path().boundingRect()
            assert (box.left(), -box.bottom(), box.right(), -box.top()) == pytest.approx((x0, y0, x1, y1), abs=1e-6)
        c, s = math.cos(math.radians(30)), math.sin(math.radians(30))
        corner = (oblong.x_mm + 1.5 * c - 0.75 * s, oblong.y_mm + 1.5 * s + 0.75 * c)
        assert not by_x[0].path().contains(QPointF(corner[0], -corner[1]))
        assert by_x[0].path().contains(QPointF(oblong.x_mm, -oblong.y_mm))
    finally:
        view.close()


@pytest.mark.req("REQ-F-13")
@pytest.mark.parametrize("hidden", [frozenset(), frozenset({"L1"})])
def test_ui61_lands_are_drawn_after_all_copper_its_outline_and_its_casing(d08, hidden):
    """Catches a via or pad drawn under the copper of a layer drawn after it, and one that the cue outlines or cases."""
    view = _show(d08, "dark colour", (900, 700), hidden)
    try:
        order = {id(item): rank for rank, item in enumerate(view.scene().items(Qt.SortOrder.AscendingOrder))}
        lands = [order[id(i)] for i in _items(view, *LAND_KINDS)]
        copper = [order[id(i)] for i in _items(view, *COPPER_KINDS)]
        assert lands and copper
        assert min(lands) > max(copper)
    finally:
        view.close()


@pytest.mark.req("REQ-F-13", "REQ-N-02")
def test_ui58_dimmed_outline_stays_empty_inside(d08):
    """Catches an outline whose inside shows a ghost of the ink once the DRC locate dims the copper to 35 %."""
    view, image = _render(d08, "dark colour", CROSSING_MM, 24.0, (420, 300))
    try:
        row = DrcRow(
            number=1,
            board=0,
            severity="error",
            rule_code="X",
            message="",
            clearance_text="",
            required_text="",
            layer_text="",
            at_mm=(1000.0, 1000.0),
        )
        locate_on_canvas(view, row, load_theme("dark"))
        for marker in _items(view, "drc-marker"):
            view.scene().removeItem(marker)
        dimmed = _place(view, CROSSING_MM, 24.0)
        assert dimmed != image, "the locate dims the ink"
        assert _crossing_measures(view, dimmed, d08, "dark colour")["centre"] == _board_fill("dark colour")
    finally:
        view.close()


@pytest.mark.req("REQ-F-13", "REQ-N-02")
@pytest.mark.parametrize("which", ["d08", "serpentine"])
def test_ui58_a_repaint_without_a_view_change_never_rebuilds_the_cue(d08, serpentine, which, monkeypatch):
    """Catches a zoom, pan, fit or resize step that rebuilds the cue geometry: it runs on the GUI thread (DEF-W-12)."""
    scene = d08 if which == "d08" else serpentine
    built = []
    real_strokes, real_part = layer_cue.Strokes.of, layer_cue.Part.of
    monkeypatch.setattr(layer_cue.Strokes, "of", classmethod(lambda cls, parts: built.append(1) or real_strokes(parts)))
    monkeypatch.setattr(layer_cue.Part, "of", classmethod(lambda cls, *args: built.append(1) or real_part(*args)))
    view = _show(scene, "dark colour", (900, 700))
    try:
        assert built, "the first draw builds the cue"
        cue = _items(view, *COPPER_KINDS)
        built.clear()
        view.zoom_by(1.25)
        view.zoom_by(0.8)
        view.zoom_by(4)
        bar = view.horizontalScrollBar()
        bar.setValue(bar.value() + 100)
        view.fit_view()
        view.resize(700, 600)
        QApplication.processEvents()
        view.viewport().grab()
        assert built == [] and set(cue) <= set(view.scene().items())
        _draw(view, scene, "dark greyscale")
        assert built, "a change of render mode does rebuild it"
    finally:
        view.close()


def _rgb(image: QImage) -> np.ndarray:
    image = image.convertToFormat(QImage.Format.Format_RGB32)
    raw = np.frombuffer(image.constBits(), dtype=np.uint8).reshape(image.height(), image.bytesPerLine() // 4, 4)
    return raw[:, : image.width(), :3].astype(int)


def _move(view) -> None:
    """Zoom in twice and pan right three times and down once, as a user drags, about the view centre."""
    view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
    view.zoom_by(1.7)
    view.zoom_by(1.25)
    QApplication.processEvents()
    for _ in range(3):
        view.horizontalScrollBar().setValue(view.horizontalScrollBar().value() + 70)
        QApplication.processEvents()
    view.verticalScrollBar().setValue(view.verticalScrollBar().value() - 55)
    QApplication.processEvents()


@pytest.mark.req("REQ-F-13", "REQ-N-02")
@pytest.mark.parametrize("which", ["d08", "serpentine"])
def test_ui58_the_cached_cue_draws_what_a_direct_paint_draws_after_zoom_and_pan(d08, serpentine, which):
    """Catches a cache that leaves a seam, a stale strip or a shifted layer after a pan or zoom step (DEF-W-12)."""
    scene = d08 if which == "d08" else serpentine
    cached, direct = _show(scene, "dark colour", (900, 700)), _show(scene, "dark colour", (900, 700))
    try:
        for item in _items(direct, "copper-cue"):
            item.setCacheMode(item.CacheMode.NoCache)
        assert all(i.cacheMode() == i.CacheMode.DeviceCoordinateCache for i in _items(cached, "copper-cue"))
        _move(cached)
        _move(direct)
        gap = np.abs(_rgb(cached.viewport().grab().toImage()) - _rgb(direct.viewport().grab().toImage()))
        assert gap.max() <= 4, f"{int((gap.max(axis=2) > 4).sum())} pixels differ by more than rounding"
    finally:
        cached.close()
        direct.close()


@pytest.mark.req("REQ-F-13", "REQ-N-02")
def test_ui58_a_repaint_without_a_view_change_paints_no_cue_and_a_pan_only_its_strip(serpentine, monkeypatch):
    """Catches a cue that is painted again on an idle repaint, or over the whole view on a pan step (DEF-W-12)."""
    painted = []
    real = layer_cue.LayerCueItem.paint

    def paint(self, painter, option, widget=None):
        painted.append(option.exposedRect.width() * painter.worldTransform().m11())
        real(self, painter, option, widget)

    monkeypatch.setattr(layer_cue.LayerCueItem, "paint", paint)
    view = _show(serpentine, "dark colour", (2400, 1500))  # a cache above Qt's default 10 MB must still be kept
    try:
        view.zoom_by(4)
        QApplication.processEvents()
        view.viewport().repaint()
        assert painted, "the first paint draws the cue"
        painted.clear()
        view.viewport().repaint()
        assert painted == []
        view.horizontalScrollBar().setValue(view.horizontalScrollBar().value() + 100)
        QApplication.processEvents()
        assert painted and max(painted) < 0.5 * view.viewport().width()
    finally:
        view.close()
