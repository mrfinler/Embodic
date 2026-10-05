"""The field table: one row per input leaf, driving forms, required checks, units and limits (ADR-0010).

Rows hold what the type hints cannot say: field kind, unit, form group, widget objectName (screens.md) and limits.
Required, neutral value, value type, choices and topologies come from the annotations (`schema.leaves`), so the table
cannot disagree with the dataclasses about them. Limits cite their source: Xcoil `normalizeParams` (engine.js
l.107-160) for serpentine, wave and shared fields, `spiral_generator_spec.md` "Inputs" for spiral fields.
"""

import dataclasses
import math
import types
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from embodic.model.schema import Choice, JsonValue, Leaf, ValueType, field_key, leaves, pattern_of
from embodic.model.vocabulary import TopologyKind
from embodic.units import MM_PER_COPPER_OZ, Unit


class FieldKind(StrEnum):
    """Design fields are choices; property fields are physical inputs that can be marked measured (D-007)."""

    DESIGN = "design"
    PROPERTY = "property"


class FieldGroup(StrEnum):
    """Form group of a field, in form order (screens.md sections 1 to 5)."""

    DESIGN = "design"
    COIL = "coil"
    PHASES = "phases"
    LAYERS = "layers"
    OUTLINE = "outline"
    FASTENERS = "fasteners"
    STACKUP = "stackup"
    ROTOR = "rotor"
    OPERATING = "operating"
    DRIVE = "drive"
    COOLING = "cooling"
    MATERIALS = "materials"
    ANALYSIS = "analysis"
    MANUFACTURING = "manufacturing"


class Sign(StrEnum):
    """Physical validity of a number; breaking it is INVALID."""

    ANY = "any"
    POSITIVE = "positive"
    NON_NEGATIVE = "non_negative"


@dataclass(frozen=True, slots=True, kw_only=True)
class Limits:
    """`sign` is validity (INVALID); `low`..`high` is the supported range (UNSUPPORTED_RANGE, Xcoil clamps to it)."""

    sign: Sign = Sign.ANY
    low: float | None = None
    high: float | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class FieldSpec:
    """One input of the design (interfaces.md section 2.3, extended with form and limit data)."""

    pointer: str  # JSON pointer into the "design" object, list items as "/stackup/layers/*/thickness_mm"
    kind: FieldKind
    unit: Unit | None  # None for enums, names and booleans
    required: bool  # required fields start empty in a blank design
    topologies: frozenset[TopologyKind]
    neutral_value: JsonValue = None  # optional fields only; written into a blank design (ADR-0010 decision 2)
    value_type: ValueType
    choices: tuple[Choice, ...] = ()
    nullable: bool = False
    variant: Choice | None = None  # union member owning the field ("copper", "arc", ...); None if all members have it
    group: FieldGroup
    widget_id: str | None  # objectName in screens.md; None where screens.md names no widget
    limits: Limits = field(default_factory=Limits)
    step: float | None = None  # Up/Down increment in the form


@dataclass(frozen=True, slots=True)
class _Row:
    kind: FieldKind
    unit: Unit | None
    group: FieldGroup
    widget_id: str | None
    limits: Limits = field(default_factory=Limits)
    step: float | None = None


D, P = FieldKind.DESIGN, FieldKind.PROPERTY
G = FieldGroup
POS, NONNEG = Sign.POSITIVE, Sign.NON_NEGATIVE
TURN_RAD = 2.0 * math.pi


def _lim(sign: Sign = Sign.ANY, low: float | None = None, high: float | None = None) -> Limits:
    return Limits(sign=sign, low=low, high=high)


