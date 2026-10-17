"""REQ-T-02: the real AnalysisResult of every packaged example holds only Traceables whose IDs resolve."""

import dataclasses

import pytest

from embodic.api import ComputeOutcome, compute
from embodic.io.examples import list_examples, load_example
from embodic.io.project import project_from_example, project_provenance
from embodic.results.registry import Registry
from embodic.results.traceable import Traceable

EXAMPLE_IDS = tuple(info.example_id for info in list_examples())
KIND_TAGS = {"input", "derived", "count"}  # the three tags of ui/strings/results.py, shown when a result has no EQ-ID


def computed(example_id: str) -> ComputeOutcome:
    """Return the outcome of a packaged example, as the engine computes it."""
    project = project_from_example(load_example(example_id))
    outcome = compute(project.design, project_provenance(project))
    assert outcome is not None and outcome.analysis is not None, example_id
    return outcome


def walk(value: object, path: str, traceables: list[tuple[str, Traceable]], bare: list[tuple[str, object]]) -> None:
    """Collect the Traceables below `value` and every number that sits outside a Traceable."""
    if isinstance(value, Traceable):
        traceables.append((path, value))
    elif dataclasses.is_dataclass(value) and not isinstance(value, type):
        for field in dataclasses.fields(value):
            walk(getattr(value, field.name), f"{path}.{field.name}", traceables, bare)
    elif isinstance(value, tuple | list):
        for index, item in enumerate(value):
            walk(item, f"{path}[{index}]", traceables, bare)
    elif isinstance(value, dict):
        for key, item in value.items():
            walk(item, f"{path}[{key!r}]", traceables, bare)
    elif isinstance(value, int | float) and not isinstance(value, bool):
        bare.append((path, value))


@pytest.fixture(scope="module", params=EXAMPLE_IDS)
def walked(request: pytest.FixtureRequest) -> tuple[ComputeOutcome, list[tuple[str, Traceable]], list]:
    """Return the outcome of one example with its walked Traceables and bare numbers."""
    outcome = computed(request.param)
    traceables: list[tuple[str, Traceable]] = []
    bare: list[tuple[str, object]] = []
    walk(outcome.analysis, "analysis", traceables, bare)
    return outcome, traceables, bare


@pytest.mark.req("REQ-T-02")
def test_t02_every_number_of_every_example_is_a_traceable(walked):
    """Catches an engine path that emits a bare float for one topology, which would reach the UI with no badge."""
    outcome, traceables, bare = walked
    assert bare == []
    paths = [path for path, _ in traceables]
    assert any(".phases[" in p for p in paths) and any(".layers[" in p for p in paths)
    assert (outcome.analysis.torque_speed is not None) == any(".torque_speed." in p for p in paths)


@pytest.mark.req("REQ-T-02")
def test_t02_every_eq_id_resolves_or_the_value_carries_a_kind_tag(walked, packaged: Registry):
    """Catches an engine path that emits an EQ-ID the registry does not hold, or a value with neither ID nor tag."""
    _, traceables, _ = walked
    for path, t in traceables:
        if t.eq_ids:
            assert set(t.eq_ids) <= packaged.equations.keys(), (path, t.eq_ids)
        else:
            assert t.kind_tag in KIND_TAGS, (path, t.kind_tag)


@pytest.mark.req("REQ-T-02")
def test_t02_every_evidence_id_resolves(walked, packaged: Registry):
    """Catches a Traceable that cites an evidence entry the packaged registry does not hold."""
    _, traceables, _ = walked
    for path, t in traceables:
        assert set(t.evidence_ids) <= packaged.evidence.keys(), (path, t.evidence_ids)


@pytest.mark.req("REQ-T-02")
def test_t02_the_walk_reports_a_bare_float_and_an_unknown_id_that_it_is_given(packaged: Registry):
    """Control. Catches a walk that cannot fail: a planted bare float and a planted unknown EQ-ID are both found."""
    outcome = computed("spiral_12c10p_d08")
    planted_t = dataclasses.replace(outcome.analysis.torque_n_m, eq_ids=("EQ-99",))
    planted = dataclasses.replace(outcome.analysis, torque_n_m=planted_t, thd_phase=0.5)
    traceables: list[tuple[str, Traceable]] = []
    bare: list[tuple[str, object]] = []
    walk(planted, "analysis", traceables, bare)
    assert bare == [("analysis.thd_phase", 0.5)]
    unresolved = [p for p, t in traceables if t.eq_ids and not set(t.eq_ids) <= packaged.equations.keys()]
    assert unresolved == ["analysis.torque_n_m"]
