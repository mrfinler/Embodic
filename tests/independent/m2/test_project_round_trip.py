"""Item 6: project file round trip and schema, through save_project / load_project / compute_project.

Defects caught: a field lost or rounded on save, a measurement or origin dropped, a stored hash that disagrees with
the design compute() sees, a saved file that its own published schema rejects, a second save that is not stable.
"""

import json
from pathlib import Path

import jsonschema
import pytest

import embodic
from embodic.api import compute, compute_project
from embodic.io.examples import list_examples, load_example
from embodic.io.project import ProjectFile, load_project, project_from_example, save_project
from embodic.model.provenance import Measurement

pytestmark = pytest.mark.req("REQ-F-15")

SCHEMA = Path(embodic.__file__).parent / "io" / "schema" / "project.v1.schema.json"
EXAMPLES = [e.example_id for e in list_examples()]


@pytest.mark.parametrize("example_id", EXAMPLES)
def test_saved_project_reloads_to_the_same_design_origin_and_measurements(tmp_path: Path, example_id: str) -> None:
    """Save then load keeps design, origin and measurements; the stored hash is compute()'s hash."""
    base = project_from_example(load_example(example_id))
    project = ProjectFile(
        design=base.design,
        origin=base.origin,
        measurements=(Measurement(pointer="/rotor/remanence_t", source="example datasheet (label: example)"),),
        ui_state={"tab": "results"},
    )
    path = tmp_path / "p.embodic.json"
    stored_hash = save_project(path, project)
    loaded, issues = load_project(path)
    assert issues == ()
    assert isinstance(loaded, ProjectFile)
    assert (loaded.design, loaded.origin, loaded.measurements) == (project.design, project.origin, project.measurements)
    outcome = compute_project(path)
    assert not isinstance(outcome, tuple)
    assert stored_hash == outcome.design_hash == compute(project.design, {}).design_hash
    assert outcome.provenance["/rotor/remanence_t"].provenance.value == "measured"


@pytest.mark.parametrize("example_id", EXAMPLES)
def test_saved_file_validates_against_the_published_schema_and_resaves_identically(
    tmp_path: Path, example_id: str
) -> None:
    """A saved file passes its schema and a re-save differs only in saved_utc."""
    first, second = tmp_path / "a.json", tmp_path / "b.json"
    save_project(first, project_from_example(load_example(example_id)))
    reloaded, _ = load_project(first)
    save_project(second, reloaded)
    doc_a, doc_b = (json.loads(p.read_text(encoding="utf-8")) for p in (first, second))
    jsonschema.validate(doc_a, json.loads(SCHEMA.read_text(encoding="utf-8")))
    doc_a.pop("saved_utc"), doc_b.pop("saved_utc")
    assert doc_a == doc_b


def test_a_value_changed_in_the_file_becomes_user_provenance(tmp_path: Path) -> None:
    """A value edited in the file is `user`, an untouched one stays `example`."""
    path = tmp_path / "p.json"
    save_project(path, project_from_example(load_example("spiral_12c16p_default")))
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["design"]["rotor"]["air_gap_mm"] = doc["design"]["rotor"]["air_gap_mm"] + 0.25
    path.write_text(json.dumps(doc), encoding="utf-8")
    loaded, _ = load_project(path)
    assert isinstance(loaded, ProjectFile)
    outcome = compute_project(path)
    assert not isinstance(outcome, tuple)
    assert outcome.provenance["/rotor/air_gap_mm"].provenance.value == "user"
    assert outcome.provenance["/rotor/poles"].provenance.value == "example"
