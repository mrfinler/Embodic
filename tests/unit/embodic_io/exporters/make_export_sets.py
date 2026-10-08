"""Write one export set per packaged example under build/exports/<example>/ for review.

Run from the repository root: ``python tests/unit/embodic_io/exporters/make_export_sets.py``. A design that fails DRC
is exported with ``allow_drc_errors=True``, so its files carry ``drc_passed=false``.
"""

import sys
import zipfile
from pathlib import Path

from embodic.api import ComputeOutcome, compute_project
from embodic.io.bundle import write_bundle
from embodic.io.examples import examples_dir
from embodic.io.exporters import ExportKind, ExportRefused, PhaseRenderMode
from embodic.io.svg_writer import write_svg


def export_set(outcome: ComputeOutcome, folder: Path, name: str) -> list[str]:
    """Write the bundle, unpack it beside itself and add the greyscale SVG; return the file names."""
    folder.mkdir(parents=True, exist_ok=True)
    kinds = [k for k in ExportKind if k is not ExportKind.README]
    assert outcome.boards is not None
    if not any(b.outline.holes for b in outcome.boards.boards):
        kinds.remove(ExportKind.DXF_SCREWS)
    bundle = folder / f"{name}.zip"
    result = write_bundle(outcome, kinds, bundle, allow_drc_errors=True)
    assert not isinstance(result, ExportRefused), result
    with zipfile.ZipFile(bundle) as archive:
        archive.extractall(folder)
    grey = write_svg(
        outcome, folder / f"{name}_greyscale.svg", mode=PhaseRenderMode.GREYSCALE_HATCH, allow_drc_errors=True
    )
    assert not isinstance(grey, ExportRefused), grey
    return sorted(p.name for p in folder.iterdir())


def main(root: Path) -> None:
    """Export every packaged example."""
    for path in sorted(examples_dir().glob("*.embodic.json")):
        name = path.name.split(".")[0]
        outcome = compute_project(path)
        assert isinstance(outcome, ComputeOutcome), outcome
        print(
            name,
            "ok" if outcome.ok else "DRC failed (exported with confirmation)",
            export_set(outcome, root / name, name),
        )


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("build/exports"))
