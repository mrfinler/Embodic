"""Theme switch and persistence; geometry zoom, pan, layers and render modes (UI-03, UI-04, UI-26, UI-27)."""

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QWidget

from embodic.model.vocabulary import Phase
from embodic.ui.theme import ThemeName, load_theme
from embodic.ui.viewmodels.appearance import PhaseRenderMode
from embodic.ui.viewmodels.outcome import eyes_shown
from embodic.ui.views.geometry_view import DATA_KIND, DATA_LAYER, DATA_PHASE, ZOOM_MAX, ZOOM_MIN

# Region objectName -> chrome token of its background (design_spec.md sections 3.1 and 8).
REGION_BACKGROUND = {
    "toolstrip": "surface",
    "statusbar": "surface",
    "results-rail": "surface",
    "inspector": "surface",
    "fig-canvas": "canvas",
}


def _background(window, name):
    """Return the colour of a pixel near the top-right inside a region (away from text and borders)."""
    widget = window.findChild(QWidget, name)
    image = widget.grab().toImage()
    return image.pixelColor(QPoint(image.width() - 6, image.height() // 2)).name()


@pytest.mark.req("REQ-N-27")
@pytest.mark.parametrize(
    ("choice", "os_dark", "expected"),
    [(ThemeName.LIGHT, True, "light"), (ThemeName.DARK, False, "dark"), (ThemeName.SYSTEM, True, "dark")],
)
def test_ui26_every_region_restyles_at_runtime_to_the_chosen_theme(make_shell, choice, os_dark, expected):
    """Catches a region that keeps the old theme after a switch, or 'system' ignoring the OS scheme."""
    window = make_shell(os_dark=os_dark).window
    other = ThemeName.DARK if expected == "light" else ThemeName.LIGHT
    window.appearance.set_theme(other)
    window.appearance.set_theme(choice)
    tokens = load_theme(expected)
    seen = {name: _background(window, name) for name in REGION_BACKGROUND}
    assert seen == {name: tokens.colours[token] for name, token in REGION_BACKGROUND.items()}
    palette = QApplication.instance().palette()
    assert palette.color(palette.ColorRole.Window).name() == tokens.colours["bg-app"]


@pytest.mark.req("REQ-N-27")
def test_ui26_the_theme_choice_persists_after_a_restart(make_shell):
    """Catches a choice that is applied but not written to the settings file."""
    first = make_shell()
    first.window.appearance.cycle_theme()
    chosen = first.window.appearance.theme.value
    first.window.close()
    second = make_shell(settings_path=first.settings_path).window
    assert second.appearance.theme.value is chosen
    assert second.tokens.name == ("dark" if chosen is ThemeName.DARK else "light")


def _items(window, kind, layer=None):
    return [
        item
        for item in window.canvas.scene().items()
        if item.data(DATA_KIND) == kind and (layer is None or item.data(DATA_LAYER) == layer)
    ]


@pytest.mark.req("REQ-N-23", "REQ-N-28")
def test_ui27_both_render_modes_draw_phase_colour_or_grey_and_keep_every_label(d08_shell):
    """Catches a mode that drops the phase letters, keeps colour in greyscale, or swaps phase styles."""
    window = d08_shell.window
    tokens = window.tokens
    for mode, attribute in ((PhaseRenderMode.COLOUR, "colour_hex"), (PhaseRenderMode.GREYSCALE_HATCH, "grey_hex")):
        if window.appearance.phase_render_mode.value is not mode:
            window.appearance.toggle_phase_render_mode()
        pens = {(item.data(DATA_PHASE), item.pen().color().name()) for item in _items(window, "copper")}
        expected = {(s.phase.value, getattr(s, attribute)) for s in tokens.phases}
        assert {pair for pair in pens if pair[0]} == expected, mode
        labels = [item.text() for item in _items(window, "label")]
        assert {label[0] for label in labels} == {"A", "B", "C"} and len(labels) >= 3, mode
        assert len(_items(window, "eye")) == 4 and len(_items(window, "hatch")) == 8, mode
        assert {item.data(DATA_PHASE) for item in _items(window, "eye")} == {Phase.A.value}
        assert {item.data(DATA_PHASE) for item in _items(window, "hatch")} == {Phase.B.value, Phase.C.value}


@pytest.mark.req("REQ-N-23")
def test_ui27_each_eye_fill_is_its_coil_eye_disc(d08_shell):
    """Catches a fill drawn past the eye disc (the view-model test proves the disc never reaches copper)."""
    window = d08_shell.window
    shown = window.outcome.state.value.scene
    discs = {
        (m.phase.value, round(m.cx_mm, 9), round(m.cy_mm, 9)): m.eye_radius_mm
        for m in eyes_shown(shown.boards[0], shown.marks[0], frozenset())
    }
    fills = _items(window, "eye") + _items(window, "hatch")
    assert len(fills) == len(discs) == 12
    for item in fills:
        rect = item.rect()
        key = (item.data(DATA_PHASE), round(rect.center().x(), 9), round(-rect.center().y(), 9))
        assert rect.width() / 2 == pytest.approx(discs[key]) and rect.height() == pytest.approx(rect.width())


@pytest.mark.req("REQ-F-13")
def test_ui03_zoom_stays_between_01x_and_200x_and_copper_width_stays_in_millimetres(d08_shell):
    """Catches unbounded zoom or cosmetic pens (strokes that keep their pixel width while zooming)."""
    canvas = d08_shell.window.canvas
    trace_width_mm = d08_shell.window.outcome.project.design.winding.coil.trace_width_mm
    for _ in range(40):
        canvas.zoom_by(1.25)
    assert canvas.zoom_factor() == pytest.approx(ZOOM_MAX)
    for _ in range(80):
        canvas.zoom_by(0.8)
    assert canvas.zoom_factor() == pytest.approx(ZOOM_MIN)
    copper = _items(d08_shell.window, "copper")
    widths = {round(item.pen().widthF(), 9) for item in copper}
    assert trace_width_mm in widths
    assert not any(item.pen().isCosmetic() for item in copper)


@pytest.mark.req("REQ-F-13")
def test_ui03_arrow_keys_pan_the_view(d08_shell, qtbot):
    """Catches a canvas whose arrow keys do nothing once zoomed in."""
    canvas = d08_shell.window.canvas
    canvas.zoom_by(4)
    centre = canvas.mapToScene(canvas.viewport().rect().center())
    qtbot.keyClick(canvas, Qt.Key.Key_Right)
    qtbot.keyClick(canvas, Qt.Key.Key_Down)
    moved = canvas.mapToScene(canvas.viewport().rect().center())
    assert moved.x() > centre.x() and moved.y() > centre.y()


@pytest.mark.req("REQ-F-13")
def test_ui04_a_hidden_layer_is_absent_from_the_scene_and_returns_when_shown(d08_shell):
    """Catches a layer toggle that only dims items, or one that cannot bring the layer back."""
    window = d08_shell.window
    before = len(_items(window, "copper", "L2"))
    assert before > 0
    window.layer_boxes["L2"].setChecked(False)
    assert _items(window, "copper", "L2") == [] and _items(window, "via", "L2") == []
    assert len(_items(window, "copper", "L1")) > 0
    window.layer_boxes["L2"].setChecked(True)
    assert len(_items(window, "copper", "L2")) == before


@pytest.mark.req("REQ-F-13", "REQ-N-23")
def test_ui04_hiding_the_top_layer_keeps_every_phase_label_and_moves_the_eyes_to_the_next_layer(d08_shell):
    """Catches labels that vanish with the top layer, or eye fills left over copper that is no longer drawn."""
    window = d08_shell.window
    window.layer_boxes["L1"].setChecked(False)
    assert {item.data(DATA_PHASE) for item in _items(window, "label")} == {"A", "B", "C"}
    eyes = _items(window, "eye") + _items(window, "hatch")
    assert len(eyes) == 12 and {item.data(DATA_LAYER) for item in eyes} == {"L2"}


@pytest.mark.req("REQ-N-27")
def test_ui26_canvas_background_follows_the_theme(d08_shell):
    """Catches a canvas left white in the dark theme."""
    window = d08_shell.window
    window.appearance.set_theme(ThemeName.DARK)
    assert window.canvas.backgroundBrush().color() == QColor(load_theme("dark").colours["canvas"])
