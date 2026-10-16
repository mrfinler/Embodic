"""F13-2 (V3-01 union ruling): the geometry zoom range is 0.1x to 200x as literals, not as the module's constants."""

import pytest


@pytest.mark.req("REQ-F-13")
def test_f13_2_zoom_range_is_01x_to_200x(d08_shell):
    """Catches a range change in geometry_view.py that the constant-comparing zoom test follows (UI-03)."""
    canvas = d08_shell.window.canvas
    for _ in range(60):
        canvas.zoom_by(1.25)
    assert canvas.zoom_factor() == pytest.approx(200.0, rel=1e-9)
    for _ in range(120):
        canvas.zoom_by(0.8)
    assert canvas.zoom_factor() == pytest.approx(0.1, rel=1e-9)
