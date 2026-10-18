"""Flux linkage, eddy-loss sums and the EC-05 edge metric of copper paths (EQ-06, EQ-12, EC-05).

A port of Xcoil analyzeElements (engine.js l.1846-1878): each path is cut into chords of at most max_segment_mm, the
radial part of every chord inside the magnet span [r_A, r_B] picks up B_z at its mid radius, and the field comes from a
table of 48 radial steps per copper z with linear interpolation, as in Xcoil.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from embodic.geometry.discretise import discretise_path
from embodic.geometry.primitives import Primitive
from embodic.model.rotor import ArcMagnet, RotorSpec
from embodic.physics.field import field_harmonic
from embodic.physics.magnets import pole_arc_ratio_block
from embodic.units import MM_PER_M, FloatArray, mm_to_m

FIELD_TABLE_STEPS = 48  # Xcoil NR in analyzeElements
_RADIAL_EPS_MM = 1.0 / MM_PER_M**3  # Xcoil analyzeElements radial tolerance, 1e-9 mm (engine.js l.1861-1862)


def pole_arc_ratio_mm(rotor: RotorSpec, radius_mm: FloatArray) -> FloatArray:
    """Return alpha_p at each radius: constant for an arc magnet, EQ-04 for a block magnet.

    Parameters
    ----------
    rotor : RotorSpec
        Magnet geometry in mm and the pole count.
    radius_mm : FloatArray
        Radii in mm.

    Returns
    -------
    FloatArray
        Pole-arc ratio, dimensionless.
    """
    magnet = rotor.magnet
    if isinstance(magnet, ArcMagnet):
        return np.full_like(np.asarray(radius_mm, dtype=np.float64), magnet.pole_arc_ratio)
    return pole_arc_ratio_block(magnet.width_mm, radius_mm, rotor.poles)


def pole_arc_ratio_eq_ids(rotor: RotorSpec) -> tuple[str, ...]:
    """Return the EQ-IDs pole_arc_ratio_mm evaluates: EQ-04 for a block magnet, none for an arc magnet's given ratio."""
    return () if isinstance(rotor.magnet, ArcMagnet) else ("EQ-04",)


def pole_arc_ratio_pointer(rotor: RotorSpec) -> str:
    """Return the input pole_arc_ratio_mm reads besides the poles: an arc magnet's ratio or a block magnet's width."""
    return "/rotor/magnet/pole_arc_ratio" if isinstance(rotor.magnet, ArcMagnet) else "/rotor/magnet/width_mm"


@dataclass(frozen=True, slots=True, kw_only=True)
class FieldTable:
    """Peak B_z and B_t of every harmonic on FIELD_TABLE_STEPS + 1 radii of the magnet span, at one copper z."""

    r_inner_mm: float
    r_outer_mm: float
    harmonics: tuple[int, ...]
    bz_t: FloatArray  # (harmonics, steps + 1)
    bt_t: FloatArray

    def at(self, radius_mm: float) -> tuple[FloatArray, FloatArray]:
        """Interpolate (B_z, B_t) per harmonic at one radius inside the span, as Xcoil `look` does."""
        steps = self.bz_t.shape[1] - 1
        x = (radius_mm - self.r_inner_mm) / (self.r_outer_mm - self.r_inner_mm) * steps
        i = max(0, min(steps - 1, math.floor(x)))
        t = x - i
        return (
            self.bz_t[:, i] * (1.0 - t) + self.bz_t[:, i + 1] * t,
            self.bt_t[:, i] * (1.0 - t) + self.bt_t[:, i + 1] * t,
        )


