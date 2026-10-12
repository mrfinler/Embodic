"""PF-01, PF-02, PF-03 and PF-05: timings on this machine, recorded with the Phase 1 targets as pass or fail facts.

The targets are `assumption` budgets for the user's reference laptop (Phase 1 test_plan_draft.md l.365-367). A number
measured on a shared 2-CPU container is no verdict on that laptop, so these tests record the facts and fail only when
the computation itself fails. PF-04 compares a later run with the recorded baseline.
"""

import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from embodic.api import compute_project

REPO = Path(__file__).resolve().parents[2]
EXAMPLES = REPO / "resources" / "examples"
STAGES = ("validate", "geometry", "drc", "physics")
# Phase 1 test_plan_draft.md l.365-367 (PF-01 to PF-03), all `assumption`.
PF01_P95_S = 1.0
PF01_STAGE_BUDGET_S = {"geometry": 0.2, "drc": 0.4, "physics": 0.3}
PF02_TARGET_S = 5.0
PF03_TARGET_S = 3.0


def percentile(values: list[float], fraction: float) -> float:
    """Return the nearest-rank percentile, so p95 of 20 runs is the 19th smallest."""
    ordered = sorted(values)
    return ordered[max(0, math.ceil(fraction * len(ordered)) - 1)]


def timed_runs(project: Path, runs: int) -> dict[str, object]:
    """Compute a project once to warm up, then `runs` full recomputes; return wall and stage percentiles in seconds."""
    walls, stages = [], {stage: [] for stage in STAGES}
    for index in range(runs + 1):
        started = time.perf_counter()
        outcome = compute_project(project)
        wall = time.perf_counter() - started
        assert not isinstance(outcome, tuple), outcome
        assert outcome.analysis is not None and outcome.drc is not None
        if index == 0:
            continue
        walls.append(wall)
        for stage in STAGES:
            stages[stage].append(outcome.timings_s[stage])
    return {
        "runs": runs,
        "wall_s": {"p50": percentile(walls, 0.5), "p95": percentile(walls, 0.95), "max": max(walls)},
        "stage_s": {s: {"p50": percentile(v, 0.5), "p95": percentile(v, 0.95)} for s, v in stages.items()},
    }


@pytest.mark.req("REQ-N-01")
def test_pf01_default_design_20_warm_runs(baseline_cases):
    """Records p50, p95 and stage times of the default design; fails only when a run does not compute."""
    case = timed_runs(EXAMPLES / "spiral_12c16p_default.embodic.json", 20)
    stage_p95 = case["stage_s"]
    case["target"] = {
        "status": "assumption",
        "p95_below_s": PF01_P95_S,
        "p95_met": case["wall_s"]["p95"] < PF01_P95_S,
        "stage_budget_s": PF01_STAGE_BUDGET_S,
        "stage_budget_met": {s: stage_p95[s]["p95"] <= b for s, b in PF01_STAGE_BUDGET_S.items()},
    }
    baseline_cases["PF-01 spiral_12c16p_default"] = case
    assert case["wall_s"]["p95"] > 0


def large_design(path: Path) -> Path:
    """Write the PF-02 design: the default example with 24 coils, 12 copper layers and 6 pairs in one series group.

    The dielectric thickness of 0.13 mm between copper layers is an example value chosen for this test.
    """
    document = json.loads((EXAMPLES / "spiral_12c16p_default.embodic.json").read_text(encoding="utf-8"))
    design = document["design"]
    design["winding"]["coil"]["coil_count"] = 24
    layers = []
    for n in range(1, 13):
        layers.append({"kind": "copper", "name": f"L{n}", "thickness_mm": 0.0348})
        if n < 12:
            layers.append({"kind": "dielectric", "material": "FR-4", "name": f"D{n}", "thickness_mm": 0.13})
    design["stackup"]["layers"] = layers
    pairs = [
        {"index": i, "layer_in": f"L{2 * i + 1}", "layer_out": f"L{2 * i + 2}", "phases": None, "rotation_deg": 0.0}
        for i in range(6)
    ]
    design["winding"]["layers"] = {"pairs": pairs, "series_groups": [list(range(6))]}
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


@pytest.mark.req("REQ-N-03")
@pytest.mark.slow
def test_pf02_large_design(baseline_cases, tmp_path):
    """Records the recompute time of 24 coils on 12 copper layers with 6 series pairs."""
    case = timed_runs(large_design(tmp_path / "large.embodic.json"), 3)
    case["design"] = "spiral_12c16p_default with coil_count 24, 12 copper layers (0.13 mm FR-4 between), 6 pairs"
    case["target"] = {"status": "assumption", "below_s": PF02_TARGET_S, "met": case["wall_s"]["max"] < PF02_TARGET_S}
    baseline_cases["PF-02 large design"] = case
    assert case["wall_s"]["max"] > 0


COLD_START = """
import sys
from pathlib import Path
from embodic.ui import app as shell
qt = shell.qt_application()
window = shell.create_shell(shell.QSettingsStore(), shell.ShellPaths(recovery_dir=Path(sys.argv[1]))).window
window.resize(1280, 800)
window.show()
qt.processEvents()
print("shown" if window.isVisible() else "hidden", flush=True)
"""


@pytest.mark.req("REQ-N-22")
def test_pf03_cold_start_to_a_shown_window_offscreen(baseline_cases, tmp_path):
    """Records process start to a shown main window on Qt's offscreen platform: `inferred` for a desktop session."""
    pytest.importorskip("PySide6")
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen", "HOME": str(tmp_path), "XDG_CONFIG_HOME": str(tmp_path)}
    seconds = []
    for run in range(3):
        started = time.perf_counter()
        completed = subprocess.run(
            [sys.executable, "-c", COLD_START, str(tmp_path / f"recovery{run}")],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        seconds.append(time.perf_counter() - started)
        assert completed.stdout.strip().splitlines()[-1:] == ["shown"], completed.stderr
    baseline_cases["PF-03 cold start offscreen"] = {
        "runs": 3,
        "wall_s": {"p50": percentile(seconds, 0.5), "max": max(seconds)},
        "platform": "offscreen (inferred for a desktop session)",
        "target": {"status": "assumption", "below_s": PF03_TARGET_S, "met": max(seconds) < PF03_TARGET_S},
    }


@pytest.mark.req("REQ-N-01")
@pytest.mark.parametrize("example", ["serpentine_16p_example", "wave_16p_example"])
def test_pf05_serpentine_and_wave_baselines(baseline_cases, example):
    """Records the recompute time of one serpentine and one wave example; no target exists."""
    case = timed_runs(EXAMPLES / f"{example}.embodic.json", 5)
    baseline_cases[f"PF-05 {example}"] = case
    assert case["wall_s"]["p95"] > 0
