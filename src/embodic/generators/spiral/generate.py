"""Spiral stator of one layer pair: Q rotated copies of the canonical coil (spiral_generator_spec.md, Full stator).

Built: G1 to G7 for one layer pair with parallel sides, arc ends, sharp corners, the outer-end jog and the full
(lead arc) or half closing of G5 (revision 2026-10-05, U-E3 and U-E3b); G8 series chains of each phase on the bus
rings (legs on layer Y, ring arcs on layer X, net PHASE_x), the star or delta links and the U/V/W(/N) leads with
their pads.
Not built yet (returned as Unbuildable, never ignored): several pairs, pair rotation, phase per pair, radial sides,
straight and stadium ends, fillets (G9), the straight lead, custom terminal offset, parallel paths, screw holes, and
polygon corner radii. Open phases end on the ring vias of their first and last coil, without pads.
"""

import dataclasses
import math
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from embodic.errors import IssueCategory, Severity, Unbuildable, ValidationIssue, message_for
from embodic.generators.spiral.artwork import CoilArtwork, coil_artwork
from embodic.generators.spiral.chain import BusRings, CoilEnds, End, PhaseChain, chain_coils, norm_angle
from embodic.generators.spiral.derived import spiral_derived
from embodic.generators.spiral.interconnect import LINE_NET, Interconnect, PhaseEnd, build_interconnect, plan_links
from embodic.generators.spiral.turns import (
    Closing,
    CoilFrame,
    LoopStop,
    LoopTurn,
    Point,
    TurnKind,
    closing_for,
    loop_turns,
    max_closing,
)
from embodic.generators.spiral.turns import radial_bound as eq_3_24_bound
from embodic.geometry.circuit import Circuit, Member, ParallelGroup, PhaseCircuit
from embodic.geometry.details import SpiralDetail, TurnLimit, TurnLimitReason
from embodic.geometry.layout import BoardStack, Layout, Via, ViaRole
from embodic.geometry.outline import build_outline
from embodic.geometry.paths import CopperPath
from embodic.geometry.primitives import Arc, Line, Primitive, PrimitiveRole, path_length_mm
from embodic.geometry.transforms import Transform, mirror, reverse_path, rotate, transform_point
from embodic.model.design import DesignParameters
from embodic.model.layers import LayerPair
from embodic.model.vocabulary import ConnectionTopology, Phase, TopologyKind, ViaSpan
from embodic.model.winding_specs import EndStyle, InnerTurnMode, LeadStyle, Sense, SideStyle, SpiralWindingSpec
from embodic.results import Registry
from embodic.winding import SpiralWindingPlan, plan_spiral_winding


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


def _limiting_reason(requested: int | None, closing_limit: int, loops: int, stop: LoopStop) -> TurnLimitReason:
    if requested is not None and requested < closing_limit:
        return TurnLimitReason.USER
    if closing_limit < loops:
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


@dataclass(frozen=True, slots=True, kw_only=True)
class _ChainCopper:
    """Path and via ids the G8 chain of one phase added."""

    legs: Mapping[tuple[int, End], int]
    ring_vias: Mapping[tuple[int, End], int]
    links: Mapping[int, int]  # from coil -> ring arc path id


def _chain_copper(
    chain: PhaseChain, phase: Phase, phase_index: int, bus: BusRings, terminal_vias: Mapping[tuple[int, End], Via],
    pair: LayerPair, paths: list[CopperPath], vias: list[Via],
) -> _ChainCopper:  # fmt: skip
    """Append the radial legs (layer Y), ring vias and ring arcs (layer X) of one phase chain, in current direction."""
    net = f"PHASE_{phase.value}"
    legs: dict[tuple[int, End], int] = {}
    ring_vias: dict[tuple[int, End], int] = {}
    links: dict[int, int] = {}

    def add_path(layer: str, prim: Primitive) -> int:
        paths.append(
            CopperPath(id=len(paths), layer=layer, net=net, primitives=(prim,), phase=phase, element=None, polarity=0)
        )
        return len(paths) - 1

    for k in chain.order:
        for end in End:
            terminal = terminal_vias[(k, end)]
            a_rad = math.atan2(terminal.y_mm, terminal.x_mm)
            r_mm = bus.radius_mm(phase_index + len(Phase) * chain.levels[(k, end)])
            ring = dataclasses.replace(
                terminal, id=len(vias), x_mm=r_mm * math.cos(a_rad), y_mm=r_mm * math.sin(a_rad), role=ViaRole.RING
            )
            vias.append(ring)
            ring_vias[(k, end)] = ring.id
            outward = Line(
                x1_mm=terminal.x_mm, y1_mm=terminal.y_mm, x2_mm=ring.x_mm, y2_mm=ring.y_mm,
                width_mm=bus.leg_width_mm, role=PrimitiveRole.LEG,
            )  # fmt: skip
            legs[(k, end)] = add_path(pair.layer_out, outward if end is End.EXIT else reverse_path((outward,))[0])
    for link in chain.links:
        start = vias[ring_vias[(link.from_coil, End.EXIT)]]
        arc = Arc(
            cx_mm=0.0, cy_mm=0.0, r_mm=bus.radius_mm(phase_index + len(Phase) * link.level),
            start_rad=math.atan2(start.y_mm, start.x_mm), sweep_rad=link.signed_sweep_rad,
            width_mm=bus.ring_width_mm, role=PrimitiveRole.RING,
        )  # fmt: skip
        links[link.from_coil] = add_path(pair.layer_in, arc)
    return _ChainCopper(legs=legs, ring_vias=ring_vias, links=links)


