"""OR rows of test_plan.md that need analyse() on a generated layout (oracle_cases.json O1-D08)."""

import importlib

import pytest


@pytest.mark.req("REQ-F-11")
@pytest.mark.xfail(
    raises=ModuleNotFoundError,
    strict=True,
    reason="OR-01 (O1-D08, Ke_LL 0.031 V*s/rad, D08 Table 9.1 p.98, band [-8 %, +8 % + e_edge 4.2 %]): analyse() "
    "exists (U-M2e-2) but the spiral generator (U-M2d) that builds the D08 layout does not; Phase 1 gaps G10 "
    "(air gap 1.4 vs 2.8 mm) and the EQ-04 T-arrangement magnets stay open",
)
def test_or01_d08_line_line_ke_within_the_registry_band() -> None:
    """Fails once the spiral generator exists, so the xfail cannot outlive the missing layout."""
    importlib.import_module("embodic.generators.spiral")
