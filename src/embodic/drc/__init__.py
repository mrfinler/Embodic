"""Design-rule check of any Layout under rule D-006 (interfaces.md section 7)."""

from embodic.drc.kernels import min_distance_arc_arc, min_distance_line_arc, min_distance_line_line
from embodic.drc.report import (
    DRC_EPSILON_MM,
    CancelToken,
    DrcCheckKind,
    DrcCheckSummary,
    DrcReport,
    DrcViolation,
)

__all__ = [
    "DRC_EPSILON_MM",
    "CancelToken",
    "DrcCheckKind",
    "DrcCheckSummary",
    "DrcReport",
    "DrcViolation",
    "min_distance_arc_arc",
    "min_distance_line_arc",
    "min_distance_line_line",
]
