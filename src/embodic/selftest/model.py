"""The types of the self-test (interfaces.md section 14): a check, its result and the report of one run."""

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TypeAlias

from embodic.outcome import VersionInfo

SelfTestValue: TypeAlias = float | int | bool | str | tuple[str, ...]


class SelfTestGroup(StrEnum):
    """What a check covers; the Tests table and the CLI show the value."""

    CLOSED_FORM = "closed form"  # CF cases of oracle_cases.json and the spiral worked examples
    EXAMPLES = "examples"  # the five packaged examples compute, with their pinned design hashes
    DRC = "drc"
    EXPORT = "export"


class SelfTestVerdict(StrEnum):
    """The outcome of one check."""

    PASSED = "passed"
    FAILED = "failed"
    NOT_RUN = "not run"  # cancelled before the check started


@dataclass(frozen=True, slots=True, kw_only=True)
class SelfTestCheck:
    """One value computed through the public functions and compared with a value copied from a pytest test."""

    id: str  # "ST-CF01"; unique; the Tests table and the CLI show it
    group: SelfTestGroup
    title: str  # English, one line
    source_test: str  # pytest node ID whose assertion gives expected, rel_tol and abs_tol
    expected: SelfTestValue
    unit: str  # display unit of a float value ("T", "ohm", "mm"), "" otherwise
    measure: Callable[[Path], SelfTestValue]  # receives an empty scratch folder; writes nowhere else
    rel_tol: float = 0.0
    abs_tol: float = 0.0


@dataclass(frozen=True, slots=True, kw_only=True)
class SelfTestResult:
    """What one check gave."""

    check_id: str
    group: SelfTestGroup
    title: str
    verdict: SelfTestVerdict
    observed: SelfTestValue | None  # None when not run, or when measure raised
    expected: SelfTestValue
    duration_s: float
    message: str  # "" when passed; else expected, observed and tolerance, or the exception type and text


@dataclass(frozen=True, slots=True, kw_only=True)
class SelfTestReport:
    """Every result of one run, with the versions it ran on."""

    results: tuple[SelfTestResult, ...]  # one per check, in catalogue order
    versions: VersionInfo
    evidence_build_id: str | None  # load_registry().evidence_build_id (section 3.1), shown, never changed by a run
    cancelled: bool

    @property
    def ok(self) -> bool:
        """Every result passed: no failure and nothing not run."""
        return all(result.verdict is SelfTestVerdict.PASSED for result in self.results)


def agrees(observed: SelfTestValue, expected: SelfTestValue, *, rel_tol: float, abs_tol: float) -> bool:
    """Compare an observed value with its expectation.

    A float or int against a float expectation: |observed - expected| <= max(abs_tol, rel_tol * |expected|).
    Anything else: equality.
    """
    if isinstance(expected, float) and isinstance(observed, int | float):
        return abs(observed - expected) <= max(abs_tol, rel_tol * abs(expected))
    return observed == expected
