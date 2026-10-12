"""The Tests dialog's state (interfaces.md section 14): results so far, the summary line and whether a run is going.

Qt-free. The runner starts `run_selftests` off the GUI thread and calls back on the GUI thread. Nothing here reaches
the registry, so a run cannot change a badge (D-007).
"""

from collections.abc import Callable, Sequence
from typing import Protocol

from embodic.drc import CancelToken
from embodic.selftest import SELFTESTS, SelfTestCheck, SelfTestReport, SelfTestResult, SelfTestVerdict
from embodic.ui.strings import text
from embodic.ui.viewmodels.observable import Observable


class SelfTestRunner(Protocol):
    """Runs the checks in a worker; both callbacks arrive on the GUI thread, `on_done` with None after a crash."""

    def start(
        self,
        checks: Sequence[SelfTestCheck],
        cancel: CancelToken,
        on_result: Callable[[SelfTestResult], None],
        on_done: Callable[[SelfTestReport | None], None],
    ) -> None:
        """Run the checks off the GUI thread with this cancel token."""


def summary_text(results: Sequence[SelfTestResult]) -> str:
    """Return "45 tests: 45 passed, 0 failed", with the not-run count when a cancel left checks out."""
    count = {verdict: 0 for verdict in SelfTestVerdict}
    for result in results:
        count[result.verdict] += 1
    fields = {
        "total": len(results),
        "passed": count[SelfTestVerdict.PASSED],
        "failed": count[SelfTestVerdict.FAILED],
        "not_run": count[SelfTestVerdict.NOT_RUN],
    }
    return text("selftest.summary.cancelled" if fields["not_run"] else "selftest.summary.done", **fields)


class SelfTestViewModel:
    """One run at a time; `run` starts from an empty table, `stop` cancels the checks not yet started."""

    def __init__(self, runner: SelfTestRunner, checks: Sequence[SelfTestCheck] = SELFTESTS) -> None:
        self._runner, self._checks = runner, tuple(checks)
        self._cancel: CancelToken | None = None
        self.rows: Observable[tuple[SelfTestResult, ...]] = Observable(())
        self.summary: Observable[str] = Observable(text("selftest.summary.idle", total=len(self._checks)))
        self.running: Observable[bool] = Observable(False)

    def run(self) -> None:
        """Start a run with a fresh cancel token; ignored while one is going."""
        if self.running.value:
            return
        self._cancel = CancelToken()
        self.rows.set(())
        self.running.set(True)
        self.summary.set(text("selftest.summary.running", done=0, total=len(self._checks)))
        self._runner.start(self._checks, self._cancel, self._on_result, self._on_done)

    def stop(self) -> None:
        """Cancel the running checks: the one under way finishes, every later one reads not run."""
        if self._cancel is not None:
            self._cancel.cancel()

    def _on_result(self, result: SelfTestResult) -> None:
        self.rows.set((*self.rows.value, result))
        self.summary.set(text("selftest.summary.running", done=len(self.rows.value), total=len(self._checks)))

    def _on_done(self, report: SelfTestReport | None) -> None:
        self.running.set(False)
        self.summary.set(text("selftest.summary.error") if report is None else summary_text(report.results))
