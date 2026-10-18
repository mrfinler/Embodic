"""Shared helpers of the field typing and stepping tests (N02 rows of fix_wave_f1.md, S rows of fix_wave_f2.md).

A wall-clock margin that load can eat is not a contract. A test that needs the 300 ms preview timer not to fire, or
to fire once, takes the timer under control instead: `hold_preview_timer` stretches its interval so it cannot expire
by itself, and `expire` ends the wait at the moment the test chooses (U-M8f, the U-M8c follow-up).
"""

import time

from PySide6.QtCore import QElapsedTimer, Qt, QTimer
from PySide6.QtWidgets import QLineEdit

from embodic.api import compute
from embodic.ui.viewmodels.outcome import OutcomeReady

KEY_DELAY_MS = 50
DEBOUNCE_MS = 300
TOLERANCE_MS = 50
HANG_GUARD_S = 10.0
HELD_MS = 600_000  # a preview timer held this long cannot expire inside a test
WAIT_TIMEOUT_MS = 10_000  # hang guard only; no assertion depends on it


class TimedCompute:
    """A compute function that records when each call starts, its design and its cancel token."""

    def __init__(self, block=None):
        self.clock = QElapsedTimer()
        self.clock.start()
        self.starts: list[tuple[int, object]] = []
        self.tokens: list[object] = []
        self.cancelled_at: list[int] = []
        self._block = block or (lambda design: False)

    def __call__(self, design, provenance, *, cache, cancel):
        """Record the call, then block until cancelled or compute."""
        self.starts.append((self.clock.elapsed(), design))
        self.tokens.append(cancel)
        if self._block(design):
            end = time.monotonic() + HANG_GUARD_S
            while not cancel.cancelled and time.monotonic() < end:
                time.sleep(0.001)
            self.cancelled_at.append(self.clock.elapsed())
            return None
        return compute(design, provenance, cache=cache, cancel=cancel)

    def now(self) -> int:
        """Return milliseconds since the test started."""
        return self.clock.elapsed()

    def r_inner(self) -> list[float]:
        """Return r_inner of every call's design, in call order."""
        return [round(design.winding.coil.r_inner_mm, 6) for _, design in self.starts]


def r_inner_of(state) -> float:
    """Return r_inner of a session state or an outcome."""
    return state.design.winding.coil.r_inner_mm


def drawn_r_inner(window) -> float | None:
    """Return r_inner of the outcome the window draws and shows results for, once no compute runs."""
    shown, _ = window.session.drawn(window.outcome.state.value)
    if shown is None or not isinstance(window.outcome.state.value, OutcomeReady):
        return None
    return r_inner_of(shown.outcome)


def focus_field(qtbot, window, name="param-r-inner") -> QLineEdit:
    """Focus a field row's line edit, with its text selected, as a click into it and Ctrl+A do."""
    field = window.findChild(QLineEdit, name)
    field.setFocus(Qt.FocusReason.MouseFocusReason)
    qtbot.waitUntil(field.hasFocus)
    field.selectAll()
    return field


def type_keys(qtbot, field, keys: str) -> None:
    """Type keys at the pace of fix_wave_f1.md (a), one every 50 ms."""
    qtbot.keyClicks(field, keys, delay=KEY_DELAY_MS)


def hold_preview_timer(window) -> QTimer:
    """Stretch the window's preview timer so that it cannot expire by itself; return it."""
    timer = window.findChild(QTimer, "preview-timer")
    assert timer is not None and timer.interval() == DEBOUNCE_MS, "REQ-N-02: the wait is 300 ms"
    timer.setInterval(HELD_MS)
    return timer


def expire(timer: QTimer) -> None:
    """End the wait of a held preview timer now, as its single shot does: stop it, then emit its timeout."""
    assert timer.isActive(), "a keystroke or a step starts the wait"
    timer.stop()
    timer.timeout.emit()
