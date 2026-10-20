"""Supported ranges that bound compute work or keep a formula finite (DEF-M2f-02, DEF-M2f-03)."""

import dataclasses
import warnings

import pytest

from embodic.api import ComputeOptions, compute
from embodic.errors import IssueCategory, Severity
from embodic.io.examples import load_example
from embodic.model.design import DesignParameters
from embodic.model.draft import DesignDraft, DraftIncomplete, draft_from_design, parse_draft
from embodic.model.provenance import derive_provenance
from embodic.model.schema import JsonValue
from embodic.model.validate import OUTLINE_MAX_MM, validate_design


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


def _serpentine_with(changes: dict[str, JsonValue]) -> DesignParameters:
    draft = draft_from_design(load_example("serpentine_16p_example")[1])
    parsed = parse_draft(DesignDraft(topology=draft.topology, values={**draft.values, **changes}))
    assert not isinstance(parsed, DraftIncomplete)
    return parsed


@pytest.mark.req("REQ-F-14")
@pytest.mark.parametrize(
    ("pointer", "value"),
    [
        # DEF-M7a-01: a 1e30 mm pitch circle overflowed the DRC grid index (INTERNAL_DRC_FAILED).
        ("/outline/screws/0/pitch_radius_mm", 1e30),
        ("/outline/screws/0/pitch_radius_mm", OUTLINE_MAX_MM * (1 + 1e-12)),
        # A 1e30 mm hole covered the whole board and computed without a message.
        ("/outline/screws/0/hole_diameter_mm", 1e30),
        ("/outline/screws/0/hole_diameter_mm", 2 * OUTLINE_MAX_MM * (1 + 1e-12)),
    ],
)
def test_a_screw_length_beyond_the_largest_board_blocks_compute(pointer: str, value: float) -> None:
    """Catches a screw pattern sized off every supported board reaching the generator and the DRC grid."""
    found = [i for i in validate_design(_serpentine_with({pointer: value})) if i.pointers == (pointer,)]
    assert [(i.code, i.severity, i.category) for i in found] == [
        ("RANGE_ABOVE_SUPPORTED", Severity.ERROR, IssueCategory.UNSUPPORTED_RANGE)
    ]


@pytest.mark.req("REQ-F-14")
@pytest.mark.parametrize("example_id", ["spiral_12c16p_default", "serpentine_16p_example", "wave_16p_example"])
def test_bv21_a_1e30_mm_screw_pitch_radius_is_an_error_and_compute_raises_no_internal_issue(example_id: str) -> None:
    """BV-21 (D-054e). Catches DEF-M7a-01 on a topology the serpentine-only test above does not reach.

    The spiral example has no screws, so it takes the serpentine example's screw pattern before the pitch radius is set.
    """
    pointer = "/outline/screws/0/pitch_radius_mm"
    design = load_example(example_id)[1]
    screws = design.outline.screws or load_example("serpentine_16p_example")[1].outline.screws
    pattern = dataclasses.replace(screws[0], pitch_radius_mm=1e30)
    far = dataclasses.replace(design, outline=dataclasses.replace(design.outline, screws=(pattern, *screws[1:])))
    found = [i for i in validate_design(far) if pointer in i.pointers]
    assert [(i.code, i.severity, i.category) for i in found] == [
        ("RANGE_ABOVE_SUPPORTED", Severity.ERROR, IssueCategory.UNSUPPORTED_RANGE)
    ]
    outcome = compute(far, derive_provenance(far, None, ()))
    assert outcome is not None
    assert [i.code for i in outcome.issues if i.code.startswith("INTERNAL_")] == []


@pytest.mark.req("REQ-F-14")
@pytest.mark.parametrize(
    "changes",
    [
        {"/outline/screws/0/pitch_radius_mm": OUTLINE_MAX_MM},
        {"/outline/screws/0/hole_diameter_mm": 2 * OUTLINE_MAX_MM},
    ],
)
def test_screw_lengths_on_the_largest_board_limits_pass_validation(changes: dict[str, JsonValue]) -> None:
    """Catches a screw bound tighter than the board outline maximum it derives from."""
    (pointer,) = changes
    assert [i.code for i in validate_design(_serpentine_with(changes)) if pointer in i.pointers] == []


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
    assert _blocking(_cf11_with({"/rotor/magnet/r_center_mm": 13.0})) == set()


@pytest.mark.req("REQ-F-14")
@pytest.mark.parametrize("r_center_mm", [12.0, 12.99])
def test_a_block_magnet_inner_radius_below_half_its_width_is_refused(r_center_mm: float) -> None:
    """Catches DEF-M2fix3-02: EQ-04 takes arcsin(w / 2r), so a span reaching r < w / 2 gave NaN with only a warning.

    CF-11 magnet: width 6 mm, length 20 mm. Centre 12 mm puts the inner radius at 2 mm, below 3 mm, and the centre
    itself is still above w / 2, so a check on the centre radius would miss it.
    """
    found = [i for i in validate_design(_cf11_with({"/rotor/magnet/r_center_mm": r_center_mm})) if "WIDER" in i.code]
    assert [(i.code, i.severity, i.category, i.value, i.limit) for i in found] == [
        (
            "INVALID_MAGNET_WIDER_THAN_RADIUS",
            Severity.ERROR,
            IssueCategory.INVALID,
            r_center_mm - 10.0,
            3.0,
        )
    ]
    assert found[0].pointers == ("/rotor/magnet/r_center_mm", "/rotor/magnet/length_mm", "/rotor/magnet/width_mm")


@pytest.mark.req("REQ-F-14")
def test_a_block_magnet_inner_radius_of_exactly_half_its_width_passes() -> None:
    """Catches an off-by-one bound: arcsin(1) is finite, so r = w / 2 is a valid radius of the field kernel."""
    assert [i for i in validate_design(_cf11_with({"/rotor/magnet/r_center_mm": 13.0})) if "WIDER" in i.code] == []


@pytest.mark.req("REQ-F-14")
def test_compute_refuses_the_narrow_radius_magnet_before_the_field_kernel_runs() -> None:
    """Catches the leak: the design reached physics, where arcsin of a value above 1 warned and gave NaN."""
    design = _cf11_with({"/rotor/magnet/r_center_mm": 12.0})
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        outcome = compute(design, derive_provenance(design, None, ()), options=ComputeOptions(run_drc=False))
    assert outcome is not None
    assert [i.code for i in outcome.issues if i.severity is Severity.ERROR] == ["INVALID_MAGNET_WIDER_THAN_RADIUS"]
    assert outcome.analysis is None
