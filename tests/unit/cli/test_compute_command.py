"""``embodic-cli compute`` (REQ-F-18, UT-CLI-01): the exit code and the JSON file that scripts read."""

import json
import re
from pathlib import Path

import pytest

from embodic.api import compute_project, outcome_to_json
from embodic.results.status import Status

CF11 = "spiral_12c16p_default"


@pytest.mark.req("REQ-F-18")
def test_compute_json_equals_the_facade_outcome(run, project_of, tmp_path: Path) -> None:
    """Catches a CLI that writes its own summary instead of the outcome: the file must equal outcome_to_json."""
    out = tmp_path / "out.json"
    code, _, _ = run("compute", project_of(CF11), "--json", out)
    expected = json.loads(json.dumps(outcome_to_json(compute_project(project_of(CF11)))))
    assert code == 0
    assert json.loads(out.read_text(encoding="utf-8")) == expected


@pytest.mark.req("REQ-F-18")
def test_compute_json_holds_value_unit_status_and_equations_of_every_result(run, project_of, tmp_path: Path) -> None:
    """Catches a JSON that drops what makes a number traceable: unit, status label and equation ids (REQ-N-01)."""
    out = tmp_path / "out.json"
    run("compute", project_of(CF11), "--json", out)
    analysis = json.loads(out.read_text(encoding="utf-8"))["analysis"]
    results = [v for v in analysis.values() if isinstance(v, dict) and "value" in v]
    assert results
    for result in results:
        assert isinstance(result["value"], int | float | list) and isinstance(result["unit"], str)
        assert result["status"] in {status.value for status in Status}
        assert result["eq_ids"] and all(eq.startswith("EQ-") for eq in result["eq_ids"])
    assert analysis["ke_phase_v_s_per_rad"]["unit"] == "V_s_per_rad"


@pytest.mark.req("REQ-F-18")
def test_compute_prints_a_summary_of_the_design(run, project_of) -> None:
    """Catches a command that exits 0 and says nothing: the design, its hash and the DRC result are on stdout."""
    code, out, _ = run("compute", project_of(CF11))
    lines = out.splitlines()
    assert code == 0
    assert lines[0] == "Design: Spiral, 12 coils, 16 poles"
    assert lines[1].startswith("Design hash: sha256:")
    assert lines[2] == "Topology: spiral, boards: 1"
    assert lines[3] == "Design rule check: passed"


@pytest.mark.req("REQ-F-18")
def test_timings_lists_every_stage_that_ran_and_only_on_request(run, project_of) -> None:
    """Catches `--timings` ignored, or timings printed unasked; a skipped DRC has no timing line entry."""
    stage = r"\d+\.\d{3}"
    _, quiet, _ = run("compute", project_of(CF11))
    _, timed, _ = run("compute", project_of(CF11), "--timings")
    _, no_drc, _ = run("compute", project_of(CF11), "--timings", "--no-drc")
    assert "Timings" not in quiet
    assert re.search(
        rf"^Timings \(s\): validate {stage}, geometry {stage}, drc {stage}, physics {stage}$", timed, re.MULTILINE
    )
    assert re.search(rf"^Timings \(s\): validate {stage}, geometry {stage}, physics {stage}$", no_drc, re.MULTILINE)
