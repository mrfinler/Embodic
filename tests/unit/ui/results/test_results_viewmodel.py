"""Result rows, the 'How was this computed' disclosure and Copy trace (UI-06, UI-07, UI-33). Qt-free."""

import dataclasses

import pytest

from embodic.results import QUANTITY_LABELS
from embodic.results.status import Status
from embodic.ui.viewmodels.results import (
    ResultsViewModel,
    disclosure,
    result_key,
    result_row,
    result_rows,
    trace_text,
)

SECTIONS = ["Equation", "Inputs", "Assumptions", "Limitations", "Validation state", "Sources"]


def rows_by_quantity(outcome):
    """Return the result rows of an outcome by quantity."""
    return {row.quantity: row for row in result_rows(outcome.analysis)}


@pytest.mark.req("REQ-T-01", "REQ-T-13", "REQ-F-13")
def test_ui06_every_row_shows_value_unit_and_the_badge_of_its_traceable(d08):
    """Catches a row without a unit, a badge not taken from the data, or a label typed into the UI."""
    rows = rows_by_quantity(d08)
    assert len(rows) == 30
    for quantity, row in rows.items():
        t = getattr(d08.analysis, quantity)
        assert row.value_text and row.unit_text, quantity
        assert row.status is t.status, quantity
        assert row.label == QUANTITY_LABELS[quantity]
        assert row.assumed_count == len(t.assumed_inputs)
        assert row.eq_ids == t.eq_ids
    assert (rows["ke_line_peak_v_s_per_rad"].value_text, rows["ke_line_peak_v_s_per_rad"].unit_text) == (
        "30.9",
        "mV·s/rad",
    )
    assert (rows["resistance_phase_operating_ohm"].value_text, rows["resistance_phase_operating_ohm"].unit_text) == (
        "502",
        "mΩ",
    )
    assert rows["winding_factor_1"].unit_text == "dimensionless"


@pytest.mark.req("REQ-T-01")
def test_ui06_a_card_title_carries_the_specification_symbol_only_where_one_is_stated(d08):
    """Catches a title without the symbol the spec states (R_ph) and one with a symbol the spec does not state."""
    rows = rows_by_quantity(d08)
    assert rows["resistance_phase_operating_ohm"].title == "Phase resistance at operating temperature R_ph"
    assert rows["ke_line_peak_v_s_per_rad"].title == "Line back-EMF constant, peak"
    assert rows["resistance_phase_operating_ohm"].label == "Phase resistance at operating temperature"


@pytest.mark.req("REQ-T-01")
def test_ui06_a_badge_follows_the_traceable_status_never_a_constant(d08):
    """Catches a hard-coded badge: changing only the traceable's status changes the row (D-007)."""
    t = d08.analysis.ke_phase_v_s_per_rad
    for status in Status:
        assert result_row("ke_phase_v_s_per_rad", dataclasses.replace(t, status=status)).status is status


@pytest.mark.req("REQ-T-01")
def test_ui06_negative_values_print_with_the_unicode_minus(d08):
    """Catches an ASCII hyphen or a lost sign on a negative result (REQ-L-07)."""
    t = dataclasses.replace(d08.analysis.torque_n_m, value=-0.0123)
    assert result_row("torque_n_m", t).value_text == "−12.3"


@pytest.mark.req("REQ-T-13", "REQ-T-01")
def test_ui06_disclosure_lists_equation_inputs_assumptions_limitations_validity_and_sources(d08, registry):
    """Catches a disclosure that drops a section, an input, an assumption or an evidence entry."""
    row = rows_by_quantity(d08)["resistance_phase_operating_ohm"]
    t = row.traceable
    sections = {s.title: s.lines for s in disclosure(row, registry)}
    assert list(sections) == SECTIONS
    assert sections["Equation"] == tuple(
        f"{eq}: {registry.equation(eq).name}. {registry.equation(eq).formula}" for eq in t.eq_ids
    )
    assert len(sections["Inputs"]) == len(t.inputs) > 0
    assert all("(" in line and " = " in line for line in sections["Inputs"])
    assert len(sections["Assumptions"]) == row.assumed_count
    assert [line.split(":")[0] for line in sections["Sources"]] == list(t.evidence_ids)
    assert sections["Validation state"][0].startswith(f"Status {t.status}: ")


