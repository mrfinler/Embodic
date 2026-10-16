"""REQ-T-05: a `verified` equation whose linked tests did not pass must stop the release (acceptance: CI fails)."""

import json
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


@pytest.mark.req("REQ-T-05")
@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="record_main exits 0 and prints the ID as 'carried by no test' (tests/unit/results/"
    "test_record_passed_tests.py l.85-117). The acceptance says CI fails and names the equation, or Agent 6 rewords "
    "it to the badge downgrade `not tested`. The decision is Fable's.",
)
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
