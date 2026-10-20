"""Put Agent 4's M1 instruments (``tests/independent/m1``) on ``sys.path``; they import each other by name."""

import sys
from pathlib import Path

_M1_DIR = str(Path(__file__).resolve().parents[2] / "independent" / "m1")
if _M1_DIR not in sys.path:
    sys.path.insert(0, _M1_DIR)
