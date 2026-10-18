"""Fix wave F4 (U-E20, Agent 2): the result chains of analyse() against the rulings of fix_wave_f4.md.

Run from the repository root (read-only; it writes nothing):

    PYTHONPATH=src python docs/phase3/engineering/checks/f4_chain_audit.py

Part 1 computes the D08 example and compares the eq_ids of every result with EXPECTED_D08 (fix_wave_f4.md section B).
Part 2 compares the rows of the other examples that the rulings name (block magnets, delta, drive).
Part 3 (question 4) sets the EC-05 threshold to 0 so that e_edge caps, marks every linked test passed, and lists the
D08 results that hold EQ-05 in their chain but do not carry the EC-05 flag.
Part 4 (questions 4 and 6) prints the label of every D08 result and the delta circulating loss value.
Part 5 (questions 1, 3, 7 and 8) checks the kernel facts the rulings rest on.
"""

import dataclasses
import math
from collections.abc import Iterator
from pathlib import Path

import numpy as np

from embodic.api import compute
from embodic.io.project import load_project, project_provenance
from embodic.model.operating import Modulation
from embodic.model.vocabulary import ConnectionTopology
from embodic.physics.drive import no_load_speed_rpm, torque_speed_envelope
from embodic.physics.emf import pole_arc_ratio_eq_ids, pole_arc_ratio_mm
from embodic.physics.interconnect import InterconnectResistance, interconnect_loss_w
from embodic.results import AnalysisResult, Registry, load_registry
from embodic.results.traceable import Traceable

REPO = Path(__file__).resolve().parents[4]
EXAMPLES = REPO / "resources" / "examples"

PHASE_EMF = ("07", "06", "05")
PHASE_R = ("10", "11", "07")
EXPECTED_D08: dict[str, tuple[str, ...]] = {
    "ke_phase_v_s_per_rad": ("06", "07", "05"),
    "ke_line_v_s_per_rad": ("09", "06", "07", "05"),
    "ke_line_peak_v_s_per_rad": ("18", *PHASE_EMF),
    "kt_n_m_per_a": ("09", "06", "07", "05"),
    "kv_rpm_per_v": ("09", "06", "07", "05"),
    "winding_factor_1": ("27", "06", "07", "05"),
    "resistance_phase_20c_ohm": PHASE_R,
    "resistance_phase_operating_ohm": PHASE_R,
    "resistance_line_ohm": ("23", "10", "11", "07"),
    "emf_phase_rms_v": ("06", "07", "05"),
    "torque_n_m": ("09", "06", "07", "05"),
    "loss_copper_w": ("10", "11", "07", "09"),
    "loss_eddy_w": ("12", "05", "10"),
    "loss_circulating_w": ("07", "06", "05", "10", "11"),
    "loss_delta_circulating_w": ("19",),
    "loss_interconnect_w": ("23", "10", "09"),
    "loss_total_w": ("26", "10", "11", "07", "09", "12", "05", "06", "19", "23"),
    "output_power_w": ("26", "09", "06", "07", "05"),
    "efficiency": ("26", "09", "06", "07", "05", "10", "11", "12", "19", "23"),
    "motor_constant_n_m_per_sqrt_w": ("26", "09", "06", "07", "05", "10", "11"),
    "thd_phase": ("18", *PHASE_EMF),
    "thd_line": ("18", *PHASE_EMF),
    "current_density_a_per_mm2": ("22", "09"),
    "skin_depth_mm": ("13", "10"),
    "inductance_estimate_h": ("14", "27", "06", "07", "05"),
    "ipc_guideline_current_a": ("15", "09"),
    "mass_copper_g": ("16",),
    "mass_laminate_g": ("16",),
    "temperature_rise_k": ("17", "26", "10", "11", "07", "09", "12", "05", "06", "19", "23"),
    "edge_leakage_fraction": ("05",),
    **{f"layers[{k}].z_mm": () for k in range(2)},
    **{f"layers[{k}].b1_peak_mid_radius_t": ("05",) for k in range(2)},
    **{f"phases[{k}].ke_peak_v_s_per_rad": ("06", "07", "05") for k in range(3)},
    **{f"phases[{k}].emf_phasor_angle_rad": ("06", "07", "05") for k in range(3)},
    **{f"phases[{k}].resistance_20c_ohm": PHASE_R for k in range(3)},
    **{f"phases[{k}].resistance_operating_ohm": PHASE_R for k in range(3)},
    **{f"phases[{k}].circulating_loss_w": ("07", "06", "05", "10", "11") for k in range(3)},
    "emf_waveform_v": ("18", *PHASE_EMF),
}
DRIVE_FULL = ("20", "14", "27", "06", "07", "05", "09", "23", "10", "11")
BLOCK_STAR = {
    "ke_line_peak_v_s_per_rad": ("18", "07", "06", "05", "04"),
    "edge_leakage_fraction": ("05", "04"),
    "loss_delta_circulating_w": ("19",),
    "loss_interconnect_w": ("23", "10", "09"),
}
ARC_STAR_DRIVE = {
    "ke_line_peak_v_s_per_rad": ("18", *PHASE_EMF),
    "edge_leakage_fraction": ("05",),
    "loss_delta_circulating_w": ("19",),
    "loss_interconnect_w": ("23", "10", "09"),
    "torque_speed.speed_rpm": ("20", "09", "06", "07", "05"),
    "torque_speed.torque_n_m": DRIVE_FULL,
    "torque_speed.power_w": DRIVE_FULL,
    "torque_speed.no_load_speed_rpm": ("20", "09", "06", "07", "05"),
    "torque_speed.base_speed_rpm": DRIVE_FULL,
}
EXPECTED_OTHER: dict[str, dict[str, tuple[str, ...]]] = {
    "spiral_12c16p_default": BLOCK_STAR,
    "spiral_12c14p": BLOCK_STAR,
    "serpentine_16p_example": ARC_STAR_DRIVE,
    "wave_16p_example": ARC_STAR_DRIVE,
}


