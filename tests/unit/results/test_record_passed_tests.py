"""TR-05: tools/record_passed_tests.py turns one REQ report into the evidence file (interfaces.md section 3.1)."""

import importlib.util
import json
import platform
from pathlib import Path

import pytest
from tests.unit.results.registries import REPO

from embodic.results.registry import load_registry, parse_passed_tests
from embodic.results.status import Status

KNOWN = frozenset({"EQT-10-GR", "EQT-10-CF04", "EQT-10-O2", "EQT-05-GR"})


def load_tool():
    """Import tools/record_passed_tests.py, which is a script and not a package module."""
    spec = importlib.util.spec_from_file_location("record_passed_tests", REPO / "tools" / "record_passed_tests.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verified_linked_tests() -> frozenset[str]:
    """Return every EQT ID that a `verified` equation of the packaged registry links; a release run must pass all."""
    equations = load_registry().equations.values()
    return frozenset(t for e in equations if e.status is Status.VERIFIED for t in e.tests)


def records(tool, *rows):
    """Return report records from (nodeid, outcome, eqt ids) rows."""
    return [tool.ReportRecord(nodeid=n, outcome=o, eqt=tuple(e)) for n, o, e in rows]


def write_report(path: Path, *rows) -> Path:
    """Write a REQ report in the shape tests/conftest.py writes, with an eqt list per record."""
    report = [{"nodeid": n, "req": ["REQ-T-05"], "eq": [], "outcome": o, "eqt": list(e)} for n, o, e in rows]
    path.write_text(json.dumps(report), encoding="utf-8")
    return path


@pytest.mark.req("REQ-T-05")
def test_tr05_an_id_passes_only_when_every_carrier_passed():
    """Catches an ID counted as passed while one of its carrying tests failed, skipped or did not run."""
    tool = load_tool()
    passed, realised_by = tool.passed_registry_tests(
        records(
            tool,
            ("t.py::a", "passed", ["EQT-10-GR", "EQT-10-CF04"]),
            ("t.py::b", "passed", ["EQT-10-GR"]),
            ("t.py::c", "skipped", ["EQT-10-CF04"]),
            ("t.py::d", "not run", ["EQT-10-O2"]),
            ("t.py::e", "passed", []),
        ),
        KNOWN,
    )
    assert passed == frozenset({"EQT-10-GR"})
    assert dict(realised_by) == {"EQT-10-GR": ("t.py::a", "t.py::b")}


@pytest.mark.req("REQ-T-05")
def test_tr05_an_unknown_eqt_id_raises():
    """Catches a typo in a marker that would otherwise never match and hide forever."""
    tool = load_tool()
    with pytest.raises(ValueError, match="EQT-10-GX"):
        tool.passed_registry_tests(records(tool, ("t.py::a", "passed", ["EQT-10-GX"])), KNOWN)


@pytest.mark.req("REQ-T-05")
@pytest.mark.parametrize(
    ("profile", "rows"),
    [
        pytest.param("commit", [("t.py::a", "passed", ["EQT-10-GR"])], id="commit-profile"),
        pytest.param("release", None, id="missing-report"),
        pytest.param("release", [("t.py::a", "passed", ["EQT-10-GR"]), ("t.py::b", "failed", [])], id="one-failed"),
        pytest.param("release", [("t.py::a", "passed", ["EQT-99-GR"])], id="unknown-id"),
    ],
)
def test_tr05_record_main_refuses_and_writes_nothing(tmp_path, profile, rows):
    """Catches evidence written for a non-release run, a red run, a missing report or an unknown ID."""
    report = tmp_path / "req_report.json"
    if rows is not None:
        write_report(report, *rows)
    out = tmp_path / "evidence" / "passed_tests.v1.json"
    argv = ["--report", str(report), "--profile", profile, "--out", str(out)]
    assert load_tool().record_main(argv) == 1
    assert not out.parent.exists() or list(out.parent.iterdir()) == []


@pytest.mark.req("REQ-T-05")
def test_tr05_record_main_writes_a_file_the_reader_parses_back(tmp_path, capsys):
    """Catches a writer whose file the reader rejects, unsorted keys, or a host name or home path in the file."""
    explicit = {"EQT-10-GR", "EQT-10-CF04", "EQT-10-O2"}
    other_verified = verified_linked_tests() - explicit
    report = write_report(
        tmp_path / "req_report.json",
        ("tests/x.py::a", "passed", ["EQT-10-GR", "EQT-10-CF04"]),
        ("tests/x.py::b", "passed", ["EQT-10-O2"]),
        ("tests/x.py::c", "skipped", []),
        ("tests/x.py::d", "not run", []),
        ("tests/x.py::verified", "passed", sorted(other_verified)),
    )
    out = tmp_path / "evidence" / "passed_tests.v1.json"
    argv = ["--report", str(report), "--profile", "release", "--out", str(out)]
    assert load_tool().record_main(argv) == 0

    text = out.read_text(encoding="utf-8")
    document = json.loads(text)
    evidence = parse_passed_tests(document)
    assert evidence is not None
    assert evidence.passed_tests == explicit | other_verified
    assert dict(evidence.realised_by) == {
        "EQT-10-CF04": ("tests/x.py::a",),
        "EQT-10-GR": ("tests/x.py::a",),
        "EQT-10-O2": ("tests/x.py::b",),
    } | {test_id: ("tests/x.py::verified",) for test_id in other_verified}
    assert list(document) == sorted(document)
    assert document["platform"] == platform.platform()
    assert document["gate_profile"] == "release"
    assert document["registry_version"] == load_registry().version
    assert document["build_id"].startswith(f"{document['embodic_version']}+g{document['git_commit'][:12]}.")
    assert platform.node() not in text
    assert str(Path.home()) not in text
    total = len({t for e in load_registry().equations.values() for t in e.tests})
    passed = len(explicit | other_verified)
    assert capsys.readouterr().out.startswith(
        f"{passed} of {total} registry test IDs passed; {total - passed} carried by no test"
    )


@pytest.mark.req("REQ-T-05")
def test_tr05_a_report_without_eqt_keys_is_refused_and_writes_nothing(tmp_path, capsys):
    """Catches a writer that crashes on a report written before the eqt markers existed (U-M5o), or that records it.

    Such a report carries no registry test, so no `verified` equation has a passing test and the release stops.
    """
    report = tmp_path / "req_report.json"
    report.write_text(json.dumps([{"nodeid": "t.py::a", "req": [], "eq": [], "outcome": "passed"}]), encoding="utf-8")
    out = tmp_path / "passed_tests.v1.json"
    assert load_tool().record_main(["--report", str(report), "--profile", "release", "--out", str(out)]) == 1
    assert "EQ-10" in capsys.readouterr().err
    assert not out.exists()
