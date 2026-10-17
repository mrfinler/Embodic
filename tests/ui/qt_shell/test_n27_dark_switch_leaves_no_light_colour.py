"""REQ-N-27 (V3-01 gap N-27): after a runtime switch to dark no visible widget keeps a light-theme colour.

`test_theme_and_geometry.py` reads the background of five regions. This walk reads the palette and the inline style
sheet of every visible widget, and the application style sheet that Qt applied, against the light-only token hexes.
A light-theme hex is "light-only" when its token differs between the two theme files and no dark token has that hex.
The palette roles are the ones the shell paints with; Qt leaves `Light` and `BrightText` at white in both themes.
"""

import re

import pytest
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication, QWidget

from embodic.ui.theme import ThemeName, load_theme

pytestmark = pytest.mark.req("REQ-N-27")

Role = QPalette.ColorRole
PAINTED_ROLES = (
    Role.Window,
    Role.WindowText,
    Role.Base,
    Role.AlternateBase,
    Role.Text,
    Role.Button,
    Role.ButtonText,
    Role.Highlight,
    Role.HighlightedText,
    Role.ToolTipBase,
    Role.ToolTipText,
    Role.PlaceholderText,
    Role.Mid,
    Role.Dark,
)
GROUPS = (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive, QPalette.ColorGroup.Disabled)
HEX = re.compile(r"#[0-9a-fA-F]{6}\b")


def light_only_hexes() -> dict[str, str]:
    """Return {hex: light token} for every light token whose dark value differs and is not a dark token's hex."""
    light, dark = load_theme("light").colours, load_theme("dark").colours
    dark_hexes = {value.lower() for value in dark.values()}
    return {
        value.lower(): token
        for token, value in light.items()
        if value.lower() != dark[token].lower() and value.lower() not in dark_hexes
    }


def stale_colours(window: QWidget) -> dict[str, list[str]]:
    """Map each light-theme colour in a visible palette, inline sheet or the applied sheet to the widgets holding it."""
    stale = light_only_hexes()
    found: dict[str, list[str]] = {}
    widgets = [window, *(w for w in window.findChildren(QWidget) if w.isVisible())]
    for widget in widgets:
        widget.ensurePolished()
        name = widget.objectName() or type(widget).__name__
        palette = widget.palette()
        for group in GROUPS:
            for role in PAINTED_ROLES:
                colour = palette.color(group, role).name()
                if colour in stale:
                    message = f"palette {group.name}/{role.name} is {colour} (light {stale[colour]})"
                    found.setdefault(message, []).append(name)
        for colour in HEX.findall(widget.styleSheet()):
            if colour.lower() in stale:
                message = f"inline style sheet holds {colour} (light {stale[colour.lower()]})"
                found.setdefault(message, []).append(name)
    for colour in HEX.findall(QApplication.instance().styleSheet()):
        if colour.lower() in stale:
            found.setdefault(f"application style sheet holds {colour} (light {stale[colour.lower()]})", []).append(
                "app"
            )
    return found


def test_n27_a_runtime_switch_to_dark_leaves_no_light_colour_in_any_visible_widget(d08_shell, qtbot):
    """Catches a widget with a hard-coded or stale light colour, which the five-region background check never visits."""
    window = d08_shell.window
    window.appearance.set_theme(ThemeName.LIGHT)
    qtbot.wait(50)
    assert stale_colours(window), "control: the light theme paints with light colours, so the scan must see them"
    window.appearance.set_theme(ThemeName.DARK)
    qtbot.wait(100)
    assert window.tokens.name == "dark"
    assert len([w for w in window.findChildren(QWidget) if w.isVisible()]) > 100
    assert {message: names[:3] for message, names in stale_colours(window).items()} == {}
