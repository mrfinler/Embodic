"""Compute worker and crash handling (UI-02, UI-05, UI-12)."""

import logging
import sys
import threading
import time
from pathlib import Path

import pytest
from PySide6.QtCore import QElapsedTimer, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from embodic.api import compute
from embodic.io.project import ProjectFile, load_project
from embodic.ui.app import RedactingFormatter, install_crash_handler
from embodic.ui.viewmodels.outcome import OutcomeComputing, OutcomeFailed, OutcomeReady

D08 = "spiral_12c10p_d08"
CANCEL_INTO_SCENE_MS = 50


@pytest.mark.req("REQ-N-02")
def test_ui02_a_new_request_cancels_the_running_one_and_only_the_latest_is_shown(make_shell, wait_ready):
    """Catches a superseded compute that runs on, or whose late result replaces the newer one.

    No clock: the first run blocks until its own token reports cancelled, which only the second request can do.
    """
    tokens = []

    def first_blocks(design, provenance, *, cache, cancel):
        tokens.append(cancel)
        if len(tokens) == 1:
            while not cancel.cancelled:
                time.sleep(0.001)
            return None
        return compute(design, provenance, cache=cache, cancel=cancel)

    shell = make_shell(compute_fn=first_blocks)
    window = shell.window
    finished = []
    shell.worker.finished.connect(lambda request_id, ready: finished.append((request_id, ready)))
    window.outcome.open_example(D08)
    window.outcome.compute_now()
    wait_ready(window)
    assert tokens[0].cancelled and not tokens[1].cancelled
    assert [(request_id, ready is None) for request_id, ready in finished] == [(1, True), (2, False)]
    assert window.outcome.state.value is finished[-1][1]


@pytest.mark.latency
@pytest.mark.req("REQ-N-02")
def test_def_u_m8n_01_a_cancel_during_the_scene_build_ends_it_early_and_no_result_reaches_the_shell(d08_shell, qtbot):
    """Catches a cancelled request whose scene build runs to its end, holding the GIL, and whose result then shows.

    The compute returns D08's outcome at once, so a job's time after it is the scene build. The worker builds it once
    without a cancel, the reference, then again with a cancel 50 ms in, sent through the worker as a new request's
    cancel is. The reference comes from the worker's thread: the same build on this process's GUI thread took twice
    as long (U-M8o), which would hide a build that ignores the cancel.
    """
    window, worker = d08_shell.window, d08_shell.worker
    outcome = window.outcome.state.value.outcome
    cancel_after_s: list[float] = []
    jobs: list[list] = []

    def returns_d08(design, provenance, *, cache, cancel):
        for delay_s in cancel_after_s:
            threading.Timer(delay_s, worker.cancel).start()
        jobs.append([time.perf_counter()])
        return outcome

    worker.compute_fn = returns_d08
    worker.finished.connect(lambda request_id, ready: jobs[-1].extend((time.perf_counter(), ready)))

    def build():
        window.outcome.compute_now()
        qtbot.waitUntil(lambda: len(jobs[-1]) == 3, timeout=10_000)
        returned, ended, ready = jobs[-1]
        return (ended - returned) * 1000, ready

    full_ms, full = build()
    cancel_after_s.append(CANCEL_INTO_SCENE_MS / 1000)
    cancelled_ms, cancelled = build()
    print(f"D08 scene build in the worker: {full_ms:.0f} ms, cancelled 50 ms in: {cancelled_ms:.0f} ms")
    assert isinstance(full, OutcomeReady), "precondition: the build without a cancel shows its result"
    assert cancelled_ms < CANCEL_INTO_SCENE_MS + full_ms / 2, (cancelled_ms, full_ms)
    assert cancelled is None
    assert isinstance(window.outcome.state.value, OutcomeComputing)


@pytest.mark.req("REQ-N-02")
def test_ui05_compute_runs_off_the_gui_thread(make_shell, wait_ready):
    """Catches a compute call on the GUI thread, which freezes input for the whole run."""
    threads = []

    def record_thread(design, provenance, **kwargs):
        threads.append(threading.get_ident())
        return compute(design, provenance, **kwargs)

    window = make_shell(compute_fn=record_thread).window
    window.outcome.open_example(D08)
    wait_ready(window)
    assert threads and threads[0] != threading.get_ident()


