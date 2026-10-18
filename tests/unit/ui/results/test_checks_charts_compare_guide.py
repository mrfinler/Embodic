"""DRC table, chart models, comparison and the equation register (UI-10, UI-17, UI-30, UI-34). Qt-free."""

import cmath
import dataclasses
import math

import numpy as np
import pytest

from embodic.errors import message_for
from embodic.model.vocabulary import Phase
from embodic.results.status import Status
from embodic.ui.viewmodels.results import (
    START_TOPIC,
    CompareViewModel,
    back_emf_chart,
    compare_chart,
    compare_rows,
    drc_table,
    equation_topic,
    guide_groups,
    nice_ticks,
    result_rows,
    tick_text,
    topic_for,
    torque_speed_charts,
)


@pytest.mark.req("REQ-F-33")
def test_drc_table_of_the_wave_example_lists_every_failure_with_catalogue_text(wave):
    """Catches a summary that disagrees with the rows, or measured and required values that print alike."""
    table = drc_table(wave)
    assert (table.state, table.summary, table.failure_count) == ("fail", "DRC: 186 failures, 0 warnings", 186)
    assert len(table.rows) == 186 and table.note is None
    first = table.rows[0]
    assert (first.number, first.rule_code, first.layer_text) == (1, "DRC_TRACE_TRACE", "L1")
    assert first.message == message_for("DRC_TRACE_TRACE")
    assert (first.clearance_text, first.required_text) == ("0.199965\u00a0mm", "0.200000\u00a0mm")
    assert first.at_mm == wave.drc[0].violations[0].at_mm


@pytest.mark.req("REQ-F-33")
def test_drc_table_of_a_passing_design_says_passed(d08):
    """Catches a pass shown as failures or an empty state after a compute."""
    table = drc_table(d08)
    assert (table.state, table.summary, table.rows) == ("pass", "DRC: passed, no failures", ())
    assert drc_table(None) is None


@pytest.mark.req("REQ-F-33")
def test_drc_table_of_a_stack_names_every_board_and_lists_failures_whatever_the_picker_shows(wave):
    """Catches a summary without the per-board verdicts, a failure row without its board, or a hidden board."""
    report = wave.drc[0]
    clean = dataclasses.replace(report, passed=True, violations=(), violation_count=0)
    two = dataclasses.replace(report, violations=report.violations[:2], violation_count=2)
    table = drc_table(dataclasses.replace(wave, drc=(clean, two, clean)))
    assert table.summary == "DRC: 2 failures, 0 warnings. Board A pass, Board B 2 failures, Board C pass."
    assert table.boards == (Phase.A, Phase.B, Phase.C)
    assert [(row.board, row.board_text) for row in table.rows] == [(2, "B"), (2, "B")]
    one = dataclasses.replace(report, violations=report.violations[:1], violation_count=1)
    assert "Board A 1 failure," in drc_table(dataclasses.replace(wave, drc=(one, clean))).summary
    assert drc_table(dataclasses.replace(wave, drc=(clean, clean))).summary.endswith(
        "DRC: passed, no failures. Board A pass, Board B pass."
    )


@pytest.mark.req("REQ-F-33")
def test_drc_table_of_one_board_has_no_board_column_text(wave, d08):
    """Catches a Board letter or a per-board sentence on a design that has one board."""
    table = drc_table(wave)
    assert table.boards == () and {row.board_text for row in table.rows} == {""}
    assert drc_table(d08).summary == "DRC: passed, no failures"


def fundamental(waveform):
    """Return the n = 1 phasor of one period sampled with both ends included (independent DFT)."""
    samples = np.asarray(waveform[:-1])
    theta = 2 * math.pi * np.arange(samples.size) / samples.size
    return 2 * complex(np.mean(samples * np.cos(theta)), -np.mean(samples * np.sin(theta)))


