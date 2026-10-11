"""Shared subjects for Agent 4's M4 checks: the five packaged examples computed through `embodic.api` only."""

import json
import math
import sys
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import pytest

M4_DIR = Path(__file__).resolve().parent
if str(M4_DIR) not in sys.path:
    sys.path.insert(0, str(M4_DIR))

ROOT = M4_DIR.parents[2]
EXAMPLES_DIR = ROOT / "resources" / "examples"
EXAMPLE_STEMS = (
    "serpentine_16p_example",
    "spiral_12c10p_d08",
    "spiral_12c14p",
    "spiral_12c16p_default",
    "wave_16p_example",
)
FULL_TURN = 2 * math.pi


def example_file(stem: str) -> Path:
    """Return the packaged project file of one example."""
    return EXAMPLES_DIR / f"{stem}.embodic.json"


def example_document(stem: str) -> dict:
    """Return one packaged project file as plain JSON, read with the standard library."""
    return json.loads(example_file(stem).read_text(encoding="utf-8"))


@cache
def outcome_of(stem: str):
    """Return embodic's ComputeOutcome for one packaged example (public facade only)."""
    from embodic.api import compute_project

    outcome = compute_project(example_file(stem))
    assert not isinstance(outcome, tuple), outcome
    return outcome


def primitive_length(prim) -> float:
    """Return the length of one Line or Arc, mm, from its public fields."""
    if hasattr(prim, "r_mm"):
        return abs(prim.sweep_rad) * prim.r_mm
    return math.hypot(prim.x2_mm - prim.x1_mm, prim.y2_mm - prim.y1_mm)


def is_arc(prim) -> bool:
    """Tell an Arc from a Line by its public fields."""
    return hasattr(prim, "r_mm")


@dataclass(frozen=True)
class LayerTally:
    """What one copper layer of one board holds, counted from the Layout primitives."""

    paths: int
    lines: int
    arcs: int
    full_circles: int
    length_mm: float


def layer_tallies(layout) -> dict[tuple[str, str], LayerTally]:
    """Tally the Layout by (layer, phase letter or 'none'), from CopperPath and primitive fields."""
    acc: dict[tuple[str, str], list] = {}
    for path in layout.paths:
        key = (path.layer, path.phase.value if path.phase is not None else "none")
        row = acc.setdefault(key, [0, 0, 0, 0, 0.0])
        row[0] += 1
        for prim in path.primitives:
            if is_arc(prim):
                row[2] += 1
                row[3] += abs(prim.sweep_rad) >= FULL_TURN - 1e-9
            else:
                row[1] += 1
            row[4] += primitive_length(prim)
    return {k: LayerTally(*v) for k, v in acc.items()}


def drc_all_passed(outcome) -> bool:
    """True when every board's DRC report lists no violation."""
    return outcome.drc is not None and all(len(r.violations) == 0 for r in outcome.drc)


@pytest.fixture(scope="session")
def export_dir(tmp_path_factory) -> Path:
    """One scratch folder for every export of the session."""
    return tmp_path_factory.mktemp("m4_exports")
