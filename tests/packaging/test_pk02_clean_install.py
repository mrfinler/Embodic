"""PK-02: a clean venv installs the hashed lock file and the wheel, and the installed CLI computes an example."""

import json
import re
from pathlib import Path

import pytest
from tests.packaging.support import LOCK, REPO, CleanVenv, installed_distributions_code, run

import embodic
from embodic.results.registry import PASSED_TESTS_FILE, package_source_sha256

EXAMPLE = REPO / "resources" / "examples" / "spiral_12c16p_default.embodic.json"
PIN = re.compile(r"^([A-Za-z0-9_.-]+)==(\S+)", re.MULTILINE)


def compute_json(venv: CleanVenv, out: Path) -> dict:
    """Run the installed `embodic-cli compute --json` on the default example and return the JSON outcome."""
    run(venv.cli, "compute", EXAMPLE, "--json", out, cwd=out.parent)
    return json.loads(out.read_text(encoding="utf-8"))


@pytest.mark.req("REQ-N-05")
def test_pk02_the_clean_venv_holds_exactly_the_lock_pins_and_the_wheel(clean_venv):
    """Catches a lock file that installs other versions than it pins, or an undeclared runtime dependency."""
    pins = {name.lower(): version for name, version in PIN.findall(LOCK.read_text(encoding="utf-8"))}
    installed = clean_venv.evaluate(installed_distributions_code("d.version"))
    assert pins == {"numpy": "2.4.6", "pyside6-essentials": "6.11.2", "shiboken6": "6.11.2"}
    assert installed == pins | {"embodic": embodic.__version__}


@pytest.mark.req("REQ-N-05", "REQ-N-06")
def test_pk02_the_installed_cli_computes_the_default_example_from_the_wheel(clean_venv, tmp_path):
    """Catches a wheel that misses resources or modules: the installed CLI must compute without the source tree."""
    outcome = compute_json(clean_venv, tmp_path / "outcome.json")
    assert outcome["ok"] is True
    assert outcome["versions"]["embodic"] == embodic.__version__
    assert clean_venv.resource_root().parts[-2:] == ("embodic", "_resources")
    assert outcome["analysis"]["resistance_phase_20c_ohm"]["status"] == "not tested"


@pytest.mark.req("REQ-T-05", "REQ-N-06")
def test_pk02_installed_wheel_applies_evidence_written_for_the_source_tree(clean_venv, tmp_path):
    """Catches installed .py files that hash differently from src/embodic, so release evidence would never apply.

    The evidence here is synthetic: it lists every registry test ID, which no gate run can claim until the eqt markers
    of U-M5o exist. It proves the installed reader and the source hash, not that any test passed.
    """
    target = clean_venv.resource_root() / "evidence" / PASSED_TESTS_FILE
    versions = clean_venv.evaluate(
        "import json, embodic; from embodic.results.registry import load_registry; r = load_registry(); "
        "print(json.dumps({'v': embodic.__version__, 'r': r.version, "
        "'tests': sorted({t for e in r.equations.values() for t in e.tests})}))"
    )
    passed = versions["tests"]
    document = {
        "build_id": f"{versions['v']}+g000000000000.20261012T000000Z",
        "embodic_version": versions["v"],
        "format": "embodic.passed-tests",
        "format_version": 1,
        "gate_profile": "release",
        "generated_utc": "2026-10-12T00:00:00Z",
        "git_commit": "0" * 40,
        "git_dirty": True,
        "numpy": "synthetic",
        "passed_tests": passed,
        "platform": "synthetic",
        "python": "synthetic",
        "realised_by": {test: ["synthetic"] for test in passed},
        "registry_version": versions["r"],
        "source_sha256": package_source_sha256(Path(embodic.__file__).resolve().parent),
    }
    target.write_text(json.dumps(document, sort_keys=True), encoding="utf-8")
    try:
        result = compute_json(clean_venv, tmp_path / "outcome.json")["analysis"]["resistance_phase_20c_ohm"]
    finally:
        target.unlink()
    assert len(passed) == 63
    assert result["eq_ids"] == ["EQ-10", "EQ-11", "EQ-07"]  # D-058d: a phase R holds the EQ-07 phase assembly
    assert result["status"] == "inferred"
    assert result["status_reasons"] == ["EQ-10 verified", "EQ-11 inferred", "EQ-07 inferred"]
