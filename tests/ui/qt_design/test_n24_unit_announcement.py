"""REQ-N-24 (V3-01 gap N-24): every inspector input with a unit shows it and announces it in its accessible description.

Expected values come from the field table (`embodic.model.fields.field_specs`): the unit of each row, shown with
`Unit.display()`. Angles are the one documented exception: the model holds radians and the form shows degrees
(`embodic.units` module docstring; `coil_panel.unit_text`). The two table widgets `layer-list` and `screw-table` hold
their units in column headers and have no per-cell description, so they are not covered here.
"""

import pytest
from PySide6.QtWidgets import QAbstractItemView, QLabel
from tests.ui.qt_design.conftest import find

from embodic.model.fields import field_specs
from embodic.model.vocabulary import TopologyKind
from embodic.units import Unit

pytestmark = pytest.mark.req("REQ-N-24")

EXAMPLE = {
    TopologyKind.SPIRAL: "spiral_12c10p_d08",
    TopologyKind.SERPENTINE: "serpentine_16p_example",
    TopologyKind.WAVE: "wave_16p_example",
}
SHOWN_IN_DEGREES = {Unit.RAD: "°"}
TABLE_WIDGETS = {"layer-list", "screw-table"}


def no_compute(design, provenance, **kwargs):
    """Stand in for the engine: the unit labels do not depend on a result."""
    return None


def unit_symbol(unit: Unit) -> str:
    """Return the symbol the form must show for a field-table unit."""
    return SHOWN_IN_DEGREES.get(unit, unit.display())


@pytest.mark.parametrize("topology", list(EXAMPLE), ids=lambda t: t.value)
def test_n24_every_unit_input_shows_and_announces_its_unit(make_shell, topology):
    """Catches an input whose unit is shown but not announced, or announced but not shown, or shown wrongly."""
    window = make_shell(compute_fn=no_compute).window
    window.session.load_example(EXAMPLE[topology])
    checked, problems, tables = 0, [], set()
    for spec in field_specs(topology):
        if spec.unit is None or spec.widget_id is None or not unit_symbol(spec.unit):
            continue
        widget = find(window, spec.widget_id)
        if isinstance(widget, QAbstractItemView):
            tables.add(spec.widget_id)
            continue
        shown = find(window, f"{spec.widget_id}-unit")
        assert isinstance(shown, QLabel)
        symbol, announced = unit_symbol(spec.unit), widget.accessibleDescription()
        checked += 1
        if shown.text() != symbol:
            problems.append(f"{spec.widget_id}: unit label {shown.text()!r}, expected {symbol!r}")
        if symbol not in announced:
            problems.append(f"{spec.widget_id}: accessible description {announced!r} lacks {symbol!r}")
    assert checked > 25
    assert tables <= TABLE_WIDGETS
    assert problems == []
