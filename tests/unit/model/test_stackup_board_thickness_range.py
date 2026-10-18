"""D-059d: a board thickness outside 0.2 to 10 mm is an unsupported range, as Xcoil reports RANGE (engine.js l.116).

The bounds are Xcoil `num('boardThickness', 0.2, 10)` (engine.js l.127). The check is independent of D-053a.
"""

import math

import pytest

from embodic.errors import IssueCategory, Severity
from embodic.model.validate import board_thickness_range_issues

pytestmark = pytest.mark.req("REQ-F-14")


def test_a_board_below_0p2_mm_is_one_unsupported_range_error_that_names_the_limit():
    """Catches a thin board that passes, or a refusal with the wrong code, category, pointer, value or limit."""
    (found,) = board_thickness_range_issues(0.15)
    assert (found.code, found.category, found.severity) == (
        "RANGE_BELOW_SUPPORTED",
        IssueCategory.UNSUPPORTED_RANGE,
        Severity.ERROR,
    )
    assert (found.pointers, found.value, found.limit) == (("/stackup/layers",), 0.15, 0.2)
    assert found.message == "The value is below the supported minimum of 0.2 mm."


def test_a_board_above_10_mm_is_one_unsupported_range_error_that_names_the_limit():
    """Catches a thick board that passes, or a maximum reported as the minimum."""
    (found,) = board_thickness_range_issues(12.0)
    assert (found.code, found.category, found.severity) == (
        "RANGE_ABOVE_SUPPORTED",
        IssueCategory.UNSUPPORTED_RANGE,
        Severity.ERROR,
    )
    assert (found.pointers, found.value, found.limit) == (("/stackup/layers",), 12.0, 10)
    assert found.message == "The value is above the supported maximum of 10 mm."


@pytest.mark.parametrize("board_mm", [0.2, 1.6, 10.0])
def test_the_ends_of_the_range_and_a_normal_board_are_supported(board_mm):
    """Catches an off-by-boundary check (< written as <=) that refuses exactly 0.2 mm or exactly 10 mm."""
    assert board_thickness_range_issues(board_mm) == ()


@pytest.mark.parametrize(
    ("board_mm", "code"),
    [
        (math.nextafter(0.2, 0.0), "RANGE_BELOW_SUPPORTED"),
        (math.nextafter(10.0, math.inf), "RANGE_ABOVE_SUPPORTED"),
        (math.inf, "RANGE_ABOVE_SUPPORTED"),
    ],
)
def test_the_float_next_to_an_end_and_infinity_are_refused(board_mm, code):
    """Catches a tolerance that lets 0.2 mm - 1 ulp through, and infinity written into a stack-up (REQ-F-14)."""
    assert [found.code for found in board_thickness_range_issues(board_mm)] == [code]
