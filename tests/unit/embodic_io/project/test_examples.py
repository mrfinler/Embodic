"""UT-IO-08: every packaged example loads, validates and computes with no ERROR issue; titles say "Example"."""

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
# The serpentine title is written by tests/unit/generators/serpentine/make_example.py (U-S4e ruling g, open).
SERPENTINE_TITLE_NAMES_XCOIL = pytest.mark.xfail(strict=True, reason="the serpentine example title names Xcoil")


@pytest.mark.req("REQ-F-25", "REQ-F-38")
def test_ut_io_08_spiral_examples_are_packaged_with_example_titles() -> None:
    """Catches a missing example file or a title without the word "Example" (D-014)."""
    infos = {info.example_id: info for info in list_examples()}
    assert SPIRAL_EXAMPLES <= infos.keys()
    for info in infos.values():
        assert "Example" in info.title
    assert {infos[i].topology for i in SPIRAL_EXAMPLES} == {TopologyKind.SPIRAL}


@pytest.mark.req("REQ-F-25", "REQ-F-38")
@pytest.mark.parametrize(
    "example_id",
    [
        pytest.param(i, marks=SERPENTINE_TITLE_NAMES_XCOIL) if i.startswith("serpentine") else i
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
