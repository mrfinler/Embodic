"""OR-02, OR-03 and OR-05 to OR-10 (test_plan.md section 4), built as docs/phase2/engineering/oracle_tests_spec.md says.

Every design goes through the public facade `embodic.api.compute`. Inputs come from oracle_cases.json; an unresolved
input takes its pre-registered 'assumed' value (variant A) or 'alternative_B' (variant B). The D08 design is OR-01's
(`test_oracles._d08_design`). Bands are the spec's; none is widened and no input was changed after a result was seen.
OR-07 and OR-08 use D09, the EC-05 calibration source, so they are not independent of EC-05 (test_plan.md section 4).
"""

import dataclasses
import json
import math
from functools import cache
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from tests.unit.generators.d08_example import D08_OUTLINE
from tests.unit.model.designs import spiral_design
from tests.unit.physics.test_oracles import _d08_design

from embodic.api import compute
from embodic.model.design import DesignParameters
from embodic.model.rotor import ArcMagnet, RotorType
from embodic.model.stackup import generate_even_stackup
from embodic.model.vocabulary import ConnectionTopology
from embodic.model.winding_specs import SideStyle, SpiralWindingSpec
from embodic.outcome import ComputeOutcome
from embodic.physics import copper_resistivity_ohm_m, field_harmonic, loss_budget_current_a, symmetry_plane_mm
from embodic.results import AnalysisResult, load_registry

pytestmark = pytest.mark.req("REQ-F-11")

ORACLE = Path(__file__).resolve().parents[3] / "docs" / "phase2" / "engineering" / "oracle_cases.json"
# oracle_tests_spec.md "Shared D09 build": named assumptions, as the U-E9 probe states them.
D09_SIDE_STYLE = SideStyle.PARALLEL  # D09 gives no side construction; D08's (Fig. 3.4 p.33) is reused
D09_COIL_GAP_MM = 0.2  # equal to D09's clearance s, as the D08 build does
D09_AMBIENT_DEGC = 20.0  # D09 states no ambient; enters only temperature_rise_k
D09_FULL_LOAD_A = 2.0  # D09 Table 7 p.8, line RMS
D08_TRACK_DEGC = 50.0  # D08 Table 4.5 PDF p.54: track temperature of the 0.39 ohm calculation
D08_COPPER_LOSS_BUDGET_W = 4.0  # D08 eq. 4.3 PDF p.53 (EV-09)
NOT_REPRESENTABLE = "not representable in Phase 2: unequal-width concentric geometry and unprinted inputs (G40)"


def _case(case_id: str) -> dict[str, Any]:
    return next(c for c in json.loads(ORACLE.read_text())["cases"] if c["case_id"] == case_id)


def _inputs(case_id: str, variant: str) -> dict[str, Any]:
    out = {}
    for name, entry in _case(case_id)["inputs"].items():
        if entry["value"] is not None:
            out[name] = entry["value"]
        elif variant == "B" and "alternative_B" in entry:
            out[name] = entry["alternative_B"]
        else:
            out[name] = entry.get("assumed")
    return out


def _d09_design(variant: str) -> DesignParameters:
    """O2-D09 at 20 degC: A is N 8 on centre lines 25.2-47.6 mm, B is N 7 on 20.2-43.8 mm; open phases."""
    v = _inputs("O2-D09", variant)
    base = spiral_design()
    assert isinstance(base.winding, SpiralWindingSpec)
    half_width = v["trace_width_mm"] / 2
    coil = dataclasses.replace(
        base.winding.coil,
        coil_count=v["coil_count"],
        # centre lines to copper edges, the convention of the D08 build (spiral_generator_spec.md worked example 2)
        r_inner_mm=v["coil_centre_line_R_i0_mm"] - half_width,
        r_outer_mm=v["coil_centre_line_R_o0_mm"] + half_width,
        trace_width_mm=v["trace_width_mm"],
        clearance_mm=v["clearance_mm"],
        coil_gap_mm=D09_COIL_GAP_MM,
        turns=v["turns_per_coil_per_layer"],
        side_style=D09_SIDE_STYLE,
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
        line_current_rms_a=D09_FULL_LOAD_A,
        winding_temperature_degc=v["measurement_temperature_degC"],
        ambient_temperature_degc=D09_AMBIENT_DEGC,
    )
    clearance = v["clearance_mm"]
    rules = dataclasses.replace(base.drc_rules, trace_clearance_mm=clearance, via_clearance_mm=clearance)
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


def _d08_design_at_track_temperature() -> DesignParameters:
    base = _d08_design()
    return dataclasses.replace(
        base, operating=dataclasses.replace(base.operating, winding_temperature_degc=D08_TRACK_DEGC)
    )


