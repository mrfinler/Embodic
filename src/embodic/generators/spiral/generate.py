"""Spiral stator of one layer stack: Q rotated copies of the canonical coil (spiral_generator_spec.md, Full stator).

Built: G1 to G7 with parallel or radial sides, arc or straight ends, sharp corners or G9 concentric fillets (parallel
sides with arc ends), the outer-end jog and the full (lead arc) or half closing of G5 (revision 2026-10-05, U-E3 and
U-E3b); layer pairs in parallel (one shared centre via) and in series groups (G5 k centre vias, G6 series via fan of
revision U-E6, DRC-checked and refused when a rule fails, D-020); G8 series chains of each phase on the bus rings (legs
on layer Y, ring arcs on layer X, net PHASE_x), the star or delta links and the U/V/W(/N) leads with their pads; the
screw holes of every fastener pattern, refused when one breaks an edge or hole-to-hole keep-out.
Pair rotation is built when every pair shares it (option M3 with one rotation, D-024 default 0); pairs rotated against
each other are refused (G6). Not built yet (returned as Unbuildable, never ignored): phase per pair, stadium ends,
series groups with straight ends, tapers (G9), the straight lead, custom terminal offset, parallel paths, and polygon
corner radii. Open phases end on the ring vias of their first and last coil, without pads.
"""

import dataclasses
import math
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType

