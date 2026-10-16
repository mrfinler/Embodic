"""D-053a: the board thickness field shows the refusal of a board thinner than its copper (ruling item 2)."""

import pytest
from tests.ui.qt_design.conftest import enter, find
from tests.ui.qt_design.test_editing import no_compute

from embodic.model.vocabulary import TopologyKind

pytestmark = pytest.mark.req("REQ-F-14", "REQ-F-32")


def test_board_thickness_shows_the_refusal_until_the_board_is_thick_enough(make_shell, qtbot):
    """Catches a refusal the user cannot see, one shown at another field, or one left after the fix."""
    window = make_shell(compute_fn=no_compute).window
    window.session.new_design(TopologyKind.SPIRAL)
    window.inspector_tabs.setCurrentWidget(window.panels["tab-board"])
    panel = window.panels["tab-board"]
    enter(qtbot, window, "param-layer-count", 8)
    enter(qtbot, window, "param-copper-weight", "2")
    enter(qtbot, window, "param-board-thickness", "0.4")
    error = find(window, "param-board-thickness-error")
    assert error.isVisibleTo(panel)
    assert error.text() == (
        "Board thickness must exceed the total copper thickness of 0.5568 mm, "
        "so that every dielectric layer is thicker than 0."
    )
    assert "/stackup/layers/0/kind" not in window.session.document.draft.values

    enter(qtbot, window, "param-board-thickness", "1.6")
    assert not error.isVisibleTo(panel)
    assert window.session.document.draft.values["/stackup/layers/14/name"] == "L8"
