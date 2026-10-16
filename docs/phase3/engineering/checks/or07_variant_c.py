# Prepared by: Agent 2 (Motor Design Expert), model: claude-opus-5-5
"""OR-07 and OR-02 on the pre-registered O2-D09 variant C and its envelope through the public API (U-E13 step 2).

Run from the repository root:
    PYTHONPATH=src /home/claude/embodic/.venv/bin/python docs/phase3/engineering/checks/or07_variant_c.py

The builds come from oracle_cases.json O2-D09 version 4 `variant_C` (committed 53253b1 before any run). Every other
input is variant A's (oracles_probe.d09_design, imported read-only). Bands and the pass rule are the registered ones.
"""

import dataclasses
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


probe = _load("oracles_probe", "docs/phase2/engineering/checks/oracles_probe.py")
f07 =_load("f_or07_probe", "docs/phase3/engineering/checks/f_or07_probe.py")

from embodic.api import compute  # noqa: E402
from embodic.model.winding_specs import EndStyle, SideStyle  # noqa: E402

ORACLE = ROOT / "docs/phase2/engineering/oracle_cases.json"
EMF_REFS_V = (6.21, 6.20, 6.22)  # D09 Table 4 p.6 calc, Table 5 p.6 FEA, Table 7 p.8 measured
R_MEASURED_OHM = 1.07  # D09 Table 6 p.7
D09_PHASE_LENGTH_MM = 3244.0  # D09 Table 1 p.3


def variant_c() -> dict:
    case = next(c for c in json.loads(ORACLE.read_text())["cases"] if c["case_id"] == "O2-D09")
    assert case["version"] == 4, case["version"]
    return case["variant_C"]


def design_of(build: dict, settings: dict, winding_degc: float):
    base = probe.d09_design("A", winding_degc)
    coil = base.winding.coil
    for name in ("coil_count", "trace_width_mm", "clearance_mm"):
        assert getattr(coil, name) == settings[name], (name, getattr(coil, name), settings[name])
    coil = dataclasses.replace(
        coil,
        r_inner_mm=build["r_inner_mm"],
        r_outer_mm=build["r_outer_mm"],
        coil_gap_mm=build["coil_gap_mm"],
        turns=settings["turns"],
        side_style=SideStyle(settings["side_style"]),
        end_style=EndStyle(build["end_style"]),
        corner_radius_mm=settings["corner_radius_mm"],
    )
    return dataclasses.replace(base, winding=dataclasses.replace(base.winding, coil=coil))


def evaluate(label: str, build: dict, settings: dict) -> dict:
    outcome = compute(design_of(build, settings, 20.0), {})
    issues = sorted(f"{i.severity.name}:{i.code}" for i in outcome.issues) if outcome else ["no outcome"]
    if outcome is None or outcome.analysis is None or outcome.boards is None:
        print(f"{label}: not buildable | issues {issues}")
        return {"label": label, "buildable": False}
    layout = outcome.boards.boards[0]
    turns = layout.detail.turns_achieved
    drc_pass = bool(outcome.drc) and all(r.passed for r in outcome.drc)
    a = outcome.analysis
    emf, e_edge = a.emf_phase_rms_v.value, a.edge_leakage_fraction.value
    devs = {ref: emf / ref - 1 for ref in EMF_REFS_V}
    emf_in = all(-0.05 <= d <= 0.05 + e_edge for d in devs.values())
    r20 = a.resistance_phase_20c_ohm.value
    r_dev = r20 / R_MEASURED_OHM - 1
    pre_ok = turns == settings["turns"] and drc_pass and not outcome.issues
    g, tab = f07.tables(outcome)
    ke_mine, _ = f07.ke_phase_a(outcome, lambda z: tab[z])
    coil_mm, chain_mm = probe.phase_a_lengths_mm(outcome)
    print(
        f"{label}: turns_achieved {turns} | DRC {'pass' if drc_pass else 'FAIL'} | issues {issues} | "
        f"preconditions {'met' if pre_ok else 'NOT met'}"
    )
    print(
        f"  OR-07 emf_phase_rms_v {emf:.5f} V | e_edge {e_edge:.4f} | band [-5.00%, {0.05 + e_edge:+.2%}] | "
        + ", ".join(f"{d:+.2%} vs {ref} V" for ref, d in devs.items())
        + f" | {'IN band' if emf_in and pre_ok else 'OUT of band' if pre_ok else 'no verdict'}"
    )
    print(
        f"  OR-02 resistance_phase_20c_ohm {r20:.5f} ohm | {r_dev:+.2%} vs 1.07 ohm | band [-8.00%, +8.00%] | "
        f"{'IN band' if abs(r_dev) <= 0.08 and pre_ok else 'OUT of band' if pre_ok else 'no verdict'}"
    )
    print(
        f"  instrument: recomputed |sum lambda| {ke_mine:.9f} vs ke_phase {a.ke_phase_v_s_per_rad.value:.9f} "
        f"(rel {ke_mine / a.ke_phase_v_s_per_rad.value - 1:.1e})"
    )
    print(
        f"  phase A copper (information): coil paths {coil_mm:.1f} mm + chain {chain_mm:.1f} mm = "
        f"{coil_mm + chain_mm:.1f} mm ({(coil_mm + chain_mm) / D09_PHASE_LENGTH_MM - 1:+.1%} vs 3244 mm); "
        f"coil paths alone {coil_mm / D09_PHASE_LENGTH_MM - 1:+.1%}"
    )
    return {"label": label, "buildable": True, "emf": emf, "r20": r20}


def main() -> None:
    print(f"oracle_cases.json sha256 {hashlib.sha256(ORACLE.read_bytes()).hexdigest()}")
    vc = variant_c()
    settings = vc["generator_settings"]["SpiralCoilSpec"]
    builds = vc["builds"]
    nominal = {k: settings[k] for k in ("r_inner_mm", "r_outer_mm", "coil_gap_mm", "end_style")}
    assert all(builds["C"][k] == v for k, v in nominal.items()), "build C differs from the registered settings"
    for label in ("C", "C-pitch", "C-hole", "C-straight"):
        b = builds[label]
        print(
            f"[{label}] {b['role']} | r {b['r_inner_mm']:.4f}-{b['r_outer_mm']:.4f} mm | gap {b['coil_gap_mm']:.4f} mm"
            f" | end {b['end_style']}"
        )
        evaluate(label, b, settings)
    out40 = probe.run(design_of(builds["C"], settings, 40.0))
    r40 = out40.analysis.resistance_phase_operating_ohm.value
    print(f"C at 40 degC (sensitivity): resistance_phase_operating_ohm {r40:.5f} ohm ({r40 / R_MEASURED_OHM - 1:+.2%})")


if __name__ == "__main__":
    main()
