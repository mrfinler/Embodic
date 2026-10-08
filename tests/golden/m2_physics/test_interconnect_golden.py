"""GR (U-M2e-4): interconnect copper, loss sum, efficiency and motor constant against Xcoil applyConnection.

The mapped layouts get their interconnect roles from Xcoil's own items (xcoil_roles.py), so P_ic and the per-phase
sums test the role bookkeeping and the ring segments (EQ-23). The loss sum and the efficiency also contain the copper
loss, which the mapped series circuit does not reproduce (DEF-M2e3-01, Agent 4 U-V2): the strict comparisons below
put Xcoil's own P_Cu in its place, and the result-level comparison records the measured gap in physics.toml.
"""

import dataclasses
import math
from collections.abc import Mapping

import pytest
from harness.allow_list import apply_allow_list
from harness.compare import INTEGRATED, KERNEL, compare_scalar, compare_sequence

from embodic.errors import message_for
from embodic.geometry.layout import BoardStack
from embodic.model.vocabulary import Phase
from embodic.physics import analyse, efficiency, path_resistance_ohm
from embodic.physics.circuit import motor_constant_n_m_per_sqrt_w
from embodic.physics.interconnect import interconnect_resistance
from embodic.results import AnalysisResult, Status
from m2_physics.test_analyse_layouts import CASES, _design, _raw, _stack
from m2_physics.test_analysis_golden import ALLOWED, FIXTURE, _xcoil, _xcoil_registry
from m2_physics.xcoil_roles import classify

pytestmark = pytest.mark.req("REQ-F-11")
UNCLASSIFIED = "INTERNAL_INTERCONNECT_UNCLASSIFIED"


def _classified(case: str) -> BoardStack:
    stack = _stack(_raw(case))
    board = classify(stack.boards[0], _raw(case), _xcoil(case)["icItems"])
    return dataclasses.replace(stack, boards=(board,))


@pytest.fixture(scope="module")
def results() -> Mapping[str, AnalysisResult]:
    """Run analyse() once per classified layout with Xcoil's copper constants."""
    out = {}
    for case in CASES:
        result = analyse(_design(_raw(case)), _classified(case), {}, _xcoil_registry(case))
        assert result is not None
        out[case] = result
    return out


@pytest.mark.parametrize("case", CASES)
def test_interconnect_sums_per_phase_match_xcoil(case: str) -> None:
    """Defect caught: a stub counted as a link, a tap stub on the wrong phase, or a ring segment of the wrong length.

    Compares Xcoil's lineStub, link and neutralRing (interconnectResistance) with the sums of the classified layout,
    both at Xcoil's resistivity at the winding temperature.
    """
    raw, x = _raw(case), _xcoil(case)
    board = _classified(case).boards[0]
    thickness = {layer["name"]: layer["copperT"] for layer in raw["layers"]}
    path_r = dict(enumerate(path_resistance_ohm(board.arrays(), thickness, x["rho"]).tolist()))
    sums = interconnect_resistance(board, (Phase.A, Phase.B, Phase.C), path_r, thickness, x["rho"])
    golden = x["interconnect"]
    for name, expected, actual in (
        ("lineStub", golden["lineStub"], sums.line_stub_ohm),
        ("link", golden["link"], sums.link_ohm),
        ("neutralRing", golden["neutralRing"], sums.neutral_ring_ohm),
    ):
        verdict = compare_sequence(expected, list(actual), INTEGRATED)
        assert verdict.ok, f"{case} {name}: {verdict}"


@pytest.mark.parametrize("case", CASES)
def test_interconnect_loss_matches_xcoil(results: Mapping[str, AnalysisResult], case: str) -> None:
    """Defect caught: P_ic with the wrong current per role or a dropped ring segment (EQ-23, star)."""
    verdict = compare_scalar(_xcoil(case)["pInterconnect"], results[case].loss_interconnect_w.value, INTEGRATED)
    assert verdict.ok, f"{case}: {verdict}"
    assert UNCLASSIFIED not in {f.code for f in results[case].loss_interconnect_w.validity}


def _with_xcoil_copper(case: str, r: AnalysisResult) -> float:
    """Return the embodic loss sum with Xcoil's P_Cu in place of embodic's (DEF-M2e3-01)."""
    return r.loss_total_w.value - r.loss_copper_w.value + _xcoil(case)["pCu"]


