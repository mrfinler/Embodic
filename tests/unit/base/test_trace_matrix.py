"""TR-01 and TR-02 logic of tools/trace_matrix.py."""

import importlib.util
from pathlib import Path

import pytest

TOOL = Path(__file__).resolve().parents[3] / "tools" / "trace_matrix.py"
spec = importlib.util.spec_from_file_location("trace_matrix", TOOL)
assert spec is not None and spec.loader is not None
trace_matrix = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trace_matrix)

Requirement = trace_matrix.Requirement
CollectedTest = trace_matrix.CollectedTest

REQS = [
    Requirement("REQ-N-21", "amended", "must", "M1", "embodic.geometry", "UT-UNI-01"),
    Requirement("REQ-F-10", "carried", "must", "M1", "embodic.drc", "UT-DRC-01"),
    Requirement("REQ-N-01", "carried", "must", "M5", "embodic.api", "PF-01"),
    Requirement("REQ-K-01", "withdrawn", "-", "-", "-", "MT-07"),
]


@pytest.mark.req("REQ-T-09")
def test_trace_matrix_parses_every_requirement_row():
    """Catches a parser that drops rows: requirements.md holds 98 Phase 1 IDs plus 11 new rows (its own summary)."""
    rows = trace_matrix.parse_requirements(trace_matrix.REQUIREMENTS.read_text(encoding="utf-8"))
    assert len(rows) == 109
    assert len({r.req_id for r in rows}) == 109
    assert rows[0].req_id == "REQ-F-01"


@pytest.mark.req("REQ-T-09")
def test_trace_matrix_reports_unmarked_tests_and_unknown_ids():
    """TR-02: catches a test without a REQ marker and a typo in a marker going unnoticed."""
    tests = [
        CollectedTest("tests/a.py::test_ok", ("REQ-N-21",), "passed"),
        CollectedTest("tests/a.py::test_bare", (), "passed"),
        CollectedTest("tests/a.py::test_typo", ("REQ-N-99",), "passed"),
    ]
    unmarked, unknown = trace_matrix.find_marker_errors(REQS, tests)
    assert unmarked == ["tests/a.py::test_bare"]
    assert unknown == ["tests/a.py::test_typo: REQ-N-99"]


@pytest.mark.req("REQ-T-09")
def test_trace_matrix_untested_counts_only_passing_live_must_requirements_due():
    """TR-01: a failing test does not cover a requirement; later milestones and withdrawn rows are not due yet."""
    tests = [
        CollectedTest("tests/a.py::test_units", ("REQ-N-21",), "passed"),
        CollectedTest("tests/a.py::test_drc", ("REQ-F-10",), "failed"),
    ]
    assert trace_matrix.find_untested(REQS, tests, "M1") == ["REQ-F-10"]
    assert trace_matrix.find_untested(REQS, tests, "M5") == ["REQ-F-10", "REQ-N-01"]


@pytest.mark.req("REQ-T-09")
def test_trace_matrix_row_counts_automated_and_passed_tests():
    """Catches a matrix row that counts a failed or unrelated test as passing."""
    tests = [
        CollectedTest("tests/a.py::test_one", ("REQ-N-21",), "passed"),
        CollectedTest("tests/a.py::test_two", ("REQ-N-21", "REQ-F-10"), "failed"),
    ]
    matrix = trace_matrix.render_matrix(REQS, tests)
    assert "| REQ-N-21 | amended | must | M1 | embodic.geometry | UT-UNI-01 | 2 | 1 |" in matrix
    assert "| REQ-F-10 | carried | must | M1 | embodic.drc | UT-DRC-01 | 1 | 0 |" in matrix
