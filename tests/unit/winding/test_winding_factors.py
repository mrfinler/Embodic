"""UT-WND-05 and UT-WND-11: distribution, turn-averaged pitch and winding factors as Traceable values (EQ-08)."""

import math
from typing import Any

import pytest

from embodic.results import Registry, Status, load_registry
from embodic.units import Unit
from embodic.winding import assign_phases, compute_winding_factors
from embodic.winding.winding_factors import distribution_factor, turn_averaged_pitch_factor

from .oracle import cf09_rows

pytestmark = [pytest.mark.req("REQ-F-02"), pytest.mark.eq("EQ-08")]

# A2-TOP §2.2 table (docs/phase1/engineering/topology_analysis.md), outermost-turn span 2π/Q, printed to 3 decimals.
A2_TOP_TABLE = (
    (12, 10, 0.933, 0.067, 0.067),
    (12, 14, 0.933, 0.067, 0.067),
    (12, 16, 0.866, 0.866, 0.866),
    (15, 16, 0.951, 0.173, 0.111),
    (18, 16, 0.945, 0.140, 0.061),
    (24, 16, 0.866, 0.866, 0.866),
    (9, 10, 0.945, 0.140, 0.061),
    (18, 20, 0.945, 0.140, 0.061),
)


@pytest.fixture(scope="module")
def registry() -> Registry:
    """Load the packaged equation registry; EQ-08 supplies status, sources and tolerance."""
    return load_registry()


def _outermost_turn(q: int, poles: int, harmonics: tuple[int, ...], registry: Registry) -> dict[int, float]:
    factors = compute_winding_factors(assign_phases(q, poles), poles, q, (2 * math.pi / q,), harmonics, registry)
    return {n: t.value for n, t in factors.items()}


@pytest.mark.parametrize(("q", "poles", "kw1", "kw5", "kw7"), A2_TOP_TABLE, ids=lambda v: str(v))
def test_ut_wnd_05_a2_top_table_as_printed(
    q: int, poles: int, kw1: float, kw5: float, kw7: float, registry: Registry
) -> None:
    """Catches a wrong k_d sum or pitch-factor argument: k_w1, k_w5, k_w7 match the printed table to 1e-3."""
    values = _outermost_turn(q, poles, (1, 5, 7), registry)
    assert [values[1], values[5], values[7]] == pytest.approx([kw1, kw5, kw7], abs=1e-3)


def test_ut_wnd_05_registry_reference_cases(registry: Registry) -> None:
    """EQ-08 reference cases of the registry: 12/10 k_w1 0.9330127; 12/16 k_w1, k_w3, k_w5 = 0.8660254, 0, 0.8660254."""
    assert _outermost_turn(12, 10, (1,), registry)[1] == pytest.approx(0.9330127, abs=5e-8)
    values = _outermost_turn(12, 16, (1, 3, 5), registry)
    assert [values[1], values[3], values[5]] == pytest.approx([0.8660254, 0.0, 0.8660254], abs=5e-8)


@pytest.mark.parametrize("row", cf09_rows(), ids=lambda r: f"{r['Q']}-{r['poles']}")
def test_ut_wnd_05_cf09_distribution_factor(row: dict[str, Any]) -> None:
    """Catches a k_d that uses mechanical angles or the wrong phase set: k_d1 equals CF-09 to 1e-9."""
    assignment = assign_phases(row["Q"], row["poles"])
    assert distribution_factor(assignment, 1, row["Q"]) == pytest.approx(row["kd1"], abs=1e-9)


@pytest.mark.parametrize(
    ("q", "poles", "expected"), [(12, 16, math.sin(math.radians(120))), (12, 10, math.sin(math.radians(75)))]
)
def test_ut_wnd_11a_single_turn_limit_is_the_coil_pitch_factor(q: int, poles: int, expected: float) -> None:
    """Catches a missing factor p or 1/2 in the pitch-factor argument: N = 1, d = 0 gives |sin(p θ_cp / 2)|."""
    assert turn_averaged_pitch_factor(1, poles, (2 * math.pi / q,)) == pytest.approx(expected, abs=1e-9)
    assert expected == pytest.approx({16: 0.8660254, 10: 0.9659258}[poles], abs=1e-7)


def _example_turn_spans(turns: int, radius_mm: float) -> tuple[float, ...]:
    """Return sigma_t = θ_cp − 2 asin(d_t / r), 12 coils, example offsets d_t = gap/2 + w/2 + t (w + s) (D15 eq. 6)."""
    gap_mm, w_mm, s_mm = 0.2, 0.5, 0.2
    return tuple(
        2 * math.pi / 12 - 2 * math.asin((gap_mm / 2 + w_mm / 2 + t * (w_mm + s_mm)) / radius_mm) for t in range(turns)
    )


@pytest.mark.parametrize("harmonic", [1, 5, 7])
def test_ut_wnd_11bc_turn_average_equals_mean_of_per_turn_values(harmonic: int) -> None:
    """Catches averaging the span before the sine: 12/16, N = 8 at mean radius 28 mm, to 1e-12 per harmonic."""
    spans = _example_turn_spans(8, 28.0)
    per_turn = [abs(math.sin(harmonic * 8 * sigma / 2)) for sigma in spans]
    sine_of_mean_span = abs(math.sin(harmonic * 8 * (sum(spans) / 8) / 2))
    average = turn_averaged_pitch_factor(harmonic, 16, spans)
    assert average == pytest.approx(sum(per_turn) / len(per_turn), abs=1e-12)
    assert average != pytest.approx(sine_of_mean_span, abs=1e-6)


def test_winding_factor_is_traceable_to_eq_08(registry: Registry) -> None:
    """Catches an untraced number: each k_w,n names EQ-08, its evidence, Q and 2p, and equals k_d,n times k_p,n."""
    spans = _example_turn_spans(8, 28.0)
    assignment = assign_phases(12, 16)
    factors = compute_winding_factors(assignment, 16, 12, spans, (1, 3), registry)
    first = factors[1]
    assert sorted(factors) == [1, 3]
    assert (first.quantity, first.unit, first.eq_ids) == ("winding_factor_1", Unit.ONE, ("EQ-08",))
    assert first.evidence_ids == registry.equation("EQ-08").sources
    assert {(i.pointer, i.value) for i in first.inputs} >= {("/winding/coil/coil_count", 12), ("/rotor/poles", 16)}
    assert first.value == pytest.approx(
        distribution_factor(assignment, 1, 12) * turn_averaged_pitch_factor(1, 16, spans)
    )
    assert first.status in (Status.INFERRED, Status.NOT_TESTED)
