"""DesignSession typing preview (REQ-N-02, fix_wave_f1.md (a)). Qt-free.

A debounced preview changes only the drawing and the results; a commit after it reuses its request; Esc brings the
committed outcome back.

A manual debounce stands in for the window's QTimer, and a recording submitter for the worker; a test delivers a
result by calling `OutcomeViewModel.on_finished` as the worker's signal does.
"""

import dataclasses

import pytest

from embodic.api import compute
from embodic.io.examples import load_example
from embodic.io.project import ProjectFile, project_provenance, save_project
from embodic.model.provenance import DefaultValue
from embodic.ui.viewmodels.outcome import OutcomeComputing, OutcomeReady, OutcomeViewModel, ready_state
from embodic.ui.viewmodels.session import DesignSession, SessionComputed, SessionEmpty

D08 = "spiral_12c10p_d08"
R_INNER = "/winding/coil/r_inner_mm"


class ManualDebounce:
    """A wait that ends when the test says so."""

    def __init__(self):
        self.action = None

    def start(self, action):
        """Hold the action."""
        self.action = action

    def stop(self):
        """Drop the action."""
        self.action = None

    def expire(self):
        """End the wait: run the held action."""
        action, self.action = self.action, None
        assert action is not None, "no wait is running"
        action()


class RecordingSubmitter:
    """Keeps every request and every cancel instead of running them."""

    def __init__(self):
        self.requests = []
        self.cancels = 0

    def submit(self, request):
        """Record a request."""
        self.requests.append(request)

    def cancel(self):
        """Count a cancel."""
        self.cancels += 1


@pytest.fixture
def rig(tmp_path):
    """Return (session, outcome view-model, submitter, debounce, autosave path) with D08 open and computed."""
    submitter, debounce = RecordingSubmitter(), ManualDebounce()
    outcome = OutcomeViewModel(submitter)
    autosave = tmp_path / "autosave.embodic.json"
    session = DesignSession(outcome, autosave_path=autosave, debounce=debounce)
    session.load_example(D08)
    deliver(outcome, submitter)
    return session, outcome, submitter, debounce, autosave


def deliver(outcome, submitter):
    """Run the latest request for real and hand its result back as the worker does."""
    request = submitter.requests[-1]
    outcome.on_finished(request.request_id, ready_state(compute(request.design, request.provenance)))


def r_inner(design) -> float:
    """Return the coil inner radius of a design."""
    return design.winding.coil.r_inner_mm


@pytest.mark.req("REQ-N-02")
def test_a_keystroke_computes_nothing_until_the_wait_ends(rig):
    """Catches a compute per keystroke: only the end of the wait submits, with the typed value."""
    session, _, submitter, debounce, _ = rig
    before = len(submitter.requests)
    session.type_text(R_INNER, 11.4)
    session.type_text(R_INNER, 11.48)
    assert len(submitter.requests) == before
    debounce.expire()
    assert [r_inner(r.design) for r in submitter.requests[before:]] == [11.48]


@pytest.mark.req("REQ-N-02")
def test_a_preview_changes_the_drawing_but_not_the_committed_state_undo_or_autosave(rig):
    """Catches a preview that commits: it must leave the state, the chips, undo and the autosave file alone."""
    session, outcome, submitter, debounce, autosave = rig
    committed, saved = session.state.value, autosave.read_bytes()
    session.type_text(R_INNER, 11.48)
    debounce.expire()
    deliver(outcome, submitter)
    shown, outdated = session.drawn(outcome.state.value)
    assert (r_inner(shown.outcome.design), outdated) == (11.48, False)
    assert session.state.value == committed
    assert autosave.read_bytes() == saved
    session.undo()
    assert isinstance(session.state.value, SessionEmpty), "the preview wrote no undo entry"


@pytest.mark.req("REQ-N-02")
@pytest.mark.parametrize("arrived", [True, False], ids=["result shown", "request in flight"])
def test_commit_after_a_preview_reuses_its_request(rig, arrived):
    """Catches a commit that computes the previewed design a second time."""
    session, outcome, submitter, debounce, _ = rig
    session.type_text(R_INNER, 11.48)
    debounce.expire()
    if arrived:
        deliver(outcome, submitter)
    before = len(submitter.requests)
    session.edit(R_INNER, 11.48)
    assert len(submitter.requests) == before
    if not arrived:
        deliver(outcome, submitter)
    state = session.state.value
    assert isinstance(state, SessionComputed) and not state.computing
    assert r_inner(state.outcome.design) == 11.48
    assert session.drawn(outcome.state.value)[0].outcome is state.outcome


