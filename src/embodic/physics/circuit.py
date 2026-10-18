"""Phase assembly from the electrical element list (EQ-07) and the connection-level results (EQ-19, EQ-23, EQ-26)."""

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from embodic.geometry.circuit import Circuit
from embodic.model.vocabulary import ConnectionTopology, Phase
from embodic.units import MM_PER_M

T_MM2_TO_V_S_PER_RAD = 1.0 / (MM_PER_M * MM_PER_M)  # T*mm^2 per rad -> V*s/rad


def add_phasors(phasors: Iterable[NDArray[np.complex128]], like: NDArray[np.complex128]) -> NDArray[np.complex128]:
    """Add phasor arrays one after another, in Xcoil's order (a pairwise NumPy reduction would reorder the terms).

    References: EQ-07 (series sum of group phasors).

    Parameters
    ----------
    phasors : Iterable[NDArray[np.complex128]]
        Phasor arrays per harmonic, all in one unit (T*mm^2, T*mm^2/ohm, V*s/rad or V at the call sites).
    like : NDArray[np.complex128]
        Array whose shape and dtype the sum takes; only those are read, so its unit (T*mm^2, V*s/rad or V) is free.

    Returns
    -------
    NDArray[np.complex128]
        The sum, in the unit of the inputs (T*mm^2, T*mm^2/ohm, V*s/rad or V at the call sites).
    """
    total = np.zeros_like(like)
    for x in phasors:
        total = total + x
    return total


@dataclass(frozen=True, slots=True, kw_only=True)
class CircuitSolution:
    """Per-phase EMF phasors of every harmonic, resistance and circulating loss.

    interfaces.md section 8 keeps harmonic 1 only; EQ-18 needs every harmonic, so the phasors are arrays in the order
    of the analysed harmonics.
    """

    phase_emf_phasor_v_s_per_rad: Mapping[Phase, NDArray[np.complex128]]
    phase_resistance_ohm: Mapping[Phase, float]
    circulating_loss_w: Mapping[Phase, float]


def solve_phase_circuit(
    circuit: Circuit,
    path_flux_linkage_t_mm2: Mapping[int, NDArray[np.complex128]],
    path_r_ohm: Mapping[int, float],
    via_r_ohm: Mapping[int, float],
    mechanical_speed_rad_per_s: float,
) -> CircuitSolution:
    """Assemble each phase: members in series inside, members of a group in parallel, groups in series.

    References: EQ-07, E_grp = sum(E_i / R_i) / sum(1 / R_i), R_grp = 1 / sum(1 / R_i),
    P_c = sum |E_i - E_grp|^2 / (2 R_i) on the fundamental (Xcoil analyzeElements l.1880-1890).

    Parameters
    ----------
    circuit : Circuit
        Phases as series groups of parallel members.
    path_flux_linkage_t_mm2 : Mapping[int, NDArray[np.complex128]]
        Flux-linkage phasors per harmonic of each path id in T*mm^2.
    path_r_ohm : Mapping[int, float]
        Resistance of each path id in ohm.
    via_r_ohm : Mapping[int, float]
        Resistance of each via id in ohm.
    mechanical_speed_rad_per_s : float
        omega_m in rad/s for the circulating loss.

    Returns
    -------
    CircuitSolution
        Phasors in V*s/rad, resistance in ohm and circulating loss in W per phase.
    """
    emf: dict[Phase, NDArray[np.complex128]] = {}
    resistance: dict[Phase, float] = {}
    circulating: dict[Phase, float] = {}
    for phase in circuit.phases:
        total = np.zeros_like(next(iter(path_flux_linkage_t_mm2.values())))
        r_phase = 0.0
        loss = 0.0
        for group in phase.groups:
            lam = [add_phasors((path_flux_linkage_t_mm2[i] for i in m.path_ids), total) for m in group.members]
            r = [
                math.fsum([*(path_r_ohm[i] for i in m.path_ids), *(via_r_ohm[i] for i in m.via_ids)])
                for m in group.members
            ]
            conductance = math.fsum(1.0 / x for x in r)
            v = add_phasors((x / ri for x, ri in zip(lam, r, strict=True)), total) / conductance
            if len(group.members) > 1:
                for x, ri in zip(lam, r, strict=True):
                    loss += abs((x[0] - v[0]) * T_MM2_TO_V_S_PER_RAD * mechanical_speed_rad_per_s) ** 2 / 2.0 / ri
            total = total + v
            r_phase += 1.0 / conductance
        emf[phase.phase] = total * T_MM2_TO_V_S_PER_RAD
        resistance[phase.phase] = r_phase
        circulating[phase.phase] = loss
    return CircuitSolution(
        phase_emf_phasor_v_s_per_rad=emf, phase_resistance_ohm=resistance, circulating_loss_w=circulating
    )


