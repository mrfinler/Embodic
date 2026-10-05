"""Spiral phase plan: feasibility, exact star of slots and winding factors (interfaces.md §4, EQ-08)."""

from embodic.winding.feasibility import Feasibility, balanced_coil_counts, check_feasibility
from embodic.winding.plan import SpiralWindingPlan, plan_issues, plan_spiral_winding
from embodic.winding.star_of_slots import CoilAssignment, assign_phases
from embodic.winding.winding_factors import compute_winding_factors

__all__ = [
    "CoilAssignment",
    "Feasibility",
    "SpiralWindingPlan",
    "assign_phases",
    "balanced_coil_counts",
    "check_feasibility",
    "compute_winding_factors",
    "plan_issues",
    "plan_spiral_winding",
]