@pytest.mark.req("REQ-N-25")
def test_ui30_back_emf_chart_has_three_phases_one_unit_and_the_badge_of_its_data(d08):
    """Catches a chart with a second unit, a missing phase, a wrong period or a curve not from the result's data."""
    chart = back_emf_chart(d08)
    assert (chart.chart_id, chart.y_unit, chart.x_unit) == ("chart-backemf", "V", "°")
    assert [(s.phase, s.label) for s in chart.series] == [(p, f"Phase {p.value}") for p in Phase]
    assert (len(chart.xs), chart.xs[0], chart.xs[-1]) == (181, 0.0, 360.0)
    analysis = d08.analysis
    assert chart.status is analysis.emf_waveform_v.status
    assert chart.eq_ids[:2] == ("EQ-18", "EQ-07")
    result_a = fundamental(analysis.emf_waveform_v.value)
    chart_a = fundamental(chart.series[0].ys)
    assert abs(chart_a - result_a) < 1e-9 * abs(result_a)
    omega = 1000.0 * 2 * math.pi / 60
    for series, phase in zip(chart.series, analysis.phases, strict=True):
        expected = cmath.rect(phase.ke_peak_v_s_per_rad.value * omega, phase.emf_phasor_angle_rad.value)
        assert abs(fundamental(series.ys) - expected) < 1e-9 * abs(expected)


@pytest.mark.req("REQ-N-25", "REQ-F-20")
def test_ui30_ui07_torque_and_power_are_two_charts_sharing_the_rpm_axis_with_the_estimate_label(d08, serpentine):
    """Catches torque and power on one chart (two units) or an EQ-20 curve shown without its estimate label."""
    assert torque_speed_charts(d08) is None
    torque, power = torque_speed_charts(serpentine)
    ts = serpentine.analysis.torque_speed
    assert (torque.chart_id, torque.y_unit, power.chart_id, power.y_unit) == (
        "chart-torque-speed",
        "N·m",
        "chart-power-speed",
        "W",
    )
    assert torque.xs == power.xs == ts.speed_rpm.value
    assert torque.x_unit == power.x_unit == "rpm"
    assert torque.series[0].ys == ts.torque_n_m.value and power.series[0].ys == ts.power_w.value
    assert (torque.status, torque.estimate_label) == (Status.UNRESOLVED, "estimate")
    assert power.status is Status.UNRESOLVED


@pytest.mark.req("REQ-N-25")
@pytest.mark.parametrize(
    ("lo", "hi", "ticks"),
    [
        (0.0, 1.95, (0.0, 0.5, 1.0, 1.5, 2.0)),
        (-1.95, 1.95, (-2.0, -1.0, 0.0, 1.0, 2.0)),
        (0.0, 0.0, (-1.0, -0.5, 0.0, 0.5, 1.0)),
    ],
)
def test_ticks_are_round_and_cover_the_range(lo, hi, ticks):
    """Catches ticks that leave data outside the axis or land on unround values."""
    assert nice_ticks(lo, hi) == ticks


@pytest.mark.req("REQ-L-07")
def test_tick_labels_use_the_unicode_minus():
    """Catches an ASCII hyphen on a negative tick."""
    assert (tick_text(-0.5), tick_text(2.0), tick_text(0.0)) == ("−0.5", "2", "0")


@pytest.mark.req("REQ-F-17", "REQ-L-08")
def test_ui10_compare_current_column_equals_the_single_design_results(d08, spiral_14p):
    """Catches a comparison that recomputes or reformats a value differently from the Results tab.

    A cell joins number and unit with U+00A0 (ruling e1); a unitless value is the number alone (D-043c: no Unit column).
    """

    def cell(single):
        unit = single.traceable.unit.display()
        return f"{single.value_text}\u00a0{single.unit_text}" if unit else single.value_text

    rows = {r.quantity: r for r in compare_rows(d08, spiral_14p)}
    for single in result_rows(spiral_14p.analysis):
        assert rows[single.quantity].current_text == cell(single)
    for single in result_rows(d08.analysis):
        assert rows[single.quantity].reference_text == cell(single)
    assert rows["winding_factor_1"].current_text.replace(".", "").isdigit(), "a unitless cell is the number alone"


@pytest.mark.req("REQ-L-08")
def test_ui34_counts_are_integers_and_deltas_carry_sign_and_direction(d08, spiral_14p):
    """Catches a count printed with decimals, a delta without its sign, or a direction that contradicts the sign."""
    rows = {r.quantity: r for r in compare_rows(d08, spiral_14p)}
    for key in ("copper-layers", "coils", "vias", "drc-failures"):
        row = rows[key]
        assert row.reference_text.isdigit() and row.current_text.isdigit(), key
        assert "." not in row.delta_text
    for row in rows.values():
        sign = row.delta_text[0]
        expected = {"+": "up", "−": "down"}.get(sign, "same")
        assert row.direction == expected, row
        assert row.direction != "same" or row.delta_text.split()[0] == "0"
    same = compare_rows(d08, d08)
    assert {(r.direction, r.delta_text.split()[0]) for r in same} == {("same", "0")}


