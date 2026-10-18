"""Whether tests/bundle may skip: it may unless the release profile has built the bundle and requires it."""

import os
from pathlib import Path

import pytest

REQUIRE_BUNDLE = "EMBODIC_REQUIRE_BUNDLE"  # set to 1 by tools/ci.py --profile release, which builds the bundle first


def require_bundle(frozen_cli: Path) -> None:
    """Return when the bundle's CLI exists; without it, fail if the run requires a bundle and skip otherwise.

    A skip would let a release pass with a build that produced no folder (REQ-N-06), as it does in the commit gate.
    """
    if frozen_cli.is_file():
        return
    if os.environ.get(REQUIRE_BUNDLE) == "1":
        pytest.fail(f"no bundle CLI at {frozen_cli} and {REQUIRE_BUNDLE}=1: the build gate failed or did not run")
    pytest.skip(f"no bundle at {frozen_cli.parent}; build it with `python tools/build_bundle.py`")
