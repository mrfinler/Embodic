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
    """Restyle every widget of the application with one theme."""
    app.setStyle("Fusion")
    QDir.setSearchPaths("theme", [str(themes_dir())])
    app.setPalette(palette_for(tokens))
    app.setStyleSheet((themes_dir() / f"{tokens.name}.qss").read_text(encoding="utf-8"))
