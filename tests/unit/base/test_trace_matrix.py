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
    """Catches a parser that drops rows: requirements.md holds 98 Phase 1 IDs plus 12 new rows (its own summary)."""
    rows = trace_matrix.parse_requirements(trace_matrix.REQUIREMENTS.read_text(encoding="utf-8"))
    assert len(rows) == 110
    assert len({r.req_id for r in rows}) == 110
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


def collected(nodeid: str, outcome: str, *req_ids: str):
    """Return one test of a REQ report."""
    return CollectedTest(nodeid, req_ids, outcome)


@pytest.mark.req("REQ-T-09", "REQ-N-02")
def test_merged_reports_give_each_test_the_outcome_of_the_report_that_ran_it():
    """Catches a merge that keeps the main report's `not run` for a latency test that the second process ran (D-074).

    Both processes collect the whole suite, so each report lists every test; the one that did not run it says `not run`.
    """
    main = [
        collected("t.py::test_steady", "passed", "REQ-N-21"),
        collected("t.py::test_latency", "not run", "REQ-N-02"),
    ]
    latency = [
        collected("t.py::test_steady", "not run", "REQ-N-21"),
        collected("t.py::test_latency", "passed", "REQ-N-02"),
    ]

    merged = trace_matrix.merge_reports([main, latency])

    assert [(t.nodeid, t.req_ids, t.outcome) for t in merged] == [
        ("t.py::test_steady", ("REQ-N-21",), "passed"),
        ("t.py::test_latency", ("REQ-N-02",), "passed"),
    ]


@pytest.mark.req("REQ-T-09", "REQ-N-02")
@pytest.mark.parametrize(
    ("first", "second", "outcome"),
    [
        ("passed", "failed", "failed"),
        ("failed", "passed", "failed"),
        ("passed", "skipped", "skipped"),
        ("not run", "not run", "not run"),
    ],
)
def test_a_test_that_two_reports_both_ran_takes_the_worse_outcome(first, second, outcome):
    """Catches a merge in which a pass in one process hides a failure or a skip in the other."""
    merged = trace_matrix.merge_reports(
        [[collected("t.py::test_a", first, "REQ-N-02")], [collected("t.py::test_a", second, "REQ-N-02")]]
    )

    assert [(t.nodeid, t.req_ids, t.outcome) for t in merged] == [("t.py::test_a", ("REQ-N-02",), outcome)]


@pytest.mark.req("REQ-T-09")
def test_merged_reports_keep_a_test_that_only_one_report_lists():
    """Catches a merge that drops a test missing from the first report, which TR-02 would then never see."""
    merged = trace_matrix.merge_reports(
        [[collected("t.py::test_a", "passed", "REQ-N-21")], [collected("t.py::test_b", "passed")]]
    )

    assert [(t.nodeid, t.req_ids) for t in merged] == [("t.py::test_a", ("REQ-N-21",)), ("t.py::test_b", ())]
