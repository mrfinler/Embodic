"""What a draft tells the user it lacks: missing required fields, invalid fields, long messages (m4_review_2.md 7.3).

Items 7, 8 and 12 of the U-M4e-3 change requests; screens.md section 6.1 (`rail-inputs`, `issues-list`).
"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QListWidget
from tests.ui.qt_design.conftest import enter, find
from tests.ui.qt_design.test_editing import no_compute

from embodic.errors import IssueCategory, Severity, ValidationIssue
from embodic.model.vocabulary import TopologyKind
from embodic.ui.viewmodels.session import SessionDrafting

D08 = "spiral_12c10p_d08"


def settle():
    """Let the window follow the session."""
    for _ in range(5):
        QApplication.processEvents()


def listed(window) -> list[str]:
    """Return the rows of the Input issues list."""
    issues = find(window, "issues-list")
    assert isinstance(issues, QListWidget)
    return [issues.item(row).text() for row in range(issues.count())]


@pytest.mark.req("REQ-F-36", "REQ-F-37")
def test_7_a_blank_draft_lists_its_missing_required_fields_in_the_rail(make_shell):
    """Catches S13 and S21: "37 required fields left" in the bar while the rail says "No input issues."."""
    window = make_shell(compute_fn=no_compute).window
    window.session.new_design(TopologyKind.SPIRAL)
    settle()
    state = window.session.state.value
    assert isinstance(state, SessionDrafting) and len(state.missing) > 1
    rows = listed(window)
    assert "No input issues." not in rows
    assert len(rows) == len(state.missing)
    coils = find(window, "param-coil-count-label").text()
    assert f"{coils}: required, no value yet." in rows
    card = find(window, "rail-inputs")
    assert card.isVisibleTo(window.rail)
    assert find(card, "rail-inputs-value").text() == f"{len(state.missing)} required fields left"
    assert find(card, "rail-inputs-value").property("state") == "fail"


@pytest.mark.req("REQ-F-36", "REQ-F-37")
def test_7_an_issue_row_of_a_missing_field_focuses_that_field(make_shell, qtbot):
    """Catches a missing-field row that is text only: activating it must take the user to the field."""
    window = make_shell(compute_fn=no_compute).window
    window.session.new_design(TopologyKind.SPIRAL)
    settle()
    window.inspector_tabs.setCurrentWidget(window.panels["tab-board"])
    coils = find(window, "param-coil-count-label").text()
    issues = find(window, "issues-list")
    (row,) = [issues.item(r) for r in range(issues.count()) if issues.item(r).text().startswith(f"{coils}:")]
    issues.itemActivated.emit(row)
    settle()
    assert QApplication.focusWidget() is find(window, "param-coil-count")


@pytest.mark.req("REQ-F-37")
def test_7_an_invalid_field_with_nothing_missing_hides_the_required_bar_and_names_the_invalid_field(
    make_shell, wait_computed, qtbot
):
    """Catches S14 and S23: "0 required fields left" beside an enabled Go to first missing field, and in the banner."""
    window = make_shell().window
    window.session.load_example(D08)
    wait_computed(window)
    enter(qtbot, window, "param-r-inner", "-1")
    settle()
    state = window.session.state.value
    assert isinstance(state, SessionDrafting) and state.missing == ()
    assert not find(window, "required-bar").isVisibleTo(window)
    banner = window.stale_label
    assert banner.isVisibleTo(window)
    assert "1 field is invalid" in banner.text() and "0 required" not in banner.text()


@pytest.mark.req("REQ-N-15")
def test_8_issues_list_wraps_a_long_message_without_a_sideways_bar(make_shell, wait_computed):
    """Catches S19: an issue message that runs off the right edge of the rail with a sideways bar (UX-AC-21)."""
    window = make_shell().window
    window.session.load_example(D08)
    wait_computed(window)
    long = " ".join(["The clearance between the outer turn and the board edge is below the rule."] * 3)
    issue = ValidationIssue(
        code="RANGE_TEST_LONG",
        category=IssueCategory.UNSUPPORTED_RANGE,
        severity=Severity.ERROR,
        message=long,
        pointers=(),
    )
    window.session.issues.set((issue,))
    settle()
    issues = find(window, "issues-list")
    assert listed(window) == [long]
    assert not issues.horizontalScrollBar().isVisible()
    rect = issues.visualItemRect(issues.item(0))
    assert rect.right() <= issues.viewport().width()
    assert rect.height() >= 3 * issues.fontMetrics().height(), rect


# Open: add_screw_pattern must write the angle offset (an empty pattern has no pointer), and provenance reads a
# written value the example does not hold as `user`; the fix belongs in embodic.model.provenance (out of U-M4e-3c).
OPEN_DEF_M4E3C_01 = "DEF-M4e3c-01: a new fastener pattern's angle offset shows a user chip nobody typed"


@pytest.mark.req("REQ-F-24")
@pytest.mark.xfail(strict=True, reason=OPEN_DEF_M4E3C_01)
def test_12_a_new_fastener_pattern_starts_its_angle_offset_with_a_default_chip(make_shell, wait_computed, qtbot):
    """Catches S20: a new pattern whose angle offset shows no chip, or a user chip for a value nobody typed."""
    window = make_shell().window
    window.session.load_example(D08)
    wait_computed(window)
    window.inspector_tabs.setCurrentWidget(window.panels["tab-board"])
    qtbot.mouseClick(find(window, "btn-screw-add"), Qt.MouseButton.LeftButton)
    settle()
    chip = find(window, "param-screw-angle-offset-prov")
    assert isinstance(chip, QLabel)
    assert chip.isVisibleTo(window.panels["tab-board"]) and chip.text() == "default"