def _with_chain(member: Member, coil: int, chained: _ChainCopper) -> Member:
    """Extend a coil's member by its entry and exit legs, ring vias and the ring arc to the next coil."""
    link = (chained.links[coil],) if coil in chained.links else ()
    return Member(
        path_ids=(chained.legs[(coil, End.ENTRY)], *member.path_ids, chained.legs[(coil, End.EXIT)], *link),
        via_ids=(chained.ring_vias[(coil, End.ENTRY)], *member.via_ids, chained.ring_vias[(coil, End.EXIT)]),
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class _CoilCopper:
    """Both layers and the three vias of every coil, with what the G8 chain needs."""

    paths: tuple[CopperPath, ...]
    vias: tuple[Via, ...]
    members: Mapping[int, Member]
    terminal_vias: Mapping[tuple[int, End], Via]
    ends: Mapping[Phase, list[CoilEnds]]


def _coil_copper(
    design: DesignParameters, plan: SpiralWindingPlan, spec: SpiralWindingSpec, art: CoilArtwork
) -> _CoilCopper:
    """Rotate the canonical X and mirrored Y artwork to every coil, in current direction per polarity."""
    paths: list[CopperPath] = []
    vias: list[Via] = []
    coil_members: dict[int, Member] = {}
    terminal_vias: dict[tuple[int, End], Via] = {}
    coil_ends: dict[Phase, list[CoilEnds]] = {phase: [] for phase in Phase}
    coil, pair = spec.coil, spec.layers.pairs[0]
    x_canonical = art.primitives
    y_canonical = reverse_path(mirror(x_canonical, 0.0))  # mirror about the coil axis, traversed outward
    via_points = (art.terminal, art.centre_via, (art.terminal[0], -art.terminal[1]))
    terminal_rad = math.atan2(art.terminal[1], art.terminal[0])
    for assignment in plan.assignment:
        k, sign = assignment.coil_index, assignment.polarity
        angle = coil.first_coil_angle_rad + k * 2 * math.pi / coil.coil_count
        net = f"PHASE_{assignment.phase.value}"
        x_prims, y_prims = rotate(x_canonical, angle), rotate(y_canonical, angle)
        if sign == 1:
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
                    polarity=sign,
                )
            )
        coil_vias = _coil_vias(design, pair, via_points, angle, net, first_id=len(vias))
        vias += coil_vias
        in_order = coil_vias if sign == 1 else coil_vias[::-1]
        terminal_vias[(k, End.ENTRY)], terminal_vias[(k, End.EXIT)] = in_order[0], in_order[-1]
        coil_members[k] = Member(path_ids=tuple(path_ids), via_ids=tuple(v.id for v in in_order))
        coil_ends[assignment.phase].append(
            CoilEnds(
                coil=k,
                entry_rad=norm_angle(angle + sign * terminal_rad),
                exit_rad=norm_angle(angle - sign * terminal_rad),
            )
        )

    return _CoilCopper(
        paths=tuple(paths), vias=tuple(vias), members=coil_members, terminal_vias=terminal_vias, ends=coil_ends
    )


def _closings(
    frame: CoilFrame, loops: tuple[LoopTurn, ...], requested: int | None
) -> tuple[Closing, Closing] | Unbuildable:
    """Return the closing to build and the one with the most turns (G5), or why none fits."""
    best = max_closing(frame, loops)
    if best is None:
        return Unbuildable(issues=(_issue("UNBUILDABLE_ZERO_TURNS", ("/winding/coil/turns",)),))
    closing = best if requested is None else closing_for(frame, loops, requested)
    if closing is None or closing.n > best.n:
        return Unbuildable(issues=(_issue("UNBUILDABLE_TURNS_EXCEED_LIMIT", ("/winding/coil/turns",), best.n),))
    return closing, best


