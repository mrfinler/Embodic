"""Item 9: run_drc mid-run cancellation checked by test_plan.md section 5.5 rule 1 (a read-counting token, no clock).

Subject: run_drc on the packaged CF-11 board. Defects caught: a token read only before the run starts, a cancelled
run that still returns a report, and a run that keeps working after the token turns true.
"""

import pytest

from embodic.drc import CancelToken, run_drc
from embodic.generators import build_layout
from embodic.io.examples import load_example
from embodic.results import load_registry

pytestmark = pytest.mark.req("REQ-F-10")


class CountingToken(CancelToken):
    """Turns cancelled at its k-th read (never when k is None) and counts every read."""

    def __init__(self, k: int | None) -> None:
        super().__init__()
        self.k, self.reads = k, 0

    @property
    def cancelled(self) -> bool:
        """Return True from the k-th read on."""
        self.reads += 1
        return self.k is not None and self.reads >= self.k


@pytest.fixture(scope="module")
def board():
    """Return the CF-11 example board and its design rules."""
    _, design = load_example("spiral_12c16p_default")
    return build_layout(design, load_registry()).boards[0], design.drc_rules


def test_cancel_at_any_read_returns_none_and_stops_reading(board) -> None:
    """Cancelling at read 1, the middle read or the last read returns None after fewer reads than a full run."""
    layout, rules = board
    full = CountingToken(None)
    assert run_drc(layout, rules, cancel=full) is not None
    assert full.reads >= 3, "the run must poll the token more than at its start and end"
    for k in sorted({1, full.reads // 2, full.reads - 1}):
        token = CountingToken(k)
        assert run_drc(layout, rules, cancel=token) is None, k
        assert token.reads == k, (k, token.reads)
