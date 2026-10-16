"""D-053a / DEF-U-M6h-01: a board thinner than its copper is refused, never clamped into a stack that looks valid.

Ruling: docs/phase3/engineering/gr07_case3_ruling.md, "Proposed change" items 1, 3 and 4.
"""

import dataclasses
import math

import pytest

from embodic.errors import IssueCategory, Severity
from embodic.model.stackup import DielectricLayer, generate_even_stackup
from embodic.model.validate import even_stackup_issues, validate_design

from .designs import spiral_design

pytestmark = pytest.mark.req("REQ-F-04", "REQ-F-14")

COPPER_2OZ_MM = 2 * 0.0348  # units.py MM_PER_COPPER_OZ, `assumption`
COPPER_8X2OZ_MM = math.fsum([COPPER_2OZ_MM] * 8)


def test_eight_layers_of_2_oz_on_a_0p4_mm_board_give_one_error_naming_board_and_copper():
    """Catches a refusal that is missing, a warning, or one that names the wrong value, limit or pointer."""
    (found,) = even_stackup_issues(8, COPPER_2OZ_MM, 0.4)
    assert (found.code, found.severity, found.category) == (
        "INVALID_STACKUP_COPPER_EXCEEDS_BOARD",
        Severity.ERROR,
        IssueCategory.INVALID,
    )
    assert found.pointers == ("/stackup/layers",)
    assert found.value == 0.4
    assert found.limit == pytest.approx(COPPER_8X2OZ_MM, abs=1e-12, rel=0.0)
    assert found.message == (
        "Board thickness must exceed the total copper thickness of 0.5568 mm, "
        "so that every dielectric layer is thicker than 0."
    )


@pytest.mark.parametrize("copper_count", [1, 2, 8])
def test_a_board_exactly_as_thick_as_its_copper_is_refused_and_1e_6_mm_more_is_accepted(copper_count):
    """Catches an off-by-boundary rule (< instead of <=), which would accept 0 mm dielectrics at B = n x t."""
    copper_mm = math.fsum([COPPER_2OZ_MM] * copper_count)
    assert [i.code for i in even_stackup_issues(copper_count, COPPER_2OZ_MM, copper_mm)] == [
        "INVALID_STACKUP_COPPER_EXCEEDS_BOARD"
    ]
    board_mm = copper_mm + 1e-6
    assert even_stackup_issues(copper_count, COPPER_2OZ_MM, board_mm) == ()
    stackup = generate_even_stackup(copper_count, COPPER_2OZ_MM, board_mm)
    dielectrics = [layer.thickness_mm for layer in stackup.layers if isinstance(layer, DielectricLayer)]
    assert len(dielectrics) == max(1, copper_count - 1)
    assert all(thickness > 0.0 for thickness in dielectrics), dielectrics
    assert stackup.board_thickness_mm() == pytest.approx(board_mm, abs=1e-12, rel=0.0)


@pytest.mark.parametrize(("copper_count", "board_mm"), [(8, 0.4), (8, COPPER_8X2OZ_MM), (1, COPPER_2OZ_MM), (1, 0.01)])
def test_the_generator_raises_instead_of_clamping_a_dielectric_to_0(copper_count, board_mm):
    """Catches a returning clamp max(0, dielectric): copper on copper and a board the user did not enter."""
    with pytest.raises(ValueError, match="board thickness"):
        generate_even_stackup(copper_count, COPPER_2OZ_MM, board_mm)


@pytest.mark.parametrize("thickness_mm", [0.0, -0.01])
def test_a_hand_edited_dielectric_of_0_mm_or_less_is_refused_at_its_own_pointer(thickness_mm):
    """Catches the dielectric limit staying non-negative, so a 0 mm dielectric passes validation (ruling item 4)."""
    design = spiral_design()
    layers = list(design.stackup.layers)
    position = next(i for i, layer in enumerate(layers) if isinstance(layer, DielectricLayer))
    layers[position] = dataclasses.replace(layers[position], thickness_mm=thickness_mm)
    thin = dataclasses.replace(design, stackup=dataclasses.replace(design.stackup, layers=tuple(layers)))
    found = [i for i in validate_design(thin) if f"/stackup/layers/{position}/thickness_mm" in i.pointers]
    assert [(i.code, i.severity) for i in found] == [("INVALID_NON_POSITIVE", Severity.ERROR)]
