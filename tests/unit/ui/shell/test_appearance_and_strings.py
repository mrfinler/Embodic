"""Appearance view-model, toolstrip strings and the string catalogue (UI-25, UI-26, UI-27). Qt-free."""

import pytest

from embodic.ui.strings import STRINGS, merge
from embodic.ui.theme import ThemeName
from embodic.ui.toolstrip import TOOLSTRIP, ToolstripTab
from embodic.ui.viewmodels.appearance import AppearanceViewModel, PhaseRenderMode


class MemoryStore:
    """Settings store that lives as long as the test."""

    def __init__(self, value=None):
        self.value = value

    def load_theme(self):
        """Return the stored choice."""
        return self.value

    def save_theme(self, value):
        """Store a choice."""
        self.value = value


@pytest.mark.req("REQ-N-27")
def test_ui26_cycle_theme_visits_light_dark_system_and_the_choice_survives_a_restart():
    """Catches a cycle that skips 'system' or a choice that is shown but never stored."""
    store = MemoryStore(ThemeName.LIGHT.value)
    appearance = AppearanceViewModel(store)
    seen = []
    appearance.theme.subscribe(seen.append)
    for _ in range(3):
        appearance.cycle_theme()
    assert seen == [ThemeName.DARK, ThemeName.SYSTEM, ThemeName.LIGHT]
    appearance.cycle_theme()
    assert AppearanceViewModel(store).theme.value is ThemeName.DARK


@pytest.mark.req("REQ-N-27")
@pytest.mark.parametrize("stored", [None, "sepia"])
def test_ui26_no_or_unknown_stored_choice_follows_the_system(stored):
    """Catches a crash or a forced light theme on first start or after a settings file from another version."""
    assert AppearanceViewModel(MemoryStore(stored)).theme.value is ThemeName.SYSTEM


@pytest.mark.req("REQ-N-23")
def test_ui27_render_mode_toggles_between_colour_and_greyscale_hatch():
    """Catches a toggle that sticks in one mode."""
    appearance = AppearanceViewModel(MemoryStore())
    assert appearance.phase_render_mode.value is PhaseRenderMode.COLOUR
    appearance.toggle_phase_render_mode()
    assert appearance.phase_render_mode.value is PhaseRenderMode.GREYSCALE_HATCH
    appearance.toggle_phase_render_mode()
    assert appearance.phase_render_mode.value is PhaseRenderMode.COLOUR


@pytest.mark.req("REQ-F-39")
def test_ui25_every_toolstrip_action_tab_and_group_has_english_text():
    """Catches a new TOOLSTRIP row without its label, tooltip, group caption or tab caption."""
    keys = [f"{a.id}.{role}" for a in TOOLSTRIP for role in ("label", "tooltip")]
    keys += [f"toolstrip.group-{a.group}.label" for a in TOOLSTRIP]
    keys += [f"toolstrip.tab-{tab.value}.label" for tab in ToolstripTab]
    assert [key for key in keys if not STRINGS.get(key, "").strip()] == []
    assert all(STRINGS[f"{a.id}.tooltip"].endswith(".") for a in TOOLSTRIP)


@pytest.mark.req("REQ-F-39")
def test_ui25_toolstrip_ids_and_commands_are_unique():
    """Catches two buttons sharing an objectName or a command."""
    assert len({a.id for a in TOOLSTRIP}) == len(TOOLSTRIP)
    assert len({a.command for a in TOOLSTRIP}) == len(TOOLSTRIP)


@pytest.mark.req("REQ-L-01")
def test_string_tables_with_one_key_twice_are_refused():
    """Catches a later area's table silently overriding a shell string."""
    with pytest.raises(ValueError, match=r"act-new\.label"):
        merge({"act-new.label": "New"}, {"act-new.label": "Create"})
