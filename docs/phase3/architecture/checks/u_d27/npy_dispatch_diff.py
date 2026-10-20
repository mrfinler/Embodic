r"""U-D27: the largest relative difference between two analysis dumps of npy_dispatch.py, per example.

Not a test. ``python npy_dispatch_diff.py a.json b.json``. Walks both JSON trees together and compares every float.
"""

import json
import sys


def floats(a, b, path=""):
    if isinstance(a, dict):
        for k in a:
            yield from floats(a[k], b[k], f"{path}/{k}")
    elif isinstance(a, list):
        for i, (x, y) in enumerate(zip(a, b, strict=True)):
            yield from floats(x, y, f"{path}/{i}")
    elif isinstance(a, float) and isinstance(b, float):
        yield path, a, b


first, second = (json.load(open(p)) for p in sys.argv[1:3])
for stem in first:
    pairs = list(floats(first[stem], second[stem]))
    differ = [(abs(a - b) / max(abs(a), abs(b)), p) for p, a, b in pairs if a != b]
    worst = max(differ, default=(0.0, "-"))
    print(f"{stem}: {len(pairs)} floats, {len(differ)} differ, largest relative {worst[0]:.3g} at {worst[1]}")
