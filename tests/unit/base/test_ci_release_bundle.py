"""The release profile of tools/ci.py builds the PyInstaller bundle before pytest and makes tests/bundle fail, not skip.

REQ-N-06 accepts "the bundle smoke test runs if the stretch unit lands". The commit and nightly profiles build no
bundle, so tests/bundle skips there; the release profile builds it and sets EMBODIC_REQUIRE_BUNDLE=1 (D-068).
"""

import importlib.util
from pathlib import Path

import pytest
from _pytest.outcomes import Failed, Skipped
from tests.bundle import bundle_gate

TOOL = Path(__file__).resolve().parents[3] / "tools" / "ci.py"
spec = importlib.util.spec_from_file_location("ci", TOOL)
assert spec is not None and spec.loader is not None
ci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci)

pytestmark = pytest.mark.req("REQ-N-06")


def is_bundle_build(gate) -> bool:
    """Return True for the gate that runs tools/build_bundle.py."""
    return Path(gate.argv[-1]).name == "build_bundle.py"


def gate_positions(profile_name: str) -> dict[str, int]:
    """Return the run-order index of the mypy, bundle-build and pytest gates of a profile (absent ones left out)."""
    positions: dict[str, int] = {}
    for index, gate in enumerate(ci.gates_for(ci.PROFILES[profile_name])):
        kind = "bundle" if is_bundle_build(gate) else gate.name.split()[0]
        positions.setdefault(kind, index)
    return positions


def test_the_release_profile_builds_the_bundle_after_the_static_gates_and_before_pytest():
    """Catches a release run whose bundle tests meet no folder: the build must precede pytest, which would skip."""
    positions = gate_positions("release")

    assert positions["mypy"] < positions["bundle"] < positions["pytest"]


@pytest.mark.parametrize("profile_name", ["commit", "nightly"])
def test_the_commit_and_nightly_profiles_build_no_bundle(profile_name):
    """Catches the minutes-long PyInstaller build leaking into the profiles that run on every commit."""
    assert "bundle" not in gate_positions(profile_name)


def pytest_gate_env(profile_name: str) -> dict[str, str]:
    """Return the environment variables that tools/ci.py adds to the pytest gate of a profile."""
    gate = next(g for g in ci.gates_for(ci.PROFILES[profile_name]) if g.name == "pytest")
    return gate.env


def test_the_release_profile_requires_the_bundle_for_pytest():
    """Catches a release run whose bundle tests skip: a failed or missing build would pass as five skips."""
    assert pytest_gate_env("release").get(bundle_gate.REQUIRE_BUNDLE) == "1"


@pytest.mark.parametrize("profile_name", ["commit", "nightly"])
def test_the_commit_and_nightly_profiles_leave_a_missing_bundle_a_skip(profile_name):
    """Catches the requirement leaking into profiles that build no bundle: every commit gate would then fail."""
    assert bundle_gate.REQUIRE_BUNDLE not in pytest_gate_env(profile_name)


@pytest.mark.parametrize(
    ("required", "outcome"),
    [("1", Failed), (None, Skipped), ("0", Skipped)],
    ids=["required-fails", "not-required-skips", "switched-off-skips"],
)
def test_a_missing_bundle_fails_only_when_the_run_requires_one(monkeypatch, tmp_path, required, outcome):
    """Catches a bundle test that skips under the release environment, which hides a build that produced nothing."""
    if required is None:
        monkeypatch.delenv(bundle_gate.REQUIRE_BUNDLE, raising=False)
    else:
        monkeypatch.setenv(bundle_gate.REQUIRE_BUNDLE, required)
    with pytest.raises(outcome):
        bundle_gate.require_bundle(tmp_path / "embodic-cli")


@pytest.mark.parametrize("required", ["1", None], ids=["required", "not-required"])
def test_a_built_bundle_is_tested_whether_or_not_the_run_requires_it(monkeypatch, tmp_path, required):
    """Catches a guard that fails or skips although the CLI is there, so that the bundle tests never run."""
    if required is None:
        monkeypatch.delenv(bundle_gate.REQUIRE_BUNDLE, raising=False)
    else:
        monkeypatch.setenv(bundle_gate.REQUIRE_BUNDLE, required)
    frozen_cli = tmp_path / "embodic-cli"
    frozen_cli.write_bytes(b"")

    assert bundle_gate.require_bundle(frozen_cli) is None


def test_the_failure_names_the_missing_cli_and_the_switch(monkeypatch, tmp_path):
    """Catches a failure message that leaves the reader without the path or the variable that caused the failure."""
    monkeypatch.setenv(bundle_gate.REQUIRE_BUNDLE, "1")
    frozen_cli = tmp_path / "embodic-cli"
    with pytest.raises(Failed) as failure:
        bundle_gate.require_bundle(frozen_cli)

    assert str(frozen_cli) in str(failure.value)
    assert bundle_gate.REQUIRE_BUNDLE in str(failure.value)
