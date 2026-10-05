"""DC resistance of copper paths and via barrels (EQ-10, EQ-11)."""

from collections.abc import Mapping

import numpy as np

from embodic.geometry.arrays import LayoutArrays
from embodic.units import MM_PER_M, FloatArray, mm_to_m

UM_PER_MM = MM_PER_M


def copper_resistivity_ohm_m(temperature_degc: float, rho20_ohm_m: float, alpha_per_k: float) -> float:
    """Return the copper resistivity at a temperature.

    References: EQ-10, rho_T = rho_20 (1 + alpha_20 (T - 20)).

    Parameters
    ----------
    temperature_degc : float
        Copper temperature in degC.
    rho20_ohm_m : float
        Resistivity at 20 degC in ohm*m (registry constant copper_resistivity_20c_ohm_m).
    alpha_per_k : float
        Temperature coefficient at 20 degC in 1/K (registry constant copper_temp_coeff_per_k).

    Returns
    -------
    float
        Resistivity in ohm*m.
    """
    return rho20_ohm_m * (1.0 + alpha_per_k * (temperature_degc - 20.0))


def path_resistance_ohm(
    arrays: LayoutArrays, layer_thickness_mm: Mapping[str, float], resistivity_ohm_m: float
) -> FloatArray:
    """Return the DC resistance of every copper path, indexed by path id.

    References: EQ-10, R = sum rho L_i / (w_i t), one term per primitive with its own width (Xcoil primsResistance).

    Parameters
    ----------
    arrays : LayoutArrays
        Per-layer primitive rows (lengths and widths in mm) with their path ids.
    layer_thickness_mm : Mapping[str, float]
        Copper thickness of each layer in mm.
    resistivity_ohm_m : float
        Resistivity at the operating temperature in ohm*m.

    Returns
    -------
    FloatArray
        Resistance in ohm per path id; 0 for an id with no copper.
    """
    size = 1 + max((int(ix.max()) for ix in arrays.path_index.values() if ix.size), default=-1)
    out = np.zeros(size, dtype=np.float64)
    for layer, path_ids in arrays.path_index.items():
        lines = arrays.lines[layer]
        arcs = arrays.arcs[layer]
        lengths = np.concatenate(
            [
                np.sqrt((lines[:, 2] - lines[:, 0]) ** 2 + (lines[:, 3] - lines[:, 1]) ** 2),
                arcs[:, 2] * np.abs(arcs[:, 4]),
            ]
        )
        widths = np.concatenate([lines[:, 4], arcs[:, 5]])
        thickness_m = mm_to_m(layer_thickness_mm[layer])
        terms = resistivity_ohm_m * mm_to_m(lengths) / (mm_to_m(widths) * thickness_m)
        np.add.at(out, path_ids, terms)
    return out


def via_resistance_ohm(
    drill_mm: float, plating_um: float, length_mm: float, resistivity_ohm_m: float, count: int
) -> float:
    """Return the resistance of count identical via barrels in parallel.

    References: EQ-11, A = pi (2 r t_p - t_p^2) with r = drill / 2 (plating grows inward), R = rho l / A / count.

    Parameters
    ----------
    drill_mm : float
        Finished drill diameter in mm.
    plating_um : float
        Barrel plating thickness in um.
    length_mm : float
        Barrel length in mm.
    resistivity_ohm_m : float
        Resistivity at the operating temperature in ohm*m.
    count : int
        Number of barrels in parallel, at least 1.

    Returns
    -------
    float
        Resistance in ohm.
    """
    r_mm = drill_mm / 2.0
    t_mm = plating_um / UM_PER_MM
    area_m2 = mm_to_m(mm_to_m(np.pi * (2.0 * r_mm * t_mm - t_mm * t_mm)))
    return float(resistivity_ohm_m * mm_to_m(length_mm) / area_m2 / count)
