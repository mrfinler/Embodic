# Prepared by: Agent 2 (Motor Design Expert), model: claude-opus-5-5
"""Build the OR-02, OR-05...OR-09 oracle designs and run each through embodic.api.compute (U-E9).

Run from the repository root:
    PYTHONPATH=src .venv/bin/python docs/phase2/engineering/checks/oracles_probe.py

Every input comes from docs/phase2/engineering/oracle_cases.json (the 'assumed' value where an input is unresolved) or
is a named assumption in ASSUMPTIONS below. Bands are the ones of oracle_tests_spec.md; nothing here is tuned.
OR-03 and OR-10 (O3-D10) are not built: the case is not runnable (oracle_tests_spec.md).
"""

import dataclasses
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from tests.unit.generators.d08_example import D08_OUTLINE  # noqa: E402
from tests.unit.model.designs import spiral_design  # noqa: E402
from tests.unit.physics.test_oracles import _d08_design  # noqa: E402

from embodic.api import compute  # noqa: E402
from embodic.geometry.primitives import primitive_length_mm  # noqa: E402
from embodic.model.design import DesignParameters  # noqa: E402
from embodic.model.rotor import ArcMagnet, RotorType  # noqa: E402
from embodic.model.stackup import generate_even_stackup  # noqa: E402
from embodic.model.vocabulary import ConnectionTopology  # noqa: E402
from embodic.model.winding_specs import SideStyle, SpiralWindingSpec  # noqa: E402
from embodic.physics import field_harmonic, loss_budget_current_a, symmetry_plane_mm  # noqa: E402

CASES = {c["case_id"]: c for c in json.loads((ROOT / "docs/phase2/engineering/oracle_cases.json").read_text())["cases"]}
ASSUMPTIONS = {
    "d09_side_style": "parallel",  # D09 gives no side construction; D08's (Fig. 3.4 p.33) is reused
    "d09_coil_gap_mm": 0.2,  # equal to D09's clearance s, as the D08 build does
    "d09_ambient_degc": 20.0,  # D09 states no ambient; enters only temperature_rise_k
    "d08_track_degc": 50.0,  # D08 Table 4.5 PDF p.54: track temperature of the 0.39 ohm calculation
    "d08_copper_loss_budget_w": 4.0,  # D08 PDF p.53 eq. 4.3 (EV-09)
}


@dataclass(frozen=True)
class Check:
    """One compared quantity: embodic value, reference and band as relative bounds (None = no pass/fail)."""

    oracle: str
    build: str
    field: str
    value: float
    reference: float
    band: tuple[float, float] | None

    @property
    def deviation(self) -> float:
        """Relative difference embodic / reference - 1."""
        return self.value / self.reference - 1.0

    @property
    def verdict(self) -> str:
        """In or out of band, or characterisation when the oracle has no band."""
        if self.band is None:
            return "characterisation"
        lo, hi = self.band
        return "IN band" if lo <= self.deviation <= hi else "OUT of band"


def inputs(case_id: str, variant: str = "A") -> dict[str, Any]:
    """Input values of one case; unresolved inputs take 'assumed' (variant A) or 'alternative_B' (variant B)."""
    out = {}
    for name, e in CASES[case_id]["inputs"].items():
        if e["value"] is not None:
            out[name] = e["value"]
        elif variant == "B" and "alternative_B" in e:
            out[name] = e["alternative_B"]
        else:
            out[name] = e.get("assumed")
    return out