def field_table(
    rotor: RotorSpec, symmetry_plane_mm: float, z_from_magnet_mm: float, harmonics: Sequence[int]
) -> FieldTable:
    """Tabulate EQ-05 over the magnet span at z_from_magnet_mm (copper z + air gap).

    Parameters
    ----------
    rotor : RotorSpec
        Rotor and magnet inputs (T, mm).
    symmetry_plane_mm : float
        G in mm.
    z_from_magnet_mm : float
        Distance from the magnet face in mm.
    harmonics : Sequence[int]
        Odd harmonic orders.

    Returns
    -------
    FieldTable
        Peak B_z and B_t in T on FIELD_TABLE_STEPS + 1 radii.
    """
    r_a, r_b = rotor.magnet.radial_span_mm()
    radii = r_a + (r_b - r_a) * np.arange(FIELD_TABLE_STEPS + 1) / FIELD_TABLE_STEPS
    z = np.full_like(radii, z_from_magnet_mm)
    alpha = pole_arc_ratio_mm(rotor, radii)
    rows = [field_harmonic(n, radii, z, rotor, symmetry_plane_mm, alpha) for n in harmonics]
    return FieldTable(
        r_inner_mm=r_a,
        r_outer_mm=r_b,
        harmonics=tuple(harmonics),
        bz_t=np.array([bz for bz, _ in rows]),
        bt_t=np.array([bt for _, bt in rows]),
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class PathField:
    """What one copper path collects from the rotor field, per harmonic."""

    flux_linkage_t_mm2: NDArray[np.complex128]  # sum B_z,n r_m dr exp(-j n p theta_m), T*mm^2
    eddy_bz_sum: FloatArray  # sum L frac B_z,n^2 w^3 in T^2 mm^4
    eddy_bt_sum: FloatArray  # sum L frac B_t,n^2 w in T^2 mm^2
    edge_weight: float  # sum |B_z,1 r_m dr| inside the span (EC-05 w)
    edge_weighted: float  # sum w exp(-d / (c_e G)), without the D_e factor


def integrate_path(
    prims: Sequence[Primitive],
    table: FieldTable,
    pole_pairs: int,
    max_segment_mm: float,
    edge_decay_mm: float,
) -> PathField:
    """Integrate one path against the field table.

    References: EQ-06 (flux linkage), EQ-12 (eddy sums), EC-05 (edge weights with decay length c_e G).

    Parameters
    ----------
    prims : Sequence[Primitive]
        The path in current direction.
    table : FieldTable
        Field at the path's copper z.
    pole_pairs : int
        p.
    max_segment_mm : float
        Longest chord in mm (Xcoil 0.5).
    edge_decay_mm : float
        c_e G in mm for the EC-05 weight.

    Returns
    -------
    PathField
        Flux linkage and the loss and edge sums.
    """
    harmonics = np.array(table.harmonics, dtype=np.float64)
    lam = np.zeros(len(harmonics), dtype=np.complex128)
    ez = np.zeros(len(harmonics))
    et = np.zeros(len(harmonics))
    edge_w = 0.0
    edge_wd = 0.0
    r_a, r_b = table.r_inner_mm, table.r_outer_mm
    for g in discretise_path(prims, max_segment_mm):
        r1, r2 = math.hypot(g.x1_mm, g.y1_mm), math.hypot(g.x2_mm, g.y2_mm)
        if max(r1, r2) <= r_a + _RADIAL_EPS_MM or min(r1, r2) >= r_b - _RADIAL_EPS_MM:
            continue
        c1, c2 = min(r_b, max(r_a, r1)), min(r_b, max(r_a, r2))
        frac = abs(c2 - c1) / abs(r2 - r1) if abs(r2 - r1) >= _RADIAL_EPS_MM else 1.0
        a1, a2 = math.atan2(g.y1_mm, g.x1_mm), math.atan2(g.y2_mm, g.x2_mm)
        am = (a1 + a2) / 2.0 + (math.pi if abs(a2 - a1) > math.pi else 0.0)
        rm = (c1 + c2) / 2.0
        bz, bt = table.at(rm)
        lam += bz * rm * (c2 - c1) * np.exp(-1j * harmonics * pole_pairs * am)
        active = g.length_mm * frac
        ez += active * bz * bz * g.width_mm**3
        et += active * bt * bt * g.width_mm
        w = abs(bz[0] * rm * (c2 - c1))
        edge_w += w
        edge_wd += w * math.exp(-min(rm - r_a, r_b - rm) / edge_decay_mm)
    return PathField(flux_linkage_t_mm2=lam, eddy_bz_sum=ez, eddy_bt_sum=et, edge_weight=edge_w, edge_weighted=edge_wd)


def eddy_loss_w(
    field: PathField,
    harmonics: Sequence[int],
    thickness_mm: float,
    electrical_speed_rad_per_s: float,
    resistivity_ohm_m: float,
) -> float:
    """Return the eddy-current loss of one path.

    References: EQ-12, P = (sigma / 24) sum_n (n omega_e)^2 sum_seg L (B_z,n^2 w^3 t + B_t,n^2 w t^3) (Xcoil
    analyzeElements l.1871).

    Parameters
    ----------
    field : PathField
        Sums from integrate_path.
    harmonics : Sequence[int]
        Harmonic orders of the sums.
    thickness_mm : float
        Copper thickness in mm.
    electrical_speed_rad_per_s : float
        omega_e in rad/s.
    resistivity_ohm_m : float
        Resistivity at the operating temperature in ohm*m.

    Returns
    -------
    float
        Loss in W.
    """
    t_m = mm_to_m(thickness_mm)
    order = np.asarray(harmonics, dtype=np.float64) * electrical_speed_rad_per_s
    bz_m4 = field.eddy_bz_sum / MM_PER_M**4
    bt_m2 = field.eddy_bt_sum / MM_PER_M**2
    terms = order**2 * (bz_m4 * t_m + bt_m2 * t_m**3)
    return float(math.fsum(terms) / (24.0 * resistivity_ohm_m))


def edge_leakage_fraction(fields: Sequence[PathField], amplitude: float) -> float:
    """Return e_edge = D_e sum w exp(-d / (c_e G)) / sum w over every path; 0 without EMF-producing copper.

    References: EC-05 of EQ-05 (registry validity_checks; D_e and c_e from its parameters).

    Parameters
    ----------
    fields : Sequence[PathField]
        Edge weights of every path (T*mm^2).
    amplitude : float
        D_e, dimensionless.

    Returns
    -------
    float
        e_edge, dimensionless (a lower bound per DEF-23).
    """
    total = math.fsum(f.edge_weight for f in fields)
    return amplitude * math.fsum(f.edge_weighted for f in fields) / total if total > 0.0 else 0.0
