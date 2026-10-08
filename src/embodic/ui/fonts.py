"""The bundled fonts (design_spec.md section 4, D-039 a): their files, the family stacks and their registration.

The module imports no Qt (import contract C2): the app hands ``register_fonts`` Qt's loader and the application.
Nothing is fetched at run time.
"""

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Protocol, TypeVar

from embodic.paths import resource_root

INTER = "Inter Variable"  # the family name inside InterVariable.ttf, which Qt registers
JETBRAINS_MONO = "JetBrains Mono"
UI_FALLBACKS = ("Segoe UI",)  # then the platform sans, which Qt picks when none of these exists
MONO_FALLBACKS = ("Cascadia Mono", "Consolas", "monospace")
BODY_PX = 13

FONT_FILES = {
    INTER: ("Inter/InterVariable.ttf",),
    JETBRAINS_MONO: ("JetBrainsMono/JetBrainsMono-Regular.ttf", "JetBrainsMono/JetBrainsMono-Medium.ttf"),
}


def font_file(relative: str) -> Path:
    """Return the path of one bundled font file, relative to ``resources/fonts``."""
    return resource_root() / "fonts" / relative


class AppFont(Protocol):
    """The part of ``QFont`` this module calls."""

    def setFamilies(self, families: Sequence[str], /) -> None:  # noqa: N802
        """Set the family list, first choice first."""

    def setPixelSize(self, size: int, /) -> None:  # noqa: N802
        """Set the size in pixels."""

    @staticmethod
    def insertSubstitutions(family: str, substitutes: Sequence[str], /) -> None:  # noqa: N802
        """Name the families Qt tries when ``family`` lacks a glyph."""


F = TypeVar("F", bound=AppFont)


class FontApplication(Protocol[F]):
    """The part of ``QApplication`` this module calls."""

    def font(self) -> F:
        """Return the application font."""

    def setFont(self, font: F, /) -> None:  # noqa: N802
        """Make ``font`` the application font."""


def register_fonts(add_font: Callable[[str], int], application: FontApplication[F]) -> None:
    """Load every bundled file and make Inter 13 px the application font, Segoe UI then the platform sans after it.

    JetBrains Mono, which the style sheet names for numbers, units and codes, falls back to Cascadia Mono, Consolas and
    then any monospace font.

    Raises
    ------
    RuntimeError
        When Qt cannot load a bundled file: the install is broken.
    """
    for family, files in FONT_FILES.items():
        for relative in files:
            path = font_file(relative)
            if add_font(str(path)) < 0:
                raise RuntimeError(f"bundled {family} font {path.name} did not load")
    font = application.font()
    font.setFamilies([INTER, *UI_FALLBACKS])
    font.setPixelSize(BODY_PX)
    font.insertSubstitutions(INTER, list(UI_FALLBACKS))
    font.insertSubstitutions(JETBRAINS_MONO, list(MONO_FALLBACKS))
    application.setFont(font)
