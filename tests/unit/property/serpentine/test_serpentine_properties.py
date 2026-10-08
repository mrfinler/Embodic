"""PR-13 (DRC never under-reports) and PR-14 (rotation symmetry) for the serpentine generator (REQ-F-34)."""

import cmath
import math
from collections.abc import Callable, Sequence

import numpy as np
import pytest
from brute_clearance import Verdict
from drc_universe import Cls, Item, contract_exemptions, sweep
from hypothesis import assume, given, settings
from hypothesis import strategies as st
from records import Arc as OwnArc
from records import Line as OwnLine
from records import disc
from tests.unit.generators.serpentine.make_example import example_design
from tests.unit.generators.serpentine.support import with_winding
from tests.unit.property.t_junctions import same_net_via_tap_pairs, t_junction_pairs

from embodic.drc import DrcReport, run_drc
from embodic.generators import build_layout
from embodic.geometry.layout import BoardStack, Layout
from embodic.geometry.primitives import Arc, PrimitiveRole
from embodic.model.design import DesignParameters
from embodic.model.provenance import derive_provenance
from embodic.model.winding_specs import CornerStyle, SerpentineWindingSpec
from embodic.physics import analyse
from embodic.results import load_registry

from .strategies import serpentine_designs

pytestmark = pytest.mark.req("REQ-F-34")
REGISTRY = load_registry()
EXAMPLES = 3
# Fractions of an electrical period: whole periods, one pole pitch (half a period) and others.
PERIOD_FRACTIONS = [1.0, 0.5, 0.25, -0.75, 0.37]
PAIR_KINDS = {"trace_trace", "trace_via", "via_via", "pad_trace", "pad_pad"}
CORNERS = {PrimitiveRole.FILLET, PrimitiveRole.TAPER}
KE_REL_TOL = 1e-8  # D-036 c; the reason is in the _check_rotation docstring


def _stack(design: DesignParameters) -> BoardStack:
    """Return the built boards; a design Xcoil's fit checks refuse is not a counter-example, so it is skipped."""
    stack = build_layout(design, REGISTRY)
    assume(isinstance(stack, BoardStack))
    assert isinstance(stack, BoardStack)
    return stack


def _built(design: DesignParameters) -> BoardStack:
    stack = build_layout(design, REGISTRY)
    assert isinstance(stack, BoardStack), stack
    return stack


def _items(layout: Layout) -> list[Item]:
    """Agent 4's universe items for the copper of one board, labelled as run_drc labels them."""
    layer_of = {name: i for i, name in enumerate(layout.copper_layers)}
    items: list[Item] = []
    for path in layout.paths:
        for k, p in enumerate(path.primitives):
            prim = (
                OwnArc(p.cx_mm, p.cy_mm, p.r_mm, p.start_rad, p.sweep_rad, p.width_mm)
                if isinstance(p, Arc)
                else OwnLine(p.x1_mm, p.y1_mm, p.x2_mm, p.y2_mm, p.width_mm)
            )
            items.append(Item(f"path:{path.id}/prim:{k}", Cls.TRACE, prim, layer_of[path.layer], path.net, path.id, k,
                              p.role in CORNERS))  # fmt: skip
    items += [Item(f"via:{v.id}", Cls.VIA, disc(v.x_mm, v.y_mm, v.pad_mm), None, v.net) for v in layout.vias]
    items += [
        Item(
            f"pad:{p.id}",
            Cls.PAD,
            disc(p.x_mm, p.y_mm, p.width_mm),
            None if p.drill_mm > 0 else layer_of[p.layer or ""],
            p.net,
        )
        for p in layout.pads
    ]
    return items


def _reported(report: DrcReport) -> set[frozenset[str]]:
    assert report.violation_count == len(report.violations), "report truncated"
    return {frozenset(v.objects) for v in report.violations if v.kind.value in PAIR_KINDS}


def _check_against_the_brute_sweep(design: DesignParameters, stack: BoardStack) -> int:
    """Compare run_drc with Agent 4's sweep on every board; return the number of pairs the sweep found."""
    rule, total = design.drc_rules.trace_clearance_mm, 0
    for layout in stack.boards:
        report = run_drc(layout, design.drc_rules)
        assert report is not None
        items = _items(layout)
        exempt = (
            set(contract_exemptions(items, layout.circuit.interconnect_path_ids))
            | t_junction_pairs(items)
            | same_net_via_tap_pairs(items)
        )
        results = [
            r for r in sweep(items, range(len(layout.copper_layers)), lambda kind: rule, exempt) if r.kind in PAIR_KINDS
        ]
        found = {frozenset((r.a, r.b)) for r in results if r.verdict is Verdict.VIOLATION}
        undecided = {frozenset((r.a, r.b)) for r in results if r.verdict is Verdict.UNDECIDED}
        reported = _reported(report)
        assert found - undecided <= reported, sorted(map(sorted, found - reported))
        assert reported - found <= undecided, sorted(map(sorted, reported - found))
        assert not (report.passed and found)
        total += len(found)
    return total


