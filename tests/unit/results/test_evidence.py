"""UT-RES-08 (evidence reader) and UT-RES-09 (badge change from the evidence), interfaces.md section 3.1."""

import json
import shutil
from pathlib import Path

import pytest

import embodic
from embodic.paths import resource_root
from embodic.results.registry import (
    PASSED_TESTS_FILE,
    evidence_applies,
    load_registry,
    package_source_sha256,
    parse_passed_tests,
)
from embodic.results.status import Status
from embodic.results.traceable import traced
from embodic.units import Unit

PACKAGE = Path(embodic.__file__).resolve().parent
EQ10_TESTS = ["EQT-10-CF04", "EQT-10-GR", "EQT-10-O2"]
EQ05_TESTS = ["EQT-05-CF01", "EQT-05-CF03", "EQT-05-EC", "EQT-05-GR", "EQT-05-O1", "EQT-05-O2"]


@pytest.fixture
def root(tmp_path: Path) -> Path:
    """Return a scratch resource root holding a copy of the packaged registries and no evidence file."""
    skip_evidence = shutil.ignore_patterns(PASSED_TESTS_FILE)
    shutil.copytree(resource_root() / "evidence", tmp_path / "evidence", ignore=skip_evidence)
    return tmp_path


def document(root: Path, passed: list[str]) -> dict:
    """Return an evidence document that applies to this tree, built from its own versions and source hash."""
    registry_version = load_registry(root).version
    return {
        "build_id": "0.0.1+g0123456789ab.20261012T120000Z",
        "embodic_version": embodic.__version__,
        "format": "embodic.passed-tests",
        "format_version": 1,
        "gate_profile": "release",
        "generated_utc": "2026-10-12T12:00:00Z",
        "git_commit": "0123456789abcdef0123456789abcdef01234567",
        "git_dirty": False,
        "numpy": "2.4.6",
        "passed_tests": sorted(passed),
        "platform": "Linux-x86_64",
        "python": "3.11.15",
        "realised_by": {test: [f"tests/unit/test_x.py::test_{test}"] for test in sorted(passed)},
        "registry_version": registry_version,
        "source_sha256": package_source_sha256(PACKAGE),
    }


def write(root: Path, content: dict | str) -> None:
    """Write the evidence file under the scratch root, as text or as JSON."""
    text = content if isinstance(content, str) else json.dumps(content, sort_keys=True)
    (root / "evidence" / PASSED_TESTS_FILE).write_text(text, encoding="utf-8")


@pytest.mark.req("REQ-T-05")
def test_ut_res_08_a_matching_file_fills_passed_tests_and_the_build_id(root):
    """Catches a reader that ignores a valid evidence file, so every badge stays `not tested` in a tested build."""
    write(root, document(root, EQ10_TESTS))
    registry = load_registry(root)
    assert registry.passed_tests == frozenset({"EQT-10-CF04", "EQT-10-GR", "EQT-10-O2"})
    assert registry.evidence_build_id == "0.0.1+g0123456789ab.20261012T120000Z"


def _without(key: str):
    def change(doc: dict) -> dict:
        del doc[key]
        return doc

    return change


def _with(key: str, value):
    def change(doc: dict) -> dict:
        doc[key] = value
        return doc

    return change


@pytest.mark.req("REQ-T-05")
@pytest.mark.parametrize(
    "change",
    [
        pytest.param(None, id="no-file"),
        pytest.param("{not json", id="not-json"),
        pytest.param(_with("format", "embodic.other"), id="wrong-format"),
        pytest.param(_with("format_version", 2), id="format-version-2"),
        pytest.param(_without("realised_by"), id="missing-key"),
        pytest.param(_with("passed_tests", ["EQT-10-GR", 7]), id="passed-tests-not-strings"),
        pytest.param(_with("passed_tests", "EQT-10-GR"), id="passed-tests-not-a-list"),
        pytest.param(_with("git_dirty", "no"), id="git-dirty-not-bool"),
        pytest.param(_with("embodic_version", "0.0.0"), id="embodic-version-changed"),
        pytest.param(_with("registry_version", "v1+000000000000.000000000000"), id="registry-version-changed"),
        pytest.param(_with("source_sha256", "0" * 64), id="source-changed"),
    ],
)
def test_ut_res_08_an_absent_unreadable_or_stale_file_gives_no_evidence_and_no_issue(root, change):
    """Catches a reader that raises, adds an issue, or trusts evidence from another build or other source code."""
    baseline_issues = load_registry(root).issues
    if isinstance(change, str):
        write(root, change)
    elif change is not None:
        write(root, change(document(root, EQ10_TESTS)))
    registry = load_registry(root)
    assert registry.passed_tests == frozenset()
    assert registry.evidence_build_id is None
    assert registry.issues == baseline_issues


