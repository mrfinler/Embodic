"""Dependency-free PDF 1.4 writer: A4 pages of text and vector paths in the bundled fonts, embedded whole.

Structure after Xcoil report.js Doc() (l.23-80), the team's own code. Each font is a ``Type0`` font with the
``Identity-H`` encoding over a ``CIDFontType2`` descendant whose ``FontFile2`` is the whole TrueType file (D-039 b).
Text is written as glyph ids taken from the font's own ``cmap``; a ``ToUnicode`` CMap maps them back, so a reader
extracts the characters the UI shows (µH, mΩ, mV·s/rad, U+2212). A character the font has no glyph for fails the
export (``MissingGlyphError``); it is never dropped or replaced.
"""

import functools
import math
import struct
import zlib
from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass, field

from embodic.errors import IssueCategory, Severity, ValidationIssue, message_for
from embodic.paths import resource_root

PAGE_W = 595.28
PAGE_H = 841.89
SANS_FILE = "Inter/InterVariable.ttf"
MONO_FILE = "JetBrainsMono/JetBrainsMono-Regular.ttf"
SANS, MONO = "F1", "F2"
BOLD_STROKE = 0.035  # stroke width per point of size that turns the regular face into the bold text style


def _f(value: float) -> str:
    text = f"{value:.3f}".rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


@dataclass(frozen=True, slots=True, kw_only=True)
class TrueTypeFont:
    """What a PDF needs from a TrueType file to embed it whole and to show text in it."""

    postscript_name: str
    data: bytes
    units_per_em: int
    advances: tuple[int, ...]  # advance width of each glyph id, font units
    glyph_of: Mapping[int, int]  # code point -> glyph id
    bbox: tuple[int, int, int, int]
    ascent: int
    descent: int
    cap_height: int

    def width_pt(self, text: str, size: float) -> float:
        """Return the advance width of ``text`` at ``size`` points; every character must have a glyph."""
        return sum(self.advances[self.glyph_of[ord(c)]] for c in text) * size / self.units_per_em

    def missing(self, text: str) -> str:
        """Return the characters of ``text`` the font has no glyph for, each once, in order."""
        return "".join(dict.fromkeys(c for c in text if ord(c) not in self.glyph_of))


def _tables(data: bytes) -> dict[bytes, bytes]:
    (count,) = struct.unpack_from(">H", data, 4)
    out: dict[bytes, bytes] = {}
    for i in range(count):
        tag, _, offset, length = struct.unpack_from(">4sLLL", data, 12 + 16 * i)
        out[tag] = data[offset : offset + length]
    return out


def _cmap_format_4(table: bytes) -> dict[int, int]:
    seg_count = struct.unpack_from(">H", table, 6)[0] // 2
    ends = struct.unpack_from(f">{seg_count}H", table, 14)
    starts = struct.unpack_from(f">{seg_count}H", table, 16 + 2 * seg_count)
    deltas = struct.unpack_from(f">{seg_count}h", table, 16 + 4 * seg_count)
    range_at = 16 + 6 * seg_count
    ranges = struct.unpack_from(f">{seg_count}H", table, range_at)
    out: dict[int, int] = {}
    for k, (start, end, delta, rng) in enumerate(zip(starts, ends, deltas, ranges, strict=True)):
        for code in range(start, end + 1):
            if code == 0xFFFF:
                continue
            if rng == 0:
                glyph = (code + delta) & 0xFFFF
            else:
                (glyph,) = struct.unpack_from(">H", table, range_at + 2 * k + rng + 2 * (code - start))
                glyph = (glyph + delta) & 0xFFFF if glyph else 0
            if glyph:
                out[code] = glyph
    return out


def _cmap_format_12(table: bytes) -> dict[int, int]:
    (groups,) = struct.unpack_from(">L", table, 12)
    out: dict[int, int] = {}
    for i in range(groups):
        start, end, glyph = struct.unpack_from(">LLL", table, 16 + 12 * i)
        out.update((code, glyph + code - start) for code in range(start, end + 1))
    return out


def _cmap(table: bytes) -> dict[int, int]:
    """Return the Unicode map: the full-repertoire format 12 subtable when present, else the BMP format 4 one."""
    (count,) = struct.unpack_from(">H", table, 2)
    by_format: dict[int, bytes] = {}
    for i in range(count):
        platform, encoding, offset = struct.unpack_from(">HHL", table, 4 + 8 * i)
        if (platform, encoding) in ((0, 3), (0, 4), (3, 1), (3, 10)):
            sub = table[offset:]
            by_format.setdefault(struct.unpack_from(">H", sub)[0], sub)
    if 12 in by_format:
        return _cmap_format_12(by_format[12])
    return _cmap_format_4(by_format[4])


