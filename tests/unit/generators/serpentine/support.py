"""Designs for the serpentine unit tests: Xcoil's default preset on an outline that clears its copper."""

import dataclasses

from tests.unit.model.designs import COPPER_2OZ_MM

from embodic.model.design import DesignParameters
from embodic.model.stackup import generate_even_stackup
from embodic.model.winding_specs import StackMode


def with_winding(design: DesignParameters, **changes: object) -> DesignParameters:
    """Return ``design`` with serpentine fields replaced."""
    return dataclasses.replace(design, winding=dataclasses.replace(design.winding, **changes))  # type: ignore[type-var]


def with_copper_count(design: DesignParameters, count: int) -> DesignParameters:
    """Return ``design`` with an even stack-up of ``count`` 2 oz copper layers on a 1.6 mm board."""
    return dataclasses.replace(design, stackup=generate_even_stackup(count, COPPER_2OZ_MM, 1.6))


def per_phase(design: DesignParameters, gap_mm: float = 0.1, layers_per_phase: int = 2) -> DesignParameters:
    """Return ``design`` as one board per phase; the stack-up then describes one board (UT-GEN-03)."""
    changed = with_winding(design, stack_mode=StackMode.ONE_BOARD_PER_PHASE, board_gap_mm=gap_mm,
                           layers_per_phase=layers_per_phase)  # fmt: skip
    return with_copper_count(changed, layers_per_phase)
