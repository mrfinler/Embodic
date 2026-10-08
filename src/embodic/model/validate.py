"""Field checks and cross-field rules of a design; user input yields issues, never exceptions (REQ-F-14).

Field checks read type and limits from the field table. Cross-field rules port Xcoil `normalizeParams` (engine.js
l.107-160) for serpentine and wave and the spiral input rules of `spiral_generator_spec.md`. Winding balance and
turn feasibility are the generators' job (UNBUILDABLE), not checked here.
"""

import math
import types
from collections.abc import Callable, Iterator, Mapping, Sequence

from embodic.errors import IssueCategory, Severity, Suggestion, ValidationIssue, message_for
from embodic.model.design import DesignParameters
from embodic.model.fields import FieldSpec, Sign, field_for
from embodic.model.schema import JsonValue, ValueType, design_values
from embodic.model.stackup import CopperLayer
from embodic.model.winding_specs import (
    PairConnection,
    SerpentineWindingSpec,
    SpiralWindingSpec,
    StackMode,
    WaveWindingSpec,
)
from embodic.units import Unit

RADIAL_SPAN_MIN_MM = 0.5  # Xcoil R_ORDER: rOut > rIn + 0.5
VIA_RING_MIN_MM = 0.1  # Xcoil VIA_RING: viaPad >= viaDrill + 0.1
TERMINAL_RING_MIN_MM = 0.3  # Xcoil PAD_RING: terminalPad >= terminalDrill + 0.3 when drilled
TRACES_MAX = 400  # Xcoil TOO_MANY: turns x strands <= 400
SPIRAL_PHASES = 3

_CATEGORY_BY_PREFIX = {"INVALID_": IssueCategory.INVALID, "RANGE_": IssueCategory.UNSUPPORTED_RANGE}


def issue(
    code: str,
    pointers: Sequence[str],
    *,
    value: float | int | str | None = None,
    limit: float | int | None = None,
    unit: Unit | None = None,
    suggestion: Suggestion | None = None,
    severity: Severity = Severity.ERROR,
) -> ValidationIssue:
    """Build an issue whose category follows the code prefix and whose message names limit and unit."""
    category = next(c for prefix, c in _CATEGORY_BY_PREFIX.items() if code.startswith(prefix))
    unit_text = f" {unit.display()}" if unit is not None and unit.display() else ""
    message = message_for(code).format(limit=limit, unit=unit_text)
    return ValidationIssue(
        code=code,
        category=category,
        severity=severity,
        message=message,
        pointers=tuple(pointers),
        value=value,
        limit=limit,
        suggestion=suggestion,
    )


def _is_int(value: JsonValue) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: JsonValue) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value)


_SHAPE_CHECKS: Mapping[ValueType, Callable[[FieldSpec, JsonValue], bool]] = types.MappingProxyType(
    {
        ValueType.INT: lambda _, v: _is_int(v),
        ValueType.FLOAT: lambda _, v: _is_number(v),
        ValueType.BOOL: lambda _, v: isinstance(v, bool),
        ValueType.TEXT: lambda _, v: isinstance(v, str),
        ValueType.CHOICE: lambda spec, v: not isinstance(v, bool) and isinstance(v, str | int) and v in spec.choices,
        ValueType.INT_LIST: lambda _, v: isinstance(v, list) and all(_is_int(i) for i in v),
        ValueType.INT_GROUPS: lambda _, v: (
            isinstance(v, list) and all(isinstance(g, list) and all(_is_int(i) for i in g) for g in v)
        ),
        ValueType.CHOICE_LIST: lambda spec, v: (
            isinstance(v, list) and all(isinstance(i, str) and i in spec.choices for i in v)
        ),
        ValueType.GROUP: lambda _, v: False,
        ValueType.LIST: lambda _, v: v == [],
    }
)


def check_value(spec: FieldSpec, pointer: str, value: JsonValue) -> tuple[ValidationIssue, ...]:
    """Check one value against its field: type, choices, validity sign and the supported range."""
    if value is None and spec.nullable:
        return ()
    if not _SHAPE_CHECKS[spec.value_type](spec, value):
        if spec.value_type is ValueType.INT and _is_number(value):
            return (issue("INVALID_NOT_INTEGER", [pointer], value=_scalar_or_none(value)),)
        code = "INVALID_CHOICE" if spec.value_type is ValueType.CHOICE else "INVALID_TYPE"
        return (issue(code, [pointer], value=_scalar_or_none(value)),)
    if spec.value_type is ValueType.TEXT and isinstance(value, str) and not value.strip():
        return (issue("INVALID_EMPTY_TEXT", [pointer]),)
    if isinstance(value, int | float) and not isinstance(value, bool):
        return tuple(_check_limits(spec, pointer, value))
    return ()


def _scalar_or_none(value: JsonValue) -> float | int | str | None:
    return value if isinstance(value, int | float | str) and not isinstance(value, bool) else None


