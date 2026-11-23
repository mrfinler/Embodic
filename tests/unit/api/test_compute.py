"""The compute facade (interfaces.md section 10): stages, cache, cancellation, internal errors, PR-09 determinism."""

import dataclasses
import json
import math
from pathlib import Path

import pytest

from embodic import api
from embodic.api import StageCache, compute, compute_project, outcome_to_json
from embodic.drc import CancelToken
from embodic.errors import IssueCategory, Severity
from embodic.io.examples import examples_dir, load_example
from embodic.io.project import LoadedDraft, ProjectFile, project_provenance, save_project
from embodic.model.design import DesignParameters
from embodic.model.draft import draft_from_design
from embodic.model.outline import PolygonOutline
from embodic.model.provenance import ProvenanceMap
from embodic.results import load_registry
from embodic.results.status import Status

CF11 = "spiral_12c16p_default"


def _cf11() -> tuple[DesignParameters, ProvenanceMap]:
    ref, design = load_example(CF11)
    return design, project_provenance(ProjectFile(design=design, origin=ref))


def _computed(design: DesignParameters, provenance: ProvenanceMap, **kwargs: object) -> api.ComputeOutcome:
    outcome = compute(design, provenance, **kwargs)  # type: ignore[arg-type]
    assert outcome is not None
    return outcome


@pytest.mark.req("REQ-F-14")
def test_cf11_runs_every_stage() -> None:
    """Catches a stage the facade skips: CF-11 gives boards, one passing DRC report per board and an analysis."""
    design, provenance = _cf11()
    outcome = _computed(design, provenance)
    assert outcome.ok
    assert outcome.boards is not None and outcome.drc is not None and outcome.analysis is not None
    assert len(outcome.drc) == len(outcome.boards.boards) == 1
    assert set(outcome.timings_s) == {"validate", "geometry", "drc", "physics"}
    assert outcome.versions.schema == 2
    assert outcome.analysis.ke_line_peak_v_s_per_rad.value > 0


@pytest.mark.req("REQ-N-04")
def test_pr_09_same_design_gives_byte_identical_json() -> None:
    """PR-09. Catches non-determinism (timings, set order, cache state) leaking into the results JSON."""
    design, provenance = _cf11()
    first = json.dumps(outcome_to_json(_computed(design, provenance, cache=StageCache())), sort_keys=True)
    second = json.dumps(outcome_to_json(_computed(design, provenance, cache=StageCache())), sort_keys=True)
    assert first == second


@pytest.mark.req("REQ-N-04")
def test_cache_reuses_stage_products_for_the_same_inputs() -> None:
    """Catches a cache that is never read: the second run returns the very objects of the first."""
    design, provenance = _cf11()
    cache = StageCache()
    first, second = _computed(design, provenance, cache=cache), _computed(design, provenance, cache=cache)
    assert second.boards is first.boards
    assert second.analysis is first.analysis
    other = _computed(design, provenance, cache=StageCache())
    assert other.boards is not first.boards and other.boards == first.boards


@pytest.mark.req("REQ-T-05")
def test_cached_analysis_uses_current_test_evidence() -> None:
    """A shared cache must not show a tested badge after its supporting evidence is removed."""
    ref, design = load_example("spiral_12c10p_d08")
    provenance = project_provenance(ProjectFile(design=design, origin=ref))
    registry = load_registry()
    check_ids = frozenset(test for eq_id in ("EQ-10", "EQ-11", "EQ-07") for test in registry.equation(eq_id).tests)
    with_tests = dataclasses.replace(registry, passed_tests=check_ids)
    without_tests = dataclasses.replace(registry, passed_tests=frozenset())
    cache = StageCache()

    checked = _computed(design, provenance, cache=cache, registry=with_tests)
    unchecked = _computed(design, provenance, cache=cache, registry=without_tests)

    assert checked.analysis is not None and unchecked.analysis is not None
    assert checked.analysis.resistance_phase_20c_ohm.status is Status.INFERRED
    assert unchecked.analysis.resistance_phase_20c_ohm.status is Status.NOT_TESTED


