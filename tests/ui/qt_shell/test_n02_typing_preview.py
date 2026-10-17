"""REQ-N-02: typing previews 300 ms after the last key; Enter, Tab and focus out commit; Esc reverts.

Rows N02-1 to N02-10 of docs/phase3/design/fix_wave_f1.md section (a). Field `param-r-inner` of D08 (11.47 mm).
"""

import dataclasses
import time

import pytest
from PySide6.QtCore import QElapsedTimer, Qt, QTimer
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QFileDialog, QLabel, QLineEdit, QToolButton
from tests.ui.qt_shell.conftest import D08

from embodic.api import compute
from embodic.errors import message_for
from embodic.io.project import load_project
from embodic.ui.viewmodels.outcome import OutcomeReady
from embodic.ui.viewmodels.session import AUTOSAVE_NAME, SessionComputed, SessionEmpty

SERPENTINE = "serpentine_16p_example"  # the packaged example that shows the check box field param-fillet-max
KEY_DELAY_MS = 50
DEBOUNCE_MS = 300
TOLERANCE_MS = 50
HANG_GUARD_S = 10.0


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


@pytest.fixture
def open_example(make_shell, wait_ready, qtbot):
    """Return a function: open_example(example_id, compute_fn) -> (shell, window), computed, with the calls cleared."""
    shells = []

    def run(example_id=D08, timed=None):
        shell = make_shell(compute_fn=timed)
        shells.append(shell)
        window = shell.window
        window.session.load_example(example_id)
        wait_ready(window)
        if timed is not None:
            timed.starts.clear()
            timed.tokens.clear()
        return shell, window

    yield run
    for shell in shells:
        shell.worker.shutdown()


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


@pytest.mark.req("REQ-N-02")
def test_n02_1_and_2_typing_previews_once_after_300_ms_and_return_commits_without_a_second_compute(open_example, qtbot):
    """N02-1, N02-2. Catches a compute per keystroke, or a commit after a preview that computes it again.

    The timer must preview: no undo entry, chip or autosave change before the commit.
    """
    timed = TimedCompute()
    shell, window = open_example(timed=timed)
    session = window.session
    chip = window.findChild(QLabel, "param-r-inner-prov")
    autosave = shell.recovery_dir / AUTOSAVE_NAME
    chip_before, saved_before = chip.text(), autosave.read_bytes()
    field = focus_field(qtbot, window)
    type_keys(qtbot, field, "11.48")
    last_key = timed.now()
    qtbot.wait(600)
    assert timed.r_inner() == [11.48]
    assert abs(timed.starts[0][0] - last_key - DEBOUNCE_MS) <= TOLERANCE_MS, timed.starts[0][0] - last_key
    assert (chip.text(), autosave.read_bytes()) == (chip_before, saved_before)
    assert r_inner_of(session.state.value) == 11.47

    qtbot.keyClick(field, Qt.Key.Key_Return)
    qtbot.wait(DEBOUNCE_MS + 100)
    assert len(timed.starts) == 1, "the commit after the preview must reuse the preview's request"
    assert chip.text() == "user"
    assert r_inner_of(session.state.value) == 11.48
    session.undo()
    assert r_inner_of(session.state.value) == 11.47, "the commit is one undo entry"
    session.undo()
    assert isinstance(session.state.value, SessionEmpty), "the preview wrote no undo entry"


@pytest.mark.req("REQ-N-02")
def test_n02_3_return_before_the_timer_computes_at_once_and_only_once(open_example, qtbot):
    """N02-3. Catches Enter that waits for the timer, or a timer left running that computes a second time."""
    timed = TimedCompute()
    _, window = open_example(timed=timed)
    field = focus_field(qtbot, window)
    type_keys(qtbot, field, "11.49")
    qtbot.wait(100)
    pressed = timed.now()
    qtbot.keyClick(field, Qt.Key.Key_Return)
    qtbot.wait(DEBOUNCE_MS + 200)
    assert timed.r_inner() == [11.49]
    assert timed.starts[0][0] - pressed <= TOLERANCE_MS, timed.starts[0][0] - pressed


