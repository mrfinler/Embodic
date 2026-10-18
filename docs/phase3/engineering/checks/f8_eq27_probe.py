"""Fix wave F8 (U-E22): EQ-27 k_u of embodic against Xcoil kw1 on the three GR-22 layouts, split into its parts.

Run from the worktree root (read-only; it writes nothing):

    PYTHONPATH=src /home/claude/embodic/.venv/bin/python docs/phase3/engineering/checks/f8_eq27_probe.py

It runs `f8_eq27_xcoil.mjs` with node for the Xcoil side, runs embodic analyse() on the mapped Xcoil layouts exactly as
tests/golden/m2_physics/test_analysis_golden.py does, and counts the primitives of phase A by role. Part 2 counts the
roles that embodic's own spiral generator emits per coil path, for the shipped spiral examples.
"""

import json
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tests" / "golden"))

from m2_physics.test_analyse_layouts import CASES, _design, _raw, _stack  # noqa: E402
from m2_physics.test_analysis_golden import _xcoil_registry  # noqa: E402

from embodic.generators import build_layout  # noqa: E402
from embodic.geometry.primitives import Line, PrimitiveRole  # noqa: E402
from embodic.io.examples import load_example  # noqa: E402
from embodic.model.vocabulary import Phase  # noqa: E402
from embodic.physics import analyse  # noqa: E402
from embodic.results import load_registry  # noqa: E402

TOPOLOGY = {"layout-sector-default": "sector", "layout-serpentine-default": "serpentine", "layout-wave-turns-2": "wave"}


def rel(a: float, b: float) -> float:
    """Relative difference of a to the reference b."""
    return abs(a - b) / abs(b)


def phase_a_roles(stack) -> Counter:
    """Count the primitives of every phase A path by role."""
    return Counter(
        prim.role.value for b in stack.boards for path in b.paths if path.phase is Phase.A for prim in path.primitives
    )


def lead_line_radii(stack) -> list[tuple[float, float]]:
    """Start and end radius of every straight LEAD primitive of phase A (mm)."""
    out = []
    for b in stack.boards:
        for path in b.paths:
            if path.phase is not Phase.A:
                continue
            for prim in path.primitives:
                if prim.role is PrimitiveRole.LEAD and isinstance(prim, Line):
                    out.append(
                        (round(math.hypot(prim.x1_mm, prim.y1_mm), 6), round(math.hypot(prim.x2_mm, prim.y2_mm), 6))
                    )
    return out


def part1(xcoil: dict) -> None:
    """Compare embodic k_u with the Xcoil parts on the three mapped layouts."""
    print("PART 1: mapped Xcoil layouts (GR-22 inputs, Xcoil copper constants)")
    for case in CASES:
        raw = _raw(case)
        stack = _stack(raw)
        r = analyse(_design(raw), stack, {}, _xcoil_registry(case))
        topo = TOPOLOGY[case]
        x = xcoil[topo]
        k_u = r.winding_factor_1.value
        ke = [p.ke_peak_v_s_per_rad.value for p in r.phases]
        roles = phase_a_roles(stack)
        print(f"  {case}")
        print(f"    embodic k_u            {k_u!r}")
        print(f"    Xcoil kw1              {x['kw1']!r}   rel diff {rel(k_u, x['kw1']):.3e}")
        print(f"    embodic Ke1 mean       {r.ke_phase_v_s_per_rad.value!r}   Xcoil Ke1 {x['Ke1']!r}")
        print(f"    embodic Ke A, B, C     {ke}")
        print(f"    phase A roles          {dict(sorted(roles.items()))}")
        if topo == "sector":
            sides = roles["side"]
            cond = x["conductorsPerPhaseXcoil"]
            print(f"    sides / Xcoil count    {sides} / {cond} = {sides / cond!r}")
            scaled = k_u * sides / cond
            print(f"    k_u x sides / count    {scaled!r}   rel diff to kw1 {rel(scaled, x['kw1']):.3e}")
            print(f"    phase A LEAD lines r   {sorted(set(lead_line_radii(stack)))}")
            print(f"    Xcoil X0 kinds         {x['x0Kinds']}   magnet span {x['magnetSpan']}")
        if topo == "serpentine":
            v = x["variants"]
            for name in ("xcoil_phaseA_over_phaseAz", "mean_over_phaseAz", "phaseA_over_allz", "mean_over_allz"):
                print(f"    Xcoil {name:<26} {v[name]!r}   rel diff to embodic {rel(k_u, v[name]):.3e}")
            per_phase = {}
            for ph in range(3):
                zs = [lay["z"] for lay in x["layers"] if lay["phase"] == ph]
                per_phase[ph] = zs
            print(f"    copper z by phase      {per_phase}")
            print(f"    Xcoil k_u per phase    {x['perPhaseKu']}   (analyze l.977-983 on each phase's own layers)")
            print(f"    Xcoil Ke A/mean - 1    {x['phaseKe'][0] / x['Ke1'] - 1:.6e}")
            print(f"    ideal A-z/all-z - 1    {x['idealPhase0Z'] / x['idealAllZ'] - 1:.6e}")


def part2() -> None:
    """Count the roles embodic's spiral generator emits per phase A coil path."""
    print("PART 2: roles per coil path from embodic's own spiral generator")
    registry = load_registry()
    for example_id in ("spiral_12c16p_default", "spiral_12c14p", "spiral_12c10p_d08"):
        _, design = load_example(example_id)
        stack = build_layout(design, registry)
        paths = [p for b in stack.boards for p in b.paths if p.phase is Phase.A]
        per_path = Counter()
        for p in paths:
            c = Counter(q.role.value for q in p.primitives)
            per_path[(c["side"], c["lead"], c["end_turn"])] += 1
        r = analyse(design, stack, {}, registry)
        k_u = r.winding_factor_1.value if r is not None else None
        print(f"  {example_id}: phase A paths by (side, lead, end_turn) count {dict(per_path)}; k_u {k_u!r}")


def main() -> None:
    """Run the Xcoil probe with node, then both parts."""
    out = subprocess.run(
        ["node", str(Path(__file__).with_name("f8_eq27_xcoil.mjs"))], check=True, capture_output=True, text=True
    ).stdout
    xcoil = json.loads(out)
    print(f"Xcoil engine sha256 {xcoil['engineSha256']} (node {xcoil['node']})")
    part1(xcoil)
    part2()


if __name__ == "__main__":
    main()
