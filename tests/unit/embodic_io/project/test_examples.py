"""UT-IO-08: every packaged example loads, validates and computes with no ERROR issue; titles say "Example"."""

from pathlib import Path

import pytest

from embodic.api import compute
from embodic.errors import Severity
from embodic.io.examples import examples_dir, list_examples, load_example
from embodic.io.project import ProjectFile, project_provenance
from embodic.model.provenance import ExampleValue
from embodic.model.validate import validate_design
from embodic.model.vocabulary import TopologyKind

from .make_examples import write_examples

SPIRAL_EXAMPLES = {"spiral_12c16p_default", "spiral_12c10p_d08", "spiral_12c14p"}


@pytest.mark.req("REQ-F-25", "REQ-F-38")
def test_ut_io_08_spiral_examples_are_packaged_with_example_titles() -> None:
    """Catches a missing example file or a title without the word "Example" (D-014)."""
    infos = {info.example_id: info for info in list_examples()}
    assert SPIRAL_EXAMPLES <= infos.keys()
    for info in infos.values():
        assert "Example" in info.title
    assert {infos[i].topology for i in SPIRAL_EXAMPLES} == {TopologyKind.SPIRAL}


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


@pytest.mark.req("REQ-F-25")
def test_ut_io_08_packaged_files_equal_the_generator_output(tmp_path: Path) -> None:
    """Catches a hand edit of a packaged example that the generator script would undo."""
    for written in write_examples(tmp_path):
        assert written.read_bytes() == (examples_dir() / written.name).read_bytes(), written.name
