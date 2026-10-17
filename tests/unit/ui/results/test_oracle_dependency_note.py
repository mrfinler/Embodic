"""REQ-T-16: the entries of OR-07 and OR-08 that the UI shows say that they are not independent of EC-05."""

import pytest

from embodic.ui.viewmodels.results import disclosure, equation_topic, result_rows

NOTE = "not independent of EC-05"


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


@pytest.mark.req("REQ-T-16")
@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="DEF-UM7d-02: no UI text names OR-07 or OR-08. The equation register and the disclosure show the EC-05 "
    "check with its threshold and statuses only; `dependent_oracles` is read from the registry and never rendered "
    "(grep of src for OR-07 finds nothing). REQ-T-16 asks for the dependency note on the entries the UI shows.",
)
@pytest.mark.parametrize("oracle", ["OR-07", "OR-08"])
def test_ui_entries_of_the_dependent_oracles_say_they_are_not_independent_of_ec05(oracle, d08, registry):
    """Catches an oracle row presented as independent evidence: the UI must show OR-07 and OR-08 with the note."""
    entries = [line for line in ui_texts(d08, registry) if oracle in line]
    assert entries, f"the UI shows no {oracle} entry"
    assert all(NOTE in line for line in entries)
