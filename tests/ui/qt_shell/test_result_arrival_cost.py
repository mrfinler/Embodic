"""DEF-U-M5h-01: work the GUI thread repeated when a result arrived, without changing what it shows.

The offscreen call tree of a D08 result (U-M6a) showed the label layout computed 21 times and the drawing rebuilt twice
in one 544 ms stall. These tests pin the repeats; the stall itself is measured by
docs/phase3/design/checks/first_paint_probe.py.
"""

from embodic.ui.views import geometry_view


def count_label_layouts(monkeypatch) -> list[int]:
    """Count calls of the label placement the canvas runs (the costly step, 4 to 25 ms each offscreen)."""
    calls = [0]
    placed = geometry_view.place_in_view

    def counting(*args, **kwargs):
        calls[0] += 1
        return placed(*args, **kwargs)

    monkeypatch.setattr(geometry_view, "place_in_view", counting)
    return calls


def test_fit_view_lays_the_labels_out_once(d08_shell, monkeypatch):
    """Catches a fit that lays the labels out at every intermediate scroll step (four times on main f07d502)."""
    canvas = d08_shell.window.canvas
    canvas.zoom_by(2.0)
    calls = count_label_layouts(monkeypatch)
    canvas.fit_view()
    assert calls[0] == 1


def test_showing_the_same_drawing_again_keeps_its_items_and_labels(d08_shell, monkeypatch):
    """Catches a render with unchanged inputs that clears and redraws the whole scene (the second render per result)."""
    window = d08_shell.window
    canvas = window.canvas
    before = set(canvas.scene().items())
    calls = count_label_layouts(monkeypatch)
    scene, hidden, mode = (
        window.outcome.state.value.scene,
        window.outcome.hidden_layers.value,
        window.appearance.phase_render_mode.value,
    )
    canvas.show_geometry(scene, window.tokens, mode, hidden)
    assert set(canvas.scene().items()) == before
    assert calls[0] == 0


def test_a_new_result_on_screen_lays_the_labels_out_once_per_drawing(d08_shell, monkeypatch, qtbot, wait_ready):
    """Catches a recompute that rebuilds the drawing for the "updating" state too (twice on main f07d502)."""
    window = d08_shell.window
    calls = count_label_layouts(monkeypatch)
    window.outcome.compute_now()
    wait_ready(window)
    assert calls[0] == 1
