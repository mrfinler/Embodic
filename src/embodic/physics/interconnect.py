"""Interconnect copper by role: Xcoil's lineStub, link and neutralRing sums and the copper loss P_ic (EQ-23).

The roles come from `Circuit.interconnect_roles` (interfaces.md section 5). Physics never infers a role from a net
name or a primitive role; a layout with interconnect paths and no roles is unclassified and yields no sums.
"""

import itertools
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from embodic.geometry.circuit import LineLead, NeutralLead, NeutralRing, PhaseLink
from embodic.geometry.layout import Layout
from embodic.geometry.primitives import Arc, Line, Primitive, primitive_length_mm
from embodic.model.vocabulary import ConnectionTopology, Phase
from embodic.units import MM_PER_M, mm_to_m


@dataclass(frozen=True, slots=True, kw_only=True)
class InterconnectResistance:
    """Per-phase sums in the order of the analysed phases, and the neutral-ring segments in ring order (ohm)."""

    line_stub_ohm: tuple[float, ...]
    link_ohm: tuple[float, ...]
    neutral_ring_ohm: tuple[float, ...]

    def total_ohm(self) -> float:
        """Return the sum of every stub, link and ring segment."""
        return math.fsum([*self.line_stub_ohm, *self.link_ohm, *self.neutral_ring_ohm])


def is_unclassified(layout: Layout) -> bool:
    """Return True when the layout has interconnect copper but its generator recorded no roles."""
    circuit = layout.circuit
    return bool(circuit.interconnect_path_ids) and not circuit.interconnect_roles


def interconnect_resistance(
    layout: Layout,
    phases: Sequence[Phase],
    path_r_ohm: Mapping[int, float],
    layer_thickness_mm: Mapping[str, float],
    resistivity_ohm_m: float,
) -> InterconnectResistance:
    """Return Xcoil's interconnectResistance sums for one classified board.

    References: EQ-23 (Xcoil interconnectResistance, engine.js l.1361-1372). A LineLead adds its path to the line
    stub of its phase, a PhaseLink to the link of its phase, a NeutralRing adds one segment per pair of consecutive
    taps, and a NeutralLead carries no current in a balanced star, so it adds nothing.

    Parameters
    ----------
    layout : Layout
        Board whose circuit lists one role per interconnect path.
    phases : Sequence[Phase]
        Analysed phases; fixes the order of the per-phase sums.
    path_r_ohm : Mapping[int, float]
        Resistance of every path by id, at the temperature wanted, in ohm.
    layer_thickness_mm : Mapping[str, float]
        Copper thickness of each layer in mm.
    resistivity_ohm_m : float
        Resistivity at the same temperature as `path_r_ohm`, for the ring segments.

    Returns
    -------
    InterconnectResistance
        The sums in ohm.
    """
    stub = [0.0] * len(phases)
    link = [0.0] * len(phases)
    ring: list[float] = []
    paths = {p.id: p for p in layout.paths}
    vias = {v.id: (v.x_mm, v.y_mm) for v in layout.vias}
    for role in layout.circuit.interconnect_roles:
        match role:
            case LineLead(path_id=pid, phase=phase):
                stub[phases.index(phase)] += path_r_ohm[pid]
            case PhaseLink(path_id=pid, phase=phase):
                link[phases.index(phase)] += path_r_ohm[pid]
            case NeutralRing(path_id=pid, tap_via_ids=taps):
                path = paths[pid]
                ring += ring_segment_resistance_ohm(
                    path.primitives,
                    [vias[t] for t in taps],
                    layer_thickness_mm[path.layer],
                    resistivity_ohm_m,
                )
            case NeutralLead():
                pass
    return InterconnectResistance(line_stub_ohm=tuple(stub), link_ohm=tuple(link), neutral_ring_ohm=tuple(ring))


def sum_boards(parts: Sequence[InterconnectResistance]) -> InterconnectResistance:
    """Add the per-phase sums of several boards, and the ring segments of the same index."""

    def add(columns: Sequence[tuple[float, ...]]) -> tuple[float, ...]:
        width = max((len(c) for c in columns), default=0)
        return tuple(math.fsum(c[i] for c in columns if i < len(c)) for i in range(width))

    return InterconnectResistance(
        line_stub_ohm=add([p.line_stub_ohm for p in parts]),
        link_ohm=add([p.link_ohm for p in parts]),
        neutral_ring_ohm=add([p.neutral_ring_ohm for p in parts]),
    )


