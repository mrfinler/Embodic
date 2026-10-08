"""Regenerate fixtures/spiral_r2_turns.json from Agent 2's reference construction (not collected by pytest).

The tests compare the generator against these numbers; this tool is the only place that imports from docs.
Run from the repo root: .venv/bin/python tests/unit/generators/make_r2_goldens.py
"""

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "docs" / "phase2" / "engineering" / "checks"))

import spiral_reference as sr  # noqa: E402

CASES = {
    "CF-11": sr.Geo(12, 18.0, 38.0, 0.5, 0.2, 0.2, 0.6),
    "CF-10": sr.Geo(12, 11.47, 45.03, 2.06, 0.8, 0.8, 0.6),
    "CF-10 pad 1.2": sr.Geo(12, 11.47, 45.03, 2.06, 0.8, 0.8, 1.2),
}


def case(g: sr.Geo) -> dict[str, object]:
    """Turn counts, closing, centre via radius and per-turn rows of one reference geometry at full precision."""
    turns, _ = sr.turn_limit(g)
    cl = sr.closing(g, turns)
    n, kind = cl["N"], cl["kind"]
    path = sr.coil_path(g, turns, n, kind)
    rows = []
    full = turns[: n - 1] if kind == "half" else turns[:n]
    tops = [tt["J"] for tt in full[1:]] + [sr.half_turn(g, n - 1)["J"] if kind == "half" else path["lead_point_L"]]
    for tt, top in zip(full, tops, strict=True):
        rows.append(
            {
                "type": tt["type"],
                "d_t": tt["d_t"],
                "R_out": tt["R_out"],
                "r_end": tt["R_in_or_apex"],
                "jog": tt["jog"],
                "outer": tt["outer"],
                "right": tt["right"],
                "inner": tt["inner"],
                "left": sr.dist(tt["D"], top),
            }
        )
    if kind == "half":
        ht = sr.half_turn(g, n - 1)
        rows.append(
            {
                "type": "half",
                "d_t": ht["d_t"],
                "R_out": ht["R_out"],
                "r_end": ht["r_v"],
                "jog": ht["jog"],
                "outer": ht["outer"],
                "right": ht["right"],
                "inner": None,
                "left": None,
            }
        )
    return {
        "loop_turns": len(turns),
        "closing": kind,
        "n": n,
        "n_full": cl["n_full"],
        "n_half": cl["n_half"],
        "r_v": path["r_v"],
        "body": path["body"],
        "lead": path["lead"],
        "stub": path["stub"],
        "total": path["total"],
        "rows": rows,
        "terminal_angle_rad": math.radians(path["terminal_angle_deg"]),
    }


if __name__ == "__main__":
    out = {name: case(g) for name, g in CASES.items()}
    target = Path(__file__).resolve().parent / "fixtures" / "spiral_r2_turns.json"
    target.write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {target}")