def _interconnect(
    design: DesignParameters, phase_ends: Mapping[tuple[Phase, int], PhaseEnd], r_bus_mm: float, clearance_mm: float,
    pair: LayerPair, first_path_id: int, first_via_id: int,
) -> Interconnect | Unbuildable:  # fmt: skip
    """Star or delta links and leads beyond the bus rings (G8); nothing for open phases or a hidden interconnect."""
    connection = design.connection
    if not connection.draw_interconnect or connection.topology is ConnectionTopology.OPEN:
        return Interconnect(paths=(), vias=(), pads=(), r_max_mm=0.0)
    links = plan_links(connection.topology, phase_ends)
    if links is None:
        return Unbuildable(issues=(_issue("UNBUILDABLE_INTERCONNECT_CROSSING", ("/connection/topology",)),))
    return build_interconnect(
        connection, phase_ends, links, r_bus_mm, clearance_mm, pair.layer_in, pair.layer_out,
        first_path_id=first_path_id, first_via_id=first_via_id, first_pad_id=0,
    )  # fmt: skip


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
    closings = _closings(frame, loops, coil.turns)
    if isinstance(closings, Unbuildable):
        return closings
    closing, best = closings
    n = closing.n
    reason = _limiting_reason(coil.turns, best.n, len(loops), stop)
    art = coil_artwork(frame, closing, design.connection.ring_width_mm)
    copper = _coil_copper(design, plan, spec, art)
    paths, vias = list(copper.paths), list(copper.vias)
    coil_members, terminal_vias, coil_ends = copper.members, copper.terminal_vias, copper.ends

    bus = BusRings.of(frame, design.connection.ring_width_mm)
    phase_groups: dict[Phase, list[ParallelGroup]] = {}
    phase_ends: dict[tuple[Phase, int], PhaseEnd] = {}
    top_level = 0
    for phase_index, phase in enumerate(Phase):
        chain = chain_coils(sorted(coil_ends[phase], key=lambda c: c.entry_rad))
        if chain is None:
            return Unbuildable(issues=(_issue("UNBUILDABLE_PHASE_CHAIN_UNROUTABLE", ("/connection/ring_width_mm",)),))
        top_level = max(top_level, len(Phase) * chain.n_levels - 1)
        chained = _chain_copper(chain, phase, phase_index, bus, terminal_vias, pair, paths, vias)
        phase_groups[phase] = [ParallelGroup(members=(_with_chain(coil_members[k], k, chained),)) for k in chain.order]
        phase_ends[(phase, 1)] = PhaseEnd(phase=phase, sign=1, via=vias[chained.ring_vias[(chain.order[0], End.ENTRY)]])
        phase_ends[(phase, -1)] = PhaseEnd(
            phase=phase, sign=-1, via=vias[chained.ring_vias[(chain.order[-1], End.EXIT)]]
        )

    r_bus_mm = bus.radius_mm(top_level) + bus.half_width_mm
    ic = _interconnect(design, phase_ends, r_bus_mm, coil.clearance_mm, pair, len(paths), len(vias))
    if isinstance(ic, Unbuildable):
        return ic
    paths += ic.paths
    vias += ic.vias
    r_max_mm = max(r_bus_mm, ic.r_max_mm)

    envelope = (coil.r_inner_mm, r_max_mm)
    length_mm = path_length_mm(art.primitives)
    detail = SpiralDetail(
        plan=plan,
        turns_achieved=n,
        turn_limit=TurnLimit(
            radial_bound=eq_3_24_bound(frame),
            loops_trapezoidal=sum(t.kind is TurnKind.TRAPEZOID for t in loops),
            loops_triangular=sum(t.kind is TurnKind.TRIANGLE for t in loops),
            eye_limit=best.n,
            limiting_reason=reason,
        ),
        track_length_per_coil_layer_mm=MappingProxyType({"X": length_mm, "Y": length_mm}),
    )
    copper_z = design.stackup.copper_z_mm()
    layout = Layout(
        topology=TopologyKind.SPIRAL,
        copper_layers=(pair.layer_in, pair.layer_out),
        copper_z_mm=MappingProxyType({name: copper_z[name] for name in (pair.layer_in, pair.layer_out)}),
        paths=tuple(paths),
        vias=tuple(vias),
        pads=ic.pads,
        outline=build_outline(design.outline, envelope),
        circuit=Circuit(
            phases=tuple(
                PhaseCircuit(phase=phase, groups=tuple(groups), terminal_net=LINE_NET[phase])
                for phase, groups in phase_groups.items()
            ),
            topology=design.connection.topology,
            interconnect_path_ids=tuple(p.id for p in ic.paths),
        ),
        symmetry=None,
        envelope_mm=envelope,
        detail=detail,
        derived=spiral_derived(design, coil, n, best.n, length_mm, envelope, registry),
    )
    return BoardStack(boards=(layout,), board_thickness_mm=design.stackup.board_thickness_mm(), board_gap_mm=0.0)
