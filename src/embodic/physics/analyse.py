"""analyse(): every result of one design as a Traceable (interfaces.md section 8, D-007).

Topology-agnostic: it reads the paths, vias, circuit and copper_z_mm of every board and the stack thickness only.
Board k of a stack sits k * (board thickness + gap) below board 0 (inferred from BoardStack.stack_thickness_mm).
"""

import cmath
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from embodic.geometry.layout import BoardStack, Layout
from embodic.geometry.primitives import Arc, Primitive, PrimitiveRole, primitive_length_mm
from embodic.model.design import DesignParameters
from embodic.model.fields import FieldKind, field_for
from embodic.model.provenance import Provenance, ProvenanceMap
from embodic.model.rotor import RotorSpec
from embodic.model.schema import JsonValue, design_values
from embodic.model.vocabulary import ConnectionTopology, Phase
from embodic.physics.circuit import (
    T_MM2_TO_V_S_PER_RAD,
    CircuitSolution,
    add_phasors,
    delta_circulating_loss_w,
    efficiency,
    line_resistance_ohm,
    motor_constant_n_m_per_sqrt_w,
    solve_phase_circuit,
)
from embodic.physics.constants import phase_constants
from embodic.physics.drive import (
    XCOIL_CURVE_POINTS,
    base_speed_rpm,
    no_load_speed_rpm,
    torque_speed_envelope,
)
from embodic.physics.emf import (
    PathField,
    eddy_loss_w,
    edge_leakage_fraction,
    field_table,
    integrate_path,
    pole_arc_ratio_mm,
)
from embodic.physics.estimates import inductance_estimate_h, mass_g
from embodic.physics.field import field_harmonic, symmetry_plane_mm
from embodic.physics.interconnect import (
    InterconnectResistance,
    interconnect_loss_w,
    interconnect_resistance,
    is_unclassified,
    sum_boards,
)
from embodic.physics.losses import current_density_a_per_mm2, ipc2221_current_a, skin_depth_mm, thd
from embodic.physics.resistance import copper_resistivity_ohm_m, path_resistance_ohm, via_resistance_ohm
from embodic.physics.thermal import temperature_rise_k
from embodic.physics.waveform import emf_waveform_v
from embodic.results import (
    AnalysisResult,
    InputRef,
    LayerResult,
    PhaseResult,
    Registry,
    Status,
    TorqueSpeedEstimate,
    Traceable,
    ValidityEffect,
    ValidityFlag,
    evaluate_validity,
    traced,
)
from embodic.results.traceable import traced_validity_metric
from embodic.units import Unit, rpm_to_rad_per_s

EDGE_CHECK_ID = "EC-05"
SKIN_DEPTH_FRACTION = 1.0 / 3.0  # REQ-T-08: w above delta / 3 raises RANGE_SKIN_DEPTH
IDEAL_INTEGRAL_STEPS = 200  # Xcoil analyzeElements `ideal` integral (EQ-27)
NON_FINITE_CODE = "RANGE_NON_FINITE_RESULT"
UNCLASSIFIED_INTERCONNECT = ValidityFlag(
    code="INTERNAL_INTERCONNECT_UNCLASSIFIED",
    message="interconnect copper not classified",
    eq_id="EQ-23",
    effect=ValidityEffect.CAP,
)


def _non_finite_flag(value: object, eq_id: str) -> tuple[ValidityFlag, ...]:
    numbers = value if isinstance(value, tuple) else (value,)
    if all(math.isfinite(n) for n in numbers if isinstance(n, float)):
        return ()
    return (ValidityFlag(code=NON_FINITE_CODE, message="value is not finite", eq_id=eq_id, effect=ValidityEffect.CAP),)


class CancelToken(Protocol):
    """Anything with a `cancelled` flag, such as embodic.drc.CancelToken (physics may not import drc, MT-01)."""

    @property
    def cancelled(self) -> bool:
        """Return whether the caller asked analyse() to stop."""
        ...


