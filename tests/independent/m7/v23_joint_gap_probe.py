"""Worst copper joint gap of every spiral example, on the clean copy and with one product mutant applied.

Run from the repository root with the dev venv:

    python tests/independent/m7/v23_joint_gap_probe.py V3-03 V3-03-04

Prints, per spiral example and per copy, the number of LEAD primitives, the number of joints and the largest distance
from the end of primitive i to the start of i + 1 over every path (the measure of `m2/test_spiral.py`
`test_every_path_is_continuous_within_1e_6`, with its `_ends`). The mutated copy is a scratch copy of the checkout.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from product_mutant_tables import CAMPAIGNS
from product_mutants import _copy_checkout

MEASURE = """
import dataclasses, itertools, math, sys
from embodic.generators import build_layout
from embodic.geometry.primitives import Arc, PrimitiveRole
from embodic.io.examples import list_examples, load_example
from embodic.results import load_registry

def ends(p):
    if isinstance(p, Arc):
        a, b = p.start_rad, p.start_rad + p.sweep_rad
        return ((p.cx_mm + p.r_mm * math.cos(a), p.cy_mm + p.r_mm * math.sin(a)),
                (p.cx_mm + p.r_mm * math.cos(b), p.cy_mm + p.r_mm * math.sin(b)))
    return (p.x1_mm, p.y1_mm), (p.x2_mm, p.y2_mm)

print("imports", __import__("embodic").__file__)
for info in list_examples():
    if info.topology.value != "spiral":
        continue
    _, design = load_example(info.example_id)
    board = build_layout(design, load_registry()).boards[0]
    gaps = [math.dist(ends(a)[1], ends(b)[0]) for path in board.paths for a, b in itertools.pairwise(path.primitives)]
    leads = sum(p.role is PrimitiveRole.LEAD for path in board.paths for p in path.primitives)
    print(f"{info.example_id}: {leads} LEAD primitives, {len(gaps)} joints, worst joint gap {max(gaps):.3e} mm")
"""


def measure(work: Path) -> str:
    """Run the measure with ``PYTHONPATH`` on ``work/src`` and return its output."""
    done = subprocess.run(
        [sys.executable, "-c", MEASURE],
        cwd=work,
        env={**os.environ, "PYTHONPATH": str(work / "src")},
        capture_output=True,
        text=True,
    )
    return done.stdout + done.stderr[-800:]


def main(campaign: str, mutant_id: str) -> int:
    """Print the measure on the clean copy, then on the copy with ``mutant_id`` applied."""
    (mutant,) = [m for m in CAMPAIGNS[campaign] if m.id == mutant_id]
    with tempfile.TemporaryDirectory(prefix="embodic-gap-") as tmp:
        work = _copy_checkout(Path(tmp))
        print(f"clean copy\n{measure(work)}")
        target = work / "src" / "embodic" / mutant.file
        source = target.read_text(encoding="utf-8")
        assert source.count(mutant.old) == 1, f"{mutant.id}: anchor not exactly once in {mutant.file}"
        target.write_text(source.replace(mutant.old, mutant.new), encoding="utf-8")
        print(f"{mutant.id} applied\n{measure(work)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
