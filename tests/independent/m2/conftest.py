"""Put ``tests/independent/m2`` on ``sys.path`` so the tests import the instruments as top-level modules."""

import sys
from pathlib import Path

_M2_DIR = str(Path(__file__).resolve().parent)
if _M2_DIR not in sys.path:
    sys.path.insert(0, _M2_DIR)
