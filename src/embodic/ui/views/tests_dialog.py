"""``dlg-tests``: run the self-tests in a worker and list each result (screens.md section 13, interfaces.md 14)."""

import logging
from collections.abc import Callable, Sequence

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal, Slot
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from embodic.drc import CancelToken
from embodic.selftest import SelfTestCheck, SelfTestReport, SelfTestResult, SelfTestVerdict, run_selftests
from embodic.ui.strings import text
from embodic.ui.theme import ThemeTokens
from embodic.ui.viewmodels.selftest import SelfTestViewModel
from embodic.ui.views.style import themed_icon

logger = logging.getLogger(__name__)

COLUMNS = ("id", "group", "result", "duration", "message")
VERDICT_ICONS = {
    SelfTestVerdict.PASSED: "check-pass",
    SelfTestVerdict.FAILED: "check-fail",
    SelfTestVerdict.NOT_RUN: "check-warn",
}


class _Job(QRunnable):
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
        self._pool.start(_Job(self, checks, cancel))

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


class TestsDialog(QDialog):
    """The Tests dialog; Esc or Stop cancels a run, Esc closes the dialog when nothing runs."""

    def __init__(
        self, vm: SelfTestViewModel, worker: SelfTestWorker, tokens: ThemeTokens, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setObjectName("dlg-tests")
        self.setWindowTitle(text("selftest.title"))
        self.vm, self.worker, self.tokens = vm, worker, tokens
        intro = QLabel(text("selftest.intro"))
        intro.setWordWrap(True)
        intro.setProperty("class", "hint")
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setObjectName("tests-table")
        self.table.setHorizontalHeaderLabels([text(f"selftest.column.{c}") for c in COLUMNS])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.summary = QLabel()
        self.summary.setObjectName("tests-summary")
        self.summary.setWordWrap(True)
        self.run_button = QPushButton()
        self.run_button.setObjectName("btn-tests-run")
        self.run_button.setProperty("class", "primary")
        self.run_button.clicked.connect(self._run_or_stop)
        foot = QHBoxLayout()
        foot.addWidget(self.summary, 1)
        foot.addWidget(self.run_button)
        layout = QVBoxLayout(self)
        layout.addWidget(intro)
        layout.addWidget(self.table, 1)
        layout.addLayout(foot)
        vm.rows.subscribe(self._show_rows)
        vm.summary.subscribe(self.summary.setText)
        vm.running.subscribe(self._show_running)
        self._show_rows(vm.rows.value)
        self.summary.setText(vm.summary.value)
        self._show_running(vm.running.value)
        self.resize(820, 600)

    def _run_or_stop(self) -> None:
        if self.vm.running.value:
            self.vm.stop()
        else:
            self.vm.run()

    def _show_running(self, running: bool) -> None:
        self.run_button.setText(text("selftest.stop" if running else "selftest.run"))

    def _show_rows(self, rows: tuple[SelfTestResult, ...]) -> None:
        self.table.setRowCount(len(rows))
        for index, result in enumerate(rows):
            verdict = result.verdict.value
            cells = [
                QTableWidgetItem(result.check_id),
                QTableWidgetItem(result.group.value),
                QTableWidgetItem(verdict),
                QTableWidgetItem(text("selftest.duration", seconds=result.duration_s)),
                QTableWidgetItem(result.message),
            ]
            icon = themed_icon(VERDICT_ICONS[result.verdict], self.tokens)
            if icon is not None:
                cells[2].setIcon(icon)
            cells[0].setToolTip(result.title)
            cells[3].setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            for column, cell in enumerate(cells):
                self.table.setItem(index, column, cell)
        if rows:
            self.table.scrollToBottom()

    def reject(self) -> None:
        """Esc: stop a run and keep the dialog open to show the rows that did not run; else close."""
        if self.vm.running.value:
            self.vm.stop()
            return
        super().reject()

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 (Qt override)
        """Stop a run and wait for the check under way, so no worker outlives the dialog."""
        self.vm.stop()
        self.worker.wait()
        super().closeEvent(event)
