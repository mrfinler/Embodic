"""D-053a: the board thickness field shows the refusal of a board thinner than its copper (ruling item 2)."""

import pytest
from tests.ui.qt_design.conftest import enter, find
from tests.ui.qt_design.test_editing import issue_item, no_compute

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


def board_tab(make_shell):
    """Open a blank spiral design on the Board tab with a window that computes nothing."""
    window = make_shell(compute_fn=no_compute).window
    window.session.new_design(TopologyKind.SPIRAL)
    panel = window.panels["tab-board"]
    window.inspector_tabs.setCurrentWidget(panel)
    return window, panel


def test_board_thickness_outside_0p2_to_10_mm_shows_the_range_refusal_until_it_is_corrected(make_shell, qtbot):
    """D-059d. Catches a 0.15 mm or 12 mm board that is written, an unseen refusal, or one left after the fix."""
    window, panel = board_tab(make_shell)
    enter(qtbot, window, "param-layer-count", 4)
    enter(qtbot, window, "param-copper-weight", "1")
    error = find(window, "param-board-thickness-error")

    enter(qtbot, window, "param-board-thickness", "0.15")
    assert error.isVisibleTo(panel)
    assert error.text() == "The value is below the supported minimum of 0.2 mm."
    assert "/stackup/layers/0/kind" not in window.session.document.draft.values

    enter(qtbot, window, "param-board-thickness", "12")
    assert error.text() == "The value is above the supported maximum of 10 mm."
    assert "/stackup/layers/0/kind" not in window.session.document.draft.values

    enter(qtbot, window, "param-board-thickness", "1.6")
    assert not error.isVisibleTo(panel)
    assert window.session.document.draft.values["/stackup/layers/6/name"] == "L4"


@pytest.mark.parametrize("board", ["0.2", "10"])
def test_board_thickness_at_an_end_of_the_range_is_accepted(make_shell, qtbot, board):
    """D-059d. Catches an end of the range that a commit refuses while a step stops on it (B-6, B-8)."""
    window, panel = board_tab(make_shell)
    enter(qtbot, window, "param-layer-count", 4)
    enter(qtbot, window, "param-copper-weight", "1")
    enter(qtbot, window, "param-board-thickness", board)
    assert not find(window, "param-board-thickness-error").isVisibleTo(panel)
    assert window.session.document.draft.values["/stackup/layers/6/name"] == "L4"


def test_a_board_below_the_range_and_thinner_than_its_copper_shows_both_refusals_one_per_line(make_shell, qtbot):
    """D-059d. Catches a second refusal that hides the first: 4 x 1 oz copper is 0.1392 mm and the board is 0.1 mm."""
    window, _ = board_tab(make_shell)
    enter(qtbot, window, "param-layer-count", 4)
    enter(qtbot, window, "param-copper-weight", "1")
    enter(qtbot, window, "param-board-thickness", "0.1")
    assert find(window, "param-board-thickness-error").text().split("\n") == [
        "The value is below the supported minimum of 0.2 mm.",
        "Board thickness must exceed the total copper thickness of 0.1392 mm, "
        "so that every dielectric layer is thicker than 0.",
    ]


@pytest.mark.parametrize(
    ("copper_oz", "board", "code", "text"),
    [
        ("0.1", "1.6", "RANGE_BELOW_SUPPORTED", "The value is below the supported minimum of 0.0087 mm."),
        ("11", "5", "RANGE_ABOVE_SUPPORTED", "The value is above the supported maximum of 0.348 mm."),
    ],
)
def test_a_copper_weight_outside_its_limits_lists_the_issue_of_the_copper_field(
    make_shell, qtbot, copper_oz, board, code, text
):
    """D-059d. Catches a copper weight outside 0.25 to 10 oz that the form accepts without any issue."""
    window, _ = board_tab(make_shell)
    enter(qtbot, window, "param-layer-count", 4)
    enter(qtbot, window, "param-copper-weight", copper_oz)
    enter(qtbot, window, "param-board-thickness", board)
    assert issue_item(window, code).text() == text