@pytest.mark.req("REQ-N-02", "REQ-F-37")
def test_n02_4_text_that_is_no_number_never_computes_and_shows_its_message_only_at_commit(open_example, qtbot):
    """N02-4. Catches a preview of an unparsable value, or a field error shown while the user is still typing."""
    timed = TimedCompute()
    _, window = open_example(timed=timed)
    field = focus_field(qtbot, window)
    error = window.findChild(QLabel, "param-r-inner-error")
    type_keys(qtbot, field, "abc")
    qtbot.wait(600)
    assert timed.starts == []
    assert not error.isVisibleTo(window)
    qtbot.keyClick(field, Qt.Key.Key_Return)
    qtbot.waitUntil(lambda: error.isVisibleTo(window))
    assert error.text() == message_for("INVALID_TYPE")
    assert field.property("invalid") == "true"
    assert timed.starts == []


@pytest.mark.req("REQ-N-02")
def test_n02_5_esc_before_the_timer_puts_the_committed_text_back_and_keeps_focus(open_example, qtbot):
    """N02-5. Catches Esc that leaves the typed text, lets the timer compute it, or moves focus away."""
    timed = TimedCompute()
    _, window = open_example(timed=timed)
    field = focus_field(qtbot, window)
    type_keys(qtbot, field, "12")
    qtbot.wait(100)
    qtbot.keyClick(field, Qt.Key.Key_Escape)
    qtbot.wait(600)
    assert timed.starts == []
    assert field.text() == "11.47"
    assert QApplication.focusWidget() is field
    assert r_inner_of(window.session.state.value) == 11.47


@pytest.mark.req("REQ-N-02")
def test_n02_6_esc_after_a_preview_brings_the_committed_results_back(open_example, qtbot):
    """N02-6. Catches a preview left on screen after Esc, or an Esc that writes an undo entry."""
    timed = TimedCompute()
    _, window = open_example(timed=timed)
    session = window.session
    value = window.findChild(QLabel, "res-ke-value")
    committed = value.text()
    field = focus_field(qtbot, window)
    type_keys(qtbot, field, "12")
    qtbot.waitUntil(lambda: drawn_r_inner(window) == 12.0)
    qtbot.keyClick(field, Qt.Key.Key_Escape)
    qtbot.waitUntil(lambda: drawn_r_inner(window) == 11.47)
    assert value.text() == committed
    assert field.text() == "11.47"
    session.undo()
    assert isinstance(session.state.value, SessionEmpty), "Esc wrote no undo entry"


@pytest.mark.req("REQ-N-02")
def test_n02_7_a_keystroke_cancels_the_preview_in_flight_at_once(open_example, qtbot):
    """N02-7. Catches a preview compute that runs on after a newer keystroke until the next timer expiry."""
    timed = TimedCompute(block=lambda design: design.winding.coil.r_inner_mm != 11.47)
    _, window = open_example(timed=timed)
    field = focus_field(qtbot, window)
    type_keys(qtbot, field, "12")
    qtbot.wait(400)
    assert timed.r_inner() == [12.0], "precondition: the preview of 12 is in flight"
    qtbot.keyClick(field, Qt.Key.Key_3)
    key = timed.now()
    qtbot.waitUntil(lambda: timed.tokens[0].cancelled, timeout=1000)
    qtbot.waitUntil(lambda: bool(timed.cancelled_at), timeout=1000)
    assert timed.cancelled_at[0] - key <= TOLERANCE_MS, timed.cancelled_at[0] - key
    qtbot.wait(600)
    assert timed.r_inner() == [12.0, 123.0]
    assert abs(timed.starts[1][0] - key - DEBOUNCE_MS) <= TOLERANCE_MS, timed.starts[1][0] - key
    qtbot.keyClick(field, Qt.Key.Key_Escape)


@pytest.mark.req("REQ-N-02")
@pytest.mark.parametrize(
    ("example_id", "tab", "name", "key"),
    [
        (D08, "tab-board", "param-modulation", Qt.Key.Key_Down),
        (SERPENTINE, "tab-coil", "param-fillet-max", Qt.Key.Key_Space),
    ],
)
def test_n02_8_a_choice_control_commits_and_computes_at_once_without_a_timer(
    open_example, qtbot, example_id, tab, name, key
):
    """N02-8. Catches a combo box or check box that waits for the typing timer before it computes."""
    timed = TimedCompute()
    _, window = open_example(example_id, timed=timed)
    window.inspector_tabs.setCurrentWidget(window.panels[tab])
    control = window.findChild(QComboBox if key == Qt.Key.Key_Down else QCheckBox, name)
    control.setFocus(Qt.FocusReason.TabFocusReason)
    qtbot.waitUntil(control.hasFocus)
    pressed = timed.now()
    qtbot.keyClick(control, key)
    qtbot.waitUntil(lambda: bool(timed.starts), timeout=1000)
    assert timed.starts[0][0] - pressed <= TOLERANCE_MS, timed.starts[0][0] - pressed
    timer = window.findChild(QTimer, "preview-timer")
    assert timer is not None and not timer.isActive()
    qtbot.wait(DEBOUNCE_MS + 100)
    assert len(timed.starts) == 1


