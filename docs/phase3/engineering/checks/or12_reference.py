# Prepared by: Agent 2 (Motor Design Expert), model: claude-opus-5-5
"""OR-12 comparator values: embodic's EQ-12 eddy loss of one straight D09 trace in a uniform sinusoidal field (U-E11).

Run from the repository root:
    PYTHONPATH=src /home/claude/embodic/.venv/bin/python docs/phase3/engineering/checks/or12_reference.py

The trace is 0.8 x 0.07 mm (D09 Table 2 p.3), 10 mm long and radial inside a hand-built uniform FieldTable (the seam
of EQT-06-CF02). B_z and B_t are applied one at a time. The FEA case of OR-12 compares its loss per metre with the
'embodic W/m' column. The amplitude 0.846122 T is the D09 A build's b1 (an example level; the loss scales with B^2).
"""

import math

import numpy as np

from embodic.geometry.primitives import Line, PrimitiveRole
from embodic.physics import eddy_loss_w, integrate_path, skin_depth_mm
from embodic.physics.emf import FieldTable

WIDTH_MM, THICK_MM, LENGTH_MM = 0.8, 0.07, 10.0
F_E_HZ = 8 * 2000 / 60  # D09 Table 2: 266.67 Hz
RHO_20 = 1.7241e-8  # registry copper_resistivity_20c_ohm_m (D-037 c)
B_T = 0.846122


def table(bz: float, bt: float) -> FieldTable:
    row = np.full((1, 49), 1.0)
    return FieldTable(r_inner_mm=25.0, r_outer_mm=46.0, harmonics=(1,), bz_t=row * bz, bt_t=row * bt)


def main() -> None:
    rho = RHO_20  # at 20 degC the temperature coefficient drops out
    omega = 2 * math.pi * F_E_HZ
    trace = (
        Line(x1_mm=30.0, y1_mm=0.0, x2_mm=30.0 + LENGTH_MM, y2_mm=0.0, width_mm=WIDTH_MM, role=PrimitiveRole.SIDE),
    )
    print(
        f"skin depth at {F_E_HZ:.2f} Hz: {skin_depth_mm(F_E_HZ, rho):.3f} mm; at n 13: {skin_depth_mm(13 * F_E_HZ, rho):.3f} mm"
    )
    w, t, sigma = WIDTH_MM * 1e-3, THICK_MM * 1e-3, 1 / rho
    for label, bz, bt, form, closed in (
        ("B_z (normal to the wide face)", B_T, 0.0, "w^3 t", sigma * omega**2 * B_T**2 * w**3 * t / 24),
        ("B_t (along the wide face)", 0.0, B_T, "w t^3", sigma * omega**2 * B_T**2 * w * t**3 / 24),
    ):
        f = integrate_path(trace, table(bz, bt), 8, 0.5, 1.0)
        p = eddy_loss_w(f, (1,), THICK_MM, omega, rho) / (LENGTH_MM * 1e-3)
        print(
            f"{label}: embodic {p:.6e} W/m, closed form sigma {form} w_e^2 B^2/24 {closed:.6e} W/m (rel {p / closed - 1:.1e})"
        )


if __name__ == "__main__":
    main()
