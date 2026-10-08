"""Serpentine stator, one board or one board per phase: a port of Xcoil ``compute`` for the serpentine topology.

Xcoil references are to /home/claude/serpentine/src/engine.js. The canonical pattern (l.411), the layer stack (l.667)
and the star or delta interconnect (l.1225, l.2527) are ported line by line; the golden regression GR-20 compares the
copper with ``xcoilRawLayout``. The board outline comes from the design's own outline inputs, not from Xcoil's
``buildMechanical`` scale factors, so the outline is the one part of the board GR-20 does not compare.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType

from embodic.errors import IssueCategory, Severity, Unbuildable, ValidationIssue, message_for
from embodic.generators.serpentine.canonical import BuildFailure, CanonFailure
from embodic.generators.serpentine.derived import serpentine_derived
from embodic.generators.serpentine.fit import max_traces_fit
from embodic.generators.serpentine.frame import Frame, Params, derive
from embodic.generators.serpentine.interconnect import (
    Interconnect,
    LeadItem,
    NeutralLeadItem,
    RingItem,
    Terminal,
    build_interconnect,
)
from embodic.generators.serpentine.plan import (
    PHASES,
    IcRole,
    LayerPlan,
    PathSpec,
    StackPlan,
    ViaPlan,
    phase_net,
    plan_stack,
)
from embodic.geometry.circuit import (
    Circuit,
    InterconnectRole,
    LineLead,
    Member,
    NeutralLead,
    NeutralRing,
    ParallelGroup,
    PhaseCircuit,
    PhaseLink,
)
from embodic.geometry.details import SerpentineDetail
from embodic.geometry.layout import BoardStack, Layout, Pad, Via, ViaRole
from embodic.geometry.outline import build_outline
from embodic.geometry.paths import CopperPath
from embodic.model.design import DesignParameters
from embodic.model.vocabulary import ConnectionTopology, Phase, TopologyKind, ViaSpan
from embodic.model.winding_specs import SerpentineWindingSpec, StackMode
from embodic.results import Registry

LINE_NET: Mapping[Phase, str] = MappingProxyType({Phase.A: "U", Phase.B: "V", Phase.C: "W"})  # D-019: A is U

_FAILURE_POINTERS: Mapping[BuildFailure, tuple[str, ...]] = MappingProxyType(
    {
        BuildFailure.R_TOO_SMALL: ("/winding/r_inner_mm", "/winding/turns", "/winding/strands"),
        BuildFailure.ACUTE_CORNER: ("/winding/turns", "/winding/corner_style", "/winding/r_inner_mm"),
        BuildFailure.BUNDLE_TOO_WIDE: ("/winding/turns", "/winding/strands", "/winding/r_inner_mm"),
        BuildFailure.GEOMETRY: ("/winding/r_outer_mm", "/winding/fillet_radius_mm"),
    }
)


def _issue(code: str, pointers: tuple[str, ...], value: int | None = None, limit: int | None = None) -> Unbuildable:
    issue = ValidationIssue(
        code=code,
        category=IssueCategory.UNBUILDABLE,
        severity=Severity.ERROR,
        message=message_for(code).format(value=value, limit=limit),
        pointers=pointers,
        value=value,
        limit=limit,
    )
    return Unbuildable(issues=(issue,))


def _refusal(failure: CanonFailure) -> Unbuildable:
    reason = failure.reasons[0]
    return _issue(f"UNBUILDABLE_SERPENTINE_{reason.value}", _FAILURE_POINTERS[reason])


def params_from_design(design: DesignParameters, spec: SerpentineWindingSpec) -> Params:
    """Xcoil ``p`` of a serpentine design; a missing end width is Xcoil's 0 (same as the trace width)."""
    return Params(
        poles=design.rotor.poles,
        phases=design.phases,
        r_in=spec.r_inner_mm,
        r_out=spec.r_outer_mm,
        turns=spec.turns,
        strands=spec.strands,
        trace_width_mm=spec.trace_width_mm,
        clearance_mm=spec.clearance_mm,
        end_width_outer_mm=spec.end_width_outer_mm or 0.0,
        end_width_inner_mm=spec.end_width_inner_mm or 0.0,
        style=spec.side_style,
        corner_style=spec.corner_style,
        fillet_radius_mm=spec.fillet_radius_mm,
        fillet_max=spec.fillet_max,
        terminal_side=spec.terminal_side,
        start_angle_rad=spec.start_angle_rad,
        layers_per_phase=spec.layers_per_phase,
        pair_connection=spec.pair_connection,
        layer_order=spec.layer_order,
        stack_mode=spec.stack_mode,
        via_pad=design.vias.pad_mm,
    )


