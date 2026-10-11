"""UT-MOD-04 and UT-MOD-05: provenance derived from origin, value and measurements; measured refusals."""

import dataclasses
import itertools
import json

import pytest

from embodic.errors import ValidationIssue
from embodic.io.examples import examples_dir, list_examples, load_example
from embodic.io.project import project_from_example, project_provenance, provenance_document
from embodic.model.outline import ScrewFit, ScrewPattern
from embodic.model.provenance import (
    DefaultValue,
    ExampleRef,
    ExampleValue,
    MeasuredValue,
    Measurement,
    UserValue,
    derive_provenance,
    drop_stale_measurements,
    mark_measured,
)
from embodic.model.schema import design_values

from .designs import spiral_design

REF = ExampleRef(example_id="spiral_12c16p_default", example_sha256="sha256:0")
BR = "/rotor/remanence_t"
SOURCE = "magnet datasheet rev C, grade N42"


def _with_br(design, remanence_t):
    return dataclasses.replace(design, rotor=dataclasses.replace(design.rotor, remanence_t=remanence_t))


EXPECTED = {
    # (origin present, value equals origin, measured) -> provenance of /rotor/remanence_t
    (True, True, True): MeasuredValue(source=SOURCE),
    (True, True, False): ExampleValue(example_id=REF.example_id),
    (True, False, True): MeasuredValue(source=SOURCE),
    (True, False, False): UserValue(),
    (False, True, True): MeasuredValue(source=SOURCE),
    (False, True, False): UserValue(),  # a required field has no neutral value, so never `default`
    (False, False, True): MeasuredValue(source=SOURCE),
    (False, False, False): UserValue(),
}


@pytest.mark.req("REQ-T-15")
@pytest.mark.parametrize(("has_origin", "equal", "measured"), list(itertools.product([True, False], repeat=3)))
def test_truth_table(has_origin, equal, measured):
    """Defect caught: a rule applied out of order, e.g. `example` winning over `measured`."""
    example = spiral_design()
    design = example if equal else _with_br(example, 1.21)
    origin = (REF, example) if has_origin else None
    measurements = [Measurement(pointer=BR, source=SOURCE)] if measured else []
    assert derive_provenance(design, origin, measurements)[BR] == EXPECTED[(has_origin, equal, measured)]


@pytest.mark.req("REQ-T-15")
def test_every_concrete_pointer_gets_provenance():
    """Defect caught: list items or variant fields left out of the saved provenance map (interfaces.md 9.1)."""
    design = spiral_design()
    assert derive_provenance(design, None, []).keys() == design_values(design).keys()


@pytest.mark.req("REQ-T-15")
def test_reentry_changes_nothing_and_back_to_example_restores_example():
    """Defect caught: keystroke-dependent provenance (ADR-0010 option C)."""
    example = spiral_design()
    origin = (REF, example)
    retyped = _with_br(example, float("1.3"))
    assert derive_provenance(retyped, origin, []) == derive_provenance(example, origin, [])
    changed = _with_br(example, 1.25)
    assert derive_provenance(changed, origin, [])[BR] == UserValue()
    back = _with_br(changed, 1.3)
    assert derive_provenance(back, origin, [])[BR] == ExampleValue(example_id=REF.example_id)


@pytest.mark.req("REQ-T-15")
def test_blank_origin_optional_field_at_neutral_is_default_until_changed():
    """Defect caught: D-019 `default` missing, or kept after the user changes the value."""
    design = spiral_design()
    pointer = "/winding/coil/corner_radius_mm"
    assert derive_provenance(design, None, [])[pointer] == DefaultValue()
    coil = dataclasses.replace(design.winding.coil, corner_radius_mm=0.3)
    changed = dataclasses.replace(design, winding=dataclasses.replace(design.winding, coil=coil))
    assert derive_provenance(changed, None, [])[pointer] == UserValue()
    assert derive_provenance(design, (REF, design), [])[pointer] == ExampleValue(example_id=REF.example_id)


