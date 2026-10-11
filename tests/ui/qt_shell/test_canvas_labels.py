"""Canvas labels, legend and eye hatch of ruling b and design_spec.md 3.3 (UX-AC-27, UX-AC-05, UI-27)."""

import itertools
import math
import re

import pytest
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtWidgets import QApplication

from embodic.model.vocabulary import Phase
from embodic.ui.viewmodels.appearance import PhaseRenderMode
from embodic.ui.viewmodels.results import drc_table
from embodic.ui.views.checks_view import locate_on_canvas
from embodic.ui.views.geometry_view import DATA_KIND, DATA_PHASE, GeometryView

# Label text per topology (design_spec.md 3.3): U+2212 is the minus, never the hyphen (F22).
PATTERN = {
    "spiral_12c10p_d08": "[ABC][1-4][+−]",
    "wave_16p_example": "[ABC][+−]",
    "serpentine_16p_example": "[ABC]",
}


CANVAS_PX = 500


def _items(canvas, kind):
    return [item for item in canvas.scene().items() if item.data(DATA_KIND) == kind]


def _label_boxes(canvas):
    """Return each shown label's text, phase and box in viewport pixels."""
    boxes = []
    for item in _items(canvas, "label"):
        centre = QPointF(canvas.mapFromScene(item.pos()))
        size = item.boundingRect().size()
        box = QRectF(centre.x() - size.width() / 2, centre.y() - size.height() / 2, size.width(), size.height())
        boxes.append((item.text(), item.data(DATA_PHASE), box))
    return boxes


def _assert_ux_ac_27(canvas, example_id, phases=frozenset("ABC")):
    boxes = _label_boxes(canvas)
    assert phases <= {phase for _, phase, _ in boxes}
    assert [label for label, _, _ in boxes if not re.fullmatch(PATTERN[example_id], label)] == []
    for (first, _, a), (second, _, b) in itertools.combinations(boxes, 2):
        assert not a.intersects(b), (first, second)
    view = QRectF(canvas.viewport().rect())
    assert [(label, box) for label, _, box in boxes if not view.contains(box)] == []
    return boxes


@pytest.fixture
def shown(make_shell, wait_ready):
    """Return a function that opens an example in a shell and returns the window once it is drawn.

    ``tall`` drags the splitter under the canvas down, as a user does to look at the drawing: at 1280 x 800 the
    results tabs leave the canvas 182 px tall.
    """

    def open_example(example_id, tall=True):
        window = make_shell().window
        window.outcome.open_example(example_id)
        wait_ready(window)
        if tall:
            window.centre_split.setSizes([CANVAS_PX, 140])
        QApplication.processEvents()
        window.canvas.fit_view()
        return window

    return open_example


@pytest.mark.req("REQ-N-23", "REQ-N-14")
@pytest.mark.parametrize("example_id", list(PATTERN))
def test_ux_ac_27_labels_never_overlap_and_name_every_phase_at_fit_zoom_and_3x(shown, example_id):
    """Catches overlapping labels (F5: "C12+R10+10+"), a phase without its letter (F6) or a hyphen for minus (F22)."""
    window = shown(example_id)
    canvas = window.canvas
    at_fit = _assert_ux_ac_27(canvas, example_id)
    r_inner, r_outer = window.outcome.state.value.scene.boards[0].envelope_mm
    canvas.zoom_by(3)
    canvas.centerOn(0, -(r_inner + r_outer) / 2)  # the top of the copper ring, not the bore
    # Zoomed in, a phase names itself when one of its fit-zoom anchors (embodic.geometry.labels) is in view with
    # room for its label: 30 px from every edge.
    room = QRectF(canvas.viewport().rect()).adjusted(30, 30, -30, -30)
    anchors = window.outcome.state.value.scene.marks[0].anchors
    in_view = frozenset(a.phase.value for a in anchors if room.contains(canvas.mapFromScene(a.x_mm, -a.y_mm)))
    assert in_view
    at_3x = _assert_ux_ac_27(canvas, example_id, in_view)
    assert at_3x and len(at_fit) >= 3