@pytest.mark.req("REQ-N-04")
def test_stage_cache_keeps_the_eight_most_recently_used() -> None:
    """Catches an unbounded cache or FIFO eviction: a read refreshes an entry, the ninth put drops the oldest."""
    cache = StageCache()
    for n in range(8):
        cache.put("drc", str(n), n)
    assert cache.get("drc", "0") == 0
    cache.put("drc", "8", 8)
    assert cache.get("drc", "1") is None
    assert cache.get("drc", "0") == 0
    assert cache.get("physics", "0") is None


@pytest.mark.req("REQ-F-14")
def test_invalid_design_stops_before_geometry() -> None:
    """Catches a facade that generates copper from an invalid design."""
    design, provenance = _cf11()
    odd = dataclasses.replace(design, rotor=dataclasses.replace(design.rotor, poles=15))
    outcome = _computed(odd, provenance)
    assert "INVALID_POLE_COUNT_ODD" in [i.code for i in outcome.issues]
    assert (outcome.boards, outcome.drc, outcome.analysis) == (None, None, None)
    assert outcome.design_hash.startswith("sha256:")
    assert not outcome.ok


@pytest.mark.req("REQ-F-14")
@pytest.mark.parametrize(("value", "encoded"), [(math.nan, "nan"), (math.inf, "inf"), (-math.inf, "-inf")])
def test_compute_reports_non_finite_design_values(value: float, encoded: str) -> None:
    """A typed design with a non-finite input is validated and its outcome has a JSON form."""
    design, provenance = _cf11()
    invalid = dataclasses.replace(design, rotor=dataclasses.replace(design.rotor, air_gap_mm=value))

    outcome = _computed(invalid, provenance)

    assert [(issue.code, issue.pointers) for issue in outcome.issues] == [("INVALID_TYPE", ("/rotor/air_gap_mm",))]
    assert outcome.design_hash == ""
    assert (outcome.boards, outcome.drc, outcome.analysis) == (None, None, None)
    document = json.loads(json.dumps(outcome_to_json(outcome), allow_nan=False))
    assert document["design"]["rotor"]["air_gap_mm"] == {"$f": encoded}


@pytest.mark.req("REQ-F-14")
def test_physics_runs_even_with_drc_violations() -> None:
    """Catches a facade that drops the analysis when DRC fails: 12/14 copper on the 93 mm CF-11 board."""
    design, provenance = _cf11()
    assert isinstance(design.outline.board, PolygonOutline)
    poles14 = dataclasses.replace(design, rotor=dataclasses.replace(design.rotor, poles=14))
    outcome = _computed(poles14, provenance)
    assert outcome.drc is not None and not outcome.drc[0].passed
    assert outcome.analysis is not None
    assert not outcome.ok


@pytest.mark.req("REQ-F-14")
def test_internal_error_becomes_an_issue_naming_the_stage(monkeypatch: pytest.MonkeyPatch) -> None:
    """Catches an exception swallowed into a default or escaping the facade."""

    def broken(*_: object) -> None:
        raise RuntimeError("generator bug")

    monkeypatch.setattr(api, "build_layout", broken)
    design, provenance = _cf11()
    outcome = _computed(design, provenance)
    internal = [i for i in outcome.issues if i.category is IssueCategory.INTERNAL]
    assert [i.code for i in internal] == ["INTERNAL_GEOMETRY_FAILED"]
    assert internal[0].severity is Severity.ERROR
    assert isinstance(internal[0].value, str) and "RuntimeError: generator bug" in internal[0].value
    assert (outcome.boards, outcome.drc, outcome.analysis) == (None, None, None)


@pytest.mark.req("REQ-F-14")
def test_internal_drc_error_still_lets_physics_run(monkeypatch: pytest.MonkeyPatch) -> None:
    """Catches a DRC failure that also drops the analysis, although physics needs only the boards."""

    def broken(*_: object, **__: object) -> None:
        raise ValueError("drc bug")

    monkeypatch.setattr(api, "run_drc", broken)
    design, provenance = _cf11()
    outcome = _computed(design, provenance)
    assert [i.code for i in outcome.issues] == ["INTERNAL_DRC_FAILED"]
    assert outcome.drc is None and outcome.analysis is not None and not outcome.ok


@pytest.mark.req("REQ-F-14")
def test_cancelled_compute_returns_none() -> None:
    """Catches a cancelled run that returns a partial outcome as if it were complete."""
    design, provenance = _cf11()
    token = CancelToken()
    token.cancel()
    assert compute(design, provenance, cancel=token) is None


