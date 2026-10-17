"""REQ-N-23: Windows high contrast (rows N23-1 to N23-6 of docs/phase3/design/fix_wave_f1.md section (b)).

The contrast property has no setter, so these tests inject it and the system palette through `create_shell`. The
palettes are examples, not readings of a Windows contrast theme.
"""

import re
from pathlib import Path

import pytest
from PySide6.QtCore import QEvent, QPoint, QRect, Qt
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication, QLabel, QLineEdit, QWidget
from tests.ui.qt_shell.conftest import D08

from embodic.ui.theme import load_theme, themes_dir
from embodic.ui.viewmodels.appearance import PhaseRenderMode
from embodic.ui.views.geometry_view import DATA_KIND, DATA_PHASE
from embodic.ui.views.high_contrast import (
    GLYPH_TOKENS,
    SYSTEM_PAIR,
    high_contrast_sheet,
    high_contrast_tokens,
    prefers_dark,
    template_tokens,
    write_glyphs,
)
from embodic.ui.views.style import palette_for

HEX = re.compile(r"#[0-9a-fA-F]{6}")
COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
TOOLTIP_TAIL = "On while Windows high contrast is on."
DARK_EXAMPLE = {"window": "#000000", "text": "#ffffff", "disabled": "#a6a6a6"}  # fix_wave_f1.md (b), example
LIGHT_EXAMPLE = {"window": "#ffffff", "text": "#000000", "disabled": "#a6a6a6"}  # second example of N23-6


def example_palette(colours: dict[str, str]) -> QPalette:
    """Return a system palette example: Window, Base and Button in one colour, the text roles in the other."""
    palette = QPalette()
    window, text = QColor(colours["window"]), QColor(colours["text"])
    for role in (QPalette.ColorRole.Window, QPalette.ColorRole.Base, QPalette.ColorRole.Button):
        palette.setColor(role, window)
    for role in (QPalette.ColorRole.WindowText, QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText):
        palette.setColor(role, text)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(colours["disabled"]))
    return palette


@pytest.fixture
def contrast_shell(make_shell, wait_ready):
    """Return a shell under high contrast with the black example palette, D08 computed."""
    shell = make_shell(high_contrast=True, system_palette=example_palette(DARK_EXAMPLE))
    shell.window.session.load_example(D08)
    wait_ready(shell.window)
    yield shell
    shell.system.high_contrast = False
    shell.window.on_os_contrast_changed()


def sheet_colours(sheet: str) -> set[str]:
    """Return the colours the rules of a style sheet use; comments are left out."""
    return {value.lower() for value in HEX.findall(COMMENT.sub("", sheet))}


def region(window, widget: QWidget) -> QRect:
    """Return a widget's rectangle in window coordinates."""
    return QRect(widget.mapTo(window, QPoint(0, 0)), widget.size())


@pytest.mark.req("REQ-N-23")
def test_n23_1_high_contrast_forces_greyscale_and_disables_the_toggle(contrast_shell):
    """N23-1. Catches colour phases under high contrast, or a toggle that would switch them back on."""
    window = contrast_shell.window
    action = window.toolstrip.actions_by_id["act-greyscale"]
    assert window.appearance.phase_render_mode.value is PhaseRenderMode.GREYSCALE_HATCH
    assert (action.isChecked(), action.isEnabled()) == (True, False)
    assert action.toolTip().endswith(TOOLTIP_TAIL)


@pytest.mark.req("REQ-N-23")
def test_n23_2_the_sheet_is_the_dark_sheet_in_system_colours(contrast_shell):
    """N23-2. Catches a theme colour left in the sheet, or a high-contrast sheet that differs in more than colours."""
    sheet = QApplication.instance().styleSheet()
    dark = load_theme("dark")
    assert sheet_colours(sheet) <= {*DARK_EXAMPLE.values(), dark.colours["canvas"]}
    template = (themes_dir() / "dark.qss").read_text(encoding="utf-8")
    assert HEX.sub("#colour", sheet) == HEX.sub("#colour", template)