def d09_design(variant: str, winding_degc: float) -> DesignParameters:
    """O2-D09 primary A (N 8, centre lines 25.2-47.6 mm) or alternative B (N 7, 20.2-43.8 mm), open phases."""
    v = inputs("O2-D09", variant)
    base = spiral_design()
    assert isinstance(base.winding, SpiralWindingSpec)
    half = v["trace_width_mm"] / 2
    coil = dataclasses.replace(
        base.winding.coil,
        coil_count=v["coil_count"],
        r_inner_mm=v["coil_centre_line_R_i0_mm"] - half,  # centre lines to copper edges, as the D08 build
        r_outer_mm=v["coil_centre_line_R_o0_mm"] + half,
        trace_width_mm=v["trace_width_mm"],
        clearance_mm=v["clearance_mm"],
        coil_gap_mm=ASSUMPTIONS["d09_coil_gap_mm"],
        turns=v["turns_per_coil_per_layer"],
        side_style=SideStyle(ASSUMPTIONS["d09_side_style"]),
    )
    rotor = dataclasses.replace(
        base.rotor,
        poles=v["poles"],
        rotor_type=RotorType(v["rotor_type"]),
        magnet=ArcMagnet(
            pole_arc_ratio=v["magnet_pole_arc_ratio"],
            r_inner_mm=v["magnet_r_inner_mm"],
            r_outer_mm=v["magnet_r_outer_mm"],
            thickness_mm=v["magnet_thickness_mm"],
        ),
        remanence_t=v["magnet_remanence_T"],
        recoil_permeability=v["magnet_recoil_permeability"],
        air_gap_mm=v["air_gap_per_side_mm"],
        back_iron_thickness_mm=v["rotor_core_thickness_mm"],
    )
    operating = dataclasses.replace(
        base.operating,
        speed_rpm=v["speed_rpm"],
        line_current_rms_a=2.0,  # D09 Table 7 p.8 full load
        winding_temperature_degc=winding_degc,
        ambient_temperature_degc=ASSUMPTIONS["d09_ambient_degc"],
    )
    rules = dataclasses.replace(
        base.drc_rules, trace_clearance_mm=v["clearance_mm"], via_clearance_mm=v["clearance_mm"]
    )
    return dataclasses.replace(
        base,
        name=f"Tokgoz D09 12/16 (O2-D09 {variant})",
        rotor=rotor,
        winding=dataclasses.replace(base.winding, coil=coil),
        stackup=generate_even_stackup(v["copper_layers"], v["copper_thickness_mm"], v["board_thickness_mm"]),
        connection=dataclasses.replace(base.connection, topology=ConnectionTopology.OPEN),
        outline=D08_OUTLINE,
        operating=operating,
        drc_rules=rules,
    )


def d08_design_at_track_temperature() -> DesignParameters:
    """OR-01's D08 design with the winding at D08's 50 degC track temperature."""
    base = _d08_design()
    op = dataclasses.replace(base.operating, winding_temperature_degc=ASSUMPTIONS["d08_track_degc"])
    return dataclasses.replace(base, operating=op)


def run(design: DesignParameters):
    """Compute through the public facade; any ERROR issue stops the probe."""
    outcome = compute(design, {})
    assert outcome is not None and outcome.analysis is not None, outcome and outcome.issues
    errors = [i.code for i in outcome.issues if i.severity.name == "ERROR"]
    assert not errors, errors
    return outcome


def describe(label: str, outcome) -> None:
    """Print what was built: turns achieved, copper envelope, DRC, issues and e_edge."""
    layout = outcome.boards.boards[0]
    turns = getattr(layout.detail, "turns_achieved", None)
    drc = "pass" if outcome.drc and all(r.passed for r in outcome.drc) else "FAIL"
    a = outcome.analysis
    print(
        f"{label}: turns_achieved {turns} | envelope {layout.envelope_mm[0]:.3f}-{layout.envelope_mm[1]:.3f} mm | "
        f"DRC {drc} | issues {sorted({i.code for i in outcome.issues})} | e_edge {a.edge_leakage_fraction.value:.4f}"
    )


def phase_a_lengths_mm(outcome) -> tuple[float, float]:
    """Copper length of phase A's members: coil paths (element set) and chain paths (bus arcs, legs)."""
    layout = outcome.boards.boards[0]
    paths = {p.id: p for p in layout.paths}
    coil = chain = 0.0
    phase = layout.circuit.phases[0]
    for group in phase.groups:
        for member in group.members:
            for pid in member.path_ids:
                p = paths[pid]
                length = math.fsum(primitive_length_mm(q) for q in p.primitives)
                if p.element is not None:
                    coil += length
                else:
                    chain += length
    return coil, chain


def bz_waveform_peak_t(outcome) -> float:
    """B_z at the pole centre, magnet mid-radius, first copper layer: sum of the odd harmonics 1 to 13 of EQ-05."""
    design, layout = outcome.design, outcome.boards.boards[0]
    rotor = design.rotor
    r_mid = np.array([sum(rotor.magnet.radial_span_mm()) / 2.0])
    z = np.array([min(layout.copper_z_mm.values()) + rotor.air_gap_mm])
    plane = symmetry_plane_mm(rotor, outcome.boards.stack_thickness_mm)
    alpha = np.array([rotor.magnet.pole_arc_ratio])
    return float(sum(field_harmonic(n, r_mid, z, rotor, plane, alpha)[0][0] for n in range(1, 14, 2)))


def expected(case_id: str, prefix: str) -> float:
    """Return the published value of the expected row whose quantity starts with prefix."""
    return next(e for e in CASES[case_id]["expected"] if e["quantity"].startswith(prefix))["value"]