@pytest.mark.req("REQ-T-06")
def test_mark_measured_refuses_empty_source_and_design_fields():
    """Defect caught: a measured mark without a source, or on a geometry field (D-007)."""
    design = spiral_design()
    empty = mark_measured(design, [], BR, "   ")
    assert isinstance(empty, ValidationIssue) and empty.code == "INVALID_MEASURED_SOURCE_EMPTY"
    geometry = mark_measured(design, [], "/winding/coil/trace_width_mm", SOURCE)
    assert isinstance(geometry, ValidationIssue) and geometry.code == "INVALID_MEASURED_DESIGN_FIELD"
    dielectric = mark_measured(design, [], "/stackup/layers/1/thickness_mm", SOURCE)
    assert isinstance(dielectric, ValidationIssue) and dielectric.code == "INVALID_MEASURED_DESIGN_FIELD"
    copper = mark_measured(design, [], "/stackup/layers/0/thickness_mm", SOURCE)
    assert copper == (Measurement(pointer="/stackup/layers/0/thickness_mm", source=SOURCE),)


@pytest.mark.req("REQ-T-06")
def test_marking_again_replaces_the_source():
    """Defect caught: two measurements stored for one field."""
    design = spiral_design()
    first = mark_measured(design, [], BR, "old record")
    assert isinstance(first, tuple)
    assert mark_measured(design, first, BR, SOURCE) == (Measurement(pointer=BR, source=SOURCE),)


@pytest.mark.req("REQ-T-06")
def test_value_change_drops_the_measurement():
    """Defect caught: a measured label surviving a change of the measured value."""
    design = spiral_design()
    measurements = [Measurement(pointer=BR, source=SOURCE), Measurement(pointer="/vias/plating_um", source="coupon")]
    changed = _with_br(design, 1.25)
    assert drop_stale_measurements(design, changed, measurements) == (measurements[1],)
    assert derive_provenance(changed, None, drop_stale_measurements(design, changed, measurements))[BR] == UserValue()


SCREW_ANGLE = "/outline/screws/0/angle_offset_rad"
SCREW_COUNT = "/outline/screws/0/count"


def _with_screws(design, *angle_offsets_rad):
    patterns = tuple(
        ScrewPattern(
            size="M3",
            fit=ScrewFit.NORMAL,
            count=8,
            pitch_radius_mm=44.5,
            hole_diameter_mm=3.4,
            angle_offset_rad=angle,
        )
        for angle in angle_offsets_rad
    )
    return dataclasses.replace(design, outline=dataclasses.replace(design.outline, screws=patterns))


@pytest.mark.req("REQ-T-15")
def test_d043a_a_field_the_origin_example_holds_no_value_for_is_default_while_at_its_neutral_value():
    """DEF-M4e3c-01. Catches a user chip on an angle offset nobody typed, in a pattern added to a screwless example."""
    example = _with_screws(spiral_design())
    added = _with_screws(example, 0.0)
    derived = derive_provenance(added, (REF, example), [])
    assert derived[SCREW_ANGLE] == DefaultValue()
    assert derived[SCREW_COUNT] == UserValue(), "a required field has no neutral value, so never `default`"


@pytest.mark.req("REQ-T-15")
def test_d043a_a_field_the_origin_example_holds_a_different_value_for_is_user_even_at_its_neutral_value():
    """Catches `default` winning where the example's own value was changed back to the neutral one."""
    example = _with_screws(spiral_design(), 0.2)
    changed = _with_screws(example, 0.0)
    assert derive_provenance(changed, (REF, example), [])[SCREW_ANGLE] == UserValue()


@pytest.mark.req("REQ-T-15")
def test_d043a_a_typed_value_of_a_field_the_origin_holds_nothing_for_is_user():
    """Catches `default` kept after the user types a value that is not the neutral one."""
    example = _with_screws(spiral_design())
    typed = _with_screws(example, 0.1)
    assert derive_provenance(typed, (REF, example), [])[SCREW_ANGLE] == UserValue()


@pytest.mark.req("REQ-T-15")
@pytest.mark.parametrize("example_id", [info.example_id for info in list_examples()])
def test_d043a_an_unmodified_example_keeps_the_provenance_map_stored_in_its_file(example_id):
    """Catches the new rule leaking into a design that is its origin: every stored entry stays `example`."""
    stored = json.loads((examples_dir() / f"{example_id}.embodic.json").read_text(encoding="utf-8"))["provenance"]
    project = project_from_example(load_example(example_id))
    assert provenance_document(project_provenance(project)) == stored
    assert {entry["provenance"] for entry in stored.values()} == {"example"}