def _terminals(plan: StackPlan) -> tuple[Terminal, ...]:
    return tuple(
        Terminal(phase=v.phase, sign=1 if v.kind == "T1" else -1, x=v.x, y=v.y, via=index)
        for index, v in enumerate(plan.vias)
        if v.terminal and v.kind in ("T1", "T2")
    )


def _item_paths(item: object) -> list[PathSpec]:
    """Xcoil items as paths: tap stubs and the ring arc are separate paths so that each has one current role."""
    match item:
        case LeadItem(net=net, phase=phase, stub=stub):
            return [PathSpec(kind="ic", net=net, prims=(stub,), ic=IcRole(kind="line", phase=phase))]
        case NeutralLeadItem(stub=stub):
            return [PathSpec(kind="ic", net="N", prims=(stub,), ic=IcRole(kind="neutral"))]
        case RingItem(link=link, stubs=stubs, arcs=arcs):
            star = link.net == "N"
            owner = -1 if star else int(link.net[1:])
            paths = [
                PathSpec(
                    kind="ic", net=link.net, prims=(stub,), ic=IcRole(kind="link", phase=t.phase if star else owner)
                )
                for stub, t in zip(stubs, link.taps, strict=True)
            ]
            for index, arc in enumerate(arcs):
                taps = tuple(t.via for t in link.taps[index : index + 2])
                ring = IcRole(kind="ring", tap_vias=taps) if star else IcRole(kind="link", phase=owner)
                paths.append(PathSpec(kind="ic", net=link.net, prims=(arc,), ic=ring))
            return paths
    raise TypeError(f"unknown interconnect item {item!r}")


def _add_interconnect(
    design: DesignParameters, spec: SerpentineWindingSpec, d: Frame, plan: StackPlan
) -> Interconnect | None:
    """Star or delta links, line stubs and terminal pads on a single board (Xcoil l.2519-2531)."""
    connection = design.connection
    wanted = connection.draw_interconnect and d.p.phases == 3 and connection.topology is not ConnectionTopology.OPEN
    if not (wanted and spec.stack_mode is StackMode.SINGLE and d.has_y):
        return None
    base = plan.r_max_cu if d.outer else plan.r_min_cu
    link_layers = tuple(range(len(plan.layers) - 1, 0, -1))
    ic = build_interconnect(connection, d.s, d.p.via_pad, _terminals(plan), base, d.sg, 0, link_layers)
    for item in ic.items:
        plan.layers[item.layer].paths.extend(_item_paths(item))
    return ic


@dataclass(frozen=True, slots=True, kw_only=True)
class _BoardIds:
    """Ids of one board's copper, by the keys the circuit needs."""

    strands: Mapping[tuple[int, int, str], tuple[int, ...]]
    buses: Mapping[tuple[int, int, str, str], int]
    links: Mapping[tuple[int, int], int]
    vias: Mapping[tuple[int, int, str], int]


def _role(role: IcRole, path_id: int) -> InterconnectRole:
    match role.kind:
        case "line":
            return LineLead(path_id=path_id, phase=PHASES[role.phase])
        case "link":
            return PhaseLink(path_id=path_id, phase=PHASES[role.phase])
        case "ring":
            return NeutralRing(path_id=path_id, tap_via_ids=role.tap_vias)
        case _:
            return NeutralLead(path_id=path_id)


def _board_paths(layers: Sequence[LayerPlan], names: Sequence[str]) -> tuple[list[CopperPath], list[InterconnectRole]]:
    paths: list[CopperPath] = []
    roles: list[InterconnectRole] = []
    for lp in layers:
        for spec in lp.paths:
            path_id = len(paths)
            paths.append(
                CopperPath(
                    id=path_id,
                    layer=names[lp.index_in_board],
                    net=spec.net,
                    primitives=spec.prims,
                    phase=PHASES[spec.phase] if spec.phase >= 0 else None,
                    element=spec.element,
                    polarity=0,
                )
            )
            if spec.ic is not None:
                roles.append(_role(spec.ic, path_id))
    return paths, roles


