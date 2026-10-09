"""One English display label per AnalysisResult field (D-038e); the PDF "Key results" table and U-M4d read it."""

import dataclasses
import re
from pathlib import Path

import pypdf
import pytest

from embodic.api import compute_project
from embodic.io.examples import examples_dir
from embodic.io.exporters import ExportSummary
from embodic.io.report import write_report_pdf
from embodic.results import QUANTITY_LABELS, AnalysisResult
from embodic.results.labels import QUANTITY_SYMBOLS, quantity_title
from embodic.ui.strings.shell import STRINGS

pytestmark = pytest.mark.req("REQ-T-02")

FIELDS = [f.name for f in dataclasses.fields(AnalysisResult)]
SPEC = Path(__file__).parents[3] / "docs" / "phase2" / "engineering" / "equation_specification.md"


def test_every_analysis_result_field_has_exactly_one_label() -> None:
    """Catches a new field shown under its raw id, and a label left behind by a renamed or removed field."""
    assert sorted(QUANTITY_LABELS) == sorted(FIELDS)


def test_labels_are_plain_distinct_english_text() -> None:
    """Catches a raw-id or empty label, and two rows that a reader cannot tell apart."""
    labels = list(QUANTITY_LABELS.values())
    assert all(label == label.strip() and label[:1].isupper() and "_" not in label for label in labels)
    assert len(set(labels)) == len(labels)


def test_the_two_labels_the_shell_shows_say_the_same_thing() -> None:
    """Catches the summary strip and the report naming the same quantity differently."""
    assert QUANTITY_LABELS["ke_line_peak_v_s_per_rad"] == STRINGS["shell.sum-ke.label"]
    assert QUANTITY_LABELS["resistance_phase_operating_ohm"] == STRINGS["shell.sum-r-phase.label"]


def test_symbols_belong_to_labelled_fields() -> None:
    """Catches a symbol left behind by a renamed or removed field."""
    assert set(QUANTITY_SYMBOLS) <= set(QUANTITY_LABELS)


def test_every_symbol_is_written_in_the_equation_specification() -> None:
    """Catches an invented or mistyped symbol: each one must appear as a whole token in equation_specification.md."""
    spec = SPEC.read_text(encoding="utf-8")
    absent = [s for s in QUANTITY_SYMBOLS.values() if not re.search(rf"(?<!\w){re.escape(s)}(?!\w)", spec)]
    assert absent == []


@pytest.mark.parametrize(
    ("quantity", "title"),
    [
        ("resistance_phase_operating_ohm", "Phase resistance at operating temperature R_ph"),
        ("kt_n_m_per_a", "Torque constant per line current, rms Kt"),
        ("current_density_a_per_mm2", "Current density J"),
        ("loss_copper_w", "Copper loss P_Cu"),
        ("efficiency", "Efficiency, electromagnetic only η"),
        ("skin_depth_mm", "Skin depth δ"),
        ("temperature_rise_k", "Temperature rise, first-order estimate ΔT"),
        ("loss_delta_circulating_w", "Delta circulating-current loss P_δ,circ"),
        ("ke_line_peak_v_s_per_rad", "Line back-EMF constant, peak"),
        ("emf_phase_rms_v", "Phase back-EMF, rms"),
    ],
)
def test_title_is_the_label_then_the_symbol_the_specification_states(quantity: str, title: str) -> None:
    """Catches a symbol before the label, and a symbol invented for a quantity the spec leaves unnamed."""
    assert quantity_title(quantity) == title


def test_the_pdf_key_results_title_carries_the_symbol(tmp_path: Path) -> None:
    """Catches a report that prints the bare label for R_ph while the cards print the symbol."""
    outcome = compute_project(examples_dir() / "spiral_12c10p_d08.embodic.json")
    summary = write_report_pdf(outcome, tmp_path / "report.pdf")
    assert isinstance(summary, ExportSummary), summary
    text = "\n".join(page.extract_text() for page in pypdf.PdfReader(summary.path).pages)
    rows = text.split("Key results", 1)[1].split("DRC summary", 1)[0].splitlines()
    assert any(row.startswith("Phase resistance at operating temperature R_ph ") for row in rows)
    assert any(row.startswith("Efficiency, electromagnetic only η ") for row in rows)
    peak = next(row for row in rows if row.startswith("Line back-EMF constant, peak"))
    assert peak.startswith("Line back-EMF constant, peak 3"), peak
