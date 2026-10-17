"""Air-gap field of the rotor magnets, 2-D harmonic model at each radius (EQ-05)."""

import math

import numpy as np

from embodic.model.rotor import RotorSpec, RotorType
from embodic.units import FloatArray


def symmetry_plane_mm(rotor: RotorSpec, board_thickness_mm: float) -> float:
    """Return G, the distance from the magnet face to the flux-symmetry or iron plane.

    References: EQ-05 G. Xcoil fieldSetup (engine.js l.868-872) uses statorThickness; analyse() passes the
    BoardStack stack_thickness_mm here (D-016), so a per-phase stack moves the plane.

    Parameters
    ----------
    rotor : RotorSpec
        Rotor type and air gap per side in mm.
    board_thickness_mm : float
        Thickness between the two rotor halves in mm (the whole stack).

    Returns
    -------
    float
        G in mm: (t + 2g) / 2 for a double rotor, t + 2g with a yoke, infinity for an open single rotor.
    """
    match rotor.rotor_type:
        case RotorType.DOUBLE:
            return (board_thickness_mm + 2.0 * rotor.air_gap_mm) / 2.0
        case RotorType.SINGLE_YOKE:
            return board_thickness_mm + 2.0 * rotor.air_gap_mm
        case RotorType.SINGLE_OPEN:
            return math.inf


def field_harmonic(
    n: int,
    radius_mm: FloatArray,
    z_mm: FloatArray,
    rotor: RotorSpec,
    symmetry_plane_mm: float,
    alpha_p: FloatArray,
) -> tuple[FloatArray, FloatArray]:
    """Return the peak axial and tangential flux density of space harmonic n.

    References: EQ-05. Port of Xcoil fieldHarmonic (engine.js l.856-867) in its exp form, which equals the registry's
    cosh/sinh form and stays finite for large u. Beyond the symmetry plane z is mirrored; below the magnet face it is 0.

    Parameters
    ----------
    n : int
        Odd harmonic order, dimensionless.
    radius_mm : FloatArray
        Radius in mm (pole pitch pi r / p).
    z_mm : FloatArray
        Distance from the magnet face in mm.
    rotor : RotorSpec
        Poles, remanence in T, recoil permeability and magnet thickness in mm.
    symmetry_plane_mm : float
        G in mm from symmetry_plane_mm(); infinity for an open rotor.
    alpha_p : FloatArray
        Pole-arc ratio, the magnet angle over the pole-pitch angle (rad per rad, so no unit); scalar or one per radius.

    Returns
    -------
    tuple[FloatArray, FloatArray]
        (B_z, B_t) peak amplitudes in T.
    """
    r = np.asarray(radius_mm, dtype=np.float64)
    z = np.asarray(z_mm, dtype=np.float64)
    a_p = np.asarray(alpha_p, dtype=np.float64)
    u = n * (rotor.poles // 2) / r
    k_n = rotor.remanence_t * 4.0 / (n * math.pi) * np.sin(n * math.pi * a_p / 2.0)
    e2a = np.exp(-2.0 * u * rotor.magnet.thickness_mm)
    g = symmetry_plane_mm
    if math.isinf(g):
        zz = np.maximum(z, 0.0)
        e2b = np.zeros_like(u)
        e2c = np.zeros_like(u)
    else:
        zz = np.maximum(np.where(z <= g, z, 2.0 * g - z), 0.0)
        e2b = np.exp(-2.0 * u * (g - zz))
        e2c = np.exp(-2.0 * u * g)
    den = rotor.recoil_permeability * (1.0 + e2a) * (1.0 - e2c) + (1.0 - e2a) * (1.0 + e2c)
    base = k_n * np.exp(-u * zz) * (1.0 - e2a) / den
    return base * (1.0 + e2b), base * (1.0 - e2b)
