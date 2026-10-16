"""Motor constant K_m on AnalysisResult (EQ-26, DEF-M2e4-01): wiring of the kernel into `analyse`."""

import dataclasses
import math

import pytest

from embodic.generators import build_layout
from embodic.io.examples import load_example
from embodic.physics import analyse
from embodic.results import AnalysisResult, Registry, load_registry
from embodic.units import Unit

pytestmark = pytest.mark.req("REQ-F-11")


@pytest.fixture(scope="module")
def registry() -> Registry:
    """Return the shipped equation registry."""
    return load_registry()


def _analysis(registry: Registry, line_current_a: float = 2.0) -> AnalysisResult:
    design = load_example("spiral_12c16p_default")[1]
    design = dataclasses.replace(
        design, operating=dataclasses.replace(design.operating, line_current_rms_a=line_current_a)
    )
    stack = build_layout(design, registry)
    result = analyse(design, stack, {}, registry)
    assert result is not None
    return result


def test_motor_constant_is_torque_over_the_root_of_phase_copper_loss_only(registry: Registry) -> None:
    """Catches K_m taken against loss_total (eddy and interconnect in the root) instead of P_Cu.

    The expectation comes from other result fields: T = (m/2) sqrt(2) Ke I and P_Cu = m R I^2, so
    K_m = (m/2) sqrt(2) Ke / sqrt(m R) with m = 3 phases.
    """
    result = _analysis(registry)
    expected = (
        1.5
        * math.sqrt(2.0)
        * result.ke_phase_v_s_per_rad.value
        / math.sqrt(3.0 * result.resistance_phase_operating_ohm.value)
    )
    km = result.motor_constant_n_m_per_sqrt_w
    assert km.value == pytest.approx(expected, rel=1e-12, abs=0.0)
    assert km.unit is Unit.N_M_PER_SQRT_W
    assert "EQ-26" in km.eq_ids
    assert result.loss_total_w.value > result.loss_copper_w.value  # the root would differ if P_total were used


def test_motor_constant_does_not_depend_on_the_current(registry: Registry) -> None:
    """Catches a K_m with a stray current or eddy term: T and sqrt(P_Cu) both scale with I."""
    low, high = _analysis(registry, 1.0), _analysis(registry, 4.0)
    assert low.torque_n_m.value != pytest.approx(high.torque_n_m.value)
    assert low.motor_constant_n_m_per_sqrt_w.value == pytest.approx(
        high.motor_constant_n_m_per_sqrt_w.value, rel=1e-12, abs=0.0
    )


def test_motor_constant_is_zero_without_phase_current(registry: Registry) -> None:
    """Catches a division by the zero copper loss: Xcoil reports 0 then (engine.js l.1435)."""
    assert _analysis(registry, 0.0).motor_constant_n_m_per_sqrt_w.value == 0.0
