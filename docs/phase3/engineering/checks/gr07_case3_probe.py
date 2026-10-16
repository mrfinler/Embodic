# Prepared by: Agent 2 (Motor Design Expert), model: claude-opus-5-5
"""GR-07 case 3 (DEF-U-M6h-01): the numbers behind docs/phase3/engineering/gr07_case3_ruling.md (U-E15).

Run from the repository root:
    PYTHONPATH=src /home/claude/embodic/.venv/bin/python docs/phase3/engineering/checks/gr07_case3_probe.py

Reads the committed Xcoil stackupFor fixtures (tests/golden/data/stackup, read-only) and calls the embodic helper.
Prints, per fixture, the feasibility margin B - n x t, Xcoil's layer-centre pitch against the copper thickness, and
whether Xcoil's entry list sums to the board thickness it reports. Exits 1 if the ruling's premises do not hold.
"""

import json
import math
import re
import sys
from pathlib import Path

from embodic.model.stackup import DielectricLayer, generate_even_stackup
from embodic.units import MM_PER_COPPER_OZ

ROOT = Path(__file__).resolve().parents[4]
FIXTURES = ROOT / "tests" / "golden" / "data" / "stackup"
ENGINE = Path("/home/claude/serpentine/src/engine.js")
THIN = "stackupfor-auto-thin-8cu-2oz-0p4mm"


def main() -> int:
    """Print the probe table and the thin-case numbers; return 1 if a premise of the ruling fails."""
    failures: list[str] = []
    engine_oz = float(re.search(r"var OZ_TO_MM = ([0-9.]+);", ENGINE.read_text()).group(1))
    print(f"MM_PER_COPPER_OZ {MM_PER_COPPER_OZ} | Xcoil OZ_TO_MM {engine_oz} | 2 oz = {2 * MM_PER_COPPER_OZ:.4f} mm")
    if engine_oz != MM_PER_COPPER_OZ:
        failures.append("copper weight constant differs from Xcoil")

    print("case | n | t mm | B mm | B - n*t mm | pitch mm | pitch - t mm | Xcoil sum(entries) - B mm")
    paths = sorted(FIXTURES.glob("stackupfor-auto-*.json"))
    if len(paths) != 11:
        failures.append(f"expected the 10 case-1 fixtures and the thin one, found {len(paths)}")
    for path in paths:
        call = json.loads(path.read_text())["calls"][0]
        n, out = call["inputs"]["nCu"], call["output"]
        t, board = out["t"][0], out["boardThickness"]
        margin = board - math.fsum(out["t"])
        pitch = out["z"][1] - out["z"][0] if n > 1 else float("nan")
        drift = math.fsum(e["t"] for e in out["entries"]) - board
        print(f"{path.stem} | {n} | {t:.4f} | {board} | {margin:+.4f} | {pitch:.4f} | {pitch - t:+.4f} | {drift:+.2e}")
        if (margin > 0) != (abs(drift) <= 1e-12):
            failures.append(f"{path.stem}: Xcoil self-consistency does not follow the sign of B - n*t")

    out = json.loads((FIXTURES / f"{THIN}.json").read_text())["calls"][0]["output"]
    helper = generate_even_stackup(8, 2 * MM_PER_COPPER_OZ, 0.4)
    z = list(helper.copper_z_mm().values())
    gaps = [layer.thickness_mm for layer in helper.layers if isinstance(layer, DielectricLayer)]
    print(f"thin case: Xcoil z[7] {out['z'][7]:.4f} mm, board {out['boardThickness']} mm")
    print(f"thin case: helper z[7] {z[7]:.4f} mm, board {helper.board_thickness_mm():.4f} mm, dielectrics {gaps}")
    print(f"thin case: board growth {helper.board_thickness_mm() / 0.4 - 1:+.1%} against the 0.4 mm entered")
    print(f"thin case: largest copper for 8 layers in 0.4 mm {0.4 / 8:.4f} mm = {0.4 / 8 / MM_PER_COPPER_OZ:.3f} oz")
    if not (helper.board_thickness_mm() > 0.4 and all(g == 0.0 for g in gaps)):
        failures.append("thin case: the helper no longer grows the board with zero dielectrics")

    for line in failures:
        print("FAIL:", line)
    print("PASS" if not failures else "FAILED")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
