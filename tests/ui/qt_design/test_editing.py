"""Editing an open design: undo history, issue navigation, suggestions, stale drawing, hints, recovery.

UI-11, UI-14, UI-15, UI-18, UI-19, UI-21 (Phase 1 test plan, carried into Phase 2).
"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidget, QMessageBox
from tests.ui.qt_design.conftest import enter, find

from embodic.io.canonical import design_hash
from embodic.io.examples import load_example
from embodic.model.draft import parse_draft
from embodic.model.provenance import ExampleValue
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
    expected = "Changed from 60 to 50: Xcoil clamps to the supported range."
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
    assert combination.text() == "Balanced: q = 2/5, periodicity t = 1."  # 12 coils, 10 poles: q = 12/(3*10)
    detail = window.session.state.value.outcome.boards.boards[0].detail
    assert find(window, "phase-pattern-string").text() == detail.plan.pattern
    assert find(window, "param-turns-hint").text() == (
        f"Built {detail.turns_achieved} turns per coil; limited by the {detail.turn_limit.limiting_reason.value} bound."
    )
    enter(qtbot, window, "param-coil-count", "9")
    wait_computed(window)
    assert window.session.state.value.design.winding.coil.coil_count == 9
    assert combination.text() == "Balanced: q = 3/10, periodicity t = 1."  # 9 coils, 10 poles: q = 9/(3*10)
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
