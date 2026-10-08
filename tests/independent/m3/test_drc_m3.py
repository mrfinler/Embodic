"""Item 2 (U-V3): brute-force DRC of every ported board against run_drc at Xcoil's clearance."""

import pytest
from cases import all_cases, have_xcoil
from drc_m3 import board_drc

pytestmark = [
    pytest.mark.req("REQ-F-34", "REQ-F-35", "REQ-F-40"),
    pytest.mark.slow,
    pytest.mark.skipif(not have_xcoil(), reason="needs node and the read-only Xcoil engine"),
]


@pytest.mark.parametrize("case_id", sorted(all_cases()))
def test_run_drc_reports_exactly_the_brute_violations(case_id: str) -> None:
    """Catches a missed D-006 violation, a false one, and an exemption wider or narrower than section 7."""
    for board in board_drc(case_id):
        assert set(board.engine) == set(board.brute), board.classes()
