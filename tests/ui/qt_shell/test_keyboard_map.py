"""Keyboard map keys, Tab stop names and the EQ chip role, driven with key events on the real shell.

DEF-U-S7-01 found keys of design_spec.md section 10 unbound; DEF-U-S7-02 and DEF-U-S7-03 found a missing accessible
name and a wrong role (WCAG 4.1.2).
"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QAccessible, QAccessibleActionInterface
from PySide6.QtWidgets import QApplication, QCheckBox, QDialog, QFileDialog, QWidget

from embodic.model.vocabulary import TopologyKind
from embodic.ui.theme import ThemeName
from embodic.ui.views.examples_gallery import ExamplesGallery
from embodic.ui.views.status_badge import EqChip

from .conftest import D08

KEY, MOD = Qt.Key, Qt.KeyboardModifier
REGIONS = ("toolstrip", "inspector", "inspector-tabs", "fig-canvas", "results-tabs", "results-rail", "statusbar")


@pytest.fixture
def opened(make_shell, wait_ready, qtbot):
    """Return a shell with D08 opened the way the gallery opens it, computed, active, focus on the toolstrip tabs."""
    shell = make_shell()
    window = shell.window
    window.session.load_example(D08)
    wait_ready(window)
    window.activateWindow()
    qtbot.waitUntil(window.isActiveWindow)
    window.findChild(QWidget, "toolstrip-tabs").setFocus()
    return window


def press(qtbot, key: Qt.Key, modifier: Qt.KeyboardModifier = MOD.NoModifier) -> None:
    """Send one key to the focused widget, as a keyboard does."""
    qtbot.keyClick(QApplication.focusWidget(), key, modifier)


def region_of(widget: QWidget | None) -> str:
    """Return the innermost design_spec.md section 5 region that holds ``widget``."""
    while widget is not None and widget.objectName() not in REGIONS:
        widget = widget.parentWidget()
    return "-" if widget is None else widget.objectName()


def accessible_name(widget: QWidget) -> str:
    """Return the name a screen reader announces for ``widget``."""
    return QAccessible.queryAccessibleInterface(widget).text(QAccessible.Text.Name)


@pytest.mark.req("REQ-N-12")
def test_alt_1_to_alt_4_bring_the_inspector_tabs_coil_phases_layers_board_forward(opened, qtbot):
    """Catches a missing Alt+1 ... Alt+4 binding, or one that opens the wrong tab (design_spec.md section 10)."""
    for key, tab in ((KEY.Key_4, "tab-board"), (KEY.Key_3, "tab-layers"), (KEY.Key_2, "tab-phases")):
        press(qtbot, key, MOD.AltModifier)
        assert opened.inspector_tabs.currentWidget().objectName() == tab
    press(qtbot, KEY.Key_1, MOD.AltModifier)
    assert opened.inspector_tabs.currentWidget().objectName() == "tab-coil"


@pytest.mark.req("REQ-N-12")
def test_ctrl_shift_t_switches_the_theme_as_the_theme_button_does(opened, qtbot):
    """Catches Ctrl+Shift+T doing nothing (UX-AC-06): from the light theme it switches to dark, then on."""
    opened.appearance.set_theme(ThemeName.LIGHT)
    press(qtbot, KEY.Key_T, MOD.ControlModifier | MOD.ShiftModifier)
    assert opened.appearance.theme.value is ThemeName.DARK
    assert opened.tokens.name == "dark"


@pytest.mark.req("REQ-N-12")
def test_ctrl_shift_n_opens_the_examples_gallery(make_shell, qtbot):
    """Catches Ctrl+Shift+N doing nothing at the start screen, where Examples is the first thing a user wants."""
    window = make_shell().window
    window.activateWindow()
    qtbot.waitUntil(window.isActiveWindow)
    window.empty_examples.setFocus()
    press(qtbot, KEY.Key_N, MOD.ControlModifier | MOD.ShiftModifier)
    qtbot.waitUntil(lambda: isinstance(QApplication.activeModalWidget(), ExamplesGallery))
    QApplication.activeModalWidget().close()


@pytest.mark.req("REQ-N-12")
def test_ctrl_shift_s_asks_for_a_file_name_and_saves_the_project(opened, qtbot, tmp_path, monkeypatch):
    """Catches Ctrl+Shift+S doing nothing (DEF-US17-02): design_spec.md section 10 binds it to Save as."""
    target = tmp_path / "saved.embodic.json"
    asked = []

    def choose(*args, **kwargs):
        asked.append(args)
        return str(target), ""

    monkeypatch.setattr(QFileDialog, "getSaveFileName", choose)
    press(qtbot, KEY.Key_S, MOD.ControlModifier | MOD.ShiftModifier)
    assert len(asked) == 1
    assert target.is_file()


@pytest.mark.req("REQ-N-12")
def test_ctrl_shift_z_redoes_the_last_undone_edit(opened, qtbot):
    """Catches Ctrl+Shift+Z doing nothing (DEF-US17-02): design_spec.md section 10 binds it to Redo beside Ctrl+Y."""
    session, pointer = opened.session, "/connection/topology"
    before = session.document.draft.values[pointer]
    other = "delta" if before == "star" else "star"
    session.edit(pointer, other)
    session.undo()
    assert session.document.draft.values[pointer] == before
    assert session.can_redo.value
    press(qtbot, KEY.Key_Z, MOD.ControlModifier | MOD.ShiftModifier)
    assert session.document.draft.values[pointer] == other
    assert not session.can_redo.value


@pytest.mark.req("REQ-N-12")
def test_ctrl_p_opens_the_export_dialog_with_the_report_checked(opened, qtbot):
    """Catches Ctrl+P doing nothing (DEF-US17-02): design_spec.md section 10 binds it to Report, the PDF report."""
    press(qtbot, KEY.Key_P, MOD.ControlModifier)
    dialog = opened.findChild(QDialog, "dlg-export")
    assert dialog is not None and dialog.isVisible()
    checked = {box.objectName() for box in dialog.findChildren(QCheckBox) if box.isChecked()}
    assert checked == {"export-format-pdf"}
    dialog.close()


@pytest.mark.req("REQ-N-12")
def test_ctrl_slash_opens_the_guide_at_the_keyboard_shortcuts(opened, qtbot):
    """Catches Ctrl+/ doing nothing (DEF-US17-02): design_spec.md section 10 binds it to Shortcuts."""
    press(qtbot, KEY.Key_Slash, MOD.ControlModifier)
    guide = opened.guide
    assert guide is not None and guide.isVisible()
    assert guide.current_topic() == "guide:keys"
    guide.close()


@pytest.mark.req("REQ-N-12")
def test_f6_and_shift_f6_cycle_the_regions_in_design_spec_order(opened, qtbot):
    """Catches F6 doing nothing, skipping a region that holds a focus stop, or a cycle out of the section 5 order.

    With D08 open the inspector's only stops are inside inspector-tabs and the status bar holds none, so the cycle has
    five stops (the inspector stop of its own is the next test).
    """
    forward = []
    for _ in range(5):
        press(qtbot, KEY.Key_F6)
        forward.append(region_of(QApplication.focusWidget()))
    assert forward == ["inspector-tabs", "fig-canvas", "results-tabs", "results-rail", "toolstrip"]
    backward = []
    for _ in range(5):
        press(qtbot, KEY.Key_F6, MOD.ShiftModifier)
        backward.append(region_of(QApplication.focusWidget()))
    assert backward == ["results-rail", "results-tabs", "fig-canvas", "inspector-tabs", "toolstrip"]


@pytest.mark.req("REQ-N-12")
def test_f6_stops_at_the_inspector_before_its_tabs_while_required_fields_are_missing(make_shell, qtbot):
    """Catches F6 jumping past `btn-first-missing`, the inspector's own stop while a new design lacks values."""
    window = make_shell().window
    window.session.new_design(TopologyKind.SPIRAL)
    window.activateWindow()
    qtbot.waitUntil(window.isActiveWindow)
    window.findChild(QWidget, "toolstrip-tabs").setFocus()
    press(qtbot, KEY.Key_F6)
    assert QApplication.focusWidget().objectName() == "btn-first-missing"
    press(qtbot, KEY.Key_F6)
    assert region_of(QApplication.focusWidget()) == "inspector-tabs"