@pytest.mark.req("REQ-N-23")
def test_n23_3_status_text_and_the_focus_ring_take_the_system_pair(contrast_shell, qtbot):
    """N23-3. Catches chrome text or the focus ring drawn in a theme grey instead of the system colours."""
    window = contrast_shell.window
    units = window.findChild(QLabel, "st-units")
    # Offscreen text is antialiased per subpixel: 13 px "mm" in white peaks at (237, 246, 247), never at #ffffff.
    # Without antialiasing every text pixel is the text colour itself.
    font = units.font()
    font.setStyleStrategy(QFont.StyleStrategy.NoAntialias)
    units.setFont(font)
    image = window.grab(region(window, units)).toImage()
    pixels = [image.pixelColor(x, y) for y in range(image.height()) for x in range(image.width())]
    assert image.pixelColor(0, 0).name() == "#000000"
    assert max(pixels, key=lambda c: c.lightness()).name() == "#ffffff"
    field = window.findChild(QLineEdit, "param-r-inner")
    field.setFocus(Qt.FocusReason.TabFocusReason)
    qtbot.waitUntil(field.hasFocus)
    ring = window.grab(region(window, field)).toImage()
    w, h = ring.width(), ring.height()
    samples = [(w // 2, 0), (w // 2, 1), (w // 2, h - 1), (w // 2, h - 2), (0, h // 2), (1, h // 2), (w - 1, h // 2)]
    assert {ring.pixelColor(x, y).name() for x, y in samples} == {"#ffffff"}


@pytest.mark.req("REQ-N-23")
def test_n23_4_the_drawing_is_dark_greyscale_with_every_label_and_eye(contrast_shell):
    """N23-4. Catches a light canvas on a black system window, colour copper, or labels and eyes lost."""
    window = contrast_shell.window
    dark = load_theme("dark")
    canvas = window.canvas
    image = canvas.viewport().grab().toImage()
    assert image.pixelColor(2, 2).name() == dark.colours["canvas"]
    items = canvas.scene().items()
    copper = {item.pen().color().name() for item in items if item.data(DATA_KIND) == "copper" and item.data(DATA_PHASE)}
    assert copper == {style.grey_hex for style in dark.phases}
    labels = [item.text() for item in items if item.data(DATA_KIND) == "label"]
    assert labels and all(re.fullmatch("[ABC][1-4][+−]", label) for label in labels)
    assert {label[0] for label in labels} == {"A", "B", "C"}
    assert sum(item.data(DATA_KIND) in ("eye", "hatch") for item in items) == 12


@pytest.mark.req("REQ-N-23")
@pytest.mark.parametrize("greyscale_before", [False, True], ids=["colour chosen", "greyscale chosen"])
def test_n23_5_turning_high_contrast_off_restores_the_theme_and_the_chosen_mode(
    make_shell, wait_ready, greyscale_before
):
    """N23-5. Catches the system palette or sheet left behind, or the user's render mode lost."""
    shell = make_shell()
    window = shell.window
    if greyscale_before:
        window.appearance.toggle_phase_render_mode()
    chosen = window.appearance.phase_render_mode.value
    shell.system.high_contrast, shell.system.palette = True, example_palette(DARK_EXAMPLE)
    window.on_os_contrast_changed()
    assert window.appearance.phase_render_mode.value is PhaseRenderMode.GREYSCALE_HATCH
    shell.system.high_contrast = False
    window.on_os_contrast_changed()
    app = QApplication.instance()
    tokens = load_theme("light")
    assert app.styleSheet() == (themes_dir() / "light.qss").read_text(encoding="utf-8")
    assert app.palette() == palette_for(tokens)
    assert window.appearance.phase_render_mode.value is chosen
    assert window.toolstrip.actions_by_id["act-greyscale"].isEnabled()
    assert not window.toolstrip.actions_by_id["act-greyscale"].toolTip().endswith(TOOLTIP_TAIL)


@pytest.mark.req("REQ-N-23")
def test_n23_6_a_system_palette_change_restyles_once_and_the_drawing_follows_its_lightness(contrast_shell):
    """N23-6, DEF-US11-05. Catches a sheet that keeps the old system colours, or a drawing theme that ignores them.

    While the theme choice is System, the drawing follows the lightness of the system window colour.
    """
    window = contrast_shell.window
    app = QApplication.instance()
    contrast_shell.system.palette = example_palette(LIGHT_EXAMPLE)
    QApplication.sendEvent(window, QEvent(QEvent.Type.ApplicationPaletteChange))
    sheet = app.styleSheet()
    assert sheet_colours(sheet) <= {*LIGHT_EXAMPLE.values(), load_theme("light").colours["canvas"]}
    assert window.canvas.backgroundBrush().color().name() == load_theme("light").colours["canvas"]
    QApplication.sendEvent(window, QEvent(QEvent.Type.ApplicationPaletteChange))
    assert app.styleSheet() == sheet


@pytest.mark.req("REQ-N-23")
def test_the_shipped_template_tokens_are_those_of_the_template_the_sheets_are_generated_from():
    """Catches theme_template_tokens.json drifting from Agent 1's tools/design/theme_template.qss.

    To regenerate: the colour tokens of each stripped template line, @dir and @focus-ring-px left out, in order.
    """
    template = (Path(__file__).resolve().parents[3] / "tools" / "design" / "theme_template.qss").read_text(
        encoding="utf-8"
    )
    expected = [
        [token for token in re.findall(r"@([a-z0-9-]+)", line) if token not in ("dir", "focus-ring-px")]
        for line in template.strip().split("\n")
    ]
    assert template_tokens() == expected


@pytest.mark.req("REQ-N-23")
@pytest.mark.parametrize("name", ["light", "dark"])
def test_each_colour_value_of_a_theme_sheet_is_the_value_of_its_template_token(name):
    """Catches a template line matched to the wrong sheet line: mapping each token to its own value changes nothing.

    In dark, `divider` and `surface-selected` share #2e2e2e in one rule and still map to different system colours,
    so the token of a value must come from the template, not from the value.
    """
    sheet = (themes_dir() / f"{name}.qss").read_text(encoding="utf-8")
    template = template_tokens()
    tokens = load_theme(name)
    own = {**tokens.colours, **{f"phase-{s.phase.value.lower()}": s.colour_hex for s in tokens.phases}}
    own |= {f"phase-{s.phase.value.lower()}-grey": s.grey_hex for s in tokens.phases}
    assert high_contrast_sheet(sheet, template, own) == sheet
    marked = high_contrast_sheet(sheet, template, {token: "#abcdef" for token in SYSTEM_PAIR})
    assert sheet_colours(marked) == {"#abcdef", tokens.colours["canvas"]}


@pytest.mark.req("REQ-N-23")
@pytest.mark.parametrize(
    ("window_hex", "dark"),
    [("#000000", True), ("#757575", True), ("#767676", False), ("#fff8dc", False), ("#ffffff", False)],
)
def test_def_us11_05_a_contrast_theme_is_dark_when_its_window_is_nearer_black(window_hex, dark):
    """DEF-US11-05. Catches the System choice resolving every contrast theme to light.

    Luminance by WCAG 2.2: #757575 is 0.178 and #767676 is 0.181, either side of 0.179 (computed by hand).
    """
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(window_hex))
    assert prefers_dark(palette) is dark


@pytest.mark.req("REQ-N-23")
def test_glyphs_are_written_in_the_mapped_colours():
    """Catches indicator glyphs left in theme greys: the check mark is Window, the chevrons WindowText."""
    tokens = load_theme("dark")
    for name, token in GLYPH_TOKENS.items():
        assert f'stroke="{tokens.colours[token]}"' in (themes_dir() / "dark" / name).read_text(encoding="utf-8")
    chrome = high_contrast_tokens(tokens, example_palette(DARK_EXAMPLE))
    folder = write_glyphs("dark", tokens.colours, chrome.colours) / "dark"
    strokes = {
        name: re.search(r'stroke="(#[0-9a-f]{6})"', (folder / name).read_text()).group(1) for name in GLYPH_TOKENS
    }
    assert strokes == {"check.svg": "#000000", "chevron-down.svg": "#ffffff", "chevron-down-disabled.svg": "#a6a6a6"}
