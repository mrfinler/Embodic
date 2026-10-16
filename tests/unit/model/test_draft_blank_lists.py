"""F37-1 (V3-01 union ruling): the exact missing-field lists of a blank serpentine and a blank wave draft.

The literals are written out by hand from the required leaves of the serpentine and wave winding specs
(interfaces.md section 2.2) in the slots of the shared sections of the spiral list, in form order. They are not
computed from field_specs().
"""

import pytest

from embodic.model.draft import DraftIncomplete, blank_draft, parse_draft
from embodic.model.vocabulary import TopologyKind

# Shared leaves after the winding block, from /connection to /vias; the winding leaves of each topology go between.
_CONNECTION = (
    "/connection/ring_width_mm",
    "/connection/terminal_pad_mm",
    "/connection/terminal_drill_mm",
)
_FROM_VIAS_ON = (
    "/vias/drill_mm",
    "/vias/pad_mm",
    "/vias/plating_um",
    "/outline/board/shape",
    "/outline/bore/shape",
    "/stackup/layers",
    "/rotor/poles",
    "/rotor/rotor_type",
    "/rotor/magnet/kind",
    "/rotor/remanence_t",
    "/rotor/recoil_permeability",
    "/rotor/air_gap_mm",
    "/rotor/back_iron_thickness_mm",
    "/operating/speed_rpm",
    "/operating/line_current_rms_a",
    "/operating/winding_temperature_degc",
    "/operating/convection_h_w_m2k",
    "/operating/ambient_temperature_degc",
    "/drc_rules/trace_clearance_mm",
    "/drc_rules/via_clearance_mm",
    "/drc_rules/edge_clearance_mm",
    "/drc_rules/hole_clearance_mm",
    "/drc_rules/min_trace_width_mm",
    "/drc_rules/min_drill_mm",
    "/drc_rules/min_annular_ring_mm",
)
SERPENTINE_BLANK_MISSING = (
    "/name",
    "/winding/r_inner_mm",
    "/winding/r_outer_mm",
    "/winding/turns",
    "/winding/trace_width_mm",
    "/winding/clearance_mm",
    *_CONNECTION,
    "/winding/layers_per_phase",
    *_FROM_VIAS_ON,
)
WAVE_BLANK_MISSING = (
    "/name",
    "/winding/r_inner_mm",
    "/winding/r_outer_mm",
    "/winding/turns",
    "/winding/trace_width_mm",
    "/winding/clearance_mm",
    "/winding/bus_width_mm",
    *_CONNECTION,
    *_FROM_VIAS_ON,
)


@pytest.mark.req("REQ-F-37")
@pytest.mark.parametrize(
    ("topology", "expected"),
    [(TopologyKind.SERPENTINE, SERPENTINE_BLANK_MISSING), (TopologyKind.WAVE, WAVE_BLANK_MISSING)],
    ids=lambda v: v.value if isinstance(v, TopologyKind) else "",
)
def test_f37_1_blank_serpentine_and_wave_drafts_list_every_required_pointer_in_form_order(topology, expected):
    """Catches a serpentine or wave required field dropped from the list, or the list in dataclass order."""
    outcome = parse_draft(blank_draft(topology))
    assert isinstance(outcome, DraftIncomplete)
    assert outcome.missing == expected
    assert outcome.issues == ()
