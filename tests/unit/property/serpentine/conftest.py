"""Put Agent 4's DRC instrument (``tests/independent/m1``) on ``sys.path`` for PR-13, read-only."""

import sys
from pathlib import Path

_M1_DIR = str(Path(__file__).resolve().parents[3] / "independent" / "m1")
if _M1_DIR not in sys.path:
    sys.path.insert(0, _M1_DIR)