def _outcome(design: DesignParameters) -> ComputeOutcome:
    """compute() with its stages; a design that fails to build or analyse fails the test, never an xfail."""
    outcome = compute(design, {})
    errors = sorted(i.code for i in outcome.issues if i.severity.name == "ERROR")
    if errors or outcome.analysis is None or outcome.boards is None:
        pytest.fail(f"{design.name} must build and analyse: {errors}")
    return outcome


@cache
def _d09(variant: str) -> ComputeOutcome:
    return _outcome(_d09_design(variant))


@cache
def _d08_at_50c() -> AnalysisResult:
    analysis = _outcome(_d08_design_at_track_temperature()).analysis
    assert analysis is not None
    return analysis


def _analysis(outcome: ComputeOutcome) -> AnalysisResult:
    assert outcome.analysis is not None
    return outcome.analysis


@pytest.mark.eqt("EQT-10-O2")
@pytest.mark.parametrize("variant", ["A", "B"])
def test_or02_d09_phase_resistance_within_8_percent_of_the_measured_value(variant: str) -> None:
    """OR-02: phase DC resistance at 20 degC against D09's measured 1.07 ohm (Table 6 p.7) in +-8 % (EQ-10).

    Defect caught: a resistance chain (EQ-10, EQ-11) or a D09 layout that misses the measured value. Both pre-registered
    turn variants are compared; U-E9's probe gave A 1.11558 ohm (+4.26 %) and B 1.01158 ohm (-5.46 %), so the pass does
    not confirm the turn count (spec F3). D09 states no measurement temperature (DEF-11); the 40 degC run is a
    sensitivity run in the spec, not a second chance, and is not repeated here.
    """
    measured = next(e for e in _case("O2-D09")["expected"] if e["quantity"] == "phase resistance")["value"]
    model = _analysis(_d09(variant)).resistance_phase_20c_ohm.value
    deviation = model / measured - 1.0
    print(f"OR-02 D09 {variant}: R_20 {model:.5f} ohm, {deviation:+.2%} against {measured} ohm")
    assert -0.08 <= deviation <= 0.08, f"R_20 {model:.5f} ohm is {deviation:+.2%} against {measured} ohm"


def _d08_loop_only_length_mm() -> float:
    """One D08 coil-layer as D08's concentric loop model (eq. 3.28-3.36, PDF p.44-45), span 2 pi / Q (EQ-03)."""
    v = _inputs("O1-D08", "A")
    w_d = v["trace_width_mm"] + v["clearance_mm"]
    span = 2.0 * math.pi / v["coil_count"]
    total = 0.0
    for i in range(v["turns_per_coil_per_layer"]):
        d = i * w_d + w_d / 2.0
        r_out, r_in = v["coil_r_outer_mm"] - i * w_d, v["coil_r_inner_mm"] + i * w_d
        phi_out, phi_in = math.asin(d / r_out), math.asin(d / r_in)
        beta_out, beta_in = span / 2.0 - phi_out, span / 2.0 - phi_in
        if beta_in > 0.0:
            arcs = 2.0 * r_out * beta_out + 2.0 * r_in * beta_in
            side = d / math.tan(phi_out) - d / math.tan(phi_in)
        else:  # triangular loop: the sides meet before the inner radius
            arcs = 2.0 * r_out * beta_out
            side = d / math.tan(phi_out) - d / math.tan(span / 2.0)
        total += arcs + 2.0 * side
    return total


