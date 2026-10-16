"""Editing an open design: undo history, issue navigation, suggestions, stale drawing, hints, recovery.

UI-11, UI-14, UI-15, UI-18, UI-19, UI-21 (Phase 1 test plan, carried into Phase 2).
"""

import dataclasses
import sys

import pytest
from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QApplication, QListWidget, QMessageBox
from tests.ui.qt_design.conftest import enter, find

from embodic.io.canonical import design_hash
from embodic.io.examples import load_example
from embodic.io.project import ProjectFile, save_project
from embodic.model.draft import parse_draft
from embodic.model.provenance import ExampleValue
from embodic.model.vocabulary import TopologyKind
from embodic.ui import app as app_module
from embodic.ui.app import unrecovered_autosave
from embodic.ui.viewmodels.session import SessionComputed, SessionDrafting, SessionEmpty
from embodic.ui.views.main_window import ShellPaths

D08 = "spiral_12c10p_d08"


def no_compute(design, provenance, **kwargs):
    """Stand in for the engine where a test needs no result: the worker treats None as cancelled."""
    return None


def session_hash(window):
    """Return the design hash of the window's open document."""
    return design_hash(parse_draft(window.session.document.draft))


def issue_item(window, code):
    """Return the issues-list row of an issue code."""
    issues: QListWidget = find(window, "issues-list")
    for row in range(issues.count()):
        found = issues.item(row).data(Qt.ItemDataRole.UserRole)
        if getattr(found, "code", None) == code:
            return issues.item(row)
    raise AssertionError(f"{code} not listed")


@pytest.mark.req("REQ-F-22")
def test_ui11_fifty_undo_and_redo_steps_through_the_toolstrip_restore_the_hash(make_shell, qtbot):
    """Catches an undo that skips steps, stops early, or leaves the form showing a value the design no longer has."""
    window = make_shell(compute_fn=no_compute).window
    window.session.load_example(D08)
    loaded = session_hash(window)
    undo, redo = (window.toolstrip.actions_by_id[name] for name in ("act-undo", "act-redo"))
    for step in range(50):
        enter(qtbot, window, "param-speed", str(1500 + step))
    edited = session_hash(window)
    assert find(window, "param-speed").text() == "1549"
    for _ in range(50):
        assert undo.isEnabled()
        undo.trigger()
    assert session_hash(window) == loaded
    assert find(window, "param-speed").text() == "1000"
    assert all(isinstance(chip, ExampleValue) for chip in window.session.chips().values())
    assert not undo.isEnabled()
    for _ in range(50):
        redo.trigger()
    assert (session_hash(window), find(window, "param-speed").text(), redo.isEnabled()) == (edited, "1549", False)


@pytest.mark.req("REQ-F-14")
def test_ui14_selecting_an_issue_opens_its_tab_and_focuses_the_input(make_shell, qtbot):
    """Catches an issue list whose rows lead nowhere, or that focuses a widget on another tab than the field's."""
    window = make_shell(compute_fn=no_compute).window
    window.session.load_example(D08)
    enter(qtbot, window, "param-r-inner", "50")
    window.inspector_tabs.setCurrentWidget(window.panels["tab-board"])
    find(window, "param-air-gap").setFocus()
    item = issue_item(window, "INVALID_ORDER")
    issues = find(window, "issues-list")
    qtbot.mouseClick(issues.viewport(), Qt.MouseButton.LeftButton, pos=issues.visualItemRect(item).center())
    assert window.inspector_tabs.currentWidget() is window.panels["tab-coil"]
    assert item.data(Qt.ItemDataRole.UserRole).pointers[0] == "/winding/coil/r_inner_mm"
    assert window.focusWidget().objectName() == "param-r-inner"