@pytest.mark.req("REQ-F-17")
def test_compare_reference_needs_confirmation_only_when_one_is_stored(d08, spiral_14p):
    """Catches a reference replaced without asking, or a first reference that asks."""
    vm = CompareViewModel()
    assert not vm.needs_confirmation()
    vm.set_reference(d08)
    assert vm.needs_confirmation() and vm.reference.value is d08
    chart = compare_chart(d08, spiral_14p)
    assert [s.reference for s in chart.series] == [True, False]
    assert chart.y_unit == "V"


@pytest.mark.req("REQ-F-26")
def test_ui17_every_register_entry_shows_the_registry_content(registry):
    """Catches a reference view that drops or rewrites a field of an equation entry or its sources."""
    for eq_id, entry in registry.equations.items():
        topic = equation_topic(eq_id, registry)
        rows = dict.fromkeys(topic.rows)
        values = [v for _, v in rows]
        assert topic.topic_id == eq_id
        assert ("Name", entry.name) in rows and ("Formula", entry.formula) in rows
        assert ("Equation gate", entry.gate.value) in rows and ("Evidence status", entry.status.value) in rows
        assert ("Test state in this build", registry.test_state(eq_id).value) in rows
        for ev_id in entry.sources:
            ev = registry.evidence.get(ev_id)
            assert any(v.startswith(f"{ev_id}: ") and (ev is None or ev.location in v) for v in values), ev_id
        for test_id in entry.tests:
            assert ("Tests", test_id) in rows
        listed = [v for h, v in rows if h == "Dominant assumptions"]
        assert all(any(assumption in v for v in listed) for assumption in entry.dominant_assumptions), eq_id


@pytest.mark.req("REQ-F-26")
def test_s32_register_hides_empty_fields_and_lists_dominant_assumptions_in_one_row(registry):
    """U-S4g S32. Catches "Label None" or "Implementation None" (Python's None printed), or one row per assumption."""
    with_two = [eq for eq, e in registry.equations.items() if len(e.dominant_assumptions) > 1]
    without_label = [eq for eq, e in registry.equations.items() if not e.label or not e.implementation]
    assert with_two and without_label, "precondition: the register has both kinds of entry"
    for eq_id, entry in registry.equations.items():
        rows = equation_topic(eq_id, registry).rows
        assert [(h, v) for h, v in rows if not v.strip() or v == "None"] == [], eq_id
        listed = [v for h, v in rows if h == "Dominant assumptions"]
        assert len(listed) == (1 if entry.dominant_assumptions else 0), eq_id
        assert all(a in listed[0].splitlines() for a in entry.dominant_assumptions), eq_id


@pytest.mark.req("REQ-F-26")
def test_ui17_guide_tree_has_the_four_groups_and_every_equation(registry):
    """Catches a register that misses an equation or a guide without its four groups."""
    groups = guide_groups(registry, (("Global", "F1", "Guide"),))
    assert [g.title for g in groups] == ["Guide topics", "Equation register", "Status labels", "Keyboard shortcuts"]
    assert [t.topic_id for t in groups[1].topics] == list(registry.equations)
    assert [t.title for t in groups[2].topics] == [s.value for s in Status]
    assert (topic_for("EQ-18", registry), topic_for(None, registry), topic_for("param-x", registry)) == (
        "EQ-18",
        START_TOPIC,
        START_TOPIC,
    )


@pytest.mark.req("REQ-F-33")
def test_drc_measured_and_required_print_the_same_six_decimals(wave):
    """U-S4g S25. Catches "0.200000" beside "3.00000": six figures give a value of 3 mm one decimal fewer."""
    first = wave.drc[0].violations[0]
    widened = dataclasses.replace(first, clearance_mm=0.2, required_mm=3.0)
    report = dataclasses.replace(wave.drc[0], violations=(widened, *wave.drc[0].violations[1:]))
    row = drc_table(dataclasses.replace(wave, drc=(report, *wave.drc[1:]))).rows[0]
    assert (row.clearance_text, row.required_text) == ("0.200000\u00a0mm", "3.000000\u00a0mm")
