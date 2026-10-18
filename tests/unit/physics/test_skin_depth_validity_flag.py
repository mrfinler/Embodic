"""REQ-T-08 (a): a trace wider than one third of the skin depth raises RANGE_SKIN_DEPTH on the R and eddy results."""

import dataclasses

import pytest

from embodic.api import compute
from embodic.io.examples import load_example
from embodic.model.provenance import derive_provenance
from embodic.results.status import ValidityEffect

SKIN_DEPTH_133_HZ_MM = 5.72  # UT-PHY-13: 133.3 Hz, 20 degC (tests/unit/physics/test_kernels.py)
WIDTH_MM = 0.4 * SKIN_DEPTH_133_HZ_MM
R_AND_EDDY = (
    "resistance_phase_20c_ohm",
    "resistance_phase_operating_ohm",
    "resistance_line_ohm",
    "loss_copper_w",
    "loss_eddy_w",
)


def analysed(trace_width_mm: float | None):
    """Return the analysis of the 12-coil 16-pole default example (1000 rpm, 133.3 Hz) at a trace width."""
    ref, design = load_example("spiral_12c16p_default")
    if trace_width_mm is not None:
        coil = dataclasses.replace(design.winding.coil, trace_width_mm=trace_width_mm)
        design = dataclasses.replace(design, winding=dataclasses.replace(design.winding, coil=coil))
    outcome = compute(design, derive_provenance(design, (ref, design), []))
    assert outcome is not None and outcome.analysis is not None
    return outcome.analysis


@pytest.mark.req("REQ-T-08")
def test_t08_a_trace_of_0_4_skin_depths_flags_the_resistance_and_the_eddy_results():
    """UT-PHY-13. Catches an unchecked validity limit: w = 0.4 delta at 133.3 Hz must raise RANGE_SKIN_DEPTH."""
    analysis = analysed(WIDTH_MM)
    for quantity in R_AND_EDDY:
        flags = [f for f in getattr(analysis, quantity).validity if f.code == "RANGE_SKIN_DEPTH"]
        assert len(flags) == 1, quantity
        assert flags[0].eq_id == "EQ-13" and flags[0].effect is ValidityEffect.LIMITATION, quantity
    for phase in analysis.phases:
        assert [f.code for f in phase.resistance_operating_ohm.validity] == ["RANGE_SKIN_DEPTH"]
    assert not [f for f in analysis.ke_phase_v_s_per_rad.validity if f.code == "RANGE_SKIN_DEPTH"]


@pytest.mark.req("REQ-T-08")
def test_t08_the_packaged_trace_width_raises_no_skin_depth_flag():
    """Control. Catches a flag raised on every design: the packaged width is far below one third of the skin depth."""
    analysis = analysed(None)
    for quantity in R_AND_EDDY:
        assert [f.code for f in getattr(analysis, quantity).validity if f.code == "RANGE_SKIN_DEPTH"] == []


@pytest.mark.req("REQ-T-08")
def test_t08_the_skin_depth_flag_travels_to_every_result_built_from_the_resistances():
    """Catches DEF-UE20-01 (fix_wave_f4.md A.4): a circulating or interconnect loss without the flag of its R."""
    analysis = analysed(WIDTH_MM)
    built_from_r = [
        analysis.loss_circulating_w,
        analysis.loss_interconnect_w,
        analysis.loss_total_w,
        analysis.efficiency,
        analysis.motor_constant_n_m_per_sqrt_w,
        analysis.temperature_rise_k,
        *(phase.circulating_loss_w for phase in analysis.phases),
    ]
    missing = [t.quantity for t in built_from_r if "RANGE_SKIN_DEPTH" not in [f.code for f in t.validity]]
    assert missing == []
    not_from_r = (analysis.skin_depth_mm, analysis.loss_delta_circulating_w, analysis.torque_n_m)
    assert [t.quantity for t in not_from_r if "RANGE_SKIN_DEPTH" in [f.code for f in t.validity]] == []