@pytest.mark.req("REQ-F-23")
def test_ui15_no_silent_rewrite_the_suggestion_applies_only_on_apply_with_notice_and_undo(make_shell, qtbot):
    """Catches a clamp applied while typing, an Apply without the inline notice, or a notice whose Undo fails."""
    window = make_shell(compute_fn=no_compute).window
    window.session.load_example(D08)
    enter(qtbot, window, "param-air-gap", "60")
    typed = session_hash(window)
    assert find(window, "param-air-gap").text() == "60"
    assert not find(window, "design-notice").isVisibleTo(window)
    apply = find(window, "btn-apply-suggestion")
    issues = find(window, "issues-list")
    issues.setCurrentItem(issue_item(window, "RANGE_ABOVE_SUPPORTED"))
    assert apply.isVisibleTo(window) and apply.text() == "Apply 50"
    assert session_hash(window) == typed
    qtbot.mouseClick(apply, Qt.MouseButton.LeftButton)
    assert find(window, "param-air-gap").text() == "50"
    assert session_hash(window) != typed
    notice = find(window, "design-notice")
    assert notice.isVisibleTo(window)
    expected = "Changed from 60 to 50: Values outside the supported range move to the nearest limit."
    assert find(window, "design-notice-text").text() == expected
    qtbot.mouseClick(find(window, "btn-notice-undo"), Qt.MouseButton.LeftButton)
    assert (find(window, "param-air-gap").text(), session_hash(window)) == ("60", typed)
    assert not notice.isVisibleTo(window)


@pytest.mark.req("REQ-F-27")
def test_ui18_an_emptied_field_keeps_the_last_drawing_marked_outdated(make_shell, qtbot, wait_computed):
    """Catches a canvas cleared by an incomplete edit, or a kept drawing that is not marked outdated."""
    shell = make_shell()
    window = shell.window
    window.session.load_example(D08)
    wait_computed(window)
    drawn = len(window.canvas.scene().items())
    assert drawn > 0
    stale = find(window, "fig-stale")
    assert not stale.isVisibleTo(window)
    enter(qtbot, window, "param-r-inner", "")
    assert isinstance(window.session.state.value, SessionDrafting)
    assert stale.isVisibleTo(window)
    assert stale.text() == "Outdated: the drawing shows the last complete design. 1 required fields left."
    assert len(window.canvas.scene().items()) == drawn
    assert len(shell.calls) == 1
    enter(qtbot, window, "param-r-inner", "11.47")
    wait_computed(window)
    assert not stale.isVisibleTo(window)


@pytest.mark.req("REQ-F-28")
def test_ui19_feasibility_hints_follow_the_winding_plan_after_each_recompute(make_shell, qtbot, wait_computed):
    """Catches hints left from the previous design, or hints that disagree with the generator's plan."""
    window = make_shell().window
    window.session.load_example(D08)
    wait_computed(window)
    combination = find(window, "hint-combination")
    # 12 coils, 10 poles: q = 12/(3*10)
    assert combination.text() == "Symmetric 3-phase pattern: q = 2/5, periodicity t = 1."
    detail = window.session.state.value.outcome.boards.boards[0].detail
    assert find(window, "phase-pattern-string").text() == detail.plan.pattern
    assert find(window, "param-turns-hint").text() == (
        f"Built {detail.turns_achieved} turns per coil; limited by the {detail.turn_limit.limiting_reason.value} bound."
    )
    enter(qtbot, window, "param-coil-count", "9")
    wait_computed(window)
    assert window.session.state.value.design.winding.coil.coil_count == 9
    # 9 coils, 10 poles: q = 9/(3*10)
    assert combination.text() == "Symmetric 3-phase pattern: q = 3/10, periodicity t = 1."
    assert len(find(window, "phase-pattern-string").text()) == 9


