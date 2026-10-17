"""The preview timer of a window: typing previews 300 ms after the last keystroke (REQ-N-02, fix_wave_f1.md (a))."""

from collections.abc import Callable

from PySide6.QtCore import QObject, QTimer

DEBOUNCE_MS = 300  # REQ-N-02; an assumption until a user study or the Windows timing run measures it


class QtDebounce(QObject):
    """Implements the session's Debounce with one single-shot QTimer; ``start`` restarts a running timer."""

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.setObjectName("preview-timer")
        self.timer.setSingleShot(True)
        self.timer.setInterval(DEBOUNCE_MS)
        self.timer.timeout.connect(self._fire)
        self._action: Callable[[], None] | None = None

    def start(self, action: Callable[[], None]) -> None:
        """Wait 300 ms again, then run ``action``."""
        self._action = action
        self.timer.start()

    def stop(self) -> None:
        """Stop the wait; its action never runs."""
        self.timer.stop()
        self._action = None

    def _fire(self) -> None:
        action, self._action = self._action, None
        if action is not None:
            action()
