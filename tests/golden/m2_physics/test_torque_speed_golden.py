"""GR (U-M2e-3): embodic.physics.drive against Xcoil's torqueSpeed curve (EQ-20, label estimate).

The golden checks the port, not the physics: EQ-20 is `cannot verify yet`. Every input of a call is read from the
fixture, where Xcoil recorded the star-equivalent resistance, inductance and EMF constant its own run used, so the
case differs from Xcoil only if the curve code differs.
"""

import math
from collections.abc import Mapping
from typing import Any

import numpy as np
import pytest
from harness.codec import load_area
from harness.compare import KERNEL, compare_scalar, compare_sequence

from embodic.model.operating import Modulation
from embodic.model.vocabulary import ConnectionTopology
from embodic.physics import (
    base_speed_rpm,
    inverter_phase_voltage_v,
    no_load_speed_rpm,
    torque_speed_envelope,
)

pytestmark = pytest.mark.req("REQ-F-20")
MODULATION = {"svpwm": Modulation.SVPWM, "sine": Modulation.SPWM, "sixstep": Modulation.SIX_STEP}
CASES = {c.case_id: c for c in load_area("physics").values() if c.fn in {"driveAnalysis", "torqueSpeed"}}


def _port(inputs: Mapping[str, Any]) -> tuple[Modulation, np.ndarray, np.ndarray]:
    """Run the port on the star-equivalent inputs of one fixture call; Xcoil stores the rms EMF constant."""
    modulation = MODULATION[inputs["modulation"]]
    speed, torque = torque_speed_envelope(
        inputs["resistance"],
        inputs["inductance"],
        inputs["keEqRms"] * math.sqrt(2.0),
        inputs["vDc"],
        modulation,
        inputs["currentLimit"],
        inputs["poles"],
        inputs["points"],
        phases=inputs["phases"],
        connection=ConnectionTopology(inputs["connection"]),
    )
    return modulation, speed, torque


def test_the_fixtures_cover_every_modulation_and_a_delta_winding() -> None:
    """Defect caught: a modulation branch or the delta star-equivalent mapping left without a golden case."""
    modulations = {c.calls[0].output["inputs"]["modulation"] for c in CASES.values()}
    assert modulations == set(MODULATION)
    assert any(c.case_id == "drive-sector-delta" for c in CASES.values())
    assert len(CASES) >= 7


def test_the_fixtures_cover_open_windings_of_two_and_one_phase() -> None:
    """Defect caught: EQ-20 for phase counts other than three (open connection) left without a golden case."""
    open_phases = {
        c.calls[0].output["inputs"]["phases"]
        for c in CASES.values()
        if c.calls[0].output["inputs"]["connection"] == "open"
    }
    assert {1, 2, 3} <= open_phases


@pytest.mark.parametrize("case_id", sorted(CASES))
def test_torque_speed_curve_matches_xcoil(case_id: str) -> None:
    """Defect caught: a wrong inverter limit, torque constant, field-weakening scan or curve end point.

    Speed, torque and power agree point by point within the kernel class (rel 1e-12).
    """
    for call in CASES[case_id].calls:
        golden = call.output
        modulation, speed, torque = _port(golden["inputs"])
        connection = ConnectionTopology(golden["inputs"]["connection"])
        power = torque * speed * 2.0 * math.pi / 60.0
        for name, expected, actual in (
            ("speed", golden["speedRpm"], speed),
            ("torque", golden["torque"], torque),
            ("power", golden["power"], power),
        ):
            verdict = compare_sequence(expected, actual.tolist(), KERNEL)
            assert verdict.ok, f"{case_id} {name}: {verdict}"
        scalars = (
            (
                "vPhaseMax",
                golden["vPhaseMax"],
                inverter_phase_voltage_v(golden["inputs"]["vDc"], modulation, connection),
            ),
            (
                "rpmNoLoad",
                golden["rpmNoLoad"],
                no_load_speed_rpm(
                    golden["inputs"]["keEqRms"] * math.sqrt(2.0), golden["inputs"]["vDc"], modulation, connection
                ),
            ),
            ("rpmBase", golden["rpmBase"], base_speed_rpm(speed, torque)),
            ("torqueMax", golden["torqueMax"], float(np.max(torque))),
        )
        for name, expected, actual in scalars:
            verdict = compare_scalar(expected, actual, KERNEL)
            assert verdict.ok, f"{case_id} {name}: {verdict}"


def test_the_synthetic_case_runs_in_field_weakening() -> None:
    """Defect caught: a fixture whose L_s is too small to move the i_d scan, so the scan is never compared.

    An L = 0 winding makes no torque above its no-load speed V / Ke_rms. The synthetic winding keeps a positive torque
    beyond it, which only the field-weakening scan (i_d < 0) can deliver.
    """
    golden = CASES["torque-speed-field-weakening"].calls[0].output
    beyond = [t for rpm, t in zip(golden["speedRpm"], golden["torque"], strict=True) if rpm > golden["rpmNoLoad"]]
    assert beyond, "the curve ends at the no-load speed"
    assert max(beyond) > 0.0