def walk(value: object, path: str = "") -> Iterator[tuple[str, Traceable[object]]]:
    """Yield (path, Traceable) for every result, with the path spelling of U-M8h_chains.md."""
    if isinstance(value, Traceable):
        yield path, value
    elif isinstance(value, tuple):
        for i, item in enumerate(value):
            yield from walk(item, f"{path}[{i}]")
    elif dataclasses.is_dataclass(value) and not isinstance(value, type):
        for f in dataclasses.fields(value):
            yield from walk(getattr(value, f.name), f"{path}.{f.name}" if path else f.name)


def analysis(example: str, registry: Registry) -> AnalysisResult:
    """Compute one shipped example through api.compute, as the app does."""
    project, issues = load_project(EXAMPLES / f"{example}.embodic.json")
    assert project is not None, issues
    outcome = compute(project.design, project_provenance(project), registry=registry)
    assert outcome is not None and outcome.analysis is not None, outcome
    return outcome.analysis


def short(eq_ids: tuple[str, ...]) -> tuple[str, ...]:
    """Drop the EQ- prefix, as the tables of U-M8h_chains.md do."""
    return tuple(e.removeprefix("EQ-") for e in eq_ids)


def compare(name: str, results: dict[str, Traceable[object]], expected: dict[str, tuple[str, ...]]) -> int:
    """Print every row whose chain differs from the ruling and return how many differ."""
    differ = 0
    for path, want in expected.items():
        got = short(results[path].eq_ids)
        if got != want:
            differ += 1
            print(f"  DIFF {name} {path}: code {', '.join(got)} | ruling {', '.join(want)}")
    print(f"  {name}: {len(expected)} rows compared, {differ} differ from the ruling")
    return differ


def part1(registry: Registry) -> None:
    """Compare every D08 result with EXPECTED_D08."""
    print("Part 1. D08 chains, code vs ruling")
    results = dict(walk(analysis("spiral_12c10p_d08", registry)))
    missing = set(results) ^ set(EXPECTED_D08)
    print(f"  results computed {len(results)}, rows in EXPECTED_D08 {len(EXPECTED_D08)}, unmatched paths {missing}")
    compare("spiral_12c10p_d08", results, EXPECTED_D08)


def part2(registry: Registry) -> None:
    """Compare the rows of EXPECTED_OTHER."""
    print("Part 2. Rows of other examples named by the rulings")
    for example, expected in EXPECTED_OTHER.items():
        compare(example, dict(walk(analysis(example, registry))), expected)


def all_passed(registry: Registry) -> Registry:
    """Return the registry with every linked test passed (badge (ii) of U-M8h_chains.md)."""
    linked = frozenset(t for e in registry.equations.values() for t in e.tests)
    return dataclasses.replace(registry, passed_tests=linked)


def part3(registry: Registry) -> None:
    """List the D08 results that hold EQ-05 in their chain, with or without the EC-05 flag, under a capping EC-05."""
    eq05 = registry.equation("EQ-05")
    capping = dataclasses.replace(eq05.validity_checks[0], threshold=0.0)
    variant = all_passed(
        dataclasses.replace(
            registry, equations={**registry.equations, "EQ-05": dataclasses.replace(eq05, validity_checks=(capping,))}
        )
    )
    results = dict(walk(analysis("spiral_12c10p_d08", variant)))
    print("Part 3. D08, EC-05 threshold 0 (e_edge caps), every linked test passed")
    print(f"  e_edge = {results['edge_leakage_fraction'].value:.6f}")
    for path, t in results.items():
        if "EQ-05" not in t.eq_ids:
            continue
        codes = [f.code for f in t.validity]
        mark = "flag" if "EC-05" in codes else "NO FLAG"
        print(f"  {mark:7s} {path:38s} badge {t.status!s:11s} chain {', '.join(short(t.eq_ids))}")


