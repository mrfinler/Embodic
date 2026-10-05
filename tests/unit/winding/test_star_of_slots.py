"""UT-WND-01, -02, -03, -06, -10: exact star of slots, feasibility rule, q and t, balanced coil counts (EQ-08)."""

import math
from fractions import Fraction
from typing import Any

import pytest

from embodic.model.vocabulary import Phase
from embodic.model.winding_specs import PhaseSequence
from embodic.winding import CoilAssignment, assign_phases, balanced_coil_counts, check_feasibility

from .oracle import cf09_rows

pytestmark = [pytest.mark.req("REQ-F-02"), pytest.mark.eq("EQ-08")]

XCOIL_BELT_EDGE_CASES = ((12, 14), (24, 14), (24, 22), (24, 26))


def _pattern(assignment: tuple[CoilAssignment, ...]) -> str:
    return "".join(c.phase.value if c.polarity == 1 else c.phase.value.lower() for c in assignment)


def _cf09(q: int, poles: int) -> dict[str, Any]:
    return next(r for r in cf09_rows() if (r["Q"], r["poles"]) == (q, poles))


def _xcoil_float_star_of_slots(q: int, poles: int) -> tuple[str, bool]:
    """Port of Xcoil engine.js `starOfSlots` l.1899-1918 for m = 3: float belts and a 1e-6 balance check (defect C6)."""
    pp = poles // 2
    alpha = 2 * math.pi * pp / q
    coils = []
    for k in range(q):
        a = math.fmod(k * alpha, 2 * math.pi)
        sector = math.floor(math.fmod(a + math.pi / 6, 2 * math.pi) / (math.pi / 3))
        coils.append(([0, 2, 1][sector % 3], 1 if sector % 2 == 0 else -1, a))
    sums = [[0.0, 0.0] for _ in range(3)]
    counts = [0, 0, 0]
    for phase, sign, a in coils:
        counts[phase] += 1
        sums[phase][0] += sign * math.cos(a)
        sums[phase][1] += sign * math.sin(a)
    mags = [math.hypot(x, y) for x, y in sums]
    ok = q % 3 == 0 and (q // math.gcd(q, pp)) % 3 == 0
    ok = ok and all(counts[i] == counts[0] and abs(mags[i] - mags[0]) <= 1e-6 * max(1.0, mags[0]) for i in range(3))
    pattern = "".join("ABC"[ph] if s > 0 else "abc"[ph] for ph, s, _ in coils)
    return pattern, ok


def test_ut_wnd_01_12_10_pattern_equals_d08_fig_3_7() -> None:
    """Catches a wrong belt order or sign: 12/10 must read AabBCcaABbcC (D08 p.36 Fig. 3.7, CF-09)."""
    assert _pattern(assign_phases(12, 10)) == "AabBCcaABbcC" == _cf09(12, 10)["pattern"]


def test_ut_wnd_02_xcoil_float_ties_reject_the_belt_edge_cases() -> None:
    """Shows the defect is real: Xcoil's float star of slots reports these four combinations unbalanced (C6)."""
    assert [_xcoil_float_star_of_slots(q, poles)[1] for q, poles in XCOIL_BELT_EDGE_CASES] == [False] * 4


@pytest.mark.parametrize(("q", "poles"), XCOIL_BELT_EDGE_CASES, ids=lambda v: str(v))
def test_ut_wnd_02_belt_edge_combinations_are_balanced(q: int, poles: int) -> None:
    """Catches a reintroduced float-tie star of slots: belt-edge phasors must go to the belt that starts there."""
    feasibility = check_feasibility(q, poles)
    assignment = assign_phases(q, poles)
    counts = [sum(1 for c in assignment if c.phase is phase) for phase in Phase]
    assert feasibility.balanced
    assert counts == [q // 3] * 3
    assert _pattern(assignment) == _cf09(q, poles)["pattern"]
    assert _pattern(assignment) != _xcoil_float_star_of_slots(q, poles)[0]


def test_ut_wnd_03_12_16_pattern_all_positive() -> None:
    """Catches a polarity or sequence error on the default example: 12/16 is ACB repeated, every coil positive."""
    assignment = assign_phases(12, 16)
    assert _pattern(assignment) == "ACBACBACBACB"
    assert {c.polarity for c in assignment} == {1}


@pytest.mark.parametrize("row", cf09_rows(), ids=lambda r: f"{r['Q']}-{r['poles']}")
def test_cf09_patterns_and_balance(row: dict[str, Any]) -> None:
    """Every CF-09 oracle row: exact pattern, exact balance and the feasibility pre-check agree with the oracle file."""
    assert _pattern(assign_phases(row["Q"], row["poles"])) == row["pattern"]
    assert check_feasibility(row["Q"], row["poles"]).balanced is row["balanced_exact"]


def test_phasor_index_is_the_exact_electrical_position() -> None:
    """Catches a phasor index taken in mechanical instead of electrical steps: coil k sits at (k p mod Q) 2pi/Q."""
    assert [c.phasor_index for c in assign_phases(12, 10)] == [(k * 5) % 12 for k in range(12)]


def test_acb_sequence_swaps_b_and_c() -> None:
    """Catches a sequence option that is ignored: ACB must exchange the B and C belts and nothing else."""
    swap = {Phase.A: Phase.A, Phase.B: Phase.C, Phase.C: Phase.B}
    abc = assign_phases(12, 10, sequence=PhaseSequence.ABC)
    acb = assign_phases(12, 10, sequence=PhaseSequence.ACB)
    assert [(swap[c.phase], c.polarity) for c in abc] == [(c.phase, c.polarity) for c in acb]


def test_ut_wnd_06_q_is_an_exact_fraction_and_t_is_gcd() -> None:
    """Catches a float q or a periodicity taken from 2p instead of p, for every Q <= 48 and 2p <= 48."""
    for q in range(1, 49):
        for poles in range(2, 49, 2):
            feasibility = check_feasibility(q, poles)
            assert feasibility.q == Fraction(q, 3 * poles)
            assert type(feasibility.q) is Fraction
            assert feasibility.periodicity == math.gcd(q, poles // 2)


def test_ut_wnd_06_rule_and_exact_balance_agree_for_every_small_combination() -> None:
    """The exact phasor check confirms the textbook rule Q/(m t) integer wherever Q != 2p (EQ-08 assumption G24)."""

    def rule(q: int, poles: int) -> bool:
        return q % 3 == 0 and (q // math.gcd(q, poles // 2)) % 3 == 0

    disagreements = [
        (q, poles)
        for q in range(3, 49)
        for poles in range(2, 49, 2)
        if q != poles and check_feasibility(q, poles).balanced != rule(q, poles)
    ]
    assert disagreements == []


def test_feasibility_reports_the_12_16_numbers() -> None:
    """Catches swapped fields: 12/16 has q = 1/4, t = 4 and at most t parallel paths (A2-TOP section 2.2 table)."""
    feasibility = check_feasibility(12, 16)
    assert (feasibility.coils, feasibility.poles, feasibility.phases) == (12, 16, 3)
    assert (feasibility.q, feasibility.periodicity, feasibility.max_parallel_paths) == (Fraction(1, 4), 4, 4)


def test_ut_wnd_10_balanced_coil_counts_for_14_poles_include_12_and_24() -> None:
    """Catches the Xcoil balancedSectorList regression (C6): 12 and 24 coils with 14 poles are balanced."""
    counts = balanced_coil_counts(14)
    assert {12, 24} <= set(counts)
    assert counts == tuple(sorted(counts))
    assert all(check_feasibility(q, 14).balanced for q in counts)
    assert all(not check_feasibility(q, 14).balanced for q in set(range(1, 97)) - set(counts))
