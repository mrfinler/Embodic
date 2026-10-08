"""UT-EXP-03 (PDF report), UT-EXP-04 (README), UT-EXP-05 (bundle and DRC refusal) and UT-IO-06 for PDF and README."""

import dataclasses
import re
import zipfile
from collections.abc import Callable
from pathlib import Path

import pypdf
import pytest

from embodic.api import ComputeOutcome
from embodic.io.bundle import write_bundle
from embodic.io.dxf_writer import write_dxf
from embodic.io.exporters import ExportKind, ExportRefused, ExportSummary
from embodic.io.pdf_writer import winansi
from embodic.io.readme_writer import write_readme
from embodic.io.report import write_report_pdf
from embodic.io.svg_writer import write_svg
from embodic.results import QUANTITY_LABELS, AnalysisResult
from embodic.results.status import Status
from embodic.results.traceable import Traceable
from embodic.units import Unit

from .conftest import WAVE

pytestmark = pytest.mark.req("REQ-F-16", "REQ-F-33", "REQ-T-07", "REQ-T-14")

STATUS = "|".join(re.escape(s.value) for s in Status)
UNITS = {winansi(u.display()).decode("cp1252") for u in Unit if u.display()} | {"(dimensionless)"}
DRAWINGS = (ExportKind.SVG, ExportKind.DXF_COMPLETE, ExportKind.DXF_OUTLINE, ExportKind.PDF_REPORT)


def _pdf_text(path: Path) -> tuple[pypdf.PdfReader, str]:
    reader = pypdf.PdfReader(path)
    return reader, "\n".join(page.extract_text() for page in reader.pages)


def test_ut_exp_03_report_every_value_has_unit_and_status(
    example_id: str, outcome_of: Callable[[str], ComputeOutcome], tmp_path: Path
) -> None:
    """UT-EXP-03. Catches a result row without unit or status word, a dropped result, and an unreadable PDF."""
    outcome = outcome_of(example_id)
    summary = write_report_pdf(outcome, tmp_path / "report.pdf")
    assert isinstance(summary, ExportSummary), summary
    reader, text = _pdf_text(summary.path)
    assert len(reader.pages) == summary.pages >= 2
    section = text.split("Key results", 1)[1].split("DRC summary", 1)[0].strip().splitlines()[1:]
    scalar = [f for f in dataclasses.fields(AnalysisResult) if f.type == Traceable[float]]
    assert len(section) == len(scalar)
    for row in section:
        assert re.search(rf"({STATUS})( \(.+\))?$", row), row
        unit_part = re.sub(rf" ({STATUS})( \(.+\))?$", "", row)
        assert any(unit_part.endswith(" " + u) or re.search(rf"\d\s?\S*{re.escape(u)}$", unit_part) for u in UNITS), row


def test_report_key_results_are_named_with_display_labels_not_ids(
    example_id: str, outcome_of: Callable[[str], ComputeOutcome], tmp_path: Path
) -> None:
    """Catches a Key results row titled with the raw field id ("ke phase v s per rad") or with another row's label."""
    summary = write_report_pdf(outcome_of(example_id), tmp_path / "report.pdf")
    assert isinstance(summary, ExportSummary), summary
    _, text = _pdf_text(summary.path)
    section = text.split("Key results", 1)[1].split("DRC summary", 1)[0].strip().splitlines()[1:]
    scalar = [f.name for f in dataclasses.fields(AnalysisResult) if f.type == Traceable[float]]
    for row, name in zip(section, scalar, strict=True):
        assert row.startswith(winansi(QUANTITY_LABELS[name]).decode("cp1252") + " "), (name, row)


def test_ut_io_06_report_carries_the_stamp(outcome_of: Callable[[str], ComputeOutcome], tmp_path: Path) -> None:
    """UT-IO-06. Catches a PDF without the REQ-T-07 fields in its text and information dictionary."""
    outcome = outcome_of(WAVE)
    summary = write_report_pdf(outcome, tmp_path / "report.pdf")
    assert isinstance(summary, ExportSummary)
    reader, text = _pdf_text(summary.path)
    for value in (outcome.versions.embodic, outcome.versions.registry, outcome.design_hash, "drc_passed false"):
        assert value in text
    assert reader.metadata is not None and reader.metadata["/DesignHash"] == outcome.design_hash
    assert "FAILED, 186 violations" in text


