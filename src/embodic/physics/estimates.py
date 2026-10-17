"""Mass (EQ-16) and the first inductance estimate (EQ-14)."""

import math
from collections.abc import Mapping
from dataclasses import dataclass

from embodic.physics.losses import MU0_H_PER_M
from embodic.units import MM_PER_M, mm_to_m

MM3_PER_CM3 = (MM_PER_M / 100.0) ** 3


@dataclass(frozen=True, slots=True, kw_only=True)
class MassBreakdown:
    """Copper and laminate mass of the boards."""

    copper_g: float
    laminate_g: float


def mass_g(
    layer_copper_area_mm2: Mapping[str, float],
    layer_thickness_mm: Mapping[str, float],
    board_area_mm2: float,
    board_thickness_mm: float,
    copper_density_g_per_cm3: float,
    laminate_density_g_per_cm3: float,
) -> MassBreakdown:
    """Return the copper and laminate mass.

    References: EQ-16, m_Cu = rho_Cu sum_L A_Cu,L t_L; m_lam = rho_lam (A_board t_board - V_Cu) (Xcoil massThermal,
    engine.js l.1378-1388, with the registry densities).

    Parameters
    ----------
    layer_copper_area_mm2 : Mapping[str, float]
        Copper area of each layer in mm^2 (sum of length x width).
    layer_thickness_mm : Mapping[str, float]
        Copper thickness of each layer in mm.
    board_area_mm2 : float
        Board area in mm^2, outline minus cutouts, summed over boards.
    board_thickness_mm : float
        Thickness of one board in mm.
    copper_density_g_per_cm3 : float
        Copper density in g/cm^3.
    laminate_density_g_per_cm3 : float
        Laminate density in g/cm^3.

    Returns
    -------
    MassBreakdown
        Masses in g.
    """
    copper_mm3 = math.fsum(a * layer_thickness_mm[layer] for layer, a in layer_copper_area_mm2.items())
    laminate_mm3 = max(0.0, board_area_mm2 * board_thickness_mm - copper_mm3)
    return MassBreakdown(
        copper_g=copper_density_g_per_cm3 * copper_mm3 / MM3_PER_CM3,
        laminate_g=laminate_density_g_per_cm3 * laminate_mm3 / MM3_PER_CM3,
    )


def inductance_estimate_h(
    series_turns: float,
    winding_factor_1: float,
    r_outer_mm: float,
    r_inner_mm: float,
    pole_pairs: int,
    effective_gap_mm: float,
) -> float:
    """Return the magnetising inductance estimate (gate 'cannot verify yet', label estimate).

    References: EQ-14(a), L_m = (3 mu0 / (4 pi)) (N k_w1)^2 (D_o^2 - D_i^2) / (p^2 delta'), delta' = 2 l_m + 2 g + t_s.

    Parameters
    ----------
    series_turns : float
        Series turns per phase N, a pure number (no unit).
    winding_factor_1 : float
        Fundamental winding factor k_w1, dimensionless (no unit).
    r_outer_mm : float
        Active outer radius in mm (D_o = 2 r).
    r_inner_mm : float
        Active inner radius in mm (D_i = 2 r).
    pole_pairs : int
        p.
    effective_gap_mm : float
        delta' in mm.

    Returns
    -------
    float
        Inductance in H.
    """
    d_o, d_i = mm_to_m(2.0 * r_outer_mm), mm_to_m(2.0 * r_inner_mm)
    return (
        3.0
        * MU0_H_PER_M
        / (4.0 * math.pi)
        * (series_turns * winding_factor_1) ** 2
        * (d_o**2 - d_i**2)
        / (pole_pairs**2 * mm_to_m(effective_gap_mm))
    )