@pytest.mark.req("REQ-N-12", "REQ-N-16")
def test_every_tab_stop_with_d08_open_has_an_accessible_name(opened, qtbot):
    """Catches a Tab stop that a screen reader announces with no name (DEF-U-S7-02 found three)."""
    first, unnamed = QApplication.focusWidget(), []
    for _ in range(400):
        widget = QApplication.focusWidget()
        if not accessible_name(widget).strip():
            unnamed.append(widget.objectName() or type(widget).__name__)
        press(qtbot, KEY.Key_Tab)
        if QApplication.focusWidget() is first:
            break
    assert QApplication.focusWidget() is first, "the Tab chain comes back to its first stop"
    assert unnamed == []


@pytest.mark.req("REQ-N-16")
def test_scroll_areas_and_the_issues_list_take_the_titles_users_read(opened):
    """Catches a name that differs from the visible title (screens.md sections 6, 6.1 and 10).

    `compare-scroll` is a Tab stop of the same kind on the Compare page, which the D08 walk above does not open.
    """
    scrolls = ("rail-scroll", "results-scroll", "compare-scroll")
    names = {name: accessible_name(opened.findChild(QWidget, name)) for name in scrolls}
    names["issues-list"] = accessible_name(opened.issues_list)
    assert names == {
        "rail-scroll": "Key results",
        "results-scroll": "Results",
        "compare-scroll": "Compare",
        "issues-list": "Input issues",
    }


@pytest.mark.req("REQ-N-16")
def test_eq_chips_are_links_that_open_the_register_and_kind_tags_stay_text(opened, qtbot):
    """Catches an EQ chip announced as static text (screens.md section 6 says link), or a dead press action."""
    chips = opened.findChildren(EqChip)
    links = [chip for chip in chips if chip.eq_id is not None]
    assert links, "D08 shows EQ chips"
    roles = {QAccessible.queryAccessibleInterface(chip).role() for chip in links}
    assert roles == {QAccessible.Role.Link}
    tags = [chip for chip in chips if chip.eq_id is None]
    assert {QAccessible.queryAccessibleInterface(chip).role() for chip in tags} <= {QAccessible.Role.StaticText}
    chip = next(c for c in links if c.objectName() == "res-r-phase-eq")
    face = QAccessible.queryAccessibleInterface(chip)
    assert face.text(QAccessible.Text.Name) == f"Equation {chip.eq_id}, opens the equation register"
    with qtbot.waitSignal(chip.activated, timeout=1000) as opened_entry:
        face.actionInterface().doAction(QAccessibleActionInterface.pressAction())
    assert opened_entry.args == [chip.eq_id]