def test_ut_exp_04_readme_names_every_file_units_frame_and_caveat(
    example_id: str, outcome_of: Callable[[str], ComputeOutcome], tmp_path: Path
) -> None:
    """UT-EXP-04 and UT-IO-06. Catches a file missing from the README, a missing unit, frame, caveat or stamp."""
    outcome = outcome_of(example_id)
    files = [write_svg(outcome, tmp_path / "a.svg", allow_drc_errors=True)]
    files.append(write_dxf(outcome, tmp_path / "a.dxf", "complete", allow_drc_errors=True))
    files.append(write_report_pdf(outcome, tmp_path / "a_report.pdf"))
    summaries = [f for f in files if isinstance(f, ExportSummary)]
    readme = write_readme(outcome, summaries, tmp_path / "README.txt")
    text = readme.path.read_text(encoding="utf-8")
    for name in ("a.svg", "a.dxf", "a_report.pdf", "README.txt"):
        assert f"  {name}: " in text
    assert "millimetres (mm)" in text
    assert "y up and centred on the shaft axis" in text
    assert "first-order estimates" in text
    assert f"design_hash: {outcome.design_hash}" in text
    assert f"registry_version: {outcome.versions.registry}" in text


def test_ut_exp_05_bundle_holds_selected_files_and_readme(
    example_id: str, outcome_of: Callable[[str], ComputeOutcome], tmp_path: Path
) -> None:
    """UT-EXP-05. Catches a selected file missing from the ZIP, an unselected one added, or no README.txt."""
    outcome = outcome_of(example_id)
    kinds = [*DRAWINGS, ExportKind.PROJECT_JSON]
    result = write_bundle(outcome, kinds, tmp_path / "motor.zip", allow_drc_errors=True)
    assert not isinstance(result, ExportRefused), result
    names = sorted(zipfile.ZipFile(tmp_path / "motor.zip").namelist())
    expected = ["README.txt", "motor.dxf", "motor.embodic.json", "motor.svg", "motor_outline.dxf", "motor_report.pdf"]
    assert names == expected
    assert sorted(str(s.path) for s in result) == expected


def test_ut_exp_05_bundle_refuses_screws_on_a_board_without_holes(
    outcome_of: Callable[[str], ComputeOutcome], tmp_path: Path
) -> None:
    """UT-EXP-05. Catches a screws drawing written (or a ZIP left behind) for a board with no screw holes."""
    result = write_bundle(outcome_of("spiral_12c16p_default"), [ExportKind.DXF_SCREWS], tmp_path / "m.zip")
    assert isinstance(result, ExportRefused) and result.reason == "no_screws"
    assert not (tmp_path / "m.zip").exists()


@pytest.mark.parametrize(
    "write",
    [
        pytest.param(lambda o, d, ok: write_svg(o, d / "w.svg", allow_drc_errors=ok), id="svg"),
        pytest.param(lambda o, d, ok: write_dxf(o, d / "w.dxf", "complete", allow_drc_errors=ok), id="dxf_complete"),
        pytest.param(lambda o, d, ok: write_dxf(o, d / "w_o.dxf", "outline", allow_drc_errors=ok), id="dxf_outline"),
        pytest.param(lambda o, d, ok: write_dxf(o, d / "w_s.dxf", "screws", allow_drc_errors=ok), id="dxf_screws"),
        pytest.param(lambda o, d, ok: write_bundle(o, list(DRAWINGS), d / "w.zip", allow_drc_errors=ok), id="bundle"),
    ],
)
def test_ut_exp_05_failed_drc_refuses_without_confirmation(
    write: Callable[[ComputeOutcome, Path, bool], object], outcome_of: Callable[[str], ComputeOutcome], tmp_path: Path
) -> None:
    """UT-EXP-05. Catches a writer that exports the failing wave example unasked, or refuses it once confirmed."""
    outcome = outcome_of(WAVE)
    refused = write(outcome, tmp_path, False)
    assert isinstance(refused, ExportRefused) and refused.reason == "drc_errors_not_confirmed"
    assert refused.issues[0].code == "DRC_EXPORT_NOT_CONFIRMED" and refused.issues[0].value == 186
    assert {i.code for i in refused.issues[1:]} == {"DRC_TRACE_TRACE", "DRC_TRACE_VIA"}
    assert list(tmp_path.iterdir()) == []
    written = write(outcome, tmp_path, True)
    assert not isinstance(written, ExportRefused)
    for path in tmp_path.glob("*.dxf"):
        assert "drc_passed=false" in path.read_text(encoding="ascii").splitlines()
    for path in tmp_path.glob("*.svg"):
        assert 'drc_passed="false"' in path.read_text(encoding="utf-8")
