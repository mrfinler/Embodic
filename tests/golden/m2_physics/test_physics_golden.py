"""GR (U-M2e): embodic.physics kernels against Xcoil v3 fixtures in tests/golden/data/physics.

Xcoil's own constants (RHO_CU_20 1.724e-8, ALPHA_CU 0.00393, VIA_PLATING_MM 0.025; engine.js l.12-15) are injected,
so a diff means the port differs, not the constant (CF-04 records the registry constant's -5.8e-5 offset).
"""

import math
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from harness.allow_list import apply_allow_list, load_allow_list
from harness.codec import load_area
from harness.compare import KERNEL, compare_scalar, compare_sequence

from embodic.model.rotor import ArcMagnet, RotorSpec, RotorType
from embodic.model.vocabulary import ConnectionTopology
from embodic.physics import (
    copper_resistivity_ohm_m,
    field_harmonic,
    ipc2221_current_a,
    phase_constants,
    skin_depth_mm,
    via_resistance_ohm,
)

XCOIL_RHO20_OHM_M = 1.724e-8
XCOIL_ALPHA_PER_K = 0.00393
pytestmark = pytest.mark.req("REQ-F-11")
CASES = load_area("physics")
LAYOUT_FNS = frozenset(
    {"computeAnalysis", "driveAnalysis", "torqueSpeed"}
)  # test_analysis_golden, test_torque_speed_golden
ALLOWED = load_allow_list(Path(__file__).parents[1] / "expected_diffs" / "physics.toml")


def _rho(temp_c: float) -> float:
    return copper_resistivity_ohm_m(temp_c, XCOIL_RHO20_OHM_M, XCOIL_ALPHA_PER_K)


def _trace_resistance(x: Mapping[str, Any]) -> float:
    rho = _rho(x["tempC"])
    return rho * (x["lengthMm"] / 1e3) / ((x["widthMm"] / 1e3) * (x["thickMm"] / 1e3))


def _via_area_mm2(x: Mapping[str, Any]) -> float:
    # A = rho l / R for a 1 mm barrel at rho 1 ohm*m recovers the kernel's area in m^2; scale to mm^2.
    return 1e-3 / via_resistance_ohm(x["drillMm"], x["platingMm"] * 1e3, 1.0, 1.0, 1) * 1e6


def _field(x: Mapping[str, Any]) -> dict[str, float]:
    f = x["F"]
    rotor = RotorSpec(
        poles=2 * f["pp"],
        rotor_type=RotorType.DOUBLE,
        magnet=ArcMagnet(pole_arc_ratio=f["alphaP"], r_inner_mm=1.0, r_outer_mm=2.0, thickness_mm=f["lm"]),
        remanence_t=f["Br"],
        recoil_permeability=f["muR"],
        air_gap_mm=0.0,
        back_iron_thickness_mm=0.0,
    )
    bz, bt = field_harmonic(x["n"], np.array([x["r"]]), np.array([x["z"]]), rotor, f["G"], np.array(f["alphaP"]))
    return {"Bt": float(bt[0]), "Bz": float(bz[0])}


def _connection(x: Mapping[str, Any]) -> dict[str, float]:
    c = phase_constants(x["an"]["Ke1"], ConnectionTopology(x["p"]["connection"]), x["p"]["phases"], 10)
    return {"KtPerArms": c.kt_n_m_per_a, "KvRpmPerV": c.kv_rpm_per_v, "keLinePk": c.ke_line_v_s_per_rad}


PORTS: Mapping[str, Callable[[Mapping[str, Any]], object]] = {
    "copperResistivity": lambda x: _rho(x["tempC"]),
    "traceResistance": _trace_resistance,
    "viaBarrelArea": _via_area_mm2,
    "skinDepthMm": lambda x: skin_depth_mm(x["freqHz"], _rho(x["tempC"])),
    "ipc2221Current": lambda x: ipc2221_current_a(x["areaMm2"], x["dT"], x["internal"]),
    "fieldHarmonic": _field,
    "applyConnection": _connection,
}


def test_every_physics_fixture_has_a_port() -> None:
    """Defect caught: a fixture added for a function that no test compares."""
    assert CASES, "no physics fixtures found"
    assert {case.fn for case in CASES.values()} <= set(PORTS) | LAYOUT_FNS


# Registry test id (interfaces.md section 3.1) that a case of each Xcoil function realises.
EQT_GR_BY_FN = {
    "copperResistivity": "EQT-10-GR",
    "traceResistance": "EQT-10-GR",
    "viaBarrelArea": "EQT-11-GR",
    "skinDepthMm": "EQT-13-GR",
    "ipc2221Current": "EQT-15-GR",
    "fieldHarmonic": "EQT-05-GR",
    "applyConnection": "EQT-09-GR",
}


@pytest.mark.parametrize(
    "case_id",
    [
        pytest.param(c, marks=pytest.mark.eqt(EQT_GR_BY_FN[case.fn]), id=c)
        for c, case in sorted(CASES.items())
        if case.fn in PORTS
    ],
)
def test_physics_kernel_matches_xcoil(case_id: str) -> None:
    """Every call agrees with Xcoil within the kernel class (rel 1e-12); an infinity must match exactly."""
    case = CASES[case_id]
    for call in case.calls:
        actual = PORTS[case.fn](call.inputs)
        if isinstance(actual, Mapping):
            verdict = compare_sequence([call.output], [actual], KERNEL)
        else:
            verdict = compare_scalar(call.output, actual, KERNEL)
        verdict = apply_allow_list(verdict, case_id, ALLOWED)
        assert verdict.ok, f"{case_id}: {verdict}"


def test_field_fixture_covers_the_open_rotor() -> None:
    """Defect caught: the open-rotor branch (G infinite) left without a golden case."""
    assert any(math.isinf(c.calls[0].inputs["F"]["G"]) for c in CASES.values() if c.fn == "fieldHarmonic")
