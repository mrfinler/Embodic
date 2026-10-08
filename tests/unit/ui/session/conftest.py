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
def session():
    """Return a DesignSession without autosave whose computes go nowhere."""
    return DesignSession(OutcomeViewModel(RecordingSubmitter()))