def _postscript_name(table: bytes) -> str:
    _, count, strings = struct.unpack_from(">HHH", table)
    for i in range(count):
        platform, _, _, name_id, length, offset = struct.unpack_from(">6H", table, 6 + 12 * i)
        if name_id == 6:
            raw = table[strings + offset : strings + offset + length]
            return raw.decode("utf-16-be" if platform in (0, 3) else "latin-1")
    raise ValueError("the font has no PostScript name (name ID 6)")


def parse_truetype(data: bytes) -> TrueTypeFont:
    """Read the tables a PDF embedding needs with ``struct``: head, hhea, maxp, hmtx, cmap, OS/2 and name."""
    tables = _tables(data)
    head, hhea, os2 = tables[b"head"], tables[b"hhea"], tables[b"OS/2"]
    (glyphs,) = struct.unpack_from(">H", tables[b"maxp"], 4)
    (metrics,) = struct.unpack_from(">H", hhea, 34)
    advances = [struct.unpack_from(">H", tables[b"hmtx"], 4 * i)[0] for i in range(metrics)]
    advances += [advances[-1]] * (glyphs - metrics)
    os2_version, cap_height = struct.unpack_from(">H", os2)[0], struct.unpack_from(">h", os2, 88)[0]
    return TrueTypeFont(
        postscript_name=_postscript_name(tables[b"name"]),
        data=data,
        units_per_em=struct.unpack_from(">H", head, 18)[0],
        advances=tuple(advances),
        glyph_of=_cmap(tables[b"cmap"]),
        bbox=struct.unpack_from(">4h", head, 36),
        ascent=struct.unpack_from(">h", hhea, 4)[0],
        descent=struct.unpack_from(">h", hhea, 6)[0],
        cap_height=cap_height if os2_version >= 2 else struct.unpack_from(">h", hhea, 4)[0],
    )


@functools.cache
def bundled_font(relative: str) -> TrueTypeFont:
    """Return a font file of ``resources/fonts``, parsed once per process."""
    return parse_truetype((resource_root() / "fonts" / relative).read_bytes())


class MissingGlyphError(Exception):
    """A text holds a character the embedded font cannot show; the export stops instead of dropping it."""

    def __init__(self, font: TrueTypeFont, missing: str, text: str) -> None:
        codes = " ".join(f"U+{ord(c):04X}" for c in missing)
        self.issue = ValidationIssue(
            code="INVALID_EXPORT_GLYPH_MISSING",
            category=IssueCategory.INVALID,
            severity=Severity.ERROR,
            message=message_for("INVALID_EXPORT_GLYPH_MISSING"),
            pointers=(),
            value=codes,
            hint=f"{font.postscript_name}: {text!r}",
        )
        super().__init__(f"{font.postscript_name} has no glyph for {codes} in {text!r}")


def rgb(colour_hex: str) -> str:
    """Return ``#rrggbb`` as three PDF colour components."""
    return " ".join(_f(int(colour_hex[i : i + 2], 16) / 255) for i in (1, 3, 5))


def info_string(text: str) -> bytes:
    """Return a PDF text string: an escaped literal for ASCII, else UTF-16BE with its byte order mark in hex."""
    if text.isascii():
        return b"(" + text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)").encode("ascii") + b")"
    return b"<feff" + text.encode("utf-16-be").hex().encode("ascii") + b">"


def arc_bezier(
    cx: float, cy: float, r: float, start: float, sweep: float
) -> list[tuple[float, float, float, float, float, float]]:
    """Return cubic Bezier segments (x1, y1, x2, y2, x3, y3) of an arc, at most a quarter turn each."""
    pieces = max(1, math.ceil(abs(sweep) / (math.pi / 2) - 1e-9))
    step = sweep / pieces
    k = 4 / 3 * math.tan(step / 4)
    out = []
    for i in range(pieces):
        a0, a1 = start + i * step, start + (i + 1) * step
        x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
        x3, y3 = cx + r * math.cos(a1), cy + r * math.sin(a1)
        out.append(
            (
                x0 - k * r * math.sin(a0), y0 + k * r * math.cos(a0),
                x3 + k * r * math.sin(a1), y3 - k * r * math.cos(a1),
                x3, y3,
            )
        )  # fmt: skip
    return out


def circle_ops(x: float, y: float, r: float) -> str:
    """Return the path operators of a closed circle."""
    ops = [f"{_f(x + r)} {_f(y)} m"]
    ops += [" ".join(_f(v) for v in seg) + " c" for seg in arc_bezier(x, y, r, 0.0, 2 * math.pi)]
    return " ".join(ops) + " h"


