"""Start state and toolstrip of the shell window (UI-23, UI-25, AX-09 inputs)."""

import logging

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QToolButton

from embodic.io.examples import list_examples
from embodic.ui.strings import STRINGS
from embodic.ui.theme import ThemeName
from embodic.ui.toolstrip import TOOLSTRIP, ToolstripTab
from embodic.ui.views.style import icons_dir
from embodic.ui.views.toolstrip_bar import ToolstripBar, UnknownCommandError

IMPLEMENTED = {"save_project", "show_examples", "compute_now", "cycle_theme", "toggle_phase_render_mode", "fit_view"}
IMPLEMENTED |= {"new_design", "set_connection_star", "set_connection_delta"}  # U-M4c session commands
IMPLEMENTED |= {f"set_topology_{name}" for name in ("spiral", "serpentine", "wave")}
DISABLED_UNTIL_UNDO = {"undo", "redo"}  # U-M4c: enabled once the session has history


@pytest.mark.req("REQ-F-21")
def test_ui23_window_opens_empty_with_new_design_and_examples_and_runs_no_compute(make_shell, qtbot):
    """Catches a start that opens a default design or computes before the user chose anything (D-014)."""
    shell = make_shell()
    window = shell.window
    qtbot.wait(50)
    assert window.centre.currentWidget().objectName() == "empty-state"
    new, examples = window.empty_new, window.empty_examples
    assert (new.objectName(), new.text(), new.isVisible()) == ("btn-empty-new", "New design", True)
    assert (examples.objectName(), examples.text(), examples.isEnabled()) == ("btn-empty-examples", "Examples", True)
    menu_ids = [a.objectName() for a in window.examples_menu().actions()]
    assert menu_ids == [f"example-{info.example_id}" for info in list_examples()]
    assert "example-spiral_12c10p_d08" in menu_ids
    assert shell.calls == []
    assert window.status["st-compute"].text() == "Ready"


@pytest.mark.req("REQ-F-39")
def test_ui25_every_action_has_label_tooltip_accessible_name_and_a_resolved_command(make_shell):
    """Catches a button without English text or accessible name, or a command that silently does nothing."""
    toolstrip = make_shell().window.toolstrip
    for row in TOOLSTRIP:
        button = toolstrip.findChild(QToolButton, row.id)
        label = STRINGS[f"{row.id}.label"]
        assert button is not None, row.id
        assert (button.text(), button.accessibleName()) == (label, label)
        assert button.toolTip().startswith(f"{label} ({row.shortcut})." if row.shortcut else f"{label}.")
        assert button.isEnabled() is (row.command in IMPLEMENTED), row.id
        if row.command not in IMPLEMENTED | DISABLED_UNTIL_UNDO:
            assert button.toolTip().endswith("Not available in this version."), row.id
        if row.shortcut:
            assert toolstrip.actions_by_id[row.id].shortcut().toString() == row.shortcut


@pytest.mark.req("REQ-F-39")
def test_ui25_a_command_no_view_model_offers_is_a_startup_error(qapp):
    """Catches a TOOLSTRIP row whose command name is misspelled being accepted at startup."""
    commands = {row.command: None for row in TOOLSTRIP if row.command != "fit_view"}
    with pytest.raises(UnknownCommandError, match="fit_view"):
        ToolstripBar(commands)


@pytest.mark.req("REQ-F-39")
def test_ui25_every_toolstrip_action_has_its_icon_file():
    """Catches a TOOLSTRIP icon stem with no SVG in resources/icons."""
    assert [row.icon for row in TOOLSTRIP if not (icons_dir() / f"{row.icon}.svg").is_file()] == []


@pytest.mark.req("REQ-F-39")
def test_ui25_a_missing_icon_logs_a_warning_and_the_button_shows_its_label(make_shell, caplog, monkeypatch, tmp_path):
    """Catches a crash or a blank button when an icon file is absent."""
    monkeypatch.setattr("embodic.ui.views.style.icons_dir", lambda: tmp_path)
    with caplog.at_level(logging.WARNING, logger="embodic.ui.views.style"):
        window = make_shell().window
    button = window.toolstrip.buttons["act-fit"]
    assert button.toolButtonStyle() == Qt.ToolButtonStyle.ToolButtonTextOnly
    assert button.text() == "Fit"
    assert "icon zoom-fit.svg is missing" in caplog.text


@pytest.mark.req("REQ-F-39", "REQ-N-12")
def test_ui25_arrow_keys_move_focus_within_a_tab_and_wrap(make_shell, qtbot):
    """Catches arrow keys that do nothing or leave the tab."""
    window = make_shell().window
    window.activateWindow()
    toolstrip = window.toolstrip
    toolstrip.show_tab(ToolstripTab.VIEW)
    theme, greyscale, fit = (toolstrip.buttons[i] for i in ("act-theme", "act-greyscale", "act-fit"))
    theme.setFocus()
    qtbot.waitUntil(theme.hasFocus)
    for key, expected in ((Qt.Key.Key_Right, greyscale), (Qt.Key.Key_Right, fit), (Qt.Key.Key_Right, theme)):
        qtbot.keyClick(window.focusWidget(), key)
        assert window.focusWidget() is expected
    qtbot.keyClick(window.focusWidget(), Qt.Key.Key_Left)
    assert window.focusWidget() is fit
    qtbot.keyClick(window.focusWidget(), Qt.Key.Key_Home)
    assert window.focusWidget() is theme


def _ink(button):
    """Return the set of opaque colours of a button's 24 px normal-mode icon."""
    image = button.icon().pixmap(24, 24).toImage()
    colours = set()
    for x in range(image.width()):
        for y in range(image.height()):
            pixel = image.pixelColor(x, y)
            if pixel.alpha() == 255:
                colours.add(pixel.name())
    return colours


@pytest.mark.req("REQ-F-39")
def test_ui25_icons_recolour_after_a_theme_switch(make_shell):
    """Catches icons that keep the light theme's ink on the dark toolstrip (AX-09 then fails)."""
    window = make_shell().window
    button = window.toolstrip.buttons["act-save"]
    window.appearance.set_theme(ThemeName.LIGHT)
    assert _ink(button) == {QColor("#141414").name()}
    window.appearance.set_theme(ThemeName.DARK)
    assert _ink(button) == {QColor("#f2f2f2").name()}