from embodic.drc import run_drc
from embodic.drc.report import violates
from embodic.errors import IssueCategory, Severity, Unbuildable, ValidationIssue, message_for
from embodic.generators.fasteners import keep_out_issues
from embodic.generators.spiral.artwork import CoilArtwork, coil_artwork, sharp_artwork
from embodic.generators.spiral.chain import BusRings, CoilEnds, End, PhaseChain, chain_coils, norm_angle
from embodic.generators.spiral.derived import spiral_derived
from embodic.generators.spiral.fillets import Corner, CornerKind, concentric_allowed, corners, radius_sequence
from embodic.generators.spiral.interconnect import LINE_NET, Interconnect, PhaseEnd, build_interconnect, plan_links
from embodic.generators.spiral.series import GroupCopper, SeriesCoil, SeriesFailure, series_coil
from embodic.generators.spiral.turns import (
    MAX_TURNS_PER_LAYER,
    Closing,
    CoilFrame,
    FullClosing,
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
from embodic.geometry.fasteners import place_holes
from embodic.geometry.layout import BoardOutline, BoardStack, Layout, Via, ViaRole
from embodic.geometry.outline import build_outline
from embodic.geometry.paths import CopperPath
from embodic.geometry.primitives import Arc, Line, Primitive, PrimitiveRole, path_length_mm
from embodic.geometry.transforms import Transform, mirror, reverse_path, rotate, transform_point
from embodic.model.design import DesignParameters
from embodic.model.layers import LayerPair
from embodic.model.vocabulary import ConnectionTopology, Phase, TopologyKind, ViaSpan
from embodic.model.winding_specs import EndStyle, InnerTurnMode, LeadStyle, Sense, SpiralWindingSpec
from embodic.results import Registry
from embodic.winding import SpiralWindingPlan, plan_spiral_winding


class TurnsExceedCause(StrEnum):
    """Who exceeds the limit of UNBUILDABLE_TURNS_EXCEED_LIMIT; the issue carries it as ``value`` (D-033e)."""

    USER_CAP = "user_cap"  # the requested turn count is above the limit
    LOOP_RULE = "loop_rule"  # more turns fit between the radii than the cap, whatever was requested


def _issue(code: str, pointers: tuple[str, ...], limit: int | None = None, value: str | None = None) -> ValidationIssue:
    return ValidationIssue(
        code=code,
        category=IssueCategory.UNBUILDABLE,
        severity=Severity.ERROR,
        message=message_for(code).format(limit=limit),
        pointers=pointers,
        value=value,
        limit=limit,
    )


def _unsupported(design: DesignParameters, spec: SpiralWindingSpec) -> tuple[str, ...]:
    """Pointers of inputs whose value selects geometry this generator does not build yet."""
    coil, pairs = spec.coil, spec.layers.pairs
    checks = {
        "/winding/layers/pairs": any(p.phases is not None for p in pairs),
        "/winding/layers/series_groups": not all(spec.layers.series_groups)
        or sorted(i for group in spec.layers.series_groups for i in group) != sorted(p.index for p in pairs),
        "/winding/coil/lead_style": coil.lead_style is not LeadStyle.RADIAL_THEN_ARC,
        # The G6 fan cuts outer arc 0 at the stub angle; straight ends have a chord there, which G6 does not cover.
        "/winding/coil/end_style": coil.end_style is EndStyle.STRAIGHT and len(spec.layers.series_groups) > 1,
        "/winding/coil/terminal_offset_mm": coil.terminal_offset_mm is not None,
        "/winding/coil/x_inward_sense": coil.x_inward_sense is not Sense.CW,
        "/winding/coil/inner_turn_mode": coil.inner_turn_mode is not InnerTurnMode.MOVING,
        "/winding/parallel_paths": spec.parallel_paths != 1,
        "/vias/vias_per_transition": design.vias.vias_per_transition != 1,
        "/outline/board/corner_radius_mm": getattr(design.outline.board, "corner_radius_mm", 0.0) != 0.0,
    }
    return tuple(pointer for pointer, unsupported in checks.items() if unsupported)


def _out_of_range(design: DesignParameters, spec: SpiralWindingSpec) -> tuple[str, ...]:
    """Pointers of inputs the geometry cannot use (D-030): a zero or NaN pitch, or a width the DRC would flag."""
    coil, vias = spec.coil, design.vias
    positive = {
        "/winding/coil/end_width_outer_mm": coil.end_width_outer_mm or coil.trace_width_mm,
        "/winding/coil/end_width_inner_mm": coil.end_width_inner_mm or coil.trace_width_mm,
        "/winding/coil/clearance_mm": coil.clearance_mm,
        "/winding/coil/r_inner_mm": coil.r_inner_mm,
        "/vias/pad_mm": vias.pad_mm,
        "/connection/ring_width_mm": design.connection.ring_width_mm,
    }
    bad = [p for p, v in positive.items() if not (math.isfinite(v) and v > 0)]
    width_mm = coil.trace_width_mm
    if not (math.isfinite(width_mm) and width_mm > 0) or violates(width_mm, design.drc_rules.min_trace_width_mm):
        bad.append("/winding/coil/trace_width_mm")
    non_negative = {
        "/winding/coil/coil_gap_mm": coil.coil_gap_mm,
        "/winding/coil/min_side_length_mm": 0.0 if coil.min_side_length_mm is None else coil.min_side_length_mm,
    }
    bad += [p for p, v in non_negative.items() if not (math.isfinite(v) and v >= 0)]
    if not math.isfinite(coil.first_coil_angle_rad):
        bad.append("/winding/coil/first_coil_angle_rad")
    bad += [f"/winding/layers/pairs/{k}/rotation_rad" for k, p in enumerate(spec.layers.pairs)
            if not math.isfinite(p.rotation_rad)]  # fmt: skip
    if not (math.isfinite(coil.r_outer_mm) and coil.r_outer_mm > coil.r_inner_mm):
        bad.append("/winding/coil/r_outer_mm")
    if coil.coil_count < 3:
        bad.append("/winding/coil/coil_count")
    return tuple(bad)


def _turns_exceed_limit(cause: TurnsExceedCause, limit: int) -> Unbuildable:
    issue = _issue("UNBUILDABLE_TURNS_EXCEED_LIMIT", ("/winding/coil/turns",), limit, cause)
    return Unbuildable(issues=(issue,))


def _refusal(design: DesignParameters, spec: SpiralWindingSpec) -> Unbuildable | None:
    if pointers := _out_of_range(design, spec):
        return Unbuildable(issues=(_issue("UNBUILDABLE_SPIRAL_INPUT_OUT_OF_RANGE", pointers),))
    if spec.coil.turns is not None and spec.coil.turns > MAX_TURNS_PER_LAYER:
        return _turns_exceed_limit(TurnsExceedCause.USER_CAP, MAX_TURNS_PER_LAYER)
    issues = []
    if spec.coil.end_style is EndStyle.STADIUM:
        issues.append(_issue("UNBUILDABLE_UNSUPPORTED_END_STYLE", ("/winding/coil/end_style",)))
    if len({p.rotation_rad for p in spec.layers.pairs}) > 1:  # pairs join coil by coil (G6, U-E6)
        issues.append(_issue("UNBUILDABLE_PAIRS_ROTATED_APART", ("/winding/layers/pairs",)))
    # Edge and hole-to-hole gaps depend on the outline inputs alone; build_outline does not read the copper envelope.
    outline = build_outline(design.outline, (spec.coil.r_inner_mm, spec.coil.r_outer_mm))
    issues += keep_out_issues(place_holes(design.outline.screws), outline, design.drc_rules)
    if pointers := _unsupported(design, spec):
        issues.append(_issue("UNBUILDABLE_SPIRAL_OPTION_NOT_IMPLEMENTED", pointers))
    return Unbuildable(issues=tuple(issues)) if issues else None


def _limiting_reason(requested: int | None, closing_limit: int, loops: int, stop: LoopStop) -> TurnLimitReason:
    if requested is not None and requested < closing_limit:
        return TurnLimitReason.USER
    if closing_limit < loops:
        return TurnLimitReason.EYE
    return TurnLimitReason.LATERAL if stop is LoopStop.LATERAL else TurnLimitReason.RADIAL


def _coil_vias(
    design: DesignParameters, span: tuple[str, str], points: tuple[Point, ...], angle_rad: float, net: str,
    first_id: int,
) -> list[Via]:  # fmt: skip
    """Ring and centre vias of the canonical coil in current order, rotated to ``angle_rad``.

    Ring vias and centre vias alternate: entry terminal, centre 0, transfer 1, ..., centre k - 1, exit terminal.
    """
    k = len(points) // 2
    roles = [ViaRole.TERMINAL if i in (0, 2 * k) else ViaRole.CENTRE if i % 2 else ViaRole.TRANSFER
             for i in range(2 * k + 1)]  # fmt: skip
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
                layer_from=span[0],
                layer_to=span[1],
                net=net,
            )
        )
    return vias


