"""UT-MOD-03: the field table covers every input leaf once, with units and the ADR-0010 property list."""

import dataclasses
import re

import pytest

from embodic.model.fields import FIELDS, FieldKind, field_specs
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
    assert counts == {"spiral": 113, "serpentine": 99, "wave": 93}
    assert len(FIELDS) == 132


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