def test_or05_d08_loop_only_resistance_within_3_percent_of_the_thesis_value() -> None:
    """OR-05 (information): D08's loop-only phase resistance at 50 degC against D08's calculated 0.39 ohm in +-3 %.

    Basis `loop_only` of O1-D08 version 4: 8 coil-layers of D08's concentric loops (EQ-03), EQ-10 at D08's 50 degC
    track temperature with the registry's rho_20 and alpha. U-E9 printed 0.381201 ohm (-2.26 %); the residual is
    `unresolved` (D08 gives neither rho_20 nor alpha_c, and 0.39 is printed to two digits).
    Basis `full_phase` (recorded, no band): `resistance_phase_operating_ohm` of OR-01's D08 design at 50 degC. U-E9
    printed 0.485162 ohm (+24.40 %); terminal stubs, the series chain and via barrels make the difference (EQ-10 note).
    Defect caught: an EQ-10 temperature term or resistivity constant that moves D08's own loop model off 0.39 ohm.
    """
    v = _inputs("O1-D08", "A")
    reference = next(e for e in _case("O1-D08")["expected"] if e["quantity"].startswith("phase resistance, loop-only"))
    registry = load_registry()
    rho = copper_resistivity_ohm_m(
        D08_TRACK_DEGC,
        registry.constant("copper_resistivity_20c_ohm_m").value,
        registry.constant("copper_temp_coeff_per_k").value,
    )
    coil_layers = v["coil_count"] // 3 * v["copper_layers"]
    section_m2 = v["trace_width_mm"] * 1e-3 * v["copper_thickness_mm"] * 1e-3
    loop_only = rho * coil_layers * _d08_loop_only_length_mm() * 1e-3 / section_m2
    full_phase = _d08_at_50c().resistance_phase_operating_ohm.value
    deviation = loop_only / reference["value"] - 1.0
    print(
        f"OR-05 D08 at {D08_TRACK_DEGC} degC: loop_only {loop_only:.6f} ohm ({deviation:+.2%}); full_phase "
        f"{full_phase:.6f} ohm ({full_phase / reference['value'] - 1.0:+.2%}, no band) against {reference['value']} ohm"
    )
    assert -0.03 <= deviation <= 0.03, f"loop_only {loop_only:.6f} ohm is {deviation:+.2%} against 0.39 ohm"


def test_or06_d08_budget_current_agrees_with_the_printed_value_through_print_rounding() -> None:
    """OR-06: EQ-21 on D08's 4 W budget and printed 0.39 ohm against D08's calculated 1.84 A (Table 4.6 PDF p.57).

    The band is print rounding only (spec section OR-06): 0.39 ohm read as [0.385, 0.395] ohm gives
    [1.8373, 1.8610] A, and 1.84 A must lie inside. EQ-21 on 0.39 ohm gives 1.84900 A (+0.49 %). Recorded, no band:
    EQ-21 on embodic's full-phase R at 50 degC, 1.65778 A in U-E9 (-9.90 %), the OR-05 basis difference again.
    Defect caught: an EQ-21 kernel without the square root or the division by the phase count.
    """
    printed_r = next(e for e in _case("O1-D08")["expected"] if e["quantity"].startswith("phase resistance, loop-only"))
    low = loss_budget_current_a(D08_COPPER_LOSS_BUDGET_W, 3, printed_r["value"] + 0.005)
    high = loss_budget_current_a(D08_COPPER_LOSS_BUDGET_W, 3, printed_r["value"] - 0.005)
    on_printed = loss_budget_current_a(D08_COPPER_LOSS_BUDGET_W, 3, printed_r["value"])
    on_embodic = loss_budget_current_a(D08_COPPER_LOSS_BUDGET_W, 3, _d08_at_50c().resistance_phase_operating_ohm.value)
    print(
        f"OR-06 D08: I on 0.39 ohm {on_printed:.5f} A, print-rounding interval [{low:.4f}, {high:.4f}] A; "
        f"I on embodic full_phase R {on_embodic:.5f} A (no band)"
    )
    assert (round(low, 4), round(on_printed, 5), round(high, 4)) == (1.8373, 1.84900, 1.8610)
    assert low <= 1.84 <= high


@pytest.mark.eqt("EQT-05-O2", "EQT-06-O2")
@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="F-OR07: D09 phase EMF out of [-5 %, +5 % + e_edge] for both pre-registered builds (U-E9: A +18.7 %, "
    "B -7.4 %); cause unresolved: G2 turn geometry and edge leakage (oracle_tests_spec.md section OR-07)",
)
@pytest.mark.parametrize("variant", ["A", "B"])
def test_or07_d09_phase_emf_within_the_registry_band(variant: str) -> None:
    """OR-07: emf_phase_rms_v at 2000 rpm against D09's 6.21 V calc., 6.20 V FEA and 6.22 V measured (RMS, inferred).

    Band [-5 %, +5 % + e_edge] with e_edge the computed edge_leakage_fraction of the built design (test_plan.md
    section 4). Not independent of EC-05: D09 Fig. 7 is the EC-05 calibration source (DEF-23 d).
    Defect caught: an EMF chain (EQ-05, EQ-06, EQ-09) or a D09 layout that misses the published EMF. Only the band check
    raises AssertionError, so a D09 design that stops building fails outright instead of hiding in the xfail.
    """
    analysis = _analysis(_d09(variant))
    model = analysis.emf_phase_rms_v.value
    upper = 0.05 + analysis.edge_leakage_fraction.value
    deviations = {ref: model / ref - 1.0 for ref in (6.21, 6.20, 6.22)}
    print(f"OR-07 D09 {variant}: E_ph {model:.5f} V, band [-5.0 %, {upper:+.2%}], deviations {deviations}")
    assert all(-0.05 <= d <= upper for d in deviations.values()), (
        f"E_ph {model:.5f} V: {', '.join(f'{d:+.2%} vs {ref} V' for ref, d in deviations.items())}; "
        f"band [-5.0 %, {upper:+.2%}]"
    )


