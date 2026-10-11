"""UT-IO-08: every packaged example loads, validates and computes with no ERROR issue; titles follow ruling g."""

import json
import re
from pathlib import Path

import pytest

from embodic.api import compute
from embodic.errors import Severity
from embodic.io.examples import examples_dir, list_examples, load_example
from embodic.io.project import ProjectFile, project_provenance, save_project
from embodic.model.provenance import ExampleValue
from embodic.model.validate import validate_design
from embodic.model.vocabulary import TopologyKind
from embodic.results.status import Status
from embodic.units import Unit

from .make_examples import write_examples

SPIRAL_EXAMPLES = {"spiral_12c16p_default", "spiral_12c10p_d08", "spiral_12c14p"}


OTHER_PROGRAM_OR_PATH = re.compile(r"xcoil|kicad|engine\.js|docs/|resources/|\.json|[A-Za-z]:\\|/home/|/Users/", re.I)
# U-S4e ruling g (m4_review_2.md): the display titles, as the gallery shows them.
RULING_G_TITLES = {
    "spiral_12c16p_default": "Spiral, 12 coils, 16 poles",
    "spiral_12c14p": "Spiral, 12 coils, 14 poles",
    "spiral_12c10p_d08": "Spiral, 12 coils, 10 poles (D08)",
    "serpentine_16p_example": "Serpentine, 16 poles",
    "wave_16p_example": "Wave, 16 poles, involute",
}
# D-041b: `/name` equals the display title, and `/name` is hashed with the design, so these moved with the rename.
EXAMPLE_HASHES = {
    "spiral_12c16p_default": "sha256:ac4fab5db06f9e8f733dc495080deeddfe0bcf58faa31ebb7ec841c1b27d9c09",
    "spiral_12c14p": "sha256:4a1997029f7063676bdb9eab703c462f4240d84916a5ddf3deec044fa4391bc1",
    "spiral_12c10p_d08": "sha256:327919a0eef55ce2c458635f6160047af7654ebd0a04e818ee225fd5f69615d8",
    "serpentine_16p_example": "sha256:8ec4c23449a0be2bf4ee6ba337b72b2e93e5906e6b53ba8ba7c441d4872dd1ca",
    "wave_16p_example": "sha256:3131a61975766c38984df5065b01f255875b79ebcfa831624c10c5db5d5c82e8",
}


@pytest.mark.req("REQ-F-25", "REQ-F-38")
def test_ut_io_08_examples_are_packaged_with_the_ruling_g_display_titles() -> None:
    """Catches a missing example file, or a title that says "Example", "default" or names another program (UX-AC-03)."""
    infos = {info.example_id: info for info in list_examples()}
    assert {example_id: info.title for example_id, info in infos.items()} == RULING_G_TITLES
    assert {infos[i].topology for i in SPIRAL_EXAMPLES} == {TopologyKind.SPIRAL}


@pytest.mark.req("REQ-F-25", "REQ-F-38")
def test_d_041b_each_example_design_is_named_by_its_display_title() -> None:
    """Catches a design name that still says "Example" or "Xcoil", which the window title and export stem show."""
    assert {i: load_example(i)[1].name for i in RULING_G_TITLES} == RULING_G_TITLES


@pytest.mark.req("REQ-F-25")
def test_ut_io_08_the_packaged_design_hashes_are_pinned() -> None:
    """Catches a builder change that moves an example design, which re-keys every saved reference to it."""
    assert {i: load_example(i)[0].example_sha256 for i in RULING_G_TITLES} == EXAMPLE_HASHES


@pytest.mark.req("REQ-F-25", "REQ-F-38")
@pytest.mark.parametrize(
    "example_id",
    sorted(p.name.split(".")[0] for p in examples_dir().glob("*.embodic.json")),
)
def test_ux_ac_03_an_exported_example_names_no_other_program_and_no_repository_path(
    example_id: str, tmp_path: Path
) -> None:
    """UX-AC-03. Catches "Xcoil", "engine.js" or a repository path in what a user sees or saves of an example."""
    info = next(info for info in list_examples() if info.example_id == example_id)
    ref, design = load_example(example_id)
    save_project(tmp_path / "saved.embodic.json", ProjectFile(design=design, origin=ref))
    saved = json.loads((tmp_path / "saved.embodic.json").read_text(encoding="utf-8"))
    shown = [info.title, info.display_note, saved["design"]["name"]]
    assert [text for text in shown if OTHER_PROGRAM_OR_PATH.search(text)] == []
    assert "example" not in saved, "the provenance note stays in the packaged file only"


@pytest.mark.req("REQ-F-25", "REQ-F-38")
@pytest.mark.parametrize("example_id", sorted(SPIRAL_EXAMPLES))
def test_ut_io_08_example_validates_and_computes_drc_clean(example_id: str) -> None:
    """Catches an example that only loads: it must validate, build, pass DRC on its own board and analyse."""
    ref, design = load_example(example_id)
    assert [i for i in validate_design(design) if i.severity is Severity.ERROR] == []
    provenance = project_provenance(ProjectFile(design=design, origin=ref))
    assert all(isinstance(p, ExampleValue) for p in provenance.values())
    outcome = compute(design, provenance)
    assert outcome is not None
    assert [i.code for i in outcome.issues if i.severity is Severity.ERROR] == []
    assert outcome.drc is not None
    assert [r.passed for r in outcome.drc] == [True]
    assert outcome.analysis is not None
    assert outcome.ok


@pytest.mark.req("REQ-F-11")
@pytest.mark.parametrize("example_id", sorted(SPIRAL_EXAMPLES))
def test_example_results_carry_interconnect_loss_and_motor_constant(example_id: str) -> None:
    """Catches P_ic left unresolved for an unclassified interconnect (U-M2-fix4) or a missing K_m with its unit."""
    ref, design = load_example(example_id)
    outcome = compute(design, project_provenance(ProjectFile(design=design, origin=ref)))
    assert outcome is not None and outcome.analysis is not None
    p_ic, k_m = outcome.analysis.loss_interconnect_w, outcome.analysis.motor_constant_n_m_per_sqrt_w
    assert p_ic.status is not Status.UNRESOLVED and p_ic.value > 0.0
    assert "INTERNAL_INTERCONNECT_UNCLASSIFIED" not in {flag.code for flag in p_ic.validity}
    assert k_m.value > 0.0 and k_m.unit is Unit.N_M_PER_SQRT_W


@pytest.mark.req("REQ-F-25")
def test_ut_io_08_packaged_files_equal_the_generator_output(tmp_path: Path) -> None:
    """Catches a hand edit of a packaged example that the generator script would undo."""
    for written in write_examples(tmp_path):
        assert written.read_bytes() == (examples_dir() / written.name).read_bytes(), written.name