def _canonical_vias(art: CoilArtwork) -> tuple[Point, Point, Point]:
    """Entry terminal, centre via and the mirrored exit terminal of the canonical coil."""
    return (art.terminal, art.centre_via, (art.terminal[0], -art.terminal[1]))


def _coil_violations(design: DesignParameters, pair: LayerPair, art: CoilArtwork) -> int:
    """DRC violations of the canonical coil alone: layer X and its three vias (layer Y is its mirror)."""
    net = "PHASE_A"
    path = CopperPath(id=0, layer=pair.layer_in, net=net, primitives=art.primitives, phase=Phase.A, element=0,
                      polarity=1)  # fmt: skip
    layers = (pair.layer_in, pair.layer_out)
    copper_z = design.stackup.copper_z_mm()
    layout = Layout(
        topology=TopologyKind.SPIRAL,
        copper_layers=layers,
        copper_z_mm=MappingProxyType({name: copper_z[name] for name in layers}),
        paths=(path,),
        vias=tuple(_coil_vias(design, layers, _canonical_vias(art), 0.0, net, first_id=0)),
        pads=(),
        outline=BoardOutline(outer=(), cutouts=(), holes=()),
        circuit=Circuit(phases=(), topology=design.connection.topology, interconnect_path_ids=()),
        symmetry=None,
        envelope_mm=(art.terminal[0], art.terminal[0]),
    )
    report = run_drc(layout, design.drc_rules, use_symmetry=False)
    assert report is not None  # None only when cancelled, and no token is passed
    return report.violation_count


def _artwork(
    design: DesignParameters, frame: CoilFrame, closing: Closing, pair: LayerPair, rho_mm: float
) -> tuple[CoilArtwork, float, Mapping[tuple[CornerKind, int], Corner]]:
    """G9: fillet at rho, shrinking by 0.7 up to 12 times until the fillets fit; sharp corners (rho 0) otherwise.

    A fillet fits when every primitive it trims keeps its direction and the coil has no DRC violation its sharp
    version does not have.
    """
    bus_mm = design.connection.ring_width_mm
    sharp = sharp_artwork(frame, closing, bus_mm)
    if rho_mm <= 0.0 or not concentric_allowed(frame):
        return sharp, 0.0, {}
    baseline = _coil_violations(design, pair, sharp)
    for r_mm in radius_sequence(rho_mm):
        filleted = corners(frame, closing, r_mm)
        art = None if filleted is None else coil_artwork(frame, closing, bus_mm, filleted)
        if art is not None and filleted is not None and _coil_violations(design, pair, art) <= baseline:
            return art, r_mm, filleted
    return sharp, 0.0, {}


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


