"""Regenerate fixtures/series_fan_vias.json from Agent 2's G6 fan (checks/series_fan_check.py, not collected by pytest).

The tests compare the generator's ring vias and fan stubs against these numbers; this tool is the only place that
imports the fan check. The check imports ``series._group`` of the generator at e1536b8, so run this tool on a checkout
of that commit (git worktree or archive), from its repo root: .venv/bin/python tests/unit/generators/make_fan_goldens.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "docs" / "phase2" / "engineering" / "checks"))

import series_fan_check as sfc  # noqa: E402

CASES = {
    "CF-11": (sfc.default_design, "keep"),
    "D08": (sfc.d08_design, None),
}


def fan(base, k: int, turns) -> dict[str, object]:
    """Ring vias and each group's fan stub ends (X entry, Y exit) of the reference coil, at full precision."""
    built = []

    def record(*args):
        coil = sfc.fan_series_coil(*args)
        built.append(coil)
        return coil

    sfc.gen.series_coil = record
    sfc.gen._series_fails_drc = lambda design, layout: False
    stack = sfc.gen.generate_spiral(sfc.series_design(base, k, turns), sfc.load_registry())
    assert isinstance(stack, sfc.BoardStack), stack
    (coil,) = built
    return {
        "ring_vias": [list(p) for p in coil.ring_vias],
        "x_stubs": [[list(g.x[0].start_point()), list(g.x[0].end_point())] for g in coil.groups],
        "y_stubs": [[list(g.y[-1].start_point()), list(g.y[-1].end_point())] for g in coil.groups],
        "centre_vias": [list(g.centre_via) for g in coil.groups],
    }


if __name__ == "__main__":
    out = {f"{name} k={k}": fan(make(), k, turns) for name, (make, turns) in CASES.items() for k in (2, 3)}
    target = Path(__file__).resolve().parent / "fixtures" / "series_fan_vias.json"
    target.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {target}")
