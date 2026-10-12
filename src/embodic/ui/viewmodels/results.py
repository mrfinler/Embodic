"""What the results area shows of a computed design: result cards, DRC table, charts, comparison, equation register.

Qt-free (import contracts C2 and C3). Every badge, label and assumption count is read from the `Traceable` (D-007);
quantity names come from `QUANTITY_LABELS` and card titles from `quantity_title` (D-038e, D-039).
"""

import cmath
import dataclasses
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal, TypeAlias

from embodic.drc import DrcReport
from embodic.errors import IssueCategory, Severity, ValidationIssue, message_for
from embodic.model.vocabulary import Phase
from embodic.outcome import ComputeOutcome
from embodic.physics.waveform import XCOIL_WAVEFORM_SAMPLES, emf_waveform_v
from embodic.results import QUANTITY_LABELS, AnalysisResult, Registry, Traceable
from embodic.results.formatting import (
    MINUS,
    NOT_A_NUMBER,
    UNIT_SPACE,
    format_fixed,
    format_quantity,
    spoken_quantity,
)
from embodic.results.labels import quantity_title
from embodic.results.status import Status, ValidityEffect, ValidityFlag, combine_status
from embodic.results.traceable import AssumedInput
from embodic.ui.strings import text
from embodic.ui.viewmodels.observable import Observable
from embodic.units import Unit, rpm_to_rad_per_s

# Phase 1 card keys (docs/phase1/design/screen_to_view_map.md); every other card is keyed by its field name.
PHASE1_KEYS: Mapping[str, str] = {
    "resistance_phase_operating_ohm": "r-phase",
    "ke_phase_v_s_per_rad": "ke",
    "kt_n_m_per_a": "kt",
    "inductance_estimate_h": "ls",
    "temperature_rise_k": "dt",
    "current_density_a_per_mm2": "j",
}
# DRC lengths print with six decimals: D-006 has no slack band (epsilon <= 1e-6 mm), so 0.199965 mm against 0.2 mm
# must read as different, and Measured and Required line up whatever their size (U-S4g S25).
DRC_DECIMALS = 6


def drc_length_text(mm: float) -> str:
    """Return a DRC length as the DRC table and the export confirmation print it: "3.000000 mm"."""
    return format_fixed(mm, Unit.MM, decimals=DRC_DECIMALS)


def result_key(quantity: str) -> str:
    """Return the objectName key of a result card: ``res-<key>``."""
    return PHASE1_KEYS.get(quantity, quantity.replace("_", "-"))


def split_value(value: float, unit: Unit) -> tuple[str, str]:
    """Return the number and the unit text of a value: 3 significant figures, U+2212 minus, a unit always present."""
    shown = format_quantity(value, unit)
    if shown == NOT_A_NUMBER:
        return shown, unit.display() or text("results.unit.dimensionless")
    number, _, unit_text = shown.partition(UNIT_SPACE)
    return number, unit_text or text("results.unit.dimensionless")


@dataclass(frozen=True, slots=True, kw_only=True)
class ResultRow:
    """One displayed number (REQ-T-01): everything the row and its 'How was this computed' disclosure need."""

    quantity: str
    label: str
    title: str  # the label, then the symbol the equation specification states
    value_text: str
    unit_text: str
    status: Status
    assumed_count: int
    eq_ids: tuple[str, ...]
    estimate_label: str | None
    accessible_name: str  # what a screen reader announces for the card: title, value, unit and status in words
    traceable: Traceable[float]


def accessible_name(title: str, t: Traceable[float]) -> str:
    """Return "<title>, <value> <unit in words>, <status>[, <label>]"; a unitless value says "dimensionless"."""
    spoken = spoken_quantity(t.value, t.unit)
    if not t.unit.display() and math.isfinite(t.value):
        spoken = f"{spoken} {text('results.unit.dimensionless')}"
    parts = (title, spoken, t.status.value, *((t.label,) if t.label else ()))
    return ", ".join(parts)


def result_row(quantity: str, t: Traceable[float]) -> ResultRow:
    """Return the row of one AnalysisResult field."""
    value_text, unit_text = split_value(t.value, t.unit)
    return ResultRow(
        quantity=quantity,
        label=QUANTITY_LABELS[quantity],
        title=quantity_title(quantity),
        value_text=value_text,
        unit_text=unit_text,
        status=t.status,
        assumed_count=len(t.assumed_inputs),
        eq_ids=t.eq_ids,
        estimate_label=t.label,
        accessible_name=accessible_name(quantity_title(quantity), t),
        traceable=t,
    )


