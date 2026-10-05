"""Spiral stator of one layer pair: Q rotated copies of the canonical coil (spiral_generator_spec.md, Full stator).

Built: G1 to G7 for one layer pair with parallel sides, arc ends, sharp corners and the radial-then-arc lead.
Not built yet (returned as Unbuildable, never ignored): several pairs, pair rotation, phase per pair, radial sides,
straight and stadium ends, fillets (G9), the straight lead, custom terminal offset, parallel paths, screw holes, and
polygon corner radii. G8 phase chaining and star or delta links are not built: the Circuit lists every coil, and
``interconnect_path_ids`` stays empty.
"""

import math
from types import MappingProxyType

from embodic.errors import IssueCategory, Severity, Unbuildable, ValidationIssue, message_for
from embodic.generators.spiral.artwork import coil_artwork
from embodic.generators.spiral.turns import CoilFrame, LoopStop, Point, TurnKind, eye, eye_limited_turns, loop_turns
from embodic.generators.spiral.turns import radial_bound as eq_3_24_bound
from embodic.geometry.circuit import Circuit, Member, ParallelGroup, PhaseCircuit
from embodic.geometry.details import SpiralDetail, TurnLimit, TurnLimitReason
from embodic.geometry.layout import BoardStack, Layout, Via, ViaRole
from embodic.geometry.outline import build_outline
from embodic.geometry.paths import CopperPath
from embodic.geometry.primitives import path_length_mm
from embodic.geometry.transforms import Transform, mirror, reverse_path, rotate, transform_point
from embodic.model.design import DesignParameters
from embodic.model.layers import LayerPair
from embodic.model.vocabulary import Phase, TopologyKind, ViaSpan
from embodic.model.winding_specs import EndStyle, InnerTurnMode, LeadStyle, Sense, SideStyle, SpiralWindingSpec
from embodic.results import Registry
from embodic.winding import plan_spiral_winding

TERMINAL_NET = MappingProxyType({Phase.A: "U", Phase.B: "V", Phase.C: "W"})  # D-019: phase A is U


def _issue(code: str, pointers: tuple[str, ...], limit: int | None = None) -> ValidationIssue:
    return ValidationIssue(
        code=code,
        category=IssueCategory.UNBUILDABLE,
        severity=Severity.ERROR,
        message=message_for(code).format(limit=limit),
        pointers=pointers,
        limit=limit,
    )


def _unsupported(design: DesignParameters, spec: SpiralWindingSpec) -> tuple[str, ...]:
    """Pointers of inputs whose value selects geometry this generator does not build yet."""
    coil, pairs = spec.coil, spec.layers.pairs
    checks = {
        "/winding/layers/pairs": len(pairs) != 1 or pairs[0].rotation_rad != 0.0 or pairs[0].phases is not None,
        "/winding/coil/side_style": coil.side_style is not SideStyle.PARALLEL,
        "/winding/coil/end_style": coil.end_style is not EndStyle.ARC,
        "/winding/coil/corner_radius_mm": coil.corner_radius_mm != 0.0,
        "/winding/coil/lead_style": coil.lead_style is not LeadStyle.RADIAL_THEN_ARC,
        "/winding/coil/terminal_offset_mm": coil.terminal_offset_mm is not None,
        "/winding/coil/x_inward_sense": coil.x_inward_sense is not Sense.CW,
        "/winding/coil/inner_turn_mode": coil.inner_turn_mode is not InnerTurnMode.MOVING,
        "/winding/parallel_paths": spec.parallel_paths != 1,
        "/vias/vias_per_transition": design.vias.vias_per_transition != 1,
        "/outline/screws": bool(design.outline.screws),
        "/outline/board/corner_radius_mm": getattr(design.outline.board, "corner_radius_mm", 0.0) != 0.0,
    }
    return tuple(pointer for pointer, unsupported in checks.items() if unsupported)