@pytest.mark.slow
@settings(max_examples=EXAMPLES, deadline=None)
@given(design=serpentine_designs())
def test_pr_13_drc_never_under_reports_on_serpentine_boards(design: DesignParameters) -> None:
    """PR-13. Catches a pair the DRC skips or invents: Agent 4's brute sweep and run_drc agree on every board.

    A passing board has no pair below rule - 1e-6 mm. The exemptions are coded in tests/independent/m1/drc_universe.py
    from interfaces.md section 7, not from embodic.
    """
    _check_against_the_brute_sweep(design, _stack(design))


def test_pr_13_the_sweep_finds_the_violations_of_a_two_strand_board() -> None:
    """PR-13 power check. Catches a vacuous property: two strands put the bus against the strand ends (XD-SER-002)."""
    design = with_winding(example_design(), strands=2, turns=2)
    assert _check_against_the_brute_sweep(design, _built(design)) > 0


def _first_phase_angle_rad(waveform: Sequence[float]) -> float:
    """Angle of the fundamental of a phase EMF waveform; the last sample repeats the first."""
    return cmath.phase(np.fft.fft(np.array(waveform)[:-1])[1])


def _measures(design: DesignParameters, stack: BoardStack) -> tuple[float, float, float, dict[str, float]]:
    """Return the first phase angle, the mean Ke, the mean R and the smallest DRC clearance per kind."""
    analysis = analyse(design, stack, derive_provenance(design, None, ()), REGISTRY)
    assert analysis is not None
    drc: dict[str, float] = {}
    for layout in stack.boards:
        report = run_drc(layout, design.drc_rules)
        assert report is not None
        for s in report.summaries:
            if s.measured_min_mm is not None:
                drc[s.kind.value] = min(drc.get(s.kind.value, math.inf), s.measured_min_mm)
    ke = math.fsum(p.ke_peak_v_s_per_rad.value for p in analysis.phases) / len(analysis.phases)
    return (
        _first_phase_angle_rad(analysis.emf_waveform_v.value),
        ke,
        analysis.resistance_phase_operating_ohm.value,
        drc,
    )


def _check_rotation(
    design: DesignParameters, fraction: float, build: Callable[[DesignParameters], BoardStack] = _built
) -> None:
    """Rotate the start angle by ``fraction`` of an electrical period and compare the two boards.

    Ke is compared at KE_REL_TOL (1e-8) and not 1e-9: when a side line is a whole number of 0.5 mm chords, rotation
    moves its computed length by one ulp, ``ceil`` flips the chord count by one, and Ke moved by 8.5e-9 relative in
    the DEF-M3a-02 counter-example (test_plan.md PR-14 branch B). R, the phasor angle and the DRC values keep 1e-9.
    """
    pole_pairs = design.rotor.poles // 2
    delta = fraction * 2.0 * math.pi / pole_pairs
    assert isinstance(design.winding, SerpentineWindingSpec)
    rotated = with_winding(design, start_angle_rad=design.winding.start_angle_rad + delta)
    angle0, ke0, r0, drc0 = _measures(design, build(design))
    angle1, ke1, r1, drc1 = _measures(rotated, build(rotated))
    assert abs(math.remainder(angle1 - angle0 + pole_pairs * delta, 2.0 * math.pi)) <= 1e-9
    assert ke1 == pytest.approx(ke0, rel=KE_REL_TOL)
    assert r1 == pytest.approx(r0, rel=1e-9)
    assert drc1.keys() == drc0.keys()
    for kind, value in drc0.items():
        assert drc1[kind] == pytest.approx(value, abs=1e-9)


@pytest.mark.slow
@settings(max_examples=EXAMPLES, deadline=None)
@given(design=serpentine_designs(corners=(CornerStyle.ROUND,)), fraction=st.sampled_from(PERIOD_FRACTIONS))
def test_pr_14_rotating_the_start_angle_shifts_the_phasor_and_keeps_ke_r_and_drc(
    design: DesignParameters, fraction: float
) -> None:
    """PR-14. Catches a copper position that depends on the start angle: Ke, R and the DRC values must not change.

    Rotating by delta moves the phase EMF by pole_pairs x delta electrical (numpy's fft angle gives the delay, as in
    PR-06). One electrical period is 2 pi / pole_pairs of mechanical angle and leaves the phasor where it was.
    """
    _check_rotation(design, fraction, _stack)


@pytest.mark.parametrize("fraction", PERIOD_FRACTIONS)
def test_pr_14_the_default_preset_follows_the_rotation(fraction: float) -> None:
    """PR-14 power check. Catches a start angle that is ignored: the phasor must move by pole_pairs x delta."""
    _check_rotation(example_design(), fraction)


def test_pr_14_counter_example_sharp_corners_with_one_turn() -> None:
    """PR-14 counter-example found by Hypothesis (DEF-M3a-02): Ke moves by 8.5e-9 relative, inside KE_REL_TOL.

    The 18 mm sharp side lines are exactly 36 chords of 0.5 mm. Rotating moves their computed length by one ulp, so
    ``ceil`` gives 36 or 37 chords, and the two valid discretisations differ by that much. It is a chord-count flip,
    not a rotation defect.
    """
    design = with_winding(example_design(), turns=1, corner_style=CornerStyle.SHARP)
    _check_rotation(design, 1.0)
