"""Shared pytest configuration: markers, Hypothesis profiles and the REQ report that tools/trace_matrix.py reads."""

import json
import os
import shutil
import socket
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from hypothesis import settings

from embodic.paths import resource_root
from embodic.results import registry

MARKERS = (
    "req(*req_ids): requirement IDs (REQ-x-nn) this test verifies; every test needs at least one (TR-02)",
    "eq(*eq_ids): equation IDs (EQ-nn) this test exercises",
    "eqt(*eqt_ids): registry test IDs (EQT-nn-kind) this test realises (interfaces.md section 3.1)",
    "slow: longer than a few seconds; runs in the nightly and release profiles only",
    "manual: needs a human; never runs in CI",
)

# Example counts are an assumption (Hypothesis default 100 per commit, 20x that overnight), not a measured need.
settings.register_profile("commit", max_examples=100, deadline=None)
settings.register_profile("nightly", max_examples=2000, deadline=None)
settings.load_profile(os.environ.get("EMBODIC_HYPOTHESIS_PROFILE", "commit"))


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register --req-report."""
    parser.addoption(
        "--req-report",
        metavar="PATH",
        default=None,
        help="write one JSON record per test (node id, REQ, EQ and EQT markers, outcome) for tools/trace_matrix.py",
    )


_Connect = Callable[[socket.socket, Any], None]


def _refuse_connection(*args: object, **kwargs: object) -> None:
    raise AssertionError(f"network connection attempted during a test: {args!r} (REQ-N-17)")


def _admit_socketpair_connect(real_connect: _Connect) -> _Connect:
    """Return a `socket.connect` that refuses every call except the one inside CPython's socketpair fallback.

    On Windows `socket.socketpair` is `_fallback_socketpair`, which listens on a loopback port and connects to it
    (Lib/socket.py). The caller's code object is the whole test: a connect from anywhere else, loopback included, fails.
    """

    def connect(sock: socket.socket, address: Any) -> None:
        if sys._getframe(1).f_code is socket._fallback_socketpair.__code__:
            real_connect(sock, address)
        else:
            _refuse_connection(sock, address)

    return connect


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Refuse `socket.socket.connect` and `socket.create_connection` in every test (REQ-N-17, V3-01 gap N-17).

    PK-07 scans imports and cannot see a dependency or a code path that connects at run time. The error is not an
    OSError, so a caller that retries on connection errors cannot swallow it. `socket.socketpair` still works: the
    connect inside its Windows fallback is the one connect admitted (D-055d).
    """
    monkeypatch.setattr(socket.socket, "connect", _admit_socketpair_connect(socket.socket.connect))
    monkeypatch.setattr(socket, "create_connection", _refuse_connection)


SHIPPED_REGISTRIES = pytest.StashKey[tuple[pytest.MonkeyPatch, Path]]()


def pytest_configure(config: pytest.Config) -> None:
    """Register the markers, the REQ report collector when asked, and the registry without build evidence."""
    for line in MARKERS:
        config.addinivalue_line("markers", line)
    report_path = config.getoption("--req-report")
    if report_path:
        config.pluginmanager.register(ReqReport(Path(report_path)), "embodic-req-report")
    config.stash[SHIPPED_REGISTRIES] = _load_registry_without_build_evidence()


def pytest_unconfigure(config: pytest.Config) -> None:
    """Restore the registry's resource root and delete the session copy."""
    patch, folder = config.stash[SHIPPED_REGISTRIES]
    patch.undo()
    shutil.rmtree(folder, ignore_errors=True)


def _load_registry_without_build_evidence() -> tuple[pytest.MonkeyPatch, Path]:
    """Point load_registry() at a copy of the shipped registries that leaves out passed_tests.v1.json (D-045f).

    A release run leaves that file in resources/evidence (interfaces.md section 3.1), and it would turn the badges under
    test away from `not tested`. A test about evidence writes its own file and passes load_registry an explicit root.
    This runs before collection because some test modules call load_registry() at import.
    """
    folder = Path(tempfile.mkdtemp(prefix="embodic-registries-"))
    skip_evidence = shutil.ignore_patterns(registry.PASSED_TESTS_FILE)
    shutil.copytree(resource_root() / "evidence", folder / "evidence", ignore=skip_evidence)
    patch = pytest.MonkeyPatch()
    patch.setattr(registry, "resource_root", lambda: folder)
    return patch, folder


class ReqReport:
    """Collect REQ/EQ/EQT markers at collection and the outcome of each test, then write them as JSON."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.records: dict[str, dict[str, object]] = {}

    @pytest.hookimpl(tryfirst=True)
    def pytest_collection_modifyitems(self, items: list[pytest.Item]) -> None:
        """Record the markers of every collected test, before -m deselects any, so TR-02 sees them all."""
        for item in items:
            self.records[item.nodeid] = {
                "nodeid": item.nodeid,
                "req": sorted({req for mark in item.iter_markers("req") for req in mark.args}),
                "eq": sorted({eq for mark in item.iter_markers("eq") for eq in mark.args}),
                "eqt": sorted({eqt for mark in item.iter_markers("eqt") for eqt in mark.args}),
                "outcome": "not run",
            }

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        """Take the call outcome; a skipped or failing setup or teardown overrides it."""
        record = self.records.get(report.nodeid)
        if record is not None and (report.when == "call" or report.outcome != "passed"):
            record["outcome"] = report.outcome

    def pytest_sessionfinish(self) -> None:
        """Write the records, sorted by node id."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        records = [self.records[nodeid] for nodeid in sorted(self.records)]
        self.path.write_text(json.dumps(records, indent=1) + "\n", encoding="utf-8")