def _board_ids(layers: Sequence[LayerPlan], paths: Sequence[CopperPath], vias: Sequence[ViaPlan]) -> _BoardIds:
    by_key: dict[tuple[int, int, str], list[int]] = {}
    buses: dict[tuple[int, int, str, str], int] = {}
    links: dict[tuple[int, int], int] = {}
    cursor = 0
    for lp in layers:
        for spec in lp.paths:
            slot = lp.slot
            if spec.kind == "strand":
                by_key.setdefault((slot.phase, slot.pair, slot.role), []).append(paths[cursor].id)
            elif spec.kind in ("vbus", "tbus"):
                buses[(slot.phase, slot.pair, slot.role, spec.kind)] = paths[cursor].id
            elif spec.kind == "link":
                links[(slot.phase, slot.pair)] = paths[cursor].id
            cursor += 1
    via_ids: dict[tuple[int, int, str], int] = {(v.phase, v.pair, v.kind): index for index, v in enumerate(vias)}
    return _BoardIds(strands={k: tuple(v) for k, v in by_key.items()}, buses=buses, links=links, vias=via_ids)


def _group(members: Sequence[tuple[tuple[int, ...], tuple[int, ...]]]) -> ParallelGroup:
    return ParallelGroup(members=tuple(Member(path_ids=p, via_ids=v) for p, v in members))


def _phase_circuit(d: Frame, k: int, ids: _BoardIds) -> PhaseCircuit:
    """Return the groups in series from T1 to T2: T bus, strands and V bus of an X layer, V via, Y layer, link.

    Every winding path is a member of exactly one group (UT-GEN-01). Xcoil's analysis counts the strands only
    (analyze l.949); the bus and link groups add the copper embodic's resistance and eddy loss count as well.
    """

    def layer_groups(pairs: Sequence[int], role: str) -> list[ParallelGroup]:
        def bus(kind: str) -> list[ParallelGroup]:
            found = [ids.buses[(k, q, role, kind)] for q in pairs if (k, q, role, kind) in ids.buses]
            return [_group([((i,), ()) for i in found])] if found else []

        strands = [_group([((ids.strands[(k, q, role)][s],), ()) for q in pairs for s in range(d.j)])]
        # current flows T -> V on an X layer and V -> T on a Y layer
        return [*bus("tbus"), *strands, *bus("vbus")] if role == "X" else [*bus("vbus"), *strands, *bus("tbus")]

    def via_group(pair: int) -> ParallelGroup:
        return _group([((), (ids.vias[(k, pair, "V")],))])

    groups: list[ParallelGroup] = []
    if d.series:
        for q in range(d.n_pairs):
            groups += layer_groups([q], "X")
            if d.has_y:
                groups += [via_group(q), *layer_groups([q], "Y")]
                if q < d.n_pairs - 1:
                    groups.append(_group([((ids.links[(k, q)],), (ids.vias[(k, q + 1, "T1")],))]))
    else:
        pairs = range(d.n_pairs)
        groups += layer_groups(pairs, "X")
        if d.has_y:
            groups += [via_group(0), *layer_groups(pairs, "Y")]
    return PhaseCircuit(phase=PHASES[k], groups=tuple(groups), terminal_net=LINE_NET[PHASES[k]])


def _vias(design: DesignParameters, plans: Sequence[ViaPlan], first: str, last: str) -> tuple[Via, ...]:
    def role(v: ViaPlan) -> ViaRole:
        if v.terminal:
            return ViaRole.TERMINAL
        return ViaRole.CENTRE if v.kind == "V" else ViaRole.TRANSFER

    return tuple(
        Via(
            id=index,
            x_mm=v.x,
            y_mm=v.y,
            drill_mm=design.vias.drill_mm,
            pad_mm=design.vias.pad_mm,
            role=role(v),
            span=ViaSpan.THROUGH,
            layer_from=first,
            layer_to=last,
            net=phase_net(v.phase),
        )
        for index, v in enumerate(plans)
    )


