"""Windows high contrast (REQ-N-23, fix_wave_f1.md (b)): the chrome takes the system colours, the drawing does not.

The high-contrast style sheet is the theme's generated sheet with each colour token replaced by its system colour.
Which token a colour value stands for comes from the template the sheet was generated from: two tokens of one rule
can share a value in a theme (dark `divider` and `surface-selected`) and still map to different system colours.
`resources/themes/theme_template.qss` is a copy of `tools/design/theme_template.qss`, which a test keeps equal.
"""

import functools
import hashlib
import re
import tempfile
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import Literal, TypeAlias

from PySide6.QtGui import QColor, QPalette

from embodic.ui.theme import ThemeTokens, themes_dir

SystemColour: TypeAlias = Literal["window", "window-text", "disabled-window-text"]

# fix_wave_f1.md (b), "Token to palette map". A token not listed (canvas, board-fill, the phases) keeps its theme
# value: the drawing keeps its own colours.
SYSTEM_PAIR: Mapping[str, SystemColour] = {
    "bg-app": "window",
    "surface": "window",
    "surface-sunken": "window",
    "surface-selected": "window",
    "text-inverse": "window",
    "text-1": "window-text",
    "text-2": "window-text",
    "text-3": "window-text",
    "divider": "window-text",
    "grid-line": "window-text",
    "border-control": "window-text",
    "border-strong": "window-text",
    "focus-ring": "window-text",
    "surface-inverse": "window-text",
    "status-pass": "window-text",
    "status-fail": "window-text",
    "status-warn": "window-text",
    "text-disabled": "disabled-window-text",
}

# The token each indicator glyph of build_themes.py is stroked in.
GLYPH_TOKENS: Mapping[str, str] = {
    "check.svg": "text-inverse",
    "chevron-down.svg": "text-2",
    "chevron-down-disabled.svg": "text-disabled",
}

# Equal contrast against black and white: (L + 0.05) / 0.05 = 1.05 / (L + 0.05) (fix_wave_f1.md (b)).
DARK_BELOW_LUMINANCE = 0.179

_TOKEN_ROW = re.compile(r"^(?P<lead>\s+@(?P<token>[a-z0-9-]+)\s+)(?P<value>#[0-9a-fA-F]{6})$")
_TEMPLATE_TOKEN = re.compile(r"@([a-z0-9-]+)")
_NOT_A_COLOUR = frozenset({"dir", "focus-ring-px"})
_HEX = re.compile(r"#[0-9a-fA-F]{6}")
TEMPLATE_FILE = "theme_template.qss"


def system_colours(palette: QPalette) -> dict[SystemColour, str]:
    """Return the three system colours the map uses, as lowercase #rrggbb."""
    active, disabled = QPalette.ColorGroup.Active, QPalette.ColorGroup.Disabled
    return {
        "window": palette.color(active, QPalette.ColorRole.Window).name(),
        "window-text": palette.color(active, QPalette.ColorRole.WindowText).name(),
        "disabled-window-text": palette.color(disabled, QPalette.ColorRole.WindowText).name(),
    }


def relative_luminance(colour: QColor) -> float:
    """Return the WCAG 2.2 relative luminance of an sRGB colour."""

    def channel(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * channel(colour.redF()) + 0.7152 * channel(colour.greenF()) + 0.0722 * channel(colour.blueF())


def prefers_dark(palette: QPalette) -> bool:
    """Return whether a contrast theme is dark: its window colour is nearer black than white (DEF-US11-05)."""
    window = palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Window)
    return relative_luminance(window) < DARK_BELOW_LUMINANCE


def high_contrast_tokens(tokens: ThemeTokens, palette: QPalette) -> ThemeTokens:
    """Return the chrome tokens under high contrast: each mapped token in its system colour, the rest unchanged."""
    system = system_colours(palette)
    colours = {token: system[SYSTEM_PAIR[token]] if token in SYSTEM_PAIR else v for token, v in tokens.colours.items()}
    return replace(tokens, colours=colours)


def high_contrast_sheet(theme_sheet: str, template: str, colours: Mapping[str, str]) -> str:
    """Return a generated theme sheet with each colour token's value replaced by ``colours[token]``.

    ``theme_sheet`` is the header build_themes.py writes followed by the rendered lines of ``template``. The n-th
    colour value of a rendered line is the n-th colour token of its template line; a token ``colours`` lacks keeps
    its value. The header's token table changes the same way.
    """
    lines = theme_sheet.split("\n")
    body = template.strip().split("\n")
    start = len(lines) - 1 - len(body)
    if start < 0 or lines[-1]:
        raise ValueError("the sheet does not end with the lines of the template")
    out = []
    for line in lines[:start]:
        row = _TOKEN_ROW.match(line)
        out.append(line if row is None else row["lead"] + colours.get(row["token"], row["value"]))
    for line, source in zip(lines[start:-1], body, strict=True):
        tokens = [t for t in _TEMPLATE_TOKEN.findall(source) if t not in _NOT_A_COLOUR]
        rule, comment, tail = line.partition(" /* ")
        values = _HEX.findall(rule)
        if len(values) != len(tokens):
            raise ValueError(f"the rendered line does not match its template line: {source}")
        pieces = _HEX.split(rule)
        swapped = [colours.get(token, value) for token, value in zip(tokens, values, strict=True)]
        out.append("".join(piece + new for piece, new in zip(pieces, [*swapped, ""], strict=True)) + comment + tail)
    return "\n".join([*out, ""])


@functools.cache
def _glyph_root() -> Path:
    return Path(tempfile.mkdtemp(prefix="embodic-high-contrast-"))


def write_glyphs(theme: str, theme_colours: Mapping[str, str], colours: Mapping[str, str]) -> Path:
    """Write the theme's indicator glyphs in ``colours`` and return the folder to search before the themes folder.

    The folder name carries the colours, so a cached pixmap of other colours is never reused.
    """
    key = hashlib.sha256(repr(sorted(colours.items())).encode()).hexdigest()[:12]
    root = _glyph_root() / key
    folder = root / theme
    folder.mkdir(parents=True, exist_ok=True)
    for name, token in GLYPH_TOKENS.items():
        svg = (themes_dir() / theme / name).read_text(encoding="utf-8")
        text = svg.replace(f'stroke="{theme_colours[token]}"', f'stroke="{colours[token]}"')
        path = folder / name
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            path.write_text(text, encoding="utf-8")
    return root
