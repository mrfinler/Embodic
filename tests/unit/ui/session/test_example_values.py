"""Packaged example values as the inspector shows them (DEF-1, D-038f). Qt-free."""

import pytest

from embodic.io.examples import list_examples
from embodic.model.provenance import ExampleValue
from embodic.model.schema import ValueType
from embodic.ui.viewmodels.session import display_text, parse_text


@pytest.mark.req("REQ-F-21")
@pytest.mark.parametrize("example_id", [info.example_id for info in list_examples()])
def test_retyping_every_shown_example_value_keeps_its_example_chip(session, example_id):
    """Catches float noise in an example file: D08's air gap 1.0999999999999999 shows as 1.1, so retyping it flips."""
    session.load_example(example_id)
    typed = 0
    for row in session.rows():
        if row.spec.value_type is ValueType.FLOAT and row.present and row.value is not None:
            session.edit(row.pointer, parse_text(row.spec, display_text(row.spec, row.value)))
            typed += 1
    assert typed >= 20
    changed = {p: chip for p, chip in session.chips().items() if not isinstance(chip, ExampleValue)}
    assert changed == {}
