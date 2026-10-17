"""REQ-N-15: every inspector form fits the inspector's width, since forms never scroll sideways.

A form's horizontal scroll bar is always off, so a form wider than its viewport is cut at the right edge without a
scroll bar to show it; the N-15 scroll-bar check cannot see that.
"""

import pytest
from PySide6.QtWidgets import QApplication

from .conftest import D08
from .test_centre_split import resize

pytestmark = pytest.mark.req("REQ-N-15")


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="DEF-U-M7c-02: the Board form needs 327 px in a 258 or 298 px viewport. Its unit column takes the 63 px "
    "of 'W/(m²·K)' on every row (ruling g 2) and a combo box needs 134 px, so a combo row needs 273 px. Every fix "
    "changes a ruled layout and waits for a design decision",
)
@pytest.mark.parametrize("size", [(960, 540), (1280, 800)])
def test_n15_every_inspector_form_is_as_narrow_as_its_viewport(make_shell, wait_ready, size):
    """Catches a form whose minimum width exceeds the inspector, which cuts its right edge (e68d5ff: tab-board)."""
    window = make_shell().window
    window.session.load_example(D08)
    wait_ready(window)
    resize(window, size)
    wider = {}
    for name, panel in window.panels.items():
        window.inspector_tabs.setCurrentWidget(panel)
        for _ in range(5):
            QApplication.processEvents()
        if panel.widget().width() > panel.viewport().width():
            wider[name] = (panel.widget().width(), panel.viewport().width())
    assert wider == {}
