"""Feasibility-rail values of a spiral board for ``Layout.derived`` (interfaces.md section 5, spec Outputs)."""

from embodic.model.design import DesignParameters
from embodic.model.winding_specs import SpiralCoilSpec
from embodic.results import Registry
from embodic.results.traceable import InputRef, KindTag, Traceable, traced
from embodic.units import Unit


def _coil_inputs(design: DesignParameters, coil: SpiralCoilSpec) -> tuple[InputRef, ...]:
    values = {
        "/winding/coil/coil_count": (coil.coil_count, Unit.ONE),
        "/winding/coil/r_inner_mm": (coil.r_inner_mm, Unit.MM),
        "/winding/coil/r_outer_mm": (coil.r_outer_mm, Unit.MM),
        "/winding/coil/trace_width_mm": (coil.trace_width_mm, Unit.MM),
        "/winding/coil/clearance_mm": (coil.clearance_mm, Unit.MM),
        "/winding/coil/coil_gap_mm": (coil.coil_gap_mm, Unit.MM),
        "/vias/pad_mm": (design.vias.pad_mm, Unit.MM),
        "/connection/ring_width_mm": (design.connection.ring_width_mm, Unit.MM),
    }
    return tuple(
        InputRef(pointer=pointer, value=value, unit=unit, provenance=None, kind=None, label=None)
        for pointer, (value, unit) in values.items()
    )


def spiral_derived(
    design: DesignParameters, coil: SpiralCoilSpec, turns: int, turn_limit: int, track_length_mm: float,
    envelope_mm: tuple[float, float], registry: Registry,
) -> tuple[Traceable[float], ...]:  # fmt: skip
    """Return turns built, the turn limit, the track length per coil-layer and the copper envelope."""
    inputs = _coil_inputs(design, coil)
    rows: tuple[tuple[str, float, Unit, KindTag], ...] = (
        ("turns_per_coil_per_layer", float(turns), Unit.ONE, "count"),
        ("turn_limit_per_coil_per_layer", float(turn_limit), Unit.ONE, "count"),
        ("track_length_per_coil_layer_mm", track_length_mm, Unit.MM, "derived"),
        ("copper_r_min_mm", envelope_mm[0], Unit.MM, "derived"),
        ("copper_r_max_mm", envelope_mm[1], Unit.MM, "derived"),
    )
    return tuple(
        traced(quantity, value, unit, eq_ids=(), inputs=inputs, registry=registry, kind_tag=kind)
        for quantity, value, unit, kind in rows
    )
