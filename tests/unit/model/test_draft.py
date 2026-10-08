"""UT-MOD-01 and UT-MOD-02: blank drafts, missing lists in form order, and draft round trips."""

import pytest

from embodic.model.draft import DesignDraft, DraftIncomplete, blank_draft, draft_from_design, parse_draft
from embodic.model.fields import field_for, field_specs
from embodic.model.vocabulary import TopologyKind

from .designs import EXAMPLES, serpentine_design, spiral_design

SPIRAL_BLANK_MISSING = (
    "/name",
    "/winding/coil/coil_count",
    "/winding/coil/r_inner_mm",
    "/winding/coil/r_outer_mm",
    "/winding/coil/trace_width_mm",
    "/winding/coil/clearance_mm",
    "/winding/coil/coil_gap_mm",
    "/connection/ring_width_mm",
    "/connection/terminal_pad_mm",
    "/connection/terminal_drill_mm",
    "/winding/layers/pairs",
    "/winding/layers/series_groups",
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


@pytest.mark.req("REQ-F-36", "REQ-F-37")
@pytest.mark.parametrize("topology", list(TopologyKind))
def test_blank_draft_has_no_required_value_and_optional_fields_at_neutral(topology):
    """Defect caught: a blank design pre-filled with a team value (D-014) or an optional field left empty."""
    draft = blank_draft(topology)
    required = {spec.pointer for spec in field_specs(topology) if spec.required}
    assert not required & draft.values.keys()
    for spec in field_specs(topology):
        if spec.pointer in draft.values:
            assert draft.values[spec.pointer] == spec.neutral_value


@pytest.mark.req("REQ-F-37")
def test_blank_spiral_draft_lists_every_required_pointer_in_form_order():
    """Defect caught: a required field missing from the list, or the list in dataclass order instead of form order."""
    outcome = parse_draft(blank_draft(TopologyKind.SPIRAL))
    assert isinstance(outcome, DraftIncomplete)
    assert outcome.missing == SPIRAL_BLANK_MISSING
    assert outcome.issues == ()


@pytest.mark.req("REQ-F-36", "REQ-F-37")
@pytest.mark.parametrize("name", list(EXAMPLES))
def test_filling_the_last_required_field_gives_the_design(name):
    """Defect caught: parse_draft returning a design while one required value is still absent."""
    design = EXAMPLES[name]()
    values = dict(draft_from_design(design).values)
    for pointer in ("/name", "/vias/plating_um", "/drc_rules/min_annular_ring_mm"):
        partial = {k: v for k, v in values.items() if k != pointer}
        outcome = parse_draft(DesignDraft(topology=design.topology, values=partial))
        assert isinstance(outcome, DraftIncomplete)
        assert outcome.missing == (pointer,)
    assert parse_draft(DesignDraft(topology=design.topology, values=values)) == design


@pytest.mark.req("REQ-F-37")
@pytest.mark.parametrize("name", list(EXAMPLES))
def test_draft_round_trip_is_exact(name):
    """UT-MOD-02. Defect caught: a field lost or converted on the way from design to draft and back."""
    design = EXAMPLES[name]()
    assert parse_draft(draft_from_design(design)) == design


@pytest.mark.req("REQ-F-37")
def test_missing_list_item_field_is_reported_with_its_index():
    """Defect caught: a half-filled stack-up layer accepted, or reported without the layer it belongs to."""
    values = dict(draft_from_design(spiral_design()).values)
    del values["/stackup/layers/1/thickness_mm"]
    outcome = parse_draft(DesignDraft(topology=TopologyKind.SPIRAL, values=values))
    assert isinstance(outcome, DraftIncomplete)
    assert outcome.missing == ("/stackup/layers/1/thickness_mm",)


@pytest.mark.req("REQ-F-37")
def test_values_of_other_topologies_and_variants_are_ignored():
    """Defect caught: values kept from a topology switch or a magnet-shape switch blocking the design."""
    design = spiral_design()
    values = dict(draft_from_design(design).values)
    values["/winding/strands"] = 3
    values["/rotor/magnet/pole_arc_ratio"] = 0.8
    assert parse_draft(DesignDraft(topology=TopologyKind.SPIRAL, values=values)) == design


@pytest.mark.req("REQ-F-14", "REQ-F-37")
def test_invalid_present_value_is_an_issue_alongside_missing_fields():
    """Defect caught: an invalid value hidden until every required field is filled."""
    draft = blank_draft(TopologyKind.WAVE)
    values = {**draft.values, "/winding/trace_width_mm": -0.4}
    outcome = parse_draft(DesignDraft(topology=TopologyKind.WAVE, values=values))
    assert isinstance(outcome, DraftIncomplete)
    assert "/winding/trace_width_mm" not in outcome.missing
    assert [(i.code, i.pointers) for i in outcome.issues] == [("INVALID_NON_POSITIVE", ("/winding/trace_width_mm",))]


@pytest.mark.req("REQ-F-37")
def test_choosing_no_bore_and_no_screws_is_a_value():
    """Defect caught: an explicit 'no bore' (None) reported as missing."""
    design = spiral_design()
    values = {k: v for k, v in draft_from_design(design).values.items() if not k.startswith("/outline/bore")}
    values["/outline/bore"] = None
    outcome = parse_draft(DesignDraft(topology=TopologyKind.SPIRAL, values=values))
    assert not isinstance(outcome, DraftIncomplete)
    assert outcome.outline.bore is None


@pytest.mark.req("REQ-F-36", "REQ-F-37")
@pytest.mark.parametrize("topology", list(TopologyKind))
def test_blank_draft_starts_with_three_phases_as_a_default(topology):
    """R9. Defect caught: `/phases` still required, so a spiral form (no phase widget) could never be completed."""
    draft = blank_draft(topology)
    assert draft.values["/phases"] == 3
    outcome = parse_draft(draft)
    assert isinstance(outcome, DraftIncomplete)
    assert "/phases" not in outcome.missing


@pytest.mark.req("REQ-F-37", "REQ-N-24")
@pytest.mark.parametrize("topology", list(TopologyKind))
def test_every_required_pointer_of_a_blank_draft_has_a_widget(topology):
    """Defect caught: a required field the form cannot fill (screen_model_diff.py list 3, R9)."""
    draft = blank_draft(topology)
    outcome = parse_draft(draft)
    assert isinstance(outcome, DraftIncomplete)
    orphans = [pointer for pointer in outcome.missing if field_for(pointer, draft.values).widget_id is None]
    assert orphans == []


@pytest.mark.req("REQ-F-24", "REQ-F-37")
def test_screw_pattern_without_hole_diameter_is_reported_missing_with_its_index():
    """D-031a. Defect caught: a hole diameter looked up from size and fit instead of entered, or the gap unreported."""
    design = serpentine_design()
    values = dict(draft_from_design(design).values)
    assert values["/outline/screws/0/hole_diameter_mm"] == 3.4
    del values["/outline/screws/0/hole_diameter_mm"]
    outcome = parse_draft(DesignDraft(topology=design.topology, values=values))
    assert isinstance(outcome, DraftIncomplete)
    assert outcome.missing == ("/outline/screws/0/hole_diameter_mm",)
    assert outcome.issues == ()
