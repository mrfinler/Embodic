"""Visible focus indicator on every focusable control of the shell (AX-03, REQ-N-12)."""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget

from embodic.ui.theme import ThemeName


def _focusable(window):
    """Return the visible controls that take focus themselves (a widget with a focus proxy hands it on)."""
    return [
        w
        for w in window.findChildren(QWidget)
        if w.isVisible() and w.isEnabled() and w.focusPolicy() & Qt.FocusPolicy.TabFocus and w.focusProxy() is None
    ]


def _ring_pixels(widget, ring):
    image = widget.grab().toImage()
    return sum(
        1 for x in range(image.width()) for y in range(image.height()) if image.pixelColor(x, y).rgb() == ring.rgb()
    )


@pytest.mark.req("REQ-N-12")
@pytest.mark.parametrize("theme", [ThemeName.LIGHT, ThemeName.DARK])
def test_ax03_every_focusable_control_shows_a_focus_ring(d08_shell, qtbot, theme):
    """Catches a control whose focused look equals its unfocused look (screenshot diff, focused vs unfocused).

    The ring must add at least twice the control's shorter side in ring-coloured pixels: a 2 px ring around the
    focused part (a button, the current tab, the canvas edge) adds far more, a caret or a dotted line does not.
    """
    window = d08_shell.window
    window.appearance.set_theme(theme)
    window.activateWindow()
    qtbot.waitUntil(window.isActiveWindow)
    ring = QColor(window.tokens.colours["focus-ring"])
    controls = _focusable(window)
    names = {w.objectName() or type(w).__name__ for w in controls}
    assert {"fig-canvas", "act-save", "toolstrip-tabs", "layer-L1"} <= names
    parking = window.canvas
    missing = []
    for widget in controls:
        other = parking if widget is not parking else window.layer_boxes["L1"]
        other.setFocus(Qt.FocusReason.TabFocusReason)
        qtbot.waitUntil(other.hasFocus)
        before = _ring_pixels(widget, ring)
        widget.setFocus(Qt.FocusReason.TabFocusReason)
        qtbot.waitUntil(widget.hasFocus)
        if _ring_pixels(widget, ring) - before < 2 * min(widget.width(), widget.height()):
            missing.append(widget.objectName() or f"{type(widget).__name__} in {widget.parent().objectName()}")
    assert missing == [], missing