@pytest.mark.req("REQ-F-31")
def test_ui21_after_an_unclean_exit_the_next_start_offers_recovery_with_the_identical_hash(make_shell, qtbot, tmp_path):
    """Catches an edit that is not autosaved, a start that does not offer it, or a recovery with another design."""
    recovery = tmp_path / "shared-recovery"
    first = make_shell(compute_fn=no_compute, recovery_dir=recovery).window
    first.session.load_example(D08)
    enter(qtbot, first, "param-speed", "1234")
    expected = session_hash(first)
    chips = dict(first.session.chips())
    autosave = unrecovered_autosave(ShellPaths(recovery_dir=recovery))
    assert autosave is not None
    second = make_shell(compute_fn=no_compute, recovery_dir=recovery).window
    assert isinstance(second.session.state.value, SessionEmpty)
    dialog = second.offer_recovery(autosave)
    assert isinstance(dialog, QMessageBox) and dialog.objectName() == "dlg-recovery"
    qtbot.mouseClick(find(dialog, "btn-recover"), Qt.MouseButton.LeftButton)
    assert isinstance(second.session.state.value, SessionComputed)
    assert session_hash(second) == expected != design_hash(load_example(D08)[1])
    assert second.session.chips() == chips
    second.close()
    assert unrecovered_autosave(ShellPaths(recovery_dir=recovery)) is None


@pytest.mark.req("REQ-F-21")
def test_ui22_typing_the_d08_air_gap_back_to_1_1_shows_the_example_chip(make_shell, qtbot):
    """Catches DEF-1: the D08 file held 1.0999999999999999, so typing the shown 1.1 back left the chip on user."""
    window = make_shell(compute_fn=no_compute).window
    window.session.load_example(D08)
    chip = find(window, "param-air-gap-prov")
    enter(qtbot, window, "param-air-gap", "1.2")
    assert chip.text() == "user"
    enter(qtbot, window, "param-air-gap", "1.1")
    assert (find(window, "param-air-gap").text(), chip.text()) == ("1.1", "example")


@pytest.mark.req("REQ-F-27")
def test_ui18_a_new_design_starts_with_an_empty_canvas(make_shell, wait_computed):
    """Catches a blank design drawn with the previous design's copper under an 'outdated' label."""
    window = make_shell().window
    window.session.load_example(D08)
    wait_computed(window)
    assert window.canvas.scene().items()
    window.session.new_design(TopologyKind.SPIRAL)
    assert not window.canvas.scene().items()
    assert not find(window, "fig-stale").isVisibleTo(window)


@pytest.mark.req("REQ-F-31")
def test_ui21_main_offers_recovery_of_the_autosave_left_by_an_unclean_exit(qtbot, tmp_path, monkeypatch):
    """Catches main() starting without the recovery offer, or a recovery that opens another design than the autosave."""
    ref, design = load_example(D08)
    edited = dataclasses.replace(design, operating=dataclasses.replace(design.operating, speed_rpm=1234.0))
    data_dir = tmp_path / "data"
    autosave = data_dir / "recovery" / "autosave.embodic.json"
    autosave.parent.mkdir(parents=True)
    save_project(autosave, ProjectFile(design=edited, origin=ref))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    monkeypatch.setattr(app_module, "app_data_dir", lambda: data_dir)
    monkeypatch.setattr(app_module, "setup_logging", lambda log_dir: log_dir)
    store = app_module.QSettingsStore
    monkeypatch.setattr(app_module, "QSettingsStore", lambda: store(settings))
    monkeypatch.setattr(sys, "excepthook", sys.excepthook)
    shells = []
    create_shell = app_module.create_shell
    monkeypatch.setattr(app_module, "create_shell", lambda *args: shells.append(create_shell(*args)) or shells[-1])
    seen = {}

    def run_event_loop(app):
        window = shells[0].window
        qtbot.addWidget(window)
        dialog = window.findChild(QMessageBox, "dlg-recovery")
        seen["offered"] = dialog is not None and dialog.isVisible()
        if dialog is not None:
            qtbot.mouseClick(find(dialog, "btn-recover"), Qt.MouseButton.LeftButton)
        seen["hash"] = session_hash(window) if window.session.document is not None else None
        return 0

    monkeypatch.setattr(QApplication, "exec", run_event_loop)
    assert app_module.main([]) == 0
    assert seen == {"offered": True, "hash": design_hash(edited)}
    assert design_hash(edited) != design_hash(design)
