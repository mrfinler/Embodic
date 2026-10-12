"""UT-SLF-03: the self-test runner with fake checks (REQ-F-25, interfaces.md section 14)."""

import json
import math
import threading
from pathlib import Path

import pytest

from embodic.drc import CancelToken
from embodic.selftest import (
    SelfTestCheck,
    SelfTestGroup,
    SelfTestResult,
    SelfTestVerdict,
    agrees,
    run_selftests,
    selftest_to_json,
)


def check(check_id: str, measure, expected=1.0, *, rel_tol: float = 0.0, abs_tol: float = 0.0) -> SelfTestCheck:
    """Return a fake check in ohm with the given tolerances."""
    return SelfTestCheck(
        id=check_id,
        group=SelfTestGroup.CLOSED_FORM,
        title=f"fake {check_id}",
        source_test="tests/unit/selftest/test_runner.py::check",
        expected=expected,
        unit="ohm",
        measure=measure,
        rel_tol=rel_tol,
        abs_tol=abs_tol,
    )


def boom(_scratch: Path) -> float:
    """Raise, as a measure with a defect would."""
    raise ZeroDivisionError("division by zero in the fake")


@pytest.mark.req("REQ-F-25")
def test_ut_slf_03_a_value_outside_tolerance_fails_with_expected_observed_and_tolerance() -> None:
    """Catches a failure message that leaves out what was expected, what was seen or how close it had to be."""
    (result,) = run_selftests([check("F-1", lambda _: 1.01, rel_tol=1e-3)]).results
    assert (result.verdict, result.observed, result.expected) == (SelfTestVerdict.FAILED, 1.01, 1.0)
    assert result.message == "expected 1.0 ohm, observed 1.01 ohm, tolerance rel. 0.001"


@pytest.mark.req("REQ-F-25")
def test_ut_slf_03_a_value_inside_tolerance_passes_with_an_empty_message() -> None:
    """Catches a tolerance applied the wrong way round (a pass inside the band reported as a failure)."""
    (result,) = run_selftests([check("P-1", lambda _: 1.0000004, abs_tol=5e-7)]).results
    assert (result.verdict, result.message) == (SelfTestVerdict.PASSED, "")


@pytest.mark.req("REQ-F-25")
def test_ut_slf_03_a_measure_that_raises_fails_and_the_next_check_still_runs() -> None:
    """Catches a runner that stops at the first exception or loses the exception's type and text."""
    report = run_selftests([check("R-1", boom), check("R-2", lambda _: 1.0)])
    first, second = report.results
    assert (first.verdict, first.observed) == (SelfTestVerdict.FAILED, None)
    assert first.message == "ZeroDivisionError: division by zero in the fake"
    assert second.verdict is SelfTestVerdict.PASSED
    assert report.ok is False


@pytest.mark.req("REQ-F-25")
def test_ut_slf_03_cancel_from_on_result_leaves_every_later_check_not_run() -> None:
    """Catches a cancel that is ignored, or a NOT_RUN result that is never reported to the listener."""
    token = CancelToken()
    seen: list[SelfTestResult] = []

    def listen(result: SelfTestResult) -> None:
        seen.append(result)
        token.cancel()

    ran: list[str] = []
    checks = [check(f"C-{n}", lambda _, n=n: ran.append(f"C-{n}") or 1.0) for n in range(4)]
    report = run_selftests(checks, cancel=token, on_result=listen)
    assert [r.verdict for r in report.results] == [SelfTestVerdict.PASSED] + [SelfTestVerdict.NOT_RUN] * 3
    assert [r.observed for r in report.results] == [1.0, None, None, None]
    assert ran == ["C-0"]
    assert [r.check_id for r in seen] == ["C-0", "C-1", "C-2", "C-3"]
    assert (report.cancelled, report.ok) == (True, False)