_ROWS: Mapping[str, _Row] = types.MappingProxyType(
    {
        "/name": _Row(D, None, G.DESIGN, "param-design-name"),
        "/phases": _Row(D, None, G.PHASES, "param-phase-count"),
        # Coil: spiral (spiral_generator_spec.md Inputs)
        "/winding/coil/coil_count": _Row(D, None, G.COIL, "param-coil-count", _lim(POS), 1),
        "/winding/coil/r_inner_mm": _Row(D, Unit.MM, G.COIL, "param-r-inner", _lim(POS), 0.5),
        "/winding/coil/r_outer_mm": _Row(D, Unit.MM, G.COIL, "param-r-outer", _lim(POS), 0.5),
        "/winding/coil/trace_width_mm": _Row(D, Unit.MM, G.COIL, "param-trace-width", _lim(POS), 0.05),
        "/winding/coil/clearance_mm": _Row(D, Unit.MM, G.COIL, "param-clearance", _lim(POS), 0.05),
        "/winding/coil/coil_gap_mm": _Row(D, Unit.MM, G.COIL, "param-coil-gap", _lim(NONNEG), 0.05),
        "/winding/coil/turns": _Row(D, None, G.COIL, "param-turns", _lim(POS), 1),
        "/winding/coil/side_style": _Row(D, None, G.COIL, "param-side-style"),
        "/winding/coil/end_style": _Row(D, None, G.COIL, "param-end-style"),
        "/winding/coil/inner_turn_mode": _Row(D, None, G.COIL, None),
        "/winding/coil/corner_radius_mm": _Row(D, Unit.MM, G.COIL, "param-corner-radius", _lim(NONNEG), 0.1),
        "/winding/coil/end_width_outer_mm": _Row(D, Unit.MM, G.COIL, None, _lim(POS), 0.05),
        "/winding/coil/end_width_inner_mm": _Row(D, Unit.MM, G.COIL, None, _lim(POS), 0.05),
        "/winding/coil/first_coil_angle_rad": _Row(D, Unit.RAD, G.COIL, "param-first-coil-angle"),
        "/winding/coil/x_inward_sense": _Row(D, None, G.COIL, "param-x-inward-sense"),
        "/winding/coil/lead_style": _Row(D, None, G.COIL, None),
        "/winding/coil/terminal_offset_mm": _Row(D, Unit.MM, G.COIL, None, _lim(NONNEG), 0.1),
        "/winding/coil/min_side_length_mm": _Row(D, Unit.MM, G.COIL, None, _lim(POS), 0.1),
        # Coil: serpentine and wave (Xcoil normalizeParams)
        "/winding/r_inner_mm": _Row(D, Unit.MM, G.COIL, "param-r-inner", _lim(POS, 1, 1000), 0.5),
        "/winding/r_outer_mm": _Row(D, Unit.MM, G.COIL, "param-r-outer", _lim(POS, 2, 2000), 0.5),
        "/winding/turns": _Row(D, None, G.COIL, "param-turns", _lim(POS, 1, 200), 1),
        "/winding/strands": _Row(D, None, G.COIL, "param-strands", _lim(POS, 1, 50), 1),
        "/winding/trace_width_mm": _Row(D, Unit.MM, G.COIL, "param-trace-width", _lim(POS, 0.05, 20), 0.05),
        "/winding/clearance_mm": _Row(D, Unit.MM, G.COIL, "param-clearance", _lim(POS, 0.05, 20), 0.05),
        "/winding/end_width_outer_mm": _Row(D, Unit.MM, G.COIL, None, _lim(POS, 0, 20), 0.05),
        "/winding/end_width_inner_mm": _Row(D, Unit.MM, G.COIL, None, _lim(POS, 0, 20), 0.05),
        "/winding/side_style": _Row(D, None, G.COIL, "param-active-style"),
        "/winding/corner_style": _Row(D, None, G.COIL, None),
        "/winding/fillet_radius_mm": _Row(D, Unit.MM, G.COIL, "param-corner-radius", _lim(NONNEG, 0, 100), 0.1),
        "/winding/fillet_max": _Row(D, None, G.COIL, "param-fillet-max"),
        "/winding/terminal_side": _Row(D, None, G.PHASES, "param-terminal-location"),
        "/winding/start_angle_rad": _Row(
            D, Unit.RAD, G.COIL, "param-first-coil-angle", _lim(low=-TURN_RAD, high=TURN_RAD)
        ),
        "/winding/wave_style": _Row(D, None, G.COIL, "param-wave-style"),
        "/winding/bus_width_mm": _Row(D, Unit.MM, G.COIL, "param-bus-width", _lim(POS, 0.1, 20), 0.1),
        # Phases
        "/connection/topology": _Row(D, None, G.PHASES, "param-connection"),
        "/winding/phase_sequence": _Row(D, None, G.PHASES, "param-phase-sequence"),
        "/winding/assignment": _Row(D, None, G.PHASES, "param-phase-assign-mode"),
        "/winding/assignment/*/coil_index": _Row(D, None, G.PHASES, "phase-table", _lim(NONNEG)),
        "/winding/assignment/*/phase": _Row(D, None, G.PHASES, "phase-table"),
        "/winding/assignment/*/polarity": _Row(D, None, G.PHASES, "phase-table"),
        "/winding/parallel_paths": _Row(D, None, G.PHASES, None, _lim(POS), 1),
        # Layers
        "/winding/layers_per_phase": _Row(D, None, G.LAYERS, "param-layers-per-phase", _lim(POS, 1, 16), 1),
        "/winding/pair_connection": _Row(D, None, G.LAYERS, "param-pair-connection"),
        "/winding/layer_order": _Row(D, None, G.LAYERS, "param-layer-order"),
        "/winding/stack_mode": _Row(D, None, G.LAYERS, "param-stack-mode"),
        "/winding/board_gap_mm": _Row(D, Unit.MM, G.LAYERS, "param-board-gap", _lim(NONNEG, 0, 10), 0.05),
        "/winding/layers/pairs": _Row(D, None, G.LAYERS, "layer-list"),
        "/winding/layers/pairs/*/index": _Row(D, None, G.LAYERS, "layer-list", _lim(NONNEG)),
        "/winding/layers/pairs/*/layer_in": _Row(D, None, G.LAYERS, "layer-list"),
        "/winding/layers/pairs/*/layer_out": _Row(D, None, G.LAYERS, "layer-list"),
        "/winding/layers/pairs/*/rotation_rad": _Row(D, Unit.RAD, G.LAYERS, "param-pair-rotation"),
        "/winding/layers/pairs/*/phases": _Row(D, None, G.LAYERS, "layer-list"),
        "/winding/layers/series_groups": _Row(D, None, G.LAYERS, "layer-list"),
        "/vias/drill_mm": _Row(D, Unit.MM, G.LAYERS, "param-via-drill", _lim(POS, 0.1, 5), 0.05),
        "/vias/pad_mm": _Row(D, Unit.MM, G.LAYERS, "param-via-pad", _lim(POS, 0.2, 10), 0.05),
        "/vias/plating_um": _Row(P, Unit.UM, G.LAYERS, "param-via-plating", _lim(POS), 1),
        "/vias/vias_per_transition": _Row(D, None, G.LAYERS, "param-vias-per-transition", _lim(POS), 1),
        "/connection/draw_interconnect": _Row(D, None, G.PHASES, None),
        "/connection/ring_width_mm": _Row(D, Unit.MM, G.PHASES, "param-ring-width", _lim(POS, 0.1, 20), 0.1),
        "/connection/terminal_pad_mm": _Row(D, Unit.MM, G.PHASES, "param-terminal-pad", _lim(POS, 0.5, 20), 0.1),
        "/connection/terminal_drill_mm": _Row(D, Unit.MM, G.PHASES, "param-terminal-drill", _lim(NONNEG, 0, 15), 0.1),
        "/connection/neutral_pad": _Row(D, None, G.PHASES, None),
        # Board outline and bore (Xcoil outlineSides 4..16, rotation -360..360 deg, corner radius 0..500)
        "/outline/board/shape": _Row(D, None, G.OUTLINE, "param-outline-shape"),
        "/outline/board/radius_mm#circle": _Row(D, Unit.MM, G.OUTLINE, "param-outline-size", _lim(POS), 0.5),
        "/outline/board/sides#polygon": _Row(D, None, G.OUTLINE, "param-outline-sides", _lim(POS, 4, 16), 1),
        "/outline/board/across_flats_mm#polygon": _Row(D, Unit.MM, G.OUTLINE, "param-outline-size", _lim(POS), 0.5),
        "/outline/board/corner_radius_mm#polygon": _Row(
            D, Unit.MM, G.OUTLINE, "param-corner-radius-board", _lim(NONNEG, 0, 500), 0.5
        ),
        "/outline/board/rotation_rad#polygon": _Row(
            D, Unit.RAD, G.OUTLINE, "param-outline-rotation", _lim(low=-TURN_RAD, high=TURN_RAD)
        ),
        "/outline/bore": _Row(D, None, G.OUTLINE, "param-bore"),
        "/outline/bore/shape": _Row(D, None, G.OUTLINE, "param-bore"),
        "/outline/bore/radius_mm#circle": _Row(D, Unit.MM, G.OUTLINE, "param-bore", _lim(POS), 0.5),
        "/outline/bore/sides#polygon": _Row(D, None, G.OUTLINE, "param-bore", _lim(POS, 4, 16), 1),
        "/outline/bore/across_flats_mm#polygon": _Row(D, Unit.MM, G.OUTLINE, "param-bore", _lim(POS), 0.5),
        "/outline/bore/corner_radius_mm#polygon": _Row(D, Unit.MM, G.OUTLINE, "param-bore", _lim(NONNEG, 0, 500), 0.5),
        "/outline/bore/rotation_rad#polygon": _Row(
            D, Unit.RAD, G.OUTLINE, "param-bore", _lim(low=-TURN_RAD, high=TURN_RAD)
        ),
        # Fasteners (Xcoil screw count 1..64, angle -360..360 deg)
        "/outline/screws": _Row(D, None, G.FASTENERS, "screw-table"),
        "/outline/screws/*/size": _Row(D, None, G.FASTENERS, "screw-table"),
        "/outline/screws/*/fit": _Row(D, None, G.FASTENERS, "screw-table"),
        "/outline/screws/*/count": _Row(D, None, G.FASTENERS, "screw-table", _lim(POS, 1, 64), 1),
        "/outline/screws/*/pitch_radius_mm": _Row(D, Unit.MM, G.FASTENERS, "screw-table", _lim(POS), 0.5),
        "/outline/screws/*/angle_offset_rad": _Row(
            D, Unit.RAD, G.FASTENERS, "screw-table", _lim(low=-TURN_RAD, high=TURN_RAD)
        ),
        # Stack-up (Xcoil copperOz 0.25..10 oz, here as finished thickness)
        "/stackup/layers": _Row(D, None, G.STACKUP, "layer-list"),
        "/stackup/layers/*/kind": _Row(D, None, G.STACKUP, "layer-list"),
        "/stackup/layers/*/name#copper": _Row(D, None, G.STACKUP, "layer-list"),
        "/stackup/layers/*/name#dielectric": _Row(D, None, G.STACKUP, "layer-list"),
        "/stackup/layers/*/thickness_mm#copper": _Row(
            P, Unit.MM, G.STACKUP, "layer-list", _lim(POS, 0.25 * MM_PER_COPPER_OZ, 10 * MM_PER_COPPER_OZ)
        ),
        "/stackup/layers/*/thickness_mm#dielectric": _Row(D, Unit.MM, G.STACKUP, "layer-list", _lim(NONNEG)),
        "/stackup/layers/*/material#dielectric": _Row(D, None, G.STACKUP, "layer-list"),
        # Rotor and magnets (Xcoil poles 2..200, Br 0.1..2, muR 1..2, airgap 0.05..50, magnet 0.1..100 mm)
        "/rotor/poles": _Row(D, None, G.ROTOR, "param-poles", _lim(POS, 2, 200), 2),
        "/rotor/rotor_type": _Row(D, None, G.ROTOR, "param-rotor-kind"),
        "/rotor/magnet/kind": _Row(D, None, G.ROTOR, "param-magnet-shape"),
        "/rotor/magnet/pole_arc_ratio#arc": _Row(D, None, G.ROTOR, "param-magnet-arc-ratio", _lim(POS, 0.05, 1), 0.01),
        "/rotor/magnet/r_inner_mm#arc": _Row(D, Unit.MM, G.ROTOR, "param-magnet-r-inner", _lim(POS, 0.5, 2000), 0.5),
        "/rotor/magnet/r_outer_mm#arc": _Row(D, Unit.MM, G.ROTOR, "param-magnet-r-outer", _lim(POS, 1, 2000), 0.5),
        "/rotor/magnet/thickness_mm#arc": _Row(D, Unit.MM, G.ROTOR, "param-magnet-thickness", _lim(POS, 0.1, 100), 0.1),
        "/rotor/magnet/thickness_mm#block": _Row(
            D, Unit.MM, G.ROTOR, "param-magnet-thickness", _lim(POS, 0.1, 100), 0.1
        ),
        "/rotor/magnet/width_mm#block": _Row(D, Unit.MM, G.ROTOR, "param-magnet-width", _lim(POS), 0.5),
        "/rotor/magnet/length_mm#block": _Row(D, Unit.MM, G.ROTOR, "param-magnet-length", _lim(POS), 0.5),
        "/rotor/magnet/r_center_mm#block": _Row(D, Unit.MM, G.ROTOR, "param-magnet-r-center", _lim(POS), 0.5),
        "/rotor/remanence_t": _Row(P, Unit.T, G.ROTOR, "param-magnet-br", _lim(POS, 0.1, 2), 0.01),
        "/rotor/recoil_permeability": _Row(P, Unit.ONE, G.ROTOR, "param-magnet-mur", _lim(POS, 1, 2), 0.01),
        "/rotor/air_gap_mm": _Row(D, Unit.MM, G.ROTOR, "param-air-gap", _lim(POS, 0.05, 50), 0.05),
        "/rotor/back_iron_thickness_mm": _Row(D, Unit.MM, G.ROTOR, "param-back-iron", _lim(NONNEG), 0.5),
        "/rotor/magnet_offset_rad": _Row(D, Unit.RAD, G.ROTOR, None),
        # Operating point, drive, cooling (Xcoil rpm 0..1e6, current 0..1e4, tempC -50..250, ambient -60..200,
        # hConv 1..5000, vDc 0..2000)
        "/operating/speed_rpm": _Row(D, Unit.RPM, G.OPERATING, "param-speed", _lim(NONNEG, 0, 1e6), 100),
        "/operating/line_current_rms_a": _Row(D, Unit.A, G.OPERATING, "param-current", _lim(NONNEG, 0, 1e4), 0.1),
        "/operating/winding_temperature_degc": _Row(
            D, Unit.DEGC, G.OPERATING, "param-copper-temp", _lim(low=-50, high=250), 1
        ),
        "/operating/dc_link_v": _Row(D, Unit.V, G.DRIVE, "param-dc-link", _lim(POS, 0, 2000), 1),
        "/operating/modulation": _Row(D, None, G.DRIVE, "param-modulation"),
        "/operating/convection_h_w_m2k": _Row(P, Unit.W_PER_M2_K, G.COOLING, "param-h-conv", _lim(POS, 1, 5000), 1),
        "/operating/ambient_temperature_degc": _Row(
            D, Unit.DEGC, G.COOLING, "param-ambient", _lim(low=-60, high=200), 1
        ),
        # Material overrides (registry constants apply while a group is None)
        "/materials/copper_resistivity_20c_ohm_m": _Row(P, None, G.MATERIALS, None),
        "/materials/copper_resistivity_20c_ohm_m/value": _Row(P, Unit.OHM_M, G.MATERIALS, None, _lim(POS)),
        "/materials/copper_resistivity_20c_ohm_m/unit": _Row(P, None, G.MATERIALS, None),
        "/materials/copper_temp_coeff_per_k": _Row(P, None, G.MATERIALS, None),
        "/materials/copper_temp_coeff_per_k/value": _Row(P, Unit.PER_K, G.MATERIALS, None, _lim(POS)),
        "/materials/copper_temp_coeff_per_k/unit": _Row(P, None, G.MATERIALS, None),
        "/materials/copper_density_g_per_cm3": _Row(P, None, G.MATERIALS, None),
        "/materials/copper_density_g_per_cm3/value": _Row(P, Unit.G_PER_CM3, G.MATERIALS, None, _lim(POS)),
        "/materials/copper_density_g_per_cm3/unit": _Row(P, None, G.MATERIALS, None),
        "/materials/laminate_density_g_per_cm3": _Row(P, None, G.MATERIALS, None),
        "/materials/laminate_density_g_per_cm3/value": _Row(P, Unit.G_PER_CM3, G.MATERIALS, None, _lim(POS)),
        "/materials/laminate_density_g_per_cm3/unit": _Row(P, None, G.MATERIALS, None),
        # Analysis
        "/analysis/harmonics": _Row(D, None, G.ANALYSIS, None),
        "/analysis/max_segment_mm": _Row(D, Unit.MM, G.ANALYSIS, None, _lim(POS), 0.1),
        # Manufacturing rules (DrcRules, U-M1c)
        "/drc_rules/trace_clearance_mm": _Row(D, Unit.MM, G.MANUFACTURING, "param-min-space", _lim(POS), 0.01),
        "/drc_rules/via_clearance_mm": _Row(D, Unit.MM, G.MANUFACTURING, "param-min-via-space", _lim(POS), 0.01),
        "/drc_rules/edge_clearance_mm": _Row(D, Unit.MM, G.MANUFACTURING, "param-min-edge", _lim(POS), 0.01),
        "/drc_rules/hole_clearance_mm": _Row(D, Unit.MM, G.MANUFACTURING, "param-min-hole-space", _lim(POS), 0.01),
        "/drc_rules/min_trace_width_mm": _Row(D, Unit.MM, G.MANUFACTURING, "param-min-trace", _lim(POS), 0.01),
        "/drc_rules/min_drill_mm": _Row(D, Unit.MM, G.MANUFACTURING, "param-min-via", _lim(POS), 0.01),
        "/drc_rules/min_annular_ring_mm": _Row(D, Unit.MM, G.MANUFACTURING, "param-min-ring", _lim(POS), 0.01),
    }
)