def ring_segment_resistance_ohm(
    primitives: Sequence[Primitive],
    taps_mm: Sequence[tuple[float, float]],
    thickness_mm: float,
    resistivity_ohm_m: float,
) -> list[float]:
    """Return the resistance of the copper between each pair of consecutive taps along one path.

    References: EQ-10 per primitive; Xcoil interconnectResistance l.1369-1370 takes the ring arc between two tap
    angles. Each tap is projected on the nearest primitive of the path; the path is walked in primitive order.

    Parameters
    ----------
    primitives : Sequence[Primitive]
        The ring path, primitives end to end.
    taps_mm : Sequence[tuple[float, float]]
        Tap via centres in ring order, in mm.
    thickness_mm : float
        Copper thickness in mm.
    resistivity_ohm_m : float
        Resistivity in ohm*m.

    Returns
    -------
    list[float]
        One resistance in ohm per segment, len(taps) - 1 entries.
    """
    lengths = [primitive_length_mm(p) for p in primitives]
    starts = [math.fsum(lengths[:i]) for i in range(len(lengths))]
    positions = [_position_mm(primitives, starts, xy) for xy in taps_mm]
    ohm_per_mm = [resistivity_ohm_m / MM_PER_M / ((p.width_mm / MM_PER_M) * mm_to_m(thickness_mm)) for p in primitives]
    out = []
    for a, b in itertools.pairwise(positions):
        lo, hi = min(a, b), max(a, b)
        out.append(
            math.fsum(
                k * max(0.0, min(hi, s + n) - max(lo, s)) for k, s, n in zip(ohm_per_mm, starts, lengths, strict=True)
            )
        )
    return out


def _position_mm(primitives: Sequence[Primitive], starts: Sequence[float], xy: tuple[float, float]) -> float:
    """Distance along the path to the projection of a point on its nearest primitive."""
    found = [_project(p, xy) for p in primitives]
    index = min(range(len(found)), key=lambda i: found[i][0])
    return starts[index] + found[index][1]


def _project(prim: Primitive, xy: tuple[float, float]) -> tuple[float, float]:
    """(distance from the point to the primitive, distance along the primitive to the foot point), in mm."""
    x, y = xy
    if isinstance(prim, Line):
        dx, dy = prim.x2_mm - prim.x1_mm, prim.y2_mm - prim.y1_mm
        length = math.hypot(dx, dy)
        t = 0.0 if length == 0.0 else min(1.0, max(0.0, ((x - prim.x1_mm) * dx + (y - prim.y1_mm) * dy) / length**2))
        return math.hypot(x - prim.x1_mm - t * dx, y - prim.y1_mm - t * dy), t * length
    assert isinstance(prim, Arc)
    angle = math.atan2(y - prim.cy_mm, x - prim.cx_mm)
    offset = (math.copysign(1.0, prim.sweep_rad) * (angle - prim.start_rad)) % (2.0 * math.pi)
    span = abs(prim.sweep_rad)
    # outside the arc: the nearer end, so a tap a rounding error before the start lands on the start
    swept = offset if offset <= span else (span if offset - span < 2.0 * math.pi - offset else 0.0)
    fx = prim.cx_mm + prim.r_mm * math.cos(prim.start_rad + math.copysign(swept, prim.sweep_rad))
    fy = prim.cy_mm + prim.r_mm * math.sin(prim.start_rad + math.copysign(swept, prim.sweep_rad))
    return math.hypot(x - fx, y - fy), prim.r_mm * swept


def interconnect_loss_w(
    resistance: InterconnectResistance, connection: ConnectionTopology, line_current_a: float
) -> float:
    """Return the copper loss of the interconnect.

    References: EQ-23 (Xcoil applyConnection l.1422-1429). Star: I_line^2 (sum stub + sum link + sum ring); delta:
    I_line^2 sum stub + I_ph^2 sum link with I_ph = I_line / sqrt(3); open: 0.

    Parameters
    ----------
    resistance : InterconnectResistance
        The sums in ohm.
    connection : ConnectionTopology
        The analysed connection.
    line_current_a : float
        Line current in A rms.

    Returns
    -------
    float
        Loss in W.
    """
    match connection:
        case ConnectionTopology.STAR:
            return line_current_a**2 * resistance.total_ohm()
        case ConnectionTopology.DELTA:
            phase_current_a = line_current_a / math.sqrt(3.0)
            return line_current_a**2 * math.fsum(resistance.line_stub_ohm) + phase_current_a**2 * math.fsum(
                resistance.link_ohm
            )
        case ConnectionTopology.OPEN:
            return 0.0