@pytest.mark.parametrize("case", CASES)
def test_loss_sum_and_efficiency_match_xcoil_given_its_copper_loss(
    results: Mapping[str, AnalysisResult], case: str
) -> None:
    """Defect caught: a loss term left out of the sum, or eta with the wrong denominator (EQ-26).

    P_eddy, P_circ, P_delta,circ, P_ic and P_out are embodic's; only P_Cu is Xcoil's. The serpentine eddy loss differs
    by XD-PHY-002, which XD-PHY-004 carries into the sum.
    """
    r, x = results[case], _xcoil(case)
    total = _with_xcoil_copper(case, r)
    xcoil = {"loss_total_given_copper": x["lossTotal"], "efficiency_given_copper": x["efficiency"]}
    embodic = {"loss_total_given_copper": total, "efficiency_given_copper": efficiency(r.output_power_w.value, total)}
    verdict = apply_allow_list(compare_sequence([xcoil], [embodic], INTEGRATED), FIXTURE[case], ALLOWED)
    assert verdict.ok, f"{case}: {verdict}"
    assert compare_scalar(x["pOut"], r.output_power_w.value, INTEGRATED).ok


@pytest.mark.parametrize("case", CASES)
def test_motor_constant_matches_xcoil_given_its_copper_loss(results: Mapping[str, AnalysisResult], case: str) -> None:
    """Defect caught: K_m from the line current, the loss sum or a missing square root (EQ-26)."""
    r, x = results[case], _xcoil(case)
    i_ph = _design(_raw(case)).operating.line_current_rms_a  # star: phase current = line current
    actual = motor_constant_n_m_per_sqrt_w(r.torque_n_m.value, x["pCu"], i_ph)
    verdict = compare_scalar(x["motorConstant"], actual, INTEGRATED)
    assert verdict.ok, f"{case}: {verdict}"


def test_motor_constant_is_zero_without_copper_loss_or_current() -> None:
    """Defect caught: a division by zero or a NaN where Xcoil reports 0 (l.1435)."""
    assert motor_constant_n_m_per_sqrt_w(0.05, 0.0, 1.0) == 0.0
    assert motor_constant_n_m_per_sqrt_w(0.05, 2.0, 0.0) == 0.0
    assert motor_constant_n_m_per_sqrt_w(0.05, 4.0, 1.0) == pytest.approx(0.025, rel=1e-15)
    assert compare_scalar(0.05 / math.sqrt(2.0), motor_constant_n_m_per_sqrt_w(0.05, 2.0, 1.0), KERNEL).ok


@pytest.mark.parametrize("case", CASES)
def test_result_level_loss_sum_and_efficiency_against_xcoil(results: Mapping[str, AnalysisResult], case: str) -> None:
    """Records the gap that the mapped circuit's copper loss leaves in the loss sum and eta (XD-PHY-005).

    Defect caught: a gap that grows beyond the measured copper-loss difference of DEF-M2e3-01.
    """
    r, x = results[case], _xcoil(case)
    xcoil = {"loss_total": x["lossTotal"], "efficiency": x["efficiency"]}
    embodic = {"loss_total": r.loss_total_w.value, "efficiency": r.efficiency.value}
    verdict = apply_allow_list(compare_sequence([xcoil], [embodic], INTEGRATED), FIXTURE[case], ALLOWED)
    assert verdict.ok, f"{case}: {verdict}"


@pytest.mark.parametrize("case", CASES)
def test_unclassified_interconnect_is_unresolved_and_adds_nothing(
    results: Mapping[str, AnalysisResult], case: str
) -> None:
    """Defect caught: roles guessed from net names, or a P_ic of 0 reported without a reason (section 5).

    The mapped layout without roles keeps its interconnect paths; analyse() must report P_ic as unresolved with the
    catalogue reason, add no interconnect resistance to R_LL, and carry the flag into the loss sum and eta.
    """
    raw = _raw(case)
    stack = _stack(raw)
    assert stack.boards[0].circuit.interconnect_path_ids and not stack.boards[0].circuit.interconnect_roles
    r = analyse(_design(raw), stack, {}, _xcoil_registry(case))
    assert r is not None
    p_ic = r.loss_interconnect_w
    assert p_ic.value == 0.0
    assert p_ic.status is Status.UNRESOLVED
    flags = {f.code: f.message for f in p_ic.validity}
    assert flags[UNCLASSIFIED] == "interconnect copper not classified"
    assert message_for(UNCLASSIFIED).startswith("Interconnect copper not classified")
    for traced in (r.resistance_line_ohm, r.loss_total_w, r.efficiency):
        assert traced.status is Status.UNRESOLVED and UNCLASSIFIED in {f.code for f in traced.validity}
    assert r.resistance_line_ohm.value < results[case].resistance_line_ohm.value
