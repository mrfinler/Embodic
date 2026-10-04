"""Golden-regression setup: puts ``tests/golden`` on ``sys.path`` and collects logged comparisons.

Every golden area imports the shared ``harness`` package. The path is added here so that import works under both
pytest import modes: ``--import-mode=importlib`` adds no test directory to ``sys.path``.
"""

import sys
from pathlib import Path

import pytest

_GOLDEN_DIR = str(Path(__file__).resolve().parent)
if _GOLDEN_DIR not in sys.path:
    sys.path.insert(0, _GOLDEN_DIR)

from harness import GoldenReport  # noqa: E402

_REPORT_KEY = pytest.StashKey[GoldenReport]()


def pytest_configure(config: pytest.Config) -> None:
    """Create the session report that golden tests record into."""
    config.stash[_REPORT_KEY] = GoldenReport()


@pytest.fixture
def golden_report(request: pytest.FixtureRequest) -> GoldenReport:
    """Return the session report; ``check`` fails on a mismatch and logs expected or indeterminate results."""
    return request.config.stash[_REPORT_KEY]


def pytest_terminal_summary(terminalreporter: pytest.TerminalReporter, config: pytest.Config) -> None:
    """Print every expected and indeterminate golden comparison after the run."""
    report = config.stash.get(_REPORT_KEY, None)
    lines = report.summary_lines() if report else []
    if lines:
        terminalreporter.section("golden comparisons: expected and indeterminate")
        for line in lines:
            terminalreporter.write_line(line)