def main() -> None:
    """Run every buildable oracle and print one row per compared quantity."""
    checks: list[Check] = []

    d08 = run(d08_design_at_track_temperature())
    describe("D08 (OR-05, OR-06)", d08)
    r_full_50 = d08.analysis.resistance_phase_operating_ohm.value
    print(
        f"  D08 resistance_phase_20c_ohm {d08.analysis.resistance_phase_20c_ohm.value:.6f}, at 50 degC {r_full_50:.6f}"
    )
    checks.append(Check("OR-05", "D08 full_phase", "resistance_phase_operating_ohm @50C", r_full_50, 0.39, None))
    budget = ASSUMPTIONS["d08_copper_loss_budget_w"]
    i_d08_r = loss_budget_current_a(budget, 3, expected("O1-D08", "phase resistance, loop-only"))
    i_embodic_r = loss_budget_current_a(budget, 3, r_full_50)
    checks.append(Check("OR-06", "EQ-21 on D08's 0.39 ohm", "loss_budget_current_a", i_d08_r, 1.84, None))
    checks.append(Check("OR-06", "EQ-21 on embodic R @50C", "loss_budget_current_a", i_embodic_r, 1.84, None))

    for variant in ("A", "B"):
        d09 = run(d09_design(variant, winding_degc=20.0))
        describe(f"D09 {variant} at 20 degC", d09)
        a = d09.analysis
        e_edge = a.edge_leakage_fraction.value
        checks.append(
            Check(
                "OR-02",
                f"D09 {variant}",
                "resistance_phase_20c_ohm",
                a.resistance_phase_20c_ohm.value,
                1.07,
                (-0.08, 0.08),
            )
        )
        d09_40 = run(d09_design(variant, winding_degc=40.0))
        checks.append(
            Check(
                "OR-02",
                f"D09 {variant} (sweep 40 C)",
                "resistance_phase_operating_ohm @40C",
                d09_40.analysis.resistance_phase_operating_ohm.value,
                1.07,
                (-0.08, 0.08),
            )
        )
        for ref, kind in ((6.21, "calc"), (6.20, "FEA"), (6.22, "meas")):
            checks.append(
                Check(
                    "OR-07",
                    f"D09 {variant} vs {kind}",
                    "emf_phase_rms_v",
                    a.emf_phase_rms_v.value,
                    ref,
                    (-0.05, 0.05 + e_edge),
                )
            )
        b1 = [layer.b1_peak_mid_radius_t.value for layer in a.layers]
        print(
            f"  D09 {variant} b1_peak_mid_radius_t per layer {[round(b, 6) for b in b1]}, "
            f"ke_phase {a.ke_phase_v_s_per_rad.value:.6f} V*s/rad, inductance {a.inductance_estimate_h.value:.4e} H"
        )
        coil_mm, chain_mm = phase_a_lengths_mm(d09)
        print(
            f"  D09 {variant} phase A copper: coil paths {coil_mm:.1f} mm (D09 Table 1: 3244 mm), "
            f"chain {chain_mm:.1f} mm;"
            f" B_z waveform peak (n 1-13) at mid-radius {bz_waveform_peak_t(d09):.4f} T"
        )
        for ref in (0.72, 0.75):
            checks.append(
                Check("OR-08", f"D09 {variant} vs {ref} T", "layers[0].b1_peak_mid_radius_t", b1[0], ref, (-0.05, 0.05))
            )
        checks.append(
            Check(
                "OR-09", f"D09 {variant}", "inductance_estimate_h [uH]", a.inductance_estimate_h.value * 1e6, 14.8, None
            )
        )

    print()
    print(f"{'oracle':6} | {'build':28} | {'field':38} | {'embodic':>10} | {'ref':>6} | {'diff':>8} | band | verdict")
    for c in checks:
        band = "none" if c.band is None else f"[{c.band[0]:+.1%}, {c.band[1]:+.1%}]"
        print(
            f"{c.oracle:6} | {c.build:28} | {c.field:38} | {c.value:10.5f} | {c.reference:6.3f} | "
            f"{c.deviation:+8.2%} | {band} | {c.verdict}"
        )
    i_lo, i_hi = (math.sqrt(budget / 3 / r) for r in (0.395, 0.385))
    print(f"\nOR-06 print rounding: R 0.39 read as [0.385, 0.395] ohm gives I in [{i_lo:.4f}, {i_hi:.4f}] A")


if __name__ == "__main__":
    main()
