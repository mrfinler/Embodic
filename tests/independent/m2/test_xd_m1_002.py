"""Item 8: XD-M1-002 re-checked by dense sampling and by M1's certified bracket.

Fixture tests/golden/data/m1/segsegdist-seeded-collinear.json (1000 Xcoil segSegDist calls). The allow-list entry
(tests/golden/expected_diffs/m1.toml, D-033c) says Xcoil's golden is a false 0 in 19 calls where the true distance is
4.0001 to 13.0848 mm, and admits 13.1 mm abs. Defects caught: an embodic distance that is wrong on any call, an
allow-list that hides a real Xcoil/embodic disagreement other than the 19, or a tolerance too small for them.
"""

import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pytest

from embodic.geometry.distance import segment_segment_distance_mm

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "m1"))
from brute_clearance import centreline_bracket
from records import Line

pytestmark = pytest.mark.req("REQ-F-10")

FIXTURE = Path(__file__).resolve().parents[2] / "golden" / "data" / "m1" / "segsegdist-seeded-collinear.json"
SAMPLES = 20001
TOML = Path(__file__).resolve().parents[2] / "golden" / "expected_diffs" / "m1.toml"


@dataclass(frozen=True)
class _Chord:
    x1_mm: float
    y1_mm: float
    x2_mm: float
    y2_mm: float


def _calls() -> list[tuple[dict[str, float], dict[str, float], float]]:
    doc = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return [(c["inputs"]["a"], c["inputs"]["b"], c["output"]) for c in doc["calls"]]


def _dense(a: dict[str, float], b: dict[str, float]) -> float:
    """Least distance from SAMPLES points of each segment to the other segment (own closed-form point distance)."""

    def to_segment(px: np.ndarray, py: np.ndarray, s: dict[str, float]) -> np.ndarray:
        dx, dy = s["x2"] - s["x1"], s["y2"] - s["y1"]
        t = np.clip(((px - s["x1"]) * dx + (py - s["y1"]) * dy) / (dx * dx + dy * dy), 0.0, 1.0)
        return np.hypot(px - s["x1"] - t * dx, py - s["y1"] - t * dy)

    t = np.linspace(0.0, 1.0, SAMPLES)
    best = math.inf
    for p, q in ((a, b), (b, a)):
        px, py = p["x1"] + t * (p["x2"] - p["x1"]), p["y1"] + t * (p["y2"] - p["y1"])
        best = min(best, float(to_segment(px, py, q).min()))
    return best


def _bracket(a: dict[str, float], b: dict[str, float]):
    return centreline_bracket(
        Line(a["x1"], a["y1"], a["x2"], a["y2"], 0.0), Line(b["x1"], b["y1"], b["x2"], b["y2"], 0.0), tol=1e-10
    )


def _chord(s: dict[str, float]) -> _Chord:
    return _Chord(s["x1"], s["y1"], s["x2"], s["y2"])


def test_embodic_distance_lies_in_the_certified_bracket_on_all_1000_calls() -> None:
    """segment_segment_distance_mm is within 1e-9 mm of the certified bracket on every call."""
    for a, b, _ in _calls():
        got, br = segment_segment_distance_mm(_chord(a), _chord(b)), _bracket(a, b)
        assert br.lo - 1e-9 <= got <= br.hi + 1e-9, (a, b, got, br)


def _false_crossings() -> list[tuple[float, float]]:
    """(golden, true distance) of every call whose golden lies outside the certified bracket."""
    wrong = []
    for a, b, golden in _calls():
        br = _bracket(a, b)
        if not br.lo - 1e-9 <= golden <= br.hi + 1e-9:
            dense = _dense(a, b)
            assert abs(dense - br.hi) <= 1e-3, (dense, br)  # the sample step is at most 1e-3 mm here
            wrong.append((golden, br.lo))
    return wrong


def test_xcoil_differs_only_in_19_false_crossings_inside_the_allow_list_tolerance() -> None:
    """Exactly 19 goldens disagree with the truth; each is a false 0, and the largest true value is below 13.1 mm."""
    wrong = _false_crossings()
    assert len(wrong) == 19
    assert {g for g, _ in wrong} == {0}
    assert max(t for _, t in wrong) == pytest.approx(13.0848, abs=1e-4)


@pytest.mark.xfail(strict=True, reason="DEF-UV2-01: the XD-M1-002 reason states 4.0001 mm as the least true value")
def test_allow_list_reason_states_the_true_range_of_the_19_calls() -> None:
    """The reason's range "a to b mm" must hold the least and largest true distance of the 19 calls."""
    reason = TOML.read_text(encoding="utf-8").split('id = "XD-M1-002"')[1].split("tolerance")[0]
    low, high = (float(x) for x in re.search(r"returns ([0-9.]+) to ([0-9.]+) mm", reason).groups())
    true = [t for _, t in _false_crossings()]
    assert (low, high) == (round(min(true), 4), round(max(true), 4))
