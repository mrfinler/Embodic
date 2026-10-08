"""Feasibility-rail values of a serpentine board for ``Layout.derived`` (interfaces.md section 5)."""

from embodic.model.design import DesignParameters
from embodic.model.winding_specs import SerpentineWindingSpec
from embodic.results import Registry
from embodic.results.traceable import InputRef, KindTag, Traceable, traced
from embodic.units import Unit


def _inputs(design: DesignParameters, spec: SerpentineWindingSpec) -> tuple[InputRef, ...]:
    values = {
        "/winding/r_inner_mm": (spec.r_inner_mm, Unit.MM),
        "/winding/r_outer_mm": (spec.r_outer_mm, Unit.MM),
        "/winding/turns": (spec.turns, Unit.ONE),
        "/winding/strands": (spec.strands, Unit.ONE),
        "/winding/trace_width_mm": (spec.trace_width_mm, Unit.MM),
        "/winding/clearance_mm": (spec.clearance_mm, Unit.MM),
        "/vias/pad_mm": (design.vias.pad_mm, Unit.MM),
    }
    return tuple(
        InputRef(pointer=pointer, value=value, unit=unit, provenance=None, kind=None, label=None)
        for pointer, (value, unit) in values.items()
    )


def serpentine_derived(
    design: DesignParameters, spec: SerpentineWindingSpec, traces_that_fit: int, rho0_mm: float,
    envelope_mm: tuple[float, float], registry: Registry,
) -> tuple[Traceable[float], ...]:  # fmt: skip
    """Return the traces per pole, the traces that fit, the level-0 fillet radius and the copper envelope."""
    inputs = _inputs(design, spec)
    rows: tuple[tuple[str, float, Unit, KindTag], ...] = (
        ("traces_per_pole", float(spec.turns * spec.strands), Unit.ONE, "count"),
        ("traces_that_fit", float(traces_that_fit), Unit.ONE, "count"),
        ("fillet_radius_level0_mm", rho0_mm, Unit.MM, "derived"),
        ("copper_r_min_mm", envelope_mm[0], Unit.MM, "derived"),
        ("copper_r_max_mm", envelope_mm[1], Unit.MM, "derived"),
    )
    return tuple(
        traced(quantity, value, unit, eq_ids=(), inputs=inputs, registry=registry, kind_tag=kind)
        for quantity, value, unit, kind in rows
    )