@pytest.mark.req("REQ-N-23")
def test_ux_ac_27_wave_shows_more_labels_when_zoomed_in_and_places_them_again_after_a_resize(shown):
    """Catches labels placed once at load: zooming in must add labels, a resize must place them for the new edge.

    At fit zoom every belt label places (DEF-UV4-01), so the resize starts from a view zoomed out below fit.
    """
    window = shown("wave_16p_example")
    canvas = window.canvas
    at_fit = [item.pos() for item in _items(canvas, "label")]
    board_top = window.outcome.state.value.scene.boards[0].envelope_mm[1]
    canvas.zoom_by(3)
    canvas.centerOn(0, -board_top)
    region = canvas.mapToScene(canvas.viewport().rect()).boundingRect()
    zoomed = [item.pos() for item in _items(canvas, "label")]
    assert len(zoomed) > sum(region.contains(pos) for pos in at_fit)
    canvas.fit_view()
    canvas.zoom_by(1 / 3)
    zoomed_out = len(_items(canvas, "label"))
    window.resize(1600, 1000)
    window.centre_split.setSizes([800, 100])
    canvas.fit_view()
    assert len(_items(canvas, "label")) > zoomed_out
    _assert_ux_ac_27(canvas, "wave_16p_example")


@pytest.mark.req("REQ-N-23")
def test_ui27_a_skipped_label_shows_in_the_hover_tooltip_of_its_copper(shown):
    """Catches a label that the placement drops with no other way to read it (ruling b)."""
    window = shown("spiral_12c10p_d08", tall=False)
    canvas = window.canvas
    every = {anchor.text for anchor in window.outcome.state.value.scene.marks[0].anchors}
    placed = {item.text() for item in _items(canvas, "label")}
    skipped = every - placed
    assert skipped, "D08 at fit zoom in a 1280 x 800 window places fewer than its 12 labels"
    tips = {item.toolTip() for item in _items(canvas, "copper")}
    assert skipped <= tips


@pytest.mark.req("REQ-N-23", "REQ-N-14")
@pytest.mark.parametrize("mode", list(PhaseRenderMode))
def test_ux_ac_05_the_canvas_legend_shows_a_solid_copper_bar_an_eye_swatch_and_the_phase_name(shown, mode):
    """Catches a canvas without a legend (F4), a dashed or wrongly coloured bar, or a legend row without its name."""
    window = shown("spiral_12c10p_d08")
    if window.appearance.phase_render_mode.value is not mode:
        window.appearance.toggle_phase_render_mode()
    canvas = window.canvas
    assert canvas.legend_phases() == tuple(Phase)
    image = canvas.viewport().grab().toImage()
    for row, phase in enumerate(Phase):
        style = window.tokens.phase_style(phase)
        ink = style.colour_hex if mode is PhaseRenderMode.COLOUR else style.grey_hex
        bar, swatch, _ = canvas.legend_row_geometry(row)
        y = round(bar.center().y() - 0.5)
        along = [image.pixelColor(x, y).name() for x in range(round(bar.left()) + 1, round(bar.right()) - 1)]
        assert set(along) == {ink}, (phase, set(along))
        assert swatch.left() > bar.right()
    legend = canvas.legend_rect()
    assert QRectF(canvas.viewport().rect()).contains(legend)


@pytest.mark.req("REQ-N-23")
def test_ui27_eye_hatch_is_drawn_in_screen_pixels_so_it_shows_at_fit_zoom(shown, qtbot):
    """Catches a hatch that scales with the board (hairlines at fit zoom, F7): its pitch must stay about 4 px."""
    window = shown("spiral_12c10p_d08")
    scene = window.outcome.state.value.scene
    canvas = GeometryView()
    qtbot.addWidget(canvas)
    canvas.resize(900, 900)
    canvas.show()
    qtbot.waitExposed(canvas)
    # Only the eyes' own layer: L2 copper is not cut out of an L1 eye, so it could show through the disc.
    canvas.show_geometry(scene, window.tokens, PhaseRenderMode.COLOUR, frozenset({"L2"}))
    canvas.fit_view()
    image = canvas.viewport().grab().toImage()
    for item in _items(canvas, "hatch"):
        colour = window.tokens.phase_style(Phase(item.data(DATA_PHASE))).colour_hex
        centre = canvas.mapFromScene(item.rect().center())
        radius = item.rect().width() / 2 * canvas.transform().m11() - 2
        assert radius > 6, radius
        # Horizontal chords above and below the label each cross one hatch line per tile width.
        crossings = []
        for dy in (-0.8, -0.65, 0.65, 0.8):
            y = centre.y() + round(radius * dy)
            half = int(math.sqrt(radius**2 - (radius * dy) ** 2))
            row = [image.pixelColor(x, y).name() for x in range(centre.x() - half, centre.x() + half + 1)]
            crossings.append([x for x, name in enumerate(row) if name == colour])
        assert sum(len(hits) for hits in crossings) >= 4, (item.data(DATA_PHASE), crossings)
        gaps = [b - a for hits in crossings for a, b in itertools.pairwise(hits)]
        assert gaps and min(gaps) >= 4, (item.data(DATA_PHASE), crossings)


