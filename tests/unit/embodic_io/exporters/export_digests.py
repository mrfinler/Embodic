"""Print the SHA-256 of the SVG drawings and the PDF report of every packaged example, with a fixed stamp.

Run from the repository root with the package of the tree under test on ``PYTHONPATH``, once per tree, and diff the two
outputs to show that a change leaves the exports byte-identical (DEF-U-M8o-02):

    PYTHONPATH=<tree>/src python tests/unit/embodic_io/exporters/export_digests.py > digests.txt

The stamp's clock is replaced by a constant, because the report and the drawing otherwise differ by the second.
"""

import dataclasses
import hashlib
import tempfile
from pathlib import Path

from embodic.api import ComputeOutcome, compute_project
from embodic.io import report
from embodic.io.examples import examples_dir
from embodic.io.exporters import ExportMetadata, ExportRefused, PhaseRenderMode, export_metadata, exportable_boards
from embodic.io.svg_writer import svg_document

GENERATED_UTC = "2026-01-01T00:00:00Z"


def _stamp(outcome: ComputeOutcome) -> ExportMetadata:
    return dataclasses.replace(export_metadata(outcome), generated_utc=GENERATED_UTC)


def digests(path: Path) -> list[tuple[str, str]]:
    """Return (export name, SHA-256) for the drawing in each render mode and the report of one example file."""
    outcome = compute_project(path)
    assert isinstance(outcome, ComputeOutcome), outcome
    boards = exportable_boards(outcome, allow_drc_errors=True)
    assert not isinstance(boards, ExportRefused), boards
    rows = []
    for mode in PhaseRenderMode:
        text, _ = svg_document(boards, mode, _stamp(outcome))
        rows.append((f"svg {mode.value}", hashlib.sha256(text.encode("utf-8")).hexdigest()))
    report.export_metadata = _stamp  # type: ignore[assignment]
    with tempfile.TemporaryDirectory() as folder:
        target = Path(folder) / "report.pdf"
        assert not isinstance(report.write_report_pdf(outcome, target), ExportRefused)
        rows.append(("pdf report", hashlib.sha256(target.read_bytes()).hexdigest()))
    return rows


def main() -> None:
    """Print one line per export of every packaged example."""
    for path in sorted(examples_dir().glob("*.embodic.json")):
        name = path.name.split(".")[0]
        for export, digest in digests(path):
            print(f"{digest}  {name} {export}")


if __name__ == "__main__":
    main()