def result_rows(analysis: AnalysisResult) -> tuple[ResultRow, ...]:
    """Return one row per scalar result of the analysis, in AnalysisResult field order."""
    rows = []
    for field in dataclasses.fields(analysis):
        t = getattr(analysis, field.name)
        if isinstance(t, Traceable) and isinstance(t.value, float):
            rows.append(result_row(field.name, t))
    return tuple(rows)


def assumptions_text(count: int) -> str:
    """Return the assumption tag: "1 assumption", "n assumptions"."""
    return text("results.asm.count-one") if count == 1 else text("results.asm.count", count=count)


@dataclass(frozen=True, slots=True, kw_only=True)
class DisclosureSection:
    """One heading of the 'How was this computed' disclosure and its lines."""

    title: str
    lines: tuple[str, ...]


def assumed_input_text(a: AssumedInput) -> str:
    """Return one line of the assumption list: item, value, reason and label."""
    head = f"{a.item} {a.value_text}".rstrip()
    reason = text(f"results.how.reason-{a.reason}")
    dominant = f", {text('results.how.dominant')}" if a.dominant else ""
    return f"{head} ({reason}{dominant}; {a.label})"


def check_text(flag: ValidityFlag, registry: Registry) -> str:
    """Return a validity flag in words; a registry check states its metric, bound, cap and the status of each part.

    The metric and the threshold of a registry validity check are fractions (EC-05 e_edge), so they print as percent.
    """
    spec = next((c for c in registry.equation(flag.eq_id).validity_checks if c.id == flag.code), None)
    if spec is None or flag.metric is None:
        return f"{flag.code}: {flag.message}"
    metric_name = spec.metric.partition("=")[0].strip()
    return text(
        "results.how.check",
        code=flag.code,
        name=spec.name,
        metric=metric_name,
        bound=text(f"results.how.bound.{flag.metric_bound.value}"),
        value=f"{format_quantity(flag.metric * 100, Unit.ONE)}{UNIT_SPACE}%",
        bound_name=flag.metric_bound.value.replace("_", " "),
        threshold=f"{spec.threshold * 100:g}{UNIT_SPACE}%",
        threshold_status=flag.threshold_status or spec.threshold_status,
        calibration_status=flag.calibration_status or spec.calibration_status,
        transfer_status=flag.transfer_status or spec.transfer_status,
    )


def _input_lines(t: Traceable[float]) -> tuple[str, ...]:
    lines = []
    for ref in t.inputs:
        if ref.provenance is not None:
            origin = ref.provenance.value
        elif ref.pointer.startswith("constant:"):
            origin = text("results.how.provenance-constant")
        else:
            origin = text("results.how.provenance-result")
        if isinstance(ref.value, float | int) and not isinstance(ref.value, bool):
            value = format_quantity(float(ref.value), ref.unit or Unit.ONE)
        else:
            value = str(ref.value)
        lines.append(f"{ref.pointer} = {value} ({origin})")
    return tuple(lines)


def _source_lines(t: Traceable[float], registry: Registry) -> tuple[str, ...]:
    lines = []
    for ev_id in t.evidence_ids:
        entry = registry.evidence.get(ev_id)
        if entry is None:
            lines.append(text("results.how.source-missing", id=ev_id))
        else:
            lines.append(
                text(
                    "results.how.source",
                    id=ev_id,
                    document=entry.document,
                    location=entry.location,
                    status=entry.status,
                )
            )
    return tuple(lines)


# Every disclosure has these sections in this order, whatever the row (a row without one says "None").
DISCLOSURE_KEYS = (
    "results.how.equation",
    "results.how.inputs",
    "results.how.assumptions",
    "results.how.limitations",
    "results.how.validity",
    "results.how.sources",
)


