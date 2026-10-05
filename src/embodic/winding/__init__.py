"""Spiral phase plan: feasibility, exact star of slots and winding factors (interfaces.md §4, EQ-08)."""

from embodic.winding.feasibility import Feasibility, balanced_coil_counts, check_feasibility
from embodic.winding.star_of_slots import CoilAssignment, assign_phases

__all__ = [
    "CoilAssignment",
    "Feasibility",
    "assign_phases",
    "balanced_coil_counts",
    "check_feasibility",
]
