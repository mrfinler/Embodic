"""Synthetic files for the controls of LG-03 to LG-06: one planted word in every kind of text the scanner reads."""

import io
import json
import zipfile
from collections.abc import Callable
from pathlib import Path

from tests.static.lg_scan import Corpus, Text, member_texts, resource_texts, source_texts


def minimal_pdf(line: str) -> bytes:
    """Return a one-page PDF whose only text is `line`, with a correct cross-reference table."""
    escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET".encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = b"%PDF-1.4\n"
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n%s\nendobj\n" % (number, body)
    table = b"".join(b"%010d 00000 n \n" % offset for offset in offsets)
    size = len(objects) + 1
    return (
        out
        + b"xref\n0 %d\n0000000000 65535 f \n%s" % (size, table)
        + b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (size, len(out))
    )


def zip_bytes(members: dict[str, str]) -> bytes:
    """Return a ZIP archive that holds the given text members."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, text in members.items():
            archive.writestr(name, text)
    return buffer.getvalue()


def write(path: Path, text: str) -> Path:
    """Write a text file, creating its folder."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _python(folder: Path, relative: str, source: str) -> list[Text]:
    package = folder / "embodic"
    write(package / relative, source)
    return list(source_texts(package))


def _resource(folder: Path, name: str, text: str) -> list[Text]:
    resources = folder / "resources"
    write(resources / name, text)
    return list(resource_texts(resources))


def _export(name: str, data: bytes) -> list[Text]:
    return list(member_texts(Corpus.EXPORTS, "planted", name, data))


PLANTERS: dict[str, Callable[[str, Path], list[Text]]] = {
    "python-literal": lambda w, f: _python(f, "mod.py", f"LABEL = {f'Planted {w} text'!r}\n"),
    "catalogue-value": lambda w, f: _python(f, "ui/strings/mod.py", f"STRINGS = {{'k': {f'Planted {w} text'!r}}}\n"),
    "identifier-after-underscore": lambda w, f: _python(f, "mod.py", f"CODE = 'RANGE_{w.upper()}_RESULT'\n"),
    "identifier-camel-case": lambda w, f: _python(f, "mod.py", f"FLAG = 'is{w.capitalize()}Result'\n"),
    "json-key": lambda w, f: _resource(f, "data.json", json.dumps({f"{w.lower()}_min_mm": 1.0})),
    "json-value": lambda w, f: _resource(f, "data.json", json.dumps({"label": f"Planted {w} text"})),
    "markdown-line": lambda w, f: _resource(f, "notes.md", f"first\nPlanted {w}\n"),
    "qss-line": lambda w, f: _resource(f, "notes.qss", f"first\nPlanted {w}\n"),
    "toml-line": lambda w, f: _resource(f, "notes.toml", f"first\nPlanted {w}\n"),
    "svg": lambda w, f: _resource(f, "icon.svg", f"<svg>\n<title>Planted {w}</title>\n</svg>\n"),
    "dxf-comment": lambda w, f: _resource(f, "part.dxf", f"0\nSECTION\n999\nPlanted {w}\n0\nEOF\n"),
    "pdf-page": lambda w, f: _export("report.pdf", minimal_pdf(f"Planted {w} text")),
    "zip-member-text": lambda w, f: _export("bundle.zip", zip_bytes({"notes.txt": f"Planted {w} text\n"})),
    "zip-member-name": lambda w, f: _export("bundle.zip", zip_bytes({f"{w.lower()}_part.dxf": "0\nEOF\n"})),
}
ARTEFACTS = tuple(PLANTERS)


def plant(artefact: str, word: str, folder: Path) -> list[Text]:
    """Return the texts of a synthetic file of one artefact kind that holds `word`."""
    return PLANTERS[artefact](word, folder)
