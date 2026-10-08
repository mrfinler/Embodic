"""UT-RES-01: AnalysisResult holds no bare float, and its JSON keeps each value's status and tag (REQ-T-02)."""

import dataclasses
import json
import typing

import pytest

from embodic.model.vocabulary import Phase
from embodic.results.analysis_result import AnalysisResult, LayerResult, PhaseResult, TorqueSpeedEstimate, to_json
from embodic.results.traceable import Traceable, traced
from embodic.units import Unit

STRUCTURAL = {"layers", "phases", "torque_speed", "registry_version", "layer", "phase"}


def traceable_fields(cls) -> dict[str, object]:
    """Return the type hints of a container, minus the fields that are structure rather than numbers."""
    return {k: v for k, v in typing.get_type_hints(cls).items() if k not in STRUCTURAL}


@pytest.mark.req("REQ-T-02")
@pytest.mark.parametrize("cls", [AnalysisResult, LayerResult, PhaseResult, TorqueSpeedEstimate])
def test_analysis_result_every_number_is_traceable(cls):
    """Catches a container field added as a bare float, which would reach the UI without unit or badge."""
    bare = {k: v for k, v in traceable_fields(cls).items() if typing.get_origin(v) is not Traceable}
    assert bare == {}


def build_result(registry) -> AnalysisResult:
    """Build a result whose every number comes from traced(), using the EQ-ID named in the contract comment."""

    def t(eq_id: str, value=1.0, unit=Unit.ONE) -> Traceable:
        return traced("q", value, unit, eq_ids=[eq_id], inputs=[], registry=registry)

    fields = {name: t("EQ-09") for name in traceable_fields(AnalysisResult)}
    fields["inductance_estimate_h"] = t("EQ-14", float("nan"), Unit.H)
    fields["emf_waveform_v"] = t("EQ-18", (0.0, 1.0), Unit.V)
    layer = LayerResult(layer="F.Cu", z_mm=t("EQ-05", 0.1, Unit.MM), b1_peak_mid_radius_t=t("EQ-05", 0.4, Unit.T))
    phase = PhaseResult(phase=Phase.A, **{k: t("EQ-10") for k in traceable_fields(PhaseResult)})
    return AnalysisResult(
        **fields, layers=(layer,), phases=(phase,), torque_speed=None, registry_version=registry.version
    )


@pytest.mark.req("REQ-T-02", "REQ-T-07")
def test_analysis_result_to_json_keeps_status_assumptions_and_encodes_non_finite(packaged):
    """Catches a JSON form that drops badge, reasons or tag, writes NaN (invalid JSON), or loses enum values."""
    data = build_result(packaged).to_json()
    text = json.dumps(data, allow_nan=False)
    inductance = data["inductance_estimate_h"]
    assert inductance["value"] == {"$f": "nan"}
    assert inductance["status"] == "unresolved"
    assert inductance["label"] == "estimate"
    assert inductance["unit"] == "H"
    assert data["layers"][0]["b1_peak_mid_radius_t"]["eq_ids"] == ["EQ-05"]
    assert data["phases"][0]["phase"] == "A"
    assert data["phases"][0]["resistance_20c_ohm"]["assumed_inputs"][0]["reason"] == "equation_assumption"
    assert data["registry_version"] == packaged.version
    assert '"status_reasons"' in text


@pytest.mark.req("REQ-T-02", "REQ-T-04")
def test_analysis_result_every_id_resolves(packaged):
    """UT-RES-01: walk every Traceable in the result; each EQ-ID and EV-ID resolves in the registry."""
    result = build_result(packaged)
    found = []

    def walk(value):
        if isinstance(value, Traceable):
            found.append(value)
        elif dataclasses.is_dataclass(value):
            for f in dataclasses.fields(value):
                walk(getattr(value, f.name))
        elif isinstance(value, tuple):
            for item in value:
                walk(item)

    walk(result)
    phase_count = len(traceable_fields(PhaseResult))
    assert len(found) == len(traceable_fields(AnalysisResult)) + len(traceable_fields(LayerResult)) + phase_count
    assert all(t.eq_ids and set(t.eq_ids) <= packaged.equations.keys() for t in found)
    assert all(set(t.evidence_ids) <= packaged.evidence.keys() for t in found)


@pytest.mark.req("REQ-T-02")
def test_analysis_result_to_json_rejects_unknown_objects():
    """Catches a serializer that writes repr() of an object it does not know."""
    with pytest.raises(TypeError):
        to_json(object())