def _out_of_range(design: DesignParameters, spec: SpiralWindingSpec) -> tuple[str, ...]:
    """Pointers of inputs the geometry cannot use: a zero turn pitch would never end the loop rule."""
    coil, vias = spec.coil, design.vias
    lengths = {
        "/winding/coil/trace_width_mm": coil.trace_width_mm,
        "/winding/coil/end_width_outer_mm": coil.end_width_outer_mm or coil.trace_width_mm,
        "/winding/coil/end_width_inner_mm": coil.end_width_inner_mm or coil.trace_width_mm,
        "/vias/pad_mm": vias.pad_mm,
        "/connection/ring_width_mm": design.connection.ring_width_mm,
    }
    bad = [p for p, v in lengths.items() if not (math.isfinite(v) and v > 0)]
    others = {
        "/winding/coil/clearance_mm": coil.clearance_mm,
        "/winding/coil/coil_gap_mm": coil.coil_gap_mm,
        "/winding/coil/r_inner_mm": coil.r_inner_mm,
        "/winding/coil/first_coil_angle_rad": coil.first_coil_angle_rad,
        "/winding/coil/min_side_length_mm": 0.0 if coil.min_side_length_mm is None else coil.min_side_length_mm,
    }
    bad += [p for p, v in others.items() if not (math.isfinite(v) and v >= 0)]
    if not (math.isfinite(coil.r_outer_mm) and coil.r_outer_mm > coil.r_inner_mm):
        bad.append("/winding/coil/r_outer_mm")
    if coil.coil_count < 3:
        bad.append("/winding/coil/coil_count")
    return tuple(bad)


def _refusal(design: DesignParameters, spec: SpiralWindingSpec) -> Unbuildable | None:
    if pointers := _out_of_range(design, spec):
        return Unbuildable(issues=(_issue("UNBUILDABLE_SPIRAL_INPUT_OUT_OF_RANGE", pointers),))
    if pointers := _unsupported(design, spec):
        return Unbuildable(issues=(_issue("UNBUILDABLE_SPIRAL_OPTION_NOT_IMPLEMENTED", pointers),))
    return None


def _limiting_reason(requested: int | None, eye_limit: int, loops: int, stop: LoopStop) -> TurnLimitReason:
    if requested is not None and requested < eye_limit:
        return TurnLimitReason.USER
    if eye_limit < loops:
        return TurnLimitReason.EYE
    return TurnLimitReason.LATERAL if stop is LoopStop.LATERAL else TurnLimitReason.RADIAL


def _coil_vias(
    design: DesignParameters, pair: LayerPair, points: tuple[Point, Point, Point], angle_rad: float, net: str,
    first_id: int,
) -> list[Via]:  # fmt: skip
    """Entry terminal, centre and exit terminal vias of the canonical coil, rotated to ``angle_rad``."""
    roles = (ViaRole.TERMINAL, ViaRole.CENTRE, ViaRole.TERMINAL)
    vias = []
    for k, (point, role) in enumerate(zip(points, roles, strict=True)):
        x_mm, y_mm = transform_point(Transform(rotation_rad=angle_rad), *point)
        vias.append(
            Via(
                id=first_id + k,
                x_mm=x_mm,
                y_mm=y_mm,
                drill_mm=design.vias.drill_mm,
                pad_mm=design.vias.pad_mm,
                role=role,
                span=ViaSpan.THROUGH,
                layer_from=pair.layer_in,
                layer_to=pair.layer_out,
                net=net,
            )
        )
    return vias


