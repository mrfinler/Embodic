"""REQ-T-16: the entries of OR-07 and OR-08 that the UI shows say that they are not independent of EC-05.

Copy and placement: docs/phase3/design/fix_wave_f1.md section (c), rows T16-1 to T16-5.
"""

from dataclasses import replace

import pytest

from embodic.ui.viewmodels.results import disclosure, equation_topic, result_rows

NOTE = "not independent of EC-05"
EC05_COPY = (
    "OR-07 and OR-08 are not independent of EC-05. They compare with data from the source that calibrates EC-05, "
    "so they cannot confirm EC-05. OR-01 is the independent check."
)
CHECK_SECTIONS = ("Limitations", "Validation state")


def ui_texts(outcome, registry) -> list[str]:
    """Return every registry-derived line the UI shows: the equation register and the disclosure of each result row."""
    lines = []
    for eq_id in registry.equations:
        topic = equation_topic(eq_id, registry)
        lines += [topic.title, *(value for _, value in topic.rows)]
    for row in result_rows(outcome.analysis):
        for section in disclosure(row, registry):
            lines += [section.title, *section.lines]
    return lines


def with_ec05_oracles(registry, *, dependent, independent):
    """Return the registry with the oracle lists of the EC-05 check of EQ-05 replaced."""
    eq = registry.equation("EQ-05")
    checks = tuple(
        replace(c, dependent_oracles=dependent, independent_oracles=independent) if c.id == "EC-05" else c
        for c in eq.validity_checks
    )
    equations = {**registry.equations, "EQ-05": replace(eq, validity_checks=checks)}
    return replace(registry, equations=equations)


def lines_after_ec05(outcome, registry) -> dict[str, list[str | None]]:
    """Return, per result row, the line after each line that starts with "EC-05 " in Limitations or Validation state."""
    found: dict[str, list[str | None]] = {}
    for row in result_rows(outcome.analysis):
        for section in disclosure(row, registry):
            if section.title not in CHECK_SECTIONS:
                continue
            for i, line in enumerate(section.lines):
                if line.startswith("EC-05 "):
                    after = section.lines[i + 1] if i + 1 < len(section.lines) else None
                    found.setdefault(row.quantity, []).append(after)
    return found


@pytest.mark.req("REQ-T-16")
@pytest.mark.parametrize("oracle", ["OR-07", "OR-08"])
def test_ui_entries_of_the_dependent_oracles_say_they_are_not_independent_of_ec05(oracle, d08, registry):
    """T16-1. Catches an oracle presented as independent evidence: the UI must show OR-07 and OR-08 with the note."""
    entries = [line for line in ui_texts(d08, registry) if oracle in line]
    assert entries, f"the UI shows no {oracle} entry"
    assert all(NOTE in line for line in entries)


@pytest.mark.req("REQ-T-16")
def test_every_ec05_check_line_of_d08_is_followed_by_the_oracle_note(d08, registry):
    """T16-2. Catches the note missing from a row, placed away from its check line, or worded differently."""
    found = lines_after_ec05(d08, registry)
    assert {"ke_phase_v_s_per_rad", "edge_leakage_fraction"} <= set(found)
    assert {q: after for q, afters in found.items() for after in afters if after != EC05_COPY} == {}


@pytest.mark.req("REQ-T-16")
def test_equation_register_lists_the_oracles_right_after_the_ec05_check(registry):
    """T16-3. Catches the register entry of EQ-05 without the Oracles row, or with it away from its check."""
    rows = equation_topic("EQ-05", registry).rows
    at = next(i for i, (label, value) in enumerate(rows) if label == "Validity checks" and value.startswith("EC-05 "))
    assert rows[at + 1] == ("Oracles", EC05_COPY)


@pytest.mark.req("REQ-T-16")
def test_one_dependent_oracle_and_no_independent_one_reads_in_the_singular_without_a_third_sentence(d08, registry):
    """T16-4. Catches a plural verb for one oracle or an empty "are the independent checks" sentence."""
    one = with_ec05_oracles(registry, dependent=("OR-07",), independent=())
    expected = (
        "OR-07 is not independent of EC-05. It compares with data from the source that calibrates EC-05, "
        "so it cannot confirm EC-05."
    )
    assert ("Oracles", expected) in equation_topic("EQ-05", one).rows
    assert {after for afters in lines_after_ec05(d08, one).values() for after in afters} == {expected}


@pytest.mark.req("REQ-T-16")
def test_check_without_dependent_oracles_gets_no_oracle_line(d08, registry):
    """T16-5. Catches a note written for a check whose registry entry names no dependent oracle."""
    none = with_ec05_oracles(registry, dependent=(), independent=("OR-01",))
    assert "Oracles" not in {label for label, _ in equation_topic("EQ-05", none).rows}
    assert not any("independent" in line for line in ui_texts(d08, none))


@pytest.mark.req("REQ-T-16")
def test_three_oracles_join_with_a_serial_comma(d08, registry):
    """Catches "A, B and C" or "A and B and C" where section (c) asks for "A, B, and C"."""
    three = with_ec05_oracles(registry, dependent=("OR-07", "OR-08", "OR-09"), independent=("OR-01", "OR-02"))
    rows = dict(equation_topic("EQ-05", three).rows)
    assert rows["Oracles"] == (
        "OR-07, OR-08, and OR-09 are not independent of EC-05. They compare with data from the source that calibrates "
        "EC-05, so they cannot confirm EC-05. OR-01 and OR-02 are the independent checks."
    )
