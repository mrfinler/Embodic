"""UT-MOD-03: the field table covers every input leaf once, with units and the ADR-0010 property list."""

import dataclasses
import re

import pytest

from embodic.model.fields import FIELD_BY_KEY, FIELDS, FieldGroup, FieldKind, Limits, Sign, field_specs
from embodic.model.schema import ValueType, field_key, leaves
from embodic.model.vocabulary import TopologyKind
from embodic.units import Unit

# ADR-0010 decision 2: B_r, mu_r, finished copper thickness, plating, convection; plus the material overrides.
PROPERTY_FIELDS = {
    "/rotor/remanence_t",
    "/rotor/recoil_permeability",
    "/stackup/layers/*/thickness_mm#copper",
    "/vias/plating_um",
    "/operating/convection_h_w_m2k",
    *(
        f"/materials/{name}{leaf}"
        for name in (
            "copper_resistivity_20c_ohm_m",
            "copper_temp_coeff_per_k",
            "copper_density_g_per_cm3",
            "laminate_density_g_per_cm3",
        )
        for leaf in ("", "/value", "/unit")
    ),
}


@pytest.mark.req("REQ-F-37", "REQ-F-32")
@pytest.mark.parametrize("topology", list(TopologyKind))
def test_every_leaf_has_exactly_one_field_and_every_field_a_leaf(topology):
    """Defect caught: a dataclass field added without a table row, or a row left behind after a field is removed."""
    from_types = [field_key(leaf.pattern, leaf.variant) for leaf in leaves(topology)]
    from_table = [field_key(spec.pointer, spec.variant) for spec in field_specs(topology)]
    assert len(from_table) == len(set(from_table))
    assert sorted(from_types) == sorted(from_table)


@pytest.mark.req("REQ-F-37")
def test_field_counts_per_topology():
    """Defect caught: a topology silently losing or gaining inputs (counts pinned from the first run)."""
    counts = {topology.value: len(field_specs(topology)) for topology in TopologyKind}
    assert counts == {"spiral": 114, "serpentine": 102, "wave": 94}
    assert len(FIELDS) == 135


@pytest.mark.req("REQ-N-24")
def test_dimension_suffixes_carry_their_unit():
    """Defect caught: a length shown without mm, or an angle row treated as millimetres."""
    for spec in FIELDS:
        leaf = spec.pointer.rsplit("/", 1)[1]
        if leaf.endswith("_mm"):
            assert spec.unit is Unit.MM, spec.pointer
        if leaf.endswith("_rad"):
            assert spec.unit is Unit.RAD, spec.pointer
        if spec.value_type in (ValueType.CHOICE, ValueType.BOOL, ValueType.TEXT):
            assert spec.unit is None, spec.pointer


@pytest.mark.req("REQ-N-24")
@pytest.mark.parametrize(
    ("key", "unit"),
    [
        ("/vias/plating_um", Unit.UM),
        ("/operating/convection_h_w_m2k", Unit.W_PER_M2_K),
        ("/materials/copper_resistivity_20c_ohm_m/value", Unit.OHM_M),
        ("/materials/copper_temp_coeff_per_k/value", Unit.PER_K),
        ("/materials/copper_density_g_per_cm3/value", Unit.G_PER_CM3),
        ("/materials/laminate_density_g_per_cm3/value", Unit.G_PER_CM3),
    ],
)
def test_property_inputs_carry_their_unit(key, unit):
    """DEF-M2a-01. Defect caught: plating, convection or a material override shown without its unit."""
    assert FIELD_BY_KEY[key].unit is unit


@pytest.mark.req("REQ-N-24")
@pytest.mark.parametrize(
    ("key", "widget_id"),
    [
        ("/phases", "param-phase-count"),
        ("/winding/terminal_side", "param-terminal-location"),
        ("/winding/bus_width_mm", "param-bus-width"),
        ("/vias/plating_um", "param-via-plating"),
        ("/connection/ring_width_mm", "param-ring-width"),
        ("/connection/terminal_pad_mm", "param-terminal-pad"),
        ("/connection/terminal_drill_mm", "param-terminal-drill"),
        ("/rotor/back_iron_thickness_mm", "param-back-iron"),
        ("/rotor/magnet/pole_arc_ratio#arc", "param-magnet-arc-ratio"),
        ("/rotor/magnet/r_inner_mm#arc", "param-magnet-r-inner"),
        ("/rotor/magnet/r_outer_mm#arc", "param-magnet-r-outer"),
        ("/rotor/magnet/width_mm#block", "param-magnet-width"),
        ("/rotor/magnet/length_mm#block", "param-magnet-length"),
        ("/rotor/magnet/r_center_mm#block", "param-magnet-r-center"),
        ("/drc_rules/via_clearance_mm", "param-min-via-space"),
        ("/drc_rules/edge_clearance_mm", "param-min-edge"),
        ("/drc_rules/hole_clearance_mm", "param-min-hole-space"),
        ("/drc_rules/min_annular_ring_mm", "param-min-ring"),
        ("/winding/stack_mode", "param-stack-mode"),
        ("/winding/board_gap_mm", "param-board-gap"),
    ],
)
def test_screens_v2_widgets_bind_their_field(key, widget_id):
    """screens.md v2 section 15 (R5, R9). Defect caught: a screens.md widget the form cannot bind to its field."""
    assert FIELD_BY_KEY[key].widget_id == widget_id


