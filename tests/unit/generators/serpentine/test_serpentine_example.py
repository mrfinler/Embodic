"""UT-IO-08 for the packaged serpentine example: it loads, validates, builds, passes DRC and analyses (REQ-F-25)."""

import tempfile
from pathlib import Path

import pytest

from embodic.api import compute
from embodic.errors import Severity
from embodic.io.examples import examples_dir, list_examples, load_example
from embodic.io.project import ProjectFile, project_provenance
from embodic.model.provenance import ExampleValue
from embodic.model.validate import validate_design
from embodic.model.vocabulary import TopologyKind
from embodic.results.status import Status

from .make_example import EXAMPLE_ID, TITLE, write_example

pytestmark = pytest.mark.req("REQ-F-25", "REQ-F-34")


def test_the_example_is_listed_with_its_display_title() -> None:
    """Catches a missing file, a title other than the builder's ruling g title, or a wrong topology."""
    info = next(i for i in list_examples() if i.example_id == EXAMPLE_ID)
    assert info.title == TITLE
    assert info.topology is TopologyKind.SERPENTINE


def test_the_packaged_file_is_what_the_script_writes() -> None:
    """Catches a hand-edited example: rerunning make_example gives the same bytes."""
    with tempfile.TemporaryDirectory() as folder:
        written = write_example(Path(folder))
        assert written.read_bytes() == (examples_dir() / written.name).read_bytes()


def test_the_example_validates_and_computes_drc_clean() -> None:
    """Catches an example that only loads: no ERROR issue, DRC passes, every field has example provenance."""
    ref, design = load_example(EXAMPLE_ID)
    assert [i for i in validate_design(design) if i.severity is Severity.ERROR] == []
    provenance = project_provenance(ProjectFile(design=design, origin=ref))
    assert all(isinstance(p, ExampleValue) for p in provenance.values())
    outcome = compute(design, provenance)
    assert outcome is not None and outcome.ok
    assert [i for i in outcome.issues if i.severity is Severity.ERROR] == []
    assert outcome.drc is not None and [r.passed for r in outcome.drc] == [True]
    assert outcome.analysis is not None
    ke = outcome.analysis.ke_phase_v_s_per_rad
    assert ke.value > 0.0 and ke.status is not Status.UNRESOLVED
    assert outcome.analysis.loss_interconnect_w.value > 0.0, "star interconnect copper must be classified"
