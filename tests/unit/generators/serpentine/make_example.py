"""Write the packaged serpentine example to resources/examples; rerunning gives the same bytes.

Run from the repository root: ``python -m tests.unit.generators.serpentine.make_example``. The parameters are Xcoil's
default serpentine preset (engine.js l.19-97, 16 poles, 4 turns, 2 layers per phase); every value is an example value
(D-014). The outline follows Xcoil's defaults: the board radius is 1.2 times the outermost copper (outlineScale), the
bore 0.85 times the innermost (innerScale), and 8 M3 screws sit 3.5 mm inside the edge.
"""

import dataclasses
from pathlib import Path

from tests.unit.model.designs import serpentine_design

from embodic.generators import build_layout
from embodic.io.canonical import design_hash
from embodic.io.examples import EXAMPLE_SUFFIX, examples_dir
from embodic.io.project import ProjectFile, encode_project, project_document
from embodic.model.design import DesignParameters
from embodic.model.outline import CircleOutline, OutlineSpec, ScrewFit, ScrewPattern
from embodic.model.provenance import ExampleRef, derive_provenance
from embodic.results import load_registry

EXAMPLE_ID = "serpentine_16p_example"
TITLE = "Serpentine, 16 poles"  # U-S4e ruling g; D-041b: also the design `/name`
SOURCE_NOTE = "Xcoil default serpentine preset (engine.js l.19-97), example values (assumption)"
SAVED_UTC = "2026-10-08T00:00:00Z"  # fixed, so a rerun rewrites identical files
OUTLINE_SCALE, BORE_SCALE = 1.2, 0.85  # Xcoil outlineScale and innerScale
SCREW_INSET_MM, SCREW_HOLE_MM = 3.5, 3.4  # Xcoil screwOuterInset; M3 normal fit, as tests/unit/model/designs.py


def example_design() -> DesignParameters:
    """Return Xcoil's default serpentine as a design whose outline clears its copper."""
    base = serpentine_design()
    base = dataclasses.replace(base, connection=dataclasses.replace(base.connection, neutral_pad=True))
    stack = build_layout(base, load_registry())
    r_min, r_max = stack.boards[0].envelope_mm  # type: ignore[union-attr]
    board_r = OUTLINE_SCALE * r_max
    screws = (
        ScrewPattern(
            size="M3",
            fit=ScrewFit.NORMAL,
            count=8,
            pitch_radius_mm=board_r - SCREW_INSET_MM,
            hole_diameter_mm=SCREW_HOLE_MM,
        ),
    )
    outline = OutlineSpec(
        board=CircleOutline(radius_mm=board_r), bore=CircleOutline(radius_mm=BORE_SCALE * r_min), screws=screws
    )
    drc = dataclasses.replace(base.drc_rules, trace_clearance_mm=0.2, via_clearance_mm=0.2)
    return dataclasses.replace(base, name=TITLE, outline=outline, drc_rules=drc)


def write_example(folder: Path, *, registry_version: str | None = None) -> Path:
    """Write the example file into `folder` and return its path.

    `registry_version` defaults to the packaged registry's (tools/sync_registry.py passes the one it is syncing to).
    """
    design = example_design()
    ref = ExampleRef(example_id=EXAMPLE_ID, example_sha256=design_hash(design))
    provenance = derive_provenance(design, (ref, design), ())
    document = project_document(
        ProjectFile(design=design, origin=ref),
        provenance,
        saved_utc=SAVED_UTC,
        registry_version=load_registry().version if registry_version is None else registry_version,
    )
    document["example"] = {"title": TITLE, "source_note": SOURCE_NOTE}
    path = folder / f"{EXAMPLE_ID}{EXAMPLE_SUFFIX}"
    path.write_text(encode_project(document), encoding="utf-8", newline="\n")
    return path


if __name__ == "__main__":
    print(write_example(examples_dir()))
