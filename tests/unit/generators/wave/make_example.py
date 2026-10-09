"""Write the packaged wave example to resources/examples; rerunning gives the same bytes.

Run from the repository root: ``python -m tests.unit.generators.wave.make_example``. The parameters are Xcoil v3's
default wave preset with ``turns: 2`` (D-016; engine.js l.19-97, tests.js l.562). Every value is an example value
(D-014). The board outline and the screws follow Xcoil's outline rules at the copper envelope of this layout
(outline scale 1.2, bore scale 0.85, screw inset 3.5 mm), rounded; they are an assumption.
"""

import dataclasses
from pathlib import Path

from tests.unit.model.designs import wave_design

from embodic.io.canonical import design_hash
from embodic.io.examples import EXAMPLE_SUFFIX, examples_dir
from embodic.io.project import ProjectFile, encode_project, project_document
from embodic.model.design import DesignParameters
from embodic.model.outline import CircleOutline, ScrewPattern
from embodic.model.provenance import ExampleRef, derive_provenance

SAVED_UTC = "2026-10-08T00:00:00Z"  # fixed, so a rerun rewrites identical files
EXAMPLE_ID = "wave_16p_example"
TITLE = "Wave, 16 poles, involute"  # U-S4e ruling g
# `/name` is hashed with the design, so it keeps its old text; see DESIGN_NAMES in make_examples.py.
DESIGN_NAME = "Example: 16-pole wave winding (involute, 2 turns)"
SOURCE_NOTE = (
    "Xcoil v3 default wave preset with turns 2 (D-016), example values (assumption); "
    "board, bore and screw circle follow Xcoil's outline rules at this copper envelope"
)
BOARD_RADIUS_MM = 55.5  # Xcoil outlineScale 1.2 at the 46.275 mm envelope: 55.53 mm
BORE_RADIUS_MM = 15.3  # innerScale 0.85 at the 18.049 mm inner copper radius: 15.34 mm
SCREW_PITCH_RADIUS_MM = 52.0  # board radius less the 3.5 mm inset: 52.03 mm


def wave_example() -> DesignParameters:
    """Xcoil's wave defaults at 2 turns on 2 copper layers, with DRC clearances equal to the trace clearance."""
    base = wave_design()
    screws = tuple(dataclasses.replace(s, pitch_radius_mm=SCREW_PITCH_RADIUS_MM) for s in base.outline.screws)
    assert all(isinstance(s, ScrewPattern) for s in screws)
    return dataclasses.replace(
        base,
        name=DESIGN_NAME,
        winding=dataclasses.replace(base.winding, turns=2),
        outline=dataclasses.replace(
            base.outline, board=CircleOutline(radius_mm=BOARD_RADIUS_MM), bore=CircleOutline(radius_mm=BORE_RADIUS_MM),
            screws=screws,
        ),
        drc_rules=dataclasses.replace(base.drc_rules, trace_clearance_mm=0.2, via_clearance_mm=0.2),
    )  # fmt: skip


def write_example(folder: Path) -> Path:
    """Write the example file into ``folder`` and return its path."""
    design = wave_example()
    ref = ExampleRef(example_id=EXAMPLE_ID, example_sha256=design_hash(design))
    provenance = derive_provenance(design, (ref, design), ())
    document = project_document(ProjectFile(design=design, origin=ref), provenance, saved_utc=SAVED_UTC)
    document["example"] = {"title": TITLE, "source_note": SOURCE_NOTE}
    path = folder / f"{EXAMPLE_ID}{EXAMPLE_SUFFIX}"
    path.write_text(encode_project(document), encoding="utf-8", newline="\n")
    return path


if __name__ == "__main__":
    print(write_example(examples_dir()))