def disclosure(row: ResultRow, registry: Registry) -> tuple[DisclosureSection, ...]:
    """Return the 'How was this computed' disclosure of a row (REQ-T-13).

    Sections: equation, inputs, assumptions, limitations, validation state and sources.
    """
    t = row.traceable
    equations = tuple(f"{eq}: {registry.equation(eq).name}. {registry.equation(eq).formula}" for eq in t.eq_ids)
    limitations = [check_text(f, registry) for f in t.validity if f.effect is ValidityEffect.LIMITATION]
    if t.label is not None:
        limitations.append(text("results.how.label", label=t.label))
    validity = [text("results.how.status", status=t.status, reasons="; ".join(t.status_reasons))]
    validity += [
        text("results.how.cap", code=f.code, message=check_text(f, registry))
        for f in t.validity
        if f.effect is ValidityEffect.CAP
    ]
    if t.tolerance is not None:
        validity.append(text("results.how.tolerance", against=t.tolerance.against, source=t.tolerance.source_ref))
    sections = (
        equations or (text(f"results.how.kind-{t.kind_tag}"),),
        _input_lines(t),
        tuple(assumed_input_text(a) for a in t.assumed_inputs),
        tuple(limitations),
        tuple(validity),
        _source_lines(t, registry),
    )
    return tuple(
        DisclosureSection(title=text(key), lines=lines or (text("results.how.none"),))
        for key, lines in zip(DISCLOSURE_KEYS, sections, strict=True)
    )


def trace_text(row: ResultRow, registry: Registry) -> str:
    """Return the plain text that Copy trace puts on the clipboard: the row, then every disclosure section."""
    header = f"{row.label}: {row.value_text} {row.unit_text} [{row.status}]"
    if row.estimate_label:
        header += f" ({row.estimate_label})"
    body = [f"{s.title}:\n" + "\n".join(f"  {line}" for line in s.lines) for s in disclosure(row, registry)]
    return "\n".join([header, *body])


class ResultsViewModel:
    """Result rows of the shown outcome, filtered by status, and their traces."""

    def __init__(self, registry: Registry) -> None:
        self.registry = registry
        self._all: tuple[ResultRow, ...] = ()
        self.rows: Observable[tuple[ResultRow, ...]] = Observable(())
        self.status_filter: Observable[frozenset[Status]] = Observable(frozenset(Status))
        self.stale: Observable[bool] = Observable(False)

    def show(self, analysis: AnalysisResult | None, *, stale: bool) -> None:
        """Take the analysis on screen; None empties the rows. ``stale`` marks a kept last valid result."""
        self._all = () if analysis is None else result_rows(analysis)
        self.stale.set(stale and analysis is not None)
        self._publish()

    def set_status_filter(self, statuses: frozenset[Status]) -> None:
        """Show only rows whose badge is one of ``statuses``."""
        self.status_filter.set(statuses)
        self._publish()

    def row(self, quantity: str) -> ResultRow:
        """Return the row of a quantity, whatever the filter; KeyError when the shown analysis has none."""
        for row in self._all:
            if row.quantity == quantity:
                return row
        raise KeyError(quantity)

    def copy_trace(self, quantity: str) -> str:
        """Return the trace text of one quantity."""
        return trace_text(self.row(quantity), self.registry)

    def _publish(self) -> None:
        self.rows.set(tuple(r for r in self._all if r.status in self.status_filter.value))


CheckState: TypeAlias = Literal["pass", "fail", "not-run"]
CardState: TypeAlias = CheckState | Literal["advice"]


@dataclass(frozen=True, slots=True, kw_only=True)
class DrcRow:
    """One reported violation as the DRC table shows it."""

    number: int
    board: int
    severity: Literal["error"]
    rule_code: str
    message: str
    measured_text: str
    required_text: str
    layer_text: str
    at_mm: tuple[float, float]
    board_text: str = ""  # phase letter of the board, "" when the design has one board


@dataclass(frozen=True, slots=True, kw_only=True)
class DrcTable:
    """The DRC tab: summary line, its check state, the rows and the truncation note."""

    state: CheckState
    summary: str
    failure_count: int
    warning_count: int
    rows: tuple[DrcRow, ...]
    note: str | None
    boards: tuple[Phase, ...] = ()  # the letter of each board when the design has more than one


def _count(n: int, one: str, many: str) -> str:
    return text(one) if n == 1 else text(many, count=n)


def _board_verdict(letter: Phase, report: DrcReport) -> str:
    if report.violation_count == 0:
        return text("drc.board.pass", letter=letter.value)
    failures = _count(report.violation_count, "drc.count.failure-one", "drc.count.failures")
    return text("drc.board.fail", letter=letter.value, failures=failures)


