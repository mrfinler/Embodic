"""Write the packaged spiral examples to resources/examples; rerunning gives the same bytes.

Run from the repository root: ``python -m tests.unit.embodic_io.project.make_examples``. The parameter sets come from
CF-11 (tests/unit/generators/default_example.py) and O1-D08 (tests/unit/generators/d08_example.py); every value is an
example value (D-014), status `assumption` unless the source note says otherwise.

Values the builders derive by float arithmetic are rounded to 1e-9 in file units (D-038f), so the number a field shows
is the number the file holds: D08's G - t/2 = 1.4 - 0.3 is 1.0999999999999999 in binary and shows as 1.1 (DEF-1). The
stack-up is kept as `generate_even_stackup` writes it, because that is what the UI's stack-up generator writes again
when the user re-enters the copper count, copper weight and board thickness the inspector shows.
"""

import dataclasses
from collections.abc import Callable
from pathlib import Path

from tests.unit.generators.d08_example import d08_design
from tests.unit.generators.default_example import default_design

from embodic.io.canonical import design_document, design_hash, draft_from_document
from embodic.io.examples import EXAMPLE_SUFFIX, examples_dir
from embodic.io.project import ProjectFile, encode_project, project_document
from embodic.model.design import DesignParameters
from embodic.model.draft import parse_draft
from embodic.model.outline import PolygonOutline
from embodic.model.provenance import ExampleRef, derive_provenance
from embodic.model.schema import JsonValue, flatten, unflatten

SAVED_UTC = "2026-10-08T00:00:00Z"  # fixed, so a rerun rewrites identical files
ROUND_DECIMALS = 9
STACKUP_PREFIX = "/stackup/"
BOARD_12C14P_ACROSS_FLATS_MM = 104.0  # the 93 mm CF-11 board cuts the 12/14 interconnect ring (copper to r 49.8 mm)


def _spiral_12c14p() -> DesignParameters:
    base = default_design()
    assert isinstance(base.outline.board, PolygonOutline)
    board = dataclasses.replace(base.outline.board, across_flats_mm=BOARD_12C14P_ACROSS_FLATS_MM)
    return dataclasses.replace(
        base,
        rotor=dataclasses.replace(base.rotor, poles=14),
        outline=dataclasses.replace(base.outline, board=board),
    )


def _round(pointer: str, value: JsonValue) -> JsonValue:
    if not isinstance(value, float) or pointer.startswith(STACKUP_PREFIX):
        return value
    rounded = round(value, ROUND_DECIMALS)
    if abs(rounded - value) > 1e-9 * abs(value):
        raise ValueError(f"rounding {pointer} = {value!r} to 1e-9 changes more than float noise")
    return rounded


def rounded_design(design: DesignParameters) -> DesignParameters:
    """Return the design with every float outside the stack-up rounded to 1e-9 in file units (mm, degrees)."""
    values = flatten(design_document(design))
    draft = draft_from_document(unflatten({pointer: _round(pointer, value) for pointer, value in values.items()}))
    assert draft is not None
    parsed = parse_draft(draft)
    assert isinstance(parsed, DesignParameters), parsed
    return parsed


# Display titles of U-S4e ruling g (m4_review_2.md); D-041b makes each the design `/name` too.
EXAMPLES: dict[str, tuple[str, str, Callable[[], DesignParameters]]] = {
    "spiral_12c16p_default": (
        "Spiral, 12 coils, 16 poles",
        "CF-11 default 12/16 spiral, example values (assumption), docs/phase2/engineering/oracle_cases.json CF-11",
        default_design,
    ),
    "spiral_12c10p_d08": (
        "Spiral, 12 coils, 10 poles (D08)",
        "D08 thesis configuration (oracle O1-D08, OR-01); the 66 mm circle board and 10 mm bore are an assumption",
        d08_design,
    ),
    "spiral_12c14p": (
        "Spiral, 12 coils, 14 poles",
        "CF-11 copper with 14 poles on a 104 mm board, example values (assumption)",
        _spiral_12c14p,
    ),
}


def write_examples(folder: Path) -> list[Path]:
    """Write every example file into `folder` and return the paths."""
    written = []
    for example_id, (title, source_note, build) in EXAMPLES.items():
        design = rounded_design(dataclasses.replace(build(), name=title))
        ref = ExampleRef(example_id=example_id, example_sha256=design_hash(design))
        provenance = derive_provenance(design, (ref, design), ())
        document = project_document(ProjectFile(design=design, origin=ref), provenance, saved_utc=SAVED_UTC)
        document["example"] = {"title": title, "source_note": source_note}
        path = folder / f"{example_id}{EXAMPLE_SUFFIX}"
        path.write_text(encode_project(document), encoding="utf-8", newline="\n")
        written.append(path)
    return written


if __name__ == "__main__":
    for path in write_examples(examples_dir()):
        print(path)