@pytest.mark.req("REQ-F-33")
def test_drc_locate_marker_survives_the_label_placement_of_later_zoom_steps(shown):
    """Catches a label pass that clears the scene or the dimmed copper of a located DRC failure."""
    window = shown("wave_16p_example")
    canvas = window.canvas
    table = drc_table(window.outcome.state.value.outcome)
    locate_on_canvas(canvas, table.rows[0], window.tokens)
    canvas.zoom_by(1.25)
    canvas.zoom_by(0.8)
    assert len(_items(canvas, "drc-marker")) == 1
    assert {round(item.opacity(), 2) for item in _items(canvas, "copper")} == {0.35}


def _phases_with_copper_in_view(canvas):
    """Return the phases whose copper shape meets the view (interconnect copper has no phase)."""
    seen = canvas.mapToScene(canvas.viewport().rect()).boundingRect()
    return {item.data(DATA_PHASE) for item in canvas.scene().items(seen) if item.data(DATA_KIND) == "copper"} - {""}


@pytest.mark.req("REQ-N-23")
def test_ruling_h_the_wave_fit_view_labels_both_signs_of_every_phase(shown):
    """U-S4e ruling h. Catches the fit view of main fd190c1 where every label read "+" while the belts alternate."""
    window = shown("wave_16p_example", tall=False)
    texts = {label for label, _, _ in _assert_ux_ac_27(window.canvas, "wave_16p_example")}
    assert {f"{p}{s}" for p in "ABC" for s in "+−"} <= texts


@pytest.mark.req("REQ-N-23")
@pytest.mark.parametrize("example_id", ["spiral_12c10p_d08", "wave_16p_example"])
@pytest.mark.parametrize("corner", [(1, 1), (-1, 1), (0, -1)])
def test_ruling_h_every_phase_with_copper_in_view_has_a_label_and_leaders_stay_inside(shown, example_id, corner):
    """U-S4e ruling h. Catches a zoomed view that shows a phase's copper but no label, or a leader leaving the view."""
    window = shown(example_id, tall=False)
    canvas = window.canvas
    canvas.zoom_by(4.0)
    r = max(board.envelope_mm[1] for board in window.outcome.state.value.scene.boards) * 0.7
    canvas.centerOn(corner[0] * r, -corner[1] * r)
    QApplication.processEvents()
    boxes = _label_boxes(canvas)
    labelled = {phase for _, phase, _ in boxes}
    assert _phases_with_copper_in_view(canvas) <= labelled, (example_id, corner)
    view = QRectF(canvas.viewport().rect()).adjusted(2, 2, -2, -2)
    for leader in _items(canvas, "leader"):
        line = leader.line()
        for end in (line.p1(), line.p2()):
            assert view.contains(QPointF(canvas.mapFromScene(end))), (example_id, corner)
    assert [(label, box) for label, _, box in boxes if not QRectF(canvas.viewport().rect()).contains(box)] == []


@pytest.mark.req("REQ-N-15")
def test_ruling_h_the_canvas_keeps_fit_zoom_through_a_resize_until_the_user_zooms(shown):
    """U-S4e ruling h. Catches the 40 px ring left in a 598 x 124 px canvas after a resize on main fd190c1."""
    window = shown("spiral_12c10p_d08", tall=False)
    canvas = window.canvas

    def ring_px():
        return canvas.mapFromScene(canvas._extent).boundingRect().height()

    for size in ((1280, 800), (1600, 1000), (1100, 700)):
        window.resize(*size)
        QApplication.processEvents()
        assert ring_px() >= 0.9 * min(canvas.viewport().width(), canvas.viewport().height()), size
    canvas.zoom_by(2.0)
    zoomed = canvas.transform().m11()
    window.resize(1300, 820)
    QApplication.processEvents()
    assert canvas.transform().m11() == zoomed, "a user zoom survives a resize"
    canvas.fit_view()
    window.resize(1500, 900)
    QApplication.processEvents()
    assert ring_px() >= 0.9 * min(canvas.viewport().width(), canvas.viewport().height())
