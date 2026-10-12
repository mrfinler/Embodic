"""OR-01, OR-02, OR-06, OR-08 re-run through the installed wheel's public API, on designs built here from paper values.

Usage (inside the wheel venv): python -I oracle_check.py --cases docs/phase2/engineering/oracle_cases.json --out o.json

Each design starts from a shipped example file only for the schema (field names, provenance block) and then sets every
value the oracle case names from oracle_cases.json (O1-D08 v4, O2-D09 v2). Conventions applied here, each labelled in
the record: coil spec radius = centre line -+ w/2 (spiral_generator_spec.md worked example 2); air gap = G - board/2
(O1-D08 note); dielectric = board - 2 x copper; coil gap = clearance; D08 pole-arc ratio 0.72 (assumption, as in
tests/independent/m2/or01.py). Expected values are the papers' numbers and the D-045g figures, compared as written.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
from pathlib import Path

import numpy as np

from embodic import api, physics
from embodic.paths import resource_root

D045G = {
    "OR-01": "-0.40 % (in band)",
    "OR-02": "+4.26 % (A) / -5.46 % (B), band +-8 %",
    "OR-06": "within print rounding",
    "OR-08": "peak 0.7384 T, band 0.72-0.75 T read as [0.7125, 0.7560] T",
}
HARMONICS = (1, 3, 5, 7, 9, 11, 13)


def case_values(cases: list[dict], case_id: str) -> dict:
    """Return input name -> value of one oracle case, the 'assumed' value where unresolved."""
    case = next(c for c in cases if c["case_id"] == case_id)
    return {
        k: (e["assumed"] if e.get("value") is None and "assumed" in e else e["value"])
        for k, e in case["inputs"].items()
    }


def template() -> dict:
    """Return the shipped D08 example as a schema template."""
    return json.loads((resource_root() / "examples" / "spiral_12c10p_d08.embodic.json").read_text())


def set_common(
    d: dict,
    *,
    poles,
    coils,
    width,
    clearance,
    turns,
    r_in_cl,
    r_out_cl,
    copper,
    board,
    air_gap,
    remanence,
    mu_r,
    magnet_mm,
    alpha,
    mag_r_in,
    mag_r_out,
    back_iron,
    topology,
    name,
) -> dict:
    """Write the oracle values into a template project and drop its example identity."""
    design = d["design"]
    design["name"] = name
    rotor = design["rotor"]
    rotor.update(
        poles=poles,
        air_gap_mm=air_gap,
        remanence_t=remanence,
        recoil_permeability=mu_r,
        rotor_type="double",
        back_iron_thickness_mm=back_iron,
    )
    rotor["magnet"].update(
        kind="arc", pole_arc_ratio=alpha, r_inner_mm=mag_r_in, r_outer_mm=mag_r_out, thickness_mm=magnet_mm
    )
    layers = design["stackup"]["layers"]
    layers[0]["thickness_mm"] = copper
    layers[2]["thickness_mm"] = copper
    layers[1]["thickness_mm"] = round(board - 2 * copper, 10)
    coil = design["winding"]["coil"]
    coil.update(
        coil_count=coils,
        trace_width_mm=width,
        clearance_mm=clearance,
        coil_gap_mm=clearance,
        turns=turns,
        r_inner_mm=round(r_in_cl - width / 2, 10),
        r_outer_mm=round(r_out_cl + width / 2, 10),
        side_style="parallel",
    )
    design["connection"]["topology"] = topology
    design["drc_rules"].update(trace_clearance_mm=clearance, via_clearance_mm=clearance)
    for key in ("design_hash", "origin_example", "example"):
        d.pop(key, None)
    return d


def compute(d: dict):
    """Compute a project dict through embodic.api.compute_project."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "case.embodic.json"
        path.write_text(json.dumps(d))
        outcome = api.compute_project(path)
    if isinstance(outcome, tuple):
        raise SystemExit(f"compute returned issues: {outcome}")
    return outcome