@pytest.mark.req("REQ-F-14", "REQ-F-15")
def test_compute_project_returns_missing_pointers_for_a_draft(tmp_path: Path) -> None:
    """Catches a draft that is computed with invented values instead of returning what is missing (D-014)."""
    design, _ = _cf11()
    values = dict(draft_from_design(design).values)
    del values["/winding/coil/trace_width_mm"], values["/rotor/poles"]
    path = tmp_path / "draft.embodic.json"
    save_project(path, LoadedDraft(draft=dataclasses.replace(draft_from_design(design), values=values), origin=None))
    result = compute_project(path)
    assert isinstance(result, tuple)
    missing = [i for i in result if i.code == "MISSING_DESIGN_INCOMPLETE"]
    assert missing[0].pointers == ("/winding/coil/trace_width_mm", "/rotor/poles")


@pytest.mark.req("REQ-F-15")
def test_compute_project_of_an_example_project(tmp_path: Path) -> None:
    """Catches compute_project losing the origin: the outcome provenance labels the example's fields `example`."""
    ref, design = load_example(CF11)
    path = tmp_path / "p.embodic.json"
    save_project(path, ProjectFile(design=design, origin=ref))
    outcome = compute_project(path)
    assert isinstance(outcome, api.ComputeOutcome)
    assert outcome.ok
    assert outcome.provenance["/rotor/poles"].provenance == "example"


@pytest.mark.req("REQ-F-15", "REQ-F-18")
def test_compute_project_returns_errors_from_a_complete_project(tmp_path: Path) -> None:
    """Invalid stored provenance is reported before computing a complete project."""
    ref, design = load_example(CF11)
    path = tmp_path / "p.embodic.json"
    save_project(path, ProjectFile(design=design, origin=ref))
    document = json.loads(path.read_text(encoding="utf-8"))
    document["provenance"]["/rotor/poles"]["provenance"] = "unknown"
    path.write_text(json.dumps(document), encoding="utf-8")

    result = compute_project(path)

    assert isinstance(result, tuple)
    assert [(issue.code, issue.pointers) for issue in result] == [("INVALID_PROVENANCE", ("/provenance/rotor/poles",))]


@pytest.mark.req("REQ-F-15")
@pytest.mark.parametrize("path", sorted(examples_dir().glob("*.embodic.json")), ids=lambda p: p.name.split(".")[0])
def test_compute_project_opens_every_packaged_example_file(path: Path) -> None:
    """Catches D-036 f: an example file the loader refused as INVALID_PROJECT_FILE could not be opened or computed.

    The file is the one the examples gallery reads, with its `example` object, and not a copy that `save_project`
    wrote. The outcome must hold the design of the example id and label its fields `example`.
    """
    outcome = compute_project(path)
    assert isinstance(outcome, api.ComputeOutcome), outcome
    assert outcome.design == load_example(path.name.split(".")[0])[1]
    assert outcome.provenance["/rotor/poles"].provenance == "example"


@pytest.mark.req("REQ-F-15")
def test_compute_project_of_a_missing_file(tmp_path: Path) -> None:
    """Catches a missing file raising instead of returning an issue."""
    result = compute_project(tmp_path / "absent.embodic.json")
    assert isinstance(result, tuple)
    assert [i.code for i in result] == ["INVALID_PROJECT_NOT_FOUND"]


@pytest.mark.req("REQ-T-10")
def test_outcome_json_names_its_format_and_calls_the_drc_distance_clearance() -> None:
    """Catches DEF-UV8-03 (D-051 a): the JSON called the computed DRC distance "measured", D-007's provenance word.

    The wave example fails DRC, so its document holds violations as well as summaries. The project schema stays 1.
    """
    ref, design = load_example("wave_16p_example")
    document = outcome_to_json(_computed(design, project_provenance(ProjectFile(design=design, origin=ref))))
    assert (document["format"], document["format_version"]) == ("embodic.outcome", 2)
    (report,) = document["drc"]
    assert {key for violation in report["violations"] for key in violation} == {
        "kind",
        "layer",
        "clearance_mm",
        "required_mm",
        "at_mm",
        "objects",
    }
    assert {key for summary in report["summaries"] for key in summary} == {
        "kind",
        "least_clearance_mm",
        "required_mm",
        "pairs_checked",
    }
    assert "measured" not in json.dumps(document["drc"])
    assert document["versions"]["schema"] == 2
