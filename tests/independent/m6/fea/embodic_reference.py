"""Embodic's OR-11 and OR-12 comparator values, recomputed through the release wheel's public API (Agent 4, U-V7).

Usage (inside a venv with the embodic 0.0.1 wheel installed):
    python -I embodic_reference.py --repo <worktree> --out results/embodic_reference.json

OR-11. The D09 A project is built by tests/independent/m5/oracle_check.py from oracle_cases.json (O2-D09 v2) and
computed with embodic.api.compute_project. b1 is AnalysisResult.layers[0].b1_peak_mid_radius_t. The harmonics 1 to 13
come from embodic.physics.field_harmonic at each radius and z the FEA samples, for magnet mu_r 1.05, 1.03 and 1.10.
OR-12. One straight trace 0.8 mm wide, 20 mm long, in a uniform FieldTable built here, through
embodic.physics.integrate_path and eddy_loss_w; resistivity from the registry constant via copper_resistivity_ohm_m.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import math
import sys
from pathlib import Path

import numpy as np

from embodic import api, physics
from embodic.geometry.primitives import Line, PrimitiveRole
from embodic.physics.emf import FieldTable

HARMONICS = (1, 3, 5, 7, 9, 11, 13)
RADII_MM = (27.0, 35.5, 44.0)
MU_R = (1.05, 1.03, 1.10)
TRACE_W_MM, TRACE_T_MM, TRACE_L_MM = 0.8, 0.07, 20.0
B0_T = 0.846122


def waveform(b: list[float]) -> dict:
    """Return the pole-centre value and the waveform maximum of sum b_n cos(n phi)."""
    phi = np.linspace(0.0, math.pi, 7201)
    wave = sum(bn * np.cos(n * phi) for bn, n in zip(b, HARMONICS, strict=True))
    i = int(np.argmax(np.abs(wave)))
    return {"centre_t": float(sum(b)), "max_t": float(abs(wave[i])), "max_at_elec_deg": math.degrees(phi[i])}


def or11(repo: Path) -> dict:
    """Return b1 of layer 0 of the D09 A build and field_harmonic rows per mu_r, radius and plane."""
    sys.path.insert(0, str(repo / "tests" / "independent" / "m5"))
    import oracle_check as oc

    cases = json.loads((repo / "docs" / "phase2" / "engineering" / "oracle_cases.json").read_text())["cases"]
    v = oc.case_values(cases, "O2-D09")
    outcome = oc.compute(oc.d09(v, "A", 20.0))
    rotor = outcome.design.rotor
    board = v["board_thickness_mm"]
    g_plane = physics.symmetry_plane_mm(rotor, board)
    layer = outcome.analysis.layers[0]
    z_l1 = v["air_gap_per_side_mm"] + float(layer.z_mm.value)
    alpha = np.array([v["magnet_pole_arc_ratio"]])
    rows = []
    for mu in MU_R:
        rot = dataclasses.replace(rotor, recoil_permeability=mu)
        for r in RADII_MM:
            for plane, z in (("copper_L1", z_l1), ("centre", g_plane)):
                b = [
                    float(physics.field_harmonic(n, np.array([r]), np.array([z]), rot, g_plane, alpha)[0][0])
                    for n in HARMONICS
                ]
                rows.append({"mu_r": mu, "r_mm": r, "plane": plane, "z_mm": z, "b_n_t": b, "b1_t": b[0], **waveform(b)})
    return {
        "b1_peak_mid_radius_t_layer0": float(layer.b1_peak_mid_radius_t.value),
        "layer0_z_mm_from_board_surface": float(layer.z_mm.value),
        "z_l1_from_magnet_mm": z_l1,
        "symmetry_plane_G_mm": g_plane,
        "rotor": {
            "poles": rotor.poles,
            "remanence_t": rotor.remanence_t,
            "recoil_permeability": rotor.recoil_permeability,
            "magnet_thickness_mm": rotor.magnet.thickness_mm,
            "pole_arc_ratio": v["magnet_pole_arc_ratio"],
        },
        "harmonics": list(HARMONICS),
        "rows": rows,
    }


def or12() -> dict:
    """Return eddy_loss_w per metre of one straight trace in uniform B_z or B_t, at f_e and 13 f_e."""
    reg = api.load_registry()
    rho20 = float(reg.constant("copper_resistivity_20c_ohm_m").value)
    alpha20 = float(reg.constant("copper_temp_coeff_per_k").value)
    rho = physics.copper_resistivity_ohm_m(20.0, rho20, alpha20)
    f_e = 8 * 2000 / 60
    trace = (
        Line(x1_mm=28.0, y1_mm=0.0, x2_mm=28.0 + TRACE_L_MM, y2_mm=0.0, width_mm=TRACE_W_MM, role=PrimitiveRole.SIDE),
    )
    rows = []
    for case, bz, bt in (("12a_Bz", B0_T, 0.0), ("12b_Bt", 0.0, B0_T)):
        for mult in (1, 13):
            row = np.ones((1, 49))
            table = FieldTable(r_inner_mm=25.0, r_outer_mm=50.0, harmonics=(1,), bz_t=row * bz, bt_t=row * bt)
            field = physics.integrate_path(trace, table, 8, 0.5, 1.0)
            omega = 2 * math.pi * f_e * mult
            p_w = physics.eddy_loss_w(field, (1,), TRACE_T_MM, omega, rho)
            rows.append(
                {
                    "case": case,
                    "frequency_hz": f_e * mult,
                    "loss_w_per_m": p_w / (TRACE_L_MM * 1e-3),
                    "skin_depth_mm": physics.skin_depth_mm(f_e * mult, rho),
                }
            )
    return {
        "rho20_ohm_m": rho20,
        "rho_ohm_m": rho,
        "b0_t": B0_T,
        "trace_mm": [TRACE_W_MM, TRACE_T_MM, TRACE_L_MM],
        "rows": rows,
    }


def main() -> int:
    """Write embodic_reference.json and print the comparator values."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = {"embodic_version": str(api.version_info()), "embodic_file": api.__file__}
    out.update(or11=or11(args.repo.resolve()), or12=or12())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=1, default=str))
    o = out["or11"]
    print(
        f"OR-11 b1_peak_mid_radius_t layer 0: {o['b1_peak_mid_radius_t_layer0']:.6f} T at z {o['z_l1_from_magnet_mm']}"
    )
    for r in o["rows"]:
        if r["mu_r"] == 1.05:
            print(
                f"  r {r['r_mm']:5.1f} {r['plane']:9s} z {r['z_mm']:.3f}: b1 {r['b1_t']:.6f} centre {r['centre_t']:.6f}"
                f" max {r['max_t']:.6f} at {r['max_at_elec_deg']:.2f} deg"
            )
    for r in out["or12"]["rows"]:
        print(
            f"OR-12 {r['case']} {r['frequency_hz']:.2f} Hz: {r['loss_w_per_m']:.6e} W/m,"
            f" delta {r['skin_depth_mm']:.4f} mm"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
