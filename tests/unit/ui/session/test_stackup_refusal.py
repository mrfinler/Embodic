"""D-053a: the session checks the stack-up generator inputs before it generates (ruling item 2). Qt-free."""

import pytest

from embodic.errors import Severity
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
