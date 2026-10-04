"""Issue vocabulary and message catalogue of embodic.errors."""

import dataclasses
import re

import pytest

from embodic import errors
from embodic.errors import IssueCategory, Severity, Suggestion, ValidationIssue

UPPER_SNAKE = re.compile(r"[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+")


@pytest.mark.req("REQ-L-01")
def test_errors_message_for_returns_catalogue_text():
    """Catches message_for returning the code or an empty string instead of the English sentence."""
    assert errors.message_for("INFO_MIGRATED") == "The project file was upgraded to the current file format."


@pytest.mark.req("REQ-L-01")
def test_errors_message_for_unknown_code_raises_key_error():
    """Catches a silent fallback that would show a raw code to the user instead of failing in tests."""
    with pytest.raises(KeyError):
        errors.message_for("INVALID_NO_SUCH_CODE")


@pytest.mark.req("REQ-L-01")
def test_errors_catalogue_codes_are_upper_snake_with_category_prefix():
    """Catches a code that breaks the naming rule of package_layout.md section 2 (e.g. 'skinDepth' or 'SKIN')."""
    bad = [
        code for code in errors.MESSAGES if not UPPER_SNAKE.fullmatch(code) or not code.startswith(errors.CODE_PREFIXES)
    ]
    assert bad == []


@pytest.mark.req("REQ-L-01")
def test_errors_catalogue_messages_are_sentences():
    """Catches a placeholder message: every entry starts with a capital letter and ends with a full stop."""
    bad = [code for code, text in errors.MESSAGES.items() if not (text[:1].isupper() and text.endswith("."))]
    assert bad == []


@pytest.mark.req("REQ-F-23")
def test_errors_issue_is_immutable_and_keyword_only():
    """Catches dropping frozen or kw_only: issues cross module seams and must not change after creation."""
    suggestion = Suggestion(pointer="/coil/turns", proposed_value=6, reason="Fits the annulus.")
    issue = ValidationIssue(
        code="RANGE_SKIN_DEPTH",
        category=IssueCategory.UNSUPPORTED_RANGE,
        severity=Severity.WARNING,
        message=errors.message_for("RANGE_SKIN_DEPTH"),
        pointers=("/coil/trace_width_mm",),
        suggestion=suggestion,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        issue.code = "INVALID_OTHER"  # type: ignore[misc]
    with pytest.raises(TypeError):
        Suggestion("/coil/turns", 6, "positional")  # type: ignore[misc]
    assert hash(issue) == hash(dataclasses.replace(issue))


@pytest.mark.req("REQ-F-19")
def test_errors_unbuildable_requires_an_unbuildable_error():
    """Catches an Unbuildable that carries only warnings, which would leave the user with no reason for the failure."""
    reason = ValidationIssue(
        code="UNBUILDABLE_NO_ROOM",
        category=IssueCategory.UNBUILDABLE,
        severity=Severity.ERROR,
        message="No turn fits between the inner and outer radius.",
        pointers=("/coil",),
    )
    warning = dataclasses.replace(reason, severity=Severity.WARNING)
    assert errors.Unbuildable(issues=(warning, reason)).issues[1] is reason
    with pytest.raises(ValueError, match="UNBUILDABLE"):
        errors.Unbuildable(issues=(warning,))
    with pytest.raises(ValueError, match="UNBUILDABLE"):
        errors.Unbuildable(issues=())