@pytest.mark.req("REQ-N-02")
def test_n02_9_toolstrip_save_while_a_field_holds_typed_text_saves_the_typed_value(
    open_example, qtbot, tmp_path, monkeypatch
):
    """N02-9, DEF-US11-03. Catches Save that writes the committed design while the field still holds typed text."""
    _, window = open_example()
    path = tmp_path / "saved.embodic.json"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args, **kwargs: (str(path), ""))
    window.save_project_dialog()
    assert load_project(path)[0].design.winding.coil.r_inner_mm == 11.47, "precondition: the first save"
    field = focus_field(qtbot, window)
    type_keys(qtbot, field, "11.5")
    save = window.toolstrip.findChild(QToolButton, "act-save")
    qtbot.mouseClick(save, Qt.MouseButton.LeftButton)
    assert QApplication.focusWidget() is field, "precondition: the click left the focus in the field"
    assert load_project(path)[0].design.winding.coil.r_inner_mm == 11.5


@pytest.mark.req("REQ-N-02")
def test_n02_9_compute_and_undo_from_the_toolstrip_commit_the_typed_text_first(open_example, qtbot):
    """DEF-US11-03. Catches Undo that skips the typed edit, and Compute that computes the committed design."""
    timed = TimedCompute()
    _, window = open_example(timed=timed)
    session = window.session
    field = focus_field(qtbot, window)
    type_keys(qtbot, field, "11.7")
    window.toolstrip.actions_by_id["act-compute"].trigger()
    assert isinstance(session.state.value, SessionComputed)
    assert r_inner_of(session.state.value) == 11.7
    type_keys(qtbot, field, "1")
    window.toolstrip.actions_by_id["act-undo"].trigger()
    assert r_inner_of(session.state.value) == 11.7, "Undo after the commit returns the value before the typing"


@pytest.mark.slow
@pytest.mark.req("REQ-N-02")
def test_n02_10_keystroke_echo_while_a_preview_result_arrives(open_example, qtbot):
    """N02-10. Measures the largest gap between 10 ms GUI ticks while typing over a preview result (nightly only).

    The compute of the 11.6 preview returns after 200 ms with a result computed beforehand, so the result lands
    about when the next keys are typed. The 100 ms bound is REQ-N-02's input-echo threshold (assumption). A fail
    belongs to U-M8a's stall work, not to the debounce.
    """
    precomputed = {}

    def returns_after_200_ms(design, provenance, *, cache, cancel):
        if design.winding.coil.r_inner_mm != 11.6:
            return compute(design, provenance, cache=cache, cancel=cancel)
        time.sleep(0.2)
        return precomputed["11.6"]

    _, window = open_example(timed=TimedCompute())
    window.outcome._submitter.compute_fn = returns_after_200_ms
    preview = dataclasses.replace(
        window.session.state.value.design,
        winding=dataclasses.replace(
            window.session.state.value.design.winding,
            coil=dataclasses.replace(window.session.state.value.design.winding.coil, r_inner_mm=11.6),
        ),
    )
    precomputed["11.6"] = compute(preview, window.session.state.value.provenance)
    clock = QElapsedTimer()
    clock.start()
    arrived = []
    window.outcome.state.subscribe(
        lambda state: (
            arrived.append((clock.elapsed(), r_inner_of(state.outcome))) if isinstance(state, OutcomeReady) else None
        )
    )
    field = focus_field(qtbot, window)
    type_keys(qtbot, field, "11.6")
    qtbot.wait(450)
    gaps, last = [], [clock.elapsed()]
    ticker = QTimer()
    ticker.setInterval(10)
    ticker.timeout.connect(lambda: (gaps.append(clock.elapsed() - last[0]), last.__setitem__(0, clock.elapsed())))
    ticker.start()
    started = clock.elapsed()
    type_keys(qtbot, field, "12345")
    qtbot.wait(100)
    ticker.stop()
    print(
        f"N02-10 largest GUI tick gap {max(gaps)} ms; window {started} to {clock.elapsed()} ms; "
        f"results set (ms, r_inner): {arrived}"
    )
    assert max(gaps) <= 100