@pytest.mark.req("REQ-T-16")
def test_ui33_ke_disclosure_states_e_edge_at_least_assumption_and_the_10_percent_cap(d08, registry):
    """Catches an EC-05 limitation that hides the lower bound, the assumption status or the cap."""
    row = rows_by_quantity(d08)["ke_phase_v_s_per_rad"]
    limitations = {s.title: s.lines for s in disclosure(row, registry)}["Limitations"]
    assert limitations == (
        "EC-05 radial edge leakage (graded): e_edge is at least 1.74\u00a0% (lower bound). Badge cap above 10\u00a0% "
        "(assumption). Calibration inferred; transfer to this design assumption.",
    )


@pytest.mark.req("REQ-F-11", "REQ-F-20", "REQ-T-05")
def test_ui07_estimates_show_their_label_and_the_unresolved_badge(d08):
    """Catches an EQ-14 or EQ-15 value shown without its estimate label or with a stronger badge."""
    rows = rows_by_quantity(d08)
    assert (rows["inductance_estimate_h"].status, rows["inductance_estimate_h"].estimate_label) == (
        Status.UNRESOLVED,
        "estimate",
    )
    assert (rows["ipc_guideline_current_a"].status, rows["ipc_guideline_current_a"].estimate_label) == (
        Status.UNRESOLVED,
        "guideline (unverified)",
    )


@pytest.mark.req("REQ-T-13")
def test_ui06_copy_trace_holds_the_row_and_every_disclosure_line(d08, registry):
    """Catches a copied trace that differs from what the disclosure shows."""
    vm = ResultsViewModel(registry)
    vm.show(d08.analysis, stale=False)
    trace = vm.copy_trace("inductance_estimate_h")
    row = vm.row("inductance_estimate_h")
    assert trace.splitlines()[0] == f"Inductance, estimate: {row.value_text} {row.unit_text} [unresolved] (estimate)"
    for section in disclosure(row, registry):
        assert f"{section.title}:" in trace
        for line in section.lines:
            assert f"  {line}" in trace
    assert trace == trace_text(row, registry)


@pytest.mark.req("REQ-T-01")
def test_ui06_status_filter_keeps_only_rows_with_a_chosen_badge(d08, registry):
    """Catches a filter that hides the wrong rows or keeps them all."""
    vm = ResultsViewModel(registry)
    vm.show(d08.analysis, stale=False)
    assert len(vm.rows.value) == 30
    vm.set_status_filter(frozenset({Status.UNRESOLVED}))
    assert {r.quantity for r in vm.rows.value} == {
        q for q, r in rows_by_quantity(d08).items() if r.status is Status.UNRESOLVED
    }
    assert {r.quantity for r in vm.rows.value} >= {"inductance_estimate_h", "ipc_guideline_current_a"}
    vm.show(None, stale=True)
    assert (vm.rows.value, vm.stale.value) == ((), False)


@pytest.mark.req("REQ-T-01")
def test_card_keys_keep_the_phase1_ids():
    """Catches a renamed Phase 1 key (screens.md section 6: r-phase, ke, kt, ls, dt, j)."""
    phase1 = ["resistance_phase_operating_ohm", "ke_phase_v_s_per_rad", "kt_n_m_per_a", "inductance_estimate_h"]
    phase1 += ["temperature_rise_k", "current_density_a_per_mm2"]
    assert [result_key(q) for q in phase1] == ["r-phase", "ke", "kt", "ls", "dt", "j"]
    assert result_key("loss_total_w") == "loss-total-w"
