"""The two verdict cards of the results rail: Inputs and DRC (screens.md section 6.1, D-039 e). Qt-free."""

import dataclasses

import pytest

from embodic.errors import IssueCategory, Severity, ValidationIssue
from embodic.ui.viewmodels.results import drc_card, drc_table, inputs_card

pytestmark = pytest.mark.req("REQ-F-33")


def issue(code: str, severity: Severity = Severity.ERROR) -> ValidationIssue:
    """Return an input issue with a fixed message."""
    return ValidationIssue(code=code, category=IssueCategory.INVALID, severity=severity, message="x", pointers=("/a",))


def test_inputs_card_says_no_input_issues_for_an_empty_issue_list():
    """Catches a pass card that shows a count, or the old 'Design' word."""
    card = inputs_card(())
    assert (card.key, card.title, card.state, card.word) == ("rail-inputs", "Inputs", "pass", "No input issues")


@pytest.mark.parametrize(("count", "word"), [(1, "1 input issue"), (3, "3 input issues")])
def test_inputs_card_counts_the_issues_the_list_shows(count, word):
    """Catches a card that disagrees with the list below it, and '1 input issues'."""
    card = inputs_card([issue(f"INVALID_{n}") for n in range(count)])
    assert (card.state, card.word) == ("fail", word)


@pytest.mark.parametrize(
    ("issues", "missing", "state", "word"),
    [
        ([issue("RANGE_NOTE", Severity.WARNING)], 0, "advice", "1 input note"),
        ([issue("A", Severity.WARNING), issue("B", Severity.INFO)], 0, "advice", "2 input notes"),
        ([issue("INVALID_A"), issue("RANGE_NOTE", Severity.WARNING)], 0, "fail", "1 input issue, 1 input note"),
        ([issue("RANGE_NOTE", Severity.WARNING)], 2, "fail", "2 required fields left, 1 input note"),
    ],
)
def test_inputs_card_counts_only_errors_as_failing_inputs_and_words_the_rest_as_notes(issues, missing, state, word):
    """U-S4h N4. Catches advice the user cannot fix counted as a failing input (a fail glyph on a warning)."""
    card = inputs_card(issues, missing)
    assert (card.state, card.word) == (state, word)


def test_drc_card_of_the_wave_example_counts_186_failures(wave):
    """Catches a DRC card that reads 'Problems found' or a count that differs from the DRC tab."""
    table = drc_table(wave)
    card = drc_card(table)
    assert (card.key, card.title, card.state, card.word) == ("rail-drc", "DRC", "fail", "186 failures")
    assert table is not None and table.failure_count == 186


def test_drc_card_of_a_passing_design_says_passed(d08):
    """Catches a pass card that shows '0 failures'."""
    card = drc_card(drc_table(d08))
    assert (card.state, card.word) == ("pass", "Passed")


def test_drc_card_says_not_run_when_the_check_did_not_run(d08):
    """Catches a design without a DRC result shown as passed."""
    card = drc_card(drc_table(dataclasses.replace(d08, drc=None)))
    assert (card.state, card.word) == ("not-run", "Not run")


def test_drc_card_uses_the_singular_for_one_failure(wave):
    """Catches '1 failures'."""
    table = drc_table(wave)
    assert table is not None
    one = dataclasses.replace(table, failure_count=1)
    assert drc_card(one).word == "1 failure"
