"""UI-09: the window renders at 100, 150 and 200 % scaling (QT_SCALE_FACTOR), one process per scale.

The grabs are kept for Agent 1's review. "No clipped or overlapping text" is a judgement on those images and is
`not tested` by this test; it checks that each scale renders the 1280 x 800 window at that many device pixels.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from PySide6.QtGui import QImage

REPO = Path(__file__).resolve().parents[3]
SCALES = ("1", "1.5", "2")


def capture_at(scale: str, out: Path) -> dict:
    """Run the acceptance lever's UI-09 shot in a new process at ``scale``; return its JSON line."""
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen", "QT_SCALE_FACTOR": scale}
    env["PYTHONPATH"] = os.pathsep.join([str(REPO / "src"), str(REPO), env.get("PYTHONPATH", "")])
    argv = [sys.executable, "-m", "tests.ui.qt_shell.capture_acceptance", str(out), "--scaling"]
    done = subprocess.run(argv, cwd=REPO, env=env, capture_output=True, text=True, timeout=300, check=True)
    return json.loads(done.stdout.strip().splitlines()[-1])


@pytest.mark.req("REQ-N-15")
@pytest.mark.parametrize("scale", SCALES)
def test_ui09_the_window_renders_at_each_scale_factor(scale, tmp_path):
    """Catches a scale factor the app ignores or fails under (a grab at 1x pixels, or no grab)."""
    row = capture_at(scale, tmp_path)
    assert [n for n in row["notes"] if n.startswith("error")] == []
    (name,) = row["files"]
    image = QImage(str(tmp_path / name))
    assert (image.width(), image.height()) == (round(1280 * float(scale)), round(800 * float(scale)))
