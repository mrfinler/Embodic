"""Entry point of the desktop app `embodic`: QApplication, theme persistence, logging and the crash handler.

``python -m embodic.ui.app --smoke`` opens the window, loads the D08 example, computes, grabs the window and quits
with exit code 0 (``--screenshot-dir DIR`` also saves the light and dark window at 1280x800 and 960x540).
"""

import argparse
import logging
import logging.handlers
import sys
import time
import traceback
import uuid
from collections.abc import Callable, Sequence
from pathlib import Path
from types import TracebackType
from typing import NamedTuple

from PySide6.QtCore import QSettings, QStandardPaths, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

from embodic.api import compute
from embodic.results import load_registry
from embodic.ui.theme import ThemeName
from embodic.ui.viewmodels.appearance import AppearanceViewModel
from embodic.ui.viewmodels.outcome import OutcomeReady, OutcomeViewModel
from embodic.ui.viewmodels.session import AUTOSAVE_NAME, DesignSession
from embodic.ui.views.main_window import MainWindow, ShellPaths, redact_home
from embodic.ui.workers import ComputeFn, ComputeWorker

logger = logging.getLogger("embodic")

SETTINGS_ORG = "embodic"
SETTINGS_APP = "embodic"
THEME_KEY = "appearance/theme"
SMOKE_EXAMPLE = "spiral_12c10p_d08"
SCREEN_SIZES_PX = ((1280, 800), (960, 540))
SMOKE_TIMEOUT_S = 60.0


class QSettingsStore:
    """AppearanceStore on QSettings (organisation and application "embodic")."""

    def __init__(self, settings: QSettings | None = None) -> None:
        self._settings = settings or QSettings(SETTINGS_ORG, SETTINGS_APP)

    def load_theme(self) -> str | None:
        """Return the stored theme choice."""
        value = self._settings.value(THEME_KEY)
        return value if isinstance(value, str) else None

    def save_theme(self, value: str) -> None:
        """Store the theme choice and write it to disk."""
        self._settings.setValue(THEME_KEY, value)
        self._settings.sync()


class RedactingFormatter(logging.Formatter):
    """Log line with the correlation id; the home folder in paths and tracebacks becomes a placeholder."""

    def __init__(self) -> None:
        super().__init__("%(asctime)s %(levelname)s [%(correlation_id)s] %(name)s: %(message)s")

    def format(self, record: logging.LogRecord) -> str:
        """Format the record, with '-' when it carries no correlation id."""
        if not hasattr(record, "correlation_id"):
            record.correlation_id = "-"
        return redact_home(super().format(record))


def app_data_dir() -> Path:
    """Return the per-user data folder Qt names for this app (no hard-coded user path)."""
    return Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))


def setup_logging(log_dir: Path) -> Path:
    """Send the app's log to ``log_dir/embodic.log`` (rotating) and return the file."""
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / "embodic.log"
    handler = logging.handlers.RotatingFileHandler(path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(RedactingFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return path


def os_prefers_dark() -> bool:
    """Return True when the OS colour scheme is dark."""
    return QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark


class Shell(NamedTuple):
    """The window and the compute worker behind it."""

    window: MainWindow
    worker: ComputeWorker


def create_shell(
    store: QSettingsStore,
    paths: ShellPaths,
    compute_fn: ComputeFn = compute,
    prefers_dark: Callable[[], bool] = os_prefers_dark,
) -> Shell:
    """Wire the view-models, the worker and the window."""
    worker = ComputeWorker(compute_fn)
    outcome = OutcomeViewModel(worker)
    session = DesignSession(outcome, autosave_path=paths.recovery_dir / AUTOSAVE_NAME)
    window = MainWindow(
        AppearanceViewModel(store), outcome, session, paths, prefers_dark, worker.shutdown, registry=load_registry()
    )
    worker.setParent(window)
    worker.finished.connect(outcome.on_finished)
    worker.failed.connect(window.on_compute_failed)
    QGuiApplication.styleHints().colorSchemeChanged.connect(lambda _scheme: window.on_os_scheme_changed())
    return Shell(window, worker)


def unrecovered_autosave(paths: ShellPaths) -> Path | None:
    """Return the autosave a previous run left behind (it exits cleanly only after deleting it), or None."""
    autosave = paths.recovery_dir / AUTOSAVE_NAME
    return autosave if autosave.exists() else None


def install_crash_handler(window: MainWindow) -> None:
    """Route an exception that escapes a GUI-thread slot to the log, the recovery save and the error dialog."""

    def handle(kind: type[BaseException], error: BaseException, tb: TracebackType | None) -> None:
        correlation_id = uuid.uuid4().hex[:12]
        text = "".join(traceback.format_exception(kind, error, tb))
        logger.error("unhandled exception\n%s", text, extra={"correlation_id": correlation_id})
        window.report_internal_error(correlation_id)

    sys.excepthook = handle


def _wait_for_result(app: QApplication, window: MainWindow) -> bool:
    deadline = time.monotonic() + SMOKE_TIMEOUT_S
    while not isinstance(window.outcome.state.value, OutcomeReady) and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    return isinstance(window.outcome.state.value, OutcomeReady)


def run_smoke(app: QApplication, window: MainWindow, screenshot_dir: Path | None) -> int:
    """Open, load D08, compute, grab, quit; 0 when the window showed a computed outcome."""
    window.resize(*SCREEN_SIZES_PX[0])
    window.show()
    window.session.load_example(SMOKE_EXAMPLE)
    if not _wait_for_result(app, window) or window.grab().isNull():
        logger.error("smoke run: no computed outcome within %.0f s", SMOKE_TIMEOUT_S)
        return 1
    if screenshot_dir is not None:
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        chosen = window.appearance.theme.value
        for theme in (ThemeName.LIGHT, ThemeName.DARK):
            window.appearance.set_theme(theme)
            for width, height in SCREEN_SIZES_PX:
                window.resize(width, height)
                app.processEvents()
                window.canvas.fit_view()
                app.processEvents()
                window.grab().save(str(screenshot_dir / f"shell_{theme.value}_{width}x{height}.png"))
        window.appearance.set_theme(chosen)
    window.close()
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Start the desktop app."""
    parser = argparse.ArgumentParser(prog="embodic", description="Design PCB stator coils.")
    parser.add_argument("--smoke", action="store_true", help="open, load the D08 example, compute, grab and quit")
    parser.add_argument("--screenshot-dir", type=Path, default=None, help="with --smoke: save window screenshots")
    args = parser.parse_args(argv)
    app = QApplication.instance() or QApplication(sys.argv[:1])
    assert isinstance(app, QApplication)
    app.setOrganizationName(SETTINGS_ORG)
    app.setApplicationName(SETTINGS_APP)
    data_dir = app_data_dir()
    setup_logging(data_dir / "logs")
    paths = ShellPaths(recovery_dir=data_dir / "recovery")
    autosave = unrecovered_autosave(paths)
    window = create_shell(QSettingsStore(), paths).window
    install_crash_handler(window)
    if args.smoke:
        return run_smoke(app, window, args.screenshot_dir)
    window.resize(1280, 800)
    window.show()
    if autosave is not None:
        window.offer_recovery(autosave)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
