"""The environment tools/ci.py gives pytest: the release profile turns a missing personal-data token into a failure.

LG-06 scans for the committer's name, address and OS account. With none to scan for, `personal_tokens()` skips, and
the commit and nightly profiles cannot tell that apart from a release run (tests/static/lg_scan.py), so the release
profile sets EMBODIC_REQUIRE_PERSONAL_TOKENS=1.
"""

import importlib.util
from pathlib import Path

import pytest
from _pytest.outcomes import Failed, Skipped
from tests.static import lg_scan

TOOL = Path(__file__).resolve().parents[3] / "tools" / "ci.py"
spec = importlib.util.spec_from_file_location("ci", TOOL)
assert spec is not None and spec.loader is not None
ci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci)

pytestmark = pytest.mark.req("REQ-L-05")


def pytest_gate_env(profile_name: str) -> dict[str, str]:
    """Return the environment variables that tools/ci.py adds to the pytest gate of a profile."""
    gate = next(g for g in ci.gates_for(ci.PROFILES[profile_name]) if g.name == "pytest")
    return gate.env


def test_the_release_profile_requires_personal_tokens_for_pytest():
    """Catches a release run that skips the LG-06 personal scan when the machine yields no token."""
    assert pytest_gate_env("release").get(lg_scan.REQUIRE_TOKENS) == "1"


@pytest.mark.parametrize("profile_name", ["commit", "nightly"])
def test_the_commit_and_nightly_profiles_leave_a_missing_personal_token_a_skip(profile_name):
    """Catches the requirement leaking into profiles that run on a machine with no committer identity."""
    assert lg_scan.REQUIRE_TOKENS not in pytest_gate_env(profile_name)


@pytest.mark.parametrize(
    ("required", "outcome"), [("1", Failed), (None, Skipped)], ids=["required-fails", "not-required-skips"]
)
def test_a_missing_personal_token_fails_only_when_the_run_requires_one(monkeypatch, required, outcome):
    """Catches a scan that skips under the release environment, which would hide the gap the variable exists for."""
    monkeypatch.setattr(lg_scan, "environment_tokens", lambda: [])
    if required is None:
        monkeypatch.delenv(lg_scan.REQUIRE_TOKENS, raising=False)
    else:
        monkeypatch.setenv(lg_scan.REQUIRE_TOKENS, required)
    with pytest.raises(outcome):
        lg_scan.personal_tokens()