def _to_unicode(used: Mapping[int, str]) -> bytes:
    lines = [
        "/CIDInit /ProcSet findresource begin 12 dict begin begincmap",
        "/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def",
        "/CMapName /Adobe-Identity-UCS def /CMapType 2 def",
        "1 begincodespacerange <0000> <FFFF> endcodespacerange",
    ]
    pairs = sorted(used.items())
    for k in range(0, len(pairs), 100):
        block = pairs[k : k + 100]
        lines.append(f"{len(block)} beginbfchar")
        lines += [f"<{gid:04X}> <{char.encode('utf-16-be').hex().upper()}>" for gid, char in block]
        lines.append("endbfchar")
    lines.append("endcmap CMapName currentdict /CMap defineresource pop end end")
    return "\n".join(lines).encode("ascii")


def _embed(
    ttf: TrueTypeFont, used: Mapping[int, str], add: Callable[[bytes], int], stream: Callable[[bytes, str], int]
) -> int:
    """Add the Type0 font, its CIDFontType2 descendant, descriptor, whole font file and ToUnicode map."""
    scale = 1000 / ttf.units_per_em
    name = ttf.postscript_name
    file_id = stream(ttf.data, f" /Length1 {len(ttf.data)}")
    bbox = " ".join(str(round(v * scale)) for v in ttf.bbox)
    descriptor = add(
        f"<< /Type /FontDescriptor /FontName /{name} /Flags 32 /FontBBox [{bbox}] /ItalicAngle 0 "
        f"/Ascent {round(ttf.ascent * scale)} /Descent {round(ttf.descent * scale)} "
        f"/CapHeight {round(ttf.cap_height * scale)} /StemV 80 /FontFile2 {file_id} 0 R >>".encode()
    )
    widths = " ".join(f"{gid} [{round(ttf.advances[gid] * scale)}]" for gid in sorted(used))
    cid_font = add(
        f"<< /Type /Font /Subtype /CIDFontType2 /BaseFont /{name} "
        f"/CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) /Supplement 0 >> "
        f"/FontDescriptor {descriptor} 0 R /CIDToGIDMap /Identity /DW 1000 /W [{widths}] >>".encode()
    )
    to_unicode = stream(_to_unicode(used), "")
    return add(
        f"<< /Type /Font /Subtype /Type0 /BaseFont /{name} /Encoding /Identity-H "
        f"/DescendantFonts [{cid_font} 0 R] /ToUnicode {to_unicode} 0 R >>".encode()
    )


