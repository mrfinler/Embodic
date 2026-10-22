"""Whether tests/bundle may skip: it may unless the release profile has built the bundle and requires it.

A bundle must also come from the source under test. tools/build_bundle.py stamps build/bundle/bundle_source.json after a
good build, and require_bundle refuses a folder whose stamp is missing or differs from the stamp of the tree (D-100c).
"""

import importlib.util
import json
import os
from pathlib import Path
from types import ModuleType

import pytest

REQUIRE_BUNDLE = "EMBODIC_REQUIRE_BUNDLE"  # set to 1 by tools/ci.py --profile release, which builds the bundle first
REPO = Path(__file__).resolve().parents[2]
BUILD_TOOL = REPO / "tools" / "build_bundle.py"


def build_tool() -> ModuleType:
    """Import tools/build_bundle.py, which is a script and not a package module."""
    spec = importlib.util.spec_from_file_location("build_bundle", BUILD_TOOL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_stamp(stamp_file: Path) -> object:
    """Return the JSON of a stamp file, or None when the file is missing or does not hold JSON."""
    try:
        return json.loads(stamp_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def require_bundle(frozen_cli: Path) -> None:
    """Return when the bundle's CLI exists and was built from this source; otherwise fail if the run requires one.

    Without the CLI, or with a stamp that is missing or differs from the stamp of the tree, a run that requires a
    bundle fails and any other run skips. A skip would let a release pass with a build that produced no folder
    (REQ-N-06), as it does in the commit gate; the stamp keeps a folder that an older release left behind from
    being compared with newer source (D-098c).
    """
    required = os.environ.get(REQUIRE_BUNDLE) == "1"
    if not frozen_cli.is_file():
        if required:
            pytest.fail(f"no bundle CLI at {frozen_cli} and {REQUIRE_BUNDLE}=1: the build gate failed or did not run")
        pytest.skip(f"no bundle at {frozen_cli.parent}; build it with `python tools/build_bundle.py`")
    tool = build_tool()
    stamp_file = frozen_cli.parent.parent / tool.STAMP_FILE
    found, expected = read_stamp(stamp_file), tool.source_stamp(REPO)
    if found == expected:
        return
    found_text = "missing or not JSON" if found is None else json.dumps(found, sort_keys=True)
    message = (
        f"the bundle at {frozen_cli.parent} was not built from this source: its stamp {stamp_file.name} is "
        f"{found_text}, the source's is {json.dumps(expected, sort_keys=True)}; "
        "rebuild it with `python tools/build_bundle.py`"
    )
    if required:
        pytest.fail(f"{message} ({REQUIRE_BUNDLE}=1)")
    pytest.skip(message)
