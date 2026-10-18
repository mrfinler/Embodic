"""REQ-N-02, UX-AC-22: in 300 ms the results update, or "Updating" shows with the previous values dimmed.

An edit takes effect at a commit or when the preview timer fires (fix_wave_f1.md section (a)). The contract for a
recompute that outlasts 300 ms is screens.md section 6: the status bar says "Updating" at once, the cards keep the
previous values, and `results-computing-veil` dims them to 60 % 300 ms after the compute starts. The dim timer is
held (its interval is stretched, then it is expired by hand), so no wall-clock margin decides a test. The default
example is `spiral_12c16p_default`, edited at `param-r-inner` (18 mm to 18.5 mm).
"""

import threading

import pytest
from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QLabel, QWidget

from embodic.api import compute
from embodic.ui.viewmodels.outcome import OutcomeComputing, OutcomeReady
from embodic.ui.views import results_view

from .typing_support import (
    HANG_GUARD_S,
    HELD_MS,
    WAIT_TIMEOUT_MS,
    TimedCompute,
    drawn_r_inner,
    expire,
    focus_field,
    hold_preview_timer,
    type_keys,
)

DEFAULT = "spiral_12c16p_default"
EDITED_R_INNER_MM = 18.5
DIMMED_SHARE = 0.6  # screens.md section 6: the values read at 60 %


class GatedCompute(TimedCompute):
    """A compute function that computes at once while its gate is open and waits at it, in flight, while closed."""

    def __init__(self) -> None:
        super().__init__()
        self.gate = threading.Event()
        self.gate.set()

    def __call__(self, design, provenance, *, cache, cancel):
        """Record the call, wait at a closed gate, then compute."""
        self.starts.append((self.now(), design))
        self.tokens.append(cancel)
        self.gate.wait(HANG_GUARD_S)
        return compute(design, provenance, cache=cache, cancel=cancel)


def strongest_ink(window: QWidget, part: QWidget, fill: str) -> QColor:
    """Return the colour painted inside a part, over everything above it, that lies furthest from the fill."""
    image = window.grab(QRect(part.mapTo(window, part.rect().topLeft()), part.size())).toImage()
    background = QColor(fill).getRgb()[:3]
    painted = {image.pixel(x, y) for x in range(image.width()) for y in range(image.height())}
    return QColor(
        max(painted, key=lambda px: sum(abs(a - b) for a, b in zip(QColor(px).getRgb()[:3], background, strict=True)))
    )


def start_edit(qtbot, window, entry: str) -> None:
    """Type 18.5 into r_inner and make it take effect: Return commits it, expiring the held timer previews it."""
    preview = hold_preview_timer(window)
    field = focus_field(qtbot, window)
    type_keys(qtbot, field, str(EDITED_R_INNER_MM))
    if entry == "return":
        qtbot.keyClick(field, Qt.Key.Key_Return)
    else:
        expire(preview)


@pytest.mark.req("REQ-N-02")
@pytest.mark.parametrize("entry", ["return", "preview timer"])
def test_ux_ac_22_a_slow_recompute_says_updating_and_dims_the_previous_values_after_300_ms(
    open_example, qtbot, settle, entry
):
    """Catches an edit whose results sit undimmed and unlabelled while a slow recompute runs.

    The compute waits at a closed gate, so it is still in flight when the dim timer is expired. Before that the cards
    hold the previous values at full strength, as the contract says the dim comes 300 ms after the compute starts.
    """
    gated = GatedCompute()
    _, window = open_example(DEFAULT, timed=gated)
    window.show_results_tab("tab-results")
    tab = window.results_tab
    veil = window.findChild(QWidget, "results-computing-veil")
    value = tab.cards["ke"].value
    ink = window.tokens.colours
    dim = tab._dim
    assert dim.interval() == results_view.COMPUTING_DIM_AFTER_MS == 300, "UX-AC-22: 'Updating' dims at 300 ms"
    dim.setInterval(HELD_MS)
    settle()
    before, full = value.text(), strongest_ink(window, value, ink["bg-app"])
    assert full.name() == ink["text-1"], "precondition: the value prints in text-1 at full strength"

    gated.gate.clear()
    start_edit(qtbot, window, entry)
    qtbot.waitUntil(lambda: bool(gated.starts) and dim.isActive(), timeout=WAIT_TIMEOUT_MS)
    assert isinstance(window.outcome.state.value, OutcomeComputing)
    assert window.status["st-compute"].text() == "Updating"
    assert value.text() == before, "the previous values stay on the cards while the compute runs"
    assert veil.isHidden(), "the dim comes 300 ms after the compute starts, not at its start"

    expire(dim)
    settle()
    assert veil.isVisible()
    assert window.status["st-compute"].text() == "Updating"
    assert value.text() == before
    dimmed = strongest_ink(window, value, ink["bg-app"])
    share = [
        (d - f) / (t - f)
        for d, t, f in zip(dimmed.getRgb()[:3], full.getRgb()[:3], QColor(ink["bg-app"]).getRgb()[:3], strict=True)
        if t != f
    ]
    assert share and all(abs(s - DIMMED_SHARE) <= 0.02 for s in share), (dimmed.name(), full.name(), share)

    gated.gate.set()
    qtbot.waitUntil(lambda: isinstance(window.outcome.state.value, OutcomeReady), timeout=WAIT_TIMEOUT_MS)
    settle()
    assert drawn_r_inner(window) == EDITED_R_INNER_MM
    assert veil.isHidden(), "the dim ends with the compute"
    assert window.status["st-compute"].text() == "Ready"
    assert value.text() != before, "the arrival replaces the previous values with the edited design's"


@pytest.mark.req("REQ-N-02")
@pytest.mark.parametrize("entry", ["return", "preview timer"])
def test_ux_ac_22_a_result_that_arrives_before_the_dim_updates_the_values_and_never_dims_them(
    open_example, qtbot, settle, entry
):
    """Catches a result that lands but leaves "Updating" or the dim timer running, so the new values show dimmed.

    The dim timer is held and never expired, which is the case of a result inside the 300 ms: the dim must not start.
    """
    gated = GatedCompute()
    _, window = open_example(DEFAULT, timed=gated)
    window.show_results_tab("tab-results")
    tab = window.results_tab
    veil = window.findChild(QWidget, "results-computing-veil")
    value = tab.cards["ke"].value
    tab._dim.setInterval(HELD_MS)
    settle()
    before = value.text()

    start_edit(qtbot, window, entry)
    qtbot.waitUntil(lambda: drawn_r_inner(window) == EDITED_R_INNER_MM, timeout=WAIT_TIMEOUT_MS)
    settle()
    assert not tab._dim.isActive(), "the arrival cancels the pending dim"
    assert veil.isHidden()
    assert window.status["st-compute"].text() == "Ready"
    assert window.findChild(QLabel, "res-ke-value").text() != before
