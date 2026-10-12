"""Strings of the Tests dialog (screens.md section 13, interfaces.md section 14)."""

from collections.abc import Mapping

STRINGS: Mapping[str, str] = {
    "selftest.title": "Self-tests",
    "selftest.intro": (
        "Checks that this installation reproduces the numbers of its build. The result changes no status badge."
    ),
    "selftest.run": "Run",
    "selftest.stop": "Stop",
    "selftest.column.id": "Test ID",
    "selftest.column.group": "Group",
    "selftest.column.result": "Result",
    "selftest.column.duration": "Duration",
    "selftest.column.message": "Message",
    "selftest.duration": "{seconds:.2f}\N{NO-BREAK SPACE}s",
    "selftest.summary.idle": "{total} tests. Run checks this installation.",
    "selftest.summary.running": "Running: {done} of {total} tests done.",
    "selftest.summary.done": "{total} tests: {passed} passed, {failed} failed",
    "selftest.summary.cancelled": "{total} tests: {passed} passed, {failed} failed, {not_run} not run",
    "selftest.summary.error": "The self-test stopped with an internal error; the log holds the details.",
}
