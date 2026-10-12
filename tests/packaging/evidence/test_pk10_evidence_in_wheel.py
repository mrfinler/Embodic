"""PK-10: after the record step, the release wheel carries the evidence file and an installed copy applies it.

tools/ci.py --profile release runs this folder after `record_passed_tests.py` and the wheel build, never before.
"""

import json

import pytest
from tests.packaging.support import REPO, CleanVenv, wheel_members

from embodic.results.registry import PASSED_TESTS_FILE

EVIDENCE = REPO / "resources" / "evidence" / PASSED_TESTS_FILE
MEMBER = f"embodic/_resources/evidence/{PASSED_TESTS_FILE}"


@pytest.fixture(scope="module")
def release_wheel():
    """Return the one wheel that the release gate built into build/dist."""
    (wheel,) = (REPO / "build" / "dist").glob("embodic-*.whl")
    return wheel


@pytest.mark.req("REQ-N-06", "REQ-T-05")
def test_pk10_the_wheel_carries_the_recorded_evidence_byte_for_byte(release_wheel):
    """Catches a wheel built before the record step, or one that leaves out the git-ignored evidence file."""
    assert wheel_members(release_wheel)[MEMBER] == EVIDENCE.read_bytes()


@pytest.mark.req("REQ-N-06", "REQ-T-05")
def test_pk10_a_clean_install_of_the_wheel_applies_the_evidence(release_wheel, tmp_path):
    """Catches evidence that a real install rejects as stale, which would leave every badge `not tested`.

    `evidence_build_id` is set only when the file applies, so it proves the check even while `passed_tests` is empty
    because no test carries an eqt marker yet (U-M5o).
    """
    recorded = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    venv = CleanVenv(tmp_path / "venv", release_wheel)
    installed = venv.evaluate(
        "import json; from embodic.results.registry import load_registry; r = load_registry(); "
        "print(json.dumps({'passed': sorted(r.passed_tests), 'build_id': r.evidence_build_id}))"
    )
    assert installed == {"passed": recorded["passed_tests"], "build_id": recorded["build_id"]}
