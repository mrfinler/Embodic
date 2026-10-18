"""Runs compute and the self-tests off the GUI thread (REQ-N-02, interfaces.md section 14).

Compute: one request at a time, a new request cancels the running one. One worker thread (a QThreadPool of one) owns
the StageCache, so the cache is never used by two threads at once. An exception from the engine is logged with a
correlation id and reported to the GUI thread (REQ-N-18, UI-12).
"""

import logging
import uuid
from collections.abc import Callable, Sequence

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from embodic.api import StageCache, compute
from embodic.drc import CancelToken
from embodic.outcome import ComputeOutcome
from embodic.selftest import SelfTestCheck, SelfTestReport, SelfTestResult, run_selftests
from embodic.ui.viewmodels.outcome import ComputeRequest, ready_state

logger = logging.getLogger(__name__)

ComputeFn = Callable[..., ComputeOutcome | None]


class _Job(QRunnable):
    def __init__(self, worker: "ComputeWorker", request: ComputeRequest, cancel: CancelToken) -> None:
        super().__init__()
        self._worker, self._request, self._cancel = worker, request, cancel

    def run(self) -> None:
        request = self._request
        try:
            worker = self._worker
            outcome = worker.compute_fn(request.design, request.provenance, cache=worker.cache, cancel=self._cancel)
            ready = None if outcome is None or self._cancel.cancelled else ready_state(outcome, self._cancel)
        except Exception:
            correlation_id = uuid.uuid4().hex[:12]
            logger.exception("compute request %d failed", request.request_id, extra={"correlation_id": correlation_id})
            self._worker.failed.emit(request.request_id, correlation_id)
            return
        self._worker.finished.emit(request.request_id, ready)


class ComputeWorker(QObject):
    """Implements ComputeSubmitter with a one-thread pool; results arrive in the GUI thread through the signals."""

    finished = Signal(int, object)  # request id, OutcomeReady or None when cancelled
    failed = Signal(int, str)  # request id, correlation id of the log entry

    def __init__(self, compute_fn: ComputeFn = compute, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.compute_fn = compute_fn
        self.cache = StageCache()
        self._pool = QThreadPool(self)
        self._pool.setMaxThreadCount(1)
        self._cancel: CancelToken | None = None

    def submit(self, request: ComputeRequest) -> None:
        """Start a request after cancelling the one before it."""
        self.cancel()
        self._cancel = CancelToken()
        self._pool.start(_Job(self, request, self._cancel))

    def cancel(self) -> None:
        """Cancel the running request; its job ends at its next check of the token."""
        if self._cancel is not None:
            self._cancel.cancel()

    def shutdown(self) -> None:
        """Cancel the running request and wait for the thread to finish."""
        self.cancel()
        self._pool.waitForDone()


class _SelfTestJob(QRunnable):
    def __init__(self, worker: "SelfTestWorker", checks: Sequence[SelfTestCheck], cancel: CancelToken) -> None:
        super().__init__()
        self._worker, self._checks, self._cancel = worker, checks, cancel

    def run(self) -> None:
        try:
            report = run_selftests(self._checks, cancel=self._cancel, on_result=self._worker.result.emit)
        except Exception:
            logger.exception("the self-test run failed")
            self._worker.done.emit(None)
            return
        self._worker.done.emit(report)


class SelfTestWorker(QObject):
    """Implements SelfTestRunner with a one-thread pool; the signals bring each result to the GUI thread."""

    result = Signal(object)  # SelfTestResult
    done = Signal(object)  # SelfTestReport, or None when the run itself raised

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._pool = QThreadPool(self)
        self._pool.setMaxThreadCount(1)
        self._on_result: Callable[[SelfTestResult], None] | None = None
        self._on_done: Callable[[SelfTestReport | None], None] | None = None
        self.result.connect(self._deliver_result)
        self.done.connect(self._deliver_done)

    def start(
        self,
        checks: Sequence[SelfTestCheck],
        cancel: CancelToken,
        on_result: Callable[[SelfTestResult], None],
        on_done: Callable[[SelfTestReport | None], None],
    ) -> None:
        """Run the checks on the pool's thread."""
        self._on_result, self._on_done = on_result, on_done
        self._pool.start(_SelfTestJob(self, checks, cancel))

    def wait(self) -> None:
        """Block until the running check, if any, has finished."""
        self._pool.waitForDone()

    @Slot(object)
    def _deliver_result(self, result: SelfTestResult) -> None:
        if self._on_result is not None:
            self._on_result(result)

    @Slot(object)
    def _deliver_done(self, report: SelfTestReport | None) -> None:
        if self._on_done is not None:
            self._on_done(report)
