"""The PDF writer's own TrueType reader against fontTools (dev-only oracle) on the bundled files (D-039 b)."""

import io

import pytest
from fontTools.ttLib import TTFont

from embodic.io.pdf_writer import MONO_FILE, SANS_FILE, parse_truetype
from embodic.paths import resource_root


def _oracle(relative: str) -> TTFont:
    return TTFont(resource_root() / "fonts" / relative)


@pytest.mark.parametrize("relative", [SANS_FILE, MONO_FILE])
def test_reader_maps_every_code_point_and_width_as_fonttools_does(relative: str) -> None:
    """Catches an off-by-one in the cmap segments or hmtx tail: text would show wrong glyphs or wrong widths."""
    oracle = _oracle(relative)
    font = parse_truetype((resource_root() / "fonts" / relative).read_bytes())
    assert font.glyph_of == {code: oracle.getGlyphID(name) for code, name in oracle.getBestCmap().items()}
    order = oracle.getGlyphOrder()
    assert font.advances == tuple(oracle["hmtx"][name][0] for name in order)
    assert font.units_per_em == oracle["head"].unitsPerEm
    assert font.postscript_name == oracle["name"].getDebugName(6)


def test_reader_falls_back_to_the_format_4_map_without_a_format_12_one() -> None:
    """Catches a reader that only understands format 12: a font with a BMP-only cmap would lose every glyph."""
    oracle = _oracle(MONO_FILE)
    oracle["cmap"].tables = [t for t in oracle["cmap"].tables if t.format == 4]
    buffer = io.BytesIO()
    oracle.save(buffer)
    font = parse_truetype(buffer.getvalue())
    expected = {code: oracle.getGlyphID(name) for code, name in oracle.getBestCmap().items()}
    assert font.glyph_of == expected and ord("Ω") in font.glyph_of
