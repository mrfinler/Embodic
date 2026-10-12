"""PK-11: the self-test passes from an installed wheel without pytest, tests/ or docs/ (test_plan.md section 5.7)."""

import pytest
from tests.packaging.support import run

ABSENT = (
    "import importlib.util, json; "
    "print(json.dumps([m for m in ('pytest', 'tests', 'docs') if importlib.util.find_spec(m)]))"
)


@pytest.mark.req("REQ-N-06")
def test_pk11_the_installed_cli_selftest_passes_without_pytest_tests_or_docs(clean_venv, tmp_path):
    """Catches a self-test check that needs pytest, a test file or a document, none of which the wheel carries."""
    assert clean_venv.evaluate(ABSENT) == [], "precondition: the venv reaches no pytest, tests or docs"
    printed = run(clean_venv.cli, "selftest", cwd=tmp_path).splitlines()
    assert printed[-1] == "45 tests: 45 passed, 0 failed"
    assert len(printed) == 46