def drc_table(outcome: ComputeOutcome | None) -> DrcTable | None:
    """Return the DRC tab of an outcome, or None before the first compute."""
    if outcome is None:
        return None
    if outcome.drc is None:
        return DrcTable(
            state="not-run", summary=text("drc.summary.not-run"), failure_count=0, warning_count=0, rows=(), note=None
        )
    warnings = sum(1 for i in outcome.issues if i.category is IssueCategory.DRC and i.severity is Severity.WARNING)
    failures = sum(r.violation_count for r in outcome.drc)
    letters = tuple(Phase)[: len(outcome.drc)] if len(outcome.drc) > 1 else ()
    violations = [(board, v) for board, report in enumerate(outcome.drc, start=1) for v in report.violations]
    rows = tuple(
        DrcRow(
            number=number,
            board=board,
            severity="error",
            rule_code=v.kind.issue_code,
            message=message_for(v.kind.issue_code),
            measured_text=drc_length_text(v.measured_mm),
            required_text=drc_length_text(v.required_mm),
            layer_text=v.layer or text("drc.layer.all"),
            at_mm=v.at_mm,
            board_text=letters[board - 1].value if letters else "",
        )
        for number, (board, v) in enumerate(violations, start=1)
    )
    state: CheckState = "fail" if failures else "pass"
    if failures == 0 and warnings == 0:
        summary = text("drc.summary.pass")
    else:
        counts = {
            "failures": _count(failures, "drc.count.failure-one", "drc.count.failures"),
            "warnings": _count(warnings, "drc.count.warning-one", "drc.count.warnings"),
        }
        summary = text("drc.summary.fail", **counts)
    if letters:
        verdicts = ", ".join(_board_verdict(letter, r) for letter, r in zip(letters, outcome.drc, strict=True))
        summary = text("drc.summary.boards", summary=summary, boards=verdicts)
    note = text("drc.truncated", shown=len(rows), total=failures) if len(rows) < failures else None
    return DrcTable(
        state=state,
        summary=summary,
        failure_count=failures,
        warning_count=warnings,
        rows=rows,
        note=note,
        boards=letters,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class StatusCard:
    """A verdict card of the results rail: the state picks the glyph, the word says it (never colour alone)."""

    key: str  # objectName of the card
    title: str
    state: CardState
    word: str


def inputs_card(issues: Sequence[ValidationIssue], missing: int = 0) -> StatusCard:
    """Return the Inputs card: missing fields and errors fail it; warnings and notes are advice, shown as notes."""
    errors = sum(1 for found in issues if found.severity is Severity.ERROR)
    advice = len(issues) - errors
    words = [_count(missing, "new-required-count.one", "new-required-count.text")] if missing else []
    words += [_count(errors, "rail.inputs.one", "rail.inputs.many")] if errors else []
    words += [_count(advice, "rail.inputs.note-one", "rail.inputs.note-many")] if advice else []
    word = ", ".join(words) or text("rail.inputs.pass")
    state: CardState = "fail" if missing or errors else "advice" if advice else "pass"
    return StatusCard(key="rail-inputs", title=text("rail.inputs.label"), state=state, word=word)


def drc_card(table: DrcTable) -> StatusCard:
    """Return the DRC card: Passed, the failure count, or Not run."""
    if table.state == "fail":
        word = _count(table.failure_count, "drc.count.failure-one", "drc.count.failures")
    else:
        word = text("shell.sum-drc.pass" if table.state == "pass" else "shell.sum-drc.not-run")
    return StatusCard(key="rail-drc", title=text("shell.sum-drc.label"), state=table.state, word=word)


@dataclass(frozen=True, slots=True, kw_only=True)
class ChartSeries:
    """One line of a chart; ``phase`` picks the phase colour and line style, None draws in ink."""

    label: str
    phase: Phase | None
    ys: tuple[float, ...]
    reference: bool = False  # drawn dashed grey (compare chart)


@dataclass(frozen=True, slots=True, kw_only=True)
class ChartModel:
    """Everything a chart draws: one x axis, one y axis with one unit, the series and the trust metadata."""

    chart_id: str
    title: str
    x_label: str
    x_unit: str
    y_label: str
    y_unit: str
    xs: tuple[float, ...]
    series: tuple[ChartSeries, ...]
    status: Status
    eq_ids: tuple[str, ...]
    assumed_count: int
    estimate_label: str | None
    note: str | None = None
    x_ticks: tuple[float, ...] | None = None  # None: round ticks from the data range
    computed: bool = True  # False stamps "Illustrative, not computed" (UI-32)


def _meta(traceables: Sequence[Traceable[Any]]) -> tuple[Status, tuple[str, ...], int, str | None]:
    """Return the weakest badge, the EQ-IDs, the distinct assumed inputs and the first label of the traceables."""
    status = combine_status(*(t.status for t in traceables))
    eq_ids = tuple(dict.fromkeys(eq for t in traceables for eq in t.eq_ids))
    assumed = {(a.item, a.value_text) for t in traceables for a in t.assumed_inputs}
    label = next((t.label for t in traceables if t.label is not None), None)
    return status, eq_ids, len(assumed), label


def phase_fundamentals_v(analysis: AnalysisResult, speed_rpm: float) -> dict[Phase, tuple[float, ...]]:
    """Return each phase's fundamental EMF over one electrical period, from its phasor with `emf_waveform_v`.

    AnalysisResult carries the harmonic waveform of the first phase only; every phase carries its fundamental
    phasor (Ke peak and angle), so the three curves are drawn on that common footing.
    """
    omega_m = rpm_to_rad_per_s(speed_rpm)
    return {
        p.phase: tuple(
            emf_waveform_v(
                {1: cmath.rect(p.ke_peak_v_s_per_rad.value * omega_m, p.emf_phasor_angle_rad.value)}
            ).tolist()
        )
        for p in analysis.phases
    }


def back_emf_chart(outcome: ComputeOutcome | None) -> ChartModel | None:
    """Return the back-EMF chart of an outcome, or None before the first analysis."""
    analysis = outcome.analysis if outcome is not None else None
    if outcome is None or analysis is None:
        return None
    speed = outcome.design.operating.speed_rpm
    curves = phase_fundamentals_v(analysis, speed)
    used: list[Traceable[Any]] = [
        analysis.emf_waveform_v,
        *(t for p in analysis.phases for t in (p.ke_peak_v_s_per_rad, p.emf_phasor_angle_rad)),
    ]
    status, eq_ids, assumed, label = _meta(used)
    samples = XCOIL_WAVEFORM_SAMPLES
    return ChartModel(
        chart_id="chart-backemf",
        title=text("chart.backemf.title", speed=f"{format_quantity(speed, Unit.ONE)}{UNIT_SPACE}rpm"),
        x_label=text("chart.backemf.x"),
        x_unit="°",
        y_label=text("chart.backemf.y"),
        y_unit=Unit.V.display(),
        xs=tuple(360.0 * k / (samples - 1) for k in range(samples)),
        x_ticks=(0.0, 90.0, 180.0, 270.0, 360.0),
        series=tuple(
            ChartSeries(label=text("chart.legend.phase", phase=phase.value), phase=phase, ys=ys)
            for phase, ys in curves.items()
        ),
        status=status,
        eq_ids=eq_ids,
        assumed_count=assumed,
        estimate_label=label,
        note=text("chart.backemf.note", thd=format_quantity(analysis.thd_phase.value, Unit.ONE)),
    )


def torque_speed_charts(outcome: ComputeOutcome | None) -> tuple[ChartModel, ChartModel] | None:
    """Return the torque-speed and power-speed small multiples (one unit each, shared rpm axis), or None."""
    analysis = outcome.analysis if outcome is not None else None
    if analysis is None or analysis.torque_speed is None:
        return None
    ts = analysis.torque_speed

    def chart(chart_id: str, title_key: str, t: Traceable[tuple[float, ...]]) -> ChartModel:
        status, eq_ids, assumed, label = _meta([ts.speed_rpm, t])
        return ChartModel(
            chart_id=chart_id,
            title=text(title_key),
            x_label=text("chart.speed.x"),
            x_unit=Unit.RPM.display(),
            y_label=text(title_key),
            y_unit=t.unit.display(),
            xs=ts.speed_rpm.value,
            series=(ChartSeries(label=text(title_key), phase=None, ys=t.value),),
            status=status,
            eq_ids=eq_ids,
            assumed_count=assumed,
            estimate_label=label,
        )

    return (
        chart("chart-torque-speed", "chart.torque.title", ts.torque_n_m),
        chart("chart-power-speed", "chart.power.title", ts.power_w),
    )


def nice_ticks(lo: float, hi: float, count: int = 5) -> tuple[float, ...]:
    """Return round tick values (1, 2 or 5 times a power of ten) covering [lo, hi]."""
    if not (math.isfinite(lo) and math.isfinite(hi)):
        return ()
    if hi <= lo:
        lo, hi = lo - 1.0, hi + 1.0
    raw = (hi - lo) / max(count - 1, 1)
    power = 10 ** math.floor(math.log10(raw))
    step = next(m * power for m in (1, 2, 5, 10) if m * power >= raw)
    first = math.floor(lo / step) * step
    ticks = []
    k = 0
    while (value := first + k * step) <= hi + step * 1e-9:
        ticks.append(0.0 if abs(value) < step * 1e-9 else value)
        k += 1
    if ticks[-1] < hi:
        ticks.append(ticks[-1] + step)
    return tuple(ticks)


def tick_text(value: float) -> str:
    """Return a tick label: shortest round form, U+2212 minus, locale-independent."""
    shown = f"{abs(value):.10g}"
    return f"{MINUS}{shown}" if value < 0 else shown


Direction: TypeAlias = Literal["up", "down", "same"]


@dataclass(frozen=True, slots=True, kw_only=True)
class CompareRow:
    """One quantity of the reference and the current design.

    A value cell joins number and unit with U+00A0 (ruling e1); a unitless value is the number alone. The table has no
    Unit column: a column unit beside a scaled cell unit ("V·s/rad", "26.4 mV·s/rad") contradicts it (D-043c).
    """

    quantity: str
    label: str
    reference_text: str
    current_text: str
    delta_text: str
    direction: Direction


def _direction(delta: float) -> Direction:
    return "up" if delta > 0 else "down" if delta < 0 else "same"


def _signed(text_value: str, delta: float) -> str:
    return f"+{text_value}" if delta > 0 else text_value


def _counts(outcome: ComputeOutcome) -> dict[str, int]:
    boards = outcome.boards.boards if outcome.boards is not None else ()
    coils = {(p.phase, p.element) for b in boards for p in b.paths if p.phase is not None and p.element is not None}
    return {
        "copper-layers": len({layer for b in boards for layer in b.copper_layers}),
        "coils": len(coils),
        "vias": sum(len(b.vias) for b in boards),
        "drc-failures": sum(r.violation_count for r in outcome.drc) if outcome.drc is not None else 0,
    }


def compare_rows(reference: ComputeOutcome, current: ComputeOutcome) -> tuple[CompareRow, ...]:
    """Return the comparison: every scalar result both designs have, then the counts as integers (UI-10, UI-34)."""
    rows = []
    if reference.analysis is not None and current.analysis is not None:
        ref_rows = {r.quantity: r for r in result_rows(reference.analysis)}
        for cur in result_rows(current.analysis):
            ref = ref_rows.get(cur.quantity)
            if ref is None:
                continue
            delta = cur.traceable.value - ref.traceable.value
            unit = cur.traceable.unit
            rows.append(
                CompareRow(
                    quantity=cur.quantity,
                    label=cur.label,
                    reference_text=format_quantity(ref.traceable.value, unit),
                    current_text=format_quantity(cur.traceable.value, unit),
                    delta_text=_signed(format_quantity(delta, unit), delta),
                    direction=_direction(delta),
                )
            )
    ref_counts, cur_counts = _counts(reference), _counts(current)
    for key, cur_n in cur_counts.items():
        delta_n = cur_n - ref_counts[key]
        rows.append(
            CompareRow(
                quantity=key,
                label=text(f"compare.count.{key}"),
                reference_text=str(ref_counts[key]),
                current_text=str(cur_n),
                delta_text=_signed(format_quantity(delta_n, Unit.COUNT), delta_n),
                direction=_direction(delta_n),
            )
        )
    return tuple(rows)


def compare_chart(reference: ComputeOutcome, current: ComputeOutcome) -> ChartModel | None:
    """Return phase A's fundamental back-EMF of both designs on one V axis, or None when either has no analysis."""
    ref_chart, cur_chart = back_emf_chart(reference), back_emf_chart(current)
    if ref_chart is None or cur_chart is None:
        return None
    first = cur_chart.series[0]
    return dataclasses.replace(
        cur_chart,
        chart_id="compare-chart",
        title=text("compare.chart.title"),
        series=(
            ChartSeries(label=text("compare.series.reference"), phase=None, ys=ref_chart.series[0].ys, reference=True),
            ChartSeries(label=text("compare.series.current"), phase=None, ys=first.ys),
        ),
        status=combine_status(ref_chart.status, cur_chart.status),
        note=None,
    )


class CompareViewModel:
    """The stored reference design; replacing it is the view's confirmed action."""

    def __init__(self) -> None:
        self.reference: Observable[ComputeOutcome | None] = Observable(None)

    def needs_confirmation(self) -> bool:
        """Return True when setting a reference would replace a stored one."""
        return self.reference.value is not None

    def set_reference(self, outcome: ComputeOutcome) -> None:
        """Store an outcome as the reference."""
        self.reference.set(outcome)


@dataclass(frozen=True, slots=True, kw_only=True)
class GuideTopic:
    """One topic of the guide: its id (an EQ-ID for register entries), title and (heading, text) rows."""

    topic_id: str
    title: str
    rows: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class GuideGroup:
    """A top-level entry of the guide's table of contents."""

    title: str
    topics: tuple[GuideTopic, ...]


START_TOPIC = "guide:start"


def equation_topic(eq_id: str, registry: Registry) -> GuideTopic:
    """Return the register entry of one equation exactly as the registry states it (UI-17).

    The dominant assumptions share one row, one per line.
    """
    e = registry.equation(eq_id)

    def source(ev_id: str) -> str:
        entry = registry.evidence.get(ev_id)
        if entry is None:
            return text("results.how.source-missing", id=ev_id)
        return text(
            "results.how.source", id=ev_id, document=entry.document, location=entry.location, status=entry.status
        )

    checks = [
        text(
            "guide.eq.check",
            id=c.id,
            name=c.name,
            rule=c.rule,
            threshold=f"{c.threshold:g}",
            threshold_status=c.threshold_status,
        )
        for c in e.validity_checks
    ]
    constants = [
        text(
            "guide.eq.constant",
            name=c.name,
            value=format_quantity(c.value, c.unit, significant=6),
            source=c.source or text("guide.eq.no-source"),
            status=c.status,
        )
        for c in e.constants
    ]
    rows: list[tuple[str, str]] = [
        ("guide.eq.name", e.name),
        ("guide.eq.formula", e.formula),
        ("guide.eq.gate", e.gate.value),
        ("guide.eq.status", e.status.value),
        ("guide.eq.test-state", registry.test_state(eq_id).value),
        ("guide.eq.label", e.label or ""),
        *(("guide.eq.sources", source(ev)) for ev in e.sources),
        ("guide.eq.assumptions", "\n".join(e.dominant_assumptions)),
        *(("guide.eq.checks", c) for c in checks),
        *(("guide.eq.tests", t) for t in e.tests),
        *(("guide.eq.constants", c) for c in constants),
        ("guide.eq.implementation", e.implementation or ""),
    ]
    shown = tuple((text(k), v) for k, v in rows if v)  # a field the registry leaves empty gets no row (S32)
    return GuideTopic(topic_id=eq_id, title=f"{eq_id} {e.name}", rows=shown)


def guide_groups(registry: Registry, keyboard_map: Sequence[tuple[str, str, str]]) -> tuple[GuideGroup, ...]:
    """Return the guide's table of contents: guide topics, equation register, status labels, keyboard shortcuts."""
    guide = (
        GuideTopic(topic_id=START_TOPIC, title=text("guide.topic.start"), rows=(("", text("guide.topic.start.body")),)),
        GuideTopic(
            topic_id="guide:badges", title=text("guide.topic.badges"), rows=(("", text("guide.topic.badges.body")),)
        ),
    )
    statuses = tuple(
        GuideTopic(
            topic_id=f"status:{s.value}",
            title=s.value,
            rows=(("", text(f"guide.status.{s.value.replace(' ', '-')}")),),
        )
        for s in Status
    )
    keys = GuideTopic(
        topic_id="guide:keys",
        title=text("guide.group.keys"),
        rows=tuple((f"{scope}: {keys}", action) for scope, keys, action in keyboard_map),
    )
    return (
        GuideGroup(title=text("guide.group.guide"), topics=guide),
        GuideGroup(
            title=text("guide.group.equations"),
            topics=tuple(equation_topic(eq_id, registry) for eq_id in registry.equations),
        ),
        GuideGroup(title=text("guide.group.statuses"), topics=statuses),
        GuideGroup(title=text("guide.group.keys"), topics=(keys,)),
    )


def topic_for(hint: str | None, registry: Registry) -> str:
    """Return the guide topic of a focused widget's hint: an EQ-ID or a topic id it names, else the start topic."""
    if hint and (hint in registry.equations or hint.startswith(("guide:", "status:"))):
        return hint
    return START_TOPIC
