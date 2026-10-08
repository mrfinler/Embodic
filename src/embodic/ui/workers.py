"""Runs compute off the GUI thread: one request at a time, a new request cancels the running one (REQ-N-02).

One worker thread (a QThreadPool of one) owns the StageCache, so the cache is never used by two threads at once.
An exception from the engine is logged with a correlation id and reported to the GUI thread (REQ-N-18, UI-12).
"""

import logging
import uuid
from collections.abc import Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal

from embodic.api import StageCache, compute
from embodic.drc import CancelToken
from embodic.outcome import ComputeOutcome
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
            ready = None if outcome is None or self._cancel.cancelled else ready_state(outcome)
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
        if self._cancel is not None:
            self._cancel.cancel()
        self._cancel = CancelToken()
        self._pool.start(_Job(self, request, self._cancel))

    def shutdown(self) -> None:
        """Cancel the running request and wait for the thread to finish."""
        if self._cancel is not None:
            self._cancel.cancel()
        self._pool.waitForDone()