def _bz_harmonics_at_pole_centre_t(outcome: ComputeOutcome) -> list[float]:
    """Peak B_z of the odd harmonics 1 to 13 (EQ-05's default set) at the magnet mid-radius and copper layer L1."""
    design, stack = outcome.design, outcome.boards
    assert stack is not None
    rotor = design.rotor
    r_mid = np.array([sum(rotor.magnet.radial_span_mm()) / 2.0])
    z = np.array([min(stack.boards[0].copper_z_mm.values()) + rotor.air_gap_mm])
    plane = symmetry_plane_mm(rotor, stack.stack_thickness_mm)
    alpha = np.array([rotor.magnet.pole_arc_ratio])
    return [float(field_harmonic(n, r_mid, z, rotor, plane, alpha)[0][0]) for n in range(1, 14, 2)]


@pytest.mark.req("REQ-F-12")
@pytest.mark.eqt("EQT-05-O2")
def test_or08_d09_synthesised_bz_peak_at_mid_radius_within_5_percent_of_the_figure_reading() -> None:
    """OR-08 (D-045b): the B_z waveform at the pole centre, magnet mid-radius, against D09 Fig. 7 p.4 (0.72-0.75 T).

    The reference is a figure reading of the waveform peak, so the compared quantity is the sum of the odd harmonics
    1 to 13 of EQ-05 at the pole centre, from `embodic.physics.field_harmonic`. The band is +-5 % of every value of the
    reading range, [0.7125, 0.7560] T (spec section OR-08). U-E9's probe printed 0.7384 T. The fundamental b1 is
    recorded, not compared: 0.846122 T (`layers[i].b1_peak_mid_radius_t`), above the peak as for any flat-topped pole.
    Not independent of EC-05: same figure as the EC-05 calibration.
    Defect caught: a field model (EQ-05 harmonic amplitude, sign or G) that moves the waveform off D09's FEA reading.
    """
    outcome = _d09("A")
    harmonics = _bz_harmonics_at_pole_centre_t(outcome)
    peak = math.fsum(harmonics)
    b1 = _analysis(outcome).layers[0].b1_peak_mid_radius_t.value
    print(f"OR-08 D09 A: synthesised B_z peak (n 1-13) {peak:.4f} T; b1 {b1:.6f} T (fundamental, recorded)")
    assert harmonics[0] == pytest.approx(b1, rel=1e-12, abs=0.0), "the n = 1 term must be analyse()'s own b1 at this z"
    assert peak == pytest.approx(0.7384, abs=5e-5)
    assert 0.75 * 0.95 <= peak <= 0.72 * 1.05, f"B_z peak {peak:.4f} T outside [0.7125, 0.7560] T"


@pytest.mark.parametrize("variant", ["A", "B"])
def test_or09_d09_inductance_estimate_is_recorded(variant: str) -> None:
    """OR-09 (characterisation, no band): inductance_estimate_h against D09's measured 14.8 uH (Table 6 p.7).

    EQ-14 is `cannot verify yet` and has no leakage or end-turn term (G1), so it reads low (`inferred`). Reading I1
    (single phase, other phases open, rotor in place) is the pre-registered `assumption`. U-E9 recorded A 8.95 uH
    (-39.5 %) and B 5.04 uH (-66.0 %). D07 is not built (G41). The test never turns red on the difference.
    Defect caught: an inductance estimate that is missing, non-finite or not positive for a buildable design.
    """
    model_uh = _analysis(_d09(variant)).inductance_estimate_h.value * 1e6
    print(f"OR-09 D09 {variant}: L {model_uh:.4f} uH against 14.8 uH measured ({model_uh / 14.8 - 1.0:+.1%}, no band)")
    assert math.isfinite(model_uh) and model_uh > 0.0


@pytest.mark.skip(reason=NOT_REPRESENTABLE)
def test_or03_d10_phase_resistance_within_8_percent_of_the_measured_value() -> None:
    """OR-03: D10 phase R against 2.15 ohm measured (D10 p.8), +-8 %. Not built: SpiralCoilSpec has one trace width."""


@pytest.mark.skip(reason=NOT_REPRESENTABLE)
def test_or10_d10_winding_temperature_rise_within_30_percent() -> None:
    """OR-10: D10 temperature rise against 83.2 K measured (D10 p.10), +-30 % on the rise. Not built: G40."""