def d08(v: dict, temperature: float) -> dict:
    """Return my D08 project (O1-D08 v4) at the given winding temperature."""
    d = set_common(
        template(),
        poles=v["poles"],
        coils=v["coil_count"],
        width=v["trace_width_mm"],
        clearance=v["clearance_mm"],
        turns=v["turns_per_coil_per_layer"],
        r_in_cl=v["coil_r_inner_mm"],
        r_out_cl=v["coil_r_outer_mm"],
        copper=v["copper_thickness_mm"],
        board=v["board_thickness_mm"],
        air_gap=v["magnet_face_to_midplane_G_mm"] - v["board_thickness_mm"] / 2,
        remanence=v["magnet_remanence_T"],
        mu_r=v["magnet_recoil_permeability"],
        magnet_mm=v["magnet_thickness_mm"],
        alpha=0.72,
        mag_r_in=v["magnet_r_inner_mm"],
        mag_r_out=v["magnet_r_outer_mm"],
        back_iron=3.0,
        topology="star",
        name="D08 own build",
    )
    d["design"]["operating"]["winding_temperature_degc"] = temperature
    return d


def d09(v: dict, variant: str, temperature: float) -> dict:
    """Return my D09 project (O2-D09 v2) for variant A or B at the given winding temperature."""
    turns, r_in_cl, r_out_cl = {"A": (8, 25.2, 47.6), "B": (7, 20.2, 43.8)}[variant]
    d = set_common(
        template(),
        poles=v["poles"],
        coils=v["coil_count"],
        width=v["trace_width_mm"],
        clearance=v["clearance_mm"],
        turns=turns,
        r_in_cl=r_in_cl,
        r_out_cl=r_out_cl,
        copper=v["copper_thickness_mm"],
        board=v["board_thickness_mm"],
        air_gap=v["air_gap_per_side_mm"],
        remanence=v["magnet_remanence_T"],
        mu_r=v["magnet_recoil_permeability"],
        magnet_mm=v["magnet_thickness_mm"],
        alpha=v["magnet_pole_arc_ratio"],
        mag_r_in=v["magnet_r_inner_mm"],
        mag_r_out=v["magnet_r_outer_mm"],
        back_iron=v["rotor_core_thickness_mm"],
        topology="open",
        name=f"D09 own build {variant}",
    )
    op = d["design"]["operating"]
    op.update(winding_temperature_degc=temperature, speed_rpm=v["speed_rpm"], line_current_rms_a=2.0)
    return d


def own_bz_peak(poles, remanence, mu_r, magnet_mm, g_plane, alpha, r_mm, z_mm) -> tuple[float, float]:
    """Own EQ-05 (cosh/sinh form, tests/independent/m2/own_emf.py), summed at the pole centre: (peak, b1)."""
    p = poles // 2
    terms = []
    for n in HARMONICS:
        u = n * p / r_mm
        k_n = 4 * remanence / (n * math.pi) * math.sin(n * math.pi * alpha / 2)
        terms.append(
            k_n
            * math.cosh(u * (g_plane - z_mm))
            / (math.cosh(u * g_plane) + mu_r / math.tanh(u * magnet_mm) * math.sinh(u * g_plane))
        )
    return sum(terms), terms[0]


def rel(x: float, ref: float) -> float:
    """Return x / ref - 1."""
    return x / ref - 1.0


