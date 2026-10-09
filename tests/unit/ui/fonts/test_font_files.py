"""The bundled font files: glyph coverage (fontTools), licence texts and the hashes FONTS.md records (D-039 a)."""

import hashlib
import re

import pytest
from fontTools.ttLib import TTFont

from embodic.paths import resource_root
from embodic.ui.fonts import FONT_FILES, font_file

FONTS_DIR = resource_root() / "fonts"
# The characters embodic prints in units, values and quantity symbols: µ, Ω, °, minus, ≈, middle dot, the no-break
# space between number and unit (U-S4e ruling e1) and the Greek η, δ, Δ of results/labels.py.
REQUIRED = {
    "µ": 0x00B5,
    "Ω": 0x03A9,
    "°": 0x00B0,
    "−": 0x2212,
    "≈": 0x2248,
    "·": 0x00B7,
    "NBSP": 0x00A0,
    "eta": 0x03B7,
    "delta": 0x03B4,
    "Delta": 0x0394,
}
FILES = [relative for files in FONT_FILES.values() for relative in files]


@pytest.mark.req("REQ-L-07")
@pytest.mark.parametrize(
    ("relative", "code"),
    [pytest.param(r, c, id=f"{r.split('/')[-1]}-{n}") for r in FILES for n, c in REQUIRED.items()],
)
def test_bundled_font_has_the_glyphs_embodic_prints(relative: str, code: int) -> None:
    """Catches a font that would show a unit symbol as a box or fall back to another family."""
    cmap = TTFont(font_file(relative), lazy=True).getBestCmap()
    assert code in cmap, f"U+{code:04X} missing from {relative}"


@pytest.mark.req("REQ-N-06")
def test_every_bundled_file_is_the_family_the_app_registers() -> None:
    """Catches a renamed or swapped file: the app would register a family the style sheet does not name."""
    for family, files in FONT_FILES.items():
        for relative in files:
            names = TTFont(font_file(relative), lazy=True)["name"]
            assert family in {names.getDebugName(1), names.getDebugName(16)}, relative


@pytest.mark.req("REQ-N-19")
def test_licence_texts_ship_beside_the_fonts() -> None:
    """Catches a font folder without its SIL OFL 1.1 text (the licence requires it with every copy)."""
    for relative in ("Inter/LICENSE.txt", "JetBrainsMono/OFL.txt"):
        assert "SIL Open Font License, Version 1.1" in (FONTS_DIR / relative).read_text(encoding="utf-8"), relative


@pytest.mark.req("REQ-N-19")
def test_fonts_md_records_the_hash_of_every_file_in_the_folder() -> None:
    """Catches a font file replaced, added or removed without FONTS.md recording its source and SHA-256."""
    table = (FONTS_DIR / "FONTS.md").read_text(encoding="utf-8")
    recorded = dict(re.findall(r"^\| `([^`]+)` \|.*\| `([0-9a-f]{64})` \|$", table, re.M))
    shipped = {
        path.relative_to(FONTS_DIR).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in FONTS_DIR.rglob("*")
        if path.is_file() and path.name != "FONTS.md"
    }
    assert recorded == shipped