def part4(registry: Registry) -> None:
    """Print the label of every labelled D08 result and the star delta-circulating loss."""
    results = dict(walk(analysis("spiral_12c10p_d08", registry)))
    print("Part 4. D08 (star) labels and the delta circulating loss")
    for path, t in results.items():
        if t.label is not None:
            print(f"  label {t.label!r:26s} {path} (chain {', '.join(short(t.eq_ids))})")
    loss_delta = results["loss_delta_circulating_w"]
    print(f"  loss_delta_circulating_w value {loss_delta.value!r}, validity {[f.code for f in loss_delta.validity]}")


def part5(registry: Registry) -> None:
    """Check the kernel facts behind the rulings on questions 1, 3, 7 and 8."""
    print("Part 5. Kernel facts")
    d08 = dict(walk(analysis("spiral_12c10p_d08", registry)))
    ke_ph = d08["ke_phase_v_s_per_rad"].value
    ke_ll = d08["ke_line_v_s_per_rad"].value
    ke_pk = d08["ke_line_peak_v_s_per_rad"].value
    print(f"  Q3 D08 star: ke_line / ke_phase = {ke_ll / ke_ph:.12f} (sqrt 3 = {math.sqrt(3.0):.12f})")
    print(f"  Q3 D08 star: ke_line_peak / ke_line = {ke_pk / ke_ll:.9f} (1 only for a fundamental-only waveform)")
    sums = InterconnectResistance(line_stub_ohm=(0.01, 0.02, 0.03), link_ohm=(0.004, 0.005, 0.006), neutral_ring_ohm=())
    i_line = 2.0  # example value
    delta = interconnect_loss_w(sums, ConnectionTopology.DELTA, i_line)
    by_hand = i_line**2 * 0.06 + (i_line / math.sqrt(3.0)) ** 2 * 0.015
    print(
        f"  Q1 interconnect_loss_w delta (example sums): {delta:.15g}, I_line^2 sum s + (I_line/sqrt3)^2 sum l = "
        f"{by_hand:.15g}"
    )
    args = dict(dc_link_v=24.0, modulation=Modulation.SVPWM, current_limit_a=5.0, poles=16, points=121)  # examples
    s1, t1 = torque_speed_envelope(0.5, 1e-4, 0.02, **args, phases=3, connection=ConnectionTopology.STAR)
    s2, t2 = torque_speed_envelope(2.0, 5e-3, 0.02, **args, phases=3, connection=ConnectionTopology.STAR)
    n0 = no_load_speed_rpm(0.02, 24.0, Modulation.SVPWM, ConnectionTopology.STAR)
    print(
        f"  Q7 speed axis equal for R 0.5/2.0 ohm and L 1e-4/5e-3 H: {np.array_equal(s1, s2)}; torque equal: "
        f"{np.array_equal(t1, t2)}; axis == linspace(0, 1.15 n0): {np.allclose(s1, np.linspace(0, 1.15 * n0, 121))}"
    )
    for example in ("spiral_12c10p_d08", "spiral_12c16p_default"):
        project, _ = load_project(EXAMPLES / f"{example}.embodic.json")
        assert project is not None
        rotor = project.design.rotor
        alpha = pole_arc_ratio_mm(rotor, np.array([20.0, 30.0, 40.0]))
        print(
            f"  Q8 {example} magnet {type(rotor.magnet).__name__}: alpha_p at r 20/30/40 mm {np.round(alpha, 6)}, "
            f"EQ-IDs evaluated {pole_arc_ratio_eq_ids(rotor)}"
        )
    pointers = {p.pointer for p in d08["ke_phase_v_s_per_rad"].inputs}
    ipc = {p.pointer for p in d08["ipc_guideline_current_a"].inputs}
    print(
        f"  inputs: /rotor/magnet/pole_arc_ratio in ke_phase inputs: {'/rotor/magnet/pole_arc_ratio' in pointers}; "
        f"/operating/ambient_temperature_degc in ipc inputs: {'/operating/ambient_temperature_degc' in ipc}"
    )


def main() -> None:
    """Run the five parts on the shipped registry."""
    registry = load_registry()
    print(
        f"registry {registry.version}; EQ-19 label {registry.equation('EQ-19').label!r}; passed tests "
        f"{len(registry.passed_tests)}"
    )
    part1(registry)
    part2(registry)
    part3(registry)
    part4(registry)
    part5(registry)


if __name__ == "__main__":
    main()
