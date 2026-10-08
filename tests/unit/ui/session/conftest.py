"""A design session whose computes are recorded instead of run."""

import pytest

from embodic.ui.viewmodels.outcome import OutcomeViewModel
from embodic.ui.viewmodels.session import DesignSession


class RecordingSubmitter:
    """Keeps every compute request instead of running it."""

    def __init__(self):
        self.requests = []

    def submit(self, request):
        """Record a request."""
        self.requests.append(request)


@pytest.fixture
def outcome_vm():
    """Return the shell's outcome view-model with a recording submitter in place of the worker."""
    return OutcomeViewModel(RecordingSubmitter())


@pytest.fixture
def session(outcome_vm):
    """Return a DesignSession without autosave whose computes go nowhere."""
    return DesignSession(outcome_vm)
