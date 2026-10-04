"""Via inputs (interfaces.md section 2.1); Phase 2 builds through vias only (D-015)."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class ViaSpec:
    """Drill, pad and plating of every winding via; `plating_um` is a property input (EQ-11)."""

    drill_mm: float
    pad_mm: float
    plating_um: float
    vias_per_transition: int = 1
