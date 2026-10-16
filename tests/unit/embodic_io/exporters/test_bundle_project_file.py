"""F16-1 (V3-01 union ruling): the project file inside the export bundle is the current design, in schema form."""

import json
import zipfile
from collections.abc import Callable
from pathlib import Path

import jsonschema
import pytest

import embodic.io
from embodic.api import ComputeOutcome
from embodic.io.bundle import write_bundle
from embodic.io.canonical import design_hash
from embodic.io.exporters import ExportKind, ExportRefused
from embodic.io.project import ProjectFile, load_project

SCHEMA_PATH = Path(embodic.io.__file__).parent / "schema" / "project.v1.schema.json"
KINDS = [
    ExportKind.SVG,
    ExportKind.DXF_COMPLETE,
    ExportKind.DXF_OUTLINE,
    ExportKind.PDF_REPORT,
    ExportKind.PROJECT_JSON,
]


@pytest.mark.req("REQ-F-16")
def test_f16_1_the_bundle_project_file_validates_and_loads_back_to_the_computed_design(
    example_id: str, outcome_of: Callable[[str], ComputeOutcome], tmp_path: Path
) -> None:
    """Catches an export that writes a stale or partial project file: schema-valid, same design hash as the outcome."""
    outcome = outcome_of(example_id)
    result = write_bundle(outcome, KINDS, tmp_path / "motor.zip", allow_drc_errors=True)
    assert not isinstance(result, ExportRefused), result
    with zipfile.ZipFile(tmp_path / "motor.zip") as bundle:
        bundle.extract("motor.embodic.json", tmp_path)
    saved = tmp_path / "motor.embodic.json"

    jsonschema.validate(json.loads(saved.read_text(encoding="utf-8")), json.loads(SCHEMA_PATH.read_text("utf-8")))
    project, issues = load_project(saved)
    assert issues == ()
    assert isinstance(project, ProjectFile)
    assert design_hash(project.design) == outcome.design_hash
