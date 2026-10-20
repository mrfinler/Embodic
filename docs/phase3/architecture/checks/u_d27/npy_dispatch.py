r"""U-D27: does NumPy's CPU dispatch target change embodic's results? Prints a SHA-256 of each example's outcome JSON.

Not a test. Run it once per target and compare the lines:

    PYTHONPATH=<tree>/src python npy_dispatch.py
    NPY_DISABLE_CPU_FEATURES="X86_V4" PYTHONPATH=<tree>/src python npy_dispatch.py
    NPY_DISABLE_CPU_FEATURES="X86_V3 X86_V4" PYTHONPATH=<tree>/src python npy_dispatch.py

An optional path argument also writes each example's analysis JSON there, for npy_dispatch_diff.py.
"""

import hashlib
import json
import sys
from pathlib import Path

from numpy._core._multiarray_umath import __cpu_dispatch__, __cpu_features__

from embodic.api import compute_project, outcome_to_json

DUMP = Path(sys.argv[1]) if len(sys.argv) > 1 else None
TREE = Path(__file__).resolve().parents[5]
STEMS = ("serpentine_16p_example", "spiral_12c10p_d08", "spiral_12c14p", "spiral_12c16p_default", "wave_16p_example")

dumps = {}
print("dispatch on:", [k for k in __cpu_dispatch__ if __cpu_features__.get(k)])
for stem in STEMS:
    outcome = compute_project(TREE / "resources" / "examples" / f"{stem}.embodic.json")
    document = outcome_to_json(outcome)
    text = json.dumps(document, sort_keys=True, ensure_ascii=False, allow_nan=False)
    drc = json.dumps(document["drc"], sort_keys=True)
    analysis = json.dumps(document["analysis"], sort_keys=True)
    dumps[stem] = document["analysis"]
    print(stem, outcome.design_hash[:12], "outcome", hashlib.sha256(text.encode()).hexdigest()[:16],
          "drc", hashlib.sha256(drc.encode()).hexdigest()[:16], "analysis",
          hashlib.sha256(analysis.encode()).hexdigest()[:16])  # fmt: skip
if DUMP:
    DUMP.write_text(json.dumps(dumps))