@dataclass(slots=True)
class PdfDocument:
    """Pages of content-stream operators; ``to_bytes`` lays out the objects and the cross-reference table."""

    pages: list[list[bytes]] = field(default_factory=list)
    fonts: dict[str, TrueTypeFont] = field(
        default_factory=lambda: {SANS: bundled_font(SANS_FILE), MONO: bundled_font(MONO_FILE)}
    )
    used: dict[str, dict[int, str]] = field(default_factory=dict)  # font -> glyph id -> the character it shows

    def new_page(self) -> None:
        """Start an A4 portrait page."""
        self.pages.append([])

    def op(self, operators: str) -> None:
        """Append raw operators to the current page."""
        self.pages[-1].append(operators.encode("ascii"))

    def glyphs(self, font: str, text: str) -> bytes:
        """Return ``text`` as a hex string of glyph ids and record them for the ToUnicode map."""
        ttf = self.fonts[font]
        if missing := ttf.missing(text):
            raise MissingGlyphError(ttf, missing, text)
        used = self.used.setdefault(font, {})
        ids = [ttf.glyph_of[ord(c)] for c in text]
        for gid, c in zip(ids, text, strict=True):
            used.setdefault(gid, c)
        return b"<" + "".join(f"{gid:04X}" for gid in ids).encode("ascii") + b">"

    def width(self, text: str, size: float, *, mono: bool = False) -> float:
        """Return the advance width of ``text`` in points."""
        return self.fonts[MONO if mono else SANS].width_pt(text, size)

    @staticmethod
    def _style(size: float, bold: bool, grey: float) -> str:
        if not bold:
            return f"{_f(grey)} g 0 Tr"
        return f"{_f(grey)} g {_f(grey)} G 2 Tr {_f(size * BOLD_STROKE)} w"

    def text(self, x: float, y: float, text: str, *, size: float = 9.0, bold: bool = False, grey: float = 0.0) -> None:
        """Show one line of text with its baseline start at (x, y) points."""
        self.pages[-1].append(
            f"BT {self._style(size, bold, grey)} /{SANS} {_f(size)} Tf {_f(x)} {_f(y)} Td ".encode("ascii")
            + self.glyphs(SANS, text)
            + b" Tj ET"
        )

    def row(
        self,
        y: float,
        cells: Sequence[tuple[float, str]],
        *,
        size: float = 8.0,
        bold: bool = False,
        mono: Collection[int] = (),
    ) -> None:
        """Show table cells on one baseline in one text object, so text extraction keeps them on one line.

        ``mono`` names the cells (by index) set in the monospaced font: values, units and codes.
        """
        parts, here = [f"BT {self._style(size, bold, 0.0)}".encode("ascii")], 0.0
        for k, (x, text) in enumerate(cells):
            font = MONO if k in mono else SANS
            move = f"{_f(x)} {_f(y)}" if k == 0 else f"{_f(x - here)} 0"
            parts.append(f"/{font} {_f(size)} Tf {move} Td ".encode("ascii") + self.glyphs(font, text) + b" Tj")
            here = x
        self.pages[-1].append(b" ".join([*parts, b"ET"]))

    def haloed_text(
        self, x: float, y: float, text: str, *, size: float, fill_hex: str, halo_hex: str, halo: float
    ) -> None:
        """Show ``text`` centred on (x, y) over a stroked outline ``halo`` points wide in ``halo_hex``."""
        sans = self.fonts[SANS]
        left = x - sans.width_pt(text, size) / 2
        base = y - sans.cap_height * size / sans.units_per_em / 2
        shown = self.glyphs(SANS, text)
        start = f"/{SANS} {_f(size)} Tf {_f(left)} {_f(base)} Td ".encode("ascii")
        self.pages[-1].append(
            f"q BT 1 Tr 1 j {_f(halo)} w {rgb(halo_hex)} RG ".encode("ascii") + start + shown + b" Tj ET Q"
        )
        self.pages[-1].append(f"BT 0 Tr {rgb(fill_hex)} rg ".encode("ascii") + start + shown + b" Tj ET")

    def stroke_path(self, segments: Sequence[str], *, width: float, colour_hex: str) -> None:
        """Stroke a path given as operator strings (``m``, ``l``, ``c``)."""
        self.op(f"{rgb(colour_hex)} RG {_f(width)} w 1 J 1 j {' '.join(segments)} S")

    def circle(self, x: float, y: float, r: float, *, fill_hex: str | None, stroke_hex: str | None = None) -> None:
        """Draw a circle, filled, stroked or both."""
        paint = "B" if fill_hex is not None and stroke_hex is not None else ("f" if fill_hex is not None else "S")
        colour = (f"{rgb(fill_hex)} rg " if fill_hex is not None else "") + (
            f"{rgb(stroke_hex)} RG 0.3 w " if stroke_hex is not None else ""
        )
        self.op(f"{colour}{circle_ops(x, y, r)} {paint}")

    def to_bytes(self, info: Mapping[str, str]) -> bytes:
        """Return the file; ``info`` becomes the document information dictionary (keys without the slash)."""
        objects: list[bytes] = []

        def add(body: bytes) -> int:
            objects.append(body)
            return len(objects)

        def stream(data: bytes, extra: str) -> int:
            packed = zlib.compress(data, 9)
            head = f"<< /Length {len(packed)} /Filter /FlateDecode{extra} >>\nstream\n".encode("ascii")
            return add(head + packed + b"\nendstream")

        font_refs = []
        for name, used in sorted(self.used.items()):
            font_refs.append(f"/{name} {_embed(self.fonts[name], used, add, stream)} 0 R")
        fonts = " ".join(font_refs)
        page_ids = []
        contents = [stream(b"\n".join(ops), "") for ops in self.pages]
        pages_id = len(objects) + len(self.pages) + 1
        for content in contents:
            page_ids.append(
                add(
                    f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {_f(PAGE_W)} {_f(PAGE_H)}] "
                    f"/Resources << /Font << {fonts} >> >> /Contents {content} 0 R >>".encode()
                )
            )
        kids = " ".join(f"{i} 0 R" for i in page_ids)
        assert add(f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode()) == pages_id
        catalog = add(f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode())
        info_id = add(b"<< " + b" ".join(f"/{k} ".encode() + info_string(v) for k, v in info.items()) + b" >>")
        out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = []
        for number, body in enumerate(objects, start=1):
            offsets.append(len(out))
            out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
        xref = len(out)
        out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
        out += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets)
        out += f"trailer\n<< /Size {len(objects) + 1} /Root {catalog} 0 R /Info {info_id} 0 R >>\n".encode()
        out += f"startxref\n{xref}\n%%EOF\n".encode()
        return bytes(out)
