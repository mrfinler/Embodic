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
# Pinned 2026-10-09 from the files before the ruling g retitle: a display title must not move a design hash.
HASHES_BEFORE_RETITLE = {
    "spiral_12c16p_default": "sha256:42b702746410833c6c52e3083613705fab52bce6c7865c216d61e7b8ba1dea58",
    "spiral_12c14p": "sha256:546ef0545182cfadb46815ec535a51e4827eeb2126ea7b70c96b58f3538e0c90",
    "spiral_12c10p_d08": "sha256:709ea86cd9d17998d231ae2beef79d813063afb6b2ff183ea9fa9050dd989761",
    "serpentine_16p_example": "sha256:3fa7f90783e1d3e9a1ec1b4d886f8fddf3a48404a32a669faf913d55527e469f",
    "wave_16p_example": "sha256:294f2a10cad44a4e13824d097697547f8c162e6f279a9d7cb2f09c45f3d2c66c",
}
# `/name` is hashed with the design, and the serpentine design name still holds the old title (open decision).
SERPENTINE_DESIGN_NAME_NAMES_XCOIL = pytest.mark.xfail(
    strict=True, reason="the serpentine design name (hashed with the design) still names Xcoil"
)


@pytest.mark.req("REQ-F-25", "REQ-F-38")
def test_ut_io_08_examples_are_packaged_with_the_ruling_g_display_titles() -> None:
    """Catches a missing example file, or a title that says "Example", "default" or names another program (UX-AC-03)."""
    infos = {info.example_id: info for info in list_examples()}
    assert {example_id: info.title for example_id, info in infos.items()} == RULING_G_TITLES
    assert {infos[i].topology for i in SPIRAL_EXAMPLES} == {TopologyKind.SPIRAL}


@pytest.mark.req("REQ-F-25")
def test_ut_io_08_a_display_title_does_not_move_the_design_hash() -> None:
    """Catches a title copied into the design (`/name` is hashed), which re-keys saved references to the example."""
    assert {i: load_example(i)[0].example_sha256 for i in RULING_G_TITLES} == HASHES_BEFORE_RETITLE


@pytest.mark.req("REQ-F-25", "REQ-F-38")
@pytest.mark.parametrize(
    "example_id",
    [
        pytest.param(i, marks=SERPENTINE_DESIGN_NAME_NAMES_XCOIL) if i.startswith("serpentine") else i
        for i in sorted(p.name.split(".")[0] for p in examples_dir().glob("*.embodic.json"))
    ],
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