def _with_chain(groups: tuple[tuple[Member, ...], ...], coil: int, chained: _ChainCopper) -> list[ParallelGroup]:
    """Series groups of one coil: entry leg, each series group's parallel layer-pair routes, exit leg and ring arc.

    When every series group has one pair, the whole coil is one member: a single route needs no parallel node.
    """
    link = (chained.links[coil],) if coil in chained.links else ()
    entry = Member(path_ids=(chained.legs[(coil, End.ENTRY)],), via_ids=(chained.ring_vias[(coil, End.ENTRY)],))
    exit_ = Member(path_ids=(chained.legs[(coil, End.EXIT)], *link), via_ids=(chained.ring_vias[(coil, End.EXIT)],))
    if all(len(group) == 1 for group in groups):
        routes = (entry, *(group[0] for group in groups), exit_)
        joined = Member(
            path_ids=tuple(i for route in routes for i in route.path_ids),
            via_ids=tuple(i for route in routes for i in route.via_ids),
        )
        return [ParallelGroup(members=(joined,))]
    return [
        ParallelGroup(members=(entry,)),
        *(ParallelGroup(members=group) for group in groups),
        ParallelGroup(members=(exit_,)),
    ]


@dataclass(frozen=True, slots=True, kw_only=True)
class _CoilCopper:
    """Both layers and the three vias of every coil, with what the G8 chain needs."""

    paths: tuple[CopperPath, ...]
    vias: tuple[Via, ...]
    members: Mapping[int, tuple[tuple[Member, ...], ...]]  # per series group in current order, one route per pair
    terminal_vias: Mapping[tuple[int, End], Via]
    ends: Mapping[Phase, list[CoilEnds]]


def _coil_copper(
    design: DesignParameters, plan: SpiralWindingPlan, spec: SpiralWindingSpec, coil_art: SeriesCoil,
    span: tuple[str, str],
) -> _CoilCopper:  # fmt: skip
    """Rotate the canonical X and Y artwork of every series group to every coil, in current direction (G6, G8)."""
    paths: list[CopperPath] = []
    vias: list[Via] = []
    coil_members: dict[int, tuple[tuple[Member, ...], ...]] = {}
    terminal_vias: dict[tuple[int, End], Via] = {}
    coil_ends: dict[Phase, list[CoilEnds]] = {phase: [] for phase in Phase}
    coil = spec.coil
    rings = coil_art.ring_vias
    first_rad = (coil.first_coil_angle_rad + spec.layers.pairs[0].rotation_rad) % (2 * math.pi)
    via_points = tuple(p for g, group in enumerate(coil_art.groups) for p in (rings[g], group.centre_via)) + rings[-1:]
    pair_groups = [tuple(p for p in spec.layers.pairs if p.index in group) for group in spec.layers.series_groups]
    for assignment in plan.assignment:
        k, sign = assignment.coil_index, assignment.polarity
        angle = first_rad + k * 2 * math.pi / coil.coil_count
        net = f"PHASE_{assignment.phase.value}"
        coil_vias = _coil_vias(design, span, via_points, angle, net, first_id=len(vias))
        vias += coil_vias
        in_order = coil_vias if sign == 1 else coil_vias[::-1]
        terminal_vias[(k, End.ENTRY)], terminal_vias[(k, End.EXIT)] = in_order[0], in_order[-1]
        groups = []
        for g, (pairs, copper) in enumerate(zip(pair_groups, coil_art.groups, strict=True)):
            x_prims, y_prims = rotate(copper.x, angle), rotate(copper.y, angle)
            own = coil_vias[2 * g : 2 * g + 3]
            routes = []
            for pair in pairs:
                if sign == 1:
                    layers_in_order = ((pair.layer_in, x_prims), (pair.layer_out, y_prims))
                else:  # a negative coil is the same copper entered at its other end (G8)
                    layers_in_order = ((pair.layer_out, reverse_path(y_prims)), (pair.layer_in, reverse_path(x_prims)))
                path_ids = []
                for layer, prims in layers_in_order:
                    path_ids.append(len(paths))
                    paths.append(
                        CopperPath(
                            id=len(paths), layer=layer, net=net, primitives=prims, phase=assignment.phase, element=k,
                            polarity=sign,
                        )
                    )  # fmt: skip
                routes.append((tuple(path_ids), tuple(v.id for v in (own if sign == 1 else own[::-1]))))
            groups.append(routes)
        if sign == -1:
            groups.reverse()
        # Each ring via joins two groups; the later group in current order drops its entry so a via counts once.
        coil_members[k] = tuple(
            tuple(Member(path_ids=p, via_ids=v if j == 0 else v[1:]) for p, v in routes)
            for j, routes in enumerate(groups)
        )
        entry_point, exit_point = (rings[0], rings[-1]) if sign == 1 else (rings[-1], rings[0])
        coil_ends[assignment.phase].append(
            CoilEnds(
                coil=k,
                entry_rad=norm_angle(angle + math.atan2(entry_point[1], entry_point[0])),
                exit_rad=norm_angle(angle + math.atan2(exit_point[1], exit_point[0])),
            )
        )

    return _CoilCopper(
        paths=tuple(paths), vias=tuple(vias), members=coil_members, terminal_vias=terminal_vias, ends=coil_ends
    )


