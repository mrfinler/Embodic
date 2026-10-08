"""Own EQ-05 field and EQ-06 flux linkage, independent of embodic.physics (item 4, OR-01).

Field: equation_specification.md EQ-05, cosh/sinh form, evaluated exactly at every chord mid radius (no table):
B_z,n = K_n cosh(u (G - z)) / (cosh(u G) + mu_r coth(u l_m) sinh(u G)), K_n = 4 B_r / (n pi) sin(n pi alpha / 2),
u = n p / r, z from the magnet face. EMF: equation_specification.md EQ-06, e = omega_m sum B_z r_m dr over chords,
dr clipped to the magnet span; the geometry walked is the subject's (embodic Layout paths), the arithmetic is own.
"""

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Field:
    """EQ-05 inputs of one rotor: poles, B_r in T, mu_r, magnet thickness, G and span in mm."""

    poles: int
    remanence_t: float
    mu_r: float
    magnet_mm: float
    g_plane_mm: float  # magnet face to symmetry plane
    alpha: float
    r_a_mm: float
    r_b_mm: float

    def bz(self, n: int, r_mm: np.ndarray, z_mm: float) -> np.ndarray:
        """Return the peak B_z of harmonic n in T at radii r_mm and distance z_mm from the magnet face."""
        u = n * (self.poles // 2) / r_mm
        k_n = 4 * self.remanence_t / (n * math.pi) * math.sin(n * math.pi * self.alpha / 2)
        g = self.g_plane_mm
        return (
            k_n * np.cosh(u * (g - z_mm)) / (np.cosh(u * g) + self.mu_r / np.tanh(u * self.magnet_mm) * np.sinh(u * g))
        )


def chord_points(prim: object, step_mm: float) -> np.ndarray:
    """Points along a Line or Arc record (read through its public fields) at most step_mm apart."""
    if hasattr(prim, "x1_mm"):
        length = math.hypot(prim.x2_mm - prim.x1_mm, prim.y2_mm - prim.y1_mm)
        t = np.linspace(0.0, 1.0, max(1, math.ceil(length / step_mm)) + 1)
        return np.column_stack([prim.x1_mm + t * (prim.x2_mm - prim.x1_mm), prim.y1_mm + t * (prim.y2_mm - prim.y1_mm)])
    count = max(1, math.ceil(prim.r_mm * abs(prim.sweep_rad) / step_mm))
    a = prim.start_rad + prim.sweep_rad * np.linspace(0.0, 1.0, count + 1)
    return np.column_stack([prim.cx_mm + prim.r_mm * np.cos(a), prim.cy_mm + prim.r_mm * np.sin(a)])


def path_flux_linkage(prims: Iterable[object], field: Field, z_mm: float, harmonics: Sequence[int], step_mm: float):
    """Complex sum B_z,n r_m dr exp(-j n p theta_m) in T mm^2 per harmonic."""
    p = field.poles // 2
    out = np.zeros(len(harmonics), dtype=np.complex128)
    for prim in prims:
        pts = chord_points(prim, step_mm)
        r = np.hypot(pts[:, 0], pts[:, 1])
        c1, c2 = np.clip(r[:-1], field.r_a_mm, field.r_b_mm), np.clip(r[1:], field.r_a_mm, field.r_b_mm)
        dr = c2 - c1
        keep = dr != 0.0
        if not keep.any():
            continue
        rm = (c1 + c2)[keep] / 2
        mid = (pts[:-1] + pts[1:])[keep] / 2
        theta = np.arctan2(mid[:, 1], mid[:, 0])
        for i, n in enumerate(harmonics):
            out[i] += np.sum(field.bz(n, rm, z_mm) * rm * dr[keep] * np.exp(-1j * n * p * theta))
    return out


def line_peak_v_s_per_rad(lam_a: np.ndarray, lam_b: np.ndarray, harmonics: Sequence[int], poles: int) -> float:
    """Peak over one electrical period of e_A - e_B per mechanical rad/s; lam in T mm^2."""
    p = poles // 2
    theta = np.linspace(0.0, 2 * math.pi / p, 7201)
    wave = sum(np.real((lam_a[i] - lam_b[i]) * np.exp(1j * n * p * theta)) for i, n in enumerate(harmonics))
    return float(np.max(np.abs(wave))) * 1e-6