def _build() -> tuple[FieldSpec, ...]:
    """Join the rows with the leaves of every topology; fail the import on a leaf without a row or a stray row."""
    by_pattern: dict[str, Leaf] = {}
    for topology in TopologyKind:
        for leaf in leaves(topology):
            key = field_key(leaf.pattern, leaf.variant)
            known = by_pattern.get(key)
            by_pattern[key] = leaf if known is None else _merge_topologies(known, leaf)
    if missing := by_pattern.keys() - _ROWS.keys():
        raise RuntimeError(f"field table has no row for {sorted(missing)}")
    if stray := _ROWS.keys() - by_pattern.keys():
        raise RuntimeError(f"field table rows match no design leaf: {sorted(stray)}")
    specs = []
    for pattern, row in _ROWS.items():
        leaf = by_pattern[pattern]
        specs.append(
            FieldSpec(
                pointer=leaf.pattern,
                variant=leaf.variant,
                kind=row.kind,
                unit=row.unit,
                required=leaf.required,
                topologies=leaf.topologies,
                neutral_value=leaf.neutral_value,
                value_type=leaf.value_type,
                choices=leaf.choices,
                nullable=leaf.nullable,
                group=row.group,
                widget_id=row.widget_id,
                limits=row.limits,
                step=row.step,
            )
        )
    return tuple(sorted(specs, key=lambda spec: list(FieldGroup).index(spec.group)))


