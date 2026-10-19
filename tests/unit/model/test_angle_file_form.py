"""DEF-UV15-04 (REQ-F-14): an angle whose degree value is not finite is refused, and compute returns the issue.

The file form stores degrees, and `design_hash` hashes the file form. A finite angle in radians above
`math.radians(sys.float_info.max)` has an infinite degree value, which canonical JSON refuses. Every field whose unit is
`Unit.RAD` is covered, so a new angle field fails `test_every_angle_field_has_a_setup` until it joins the table.
"""

import math
import sys

import pytest

from embodic.api import compute
from embodic.errors import IssueCategory, Severity
from embodic.io.canonical import RAD_PATTERNS, design_hash, has_file_form
from embodic.io.examples import load_example
from embodic.model.design import DesignParameters
from embodic.model.draft import DesignDraft, DraftIncomplete, draft_from_design, parse_draft
from embodic.model.fields import FIELDS
from embodic.model.provenance import derive_provenance
from embodic.model.schema import JsonValue
from embodic.model.validate import validate_design

# Largest angle in radians whose degrees are finite: a property of IEEE doubles, found here by stepping, not read from
# the product.
LARGEST_RAD = math.radians(sys.float_info.max)
FIRST_BEYOND_RAD = math.nextafter(LARGEST_RAD, math.inf)
BORE_POLYGON: dict[str, JsonValue] = {
    "/outline/bore/shape": "polygon",
    "/outline/bore/sides": 6,
    "/outline/bore/across_flats_mm": 12.0,
    "/outline/bore/corner_radius_mm": 0.0,
}

# pattern -> (example, concrete pointer in it, extra leaves that make the field apply)
SETUPS: dict[str, tuple[str, str, dict[str, JsonValue]]] = {
    "/winding/coil/first_coil_angle_rad": (
        "spiral_12c16p_default",
        "/winding/coil/first_coil_angle_rad",
        {},
    ),
    "/winding/start_angle_rad": ("serpentine_16p_example", "/winding/start_angle_rad", {}),
    "/winding/layers/pairs/*/rotation_rad": (
        "spiral_12c16p_default",
        "/winding/layers/pairs/0/rotation_rad",
        {},
    ),
    "/outline/board/rotation_rad": ("spiral_12c16p_default", "/outline/board/rotation_rad", {}),
    "/outline/bore/rotation_rad": (
        "spiral_12c16p_default",
        "/outline/bore/rotation_rad",
        BORE_POLYGON,
    ),
    "/outline/screws/*/angle_offset_rad": (
        "serpentine_16p_example",
        "/outline/screws/0/angle_offset_rad",
        {},
    ),
    "/rotor/magnet_offset_rad": ("spiral_12c16p_default", "/rotor/magnet_offset_rad", {}),
}
UNLIMITED = sorted(
    spec.pointer for spec in FIELDS if spec.pointer in SETUPS and spec.limits.low is None and spec.limits.high is None
)


def _design_with(pattern: str, value: float) -> tuple[DesignParameters, str]:
    example, pointer, extra = SETUPS[pattern]
    draft = draft_from_design(load_example(example)[1])
    parsed = parse_draft(DesignDraft(topology=draft.topology, values={**draft.values, **extra, pointer: value}))
    assert not isinstance(parsed, DraftIncomplete), parsed
    return parsed, pointer


@pytest.mark.req("REQ-F-14")
def test_the_boundary_used_here_is_the_last_angle_with_finite_degrees() -> None:
    """Catches a wrong oracle: the degrees of the boundary are finite and those of the next float are not."""
    assert math.isfinite(math.degrees(LARGEST_RAD))
    assert math.isinf(math.degrees(FIRST_BEYOND_RAD))


@pytest.mark.req("REQ-F-14")
def test_every_angle_field_has_a_setup() -> None:
    """Catches a new angle field that no test below exercises."""
    assert set(SETUPS) == RAD_PATTERNS


@pytest.mark.req("REQ-F-14")
@pytest.mark.parametrize("pattern", sorted(SETUPS))
@pytest.mark.parametrize("sign", [1, -1])
@pytest.mark.parametrize("magnitude", [FIRST_BEYOND_RAD, 1e307])
def test_an_angle_with_no_finite_degrees_is_refused_by_validation(pattern: str, sign: int, magnitude: float) -> None:
    """Catches an angle field that lets a radian value with infinite degrees pass validation."""
    design, pointer = _design_with(pattern, sign * magnitude)
    assert not has_file_form(design)
    found = [i for i in validate_design(design) if i.pointers == (pointer,)]
    code = "RANGE_ABOVE_SUPPORTED" if sign > 0 else "RANGE_BELOW_SUPPORTED"
    assert [(i.code, i.severity, i.category) for i in found] == [
        (code, Severity.ERROR, IssueCategory.UNSUPPORTED_RANGE)
    ]


@pytest.mark.req("REQ-F-14")
@pytest.mark.parametrize("pattern", sorted(SETUPS))
@pytest.mark.parametrize("sign", [1, -1])
def test_compute_returns_the_issue_for_an_angle_with_no_finite_degrees(pattern: str, sign: int) -> None:
    """Catches compute raising from `design_hash` before validation refuses the value (PR-05)."""
    design, pointer = _design_with(pattern, sign * FIRST_BEYOND_RAD)
    outcome = compute(design, derive_provenance(design, None, ()))
    assert outcome is not None
    assert outcome.design == design
    assert not outcome.ok
    code = "RANGE_ABOVE_SUPPORTED" if sign > 0 else "RANGE_BELOW_SUPPORTED"
    assert [(i.code, i.pointers) for i in outcome.issues if i.severity is Severity.ERROR] == [(code, (pointer,))]
    assert outcome.design_hash == "", "a design without a file form has no hash"
    assert outcome.boards is None and outcome.analysis is None


@pytest.mark.req("REQ-F-14")
@pytest.mark.parametrize("pattern", UNLIMITED)
@pytest.mark.parametrize("sign", [1, -1])
def test_the_largest_angle_with_finite_degrees_passes_validation_and_hashes(pattern: str, sign: int) -> None:
    """Catches a bound tighter than the file form needs: the boundary angle is valid and has a design hash."""
    design, pointer = _design_with(pattern, sign * LARGEST_RAD)
    assert [i for i in validate_design(design) if pointer in i.pointers] == []
    assert has_file_form(design)
    assert design_hash(design).startswith("sha256:")
