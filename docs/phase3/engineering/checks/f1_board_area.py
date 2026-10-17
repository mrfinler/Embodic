"""Fix wave F1 item A (DEF-M7b-01): analytic board area against the chord area and Xcoil (U-E17, Agent 2).

Run from the repository root: PYTHONPATH=src python3 docs/phase3/engineering/checks/f1_board_area.py

The loop area here is written from Green's theorem, A = 1/2 sum (x dy - y dx), with no embodic code: a line adds
(x1 y2 - x2 y1) / 2 and an arc adds its chord term plus the signed circular segment r^2 (s - sin s) / 2. embodic is
imported only to read the value the current code returns (board_area_mm2) and the chord count it uses (piece_count).
Xcoil's outlinePrims and outlineArea (engine.js l.1055 and l.1094) run in node for the rounded polygon oracle.
"""

import json
import math
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

from embodic.geometry.discretise import piece_count
from embodic.geometry.layout import BoardOutline, Hole
from embodic.geometry.outline import build_outline
from embodic.geometry.primitives import Arc, Line, PrimitiveRole
from embodic.model.outline import CircleOutline, OutlineSpec, PolygonOutline, ScrewFit, ScrewPattern
from embodic.physics.analyse import board_area_mm2

ROOT = Path(__file__).resolve().parents[4]
ENGINE = os.environ.get("XCOIL_ENGINE", "/home/claude/serpentine/src/engine.js")
TAGS = ("sector-default", "serpentine-default", "wave-turns-2")


def green_loop(prims: list[dict]) -> float:
    """Signed area of a closed chain of {'L': x1, y1, x2, y2} and {'A': cx, cy, r, a, s} records."""
    total = 0.0
    for q in prims:
        if q["t"] == "L":
            total += (q["x1"] * q["y2"] - q["x2"] * q["y1"]) / 2
        else:
            x1, y1 = q["cx"] + q["r"] * math.cos(q["a"]), q["cy"] + q["r"] * math.sin(q["a"])
            b = q["a"] + q["s"]
            x2, y2 = q["cx"] + q["r"] * math.cos(b), q["cy"] + q["r"] * math.sin(b)
            total += (x1 * y2 - x2 * y1) / 2 + q["r"] ** 2 * (q["s"] - math.sin(q["s"])) / 2
    return total


def green_outline(outer: list[dict], cutouts: list[list[dict]], hole_dia: list[float]) -> float:
    """Board face area: outer loop minus cutout loops minus round holes."""
    holes = math.fsum(math.pi * d * d / 4 for d in hole_dia)
    return abs(green_loop(outer)) - math.fsum(abs(green_loop(c)) for c in cutouts) - holes


def from_xcoil(r: dict) -> dict:
    """Xcoil primitive record (board dump) to a loop record."""
    if r["type"] == "arc":
        return {"t": "A", "cx": r["cx"], "cy": r["cy"], "r": r["r"], "a": r["a1"], "s": r["a2"] - r["a1"]}
    return {"t": "L", "x1": r["start"][0], "y1": r["start"][1], "x2": r["end"][0], "y2": r["end"][1]}


def from_embodic(p: Line | Arc) -> dict:
    """Convert an embodic Line or Arc to a loop record."""
    if isinstance(p, Arc):
        return {"t": "A", "cx": p.cx_mm, "cy": p.cy_mm, "r": p.r_mm, "a": p.start_rad, "s": p.sweep_rad}
    return {"t": "L", "x1": p.x1_mm, "y1": p.y1_mm, "x2": p.x2_mm, "y2": p.y2_mm}


def to_embodic(q: dict) -> Line | Arc:
    """Loop record to an embodic outline primitive."""
    if q["t"] == "A":
        return Arc(
            cx_mm=q["cx"], cy_mm=q["cy"], r_mm=q["r"], start_rad=q["a"], sweep_rad=q["s"], width_mm=0.0,
            role=PrimitiveRole.OUTLINE,
        )  # fmt: skip
    return Line(x1_mm=q["x1"], y1_mm=q["y1"], x2_mm=q["x2"], y2_mm=q["y2"], width_mm=0.0, role=PrimitiveRole.OUTLINE)


def chord_deficit(q: dict) -> float:
    """Area between an arc and its embodic chords: n segments of r^2 (phi - sin phi) / 2, phi = |s| / n."""
    if q["t"] != "A":
        return 0.0
    n = piece_count(to_embodic(q), 0.5)
    phi = abs(q["s"]) / n
    return n * q["r"] ** 2 * (phi - math.sin(phi)) / 2


def golden_layouts() -> None:
    """A1: the three golden layouts of the mass_thermal area."""
    print("A1. Golden layouts: analytic (Green) vs Xcoil boardArea vs embodic board_area_mm2 (chords)")
    for tag in TAGS:
        raw = json.loads((ROOT / f"tests/golden/data/m1_layout/layout-{tag}.json").read_text())["calls"][0]["output"]
        xcoil = json.loads((ROOT / f"tests/golden/data/mass_thermal/mass-thermal-{tag}.json").read_text())
        x = xcoil["calls"][0]["output"]
        mech = raw["mech"]
        outer = [from_xcoil(r) for r in mech["prims"]]
        cutouts = [[from_xcoil(r) for r in mech["borePrims"]]] if mech["borePrims"] else []
        dia = [h["dia"] for h in mech["holes"]]
        analytic = green_outline(outer, cutouts, dia)
        outline = BoardOutline(
            outer=tuple(map(to_embodic, outer)),
            cutouts=tuple(tuple(map(to_embodic, c)) for c in cutouts),
            holes=tuple(Hole(x_mm=h["x"], y_mm=h["y"], diameter_mm=h["dia"], label="") for h in mech["holes"]),
        )
        chords = board_area_mm2(SimpleNamespace(outline=outline))
        predicted = math.fsum(map(chord_deficit, outer)) - math.fsum(chord_deficit(q) for c in cutouts for q in c)
        lam_scale = chords / x["boardArea"]
        print(f"  {tag}: outer r {mech['prims'][0]['r']} mm, bore r {mech['borePrims'][0]['r']} mm, {len(dia)} holes")
        print(f"    Xcoil boardArea      {x['boardArea']!r} mm2")
        rel = (analytic - x["boardArea"]) / x["boardArea"]
        print(f"    Green analytic       {analytic!r} mm2, rel to Xcoil {rel:.3e}")
        print(f"    embodic chords       {chords!r} mm2, rel to Xcoil {lam_scale - 1:.4e}")
        print(f"    analytic - chords    {analytic - chords:.9f} mm2; predicted segment sum {predicted:.9f} mm2")
        print(f"    Xcoil massLaminate   {x['thermal']['massLaminate']!r} g, nBoards {x['nBoards']}")


