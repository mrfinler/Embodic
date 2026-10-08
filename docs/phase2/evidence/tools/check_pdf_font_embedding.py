"""Check that the PDF report embeds each bundled font file whole and byte for byte (D-039 b, OFL condition 2 reading).

Rerun from the repository root: PYTHONPATH=src python docs/phase2/evidence/tools/check_pdf_font_embedding.py
Needs the dev extra (pypdf, fontTools). Exit 1 when an embedded font stream differs from the file in resources/fonts,
when a bundled font that the writer names is missing from the PDF, or when a font file's SHA-256 differs from FONTS.md.
"""

from __future__ import annotations

import hashlib
import io
import re
import sys
import tempfile
from pathlib import Path

import pypdf
from fontTools.ttLib import TTFont

from embodic.api import ComputeOutcome, compute_project
from embodic.io.examples import examples_dir
from embodic.io.exporters import ExportSummary
from embodic.io.pdf_writer import MONO_FILE, SANS_FILE
from embodic.io.report import write_report_pdf
from embodic.paths import resource_root

FONTS = resource_root() / "fonts"
EXAMPLE = "spiral_12c10p_d08"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fonts_md_hashes() -> dict[str, str]:
    table = (FONTS / "FONTS.md").read_text(encoding="utf-8")
    return dict(re.findall(r"^\| `([^`]+)` \|.*\| `([0-9a-f]{64})` \|$", table, re.M))


def embedded_fonts(pdf: Path) -> dict[str, bytes]:
    """BaseFont name -> decoded FontFile2 stream, over every page of the PDF."""
    found: dict[str, bytes] = {}
    for page in pypdf.PdfReader(pdf).pages:
        for ref in page["/Resources"]["/Font"].values():
            font = ref.get_object()
            (descendant,) = font["/DescendantFonts"]
            stream = descendant.get_object()["/FontDescriptor"]["/FontFile2"].get_object()
            found[str(font["/BaseFont"])] = stream.get_data()
    return found


def main() -> int:
    outcome = compute_project(examples_dir() / f"{EXAMPLE}.embodic.json")
    assert isinstance(outcome, ComputeOutcome), outcome
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        summary = write_report_pdf(outcome, Path(tmp) / "report.pdf")
        assert isinstance(summary, ExportSummary), summary
        embedded = embedded_fonts(summary.path)
    recorded = fonts_md_hashes()
    for relative in (SANS_FILE, MONO_FILE):
        disk = (FONTS / relative).read_bytes()
        name = TTFont(io.BytesIO(disk))["name"].getDebugName(6)
        stream = embedded.get(f"/{name}")
        same = stream is not None and sha256(stream) == sha256(disk)
        listed = recorded.get(relative) == sha256(disk)
        names = TTFont(io.BytesIO(stream))["name"] if stream else None
        print(f"{relative}: disk {sha256(disk)} bytes {len(disk)}")
        print(f"  embedded /{name}: {sha256(stream) if stream else 'absent'} bytes {len(stream or b'')}")
        print(f"  identical to disk: {same} | FONTS.md hash matches disk: {listed}")
        if names:
            print(f"  name ID 0 in the embedded copy: {names.getDebugName(0)!r}")
            print(f"  name ID 13 in the embedded copy: {names.getDebugName(13)!r}")
        failures += [] if same else [f"{relative}: embedded stream differs from the file"]
        failures += [] if listed else [f"{relative}: FONTS.md hash differs from the file"]
    print(f"fonts in the PDF: {sorted(embedded)}")
    for message in failures:
        print("FAIL:", message)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
