"""Packaged examples: one self-describing project file per example in resources/examples, found by a folder scan.

An example file is a project file with an `example` object (`title`, `source_note`); its file stem minus
`.embodic.json` is the example id. No index file lists them (work_breakdown.md section 4).
"""

import functools
import json
from dataclasses import dataclass
from pathlib import Path

from embodic.io.canonical import design_hash, draft_from_document
from embodic.model.design import DesignParameters
from embodic.model.draft import parse_draft
from embodic.model.provenance import ExampleRef
from embodic.model.vocabulary import TopologyKind
from embodic.paths import resource_root

EXAMPLE_SUFFIX = ".embodic.json"
# The note the UI shows per example; the source note in the file keeps the provenance (m4_review.md ruling g 4).
DISPLAY_NOTES = {
    "serpentine_16p_example": "Serpentine settings of the reference generator. Example values (assumption).",
    "spiral_12c10p_d08": "D08 thesis configuration. The 66 mm circle board and 10 mm bore are an assumption.",
    "spiral_12c14p": "CF-11 copper with 14 poles on a 104 mm board. Example values (assumption).",
    "spiral_12c16p_default": "CF-11 copper with 12 coils and 16 poles. Example values (assumption).",
    "wave_16p_example": (
        "Involute wave settings of the reference generator. Example values (assumption); board, bore and screw "
        "circle follow the reference outline rules at this copper envelope."
    ),
}


@dataclass(frozen=True, slots=True, kw_only=True)
class ExampleInfo:
    """What the Examples gallery shows for one example."""

    example_id: str
    title: str  # English display title shown in the Examples gallery (ruling g: no "Example", no other program)
    topology: TopologyKind
    source_note: str  # provenance kept in the file, e.g. "D08 thesis configuration (oracle O1)"; never shown
    display_note: str  # what the gallery shows: no other program's name and no repository path (UX-AC-03)


def examples_dir() -> Path:
    """Return the folder of the packaged example files."""
    return resource_root() / "examples"


def _example_files() -> dict[str, Path]:
    return {path.name[: -len(EXAMPLE_SUFFIX)]: path for path in sorted(examples_dir().glob(f"*{EXAMPLE_SUFFIX}"))}


def _parse(path: Path) -> tuple[dict[str, object], DesignParameters]:
    """Read a packaged example; a file that is not a complete design is a packaging error (ValueError)."""
    document = json.loads(path.read_text(encoding="utf-8"))
    draft = draft_from_document(document["design"])
    if draft is None:
        raise ValueError(f"packaged example {path.name} names no known topology")
    design = parse_draft(draft)
    if not isinstance(design, DesignParameters):
        raise ValueError(f"packaged example {path.name} is incomplete: {design.missing} {design.issues}")
    return document["example"], design


def list_examples() -> tuple[ExampleInfo, ...]:
    """Every packaged example, sorted by id."""
    infos = []
    for example_id, path in _example_files().items():
        meta, design = _parse(path)
        infos.append(
            ExampleInfo(
                example_id=example_id,
                title=str(meta["title"]),
                topology=design.topology,
                source_note=str(meta["source_note"]),
                display_note=DISPLAY_NOTES[example_id],
            )
        )
    return tuple(infos)


@functools.cache
def _load(path: Path) -> tuple[ExampleRef, DesignParameters]:
    """Parse one packaged file once per process: the files ship with the program and do not change while it runs.

    The result is shared by every caller. ExampleRef and DesignParameters are frozen all the way down, so no caller can
    change what a later lookup returns.
    """
    _, design = _parse(path)
    return ExampleRef(example_id=path.name.removesuffix(EXAMPLE_SUFFIX), example_sha256=design_hash(design)), design


def load_example(example_id: str) -> tuple[ExampleRef, DesignParameters]:
    """Return the reference and design of a packaged example; KeyError for an unknown id."""
    return _load(_example_files()[example_id])


def packaged_example(ref: ExampleRef) -> DesignParameters | None:
    """Return the packaged design a reference names, or None when that id with that hash is not packaged."""
    if ref.example_id not in _example_files():
        return None
    packaged_ref, design = load_example(ref.example_id)
    return design if packaged_ref == ref else None
