"""D-053a: the session checks the stack-up generator inputs before it generates (ruling item 2). Qt-free."""

import math

import pytest

from embodic.errors import IssueCategory, Severity
from embodic.model.vocabulary import TopologyKind

pytestmark = pytest.mark.req("REQ-F-14", "REQ-F-32")


def enter(session, copper_count, copper_oz, board_thickness_mm):
    """Enter the three generator inputs in screen order."""
    session.set_stackup_input("copper_count", copper_count)
    session.set_stackup_input("copper_oz", copper_oz)
    session.set_stackup_input("board_thickness_mm", board_thickness_mm)


def layer_values(session):
    """Return every stack-up value of the open draft."""
    return {k: v for k, v in session.document.draft.values.items() if k.startswith("/stackup/layers")}


def test_a_board_thinner_than_its_copper_writes_nothing_and_holds_one_error(session):
    """Catches the generator being called on 8 x 2 oz in 0.4 mm, or a refusal that gives no message."""
    session.new_design(TopologyKind.SPIRAL)
    before = layer_values(session)
    enter(session, 8, 2.0, 0.4)
    assert layer_values(session) == before
    assert "/stackup/layers" in session.state.value.missing
    assert [(i.code, i.severity, i.value) for i in session.stackup_issues.value] == [
        ("INVALID_STACKUP_COPPER_EXCEEDS_BOARD", Severity.ERROR, 0.4)
    ]
    assert session.stackup_inputs().board_thickness_mm == 0.4


def test_correcting_the_board_thickness_clears_the_error_and_writes_the_stackup(session):
    """Catches an error that outlives its cause or pending inputs that the refusal threw away."""
    session.new_design(TopologyKind.SPIRAL)
    enter(session, 8, 2.0, 0.4)
    session.set_stackup_input("board_thickness_mm", 1.6)
    assert session.stackup_issues.value == ()
    values = session.document.draft.values
    assert [values[f"/stackup/layers/{i}/name"] for i in (0, 14)] == ["L1", "L8"]
    assert all(values[f"/stackup/layers/{i}/thickness_mm"] > 0.0 for i in range(1, 15, 2))


def test_opening_another_design_clears_the_error(session):
    """Catches a refusal message left under the board thickness of the next design."""
    session.new_design(TopologyKind.SPIRAL)
    enter(session, 8, 2.0, 0.4)
    session.new_design(TopologyKind.WAVE)
    assert session.stackup_issues.value == ()


@pytest.mark.parametrize(
    ("board_mm", "code"),
    [(0.15, "RANGE_BELOW_SUPPORTED"), (12.0, "RANGE_ABOVE_SUPPORTED"), (math.inf, "RANGE_ABOVE_SUPPORTED")],
)
def test_a_board_outside_the_supported_range_writes_nothing_and_holds_one_range_error(session, board_mm, code):
    """D-059d. Catches a board of 0.15 mm, 12 mm or infinity that the generator turns into a written stack-up."""
    session.new_design(TopologyKind.SPIRAL)
    before = layer_values(session)
    enter(session, 4, 1.0, board_mm)
    assert layer_values(session) == before
    assert [(i.code, i.category, i.severity, i.value) for i in session.stackup_issues.value] == [
        (code, IssueCategory.UNSUPPORTED_RANGE, Severity.ERROR, board_mm)
    ]
    assert session.stackup_inputs().board_thickness_mm == board_mm


@pytest.mark.parametrize("board_mm", [0.2, 10.0])
def test_a_board_at_an_end_of_the_range_is_written_and_a_correction_clears_the_range_error(session, board_mm):
    """D-059d. Catches an end of the range that is refused, and a range error left after the board is corrected."""
    session.new_design(TopologyKind.SPIRAL)
    enter(session, 4, 1.0, 0.15)
    session.set_stackup_input("board_thickness_mm", board_mm)
    assert session.stackup_issues.value == ()
    total = sum(v for k, v in layer_values(session).items() if k.endswith("/thickness_mm"))
    assert total == pytest.approx(board_mm)


def test_a_board_below_the_range_and_thinner_than_its_copper_holds_both_errors_range_first(session):
    """D-059d. Catches one refusal that hides the other: 4 x 1 oz is 0.1392 mm of copper, and the board is 0.1 mm."""
    session.new_design(TopologyKind.SPIRAL)
    enter(session, 4, 1.0, 0.1)
    assert [i.code for i in session.stackup_issues.value] == [
        "RANGE_BELOW_SUPPORTED",
        "INVALID_STACKUP_COPPER_EXCEEDS_BOARD",
    ]
    assert layer_values(session) == {}


@pytest.mark.parametrize(
    ("copper_oz", "board_mm", "code"), [(0.1, 1.6, "RANGE_BELOW_SUPPORTED"), (11.0, 5.0, "RANGE_ABOVE_SUPPORTED")]
)
def test_a_copper_weight_outside_its_limits_is_written_and_shows_the_issue_of_the_copper_field(
    session, copper_oz, board_mm, code
):
    """D-059d. Catches a copper weight whose range issue is lost on the way from the helper to the copper layers."""
    session.new_design(TopologyKind.SPIRAL)
    enter(session, 4, copper_oz, board_mm)
    assert session.stackup_issues.value == ()
    copper = [i for i in session.issues.value if i.pointers[0].startswith("/stackup/layers/")]
    assert {(i.code, i.category) for i in copper} == {(code, IssueCategory.UNSUPPORTED_RANGE)}
    assert sorted(i.pointers[0] for i in copper) == [f"/stackup/layers/{n}/thickness_mm" for n in (0, 2, 4, 6)]


@pytest.mark.parametrize("copper_oz", [0.25, 10.0])
def test_a_copper_weight_at_an_end_of_its_range_shows_no_issue(session, copper_oz):
    """Catches a copper range that the helper and the copper field read differently (an end refused by one only)."""
    session.new_design(TopologyKind.SPIRAL)
    enter(session, 4, copper_oz, 5.0)
    assert session.stackup_issues.value == ()
    assert [i for i in session.issues.value if i.pointers[0].startswith("/stackup/layers/")] == []