class _Inputs:
    """InputRefs from the design, its provenance and the registry constants."""

    def __init__(self, design: DesignParameters, provenance: ProvenanceMap, registry: Registry) -> None:
        self._values: dict[str, JsonValue] = design_values(design)
        self._provenance = provenance
        self._registry = registry

    def field(self, pointer: str) -> InputRef:
        spec = field_for(pointer, self._values)
        record = self._provenance.get(pointer)
        provenance = record.provenance if record is not None else None
        unmeasured = spec.kind is FieldKind.PROPERTY and provenance is not Provenance.MEASURED
        value = self._values[pointer]
        assert isinstance(value, int | float | str)
        return InputRef(
            pointer=pointer,
            value=value,
            unit=spec.unit,
            provenance=provenance,
            kind=spec.kind,
            label=Status.ASSUMPTION if unmeasured else None,
        )

    def constant(self, name: str) -> InputRef:
        c = self._registry.constant(name)
        return InputRef(
            pointer=f"constant:{name}", value=c.value, unit=c.unit, provenance=None, kind=None, label=c.status
        )

    def copper_thickness(self, design: DesignParameters) -> tuple[InputRef, ...]:
        return tuple(
            self.field(f"/stackup/layers/{i}/thickness_mm")
            for i, layer in enumerate(design.stackup.layers)
            if layer.kind == "copper"
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class _BoardFields:
    """Per-board integration results keyed by path id."""

    fields: Mapping[int, PathField]
    eddy_w: float


def _loop_area_mm2(loop: Sequence[Primitive]) -> float:
    """Exact area of a chained closed loop by Green's theorem, A = 1/2 sum (x dy - y dx) over its primitives.

    An arc adds its chord term plus the signed circular segment r^2 (s - sin s) / 2, so a clockwise arc of a clockwise
    loop keeps the sign of the loop. The absolute value makes the orientation irrelevant (DEF-M7b-01).
    """
    twice_area_mm2 = 0.0
    for p in loop:
        (x1, y1), (x2, y2) = p.start_point(), p.end_point()
        twice_area_mm2 += x1 * y2 - x2 * y1
        if isinstance(p, Arc):
            twice_area_mm2 += p.r_mm**2 * (p.sweep_rad - math.sin(p.sweep_rad))
    return abs(twice_area_mm2) / 2.0


def board_area_mm2(layout: Layout) -> float:
    """Return the exact board face area: outline minus cutouts minus screw holes.

    References: EQ-16 and EQ-17 (A_board). Arcs count as arcs, not as their 0.5 mm chords.

    Parameters
    ----------
    layout : Layout
        Board with its outline primitives and holes in mm.

    Returns
    -------
    float
        Area of one face in mm^2.
    """
    outline = layout.outline
    area = _loop_area_mm2(outline.outer) - math.fsum(_loop_area_mm2(c) for c in outline.cutouts)
    return area - math.fsum(math.pi * h.diameter_mm**2 / 4.0 for h in outline.holes)


def _via_resistance(layout: Layout, plating_um: float, length_mm: float, rho: float) -> dict[int, float]:
    """Barrel resistance of every via; a through via spans one board thickness (EQ-11)."""
    return {v.id: via_resistance_ohm(v.drill_mm, plating_um, length_mm, rho, 1) for v in layout.vias}


def _phase_paths(layout: Layout, phase: Phase) -> list[int]:
    return [
        i for pc in layout.circuit.phases if pc.phase is phase for g in pc.groups for m in g.members for i in m.path_ids
    ]


def analyse(
    design: DesignParameters,
    boards: BoardStack,
    provenance: ProvenanceMap,
    registry: Registry,
    *,
    cancel: CancelToken | None = None,
) -> AnalysisResult | None:
    """Return every result of the design on these boards; None only when cancelled.

    References: EQ-04 to EQ-07, EQ-09 to EQ-19, EQ-22, EQ-23, EQ-26, EQ-27 and EC-05; each result names its own chain.

    Parameters
    ----------
    design : DesignParameters
        Rotor, stack-up, operating point, materials and analysis options.
    boards : BoardStack
        The generated boards with their circuits.
    provenance : ProvenanceMap
        Provenance of every design pointer, for the assumed-inputs tag.
    registry : Registry
        Equations, evidence and constants; decides every badge.
    cancel : CancelToken | None
        Checked between boards.

    Returns
    -------
    AnalysisResult | None
        The traced results.
    """
    rotor, op, options = design.rotor, design.operating, design.analysis
    inputs = _Inputs(design, provenance, registry)

    def tr(
        quantity: str,
        value: object,
        unit: Unit,
        eq_ids: Sequence[str],
        refs: Sequence[InputRef],
        validity: Sequence[ValidityFlag] = (),
        kind_tag: str = "computed",
    ) -> Traceable:  # type: ignore[type-arg]
        return traced(
            quantity,
            value,
            unit,
            eq_ids=eq_ids,
            inputs=refs,
            registry=registry,
            validity=(*validity, *_non_finite_flag(value, eq_ids[0])),
            kind_tag=kind_tag,  # type: ignore[arg-type]
        )

    rho20 = registry.constant("copper_resistivity_20c_ohm_m").value
    alpha = registry.constant("copper_temp_coeff_per_k").value
    rho_op = copper_resistivity_ohm_m(op.winding_temperature_degc, rho20, alpha)
    thickness = {layer.name: layer.thickness_mm for layer in design.stackup.copper_layers()}
    pole_pairs = rotor.poles // 2
    harmonics = tuple(options.harmonics)
    omega_m = rpm_to_rad_per_s(op.speed_rpm)
    f_e = pole_pairs * op.speed_rpm / 60.0
    omega_e = 2.0 * math.pi * f_e
    g_plane = symmetry_plane_mm(rotor, boards.stack_thickness_mm)
    z_max = max(z for b in boards.boards for z in b.copper_z_mm.values())
    edge_g = g_plane if math.isfinite(g_plane) else z_max + rotor.air_gap_mm
    check = registry.equation("EQ-05").validity_checks[0]
    assert check.id == EDGE_CHECK_ID
    edge_amplitude = float(check.parameters["D_e"])
    edge_decay_mm = float(check.parameters["c_e"]) * edge_g

    tables = {}
    board_fields: list[_BoardFields] = []
    solutions: list[CircuitSolution] = []
    r20_by_board: list[Mapping[Phase, float]] = []
    r_op_by_board: list[Mapping[int, float]] = []
    for layout in boards.boards:
        if cancel is not None and cancel.cancelled:
            return None
        z_of = layout.copper_z_mm
        for z in z_of.values():
            if z not in tables:
                tables[z] = field_table(rotor, g_plane, z + rotor.air_gap_mm, harmonics)
        fields = {
            p.id: integrate_path(p.primitives, tables[z_of[p.layer]], pole_pairs, options.max_segment_mm, edge_decay_mm)
            for p in layout.paths
        }
        eddy = math.fsum(
            eddy_loss_w(fields[p.id], harmonics, thickness[p.layer], omega_e, rho_op) for p in layout.paths
        )
        board_fields.append(_BoardFields(fields=fields, eddy_w=eddy))
        arrays = layout.arrays()
        lam = {i: f.flux_linkage_t_mm2 for i, f in fields.items()}
        r_op = dict(enumerate(path_resistance_ohm(arrays, thickness, rho_op).tolist()))
        r_20 = dict(enumerate(path_resistance_ohm(arrays, thickness, rho20).tolist()))
        via_op = _via_resistance(layout, design.vias.plating_um, boards.board_thickness_mm, rho_op)
        via_20 = _via_resistance(layout, design.vias.plating_um, boards.board_thickness_mm, rho20)
        r_op_by_board.append(r_op)
        solutions.append(solve_phase_circuit(layout.circuit, lam, r_op, via_op, omega_m))
        r20_by_board.append(solve_phase_circuit(layout.circuit, lam, r_20, via_20, omega_m).phase_resistance_ohm)

    phases = tuple(dict.fromkeys(ph for s in solutions for ph in s.phase_emf_phasor_v_s_per_rad))
    zero = np.zeros(len(harmonics), dtype=np.complex128)
    emf = {ph: add_phasors((s.phase_emf_phasor_v_s_per_rad.get(ph, zero) for s in solutions), zero) for ph in phases}
    r_op_ph = {ph: math.fsum(s.phase_resistance_ohm.get(ph, 0.0) for s in solutions) for ph in phases}
    r_20_ph = {ph: math.fsum(r.get(ph, 0.0) for r in r20_by_board) for ph in phases}
    circ_ph = {ph: math.fsum(s.circulating_loss_w.get(ph, 0.0) for s in solutions) for ph in phases}
    m = len(phases)
    ke_ph = {ph: float(abs(emf[ph][0])) for ph in phases}
    emf_angle_ph = {ph: cmath.phase(emf[ph][0]) for ph in phases}
    ke1 = math.fsum(ke_ph.values()) / m
    topology = boards.boards[0].circuit.topology
    connection = topology if design.phases == 3 else ConnectionTopology.OPEN
    constants = phase_constants(ke1, topology, design.phases, rotor.poles)
    i_line = op.line_current_rms_a
    i_ph = i_line / math.sqrt(3.0) if connection is ConnectionTopology.DELTA else i_line
    unclassified = any(is_unclassified(b) for b in boards.boards)
    ic_validity: tuple[ValidityFlag, ...] = (UNCLASSIFIED_INTERCONNECT,) if unclassified else ()
    ic = (
        InterconnectResistance(line_stub_ohm=(0.0,) * m, link_ohm=(0.0,) * m, neutral_ring_ohm=())
        if unclassified
        else sum_boards(
            [
                interconnect_resistance(b, phases, r, thickness, rho_op)
                for b, r in zip(boards.boards, r_op_by_board, strict=True)
            ]
        )
    )

    # Inputs per chain, so every tag lists what its result used.
    field_refs = [
        inputs.field(p)
        for p in (
            "/rotor/remanence_t",
            "/rotor/recoil_permeability",
            "/rotor/air_gap_mm",
            "/rotor/poles",
            "/rotor/magnet/thickness_mm",
        )
    ]
    speed = inputs.field("/operating/speed_rpm")
    current = inputs.field("/operating/line_current_rms_a")
    temperature = inputs.field("/operating/winding_temperature_degc")
    copper_t = inputs.copper_thickness(design)
    rho_refs = [inputs.constant("copper_resistivity_20c_ohm_m"), inputs.constant("copper_temp_coeff_per_k")]
    emf_refs = field_refs
    r_refs = [*copper_t, temperature, *rho_refs]
    loss_refs = [*r_refs, current]

    edge_fields = [f for b in board_fields for f in b.fields.values()]
    e_edge = edge_leakage_fraction(edge_fields, edge_amplitude)
    edge_flag = evaluate_validity(check, "EQ-05", e_edge)
    emf_validity = (edge_flag,)

    widths = [p.width_mm for b in boards.boards for path in b.paths if path.phase is not None for p in path.primitives]
    w_min, w_max = min(widths), max(widths)
    delta_mm = skin_depth_mm(f_e, rho_op)
    skin_validity: tuple[ValidityFlag, ...] = ()
    if w_max > delta_mm * SKIN_DEPTH_FRACTION:
        skin_validity = (
            ValidityFlag(
                code="RANGE_SKIN_DEPTH",
                message=f"trace width {w_max:g} mm above one third of the skin depth {delta_mm:g} mm",
                eq_id="EQ-13",
                effect=ValidityEffect.LIMITATION,
                metric=w_max / delta_mm,
            ),
        )

    p_cu = math.fsum(i_ph * i_ph * r for r in r_op_ph.values())
    p_eddy = math.fsum(b.eddy_w for b in board_fields)
    p_circ = math.fsum(circ_ph.values())
    phase_emf_v = [emf[ph] * omega_m for ph in phases]
    p_delta = (
        delta_circulating_loss_w(phase_emf_v, math.fsum([*r_op_ph.values(), *ic.link_ohm]))
        if connection is ConnectionTopology.DELTA
        else 0.0
    )
    torque = (m / 2.0) * ke1 * i_ph * math.sqrt(2.0)
    p_ic = interconnect_loss_w(ic, connection, i_line)
    loss_total = p_cu + p_eddy + p_circ + p_delta + p_ic
    p_out = torque * omega_m
    r_line = line_resistance_ohm(
        [r_op_ph[ph] for ph in phases], connection, ic.line_stub_ohm, ic.link_ohm, ic.neutral_ring_ohm
    )

    first = phases[0]
    amplitudes = {n: float(abs(e)) for n, e in zip(harmonics, emf[first], strict=True)}
    line_phasors = _line_phasors([emf[ph] for ph in phases], connection)
    line_amplitudes = {n: float(abs(e)) for n, e in zip(harmonics, line_phasors, strict=True)}
    waveform = emf_waveform_v(dict(zip(harmonics, emf[first] * omega_m, strict=True)))
    ke_line_peak = float(np.max(np.abs(emf_waveform_v(dict(zip(harmonics, line_phasors, strict=True))))))

    parallel = max((len(g.members) for b in boards.boards for pc in b.circuit.phases for g in pc.groups), default=1)
    t_min = min(thickness[layer] for b in boards.boards for layer in b.copper_layers)
    density = current_density_a_per_mm2(i_ph, parallel, w_min, t_min)
    temp_rise_k = op.winding_temperature_degc - op.ambient_temperature_degc
    outer_layers = {boards.boards[0].copper_layers[0], boards.boards[0].copper_layers[-1]}
    ipc_phase = min(
        ipc2221_current_a(w_min * thickness[layer], temp_rise_k, layer not in outer_layers) * parallel
        for layer in boards.boards[0].copper_layers
    )
    ipc_line = ipc_phase * (math.sqrt(3.0) if connection is ConnectionTopology.DELTA else 1.0)

    r_a, r_b = rotor.magnet.radial_span_mm()
    sides = sum(
        1
        for b in boards.boards
        for i in _phase_paths(b, first)
        for prim in b.paths[i].primitives
        if prim.role is PrimitiveRole.SIDE
    )
    conductors = sides / parallel
    all_z = sorted(tables)
    ideal = _ideal_integral(rotor, g_plane, all_z, r_a, r_b)
    k_u = ke1 / T_MM2_TO_V_S_PER_RAD / (ideal * conductors) if ideal > 0.0 and conductors > 0 else 0.0
    r_min_cu, r_max_cu = boards.boards[0].envelope_mm
    effective_gap = 2.0 * rotor.magnet.thickness_mm + 2.0 * rotor.air_gap_mm + boards.stack_thickness_mm
    inductance = inductance_estimate_h(conductors / 2.0, k_u, r_max_cu, r_min_cu, pole_pairs, effective_gap)

    areas: dict[str, float] = {}
    for b in boards.boards:
        for path in b.paths:
            areas[path.layer] = areas.get(path.layer, 0.0) + math.fsum(
                primitive_length_mm(q) * q.width_mm for q in path.primitives
            )
    board_area = board_area_mm2(boards.boards[0])
    mass = mass_g(
        areas,
        thickness,
        board_area * len(boards.boards),
        boards.board_thickness_mm,
        registry.constant("copper_density_g_per_cm3").value,
        registry.constant("laminate_density_g_per_cm3").value,
    )
    cooling = inputs.field("/operating/convection_h_w_m2k")
    sum_eq = ("EQ-26", "EQ-10", "EQ-11", "EQ-12", "EQ-07", "EQ-19", "EQ-23", "EQ-09", "EQ-06")
    sum_refs = [*emf_refs, *loss_refs, speed]
    sum_validity = (*emf_validity, *skin_validity, *ic_validity)
    d_t = temperature_rise_k(loss_total, board_area, op.convection_h_w_m2k)  # a stack cools through its outer faces

    ke_t = tr("ke_phase_v_s_per_rad", ke1, Unit.V_S_PER_RAD, ("EQ-06", "EQ-07", "EQ-05"), emf_refs, emf_validity)
    edge_t = traced_validity_metric("edge_leakage_fraction", check, "EQ-05", e_edge, inputs=emf_refs, registry=registry)
    layer_results = tuple(
        LayerResult(
            layer=name,
            z_mm=tr("layer_z_mm", z, Unit.MM, ("EQ-05",), copper_t, kind_tag="derived"),
            b1_peak_mid_radius_t=tr(
                "b1_peak_mid_radius_t",
                float(
                    field_harmonic(
                        1,
                        np.array([(r_a + r_b) / 2.0]),
                        np.array([z + rotor.air_gap_mm]),
                        rotor,
                        g_plane,
                        pole_arc_ratio_mm(rotor, np.array([(r_a + r_b) / 2.0])),
                    )[0][0]
                ),
                Unit.T,
                ("EQ-05", "EQ-04"),
                field_refs,
            ),
        )
        for name, z in boards.boards[0].copper_z_mm.items()
    )
    phase_results = tuple(
        PhaseResult(
            phase=ph,
            ke_peak_v_s_per_rad=tr(
                "phase_ke_peak", ke_ph[ph], Unit.V_S_PER_RAD, ("EQ-06", "EQ-07"), emf_refs, emf_validity
            ),
            emf_phasor_angle_rad=tr(
                "phase_emf_phasor_angle", emf_angle_ph[ph], Unit.RAD, ("EQ-06", "EQ-07"), emf_refs, emf_validity
            ),
            resistance_20c_ohm=tr(
                "phase_resistance_20c", r_20_ph[ph], Unit.OHM, ("EQ-10", "EQ-11"), r_refs, skin_validity
            ),
            resistance_operating_ohm=tr(
                "phase_resistance_operating", r_op_ph[ph], Unit.OHM, ("EQ-10", "EQ-11"), r_refs, skin_validity
            ),
            circulating_loss_w=tr(
                "phase_circulating_loss", circ_ph[ph], Unit.W, ("EQ-07",), [*emf_refs, *r_refs, speed]
            ),
        )
        for ph in phases
    )
    torque_speed = None
    if op.dc_link_v is not None and ke1 > 0.0:
        drive_refs = [*emf_refs, *r_refs, current, inputs.field("/operating/dc_link_v")]
        drive_refs.append(inputs.field("/operating/modulation"))
        drive_eq = ("EQ-20", "EQ-14", "EQ-09", "EQ-23")
        drive_validity = (*emf_validity, *ic_validity)
        is_open = connection is ConnectionTopology.OPEN
        ke_equivalent = ke1 if is_open else constants.ke_line_v_s_per_rad / math.sqrt(3.0)
        speed_rpm, curve_torque_n_m = torque_speed_envelope(
            r_line if is_open else r_line / 2.0,
            inductance / 3.0 if connection is ConnectionTopology.DELTA else inductance,
            ke_equivalent,
            op.dc_link_v,
            op.modulation,
            i_line,
            rotor.poles,
            XCOIL_CURVE_POINTS,
            phases=design.phases,
            connection=connection,
        )
        power_w = curve_torque_n_m * speed_rpm * (2.0 * math.pi / 60.0)
        torque_speed = TorqueSpeedEstimate(
            speed_rpm=tr("torque_speed_rpm", tuple(speed_rpm.tolist()), Unit.RPM, drive_eq, drive_refs, drive_validity),
            torque_n_m=tr(
                "torque_speed_torque", tuple(curve_torque_n_m.tolist()), Unit.N_M, drive_eq, drive_refs, drive_validity
            ),
            power_w=tr("torque_speed_power", tuple(power_w.tolist()), Unit.W, drive_eq, drive_refs, drive_validity),
            no_load_speed_rpm=tr(
                "no_load_speed",
                no_load_speed_rpm(ke_equivalent, op.dc_link_v, op.modulation, connection),
                Unit.RPM,
                drive_eq,
                drive_refs,
                drive_validity,
            ),
            base_speed_rpm=tr(
                "base_speed",
                base_speed_rpm(speed_rpm, curve_torque_n_m),
                Unit.RPM,
                drive_eq,
                drive_refs,
                drive_validity,
            ),
        )
    return AnalysisResult(
        ke_phase_v_s_per_rad=ke_t,
        ke_line_v_s_per_rad=tr(
            "ke_line", constants.ke_line_v_s_per_rad, Unit.V_S_PER_RAD, ("EQ-09", "EQ-06"), emf_refs, emf_validity
        ),
        ke_line_peak_v_s_per_rad=tr(
            "ke_line_peak", ke_line_peak, Unit.V_S_PER_RAD, ("EQ-18", "EQ-09", "EQ-06"), emf_refs, emf_validity
        ),
        kt_n_m_per_a=tr("kt", constants.kt_n_m_per_a, Unit.N_M_PER_A, ("EQ-09", "EQ-06"), emf_refs, emf_validity),
        kv_rpm_per_v=tr("kv", constants.kv_rpm_per_v, Unit.RPM_PER_V, ("EQ-09", "EQ-06"), emf_refs, emf_validity),
        winding_factor_1=tr("utilisation_factor_k_u", k_u, Unit.ONE, ("EQ-27", "EQ-06"), emf_refs, emf_validity),
        resistance_phase_20c_ohm=tr(
            "resistance_phase_20c", math.fsum(r_20_ph.values()) / m, Unit.OHM, ("EQ-10", "EQ-11"), r_refs, skin_validity
        ),
        resistance_phase_operating_ohm=tr(
            "resistance_phase_operating",
            math.fsum(r_op_ph.values()) / m,
            Unit.OHM,
            ("EQ-10", "EQ-11"),
            r_refs,
            skin_validity,
        ),
        resistance_line_ohm=tr(
            "resistance_line", r_line, Unit.OHM, ("EQ-23", "EQ-10", "EQ-11"), r_refs, (*skin_validity, *ic_validity)
        ),
        emf_phase_rms_v=tr(
            "emf_phase_rms",
            ke1 * omega_m / math.sqrt(2.0),
            Unit.V,
            ("EQ-06", "EQ-07"),
            [*emf_refs, speed],
            emf_validity,
        ),
        torque_n_m=tr("torque", torque, Unit.N_M, ("EQ-09", "EQ-06"), [*emf_refs, current], emf_validity),
        loss_copper_w=tr("loss_copper", p_cu, Unit.W, ("EQ-10", "EQ-11"), loss_refs, skin_validity),
        loss_eddy_w=tr("loss_eddy", p_eddy, Unit.W, ("EQ-12", "EQ-05"), [*emf_refs, *r_refs, speed], skin_validity),
        loss_circulating_w=tr("loss_circulating", p_circ, Unit.W, ("EQ-07",), [*emf_refs, *r_refs, speed]),
        loss_delta_circulating_w=tr(
            "loss_delta_circulating", p_delta, Unit.W, ("EQ-19", "EQ-06"), [*emf_refs, *r_refs, speed], emf_validity
        ),
        loss_interconnect_w=tr("loss_interconnect", p_ic, Unit.W, ("EQ-23", "EQ-10"), loss_refs, ic_validity),
        loss_total_w=tr("loss_total", loss_total, Unit.W, sum_eq, sum_refs, sum_validity),
        output_power_w=tr("output_power", p_out, Unit.W, ("EQ-26", "EQ-09", "EQ-06"), [*emf_refs, current, speed]),
        efficiency=tr("efficiency", efficiency(p_out, loss_total), Unit.ONE, sum_eq, sum_refs, sum_validity),
        motor_constant_n_m_per_sqrt_w=tr(
            "motor_constant",
            motor_constant_n_m_per_sqrt_w(torque, p_cu, i_ph),
            Unit.N_M_PER_SQRT_W,
            ("EQ-26", "EQ-09", "EQ-06", "EQ-10", "EQ-11"),
            [*emf_refs, *loss_refs],
            (*emf_validity, *skin_validity),
        ),
        thd_phase=tr("thd_phase", thd(amplitudes), Unit.ONE, ("EQ-18", "EQ-06"), emf_refs),
        thd_line=tr("thd_line", thd(line_amplitudes), Unit.ONE, ("EQ-18", "EQ-06"), emf_refs),
        current_density_a_per_mm2=tr("current_density", density, Unit.A_PER_MM2, ("EQ-22",), [*copper_t, current]),
        skin_depth_mm=tr("skin_depth", delta_mm, Unit.MM, ("EQ-13", "EQ-10"), [temperature, speed, *rho_refs]),
        inductance_estimate_h=tr("inductance_estimate", inductance, Unit.H, ("EQ-14", "EQ-27"), emf_refs),
        ipc_guideline_current_a=tr("ipc_guideline_current", ipc_line, Unit.A, ("EQ-15",), [*copper_t, temperature]),
        mass_copper_g=tr(
            "mass_copper", mass.copper_g, Unit.G, ("EQ-16",), [*copper_t, inputs.constant("copper_density_g_per_cm3")]
        ),
        mass_laminate_g=tr(
            "mass_laminate",
            mass.laminate_g,
            Unit.G,
            ("EQ-16",),
            [*copper_t, inputs.constant("laminate_density_g_per_cm3")],
        ),
        temperature_rise_k=tr("temperature_rise", d_t, Unit.K, ("EQ-17", *sum_eq), [*sum_refs, cooling], sum_validity),
        edge_leakage_fraction=edge_t,
        layers=layer_results,
        phases=phase_results,
        emf_waveform_v=tr(
            "emf_waveform", tuple(waveform.tolist()), Unit.V, ("EQ-18", "EQ-06"), [*emf_refs, speed], emf_validity
        ),
        torque_speed=torque_speed,
        registry_version=registry.version,
    )


def _line_phasors(
    phase_phasors: Sequence[NDArray[np.complex128]], connection: ConnectionTopology
) -> NDArray[np.complex128]:
    """Line phasors per harmonic of the first line, matching line_waveforms_v (EQ-18)."""
    ph = list(phase_phasors)
    match connection:
        case ConnectionTopology.STAR:
            return ph[0] - ph[1]
        case ConnectionTopology.DELTA:
            return ph[0] - (ph[0] + ph[1] + ph[2]) / 3.0
        case ConnectionTopology.OPEN:
            return ph[0]


def _ideal_integral(rotor_spec: RotorSpec, g_plane: float, z_list: Sequence[float], r_a: float, r_b: float) -> float:
    """Mean over copper z of the integral of B_z,1 r dr over the magnet span (Xcoil analyzeElements `ideal`, EQ-27)."""
    radii = r_a + (r_b - r_a) * (np.arange(IDEAL_INTEGRAL_STEPS) + 0.5) / IDEAL_INTEGRAL_STEPS
    alpha = pole_arc_ratio_mm(rotor_spec, radii)
    mean_bz = np.mean(
        [
            field_harmonic(1, radii, np.full_like(radii, z + rotor_spec.air_gap_mm), rotor_spec, g_plane, alpha)[0]
            for z in z_list
        ],
        axis=0,
    )
    return float(np.sum(mean_bz * radii * (r_b - r_a) / IDEAL_INTEGRAL_STEPS))
