"""One English display label per AnalysisResult field (D-038e); the PDF "Key results" table and U-M4d read it."""

import dataclasses

import pytest

from embodic.results import QUANTITY_LABELS, AnalysisResult
from embodic.ui.strings.shell import STRINGS

pytestmark = pytest.mark.req("REQ-T-02")

FIELDS = [f.name for f in dataclasses.fields(AnalysisResult)]


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