def _merge_topologies(known: Leaf, leaf: Leaf) -> Leaf:
    if (known.value_type, known.required, known.neutral_value) != (leaf.value_type, leaf.required, leaf.neutral_value):
        raise RuntimeError(f"{leaf.pattern} differs between topologies")
    return dataclasses.replace(known, topologies=known.topologies | leaf.topologies)


FIELDS: tuple[FieldSpec, ...] = _build()
FIELD_BY_KEY: Mapping[str, FieldSpec] = types.MappingProxyType(
    {field_key(spec.pointer, spec.variant): spec for spec in FIELDS}
)
_TAG_NAMES = ("kind", "shape")


def field_for(pointer: str, values: Mapping[str, JsonValue]) -> FieldSpec:
    """Return the field of a concrete pointer; the sibling kind or shape value in `values` picks the union member."""
    pattern = pattern_of(pointer)
    parent = pointer.rsplit("/", 1)[0]
    for tag_name in _TAG_NAMES:
        tag = values.get(f"{parent}/{tag_name}")
        if isinstance(tag, str) and (spec := FIELD_BY_KEY.get(field_key(pattern, tag))) is not None:
            return spec
    return FIELD_BY_KEY[pattern]


def field_specs(topology: TopologyKind) -> tuple[FieldSpec, ...]:
    """Return the fields that apply to a topology, in form order."""
    return tuple(spec for spec in FIELDS if topology in spec.topologies)
