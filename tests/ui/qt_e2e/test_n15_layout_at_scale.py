"""REQ-N-15 (V3-01 gap N-15): D08 lays out without clipping, overlap or sideways forms at 1x, 1.5x and 2x.

One new process per `QT_SCALE_FACTOR` runs `n15_layout_probe` (three window sizes each). The probe applies the clipped
text check of `tests/independent/m4/test_ui_behaviour.py`, compares the geometries of visible sibling widgets and reads
each inspector form's horizontal scroll bar. "Full screen" is 1920 x 1080, see the probe's docstring.
"""

import functools
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import embodic

REPO = Path(__file__).resolve().parents[3]
SCALES = ("1", "1.5", "2")
SIZES = ("960x540", "1280x800", "full-screen 1920x1080")

pytestmark = pytest.mark.req("REQ-N-15")


@functools.cache
def probe(scale: str) -> dict:
    """Run the probe in a new process at ``scale`` with the same embodic package as this process; return its JSON."""
    package_root = str(Path(embodic.__file__).resolve().parents[1])
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen", "QT_SCALE_FACTOR": scale, "PYTHONIOENCODING": "utf-8"}
    env["PYTHONPATH"] = os.pathsep.join([package_root, str(REPO), env.get("PYTHONPATH", "")])
    argv = [sys.executable, "-m", "tests.ui.qt_e2e.n15_layout_probe"]
    done = subprocess.run(argv, cwd=REPO, env=env, capture_output=True, encoding="utf-8", timeout=600, check=True)
    return json.loads(done.stdout.strip().splitlines()[-1])


@pytest.mark.parametrize("scale", SCALES)
@pytest.mark.parametrize("size", SIZES)
def test_n15_no_text_is_clipped_and_no_sibling_widgets_overlap(scale: str, size: str) -> None:
    """Catches clipped text or overlapping widgets that appear only at a scale factor above 1."""
    report = probe(scale)
    assert report["scale"] == float(scale)
    assert report["sizes"][size]["clipped"] == []
    assert report["sizes"][size]["overlaps"] == []


@pytest.mark.parametrize("scale", SCALES)
@pytest.mark.parametrize("size", SIZES)
def test_n15_no_form_shows_a_horizontal_scroll_bar_with_a_range(scale: str, size: str) -> None:
    """Catches an inspector form that scrolls sideways at a window size or scale factor (REQ-N-15 acceptance)."""
    assert probe(scale)["sizes"][size]["sideways"] == []
