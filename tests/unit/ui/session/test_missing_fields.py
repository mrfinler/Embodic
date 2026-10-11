"""The missing-field list names each control the user fills once (m4_review_2.md 7.3; U-M4e-3c open question)."""

import pytest

from embodic.model.draft import blank_draft, parse_draft
from embodic.model.vocabulary import TopologyKind
from embodic.ui.viewmodels.session import missing_fields

PAIRS = "/winding/layers/pairs"
SERIES_GROUPS = "/winding/layers/series_groups"
STACKUP = "/stackup/layers"


@pytest.mark.req("REQ-F-37")
def test_a_blank_spiral_lists_its_copper_layers_control_once():
    """Catches a row per pointer: pairs, series groups and stack-up all fill from "Copper layers" (D-024)."""
    draft = blank_draft(TopologyKind.SPIRAL)
    missing = parse_draft(draft).missing
    assert {PAIRS, SERIES_GROUPS, STACKUP} <= set(missing)
    fields = missing_fields(draft, missing)
    assert set(missing) - set(fields) == {SERIES_GROUPS, STACKUP}
    assert len(fields) == len(missing) - 2 == 35


@pytest.mark.req("REQ-F-37")
@pytest.mark.parametrize("topology", [TopologyKind.SERPENTINE, TopologyKind.WAVE])
def test_a_draft_whose_missing_pointers_each_have_their_own_control_keeps_all_of_them(topology):
    """Catches a grouping that merges controls which only look alike, or one that reorders the form order."""
    draft = blank_draft(topology)
    missing = parse_draft(draft).missing
    assert missing_fields(draft, missing) == missing
