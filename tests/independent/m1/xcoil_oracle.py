"""Python side of the third oracle: Xcoil v3 kernels run under Node, read-only (``/home/claude/serpentine``).

Known limits, read in ``engine.js`` on 2026-10-04 (``verified`` by reading):

- ``segSegDist`` (l.563) and ``ptSegDist`` (l.573) are exact segment kernels.
- ``drcObjects`` (l.1693) discretises every primitive with ``discretize(prims, 0.5)`` (l.536, sagitta tolerance
  0.001 mm), so an arc distance can be off by up to 0.001 mm per arc. It also skips pairs inside one object closer than
  ``1.6 * (wMax + s)`` along the path, a wider exemption than D-006 allows. Use it as an oracle for values between
  objects, not for exemptions.
"""

import json
import shutil
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from records import Line, Prim

ENGINE = Path("/home/claude/serpentine/src/engine.js")
SCRIPT = Path(__file__).resolve().parent / "xcoil_oracle.cjs"


def available() -> bool:
    """Node and the Xcoil engine are both present."""
    return shutil.which("node") is not None and ENGINE.is_file()


def _call(request: dict[str, Any]) -> Any:
    out = subprocess.run(
        ["node", str(SCRIPT)],
        input=json.dumps({"engine": str(ENGINE), **request}),
        capture_output=True,
        text=True,
        check=True,
        timeout=120,
    )
    return json.loads(out.stdout)


def xcoil_prim(p: Prim, kind: str = "side") -> dict[str, Any]:
    """Return the primitive in Xcoil's own record shape (``t`` 'L' or 'A', arcs as a1 and a2)."""
    if isinstance(p, Line):
        return {"t": "L", "x1": p.x1, "y1": p.y1, "x2": p.x2, "y2": p.y2, "w": p.width, "kind": kind}
    return {"t": "A", "cx": p.cx, "cy": p.cy, "r": p.r, "a1": p.start, "a2": p.start + p.sweep, "w": p.width,
            "kind": kind}  # fmt: skip


def seg_seg_dist(pairs: Sequence[tuple[Line, Line]]) -> list[float]:
    """Xcoil ``segSegDist`` for each pair of segments."""
    return [float(d) for d in _call({"op": "segSegDist", "pairs": [[xcoil_prim(a), xcoil_prim(b)] for a, b in pairs]})]


def pt_seg_dist(cases: Sequence[tuple[float, float, Line]]) -> list[float]:
    """Xcoil ``ptSegDist`` for each (x, y, segment)."""
    return [float(d) for d in _call({"op": "ptSegDist", "cases": [[x, y, xcoil_prim(s)] for x, y, s in cases]})]


def drc_objects(objects: Sequence[Sequence[Prim]], clearance_mm: float) -> float:
    """Xcoil ``drcObjects`` minimum clearance over objects, each one path, with self pairs skipped (``noSelf``)."""
    w_max = max(p.width for obj in objects for p in obj)
    payload = [{"prims": [xcoil_prim(p) for p in obj], "noSelf": True} for obj in objects]
    return float(_call({"op": "drcObjects", "objects": payload, "s": clearance_mm, "wMax": w_max})["clearance"])
