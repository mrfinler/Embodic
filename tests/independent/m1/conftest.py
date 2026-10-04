"""Put ``tests/independent/m1`` on ``sys.path`` so the tests import the instruments as top-level modules.

``--import-mode=importlib`` adds no test directory to ``sys.path``; the golden harness uses the same pattern.
"""

import sys
from pathlib import Path

_M1_DIR = str(Path(__file__).resolve().parent)
if _M1_DIR not in sys.path:
    sys.path.insert(0, _M1_DIR)
