"""Dependency-free PDF 1.4 writer: A4 pages of text and vector paths in the standard Helvetica fonts, no embedding.

Structure after Xcoil report.js Doc() (l.23-80), the team's own code. Text is WinAnsi; characters outside it are
replaced by ASCII spellings (the ohm sign becomes ``ohm``) so the standard fonts can show every value.
"""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

PAGE_W = 595.28
PAGE_H = 841.89
FONTS = {"F1": "Helvetica", "F2": "Helvetica-Bold"}
_SUBSTITUTE = {
    "\u2212": "-",  # minus sign
    "\u03a9": "ohm",
    "\u221a": "sqrt",
    "\u2264": "<=",
    "\u2265": ">=",
    "\u00d7": "x",
}


def _f(value: float) -> str:
    text = f"{value:.3f}".rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def winansi(text: str) -> bytes:
    """Return ``text`` in WinAnsi (cp1252), with ASCII spellings for the characters it lacks."""
    spelled = "".join(_SUBSTITUTE.get(c, c) for c in text)
    return spelled.encode("cp1252", errors="replace")


def pdf_string(text: str) -> bytes:
    """Return a PDF literal string: parentheses and backslash escaped, bytes above 126 as octal escapes."""
    out = bytearray(b"(")
    for byte in winansi(text):
        if byte in b"()\\":
            out += b"\\" + bytes([byte])
        elif byte > 126 or byte < 32:
            out += f"\\{byte:03o}".encode("ascii")
        else:
            out.append(byte)
    return bytes(out + b")")


def rgb(colour_hex: str) -> str:
    """Return ``#rrggbb`` as three PDF colour components."""
    return " ".join(_f(int(colour_hex[i : i + 2], 16) / 255) for i in (1, 3, 5))


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


@dataclass(slots=True)
class PdfDocument:
    """Pages of content-stream operators; ``to_bytes`` lays out the objects and the cross-reference table."""

    pages: list[list[bytes]] = field(default_factory=list)

    def new_page(self) -> None:
        """Start an A4 portrait page."""
        self.pages.append([])

    def op(self, operators: str) -> None:
        """Append raw operators to the current page."""
        self.pages[-1].append(operators.encode("ascii"))

    def text(self, x: float, y: float, text: str, *, size: float = 9.0, bold: bool = False, grey: float = 0.0) -> None:
        """Show one line of text with its baseline start at (x, y) points."""
        font = "F2" if bold else "F1"
        self.pages[-1].append(
            f"BT {_f(grey)} g /{font} {_f(size)} Tf {_f(x)} {_f(y)} Td ".encode("ascii") + pdf_string(text) + b" Tj ET"
        )

    def row(self, y: float, cells: Sequence[tuple[float, str]], *, size: float = 8.0, bold: bool = False) -> None:
        """Show table cells on one baseline in one text object, so text extraction keeps them on one line."""
        font = "F2" if bold else "F1"
        parts, here = [f"BT 0 g /{font} {_f(size)} Tf".encode("ascii")], 0.0
        for k, (x, text) in enumerate(cells):
            move = f"{_f(x)} {_f(y)}" if k == 0 else f"{_f(x - here)} 0"
            parts.append(f"{move} Td ".encode("ascii") + pdf_string(text) + b" Tj")
            here = x
        self.pages[-1].append(b" ".join([*parts, b"ET"]))

    def stroke_path(self, segments: Sequence[str], *, width: float, colour_hex: str) -> None:
        """Stroke a path given as operator strings (``m``, ``l``, ``c``)."""
        self.op(f"{rgb(colour_hex)} RG {_f(width)} w 1 J 1 j {' '.join(segments)} S")

    def circle(self, x: float, y: float, r: float, *, fill_hex: str | None, stroke_hex: str | None = None) -> None:
        """Draw a circle, filled, stroked or both."""
        ops = [f"{_f(x + r)} {_f(y)} m"]
        ops += [" ".join(_f(v) for v in seg) + " c" for seg in arc_bezier(x, y, r, 0.0, 2 * math.pi)]
        paint = "B" if fill_hex is not None and stroke_hex is not None else ("f" if fill_hex is not None else "S")
        colour = (f"{rgb(fill_hex)} rg " if fill_hex is not None else "") + (
            f"{rgb(stroke_hex)} RG 0.3 w " if stroke_hex is not None else ""
        )
        self.op(f"{colour}{' '.join(ops)} h {paint}")

    def to_bytes(self, info: Mapping[str, str]) -> bytes:
        """Return the file; ``info`` becomes the document information dictionary (keys without the slash)."""
        objects: list[bytes] = []

        def add(body: bytes) -> int:
            objects.append(body)
            return len(objects)

        font_ids = {
            name: add(f"<< /Type /Font /Subtype /Type1 /BaseFont /{base} /Encoding /WinAnsiEncoding >>".encode())
            for name, base in FONTS.items()
        }
        fonts = " ".join(f"/{name} {oid} 0 R" for name, oid in font_ids.items())
        pages_id = len(objects) + 2 * len(self.pages) + 1
        page_ids = []
        for ops in self.pages:
            stream = b"\n".join(ops)
            content = add(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream")
            page_ids.append(
                add(
                    f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {_f(PAGE_W)} {_f(PAGE_H)}] "
                    f"/Resources << /Font << {fonts} >> >> /Contents {content} 0 R >>".encode()
                )
            )
        kids = " ".join(f"{i} 0 R" for i in page_ids)
        assert add(f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode()) == pages_id
        catalog = add(f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode())
        info_id = add(b"<< " + b" ".join(f"/{k} ".encode() + pdf_string(v) for k, v in info.items()) + b" >>")
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
