"""The phase render mode is one enum shared by the view-model and the writers (D-038a)."""

import pytest

from embodic.io.exporters import PhaseRenderMode
from embodic.ui.viewmodels.appearance import AppearanceViewModel

pytestmark = pytest.mark.req("REQ-N-23")


class _MemoryStore:
    def load_theme(self) -> str | None:
        return None

    def save_theme(self, value: str) -> None:
        pass


def test_the_view_model_hands_the_writers_their_own_enum_member() -> None:
    """Catches a second PhaseRenderMode enum: the writers test the mode with `is`, so a copy would draw colour."""
    model = AppearanceViewModel(_MemoryStore())
    assert model.phase_render_mode.value is PhaseRenderMode.COLOUR
    model.toggle_phase_render_mode()
    assert model.phase_render_mode.value is PhaseRenderMode.GREYSCALE_HATCH