def _pads(design: DesignParameters, ic: Interconnect | None, names: Sequence[str]) -> tuple[Pad, ...]:
    if ic is None:
        return ()
    connection = design.connection
    smd = not connection.terminal_drill_mm > 0
    return tuple(
        Pad(
            id=index,
            x_mm=site.x,
            y_mm=site.y,
            shape="round",
            width_mm=connection.terminal_pad_mm,
            height_mm=connection.terminal_pad_mm,
            rotation_rad=0.0,
            drill_mm=connection.terminal_drill_mm,
            layer=names[site.layer] if smd else None,
            net=site.net,
            label=site.net,
        )
        for index, site in enumerate(ic.pads)
    )


def _board(
    design: DesignParameters, spec: SerpentineWindingSpec, d: Frame, plan: StackPlan, ic: Interconnect | None,
    board: int, names: Sequence[str], z_mm: Mapping[str, float], traces_fit: int, registry: Registry,
) -> Layout:  # fmt: skip
    layers = [lp for lp in plan.layers if lp.board == board]
    paths, roles = _board_paths(layers, names)
    phases = [board] if d.p.stack_mode is StackMode.ONE_BOARD_PER_PHASE else list(range(d.p.phases))
    plans = [v for v in plan.vias if v.phase in phases]
    ids = _board_ids(layers, paths, plans)
    pitch = design.stackup.board_thickness_mm() + spec.board_gap_mm
    r_min = min(plan.r_min_cu, ic.r_edge) if ic else plan.r_min_cu
    r_max = max(plan.r_max_cu, ic.r_edge) if ic else plan.r_max_cu
    envelope = (r_min, r_max)
    return Layout(
        topology=TopologyKind.SERPENTINE,
        copper_layers=tuple(names),
        copper_z_mm=MappingProxyType({n: board * pitch + z_mm[n] for n in names}),
        paths=tuple(paths),
        vias=_vias(design, plans, names[0], names[-1]),
        pads=_pads(design, ic, names),
        outline=build_outline(design.outline, envelope),
        circuit=Circuit(
            phases=tuple(_phase_circuit(d, k, ids) for k in phases),
            topology=design.connection.topology,
            interconnect_path_ids=tuple(r.path_id for r in roles),
            interconnect_roles=tuple(roles),
        ),
        symmetry=None,
        envelope_mm=envelope,
        detail=SerpentineDetail(
            max_turns_that_fit=traces_fit,
            layer_phase=MappingProxyType({names[lp.index_in_board]: PHASES[lp.slot.phase] for lp in layers}),
            canonical_frame_rad=d.theta_g,
        ),
        derived=serpentine_derived(design, spec, traces_fit, plan.canon[phases[0]].rho0, envelope, registry),
    )


def generate_serpentine(design: DesignParameters, registry: Registry) -> BoardStack | Unbuildable:
    """Build the boards of a serpentine design; a winding other than SerpentineWindingSpec raises TypeError."""
    spec = design.winding
    if not isinstance(spec, SerpentineWindingSpec):
        raise TypeError(f"generate_serpentine needs a serpentine winding, got {type(spec).__name__}")
    d = derive(params_from_design(design, spec))
    plan = plan_stack(d)
    if isinstance(plan, CanonFailure):
        return _refusal(plan)
    copper = design.stackup.copper_layers()
    if len(copper) != plan.per_board:
        return _issue("UNBUILDABLE_SERPENTINE_COPPER_COUNT", ("/stackup/layers",), plan.per_board, len(copper))
    ic = _add_interconnect(design, spec, d, plan)
    names = [layer.name for layer in copper]
    z_mm = design.stackup.copper_z_mm()
    traces_fit = max_traces_fit(d.p)
    boards = tuple(
        _board(design, spec, d, plan, ic, b, names, z_mm, traces_fit, registry) for b in range(plan.n_boards)
    )
    return BoardStack(
        boards=boards,
        board_thickness_mm=design.stackup.board_thickness_mm(),
        board_gap_mm=spec.board_gap_mm if plan.n_boards > 1 else 0.0,
    )