def main() -> int:
    """Run OR-01, OR-06, OR-02 (A, B) and OR-08 and print one JSON row each."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    cases = json.loads(args.cases.read_text())["cases"]
    v08, v09 = case_values(cases, "O1-D08"), case_values(cases, "O2-D09")
    rows = []

    o = compute(d08(v08, 20.0))
    ke = o.analysis.ke_line_peak_v_s_per_rad
    e_edge = next((f.one_sided_addon for f in ke.validity if f.code == "EC-05"), 0.0)
    r1 = rel(ke.value, 0.031)
    rows.append(
        {
            "oracle": "OR-01",
            "quantity": "ke_line_peak_v_s_per_rad",
            "value": ke.value,
            "reference": 0.031,
            "rel": r1,
            "band": [-0.08, 0.08 + e_edge],
            "in_band": -0.08 <= r1 <= 0.08 + e_edge,
            "drc_violations": sum(b.violation_count for b in o.drc),
            "issues": len(o.issues),
            "D-045g": D045G["OR-01"],
        }
    )

    i_printed = physics.loss_budget_current_a(4.0, 3, 0.39)
    i_own = math.sqrt((4.0 / 3) / 0.39)
    lo, hi = math.sqrt((4.0 / 3) / 0.395), math.sqrt((4.0 / 3) / 0.385)
    o50 = compute(d08(v08, 50.0))
    r50 = o50.analysis.resistance_phase_operating_ohm.value
    rows.append(
        {
            "oracle": "OR-06",
            "quantity": "loss_budget_current_a(4.0, 3, 0.39)",
            "value": i_printed,
            "own_closed_form": i_own,
            "reference": 1.84,
            "rel": rel(i_printed, 1.84),
            "print_rounding_interval": [lo, hi],
            "in_band": lo <= 1.84 <= hi and abs(i_printed - i_own) < 1e-12,
            "full_phase_r50_ohm": r50,
            "current_on_full_phase_r50": physics.loss_budget_current_a(4.0, 3, r50),
            "D-045g": D045G["OR-06"],
        }
    )

    for variant in ("A", "B"):
        o9 = compute(d09(v09, variant, 20.0))
        r20 = o9.analysis.resistance_phase_20c_ohm.value
        r2 = rel(r20, 1.07)
        rows.append(
            {
                "oracle": "OR-02",
                "variant": variant,
                "quantity": "resistance_phase_20c_ohm",
                "value": r20,
                "reference": 1.07,
                "rel": r2,
                "band": [-0.08, 0.08],
                "in_band": abs(r2) <= 0.08,
                "issues": len(o9.issues),
                "drc_violations": sum(b.violation_count for b in o9.drc),
                "D-045g": D045G["OR-02"],
            }
        )
        if variant == "A":
            rotor = o9.design.rotor
            g_plane = v09["air_gap_per_side_mm"] + v09["board_thickness_mm"] / 2
            r_mid = (v09["magnet_r_inner_mm"] + v09["magnet_r_outer_mm"]) / 2
            layer = o9.analysis.layers[0]
            z_product = v09["air_gap_per_side_mm"] + float(
                layer.z_mm.value
            )  # LayerResult.z_mm is from the board surface
            bz = [
                float(
                    physics.field_harmonic(
                        n,
                        np.array([r_mid]),
                        np.array([z_product]),
                        rotor,
                        g_plane,
                        np.array([v09["magnet_pole_arc_ratio"]]),
                    )[0][0]
                )
                for n in HARMONICS
            ]
            phi = np.linspace(0.0, math.pi, 3601)
            wave = sum(b * np.cos(n * phi) for b, n in zip(bz, HARMONICS, strict=True))
            peak_api = float(np.max(np.abs(wave)))
            z_own = v09["air_gap_per_side_mm"] + v09["copper_thickness_mm"] / 2
            peak_own, b1_own = own_bz_peak(
                16,
                v09["magnet_remanence_T"],
                v09["magnet_recoil_permeability"],
                v09["magnet_thickness_mm"],
                g_plane,
                v09["magnet_pole_arc_ratio"],
                r_mid,
                z_own,
            )
            rows.append(
                {
                    "oracle": "OR-08",
                    "quantity": "B_z peak at mid-radius, harmonics 1-13 (field_harmonic)",
                    "value": peak_api,
                    "reference_range": [0.72, 0.75],
                    "band": [0.7125, 0.7560],
                    "in_band": 0.7125 <= peak_api <= 0.7560,
                    "layer_z_mm_product": z_product,
                    "b1_product_layer": layer.b1_peak_mid_radius_t.value,
                    "b1_field_harmonic": bz[0],
                    "own_peak": peak_own,
                    "own_b1": b1_own,
                    "own_z_from_magnet_mm": z_own,
                    "D-045g": D045G["OR-08"],
                }
            )

    for row in rows:
        print(json.dumps(row))
    if args.out is not None:
        args.out.write_text(json.dumps(rows, indent=1))
    return 0 if all(r["in_band"] for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
