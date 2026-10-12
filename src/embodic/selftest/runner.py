"""Run self-test checks in order and report each result (interfaces.md section 14). Imports no Qt and no pytest."""

import math
import tempfile
import time
from collections.abc import Callable, Sequence
from pathlib import Path

from embodic.api import version_info
from embodic.drc import CancelToken
from embodic.io.board_dump import NONFINITE_TAG
from embodic.model.schema import JsonValue
from embodic.results import load_registry
from embodic.selftest.catalogue import SELFTESTS, forget_computed
from embodic.selftest.model import (
    SelfTestCheck,
    SelfTestReport,
    SelfTestResult,
    SelfTestValue,
    SelfTestVerdict,
    agrees,
)


def _value_text(value: SelfTestValue, unit: str) -> str:
    text = repr(value)
    return f"{text} {unit}" if unit else text


def _tolerance_text(check: SelfTestCheck) -> str:
    parts = [f"rel. {check.rel_tol:g}"] if check.rel_tol else []
    if check.abs_tol:
        parts.append(f"abs. {check.abs_tol:g}" + (f" {check.unit}" if check.unit else ""))
    return f"tolerance {' or '.join(parts)}" if parts else "exact"


def _run_one(check: SelfTestCheck) -> SelfTestResult:
    observed: SelfTestValue | None = None
    started = time.perf_counter()
    try:
        with tempfile.TemporaryDirectory(prefix="embodic-selftest-") as scratch:
            observed = check.measure(Path(scratch))
    except Exception as error:
        verdict, message = SelfTestVerdict.FAILED, f"{type(error).__name__}: {error}"
    else:
        if agrees(observed, check.expected, rel_tol=check.rel_tol, abs_tol=check.abs_tol):
            verdict, message = SelfTestVerdict.PASSED, ""
        else:
            verdict = SelfTestVerdict.FAILED
            message = (
                f"expected {_value_text(check.expected, check.unit)}, observed {_value_text(observed, check.unit)}, "
                f"{_tolerance_text(check)}"
            )
    return SelfTestResult(
        check_id=check.id,
        group=check.group,
        title=check.title,
        verdict=verdict,
        observed=observed,
        expected=check.expected,
        duration_s=time.perf_counter() - started,
        message=message,
    )


def _not_run(check: SelfTestCheck) -> SelfTestResult:
    return SelfTestResult(
        check_id=check.id,
        group=check.group,
        title=check.title,
        verdict=SelfTestVerdict.NOT_RUN,
        observed=None,
        expected=check.expected,
        duration_s=0.0,
        message="",
    )


def run_selftests(
    checks: Sequence[SelfTestCheck] = SELFTESTS,
    *,
    cancel: CancelToken | None = None,
    on_result: Callable[[SelfTestResult], None] | None = None,
) -> SelfTestReport:
    """Run the checks in order, each with its own temporary folder that is deleted afterwards.

    A check that raises is FAILED with the exception type and message, and the run goes on. After cancel, every check
    not yet started is NOT_RUN. on_result is called once per result, from the running thread.
    """
    results: list[SelfTestResult] = []
    try:
        for check in checks:
            stopped = cancel is not None and cancel.cancelled
            result = _not_run(check) if stopped else _run_one(check)
            results.append(result)
            if on_result is not None:
                on_result(result)
    finally:
        forget_computed()
    # The registry field arrives with U-M5b (section 3.1); until then every build reads as having no evidence.
    build_id: str | None = getattr(load_registry(), "evidence_build_id", None)
    return SelfTestReport(
        results=tuple(results),
        versions=version_info(),
        evidence_build_id=build_id,
        cancelled=any(result.verdict is SelfTestVerdict.NOT_RUN for result in results),
    )


def _json_value(value: SelfTestValue | None) -> JsonValue:
    if isinstance(value, float) and not math.isfinite(value):
        return {NONFINITE_TAG: "nan" if math.isnan(value) else ("inf" if value > 0 else "-inf")}
    if isinstance(value, tuple):
        return list(value)
    return value


def selftest_to_json(report: SelfTestReport) -> dict[str, JsonValue]:
    """Versions, evidence_build_id, cancelled and one object per result; floats in the encoding of section 9.2."""
    versions = report.versions
    return {
        "versions": {
            "embodic": versions.embodic,
            "schema": versions.schema,
            "registry": versions.registry,
            "python": versions.python,
            "numpy": versions.numpy,
        },
        "evidence_build_id": report.evidence_build_id,
        "cancelled": report.cancelled,
        "results": [
            {
                "check_id": result.check_id,
                "group": result.group.value,
                "title": result.title,
                "verdict": result.verdict.value,
                "observed": _json_value(result.observed),
                "expected": _json_value(result.expected),
                "duration_s": result.duration_s,
                "message": result.message,
            }
            for result in report.results
        ],
    }