@pytest.mark.req("REQ-F-25")
def test_ut_slf_03_ok_only_when_every_result_passed() -> None:
    """Catches `ok` read from the failure count alone, which would call a cancelled run a success."""
    assert run_selftests([check("A", lambda _: 1.0), check("B", lambda _: 1.0)]).ok is True
    assert run_selftests([check("A", lambda _: 1.0), check("B", lambda _: 2.0)]).ok is False


@pytest.mark.req("REQ-F-25")
def test_ut_slf_03_each_check_gets_its_own_empty_scratch_folder_that_is_deleted() -> None:
    """Catches checks that share a folder (one check's files changing another's result) or leave files behind."""
    folders: list[Path] = []

    def write(scratch: Path) -> bool:
        empty = not any(scratch.iterdir())
        (scratch / "out.txt").write_text("x", encoding="utf-8")
        folders.append(scratch)
        return empty

    report = run_selftests([check("W-1", write, True), check("W-2", write, True)])
    assert [r.verdict for r in report.results] == [SelfTestVerdict.PASSED] * 2
    assert folders[0] != folders[1]
    assert [f.exists() for f in folders] == [False, False]


@pytest.mark.req("REQ-F-25")
def test_ut_slf_03_measure_runs_on_the_calling_thread_and_on_result_too() -> None:
    """Catches a runner that starts threads of its own; the Tests dialog relies on running it in its worker."""
    threads: list[int] = []
    run_selftests(
        [check("T-1", lambda _: threads.append(threading.get_ident()) or 1.0)],
        on_result=lambda _: threads.append(threading.get_ident()),
    )
    assert threads == [threading.get_ident()] * 2


@pytest.mark.req("REQ-F-25")
def test_ut_slf_03_selftest_to_json_round_trips_through_json_loads() -> None:
    """Catches a document that json cannot read: a bare NaN, a tuple of names or an enum object."""
    checks = [
        check("J-1", lambda _: math.nan),
        check("J-2", lambda _: ("a.txt", "b.txt"), ("a.txt", "b.txt")),
        check("J-3", boom),
    ]
    report = run_selftests(checks)
    document = selftest_to_json(report)
    text = json.dumps(document, allow_nan=False)
    loaded = json.loads(text)
    assert loaded == document
    assert loaded["cancelled"] is False
    assert loaded["versions"]["embodic"] == report.versions.embodic
    assert "evidence_build_id" in loaded
    assert [r["verdict"] for r in loaded["results"]] == ["failed", "passed", "failed"]
    assert loaded["results"][0]["observed"] == {"$f": "nan"}
    assert loaded["results"][1]["observed"] == ["a.txt", "b.txt"]
    assert loaded["results"][2]["observed"] is None
    assert loaded["results"][0]["group"] == "closed form"


@pytest.mark.req("REQ-F-25")
@pytest.mark.parametrize(
    ("observed", "expected", "rel_tol", "abs_tol", "agreed"),
    [
        (0.731313131, 0.7313131313131313, 1e-9, 0.0, True),
        (0.7313, 0.7313131313131313, 1e-9, 0.0, False),
        (10, 10, 0.0, 0.0, True),
        (415.48075, 415.4808, 0.0, 5e-5, True),
        (415.4807, 415.4808, 0.0, 5e-5, False),
        ("AabBCcaABbcC", "AabBCcaABbcC", 0.0, 0.0, True),
        ("AabBCcaABbcC", "AabBCcaABbCc", 1.0, 1.0, False),
        (("a", "b"), ("a", "b"), 0.0, 0.0, True),
        (math.nan, 1.0, 1.0, 1.0, False),
    ],
)
def test_ut_slf_03_agrees_applies_the_larger_of_the_two_tolerances(observed, expected, rel_tol, abs_tol, agreed):
    """Catches a tolerance that uses the observed value as the scale, a tolerance on a string, or a NaN that passes."""
    assert agrees(observed, expected, rel_tol=rel_tol, abs_tol=abs_tol) is agreed
