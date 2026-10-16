"""REQ-T-13: the 'How was this computed' disclosure and Copy trace of every result row of D08 and the wave example."""

import dataclasses
import re

import pytest

from embodic.api import compute
from embodic.io.examples import load_example
from embodic.model.provenance import derive_provenance, mark_measured
from embodic.ui.viewmodels.results import ResultsViewModel, disclosure, result_rows

SECTIONS = ["Equation", "Inputs", "Assumptions", "Limitations", "Validation state", "Sources"]
PROVENANCE_WORDS = {"user", "example", "measured", "default"}
INPUT_LINE = re.compile(r"(?P<pointer>\S+) = (?P<value>.+) \((?P<origin>[^()]+)\)")
NONE_LINE = "None"
BR = "/rotor/remanence_t"
SPEED = "/operating/speed_rpm"
GAP = "/rotor/air_gap_mm"


@pytest.fixture(params=["d08", "wave"])
def outcome(request):
    """Return the computed D08 spiral, then the computed wave example."""
    return request.getfixturevalue(request.param)


@pytest.mark.req("REQ-T-13")
def test_t13_every_row_has_the_six_sections_and_a_line_in_each(outcome, registry):
    """Catches one row whose disclosure drops a section, or one that leaves a section empty instead of saying None."""
    rows = result_rows(outcome.analysis)
    assert len(rows) == 30
    for row in rows:
        sections = disclosure(row, registry)
        assert [s.title for s in sections] == SECTIONS, row.quantity
        assert all(s.lines and all(line.strip() for line in s.lines) for s in sections), row.quantity


@pytest.mark.req("REQ-T-13")
def test_t13_every_input_line_names_where_the_value_came_from(outcome, registry):
    """Catches an input listed without its provenance word. A registry constant is not a user input and says so."""
    for row in result_rows(outcome.analysis):
        inputs = disclosure(row, registry)[1].lines
        assert len(inputs) == len(row.traceable.inputs) > 0, row.quantity
        for line in inputs:
            match = INPUT_LINE.fullmatch(line)
            assert match is not None, (row.quantity, line)
            if match["pointer"].startswith("/"):
                assert match["origin"] in PROVENANCE_WORDS, (row.quantity, line)
            else:
                assert match["origin"] in {"registry constant", "result"}, (row.quantity, line)


@pytest.mark.req("REQ-T-13")
def test_t13_the_assumptions_section_counts_what_the_card_tag_counts(outcome, registry):
    """Catches a disclosure whose assumptions list disagrees with the 'n assumptions' tag of the same card."""
    for row in result_rows(outcome.analysis):
        lines = disclosure(row, registry)[2].lines
        if row.assumed_count == 0:
            assert lines == (NONE_LINE,), row.quantity
        else:
            assert len(lines) == row.assumed_count, row.quantity


@pytest.mark.req("REQ-T-13")
def test_t13_copy_trace_holds_every_disclosure_line_of_every_row(outcome, registry):
    """Catches a Copy trace that omits a section title or a line that the disclosure shows."""
    vm = ResultsViewModel(registry)
    vm.show(outcome.analysis, stale=False)
    for row in result_rows(outcome.analysis):
        trace = vm.copy_trace(row.quantity)
        for section in disclosure(row, registry):
            assert f"{section.title}:" in trace, (row.quantity, section.title)
            for line in section.lines:
                assert line in trace, (row.quantity, line)


@pytest.mark.req("REQ-T-13")
def test_t13_inputs_show_user_example_and_measured_where_they_apply(registry):
    """Catches a disclosure that prints one constant word: a changed speed is `user`, a marked B_r is `measured`."""
    ref, design = load_example("spiral_12c10p_d08")
    operating = dataclasses.replace(design.operating, speed_rpm=design.operating.speed_rpm + 100.0)
    edited = dataclasses.replace(design, operating=operating)
    marked = mark_measured(edited, [], BR, "magnet datasheet rev C")
    assert isinstance(marked, tuple)
    outcome = compute(edited, derive_provenance(edited, (ref, design), list(marked)))
    origins: dict[str, set[str]] = {}
    for row in result_rows(outcome.analysis):
        for line in disclosure(row, registry)[1].lines:
            match = INPUT_LINE.fullmatch(line)
            assert match is not None
            origins.setdefault(match["pointer"], set()).add(match["origin"])
    assert origins[BR] == {"measured"}
    assert origins[SPEED] == {"user"}
    assert origins[GAP] == {"example"}
