"""Items 3 to 6 (U-V3): own-field Ke on ported layouts, the two examples against Xcoil compute(), V8 vs glibc ulps."""

import pytest
from cases import have_xcoil
from examples_m3 import embodic, rows, xcoil
from gr22_own import embodic_ke_ll_peak, own_ke_ll_peak
from subject import stack_for
from ulp import measure

pytestmark = [
    pytest.mark.req("REQ-F-34", "REQ-F-35", "REQ-F-11"),
    pytest.mark.skipif(not have_xcoil(), reason="needs node and the read-only Xcoil engine"),
]

# Own chords (0.05 mm, 7 harmonics) against embodic's field table: measured -1.0e-4 and -2.0e-5 on these layouts;
# M2's OR-01 gap was -3.8e-5. A z off by one copper thickness moves Ke by about 1e-3, so 3e-4 still catches it.
OWN_FIELD_REL = 3e-4


@pytest.mark.parametrize("case_id", ["s-radial-t4", "w-involute-p20-l2-m3"])
def test_gr22_ke_from_own_field(case_id: str) -> None:
    """Item 4: catches a field, z, phase-sum or path-direction change in physics on a ported layout."""
    assert embodic_ke_ll_peak(case_id) / own_ke_ll_peak(case_id) - 1 == pytest.approx(0, abs=OWN_FIELD_REL)


def test_per_phase_stack_ke_uses_the_board_z() -> None:
    """Item 3: Ke of a per-phase stack must use each board's own z (DEF-M3a-01: +5.1 % on 72b3231, now closed)."""
    case_id = "s-perphase-3-t5-gap0p3"
    assert embodic_ke_ll_peak(case_id) / own_ke_ll_peak(case_id) - 1 == pytest.approx(0, abs=OWN_FIELD_REL)


def test_def_m3a_01_cause_is_the_doubled_board_offset() -> None:
    """Item 3 diagnosis: moving board k by a further k x pitch in the own model reproduces embodic's Ke."""
    case_id = "s-perphase-3-t5-gap0p3"
    stack = stack_for(case_id)
    pitch = stack.board_thickness_mm + stack.board_gap_mm
    subject = embodic_ke_ll_peak(case_id)
    if abs(subject / own_ke_ll_peak(case_id) - 1) <= OWN_FIELD_REL:
        pytest.skip("DEF-M3a-01 fixed on this head; the diagnosis no longer applies")
    assert subject / own_ke_ll_peak(case_id, z_shift_per_board_mm=pitch) - 1 == pytest.approx(0, abs=OWN_FIELD_REL)


def _row(example_id: str, name: str) -> tuple[float, float]:
    (row,) = [(e, x) for n, e, x in rows(example_id) if n.startswith(name)]
    return row


@pytest.mark.parametrize("example_id", ["serpentine_16p_example", "wave_16p_example"])
def test_example_ke_fundamental_equals_xcoil(example_id: str) -> None:
    """Item 5: Xcoil's Ke1 and keLinePk are fundamentals; embodic's phase and line fundamentals must equal them."""
    for name in ("Ke phase fundamental", "Ke line fundamental"):
        e, x = _row(example_id, name)
        assert e == pytest.approx(x, rel=1e-9)


@pytest.mark.parametrize("example_id", ["serpentine_16p_example", "wave_16p_example"])
def test_example_line_peak_is_below_the_fundamental(example_id: str) -> None:
    """Item 5: embodic's waveform peak is a different quantity (fundamental vs peak); flat-topped EMF peaks lower."""
    peak, fundamental = _row(example_id, "Ke line waveform peak")
    assert 0.95 * fundamental < peak < fundamental


def test_example_resistance_differs_only_by_the_named_causes() -> None:
    """Item 5: serpentine +0.396 % (XD-PHY-003, vbus copper; via barrels); wave +0.278 % (D-035 e, via length)."""
    s_e, s_x = _row("serpentine_16p_example", "R phase")
    w_e, w_x = _row("wave_16p_example", "R phase")
    assert s_e / s_x - 1 == pytest.approx(3.957e-3, abs=2e-5)
    assert w_e / w_x - 1 == pytest.approx(2.781e-3, abs=2e-5)


def test_serpentine_example_interconnect_loss_equals_xcoil() -> None:
    """Item 5: catches a lead, link or ring segment dropped from P_ic."""
    e, x = _row("serpentine_16p_example", "P_ic")
    assert e == pytest.approx(x, rel=1e-3)


def test_wave_example_interconnect_loss_equals_xcoil() -> None:
    """Item 5: catches a lead, link or ring segment dropped from P_ic on the wave example (DEF-UV3-02, -77 % before)."""
    e, x = _row("wave_16p_example", "P_ic")
    assert e == pytest.approx(x, rel=1e-3)


def test_example_drc_counts() -> None:
    """Item 5: serpentine clean on both; wave violations only where Xcoil's 4 um slack hides them or on copper.

    The copper exception is interconnect paths, which the in-flight U-M3-fix changes (star split, T-junction rule).
    """
    assert [r.violation_count for r in embodic("serpentine_16p_example").drc] == [0]
    assert xcoil("serpentine_16p_example")["drcIssues"] == xcoil("wave_16p_example")["drcIssues"] == 0
    out = embodic("wave_16p_example")
    (report,) = out.drc
    interconnect = {f"path:{i}" for i in out.boards.boards[0].circuit.interconnect_path_ids}
    rule = xcoil("wave_16p_example")["params"]["clearance"]
    unexplained = [
        v
        for v in report.violations
        if not (rule - 0.004 <= v.clearance_mm < rule) and not any(o.split("/")[0] in interconnect for o in v.objects)
    ]
    assert report.violation_count == len(report.violations) > 0
    assert unexplained == []


def test_v8_and_glibc_trig_differ_by_at_most_one_ulp() -> None:
    """Item 6: D-035 f signs off 1-ulp differences; a 2-ulp or larger gap would void GR-21's 1e-9 mm basis."""
    for name, (worst, count, _) in measure().items():
        assert worst <= 1, name
        assert count < 1000, name
