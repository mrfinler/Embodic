"""Apply a theme to the application: Fusion style, a QPalette from the tokens, Agent 1's style sheet, icons."""

import functools
import logging
from pathlib import Path

from PySide6.QtCore import QByteArray, QDir, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPalette, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication

from embodic.paths import resource_root
from embodic.ui.theme import ThemeTokens, recolour_svg, themes_dir
from embodic.ui.views.high_contrast import TEMPLATE_FILE, high_contrast_sheet, high_contrast_tokens, write_glyphs

logger = logging.getLogger(__name__)

ICON_SIZES_PX = (24, 16)


def icons_dir() -> Path:
    """Return the folder of the monochrome toolstrip icons."""
    return resource_root() / "icons"


def _svg_text(stem: str) -> str | None:
    path = icons_dir() / f"{stem}.svg"
    if not path.is_file():
        logger.warning("icon %s.svg is missing; its button shows the label only", stem)
        return None
    return path.read_text(encoding="utf-8")


@functools.cache
def _pixmap(svg: str, colour_hex: str, size_px: int) -> QPixmap:
    renderer = QSvgRenderer(QByteArray(recolour_svg(svg, colour_hex, size_px).encode("utf-8")))
    pixmap = QPixmap(QSize(size_px, size_px))
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap


def themed_icon(stem: str, tokens: ThemeTokens) -> QIcon | None:
    """Return the icon drawn in the theme's icon colours, or None (with one warning) when its file is missing.

    The icon colours equal ``text-1`` and ``text-disabled`` in tokens.json > icon_color for both themes.
    """
    svg = _svg_text(stem)
    if svg is None:
        return None
    icon = QIcon()
    for size_px in ICON_SIZES_PX:
        icon.addPixmap(_pixmap(svg, tokens.colours["text-1"], size_px), QIcon.Mode.Normal)
        icon.addPixmap(_pixmap(svg, tokens.colours["text-disabled"], size_px), QIcon.Mode.Disabled)
    return icon


def palette_for(tokens: ThemeTokens) -> QPalette:
    """Return a Fusion palette built from the chrome tokens, so unstyled parts follow the theme."""
    c = {token: QColor(value) for token, value in tokens.colours.items()}
    palette = QPalette()
    roles = {
        QPalette.ColorRole.Window: "bg-app",
        QPalette.ColorRole.WindowText: "text-1",
        QPalette.ColorRole.Base: "surface",
        QPalette.ColorRole.AlternateBase: "surface-sunken",
        QPalette.ColorRole.Text: "text-1",
        QPalette.ColorRole.Button: "surface",
        QPalette.ColorRole.ButtonText: "text-1",
        QPalette.ColorRole.Highlight: "surface-inverse",
        QPalette.ColorRole.HighlightedText: "text-inverse",
        QPalette.ColorRole.ToolTipBase: "surface-inverse",
        QPalette.ColorRole.ToolTipText: "text-inverse",
        QPalette.ColorRole.PlaceholderText: "text-3",
        QPalette.ColorRole.Mid: "border-control",
        QPalette.ColorRole.Dark: "border-strong",
    }
    for role, token in roles.items():
        palette.setColor(role, c[token])
    for role in (QPalette.ColorRole.WindowText, QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText):
        palette.setColor(QPalette.ColorGroup.Disabled, role, c["text-disabled"])
    return palette


def apply_theme(app: QApplication, tokens: ThemeTokens) -> None:
    """Restyle every widget of the application with one theme.

    Setting a style sheet repolishes every widget of the application, even when the text is the one already applied:
    a second window's build spent about 0.7 s of its 1.7 s there (U-M6f), so an unchanged sheet is not set again.
    """
    app.setStyle("Fusion")
    QDir.setSearchPaths("theme", [str(themes_dir())])
    app.setPalette(palette_for(tokens))
    _set_sheet(app, (themes_dir() / f"{tokens.name}.qss").read_text(encoding="utf-8"))


def apply_high_contrast(app: QApplication, tokens: ThemeTokens, system: QPalette) -> ThemeTokens:
    """Restyle the chrome in the system colours of ``system``, the palette already applied (fix_wave_f1.md (b)).

    Return the chrome tokens. The sheet is rendered as text, not from palette() references: a disabled label styled
    with palette(window-text) painted the active colour, and a palette change reached it only with the next sheet.
    """
    app.setStyle("Fusion")
    chrome = high_contrast_tokens(tokens, system)
    glyphs = write_glyphs(tokens.name, tokens.colours, chrome.colours)
    QDir.setSearchPaths("theme", [str(glyphs), str(themes_dir())])
    theme_sheet = (themes_dir() / f"{tokens.name}.qss").read_text(encoding="utf-8")
    template = (themes_dir() / TEMPLATE_FILE).read_text(encoding="utf-8")
    _set_sheet(app, high_contrast_sheet(theme_sheet, template, chrome.colours))
    return chrome


def _set_sheet(app: QApplication, sheet: str) -> None:
    if app.styleSheet() != sheet:
        app.setStyleSheet(sheet)
