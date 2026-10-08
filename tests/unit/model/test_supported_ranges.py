"""Supported ranges that bound compute work or keep a formula finite (DEF-M2f-02, DEF-M2f-03)."""

import pytest

from embodic.errors import IssueCategory, Severity
from embodic.io.examples import load_example
from embodic.model.design import DesignParameters
from embodic.model.draft import DesignDraft, DraftIncomplete, draft_from_design, parse_draft
from embodic.model.schema import JsonValue
from embodic.model.validate import validate_design


def _cf11_with(changes: dict[str, JsonValue]) -> DesignParameters:
    draft = draft_from_design(load_example("spiral_12c16p_default")[1])
    parsed = parse_draft(DesignDraft(topology=draft.topology, values={**draft.values, **changes}))
    assert not isinstance(parsed, DraftIncomplete)
    return parsed


def _blocking(design: DesignParameters) -> set[tuple[str, tuple[str, ...]]]:
    return {(i.code, i.pointers) for i in validate_design(design) if i.severity is Severity.ERROR}


@pytest.mark.req("REQ-F-14")
@pytest.mark.parametrize(
    ("changes", "code", "pointers"),
    [
        # Physics cuts every path into length / max_segment chords: 0.001 mm ran for minutes in PR-05.
        ({"/analysis/max_segment_mm": 0.001}, "RANGE_BELOW_SUPPORTED", ("/analysis/max_segment_mm",)),
        ({"/analysis/max_segment_mm": 5e-324}, "RANGE_BELOW_SUPPORTED", ("/analysis/max_segment_mm",)),
        # The DRC broad phase keeps every pair closer than the rule: 64 mm stalled the gate.
        ({"/drc_rules/trace_clearance_mm": 64}, "RANGE_ABOVE_SUPPORTED", ("/drc_rules/trace_clearance_mm",)),
        ({"/drc_rules/via_clearance_mm": 999.9}, "RANGE_ABOVE_SUPPORTED", ("/drc_rules/via_clearance_mm",)),
        ({"/drc_rules/edge_clearance_mm": 64}, "RANGE_ABOVE_SUPPORTED", ("/drc_rules/edge_clearance_mm",)),
        ({"/drc_rules/hole_clearance_mm": 1000}, "RANGE_ABOVE_SUPPORTED", ("/drc_rules/hole_clearance_mm",)),
        # Underflowing plating makes the via barrel area 0 and the via resistance a division by zero.
        ({"/vias/plating_um": 5e-324}, "RANGE_BELOW_SUPPORTED", ("/vias/plating_um",)),
        # Magnet sizes of 1e-164 mm reached physics (DEF-M2f-02).
        ({"/rotor/magnet/length_mm": 1.5e-164}, "RANGE_BELOW_SUPPORTED", ("/rotor/magnet/length_mm",)),
        ({"/rotor/magnet/width_mm": 1e-6}, "RANGE_BELOW_SUPPORTED", ("/rotor/magnet/width_mm",)),
        ({"/rotor/magnet/r_center_mm": 1e300}, "RANGE_ABOVE_SUPPORTED", ("/rotor/magnet/r_center_mm",)),
        # A 1e300 mm outline overflows segment lengths in DRC and discretisation.
        ({"/outline/bore/radius_mm": 1e300}, "RANGE_ABOVE_SUPPORTED", ("/outline/bore/radius_mm",)),
        ({"/outline/board/across_flats_mm": 1e300}, "RANGE_ABOVE_SUPPORTED", ("/outline/board/across_flats_mm",)),
        # IPC-2221 raises a negative temperature rise to 0.44, which is complex.
        (
            {"/operating/winding_temperature_degc": 3},
            "RANGE_WINDING_BELOW_AMBIENT",
            ("/operating/winding_temperature_degc", "/operating/ambient_temperature_degc"),
        ),
    ],
)
def test_values_outside_the_supported_range_block_compute(
    changes: dict[str, JsonValue], code: str, pointers: tuple[str, ...]
) -> None:
    """Catches a value that reaches a stage which stalls or raises on it instead of returning a blocking issue."""
    design = _cf11_with(changes)
    found = [i for i in validate_design(design) if (i.code, i.pointers) == (code, pointers)]
    assert len(found) == 1
    assert found[0].severity is Severity.ERROR
    assert found[0].category is IssueCategory.UNSUPPORTED_RANGE


@pytest.mark.req("REQ-F-14")
@pytest.mark.parametrize(
    "changes",
    [
        {},
        {"/analysis/max_segment_mm": 0.1},
        {"/drc_rules/trace_clearance_mm": 5.0},
        {"/vias/plating_um": 1.0},
        {"/operating/winding_temperature_degc": 25.0, "/operating/ambient_temperature_degc": 25.0},
    ],
)
def test_values_at_the_supported_limits_pass(changes: dict[str, JsonValue]) -> None:
    """Catches a bound that refuses the packaged example or a value on the supported limit."""
    assert _blocking(_cf11_with(changes)) == set()


@pytest.mark.req("REQ-F-14")
@pytest.mark.parametrize(
    ("changes", "code", "category"),
    [
        # CF-11 coil spans r 18 to 38 mm; a 20 mm block centred at 5 mm spans -5 to 15 mm (DEF-M2f-01).
        ({"/rotor/magnet/r_center_mm": 5.0}, "INVALID_MAGNET_CROSSES_AXIS", IssueCategory.INVALID),
        ({"/rotor/magnet/r_center_mm": 60.0}, "RANGE_MAGNET_OUTSIDE_WINDING", IssueCategory.UNSUPPORTED_RANGE),
    ],
)
def test_a_magnet_that_misses_the_winding_blocks_compute(
    changes: dict[str, JsonValue], code: str, category: IssueCategory
) -> None:
    """Catches a magnet span that reaches physics with Ke = 0, where kv and THD come back as infinity."""
    found = [i for i in validate_design(_cf11_with(changes)) if i.code == code]
    assert [(i.severity, i.category) for i in found] == [(Severity.ERROR, category)]


@pytest.mark.req("REQ-F-14")
def test_a_magnet_overlapping_one_end_of_the_winding_passes() -> None:
    """Catches an overlap rule that also refuses a magnet covering only part of the copper span."""
    assert _blocking(_cf11_with({"/rotor/magnet/r_center_mm": 12.0})) == set()
