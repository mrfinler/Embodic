"""GR-22 (wave part): `analyse` on the generated wave boards against Xcoil's `compute().analysis` (REQ-F-35, REQ-F-11).

Xcoil's copper constants are injected into the registry, so a difference means the port differs, not the resistivity
constant (embodic's registry holds 1.7241e-8, Xcoil 1.724e-8).
"""

import dataclasses
from collections.abc import Mapping
from functools import cache
from typing import Any

import pytest
from harness import (
    EXPECTED_DIFFS_DIR,
    INTEGRATED,
    Comparison,
    GoldenCase,
    apply_allow_list,
    compare_scalar,
    compare_sequence,
    load_allow_list,
    load_area,
    load_case,
    near_threshold,
)
from harness.codec import DATA_DIR

from embodic.generators.wave import generate_wave
from embodic.geometry.circuit import LineLead, NeutralLead, PhaseLink
from embodic.geometry.discretise import piece_ratios
from embodic.geometry.layout import BoardStack
from embodic.physics import analyse
from embodic.results import AnalysisResult, Registry, load_registry

from .param_map import design_from_xcoil

pytestmark = pytest.mark.req("REQ-F-35", "REQ-F-11")

ANALYSES = {cid: c for cid, c in load_area("wave").items() if c.fn == "waveAnalysis"}
PHYSICS = load_area("physics")


def _layout_case(analysis_id: str) -> GoldenCase:
    return load_case(DATA_DIR / "wave" / f"{analysis_id.replace('wave-analysis-', 'wave-', 1)}.json")


def _xcoil_registry(xcoil: Mapping[str, Any], temp_c: float) -> Registry:
    rho20 = PHYSICS["copper-resistivity-20c"].calls[0].output
    alpha = (xcoil["rho"] / rho20 - 1.0) / (temp_c - 20.0)
    values = {"copper_resistivity_20c_ohm_m": rho20, "copper_temp_coeff_per_k": alpha}
    registry = load_registry()
    equations = {
        eq_id: dataclasses.replace(
            entry, constants=tuple(dataclasses.replace(c, value=values.get(c.name, c.value)) for c in entry.constants)
        )
        for eq_id, entry in registry.equations.items()
    }
    return dataclasses.replace(registry, equations=equations)


@cache
def _run(analysis_id: str) -> tuple[Mapping[str, Any], AnalysisResult, BoardStack]:
    xcoil = ANALYSES[analysis_id].calls[0].output
    params = _layout_case(analysis_id).calls[0].output["params"]
    design = design_from_xcoil(params)
    registry = _xcoil_registry(xcoil, params["tempC"])
    stack = generate_wave(design, registry)
    assert isinstance(stack, BoardStack)
    result = analyse(design, stack, {}, registry)
    assert result is not None
    return xcoil, result, stack


FLIP_BOUND = 1e-6  # a one-chord change at 0.5 mm moves Ke by under 1e-6 relative (measured: 0.5 mm against 0.05 mm)


def _chord_count_can_flip(stack: BoardStack) -> bool:
    """Return whether a primitive has len / 0.5 mm within 1e-9 of an integer.

    Then ceil() depends on the last bit of the rotated end points, which differ between V8 and glibc cos/sin
    (GR-17's near-threshold rule).
    """
    ratios = (r for path in stack.boards[0].paths for q in path.primitives for r in piece_ratios(q))
    return any(near_threshold(r, float(round(r))) for r in ratios)


def _check(report: Any, analysis_id: str, golden: list[float], actual: list[float], stack: BoardStack) -> None:
    """Match within 1e-9, or log indeterminate when a chord count may have flipped and the gap is under 1e-6."""
    comparison = compare_sequence(golden, actual, INTEGRATED)
    small = all(abs(a - g) <= FLIP_BOUND * max(abs(g), 1e-300) for g, a in zip(golden, actual, strict=True))
    if not comparison.ok and small and _chord_count_can_flip(stack):
        note = f"{len(comparison.diffs)} values differ by under {FLIP_BOUND:g} relative; a chord count may have flipped"
        comparison = Comparison(indeterminate=(note,))
    report.check(analysis_id, comparison)


@pytest.mark.eqt("EQT-06-GR", "EQT-07-GR", "EQT-12-GR")
@pytest.mark.parametrize("analysis_id", ANALYSES)
def test_gr22_ke_per_phase_and_eddy_loss_match_xcoil(analysis_id: str, golden_report: Any) -> None:
    """Catches a wrong EMF sum (belt sign, element direction, layer copy) or eddy-loss integral: 1e-9 relative."""
    xcoil, r, stack = _run(analysis_id)
    phases = len(xcoil["phaseKe"])
    golden = [xcoil["Ke1"], *xcoil["phaseKe"], xcoil["pEddy"]]
    actual = [
        r.ke_phase_v_s_per_rad.value,
        *(p.ke_peak_v_s_per_rad.value for p in r.phases[:phases]),
        r.loss_eddy_w.value,
    ]
    _check(golden_report, analysis_id, golden, actual, stack)


