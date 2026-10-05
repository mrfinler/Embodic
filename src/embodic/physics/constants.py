"""Motor constants from the phase EMF constant and the connection (EQ-09)."""

import math
from dataclasses import dataclass

from embodic.model.vocabulary import ConnectionTopology


@dataclass(frozen=True, slots=True, kw_only=True)
class MotorConstants:
    """Terminal constants seen by the drive."""

    ke_line_v_s_per_rad: float
    kt_n_m_per_a: float  # per line ampere rms
    kv_rpm_per_v: float


def phase_constants(
    ke_phase_v_s_per_rad: float, topology: ConnectionTopology, phases: int, poles: int
) -> MotorConstants:
    """Return Ke line-to-line, Kt per line ampere rms and Kv.

    References: EQ-09 (Xcoil applyConnection, engine.js l.1398-1406). Star: Ke_LL = sqrt(3) Ke_ph; delta and open:
    Ke_LL = Ke_ph. Kt = (m / sqrt(2)) Ke_ph, divided by sqrt(3) in delta. Kv = 60 / (2 pi Ke_LL). A connection other
    than open needs three phases, as in Xcoil.

    Parameters
    ----------
    ke_phase_v_s_per_rad : float
        Peak phase EMF per mechanical rad/s in V*s/rad.
    topology : ConnectionTopology
        Star, delta or open.
    phases : int
        Phase count m.
    poles : int
        Rotor pole count; Ke is per mechanical radian, so the identities do not use it.

    Returns
    -------
    MotorConstants
        Ke_LL in V*s/rad, Kt in N*m/A, Kv in rpm/V (infinity for Ke_LL = 0).
    """
    del poles
    connection = topology if phases == 3 else ConnectionTopology.OPEN
    ke_line = ke_phase_v_s_per_rad * math.sqrt(3.0) if connection is ConnectionTopology.STAR else ke_phase_v_s_per_rad
    kt = (
        phases
        * ke_phase_v_s_per_rad
        / math.sqrt(2.0)
        * (1.0 / math.sqrt(3.0) if connection is ConnectionTopology.DELTA else 1.0)
    )
    kv = 60.0 / (2.0 * math.pi) / ke_line if ke_line > 0.0 else math.inf
    return MotorConstants(ke_line_v_s_per_rad=ke_line, kt_n_m_per_a=kt, kv_rpm_per_v=kv)