@pytest.mark.slow
@pytest.mark.latency
@pytest.mark.req("REQ-N-02")
def test_ui05_event_loop_answers_within_100ms_during_a_3s_compute(make_shell, qtbot):
    """Measures the largest gap between 10 ms GUI timer ticks during a 3 s synthetic compute (nightly only).

    The 100 ms bound is REQ-N-02's input-echo threshold (assumption); the idle baseline is measured first and printed.
    """
    finished = []

    def synthetic(design, provenance, *, cache, cancel):
        end = time.perf_counter() + 3.0
        while time.perf_counter() < end and not cancel.cancelled:
            sum(i * i for i in range(2000))
        finished.append(True)
        return None

    shell = make_shell(compute_fn=synthetic)
    window = shell.window

    def largest_gap(duration_ms):
        clock, gaps, last = QElapsedTimer(), [], [0]
        clock.start()
        timer = QTimer()
        timer.setInterval(10)
        timer.timeout.connect(lambda: (gaps.append(clock.elapsed() - last[0]), last.__setitem__(0, clock.elapsed())))
        timer.start()
        qtbot.wait(duration_ms)
        timer.stop()
        return max(gaps)

    baseline = largest_gap(1000)
    window.outcome.open_example(D08)
    # Opening posts the window's repaint. Left in the window it becomes the first tick's gap, 4 ms alone and about
    # 250 ms against the worker's GIL, which measures that paint instead of the loop's answers during the compute.
    QApplication.processEvents()
    during = largest_gap(2500)
    print(f"largest GUI tick gap: idle {baseline} ms, during compute {during} ms")
    assert (len(shell.calls), finished) == (1, []), "the whole measurement must lie inside the synthetic compute"
    assert during < 100


@pytest.mark.req("REQ-N-18")
def test_ui12_an_engine_exception_shows_an_english_dialog_saves_the_project_and_logs_a_correlation_id(
    make_shell, qtbot, tmp_path, wait_ready
):
    """Catches a crash that kills the app, loses the project, or leaves a log line nobody can match to the dialog."""
    log_path = tmp_path / "embodic.log"
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(RedactingFormatter())
    logging.getLogger("embodic").addHandler(handler)
    try:

        def explode(design, provenance, **kwargs):
            raise RuntimeError("injected engine fault")

        shell = make_shell(compute_fn=explode)
        window = shell.window
        window.outcome.open_example(D08)
        qtbot.waitUntil(lambda: isinstance(window.outcome.state.value, OutcomeFailed), timeout=10_000)
        correlation_id = window.outcome.state.value.correlation_id
        dialog = window.findChild(QMessageBox, "dlg-error")
        assert dialog is not None and dialog.isVisible()
        assert dialog.windowTitle() == "Internal error"
        assert correlation_id in dialog.text() and "The program keeps running." in dialog.text()
        saved = shell.recovery_dir / f"recovery-{correlation_id}.embodic.json"
        loaded, issues = load_project(saved)
        assert issues == () and isinstance(loaded, ProjectFile)
        assert loaded.design == window.outcome.project.design
        handler.flush()
        log = log_path.read_text(encoding="utf-8")
        assert f"[{correlation_id}]" in log and "RuntimeError: injected engine fault" in log
        assert str(Path.home()) not in log

        shell.worker.compute_fn = compute
        dialog.accept()
        window.outcome.compute_now()
        wait_ready(window)
        assert isinstance(window.outcome.state.value, OutcomeReady)
    finally:
        logging.getLogger("embodic").removeHandler(handler)
        handler.close()


@pytest.mark.req("REQ-N-18")
def test_ui12_log_lines_replace_the_home_folder_with_a_placeholder():
    """Catches a traceback path that writes the user's account name into the log file."""
    record = logging.LogRecord("embodic", logging.ERROR, __file__, 1, "%s", (str(Path.home() / "x.py"),), None)
    line = RedactingFormatter().format(record)
    assert "%USERPROFILE%" in line and str(Path.home()) not in line and "[-]" in line


@pytest.mark.req("REQ-N-18")
def test_ui12_an_exception_in_a_gui_slot_also_saves_and_explains(d08_shell, monkeypatch):
    """Catches a GUI-thread exception (outside the worker) that is printed to a console nobody sees."""
    monkeypatch.setattr(sys, "excepthook", sys.excepthook)
    window = d08_shell.window
    install_crash_handler(window)
    try:
        raise ValueError("injected slot fault")
    except ValueError as error:
        sys.excepthook(type(error), error, error.__traceback__)
    dialog = window.findChild(QMessageBox, "dlg-error")
    assert dialog is not None and dialog.isVisible()
    saved = sorted(d08_shell.recovery_dir.glob("recovery-*.embodic.json"))
    assert len(saved) == 1 and saved[0].stem.removeprefix("recovery-").removesuffix(".embodic") in dialog.text()