@pytest.mark.eqt("EQT-07-GR", "EQT-09-GR", "EQT-18-GR")
@pytest.mark.parametrize("analysis_id", [a for a, c in ANALYSES.items() if len(c.calls[0].output["phaseKe"]) == 3])
def test_gr22_three_phase_line_quantities_match_xcoil(analysis_id: str, golden_report: Any) -> None:
    """Catches a wrong line constant, waveform synthesis or torque on a three-phase wave board."""
    xcoil, r, stack = _run(analysis_id)
    golden = [xcoil["keLinePk"], xcoil["keLinePeakWaveform"], xcoil["thd"], xcoil["torque"], xcoil["pCirc"]]
    actual = [
        r.ke_line_v_s_per_rad.value, r.ke_line_peak_v_s_per_rad.value, r.thd_phase.value, r.torque_n_m.value,
        sum(p.circulating_loss_w.value for p in r.phases),
    ]  # fmt: skip
    _check(golden_report, analysis_id, golden, actual, stack)


@pytest.mark.parametrize("analysis_id", ANALYSES)
def test_gr22_phase_resistance_differs_from_xcoil_only_by_the_via_barrel_length(analysis_id: str) -> None:
    """Catches a missing or doubled via term and any other resistance error (EQ-10, EQ-11).

    Xcoil sizes the via of a wave element from the spacing of adjacent copper layers, `hAdj` (engine.js l.1832);
    `analyse` uses the board thickness. Giving the stack the spacing as its thickness must remove the whole difference.
    """
    xcoil, r, stack = _run(analysis_id)
    params = _layout_case(analysis_id).calls[0].output["params"]
    design = design_from_xcoil(params)
    z = list(stack.boards[0].copper_z_mm.values())
    spaced = dataclasses.replace(stack, board_thickness_mm=abs(z[1] - z[0]))
    registry = _xcoil_registry(xcoil, params["tempC"])
    again = analyse(design, spaced, {}, registry)
    assert again is not None
    phases = len(xcoil["phaseR"])
    golden = xcoil["phaseR"]
    verdict = compare_scalar(sum(golden) / phases, again.resistance_phase_operating_ohm.value, INTEGRATED)
    assert verdict.ok, f"{analysis_id}: {verdict}"
    assert r.resistance_phase_operating_ohm.value > again.resistance_phase_operating_ohm.value


INTERCONNECT_CASES = [
    a for a, c in ANALYSES.items() if len(c.calls[0].output["phaseKe"]) == 3 and not a.endswith("-open")
]
OVERLAP_STAR = "wave-analysis-overlap-l2-m3-p16-t2"
OVERLAP_DELTA = "wave-analysis-overlap-l2-m3-p16-t2-delta"
ALLOW = load_allow_list(EXPECTED_DIFFS_DIR / "wave.toml")


@pytest.mark.parametrize("analysis_id", INTERCONNECT_CASES)
def test_gr22_interconnect_loss_matches_xcoil_for_star_and_delta(analysis_id: str, golden_report: Any) -> None:
    """Catches DEF-U-M3b-01: a star item of stubs and ring in one path, which counted 0.24 of Xcoil's loss.

    The overlap star and delta are compared too: embodic counts the tap stubs (star) or the line leads (delta) and
    Xcoil counts neither (engine.js l.2154-2172), and XD-WAVE-001 and XD-WAVE-002 admit exactly that.
    """
    xcoil, r, _ = _run(analysis_id)
    comparison = compare_scalar(xcoil["pInterconnect"], r.loss_interconnect_w.value, INTEGRATED)
    golden_report.check(analysis_id, apply_allow_list(comparison, analysis_id, ALLOW))


@pytest.mark.parametrize(
    ("analysis_id", "uncounted"), [(OVERLAP_STAR, PhaseLink), (OVERLAP_DELTA, LineLead)], ids=["star", "delta"]
)
def test_gr22_overlap_difference_is_the_uncounted_copper_and_nothing_else(
    analysis_id: str, uncounted: type[PhaseLink | LineLead]
) -> None:
    """Catches an allow-list entry that hides more than it says: three PhaseLink stubs (XD-WAVE-001) or LineLead leads.

    Reclassifying them as NeutralLead copper (no current, as in Xcoil's `link: [0, 0, 0]`, engine.js l.2172, and its
    unset `icR`, l.2154) makes embodic's interconnect loss equal Xcoil's, so no other copper differs.
    """
    xcoil, r, stack = _run(analysis_id)
    board = stack.boards[0]
    assert sum(isinstance(role, uncounted) for role in board.circuit.interconnect_roles) == 3
    roles = tuple(
        NeutralLead(path_id=x.path_id) if isinstance(x, uncounted) else x for x in board.circuit.interconnect_roles
    )
    stripped = dataclasses.replace(board, circuit=dataclasses.replace(board.circuit, interconnect_roles=roles))
    params = _layout_case(analysis_id).calls[0].output["params"]
    again = analyse(
        design_from_xcoil(params),
        dataclasses.replace(stack, boards=(stripped,)),
        {},
        _xcoil_registry(xcoil, params["tempC"]),
    )
    assert again is not None
    assert r.loss_interconnect_w.value > xcoil["pInterconnect"]
    verdict = compare_scalar(xcoil["pInterconnect"], again.loss_interconnect_w.value, INTEGRATED)
    assert verdict.ok, verdict


def test_gr22_every_allow_listed_case_still_differs() -> None:
    """Catches a stale entry: each listed case must still differ from Xcoil, else the entry is deleted."""
    for entry in ALLOW:
        xcoil, r, _ = _run(entry.case)
        assert not compare_scalar(xcoil["pInterconnect"], r.loss_interconnect_w.value, INTEGRATED).ok, entry.id
