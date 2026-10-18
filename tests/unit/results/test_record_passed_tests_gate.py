"""REQ-T-05: a `verified` equation whose linked tests did not pass must stop the release (acceptance: CI fails)."""

import json
import re
from pathlib import Path

import pytest
from tests.unit.results.test_record_passed_tests import load_tool

from embodic.results.registry import load_registry
from embodic.results.status import Status


def verified_equation_with_one_linked_test() -> tuple[str, str]:
    """Return a `verified` equation of the packaged registry and its only linked EQT ID."""
    registry = load_registry()
    for eq_id, equation in registry.equations.items():
        if equation.status is Status.VERIFIED and len(equation.tests) == 1:
            return eq_id, equation.tests[0]
    raise AssertionError("the packaged registry has no verified equation with exactly one linked test")


def verified_equations() -> dict[str, tuple[str, ...]]:
    """Return each `verified` equation of the packaged registry with its linked EQT IDs."""
    registry = load_registry()
    return {eq_id: e.tests for eq_id, e in registry.equations.items() if e.status is Status.VERIFIED}


def release_report(path: Path, *, skipping: str | None = None) -> Path:
    """Write a report in which every linked test of every verified equation passed, except `skipping` (skipped)."""
    records = [
        {"nodeid": f"tests/x.py::{eqt_id}", "req": ["REQ-T-05"], "eq": [], "outcome": "passed", "eqt": [eqt_id]}
        for tests in verified_equations().values()
        for eqt_id in tests
        if eqt_id != skipping
    ]
    if skipping is not None:
        skipped = {"nodeid": "tests/x.py::skipped", "req": ["REQ-T-05"], "eq": [], "outcome": "skipped"}
        records.append({**skipped, "eqt": [skipping]})
    path.write_text(json.dumps(records), encoding="utf-8")
    return path


def run_record(report: Path, out: Path) -> int:
    """Run the release record step on a report and return its exit code."""
    argv = ["--report", str(report), "--profile", "release", "--out", str(out)]
    return load_tool().record_main(argv)


@pytest.mark.req("REQ-T-05")
def test_a_report_that_passes_every_linked_test_of_every_verified_equation_records_the_evidence(tmp_path: Path) -> None:
    """Control for the refusals below: catches a gate that refuses a complete release run."""
    out = tmp_path / "passed_tests.v1.json"
    assert run_record(release_report(tmp_path / "req_report.json"), out) == 0
    assert out.is_file()


@pytest.mark.req("REQ-T-05")
def test_a_verified_equation_whose_only_linked_test_did_not_pass_stops_the_release(tmp_path: Path, capsys) -> None:
    """Catches a release that ships a `verified` equation whose tests did not run: exit 1 and the equation named."""
    eq_id, eqt_id = verified_equation_with_one_linked_test()
    report = tmp_path / "req_report.json"
    unrelated = {"nodeid": "tests/x.py::a", "req": ["REQ-T-05"], "eq": [], "outcome": "passed", "eqt": []}
    skipped = {"nodeid": "tests/x.py::b", "req": ["REQ-T-05"], "eq": [], "outcome": "skipped", "eqt": [eqt_id]}
    report.write_text(json.dumps([unrelated, skipped]), encoding="utf-8")
    argv = ["--report", str(report), "--profile", "release", "--out", str(tmp_path / "passed_tests.v1.json")]
    code = load_tool().record_main(argv)
    output = capsys.readouterr()
    assert code == 1
    assert eq_id in output.out + output.err


@pytest.mark.req("REQ-T-05")
def test_a_verified_equation_missing_one_of_several_linked_tests_stops_the_release(tmp_path: Path, capsys) -> None:
    """Catches a gate that counts one passing linked test as enough: UT-RES-09 keeps such a result `not tested`.

    Every other verified equation passed all its tests, so only the equation missing one test may be named.
    """
    eq_id, tests = next((k, t) for k, t in verified_equations().items() if len(t) > 1)
    out = tmp_path / "passed_tests.v1.json"
    code = run_record(release_report(tmp_path / "req_report.json", skipping=tests[-1]), out)
    output = capsys.readouterr()
    assert code == 1
    assert re.findall(r"\bEQ-\d+\b", output.out + output.err) == [eq_id]
    assert not out.exists()


@pytest.mark.req("REQ-T-05")
def test_stderr_alone_names_the_equation_and_the_registry_tests_of_it_that_passed(tmp_path: Path, capsys) -> None:
    """Catches a refusal that names the equation but not which of its linked tests passed in the run.

    requirements.md REQ-T-05 (revision 2026-10-17, U-D20): the gate names on stderr the equation with the registry test
    IDs that passed. The assertions read stderr only, because a CI log keeps the two streams apart.
    """
    eq_id, tests = next((k, t) for k, t in verified_equations().items() if len(t) > 1)
    skipped = tests[-1]
    report = release_report(tmp_path / "req_report.json", skipping=skipped)
    code = run_record(report, tmp_path / "passed_tests.v1.json")
    named = set(re.findall(r"(?<![\w-])(?:EQ|EQT)-[\w-]*\w", capsys.readouterr().err))
    assert code == 1
    assert eq_id in named
    assert named & set(tests) == set(tests) - {skipped}, "the passed tests are named, the test that did not pass is not"


@pytest.mark.req("REQ-T-05")
def test_stderr_names_a_refused_equation_none_of_whose_linked_tests_passed(tmp_path: Path, capsys) -> None:
    """Catches a refusal that lists every linked ID of an equation when none of them passed, or drops the equation."""
    eq_id = next(iter(verified_equations()))
    records = [
        {"nodeid": f"tests/x.py::{eqt}", "req": ["REQ-T-05"], "eq": [], "outcome": "passed", "eqt": [eqt]}
        for other, linked in verified_equations().items()
        if other != eq_id
        for eqt in linked
    ]
    report = tmp_path / "req_report.json"
    report.write_text(json.dumps(records), encoding="utf-8")
    code = run_record(report, tmp_path / "passed_tests.v1.json")
    named = set(re.findall(r"(?<![\w-])(?:EQ|EQT)-[\w-]*\w", capsys.readouterr().err))
    assert code == 1
    assert named == {eq_id}
