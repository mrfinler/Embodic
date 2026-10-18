"""GR-22 (U-M2e-3): analyse() on the three mapped Xcoil layouts against compute().analysis fixtures.

Covers EQ-06 (Ke per phase), EQ-12 (eddy loss), EQ-18 (phase THD, phase and line waveform), EQ-23 (line resistance with
interconnect copper), EQ-26 (efficiency) and EQ-27 (utilisation factor k_u). Xcoil's copper constants are injected into
the registry, so a diff means the port differs, not the resistivity constant (embodic's registry holds 1.7241e-8, Xcoil
1.724e-8). Every Xcoil number comes from a fixture of tests/golden/data/physics.

Resistance and copper loss are not compared at result level on sector and wave: the mapper returns no element list, so
`_series_circuit` sums every phase-tagged path in series. For those layouts EQ-10 is checked per object kind in
test_copper_accounting_golden.py and the line-resistance kernel takes Xcoil's own phase resistances here.
"""

import dataclasses
import math
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest
from harness.allow_list import apply_allow_list, load_allow_list
from harness.codec import load_area
from harness.compare import INTEGRATED, KERNEL, Tolerance, compare_scalar, compare_sequence

from embodic.geometry.primitives import PrimitiveRole
from embodic.model.vocabulary import ConnectionTopology, Phase
from embodic.physics import analyse, efficiency, line_resistance_ohm
from embodic.results import AnalysisResult, Registry, load_registry
from m2_physics.test_analyse_layouts import CASES, _design, _raw, _stack

pytestmark = pytest.mark.req("REQ-F-11")
AREA = load_area("physics")
ALLOWED = load_allow_list(Path(__file__).parents[1] / "expected_diffs" / "physics.toml")
FIXTURE = {
    "layout-sector-default": "analysis-sector-default",
    "layout-serpentine-default": "analysis-serpentine-default",
    "layout-wave-turns-2": "analysis-wave-turns-2",
}
UTILISATION_FIXTURE = {
    "layout-sector-default": "utilisation-factor-sector-default",
    "layout-serpentine-default": "utilisation-factor-serpentine-default",
    "layout-wave-turns-2": "utilisation-factor-wave-turns-2",
}
WAVEFORM_ABS_FRACTION = 1e-9  # of the waveform peak: a zero crossing has no meaningful relative error


def _xcoil(case: str) -> Mapping[str, Any]:
    return AREA[FIXTURE[case]].calls[0].output


def _xcoil_registry(case: str) -> Registry:
    """Return the packaged registry with Xcoil's 20 degC resistivity and temperature coefficient from fixtures."""
    rho20 = AREA["copper-resistivity-20c"].calls[0].output
    temp_c = _raw(case)["params"]["tempC"]
    alpha = (_xcoil(case)["rho"] / rho20 - 1.0) / (temp_c - 20.0)
    values = {"copper_resistivity_20c_ohm_m": rho20, "copper_temp_coeff_per_k": alpha}
    registry = load_registry()
    equations = {
        eq_id: dataclasses.replace(
            entry, constants=tuple(dataclasses.replace(c, value=values.get(c.name, c.value)) for c in entry.constants)
        )
        for eq_id, entry in registry.equations.items()
    }
    return dataclasses.replace(registry, equations=equations)


@pytest.fixture(scope="module")
def results() -> Mapping[str, AnalysisResult]:
    """Run analyse() once per layout with Xcoil's copper constants."""
    out = {}
    for case in CASES:
        raw = _raw(case)
        result = analyse(_design(raw), _stack(raw), {}, _xcoil_registry(case))
        assert result is not None
        out[case] = result
    return out


def _compared(case: str, r: AnalysisResult) -> tuple[dict[str, float], dict[str, float]]:
    """Return (Xcoil, embodic) values by quantity name for one layout."""
    x = _xcoil(case)
    xcoil = {
        "ke_phase": x["Ke1"],
        "ke_phase_a": x["phaseKe"][0],
        "ke_phase_b": x["phaseKe"][1],
        "ke_phase_c": x["phaseKe"][2],
        "ke_line": x["keLinePk"],
        "ke_line_peak": x["keLinePeakWaveform"],
        "thd_phase": x["thd"],
        "torque": x["torque"],
        "loss_eddy": x["pEddy"],
        "loss_circulating": x["pCirc"],
    }
    embodic = {
        "ke_phase": r.ke_phase_v_s_per_rad.value,
        "ke_phase_a": r.phases[0].ke_peak_v_s_per_rad.value,
        "ke_phase_b": r.phases[1].ke_peak_v_s_per_rad.value,
        "ke_phase_c": r.phases[2].ke_peak_v_s_per_rad.value,
        "ke_line": r.ke_line_v_s_per_rad.value,
        "ke_line_peak": r.ke_line_peak_v_s_per_rad.value,
        "thd_phase": r.thd_phase.value,
        "torque": r.torque_n_m.value,
        "loss_eddy": r.loss_eddy_w.value,
        "loss_circulating": math.fsum(p.circulating_loss_w.value for p in r.phases),
    }
    return xcoil, embodic