@pytest.mark.req("REQ-N-24")
def test_ruling_c_screw_leaves_bind_to_the_three_column_table_or_their_own_field():
    """U-S4e ruling c. Defect caught: fit or angle offset left in the table cells, or a leaf bound to no widget."""
    screws = {spec.pointer: spec.widget_id for spec in FIELDS if spec.pointer.startswith("/outline/screws")}
    assert screws == {
        "/outline/screws": "screw-table",
        "/outline/screws/*/size": "screw-table",
        "/outline/screws/*/count": "screw-table",
        "/outline/screws/*/pitch_radius_mm": "screw-table",
        "/outline/screws/*/fit": "param-screw-fit",
        "/outline/screws/*/hole_diameter_mm": "param-screw-hole-diameter",
        "/outline/screws/*/angle_offset_rad": "param-screw-angle-offset",
    }


@pytest.mark.req("REQ-N-24")
def test_ruling_c_pair_pointers_bind_to_the_pair_list_and_the_rotation_field():
    """U-S4e ruling c. Defect caught: a pair pointer still bound to `layer-list`, whose rows are layers, not pairs."""
    pairs = {spec.pointer: spec.widget_id for spec in FIELDS if spec.pointer.startswith("/winding/layers/")}
    assert pairs == {
        "/winding/layers/pairs": "pair-list",
        "/winding/layers/pairs/*/index": "pair-list",
        "/winding/layers/pairs/*/layer_in": "pair-list",
        "/winding/layers/pairs/*/layer_out": "pair-list",
        "/winding/layers/pairs/*/phases": "pair-list",
        "/winding/layers/pairs/*/rotation_rad": "param-pair-rotation",
        "/winding/layers/series_groups": "pair-list",
    }


@pytest.mark.req("REQ-F-24", "REQ-N-24")
def test_screw_hole_diameter_is_a_required_positive_mm_input_with_its_own_widget():
    """D-031a, interfaces.md section 2.2 row. Defect caught: a default or unit-less hole diameter, a missing widget."""
    spec = FIELD_BY_KEY["/outline/screws/*/hole_diameter_mm"]
    assert (spec.kind, spec.unit, spec.required, spec.neutral_value) == (FieldKind.DESIGN, Unit.MM, True, None)
    assert (spec.group, spec.widget_id) == (FieldGroup.FASTENERS, "param-screw-hole-diameter")
    assert (spec.limits, spec.step, spec.topologies) == (Limits(sign=Sign.POSITIVE), 0.1, frozenset(TopologyKind))


@pytest.mark.req("REQ-T-06")
def test_property_fields_are_the_adr_0010_list():
    """Defect caught: a design field becoming markable as measured, or a property field that cannot be."""
    keys = {field_key(spec.pointer, spec.variant) for spec in FIELDS if spec.kind is FieldKind.PROPERTY}
    assert keys == PROPERTY_FIELDS


@pytest.mark.req("REQ-F-36")
def test_required_fields_have_no_neutral_value_and_property_fields_are_required():
    """Defect caught: a silent default for a required field (D-014), or a defaulted physical property (ADR-0010)."""
    for spec in FIELDS:
        if spec.required:
            assert spec.neutral_value is None, spec.pointer
        if spec.kind is FieldKind.PROPERTY and spec.value_type is ValueType.FLOAT:
            assert spec.required, spec.pointer


@pytest.mark.req("REQ-F-32")
def test_topology_applicability():
    """Defect caught: a serpentine-only input shown for spiral, or a shared input hidden for one topology."""
    by_key = {field_key(s.pointer, s.variant): s.topologies for s in FIELDS}
    assert by_key["/winding/coil/coil_count"] == {TopologyKind.SPIRAL}
    assert by_key["/winding/layers_per_phase"] == {TopologyKind.SERPENTINE}
    assert by_key["/winding/bus_width_mm"] == {TopologyKind.WAVE}
    assert by_key["/winding/r_inner_mm"] == {TopologyKind.SERPENTINE, TopologyKind.WAVE}
    assert by_key["/rotor/poles"] == set(TopologyKind)


@pytest.mark.req("REQ-N-24")
def test_widget_ids_are_screens_md_object_names():
    """Defect caught: a widget id that is not a screens.md objectName shape (lowercase words joined by '-')."""
    for spec in FIELDS:
        if spec.widget_id is not None:
            assert re.fullmatch(r"[a-z]+(-[a-z]+)+", spec.widget_id), spec.widget_id


@pytest.mark.req("REQ-F-37")
def test_field_specs_are_frozen():
    """Defect caught: a form mutating the shared table at run time."""
    with pytest.raises(dataclasses.FrozenInstanceError):
        FIELDS[0].required = False  # type: ignore[misc]


@pytest.mark.req("REQ-F-34")
def test_d016_rows_match_interfaces_section_2_2():
    """D-016 FIELDS rows. Defect caught: a stack-mode default that leaves one board, or a gap without Xcoil's limits."""
    mode, gap = FIELD_BY_KEY["/winding/stack_mode"], FIELD_BY_KEY["/winding/board_gap_mm"]
    assert (mode.kind, mode.unit, mode.required, mode.neutral_value) == (FieldKind.DESIGN, None, False, "single")
    assert mode.choices == ("single", "one_board_per_phase")
    assert (gap.kind, gap.unit, gap.required, gap.neutral_value, gap.step) == (
        FieldKind.DESIGN,
        Unit.MM,
        False,
        0.1,
        0.05,
    )
    assert (gap.limits.sign, gap.limits.low, gap.limits.high) == (Sign.NON_NEGATIVE, 0, 10)
    assert mode.topologies == gap.topologies == {TopologyKind.SERPENTINE}
    assert mode.group is gap.group is FieldGroup.LAYERS
