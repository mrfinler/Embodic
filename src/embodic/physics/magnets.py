"""Magnet geometry seen by the field model (EQ-04)."""

import numpy as np

from embodic.units import FloatArray


def pole_arc_ratio_block(width_mm: float, radius_mm: FloatArray, poles: int) -> FloatArray:
    """Return the pole-arc ratio of a rectangular block magnet at each radius.

    References: EQ-04, alpha_p(r) = 2 p asin(w / (2 r)) / pi with p = poles / 2.

    Parameters
    ----------
    width_mm : float
        Tangential block width in mm.
    radius_mm : FloatArray
        Radii in mm; each must be at least width_mm / 2.
    poles : int
        Rotor pole count 2p.

    Returns
    -------
    FloatArray
        Pole-arc ratio, dimensionless, one per radius.
    """
    pole_pairs = poles // 2
    return 2.0 * pole_pairs * np.arcsin(width_mm / (2.0 * np.asarray(radius_mm, dtype=np.float64))) / np.pi
