"""Item 2 (U-V3): brute-force DRC of every ported board against run_drc at Xcoil's clearance."""

import pytest
from cases import all_cases, have_xcoil
from drc_m3 import board_drc

pytestmark = [
    pytest.mark.req("REQ-F-34", "REQ-F-35", "REQ-F-40"),
    pytest.mark.slow,
    pytest.mark.skipif(not have_xcoil(), reason="needs node and the read-only Xcoil engine"),
]

DEF_UV3_01 = pytest.mark.xfail(
    strict=True,
    reason="DEF-UV3-01: the end group at a path's last end omits the fillet before the terminating main "
    "(src/embodic/drc/items.py l.177-180); run_drc reports 2 trace_via pairs that interfaces.md section 7 "
    "rule 2 exempts",
)
CASES = [pytest.param(c, marks=DEF_UV3_01) if c == "w-overlap-p12-l4-m1" else c for c in sorted(all_cases())]


@pytest.mark.parametrize("case_id", CASES)
def test_run_drc_reports_exactly_the_brute_violations(case_id: str) -> None:
    """Catches a missed D-006 violation, a false one, and an exemption wider or narrower than section 7."""
    for board in board_drc(case_id):
        assert set(board.engine) == set(board.brute), board.classes()