def _check_limits(spec: FieldSpec, pointer: str, number: float) -> Iterator[ValidationIssue]:
    limits = spec.limits
    if limits.sign is Sign.POSITIVE and not number > 0:
        yield issue("INVALID_NON_POSITIVE", [pointer], value=number, limit=0, unit=spec.unit)
        return
    if limits.sign is Sign.NON_NEGATIVE and number < 0:
        yield issue("INVALID_NEGATIVE", [pointer], value=number, limit=0, unit=spec.unit)
        return
    if limits.low is not None and number < limits.low:
        clamp = Suggestion(pointer=pointer, proposed_value=limits.low, reason="Xcoil clamps to the supported range.")
        yield issue(
            "RANGE_BELOW_SUPPORTED", [pointer], value=number, limit=limits.low, unit=spec.unit, suggestion=clamp
        )
    elif limits.high is not None and number > limits.high:
        clamp = Suggestion(pointer=pointer, proposed_value=limits.high, reason="Xcoil clamps to the supported range.")
        yield issue(
            "RANGE_ABOVE_SUPPORTED", [pointer], value=number, limit=limits.high, unit=spec.unit, suggestion=clamp
        )


def _poles_even(design: DesignParameters) -> Iterator[ValidationIssue]:
    poles = design.rotor.poles
    if poles % 2:
        fix = Suggestion(pointer="/rotor/poles", proposed_value=poles + 1, reason="Xcoil rounds up to an even count.")
        yield issue("INVALID_POLE_COUNT_ODD", ["/rotor/poles"], value=poles, suggestion=fix)


def _radial_order(design: DesignParameters) -> Iterator[ValidationIssue]:
    match design.winding:
        case SpiralWindingSpec(coil=coil):
            if not coil.r_outer_mm > coil.r_inner_mm:
                yield issue("INVALID_ORDER", ["/winding/coil/r_inner_mm", "/winding/coil/r_outer_mm"])
        case SerpentineWindingSpec() | WaveWindingSpec() as spec:
            pointers = ["/winding/r_inner_mm", "/winding/r_outer_mm"]
            if not spec.r_outer_mm > spec.r_inner_mm:
                yield issue("INVALID_ORDER", pointers)
            elif not spec.r_outer_mm > spec.r_inner_mm + RADIAL_SPAN_MIN_MM:
                yield issue("INVALID_RADIAL_SPAN", pointers, value=spec.r_outer_mm, limit=RADIAL_SPAN_MIN_MM)


def _magnet_order(design: DesignParameters) -> Iterator[ValidationIssue]:
    magnet = design.rotor.magnet
    if magnet.kind == "arc" and not magnet.r_outer_mm > magnet.r_inner_mm:
        yield issue("INVALID_MAGNET_ORDER", ["/rotor/magnet/r_inner_mm", "/rotor/magnet/r_outer_mm"])


