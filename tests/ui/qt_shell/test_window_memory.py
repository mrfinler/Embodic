"""DEF-U-M6f-01: a closed shell window must give back its widgets and its memory.

Before U-M6f every window of the test session stayed alive: about 49 MiB and 2650 widgets each on 28f4c39, and each new
window repolished all of them, so the commit gate on cb08153 reached 4.5 GB and was killed by the memory limit.
"""

import gc
from pathlib import Path

import pytest
import shiboken6
from PySide6.QtCore import QCoreApplication, QEvent, QSettings, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

from embodic.ui.app import QSettingsStore, create_shell
from embodic.ui.views.main_window import ShellPaths

WINDOWS = 20
# A leaked window cost 48.7 MiB on 28f4c39 (12.3 MiB on f07d502) and its detached inspector forms alone about 35 MiB.
# Without a leak, RSS grew 0.1 MiB from the second to the twentieth window (U-M6f report); 20 MiB is under one leak.
RSS_GROWTH_BOUND_MIB = 20.0
STATUS = Path("/proc/self/status")

_previous_test_window = []


def rss_mib() -> float:
    """Return the resident set size of this process from /proc, after Python freed its unreachable cycles."""
    gc.collect()
    for line in STATUS.read_text(encoding="ascii").splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1]) / 1024
    raise AssertionError("no VmRSS line in /proc/self/status")


def open_and_close(app: QApplication, folder: Path) -> None:
    """Open a shell window and close it the way a test's teardown does: close, deleteLater, deliver the delete."""
    store = QSettingsStore(QSettings(str(folder / "settings.ini"), QSettings.Format.IniFormat))
    window, _ = create_shell(store, ShellPaths(recovery_dir=folder / "recovery"), prefers_dark=lambda: False)
    window.resize(1280, 800)
    window.show()
    app.processEvents()
    window.close()
    window.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


@pytest.mark.req("REQ-N-02")
@pytest.mark.skipif(not STATUS.exists(), reason="reads VmRSS from /proc")
def test_closed_windows_leave_no_widget_and_no_memory_behind(qapp, tmp_path):
    """Catches a closed window whose widgets survive: its detached inspector forms (1841 widgets each on 28f4c39)."""
    before = len(QApplication.allWidgets())
    open_and_close(qapp, tmp_path / "w0")
    open_and_close(qapp, tmp_path / "w1")
    warm = rss_mib()
    for index in range(2, WINDOWS):
        open_and_close(qapp, tmp_path / f"w{index}")
        assert len(QApplication.allWidgets()) == before, f"window {index + 1}"
        gc.collect()  # garbage left to pile up stays as heap the next window does not reuse, a high-water mark
    assert rss_mib() - warm < RSS_GROWTH_BOUND_MIB


@pytest.mark.req("REQ-N-27")
def test_an_os_scheme_change_reaches_no_deleted_window(qapp, tmp_path):
    """Catches a scheme connection that outlives its window: a lambda kept it and called into the deleted window."""
    open_and_close(qapp, tmp_path)
    QGuiApplication.styleHints().colorSchemeChanged.emit(Qt.ColorScheme.Dark)


@pytest.mark.req("REQ-N-02")
def test_a_window_a_test_opened_is_open(make_shell):
    """First half of the pair below: keep the window this test opened, which pytest-qt closes at teardown."""
    _previous_test_window.append(make_shell().window)
    assert shiboken6.isValid(_previous_test_window[0])


@pytest.mark.req("REQ-N-02")
def test_the_window_of_the_previous_test_is_deleted():
    """Catches a teardown that closes a window without deleting it: pytest-qt's deleteLater was never delivered."""
    assert len(_previous_test_window) == 1, "runs after test_a_window_a_test_opened_is_open"
    assert not shiboken6.isValid(_previous_test_window.pop())