@pytest.mark.req("REQ-T-05")
def test_ut_res_08_evidence_applies_skips_only_the_source_hash_when_it_is_none(root):
    """Catches a frozen build (no .py files) rejecting valid evidence, or a None hash skipping the version checks."""
    evidence = parse_passed_tests(document(root, EQ10_TESTS) | {"source_sha256": "f" * 64})
    assert evidence is not None
    current = {"embodic_version": evidence.embodic_version, "registry_version": evidence.registry_version}
    assert evidence_applies(evidence, **current, source_sha256=None) is True
    assert evidence_applies(evidence, **current, source_sha256="e" * 64) is False
    assert evidence_applies(evidence, **(current | {"embodic_version": "9.9.9"}), source_sha256=None) is False
    assert evidence_applies(evidence, **(current | {"registry_version": "v1+x.y"}), source_sha256=None) is False


@pytest.mark.req("REQ-T-05")
def test_ut_res_08_source_hash_follows_one_byte_and_is_none_without_python_files(tmp_path):
    """Catches a hash that misses an edit to the code, depends on __pycache__, or invents a value for a frozen build."""
    package = tmp_path / "pkg"
    (package / "sub" / "__pycache__").mkdir(parents=True)
    (package / "a.py").write_bytes(b"x = 1\n")
    (package / "sub" / "b.py").write_bytes(b"y = 2\n")
    (package / "data.json").write_bytes(b"{}")
    before = package_source_sha256(package)
    (package / "sub" / "__pycache__" / "b.cpython-311.py").write_bytes(b"cached")
    assert package_source_sha256(package) == before
    (package / "sub" / "b.py").write_bytes(b"y = 3\n")
    after = package_source_sha256(package)
    assert before is not None
    assert len(before) == 64
    assert after != before
    empty = tmp_path / "frozen"
    (empty / "embodic").mkdir(parents=True)
    (empty / "embodic" / "app.pyc").write_bytes(b"compiled")
    assert package_source_sha256(empty) is None


def _badges(registry):
    """Return the four results UT-RES-09 names, traced against one registry."""
    return {
        "eq10": traced("resistance_phase_20c_ohm", 1.5, Unit.OHM, eq_ids=("EQ-10",), inputs=(), registry=registry),
        "eq05": traced("b1_peak_t", 0.4, Unit.T, eq_ids=("EQ-05",), inputs=(), registry=registry),
        "eq14": traced("inductance_estimate_h", 2e-6, Unit.H, eq_ids=("EQ-14",), inputs=(), registry=registry),
        "input": traced("air_gap_mm", 1.0, Unit.MM, eq_ids=(), inputs=(), registry=registry, kind_tag="input"),
    }


@pytest.mark.req("REQ-T-05")
def test_ut_res_09_evidence_for_every_linked_test_lifts_the_badge_to_the_equation_status(root):
    """Catches badges that ignore the evidence, or evidence that changes more than the test state (D-007)."""
    without = _badges(load_registry(root))
    write(root, document(root, EQ10_TESTS + EQ05_TESTS))
    registry = load_registry(root)
    with_evidence = _badges(registry)
    assert {key: t.status for key, t in without.items()} == {
        "eq10": Status.NOT_TESTED,
        "eq05": Status.NOT_TESTED,
        "eq14": Status.UNRESOLVED,
        "input": Status.NOT_TESTED,
    }
    assert {key: t.status for key, t in with_evidence.items()} == {
        "eq10": Status.VERIFIED,
        "eq05": Status.INFERRED,
        "eq14": Status.UNRESOLVED,
        "input": Status.NOT_TESTED,
    }
    assert registry.test_state("EQ-10") is Status.VERIFIED
    assert registry.test_state("EQ-05") is Status.INFERRED
    for key, result in with_evidence.items():
        assert (result.value, result.assumed_inputs, result.validity) == (
            without[key].value,
            without[key].assumed_inputs,
            without[key].validity,
        )


@pytest.mark.req("REQ-T-05")
def test_ut_res_09_one_missing_linked_test_keeps_the_badge_not_tested(root):
    """Catches a test state that turns on when only some of an equation's registry tests passed."""
    write(root, document(root, EQ10_TESTS[:-1]))
    registry = load_registry(root)
    assert registry.passed_tests == frozenset({"EQT-10-CF04", "EQT-10-GR"})
    assert _badges(registry)["eq10"].status is Status.NOT_TESTED
    assert registry.test_state("EQ-10") is Status.NOT_TESTED


@pytest.mark.req("REQ-T-05")
def test_d045f_evidence_a_release_run_left_in_the_tree_never_reaches_the_test_session(root):
    """Catches a session whose default registry reads resources/evidence/passed_tests.v1.json (DEF-U-M5b-01, D-045f).

    The planted file applies to this tree but lists no test, so a run killed before the restore changes no badge.
    """
    leftover = resource_root() / "evidence" / PASSED_TESTS_FILE
    previous = leftover.read_bytes() if leftover.exists() else None
    leftover.write_text(json.dumps(document(root, []), sort_keys=True), encoding="utf-8")
    try:
        read_explicitly, read_by_default = load_registry(resource_root()), load_registry()
    finally:
        if previous is None:
            leftover.unlink()
        else:
            leftover.write_bytes(previous)
    assert read_explicitly.evidence_build_id == "0.0.1+g0123456789ab.20261012T120000Z", "precondition: the file applies"
    assert read_by_default.evidence_build_id is None
    assert read_by_default.passed_tests == frozenset()