def _serpentine_layers(design: DesignParameters) -> Iterator[ValidationIssue]:
    spec = design.winding
    if not isinstance(spec, SerpentineWindingSpec):
        return
    count = spec.layers_per_phase
    if count != 1 and count % 2:
        fix = Suggestion(
            pointer="/winding/layers_per_phase", proposed_value=count + 1, reason="Xcoil rounds up to an even count."
        )
        yield issue("INVALID_LAYERS_PER_PHASE", ["/winding/layers_per_phase"], value=count, suggestion=fix)
    pairs = 1 if count == 1 else count // 2
    if spec.pair_connection is PairConnection.SERIES and pairs > design.rotor.poles // 2:
        pointers = ["/winding/layers_per_phase", "/winding/pair_connection", "/rotor/poles"]
        yield issue("INVALID_SERIES_PAIRS_EXCEED_POLE_PAIRS", pointers, value=pairs, limit=design.rotor.poles // 2)
    copper = len(design.stackup.copper_layers())
    expected = count if spec.stack_mode is StackMode.ONE_BOARD_PER_PHASE else design.phases * count
    if copper != expected:
        pointers = ["/stackup/layers", "/winding/layers_per_phase", "/winding/stack_mode"]
        yield issue("INVALID_SERPENTINE_COPPER_COUNT", pointers, value=copper, limit=expected)
    if spec.turns * spec.strands > TRACES_MAX:
        yield issue(
            "RANGE_TOO_MANY_TRACES",
            ["/winding/turns", "/winding/strands"],
            value=spec.turns * spec.strands,
            limit=TRACES_MAX,
        )


def _via_rings(design: DesignParameters) -> Iterator[ValidationIssue]:
    vias, connection = design.vias, design.connection
    if vias.pad_mm < vias.drill_mm + VIA_RING_MIN_MM:
        yield issue("INVALID_VIA_RING", ["/vias/drill_mm", "/vias/pad_mm"], value=vias.pad_mm, limit=VIA_RING_MIN_MM)
    drill_mm = connection.terminal_drill_mm
    if drill_mm > 0 and connection.terminal_pad_mm < drill_mm + TERMINAL_RING_MIN_MM:
        pointers = ["/connection/terminal_drill_mm", "/connection/terminal_pad_mm"]
        yield issue("INVALID_TERMINAL_PAD_RING", pointers, value=connection.terminal_pad_mm, limit=TERMINAL_RING_MIN_MM)


def _spiral_inputs(design: DesignParameters) -> Iterator[ValidationIssue]:
    spec = design.winding
    if not isinstance(spec, SpiralWindingSpec):
        return
    if design.phases != SPIRAL_PHASES:
        yield issue("INVALID_SPIRAL_PHASES", ["/phases"], value=design.phases, limit=SPIRAL_PHASES)
    coil = spec.coil
    if coil.coil_gap_mm < coil.clearance_mm:
        spacing = Suggestion(
            pointer="/winding/coil/coil_gap_mm",
            proposed_value=coil.clearance_mm,
            reason="The generator uses the trace spacing when the gap is smaller.",
        )
        yield issue(
            "RANGE_COIL_GAP_BELOW_CLEARANCE",
            ["/winding/coil/coil_gap_mm", "/winding/coil/clearance_mm"],
            value=coil.coil_gap_mm,
            limit=coil.clearance_mm,
            suggestion=spacing,
            severity=Severity.INFO,
        )
    for name, width_mm in (
        ("end_width_outer_mm", coil.end_width_outer_mm),
        ("end_width_inner_mm", coil.end_width_inner_mm),
    ):
        if width_mm is not None and width_mm < coil.trace_width_mm:
            pointers = [f"/winding/coil/{name}", "/winding/coil/trace_width_mm"]
            yield issue("INVALID_END_WIDTH_BELOW_TRACE", pointers, value=width_mm, limit=coil.trace_width_mm)
    yield from _layer_pairs(design, spec)


def _layer_pairs(design: DesignParameters, spec: SpiralWindingSpec) -> Iterator[ValidationIssue]:
    copper_count = len(design.stackup.copper_layers())
    if copper_count % 2:
        yield issue("RANGE_SPIRAL_COPPER_COUNT_ODD", ["/stackup/layers"], value=copper_count, severity=Severity.WARNING)
    copper = {layer.name for layer in design.stackup.copper_layers()}
    indices = [pair.index for pair in spec.layers.pairs]
    for position, pair in enumerate(spec.layers.pairs):
        base = f"/winding/layers/pairs/{position}"
        for side in ("layer_in", "layer_out"):
            if getattr(pair, side) not in copper:
                yield issue("INVALID_PAIR_LAYER_UNKNOWN", [f"{base}/{side}"], value=getattr(pair, side))
        if pair.layer_in == pair.layer_out:
            yield issue("INVALID_PAIR_LAYER_SAME", [f"{base}/layer_in", f"{base}/layer_out"], value=pair.layer_in)
        if indices.count(pair.index) > 1:
            yield issue("INVALID_PAIR_INDEX_DUPLICATE", [f"{base}/index"], value=pair.index)
    grouped = sorted(index for group in spec.layers.series_groups for index in group)
    if grouped != sorted(indices):
        yield issue("INVALID_SERIES_GROUPS", ["/winding/layers/series_groups"])


def _stackup(design: DesignParameters) -> Iterator[ValidationIssue]:
    layers = design.stackup.layers
    if not any(isinstance(layer, CopperLayer) for layer in layers):
        yield issue("INVALID_STACKUP_NO_COPPER", ["/stackup/layers"])
    names = [layer.name for layer in layers]
    for position, name in enumerate(names):
        if names.index(name) != position:
            yield issue("INVALID_LAYER_NAME_DUPLICATE", [f"/stackup/layers/{position}/name"], value=name)


def _harmonics(design: DesignParameters) -> Iterator[ValidationIssue]:
    for position, order in enumerate(design.analysis.harmonics):
        if order < 1 or order % 2 == 0:
            yield issue("INVALID_HARMONIC", [f"/analysis/harmonics/{position}"], value=order)


CROSS_FIELD_RULES: tuple[Callable[[DesignParameters], Iterator[ValidationIssue]], ...] = (
    _poles_even,
    _radial_order,
    _magnet_order,
    _serpentine_layers,
    _via_rings,
    _spiral_inputs,
    _stackup,
    _harmonics,
)


def validate_design(design: DesignParameters) -> tuple[ValidationIssue, ...]:
    """Single-field ranges and cross-field relations (INVALID, UNSUPPORTED_RANGE).

    Winding and geometry feasibility are the generators' job (UNBUILDABLE).
    """
    values = design_values(design)
    field_issues = (
        found for pointer, value in values.items() for found in check_value(field_for(pointer, values), pointer, value)
    )
    return (*field_issues, *(found for rule in CROSS_FIELD_RULES for found in rule(design)))