def _closings(
    frame: CoilFrame, loops: tuple[LoopTurn, ...], stop: LoopStop, requested: int | None, vias: int
) -> tuple[Closing, Closing] | Unbuildable:
    """Return the closing to build and the one with the most turns (G5) for ``vias`` centre vias, or why none fits."""
    if stop is LoopStop.CAP:
        return _turns_exceed_limit(TurnsExceedCause.LOOP_RULE, MAX_TURNS_PER_LAYER)
    best = max_closing(frame, loops, vias)
    if best is None:
        return Unbuildable(issues=(_issue("UNBUILDABLE_ZERO_TURNS", ("/winding/coil/turns",)),))
    if best.n > MAX_TURNS_PER_LAYER:
        return _turns_exceed_limit(TurnsExceedCause.LOOP_RULE, MAX_TURNS_PER_LAYER)
    closing = best if requested is None else closing_for(frame, loops, requested, vias)
    if closing is None or closing.n > best.n:
        return _turns_exceed_limit(TurnsExceedCause.USER_CAP, best.n)
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


def _series_coil(
    frame: CoilFrame, closing: Closing, bus_width_mm: float, groups: int, art: CoilArtwork,
    filleted: Mapping[tuple[CornerKind, int], Corner],
) -> SeriesCoil | SeriesFailure:  # fmt: skip
    """Return the canonical coil as series groups; one group is the single-pair artwork and its mirror."""
    if groups == 1:
        mirrored = (art.terminal[0], -art.terminal[1])
        copper = GroupCopper(x=art.primitives, y=reverse_path(mirror(art.primitives, 0.0)), centre_via=art.centre_via)
        return SeriesCoil(groups=(copper,), ring_vias=(art.terminal, mirrored))
    assert isinstance(closing, FullClosing)  # closing_for gives k > 1 vias only the full closing
    return series_coil(frame, closing, bus_width_mm, groups, filleted)


_SERIES_FAILURES = {
    SeriesFailure.FILLET: (
        "UNBUILDABLE_SPIRAL_INPUT_OUT_OF_RANGE",
        ("/winding/layers/series_groups", "/winding/coil/corner_radius_mm"),
    ),
    SeriesFailure.FAN: ("UNBUILDABLE_SERIES_VIA_FAN_DRC", ("/winding/layers/series_groups",)),
}


def _series_fails_drc(design: DesignParameters, layout: Layout) -> bool:
    """D-020: series pairs are DRC-checked before they are returned, so a via fan that breaks a rule is refused."""
    report = run_drc(layout, design.drc_rules)
    assert report is not None  # None only when cancelled, and no token is passed
    return report.violation_count > 0


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
    k = len(spec.layers.series_groups)
    closings = _closings(frame, loops, stop, coil.turns, k)
    if isinstance(closings, Unbuildable):
        return closings
    closing, best = closings
    n = closing.n
    reason = _limiting_reason(coil.turns, best.n, len(loops), stop)
    art, rho_used_mm, filleted = _artwork(design, frame, closing, pair, coil.corner_radius_mm)
    coil_art = _series_coil(frame, closing, design.connection.ring_width_mm, k, art, filleted)
    if isinstance(coil_art, SeriesFailure):
        return Unbuildable(issues=(_issue(*_SERIES_FAILURES[coil_art]),))
    copper_z = design.stackup.copper_z_mm()
    layers = tuple(sorted({n for p in spec.layers.pairs for n in (p.layer_in, p.layer_out)}, key=copper_z.__getitem__))
    copper = _coil_copper(design, plan, spec, coil_art, (layers[0], layers[-1]))
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
        phase_groups[phase] = [g for k in chain.order for g in _with_chain(coil_members[k], k, chained)]
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
            closing=closing.kind,
        ),
        track_length_per_coil_layer_mm=MappingProxyType({"X": length_mm, "Y": length_mm}),
        rho_used_mm=rho_used_mm,
    )
    layout = Layout(
        topology=TopologyKind.SPIRAL,
        copper_layers=layers,
        copper_z_mm=MappingProxyType({name: copper_z[name] for name in layers}),
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
    if k > 1 and _series_fails_drc(design, layout):
        return Unbuildable(issues=(_issue("UNBUILDABLE_SERIES_VIA_FAN_DRC", ("/winding/layers/series_groups",)),))
    return BoardStack(boards=(layout,), board_thickness_mm=design.stackup.board_thickness_mm(), board_gap_mm=0.0)
