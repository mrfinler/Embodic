"""PR-13 (DRC never under-reports on wave boards) and PR-14 (rotation invariance), REQ-F-35.

PR-13 uses Agent 4's independent brute-force sweep (tests/independent/m1): whenever `run_drc` passes, the sweep finds no
non-exempt pair below the D-006 threshold, and every pair the sweep finds below it is also reported by `run_drc`.
"""

import json
import math
from functools import cache

import pytest
from board_dump_reader import parse_board_dump
from brute_clearance import Verdict
from drc_universe import contract_exemptions, sweep
from embodic_adapter import pair_violations, uniform_rules
from gr19 import universe
from tests.unit.generators.wave.designs import wave
from tests.unit.property.chord_counts import designed_integers_snapped, roundoff_rel
from tests.unit.property.t_junctions import same_net_via_tap_pairs, t_junction_pairs

from embodic.drc import run_drc
from embodic.generators.wave.generate import generate_wave_rotated
from embodic.geometry.layout import BoardStack, Layout
from embodic.io.board_dump import dump_layout, encode_board_dump
from embodic.model.design import DesignParameters
from embodic.model.winding_specs import WaveStyle
from embodic.physics import analyse
from embodic.results import load_registry

pytestmark = pytest.mark.req("REQ-F-35")

RULE_MM = 0.2
REGISTRY = load_registry()


@cache
def _layout(style: str, poles: int, phases: int) -> Layout:
    stack = generate_wave_rotated(wave(WaveStyle(style), poles=poles, phases=phases), REGISTRY, 0.0)
    return stack.boards[0]  # type: ignore[union-attr]


@pytest.mark.req("REQ-F-10")
@pytest.mark.parametrize(
    ("style", "poles", "phases"),
    [("involute", 8, 3), ("jog", 8, 3), ("chord", 8, 3), ("overlap", 8, 3), ("involute", 8, 2), ("overlap", 8, 1)],
)
def test_pr_13_run_drc_never_under_reports_on_a_wave_board(style: str, poles: int, phases: int) -> None:
    """PR-13. Catches a wave board whose exempt pairs or broad phase hide a pair below the D-006 threshold."""
    layout = _layout(style, poles, phases)
    report = run_drc(layout, uniform_rules(RULE_MM))
    assert report is not None
    dump = parse_board_dump(json.loads(encode_board_dump(dump_layout(layout, case_id="pr-13"))))
    items = universe(dump, {"vias": [{"phase": 0}] * len(dump.vias)}, intended=False)
    exempt = (
        set(contract_exemptions(items, frozenset(layout.circuit.interconnect_path_ids)))
        | t_junction_pairs(items)
        | same_net_via_tap_pairs(items)
    )
    results = sweep(items, range(len(dump.layers)), lambda kind: RULE_MM, exempt)
    brute = {frozenset((r.a, r.b)) for r in results if r.verdict is Verdict.VIOLATION}
    engine = set(pair_violations(report))
    assert brute <= engine, (
        f"{len(brute - engine)} pairs below the threshold are not reported, e.g. {sorted(brute - engine)[:3]}"
    )
    if report.passed:
        assert not brute


def _scalars(layout: Layout) -> list[float]:
    report = run_drc(layout, uniform_rules(RULE_MM))
    assert report is not None
    return [s.least_clearance_mm for s in report.summaries if s.least_clearance_mm is not None]


@pytest.mark.parametrize("style", [s.value for s in WaveStyle])
@pytest.mark.parametrize("turn", [1.0, 1.0 / 3.0])
def test_pr_14_rotating_the_start_angle_leaves_ke_resistance_and_drc_values_unchanged(style: str, turn: float) -> None:
    """PR-14. Catches a generator whose result depends on the start angle: |Ke|, R and every DRC minimum are invariant.

    The rotation is one electrical period (360 / pole pairs degrees) times ``turn``. The phasor angle part of PR-14 is
    not tested: AnalysisResult has no per-phase phasor field yet (PR-07, D-034). The fundamental |Ke| is compared, not
    the peak of the synthesised waveform, which differs by 1.4e-8 relative on the overlap style because the peak is
    found on a sampled waveform whose phase moves with the rotation.
    """
    design = wave(WaveStyle(style), poles=8)
    _check_rotation(design, 360.0 / (design.rotor.poles // 2) * turn)


def _check_rotation(design: DesignParameters, degrees: float) -> None:
    """Compare the boards at 0 and ``degrees``, built and analysed with the designed-integer chord counts held equal.

    Ke, line Ke and the eddy loss sum the same chords, so they are compared at the round-off bound 2 (N + 10) u
    (DEF-UE16-01, D-054a); R and the DRC minima keep 1e-9.
    """
    with designed_integers_snapped():
        base = generate_wave_rotated(design, REGISTRY, 0.0)
        turned = generate_wave_rotated(design, REGISTRY, degrees)
        assert isinstance(base, BoardStack) and isinstance(turned, BoardStack)
        a, b = analyse(design, base, {}, REGISTRY), analyse(design, turned, {}, REGISTRY)
        rel = roundoff_rel(base, design.analysis.max_segment_mm)
    assert a is not None and b is not None
    for name in ("ke_phase_v_s_per_rad", "ke_line_v_s_per_rad", "loss_eddy_w"):
        assert getattr(b, name).value == pytest.approx(getattr(a, name).value, rel=rel), name
    assert b.resistance_phase_20c_ohm.value == pytest.approx(a.resistance_phase_20c_ohm.value, rel=1e-9)
    first, second = _scalars(base.boards[0]), _scalars(turned.boards[0])
    assert second == pytest.approx(first, abs=1e-9)
    assert math.isfinite(a.ke_line_v_s_per_rad.value) and a.ke_line_v_s_per_rad.value > 0.0


@pytest.mark.parametrize("ulps", [1, 4, 8])
def test_pr_14_overlap_keeps_ke_when_the_platform_rounds_the_rotation_differently(ulps: int) -> None:
    """DEF-UE16-01. Catches a Ke comparison that depends on the last bits of sin and cos (Windows UCRT against glibc).

    A rotation a few ulp off one electrical period stands in for another platform: it flips chord counts of the 54
    designed-integer primitives and moved Ke by 2.4e-10 to 4.4e-8 (U-E16 probe, pr14_and_reqf_texts.md section 1.3).
    """
    design = wave(WaveStyle.OVERLAP, poles=8)
    period_deg = 360.0 / (design.rotor.poles // 2)
    _check_rotation(design, period_deg + ulps * math.ulp(period_deg))
