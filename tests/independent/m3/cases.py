"""Agent 4's own M3 parameter sets (U-V3) and the Xcoil dump they produce under Node.

The sets differ from the golden case lists in tools/golden/cases on purpose: each mixes options those lists vary
one at a time.
"""

import json
import os
import shutil
import subprocess
from functools import cache
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = Path(os.environ.get("XCOIL_ENGINE", "/home/claude/serpentine/src/engine.js"))

SERPENTINE: dict[str, dict[str, Any]] = {
    "s-radial-t4": {"style": "radial", "turns": 4},
    "s-perphase-3-t5-gap0p3": {"stackMode": "perPhase", "turns": 5, "boardGap": 0.3},
    "s-sharp-inner-4l-series": {
        "cornerStyle": "sharp", "terminalSide": "inner", "layersPerPhase": 4, "pairConnection": "series", "turns": 3,
    },
    "s-12p-1ph-2l": {"poles": 12, "rIn": 15, "rOut": 35, "phases": 1, "layersPerPhase": 2},
    "s-delta-filletmax-t5": {"connection": "delta", "filletMax": True, "turns": 5},
    "s-interleaved-open-t4": {"layerOrder": "interleaved", "layersPerPhase": 2, "connection": "open", "turns": 4},
}  # fmt: skip

WAVE: dict[str, dict[str, Any]] = {
    "w-involute-p20-l2-m3": {"waveStyle": "involute", "turns": 2, "poles": 20},
    "w-jog-p16-l4-m3": {"waveStyle": "jog", "turns": 2, "waveLayers": 4},
    "w-chord-p8-l2-m2-t3": {"waveStyle": "chord", "turns": 3, "phases": 2, "poles": 8},
    "w-overlap-p12-l4-m1": {"waveStyle": "overlap", "turns": 2, "waveLayers": 4, "phases": 1, "poles": 12},
    "w-involute-p16-l6-m3-delta": {"waveStyle": "involute", "turns": 2, "waveLayers": 6, "connection": "delta"},
    "w-jog-p12-l2-m3-open": {"waveStyle": "jog", "turns": 2, "poles": 12, "connection": "open"},
}


def all_cases() -> dict[str, dict[str, Any]]:
    """Return every case id with its Xcoil input."""
    return {**SERPENTINE, **{k: {"topology": "wave", **v} for k, v in WAVE.items()}}


def have_xcoil() -> bool:
    """Return True when node and the read-only Xcoil engine are present."""
    return shutil.which("node") is not None and ENGINE.is_file()


def run_node(request: dict[str, Any]) -> dict[str, Any]:
    """Run ``xcoil_dump.cjs`` on one request and return its JSON answer."""
    proc = subprocess.run(
        ["node", str(HERE / "xcoil_dump.cjs")],
        input=json.dumps(request),
        capture_output=True,
        text=True,
        check=True,
        timeout=300,
        env={**os.environ, "XCOIL_ENGINE": str(ENGINE)},
    )
    return json.loads(proc.stdout)


@cache
def xcoil_dumps() -> dict[str, dict[str, Any]]:
    """Return Xcoil's own raw layout for every case, keyed by case id."""
    request = {"cases": [{"id": k, "params": v} for k, v in all_cases().items()]}
    return {c["id"]: c for c in run_node(request)["cases"]}