def xcoil_rounded(shape: str, sides: int, apothem: float, rot: float, corner: float) -> tuple[list[dict], float]:
    """Xcoil outlinePrims and outlineArea for one outline, run in node."""
    js = (
        f"const E = require({json.dumps(ENGINE)});"
        f"const p = E.outlinePrims({json.dumps(shape)}, {sides}, {apothem}, {rot}, {corner});"
        f"console.log(JSON.stringify({{p, a: E.outlineArea({json.dumps(shape)}, {sides}, {apothem}, {corner})}}));"
    )
    out = json.loads(subprocess.run(["node", "-e", js], check=True, capture_output=True, text=True).stdout)
    prims = [
        {"t": "A", "cx": q["cx"], "cy": q["cy"], "r": q["r"], "a": q["a1"], "s": q["a2"] - q["a1"]}
        if q["t"] == "A"
        else {"t": "L", "x1": q["x1"], "y1": q["y1"], "x2": q["x2"], "y2": q["y2"]}
        for q in out["p"]
    ]
    return prims, out["a"]


def reverse(loop: list[dict]) -> list[dict]:
    """Return the same loop traversed the other way."""
    out = []
    for q in reversed(loop):
        if q["t"] == "A":
            out.append({**q, "a": q["a"] + q["s"], "s": -q["s"]})
        else:
            out.append({"t": "L", "x1": q["x2"], "y1": q["y2"], "x2": q["x1"], "y2": q["y1"]})
    return out


def closed_form_cases() -> None:
    """A2: closed-form areas of build_outline loops and of a rounded Xcoil polygon."""
    print("A2. Closed-form cases on build_outline (embodic generators) and on Xcoil's rounded polygon")
    m3 = ScrewPattern(size="M3", fit=ScrewFit.NORMAL, count=6, pitch_radius_mm=42.0, hole_diameter_mm=3.4)
    cases = {
        "C1 circle r 57.84": (OutlineSpec(board=CircleOutline(radius_mm=57.84), bore=None), math.pi * 57.84**2),
        "C2 12-gon 93 flats": (
            OutlineSpec(board=PolygonOutline(sides=12, across_flats_mm=93.0), bore=None),
            12 * 46.5**2 * math.tan(math.pi / 12),
        ),
        "C3 12-gon 93 flats - bore r 12.5 - 6 x 3.4": (
            OutlineSpec(
                board=PolygonOutline(sides=12, across_flats_mm=93.0), bore=CircleOutline(radius_mm=12.5), screws=(m3,)
            ),
            12 * 46.5**2 * math.tan(math.pi / 12) - math.pi * 12.5**2 - 6 * math.pi * 3.4**2 / 4,
        ),
        "C4 circle r 50 - hexagon bore 20 flats rot 0.3": (
            OutlineSpec(
                board=CircleOutline(radius_mm=50.0),
                bore=PolygonOutline(sides=6, across_flats_mm=20.0, rotation_rad=0.3),
            ),
            math.pi * 50.0**2 - 6 * 10.0**2 * math.tan(math.pi / 6),
        ),
    }
    for name, (spec, expected) in cases.items():
        o = build_outline(spec, (0.0, 0.0))
        green = green_outline([from_embodic(p) for p in o.outer], [[from_embodic(p) for p in c] for c in o.cutouts],
                              [h.diameter_mm for h in o.holes])  # fmt: skip
        chords = board_area_mm2(SimpleNamespace(outline=o))
        print(f"  {name}: expected {expected!r}, Green {green!r} (rel {(green - expected) / expected:.2e}), "
              f"chords rel {(chords - expected) / expected:.3e}")  # fmt: skip
    loop, xa = xcoil_rounded("polygon", 8, 50.0, 0.0, 5.0)
    n, a, rc = 8, 50.0, 5.0
    closed = n * a * a * math.tan(math.pi / n) - n * rc * rc * (math.tan(math.pi / n) - math.pi / n)
    g, gr = green_loop(loop), green_loop(reverse(loop))
    chords = board_area_mm2(SimpleNamespace(outline=BoardOutline(outer=tuple(map(to_embodic, loop)), cutouts=(),
                                                                 holes=())))  # fmt: skip
    print(f"  C5 Xcoil outlinePrims octagon a 50 rc 5: outlineArea {xa!r}, closed form {closed!r}")
    print(f"     Green {g!r} (rel {(g - closed) / closed:.2e}), reversed loop {gr!r}")
    print(f"     chords rel {(chords - closed) / closed:.3e}")
    print(f"     loop records: {len(loop)} ({sum(q['t'] == 'A' for q in loop)} arcs)")


if __name__ == "__main__":
    golden_layouts()
    closed_form_cases()
