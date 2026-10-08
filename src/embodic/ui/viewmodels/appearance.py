"""Theme choice and phase render mode, persisted through an injected store (QSettings in the app)."""

from typing import Protocol

from embodic.io.exporters import PhaseRenderMode
from embodic.ui.theme import ThemeName
from embodic.ui.viewmodels.observable import Observable

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


class AppearanceViewModel:
    """Theme choice (light, dark, system) and the phase render mode of the geometry view."""

    def __init__(self, store: AppearanceStore) -> None:
        self._store = store
        stored = store.load_theme()
        initial = ThemeName(stored) if stored in tuple(ThemeName) else ThemeName.SYSTEM
        self.theme: Observable[ThemeName] = Observable(initial)
        self.phase_render_mode: Observable[PhaseRenderMode] = Observable(PhaseRenderMode.COLOUR)

    def set_theme(self, choice: ThemeName) -> None:
        """Show and remember a theme choice."""
        self.theme.set(choice)
        self._store.save_theme(choice.value)

    def cycle_theme(self) -> None:
        """Move to the next choice: light, dark, system, light."""
        self.set_theme(THEME_CYCLE[self.theme.value])

    def toggle_phase_render_mode(self) -> None:
        """Switch between colour and greyscale with hatching."""
        modes = tuple(PhaseRenderMode)
        self.phase_render_mode.set(modes[1 - modes.index(self.phase_render_mode.value)])
