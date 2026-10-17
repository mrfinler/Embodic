"""REQ-T-07 and REQ-T-14: the version stamp in the project JSON, the PDF text and README.txt."""

import json
import re
from collections.abc import Callable
from pathlib import Path

import pypdf
import pytest

from embodic.api import ComputeOutcome
from embodic.io.exporters import ExportSummary
from embodic.io.project import ProjectFile, save_project
from embodic.io.readme_writer import write_readme
from embodic.io.report import write_report_pdf

UTC_STAMP = r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ"


def project_json(outcome: ComputeOutcome, folder: Path) -> dict[str, object]:
    """Save the outcome's design as a project file and read the JSON back."""
    path = folder / "motor.embodic.json"
    save_project(path, ProjectFile(design=outcome.design, origin=None))
    return json.loads(path.read_text(encoding="utf-8"))


def readme_lines(outcome: ComputeOutcome, folder: Path) -> list[str]:
    """Write README.txt for an outcome and return its lines."""
    summary = write_readme(outcome, [], folder / "README.txt")
    assert isinstance(summary, ExportSummary)
    return summary.path.read_text(encoding="utf-8").splitlines()


@pytest.mark.req("REQ-T-07")
def test_t07_project_json_holds_the_embodic_version_the_design_hash_and_a_utc_date(
    example_id: str, outcome_of: Callable[[str], ComputeOutcome], tmp_path: Path
) -> None:
    """Catches a saved project without the version of the program that wrote it, its design hash or a UTC date."""
    outcome = outcome_of(example_id)
    document = project_json(outcome, tmp_path)
    assert document["app_version"] == outcome.versions.embodic
    assert document["design_hash"] == outcome.design_hash
    assert re.fullmatch(UTC_STAMP, str(document["saved_utc"]))


@pytest.mark.req("REQ-T-07")
@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="DEF-UM7d-01: the project file holds app_version, saved_utc and design_hash only (interfaces.md l.3067). "
    "REQ-T-07 lists the project JSON among the files that carry the engine version and the registry version.",
)
def test_t07_project_json_holds_the_engine_version_and_the_registry_version(
    outcome_of: Callable[[str], ComputeOutcome], tmp_path: Path
) -> None:
    """Catches a project file that drops the registry version or the engine version of the REQ-T-07 stamp."""
    outcome = outcome_of("spiral_12c10p_d08")
    text = json.dumps(project_json(outcome, tmp_path))
    assert outcome.versions.registry in text
    assert any("engine" in key for key in json.loads(text))


@pytest.mark.req("REQ-T-07")
def test_t07_pdf_text_holds_a_generated_utc_value(
    example_id: str, outcome_of: Callable[[str], ComputeOutcome], tmp_path: Path
) -> None:
    """Catches a PDF report whose text drops the generation date, or writes it in another form than UTC seconds."""
    summary = write_report_pdf(outcome_of(example_id), tmp_path / "report.pdf")
    assert isinstance(summary, ExportSummary)
    text = "\n".join(page.extract_text() for page in pypdf.PdfReader(summary.path).pages)
    assert re.search(rf"^generated_utc {UTC_STAMP}$", text, re.MULTILINE)


@pytest.mark.req("REQ-T-07")
def test_t07_readme_carries_the_versions_of_the_outcome_and_a_generated_utc_line(
    example_id: str, outcome_of: Callable[[str], ComputeOutcome], tmp_path: Path
) -> None:
    """Catches a README that drops one stamp field or prints a version other than the outcome's."""
    outcome = outcome_of(example_id)
    lines = readme_lines(outcome, tmp_path)
    assert f"embodic_version: {outcome.versions.embodic}" in lines
    assert f"engine_version: {outcome.versions.embodic}" in lines
    assert any(re.fullmatch(rf"generated_utc: {UTC_STAMP}", line) for line in lines)


@pytest.mark.req("REQ-T-14")
def test_t14_readme_names_the_embodic_version_of_the_outcome(
    example_id: str, outcome_of: Callable[[str], ComputeOutcome], tmp_path: Path
) -> None:
    """Catches an export set whose README does not say which embodic version produced it."""
    outcome = outcome_of(example_id)
    assert f"embodic_version: {outcome.versions.embodic}" in readme_lines(outcome, tmp_path)