def delta_circulating_loss_w(phase_emf_v: Sequence[NDArray[np.complex128]], loop_resistance_ohm: float) -> float:
    """Return the loss of the current that harmonics not cancelling around a delta drive (upper bound).

    References: EQ-19, I_n = |sum_ph E_n| / R_loop, P = sum_n I_n^2 R_loop / 2 with peak phasors (Xcoil applyConnection
    l.1412-1418); the mesh inductance is neglected, so the result is an upper bound.

    Parameters
    ----------
    phase_emf_v : Sequence[NDArray[np.complex128]]
        Peak EMF phasor per harmonic of each phase in V.
    loop_resistance_ohm : float
        Resistance around the mesh in ohm.

    Returns
    -------
    float
        Loss in W.
    """
    mesh = np.abs(add_phasors(phase_emf_v, phase_emf_v[0]))
    return float(math.fsum((mesh / loop_resistance_ohm) ** 2 / 2.0) * loop_resistance_ohm)


def line_resistance_ohm(
    phase_r_ohm: Sequence[float],
    topology: ConnectionTopology,
    line_stub_ohm: Sequence[float] = (0.0, 0.0, 0.0),
    link_ohm: Sequence[float] = (0.0, 0.0, 0.0),
    neutral_ring_ohm: Sequence[float] = (),
) -> float:
    """Return the terminal-to-terminal resistance.

    References: EQ-23 (Xcoil applyConnection l.1421-1430). Star: R_LL = (2/3) sum(R_k + l_k + s_k) + (2/3)(n_1 + n_2);
    delta: b_k = R_k + l_k, R_LL = (1/3) sum b_k (S - b_k) / S + (2/3) sum s_k; open: the mean phase resistance.

    Parameters
    ----------
    phase_r_ohm : Sequence[float]
        Winding resistance of each phase in ohm.
    topology : ConnectionTopology
        Star, delta or open.
    line_stub_ohm : Sequence[float]
        Terminal stub resistance per phase in ohm.
    link_ohm : Sequence[float]
        Phase link resistance per phase in ohm.
    neutral_ring_ohm : Sequence[float]
        The two neutral-ring segments in ohm (star only).

    Returns
    -------
    float
        Resistance in ohm.
    """
    match topology:
        case ConnectionTopology.STAR:
            ring = 2.0 * math.fsum(neutral_ring_ohm[:2]) / 3.0
            return 2.0 * math.fsum([*phase_r_ohm, *line_stub_ohm, *link_ohm]) / 3.0 + ring
        case ConnectionTopology.DELTA:
            branch = [r + lk for r, lk in zip(phase_r_ohm, link_ohm, strict=True)]
            total = math.fsum(branch)
            return math.fsum(b * (total - b) / total for b in branch) / 3.0 + 2.0 * math.fsum(line_stub_ohm) / 3.0
        case ConnectionTopology.OPEN:
            return math.fsum(phase_r_ohm) / len(phase_r_ohm)


def efficiency(output_w: float, loss_w: float) -> float:
    """Return eta = P_out / (P_out + P_loss), 0 without output.

    References: EQ-26 (Xcoil applyConnection l.1434).

    Parameters
    ----------
    output_w : float
        Mechanical output T omega_m in W.
    loss_w : float
        Loss sum in W.

    Returns
    -------
    float
        Efficiency, dimensionless.
    """
    return output_w / (output_w + loss_w) if output_w > 0.0 else 0.0


def motor_constant_n_m_per_sqrt_w(torque_n_m: float, copper_loss_w: float, phase_current_a: float) -> float:
    """Return K_m = T / sqrt(P_Cu), 0 without copper loss or phase current.

    References: EQ-26 (Xcoil applyConnection l.1435).

    Parameters
    ----------
    torque_n_m : float
        Torque at the operating current in N*m.
    copper_loss_w : float
        Winding copper loss in W.
    phase_current_a : float
        Phase current in A rms.

    Returns
    -------
    float
        Motor constant in N*m/sqrt(W).
    """
    return torque_n_m / math.sqrt(copper_loss_w) if copper_loss_w > 0.0 and phase_current_a > 0.0 else 0.0