@pytest.mark.eqt("EQT-06-GR", "EQT-07-GR", "EQT-09-GR", "EQT-12-GR", "EQT-18-GR")
@pytest.mark.parametrize("case", CASES)
def test_result_quantities_match_xcoil(results: Mapping[str, AnalysisResult], case: str) -> None:
    """Defect caught: a wrong EMF sum, THD, line waveform peak, torque or eddy-loss coefficient (EQ-06, 09, 12, 18).

    Each value agrees within the integrated class (rel 1e-9). The serpentine eddy loss differs by XD-PHY-002.
    """
    xcoil, embodic = _compared(case, results[case])
    verdict = compare_sequence([xcoil], [embodic], INTEGRATED)
    verdict = apply_allow_list(verdict, FIXTURE[case], ALLOWED)
    assert verdict.ok, f"{case}: {verdict}"


@pytest.mark.eqt("EQT-18-GR")
@pytest.mark.parametrize("case", CASES)
def test_phase_waveform_matches_xcoil(results: Mapping[str, AnalysisResult], case: str) -> None:
    """Defect caught: a harmonic with the wrong phase or amplitude in the synthesised waveform (EQ-18)."""
    golden = _xcoil(case)["phaseWaveform"]
    peak = max(abs(v) for v in golden)
    tolerance = Tolerance("waveform", rel=0.0, abs=WAVEFORM_ABS_FRACTION * peak)
    verdict = compare_sequence(golden, list(results[case].emf_waveform_v.value), tolerance)
    assert verdict.ok, f"{case}: {verdict}"


@pytest.mark.eqt("EQT-23-GR")
@pytest.mark.parametrize("case", CASES)
def test_line_resistance_with_interconnect_copper_matches_xcoil(case: str) -> None:
    """Defect caught: a wrong star formula or a dropped stub, link or neutral-ring term in EQ-23.

    The kernel gets Xcoil's own phase resistances and interconnect resistances, so only the network algebra is tested.
    """
    x = _xcoil(case)
    ic = x["interconnect"]
    actual = line_resistance_ohm(x["phaseR"], ConnectionTopology.STAR, ic["lineStub"], ic["link"], ic["neutralRing"])
    verdict = compare_scalar(x["rLineLine"], actual, KERNEL)
    assert verdict.ok, f"{case}: {verdict}"
    without = line_resistance_ohm(x["phaseR"], ConnectionTopology.STAR)
    assert actual > without, "the fixture has interconnect copper, so dropping it must change the result"


@pytest.mark.eqt("EQT-26-GR")
@pytest.mark.parametrize("case", CASES)
def test_efficiency_matches_xcoil(case: str) -> None:
    """Defect caught: eta = P_out / (P_out + P_loss) with the wrong denominator (EQ-26).

    Xcoil's own P_out and loss sum, which include interconnect copper, go in.
    """
    x = _xcoil(case)
    verdict = compare_scalar(x["efficiency"], efficiency(x["pOut"], x["lossTotal"]), KERNEL)
    assert verdict.ok, f"{case}: {verdict}"


@pytest.mark.eqt("EQT-27-GR")
@pytest.mark.parametrize("case", CASES)
def test_utilisation_factor_matches_eq27(results: Mapping[str, AnalysisResult], case: str) -> None:
    """Defect caught: a k_u that departs from EQ-27 in the series count, the Ke, the ideal's z or the 1e-6 scale.

    Named departures: a count that drops the partial last side of a spiral (sector 0.896 against 0.784), phase A's Ke in
    place of the three-phase ratio (serpentine, 6.4e-6), an ideal evaluated at phase A's z only (4.2e-3), and a lost
    1e-6 scale. The fixture's `ku` is Xcoil's `kw1` on sector and wave and the three-phase ratio on serpentine
    (fix_wave_f8.md A.4).
    """
    golden = AREA[UTILISATION_FIXTURE[case]].calls[0].output
    assert golden["ku"] > 0.0
    verdict = compare_scalar(golden["ku"], results[case].winding_factor_1.value, INTEGRATED)
    assert verdict.ok, f"{case}: {verdict}"


@pytest.mark.parametrize("case", CASES)
def test_mapped_side_count_is_the_series_conductor_count(case: str) -> None:
    """Defect caught: a mapping that loses or adds a radial conductor (sector: 56 against 64).

    The case is the sector's partial last side. analyse() divides phase A's SIDE primitives by the largest parallel
    group to get the series conductors per phase.
    """
    board = _stack(_raw(case)).boards[0]
    phase_a = next(pc for pc in board.circuit.phases if pc.phase is Phase.A)
    sides = sum(
        1
        for group in phase_a.groups
        for member in group.members
        for i in member.path_ids
        for prim in board.paths[i].primitives
        if prim.role is PrimitiveRole.SIDE
    )
    parallel = max(len(g.members) for pc in board.circuit.phases for g in pc.groups)
    expected = AREA[UTILISATION_FIXTURE[case]].calls[0].output["conductorsPerPhase"]
    assert sides / parallel == expected