@pytest.mark.req("REQ-N-02")
def test_revert_brings_the_committed_outcome_back_without_an_undo_entry(rig):
    """Catches Esc that leaves the preview on screen or records an edit."""
    session, outcome, submitter, debounce, _ = rig
    committed = session.state.value
    session.type_text(R_INNER, 12.0)
    debounce.expire()
    deliver(outcome, submitter)
    session.revert_typing()
    assert submitter.requests[-1].design == committed.design
    deliver(outcome, submitter)
    shown, _ = session.drawn(outcome.state.value)
    assert r_inner(shown.outcome.design) == 11.47
    assert session.state.value.design == committed.design
    session.undo()
    assert isinstance(session.state.value, SessionEmpty)


@pytest.mark.req("REQ-N-02")
def test_a_keystroke_cancels_the_preview_in_flight_and_the_shown_result_stays(rig):
    """Catches a preview compute left running after a newer keystroke, or a drawing stuck in the computing state."""
    session, outcome, submitter, debounce, _ = rig
    session.type_text(R_INNER, 12.0)
    debounce.expire()
    assert isinstance(outcome.state.value, OutcomeComputing)
    session.type_text(R_INNER, 123.0)
    assert submitter.cancels == 1
    assert isinstance(outcome.state.value, OutcomeReady)
    assert r_inner(session.drawn(outcome.state.value)[0].outcome.design) == 11.47
    late = submitter.requests[-1]
    outcome.on_finished(late.request_id, ready_state(compute(late.design, late.provenance)))
    assert r_inner(outcome.state.value.outcome.design) == 11.47, "the cancelled request's late result is dropped"


@pytest.mark.req("REQ-N-02")
@pytest.mark.parametrize("typed", [11.47, "abc", None], ids=["committed value", "not a number", "empty"])
def test_text_without_a_new_design_computes_no_preview(rig, typed):
    """Catches a preview of the committed value, of text that is no number, or of an empty field."""
    session, _, submitter, debounce, _ = rig
    before = len(submitter.requests)
    session.type_text(R_INNER, typed)
    debounce.expire()
    assert len(submitter.requests) == before


@pytest.mark.req("REQ-N-02")
def test_commit_typing_commits_the_typed_text(rig):
    """DEF-US11-03: catches a command that reads the design while the typed text is still uncommitted."""
    session, _, _, _, _ = rig
    session.type_text(R_INNER, 11.5)
    session.commit_typing()
    assert r_inner(session.state.value.design) == 11.5
    session.undo()
    assert r_inner(session.state.value.design) == 11.47


@pytest.mark.req("REQ-T-15")
def test_session_provenance_equals_project_provenance(rig):
    """Catches the session's cached-origin provenance drifting from `project_provenance` after an edit."""
    session, _, submitter, _, _ = rig
    session.edit(R_INNER, 11.5)
    state = session.state.value
    ref, _ = load_example(D08)
    assert state.provenance == project_provenance(ProjectFile(design=state.design, origin=ref))
    assert submitter.requests[-1].provenance == state.provenance


@pytest.mark.req("REQ-T-15", "REQ-F-15")
def test_session_provenance_of_an_origin_no_longer_packaged_is_user_not_default(tmp_path):
    """Catches the rule of `project_provenance` that an unknown origin gives `user` instead of `default`."""
    submitter = RecordingSubmitter()
    session = DesignSession(OutcomeViewModel(submitter))
    ref, design = load_example(D08)
    project = ProjectFile(design=design, origin=dataclasses.replace(ref, example_sha256="sha256:" + "0" * 64))
    path = tmp_path / "stale-origin.embodic.json"
    save_project(path, project)
    session.open_project(path)
    state = session.state.value
    assert isinstance(state, SessionComputed)
    assert state.provenance == project_provenance(project)
    assert not any(isinstance(kind, DefaultValue) for kind in state.provenance.values())
