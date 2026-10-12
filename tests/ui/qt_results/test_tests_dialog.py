"""UI-35: the Tests dialog runs the self-tests in a worker, lists every result and never moves a badge (REQ-F-25)."""

import threading
import time
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton, QTableWidget, QWidget

from embodic.selftest import SELFTESTS, SelfTestCheck, SelfTestGroup
from embodic.ui.toolstrip import TOOLSTRIP, ToolstripTab
from embodic.ui.viewmodels.selftest import SelfTestViewModel
from embodic.ui.views import tests_dialog

CF11 = "spiral_12c16p_default"
RUN_TIMEOUT_MS = 180_000  # hang guard only


def slow(check_id: str, seconds: float, threads: list[int]) -> SelfTestCheck:
    """Return a check that records its thread, sleeps, then passes."""

    def measure(_: Path) -> float:
        threads.append(threading.get_ident())
        time.sleep(seconds)
        return 1.0

    return SelfTestCheck(
        id=check_id,
        group=SelfTestGroup.EXPORT,
        title=f"slow {check_id}",
        source_test="tests/ui/qt_results/test_tests_dialog.py::slow",
        expected=1.0,
        unit="",
        measure=measure,
    )


def column(table: QTableWidget, index: int) -> list[str]:
    """Return the texts of one column."""
    return [table.item(row, index).text() for row in range(table.rowCount())]


def badges(window: QWidget) -> dict[str, str]:
    """Return every badge label of the window by objectName."""
    return {
        label.objectName(): label.text()
        for label in window.findChildren(QLabel)
        if label.objectName().endswith("-badge")
    }


def open_dialog(window, qtbot, checks) -> tests_dialog.TestsDialog:
    """Open a Tests dialog over the window that runs ``checks`` instead of the catalogue."""
    worker = tests_dialog.SelfTestWorker(window)
    dialog = tests_dialog.TestsDialog(SelfTestViewModel(worker, checks), worker, window.tokens, window)
    qtbot.addWidget(dialog)
    dialog.show()
    return dialog


@pytest.mark.req("REQ-F-25")
def test_ui35_the_view_tab_help_group_opens_the_tests_dialog(make_window, qtbot) -> None:
    """D-045c. Catches a missing entry point, or one in another tab, group or with another icon."""
    (action,) = [a for a in TOOLSTRIP if a.id == "act-tests"]
    assert (action.tab, action.group, action.icon, action.command) == (
        ToolstripTab.VIEW,
        "help",
        "check-pass",
        "show_tests",
    )
    window = make_window()
    assert window.toolstrip.buttons["act-tests"].text() == "Self-tests"
    window.toolstrip.actions_by_id["act-tests"].trigger()
    dialog = window.findChild(tests_dialog.TestsDialog, "dlg-tests")
    assert dialog is not None and dialog.isVisible()
    assert dialog.findChild(QPushButton, "btn-tests-run").text() == "Run"
    assert dialog.findChild(QLabel, "tests-summary").text() == "45 tests. Run checks this installation."
    dialog.close()


@pytest.mark.req("REQ-F-25")
def test_ui35_a_run_lists_45_passed_rows_reads_45_passed_and_moves_no_badge(make_window, load, qtbot) -> None:
    """Catches a row without its icon and word, a wrong summary, or a run that changes a result badge."""
    window = load(make_window(), CF11)
    before = badges(window)
    assert before
    window.show_tests()
    dialog = window.tests_dialog
    qtbot.mouseClick(dialog.findChild(QPushButton, "btn-tests-run"), Qt.MouseButton.LeftButton)
    assert dialog.run_button.text() == "Stop"
    qtbot.waitUntil(lambda: not dialog.vm.running.value, timeout=RUN_TIMEOUT_MS)
    table = dialog.findChild(QTableWidget, "tests-table")
    assert column(table, 0) == [check.id for check in SELFTESTS]
    assert column(table, 1) == [check.group.value for check in SELFTESTS]
    assert set(column(table, 2)) == {"passed"}
    assert all(not table.item(row, 2).icon().isNull() for row in range(table.rowCount()))
    assert all(text.endswith("\N{NO-BREAK SPACE}s") for text in column(table, 3))
    assert set(column(table, 4)) == {""}
    assert dialog.findChild(QLabel, "tests-summary").text() == "45 tests: 45 passed, 0 failed"
    assert dialog.run_button.text() == "Run"
    assert badges(window) == before
    dialog.close()


@pytest.mark.req("REQ-F-25")
def test_ui35_the_checks_run_on_a_thread_other_than_the_gui_thread(make_window, qtbot) -> None:
    """Catches a run on the GUI thread, which freezes the window for the whole run."""
    threads: list[int] = []
    dialog = open_dialog(make_window(), qtbot, [slow("ST-A", 0.0, threads), slow("ST-B", 0.0, threads)])
    dialog.run_button.click()
    qtbot.waitUntil(lambda: not dialog.vm.running.value, timeout=RUN_TIMEOUT_MS)
    assert len(threads) == 2
    assert threading.get_ident() not in threads
    assert dialog.summary.text() == "2 tests: 2 passed, 0 failed"


@pytest.mark.req("REQ-F-25")
@pytest.mark.parametrize("how", ["esc", "stop"])
def test_ui35_esc_and_stop_cancel_and_the_rest_read_not_run(make_window, qtbot, how) -> None:
    """Catches a cancel that is ignored, rows that vanish instead of reading not run, or Esc closing mid-run."""
    threads: list[int] = []
    checks = [slow(f"ST-{n}", 0.3, threads) for n in range(6)]
    dialog = open_dialog(make_window(), qtbot, checks)
    dialog.run_button.click()
    qtbot.waitUntil(lambda: dialog.table.rowCount() >= 1, timeout=RUN_TIMEOUT_MS)
    if how == "esc":
        qtbot.keyClick(dialog, Qt.Key.Key_Escape)
    else:
        dialog.run_button.click()
    qtbot.waitUntil(lambda: not dialog.vm.running.value, timeout=RUN_TIMEOUT_MS)
    words = column(dialog.table, 2)
    assert dialog.isVisible()
    assert len(words) == 6
    assert words[0] == "passed" and words[-1] == "not run"
    assert words.count("not run") >= 3
    passed = words.count("passed")
    assert dialog.summary.text() == f"6 tests: {passed} passed, 0 failed, {6 - passed} not run"


@pytest.mark.req("REQ-F-25")
def test_ui35_a_second_run_starts_from_an_empty_table(make_window, qtbot) -> None:
    """Catches rows of the last run left in the table while the next one runs."""
    threads: list[int] = []
    dialog = open_dialog(make_window(), qtbot, [slow("ST-A", 0.1, threads), slow("ST-B", 0.1, threads)])
    dialog.run_button.click()
    qtbot.waitUntil(lambda: not dialog.vm.running.value, timeout=RUN_TIMEOUT_MS)
    assert dialog.table.rowCount() == 2
    dialog.run_button.click()
    assert dialog.table.rowCount() == 0
    qtbot.waitUntil(lambda: not dialog.vm.running.value, timeout=RUN_TIMEOUT_MS)
    assert column(dialog.table, 0) == ["ST-A", "ST-B"]