def generate_spiral(design: DesignParameters, registry: Registry) -> BoardStack | Unbuildable:
    """Build one board; a winding other than SpiralWindingSpec raises TypeError (a dispatch bug, not user input)."""
    spec = design.winding
    if not isinstance(spec, SpiralWindingSpec):
        raise TypeError(f"generate_spiral needs a spiral winding, got {type(spec).__name__}")
    if refusal := _refusal(design, spec):
        return refusal
    plan = plan_spiral_winding(design, spec, registry)
    if isinstance(plan, Unbuildable):
        return plan

    coil, pair = spec.coil, spec.layers.pairs[0]
    frame = CoilFrame.of(coil, design.vias.pad_mm)
    loops, stop = loop_turns(frame)
    eye_limit = eye_limited_turns(frame, loops)
    if eye_limit == 0 or eye(frame, loops, eye_limit).via_radius_mm <= frame.offset_mm(eye_limit):
        return Unbuildable(issues=(_issue("UNBUILDABLE_ZERO_TURNS", ("/winding/coil/turns",)),))
    if coil.turns is not None and not 1 <= coil.turns <= eye_limit:
        return Unbuildable(issues=(_issue("UNBUILDABLE_TURNS_EXCEED_LIMIT", ("/winding/coil/turns",), eye_limit),))
    n = eye_limit if coil.turns is None else coil.turns
    reason = _limiting_reason(coil.turns, eye_limit, len(loops), stop)
    turns = loops[:n]
    art = coil_artwork(frame, turns, eye(frame, loops, n).via_radius_mm, design.connection.ring_width_mm)
    x_canonical = art.primitives
    y_canonical = reverse_path(mirror(x_canonical, 0.0))  # mirror about the coil axis, traversed outward

    paths: list[CopperPath] = []
    vias: list[Via] = []
    phase_groups: dict[Phase, list[ParallelGroup]] = {phase: [] for phase in Phase}
    via_points = (art.terminal, art.centre_via, (art.terminal[0], -art.terminal[1]))
    for assignment in plan.assignment:
        k = assignment.coil_index
        angle = coil.first_coil_angle_rad + k * 2 * math.pi / coil.coil_count
        net = f"PHASE_{assignment.phase.value}"
        x_prims, y_prims = rotate(x_canonical, angle), rotate(y_canonical, angle)
        if assignment.polarity == 1:
            layers_in_order = ((pair.layer_in, x_prims), (pair.layer_out, y_prims))
        else:  # a negative coil is the same copper entered at its CW-side terminal (G8)
            layers_in_order = ((pair.layer_out, reverse_path(y_prims)), (pair.layer_in, reverse_path(x_prims)))
        path_ids = []
        for layer, prims in layers_in_order:
            path_ids.append(len(paths))
            paths.append(
                CopperPath(
                    id=len(paths),
                    layer=layer,
                    net=net,
                    primitives=prims,
                    phase=assignment.phase,
                    element=k,
                    polarity=assignment.polarity,
                )
            )
        coil_vias = _coil_vias(design, pair, via_points, angle, net, first_id=len(vias))
        vias += coil_vias
        via_ids = [v.id for v in coil_vias]
        if assignment.polarity == -1:
            via_ids.reverse()
        member = Member(path_ids=tuple(path_ids), via_ids=tuple(via_ids))
        phase_groups[assignment.phase].append(ParallelGroup(members=(member,)))

    envelope = (coil.r_inner_mm, max(coil.r_outer_mm, math.hypot(*art.terminal) + design.vias.pad_mm / 2))
    length_mm = path_length_mm(x_canonical)
    detail = SpiralDetail(
        plan=plan,
        turns_achieved=n,
        turn_limit=TurnLimit(
            radial_bound=eq_3_24_bound(frame),
            loops_trapezoidal=sum(t.kind is TurnKind.TRAPEZOID for t in loops),
            loops_triangular=sum(t.kind is TurnKind.TRIANGLE for t in loops),
            eye_limit=eye_limit,
            limiting_reason=reason,
        ),
        track_length_per_coil_layer_mm=MappingProxyType({"X": length_mm, "Y": path_length_mm(y_canonical)}),
    )
    copper_z = design.stackup.copper_z_mm()
    layout = Layout(
        topology=TopologyKind.SPIRAL,
        copper_layers=(pair.layer_in, pair.layer_out),
        copper_z_mm=MappingProxyType({name: copper_z[name] for name in (pair.layer_in, pair.layer_out)}),
        paths=tuple(paths),
        vias=tuple(vias),
        pads=(),
        outline=build_outline(design.outline, envelope),
        circuit=Circuit(
            phases=tuple(
                PhaseCircuit(phase=phase, groups=tuple(groups), terminal_net=TERMINAL_NET[phase])
                for phase, groups in phase_groups.items()
            ),
            topology=design.connection.topology,
            interconnect_path_ids=(),
        ),
        symmetry=None,
        envelope_mm=envelope,
        detail=detail,
    )
    return BoardStack(boards=(layout,), board_thickness_mm=design.stackup.board_thickness_mm(), board_gap_mm=0.0)
