"""Theme choice, phase render mode and the canvas share of the centre pane, persisted through an injected store."""

from typing import Protocol

from embodic.io.exporters import PhaseRenderMode as PhaseRenderMode  # geometry_view still imports it from here
from embodic.ui.theme import ThemeName
from embodic.ui.viewmodels.observable import Observable

CANVAS_SHARE = 0.6  # design_spec.md section 5, U-S4e ruling b: the canvas is what the user designs
CANVAS_MIN_PX = 240  # legend plus a ring that holds the labels
RESULTS_MIN_PX = 180  # tab bar plus one card row
COMPACT_BELOW_PX = 620  # client height under which the canvas becomes the "Drawing" results tab

THEME_CYCLE: dict[ThemeName, ThemeName] = {
    ThemeName.LIGHT: ThemeName.DARK,
    ThemeName.DARK: ThemeName.SYSTEM,
    ThemeName.SYSTEM: ThemeName.LIGHT,
}


class AppearanceStore(Protocol):
    """Where the theme choice survives a restart."""

    def load_theme(self) -> str | None:
        """Return the stored choice, or None when nothing is stored."""

    def save_theme(self, value: str) -> None:
        """Store a choice."""

    def load_canvas_share(self) -> float | None:
        """Return the stored canvas share of the centre pane (0 to 1), or None."""

    def save_canvas_share(self, value: float) -> None:
        """Store the canvas share."""


def split_sizes(total_px: int, share: float) -> tuple[int, int]:
    """Return the canvas and results heights of a centre pane ``total_px`` tall, both held to their minimums."""
    canvas = round(total_px * share)
    canvas = max(CANVAS_MIN_PX, min(canvas, total_px - RESULTS_MIN_PX))
    return canvas, total_px - canvas


class AppearanceViewModel:
    """Theme choice (light, dark, system) and the phase render mode of the geometry view."""

    def __init__(self, store: AppearanceStore) -> None:
        self._store = store
        stored = store.load_theme()
        initial = ThemeName(stored) if stored in tuple(ThemeName) else ThemeName.SYSTEM
        self.theme: Observable[ThemeName] = Observable(initial)
        self.phase_render_mode: Observable[PhaseRenderMode] = Observable(PhaseRenderMode.COLOUR)
        share = store.load_canvas_share()
        self.canvas_share = share if share is not None and 0.0 <= share <= 1.0 else CANVAS_SHARE

    def set_theme(self, choice: ThemeName) -> None:
        """Show and remember a theme choice."""
        self.theme.set(choice)
        self._store.save_theme(choice.value)

    def set_canvas_share(self, canvas_px: int, results_px: int) -> None:
        """Remember the split a drag left as the canvas fraction; pixels are not stored, the window size changes."""
        if canvas_px + results_px > 0:
            self.canvas_share = canvas_px / (canvas_px + results_px)
            self._store.save_canvas_share(self.canvas_share)

    def cycle_theme(self) -> None:
        """Move to the next choice: light, dark, system, light."""
        self.set_theme(THEME_CYCLE[self.theme.value])

    def toggle_phase_render_mode(self) -> None:
        """Switch between colour and greyscale with hatching."""
        modes = tuple(PhaseRenderMode)
        self.phase_render_mode.set(modes[1 - modes.index(self.phase_render_mode.value)])
